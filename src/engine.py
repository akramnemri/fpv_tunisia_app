"""Moteur de calcul — reproduit les formules Excel."""
import numpy as np
import numpy_financial as npf
from typing import Optional
from src.models import DamProfile, EconomicConstants, ProjectResults, ProjectInputs

def compute_project(dam: DamProfile, const: EconomicConstants, inputs: ProjectInputs) -> ProjectResults:
    """Calcule tous les indicateurs pour un barrage donné et des paramètres utilisateur."""

    # --- Mode inverse (power -> budget) ---
    if inputs.mode == "power" and inputs.desired_power and inputs.desired_power > 0:
        retained_power = inputs.desired_power
        max_power = retained_power
    else:
        # --- Puissance ---
        max_power = np.floor(inputs.budget / dam.cost_per_mwc * 10) / 10

        if inputs.desired_power is None or inputs.desired_power == 0:
            retained_power = max_power
        else:
            retained_power = min(inputs.desired_power, max_power)

    # --- CAPEX (needed for both modes) ---
    capex = dam.cost_per_mwc * retained_power

    # --- Production ---
    production_y1 = retained_power * 1000 * dam.productible
    production_gwh = production_y1 / 1e6

    # --- Eau ---
    water_saved = dam.economy_water_m3_mwc * retained_power

    # --- Surfaces ---
    surface_occupied = (retained_power / 20) * 9.25
    coverage_rate = (surface_occupied / dam.surface_ha) * 100

    alert_ok = coverage_rate <= dam.max_coverage_rate
    alert = "✅ Seuil respecté" if alert_ok else dam.alert_text

    # --- CAPEX / OPEX ---
    opex = capex * const.J4

    # --- Aquatic gain ---
    from src.config import get_aquatic_gain
    aq = get_aquatic_gain(dam.id)
    aquatic_gain_percent = aq.get("gain_percent", 0.0)
    aquatic_gain_kwh = aq.get("gain_kwh", 0) * (retained_power / 20.0)

    # --- CO2 ---
    co2_avoided = production_y1 * const.J7
    co2_emitted = production_y1 * const.J8
    co2_net = co2_avoided - co2_emitted

    # --- Financement ---
    loan_amount = capex * (inputs.loan_share / 100)
    equity = capex - loan_amount

    if inputs.loan_rate > 0 and inputs.loan_share > 0:
        r = inputs.loan_rate / 100
        annuity = npf.pmt(r, 10, -loan_amount)
    else:
        annuity = 0.0

    # --- Cash-flows 25 ans ---
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

    # --- Indicateurs ---
    van = npf.npv(const.J5, cash_flows[1:]) + cash_flows[0]
    try:
        tri = npf.irr(cash_flows)
    except:
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
    )
