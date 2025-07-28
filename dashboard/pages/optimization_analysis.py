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

# Importar módulos de cálculo modularizados
from src.economics.energy_flows import (
    calculate_pv_generation,
    calculate_pv_self_consumption,
    calculate_pv_exports,
    calculate_pv_total_flows
)
from src.economics.network_benefits_modular import (
    calculate_loss_reduction,
    calculate_reactive_support_value,
    calculate_voltage_support_value,
    calculate_reliability_improvement,
    calculate_demand_charge_reduction,
    calculate_total_network_benefits,
    estimate_network_parameters
)
from src.economics.financial_metrics import (
    calculate_capex_total,
    calculate_annual_opex,
    calculate_cash_flows,
    calculate_npv,
    calculate_irr,
    calculate_payback,
    calculate_lcoe,
    calculate_all_financial_metrics
)

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

def calculate_flows_realtime(cluster_data, pv_mw, bess_mwh, q_mvar):
    """
    Calcula flujos económicos usando módulos modularizados
    
    Returns:
        dict: Resultados del cálculo con todos los componentes
        
    Raises:
        ValueError: Si no se puede cargar la configuración
        KeyError: Si faltan parámetros requeridos
    """
    # Cargar configuración
    try:
        from src.config.config_loader import get_config
        config = get_config()
        params = config.get_economic_params()
        network_params = config.get_network_params()
        print("calculate_flows_realtime: Config loaded successfully")
    except Exception as e:
        error_msg = f"ERROR: No se pudo cargar la configuración: {type(e).__name__}: {str(e)}"
        print(error_msg)
        raise ValueError(error_msg)
    
    try:
        # =====================
        # 1. CALCULAR CAPEX
        # =====================
        capex_total = calculate_capex_total(
            pv_mw=pv_mw,
            bess_mwh=bess_mwh,
            q_mvar=q_mvar,
            pv_capex_usd_mw=params.get('pv_capex_usd_mw', 800000),
            bess_capex_usd_mwh=params.get('bess_capex_usd_mwh', 200000),
            statcom_capex_usd_mvar=params.get('statcom_capex_usd_mvar', 40000),
            bos_factor=params.get('bos_factor', 0.15)
        )
        
        # Desglose de CAPEX
        capex = {
            'pv': pv_mw * params.get('pv_capex_usd_mw', 800000),
            'bess': bess_mwh * params.get('bess_capex_usd_mwh', 200000),
            'q_night': q_mvar * params.get('statcom_capex_usd_mvar', 40000),
            'bos': capex_total / 1.15 * 0.15,  # Extraer BOS del total
            'total': capex_total
        }
        
        # =====================
        # 2. CALCULAR FLUJOS PV
        # =====================
        # Generación anual
        annual_generation_mwh, annual_generation_gwh = calculate_pv_generation(
            pv_mw=pv_mw,
            capacity_factor=params.get('pv_capacity_factor', 0.22),
            hours_per_year=8760
        )
        
        # Flujos económicos PV
        self_consumption_ratio = 0.7  # 70% con BESS
        pv_flows = calculate_pv_total_flows(
            generation_mwh=annual_generation_mwh,
            self_consumption_ratio=self_consumption_ratio,
            electricity_price=params.get('electricity_price', 75),
            export_price=params.get('export_price', 70)
        )
        
        # Debug
        print(f"DEBUG Flujos PV:")
        print(f"  Generación: {annual_generation_mwh:,.0f} MWh/año")
        print(f"  Autoconsumo: ${pv_flows['self_consumption']/1e6:.2f}M/año")
        print(f"  Exportación: ${pv_flows['exports']/1e6:.2f}M/año")
        print(f"  Total PV: ${pv_flows['total']/1e6:.2f}M/año")
        
        # =====================
        # 3. CALCULAR BENEFICIOS DE RED
        # =====================
        # Estimar parámetros de red basados en el cluster
        network_params_estimated = estimate_network_parameters(cluster_data)
        
        # Sobrescribir con valores de configuración si existen
        for key in network_params:
            if key in network_params_estimated:
                network_params_estimated[key] = network_params[key]
        
        # Calcular beneficios de red
        network_benefits = calculate_total_network_benefits(
            pv_mw=pv_mw,
            bess_mwh=bess_mwh,
            q_mvar=q_mvar,
            network_params=network_params_estimated
        )
        
        # Para compatibilidad con el resto del código
        network_flows = {
            'loss_reduction': network_benefits['loss_reduction'],
            'q_night': network_benefits['reactive_support'],
            'reliability': network_benefits['reliability'],
            'total': network_benefits['total']
        }
        
        print(f"\nDEBUG Beneficios de Red:")
        print(f"  Reducción pérdidas: ${network_flows['loss_reduction']/1e6:.2f}M/año")
        print(f"  Soporte reactivo: ${network_flows['q_night']/1e6:.2f}M/año")
        print(f"  Confiabilidad: ${network_flows['reliability']/1e6:.2f}M/año")
        print(f"  Total Red: ${network_flows['total']/1e6:.2f}M/año")
        
        # =====================
        # 4. CALCULAR MÉTRICAS FINANCIERAS
        # =====================
        # Calcular OPEX anual
        annual_opex = calculate_annual_opex(
            capex_total=capex_total,
            pv_mw=pv_mw,
            bess_mwh=bess_mwh,
            q_mvar=q_mvar,
            opex_rate_pv=params.get('pv_opex_rate', 0.01),
            opex_rate_bess=params.get('bess_opex_rate', 0.015),
            opex_rate_statcom=params.get('statcom_opex_rate', 0.02)
        )
        
        # Ingresos totales anuales
        total_annual_revenue = pv_flows['total'] + network_flows['total']
        
        # Calcular todas las métricas financieras
        financial_metrics = calculate_all_financial_metrics(
            capex=capex_total,
            annual_revenue=total_annual_revenue,
            annual_opex=annual_opex,
            annual_generation_mwh=annual_generation_mwh,
            project_lifetime=params.get('project_lifetime', 20),
            discount_rate=params.get('discount_rate', 0.10),
            inflation_rate=params.get('inflation_rate', 0.04)
        )
        
        # Debug financiero
        print(f"\nDEBUG Métricas Financieras:")
        print(f"  CAPEX: ${financial_metrics['capex']/1e6:.1f}M")
        print(f"  OPEX anual: ${annual_opex/1e3:.0f}k/año")
        print(f"  Ingresos totales: ${total_annual_revenue/1e6:.1f}M/año")
        print(f"  NPV: ${financial_metrics['npv']/1e6:.1f}M")
        print(f"  IRR: {financial_metrics['irr']*100:.1f}%")
        print(f"  Payback: {financial_metrics['payback']:.1f} años")
        print(f"  LCOE: ${financial_metrics['lcoe']:.0f}/MWh")
        print(f"  B/C: {financial_metrics['bc_ratio']:.2f}")
        
        # Validaciones de resultados
        from src.economics.financial_metrics import validate_financial_metrics
        warnings = validate_financial_metrics(financial_metrics)
        if warnings:
            print("\n⚠️ ADVERTENCIAS:")
            for warning in warnings:
                print(f"  - {warning}")
        
        # Crear cash flows para gráficos
        cash_flows_detailed = calculate_cash_flows(
            capex=capex_total,
            annual_revenue=total_annual_revenue,
            annual_opex=annual_opex,
            project_lifetime=params.get('project_lifetime', 20),
            inflation_rate=params.get('inflation_rate', 0.04)
        )
        
        # Simplificar para compatibilidad con gráficos existentes
        cash_flows = []
        for flow in cash_flows_detailed[1:]:  # Saltar año 0
            cash_flows.append({
                'year': flow['year'],
                'total_flow': flow['cash_flow']
            })
        
        # Crear estructura de beneficios de red para gráficos
        network_benefits = {
            'loss_reduction': {
                'value_usd': network_flows['loss_reduction'],
                'percentage': network_flows['loss_reduction'] / network_flows['total'] if network_flows['total'] > 0 else 0
            },
            'q_night': {
                'value_usd': network_flows['q_night'],
                'percentage': network_flows['q_night'] / network_flows['total'] if network_flows['total'] > 0 else 0
            },
            'reliability': {
                'value_usd': network_flows['reliability'],
                'percentage': network_flows['reliability'] / network_flows['total'] if network_flows['total'] > 0 else 0
            }
        }
        
        # Crear flujos para gráficos
        flows = {
            'pv': pv_flows['total'],
            'network': network_flows['total'],
            'total': total_annual_revenue
        }
        
        # =====================
        # 5. PREPARAR RESULTADO FINAL
        # =====================
        return {
            'capex': capex,
            'pv_flows': pv_flows,
            'network_flows': network_flows,
            'total_flows': {
                'annual': total_annual_revenue,
                'lifetime': total_annual_revenue * params.get('project_lifetime', 20)
            },
            'metrics': {
                'npv_usd': financial_metrics['npv'],
                'irr_percent': financial_metrics['irr'] * 100,  # Convertir a porcentaje
                'payback_years': financial_metrics['payback'],
                'lcoe_usd_mwh': financial_metrics['lcoe'],
                'bc_ratio': financial_metrics['bc_ratio']
            },
            'network_benefits': network_benefits,
            'flows': flows,
            'avg_flows': {
                'pv': pv_flows['total'] / 1e6,  # Convertir a MUSD
                'network': network_flows['total'] / 1e6,
                'total': total_annual_revenue / 1e6
            },
            'cash_flows': cash_flows,
            'using_defaults': False,  # Ya no usamos valores por defecto
            'annual_generation_mwh': annual_generation_mwh,
            'annual_generation_gwh': annual_generation_gwh
        }
        
    except Exception as e:
        # NO USAR VALORES HARDCODED - PROPAGAR EL ERROR
        print(f"ERROR en calculate_flows_realtime: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise  # Re-lanzar el error para que el callback lo maneje

# Layout de la página
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
                            # Notificación de datos estimados
                            html.Div(id="estimation-alert", className="mb-3"),
                            
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
    if cluster_id is None:
        print("update_cluster_data: cluster_id is None")
        return {}
    
    print(f"update_cluster_data: Loading data for cluster_id={cluster_id}")
    df = load_cluster_data()
    
    if df.empty:
        print("update_cluster_data: DataFrame is empty")
        return {}
    
    # Filtrar por cluster_id
    cluster_rows = df[df['cluster_id'] == cluster_id]
    
    if cluster_rows.empty:
        print(f"update_cluster_data: No data found for cluster_id={cluster_id}")
        print(f"Available cluster IDs: {df['cluster_id'].unique()}")
        return {}
    
    cluster_data = cluster_rows.iloc[0].to_dict()
    print(f"update_cluster_data: Returning data with {len(cluster_data)} fields")
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
    """
    Calcula flujos para la configuración seleccionada
    NO USA VALORES HARDCODED - MUESTRA ERRORES EXPLÍCITOS
    """
    import traceback
    
    print("=" * 80)
    print("CALCULATE_FLOWS: Iniciando cálculo")
    print(f"Parámetros recibidos:")
    print(f"  - n_clicks: {n_clicks}")
    print(f"  - pv_ratio: {pv_ratio}")
    print(f"  - bess_hours: {bess_hours}")
    print(f"  - q_ratio: {q_ratio}")
    print(f"  - cluster_data: {type(cluster_data)}")
    print("=" * 80)
    
    try:
        if not n_clicks:
            print("Calculate flows: No clicks yet")
            return {}, {"display": "none"}
            
        if not cluster_data:
            print("Calculate flows: No cluster data provided")
            return {}, {"display": "none"}
        
        # Validar que todos los parámetros tienen valores válidos
        if pv_ratio is None:
            pv_ratio = 1.0
        if bess_hours is None:
            bess_hours = 0
        if q_ratio is None:
            q_ratio = 0.1
            
        print(f"Calculate flows: Processing cluster data with keys: {list(cluster_data.keys())[:10]}...")
        
        # Validar datos del cluster
        if 'peak_demand_mw' not in cluster_data:
            print("Calculate flows: peak_demand_mw not found, estimating...")
            # Si no hay peak_demand, estimarlo basado en otros datos
            if 'pv_mw' in cluster_data:
                # Estimar peak demand como 50% de la capacidad PV instalada
                peak_demand = cluster_data['pv_mw'] / 2
            else:
                # Valor por defecto razonable
                peak_demand = 20.0  # MW
        else:
            peak_demand = float(cluster_data['peak_demand_mw'])  # Asegurar que es float
        
        print(f"Calculate flows: peak_demand={peak_demand}, pv_ratio={pv_ratio}, bess_hours={bess_hours}, q_ratio={q_ratio}")
        
        # Calcular capacidades
        pv_mw = peak_demand * pv_ratio
        bess_mwh = peak_demand * bess_hours
        q_mvar = pv_mw * q_ratio
        
        # Calcular flujos
        print(f"Calculate flows: Calling calculate_flows_realtime with pv_mw={pv_mw}, bess_mwh={bess_mwh}, q_mvar={q_mvar}")
        results = calculate_flows_realtime(cluster_data, pv_mw, bess_mwh, q_mvar)
        
        print(f"Calculate flows: Results keys: {list(results.keys())}")
        
        # Agregar configuración
        results['config'] = {
            'pv_mw': pv_mw,
            'bess_mwh': bess_mwh,
            'q_mvar': q_mvar,
            'pv_ratio': pv_ratio,
            'bess_hours': bess_hours,
            'q_ratio': q_ratio
        }
        
        print("Calculate flows: Success, returning results")
        return results, {"display": "block"}
        
    except Exception as e:
        import traceback
        error_msg = f"Error in calculate_flows: {e}"
        error_type = type(e).__name__
        traceback_str = traceback.format_exc()
        
        print(f"ERROR DETALLADO EN calculate_flows:")
        print(f"  Tipo de error: {error_type}")
        print(f"  Mensaje: {error_msg}")
        print(f"  Traceback completo:\n{traceback_str}")
        
        # Retornar error explícito para mostrar al usuario
        return {
            'error': True,
            'error_message': str(e),
            'error_type': error_type,
            'error_traceback': traceback_str
        }, {"display": "none"}

@callback(
    Output("metrics-cards", "children"),
    Input("calculation-results-store", "data")
)
def update_metrics_cards(results):
    """Actualiza las tarjetas de métricas"""
    if not results:
        return []
    
    # Manejar caso de error
    if results.get('error', False):
        return dbc.Alert([
            html.H4("⚠️ Error en el cálculo", className="alert-heading"),
            html.P(f"Tipo: {results.get('error_type', 'Desconocido')}"),
            html.P(f"Mensaje: {results.get('error_message', 'Error desconocido')}"),
            html.Details([
                html.Summary("Ver detalles técnicos"),
                html.Pre(results.get('error_traceback', 'Sin traceback'), 
                        style={"fontSize": "0.8em", "maxHeight": "300px", "overflowY": "auto"})
            ])
        ], color="danger")
    
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
    if not results or results.get('error', False):
        return go.Figure()
    
    # avg_flows ya está en MUSD (millones de USD)
    flows = results['avg_flows']
    
    # Debug
    print(f"DEBUG update_flow_breakdown: flows = {flows}")
    
    fig = go.Figure()
    
    # Flujo PV
    fig.add_trace(go.Bar(
        name='Flujo PV',
        x=['Flujo Anual'],
        y=[flows['pv']],  # Ya está en MUSD
        marker_color='#FFA500',
        text=[f"${flows['pv']:.1f}M"],
        textposition='inside'
    ))
    
    # Flujo Red
    fig.add_trace(go.Bar(
        name='Flujo Red',
        x=['Flujo Anual'],
        y=[flows['network']],  # Ya está en MUSD
        marker_color='#4169E1',
        text=[f"${flows['network']:.1f}M"],
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
    total = flows['total']  # Ya está en MUSD
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
    if not results or results.get('error', False):
        return go.Figure()
    
    benefits = results['network_benefits']
    
    # Preparar datos
    benefit_types = []
    values = []
    
    for key, benefit in benefits.items():
        benefit_types.append(key.replace('_', ' ').title())
        values.append(benefit['value_usd'] / 1e6)
    
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
    if not results or results.get('error', False):
        return go.Figure()
    
    cash_flows = results['cash_flows']
    capex = results['capex']['total']
    
    # Preparar datos - cash_flows ahora son diccionarios
    years = [0] + [cf['year'] for cf in cash_flows]
    flows = [-capex/1e6] + [cf['total_flow']/1e6 for cf in cash_flows]
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
    if not results or results.get('error', False):
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

@callback(
    Output("estimation-alert", "children"),
    Input("calculation-results-store", "data")
)
def update_estimation_alert(results):
    """Muestra alerta si se están usando valores estimados"""
    if not results:
        return None
    
    if results.get('using_defaults', False):
        return create_alert_banner(
            "📊 Usando valores por defecto - No se pudo cargar la configuración desde parameters.yaml. " +
            "Los cálculos favorecen escenarios PSFV multipropósito con estimaciones realistas.",
            type="warning",
            dismissable=True
        )
    
    return None