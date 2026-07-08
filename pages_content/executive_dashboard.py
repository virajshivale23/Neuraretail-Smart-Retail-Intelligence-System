# =====================================================
# FILE: pages_content/executive_dashboard.py
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.styling import apply_enterprise_theme, risk_badge_html


def calculate_business_health_score(sales: pd.DataFrame, rfm: pd.DataFrame, inventory: pd.DataFrame) -> float:
    # 1. Retention rate (recency <= 90 days)
    retention_rate = (rfm["Recency"] <= 90).mean() * 100

    # 2. Inventory Health (% of SKUs not labeled High Risk/high stockout risk)
    critical_skus = (inventory["Risk"] == "High Risk").sum()
    inventory_health = (1 - (critical_skus / max(len(inventory), 1))) * 100

    # 3. Revenue Trend (YoY/MoM proxy)
    max_date = pd.to_datetime(sales["InvoiceDate"]).max()
    t30_ago = max_date - pd.Timedelta(days=30)
    t60_ago = max_date - pd.Timedelta(days=60)

    sales_dates = pd.to_datetime(sales["InvoiceDate"])
    rev_last_30 = sales.loc[sales_dates >= t30_ago, "Revenue"].sum()
    rev_prev_30 = sales.loc[(sales_dates >= t60_ago) & (sales_dates < t30_ago), "Revenue"].sum()

    revenue_growth_score = 100.0
    if rev_prev_30 > 0:
        ratio = rev_last_30 / rev_prev_30
        if ratio >= 1.0:
            revenue_growth_score = min(100.0, 90.0 + (ratio - 1.0) * 100.0)
        else:
            revenue_growth_score = max(0.0, 90.0 * ratio)

    # Combine scores: Retention (1/3), Inventory Health (1/3), Revenue Trend (1/3)
    # -- Data Quality component removed along with the Data Quality page.
    health_score = (retention_rate + inventory_health + revenue_growth_score) / 3.0
    return round(health_score, 1)


def _style_map_dark(fig: go.Figure) -> go.Figure:
    """Apply a dark-friendly palette to the choropleth so it doesn't render
    as a bright white/light rectangle on the dark theme."""
    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=10, b=0),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#334155",
            landcolor="#0F172A",
            showland=True,
            showocean=True,
            oceancolor="#0B1220",
            lakecolor="#0B1220",
            subunitcolor="#1E293B",
            projection_type="natural earth",
            bgcolor="rgba(0,0,0,0)",
        ),
        coloraxis_colorbar=dict(
            title=dict(text="Revenue (£)", font=dict(family="Inter", color="#CBD5E1", size=12)),
            thicknessmode="pixels", thickness=12,
            lenmode="pixels", len=250,
            yanchor="bottom", y=0.1,
            tickfont=dict(family="Inter", color="#CBD5E1"),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
    )
    return fig


def render(sales: pd.DataFrame, rfm: pd.DataFrame, forecast: pd.DataFrame, inventory: pd.DataFrame) -> None:
    # Session state for country filtering
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = None

    # Filter sales data based on selection
    if st.session_state.selected_country:
        filtered_sales = sales[sales["Country"] == st.session_state.selected_country]
        st.markdown(f'<div class="filter-chip">📍 Region Active: {st.session_state.selected_country}</div>', unsafe_allow_html=True)
    else:
        filtered_sales = sales
        st.markdown('<div class="filter-chip">🌐 Region Active: Global</div>', unsafe_allow_html=True)

    if filtered_sales.empty:
        st.warning("No transactions recorded for the selected region.")
        st.stop()

    # =================================================
    # 1. MAP -- shown first so country selection is the
    #    entry point into the rest of the dashboard
    # =================================================
    st.subheader("🌍 Geographic Revenue Heatmap")
    st.markdown(
        '<div class="map-hint">🗺️ Click a country to filter every metric, chart, '
        'and table on this page. Click the same country again, or use the sidebar '
        'button, to clear the filter.</div>',
        unsafe_allow_html=True,
    )

    country_revenue = sales.groupby("Country")["Revenue"].sum().reset_index()

    map_fig = px.choropleth(
        country_revenue,
        locations="Country",
        locationmode="country names",
        color="Revenue",
        color_continuous_scale=["#1E3A8A", "#2563EB", "#60A5FA", "#93C5FD", "#DBEAFE"],
        hover_name="Country",
        hover_data={"Revenue": ":,.0f"},
    )
    map_fig = _style_map_dark(map_fig)

    # Highlight selected country on map
    if st.session_state.selected_country:
        map_fig.add_trace(
            go.Choropleth(
                locations=[st.session_state.selected_country],
                z=[1],
                locationmode="country names",
                showscale=False,
                colorscale=[[0, "rgba(245,158,11,0)"], [1, "rgba(245,158,11,0)"]],
                marker_line_color="#F59E0B",
                marker_line_width=3,
                hoverinfo="skip",
            )
        )

    map_event = st.plotly_chart(
        map_fig,
        use_container_width=True,
        on_select="rerun",
        key="country_map",
        config={"displayModeBar": False},
    )

    # Selection processing
    clicked_points = map_event.get("selection", {}).get("points", []) if map_event else []
    if clicked_points:
        clicked_country = clicked_points[0].get("location")
        if clicked_country:
            if st.session_state.selected_country == clicked_country:
                st.session_state.selected_country = None
            else:
                st.session_state.selected_country = clicked_country
            st.rerun()

    st.markdown("---")

    # =================================================
    # 2. KPI ROW -- right under the map, reacts instantly
    #    to whichever country was just clicked
    # =================================================
    revenue = filtered_sales["Revenue"].sum()
    customers = filtered_sales["Customer ID"].nunique()
    products = filtered_sales["StockCode"].nunique()
    countries = filtered_sales["Country"].nunique()
    total_transactions = filtered_sales["Invoice"].nunique()
    avg_order_val = revenue / max(total_transactions, 1)

    max_date = pd.to_datetime(sales["InvoiceDate"]).max()
    t30_ago = max_date - pd.Timedelta(days=30)
    t60_ago = max_date - pd.Timedelta(days=60)
    sales_dates = pd.to_datetime(sales["InvoiceDate"])

    rev_last_30 = filtered_sales.loc[sales_dates >= t30_ago, "Revenue"].sum()
    rev_prev_30 = filtered_sales.loc[(sales_dates >= t60_ago) & (sales_dates < t30_ago), "Revenue"].sum()

    if rev_prev_30 > 0:
        rev_change = ((rev_last_30 - rev_prev_30) / rev_prev_30) * 100
        rev_delta = f"{rev_change:+.1f}% MoM"
    else:
        rev_delta = "0.0% MoM"

    st.subheader("Key Performance Indicators")
    kpi_cols = st.columns(4)

    kpi_cols[0].metric("Gross Revenue", f"£{revenue:,.0f}", delta=rev_delta)
    kpi_cols[1].metric("AOV / Transactions", f"£{avg_order_val:,.1f}", delta=f"{total_transactions:,} Orders")

    if st.session_state.selected_country:
        country_rfm_ids = filtered_sales["Customer ID"].unique()
        active_cust_pct = (rfm[rfm["Customer ID"].isin(country_rfm_ids)]["Recency"] <= 90).mean() * 100 if customers else 0.0
    else:
        active_cust_pct = (rfm["Recency"] <= 90).mean() * 100
    kpi_cols[2].metric("Active Customers", f"{customers:,}", delta=f"{active_cust_pct:.1f}% Active")

    crit_count = (inventory["ReorderPoint"] > 0).sum()
    kpi_cols[3].metric(
        "Supply Chain Risk", f"{crit_count:,} SKUs",
        delta=f"{len(inventory[inventory['ABC_Class'] == 'A']):,} Class A SKUs",
        delta_color="inverse",
    )

    # Secondary row -- extra context that's most useful right after a click
    kpi_cols2 = st.columns(4)
    kpi_cols2[0].metric("Products Sold", f"{products:,}")
    kpi_cols2[1].metric("Markets Represented", f"{countries:,}")
    kpi_cols2[2].metric("Transactions", f"{total_transactions:,}")
    kpi_cols2[3].metric("Units Sold", f"{filtered_sales['Quantity'].sum():,.0f}")

    st.markdown("---")

    # =================================================
    # 3. Business Health Score + AI Summary
    #    (fixed: built as a single st.markdown call each
    #    so the wrapping <div> actually contains its content)
    # =================================================
    health_score = calculate_business_health_score(sales, rfm, inventory)

    left_col, right_col = st.columns([1, 2])

    with left_col:
        health_color = "#10B981" if health_score >= 80 else ("#F59E0B" if health_score >= 60 else "#EF4444")
        status_text = (
            "Platform is operating optimally." if health_score >= 80
            else ("System requires attention." if health_score >= 60 else "Critical issues detected.")
        )
        st.markdown(f"""
            <div style="
                background-color:#161F32;
                border:1px solid #1E293B;
                border-radius:16px;
                padding:24px;
                height:320px;
                text-align:center;
                display:flex;
                flex-direction:column;
                justify-content:center;
                align-items:center;
                box-shadow:0px 4px 14px rgba(0,0,0,0.35);
            ">
                <div style="font-size:14px; font-weight:600; color:#94A3B8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:10px;">Business Health Score</div>
                <div style="width:140px; height:140px; border-radius:50%; border:12px solid {health_color}33; border-top-color:{health_color}; display:flex; align-items:center; justify-content:center; margin:10px 0;">
                    <span style="font-size:36px; font-weight:700; color:#F8FAFC;">{health_score}%</span>
                </div>
                <div style="font-size:13px; font-weight:500; color:{health_color}; margin-top:10px;">
                    {status_text}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with right_col:
        critical_count = (inventory["Risk"] == "High Risk").sum()
        high_risk_churn = (rfm["Recency"] > 90).sum()

        st.markdown(f"""
            <div style="
                background-color:#161F32;
                border:1px solid #1E293B;
                border-radius:16px;
                padding:24px;
                height:320px;
                overflow-y:auto;
                box-shadow:0px 4px 14px rgba(0,0,0,0.35);
            ">
                <div style="font-weight:700; color:#F8FAFC; font-size:15px; margin-bottom:10px;">🤖 Executive AI Summary &amp; Smart Alerts</div>
                <p style="color:#CBD5E1; font-size:14px; line-height:1.5;">
                    NeuralRetail is currently performing at an aggregate <strong style="color:#F8FAFC;">Business Health Score of {health_score}%</strong>.
                    Gross Revenue sits at <strong style="color:#F8FAFC;">£{revenue:,.2f}</strong> across <strong style="color:#F8FAFC;">{countries}</strong> operating markets.
                    A total of <strong style="color:#F8FAFC;">{customers:,}</strong> active customer accounts were analyzed with an Average Order Value (AOV) of <strong style="color:#F8FAFC;">£{avg_order_val:,.2f}</strong>.
                </p>
                <div style="margin-top:15px; display:flex; flex-direction:column; gap:8px;">
                    <div style="display:flex; align-items:flex-start; gap:8px; font-size:13px;">
                        <span style="color:#EF4444; font-weight:bold; white-space:nowrap;">⚠️ Risk Alert:</span>
                        <span style="color:#CBD5E1;">{critical_count} critical products are flagged at high demand, indicating imminent stockout risk.</span>
                    </div>
                    <div style="display:flex; align-items:flex-start; gap:8px; font-size:13px;">
                        <span style="color:#F59E0B; font-weight:bold; white-space:nowrap;">⚠️ Opportunity:</span>
                        <span style="color:#CBD5E1;">{high_risk_churn} churned/inactive customers (inactive &gt; 90 days) represent £{rfm.loc[rfm["Recency"] > 90, "Monetary"].sum():,.0f} in historical revenue. Direct win-back campaigns could recover up to 15% of this volume.</span>
                    </div>
                    <div style="display:flex; align-items:flex-start; gap:8px; font-size:13px;">
                        <span style="color:#10B981; font-weight:bold; white-space:nowrap;">✨ Growth Tactic:</span>
                        <span style="color:#CBD5E1;">Class A inventory products contribute 80% of revenue. Focus vendor optimizations and lead-time reductions on Class A products to improve margins by 2-3%.</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # =================================================
    # 4. Revenue trend + top performers
    # =================================================
    left, right = st.columns(2)

    with left:
        monthly = filtered_sales.groupby(["Year", "Month"])["Revenue"].sum().reset_index()
        monthly["Period"] = monthly["Year"].astype(str) + "-" + monthly["Month"].astype(str).str.zfill(2)
        fig1 = px.area(monthly, x="Period", y="Revenue", title="Revenue Trajectory (Trend Analysis)")
        fig1.update_traces(
            line_color="#2563EB",
            fillcolor="rgba(37,99,235,0.15)",
            line_shape="spline",
            line_width=3,
            mode="lines+markers",
            marker=dict(size=6, color="#93C5FD"),
        )
        st.plotly_chart(apply_enterprise_theme(fig1), use_container_width=True)

    with right:
        if st.session_state.selected_country:
            top_data = filtered_sales.groupby("Description")["Revenue"].sum().sort_values(ascending=False).head(8).reset_index()
            fig2 = px.bar(top_data, x="Revenue", y="Description", orientation="h", title=f"Top Performing SKUs in {st.session_state.selected_country}")
        else:
            top_data = filtered_sales.groupby("Country")["Revenue"].sum().sort_values(ascending=False).head(8).reset_index()
            fig2 = px.bar(top_data, x="Revenue", y="Country", orientation="h", title="Top Performing Operating Regions")

        fig2.update_traces(
            marker_color="#60A5FA",
            marker_line_color="#2563EB",
            marker_line_width=1,
            texttemplate='£%{x:,.0f}',
            textposition='outside',
        )
        fig2 = apply_enterprise_theme(fig2)
        fig2.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # =================================================
    # 5. Temporal demand patterns
    # =================================================
    st.subheader("Operational & Temporal Demand Patterns")
    c_left, c_right = st.columns(2)

    with c_left:
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_sales = filtered_sales.groupby("Weekday")["Revenue"].sum().reindex(weekday_order).reset_index()
        fig4 = px.bar(weekday_sales, x="Weekday", y="Revenue", title="Revenue Distribution by Day of Week")
        fig4.update_traces(marker_color="#10B981", marker_line_color="#059669", marker_line_width=1)
        st.plotly_chart(apply_enterprise_theme(fig4), use_container_width=True)

    with c_right:
        hourly_sales = filtered_sales.groupby("Hour")["Revenue"].sum().reset_index()
        fig5 = px.line(hourly_sales, x="Hour", y="Revenue", title="Intraday Revenue Curve")
        fig5.update_traces(line_color="#F59E0B", line_shape="spline", line_width=3, mode="lines+markers", marker=dict(size=6))
        fig5 = apply_enterprise_theme(fig5)
        fig5.update_layout(xaxis=dict(tickmode="linear", tick0=0, dtick=2))
        st.plotly_chart(fig5, use_container_width=True)