"""Moteur de calcul — reproduit les formules Excel.

PATCH 2025-06
  - J1 par défaut → 0.307 TND/kWh (tarif STEG 2025). Mettre à jour la table
    `constants` en base : UPDATE constants SET value=0.307 WHERE key='J1';
  - Mode inverse power → budget consolidé
  - Puissance par défaut = 20 MWc (si budget=0 ET desired_power=0)
  - Calcul des équivalences environnementales (arbres, voitures, piscines)
"""
import numpy as np
import numpy_financial as npf
from typing import Optional
from src.models import (
    DamProfile, EconomicConstants, ProjectResults,
    ProjectInputs, EnvironmentalEquivalences,
)

# ---------------------------------------------------------------------------
# Constantes d'équivalences environnementales (ADEME / CITEPA)
# ---------------------------------------------------------------------------
_TREE_CO2_T_PER_YEAR = 0.02   # 1 arbre absorbe 0.02 tCO₂/an
_CAR_CO2_T_PER_YEAR = 2.5     # 1 voiture émet 2.5 tCO₂/an
_POOL_VOLUME_M3 = 2500         # 1 piscine olympique = 2 500 m³

# Puissance de référence par défaut (cas d'étude principal)
DEFAULT_POWER_MWC = 20.0
# Coût unitaire CAPEX (relation linéaire fixe)
CAPEX_PER_MWC = 2_300_000.0   # TND/MWc


def _compute_equivalences(co2_net_kg: float, water_saved_m3: float) -> EnvironmentalEquivalences:
    """Calcule les équivalences environnementales pédagogiques."""
    co2_net_tonnes = co2_net_kg / 1_000.0
    return EnvironmentalEquivalences(
        trees_planted=int(co2_net_tonnes / _TREE_CO2_T_PER_YEAR),
        cars_removed=int(co2_net_tonnes / _CAR_CO2_T_PER_YEAR),
        olympic_pools=round(water_saved_m3 / _POOL_VOLUME_M3, 1),
        co2_avoided_tonnes=round(co2_net_tonnes, 1),
    )


def compute_project(dam: DamProfile, const: EconomicConstants, inputs: ProjectInputs) -> ProjectResults:
    """Calcule tous les indicateurs pour un barrage donné et des paramètres utilisateur.

    Modes supportés
    ---------------
    "budget"  : l'utilisateur saisit un budget TND → puissance max calculée.
    "power"   : l'utilisateur saisit une puissance MWc → budget déduit.
    Valeur par défaut : 20 MWc (si ni budget ni puissance fournis).
    """

    # ------------------------------------------------------------------
    # 1. Résolution budget / puissance
    # ------------------------------------------------------------------
    if inputs.mode == "power" and inputs.desired_power and inputs.desired_power > 0:
        # Mode inverse : puissance connue → budget déduit
        retained_power = inputs.desired_power
        max_power = retained_power
    else:
        # Mode normal : budget → puissance
        # Valeur par défaut si budget ET puissance sont nuls
        if (inputs.budget is None or inputs.budget == 0) and \
           (inputs.desired_power is None or inputs.desired_power == 0):
            retained_power = DEFAULT_POWER_MWC
            max_power = DEFAULT_POWER_MWC
        else:
            budget_val = inputs.budget if inputs.budget and inputs.budget > 0 else 0
            max_power = np.floor(budget_val / CAPEX_PER_MWC * 10) / 10

            if inputs.desired_power is None or inputs.desired_power == 0:
                retained_power = max(0, max_power)
            else:
                retained_power = max(0, min(inputs.desired_power, max_power))

    # ------------------------------------------------------------------
    # 2. CAPEX  (relation linéaire fixe : 2 300 000 TND/MWc)
    # ------------------------------------------------------------------
    capex = CAPEX_PER_MWC * retained_power

    # ------------------------------------------------------------------
    # 3. Production
    # ------------------------------------------------------------------
    production_y1 = retained_power * 1000 * dam.productible
    production_gwh = production_y1 / 1e6

    # ------------------------------------------------------------------
    # 4. Eau
    # ------------------------------------------------------------------
    water_saved = dam.economy_water_m3_mwc * retained_power

    # ------------------------------------------------------------------
    # 5. Surfaces
    # ------------------------------------------------------------------
    surface_occupied = (retained_power / 20) * 9.25
    coverage_rate = (surface_occupied / dam.surface_ha) * 100

    alert_ok = coverage_rate <= dam.max_coverage_rate
    alert = "✅ Seuil respecté" if alert_ok else dam.alert_text

    # ------------------------------------------------------------------
    # 6. CAPEX / OPEX
    # ------------------------------------------------------------------
    opex = capex * const.J4

    # ------------------------------------------------------------------
    # 7. Gain aquatique
    # ------------------------------------------------------------------
    from src.config import get_aquatic_gain
    aq = get_aquatic_gain(dam.id)
    aquatic_gain_percent = aq.get("gain_percent", 0.0)
    aquatic_gain_kwh = aq.get("gain_kwh", 0) * (retained_power / 20.0)

    # ------------------------------------------------------------------
    # 8. CO₂
    # ------------------------------------------------------------------
    co2_avoided = (production_y1 / 1000) * const.J7          # MWh * kg/MWh = kg
    co2_emitted = (production_y1 / 1000) * const.J8
    co2_net = co2_avoided - co2_emitted                   # kg (already correct)

    # ------------------------------------------------------------------
    # 9. Équivalences environnementales  (PATCH 2025-06)
    # ------------------------------------------------------------------
    equivalences = _compute_equivalences(co2_net, water_saved)

    # ------------------------------------------------------------------
    # 10. Financement
    # ------------------------------------------------------------------
    loan_amount = capex * (inputs.loan_share / 100)
    equity = capex - loan_amount

    if inputs.loan_rate > 0 and inputs.loan_share > 0:
        r = inputs.loan_rate / 100
        annuity = npf.pmt(r, 10, -loan_amount)
    else:
        annuity = 0.0

    # ------------------------------------------------------------------
    # 11. Cash-flows 25 ans
    # ------------------------------------------------------------------
    years = list(range(const.J6 + 1))
    cash_flows = []

    for year in years:
        if year == 0:
            cf = -capex
        else:
            prod = production_y1 * ((1 - const.J3) ** (year - 1))
            price = const.J1 * ((1 + const.J2) ** (year - 1))
            revenue = prod * price
            opex_y = opex * ((1 + 0.02) ** (year - 1))
            ann = annuity if year <= 10 else 0
            cf = revenue - opex_y - ann
        cash_flows.append(cf)

    # ------------------------------------------------------------------
    # 12. Indicateurs financiers
    # ------------------------------------------------------------------
    van = npf.npv(const.J5, cash_flows[1:]) + cash_flows[0]
    try:
        tri = npf.irr(cash_flows)
    except Exception:
        tri = 0.0

    total_cf = sum(cash_flows)
    roi = (total_cf / capex) * 100 if capex > 0 else 0

    cumsum = np.cumsum(cash_flows)
    payback = None
    for i, val in enumerate(cumsum):
        if val > 0:
            payback = i
            break

    return ProjectResults(
        max_power=max_power,
        retained_power=retained_power,
        production_y1_kwh=production_y1,
        production_gwh=production_gwh,
        water_saved_m3=water_saved,
        surface_occupied_ha=surface_occupied,
        coverage_rate=coverage_rate,
        max_coverage=dam.max_coverage_rate,
        alert=alert,
        alert_ok=alert_ok,
        capex=capex,
        opex=opex,
        co2_avoided=co2_avoided,
        co2_emitted=co2_emitted,
        co2_net=co2_net,
        loan_amount=loan_amount,
        equity=equity,
        annuity=annuity,
        cash_flows=cash_flows,
        years=years,
        van=van,
        tri=tri,
        roi=roi,
        payback=payback,
        aquatic_gain_percent=aquatic_gain_percent,
        aquatic_gain_kwh=aquatic_gain_kwh,
        equivalences=equivalences,         # PATCH 2025-06
    )