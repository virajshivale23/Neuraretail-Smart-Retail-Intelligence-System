# =====================================================
# FILE: utils/styling.py
# =====================================================

import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ---------------------------------------------------------------------
   Design tokens -- one source of truth for spacing/radius/shadow scale
   so every card, button, and container reads as one coherent system
   rather than a pile of one-off values.
--------------------------------------------------------------------- */
:root {
    --radius-sm: 10px;
    --radius-md: 16px;
    --radius-pill: 9999px;

    --shadow-resting: 0 4px 12px rgba(15, 23, 42, 0.04);
    --shadow-hover: 0 16px 28px -8px rgba(15, 23, 42, 0.12);
    --shadow-accent-hover: 0 16px 28px -8px rgba(37, 99, 235, 0.16);

    --ease-out: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global Styles */
html, body, [class*="css"], .st-emotion-cache-16idsys p {
    font-family: 'Inter', sans-serif !important;
    color: #0F172A !important;
}

.stApp {
    background-color: #F8FAFC;
}

/* Remove default Streamlit top header styling and footer */
#MainMenu, footer, header {
    visibility: hidden;
    height: 0px !important;
}

/* Sidebar Styling - Slate Dark */
section[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 1px solid #1E293B;
}

section[data-testid="stSidebar"] * {
    color: #F8FAFC !important;
}

section[data-testid="stSidebar"] hr {
    border-color: #1E293B;
}

/* Sidebar Radio Navigation */
.stRadio > div {
    gap: 8px;
}

.stRadio label {
    padding: 10px 14px;
    background: transparent;
    border-radius: 10px;
    transition: all 0.25s ease;
    cursor: pointer;
    border: 1px solid transparent;
}

.stRadio label:hover {
    background: #1E293B;
    transform: translateX(4px);
    border-color: rgba(96, 165, 250, 0.2);
}

.stRadio div[role="radiogroup"] > div[data-checked="true"] > label {
    background: #2563EB !important;
    font-weight: 600 !important;
    border-color: #60A5FA !important;
}

/* Typography */
h1 {
    font-size: 32px !important;
    font-weight: 700 !important;
    color: #1E3A8A !important;
    letter-spacing: -0.025em;
    margin-bottom: 20px !important;
    margin-top: 10px !important;
}

h2 {
    font-size: 22px !important;
    font-weight: 600 !important;
    color: #1E3A8A !important;
    margin-top: 24px !important;
    margin-bottom: 12px !important;
}

h3 {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #64748B !important;
    margin-top: 16px !important;
    margin-bottom: 8px !important;
}

/* Metric Cards - Glassmorphism with a subtle shimmer sweep on hover */
div[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(10px);
    border-radius: var(--radius-md) !important;
    padding: 22px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: var(--shadow-resting) !important;
    transition: transform 0.35s var(--ease-out), box-shadow 0.35s var(--ease-out), border-color 0.35s var(--ease-out) !important;
    position: relative;
    overflow: hidden;
}

div[data-testid="metric-container"]::after {
    content: "";
    position: absolute;
    top: 0;
    left: -120%;
    width: 60%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.55), transparent);
    transition: left 0.6s var(--ease-out);
    pointer-events: none;
}

div[data-testid="metric-container"]:hover {
    transform: translateY(-6px) !important;
    box-shadow: var(--shadow-accent-hover) !important;
    border-color: #60A5FA !important;
    background: rgba(255, 255, 255, 0.97) !important;
}

div[data-testid="metric-container"]:hover::after {
    left: 120%;
}

div[data-testid="metric-container"] label,
div[data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #0F172A !important;
    font-weight: 700 !important;
    font-size: 28px !important;
    margin-top: 6px;
    transition: color 0.3s ease;
}

div[data-testid="metric-container"]:hover div[data-testid="stMetricValue"] {
    color: #1E3A8A !important;
}

/* Metric Delta formatting */
div[data-testid="stMetricDelta"] {
    font-weight: 600 !important;
    font-size: 14px !important;
}

/* Respect users who've asked for less motion */
@media (prefers-reduced-motion: reduce) {
    div[data-testid="metric-container"],
    div[data-testid="metric-container"]:hover,
    div[data-testid="metric-container"]::after {
        transform: none !important;
        transition: none !important;
    }
}

/* Dataframe containers */
div[data-testid="stDataFrame"] {
    background: #FFFFFF;
    border-radius: var(--radius-md);
    border: 1px solid #E2E8F0;
    box-shadow: var(--shadow-resting);
    padding: 10px;
    transition: box-shadow 0.3s var(--ease-out);
}

div[data-testid="stDataFrame"]:hover {
    box-shadow: var(--shadow-hover);
}

/* Premium Buttons */
.stButton>button {
    background: #2563EB !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1px solid #2563EB !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 8px rgba(37, 99, 235, 0.15) !important;
}

.stButton>button:hover {
    background: #1E3A8A !important;
    border-color: #1E3A8A !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 12px rgba(37, 99, 235, 0.25) !important;
}

/* Filter Chips */
.filter-chip {
    display: inline-flex;
    align-items: center;
    background: #EFF6FF;
    color: #1E3A8A;
    padding: 8px 16px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid #BFDBFE;
    margin-bottom: 20px;
}

/* Map hint / Summary box */
.map-hint {
    background: #FFFFFF;
    border-left: 4px solid #2563EB;
    color: #64748B;
    padding: 14px 18px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    border-top: 1px solid #E2E8F0;
    border-right: 1px solid #E2E8F0;
    border-bottom: 1px solid #E2E8F0;
}

/* Alert/Recommender Boxes */
.ai-recommendation-box {
    background-color: #FFFFFF;
    border-left: 4px solid #10B981;
    padding: 20px;
    border-radius: var(--radius-sm);
    border-top: 1px solid #E2E8F0;
    border-right: 1px solid #E2E8F0;
    border-bottom: 1px solid #E2E8F0;
    margin-top: 15px;
    box-shadow: var(--shadow-resting);
    transition: box-shadow 0.3s var(--ease-out), transform 0.3s var(--ease-out);
}

.ai-recommendation-box:hover {
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
}

.ai-recommendation-box.warning {
    border-left-color: #F59E0B;
}

.ai-recommendation-box.danger {
    border-left-color: #EF4444;
}

.ai-recommendation-box.info {
    border-left-color: #2563EB;
}

.ai-title {
    color: #1E3A8A;
    font-weight: 700;
    font-size: 16px;
    margin-top: 0;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.ai-content {
    color: #475569;
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
}

/* Styled HTML tables */
.custom-table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 14px;
    text-align: left;
}

.custom-table th {
    background-color: #F1F5F9;
    color: #1E3A8A;
    font-weight: 600;
    padding: 12px;
    border-bottom: 2px solid #E2E8F0;
}

.custom-table td {
    padding: 12px;
    border-bottom: 1px solid #E2E8F0;
    color: #0F172A;
}

.custom-table tr:hover {
    background-color: #F8FAFC;
}

/* Badges */
.risk-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}

.risk-high {
    background: #FEF2F2;
    color: #EF4444;
    border: 1px solid #FCA5A5;
}

.risk-medium {
    background: #FFFBEB;
    color: #F59E0B;
    border: 1px solid #FCD34D;
}

.risk-low {
    background: #ECFDF5;
    color: #10B981;
    border: 1px solid #6EE7B7;
}

/* Styled Card wrapper */
.dashboard-card {
    background: #FFFFFF;
    border-radius: var(--radius-md);
    border: 1px solid #E2E8F0;
    padding: 24px;
    box-shadow: var(--shadow-resting);
    margin-bottom: 24px;
    transition: box-shadow 0.3s var(--ease-out);
}

.dashboard-card:hover {
    box-shadow: var(--shadow-hover);
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #F8FAFC; 
}
::-webkit-scrollbar-thumb {
    background: #CBD5E1; 
    border-radius: 8px;
}
::-webkit-scrollbar-thumb:hover {
    background: #94A3B8; 
}
</style>
"""

def inject_base_css():
    st.markdown(BASE_CSS, unsafe_allow_html=True)

def risk_badge_html(risk_tier):
    css_class = {
        "High Risk": "risk-high",
        "Medium Risk": "risk-medium",
        "Low Risk": "risk-low"
    }.get(risk_tier, "risk-low")
    return f'<span class="risk-badge {css_class}">{risk_tier}</span>'

def apply_enterprise_theme(fig: go.Figure) -> go.Figure:
    """
    Applies NeuralRetail styling standard to Plotly chart layouts.
    Includes custom colors, fonts, hover tooltips, and grid rules.
    """
    fig.update_layout(
        font=dict(family="Inter", color="#64748B", size=12),
        title=dict(font=dict(family="Inter", size=16, color="#1E3A8A"), pad=dict(b=15)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=13,
            font_family="Inter",
            bordercolor="#E2E8F0"
        ),
        margin=dict(t=50, l=20, r=20, b=20),
        xaxis=dict(
            showgrid=False, 
            zeroline=False, 
            linecolor="#E2E8F0", 
            tickfont=dict(color="#64748B"),
            title=dict(font=dict(color="#64748B", size=12))
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor="#F1F5F9", 
            zeroline=False, 
            tickfont=dict(color="#64748B"),
            title=dict(font=dict(color="#64748B", size=12))
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#64748B", size=11)
        ),
        # Theme: Primary (Deep Blue), Secondary (Electric Blue), Accent (Light Blue), Success (Emerald), Warning (Orange), Danger (Red)
        colorway=["#1E3A8A", "#2563EB", "#60A5FA", "#10B981", "#F59E0B", "#EF4444"]
    )
    return fig