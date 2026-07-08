# =====================================================
# FILE: pages_content/customer_intelligence.py
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.styling import apply_enterprise_theme
from utils.data_loader import load_churn_model, DataLoadError
from utils.model_utils import score_customers, add_churn_label

def render(sales: pd.DataFrame, rfm: pd.DataFrame) -> None:
    # 1. Enforce country filtering matching global state
    if st.session_state.get("selected_country"):
        st.markdown(f'<div class="filter-chip">📍 Region Active: {st.session_state.selected_country}</div>', unsafe_allow_html=True)
        filtered_customer_ids = sales[sales["Country"] == st.session_state.selected_country]["Customer ID"].unique()
        rfm_view = rfm[rfm["Customer ID"].isin(filtered_customer_ids)].copy()
    else:
        rfm_view = rfm.copy()
        st.markdown('<div class="filter-chip">🌐 Region Active: Global</div>', unsafe_allow_html=True)

    if rfm_view.empty:
        st.warning("No segment data available for current constraints.")
        return

    # Load Churn Model and calculate Expected CLV dynamically
    try:
        churn_model = load_churn_model()
        rfm_labeled = add_churn_label(rfm_view)
        scored_rfm = score_customers(rfm_labeled, churn_model)
        # Expected CLV = Monetary * (1 - Churn Probability)
        rfm_view["ChurnProbability"] = scored_rfm["ChurnProbability"]
        rfm_view["eCLV"] = rfm_view["Monetary"] * (1.0 - rfm_view["ChurnProbability"])
        rfm_view["RiskTier"] = scored_rfm["RiskTier"]
    except Exception as exc:
        # Fallback if model fails to load
        st.warning(f"Could not load churn predictions for CLV calculations: {exc}")
        rfm_view["ChurnProbability"] = 0.5
        rfm_view["eCLV"] = rfm_view["Monetary"] * 0.5
        rfm_view["RiskTier"] = "Medium Risk"

    # Segment metrics
    segment_counts = rfm_view["Segment"].value_counts().reset_index()
    segment_counts.columns = ["Segment", "Count"]

    def get_seg_metrics(name):
        segment_data = rfm_view[rfm_view["Segment"] == name]
        count = len(segment_data)
        avg_spend = segment_data["Monetary"].mean() if count > 0 else 0.0
        return count, avg_spend

    c1, c2, c3, c4 = st.columns(4)
    
    loyal_count, loyal_spend = get_seg_metrics("Loyal Customers")
    lost_count, lost_spend = get_seg_metrics("Lost Customers")
    champs_count, champs_spend = get_seg_metrics("Champions")
    vip_count, vip_spend = get_seg_metrics("VIP Customers")

    c1.metric("Loyal Customers", f"{loyal_count:,}", f"£{loyal_spend:,.0f} avg spend")
    c2.metric("Lost Customers", f"{lost_count:,}", f"£{lost_spend:,.0f} value-at-risk", delta_color="inverse")
    c3.metric("Champions", f"{champs_count:,}", f"£{champs_spend:,.0f} avg spend")
    c4.metric("VIP Customers", f"{vip_count:,}", f"£{vip_spend:,.0f} avg spend")

    st.markdown("---")

    # Segment Share Plots
    left_plot, right_plot = st.columns([1.2, 1])

    with left_plot:
        fig_bar = px.bar(
            segment_counts.sort_values("Count", ascending=True),
            x="Count", y="Segment", orientation="h",
            title="Segment Audience Share",
            color="Count",
            color_continuous_scale=["#60A5FA", "#2563EB", "#1E3A8A"]
        )
        fig_bar = apply_enterprise_theme(fig_bar)
        st.plotly_chart(fig_bar, use_container_width=True)

    with right_plot:
        fig_pie = px.pie(
            segment_counts, values="Count", names="Segment", hole=0.6,
            title="Audience Proportions"
        )
        fig_pie = apply_enterprise_theme(fig_pie)
        # Apply palette
        fig_pie.update_traces(
            textposition='inside', 
            textinfo='percent',
            marker=dict(colors=["#1E3A8A", "#2563EB", "#60A5FA", "#10B981"])
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # Customer Distribution Plot: Recency vs Frequency
    st.subheader("RFM Portfolio Distribution")
    st.markdown('<div class="map-hint">📊 The chart below maps customers on Recency (X-axis) and Frequency (Y-axis). Bubble size corresponds to Monetary value, and colors map to segments.</div>', unsafe_allow_html=True)
    
    # Cap monetary values for bubble sizing to prevent massive bubbles
    rfm_view["BubbleSize"] = np.clip(rfm_view["Monetary"], 10, 50000)
    
    fig_scatter = px.scatter(
        rfm_view,
        x="Recency",
        y="Frequency",
        size="BubbleSize",
        color="Segment",
        hover_name="Customer ID",
        hover_data={"Recency": True, "Frequency": True, "Monetary": ":,.2f", "eCLV": ":,.2f", "BubbleSize": False},
        color_discrete_map={
            "Loyal Customers": "#2563EB",
            "Lost Customers": "#EF4444",
            "Champions": "#10B981",
            "VIP Customers": "#F59E0B"
        },
        title="Recency vs Frequency Cluster Mapping"
    )
    fig_scatter = apply_enterprise_theme(fig_scatter)
    fig_scatter.update_layout(xaxis_title="Recency (Days Stale)", yaxis_title="Frequency (Unique Orders)")
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    # CLV Analysis Section
    st.subheader("Customer Lifetime Value (CLV) Projections")
    
    clv_col1, clv_col2 = st.columns(2)
    with clv_col1:
        # Histogram of CLV
        fig_clv = px.histogram(
            rfm_view, x="eCLV", nbins=50, 
            title="Expected CLV Distribution (Value Discounted by Churn Risk)",
            color_discrete_sequence=["#1E3A8A"]
        )
        fig_clv = apply_enterprise_theme(fig_clv)
        fig_clv.update_layout(xaxis_title="Expected CLV (£)", yaxis_title="Customer Count")
        st.plotly_chart(fig_clv, use_container_width=True)
        
    with clv_col2:
        # Table of VIPs / Top CLV Customers
        st.markdown("##### 🏆 Premium High-CLV Portfolio")
        top_clv = rfm_view.sort_values("eCLV", ascending=False).head(10)[["Customer ID", "Segment", "Recency", "Frequency", "Monetary", "eCLV"]]
        
        # Display as a premium table
        table_html = """
        <table class="custom-table">
            <thead>
                <tr>
                    <th>Customer ID</th>
                    <th>Segment</th>
                    <th>Recency</th>
                    <th>Frequency</th>
                    <th>Monetary</th>
                    <th>Expected CLV</th>
                </tr>
            </thead>
            <tbody>
        """
        for _, row in top_clv.iterrows():
            table_html += f"""
                <tr>
                    <td><strong>{int(row['Customer ID'])}</strong></td>
                    <td>{row['Segment']}</td>
                    <td>{row['Recency']} days</td>
                    <td>{row['Frequency']} purchases</td>
                    <td>£{row['Monetary']:,.2f}</td>
                    <td><span style="color: #10B981; font-weight: 600;">£{row['eCLV']:,.2f}</span></td>
                </tr>
            """
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("---")

    # Segment Explorer & Directory Exports
    st.subheader("Cohort Directory Explorer")
    cohort = st.selectbox("Select Target Cohort to Drill Down:", ["Champions", "VIP Customers", "Lost Customers", "Loyal Customers"])
    
    cohort_data = rfm_view[rfm_view["Segment"] == cohort].copy()
    cohort_data = cohort_data.sort_values("eCLV", ascending=False)
    
    st.markdown(f"Showing **{len(cohort_data):,}** customers classified as **{cohort}**.")
    
    # Render with nice formatting
    st.dataframe(
        cohort_data[["Customer ID", "Recency", "Frequency", "Monetary", "ChurnProbability", "eCLV", "RiskTier"]].rename(
            columns={
                "Customer ID": "Entity ID",
                "Monetary": "Historical Spend (£)",
                "ChurnProbability": "Churn Risk (%)",
                "eCLV": "Expected CLV (£)",
                "RiskTier": "Risk Status"
            }
        ).style.format({
            "Historical Spend (£)": "£{:,.2f}",
            "Churn Risk (%)": "{:.1%}",
            "Expected CLV (£)": "£{:,.2f}"
        }),
        use_container_width=True,
        height=300
    )

    # AI Action Plan based on selected cohort
    recs = {
        "Champions": "Champions represent your most loyal and high-spending cohort. <strong>Recommendation</strong>: Offer early access to new lines, launch referral rewards, and seek product testimonials.",
        "VIP Customers": "VIP Customers have high spending capacity. <strong>Recommendation</strong>: Assign a dedicated customer success rep, invite to VIP-only feedback sessions, and issue exclusive high-end product offers.",
        "Lost Customers": "Lost Customers have high historical value but haven't purchased in over 90 days. <strong>Recommendation</strong>: Deploy aggressive reactivation discounts (20-30% off), trigger feedback email flows, or survey to find exit drivers.",
        "Loyal Customers": "Loyal Customers purchase frequently but at average price points. <strong>Recommendation</strong>: Cross-sell related items to increase baseline order values, offer points-based loyalty milestones, and upsell premium memberships."
    }
    
    st.markdown(f"""
    <div class="ai-recommendation-box info">
        <div class="ai-title">🤖 AI Cohort Marketing Strategy: {cohort}</div>
        <p class="ai-content">{recs.get(cohort)}</p>
    </div>
    """, unsafe_allow_html=True)