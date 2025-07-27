"""
Dashboard FASE 3: Configuración de Parámetros de Optimización
==========================================================
Permite ajustar parámetros económicos, técnicos y restricciones
para el análisis de flujos integrados.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import dash
from dash import dcc, html, dash_table, callback, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import json
from datetime import datetime

# Configuración de paths
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_FILE = BASE_DIR / "config" / "parameters.yaml"
DATA_DIR = BASE_DIR / "data" / "processed"
OPTIMIZATION_DIR = BASE_DIR / "reports" / "clustering" / "optimization"

# Importar config loader y componentes
import sys
sys.path.append(str(BASE_DIR))
from src.config.config_loader import get_config
from dashboard.components.optimization_components import (
    create_header_section, create_config_card, create_form_group,
    create_slider_with_value, create_metric_card_v3, create_alert_banner,
    COLORS
)

# Registrar página
dash.register_page(
    __name__,
    path='/optimization-config',
    name='Configuración Optimización',
    title='Configuración de Parámetros - FASE 3'
)

def load_current_config():
    """Carga la configuración actual desde el archivo YAML"""
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def save_config(config_data):
    """Guarda la configuración actualizada al archivo YAML"""
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

# Layout de la página
layout = dbc.Container([
    # Header
    create_header_section(
        "Configuración de Parámetros de Optimización",
        "Ajuste los parámetros económicos y técnicos para el análisis de flujos integrados",
        icon="fas fa-cogs"
    ),
    
    # Alert informativo
    create_alert_banner(
        "Los cambios en los parámetros se aplicarán a todos los análisis futuros. Los valores actuales provienen del archivo parameters.yaml",
        type="info",
        dismissable=True
    ),
    
    # Sección 1: Precios de Energía
    create_config_card(
        "Precios de Energía",
        dbc.Row([
            dbc.Col([
                create_form_group(
                    "Precio Promedio",
                    dbc.InputGroup([
                        dbc.InputGroupText("$", className="bg-light"),
                        dbc.Input(
                            id="electricity-price",
                            type="number",
                            placeholder="75.0"
                        ),
                        dbc.InputGroupText("/MWh", className="bg-light")
                    ]),
                    "Precio base de electricidad",
                    icon="fas fa-bolt"
                )
            ], md=4),
            
            dbc.Col([
                create_form_group(
                    "Tarifa Residencial",
                    dbc.InputGroup([
                        dbc.InputGroupText("$", className="bg-light"),
                        dbc.Input(
                            id="tariff-residential",
                            type="number",
                            placeholder="65.0"
                        ),
                        dbc.InputGroupText("/MWh", className="bg-light")
                    ]),
                    icon="fas fa-home"
                )
            ], md=4),
            
            dbc.Col([
                create_form_group(
                    "Tarifa Comercial",
                    dbc.InputGroup([
                        dbc.InputGroupText("$", className="bg-light"),
                        dbc.Input(
                            id="tariff-commercial",
                            type="number",
                            placeholder="85.0"
                        ),
                        dbc.InputGroupText("/MWh", className="bg-light")
                    ]),
                    icon="fas fa-building"
                )
            ], md=4),
            
            dbc.Col([
                create_form_group(
                    "Tarifa Industrial",
                    dbc.InputGroup([
                        dbc.InputGroupText("$", className="bg-light"),
                        dbc.Input(
                            id="tariff-industrial",
                            type="number",
                            placeholder="95.0"
                        ),
                        dbc.InputGroupText("/MWh", className="bg-light")
                    ]),
                    icon="fas fa-industry"
                )
            ], md=4),
            
            dbc.Col([
                create_form_group(
                    "Precio Exportación",
                    dbc.InputGroup([
                        dbc.InputGroupText("$", className="bg-light"),
                        dbc.Input(
                            id="export-price",
                            type="number",
                            placeholder="70.0"
                        ),
                        dbc.InputGroupText("/MWh", className="bg-light")
                    ]),
                    icon="fas fa-upload"
                )
            ], md=4),
            
            dbc.Col([
                create_form_group(
                    "Costo Energía Upstream",
                    dbc.InputGroup([
                        dbc.InputGroupText("$", className="bg-light"),
                        dbc.Input(
                            id="upstream-cost",
                            type="number",
                            placeholder="60.0"
                        ),
                        dbc.InputGroupText("/MWh", className="bg-light")
                    ]),
                    icon="fas fa-download"
                )
            ], md=4)
        ]),
        icon="fas fa-dollar-sign",
        color="light"
    ),
    
    # Sección 2: Costos CAPEX
    create_config_card(
        "Costos de Inversión (CAPEX)",
        dbc.Row([
            dbc.Col([
                create_form_group(
                    "Solar Fotovoltaico",
                    dbc.InputGroup([
                        dbc.InputGroupText("$", className="bg-light"),
                        dbc.Input(
                            id="pv-capex",
                            type="number",
                            placeholder="800,000"
                        ),
                        dbc.InputGroupText("/MW", className="bg-light")
                    ]),
                    "Costo de instalación solar",
                    icon="fas fa-solar-panel"
                )
            ], md=4),
            
            dbc.Col([
                create_form_group(
                    "Almacenamiento BESS",
                    dbc.InputGroup([
                        dbc.InputGroupText("$", className="bg-light"),
                        dbc.Input(
                            id="bess-capex-mwh",
                            type="number",
                            placeholder="200,000"
                        ),
                        dbc.InputGroupText("/MWh", className="bg-light")
                    ]),
                    "Costo de baterías",
                    icon="fas fa-battery-full"
                )
            ], md=4),
            
            dbc.Col([
                create_form_group(
                    "Compensación Reactiva",
                    dbc.InputGroup([
                        dbc.InputGroupText("$", className="bg-light"),
                        dbc.Input(
                            id="statcom-capex",
                            type="number",
                            placeholder="40,000"
                        ),
                        dbc.InputGroupText("/MVAr", className="bg-light")
                    ]),
                    "Costo de STATCOM",
                    icon="fas fa-charging-station"
                )
            ], md=4)
        ]),
        icon="fas fa-hard-hat",
        color="light"
    ),
    
    # Sección 3: Parámetros Financieros
    create_config_card(
        "Parámetros Financieros",
        html.Div([
            dbc.Row([
                dbc.Col([
                    create_form_group(
                        "Tasa de Descuento",
                        html.Div([
                            dcc.Slider(
                                id="discount-rate",
                                min=5,
                                max=20,
                                step=0.5,
                                value=10,
                                marks={i: f'{i}%' for i in range(5, 21, 5)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Div(id="discount-rate-value", className="text-center mt-2 text-primary fw-bold")
                        ]),
                        "WACC del proyecto",
                        icon="fas fa-percentage"
                    )
                ], md=12, className="mb-4"),
            ]),
            
            dbc.Row([
                dbc.Col([
                    create_form_group(
                        "Vida Útil del Proyecto",
                        html.Div([
                            dcc.Slider(
                                id="project-lifetime",
                                min=15,
                                max=30,
                                step=1,
                                value=25,
                                marks={i: f'{i}' for i in range(15, 31, 5)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Div(id="project-lifetime-value", className="text-center mt-2 text-success fw-bold")
                        ]),
                        "Período de evaluación",
                        icon="fas fa-calendar-alt"
                    )
                ], md=12, className="mb-4"),
            ]),
            
            dbc.Row([
                dbc.Col([
                    create_form_group(
                        "OPEX Solar",
                        html.Div([
                            dcc.Slider(
                                id="pv-opex-rate",
                                min=0.5,
                                max=3,
                                step=0.1,
                                value=1.0,
                                marks={i: f'{i}%' for i in range(0, 4)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Div(id="pv-opex-rate-value", className="text-center mt-2 text-warning fw-bold")
                        ]),
                        "Costos operativos anuales",
                        icon="fas fa-tools"
                    )
                ], md=12),
            ])
        ]),
        icon="fas fa-chart-line",
        color="light"
    ),
    
    # Sección 4: Restricciones de Optimización
    create_config_card(
        "Restricciones de Optimización",
        html.Div([
            dbc.Row([
                dbc.Col([
                    create_form_group(
                        "TIR Mínima",
                        dbc.InputGroup([
                            dbc.Input(
                                id="min-irr",
                                type="number",
                                value=15
                            ),
                            dbc.InputGroupText("%", className="bg-light")
                        ]),
                        "Rentabilidad mínima aceptable",
                        icon="fas fa-chart-pie"
                    )
                ], md=4),
                
                dbc.Col([
                    create_form_group(
                        "Payback Máximo",
                        dbc.InputGroup([
                            dbc.Input(
                                id="max-payback",
                                type="number",
                                value=10
                            ),
                            dbc.InputGroupText("años", className="bg-light")
                        ]),
                        "Período de recuperación",
                        icon="fas fa-hourglass-half"
                    )
                ], md=4),
                
                dbc.Col([
                    create_form_group(
                        "Ratio B/C Mínimo",
                        dbc.InputGroup([
                            dbc.Input(
                                id="min-bc-ratio",
                                type="number",
                                value=1.2,
                                step=0.1
                            ),
                            dbc.InputGroupText("x", className="bg-light")
                        ]),
                        "Beneficio/Costo mínimo",
                        icon="fas fa-balance-scale"
                    )
                ], md=4),
            ]),
            
            dbc.Row([
                dbc.Col([
                    create_form_group(
                        "Presupuesto Total Disponible",
                        dbc.InputGroup([
                            dbc.InputGroupText("$", className="bg-light"),
                            dbc.Input(
                                id="total-budget",
                                type="number",
                                placeholder="Sin restricción"
                            ),
                            dbc.InputGroupText("MUSD", className="bg-light")
                        ]),
                        "Dejar vacío para sin límite",
                        icon="fas fa-wallet"
                    )
                ], md=6, className="mt-3")
            ], justify="center")
        ]),
        icon="fas fa-filter",
        color="light"
    ),
    
    # Botones de acción
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button(
                            [html.I(className="fas fa-save me-2"), "Guardar Configuración"],
                            id="save-config-btn",
                            color="primary",
                            size="lg",
                            className="me-2"
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-undo me-2"), "Restaurar Por Defecto"],
                            id="reset-config-btn",
                            color="secondary",
                            outline=True,
                            size="lg",
                            className="me-2"
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-play me-2"), "Ejecutar Análisis"],
                            id="run-analysis-btn",
                            color="success",
                            size="lg"
                        ),
                    ])
                ], width=12, className="text-center")
            ])
        ])
    ], className="shadow-sm border-0 mb-4"),
    
    # Área de mensajes
    html.Div(id="config-message"),
    
    # Store para datos
    dcc.Store(id="current-config-store"),
], fluid=True)

# Callbacks
@callback(
    Output("current-config-store", "data"),
    Output("electricity-price", "value"),
    Output("tariff-residential", "value"),
    Output("tariff-commercial", "value"),
    Output("tariff-industrial", "value"),
    Output("export-price", "value"),
    Output("upstream-cost", "value"),
    Output("pv-capex", "value"),
    Output("bess-capex-mwh", "value"),
    Output("statcom-capex", "value"),
    Output("discount-rate", "value"),
    Output("project-lifetime", "value"),
    Output("pv-opex-rate", "value"),
    Output("min-irr", "value"),
    Output("max-payback", "value"),
    Output("min-bc-ratio", "value"),
    Input("config-message", "id")  # Trigger on load
)
def load_current_values(_):
    """Carga los valores actuales de configuración"""
    config = load_current_config()
    
    return (
        config,
        config['energy_prices']['electricity_price'],
        config['energy_prices']['tariff_residential'],
        config['energy_prices']['tariff_commercial'],
        config['energy_prices']['tariff_industrial'],
        config['energy_prices']['export_price'],
        config['energy_prices']['upstream_energy_cost'],
        config['capex']['pv_capex_usd_mw'],
        config['capex']['bess_capex_usd_mwh'],
        config['capex']['statcom_capex_usd_mvar'],
        config['financial']['discount_rate'] * 100,
        config['financial']['project_lifetime'],
        config['opex']['pv_opex_rate'] * 100,
        config['optimization_constraints']['min_irr'] * 100,
        config['optimization_constraints']['max_payback'],
        config['optimization_constraints']['min_bc_ratio']
    )

# Callbacks para mostrar valores de sliders
@callback(
    Output("discount-rate-value", "children"),
    Input("discount-rate", "value")
)
def update_discount_rate_display(value):
    return f"{value}%"

@callback(
    Output("project-lifetime-value", "children"),
    Input("project-lifetime", "value")
)
def update_project_lifetime_display(value):
    return f"{value} años"

@callback(
    Output("pv-opex-rate-value", "children"),
    Input("pv-opex-rate", "value")
)
def update_pv_opex_rate_display(value):
    return f"{value}% CAPEX/año"

@callback(
    Output("config-message", "children"),
    Input("save-config-btn", "n_clicks"),
    State("electricity-price", "value"),
    State("tariff-residential", "value"),
    State("tariff-commercial", "value"),
    State("tariff-industrial", "value"),
    State("export-price", "value"),
    State("upstream-cost", "value"),
    State("pv-capex", "value"),
    State("bess-capex-mwh", "value"),
    State("statcom-capex", "value"),
    State("discount-rate", "value"),
    State("project-lifetime", "value"),
    State("pv-opex-rate", "value"),
    State("min-irr", "value"),
    State("max-payback", "value"),
    State("min-bc-ratio", "value"),
    State("current-config-store", "data"),
    prevent_initial_call=True
)
def save_configuration(n_clicks, electricity_price, tariff_res, tariff_com, tariff_ind,
                      export_price, upstream_cost, pv_capex, bess_capex, statcom_capex,
                      discount_rate, project_lifetime, pv_opex_rate,
                      min_irr, max_payback, min_bc_ratio, current_config):
    """Guarda la configuración actualizada"""
    if not n_clicks:
        return ""
    
    try:
        # Actualizar valores en la configuración
        current_config['energy_prices']['electricity_price'] = electricity_price
        current_config['energy_prices']['tariff_residential'] = tariff_res
        current_config['energy_prices']['tariff_commercial'] = tariff_com
        current_config['energy_prices']['tariff_industrial'] = tariff_ind
        current_config['energy_prices']['export_price'] = export_price
        current_config['energy_prices']['upstream_energy_cost'] = upstream_cost
        
        current_config['capex']['pv_capex_usd_mw'] = pv_capex
        current_config['capex']['bess_capex_usd_mwh'] = bess_capex
        current_config['capex']['statcom_capex_usd_mvar'] = statcom_capex
        
        current_config['financial']['discount_rate'] = discount_rate / 100
        current_config['financial']['project_lifetime'] = int(project_lifetime)
        current_config['opex']['pv_opex_rate'] = pv_opex_rate / 100
        
        current_config['optimization_constraints']['min_irr'] = min_irr / 100
        current_config['optimization_constraints']['max_payback'] = max_payback
        current_config['optimization_constraints']['min_bc_ratio'] = min_bc_ratio
        
        # Guardar al archivo
        save_config(current_config)
        
        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            "Configuración guardada exitosamente. ",
            html.Small(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        ], color="success", dismissable=True, className="mt-3")
        
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-circle me-2"),
            f"Error al guardar configuración: {str(e)}"
        ], color="danger", dismissable=True, className="mt-3")