# =====================================================
# FILE: app_v2.py
# =====================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import DataLoadError, load_data
from utils.styling import inject_base_css
from pages_content import (
    executive_dashboard,
    customer_intelligence,
    churn_prediction,
    sales_forecasting,
    inventory_optimization,
)
from auth import login

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="NeuralRetail Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)
name, authentication_status, username, authenticator = login()

if authentication_status is False:
    st.error("Incorrect username or password")
    st.stop()

elif authentication_status is None:
    st.warning("Please login to continue")
    st.stop()

# User Role
role = username

# Base enterprise styles (cards, tables, ai-recommendation-box, etc.)
# used by the individual pages_content modules.
inject_base_css()

# Interface theme layer -- dark "NeuralRetail" look (map hints, filter
# chips, high-contrast KPI cards) layered on top of the base theme.
st.markdown("""
<style>

/* ---------- App background ---------- */
.stApp{
    background-color:#0B1220;
}

.main, .block-container{
    background-color:#0B1220;
    color:#E2E8F0;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"]{
    background-color:#0F172A;
    border-right:1px solid #1E293B;
}

section[data-testid="stSidebar"] *{
    color:#E2E8F0 !important;
}

/* ---------- Headings & body text ---------- */
h1, h2, h3, h4{
    color:#F8FAFC !important;
}

p, span, label, .stMarkdown, .stCaption{
    color:#CBD5E1;
}

/* ---------- KPI / metric cards ---------- */
div[data-testid="stMetric"],
div[data-testid="metric-container"]{
    background-color:#161F32;
    padding:18px;
    border-radius:14px;
    border:1px solid #1E293B;
    border-left:5px solid #3B82F6;
    box-shadow:0px 4px 14px rgba(0,0,0,0.35);
}

div[data-testid="stMetricLabel"]{
    color:#94A3B8 !important;
    font-weight:600;
    text-transform:uppercase;
    font-size:12px;
    letter-spacing:0.04em;
}

div[data-testid="stMetricValue"]{
    color:#F8FAFC !important;
    font-size:28px !important;
    font-weight:700 !important;
}

div[data-testid="stMetricDelta"]{
    font-weight:600;
}

/* ---------- Callout boxes ---------- */
.map-hint{
    background-color:#101B34;
    border-left:4px solid #3B82F6;
    padding:10px 14px;
    border-radius:8px;
    font-size:14px;
    color:#BFDBFE;
    margin-bottom:10px;
}

.filter-chip{
    display:inline-block;
    background-color:#3B82F6;
    color:white;
    padding:6px 14px;
    border-radius:20px;
    font-weight:600;
    font-size:13px;
    margin-bottom:10px;
}

/* ---------- Tables / dataframes ---------- */
div[data-testid="stDataFrame"]{
    background-color:#161F32;
    border-radius:10px;
    border:1px solid #1E293B;
}

/* ---------- Alerts (success/warning/error/info) ---------- */
div[data-testid="stAlert"]{
    background-color:#161F32;
    border:1px solid #1E293B;
    color:#E2E8F0;
}

/* ---------- Horizontal rule ---------- */
hr{
    border-color:#1E293B;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# LOAD DATA
# =====================================================

try:
    sales, rfm, forecast, inventory = load_data()
except DataLoadError as exc:
    st.error(f"Platform Initialization Error: {exc}")
    st.stop()

# =====================================================
# SIDEBAR (nav only -- filters live on the map)
# =====================================================

st.sidebar.markdown("""
# 🛍️ NeuralRetail

AI Powered Retail Analytics

---
""")

# =====================================================
# USER INFORMATION
# =====================================================

st.sidebar.markdown("---")

st.sidebar.success(f"👤 Logged in as:\n\n{name}")

st.sidebar.info(f"🔑 Role:\n\n{role.capitalize()}")

if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()
st.sidebar.markdown("---")

PAGES = [
    "📊 Executive Dashboard",
    "👥 Customer Intelligence",
    "⚠️ Churn Prediction",
    "📈 Sales Forecasting",
    "📦 Inventory Optimization",
]

page = st.sidebar.radio("Navigation", PAGES)

st.sidebar.markdown("---")
st.sidebar.caption(
    "📍 Country filtering is done by clicking the map "
    "on the Executive Dashboard, not from this sidebar."
)

if "selected_country" not in st.session_state:
    st.session_state.selected_country = None

if st.session_state.selected_country:
    st.sidebar.success(f"Active filter: **{st.session_state.selected_country}**")
    if st.sidebar.button("Clear country filter", use_container_width=True):
        st.session_state.selected_country = None
        st.rerun()

st.sidebar.caption("Environment: Production")

# =====================================================
# ROUTING
# =====================================================

if page == "📊 Executive Dashboard":
    st.title("📊 Executive Dashboard")
    executive_dashboard.render(sales, rfm, forecast, inventory)

elif page == "👥 Customer Intelligence":
    st.title("👥 Customer Intelligence")
    customer_intelligence.render(sales, rfm)

elif page == "⚠️ Churn Prediction":
    st.title("⚠️ Churn Prediction Engine")
    churn_prediction.render(sales, rfm)

elif page == "📈 Sales Forecasting":
    st.title("📈 Sales Forecasting")
    sales_forecasting.render(sales, forecast)

elif page == "📦 Inventory Optimization":
    st.title("📦 Inventory Optimization")
    inventory_optimization.render(sales, inventory)

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")
st.caption("Developed by Viraj Shivale | NeuralRetail Analytics Project v2.0")