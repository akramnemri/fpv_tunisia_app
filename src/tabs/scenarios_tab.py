"""Onglet Scénarios économiques — comparaison d'indexation."""
import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
from src.config import load_scenarios, load_constants
from src.charts import scenario_comparison_chart

def calculate_scenarios_for_capacity(power_mwc: float, const_dict: dict, dam_productible: float = None) -> list:
    """Calculate VAN, TRI, ROI, payback for each indexation scenario for given capacity."""
    J1 = const_dict['J1']
    J2_values = [0.02, 0.05, 0.08]  # Scénarios: Conservateur, Base, Optimiste
    J3 = const_dict['J3']
    J4 = const_dict['J4']
    J5 = const_dict['J5']
    J6 = 25
    
    CAPEX_PER_MWC = 2_300_000.0
    loan_share = 70.0
    loan_rate = 5.0
    
    results = []
    # Use default Sidi Saad productible or provided value
    dam_productible = dam_productible or 1780  # Sidi Saad productible (kWh/kWc)
    
    for i, J2 in enumerate(J2_values, start=1):
        capex = CAPEX_PER_MWC * power_mwc
        production_y1 = power_mwc * 1000 * dam_productible
        opex = capex * J4
        
        loan_amount = capex * (loan_share / 100)
        if loan_rate > 0 and loan_share > 0:
            annuity = npf.pmt(loan_rate / 100, 10, -loan_amount)
        else:
            annuity = 0.0
        
        years = list(range(J6 + 1))
        cash_flows = [-capex]
        
        for year in range(1, J6 + 1):
            prod = production_y1 * ((1 - J3) ** (year - 1))
            price = J1 * ((1 + J2) ** (year - 1))
            revenue = prod * price
            opex_y = opex * ((1 + 0.02) ** (year - 1))
            ann = annuity if year <= 10 else 0
            cf = revenue - opex_y - ann
            cash_flows.append(cf)
        
        van = npf.npv(J5, cash_flows[1:]) + cash_flows[0]
        try:
            tri = npf.irr(cash_flows) * 100
        except Exception:
            tri = 0.0
        
        total_cf = sum(cash_flows)
        roi = (total_cf / capex) * 100 if capex > 0 else 0
        
        cumsum = np.cumsum(cash_flows)
        payback = None
        for i_val, val in enumerate(cumsum):
            if val > 0:
                payback = i_val
                break
        
        scenario_names = ["Conservateur (2%)", "Base (5%)", "Optimiste (8%)"]
        
        results.append({
            'id': i,
            'scenario_name': scenario_names[i-1],
            'indexation_rate': J2,
            'van_tnd': van,
            'tri_percent': tri,
            'roi_percent': roi,
            'payback_years': payback if payback else 0,
        })
    
    return results

def render(conn):
    st.subheader("💵 Scénarios d'indexation des tariffs")
    st.markdown("Comparaison des hypothèses d'évolution du prix de vente (2%, 5%, 8% d'indexation annuelle)")
    st.info("💡 Prix de vente initial : **0,307 TND/kWh** (tarif STEG 2025)")
    
    const_dict = load_constants(conn)
    
    power_mwc = 20.0
    if 'inputs' in st.session_state and st.session_state['inputs'].desired_power:
        power_mwc = st.session_state['inputs'].desired_power
    elif 'inputs' in st.session_state and st.session_state['inputs'].budget:
        max_power = np.floor(st.session_state['inputs'].budget / 2_300_000 * 10) / 10
        power_mwc = max(0, max_power) if max_power > 0 else 20.0
    
    scenarios = calculate_scenarios_for_capacity(power_mwc, const_dict)
    scenarios_df = pd.DataFrame(scenarios)

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