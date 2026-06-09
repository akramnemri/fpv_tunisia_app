"""Générateurs de graphiques Plotly (réutilisables)."""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List

def cashflow_chart(years: List[int], cash_flows: List[float]) -> go.Figure:
    """Graphique cash-flows annuels + cumulé."""
    df = pd.DataFrame({
        'Année': years,
        'Cash-flow': cash_flows,
        'Cumulé': pd.Series(cash_flows).cumsum()
    })
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Bar(x=df['Année'], y=df['Cash-flow'], name="Annuel", marker_color='steelblue'))
    fig.add_trace(go.Scatter(x=df['Année'], y=df['Cumulé'], name="Cumulé", mode='lines+markers',
                              line=dict(color='orange', width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.update_layout(height=450, xaxis_title="Année", yaxis_title="TND", showlegend=True)
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
    fig = make_subplots(rows=2, cols=1, subplot_titles=("Température des cellules", "Production mensuelle"),
                        vertical_spacing=0.12)
    fig.add_trace(go.Scatter(x=therm_df['month_name'], y=therm_df['tcell_terre'],
                              mode='lines+markers', name='Terrestre', line=dict(color='red')), row=1, col=1)
    fig.add_trace(go.Scatter(x=therm_df['month_name'], y=therm_df['tcell_float'],
                              mode='lines+markers', name='Flottant', line=dict(color='blue')), row=1, col=1)
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
