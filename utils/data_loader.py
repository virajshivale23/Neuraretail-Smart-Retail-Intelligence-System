"""
Centralized data & artifact loading for NeuralRetail.

Every page pulls its data through the functions in this module instead
of reading CSVs/pickles directly. That gives us one place to:
  - control caching behaviour
  - handle missing-file errors gracefully (instead of a raw traceback
    taking down the whole app)
  - log what was loaded, from where, and how long it took
  - keep file paths consistent if the folder layout ever changes

All public loaders are decorated with @st.cache_data / @st.cache_resource
so repeated navigation between pages does not re-read disk or
re-deserialize models.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import joblib
import pandas as pd
import streamlit as st

logger = logging.getLogger("neuralretail.data_loader")
if not logger.handlers:
    # Keep logging config local to this module so importing it doesn't
    # clobber logging config elsewhere in the app.
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Paths -- change these once here if the folder layout ever moves.
#
# Resolved relative to THIS FILE's location (utils/data_loader.py), not the
# process's current working directory. Streamlit's cwd depends entirely on
# where the terminal happens to be when `streamlit run` is invoked, which is
# fragile -- anchoring to the project root (one level up from utils/) means
# `data/` and `models/` resolve correctly no matter where the app is launched
# from, as long as the folder structure itself (project_root/data,
# project_root/models, project_root/utils) stays intact.
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"

SALES_PATH = DATA_DIR / "online_retail_clean.csv"
RFM_PATH = DATA_DIR / "rfm_segments.csv"
FORECAST_PATH = DATA_DIR / "revenue_forecast.csv"
INVENTORY_PATH = DATA_DIR / "inventory_plan.csv"

CHURN_MODEL_PATH = MODELS_DIR / "churn_model.pkl"
PROPHET_MODEL_PATH = MODELS_DIR / "prophet_model.pkl"

# Business rule from notebook 05: a customer with no purchase in the last
# 90 days is treated as churned. Kept as a named constant so every page
# that needs the churn definition references the same number.
CHURN_RECENCY_THRESHOLD_DAYS = 90


class DataLoadError(RuntimeError):
    """Raised when a required data or model artifact cannot be loaded."""


def _require_file(path: Path) -> None:
    """Raise a clear, actionable error if an expected artifact is missing."""
    if not path.exists():
        raise DataLoadError(
            f"Expected file not found: '{path.resolve()}'. "
            f"Run the corresponding notebook to generate it, or confirm "
            f"your data/models folders sit alongside this project's "
            f"utils/ and pages_content/ folders."
        )


@st.cache_data(show_spinner="Loading core datasets...")
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the four core CSV artifacts used across the dashboard.

    Returns
    -------
    (sales, rfm, forecast, inventory) : tuple of DataFrames
    """
    try:
        for path in (SALES_PATH, RFM_PATH, FORECAST_PATH, INVENTORY_PATH):
            _require_file(path)

        sales = pd.read_csv(SALES_PATH)
        rfm = pd.read_csv(RFM_PATH)
        forecast = pd.read_csv(FORECAST_PATH)
        inventory = pd.read_csv(INVENTORY_PATH)

        logger.info(
            "Loaded core datasets: sales=%d rows, rfm=%d rows, "
            "forecast=%d rows, inventory=%d rows",
            len(sales), len(rfm), len(forecast), len(inventory),
        )
        return sales, rfm, forecast, inventory

    except DataLoadError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface as a clean, typed error
        logger.exception("Failed to load core datasets")
        raise DataLoadError(f"Could not load core datasets: {exc}") from exc


@st.cache_resource(show_spinner="Loading churn model...")
def load_churn_model():
    """
    Load the trained XGBoost churn classifier saved by notebook 05.

    Uses @st.cache_resource (not cache_data) because the model is a
    live object with methods, not serializable tabular data.
    """
    try:
        _require_file(CHURN_MODEL_PATH)
        model = joblib.load(CHURN_MODEL_PATH)
        logger.info("Loaded churn model from %s", CHURN_MODEL_PATH)
        return model
    except DataLoadError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to load churn model")
        raise DataLoadError(f"Could not load churn model: {exc}") from exc


@st.cache_resource(show_spinner="Loading forecasting model...")
def load_prophet_model():
    """Load the trained Prophet model saved by notebook 04, if present."""
    try:
        _require_file(PROPHET_MODEL_PATH)
        model = joblib.load(PROPHET_MODEL_PATH)
        logger.info("Loaded Prophet model from %s", PROPHET_MODEL_PATH)
        return model
    except DataLoadError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to load Prophet model")
        raise DataLoadError(f"Could not load Prophet model: {exc}") from exc