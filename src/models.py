"""Modèles de données et structures du projet."""
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ProjectInputs:
    """Paramètres saisis par l'utilisateur."""
    budget: float
    desired_power: Optional[float]  # None si laissé vide
    objective: str  # "Production", "Économie d'eau", "Mixte"
    loan_rate: float
    loan_share: float
    mode: str = "budget"  # "budget" ou "power"

@dataclass
class DamProfile:
    """Profil d'un barrage (données statiques DB)."""
    id: int
    name: str
    productible: float
    economy_water_m3_mwc: float
    surface_ha: float
    cost_per_mwc: float
    constraint_type: str
    max_coverage_rate: float
    alert_text: str
    covered_surface_m2: float

@dataclass
class EconomicConstants:
    """Constantes économiques J1-J8."""
    J1: float  # Prix vente initial
    J2: float  # Indexation
    J3: float  # Dégradation
    J4: float  # OPEX
    J5: float  # Actualisation
    J6: int    # Durée vie (int pour range)
    J7: float  # CO2 évité
    J8: float  # CO2 FPV

@dataclass
class ProjectResults:
    """Résultats complets d'une simulation."""
    max_power: float
    retained_power: float
    production_y1_kwh: float
    production_gwh: float
    water_saved_m3: float
    surface_occupied_ha: float
    coverage_rate: float
    max_coverage: float
    alert: str
    alert_ok: bool
    capex: float
    opex: float
    co2_avoided: float
    co2_emitted: float
    co2_net: float
    loan_amount: float
    equity: float
    annuity: float
    cash_flows: List[float]
    years: List[int]
    van: float
    tri: float
    roi: float
    payback: Optional[int]
    aquatic_gain_percent: float = 0.0
    aquatic_gain_kwh: float = 0.0
