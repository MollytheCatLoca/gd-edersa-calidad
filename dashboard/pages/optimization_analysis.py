"""
Dashboard FASE 3: Análisis de Configuraciones en Tiempo Real
=======================================================
Permite explorar diferentes configuraciones de GD y ver resultados
de flujos integrados en tiempo real.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Configuración de paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
OPTIMIZATION_DIR = BASE_DIR / "reports" / "clustering" / "optimization"

# Importar módulos necesarios
import sys
sys.path.append(str(BASE_DIR))
from src.economics.integrated_cash_flow import IntegratedCashFlowCalculator
from src.economics.network_benefits import NetworkBenefitsCalculator
from src.config.config_loader import get_config
from dashboard.components.optimization_components import (
    create_header_section, create_config_card, create_form_group,
    create_slider_with_value, create_metric_card_v3, create_alert_banner,
    create_loading_overlay, COLORS
)

# Registrar página
dash.register_page(
    __name__,
    path='/optimization-analysis',
    name='Análisis de Optimización',
    title='Análisis de Configuraciones - FASE 3'
)

# Cargar datos de clusters
def load_cluster_data():
    """Carga datos de clusters preparados"""
    cluster_file = OPTIMIZATION_DIR / 'clusters_optimization_data.parquet'
    if cluster_file.exists():
        return pd.read_parquet(cluster_file)
    return pd.DataFrame()

# Calcular flujos para una configuración
def calculate_flows_realtime(cluster_data, pv_mw, bess_mwh, q_night_mvar):
    """Calcula flujos en tiempo real para una configuración"""
    # Inicializar calculadores
    cash_flow_calc = IntegratedCashFlowCalculator()
    network_calc = NetworkBenefitsCalculator()
    
    # Calcular CAPEX
    config = get_config()
    capex_params = config.get_section('capex')
    
    pv_capex = pv_mw * capex_params['pv_capex_usd_mw']
    bess_capex = bess_mwh * capex_params['bess_capex_usd_mwh']
    if q_night_mvar <= pv_mw * 0.3:
        q_capex = q_night_mvar * capex_params['statcom_capex_usd_mvar'] * 0.3
    else:
        q_capex = q_night_mvar * capex_params['statcom_capex_usd_mvar']
    
    subtotal = pv_capex + bess_capex + q_capex
    bos_capex = subtotal * capex_params['bos_factor']
    
    capex = {
        'pv': pv_capex,
        'bess': bess_capex,
        'q_night': q_capex,
        'bos': bos_capex,
        'total': subtotal + bos_capex
    }
    
    # Calcular flujos
    cash_flows = cash_flow_calc.calculate_integrated_flows(
        cluster_data, pv_mw, bess_mwh, q_night_mvar, capex
    )
    
    # Calcular métricas
    metrics = cash_flow_calc.calculate_financial_metrics(cash_flows, capex['total'])
    
    # Calcular beneficios de red
    network_benefits = network_calc.calculate_all_benefits(
        cluster_data, pv_mw, bess_mwh, q_night_mvar
    )
    
    # Preparar resultados
    avg_pv_flow = sum(cf.pv_flow for cf in cash_flows) / len(cash_flows)
    avg_network_flow = sum(cf.network_flow for cf in cash_flows) / len(cash_flows)
    avg_total_flow = sum(cf.total_flow for cf in cash_flows) / len(cash_flows)
    
    return {
        'capex': capex,
        'metrics': metrics,
        'avg_flows': {
            'pv': avg_pv_flow,
            'network': avg_network_flow,
            'total': avg_total_flow
        },
        'network_benefits': network_benefits,
        'cash_flows': cash_flows
    }

# Layout
layout = dbc.Container([
    # Header
    create_header_section(
        "Análisis de Configuraciones de GD",
        "Explore diferentes configuraciones y vea resultados en tiempo real",
        icon="fas fa-chart-line"
    ),
    
    # Panel de control
    dbc.Row([
        dbc.Col([
            create_config_card(
                "Configuración de Análisis",
                html.Div([
                    # Selector de cluster
                    create_form_group(
                        "Seleccionar Cluster",
                        dcc.Dropdown(
                            id="cluster-selector",
                            placeholder="Seleccione un cluster...",
                            className="form-control"
                        ),
                        "Elija el cluster para analizar configuraciones de GD",
                        icon="fas fa-map-marker-alt"
                    ),
            
                    # Configuración PV
                    create_form_group(
                        "Capacidad PV (ratio sobre demanda pico)",
                        html.Div([
                            dcc.Slider(
                                id="pv-ratio-slider",
                                min=0.5,
                                max=2.0,
                                step=0.1,
                                value=1.0,
                                marks={i/10: f'{i/10:.1f}x' for i in range(5, 21, 5)},
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-3"
                            ),
                            html.Div(id="pv-mw-display", className="text-center text-primary fw-bold")
                        ]),
                        "Define la capacidad solar como múltiplo de la demanda pico",
                        icon="fas fa-solar-panel"
                    ),
            
                    # Configuración BESS
                    create_form_group(
                        "Almacenamiento BESS (horas)",
                        html.Div([
                            dcc.Slider(
                                id="bess-hours-slider",
                                min=0,
                                max=4,
                                step=0.5,
                                value=0,
                                marks={i: f'{i}h' for i in range(5)},
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-3"
                            ),
                            html.Div(id="bess-mwh-display", className="text-center text-success fw-bold")
                        ]),
                        "Horas de almacenamiento a demanda pico",
                        icon="fas fa-battery-full"
                    ),
            
                    # Configuración Q nocturno
                    create_form_group(
                        "Compensación Reactiva Nocturna (ratio sobre PV)",
                        html.Div([
                            dcc.Slider(
                                id="q-night-ratio-slider",
                                min=0,
                                max=0.3,
                                step=0.05,
                                value=0.1,
                                marks={i/100: f'{i}%' for i in range(0, 31, 10)},
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-3"
                            ),
                            html.Div(id="q-mvar-display", className="text-center text-info fw-bold")
                        ]),
                        "Capacidad STATCOM para soporte nocturno",
                        icon="fas fa-moon"
                    ),
            
                    # Botón de cálculo
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-calculator me-2"), "Calcular Flujos"],
                            id="calculate-flows-btn",
                            color="primary",
                            size="lg",
                            className="w-100"
                        )
                    ], className="mt-4")
                ]),
                icon="fas fa-sliders-h",
                color="light"
            )
        ], md=4, className="mb-4"),
    
        # Panel de resultados
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    # Loading overlay
                    dcc.Loading(
                        id="loading-results",
                        type="circle",
                        children=[
                            # Métricas principales
                            html.Div([
                                html.H3([
                                    html.I(className="fas fa-chart-bar me-2"),
                                    "Métricas Financieras"
                                ], className="mb-4"),
                                html.Div(id="metrics-cards"),
                            ], className="mb-4"),
        
                            # Gráficos de flujos
                            dbc.Row([
                                # Desglose de flujos
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardHeader([
                                            html.I(className="fas fa-coins me-2"),
                                            "Desglose de Flujos Anuales"
                                        ]),
                                        dbc.CardBody([
                                            dcc.Graph(id="flow-breakdown-chart")
                                        ])
                                    ], className="h-100")
                                ], md=6, className="mb-4"),
                                
                                # Desglose de beneficios de red
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardHeader([
                                            html.I(className="fas fa-network-wired me-2"),
                                            "Beneficios en Red"
                                        ]),
                                        dbc.CardBody([
                                            dcc.Graph(id="network-benefits-chart")
                                        ])
                                    ], className="h-100")
                                ], md=6, className="mb-4"),
                            ]),
        
                            # Flujo de caja en el tiempo
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-timeline me-2"),
                                    "Flujo de Caja Proyectado"
                                ]),
                                dbc.CardBody([
                                    dcc.Graph(id="cashflow-timeline-chart")
                                ])
                            ], className="mb-4"),
                            
                            # Tabla de desglose detallado
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-table me-2"),
                                    "Desglose Detallado de Flujos"
                                ]),
                                dbc.CardBody([
                                    html.Div(id="detailed-breakdown-table")
                                ])
                            ])
                        ]
                    )
                ])
            ], id="results-panel", style={"display": "none"}, className="shadow-sm")
        ], md=8)
    ]),
    
    # Store para datos
    dcc.Store(id="calculation-results-store"),
    dcc.Store(id="cluster-data-store"),
], fluid=True)

# Callbacks
@callback(
    Output("cluster-selector", "options"),
    Output("cluster-selector", "value"),
    Input("cluster-selector", "id")
)
def load_clusters(_):
    """Carga opciones de clusters"""
    df = load_cluster_data()
    if df.empty:
        return [], None
    
    options = [
        {
            "label": f"Cluster {row['cluster_id']} - {row['peak_demand_mw']:.1f} MW - {row['total_users']:,.0f} usuarios",
            "value": row['cluster_id']
        }
        for _, row in df.iterrows()
    ]
    
    # Seleccionar el primer cluster por defecto
    return options, df.iloc[0]['cluster_id']

@callback(
    Output("cluster-data-store", "data"),
    Input("cluster-selector", "value")
)
def update_cluster_data(cluster_id):
    """Actualiza datos del cluster seleccionado"""
    if not cluster_id:
        return {}
    
    df = load_cluster_data()
    cluster_data = df[df['cluster_id'] == cluster_id].iloc[0].to_dict()
    return cluster_data

@callback(
    Output("pv-mw-display", "children"),
    Output("bess-mwh-display", "children"),
    Output("q-mvar-display", "children"),
    Input("pv-ratio-slider", "value"),
    Input("bess-hours-slider", "value"),
    Input("q-night-ratio-slider", "value"),
    State("cluster-data-store", "data")
)
def update_capacity_displays(pv_ratio, bess_hours, q_ratio, cluster_data):
    """Actualiza displays de capacidades"""
    if not cluster_data:
        return "", "", ""
    
    peak_demand = cluster_data.get('peak_demand_mw', 0)
    pv_mw = peak_demand * pv_ratio
    bess_mwh = peak_demand * bess_hours
    q_mvar = pv_mw * q_ratio
    
    return (
        f"{pv_mw:.1f} MW",
        f"{bess_mwh:.1f} MWh",
        f"{q_mvar:.1f} MVAr"
    )

@callback(
    Output("calculation-results-store", "data"),
    Output("results-panel", "style"),
    Input("calculate-flows-btn", "n_clicks"),
    State("pv-ratio-slider", "value"),
    State("bess-hours-slider", "value"),
    State("q-night-ratio-slider", "value"),
    State("cluster-data-store", "data"),
    prevent_initial_call=True
)
def calculate_flows(n_clicks, pv_ratio, bess_hours, q_ratio, cluster_data):
    """Calcula flujos para la configuración seleccionada"""
    if not n_clicks or not cluster_data:
        return {}, {"display": "none"}
    
    # Calcular capacidades
    peak_demand = cluster_data['peak_demand_mw']
    pv_mw = peak_demand * pv_ratio
    bess_mwh = peak_demand * bess_hours
    q_mvar = pv_mw * q_ratio
    
    # Calcular flujos
    results = calculate_flows_realtime(cluster_data, pv_mw, bess_mwh, q_mvar)
    
    # Agregar configuración
    results['config'] = {
        'pv_mw': pv_mw,
        'bess_mwh': bess_mwh,
        'q_mvar': q_mvar,
        'pv_ratio': pv_ratio,
        'bess_hours': bess_hours,
        'q_ratio': q_ratio
    }
    
    return results, {"display": "block"}

@callback(
    Output("metrics-cards", "children"),
    Input("calculation-results-store", "data")
)
def update_metrics_cards(results):
    """Actualiza las tarjetas de métricas"""
    if not results:
        return []
    
    metrics = results['metrics']
    capex = results['capex']['total'] / 1e6
    
    return dbc.Row([
        dbc.Col([
            create_metric_card_v3(
                "CAPEX Total",
                f"${capex:.1f}M",
                "Inversión inicial",
                icon="fas fa-dollar-sign",
                color="blue",
                gradient=True
            )
        ], md=4, lg=2, className="mb-3"),
        
        dbc.Col([
            create_metric_card_v3(
                "NPV",
                f"${metrics['npv_usd']/1e6:.1f}M",
                "Valor presente neto",
                icon="fas fa-chart-line",
                color="green",
                gradient=True
            )
        ], md=4, lg=2, className="mb-3"),
        
        dbc.Col([
            create_metric_card_v3(
                "TIR",
                f"{metrics['irr_percent']:.1f}%",
                "Tasa interna de retorno",
                icon="fas fa-percentage",
                color="purple",
                gradient=True
            )
        ], md=4, lg=2, className="mb-3"),
        
        dbc.Col([
            create_metric_card_v3(
                "Payback",
                f"{metrics['payback_years']:.1f}",
                "Años de recuperación",
                icon="fas fa-hourglass-half",
                color="orange",
                gradient=True
            )
        ], md=6, lg=3, className="mb-3"),
        
        dbc.Col([
            create_metric_card_v3(
                "Ratio B/C",
                f"{metrics['bc_ratio']:.2f}x",
                "Beneficio/Costo",
                icon="fas fa-balance-scale",
                color="teal",
                gradient=True
            )
        ], md=6, lg=3, className="mb-3"),
    ])

@callback(
    Output("flow-breakdown-chart", "figure"),
    Input("calculation-results-store", "data")
)
def update_flow_breakdown(results):
    """Actualiza gráfico de desglose de flujos"""
    if not results:
        return go.Figure()
    
    flows = results['avg_flows']
    
    fig = go.Figure()
    
    # Flujo PV
    fig.add_trace(go.Bar(
        name='Flujo PV',
        x=['Flujo Anual'],
        y=[flows['pv']/1e6],
        marker_color='#FFA500',
        text=[f"${flows['pv']/1e6:.1f}M"],
        textposition='inside'
    ))
    
    # Flujo Red
    fig.add_trace(go.Bar(
        name='Flujo Red',
        x=['Flujo Anual'],
        y=[flows['network']/1e6],
        marker_color='#4169E1',
        text=[f"${flows['network']/1e6:.1f}M"],
        textposition='inside'
    ))
    
    fig.update_layout(
        barmode='stack',
        yaxis_title="Flujo Anual (MUSD)",
        showlegend=True,
        height=400,
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Agregar línea de flujo total
    total = flows['total']/1e6
    fig.add_annotation(
        x=0, y=total + 2,
        text=f"Total: ${total:.1f}M/año",
        showarrow=False,
        font=dict(size=14, color="black", family="Arial Black")
    )
    
    return fig

@callback(
    Output("network-benefits-chart", "figure"),
    Input("calculation-results-store", "data")
)
def update_network_benefits(results):
    """Actualiza gráfico de beneficios en red"""
    if not results:
        return go.Figure()
    
    benefits = results['network_benefits']
    
    # Preparar datos
    benefit_types = []
    values = []
    
    for key, benefit in benefits.items():
        benefit_types.append(key.replace('_', ' ').title())
        values.append(benefit.value_usd / 1e6)
    
    fig = go.Figure(data=[
        go.Bar(
            x=benefit_types,
            y=values,
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
            text=[f"${v:.2f}M" for v in values],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        xaxis_title="Tipo de Beneficio",
        yaxis_title="Valor Total (MUSD)",
        height=400,
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

@callback(
    Output("cashflow-timeline-chart", "figure"),
    Input("calculation-results-store", "data")
)
def update_cashflow_timeline(results):
    """Actualiza gráfico de flujo de caja en el tiempo"""
    if not results:
        return go.Figure()
    
    cash_flows = results['cash_flows']
    capex = results['capex']['total']
    
    # Preparar datos
    years = [0] + [cf.year for cf in cash_flows]
    flows = [-capex/1e6] + [cf.total_flow/1e6 for cf in cash_flows]
    cumulative = np.cumsum(flows)
    
    fig = go.Figure()
    
    # Flujos anuales
    fig.add_trace(go.Bar(
        name='Flujo Anual',
        x=years,
        y=flows,
        marker_color=['red' if f < 0 else 'green' for f in flows],
        text=[f"${f:.1f}M" for f in flows],
        textposition='outside'
    ))
    
    # Flujo acumulado
    fig.add_trace(go.Scatter(
        name='Flujo Acumulado',
        x=years,
        y=cumulative,
        mode='lines+markers',
        line=dict(color='blue', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    # Línea de break-even
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        xaxis_title="Año",
        yaxis_title="Flujo Anual (MUSD)",
        yaxis2=dict(
            title="Flujo Acumulado (MUSD)",
            overlaying='y',
            side='right'
        ),
        height=400,
        template="plotly_white",
        hovermode='x unified',
        font=dict(family="system-ui, -apple-system, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

@callback(
    Output("detailed-breakdown-table", "children"),
    Input("calculation-results-store", "data")
)
def update_detailed_breakdown(results):
    """Actualiza tabla de desglose detallado"""
    if not results:
        return html.Div()
    
    # Preparar datos para la tabla
    config = results['config']
    capex = results['capex']
    flows = results['avg_flows']
    metrics = results['metrics']
    
    # Crear tabla con Bootstrap
    table_header = html.Thead([
        html.Tr([
            html.Th("Concepto", className="text-start"),
            html.Th("Valor", className="text-end")
        ])
    ], className="table-light")
    
    rows = [
        # Configuración
        html.Tr([
            html.Td(html.Strong("Configuración"), colSpan=2, className="table-secondary")
        ]),
        html.Tr([
            html.Td([html.I(className="fas fa-solar-panel me-2 text-warning"), "Capacidad PV"]),
            html.Td(f"{config['pv_mw']:.1f} MW", className="text-end")
        ]),
        html.Tr([
            html.Td([html.I(className="fas fa-battery-full me-2 text-success"), "Capacidad BESS"]),
            html.Td(f"{config['bess_mwh']:.1f} MWh", className="text-end")
        ]),
        html.Tr([
            html.Td([html.I(className="fas fa-moon me-2 text-info"), "Capacidad Q Nocturno"]),
            html.Td(f"{config['q_mvar']:.1f} MVAr", className="text-end")
        ]),
        
        # CAPEX
        html.Tr([
            html.Td(html.Strong("CAPEX"), colSpan=2, className="table-secondary")
        ]),
        html.Tr([
            html.Td("PV"),
            html.Td(f"${capex['pv']/1e6:.2f}M", className="text-end")
        ]),
        html.Tr([
            html.Td("BESS"),
            html.Td(f"${capex['bess']/1e6:.2f}M", className="text-end")
        ]),
        html.Tr([
            html.Td("STATCOM/Q"),
            html.Td(f"${capex['q_night']/1e6:.2f}M", className="text-end")
        ]),
        html.Tr([
            html.Td("BOS (15%)"),
            html.Td(f"${capex['bos']/1e6:.2f}M", className="text-end")
        ]),
        html.Tr([
            html.Td(html.Strong("Total CAPEX")),
            html.Td(html.Strong(f"${capex['total']/1e6:.2f}M"), className="text-end text-primary")
        ]),
        
        # Flujos
        html.Tr([
            html.Td(html.Strong("Flujos Anuales Promedio"), colSpan=2, className="table-secondary")
        ]),
        html.Tr([
            html.Td("Flujo PV"),
            html.Td(f"${flows['pv']/1e6:.2f}M/año", className="text-end")
        ]),
        html.Tr([
            html.Td("Flujo Red"),
            html.Td(f"${flows['network']/1e6:.2f}M/año", className="text-end")
        ]),
        html.Tr([
            html.Td(html.Strong("Flujo Total")),
            html.Td(html.Strong(f"${flows['total']/1e6:.2f}M/año"), className="text-end text-success")
        ]),
        
        # Indicadores
        html.Tr([
            html.Td(html.Strong("Indicadores Clave"), colSpan=2, className="table-secondary")
        ]),
        html.Tr([
            html.Td([html.I(className="fas fa-chart-pie me-2 text-info"), "Ratio Beneficios Red"]),
            html.Td(f"{flows['network']/flows['total']*100:.1f}%", className="text-end")
        ]),
        html.Tr([
            html.Td([html.I(className="fas fa-coins me-2 text-warning"), "Impacto por MUSD invertido"]),
            html.Td(f"{metrics['npv_usd']/capex['total']:.2f}x", className="text-end")
        ]),
    ]
    
    return dbc.Table(
        [table_header, html.Tbody(rows)],
        striped=True,
        hover=True,
        responsive=True,
        className="mb-0"
    )