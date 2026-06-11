"""Onglet Performance thermique — terre vs flottant."""
import streamlit as st
from src.config import load_thermal
from src.charts import thermal_comparison_chart

def render(conn, dam_id: int, dam_name: str):
    st.subheader("🌡️ Gain de production par refroidissement aquatique")
    st.markdown("Comparaison modules terrestres vs. flottants (coefficients Uc=35, Uv=8)")

    therm_df = load_thermal(conn, dam_id)

    if therm_df.empty:
        st.info(f"Données thermiques détaillées disponibles uniquement pour Sidi Saad (étude PVsyst de référence).\n"
                f"Pour {dam_name}, les données seront ajoutées après simulation PVsyst.")
        return

    fig = thermal_comparison_chart(therm_df, dam_name)
    st.plotly_chart(fig, width='stretch')

    total_gain = therm_df['gain_kwh'].sum()
    avg_gain_pct = therm_df['gain_percent'].mean()
    st.success(f"📈 **Gain annuel total : {total_gain:,.0f} kWh** (écart moyen +{avg_gain_pct:.2f}%)")
    
    # Équivalents écologiques du gain
    co2_equiv = total_gain * 0.000445  # Facteur CO2 évité
    st.info(f"🌱 Équivalent CO₂ évité grâce au gain : **{co2_equiv:.1f} tonnes/an**")

    with st.expander("📋 Données thermiques détaillées"):
        import pandas as pd
        disp = therm_df[['month_name', 'temp_c', 'tcell_terre', 'tcell_float',
                         'egrid_terre_kwh', 'egrid_float_kwh', 'gain_kwh', 'gain_percent']].copy()
        disp.columns = ['Mois', 'T ambiante (°C)', 'T cellule terre (°C)', 'T cellule float (°C)',
                        'Production terre (kWh)', 'Production float (kWh)', 'Gain (kWh)', 'Gain (%)']
        st.dataframe(disp.style.format({
            'T ambiante (°C)': '{:.1f}', 'T cellule terre (°C)': '{:.1f}', 'T cellule float (°C)': '{:.1f}',
            'Production terre (kWh)': '{:,.0f}', 'Production float (kWh)': '{:,.0f}',
            'Gain (kWh)': '{:,.0f}', 'Gain (%)': '{:.2f}'
        }), width='stretch')