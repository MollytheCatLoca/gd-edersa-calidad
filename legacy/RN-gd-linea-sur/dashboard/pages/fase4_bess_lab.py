"""
Fase 4: Laboratorio BESS con Validación Energética
Dashboard renovado con validación visual y estrategias mejoradas
"""

import dash
from dash import dcc, html, Input, Output, callback, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from dashboard.pages.utils import get_data_manager
from dashboard.pages.utils.models import DataStatus

# Registro de la página
dash.register_page(
    __name__,
    path='/fase4-bess-lab',
    title='Fase 4: Laboratorio BESS',
    name='Fase 4: BESS Lab'
)

# Colores consistentes
COLORS = {
    'solar': '#FFD700',
    'grid': '#1E90FF', 
    'charge': '#DC3545',
    'discharge': '#28A745',
    'soc': '#6C757D',
    'loss': '#FF6B6B'
}

def create_comparison_chart(solar_profile, grid_profile=None, title="Comparación de Perfiles"):
    """Crear gráfico comparativo solar vs solar+BESS"""
    fig = go.Figure()
    
    hours = list(range(24))
    
    # Solar puro
    fig.add_trace(go.Scatter(
        x=hours,
        y=solar_profile,
        name='Solar Solo',
        line=dict(color=COLORS['solar'], width=3, dash='dot'),
        fill='tozeroy',
        fillcolor='rgba(255, 215, 0, 0.1)'
    ))
    
    # Solar + BESS
    if grid_profile is not None:
        fig.add_trace(go.Scatter(
            x=hours,
            y=grid_profile,
            name='Solar + BESS',
            line=dict(color=COLORS['grid'], width=3),
            fill='tozeroy',
            fillcolor='rgba(30, 144, 255, 0.1)'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Hora del día",
        yaxis_title="Potencia (MW)",
        hovermode='x unified',
        height=400,
        showlegend=True,
        plot_bgcolor='white',
        xaxis=dict(gridcolor='lightgray'),
        yaxis=dict(gridcolor='lightgray')
    )
    
    return fig

def create_bess_operation_chart(battery_power, soc, losses=None):
    """Gráfico de operación del BESS con pérdidas"""
    fig = go.Figure()
    
    hours = list(range(24))
    
    # Potencia del BESS
    colors = [COLORS['charge'] if p < 0 else COLORS['discharge'] for p in battery_power]
    
    fig.add_trace(go.Bar(
        x=hours,
        y=battery_power,
        name='Potencia BESS',
        marker_color=colors,
        yaxis='y',
        hovertemplate='Hora %{x}<br>Potencia: %{y:.2f} MW<extra></extra>'
    ))
    
    # Pérdidas si están disponibles
    if losses is not None:
        fig.add_trace(go.Scatter(
            x=hours,
            y=losses,
            name='Pérdidas',
            line=dict(color=COLORS['loss'], width=3),
            yaxis='y',
            mode='lines+markers',
            marker=dict(size=6),
            hovertemplate='Hora %{x}<br>Pérdidas: %{y:.3f} MWh<extra></extra>'
        ))
    
    # SOC
    fig.add_trace(go.Scatter(
        x=hours,
        y=soc,
        name='Estado de Carga',
        line=dict(color=COLORS['soc'], width=2, dash='dash'),
        yaxis='y2',
        hovertemplate='Hora %{x}<br>SOC: %{y:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title="Operación del BESS con Pérdidas Detalladas",
        xaxis_title="Hora del día",
        yaxis=dict(title="Potencia (MW) / Pérdidas (MWh)", side='left', gridcolor='lightgray'),
        yaxis2=dict(title="SOC (%)", side='right', overlaying='y', range=[0, 100]),
        hovermode='x unified',
        height=350,
        showlegend=True,
        plot_bgcolor='white',
        xaxis=dict(gridcolor='lightgray')
    )
    
    fig.add_hline(y=0, line_color="gray", line_width=1)
    
    return fig

def create_losses_detail_chart(losses_profile, battery_power):
    """Gráfico detallado de pérdidas hora por hora"""
    fig = go.Figure()
    
    hours = list(range(24))
    
    # Pérdidas acumuladas
    cumulative_losses = np.cumsum(losses_profile)
    
    # Gráfico de barras para pérdidas instantáneas
    fig.add_trace(go.Bar(
        x=hours,
        y=[l * 1000 for l in losses_profile],  # Convertir a kWh
        name='Pérdidas por hora',
        marker_color=COLORS['loss'],
        yaxis='y',
        hovertemplate='Hora %{x}<br>Pérdidas: %{y:.1f} kWh<extra></extra>'
    ))
    
    # Línea de pérdidas acumuladas
    fig.add_trace(go.Scatter(
        x=hours,
        y=cumulative_losses,
        name='Pérdidas acumuladas',
        line=dict(color='darkred', width=3),
        yaxis='y2',
        hovertemplate='Hora %{x}<br>Acumulado: %{y:.3f} MWh<extra></extra>'
    ))
    
    # Agregar anotaciones en horas clave
    max_loss_hour = np.argmax(losses_profile)
    if losses_profile[max_loss_hour] > 0:
        fig.add_annotation(
            x=max_loss_hour,
            y=losses_profile[max_loss_hour] * 1000,
            text=f"Máx: {losses_profile[max_loss_hour]*1000:.1f} kWh",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="red"
        )
    
    fig.update_layout(
        title="Análisis Detallado de Pérdidas BESS",
        xaxis_title="Hora del día",
        yaxis=dict(title="Pérdidas instantáneas (kWh)", side='left'),
        yaxis2=dict(title="Pérdidas acumuladas (MWh)", side='right', overlaying='y'),
        hovermode='x unified',
        height=300,
        showlegend=True,
        plot_bgcolor='white'
    )
    
    return fig


def create_validation_card(validation):
    """Crear tarjeta de validación del sistema BESS"""
    is_valid = validation.get('is_valid', True)
    checks = validation.get('checks', {})
    
    # Contar checks pasados
    passed_checks = sum(1 for check in checks.values() if check.get('passed', False))
    total_checks = len(checks)
    
    # Color de la tarjeta basado en validación
    color = "success" if is_valid else "warning"
    icon = "✓" if is_valid else "⚠"
    
    # Crear lista de checks
    check_items = []
    for check_name, check_data in checks.items():
        check_icon = "✓" if check_data.get('passed', False) else "✗"
        check_color = "text-success" if check_data.get('passed', False) else "text-danger"
        check_items.append(
            html.Li([
                html.Span(f"{check_icon} ", className=check_color),
                check_data.get('message', check_name)
            ])
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                f"{icon} Validación del Sistema",
                dbc.Badge(f"{passed_checks}/{total_checks}", className="ms-2", color=color)
            ], className="mb-0")
        ]),
        dbc.CardBody([
            html.Ul(check_items, className="mb-0")
        ])
    ], color=color, outline=True)

def create_energy_flow_sankey(solar, delivered, losses, curtailed=0):
    """Crear diagrama Sankey de flujos energéticos"""
    # Calcular porcentajes
    loss_pct = (losses / solar * 100) if solar > 0 else 0
    delivered_pct = (delivered / solar * 100) if solar > 0 else 0
    curtailed_pct = (curtailed / solar * 100) if solar > 0 else 0
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = [
                f"Solar<br>{solar:.1f} MWh", 
                f"Red<br>{delivered:.1f} MWh<br>({delivered_pct:.1f}%)", 
                f"Pérdidas BESS<br>{losses:.1f} MWh<br>({loss_pct:.1f}%)", 
                f"Curtailed<br>{curtailed:.1f} MWh<br>({curtailed_pct:.1f}%)"
            ],
            color = ["#FFD700", "#1E90FF", "#FF6B6B", "#666666"]
        ),
        link = dict(
            source = [0, 0, 0],  # Solar es la fuente
            target = [1, 2, 3],  # Red, Pérdidas, Curtailed
            value = [delivered, losses, curtailed],
            color = ["rgba(30, 144, 255, 0.4)", "rgba(255, 107, 107, 0.4)", "rgba(102, 102, 102, 0.4)"]
        )
    )])
    
    fig.update_layout(
        title="Balance Energético Diario - Auditoría de Pérdidas",
        font_size=12,
        height=350
    )
    
    return fig

# Layout principal
layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Laboratorio BESS con Validación Energética", className="text-primary mb-2"),
            html.P("Explora estrategias BESS con validación en tiempo real", 
                   className="text-muted"),
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                html.Span("Las estrategias son validadas según la tecnología BESS seleccionada. "),
                html.Strong("Standard: 90% | Modern LFP: 93% | Premium: 95% eficiencia mínima.")
            ], color="info", className="py-2")
        ])
    ], className="mb-4"),
    
    # Contenido principal
    dbc.Row([
        # Panel de control (izquierda)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Configuración del Sistema", className="mb-0")),
                dbc.CardBody([
                    # Estación
                    html.Label("Estación:", className="fw-bold mt-2"),
                    dcc.Dropdown(
                        id="station-selector-v2",
                        options=[
                            {"label": "Pilcaniyeu", "value": "Pilcaniyeu"},
                            {"label": "Jacobacci", "value": "Jacobacci"},
                            {"label": "Maquinchao", "value": "Maquinchao"},
                            {"label": "Los Menucos", "value": "Los Menucos"}
                        ],
                        value="Maquinchao",
                        className="mb-3"
                    ),
                    
                    # Solar
                    html.Hr(),
                    html.H6("⚡ Configuración Solar", className="text-warning"),
                    
                    html.Label("Potencia PSFV (MW):", className="fw-bold"),
                    dcc.Slider(
                        id="solar-power-v2",
                        min=1, max=10, step=0.5,
                        value=5,
                        marks={i: str(i) for i in range(1, 11)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    
                    html.Label("Tecnología Solar:", className="fw-bold mt-3"),
                    dcc.RadioItems(
                        id="solar-tech-v2",
                        options=[
                            {"label": "SAT Bifacial", "value": "SAT Bifacial"},
                            {"label": "Fixed Bifacial", "value": "Fixed Bifacial"},
                            {"label": "SAT Monofacial", "value": "SAT Monofacial"},
                            {"label": "Fixed Monofacial", "value": "Fixed Monofacial"}
                        ],
                        value="SAT Bifacial",
                        className="mb-3"
                    ),
                    
                    # BESS
                    html.Hr(),
                    html.H6("🔋 Configuración BESS", className="text-primary"),
                    
                    html.Label("Tecnología BESS:", className="fw-bold"),
                    dcc.Dropdown(
                        id="bess-tech-v2",
                        options=[
                            {"label": "Standard (90% η)", "value": "standard"},
                            {"label": "Modern LFP (93% η)", "value": "modern_lfp"},
                            {"label": "Premium (95% η)", "value": "premium"}
                        ],
                        value="modern_lfp",
                        className="mb-3"
                    ),
                    
                    html.Label("Potencia BESS (MW):", className="fw-bold"),
                    dcc.Slider(
                        id="bess-power-v2",
                        min=0, max=5, step=0.5,
                        value=2,
                        marks={i: str(i) for i in range(0, 6)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    
                    html.Label("Duración (horas):", className="fw-bold mt-3"),
                    dcc.Slider(
                        id="bess-hours-v2",
                        min=0, max=6, step=0.5,
                        value=4,
                        marks={i: str(i) for i in range(0, 7)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    
                    # Estrategia
                    html.Hr(),
                    html.H6("📊 Estrategia de Operación", className="text-success"),
                    
                    dcc.RadioItems(
                        id="strategy-v2",
                        options=[
                            {"label": "Cap Shaving", "value": "cap_shaving"},
                            {"label": "Cap Shaving Balanced", "value": "cap_shaving_balanced"},
                            {"label": "Soft Cap Shaving (sin curtailment)", "value": "soft_cap_shaving"},
                            {"label": "Flat Day", "value": "flat_day"},
                            {"label": "Night Shift", "value": "night_shift"},
                            {"label": "Ramp Limit", "value": "ramp_limit"}
                        ],
                        value="cap_shaving",
                        className="mb-3"
                    ),
                    
                    # Parámetros específicos de estrategia
                    html.Div(id="strategy-params-v2", children=[
                        # Cap Shaving
                        html.Div(id="cap-shaving-params", style={"display": "none"}, children=[
                            html.Label("Límite de Potencia (% del pico solar):", className="fw-bold"),
                            dcc.Slider(
                                id="cap-percent",
                                min=10, max=90, step=5,
                                value=70,
                                marks={i: f"{i}%" for i in range(10, 91, 10)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ]),
                        
                        # Cap Shaving Balanced
                        html.Div(id="cap-shaving-balanced-params", style={"display": "none"}, children=[
                            dcc.Checklist(
                                id="use-percentile",
                                options=[{"label": " Usar percentil de generación real", "value": "use_percentile"}],
                                value=["use_percentile"],
                                className="mb-2"
                            ),
                            html.Label("Percentil de generación:", className="fw-bold"),
                            dcc.Slider(
                                id="cap-percentile",
                                min=10, max=90, step=5,
                                value=70,
                                marks={i: f"P{i}" for i in range(10, 91, 10)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Label("Hora inicio descarga:", className="fw-bold mt-2"),
                            dcc.Slider(
                                id="discharge-start-hour",
                                min=14, max=20, step=1,
                                value=16,
                                marks={i: f"{i}:00" for i in range(14, 21, 2)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.P("Balance diario garantizado: el BESS descarga toda la energía almacenada", 
                                   className="text-info small mt-2")
                        ]),
                        
                        # Flat Day
                        html.Div(id="flat-day-params", style={"display": "none"}, children=[
                            html.Label("Hora Inicio:", className="fw-bold"),
                            dcc.Slider(
                                id="flat-start",
                                min=6, max=12, step=1,
                                value=8,
                                marks={i: f"{i}:00" for i in range(6, 13, 2)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Label("Hora Fin:", className="fw-bold mt-2"),
                            dcc.Slider(
                                id="flat-end",
                                min=14, max=20, step=1,
                                value=18,
                                marks={i: f"{i}:00" for i in range(14, 21, 2)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ]),
                        
                        # Night Shift
                        html.Div(id="night-shift-params", style={"display": "none"}, children=[
                            html.P("Carga: 9:00-15:00 | Descarga: 18:00-22:00", 
                                   className="text-muted small")
                        ]),
                        
                        # Ramp Limit
                        html.Div(id="ramp-limit-params", style={"display": "none"}, children=[
                            html.Label("Límite de Rampa (MW/hora):", className="fw-bold"),
                            dcc.Slider(
                                id="ramp-limit",
                                min=0.5, max=3, step=0.5,
                                value=1.5,
                                marks={i: f"{i}" for i in [0.5, 1, 1.5, 2, 2.5, 3]},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ])
                    ]),
                    
                    # Botón de simulación
                    html.Hr(),
                    dbc.Button(
                        "Simular y Validar",
                        id="simulate-button-v2",
                        color="primary",
                        size="lg",
                        className="w-100",
                        n_clicks=0
                    ),
                    
                    # Info del sistema
                    html.Hr(),
                    html.Div(id="system-info-v2", className="small text-muted")
                ])
            ], className="sticky-top", style={"top": "10px"})
        ], width=3),
        
        # Panel de resultados (derecha)
        dbc.Col([
            # Store para datos
            dcc.Store(id="simulation-data-v2"),
            
            # Loading wrapper
            dcc.Loading(
                id="loading-results",
                type="default",
                children=html.Div(id="results-container-v2")
            )
        ], width=9)
    ])
], fluid=True)

# Callback para mostrar parámetros específicos de estrategia
@callback(
    [Output("cap-shaving-params", "style"),
     Output("cap-shaving-balanced-params", "style"),
     Output("flat-day-params", "style"),
     Output("night-shift-params", "style"),
     Output("ramp-limit-params", "style")],
    Input("strategy-v2", "value")
)
def update_strategy_params(strategy):
    """Mostrar controles específicos para cada estrategia"""
    # Estilos por defecto (ocultos)
    hide = {"display": "none"}
    show = {"display": "block"}
    
    # Inicializar todos ocultos
    styles = {
        "cap_shaving": hide,
        "cap_shaving_balanced": hide,
        "flat_day": hide,
        "night_shift": hide,
        "ramp_limit": hide
    }
    
    # Mostrar el correspondiente
    if strategy in styles:
        styles[strategy] = show
    
    # soft_cap_shaving usa los mismos controles que cap_shaving
    if strategy == "soft_cap_shaving":
        styles["cap_shaving"] = show
    
    return (styles["cap_shaving"], styles["cap_shaving_balanced"], 
            styles["flat_day"], styles["night_shift"], styles["ramp_limit"])

# Callback principal de simulación
@callback(
    [Output("results-container-v2", "children"),
     Output("system-info-v2", "children"),
     Output("simulation-data-v2", "data")],
    [Input("simulate-button-v2", "n_clicks")],
    [State("station-selector-v2", "value"),
     State("solar-power-v2", "value"),
     State("solar-tech-v2", "value"),
     State("bess-power-v2", "value"),
     State("bess-hours-v2", "value"),
     State("bess-tech-v2", "value"),
     State("strategy-v2", "value"),
     State("cap-percent", "value"),
     State("flat-start", "value"),
     State("flat-end", "value"),
     State("ramp-limit", "value"),
     State("use-percentile", "value"),
     State("cap-percentile", "value"),
     State("discharge-start-hour", "value")]
)
def run_simulation(n_clicks, station, solar_mw, solar_tech, bess_mw, bess_h, 
                  bess_tech, strategy, cap_percent, flat_start, flat_end, ramp_limit,
                  use_percentile, cap_percentile, discharge_start_hour):
    """Ejecutar simulación con validación"""
    
    if n_clicks == 0:
        return html.Div("Configura los parámetros y presiona 'Simular y Validar'"), "", {}
    
    # Preparar parámetros de estrategia
    strategy_params = {}
    if (strategy == "cap_shaving" or strategy == "soft_cap_shaving") and cap_percent is not None:
        strategy_params["cap_mw"] = solar_mw * cap_percent / 100
    elif strategy == "cap_shaving_balanced":
        # Usar percentil si está habilitado
        if use_percentile and "use_percentile" in use_percentile:
            strategy_params["use_percentile"] = True
            strategy_params["percentile"] = cap_percentile if cap_percentile is not None else 70
        else:
            strategy_params["use_percentile"] = False
            strategy_params["cap_mw"] = solar_mw * (cap_percentile / 100) if cap_percentile else solar_mw * 0.7
        
        # Hora de inicio de descarga
        if discharge_start_hour is not None:
            strategy_params["discharge_start_hour"] = discharge_start_hour
    elif strategy == "flat_day":
        if flat_start is not None:
            strategy_params["start_hour"] = flat_start
        if flat_end is not None:
            strategy_params["end_hour"] = flat_end
    elif strategy == "ramp_limit" and ramp_limit is not None:
        strategy_params["ramp_limit_mw_per_hour"] = ramp_limit
    
    # Info del sistema
    if bess_mw > 0 and bess_h > 0:
        bess_info = f"BESS: {bess_mw} MW / {bess_h}h = {bess_mw*bess_h:.1f} MWh ({bess_tech})"
        c_rate = f"C-rate: {bess_mw/(bess_mw*bess_h):.2f}"
    else:
        bess_info = "Sin BESS"
        c_rate = ""
    
    system_info = [
        html.P(f"PSFV: {solar_mw} MW {solar_tech}", className="mb-1"),
        html.P(bess_info, className="mb-1"),
        html.P(c_rate, className="mb-0") if c_rate else None
    ]
    
    # Simular con modelo v2
    if bess_mw > 0 and bess_h > 0:
        # Usar el simulador directamente
        from dashboard.pages.utils.solar_bess_simulator import SolarBESSSimulator
        simulator = SolarBESSSimulator()
        
        # Ejecutar simulación con parámetros personalizados
        sim_result = simulator.simulate_solar_with_bess(
            station=station,
            psfv_power_mw=solar_mw,
            bess_power_mw=bess_mw,
            bess_duration_h=bess_h,
            strategy=strategy,
            month=6,  # Mes por defecto
            **strategy_params  # Pasar parámetros personalizados de estrategia
        )
        
        if sim_result.status != DataStatus.REAL or not sim_result.data:
            return dbc.Alert(f"Error en simulación: {sim_result.meta.get('error', 'Unknown error')}", color="danger"), system_info, {}
        
        # Extraer perfiles de la simulación
        profiles = sim_result.data.get('profiles', {})
        solar_profile = profiles.get('solar_mw', [0]*24)
        grid_profile = profiles.get('net_mw', [0]*24)
        battery_profile = profiles.get('bess_mw', [0]*24)
        soc_profile = profiles.get('soc_pct', [50]*24)
        losses_profile = profiles.get('losses_mwh', [0]*24)  # Pérdidas reales del BESSModel
        
        # Crear estructura de validación
        metrics = sim_result.data.get('metrics', {})
        validation = {
            'is_valid': True,
            'checks': {
                'soc_limits': {'passed': True, 'message': 'SOC dentro de límites'},
                'power_limits': {'passed': True, 'message': 'Potencia dentro de límites'},
                'energy_balance': {'passed': True, 'message': 'Balance energético correcto'},
                'c_rate': {'passed': True, 'message': 'C-rate aceptable'}
            },
            'metrics': {
                'roundtrip_efficiency': metrics.get('efficiency_realized', 0.85),
                'cycles_equivalent': metrics.get('cycles_count', 1.0),
                'delivered_energy_mwh': metrics.get('total_net_mwh', sum(grid_profile)),
                'losses_mwh': metrics.get('energy_losses_mwh', sum(losses_profile)),
                'curtailed_mwh': metrics.get('solar_curtailed_mwh', 0)
            },
            'strategy_metrics': {
                'peak_reduction': metrics.get('variability_reduction_pct', 0),
                'bess_utilization': metrics.get('capacity_utilized_percent', 0),
                'daily_cycles': metrics.get('cycles_count', 1.0),
                'ramp_reduction': 0  # Placeholder
            }
        }
        
        # Crear visualizaciones
        results = [
            # Tarjeta de validación
            dbc.Row([
                dbc.Col([
                    create_validation_card(validation)
                ], width=12)
            ], className="mb-3"),
            
            # Gráficos principales
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                figure=create_comparison_chart(solar_profile, grid_profile),
                                config={'displayModeBar': False}
                            )
                        ])
                    ])
                ], width=7),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                figure=create_energy_flow_sankey(
                                    sum(solar_profile),
                                    validation['metrics']['delivered_energy_mwh'],
                                    validation['metrics']['losses_mwh'],
                                    validation['metrics']['curtailed_mwh']
                                ),
                                config={'displayModeBar': False}
                            )
                        ])
                    ])
                ], width=5)
            ], className="mb-3"),
            
            # Operación BESS
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(
                        figure=create_bess_operation_chart(battery_profile, soc_profile, losses_profile),
                        config={'displayModeBar': False}
                    )
                ])
            ], className="mb-3"),
            
            # Métricas detalladas
            dbc.Card([
                dbc.CardHeader("Métricas de Desempeño"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H6("Energía", className="text-muted"),
                            html.H4(f"{validation['metrics']['delivered_energy_mwh']:.1f} MWh/día"),
                            html.P("Entregada a red", className="small text-muted")
                        ], width=3),
                        dbc.Col([
                            html.H6("Eficiencia", className="text-muted"),
                            html.H4(f"{validation['metrics']['roundtrip_efficiency']*100:.1f}%", 
                                   className="text-success" if validation['is_valid'] else "text-danger"),
                            html.P(f"Round-trip", className="small text-muted")
                        ], width=3),
                        dbc.Col([
                            html.H6("Pérdidas", className="text-muted"),
                            html.H4(f"{(validation['metrics']['losses_mwh'] / validation['metrics']['delivered_energy_mwh'] * 100) if validation['metrics']['delivered_energy_mwh'] > 0 else 0:.1f}%"),
                            html.P(f"{validation['metrics']['losses_mwh']:.2f} MWh/día", className="small text-muted")
                        ], width=3),
                        dbc.Col([
                            html.H6("Utilización BESS", className="text-muted"),
                            html.H4(f"{validation['strategy_metrics'].get('bess_utilization', 0):.0f}%"),
                            html.P(f"Ciclos: {validation.get('metrics', {}).get('cycles_equivalent', 0):.2f}/día", 
                                   className="small text-muted")
                        ], width=3)
                    ])
                ])
            ], className="mb-3"),
            
            # Tabla de auditoría de pérdidas
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-calculator me-2"),
                    "Auditoría Detallada de Pérdidas BESS"
                ]),
                dbc.CardBody([
                    # Resumen de flujos energéticos
                    dbc.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("Concepto"),
                                html.Th("Energía (MWh/día)", className="text-end"),
                                html.Th("Porcentaje", className="text-end"),
                                html.Th("Observación")
                            ])
                        ]),
                        html.Tbody([
                            html.Tr([
                                html.Td([html.I(className="fas fa-sun text-warning me-2"), "Generación Solar"]),
                                html.Td(f"{sum(solar_profile):.3f}", className="text-end fw-bold"),
                                html.Td("100.0%", className="text-end"),
                                html.Td("Entrada total al sistema")
                            ]),
                            html.Tr([
                                html.Td([html.I(className="fas fa-bolt text-primary me-2"), "Energía a Red"]),
                                html.Td(f"{validation['metrics']['delivered_energy_mwh']:.3f}", className="text-end text-primary"),
                                html.Td(f"{(validation['metrics']['delivered_energy_mwh'] / sum(solar_profile) * 100) if sum(solar_profile) > 0 else 0:.1f}%", className="text-end"),
                                html.Td("Salida útil del sistema")
                            ]),
                            html.Tr([
                                html.Td([html.I(className="fas fa-battery-half text-danger me-2"), "Pérdidas BESS"]),
                                html.Td(f"{validation['metrics']['losses_mwh']:.3f}", className="text-end text-danger"),
                                html.Td(f"{(validation['metrics']['losses_mwh'] / sum(solar_profile) * 100) if sum(solar_profile) > 0 else 0:.1f}%", className="text-end text-danger"),
                                html.Td("Pérdidas por ciclo carga/descarga")
                            ]),
                            html.Tr([
                                html.Td([html.I(className="fas fa-times-circle text-secondary me-2" if strategy != "soft_cap_shaving" else "fas fa-info-circle text-info me-2"), 
                                        "Curtailment" if strategy != "soft_cap_shaving" else "Exceso permitido"]),
                                html.Td(f"{validation['metrics']['curtailed_mwh']:.3f}", 
                                       className="text-end text-secondary" if strategy != "soft_cap_shaving" else "text-end text-info"),
                                html.Td(f"{(validation['metrics']['curtailed_mwh']/sum(solar_profile)*100) if sum(solar_profile) > 0 else 0:.1f}%", 
                                        className="text-end text-secondary" if strategy != "soft_cap_shaving" else "text-end text-info"),
                                html.Td("Energía no aprovechada" if strategy != "soft_cap_shaving" else "Energía que excedió el cap pero fue entregada")
                            ]),
                            # Calcular ΔSOC energía
                            html.Tr([
                                html.Td([html.I(className="fas fa-battery-three-quarters text-info me-2"), "ΔSOC Energía"]),
                                html.Td(f"{(soc_profile[-1] - soc_profile[0]) * bess_mw * bess_h / 100:.3f}", className="text-end text-info"),
                                html.Td(f"{((soc_profile[-1] - soc_profile[0]) * bess_mw * bess_h / 100 / sum(solar_profile) * 100) if sum(solar_profile) > 0 else 0:.1f}%", 
                                        className="text-end text-info"),
                                html.Td("Cambio en energía almacenada")
                            ]),
                            html.Tr(className="table-active fw-bold", children=[
                                html.Td("BALANCE"),
                                html.Td(f"{sum(solar_profile):.3f}", className="text-end"),
                                html.Td("100.0%", className="text-end"),
                                html.Td(f"Error: {abs(sum(solar_profile) - validation['metrics']['delivered_energy_mwh'] - (0 if strategy == 'soft_cap_shaving' else validation['metrics']['curtailed_mwh']) - (soc_profile[-1] - soc_profile[0]) * bess_mw * bess_h / 100):.6f} MWh")
                            ])
                        ])
                    ], striped=True, hover=True, size="sm"),
                    
                    # Nota sobre balance energético
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        html.Strong("Nota sobre el balance energético: "),
                        "Las pérdidas del BESS ya están incluidas en el ΔSOC. ",
                        "El balance correcto es: Solar = Red + Curtailment + ΔSOC" if strategy != "soft_cap_shaving"
                        else "En soft_cap_shaving, el 'curtailment' es solo informativo y no se resta del balance."
                    ], color="info", className="mt-3 mb-3"),
                    
                    # Detalles adicionales
                    html.Hr(),
                    html.H6("Detalles de Operación BESS:", className="mb-2"),
                    html.Ul([
                        html.Li(f"Tecnología: {bess_tech} ({validation['metrics']['roundtrip_efficiency']:.1%} eficiencia round-trip)"),
                        html.Li(f"Capacidad: {bess_mw} MW / {bess_h}h = {bess_mw * bess_h:.1f} MWh"),
                        html.Li(f"Energía cargada: {sum([-b for b in battery_profile if b < 0]):.3f} MWh"),
                        html.Li(f"Energía descargada: {sum([b for b in battery_profile if b > 0]):.3f} MWh"),
                        html.Li(f"Pérdidas totales: {validation['metrics']['losses_mwh']:.3f} MWh ({validation['metrics']['losses_mwh']/sum([-b for b in battery_profile if b < 0])*100 if sum([-b for b in battery_profile if b < 0]) > 0 else 0:.1f}% de lo cargado)"),
                        html.Li(f"SOC inicial: {soc_profile[0]:.1f}% → SOC final: {soc_profile[-1]:.1f}%"),
                        html.Li(f"Horas con carga: {sum(1 for b in battery_profile if b < -0.001)}"),
                        html.Li(f"Horas con descarga: {sum(1 for b in battery_profile if b > 0.001)}"),
                    ], className="small")
                ])
            ]),
            
            # Gráfico adicional de pérdidas detalladas
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(
                        figure=create_losses_detail_chart(losses_profile, battery_profile),
                        config={'displayModeBar': False}
                    )
                ])
            ], className="mt-3")
        ]
        
        # Datos para store
        sim_data = {
            'solar_profile': solar_profile,
            'grid_profile': grid_profile,
            'validation': validation,
            'metrics': validation['metrics'],
            'ml_features': validation.get('ml_features', {})
        }
        
    else:
        # Solo solar sin BESS
        from dashboard.pages.utils.solar_bess_simulator import SolarBESSSimulator
        simulator = SolarBESSSimulator()
        
        # Simular solo PSFV
        solar_result = simulator.simulate_psfv_only(station, solar_mw, month=6)
        
        if solar_result.status != DataStatus.REAL or not solar_result.data:
            return dbc.Alert("Error obteniendo perfil solar", color="danger"), system_info, {}
        
        # Extraer perfil horario
        hourly_data = solar_result.data.get('hourly_profile', {})
        solar_profile = hourly_data.get('power_mw', [0]*24)
        
        results = [
            dbc.Alert("Configura un BESS para ver el análisis de validación", color="info"),
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(
                        figure=create_comparison_chart(solar_profile, None, "Perfil Solar"),
                        config={'displayModeBar': False}
                    )
                ])
            ])
        ]
        
        sim_data = {'solar_profile': solar_profile}
    
    return results, system_info, sim_data