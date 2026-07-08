"""
Forecast utilities.

Prophet's raw output (`revenue_forecast.csv`) contains a row for every
historical training day PLUS every future day it was asked to predict --
that's why the dashboard was showing ~694 "forecast days" instead of the
intended 60: it was counting ~604 historical fitted rows as if they were
forecast rows.

get_future_forecast() isolates just the future horizon, based on the
actual last transaction date in the sales data -- not on row position --
so this stays correct even if the forecast CSV is regenerated with a
different horizon later.
"""

from __future__ import annotations

import pandas as pd

# Single source of truth for how far ahead the dashboard should show.
# Change this one constant (and the `periods=` argument in notebook 04)
# if the desired horizon ever changes.
FORECAST_HORIZON_DAYS = 60


def get_future_forecast(
    forecast: pd.DataFrame,
    sales: pd.DataFrame,
    horizon_days: int = FORECAST_HORIZON_DAYS,
) -> pd.DataFrame:
    """
    Return only the future portion of a Prophet forecast output.

    Parameters
    ----------
    forecast : DataFrame with a 'ds' column (as produced by notebook 04)
    sales : cleaned transaction-level DataFrame with an 'InvoiceDate' column,
            used to determine where "history" ends and "future" begins
    horizon_days : how many future days to keep (default 60)

    Returns
    -------
    DataFrame limited to the next `horizon_days` days after the last
    actual sale, sorted chronologically.
    """
    forecast = forecast.copy()
    forecast["ds"] = pd.to_datetime(forecast["ds"])

    last_actual_date = pd.to_datetime(sales["InvoiceDate"]).max().normalize()

    future_only = forecast[forecast["ds"] > last_actual_date].sort_values("ds")

    return future_only.head(horizon_days).reset_index(drop=True)