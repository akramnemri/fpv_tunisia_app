"""Onglet Évaporation mensuelle — Penman-Monteith."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.charts import evaporation_bar_chart, evaporation_volume_chart

def render(conn, dam_id: int, dam_name: str, retained_power: float, covered_m2: float = 92489):
    st.subheader("💧 Analyse mensuelle de l'évaporation")

    from src.config import load_evap
    evap_df = load_evap(conn, dam_id)

    if evap_df.empty:
        st.warning("Données d'évaporation non disponibles pour ce barrage.")
        return

    # --- Scaling dynamique selon puissance retenue ---
    # Le fichier Excel suppose 20 MWc = 92,489 m². On scale proportionnellement.
    scale_factor = (retained_power / 20.0) if retained_power > 0 else 1.0
    actual_covered = covered_m2 * scale_factor

    evap_df = evap_df.copy()
    evap_df['volume_without_fpv_scaled'] = evap_df['volume_without_fpv'] * scale_factor
    evap_df['volume_with_fpv_scaled'] = evap_df['volume_with_fpv'] * scale_factor
    evap_df['water_saved_month'] = evap_df['volume_without_fpv_scaled'] - evap_df['volume_with_fpv_scaled']

    # --- Charts ---
    c1, c2 = st.columns(2)
    with c1:
        fig1 = evaporation_bar_chart(evap_df, dam_name)
        st.plotly_chart(fig1, width='stretch')
    with c2:
        fig2 = evaporation_volume_chart(evap_df, dam_name)
        # Override with scaled values
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=evap_df['month_name'], y=evap_df['volume_without_fpv_scaled'],
                               name='Sans FPV', marker_color='lightcoral'))
        fig2.add_trace(go.Bar(x=evap_df['month_name'], y=evap_df['volume_with_fpv_scaled'],
                               name='Avec FPV', marker_color='steelblue'))
        fig2.update_layout(barmode='group', title=f"Volumes évaporés — {dam_name} ({retained_power:.1f} MWc)",
                           yaxis_title="m³", height=400)
        st.plotly_chart(fig2, width='stretch')

    total_saved = evap_df['water_saved_month'].sum()
    st.success(f"💧 **Économie d'eau totale annuelle : {total_saved:,.0f} m³** (surface couverte : {actual_covered:,.0f} m²)")

    # --- Tableau détaillé ---
    with st.expander("📋 Données mensuelles détaillées"):
        display = evap_df[['month_name', 'temp_c', 'hr_percent', 'wind_ms', 'rs_kwh_m2_day',
                            'e_mm_day', 'days', 'volume_without_fpv_scaled', 'volume_with_fpv_scaled', 'water_saved_month']].copy()
        display.columns = ['Mois', 'T (°C)', 'HR (%)', 'Vent (m/s)', 'RS (kWh/m²/j)',
                           'E (mm/j)', 'Jours', 'Sans FPV (m³)', 'Avec FPV (m³)', 'Économie (m³)']
        st.dataframe(display.style.format({
            'T (°C)': '{:.1f}', 'HR (%)': '{:.1f}', 'Vent (m/s)': '{:.2f}',
            'RS (kWh/m²/j)': '{:.2f}', 'E (mm/j)': '{:.3f}',
            'Sans FPV (m³)': '{:,.0f}', 'Avec FPV (m³)': '{:,.0f}', 'Économie (m³)': '{:,.0f}'
        }), width='stretch')
