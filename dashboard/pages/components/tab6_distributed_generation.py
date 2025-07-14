"""
Tab 6: Generación Distribuida - Análisis de Costos
NO HARDCODING - Todos los datos vienen del DataManager
"""

from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from pathlib import Path
from dashboard.pages.utils import get_data_manager

def render_dg_tab():
    """Render the distributed generation tab content."""
    
    # Get fresh data from DataManager EVERY TIME
    dm = get_data_manager()
    gd_costs = dm.get_gd_costs()
    
    # Extract values for display
    potencia_mw = gd_costs["potencia_mw"]
    factor_capacidad = gd_costs["factor_capacidad"]
    horas_dia = gd_costs["horas_dia_base"]
    dias_ano = gd_costs["dias_ano"]
    
    # Generation values
    generacion_anual_mwh = gd_costs["generacion_anual_mwh"]
    generacion_mensual_mwh = gd_costs["generacion_mensual_mwh"]
    
    # Costs - Use values from DataManager, don't recalculate
    costo_total_anual = gd_costs["costo_total_anual"]
    costo_total_mensual = gd_costs["costo_total_mensual"]
    costo_por_mwh = gd_costs["costo_por_mwh"]  # Use calculated value from DataManager
    costo_por_kw_mes = costo_total_mensual / (potencia_mw * 1000) if potencia_mw > 0 else 0
    
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H3([
                    html.I(className="fas fa-bolt me-2"),
                    "Análisis de Costos - Generación Distribuida Los Menucos"
                ], className="text-primary mb-3"),
                html.P("Sistema de generación térmica a gas natural de 3 MW instalado en ET Los Menucos",
                       className="text-muted"),
                html.Hr()
            ])
        ]),
        
        # Sección 1: Descripción del Sistema
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-cogs me-2"),
                    "Características del Sistema"
                ], className="mb-3"),
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6("Potencia Instalada", className="text-muted"),
                                html.H4(f"{potencia_mw} MW", className="text-primary"),
                                html.Small("2 × 1.5 MW motogeneradores")
                            ], md=3),
                            dbc.Col([
                                html.H6("Combustible", className="text-muted"),
                                html.H4("Gas Natural", className="text-success"),
                                html.Small(f"{gd_costs['consumo_gas']} m³/kWh")
                            ], md=3),
                            dbc.Col([
                                html.H6("Conexión", className="text-muted"),
                                html.H4("13.2 kV", className="text-info"),
                                html.Small("ET Los Menucos")
                            ], md=3),
                            dbc.Col([
                                html.H6("Operación", className="text-muted"),
                                html.H4(f"{int(horas_dia)}h × FC {factor_capacidad}", className="text-warning"),
                                html.Small(f"{dias_ano} días/año")
                            ], md=3)
                        ])
                    ])
                ], className="shadow mb-4")
            ])
        ]),
        
        # Sección 2: Métricas Clave
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-chart-line me-2"),
                    "Métricas Clave de Operación"
                ], className="mb-3")
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Generación Anual", className="text-muted mb-1"),
                        html.H3(f"{int(generacion_anual_mwh):,} MWh", className="text-primary mb-0"),
                        html.Small(f"{int(generacion_mensual_mwh)} MWh/mes", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Costo Total", className="text-muted mb-1"),
                        html.H3(f"${int(costo_total_anual):,}", className="text-danger mb-0"),
                        html.Small(f"${int(costo_total_mensual):,}/mes", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Costo por MWh", className="text-muted mb-1"),
                        html.H3(f"${costo_por_mwh:.1f}", className="text-warning mb-0"),
                        html.Small("USD/MWh", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Costo por kW", className="text-muted mb-1"),
                        html.H3(f"${costo_por_kw_mes:.2f}", className="text-info mb-0"),
                        html.Small("USD/kW-mes", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3)
        ], className="mb-4"),
        
        # Sección 3: Tabla de Costos
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-table me-2"),
                    "Desglose Detallado de Costos"
                ], className="mb-3")
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div(id="dg-cost-table")
                    ])
                ], className="shadow")
            ], md=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id="dg-pie-chart", config={'displayModeBar': False})
                    ])
                ], className="shadow")
            ], md=4)
        ], className="mb-4"),
        
        # Sección 4: Análisis Fijos vs Variables
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-balance-scale me-2"),
                    "Estructura de Costos"
                ], className="mb-3")
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id="dg-fixed-variable-chart", config={'displayModeBar': False})
                    ])
                ], className="shadow")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Indicadores de Eficiencia", className="mb-3"),
                        html.Div(id="dg-efficiency-indicators")
                    ])
                ], className="shadow")
            ], md=6)
        ], className="mb-4"),
        
        # Sección 5: Calculadora Interactiva
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-calculator me-2"),
                    "Calculadora de Costos - Análisis de Sensibilidad"
                ], className="mb-3")
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Factor de Capacidad"),
                                dcc.Slider(
                                    id="dg-fc-slider",
                                    min=0.5,
                                    max=1.0,
                                    step=0.05,
                                    value=factor_capacidad,
                                    marks={i/10: f"{i/10:.1f}" for i in range(5, 11)},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Horas por Día"),
                                dcc.Slider(
                                    id="dg-hours-slider",
                                    min=2,
                                    max=24,
                                    step=1,
                                    value=horas_dia,
                                    marks={i: str(i) for i in [2, 4, 8, 12, 16, 20, 24]},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Precio Gas (USD/m³)"),
                                dcc.Slider(
                                    id="dg-gas-price-slider",
                                    min=0.05,
                                    max=0.20,
                                    step=0.01,
                                    value=gd_costs['precio_gas'],
                                    marks={i/100: f"{i/100:.2f}" for i in [5, 10, 15, 20]},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                )
                            ], md=4)
                        ], className="mb-3"),
                        html.Div(id="dg-calculator-results")
                    ])
                ], className="shadow")
            ])
        ], className="mb-4"),
        
        # Sección 6: Curva de Costo USD/MWh vs Horas de Operación
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-chart-area me-2"),
                    "Análisis de Sensibilidad - Horas de Operación"
                ], className="mb-3")
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id="dg-cost-curve", config={'displayModeBar': False}),
                        html.Small(
                            "* Análisis del costo unitario en función de las horas de operación diaria",
                            className="text-muted mt-2"
                        )
                    ])
                ], className="shadow")
            ])
        ], className="mb-4"),
        
        # Footer
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "Análisis comparativo con tecnologías alternativas (Solar + BESS) disponible en Fase 4 del estudio."
                ], color="info", className="mb-0")
            ])
        ])
    ])

# Callback para actualizar la tabla de costos
@callback(
    Output("dg-cost-table", "children"),
    Input("dg-cost-table", "id")
)
def update_cost_table(_):
    """Update cost breakdown table with real-time data."""
    
    # Get fresh data every time
    dm = get_data_manager()
    gd_costs = dm.get_gd_costs()
    
    # Extract values
    alquiler_mensual = gd_costs["alquiler_mensual"]
    alquiler_anual = gd_costs["alquiler_anual"]
    opex_mensual = gd_costs["opex_mensual"]
    opex_total_anual = gd_costs["opex_total_anual"]
    combustible_mensual = gd_costs["costo_combustible_mensual"]
    combustible_anual = gd_costs["costo_combustible_anual"]
    oym_mensual = gd_costs["costo_oym_mensual"]
    oym_anual = gd_costs["costo_oym_anual"]
    total_mensual = gd_costs["costo_total_mensual"]
    total_anual = gd_costs["costo_total_anual"]
    
    data = {
        'Concepto': [
            'Alquiler Equipos',
            'OPEX (3 MW)',
            'Combustible (Gas Natural)',
            'Operación y Mantenimiento',
            'TOTAL'
        ],
        'Mensual (USD)': [
            f"${int(alquiler_mensual):,}",
            f"${int(opex_mensual):,}",
            f"${int(combustible_mensual):,}",
            f"${int(oym_mensual):,}",
            f"${int(total_mensual):,}"
        ],
        'Anual (USD)': [
            f"${int(alquiler_anual):,}",
            f"${int(opex_total_anual):,}",
            f"${int(combustible_anual):,}",
            f"${int(oym_anual):,}",
            f"${int(total_anual):,}"
        ],
        '% del Total': [
            f"{(alquiler_anual/total_anual)*100:.1f}%",
            f"{(opex_total_anual/total_anual)*100:.1f}%",
            f"{(combustible_anual/total_anual)*100:.1f}%",
            f"{(oym_anual/total_anual)*100:.1f}%",
            "100.0%"
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Create table
    table = dbc.Table.from_dataframe(
        df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mb-0"
    )
    
    return html.Div([
        table,
        html.Small(
            f"* Costos basados en datos reales - Alquiler: ${gd_costs['alquiler_referencia']['costo_unitario']:.2f} USD/kW-mes", 
            className="text-muted mt-2"
        )
    ])

# Callback para el gráfico de torta
@callback(
    Output("dg-pie-chart", "figure"),
    Input("dg-pie-chart", "id")
)
def update_pie_chart(_):
    """Update cost distribution pie chart with real-time data."""
    
    # Get fresh data
    dm = get_data_manager()
    gd_costs = dm.get_gd_costs()
    
    labels = ['Alquiler', 'OPEX', 'Combustible', 'O&M']
    values = [
        gd_costs["alquiler_anual"],
        gd_costs["opex_total_anual"],
        gd_costs["costo_combustible_anual"],
        gd_costs["costo_oym_anual"]
    ]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textposition='inside',
        textinfo='percent+label',
        marker=dict(colors=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'])
    )])
    
    fig.update_layout(
        title="Distribución de Costos Anuales",
        showlegend=False,
        height=300,
        margin=dict(t=40, b=20, l=20, r=20),
        annotations=[dict(
            text='Costos<br>Anuales',
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False
        )]
    )
    
    return fig

# Callback para el gráfico de costos fijos vs variables
@callback(
    Output("dg-fixed-variable-chart", "figure"),
    Input("dg-fixed-variable-chart", "id")
)
def update_fixed_variable_chart(_):
    """Update fixed vs variable costs chart with real-time data."""
    
    # Get fresh data
    dm = get_data_manager()
    gd_costs = dm.get_gd_costs()
    
    categories = ['Mensual', 'Anual']
    fixed_costs = [
        gd_costs["alquiler_mensual"] + gd_costs["costo_oym_mensual"],
        gd_costs["alquiler_anual"] + gd_costs["costo_oym_anual"]
    ]
    variable_costs = [
        gd_costs["opex_mensual"] + gd_costs["costo_combustible_mensual"],
        gd_costs["opex_total_anual"] + gd_costs["costo_combustible_anual"]
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Costos Fijos',
        x=categories,
        y=fixed_costs,
        text=[f"${x:,.0f}" for x in fixed_costs],
        textposition='auto',
        marker_color='#3498db'
    ))
    
    fig.add_trace(go.Bar(
        name='Costos Variables',
        x=categories,
        y=variable_costs,
        text=[f"${x:,.0f}" for x in variable_costs],
        textposition='auto',
        marker_color='#e74c3c'
    ))
    
    fig.update_layout(
        title="Clasificación de Costos: Fijos vs Variables",
        barmode='stack',
        height=350,
        yaxis_title="USD",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Callback para indicadores de eficiencia
@callback(
    Output("dg-efficiency-indicators", "children"),
    Input("dg-efficiency-indicators", "id")
)
def update_efficiency_indicators(_):
    """Update efficiency indicators with real-time data."""
    
    # Get fresh data
    dm = get_data_manager()
    gd_costs = dm.get_gd_costs()
    
    # Calculate indicators
    factor_utilizacion = (gd_costs["horas_dia_base"]/24 * gd_costs["factor_capacidad"]) * 100
    costo_por_hora = gd_costs["costo_total_anual"] / (gd_costs["horas_dia_base"] * gd_costs["dias_ano"])
    horas_anuales = int(gd_costs["horas_dia_base"] * gd_costs["dias_ano"])
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H6("Factor de Utilización", className="text-muted"),
                html.H4(f"{factor_utilizacion:.1f}%", className="text-primary"),
                html.Small("Capacidad real utilizada")
            ], md=6),
            dbc.Col([
                html.H6("Costo por Hora", className="text-muted"),
                html.H4(f"${costo_por_hora:.1f}/h", className="text-warning"),
                html.Small("Durante operación")
            ], md=6)
        ], className="mb-3"),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.H6("Horas Anuales", className="text-muted"),
                html.H4(f"{horas_anuales:,}", className="text-info"),
                html.Small("Horas de operación")
            ], md=6),
            dbc.Col([
                html.H6("Costo Unitario", className="text-muted"),
                html.H4(f"${gd_costs['alquiler_referencia']['costo_unitario']:.2f}", className="text-success"),
                html.Small("USD/kW-mes alquiler")
            ], md=6)
        ])
    ])

# Callback para la calculadora interactiva
@callback(
    Output("dg-calculator-results", "children"),
    [Input("dg-fc-slider", "value"),
     Input("dg-hours-slider", "value"),
     Input("dg-gas-price-slider", "value")]
)
def update_calculator(fc, hours, gas_price):
    """Update calculator results based on slider inputs."""
    
    # Use DataManager function to calculate costs
    dm = get_data_manager()
    result = dm.calculate_gd_cost_per_mwh(hours_per_day=hours, fc=fc, gas_price=gas_price)
    
    # Get base values for comparison
    gd_costs_base = dm.get_gd_costs()
    
    # Extract results
    gen_anual_mwh = result["annual_generation_mwh"]
    gen_mensual_mwh = gen_anual_mwh / 12
    total_anual = result["annual_cost_usd"]
    total_mensual = result["monthly_cost_usd"]
    costo_mwh = result["cost_per_mwh"]
    
    # Comparación con caso base
    diff_mensual = total_mensual - gd_costs_base["costo_total_mensual"]
    diff_anual = total_anual - gd_costs_base["costo_total_anual"]
    diff_percent = ((total_anual / gd_costs_base["costo_total_anual"]) - 1) * 100 if gd_costs_base["costo_total_anual"] > 0 else 0
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Generación Anual", className="text-muted"),
                    html.H4(f"{int(gen_anual_mwh):,} MWh", className="text-primary"),
                    html.Small(f"{int(gen_mensual_mwh)} MWh/mes")
                ])
            ], className="text-center")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Costo Total Anual", className="text-muted"),
                    html.H4(f"${int(total_anual):,}", 
                           className="text-danger" if diff_anual > 0 else "text-success"),
                    html.Small(f"${int(total_mensual):,}/mes")
                ])
            ], className="text-center")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Costo por MWh", className="text-muted"),
                    html.H4(f"${costo_mwh:.1f}", className="text-warning"),
                    html.Small("USD/MWh")
                ])
            ], className="text-center")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Diferencia vs Base", className="text-muted"),
                    html.H4(f"{diff_percent:+.1f}%", 
                           className="text-danger" if diff_percent > 0 else "text-success"),
                    html.Small(f"${int(diff_anual):+,}/año")
                ])
            ], className="text-center")
        ], md=3)
    ])

# Callback para la curva de costo USD/MWh vs horas de operación
@callback(
    Output("dg-cost-curve", "figure"),
    Input("dg-cost-curve", "id")
)
def update_cost_curve(_):
    """Generate cost curve USD/MWh vs daily operation hours."""
    
    # Get DataManager instance
    dm = get_data_manager()
    gd_costs_base = dm.get_gd_costs()
    
    # Rango de horas de operación diaria
    hours_range = list(range(2, 13))  # 2 a 12 horas
    cost_per_mwh = []
    
    # Calcular costo por MWh para cada punto usando DataManager
    for hours in hours_range:
        result = dm.calculate_gd_cost_per_mwh(hours_per_day=hours)
        cost_per_mwh.append(result["cost_per_mwh"])
    
    # Crear el gráfico
    fig = go.Figure()
    
    # Línea principal
    fig.add_trace(go.Scatter(
        x=hours_range,
        y=cost_per_mwh,
        mode='lines+markers',
        name='Costo USD/MWh',
        line=dict(color='#e74c3c', width=3),
        marker=dict(size=8),
        text=[f"${c:.1f}/MWh" for c in cost_per_mwh],
        textposition="top center",
        hovertemplate='<b>%{x} horas/día</b><br>Costo: $%{y:.1f}/MWh<extra></extra>'
    ))
    
    # Punto actual (4 horas)
    current_hours = int(gd_costs_base["horas_dia_base"])
    if current_hours in hours_range:
        current_cost = cost_per_mwh[hours_range.index(current_hours)]
        fig.add_trace(go.Scatter(
            x=[current_hours],
            y=[current_cost],
            mode='markers+text',
            name='Operación Actual',
            marker=dict(size=15, color='#27ae60', symbol='star'),
            text=[f'Actual<br>${current_cost:.1f}'],
            textposition="bottom center",
            showlegend=False
        ))
    
    # Línea horizontal de referencia (precio compra EdERSA)
    precio_edersa = gd_costs_base["precio_compra_edersa"]
    fig.add_hline(
        y=precio_edersa, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Precio Compra EdERSA: ${precio_edersa}/MWh",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="Curva de Costo USD/MWh vs Horas de Operación Diaria",
        xaxis_title="Horas de Operación Diaria",
        yaxis_title="Costo USD/MWh",
        height=400,
        hovermode='x unified',
        xaxis=dict(
            tickmode='linear',
            tick0=2,
            dtick=1,
            range=[1.5, 12.5]
        ),
        yaxis=dict(
            rangemode='tozero',
            tickformat='$,.0f'
        ),
        showlegend=False
    )
    
    # Agregar anotación con insight
    if 8 in hours_range:
        fig.add_annotation(
            x=8,
            y=cost_per_mwh[hours_range.index(8)],
            text="Punto de equilibrio<br>económico (~8h/día)",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowcolor="#34495e",
            ax=40,
            ay=-40,
            bordercolor="#34495e",
            borderwidth=1,
            bgcolor="rgba(255,255,255,0.9)"
        )
    
    return fig