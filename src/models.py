"""Modèles de données et structures du projet."""
from dataclasses import dataclass, field
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
    """Constantes économiques J1-J8.

    PATCH 2025-06 : J1 mis à jour → 0.307 TND/kWh (tarif STEG 2025).
    Valeur précédente : 0.285 TND/kWh.
    """
    J1: float  # Prix vente initial  ← 0.307 TND/kWh (STEG 2025)
    J2: float  # Indexation
    J3: float  # Dégradation
    J4: float  # OPEX ratio
    J5: float  # Taux d'actualisation
    J6: int    # Durée de vie (int pour range)
    J7: float  # Facteur CO2 évité (kg/kWh)
    J8: float  # Facteur CO2 émis FPV (kg/kWh)


@dataclass
class EnvironmentalEquivalences:
    """Équivalences environnementales pour affichage pédagogique.

    Sources des facteurs : ADEME, CITEPA.
      - 1 arbre absorbe ~0.02 tCO₂/an
      - 1 voiture émet ~2.5 tCO₂/an
      - 1 piscine olympique = 2 500 m³
    """
    trees_planted: int          # CO₂_évité_t / 0.02
    cars_removed: int           # CO₂_évité_t / 2.5
    olympic_pools: float        # eau économisée / 2 500
    co2_avoided_tonnes: float   # CO₂ net en tonnes


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
    # PATCH 2025-06 : équivalences environnementales
    equivalences: Optional[EnvironmentalEquivalences] = None


@dataclass
class DamScore:
    """Score de priorité d'un barrage pour l'installation FPV.

    Pondérations (rapport de modifications 2025-06) :
      Production annuelle      30 %
      Économie d'eau           25 %
      Gain aquatique           20 %
      Performance Ratio (PR)   15 %
      Contrainte environnement 10 %  (pénalité Ramsar)
    """
    dam_id: int
    dam_name: str
    score: float                  # 0 – 100
    rank: int
    color: str                    # 🔴 🟠 🟡 🟢
    production_score: float
    water_score: float
    aquatic_score: float
    pr_score: float
    constraint_score: float
    # Valeurs brutes (pour tooltip)
    production_gwh: float
    water_m3: float
    aquatic_gain_pct: float
    pr_pct: float
    has_ramsar: bool