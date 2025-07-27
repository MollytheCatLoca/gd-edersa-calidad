"""
Dashboard FASE 3: Comparación de Escenarios
=========================================
Permite comparar múltiples configuraciones y escenarios de optimización
para identificar la solución más efectiva.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import dash
from dash import dcc, html, callback, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Configuración de paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
OPTIMIZATION_DIR = BASE_DIR / "reports" / "clustering" / "optimization"
RESULTS_DIR = OPTIMIZATION_DIR / "integrated_flows"

# Importar módulos necesarios
import sys
sys.path.append(str(BASE_DIR))
from src.economics.integrated_cash_flow import IntegratedCashFlowCalculator
from src.config.config_loader import get_config
from dashboard.components.optimization_components import (
    create_header_section, create_config_card, create_form_group,
    create_slider_with_value, create_metric_card_v3, create_alert_banner,
    create_scenario_card, create_comparison_table, COLORS
)

# Registrar página
dash.register_page(
    __name__,
    path='/optimization-comparison',
    name='Comparación de Escenarios',
    title='Comparación de Escenarios - FASE 3'
)

# Funciones auxiliares
def load_saved_scenarios():
    """Carga escenarios guardados"""
    scenarios_file = OPTIMIZATION_DIR / 'saved_scenarios.json'
    if scenarios_file.exists():
        with open(scenarios_file, 'r') as f:
            return json.load(f)
    return {}

def save_scenario(name, config, results):
    """Guarda un escenario"""
    scenarios = load_saved_scenarios()
    scenarios[name] = {
        'config': config,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    
    scenarios_file = OPTIMIZATION_DIR / 'saved_scenarios.json'
    with open(scenarios_file, 'w') as f:
        json.dump(scenarios, f, indent=2)
    
    return scenarios

# Layout
layout = dbc.Container([
    # Header
    create_header_section(
        "Comparación de Escenarios de Optimización",
        "Compare diferentes configuraciones para maximizar el impacto en red",
        icon="fas fa-balance-scale"
    ),
    
    dbc.Row([
        # Panel de escenarios
        dbc.Col([
            create_config_card(
                "Gestión de Escenarios",
                html.Div([
                    # Botón para agregar escenario
                    dbc.Button(
                        [html.I(className="fas fa-plus me-2"), "Agregar Escenario"],
                        id="add-scenario-btn",
                        color="primary",
                        size="lg",
                        className="w-100 mb-4"
                    ),
                    
                    # Lista de escenarios
                    html.Div(id="scenarios-list"),
                    
                    # Sección de escenarios guardados
                    html.Hr(className="my-4"),
                    html.H5([
                        html.I(className="fas fa-save me-2 text-secondary"),
                        "Escenarios Guardados"
                    ], className="mb-3"),
                    
                    create_form_group(
                        "Seleccionar escenario",
                        dcc.Dropdown(
                            id="saved-scenarios-dropdown",
                            placeholder="Seleccionar escenario guardado...",
                            className="mb-3"
                        ),
                        icon="fas fa-folder-open"
                    ),
                    
                    dbc.Button(
                        [html.I(className="fas fa-download me-2"), "Cargar Escenario"],
                        id="load-scenario-btn",
                        color="secondary",
                        outline=True,
                        className="w-100"
                    ),
                ]),
                icon="fas fa-layer-group",
                color="light"
            )
        ], md=4, lg=3, className="mb-4"),
    
        # Panel de comparación
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    # Tabs de comparación
                    dbc.Tabs(id="comparison-tabs", active_tab='metrics', children=[
                        dbc.Tab(label='Métricas Principales', tab_id='metrics'),
                        dbc.Tab(label='Flujos de Caja', tab_id='cashflows'),
                        dbc.Tab(label='Beneficios de Red', tab_id='network'),
                        dbc.Tab(label='Análisis Multi-criterio', tab_id='multicriteria'),
                        dbc.Tab(label='Matriz de Decisión', tab_id='decision'),
                    ], className="mb-4"),
                    
                    # Contenido de tabs
                    dcc.Loading(
                        id="loading-comparison",
                        type="circle",
                        children=[
                            html.Div(id="comparison-content")
                        ]
                    )
                ])
            ], className="shadow-sm")
        ], md=8, lg=9)
    ]),
    
    # Stores para datos
    dcc.Store(id="scenarios-store", data={}),
    dcc.Store(id="scenario-counter", data=0),
    
    # Modal para configurar escenario
    html.Div(id="scenario-config-modal", style={"display": "none"}),
], fluid=True)

# Callbacks
@callback(
    Output("saved-scenarios-dropdown", "options"),
    Input("saved-scenarios-dropdown", "id")
)
def update_saved_scenarios(_):
    """Actualiza lista de escenarios guardados"""
    scenarios = load_saved_scenarios()
    return [{"label": name, "value": name} for name in scenarios.keys()]

@callback(
    Output("scenarios-store", "data"),
    Output("scenario-counter", "data"),
    Output("scenarios-list", "children"),
    Input("add-scenario-btn", "n_clicks"),
    Input("load-scenario-btn", "n_clicks"),
    Input({"type": "remove-scenario", "index": ALL}, "n_clicks"),
    Input({"type": "update-scenario", "index": ALL}, "n_clicks"),
    State("scenarios-store", "data"),
    State("scenario-counter", "data"),
    State("saved-scenarios-dropdown", "value"),
    State({"type": "scenario-name", "index": ALL}, "value"),
    State({"type": "cluster-select", "index": ALL}, "value"),
    State({"type": "pv-ratio", "index": ALL}, "value"),
    State({"type": "bess-hours", "index": ALL}, "value"),
    State({"type": "q-ratio", "index": ALL}, "value"),
    prevent_initial_call=True
)
def manage_scenarios(add_clicks, load_clicks, remove_clicks, update_clicks,
                    scenarios, counter, saved_name, names, clusters, 
                    pv_ratios, bess_hours, q_ratios):
    """Gestiona los escenarios activos"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return scenarios, counter, []
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Agregar nuevo escenario
    if trigger_id == "add-scenario-btn":
        counter += 1
        scenarios[f"scenario_{counter}"] = {
            "name": f"Escenario {counter}",
            "cluster_id": None,
            "pv_ratio": 1.0,
            "bess_hours": 0,
            "q_ratio": 0.1,
            "results": None
        }
    
    # Cargar escenario guardado
    elif trigger_id == "load-scenario-btn" and saved_name:
        saved_scenarios = load_saved_scenarios()
        if saved_name in saved_scenarios:
            counter += 1
            scenario_data = saved_scenarios[saved_name]
            scenarios[f"scenario_{counter}"] = {
                "name": saved_name,
                "cluster_id": scenario_data['config'].get('cluster_id'),
                "pv_ratio": scenario_data['config'].get('pv_ratio', 1.0),
                "bess_hours": scenario_data['config'].get('bess_hours', 0),
                "q_ratio": scenario_data['config'].get('q_ratio', 0.1),
                "results": scenario_data['results']
            }
    
    # Eliminar escenario
    elif "remove-scenario" in trigger_id:
        import json
        index = json.loads(trigger_id)['index']
        if index in scenarios:
            del scenarios[index]
    
    # Actualizar escenario
    elif "update-scenario" in trigger_id:
        # Actualizar todos los escenarios con los valores actuales
        for i, key in enumerate(list(scenarios.keys())):
            if i < len(names):
                scenarios[key]['name'] = names[i] or scenarios[key]['name']
            if i < len(clusters):
                scenarios[key]['cluster_id'] = clusters[i]
            if i < len(pv_ratios):
                scenarios[key]['pv_ratio'] = pv_ratios[i]
            if i < len(bess_hours):
                scenarios[key]['bess_hours'] = bess_hours[i]
            if i < len(q_ratios):
                scenarios[key]['q_ratio'] = q_ratios[i]
    
    # Crear lista de escenarios
    scenarios_list = []
    for key, scenario in scenarios.items():
        card = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        dbc.Input(
                            id={"type": "scenario-name", "index": key},
                            value=scenario['name'],
                            className="form-control-lg",
                            placeholder="Nombre del escenario"
                        )
                    ], width=8),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button(
                                html.I(className="fas fa-sync"),
                                id={"type": "update-scenario", "index": key},
                                color="success",
                                size="sm",
                                title="Actualizar"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-trash"),
                                id={"type": "remove-scenario", "index": key},
                                color="danger",
                                size="sm",
                                title="Eliminar"
                            ),
                        ], className="float-end")
                    ], width=4)
                ])
            ], className="bg-light"),
            dbc.CardBody([
                # Configuración
                create_form_group(
                    "Cluster",
                    dcc.Dropdown(
                        id={"type": "cluster-select", "index": key},
                        options=[
                            {"label": f"Cluster {i}", "value": i} 
                            for i in range(1, 16)
                        ],
                        value=scenario['cluster_id'],
                        className="mb-3"
                    ),
                    icon="fas fa-map-marker-alt"
                ),
                
                create_form_group(
                    "PV Ratio",
                    html.Div([
                        dcc.Slider(
                            id={"type": "pv-ratio", "index": key},
                            min=0.5, max=2.0, step=0.1,
                            value=scenario['pv_ratio'],
                            marks={i/10: f'{i/10:.1f}x' for i in range(5, 21, 5)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        html.Div(f"Valor: {scenario['pv_ratio']:.1f}x", 
                                className="text-center text-primary fw-bold mt-2")
                    ]),
                    icon="fas fa-solar-panel"
                ),
                
                create_form_group(
                    "BESS (horas)",
                    html.Div([
                        dcc.Slider(
                            id={"type": "bess-hours", "index": key},
                            min=0, max=4, step=0.5,
                            value=scenario['bess_hours'],
                            marks={i: f'{i}h' for i in range(5)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        html.Div(f"Valor: {scenario['bess_hours']}h", 
                                className="text-center text-success fw-bold mt-2")
                    ]),
                    icon="fas fa-battery-full"
                ),
                
                create_form_group(
                    "Q Night Ratio",
                    html.Div([
                        dcc.Slider(
                            id={"type": "q-ratio", "index": key},
                            min=0, max=0.3, step=0.05,
                            value=scenario['q_ratio'],
                            marks={i/100: f'{i}%' for i in range(0, 31, 10)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        html.Div(f"Valor: {scenario['q_ratio']*100:.0f}%", 
                                className="text-center text-info fw-bold mt-2")
                    ]),
                    icon="fas fa-moon"
                ),
                
                # Estado del escenario
                dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    "Configurado" if scenario['results'] else "Pendiente de cálculo"
                ], color="success" if scenario['results'] else "warning", 
                  className="mb-0 py-2")
            ])
        ], className="mb-3 shadow-sm")
        
        scenarios_list.append(card)
    
    return scenarios, counter, scenarios_list

@callback(
    Output("comparison-content", "children"),
    Input("comparison-tabs", "active_tab"),
    Input("scenarios-store", "data")
)
def update_comparison_content(active_tab, scenarios):
    """Actualiza el contenido de comparación según el tab activo"""
    if not scenarios:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No hay escenarios para comparar. Agregue al menos un escenario para comenzar."
        ], color="info", className="text-center")
    
    # Calcular resultados para escenarios sin resultados
    for key, scenario in scenarios.items():
        if scenario['results'] is None and scenario['cluster_id'] is not None:
            scenario['results'] = calculate_scenario_results(scenario)
    
    # Filtrar escenarios con resultados
    valid_scenarios = {k: v for k, v in scenarios.items() 
                      if v['results'] is not None}
    
    if not valid_scenarios:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Configure los escenarios con clusters válidos para ver comparaciones."
        ], color="warning", className="text-center")
    
    if active_tab == 'metrics':
        return create_metrics_comparison(valid_scenarios)
    elif active_tab == 'cashflows':
        return create_cashflow_comparison(valid_scenarios)
    elif active_tab == 'network':
        return create_network_comparison(valid_scenarios)
    elif active_tab == 'multicriteria':
        return create_multicriteria_analysis(valid_scenarios)
    elif active_tab == 'decision':
        return create_decision_matrix(valid_scenarios)
    
    return html.Div()

def calculate_scenario_results(scenario):
    """Calcula resultados para un escenario"""
    # Simulación de cálculo (en producción usaría IntegratedCashFlowCalculator)
    base_npv = 10.0  # MUSD
    
    # Ajustar por configuración
    pv_factor = scenario['pv_ratio'] ** 0.8
    bess_factor = 1 + scenario['bess_hours'] * 0.1
    q_factor = 1 + scenario['q_ratio'] * 2
    
    npv = base_npv * pv_factor * bess_factor * q_factor
    
    return {
        'npv_musd': npv,
        'irr_percent': 15 + (pv_factor - 1) * 5,
        'payback_years': 8 / pv_factor,
        'bc_ratio': 1.5 * pv_factor,
        'capex_musd': 5 * scenario['pv_ratio'] + 2 * scenario['bess_hours'],
        'network_benefits_musd': npv * 0.3,
        'pv_flow_musd': npv * 0.7,
        'lcoe_usd_mwh': 50 / pv_factor
    }

def create_metrics_comparison(scenarios):
    """Crea comparación de métricas principales"""
    # Preparar datos
    metrics_data = []
    for name, scenario in scenarios.items():
        results = scenario['results']
        metrics_data.append({
            'Escenario': scenario['name'],
            'NPV (MUSD)': results['npv_musd'],
            'TIR (%)': results['irr_percent'],
            'Payback (años)': results['payback_years'],
            'Ratio B/C': results['bc_ratio'],
            'CAPEX (MUSD)': results['capex_musd']
        })
    
    df = pd.DataFrame(metrics_data)
    
    # Crear gráficos con estilo mejorado
    fig1 = px.bar(df, x='Escenario', y=['NPV (MUSD)', 'CAPEX (MUSD)'],
                  title="NPV vs CAPEX", barmode='group',
                  color_discrete_map={'NPV (MUSD)': COLORS['success'], 
                                    'CAPEX (MUSD)': COLORS['primary']})
    
    fig1.update_layout(
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    
    fig2 = px.scatter(df, x='TIR (%)', y='Payback (años)', 
                     size='NPV (MUSD)', color='Escenario',
                     title="TIR vs Payback (tamaño = NPV)")
    
    fig2.update_layout(
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    
    # Tabla resumen con Bootstrap
    table = dbc.Table([
        html.Thead([
            html.Tr([html.Th(col) for col in df.columns])
        ], className="table-light"),
        html.Tbody([
            html.Tr([
                html.Td(df.iloc[i][col]) if not isinstance(df.iloc[i][col], float) 
                else html.Td(f"{df.iloc[i][col]:.2f}")
                for col in df.columns
            ]) for i in range(len(df))
        ])
    ], striped=True, hover=True, responsive=True, className="mb-0")
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-chart-bar me-2"),
                "Comparación de Métricas Financieras"
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(figure=fig1)
                    ], md=6),
                    dbc.Col([
                        dcc.Graph(figure=fig2)
                    ], md=6)
                ], className="mb-4"),
                
                html.Hr(),
                
                html.H5([
                    html.I(className="fas fa-table me-2"),
                    "Tabla Resumen"
                ], className="mb-3"),
                table
            ])
        ], className="shadow-sm")
    ])

def create_cashflow_comparison(scenarios):
    """Crea comparación de flujos de caja"""
    fig = go.Figure()
    
    years = list(range(26))  # 0 a 25 años
    
    for name, scenario in scenarios.items():
        results = scenario['results']
        
        # Simular flujos de caja
        cash_flows = [-results['capex_musd']]  # Año 0
        annual_flow = (results['pv_flow_musd'] + results['network_benefits_musd']) / 25
        
        for year in range(1, 26):
            degradation = 0.995 ** year
            cash_flows.append(annual_flow * degradation)
        
        cumulative = np.cumsum(cash_flows)
        
        # Agregar línea de flujo acumulado
        fig.add_trace(go.Scatter(
            x=years,
            y=cumulative,
            mode='lines+markers',
            name=scenario['name'],
            line=dict(width=3)
        ))
    
    # Línea de break-even
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title="Flujo de Caja Acumulado - Comparación",
        xaxis_title="Año",
        yaxis_title="Flujo Acumulado (MUSD)",
        hovermode='x unified',
        height=500,
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-chart-line me-2"),
            "Comparación de Flujos de Caja"
        ]),
        dbc.CardBody([
            dcc.Graph(figure=fig)
        ])
    ], className="shadow-sm")

def create_network_comparison(scenarios):
    """Crea comparación de beneficios en red"""
    # Preparar datos
    benefits_data = []
    
    for name, scenario in scenarios.items():
        results = scenario['results']
        benefits_data.append({
            'Escenario': scenario['name'],
            'Reducción Pérdidas': results['network_benefits_musd'] * 0.4,
            'Soporte Voltaje': results['network_benefits_musd'] * 0.3,
            'Diferimiento Inversión': results['network_benefits_musd'] * 0.2,
            'Q at Night': results['network_benefits_musd'] * 0.1
        })
    
    df = pd.DataFrame(benefits_data)
    
    # Gráfico de barras apiladas
    fig = go.Figure()
    
    benefit_types = ['Reducción Pérdidas', 'Soporte Voltaje', 
                    'Diferimiento Inversión', 'Q at Night']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, benefit in enumerate(benefit_types):
        fig.add_trace(go.Bar(
            name=benefit,
            x=df['Escenario'],
            y=df[benefit],
            marker_color=colors[i]
        ))
    
    fig.update_layout(
        barmode='stack',
        title="Desglose de Beneficios en Red",
        xaxis_title="Escenario",
        yaxis_title="Beneficio (MUSD)",
        height=500,
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-network-wired me-2"),
            "Comparación de Beneficios en Red"
        ]),
        dbc.CardBody([
            dcc.Graph(figure=fig)
        ])
    ], className="shadow-sm")

def create_multicriteria_analysis(scenarios):
    """Crea análisis multi-criterio"""
    # Criterios y pesos
    criteria = {
        'NPV': 0.3,
        'TIR': 0.2,
        'Payback': 0.15,
        'Beneficios Red': 0.2,
        'LCOE': 0.15
    }
    
    # Normalizar y calcular scores
    scores_data = []
    
    for name, scenario in scenarios.items():
        results = scenario['results']
        
        # Normalizar valores (0-1)
        normalized = {
            'NPV': results['npv_musd'] / 20,  # Asumiendo max 20 MUSD
            'TIR': results['irr_percent'] / 30,  # Asumiendo max 30%
            'Payback': 1 - (results['payback_years'] / 15),  # Invertido, max 15 años
            'Beneficios Red': results['network_benefits_musd'] / 10,  # Max 10 MUSD
            'LCOE': 1 - (results['lcoe_usd_mwh'] / 100)  # Invertido, max 100 USD/MWh
        }
        
        # Calcular score ponderado
        total_score = sum(normalized[crit] * weight 
                         for crit, weight in criteria.items())
        
        scores_data.append({
            'Escenario': scenario['name'],
            **normalized,
            'Score Total': total_score
        })
    
    df = pd.DataFrame(scores_data)
    
    # Gráfico de radar
    fig = go.Figure()
    
    for _, row in df.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[row[crit] for crit in criteria.keys()],
            theta=list(criteria.keys()),
            fill='toself',
            name=row['Escenario']
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title="Análisis Multi-criterio",
        height=500,
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, sans-serif")
    )
    
    # Ranking
    df_sorted = df.sort_values('Score Total', ascending=False)
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-radar-chart me-2"),
            "Análisis Multi-criterio"
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig)
                ], md=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Ranking Final", className="bg-primary text-white"),
                        dbc.CardBody([
                            dbc.ListGroup([
                                dbc.ListGroupItem([
                                    dbc.Badge(f"#{i+1}", color="primary", className="me-2"),
                                    f"{row['Escenario']}",
                                    dbc.Badge(f"Score: {row['Score Total']:.3f}", 
                                            color="success", className="float-end")
                                ]) for i, (_, row) in enumerate(df_sorted.iterrows())
                            ])
                        ])
                    ], className="shadow-sm")
                ], md=4)
            ])
        ])
    ], className="shadow-sm")

def create_decision_matrix(scenarios):
    """Crea matriz de decisión"""
    # Preparar matriz
    matrix_data = []
    
    for name, scenario in scenarios.items():
        results = scenario['results']
        
        # Evaluar criterios binarios
        matrix_data.append({
            'Escenario': scenario['name'],
            'NPV > 10M': '✅' if results['npv_musd'] > 10 else '❌',
            'TIR > 15%': '✅' if results['irr_percent'] > 15 else '❌',
            'Payback < 10 años': '✅' if results['payback_years'] < 10 else '❌',
            'B/C > 1.5': '✅' if results['bc_ratio'] > 1.5 else '❌',
            'LCOE < 60': '✅' if results['lcoe_usd_mwh'] < 60 else '❌',
            'Red > 30%': '✅' if results['network_benefits_musd']/results['npv_musd'] > 0.3 else '❌'
        })
    
    df = pd.DataFrame(matrix_data)
    
    # Crear tabla visual con Bootstrap
    table = dbc.Table([
        html.Thead([
            html.Tr([html.Th(col) for col in df.columns])
        ], className="table-primary"),
        html.Tbody([
            html.Tr([
                html.Td(df.iloc[i][col], className="text-center") 
                for col in df.columns
            ]) for i in range(len(df))
        ])
    ], striped=True, hover=True, responsive=True, className="mb-0")
    
    # Recomendaciones
    recommendations = []
    recommendation_cards = []
    
    for _, row in df.iterrows():
        check_count = sum(1 for col in df.columns[1:] if row[col] == '✅')
        if check_count >= 5:
            color = "success"
            icon = "fas fa-check-circle"
            status = "Altamente recomendado"
        elif check_count >= 3:
            color = "warning"
            icon = "fas fa-exclamation-circle"
            status = "Recomendado con reservas"
        else:
            color = "danger"
            icon = "fas fa-times-circle"
            status = "No recomendado"
        
        recommendation_cards.append(
            dbc.Alert([
                html.I(className=f"{icon} me-2"),
                html.Strong(row['Escenario']),
                html.Span(f": {status} "),
                dbc.Badge(f"{check_count}/6 criterios", color="dark", className="ms-2")
            ], color=color, className="mb-2")
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-th me-2"),
            "Matriz de Decisión"
        ]),
        dbc.CardBody([
            html.H5([
                html.I(className="fas fa-clipboard-check me-2"),
                "Criterios de Evaluación"
            ], className="mb-3"),
            table,
            
            html.Hr(className="my-4"),
            
            html.H5([
                html.I(className="fas fa-lightbulb me-2"),
                "Recomendaciones"
            ], className="mb-3"),
            html.Div(recommendation_cards)
        ])
    ], className="shadow-sm")