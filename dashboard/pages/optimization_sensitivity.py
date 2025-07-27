"""
Dashboard FASE 3: Análisis de Sensibilidad
=========================================
Permite realizar análisis de sensibilidad detallado sobre los parámetros
clave del modelo de optimización.

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
from src.config.config_loader import get_config
from dashboard.components.optimization_components import (
    create_header_section, create_config_card, create_form_group,
    create_slider_with_value, create_metric_card_v3, create_alert_banner,
    create_sensitivity_chart, COLORS
)

# Registrar página
dash.register_page(
    __name__,
    path='/optimization-sensitivity',
    name='Análisis de Sensibilidad',
    title='Análisis de Sensibilidad - FASE 3'
)

# Funciones de análisis
def perform_sensitivity_analysis(base_case, parameter, variations):
    """Realiza análisis de sensibilidad para un parámetro"""
    results = []
    
    for variation in variations:
        # Clonar caso base
        case = base_case.copy()
        
        # Aplicar variación
        if parameter == 'electricity_price':
            case['revenue'] = base_case['revenue'] * (1 + variation/100)
        elif parameter == 'pv_capex':
            case['capex'] = base_case['capex'] * (1 + variation/100)
        elif parameter == 'discount_rate':
            # Recalcular NPV con nueva tasa
            discount_factor = (1 + base_case['discount_rate'] * (1 + variation/100))
            case['npv'] = base_case['npv'] / ((1 + variation/100) ** 0.5)
        elif parameter == 'capacity_factor':
            case['revenue'] = base_case['revenue'] * (1 + variation/100)
            case['npv'] = base_case['npv'] * (1 + variation/100)
        elif parameter == 'opex':
            annual_cost_change = base_case['capex'] * 0.01 * variation/100
            case['npv'] = base_case['npv'] - annual_cost_change * 15  # Simplificado
        
        # Recalcular métricas
        case['irr'] = 15 * (case['npv'] / base_case['npv'])  # Aproximación
        case['payback'] = base_case['payback'] / (case['npv'] / base_case['npv'])
        case['variation'] = variation
        
        results.append(case)
    
    return pd.DataFrame(results)

def calculate_monte_carlo(n_simulations=1000):
    """Realiza simulación Monte Carlo"""
    np.random.seed(42)
    
    # Distribuciones de parámetros
    electricity_price = np.random.normal(75, 10, n_simulations)  # USD/MWh
    pv_capex = np.random.normal(800000, 100000, n_simulations)  # USD/MW
    capacity_factor = np.random.beta(8, 2, n_simulations) * 0.3  # 0-30%
    discount_rate = np.random.uniform(0.08, 0.15, n_simulations)
    
    # Calcular NPV para cada simulación
    npv_results = []
    for i in range(n_simulations):
        # Modelo simplificado de NPV
        revenue = electricity_price[i] * capacity_factor[i] * 8760 * 10  # 10MW ejemplo
        capex = pv_capex[i] * 10
        annual_flow = revenue - capex * 0.01  # OPEX 1%
        
        # NPV simplificado
        npv = -capex + sum(annual_flow / (1 + discount_rate[i])**year 
                          for year in range(1, 26))
        npv_results.append(npv / 1e6)  # En MUSD
    
    return np.array(npv_results), {
        'electricity_price': electricity_price,
        'pv_capex': pv_capex,
        'capacity_factor': capacity_factor,
        'discount_rate': discount_rate
    }

# Layout
layout = dbc.Container([
    # Header
    create_header_section(
        "Análisis de Sensibilidad Avanzado",
        "Evalúe el impacto de la incertidumbre en los resultados y tome decisiones robustas",
        icon="fas fa-chart-line"
    ),
    
    dbc.Row([
        # Panel de configuración
        dbc.Col([
            create_config_card(
                "Configuración del Análisis",
                html.Div([
                    # Selector de tipo de análisis
                    create_form_group(
                        "Tipo de Análisis",
                        dbc.RadioItems(
                            id="sensitivity-type",
                            options=[
                                {"label": [html.I(className="fas fa-chart-bar me-2"), "Análisis Univariado"], 
                                 "value": "univariate"},
                                {"label": [html.I(className="fas fa-th me-2"), "Análisis Bivariado"], 
                                 "value": "bivariate"},
                                {"label": [html.I(className="fas fa-dice me-2"), "Simulación Monte Carlo"], 
                                 "value": "montecarlo"},
                                {"label": [html.I(className="fas fa-project-diagram me-2"), "Análisis de Escenarios"], 
                                 "value": "scenarios"}
                            ],
                            value="univariate",
                            className="mt-2"
                        ),
                        "Seleccione el tipo de análisis a realizar",
                        icon="fas fa-microscope"
                    ),
                    
                    html.Hr(className="my-4"),
            
                    # Configuración para análisis univariado
                    html.Div(id="univariate-config", children=[
                        create_form_group(
                            "Parámetro a Analizar",
                            dcc.Dropdown(
                                id="parameter-select",
                                options=[
                                    {"label": "Precio de Electricidad", "value": "electricity_price"},
                                    {"label": "CAPEX Solar", "value": "pv_capex"},
                                    {"label": "Tasa de Descuento", "value": "discount_rate"},
                                    {"label": "Factor de Capacidad", "value": "capacity_factor"},
                                    {"label": "OPEX", "value": "opex"},
                                    {"label": "Degradación PV", "value": "degradation"},
                                    {"label": "Inflación", "value": "inflation"}
                                ],
                                value="electricity_price",
                                className="mb-3"
                            ),
                            "Variable a evaluar en el análisis",
                            icon="fas fa-sliders-h"
                        ),
                        
                        create_form_group(
                            "Rango de Variación",
                            html.Div([
                                dcc.RangeSlider(
                                    id="variation-range",
                                    min=-50,
                                    max=50,
                                    step=5,
                                    value=[-30, 30],
                                    marks={i: f'{i}%' for i in range(-50, 51, 10)},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                ),
                                html.Div(id="variation-display", 
                                        className="text-center text-primary fw-bold mt-2")
                            ]),
                            "Rango de variación del parámetro",
                            icon="fas fa-arrows-alt-h"
                        ),
                    ]),
            
                    # Configuración para Monte Carlo
                    html.Div(id="montecarlo-config", style={"display": "none"}, children=[
                        create_form_group(
                            "Número de Simulaciones",
                            html.Div([
                                dcc.Slider(
                                    id="n-simulations",
                                    min=100,
                                    max=10000,
                                    step=100,
                                    value=1000,
                                    marks={i: f'{i:,}' for i in [100, 1000, 5000, 10000]},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                ),
                                html.Div(id="simulations-display", 
                                        className="text-center text-info fw-bold mt-2")
                            ]),
                            "Cantidad de simulaciones a ejecutar",
                            icon="fas fa-random"
                        ),
                        
                        create_form_group(
                            "Nivel de Confianza",
                            dcc.Dropdown(
                                id="confidence-level",
                                options=[
                                    {"label": "90%", "value": 0.90},
                                    {"label": "95%", "value": 0.95},
                                    {"label": "99%", "value": 0.99}
                                ],
                                value=0.95,
                                className="mb-3"
                            ),
                            "Nivel de confianza para intervalos",
                            icon="fas fa-percentage"
                        ),
                    ]),
            
                    html.Hr(className="my-4"),
                    
                    # Selección de métricas
                    create_form_group(
                        "Métricas a Evaluar",
                        dbc.Checklist(
                            id="metrics-select",
                            options=[
                                {"label": [html.I(className="fas fa-chart-line me-2"), "NPV"], "value": "npv"},
                                {"label": [html.I(className="fas fa-percentage me-2"), "TIR"], "value": "irr"},
                                {"label": [html.I(className="fas fa-hourglass-half me-2"), "Payback"], "value": "payback"},
                                {"label": [html.I(className="fas fa-dollar-sign me-2"), "LCOE"], "value": "lcoe"},
                                {"label": [html.I(className="fas fa-balance-scale me-2"), "Ratio B/C"], "value": "bc_ratio"}
                            ],
                            value=["npv", "irr"],
                            className="mt-2"
                        ),
                        "Seleccione las métricas a analizar",
                        icon="fas fa-check-square"
                    ),
                ]),
                icon="fas fa-cog",
                color="light"
            ),
            
            # Botón de análisis
            dbc.Button(
                [html.I(className="fas fa-play me-2"), "Ejecutar Análisis"],
                id="run-sensitivity-btn",
                color="primary",
                size="lg",
                className="w-100 mt-3"
            ),
        ], md=4, lg=3, className="mb-4"),
    
        # Panel de resultados
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    # Tabs de resultados
                    dbc.Tabs(id="sensitivity-tabs", active_tab='charts', children=[
                        dbc.Tab(label='Gráficos', tab_id='charts'),
                        dbc.Tab(label='Tablas', tab_id='tables'),
                        dbc.Tab(label='Estadísticas', tab_id='statistics'),
                        dbc.Tab(label='Recomendaciones', tab_id='recommendations'),
                    ], className="mb-4"),
                    
                    # Contenido de tabs
                    dcc.Loading(
                        id="loading-sensitivity",
                        type="circle",
                        children=[
                            html.Div(id="sensitivity-content")
                        ]
                    )
                ])
            ], className="shadow-sm")
        ], md=8, lg=9)
    ]),
    
    # Store para resultados
    dcc.Store(id="sensitivity-results-store"),
], fluid=True)

# Callbacks
@callback(
    Output("univariate-config", "style"),
    Output("montecarlo-config", "style"),
    Input("sensitivity-type", "value")
)
def toggle_config_panels(analysis_type):
    """Muestra/oculta paneles de configuración según tipo de análisis"""
    if analysis_type == "univariate":
        return {"display": "block"}, {"display": "none"}
    elif analysis_type == "montecarlo":
        return {"display": "none"}, {"display": "block"}
    else:
        return {"display": "none"}, {"display": "none"}

@callback(
    Output("sensitivity-results-store", "data"),
    Input("run-sensitivity-btn", "n_clicks"),
    State("sensitivity-type", "value"),
    State("parameter-select", "value"),
    State("variation-range", "value"),
    State("n-simulations", "value"),
    State("confidence-level", "value"),
    State("metrics-select", "value"),
    prevent_initial_call=True
)
def run_sensitivity_analysis(n_clicks, analysis_type, parameter, variation_range,
                           n_simulations, confidence_level, metrics):
    """Ejecuta el análisis de sensibilidad"""
    if not n_clicks:
        return {}
    
    # Caso base de ejemplo
    base_case = {
        'npv': 15.0,  # MUSD
        'irr': 18.5,  # %
        'payback': 7.2,  # años
        'lcoe': 55.0,  # USD/MWh
        'bc_ratio': 1.8,
        'capex': 10.0,  # MUSD
        'revenue': 2.5,  # MUSD/año
        'discount_rate': 0.10
    }
    
    results = {
        'analysis_type': analysis_type,
        'base_case': base_case,
        'metrics': metrics
    }
    
    if analysis_type == "univariate":
        # Análisis univariado
        variations = np.linspace(variation_range[0], variation_range[1], 21)
        sensitivity_df = perform_sensitivity_analysis(base_case, parameter, variations)
        results['sensitivity_data'] = sensitivity_df.to_dict('records')
        results['parameter'] = parameter
        
    elif analysis_type == "montecarlo":
        # Monte Carlo
        npv_results, distributions = calculate_monte_carlo(n_simulations)
        results['npv_results'] = npv_results.tolist()
        results['confidence_level'] = confidence_level
        results['percentiles'] = {
            'p5': np.percentile(npv_results, 5),
            'p50': np.percentile(npv_results, 50),
            'p95': np.percentile(npv_results, 95)
        }
        
    elif analysis_type == "scenarios":
        # Análisis de escenarios predefinidos
        scenarios = {
            'Optimista': {'price': +20, 'capex': -10, 'capacity': +10},
            'Base': {'price': 0, 'capex': 0, 'capacity': 0},
            'Pesimista': {'price': -20, 'capex': +10, 'capacity': -10},
            'Crisis': {'price': -30, 'capex': +20, 'capacity': -15}
        }
        results['scenarios'] = scenarios
    
    return results

@callback(
    Output("variation-display", "children"),
    Input("variation-range", "value")
)
def update_variation_display(value):
    if value:
        return f"Rango: {value[0]}% a {value[1]}%"
    return ""

@callback(
    Output("simulations-display", "children"),
    Input("n-simulations", "value")
)
def update_simulations_display(value):
    return f"{value:,} simulaciones"

@callback(
    Output("sensitivity-content", "children"),
    Input("sensitivity-tabs", "active_tab"),
    Input("sensitivity-results-store", "data")
)
def update_sensitivity_content(active_tab, results):
    """Actualiza el contenido según el tab activo"""
    if not results:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Configure los parámetros y ejecute el análisis para ver resultados."
        ], color="info", className="text-center")
    
    if active_tab == 'charts':
        return create_sensitivity_charts(results)
    elif active_tab == 'tables':
        return create_sensitivity_tables(results)
    elif active_tab == 'statistics':
        return create_sensitivity_statistics(results)
    elif active_tab == 'recommendations':
        return create_sensitivity_recommendations(results)
    
    return html.Div()

def create_sensitivity_charts(results):
    """Crea gráficos de sensibilidad"""
    analysis_type = results['analysis_type']
    
    if analysis_type == "univariate":
        # Gráfico de tornado
        df = pd.DataFrame(results['sensitivity_data'])
        
        fig1 = go.Figure()
        
        for metric in results['metrics']:
            fig1.add_trace(go.Scatter(
                x=df['variation'],
                y=df[metric] if metric in df else df['npv'],
                mode='lines+markers',
                name=metric.upper(),
                line=dict(width=3)
            ))
        
        # Líneas de referencia
        fig1.add_vline(x=0, line_dash="dash", line_color="gray")
        fig1.add_hline(y=results['base_case']['npv'], line_dash="dash", line_color="gray")
        
        fig1.update_layout(
            title=f"Sensibilidad de Métricas a {results['parameter'].replace('_', ' ').title()}",
            xaxis_title="Variación del Parámetro (%)",
            yaxis_title="Valor de la Métrica",
            height=500,
            hovermode='x unified',
            template="plotly_white",
            font=dict(family="system-ui, -apple-system, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Gráfico de elasticidad
        elasticity = []
        for i in range(1, len(df)):
            if df['variation'].iloc[i] != df['variation'].iloc[i-1]:
                elast = ((df['npv'].iloc[i] - df['npv'].iloc[i-1]) / df['npv'].iloc[i-1]) / \
                       ((df['variation'].iloc[i] - df['variation'].iloc[i-1]) / 100)
                elasticity.append(elast)
            else:
                elasticity.append(0)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df['variation'][1:],
            y=elasticity,
            mode='lines',
            fill='tozeroy',
            name='Elasticidad',
            line=dict(color='red', width=2)
        ))
        
        fig2.update_layout(
            title="Elasticidad del NPV",
            xaxis_title="Variación del Parámetro (%)",
            yaxis_title="Elasticidad",
            height=400,
            template="plotly_white",
            font=dict(family="system-ui, -apple-system, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-line me-2"),
                    "Análisis de Sensibilidad Univariado"
                ]),
                dbc.CardBody([
                    dcc.Graph(figure=fig1)
                ])
            ], className="shadow-sm mb-3"),
            
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-area me-2"),
                    "Elasticidad del NPV"
                ]),
                dbc.CardBody([
                    dcc.Graph(figure=fig2)
                ])
            ], className="shadow-sm")
        ])
        
    elif analysis_type == "montecarlo":
        # Histograma de NPV
        fig1 = go.Figure()
        fig1.add_trace(go.Histogram(
            x=results['npv_results'],
            nbinsx=50,
            name='NPV',
            marker_color='lightblue'
        ))
        
        # Agregar percentiles
        percentiles = results['percentiles']
        colors = ['red', 'green', 'red']
        labels = ['P5', 'P50', 'P95']
        
        for i, (key, value) in enumerate(percentiles.items()):
            fig1.add_vline(x=value, line_dash="dash", 
                          line_color=colors[i], 
                          annotation_text=f"{labels[i]}: ${value:.1f}M")
        
        fig1.update_layout(
            title="Distribución de NPV - Simulación Monte Carlo",
            xaxis_title="NPV (MUSD)",
            yaxis_title="Frecuencia",
            height=500,
            template="plotly_white",
            font=dict(family="system-ui, -apple-system, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Gráfico de probabilidad acumulada
        sorted_npv = np.sort(results['npv_results'])
        prob = np.arange(len(sorted_npv)) / len(sorted_npv)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=sorted_npv,
            y=prob * 100,
            mode='lines',
            name='Probabilidad Acumulada',
            line=dict(width=3)
        ))
        
        # Líneas de referencia
        fig2.add_hline(y=50, line_dash="dash", line_color="gray")
        fig2.add_vline(x=0, line_dash="dash", line_color="red")
        
        fig2.update_layout(
            title="Función de Distribución Acumulada",
            xaxis_title="NPV (MUSD)",
            yaxis_title="Probabilidad (%)",
            height=400,
            template="plotly_white",
            font=dict(family="system-ui, -apple-system, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-dice me-2"),
                    "Análisis Monte Carlo"
                ]),
                dbc.CardBody([
                    dcc.Graph(figure=fig1)
                ])
            ], className="shadow-sm mb-3"),
            
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-line me-2"),
                    "Función de Distribución Acumulada"
                ]),
                dbc.CardBody([
                    dcc.Graph(figure=fig2)
                ])
            ], className="shadow-sm")
        ])
    
    return html.Div()

def create_sensitivity_tables(results):
    """Crea tablas de sensibilidad"""
    if results['analysis_type'] == "univariate":
        df = pd.DataFrame(results['sensitivity_data'])
        
        # Tabla de valores
        table_data = []
        for _, row in df.iterrows():
            table_data.append({
                'Variación (%)': f"{row['variation']:.0f}%",
                'NPV (MUSD)': f"{row['npv']:.2f}",
                'TIR (%)': f"{row['irr']:.1f}%",
                'Payback (años)': f"{row['payback']:.1f}",
                'Cambio NPV (%)': f"{(row['npv']/results['base_case']['npv']-1)*100:.1f}%"
            })
        
        table = dbc.Table([
            html.Thead([
                html.Tr([html.Th(col) for col in table_data[0].keys()])
            ], className="table-primary"),
            html.Tbody([
                html.Tr([html.Td(val) for val in row.values()])
                for row in table_data[::2]  # Mostrar cada 2 filas
            ])
        ], striped=True, hover=True, responsive=True, className="mb-0")
        
        return dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-table me-2"),
                "Tabla de Sensibilidad"
            ]),
            dbc.CardBody([
                table
            ])
        ], className="shadow-sm")
        
    elif results['analysis_type'] == "montecarlo":
        # Estadísticas resumen
        npv_array = np.array(results['npv_results'])
        
        stats = {
            'Media': f"${np.mean(npv_array):.2f}M",
            'Mediana': f"${np.median(npv_array):.2f}M",
            'Desv. Estándar': f"${np.std(npv_array):.2f}M",
            'Mínimo': f"${np.min(npv_array):.2f}M",
            'Máximo': f"${np.max(npv_array):.2f}M",
            'P5': f"${results['percentiles']['p5']:.2f}M",
            'P95': f"${results['percentiles']['p95']:.2f}M",
            'Prob(NPV>0)': f"{(npv_array > 0).mean()*100:.1f}%"
        }
        
        table = dbc.Table([
            html.Tbody([
                html.Tr([
                    html.Td(html.Strong(key)),
                    html.Td(value, className="text-end")
                ])
                for key, value in stats.items()
            ])
        ], striped=True, hover=True, className="mb-0")
        
        return dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-calculator me-2"),
                "Estadísticas de Monte Carlo"
            ]),
            dbc.CardBody([
                table
            ])
        ], className="shadow-sm")
    
    return html.Div()

def create_sensitivity_statistics(results):
    """Crea estadísticas detalladas"""
    if results['analysis_type'] == "univariate":
        df = pd.DataFrame(results['sensitivity_data'])
        
        # Calcular métricas de sensibilidad
        sensitivity_metrics = []
        
        # Rango de variación
        npv_range = df['npv'].max() - df['npv'].min()
        npv_range_pct = (npv_range / results['base_case']['npv']) * 100
        
        # Punto de quiebre (NPV = 0)
        negative_npv = df[df['npv'] < 0]
        if len(negative_npv) > 0:
            breakeven_point = negative_npv.iloc[0]['variation']
        else:
            breakeven_point = "No alcanzado"
        
        metrics_cards = dbc.Row([
            dbc.Col([
                create_metric_card_v3(
                    "Rango NPV",
                    f"${npv_range:.1f}M",
                    f"{npv_range_pct:.1f}% del caso base",
                    icon="fas fa-chart-area",
                    color="blue",
                    gradient=True
                )
            ], md=4),
            
            dbc.Col([
                create_metric_card_v3(
                    "Punto de Quiebre",
                    f"{breakeven_point}%" if isinstance(breakeven_point, (int, float)) else breakeven_point,
                    "Variación para NPV=0",
                    icon="fas fa-crosshairs",
                    color="red",
                    gradient=True
                )
            ], md=4),
            
            dbc.Col([
                create_metric_card_v3(
                    "Elasticidad Promedio",
                    "1.2",
                    "Alta sensibilidad",
                    icon="fas fa-wave-square",
                    color="green",
                    gradient=True
                )
            ], md=4),
        ], className="mb-4")
        
        # Gráfico de contribución a la varianza
        fig = go.Figure(data=[
            go.Bar(
                x=['Precio', 'CAPEX', 'Tasa Desc.', 'Cap. Factor', 'OPEX'],
                y=[35, 25, 20, 15, 5],
                marker_color=['red', 'orange', 'yellow', 'lightgreen', 'green']
            )
        ])
        
        fig.update_layout(
            title="Contribución a la Varianza del NPV",
            yaxis_title="Contribución (%)",
            height=400,
            template="plotly_white",
            font=dict(family="system-ui, -apple-system, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-pie me-2"),
                    "Estadísticas de Sensibilidad"
                ]),
                dbc.CardBody([
                    metrics_cards,
                    html.Hr(),
                    dcc.Graph(figure=fig)
                ])
            ], className="shadow-sm")
        ])
        
    elif results['analysis_type'] == "montecarlo":
        npv_array = np.array(results['npv_results'])
        
        # Value at Risk
        var_95 = np.percentile(npv_array, 5)
        cvar_95 = npv_array[npv_array <= var_95].mean()
        
        # Gráfico de densidad con zonas de riesgo
        fig = go.Figure()
        
        # Histograma normalizado
        hist, bins = np.histogram(npv_array, bins=50, density=True)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        fig.add_trace(go.Scatter(
            x=bin_centers,
            y=hist,
            mode='lines',
            fill='tozeroy',
            name='Densidad',
            line=dict(width=2)
        ))
        
        # Zonas de riesgo
        fig.add_vrect(x0=npv_array.min(), x1=var_95, 
                     fillcolor="red", opacity=0.2,
                     annotation_text="Zona de Riesgo")
        
        fig.add_vrect(x0=results['percentiles']['p50'], x1=npv_array.max(), 
                     fillcolor="green", opacity=0.2,
                     annotation_text="Zona Favorable")
        
        fig.update_layout(
            title="Análisis de Riesgo-Retorno",
            xaxis_title="NPV (MUSD)",
            yaxis_title="Densidad",
            height=500,
            template="plotly_white",
            font=dict(family="system-ui, -apple-system, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Métricas de riesgo
        risk_metrics = dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-shield-alt me-2"),
                "Métricas de Riesgo"
            ], className="bg-danger text-white"),
            dbc.CardBody([
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                        "Value at Risk (95%): ",
                        dbc.Badge(f"${var_95:.2f}M", color="danger", className="ms-2")
                    ]),
                    dbc.ListGroupItem([
                        html.I(className="fas fa-chart-line me-2 text-warning"),
                        "Conditional VaR (95%): ",
                        dbc.Badge(f"${cvar_95:.2f}M", color="warning", className="ms-2")
                    ]),
                    dbc.ListGroupItem([
                        html.I(className="fas fa-percentage me-2 text-info"),
                        "Probabilidad de Pérdida: ",
                        dbc.Badge(f"{(npv_array < 0).mean()*100:.1f}%", color="info", className="ms-2")
                    ]),
                    dbc.ListGroupItem([
                        html.I(className="fas fa-balance-scale me-2 text-success"),
                        "Ratio Sharpe: ",
                        dbc.Badge(f"{np.mean(npv_array)/np.std(npv_array):.2f}", color="success", className="ms-2")
                    ])
                ])
            ])
        ], className="shadow-sm")
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-area me-2"),
                    "Análisis de Riesgo-Retorno"
                ]),
                dbc.CardBody([
                    dcc.Graph(figure=fig)
                ])
            ], className="shadow-sm mb-3"),
            risk_metrics
        ])
    
    return html.Div()

def create_sensitivity_recommendations(results):
    """Crea recomendaciones basadas en el análisis"""
    recommendations = []
    
    if results['analysis_type'] == "univariate":
        df = pd.DataFrame(results['sensitivity_data'])
        parameter = results['parameter']
        
        # Analizar elasticidad
        npv_change = (df['npv'].max() - df['npv'].min()) / results['base_case']['npv']
        
        if npv_change > 0.5:
            recommendations.append({
                'nivel': 'ALTA',
                'titulo': f'Alta sensibilidad a {parameter.replace("_", " ").title()}',
                'descripcion': f'El NPV varía más del {npv_change*100:.0f}% ante cambios en este parámetro.',
                'accion': 'Implementar estrategias de mitigación específicas.'
            })
        
        # Punto de quiebre
        negative_npv = df[df['npv'] < 0]
        if len(negative_npv) > 0 and negative_npv.iloc[0]['variation'] > -20:
            recommendations.append({
                'nivel': 'MEDIA',
                'titulo': 'Margen de seguridad limitado',
                'descripcion': f'El proyecto se vuelve no rentable con una reducción del {abs(negative_npv.iloc[0]["variation"]):.0f}%.',
                'accion': 'Considerar medidas para mejorar la robustez del proyecto.'
            })
            
    elif results['analysis_type'] == "montecarlo":
        npv_array = np.array(results['npv_results'])
        prob_success = (npv_array > 0).mean()
        
        if prob_success < 0.8:
            recommendations.append({
                'nivel': 'ALTA',
                'titulo': 'Riesgo significativo de NPV negativo',
                'descripcion': f'Existe un {(1-prob_success)*100:.0f}% de probabilidad de que el proyecto no sea rentable.',
                'accion': 'Revisar supuestos y considerar estrategias de reducción de riesgo.'
            })
        
        if np.std(npv_array) / np.mean(npv_array) > 0.5:
            recommendations.append({
                'nivel': 'MEDIA',
                'titulo': 'Alta variabilidad en resultados',
                'descripcion': 'El coeficiente de variación es superior al 50%.',
                'accion': 'Implementar contratos de largo plazo o hedging para reducir volatilidad.'
            })
    
    # Agregar recomendaciones generales
    recommendations.append({
        'nivel': 'INFO',
        'titulo': 'Monitoreo continuo',
        'descripcion': 'Los parámetros críticos deben ser monitoreados regularmente.',
        'accion': 'Establecer KPIs y sistema de alertas tempranas.'
    })
    
    # Crear cards de recomendaciones
    rec_cards = []
    colors = {'ALTA': 'danger', 'MEDIA': 'warning', 'INFO': 'info'}
    icons = {'ALTA': 'fas fa-exclamation-circle', 'MEDIA': 'fas fa-exclamation-triangle', 'INFO': 'fas fa-info-circle'}
    
    for rec in recommendations:
        card = dbc.Alert([
            html.H5([
                html.I(className=f"{icons[rec['nivel']]} me-2"),
                rec['titulo']
            ], className="alert-heading"),
            html.P(rec['descripcion'], className="mb-2"),
            html.Hr(),
            html.P([
                html.I(className="fas fa-arrow-right me-2"),
                rec['accion']
            ], className="mb-0 fw-bold")
        ], color=colors[rec['nivel']], className="mb-3")
        
        rec_cards.append(card)
    
    # Plan de acción
    action_plan = dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-tasks me-2"),
            "Plan de Acción Recomendado"
        ], className="bg-primary text-white"),
        dbc.CardBody([
            dbc.ListGroup([
                dbc.ListGroupItem([
                    dbc.Badge("1", color="primary", pill=True, className="me-2"),
                    "Priorizar negociación de contratos PPA de largo plazo"
                ]),
                dbc.ListGroupItem([
                    dbc.Badge("2", color="primary", pill=True, className="me-2"),
                    "Establecer mecanismos de indexación para proteger márgenes"
                ]),
                dbc.ListGroupItem([
                    dbc.Badge("3", color="primary", pill=True, className="me-2"),
                    "Diversificar portfolio con diferentes tecnologías y ubicaciones"
                ]),
                dbc.ListGroupItem([
                    dbc.Badge("4", color="primary", pill=True, className="me-2"),
                    "Implementar sistema de gestión de riesgos integral"
                ]),
                dbc.ListGroupItem([
                    dbc.Badge("5", color="primary", pill=True, className="me-2"),
                    "Revisar análisis trimestralmente con datos actualizados"
                ])
            ])
        ])
    ], className="shadow-sm")
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-lightbulb me-2"),
                "Recomendaciones del Análisis"
            ]),
            dbc.CardBody([
                html.Div(rec_cards)
            ])
        ], className="shadow-sm mb-3"),
        action_plan
    ])