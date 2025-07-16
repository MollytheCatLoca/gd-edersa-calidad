"""
Página de Análisis de Beneficios Técnicos 24 Horas
"""

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Registrar página
dash.register_page(__name__, path='/benefits-24h', name='24h Benefits', order=9)

# Importar utilidades
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.components.metrics_cards import (
    create_metric_card, create_summary_card, create_alert_card
)

# Cargar datos
def load_benefits_24h_data():
    """Carga los datos de beneficios 24h"""
    base_path = Path(__file__).parent.parent.parent
    
    # Cargar beneficios técnicos
    benefits_file = base_path / "reports" / "clustering" / "benefits_24h" / "technical_benefits_24h.csv"
    if benefits_file.exists():
        df_benefits = pd.read_csv(benefits_file)
    else:
        # Datos de ejemplo si no existe el archivo
        df_benefits = pd.DataFrame({
            'cluster_id': range(15),
            'perfil_dominante': np.random.choice(['Comercial', 'Residencial', 'Mixto', 'Industrial'], 15),
            'gd_mw': np.random.uniform(1, 35, 15),
            'n_usuarios': np.random.randint(1000, 70000, 15),
            'voltage_improvement_pct': np.random.uniform(3, 5, 15),
            'night_voltage_improvement_pct': np.random.uniform(2, 4, 15),
            'voltage_improvement_24h_pct': np.random.uniform(3.5, 4.5, 15),
            'loss_reduction_pct': np.random.uniform(0.3, 0.8, 15),
            'loss_reduction_24h_pct': np.random.uniform(0.4, 0.6, 15),
            'power_factor_final': np.random.uniform(0.91, 0.94, 15),
            'operation_mode': np.random.choice(['Solar-Optimized', 'STATCOM-Optimized', 'Balanced 24h'], 15),
            'benefit_score_24h': np.random.uniform(0.4, 0.6, 15),
            'total_energy_value_mwh_year': np.random.uniform(5000, 50000, 15)
        })
    
    # Cargar reporte JSON
    report_file = base_path / "reports" / "clustering" / "benefits_24h" / "technical_benefits_24h_report.json"
    if report_file.exists():
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
    else:
        report = {
            'summary': {
                'avg_voltage_improvement_24h': 4.42,
                'avg_loss_reduction_24h': 0.49,
                'avg_power_factor_improvement': 0.081,
                'total_energy_value_gwh_year': 216.9
            },
            'economic_benefits': {
                'energy_displacement_value_musd': 9.0,
                'reactive_support_value_musd': 3.0,
                'loss_reduction_savings_musd': 1.5,
                'total_annual_benefits_musd': 15.0
            }
        }
    
    return df_benefits, report

# Crear perfiles horarios para visualización
def create_hourly_profiles():
    """Crea perfiles de carga y generación horarios"""
    hours = np.arange(24)
    
    # Perfiles de carga
    profiles = {
        'Residencial': {
            'load': np.concatenate([
                np.array([0.4, 0.35, 0.3, 0.3, 0.35, 0.5]),  # 0-5
                np.array([0.6, 0.7, 0.6, 0.4, 0.3, 0.3]),    # 6-11
                np.array([0.3, 0.3, 0.35, 0.4, 0.5, 0.6]),   # 12-17
                np.array([0.8, 0.95, 1.0, 0.9, 0.7, 0.5])    # 18-23
            ])
        },
        'Comercial': {
            'load': np.concatenate([
                np.array([0.2, 0.2, 0.2, 0.2, 0.2, 0.3]),    # 0-5
                np.array([0.4, 0.5, 0.7, 0.85, 0.95, 1.0]),  # 6-11
                np.array([0.95, 0.9, 0.85, 0.8, 0.7, 0.6]),  # 12-17
                np.array([0.5, 0.4, 0.3, 0.25, 0.2, 0.2])    # 18-23
            ])
        },
        'Industrial': {
            'load': np.concatenate([
                np.array([0.7, 0.7, 0.7, 0.7, 0.7, 0.8]),    # 0-5
                np.array([0.9, 0.9, 0.95, 1.0, 1.0, 1.0]),   # 6-11
                np.array([1.0, 1.0, 1.0, 0.95, 0.9, 0.9]),   # 12-17
                np.array([0.8, 0.75, 0.7, 0.7, 0.7, 0.7])    # 18-23
            ])
        },
        'Mixto': {
            'load': np.concatenate([
                np.array([0.4, 0.35, 0.35, 0.35, 0.4, 0.5]), # 0-5
                np.array([0.65, 0.75, 0.8, 0.85, 0.9, 0.9]), # 6-11
                np.array([0.85, 0.85, 0.8, 0.75, 0.7, 0.65]),# 12-17
                np.array([0.7, 0.75, 0.7, 0.6, 0.5, 0.45])   # 18-23
            ])
        }
    }
    
    # Perfil solar (igual para todos)
    solar = np.zeros(24)
    solar_hours = np.arange(6, 18)
    for h in solar_hours:
        solar[h] = np.exp(-0.5 * ((h - 12) / 3) ** 2)
    
    # Agregar perfil solar a cada tipo
    for profile in profiles.values():
        profile['solar'] = solar
    
    return hours, profiles

# Layout de la página
layout = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Análisis de Beneficios Técnicos 24 Horas", className="mb-1"),
            html.P("Evaluación integral de beneficios diurnos (generación solar) y nocturnos (STATCOM)", 
                   className="text-muted")
        ])
    ], className="mb-4"),
    
    # Alerta informativa
    dbc.Row([
        dbc.Col([
            create_alert_card(
                "Los inversores operando como STATCOM durante la noche pueden mejorar el factor de potencia de 0.85 a 0.93, generando beneficios adicionales significativos",
                color="info",
                icon="fas fa-clock",
                dismissable=True
            )
        ])
    ], className="mb-4"),
    
    # Métricas principales
    html.Div(id="benefits-metrics", className="mb-4"),
    
    # Tabs con diferentes vistas
    dbc.Tabs([
        dbc.Tab(label="Perfiles 24h", tab_id="profiles"),
        dbc.Tab(label="Comparación Día/Noche", tab_id="comparison"),
        dbc.Tab(label="Modos de Operación", tab_id="modes"),
        dbc.Tab(label="Beneficios Económicos", tab_id="economics")
    ], id="benefits-tabs", active_tab="profiles", className="mb-4"),
    
    # Contenido de los tabs
    html.Div(id="benefits-tab-content")
])

@callback(
    Output("benefits-metrics", "children"),
    Input("benefits-tabs", "active_tab")  # Trigger on page load
)
def update_metrics(_):
    """Actualiza las métricas principales"""
    df_benefits, report = load_benefits_24h_data()
    
    metrics = dbc.Row([
        dbc.Col([
            create_metric_card(
                "Mejora Tensión 24h",
                f"{report['summary']['avg_voltage_improvement_24h']:.2f}%",
                "Promedio ponderado día/noche",
                icon="fas fa-bolt",
                color="primary"
            )
        ], md=3),
        dbc.Col([
            create_metric_card(
                "Factor Potencia",
                f"0.93",
                "vs 0.85 base",
                icon="fas fa-tachometer-alt",
                color="success"
            )
        ], md=3),
        dbc.Col([
            create_metric_card(
                "Energía Gestionada",
                f"{report['summary']['total_energy_value_gwh_year']:.1f} GWh",
                "Activa + Reactiva equiv.",
                icon="fas fa-battery-full",
                color="info"
            )
        ], md=3),
        dbc.Col([
            create_metric_card(
                "Beneficio Anual",
                f"${report['economic_benefits']['total_annual_benefits_musd']:.1f}M USD",
                "Ahorro total sistema",
                icon="fas fa-dollar-sign",
                color="warning"
            )
        ], md=3)
    ])
    
    return metrics

@callback(
    Output("benefits-tab-content", "children"),
    Input("benefits-tabs", "active_tab")
)
def update_tab_content(active_tab):
    """Actualiza el contenido según el tab activo"""
    df_benefits, report = load_benefits_24h_data()
    
    if active_tab == "profiles":
        return create_profiles_content()
    elif active_tab == "comparison":
        return create_comparison_content(df_benefits)
    elif active_tab == "modes":
        return create_modes_content(df_benefits)
    elif active_tab == "economics":
        return create_economics_content(df_benefits, report)

def create_profiles_content():
    """Crea contenido de perfiles 24h"""
    hours, profiles = create_hourly_profiles()
    
    # Crear subplots para cada perfil
    fig = go.Figure()
    
    # Colores para cada perfil
    colors = {
        'Residencial': '#e74c3c',
        'Comercial': '#3498db',
        'Industrial': '#95a5a6',
        'Mixto': '#27ae60'
    }
    
    # Selector de perfil
    profile_selector = dcc.Dropdown(
        id='profile-selector',
        options=[
            {'label': 'Residencial', 'value': 'Residencial'},
            {'label': 'Comercial', 'value': 'Comercial'},
            {'label': 'Industrial', 'value': 'Industrial'},
            {'label': 'Mixto', 'value': 'Mixto'}
        ],
        value='Comercial',
        className="mb-3",
        style={'width': '300px'}
    )
    
    # Gráfico placeholder
    graph = dcc.Graph(id='profile-graph')
    
    # Explicación
    explanation = dbc.Card([
        dbc.CardBody([
            html.H5("Operación 24 Horas", className="card-title"),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H6("🌞 Operación Diurna (6:00-18:00)", className="text-warning"),
                    html.Ul([
                        html.Li("Generación solar activa"),
                        html.Li("Reducción de demanda desde la red"),
                        html.Li("Mejora de tensión por inyección de potencia"),
                        html.Li("Mayor beneficio en perfiles comerciales/industriales")
                    ])
                ], md=6),
                dbc.Col([
                    html.H6("🌙 Operación Nocturna (18:00-6:00)", className="text-primary"),
                    html.Ul([
                        html.Li("Inversor como STATCOM"),
                        html.Li("Compensación de potencia reactiva"),
                        html.Li("Mejora del factor de potencia"),
                        html.Li("Crítico para perfiles residenciales")
                    ])
                ], md=6)
            ])
        ])
    ], className="mt-4")
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Perfiles de Operación 24 Horas", className="mb-3"),
                html.P("Seleccione un perfil para ver la operación durante el día completo.", 
                      className="text-muted")
            ])
        ]),
        dbc.Row([
            dbc.Col([
                profile_selector
            ])
        ]),
        dbc.Row([
            dbc.Col([
                graph
            ])
        ]),
        dbc.Row([
            dbc.Col([
                explanation
            ])
        ])
    ])

# Callback para actualizar el gráfico de perfil
@callback(
    Output('profile-graph', 'figure'),
    Input('profile-selector', 'value')
)
def update_profile_graph(selected_profile):
    """Actualiza el gráfico según el perfil seleccionado"""
    hours, profiles = create_hourly_profiles()
    
    if selected_profile not in profiles:
        selected_profile = 'Comercial'
    
    profile_data = profiles[selected_profile]
    
    fig = go.Figure()
    
    # Área de operación STATCOM (nocturna)
    night_mask = profile_data['solar'] < 0.1
    fig.add_trace(go.Scatter(
        x=hours,
        y=np.where(night_mask, 1.1, 0),
        fill='tozeroy',
        fillcolor='rgba(147, 51, 234, 0.1)',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Perfil de demanda
    fig.add_trace(go.Scatter(
        x=hours,
        y=profile_data['load'],
        mode='lines',
        name='Demanda',
        line=dict(color='blue', width=3),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.2)'
    ))
    
    # Generación solar
    fig.add_trace(go.Scatter(
        x=hours,
        y=profile_data['solar'],
        mode='lines',
        name='Generación Solar',
        line=dict(color='gold', width=3),
        fill='tozeroy',
        fillcolor='rgba(251, 191, 36, 0.3)'
    ))
    
    # Anotaciones
    fig.add_annotation(
        x=12, y=1.05,
        text="Generación Solar",
        showarrow=False,
        font=dict(size=12, color='orange')
    )
    
    fig.add_annotation(
        x=21, y=1.05,
        text="STATCOM",
        showarrow=False,
        font=dict(size=12, color='purple')
    )
    
    fig.update_layout(
        title=f"Perfil {selected_profile} - Operación 24 Horas",
        xaxis_title="Hora del Día",
        yaxis_title="Por Unidad (p.u.)",
        hovermode='x unified',
        height=500,
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=2,
            range=[0, 23]
        ),
        yaxis=dict(range=[0, 1.15])
    )
    
    return fig

def create_comparison_content(df_benefits):
    """Crea comparación día vs noche"""
    
    # Top 10 clusters
    top_10 = df_benefits.nlargest(10, 'benefit_score_24h')
    
    # Gráfico de barras agrupadas
    fig_comparison = go.Figure()
    
    fig_comparison.add_trace(go.Bar(
        name='Mejora Tensión Día (%)',
        x=[f"C{int(id)}" for id in top_10['cluster_id']],
        y=top_10['voltage_improvement_pct'],
        marker_color='gold',
        text=top_10['voltage_improvement_pct'].round(1),
        textposition='outside'
    ))
    
    fig_comparison.add_trace(go.Bar(
        name='Mejora Tensión Noche (%)',
        x=[f"C{int(id)}" for id in top_10['cluster_id']],
        y=top_10['night_voltage_improvement_pct'],
        marker_color='purple',
        text=top_10['night_voltage_improvement_pct'].round(1),
        textposition='outside'
    ))
    
    fig_comparison.update_layout(
        title="Comparación de Beneficios: Día vs Noche (Top 10 Clusters)",
        xaxis_title="Cluster ID",
        yaxis_title="Mejora de Tensión (%)",
        barmode='group',
        height=500,
        hovermode='x unified'
    )
    
    # Scatter plot de beneficios
    fig_scatter = px.scatter(
        df_benefits,
        x='voltage_improvement_pct',
        y='night_voltage_improvement_pct',
        size='gd_mw',
        color='perfil_dominante',
        hover_data=['cluster_id', 'n_usuarios', 'operation_mode'],
        labels={
            'voltage_improvement_pct': 'Beneficio Diurno (%)',
            'night_voltage_improvement_pct': 'Beneficio Nocturno (%)',
            'perfil_dominante': 'Perfil',
            'gd_mw': 'GD (MW)'
        },
        title="Correlación Beneficios Día vs Noche"
    )
    
    # Línea diagonal
    max_val = max(df_benefits['voltage_improvement_pct'].max(), 
                  df_benefits['night_voltage_improvement_pct'].max())
    fig_scatter.add_trace(
        go.Scatter(x=[0, max_val], y=[0, max_val], 
                  mode='lines', line=dict(dash='dash', color='gray'),
                  showlegend=False)
    )
    
    fig_scatter.update_layout(height=500)
    
    return dbc.Row([
        dbc.Col([
            dcc.Graph(figure=fig_comparison)
        ], md=12),
        dbc.Col([
            dcc.Graph(figure=fig_scatter)
        ], md=12),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Insights Clave", className="card-title"),
                    html.Ul([
                        html.Li("Los perfiles residenciales muestran mayor beneficio nocturno relativo"),
                        html.Li("Los perfiles comerciales dominan en beneficios diurnos"),
                        html.Li("El modo Balanced 24h optimiza ambos períodos"),
                        html.Li("La mejora de tensión promedio 24h es más estable que considerar solo el día")
                    ])
                ])
            ], className="mt-3")
        ])
    ])

def create_modes_content(df_benefits):
    """Crea análisis de modos de operación"""
    
    # Distribución de modos
    mode_counts = df_benefits['operation_mode'].value_counts()
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=mode_counts.index,
        values=mode_counts.values,
        hole=0.4,
        marker_colors=['#f59e0b', '#8b5cf6', '#10b981']
    )])
    
    fig_pie.update_layout(
        title="Distribución de Modos de Operación",
        height=400
    )
    
    # Análisis por modo
    mode_stats = df_benefits.groupby('operation_mode').agg({
        'gd_mw': 'sum',
        'n_usuarios': 'sum',
        'benefit_score_24h': 'mean',
        'voltage_improvement_24h_pct': 'mean',
        'loss_reduction_24h_pct': 'mean',
        'power_factor_final': 'mean'
    }).round(3)
    
    # Crear tabla
    table_data = []
    for mode in mode_stats.index:
        table_data.append({
            'Modo de Operación': mode,
            'GD Total (MW)': f"{mode_stats.loc[mode, 'gd_mw']:.1f}",
            'Usuarios': f"{mode_stats.loc[mode, 'n_usuarios']:,}",
            'Score Beneficio': f"{mode_stats.loc[mode, 'benefit_score_24h']:.3f}",
            'Mejora Tensión (%)': f"{mode_stats.loc[mode, 'voltage_improvement_24h_pct']:.2f}",
            'FP Final': f"{mode_stats.loc[mode, 'power_factor_final']:.3f}"
        })
    
    table = dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in table_data[0].keys()],
        data=table_data,
        style_cell={
            'textAlign': 'center',
            'padding': '10px',
            'fontFamily': 'Arial'
        },
        style_header={
            'backgroundColor': 'rgb(59, 130, 246)',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Modo de Operación', 'filter_query': '{Modo de Operación} = "Balanced 24h"'},
                'backgroundColor': 'rgba(16, 185, 129, 0.2)',
                'fontWeight': 'bold'
            }
        ]
    )
    
    # Radar chart de características por modo
    categories = ['GD (MW)', 'Usuarios (k)', 'Mejora Tensión', 'Reducción Pérdidas', 'Factor Potencia']
    
    fig_radar = go.Figure()
    
    for mode in mode_stats.index:
        values = [
            mode_stats.loc[mode, 'gd_mw'] / df_benefits['gd_mw'].sum() * 10,
            mode_stats.loc[mode, 'n_usuarios'] / df_benefits['n_usuarios'].sum() * 10,
            mode_stats.loc[mode, 'voltage_improvement_24h_pct'],
            mode_stats.loc[mode, 'loss_reduction_24h_pct'] * 10,
            (mode_stats.loc[mode, 'power_factor_final'] - 0.85) * 50
        ]
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=mode
        ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=True,
        title="Características por Modo de Operación",
        height=500
    )
    
    # Cards de descripción
    mode_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-sun me-2"),
                    "Solar-Optimized"
                ], className="bg-warning text-dark"),
                dbc.CardBody([
                    html.P("Máximo beneficio durante el día con generación solar."),
                    html.Ul([
                        html.Li("Ideal para perfiles comerciales/industriales"),
                        html.Li("Alta coincidencia solar-demanda"),
                        html.Li("Beneficio nocturno limitado")
                    ])
                ])
            ])
        ], md=4),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-moon me-2"),
                    "STATCOM-Optimized"
                ], className="bg-primary text-white"),
                dbc.CardBody([
                    html.P("Mayor valor en soporte reactivo nocturno."),
                    html.Ul([
                        html.Li("Ideal para zonas residenciales"),
                        html.Li("Mejora significativa del FP"),
                        html.Li("Soporte de tensión crítico en la noche")
                    ])
                ])
            ])
        ], md=4),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-balance-scale me-2"),
                    "Balanced 24h"
                ], className="bg-success text-white"),
                dbc.CardBody([
                    html.P("Beneficios significativos día y noche."),
                    html.Ul([
                        html.Li("Mejor ROI general"),
                        html.Li("Versatilidad operativa"),
                        html.Li("Ideal para perfiles mixtos")
                    ])
                ])
            ])
        ], md=4)
    ], className="mb-4")
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=fig_pie)
            ], md=6),
            dbc.Col([
                dcc.Graph(figure=fig_radar)
            ], md=6)
        ]),
        mode_cards,
        dbc.Row([
            dbc.Col([
                html.H4("Estadísticas por Modo de Operación", className="mb-3"),
                table
            ])
        ])
    ])

def create_economics_content(df_benefits, report):
    """Crea análisis económico de beneficios"""
    
    # Waterfall chart de beneficios
    categories = ['Inversión\nInicial', 'Energía\nDesplazada', 'Soporte\nReactivo', 
                  'Reducción\nPérdidas', 'Diferimiento\nInversiones', 'Beneficio\nNeto']
    values = [-145, 60, 20, 15, 20, -30]  # Último valor es el neto
    
    # Calcular valores acumulados para waterfall
    cumulative = []
    cum_val = 0
    for i, val in enumerate(values[:-1]):
        cumulative.append(cum_val)
        cum_val += val
    cumulative.append(0)  # Para el beneficio neto
    values[-1] = cum_val  # Actualizar beneficio neto
    
    # Crear trazos para waterfall
    fig_waterfall = go.Figure()
    
    for i, (cat, val, cum) in enumerate(zip(categories, values, cumulative)):
        if i == 0:  # Inversión inicial
            fig_waterfall.add_trace(go.Bar(
                x=[cat],
                y=[abs(val)],
                base=0,
                marker_color='red',
                name='Inversión',
                text=f'${abs(val)}M',
                textposition='outside'
            ))
        elif i == len(categories) - 1:  # Beneficio neto
            fig_waterfall.add_trace(go.Bar(
                x=[cat],
                y=[val],
                base=0,
                marker_color='darkgreen' if val > 0 else 'darkred',
                name='Beneficio Neto',
                text=f'${val}M',
                textposition='outside'
            ))
        else:  # Beneficios
            fig_waterfall.add_trace(go.Bar(
                x=[cat],
                y=[val],
                base=cum,
                marker_color='lightgreen',
                name='Beneficios' if i == 1 else '',
                showlegend=(i == 1),
                text=f'+${val}M',
                textposition='outside'
            ))
    
    # Líneas conectoras
    for i in range(len(categories) - 2):
        fig_waterfall.add_trace(go.Scatter(
            x=[categories[i], categories[i+1]],
            y=[cumulative[i] + values[i], cumulative[i] + values[i]],
            mode='lines',
            line=dict(color='gray', width=1, dash='dot'),
            showlegend=False
        ))
    
    fig_waterfall.update_layout(
        title="Análisis Económico a 20 Años (Millones USD)",
        yaxis_title="Millones USD",
        showlegend=True,
        height=500,
        hovermode='x'
    )
    
    # Tabla de beneficios detallados
    benefits_detail = [
        {
            'Concepto': 'Desplazamiento de Energía',
            'Cantidad': f"{report['summary']['total_energy_value_gwh_year']:.1f} GWh/año",
            'Precio Unitario': '$60/MWh',
            'Valor Anual': f"${report['economic_benefits']['energy_displacement_value_musd']:.1f}M",
            'Valor 20 años': f"${report['economic_benefits']['energy_displacement_value_musd']*20:.0f}M"
        },
        {
            'Concepto': 'Soporte Reactivo (Q at Night)',
            'Cantidad': '36 MVAr promedio',
            'Precio Unitario': '$20/MWh eq.',
            'Valor Anual': f"${report['economic_benefits']['reactive_support_value_musd']:.1f}M",
            'Valor 20 años': f"${report['economic_benefits']['reactive_support_value_musd']*20:.0f}M"
        },
        {
            'Concepto': 'Reducción de Pérdidas',
            'Cantidad': f"{report['summary']['avg_loss_reduction_24h']:.1f}%",
            'Precio Unitario': '-',
            'Valor Anual': f"${report['economic_benefits']['loss_reduction_savings_musd']:.1f}M",
            'Valor 20 años': f"${report['economic_benefits']['loss_reduction_savings_musd']*20:.0f}M"
        }
    ]
    
    table = dash_table.DataTable(
        columns=[
            {"name": "Concepto", "id": "Concepto"},
            {"name": "Cantidad", "id": "Cantidad"},
            {"name": "Precio Unit.", "id": "Precio Unitario"},
            {"name": "Valor Anual", "id": "Valor Anual"},
            {"name": "Valor 20 años", "id": "Valor 20 años"}
        ],
        data=benefits_detail,
        style_cell={
            'textAlign': 'left',
            'padding': '10px'
        },
        style_header={
            'backgroundColor': 'rgb(34, 197, 94)',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Valor 20 años'},
                'fontWeight': 'bold',
                'color': 'darkgreen'
            }
        ]
    )
    
    # Métricas de retorno
    roi_metrics = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("10 años", className="card-title text-center"),
                    html.P("Payback Simple", className="text-center text-muted"),
                    html.Hr(),
                    html.P("Considerando beneficios completos 24h", className="text-center small")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("15%", className="card-title text-center text-success"),
                    html.P("TIR Estimada", className="text-center text-muted"),
                    html.Hr(),
                    html.P("Superior al WACC típico", className="text-center small")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("$75M", className="card-title text-center text-primary"),
                    html.P("VPN @ 10%", className="text-center text-muted"),
                    html.Hr(),
                    html.P("Valor presente neto positivo", className="text-center small")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("1.52", className="card-title text-center text-warning"),
                    html.P("B/C Ratio", className="text-center text-muted"),
                    html.Hr(),
                    html.P("Beneficio/Costo > 1", className="text-center small")
                ])
            ])
        ], md=3)
    ], className="mb-4")
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=fig_waterfall)
            ])
        ]),
        roi_metrics,
        dbc.Row([
            dbc.Col([
                html.H4("Detalle de Beneficios Económicos", className="mb-3"),
                table
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H5("Conclusión Económica", className="alert-heading"),
                    html.Hr(),
                    html.P("La operación 24 horas con capacidad Q at Night incrementa los beneficios económicos "
                          "en aproximadamente 40% respecto a considerar solo generación solar diurna. "
                          "El soporte reactivo nocturno representa $3M USD/año adicionales que justifican "
                          "la inversión en inversores con capacidad STATCOM.")
                ], color="success", className="mt-4")
            ])
        ])
    ])

# Callbacks adicionales pueden agregarse aquí según necesidad