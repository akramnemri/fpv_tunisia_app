"""FPV Tunisia — Application principale Streamlit.
Architecture modulaire : config → models → engine → charts → tabs.
"""
import streamlit as st
import pandas as pd

from src.config import get_connection, load_constants, load_dams
from src.models import DamProfile, EconomicConstants, ProjectInputs
from src.engine import compute_project

from src.tabs import simulation_tab, evaporation_tab, thermal_tab, scenarios_tab, comparison_tab, ranking_tab

st.set_page_config(
    page_title="FPV Tunisia — Outil d'aide à la décision",
    layout="wide",
    page_icon="☀️"
)

# ───────────────────────────────────────────
# INIT
# ───────────────────────────────────────────
conn = get_connection()
const_dict = load_constants(conn)
const = EconomicConstants(
    J1=const_dict['J1'],
    J2=const_dict['J2'],
    J3=const_dict['J3'],
    J4=const_dict['J4'],
    J5=const_dict['J5'],
    J6=int(const_dict['J6']),
    J7=const_dict['J7'],
    J8=const_dict['J8'],
)

dams_df = load_dams(conn)
dams_list = dams_df.to_dict('records')

# ───────────────────────────────────────────
# SIDEBAR — User Inputs
# ───────────────────────────────────────────
st.sidebar.header("🎛️ Paramètres du projet")

dam_names = ["Tous (comparaison)"] + dams_df['name'].tolist()
selected_dam = st.sidebar.selectbox("Sélectionner un barrage", dam_names)

# --- Mode inversible : Budget ⇄ Puissance ---
st.sidebar.divider()
st.sidebar.subheader("⚙️ Mode de calcul")

mode = st.sidebar.radio(
    "Choisir le mode",
    ["💰 Budget → Puissance", "⚡ Puissance → Budget"],
    index=0,
    help="En mode 'Budget', vous entrez un budget et l'application calcule la puissance maximale. En mode 'Puissance', vous entrez une puissance souhaitée et l'application calcule le budget nécessaire."
)

# Valeurs par défaut : 20 MWc
DEFAULT_POWER = 20.0
DEFAULT_BUDGET = int(DEFAULT_POWER * 2_300_000)  # 46,000,000 TND

if mode == "💰 Budget → Puissance":
    inputs_mode = "budget"
    budget = st.sidebar.number_input(
        "Budget (TND)", min_value=0, value=DEFAULT_BUDGET, step=1_000_000, format="%d"
    )
    desired_power_raw = st.sidebar.number_input(
        "Puissance souhaitée (MWc) — optionnel", min_value=0.0, value=0.0, step=1.0, format="%.1f"
    )
    desired_power = None if desired_power_raw == 0 else desired_power_raw
else:
    inputs_mode = "power"
    desired_power_raw = st.sidebar.number_input(
        "Puissance souhaitée (MWc)", min_value=0.1, value=DEFAULT_POWER, step=1.0, format="%.1f"
    )
    desired_power = desired_power_raw
    # Calcul du budget nécessaire pour info
    required_budget = int(desired_power * 2_300_000)
    st.sidebar.info(f"💡 Budget nécessaire : **{required_budget:,.0f} TND**")
    budget = required_budget  # Utilisé pour compatibilité

objective = st.sidebar.selectbox(
    "Objectif prioritaire", ["Production", "Économie d'eau", "Mixte"]
)

st.sidebar.divider()
st.sidebar.subheader("💰 Financement")

loan_rate = st.sidebar.number_input(
    "Taux d'emprunt (%)", min_value=0.0, max_value=20.0, value=0.0, step=0.5
)
loan_share = st.sidebar.number_input(
    "Part d'emprunt (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0
)

inputs = ProjectInputs(
    budget=budget,
    desired_power=desired_power,
    objective=objective,
    loan_rate=loan_rate,
    loan_share=loan_share,
    mode=inputs_mode,
)

# ───────────────────────────────────────────
# MAIN TABS
# ───────────────────────────────────────────
tab_sim, tab_evap, tab_therm, tab_scen, tab_comp, tab_rank = st.tabs([
    "📊 Simulation",
    "📈 Évaporation mensuelle",
    "🌡️ Performance thermique",
    "💵 Scénarios économiques",
    "🔍 Comparaison multi-barrages",
    "🏆 Classement prioritaire"
])

# ─── TAB 1: Simulation ─────────────────────
with tab_sim:
    if selected_dam == "Tous (comparaison)":
        st.info(
            "Sélectionnez un barrage spécifique dans la barre latérale pour voir la simulation détaillée, "
            "ou consultez l'onglet 'Comparaison multi-barrages'."
        )
    else:
        dam_dict = dams_df[dams_df['name'] == selected_dam].iloc[0].to_dict()
        dam = DamProfile(**dam_dict)
        results = compute_project(dam, const, inputs)
        simulation_tab.render(results)

# ─── TAB 2: Evaporation ────────────────────
with tab_evap:
    if selected_dam == "Tous (comparaison)":
        dam_select = st.selectbox("Choisir un barrage pour l'analyse", dams_df['name'].tolist(), key="evap_dam")
    else:
        dam_select = selected_dam

    dam_row = dams_df[dams_df['name'] == dam_select].iloc[0]
    dam = DamProfile(**dam_row.to_dict())
    results = compute_project(dam, const, inputs)
    evaporation_tab.render(conn, dam.id, dam.name, results.retained_power, dam.covered_surface_m2)

# ─── TAB 3: Thermal ────────────────────────
with tab_therm:
    if selected_dam == "Tous (comparaison)":
        dam_select_t = st.selectbox("Choisir un barrage", dams_df['name'].tolist(), key="therm_dam")
    else:
        dam_select_t = selected_dam

    dam_id_t = int(dams_df[dams_df['name'] == dam_select_t]['id'].values[0])
    thermal_tab.render(conn, dam_id_t, dam_select_t)

# ─── TAB 4: Scenarios ──────────────────────
with tab_scen:
    scenarios_tab.render(conn)

# ─── TAB 5: Comparison ─────────────────────
with tab_comp:
    comparison_tab.render(dams_list, const, inputs)

# ─── TAB 6: Ranking ───────────────────────
with tab_rank:
    ranking_tab.render(conn)

# ─── Footer ────────────────────────────────
st.sidebar.divider()
st.sidebar.caption("FPV Tunisia v2.1 — Mode inversible | Prix STEG 2025 | Juin 2026")