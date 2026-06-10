"""Onglet Comparaison multi-barrages."""
import streamlit as st
import pandas as pd
from src.models import DamProfile, EconomicConstants, ProjectInputs
from src.engine import compute_project
from src.charts import production_comparison_chart, water_comparison_chart

def compute_score(res, dam, inputs):
    """Calcule un score sur 100 basé sur production, eau et VAN."""
    prod_score = min(res.production_gwh / 40.0, 1.0) * 40
    water_score = min(res.water_saved_m3 / 150000.0, 1.0) * 30
    van_score = min(res.van / 100e6, 1.0) * 30
    total = prod_score + water_score + van_score
    
    if total >= 80:
        color = "blue"
    elif total >= 60:
        color = "green"
    elif total >= 40:
        color = "yellow"
    elif total >= 20:
        color = "orange"
    else:
        color = "red"
    
    return total, color


def render(dams_list: list, const: EconomicConstants, inputs: ProjectInputs):
    st.subheader("🔍 Comparaison des 5 barrages avec votre budget")

    results = []
    for dam_dict in dams_list:
        dam = DamProfile(**dam_dict)
        res = compute_project(dam, const, inputs)
        results.append({
            'Barrage': dam.name,
            'Puissance max (MWc)': res.max_power,
            'Puissance retenue (MWc)': res.retained_power,
            'Production (GWh/an)': res.production_gwh,
            'Économie eau (m³/an)': res.water_saved_m3,
            'Taux couverture (%)': res.coverage_rate,
            'Seuil max (%)': res.max_coverage,
            'Alerte': '⚠️' if not res.alert_ok else '✅',
            'CAPEX (MTND)': res.capex / 1e6,
            'VAN (MTND)': res.van / 1e6,
            'TRI (%)': res.tri * 100,
            'Temps retour (ans)': res.payback if res.payback else '-'
        })

    comp_df = pd.DataFrame(results)

    st.dataframe(comp_df.style.format({
        'Puissance max (MWc)': '{:.1f}',
        'Puissance retenue (MWc)': '{:.1f}',
        'Production (GWh/an)': '{:.2f}',
        'Économie eau (m³/an)': '{:,.0f}',
        'Taux couverture (%)': '{:.2f}',
        'Seuil max (%)': '{:.0f}',
        'CAPEX (MTND)': '{:.1f}',
        'VAN (MTND)': '{:.1f}',
        'TRI (%)': '{:.1f}',
    }), width='stretch')

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        fig1 = production_comparison_chart(comp_df)
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, width='stretch')
    with c2:
        fig2 = water_comparison_chart(comp_df)
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, width='stretch')

    # Ranking
    st.divider()
    st.subheader("🏆 Classement selon votre objectif")

    if inputs.objective == "Production":
        ranked = comp_df.sort_values('Production (GWh/an)', ascending=False)
        st.markdown("**Classement par production maximale :**")
    elif inputs.objective == "Économie d'eau":
        ranked = comp_df.sort_values('Économie eau (m³/an)', ascending=False)
        st.markdown("**Classement par économie d'eau maximale :**")
    else:
        ranked = comp_df.copy()
        ranked['Score'] = (ranked['Production (GWh/an)'] / ranked['Production (GWh/an)'].max() +
                          ranked['Économie eau (m³/an)'] / ranked['Économie eau (m³/an)'].max()) / 2
        ranked = ranked.sort_values('Score', ascending=False)
        st.markdown("**Classement mixte (production + eau normalisés) :**")

    for i, (_, row) in enumerate(ranked.iterrows(), 1):
        st.markdown(f"**{i}. {row['Barrage']}** — {row['Production (GWh/an)']:.2f} GWh | {row['Économie eau (m³/an)']:,.0f} m³ | {row['Alerte']}")
