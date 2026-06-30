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
        if result:  # Has data (economie_m3_per_mwc key exists)
            dam_totals[dam_name] = result
    
    return dam_totals

def render(conn):
    st.subheader("🏆 Classement prioritaire des barrages pour l'installation FPV")
    
    # Weight configuration
    st.markdown("---")
    st.subheader("⚖️ Pondérations personnalisées")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        w_prod = st.slider("Production (GWh/an)", 0, 100, 30, key="w_prod")
        w_water = st.slider("Économie d'eau (m³/an)", 0, 100, 25, key="w_water")
    with col2:
        w_aquatic = st.slider("Gain aquatique (%)", 0, 100, 20, key="w_aquatic")
        w_pr = st.slider("Performance Ratio", 0, 100, 15, key="w_pr")
    with col3:
        w_constraint = st.slider("Contrainte environnementale", 0, 100, 10, key="w_constraint")
    
    # Validate and normalize weights
    total_weight = w_prod + w_water + w_aquatic + w_pr + w_constraint
    if total_weight != 100:
        st.warning(f"⚠️ Total pondérations: **{total_weight}%** (devrait être 100%)")
        weights = None
    else:
        weights = {
            'production': w_prod / 100.0,
            'water': w_water / 100.0,
            'aquatic': w_aquatic / 100.0,
            'pr': w_pr / 100.0,
            'constraint': w_constraint / 100.0,
        }
    
    # Display criterion descriptions
    st.markdown("""
    **Critères :**
    - Production annuelle : kWh/kWc
    - Économie d'eau : m³ économisés par MWc installé
    - Gain aquatique (flottant) : pourcentage d'énergie supplémentaire
    - Performance Ratio (PR) : efficacité énergétique
    - Contrainte environnementale : pénalité si site Ramsar (Sidi Saad)
    """)
    
    # Get user-selected power or default to 20 MWc
    power_mwc = st.session_state.get('power_mwc', 20.0)
    
    # Try to load from Excel, fallback to DB
    dam_totals = load_all_dam_data_from_excel()
    
    with st.spinner("Calcul du classement en cours..."):
        scores = compute_dam_scores(conn, power_mwc=power_mwc, dam_totals=dam_totals if dam_totals else None, weights=weights)
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