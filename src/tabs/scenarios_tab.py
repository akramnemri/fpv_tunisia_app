"""Onglet Scénarios économiques — comparaison d'indexation."""
import streamlit as st
from src.config import load_scenarios
from src.charts import scenario_comparison_chart

def render(conn):
    st.subheader("💵 Scénarios d'indexation des tarifs")
    st.markdown("Comparaison des hypothèses d'évolution du prix de vente (2%, 5%, 8% d'indexation annuelle)")
    st.info("💡 Prix de vente initial : **0,307 TND/kWh** (tarif STEG 2025)")

    scenarios_df = load_scenarios(conn)

    c1, c2, c3 = st.columns(3)
    for i, (_, row) in enumerate(scenarios_df.iterrows()):
        with [c1, c2, c3][i]:
            st.metric(
                row['scenario_name'],
                f"VAN: {row['van_tnd']:,.0f} TND",
                f"TRI: {row['tri_percent']:.1f}% | Retour: {row['payback_years']:.0f} ans"
            )

    fig = scenario_comparison_chart(scenarios_df)
    st.plotly_chart(fig, width='stretch')

    with st.expander("📋 Détails des scénarios"):
        st.dataframe(scenarios_df[['scenario_name', 'indexation_rate', 'van_tnd', 'tri_percent', 'roi_percent', 'payback_years']].style.format({
            'indexation_rate': '{:.0%}', 'van_tnd': '{:,.0f}', 'tri_percent': '{:.1f}',
            'roi_percent': '{:.0f}', 'payback_years': '{:.0f}'
        }), width='stretch')