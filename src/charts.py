"""Générateurs de graphiques Plotly (réutilisables).

PATCH 2025-06
  - ranking_chart()          : classement prioritaire des barrages (score + couleur)
  - equivalences_chart()     : bénéfices environnementaux avec équivalences
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List

# Palette couleurs priorité (cohérente avec _score_color dans config.py)
_COLOR_MAP = {
    "green": "#27ae60",      # Excellent
    "lightgreen": "#2ecc71", # Good
    "yellow": "#f39c12",   # Medium
    "orange": "#e67e22",    # Low
    "red": "#e74c3c",       # Caution
}


# ---------------------------------------------------------------------------
# Graphiques existants
# ---------------------------------------------------------------------------

def cashflow_chart(years: List[int], cash_flows: List[float]) -> go.Figure:
    """Graphique cash-flows annuels + cumulé."""
    df = pd.DataFrame({
        'Année': years,
        'Cash-flow': cash_flows,
        'Cumulé': pd.Series(cash_flows).cumsum()
    })
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Bar(x=df['Année'], y=df['Cash-flow'], name="Annuel",
                         marker_color='steelblue'))
    fig.add_trace(go.Scatter(x=df['Année'], y=df['Cumulé'], name="Cumulé",
                             mode='lines+markers',
                             line=dict(color='orange', width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.update_layout(height=450, xaxis_title="Année", yaxis_title="TND",
                      showlegend=True)
    return fig


def evaporation_bar_chart(evap_df: pd.DataFrame, dam_name: str) -> go.Figure:
    """Taux d'évaporation quotidien par mois."""
    fig = px.bar(evap_df, x='month_name', y='e_mm_day',
                 title=f"Taux d'évaporation quotidien — {dam_name}",
                 labels={'e_mm_day': 'E (mm/j)', 'month_name': 'Mois'},
                 color_discrete_sequence=['#e74c3c'])
    fig.update_layout(height=400)
    return fig


def evaporation_volume_chart(evap_df: pd.DataFrame, dam_name: str) -> go.Figure:
    """Volumes évaporés avec/sans FPV."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=evap_df['month_name'], y=evap_df['volume_without_fpv'],
                         name='Sans FPV', marker_color='lightcoral'))
    fig.add_trace(go.Bar(x=evap_df['month_name'], y=evap_df['volume_with_fpv'],
                         name='Avec FPV', marker_color='steelblue'))
    fig.update_layout(barmode='group', title=f"Volumes évaporés — {dam_name}",
                      yaxis_title="m³", height=400)
    return fig


def thermal_comparison_chart(therm_df: pd.DataFrame, dam_name: str) -> go.Figure:
    """Comparaison température cellules + production terre vs float."""
    fig = make_subplots(rows=2, cols=1,
                        subplot_titles=("Température des cellules",
                                        "Production mensuelle"),
                        vertical_spacing=0.12)
    fig.add_trace(go.Scatter(x=therm_df['month_name'], y=therm_df['tcell_terre'],
                              mode='lines+markers', name='Terrestre',
                              line=dict(color='red')), row=1, col=1)
    fig.add_trace(go.Scatter(x=therm_df['month_name'], y=therm_df['tcell_float'],
                              mode='lines+markers', name='Flottant',
                              line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Bar(x=therm_df['month_name'], y=therm_df['egrid_terre_kwh'],
                          name='Terrestre', marker_color='lightcoral'), row=2, col=1)
    fig.add_trace(go.Bar(x=therm_df['month_name'], y=therm_df['egrid_float_kwh'],
                          name='Flottant', marker_color='steelblue'), row=2, col=1)
    fig.update_layout(height=650, showlegend=True)
    return fig


def scenario_comparison_chart(scenarios_df: pd.DataFrame) -> go.Figure:
    """Comparaison des scénarios économiques."""
    fig = px.bar(scenarios_df, x='scenario_name', y=['van_tnd', 'tri_percent'],
                 barmode='group', title="Comparaison des scénarios d'indexation")
    fig.update_layout(height=450)
    return fig


def production_comparison_chart(comp_df: pd.DataFrame) -> go.Figure:
    """Production par barrage."""
    return px.bar(comp_df, x='Barrage', y='Production (GWh/an)', color='Alerte',
                  title="Production annuelle par barrage",
                  color_discrete_map={'✅': 'green', '⚠️': 'orange'})


def water_comparison_chart(comp_df: pd.DataFrame) -> go.Figure:
    """Économie d'eau par barrage."""
    return px.bar(comp_df, x='Barrage', y='Économie eau (m³/an)', color='Alerte',
                  title="Économie d'eau annuelle par barrage",
                  color_discrete_map={'✅': 'green', '⚠️': 'orange'})


# ---------------------------------------------------------------------------
# PATCH 2025-06 — Nouveaux graphiques
# ---------------------------------------------------------------------------

def ranking_chart(scores_df: pd.DataFrame) -> go.Figure:
    """Classement prioritaire des barrages par score pondéré.

    Parameters
    ----------
    scores_df : DataFrame produit par config.scores_to_dataframe()
        Colonnes attendues : 'Barrage', 'Score',
        'Production (GWh/an)', 'Eau (m³/an)', 'Gain aquatique (%)'.
    """
    # Extraire la couleur depuis la colonne 'Rang' ("red #1" → "red" ou "🔴 #1" → "🔴")
    # Handle both text and emoji color formats
    def extract_color(rang_str):
        if rang_str in ["red", "orange", "yellow", "green"]:
            return rang_str
        import re
        match = re.match(r'([🔴🟠🟡🟢]|red|orange|yellow|green)\s*#', rang_str)
        return match.group(1) if match else "green"
    
    emoji_colors = scores_df['Rang'].apply(extract_color)
    bar_colors = [_COLOR_MAP.get(e, '#95a5a6') for e in emoji_colors]

    fig = go.Figure()

    # Barre de score
    fig.add_trace(go.Bar(
        x=scores_df['Barrage'],
        y=scores_df['Score'],
        marker_color=bar_colors,
        text=[f"{s:.0f}" for s in scores_df['Score']],
        textposition='outside',
        name='Score global',
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Score : %{y:.1f}/100<br>"
            "<extra></extra>"
        ),
    ))

    # Sous-scores empilés (optionnel — mode grouped)
    for col, color, label in [
        ('Production (GWh/an)', '#3498db', 'Production'),
        ('Eau (m³/an)',          '#1abc9c', 'Eau'),
        ('Gain aquatique (%)',   '#9b59b6', 'Gain aquatique'),
    ]:
        if col in scores_df.columns:
            # Normalisation visuelle simple pour comparaison
            vals = scores_df[col]
            mn, mx = vals.min(), vals.max()
            norm = (vals - mn) / (mx - mn) * 100 if mx != mn else pd.Series([50.0]*len(vals))
            fig.add_trace(go.Bar(
                x=scores_df['Barrage'],
                y=norm,
                name=label,
                marker_color=color,
                opacity=0.45,
                visible='legendonly',
            ))

    fig.add_hline(y=90, line_dash="dot", line_color="#e74c3c",
                  annotation_text="Seuil priorité max (90)", annotation_position="right")
    fig.add_hline(y=75, line_dash="dot", line_color="#e67e22",
                  annotation_text="Seuil haute priorité (75)", annotation_position="right")

    fig.update_layout(
        title="🏆 Classement prioritaire des barrages — FPV",
        xaxis_title="Barrage",
        yaxis_title="Score (0 – 100)",
        yaxis_range=[0, 115],
        barmode='overlay',
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    )
    return fig


def equivalences_chart(
    trees: int,
    cars: int,
    pools: float,
    co2_t: float,
    water_m3: float,
    dam_name: str,
) -> go.Figure:
    """Graphique bénéfices environnementaux avec équivalences pédagogiques.

    Affiche un graphique à indicateurs (gauge / indicator) pour rendre
    les bénéfices compréhensibles pour un public non-technique.
    """
    fig = make_subplots(
        rows=2, cols=3,
        specs=[[{"type": "indicator"}] * 3,
               [{"type": "indicator"}] * 3],
        vertical_spacing=0.3,
    )

    indicators = [
        # (valeur, titre, suffixe, ligne, colonne)
        (co2_t,   "🌱 CO₂ évité",           " t/an",     1, 1),
        (trees,   "🌳 Arbres équivalents",   "",          1, 2),
        (cars,    "🚗 Voitures retirées",    "",          1, 3),
        (water_m3 / 1000, "💧 Eau économisée", " 000 m³/an", 2, 1),
        (pools,   "🏊 Piscines olympiques", "",          2, 2),
        (0,       "",                        "",          2, 3),   # placeholder
    ]

    for val, title, suffix, row, col in indicators:
        if not title:
            continue
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=val,
                number={"suffix": suffix, "font": {"size": 28}},
                title={"text": title, "font": {"size": 14}},
            ),
            row=row, col=col,
        )

    fig.update_layout(
        title=f"🌍 Bénéfices environnementaux annuels — {dam_name}",
        height=380,
        margin=dict(t=60, b=20),
    )
    return fig


def aquatic_gain_chart(therm_df: pd.DataFrame, dam_name: str) -> go.Figure:
    """Gain énergétique mensuel flottant vs terrestre (kWh + %).

    PATCH 2025-06 : graphique dédié au gain aquatique pour l'onglet score.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Gain mensuel (kWh)", "Gain mensuel (%)"),
    )

    gain_kwh = therm_df['egrid_float_kwh'] - therm_df['egrid_terre_kwh']
    gain_pct = (gain_kwh / therm_df['egrid_terre_kwh'].replace(0, float('nan'))) * 100

    fig.add_trace(go.Bar(
        x=therm_df['month_name'], y=gain_kwh,
        name='Gain (kWh)', marker_color='#27ae60',
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=therm_df['month_name'], y=gain_pct,
        mode='lines+markers', name='Gain (%)',
        line=dict(color='#8e44ad', width=2),
    ), row=1, col=2)

    fig.update_layout(
        title=f"Gain aquatique mensuel — {dam_name}",
        height=400,
        showlegend=True,
    )
    return fig