"""
Tab 3: Análisis de Líneas y Conductores
"""

from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import math
from pathlib import Path
from dashboard.pages.utils import get_data_manager

def render_lines_tab():
    """Render the lines tab content."""
    # Get data from data manager
    dm = get_data_manager()
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Análisis de Líneas de Transmisión y Conductores", className="mb-3"),
                html.Hr()
            ])
        ]),
        
        # Summary metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Longitud Total", className="text-muted mb-1"),
                        html.H3("270 km", className="text-primary mb-0"),
                        html.Small("6 tramos", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Conductores", className="text-muted mb-1"),
                        html.H3("2 tipos", className="text-success mb-0"),
                        html.Small("120 y 70 Al/Al", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Pérdidas Totales", className="text-muted mb-1"),
                        html.H3("~130 kW", className="text-warning mb-0"),
                        html.Small("~3.4% carga", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Utilización Térmica", className="text-muted mb-1"),
                        html.H3("<40%", className="text-info mb-0"),
                        html.Small("Con margen", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3)
        ], className="mb-4"),
        
        # Main lines table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-bolt me-2"),
                        "Parámetros Eléctricos de Líneas"
                    ]),
                    dbc.CardBody([
                        html.Div(id="f3-lines-parameters-table")
                    ])
                ], className="shadow")
            ], md=12)
        ], className="mb-4"),
        
        # Visualizations row 1
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Impedancias por Tramo"),
                    dbc.CardBody([
                        dcc.Graph(id="f3-line-impedance-chart")
                    ])
                ], className="shadow")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Pérdidas de Potencia por Tramo"),
                    dbc.CardBody([
                        dcc.Graph(id="f3-line-losses-chart")
                    ])
                ], className="shadow")
            ], md=6)
        ], className="mb-4"),
        
        # Visualizations row 2
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Capacidad Térmica vs Carga Actual"),
                    dbc.CardBody([
                        dcc.Graph(id="f3-line-thermal-chart")
                    ])
                ], className="shadow")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Caída de Tensión Acumulada"),
                    dbc.CardBody([
                        dcc.Graph(id="f3-voltage-drop-chart")
                    ])
                ], className="shadow")
            ], md=6)
        ])
    ])

@callback(
    Output("f3-lines-parameters-table", "children"),
    Input("f3-lines-parameters-table", "id")
)
def update_lines_parameters_table(_):
    """Create detailed lines parameters table."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    edges_result = dm.get_edges()
    edges = edges_result.data if edges_result.data else {}
    
    lines_data = []
    
    for edge_key, edge in edges.items():
        lines_data.append({
            "Tramo": f"{edge.get('from', '')} - {edge.get('to', '')}",
            "Longitud": f"{edge.get('length_km', 0)} km",
            "Conductor": edge.get('conductor', {}).get('type', 'N/D'),
            "R (Ω)": f"{edge.get('total_impedance', {}).get('r_ohm', 0):.2f}",
            "X (Ω)": f"{edge.get('total_impedance', {}).get('x_ohm', 0):.2f}",
            "Z (Ω)": f"{edge.get('total_impedance', {}).get('z_ohm', 0):.2f}",
            "Ángulo": f"{edge.get('total_impedance', {}).get('angle_deg', 0):.1f}°",
            "I máx (A)": edge.get('parameters', {}).get('thermal_limit_amps', 'N/D'),
            "S máx (MVA)": edge.get('parameters', {}).get('thermal_limit_mva', 'N/D')
        })
    
    # Add totals row
    total_r = sum(edge.get('total_impedance', {}).get('r_ohm', 0) for edge in edges.values())
    total_x = sum(edge.get('total_impedance', {}).get('x_ohm', 0) for edge in edges.values())
    total_z = math.sqrt(total_r**2 + total_x**2)
    
    lines_data.append({
        "Tramo": "TOTAL SISTEMA",
        "Longitud": "270 km",
        "Conductor": "Mixto",
        "R (Ω)": f"{total_r:.2f}",
        "X (Ω)": f"{total_x:.2f}",
        "Z (Ω)": f"{total_z:.2f}",
        "Ángulo": f"{math.degrees(math.atan2(total_x, total_r)):.1f}°",
        "I máx (A)": "-",
        "S máx (MVA)": "-"
    })
    
    df = pd.DataFrame(lines_data)
    
    return dbc.Table.from_dataframe(
        df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mb-0",
        style={"fontSize": "0.85rem"}
    )

@callback(
    Output("f3-line-impedance-chart", "figure"),
    Input("f3-line-impedance-chart", "id")
)
def update_line_impedance_chart(_):
    """Create line impedance visualization."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    edges_result = dm.get_edges()
    edges = edges_result.data if edges_result.data else {}
    
    segments = []
    r_values = []
    x_values = []
    z_values = []
    
    for edge_key, edge in edges.items():
        segments.append(f"{edge.get('from', '')} -<br>{edge.get('to', '')}")
        r_values.append(edge.get('total_impedance', {}).get('r_ohm', 0))
        x_values.append(edge.get('total_impedance', {}).get('x_ohm', 0))
        z_values.append(edge.get('total_impedance', {}).get('z_ohm', 0))
    
    fig = go.Figure()
    
    # R component
    fig.add_trace(go.Bar(
        name='R (Resistencia)',
        x=segments,
        y=r_values,
        marker_color='red',
        text=[f"{r:.1f} Ω" for r in r_values],
        textposition='outside'
    ))
    
    # X component
    fig.add_trace(go.Bar(
        name='X (Reactancia)',
        x=segments,
        y=x_values,
        marker_color='blue',
        text=[f"{x:.1f} Ω" for x in x_values],
        textposition='outside'
    ))
    
    # Z magnitude as line
    fig.add_trace(go.Scatter(
        name='Z (Impedancia)',
        x=segments,
        y=z_values,
        mode='lines+markers',
        line=dict(color='green', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Componentes de Impedancia por Tramo",
        xaxis_title="Tramo",
        yaxis=dict(title="R, X (Ω)", side='left'),
        yaxis2=dict(title="Z (Ω)", overlaying='y', side='right'),
        barmode='group',
        height=400,
        hovermode='x unified'
    )
    
    return fig

@callback(
    Output("f3-line-losses-chart", "figure"),
    Input("f3-line-losses-chart", "id")
)
def update_line_losses_chart(_):
    """Create line losses visualization."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    edges_result = dm.get_edges()
    edges = edges_result.data if edges_result.data else {}
    # get_system_summary() returns dict directly in DataManagerV2
    system_summary = dm.get_system_summary()
    
    # Estimate current flow and losses
    segments = []
    losses_kw = []
    percentages = []
    
    # Get total load for starting current
    total_load = system_summary.get('total_load', {}).get('active_power_mw', 3.8)
    
    # Simplified current flow (decreasing from source)
    currents_mw = [total_load, total_load * 0.92, total_load * 0.89, total_load * 0.53, total_load * 0.39, total_load * 0.37]
    
    i = 0
    for edge_key, edge in edges.items():
        segments.append(f"{edge.get('from', '')} - {edge.get('to', '')}")
        
        # Calculate losses: P_loss = I^2 * R
        r_ohm = edge.get('total_impedance', {}).get('r_ohm', 0)
        current_a = (currents_mw[i] * 1000) / (math.sqrt(3) * 33 * 0.95)  # Approximate current
        loss_kw = 3 * (current_a**2) * r_ohm / 1000  # 3-phase losses in kW
        
        losses_kw.append(loss_kw)
        percentages.append((loss_kw / (currents_mw[i] * 1000)) * 100 if currents_mw[i] > 0 else 0)
        i += 1
    
    fig = go.Figure()
    
    # Losses bars
    fig.add_trace(go.Bar(
        x=segments,
        y=losses_kw,
        name='Pérdidas (kW)',
        marker_color='orange',
        text=[f"{loss:.1f} kW<br>{pct:.1f}%" for loss, pct in zip(losses_kw, percentages)],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Pérdidas: %{y:.1f} kW<br>%{text}<extra></extra>'
    ))
    
    # Add total annotation
    total_losses = sum(losses_kw)
    fig.add_annotation(
        x=0.5, y=max(losses_kw) * 1.2,
        text=f"Total: {total_losses:.1f} kW",
        showarrow=False,
        font=dict(size=14, color='red'),
        bgcolor='lightyellow',
        bordercolor='orange'
    )
    
    fig.update_layout(
        title="Pérdidas de Potencia por Tramo",
        xaxis_title="Tramo",
        yaxis_title="Pérdidas (kW)",
        height=400,
        showlegend=False
    )
    
    return fig

@callback(
    Output("f3-line-thermal-chart", "figure"),
    Input("f3-line-thermal-chart", "id")
)
def update_line_thermal_chart(_):
    """Create thermal capacity utilization chart."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    edges_result = dm.get_edges()
    edges = edges_result.data if edges_result.data else {}
    # get_system_summary() returns dict directly in DataManagerV2
    system_summary = dm.get_system_summary()
    
    segments = []
    thermal_limits = []
    actual_loads = []
    utilization = []
    
    # Get total load
    total_load = system_summary.get('total_load', {}).get('active_power_mw', 3.8)
    
    # Approximate current loads based on power flow
    loads_mva = [total_load, total_load * 0.92, total_load * 0.89, total_load * 0.53, total_load * 0.39, total_load * 0.37]
    
    i = 0
    for edge_key, edge in edges.items():
        segments.append(f"{edge.get('from', '')[:8]} -<br>{edge.get('to', '')[:8]}")
        limit = edge.get('parameters', {}).get('thermal_limit_mva', 16)
        thermal_limits.append(limit)
        actual_loads.append(loads_mva[i])
        utilization.append((loads_mva[i] / limit) * 100)
        i += 1
    
    fig = go.Figure()
    
    # Thermal limit bars
    fig.add_trace(go.Bar(
        name='Capacidad Térmica',
        x=segments,
        y=thermal_limits,
        marker_color='lightgray',
        opacity=0.5
    ))
    
    # Actual load bars
    fig.add_trace(go.Bar(
        name='Carga Actual',
        x=segments,
        y=actual_loads,
        marker_color=['green' if u < 70 else 'orange' if u < 90 else 'red' for u in utilization],
        text=[f"{load:.1f} MVA<br>{u:.0f}%" for load, u in zip(actual_loads, utilization)],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Capacidad Térmica vs Carga Actual por Tramo",
        xaxis_title="Tramo",
        yaxis_title="Potencia (MVA)",
        barmode='overlay',
        height=400,
        showlegend=True
    )
    
    return fig

@callback(
    Output("f3-voltage-drop-chart", "figure"),
    Input("f3-voltage-drop-chart", "id")
)
def update_voltage_drop_chart(_):
    """Create cumulative voltage drop visualization."""
    
    # Voltage profile along the line
    stations = ['Pilcaniyeu', 'Comallo', 'Onelli', 'Jacobacci', 'Maquinchao', 'Aguada', 'Los Menucos']
    distances = [0, 70, 120, 150, 210, 240, 270]
    
    # Estimated voltage levels (p.u.)
    voltage_no_reg = [1.00, 0.92, 0.85, 0.80, 0.70, 0.65, 0.59]  # Without regulation
    voltage_with_reg = [1.00, 0.97, 0.94, 0.95, 0.90, 0.87, 0.85]  # With regulation
    
    fig = go.Figure()
    
    # Without regulation line
    fig.add_trace(go.Scatter(
        x=distances,
        y=voltage_no_reg,
        mode='lines+markers',
        name='Sin Regulación',
        line=dict(color='red', width=3, dash='dash'),
        marker=dict(size=8),
        text=[f'{v:.2f} pu' for v in voltage_no_reg],
        textposition='bottom center'
    ))
    
    # With regulation line
    fig.add_trace(go.Scatter(
        x=distances,
        y=voltage_with_reg,
        mode='lines+markers',
        name='Con Regulación',
        line=dict(color='blue', width=3),
        marker=dict(size=10),
        text=[f'{v:.2f} pu' for v in voltage_with_reg],
        textposition='top center'
    ))
    
    # Add station names
    for i, (dist, station) in enumerate(zip(distances, stations)):
        fig.add_annotation(
            x=dist,
            y=0.55,
            text=station,
            showarrow=False,
            font=dict(size=9),
            textangle=-45
        )
    
    # Add regulation points
    reg_points = [
        {"km": 0, "name": "RBC", "y": 1.00},
        {"km": 150, "name": "Reg Serie", "y": 0.95},
        {"km": 270, "name": "Reg Serie", "y": 0.85}
    ]
    
    for reg in reg_points:
        fig.add_annotation(
            x=reg["km"],
            y=reg["y"],
            text=f"⚡ {reg['name']}",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-30,
            bgcolor="yellow",
            bordercolor="orange"
        )
    
    # Add acceptable voltage limits
    fig.add_hline(y=0.95, line_dash="dot", line_color="green",
                  annotation_text="Límite superior aceptable (0.95 pu)")
    fig.add_hline(y=0.90, line_dash="dot", line_color="orange",
                  annotation_text="Límite inferior aceptable (0.90 pu)")
    
    fig.update_layout(
        title="Perfil de Tensión a lo Largo del Sistema",
        xaxis_title="Distancia desde Pilcaniyeu (km)",
        yaxis_title="Tensión (p.u.)",
        yaxis_range=[0.5, 1.05],
        height=400,
        hovermode='x unified'
    )
    
    return fig