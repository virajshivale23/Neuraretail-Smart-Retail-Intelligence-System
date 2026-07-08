"""
Model-facing utilities: feature prep, scoring, evaluation, and
explainability helpers for the Churn Prediction page.

Keeping this separate from data_loader.py so "get me raw data" and
"do ML things with a model" stay cleanly separated (separation of
concerns).
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import (
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from utils.data_loader import CHURN_RECENCY_THRESHOLD_DAYS

logger = logging.getLogger("neuralretail.model_utils")

CHURN_FEATURES = ["Recency", "Frequency", "Monetary"]


def add_churn_label(rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Attach a binary Churn label to an RFM table using the same business
    rule defined in notebook 05 (no purchase in the last 90 days).

    This does not mutate the input frame.
    """
    out = rfm.copy()
    if "Churn" not in out.columns:
        out["Churn"] = (out["Recency"] > CHURN_RECENCY_THRESHOLD_DAYS).astype(int)
    return out


@st.cache_data(show_spinner=False)
def score_customers(rfm_with_churn: pd.DataFrame, _model) -> pd.DataFrame:
    """
    Run the churn model over every customer and attach a churn
    probability + risk tier.

    Parameters
    ----------
    rfm_with_churn : DataFrame with Recency/Frequency/Monetary/Churn columns
    _model : fitted classifier with predict_proba (leading underscore tells
             st.cache_data not to try to hash the unhashable model object)
    """
    missing = [c for c in CHURN_FEATURES if c not in rfm_with_churn.columns]
    if missing:
        raise ValueError(f"RFM table is missing required feature(s): {missing}")

    X = rfm_with_churn[CHURN_FEATURES]
    probabilities = _model.predict_proba(X)[:, 1]

    scored = rfm_with_churn.copy()
    scored["ChurnProbability"] = probabilities
    scored["RiskTier"] = pd.cut(
        scored["ChurnProbability"],
        bins=[-0.01, 0.33, 0.66, 1.0],
        labels=["Low Risk", "Medium Risk", "High Risk"],
    )
    return scored


@st.cache_data(show_spinner=False)
def evaluate_model(rfm_with_churn: pd.DataFrame, _model) -> dict:
    """
    Reproduce the notebook 05 train/test split (same random_state=42,
    same stratification) so the ROC/PR curves and confusion matrix shown
    on the dashboard match what was reported during model development.

    Returns a dict of arrays/scalars ready for plotting -- no plotting
    logic lives here, keeping this function reusable and unit-testable.
    """
    X = rfm_with_churn[CHURN_FEATURES]
    y = rfm_with_churn["Churn"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    y_prob = _model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    fpr, tpr, _ = roc_curve(y_test, y_prob)
    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    feature_importance = pd.DataFrame({
        "Feature": CHURN_FEATURES,
        "Importance": getattr(_model, "feature_importances_", np.zeros(len(CHURN_FEATURES))),
    }).sort_values("Importance", ascending=False)

    return {
        "fpr": fpr,
        "tpr": tpr,
        "auc": auc,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": cm,
        "feature_importance": feature_importance,
        "X_test": X_test,
        "y_test": y_test,
        "test_size": len(y_test),
    }


@st.cache_data(show_spinner="Computing SHAP explanations...")
def compute_shap_values(_model, X: pd.DataFrame) -> Optional[np.ndarray]:
    """
    Compute SHAP values for a tree-based model (XGBoost).

    Returns None (rather than raising) if the `shap` package is not
    installed, so the page can degrade gracefully -- showing built-in
    feature importance instead of blocking the whole page.
    """
    try:
        import shap  # local import: optional dependency
    except ImportError:
        logger.warning("shap is not installed; skipping SHAP explanations.")
        return None

    try:
        explainer = shap.TreeExplainer(_model)
        shap_values = explainer.shap_values(X)
        return shap_values
    except Exception:  # noqa: BLE001
        logger.exception("SHAP computation failed")
        return None


def business_recommendation(row: pd.Series) -> str:
    """
    Translate a scored customer row into a plain-language recommended
    action. Rule-based on purpose: it's fast, transparent, and doesn't
    require an LLM call just to say "call this customer."
    """
    if row["RiskTier"] == "High Risk" and row["Monetary"] > 0:
        return "Win-back campaign: high value, high churn risk"
    if row["RiskTier"] == "High Risk":
        return "Re-engagement offer"
    if row["RiskTier"] == "Medium Risk" and row["Frequency"] >= 5:
        return "Loyalty / upsell campaign"
    if row["RiskTier"] == "Low Risk" and row["Monetary"] > 0:
        return "Maintain relationship; consider premium membership"
    return "Monitor"