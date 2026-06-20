"""Onglet Classement prioritaire des barrages (score + couleurs)."""
import streamlit as st
import pandas as pd
from src.config import compute_dam_scores, scores_to_dataframe, load_dams, get_aquatic_gain, load_dam_evaporation_from_excel
from src.charts import ranking_chart

def load_all_dam_data_from_excel() -> dict:
    """Load all dam data from current study Excel file."""
    dam_names = ["Sidi Saad", "Sidi Salem", "Sidi El Barrak", "Bouhertma", "Sejnane"]
    dam_totals = {}
    
    for dam_name in dam_names:
        result = load_dam_evaporation_from_excel(dam_name)
        if 'error' not in result:
            dam_totals[dam_name] = result
    
    return dam_totals

def render(conn):
    st.subheader("🏆 Classement prioritaire des barrages pour l'installation FPV")
    st.markdown("""
    **Critères et pondérations :**
    - Production annuelle : 30%
    - Économie d'eau : 25%
    - Gain aquatique (flottant) : 20%
    - Performance Ratio (PR) : 15%
    - Contrainte environnementale : 10% (pénalité si site Ramsar)
    """)

    # Get user-selected power or default to 20 MWc
    power_mwc = st.session_state.get('power_mwc', 20.0)
    
    # Try to load from Excel, fallback to DB
    dam_totals = load_all_dam_data_from_excel()
    
    with st.spinner("Calcul du classement en cours..."):
        scores = compute_dam_scores(conn, power_mwc=power_mwc, dam_totals=dam_totals if dam_totals else None)
        df_scores = scores_to_dataframe(scores)

    fig = ranking_chart(df_scores)
    st.plotly_chart(fig, width='stretch')

    st.dataframe(df_scores.style.format({
        'Score': '{:.1f}',
        'Production (GWh/an)': '{:.2f}',
        'Eau (m³/an)': '{:,.0f}',
        'Gain aquatique (%)': '{:.2f}'
    }), width='stretch')

    with st.expander("📋 Détail des sous-scores"):
        detail = [{
            "Barrage": s.dam_name,
            "Production (sur 100)": s.production_score,
            "Eau (sur 100)": s.water_score,
            "Gain aquatique (sur 100)": s.aquatic_score,
            "PR (sur 100)": s.pr_score,
            "Contrainte (sur 100)": s.constraint_score,
        } for s in scores]
        st.dataframe(pd.DataFrame(detail).style.format({
            "Production (sur 100)": "{:.1f}",
            "Eau (sur 100)": "{:.1f}",
            "Gain aquatique (sur 100)": "{:.1f}",
            "PR (sur 100)": "{:.1f}",
            "Contrainte (sur 100)": "{:.1f}",
        }))