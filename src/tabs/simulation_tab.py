"""Onglet Simulation — résultats principaux + cash-flows."""
import streamlit as st
import pandas as pd
import numpy as np
from src.models import ProjectResults
from src.charts import cashflow_chart

def render(results: ProjectResults):
    st.subheader("📊 Résultats de la simulation")

    # --- KPIs ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Puissance maximale", f"{results.max_power:.1f} MWc")
        st.metric("Puissance retenue", f"{results.retained_power:.1f} MWc")
        st.metric("Production année 1", f"{results.production_gwh:.2f} GWh")
    with c2:
        st.metric("CAPEX", f"{results.capex:,.0f} TND")
        st.metric("OPEX/an", f"{results.opex:,.0f} TND")
        st.metric("Économie d'eau", f"{results.water_saved_m3:,.0f} m³/an")
    with c3:
        st.metric("Taux couverture", f"{results.coverage_rate:.2f}%",
                  delta=f"max {results.max_coverage}%", delta_color="off")
        if not results.alert_ok:
            st.error(results.alert)
        else:
            st.success(results.alert)

    st.divider()

    # --- CO2 ---
    c1, c2, c3 = st.columns(3)
    c1.metric("CO₂ évité", f"{results.co2_avoided:.1f} t/an")
    c2.metric("CO₂ émis (FPV)", f"{results.co2_emitted:.1f} t/an")
    c3.metric("Bilan net CO₂", f"{results.co2_net:.1f} t/an")

    st.divider()

    # --- Cash-flows ---
    st.subheader("📉 Cash-flows sur 25 ans")
    fig = cashflow_chart(results.years, results.cash_flows)
    st.plotly_chart(fig, width='stretch')

    # --- Indicateurs financiers ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("VAN (10%)", f"{results.van:,.0f} TND")
    c2.metric("TRI", f"{results.tri*100:.1f}%")
    c3.metric("ROI (25 ans)", f"{results.roi:.0f}%")
    payback_str = f"{results.payback} ans" if results.payback else "Non rentable"
    c4.metric("Temps de retour", payback_str)

    # --- Tableau détaillé ---
    with st.expander("📋 Tableau détaillé des cash-flows"):
        df = pd.DataFrame({
            'Année': results.years,
            'Cash-flow (TND)': results.cash_flows,
            'Cumulé (TND)': np.cumsum(results.cash_flows)
        })
        st.dataframe(df.style.format({
            'Cash-flow (TND)': '{:,.0f}',
            'Cumulé (TND)': '{:,.0f}'
        }), width='stretch')
