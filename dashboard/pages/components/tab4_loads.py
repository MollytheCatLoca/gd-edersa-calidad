"""
Tab 4: Cargas y Factor de Potencia
"""

from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import math
from pathlib import Path
from dashboard.pages.utils import get_data_manager

def render_loads_tab():
    """Render the loads tab content."""
    # Get data from data manager
    dm = get_data_manager()
    # get_system_summary() returns dict directly in DataManagerV2
    system_summary = dm.get_system_summary()
    # DataManagerV2 returns DataResult, so we need to access .data
    nodes_result = dm.get_nodes()
    nodes = nodes_result.data if nodes_result.data else {}
    
    # Get totals from system summary
    total_load = system_summary.get('total_load', {})
    total_mw = total_load.get('active_power_mw', 3.80)
    total_mvar = total_load.get('reactive_power_mvar', 1.05)
    total_mva = total_load.get('apparent_power_mva', 3.943)
    avg_pf = total_load.get('power_factor', 0.964)
    
    # Count stations with load
    stations_with_load = sum(1 for node in nodes.values() if node.get('load_mw', 0) > 0)
    total_stations = len([n for n in nodes.values() if n.get('type') in ['substation', 'switching_station']])
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Análisis Detallado de Cargas y Factor de Potencia", className="mb-3"),
                html.Hr()
            ])
        ]),
        
        # Summary metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Carga Total Sistema", className="text-muted mb-1"),
                        html.H3(f"{total_mw:.2f} MW", className="text-primary mb-0"),
                        html.Small(f"{total_mvar:.2f} MVAr | {total_mva:.2f} MVA", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Factor Potencia Promedio", className="text-muted mb-1"),
                        html.H3(f"{avg_pf:.3f}", className="text-success mb-0"),
                        html.Small("Inductivo", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Concentración Crítica", className="text-muted mb-1"),
                        html.H3("75%", className="text-warning mb-0"),
                        html.Small("Jacobacci + Los Menucos", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Estaciones con Carga", className="text-muted mb-1"),
                        html.H3(f"{stations_with_load} de {total_stations}", className="text-info mb-0"),
                        html.Small("Con carga activa", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3)
        ], className="mb-4"),
        
        # Main loads table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-plug me-2"),
                        "Detalle de Cargas por Estación Transformadora"
                    ]),
                    dbc.CardBody([
                        html.Div(id="f4-loads-detail-table")
                    ])
                ], className="shadow")
            ], md=12)
        ], className="mb-4"),
        
        # Visualizations row 1
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Distribución de Potencia Activa"),
                    dbc.CardBody([
                        dcc.Graph(id="f4-active-power-distribution")
                    ])
                ], className="shadow")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Factor de Potencia por Estación"),
                    dbc.CardBody([
                        dcc.Graph(id="f4-power-factor-analysis")
                    ])
                ], className="shadow")
            ], md=6)
        ], className="mb-4"),
        
        # Visualizations row 2
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Triángulo de Potencias"),
                    dbc.CardBody([
                        dcc.Graph(id="f4-power-triangle")
                    ])
                ], className="shadow")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Análisis Temporal de Demanda"),
                    dbc.CardBody([
                        dcc.Graph(id="f4-demand-temporal")
                    ])
                ], className="shadow")
            ], md=6)
        ]),
        
        # Additional analysis row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-line me-2"),
                        "Análisis de Criticidad y Compensación"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6("Puntos Críticos Identificados:", className="mb-3"),
                                html.Ul([
                                    html.Li([
                                        html.Strong("Jacobacci: "),
                                        "38.2% de la carga total, FP = 0.924 (requiere compensación)"
                                    ]),
                                    html.Li([
                                        html.Strong("Los Menucos: "),
                                        "36.8% de la carga total, FP = 0.990 (excelente)"
                                    ]),
                                    html.Li([
                                        html.Strong("Concentración: "),
                                        "75% de carga en solo 2 puntos aumenta vulnerabilidad"
                                    ])
                                ])
                            ], md=6),
                            dbc.Col([
                                html.H6("Oportunidades de Mejora:", className="mb-3"),
                                html.Ul([
                                    html.Li("Compensación reactiva en Jacobacci: ~400 kVAr"),
                                    html.Li("Posible compensación en Comallo: ~50 kVAr"),
                                    html.Li("Evaluar redistribución de cargas para reducir concentración"),
                                    html.Li("Considerar GD en puntos de alta demanda")
                                ])
                            ], md=6)
                        ])
                    ])
                ], className="shadow")
            ], md=12)
        ], className="mt-4")
    ])

@callback(
    Output("f4-loads-detail-table", "children"),
    Input("f4-loads-detail-table", "id")
)
def update_loads_detail_table(_):
    """Create detailed loads table."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    nodes_result = dm.get_nodes()
    nodes = nodes_result.data if nodes_result.data else {}
    # get_system_summary() returns dict directly in DataManagerV2
    system_summary = dm.get_system_summary()
    
    # Get total from system summary
    total_mw = system_summary.get('total_load', {}).get('active_power_mw', 3.80)
    
    # Create loads data
    loads_data = []
    for node_key, node in nodes.items():
        if node.get("load_mw", 0) > 0 or node.get("load_mvar", 0) > 0:
            load_mw = node.get("load_mw", 0)
            load_mvar = node.get("load_mvar", 0)
            load_mva = math.sqrt(load_mw**2 + load_mvar**2)
            pf = load_mw / load_mva if load_mva > 0 else 1.0
            
            loads_data.append({
                "Estación": node.get("name", node_key),
                "P [MW]": f"{load_mw:.2f}",
                "Q [MVAr]": f"{load_mvar:.2f}",
                "S [MVA]": f"{load_mva:.3f}",
                "FP": f"{pf:.3f}",
                "% del Total": f"{(load_mw/total_mw)*100:.1f}%" if total_mw > 0 else "0%",
                "Población": f"{node.get('population', 'N/D'):,}" if node.get('population') else "N/D",
                "Criticidad": "Alta" if node.get("criticality") == "high" else "Normal",
                "kW/habitante": f"{(load_mw*1000/node.get('population', 1)):.1f}" if node.get('population') else "N/D"
            })
    
    # Add totals row from system summary
    total_load = system_summary.get('total_load', {})
    total_population = sum(node.get('population', 0) for node in nodes.values() if node.get('population'))
    
    loads_data.append({
        "Estación": "TOTAL SISTEMA",
        "P [MW]": f"{total_load.get('active_power_mw', 3.80):.2f}",
        "Q [MVAr]": f"{total_load.get('reactive_power_mvar', 1.05):.2f}",
        "S [MVA]": f"{total_load.get('apparent_power_mva', 3.943):.3f}",
        "FP": f"{total_load.get('power_factor', 0.964):.3f}",
        "% del Total": "100%",
        "Población": f"~{total_population:,}" if total_population > 0 else "N/D",
        "Criticidad": "-",
        "kW/habitante": f"{(total_load.get('active_power_mw', 3.80)*1000/total_population):.0f}" if total_population > 0 else "N/D"
    })
    
    df = pd.DataFrame(loads_data)
    
    return dbc.Table.from_dataframe(
        df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mb-0",
        style={"fontSize": "0.9rem"}
    )

@callback(
    Output("f4-active-power-distribution", "figure"),
    Input("f4-active-power-distribution", "id")
)
def update_active_power_distribution(_):
    """Create active power distribution chart."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    nodes_result = dm.get_nodes()
    nodes = nodes_result.data if nodes_result.data else {}
    
    # Extract load data
    stations = []
    loads_mw = []
    colors = []
    
    for node_key, node in nodes.items():
        if node.get("load_mw", 0) > 0:
            stations.append(node.get("name", node_key))
            loads_mw.append(node.get("load_mw", 0))
            colors.append("red" if node.get("criticality") == "high" else "blue")
    
    # Create pie chart
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=stations,
        values=loads_mw,
        hole=0.4,
        marker_colors=colors,
        textfont_size=12,
        textposition='auto',
        textinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>' +
                      'Potencia: %{value} MW<br>' +
                      'Porcentaje: %{percent}<br>' +
                      '<extra></extra>'
    ))
    
    fig.update_layout(
        title="Distribución de Potencia Activa por Estación",
        annotations=[dict(text='3.80 MW<br>Total', x=0.5, y=0.5, font_size=16, showarrow=False)],
        height=400,
        showlegend=True
    )
    
    return fig

@callback(
    Output("f4-power-factor-analysis", "figure"),
    Input("f4-power-factor-analysis", "id")
)
def update_power_factor_analysis(_):
    """Create power factor analysis chart."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    nodes_result = dm.get_nodes()
    nodes = nodes_result.data if nodes_result.data else {}
    
    stations = []
    power_factors = []
    colors = []
    
    for node_key, node in nodes.items():
        if node.get("load_mw", 0) > 0:
            load_mw = node.get("load_mw", 0)
            load_mvar = node.get("load_mvar", 0)
            load_mva = math.sqrt(load_mw**2 + load_mvar**2)
            pf = load_mw / load_mva if load_mva > 0 else 1.0
            
            stations.append(node.get("name", node_key))
            power_factors.append(pf)
            
            # Color based on PF value
            if pf >= 0.95:
                colors.append("green")
            elif pf >= 0.90:
                colors.append("orange")
            else:
                colors.append("red")
    
    fig = go.Figure()
    
    # Bar chart
    fig.add_trace(go.Bar(
        x=stations,
        y=power_factors,
        marker_color=colors,
        text=[f"{pf:.3f}" for pf in power_factors],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>FP: %{y:.3f}<extra></extra>'
    ))
    
    # Add reference lines
    fig.add_hline(y=0.95, line_dash="dash", line_color="green", 
                  annotation_text="Objetivo FP ≥ 0.95")
    fig.add_hline(y=0.90, line_dash="dot", line_color="orange",
                  annotation_text="Mínimo aceptable FP = 0.90")
    
    fig.update_layout(
        title="Factor de Potencia por Estación",
        xaxis_title="Estación",
        yaxis_title="Factor de Potencia",
        yaxis_range=[0.85, 1.05],
        height=400,
        showlegend=False
    )
    
    return fig

@callback(
    Output("f4-power-triangle", "figure"),
    Input("f4-power-triangle", "id")
)
def update_power_triangle(_):
    """Create power triangle visualization."""
    dm = get_data_manager()
    # get_system_summary() returns dict directly in DataManagerV2
    system_summary = dm.get_system_summary()
    # DataManagerV2 returns DataResult, so we need to access .data
    nodes_result = dm.get_nodes()
    nodes = nodes_result.data if nodes_result.data else {}
    
    fig = go.Figure()
    
    # System total power triangle from system summary
    total_load = system_summary.get('total_load', {})
    P = total_load.get('active_power_mw', 3.80)  # MW
    Q = total_load.get('reactive_power_mvar', 1.05)  # MVAr
    S = total_load.get('apparent_power_mva', math.sqrt(P**2 + Q**2))  # MVA
    angle = math.degrees(math.atan2(Q, P))
    pf = total_load.get('power_factor', 0.964)
    
    # Draw triangle
    fig.add_trace(go.Scatter(
        x=[0, P, P, 0],
        y=[0, 0, Q, 0],
        mode='lines+markers',
        fill='toself',
        fillcolor='rgba(0,100,200,0.2)',
        line=dict(color='blue', width=3),
        name='Sistema Total',
        hoverinfo='skip'
    ))
    
    # Add arrows and labels
    # Active power arrow
    fig.add_annotation(
        x=P/2, y=-0.1,
        text=f"P = {P} MW",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="green",
        ax=0,
        ay=-30,
        font=dict(size=14, color="green")
    )
    
    # Reactive power arrow
    fig.add_annotation(
        x=P+0.1, y=Q/2,
        text=f"Q = {Q} MVAr",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="red",
        ax=30,
        ay=0,
        font=dict(size=14, color="red")
    )
    
    # Apparent power arrow
    fig.add_annotation(
        x=P/2, y=Q/2,
        text=f"S = {S:.2f} MVA",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="blue",
        ax=-30,
        ay=-30,
        font=dict(size=14, color="blue")
    )
    
    # Angle annotation
    fig.add_annotation(
        x=0.5, y=0.1,
        text=f"φ = {angle:.1f}°<br>cos φ = {pf:.3f}",
        showarrow=False,
        font=dict(size=12),
        bgcolor="white",
        bordercolor="black"
    )
    
    # Add individual station triangles for critical nodes
    stations_data = []
    critical_nodes = ['jacobacci', 'los_menucos']
    colors = ["rgba(255,0,0,0.1)", "rgba(0,255,0,0.1)"]
    
    for i, node_key in enumerate(critical_nodes):
        if node_key in nodes:
            node = nodes[node_key]
            stations_data.append({
                "name": node.get('name', node_key.title()),
                "P": node.get('load_mw', 0),
                "Q": node.get('load_mvar', 0),
                "color": colors[i]
            })
    
    for st in stations_data:
        fig.add_trace(go.Scatter(
            x=[0, st["P"], st["P"], 0],
            y=[0, 0, st["Q"], 0],
            mode='lines',
            fill='toself',
            fillcolor=st["color"],
            line=dict(width=1, dash='dash'),
            name=st["name"],
            hovertemplate=f'<b>{st["name"]}</b><br>P: {st["P"]} MW<br>Q: {st["Q"]} MVAr<extra></extra>'
        ))
    
    fig.update_layout(
        title="Triángulo de Potencias del Sistema",
        xaxis_title="Potencia Activa P (MW)",
        yaxis_title="Potencia Reactiva Q (MVAr)",
        xaxis_range=[-0.5, 4.5],
        yaxis_range=[-0.5, 1.5],
        height=400,
        showlegend=True,
        hovermode='closest'
    )
    
    return fig

@callback(
    Output("f4-demand-temporal", "figure"),
    Input("f4-demand-temporal", "id")
)
def update_demand_temporal(_):
    """Create temporal demand analysis chart."""
    dm = get_data_manager()
    system_summary = dm.get_system_summary()
    
    # Get total loads
    total_load_data = system_summary.get('total_load', {})
    peak_mw = total_load_data.get('active_power_mw', 3.80)
    peak_mvar = total_load_data.get('reactive_power_mvar', 1.05)
    
    # Simulated typical daily profile
    hours = list(range(24))
    
    # Base profile (normalized)
    base_profile = [0.6, 0.55, 0.52, 0.50, 0.52, 0.60, 0.75, 0.85, 
                    0.90, 0.88, 0.85, 0.82, 0.80, 0.82, 0.85, 0.88,
                    0.92, 0.95, 1.00, 0.98, 0.95, 0.88, 0.80, 0.70]
    
    # Apply to total load
    total_load = [peak_mw * factor for factor in base_profile]
    
    # Estimate reactive power profile
    reactive_profile = [peak_mvar * factor * (0.9 + 0.1 * (1-factor)) for factor in base_profile]
    
    fig = go.Figure()
    
    # Active power
    fig.add_trace(go.Scatter(
        x=hours,
        y=total_load,
        mode='lines+markers',
        name='Potencia Activa (MW)',
        line=dict(color='blue', width=3),
        marker=dict(size=6),
        hovertemplate='Hora: %{x}:00<br>P: %{y:.2f} MW<extra></extra>'
    ))
    
    # Reactive power
    fig.add_trace(go.Scatter(
        x=hours,
        y=reactive_profile,
        mode='lines+markers',
        name='Potencia Reactiva (MVAr)',
        line=dict(color='red', width=2, dash='dash'),
        marker=dict(size=5),
        hovertemplate='Hora: %{x}:00<br>Q: %{y:.2f} MVAr<extra></extra>'
    ))
    
    # Add peak hour annotation
    fig.add_annotation(
        x=18, y=peak_mw,
        text=f"Pico: 19:00 hs<br>{peak_mw:.2f} MW",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-40,
        bgcolor="yellow",
        bordercolor="orange"
    )
    
    # Add critical zone (above 95% of peak)
    critical_threshold = peak_mw * 0.95
    fig.add_hrect(
        y0=critical_threshold, y1=peak_mw * 1.05,
        fillcolor="red", opacity=0.1,
        annotation_text="Zona crítica - Sin margen",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title="Perfil Típico de Demanda Diaria",
        xaxis_title="Hora del día",
        yaxis_title="Potencia",
        xaxis=dict(tickmode='linear', tick0=0, dtick=2),
        height=400,
        hovermode='x unified',
        legend=dict(x=0.02, y=0.98)
    )
    
    return fig