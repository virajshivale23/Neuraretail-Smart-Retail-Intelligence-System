# =====================================================
# FILE: pages_content/churn_prediction.py
# =====================================================

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import DataLoadError, load_churn_model
from utils.model_utils import (
    add_churn_label,
    business_recommendation,
    compute_shap_values,
    evaluate_model,
    score_customers,
)
from utils.styling import apply_enterprise_theme, risk_badge_html

def _kpi_row(scored: pd.DataFrame, auc: float) -> None:
    high_risk = int((scored["RiskTier"] == "High Risk").sum())
    avg_prob = scored["ChurnProbability"].mean()
    revenue_at_risk = scored.loc[scored["RiskTier"] == "High Risk", "Monetary"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers Scored", f"{len(scored):,}")
    c2.metric("Critical Risk Cohort", f"{high_risk:,}")
    c3.metric("Mean Churn Probability", f"{avg_prob:.1%}")
    c4.metric("Capital at Risk (£)", f"£{revenue_at_risk:,.0f}", f"{auc:.3f} ROC-AUC", delta_color="normal")

def _model_performance_section(eval_results: dict) -> None:
    st.subheader("📊 Classifier Diagnostic Benchmarks")

    left, right = st.columns(2)

    with left:
        fig_roc = go.Figure()
        fig_roc.add_trace(
            go.Scatter(
                x=eval_results["fpr"], y=eval_results["tpr"],
                mode="lines", name=f"ROC (AUC = {eval_results['auc']:.3f})",
                line=dict(color="#2563EB", width=3, shape="spline"),
            )
        )
        fig_roc.add_trace(
            go.Scatter(
                x=[0, 1], y=[0, 1], mode="lines", name="Random Baseline",
                line=dict(color="#64748B", dash="dash"),
            )
        )
        fig_roc = apply_enterprise_theme(fig_roc)
        fig_roc.update_layout(
            title="Receiver Operating Characteristic (ROC) Curve", 
            xaxis_title="False Positive Rate",
            yaxis_title="True Positive Rate", 
            height=380,
        )
        st.plotly_chart(fig_roc, use_container_width=True)

    with right:
        fig_pr = go.Figure()
        fig_pr.add_trace(
            go.Scatter(
                x=eval_results["recall"], y=eval_results["precision"],
                mode="lines", name="Precision-Recall Curve",
                line=dict(color="#10B981", width=3, shape="spline"),
            )
        )
        fig_pr = apply_enterprise_theme(fig_pr)
        fig_pr.update_layout(
            title="Precision-Recall (PR) Curve", 
            xaxis_title="Recall",
            yaxis_title="Precision", 
            height=380,
        )
        st.plotly_chart(fig_pr, use_container_width=True)

    left2, right2 = st.columns(2)

    with left2:
        cm = eval_results["confusion_matrix"]
        fig_cm = px.imshow(
            cm, text_auto=True, 
            color_continuous_scale=["#EFF6FF", "#BFDBFE", "#2563EB", "#1E3A8A"],
            labels=dict(x="Predicted", y="Actual", color="Count"),
            x=["Retained", "Churned"], y=["Retained", "Churned"],
        )
        fig_cm = apply_enterprise_theme(fig_cm)
        fig_cm.update_layout(title="Diagnostic Confusion Matrix", height=380)
        st.plotly_chart(fig_cm, use_container_width=True)

    with right2:
        fig_imp = px.bar(
            eval_results["feature_importance"],
            x="Importance", y="Feature", orientation="h",
            color="Importance", 
            color_continuous_scale=["#60A5FA", "#2563EB"],
            title="Relative Feature Importance",
        )
        fig_imp = apply_enterprise_theme(fig_imp)
        fig_imp.update_layout(height=380, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_imp, use_container_width=True)

    st.caption(
        f"Model evaluated on {eval_results['test_size']:,} held-out test customers "
        f"(80/20 train/test split, random_state=42 -- matching notebook 05)."
    )

def _shap_section(model, X_sample: pd.DataFrame) -> None:
    st.subheader("🔍 Explainable AI (SHAP Global Feature Impact)")

    shap_values = compute_shap_values(model, X_sample)

    if shap_values is None:
        st.info(
            "SHAP explainability package is not available in the runtime. "
            "Displaying standard permutation importances above as the fallback."
        )
        return

    # Check for multiclass SHAP values shape (which returns a list of arrays)
    if isinstance(shap_values, list):
        # binary classification XGBoost sometimes returns list of shape [class_0, class_1]
        shap_values = shap_values[1]

    # Calculate absolute mean SHAP values
    mean_abs_shap = pd.DataFrame({
        "Feature": X_sample.columns,
        "Mean |SHAP value|": np.abs(shap_values).mean(axis=0),
    }).sort_values("Mean |SHAP value|", ascending=False)

    fig = px.bar(
        mean_abs_shap, x="Mean |SHAP value|", y="Feature", orientation="h",
        color="Mean |SHAP value|", color_continuous_scale=["#C084FC", "#8B5CF6"],
        title="Absolute SHAP Value Distribution (Global Impact)",
    )
    fig = apply_enterprise_theme(fig)
    fig.update_layout(yaxis=dict(autorange="reversed"), height=300)
    st.plotly_chart(fig, use_container_width=True)

    top_feature = mean_abs_shap.iloc[0]["Feature"]
    st.markdown(f"""
    <div class="ai-recommendation-box info" style="margin-top: 5px;">
        <div class="ai-title">🤖 SHAP Insight</div>
        <p class="ai-content">
            SHAP calculations indicate that <strong>{top_feature}</strong> exerts the strongest mathematical pull 
            on the model's classifications of customer churn across the active database.
        </p>
    </div>
    """, unsafe_allow_html=True)

def _customer_risk_table(scored: pd.DataFrame) -> None:
    st.subheader("👤 Customer Risk Ledger & Action Triggers")

    search = st.text_input("🔍 Search Cohort Directory by Customer ID", key="churn_search")

    view = scored.copy()
    if search:
        view = view[view["Customer ID"].astype(str).str.contains(search, na=False)]

    view = view.sort_values("ChurnProbability", ascending=False)
    view["Recommended Action"] = view.apply(business_recommendation, axis=1)

    display_cols = [
        "Customer ID", "Segment", "Recency", "Frequency", "Monetary",
        "ChurnProbability", "RiskTier", "Recommended Action",
    ]
    display_cols = [c for c in display_cols if c in view.columns]

    st.dataframe(
        view[display_cols].head(250).style.format({
            "ChurnProbability": "{:.1%}",
            "Monetary": "£{:,.2f}"
        }),
        use_container_width=True,
        height=400
    )
    st.caption(f"Displaying top {min(250, len(view))} of {len(view):,} matching customer records, ranked by churn risk probability.")

def render(sales: pd.DataFrame, rfm: pd.DataFrame) -> None:
    # Set page titles and filter status
    st.markdown('<div class="filter-chip">⚠️ Model Environment: XGBoost Native</div>', unsafe_allow_html=True)
    st.caption(
        "Powered by the XGBoost classifier trained in notebook 05. "
        "A customer is labeled churned if they have not purchased in the last 90 days."
    )

    try:
        model = load_churn_model()
    except DataLoadError as exc:
        st.error(
            "Could not load the churn model. Make sure "
            "`models/churn_model.pkl` exists (run notebook 05 to "
            f"generate it).\n\nDetails: {exc}"
        )
        return

    rfm_labeled = add_churn_label(rfm)

    if st.session_state.get("selected_country"):
        country = st.session_state.selected_country
        st.markdown(f'<div class="filter-chip">📍 Filtered by map selection: {country}</div>', unsafe_allow_html=True)
        ids_in_country = sales.loc[sales["Country"] == country, "Customer ID"].unique()
        rfm_labeled = rfm_labeled[rfm_labeled["Customer ID"].isin(ids_in_country)]

    if rfm_labeled.empty:
        st.warning("No customer records found matching the country filter.")
        return

    try:
        scored = score_customers(rfm_labeled, model)
        eval_results = evaluate_model(rfm_labeled, model)
    except ValueError as exc:
        st.error(f"Could not score customers: {exc}")
        return

    _kpi_row(scored, eval_results["auc"])
    st.markdown("---")

    # Risk Distributions Charts
    left_dist, right_dist = st.columns(2)
    with left_dist:
        # Probability Distribution
        fig_dist = px.histogram(
            scored, x="ChurnProbability", nbins=30, 
            color_discrete_sequence=["#2563EB"],
            title="Churn Probability Distribution Density Map",
        )
        fig_dist = apply_enterprise_theme(fig_dist)
        fig_dist.update_layout(xaxis_title="Churn Probability", yaxis_title="Customer Count")
        st.plotly_chart(fig_dist, use_container_width=True)
        
    with right_dist:
        # Risk Tier proportions
        risk_counts = scored["RiskTier"].value_counts().reset_index()
        risk_counts.columns = ["RiskTier", "Count"]
        fig_pie = px.pie(
            risk_counts, values="Count", names="RiskTier", hole=0.6,
            color="RiskTier",
            color_discrete_map={
                "High Risk": "#EF4444", 
                "Medium Risk": "#F59E0B", 
                "Low Risk": "#10B981"
            },
            title="Portfolio Customer Base by Risk Tier",
        )
        fig_pie = apply_enterprise_theme(fig_pie)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    _model_performance_section(eval_results)

    st.markdown("---")
    _shap_section(model, eval_results["X_test"])

    st.markdown("---")
    _customer_risk_table(scored)

    st.markdown("---")
    top_risk_segment = (
        scored[scored["RiskTier"] == "High Risk"]["Segment"].mode()
        if "Segment" in scored.columns else pd.Series(dtype=str)
    )
    segment_note = (
        f" Most of them belong to the <strong>{top_risk_segment.iloc[0]}</strong> segment."
        if not top_risk_segment.empty else ""
    )
    
    st.markdown(f"""
    <div class="ai-recommendation-box danger">
        <div class="ai-title">🤖 AI Risk Mitigation Advisory</div>
        <p class="ai-content">
            <strong>Business Recommendation:</strong> {int((scored['RiskTier'] == 'High Risk').sum())} customer accounts are flagged 
            at critical risk of churn, representing £{scored.loc[scored['RiskTier'] == 'High Risk', 'Monetary'].sum():,.0f} 
            in value-at-risk.{segment_note} Prioritize targeted win-back campaigns and trigger re-engagement workflows 
            for this group before the close of the current fiscal cycle.
        </p>
    </div>
    """, unsafe_allow_html=True)