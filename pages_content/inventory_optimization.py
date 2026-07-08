# =====================================================
# FILE: pages_content/inventory_optimization.py
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.styling import apply_enterprise_theme

def render(sales: pd.DataFrame, inventory: pd.DataFrame) -> None:
    # 1. Page Header & Info
    st.markdown('<div class="filter-chip">📦 Supply Chain: Multi-Echelon EOQ & ROP Engine</div>', unsafe_allow_html=True)
    st.caption("Inventory health diagnostics, ABC stratification, and interactive Economic Order Quantity (EOQ) controllers.")

    # 2. Interactive Sliders in sidebar or main page for dynamic calculation
    st.subheader("⚙️ Simulation parameters")
    left_param, mid_param, right_param = st.columns(3)
    
    with left_param:
        setup_cost = st.slider("Setup / Ordering Cost (£ per order)", min_value=5.0, max_value=250.0, value=50.0, step=5.0, key="setup_cost_slider")
    with mid_param:
        holding_rate = st.slider("Holding Cost Rate (% of unit value per year)", min_value=5.0, max_value=50.0, value=15.0, step=1.0, key="holding_rate_slider") / 100.0
    with right_param:
        lead_time = st.slider("Vendor Lead Time (Days)", min_value=1, max_value=30, value=7, key="lead_time_slider")

    # 3. Dynamic Re-calculation of EOQ and ROP
    # Unit price proxy = Revenue / AnnualDemand. We cap unit price to avoid division by zero or extreme outliers.
    inventory_calc = inventory.copy()
    inventory_calc["UnitPrice"] = (inventory_calc["Revenue"] / inventory_calc["AnnualDemand"].clip(lower=1)).clip(lower=0.01)
    
    # H (Holding Cost per unit per year) = holding_rate * UnitPrice
    inventory_calc["H"] = holding_rate * inventory_calc["UnitPrice"]
    
    # EOQ = sqrt( (2 * AnnualDemand * SetupCost) / H )
    inventory_calc["EOQ_Calc"] = np.sqrt((2 * inventory_calc["AnnualDemand"] * setup_cost) / inventory_calc["H"].clip(lower=0.01))
    
    # ROP = (DailyDemand * LeadTime) + SafetyStock
    inventory_calc["ROP_Calc"] = (inventory_calc["DailyDemand"] * lead_time) + inventory_calc["SafetyStock"]

    # Inventory Health Score: % of SKUs not requiring urgent replenishment
    # Suppose a stockout risk occurs if safety stock is compromised
    total_skus = len(inventory_calc)
    
    # We simulate current stock level for visualization (mock stock between SafetyStock and EOQ)
    # We set seed for reproducibility
    np.random.seed(42)
    inventory_calc["CurrentStock"] = inventory_calc["SafetyStock"] + np.random.uniform(0.1, 0.9, size=total_skus) * inventory_calc["EOQ_Calc"]
    
    critical_skus = (inventory_calc["CurrentStock"] <= inventory_calc["ROP_Calc"]).sum()
    inventory_health_score = (1 - (critical_skus / max(total_skus, 1))) * 100

    # Metric Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Managed SKUs", f"{total_skus:,}")
    c2.metric("Mean Economic Order Qty", f"{inventory_calc['EOQ_Calc'].mean():,.1f} units")
    c3.metric("Critical Refill Triggers", f"{critical_skus:,} SKUs", f"Health: {inventory_health_score:.1f}%", delta_color="inverse" if inventory_health_score < 80 else "normal")
    c4.metric("Inventory Carrying Rate", f"{holding_rate * 100:.1f}% / year")

    st.markdown("---")

    # ABC Classification Analysis
    st.subheader("ABC Inventory Stratification")
    
    # Sort inventory by Revenue descending to build Lorenz Curve
    abc_data = inventory_calc.sort_values("Revenue", ascending=False).reset_index(drop=True)
    abc_data["CumRevenue"] = abc_data["Revenue"].cumsum()
    total_rev = abc_data["Revenue"].sum()
    abc_data["CumRevenuePct"] = (abc_data["CumRevenue"] / total_rev) * 100
    abc_data["CumProductsPct"] = ((abc_data.index + 1) / len(abc_data)) * 100

    left_abc, right_abc = st.columns([1.2, 1])
    
    with left_abc:
        # Lorenz Curve Plot
        fig_lorenz = go.Figure()
        
        # Area under curve
        fig_lorenz.add_trace(go.Scatter(
            x=abc_data["CumProductsPct"],
            y=abc_data["CumRevenuePct"],
            mode="lines",
            fill="toself",
            fillcolor="rgba(37,99,235,0.06)",
            line=dict(color="#2563EB", width=3),
            name="Lorenz Curve"
        ))
        
        # Threshold annotations lines
        fig_lorenz.add_shape(type="line", x0=20, y0=0, x1=20, y1=80, line=dict(color="#EF4444", dash="dash", width=1.5))
        fig_lorenz.add_shape(type="line", x0=0, y0=80, x1=20, y1=80, line=dict(color="#EF4444", dash="dash", width=1.5))
        
        fig_lorenz = apply_enterprise_theme(fig_lorenz)
        fig_lorenz.update_layout(
            title="Lorenz Revenue Concentration Curve",
            xaxis_title="% of Products (SKUs)",
            yaxis_title="% of Cumulative Revenue",
            xaxis=dict(range=[0, 100]),
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig_lorenz, use_container_width=True)
        
    with right_abc:
        # ABC Share Pie Chart
        abc_counts = abc_data["ABC_Class"].value_counts().reset_index()
        abc_counts.columns = ["Class", "Count"]
        
        fig_abc_pie = px.pie(
            abc_counts, values="Count", names="Class", hole=0.6,
            title="ABC Class SKU Proportions"
        )
        fig_abc_pie = apply_enterprise_theme(fig_abc_pie)
        fig_abc_pie.update_traces(
            textposition='inside', textinfo='percent+label',
            marker=dict(colors=["#10B981", "#F59E0B", "#EF4444"])
        )
        st.plotly_chart(fig_abc_pie, use_container_width=True)

    st.markdown("---")

    # Dynamic Supply Chain Action Plan (Critical Products)
    st.subheader("🚨 Supply Chain Action Plan (Critical SKUs)")
    st.markdown(f'<div class="map-hint">⚠️ The following products have simulated stock levels below their calculated Reorder Point (ROP = {lead_time} days demand + safety stock) and require immediate replenishment.</div>', unsafe_allow_html=True)

    critical_list = inventory_calc[inventory_calc["CurrentStock"] <= inventory_calc["ROP_Calc"]].copy()
    critical_list = critical_list.sort_values("Revenue", ascending=False)

    if critical_list.empty:
        st.success("Nominal levels confirmed. No stockout risks detected in the active portfolio.")
    else:
        st.dataframe(
            critical_list[["StockCode", "Description", "ABC_Class", "AnnualDemand", "CurrentStock", "ROP_Calc", "EOQ_Calc", "Revenue"]].rename(
                columns={
                    "ABC_Class": "Class",
                    "AnnualDemand": "Annual Sales (Units)",
                    "CurrentStock": "Current Stock (Units)",
                    "ROP_Calc": "Reorder Trigger (Units)",
                    "EOQ_Calc": "Target EOQ (Units)",
                    "Revenue": "Historical Value Contribution (£)"
                }
            ).style.format({
                "Current Stock (Units)": "{:.1f}",
                "Reorder Trigger (Units)": "{:.1f}",
                "Target EOQ (Units)": "{:.1f}",
                "Historical Value Contribution (£)": "£{:,.2f}"
            }),
            use_container_width=True,
            height=300
        )

    st.markdown("---")

    # Complete Managed SKU Directory Search
    st.subheader("🔍 Complete Inventory Directory Explorer")
    search = st.text_input("Filter Inventory by SKU Code or Description:")
    
    view_data = inventory_calc.copy()
    if search:
        view_data = view_data[
            (view_data["Description"].astype(str).str.contains(search, case=False, na=False)) |
            (view_data["StockCode"].astype(str).str.contains(search, case=False, na=False))
        ]
        
    st.dataframe(
        view_data[["StockCode", "Description", "ABC_Class", "AnnualDemand", "Revenue", "DailyDemand", "SafetyStock", "ROP_Calc", "EOQ_Calc", "CurrentStock"]].rename(
            columns={
                "ABC_Class": "Class",
                "ROP_Calc": "Reorder Point (ROP)",
                "EOQ_Calc": "Economic Order Qty (EOQ)",
                "CurrentStock": "Current Stock"
            }
        ).style.format({
            "Revenue": "£{:,.2f}",
            "DailyDemand": "{:.2f}",
            "SafetyStock": "{:.1f}",
            "Reorder Point (ROP)": "{:.1f}",
            "Economic Order Qty (EOQ)": "{:.1f}",
            "Current Stock": "{:.1f}"
        }),
        use_container_width=True,
        height=350
    )

    # Explanation block of formulas
    st.markdown(r"""
    <div class="ai-recommendation-box info">
        <div class="ai-title">🤖 Supply Chain Formulas & Rationale</div>
        <p class="ai-content">
            - <strong>Economic Order Quantity (EOQ)</strong>: Evaluates the optimal order size to minimize cumulative holding costs and ordering costs. 
            Formula: \(EOQ = \sqrt{\frac{2DS}{H}}\), where \(D\) is annual demand, \(S\) is ordering setup cost, and \(H\) is holding carrying cost.<br><br>
            - <strong>Reorder Point (ROP)</strong>: Triggers a restocking request when inventory drops below the threshold. 
            Formula: \(ROP = (Daily \, Demand \times Lead \, Time) + Safety \, Stock\).
        </p>
    </div>
    """, unsafe_allow_html=True)