"""
Tab 1: Vista General del Sistema
"""

from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import math
from pathlib import Path
from dashboard.pages.utils import get_data_manager

def render_overview_tab():
    """Render the overview tab content."""
    # Get data from data manager
    dm = get_data_manager()
    
    return html.Div([
        dbc.Row([
            # Left side - Main unifilar diagram
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-network-wired me-2"),
                        "Diagrama Unifilar Interactivo"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id="f1-unifilar-avanzado",
                            style={"height": "600px"},
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
                                'toImageButtonOptions': {
                                    'format': 'png',
                                    'filename': 'unifilar_linea_sur',
                                    'height': 800,
                                    'width': 1200,
                                    'scale': 2
                                }
                            }
                        )
                    ])
                ], className="shadow")
            ], md=8),
            
            # Right side - Information panels
            dbc.Col([
                # Geographic mini-map
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-map-marked-alt me-2"),
                        "Ubicación Geográfica"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id="f1-geo-map",
                            style={"height": "280px"}
                        )
                    ])
                ], className="shadow mb-3"),
                
                # Station information table
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-list me-2"),
                        "Resumen de Estaciones"
                    ]),
                    dbc.CardBody([
                        html.Div(id="f1-station-table")
                    ])
                ], className="shadow"),
                
                # System information
                dbc.Card([
                    dbc.CardHeader("Información del Sistema"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6("Tensión Nominal:", className="mb-1"),
                                html.P("33 kV", className="mb-0 fw-bold")
                            ], md=4),
                            dbc.Col([
                                html.H6("Operador:", className="mb-1"),
                                html.P("EdERSA - Empresa de Energía Río Negro S.A.", className="mb-0")
                            ], md=4),
                            dbc.Col([
                                html.H6("Estado del Sistema:", className="mb-1"),
                                html.Div([
                                    dbc.Badge("Operativo", color="success", className="me-2"),
                                    dbc.Badge("Con Restricciones", color="warning", className="me-2"),
                                    dbc.Badge("Crítico", color="danger")
                                ])
                            ], md=4)
                        ])
                    ], className="py-2")
                ], className="shadow-sm mt-3")
            ], md=4)
        ])
    ])

@callback(
    Output("f1-unifilar-avanzado", "figure"),
    Input("f1-unifilar-avanzado", "id")
)
def update_advanced_unifilar(_):
    """Create advanced interactive single-line diagram."""
    dm = get_data_manager()
    
    fig = go.Figure()
    
    # Define station data with all details
    # DataManagerV2 returns DataResult, so we need to access .data
    nodes_data = dm.get_nodes().data if dm.get_nodes().data else {}
    
    stations = [
        {
            "name": "Pilcaniyeu",
            "x": 0, "y": 0, "km": 0,
            "data": nodes_data.get("pilcaniyeu", {}),
            "transformer": "25 MVA<br>132/33 kV<br>RBC ±10%",
            "load_mw": 0, "load_mvar": 0
        },
        {
            "name": "Comallo",
            "x": 70, "y": 0, "km": 70,
            "data": nodes_data.get("comallo", {}),
            "transformer": "1.5 MVA<br>33/13.2 kV<br>Dy11",
            "load_mw": 0.30, "load_mvar": 0.10
        },
        {
            "name": "Onelli",
            "x": 120, "y": 0, "km": 120,
            "data": nodes_data.get("onelli", {}),
            "transformer": "40 kVA<br>33/13.2 kV<br>Dyn11",
            "load_mw": 0.10, "load_mvar": 0.04
        },
        {
            "name": "Jacobacci",
            "x": 150, "y": 0, "km": 150,
            "data": nodes_data.get("jacobacci", {}),
            "transformer": "5 MVA<br>33/13.2 kV<br>Dy11",
            "load_mw": 1.45, "load_mvar": 0.60,
            "critical": True
        },
        {
            "name": "Maquinchao",
            "x": 210, "y": 0, "km": 210,
            "data": nodes_data.get("maquinchao", {}),
            "transformer": "0.5 MVA<br>33/13.2 kV<br>Dy11",
            "load_mw": 0.50, "load_mvar": 0.10
        },
        {
            "name": "Aguada",
            "x": 240, "y": 0, "km": 240,
            "data": nodes_data.get("aguada_guerra", {}),
            "transformer": "Sin transf.<br>33 kV",
            "load_mw": 0.05, "load_mvar": 0.01
        },
        {
            "name": "Los Menucos",
            "x": 270, "y": 0, "km": 270,
            "data": nodes_data.get("los_menucos", {}),
            "transformer": "~6 MVA<br>33/13.2 kV<br>Dy11",
            "load_mw": 1.40, "load_mvar": 0.20,
            "critical": True,
            "has_gd": True
        }
    ]
    
    # Draw main 33kV line
    fig.add_trace(go.Scatter(
        x=[s["x"] for s in stations],
        y=[0] * len(stations),
        mode='lines',
        line=dict(color='blue', width=4),
        name='Línea 33 kV',
        hoverinfo='skip'
    ))
    
    # Draw stations
    for i, st in enumerate(stations):
        # Determine color based on criticality
        if st.get("critical"):
            color = 'red'
            symbol = 'square'
            size = 20
        else:
            color = 'darkblue'
            symbol = 'circle'
            size = 15
            
        # Station marker
        fig.add_trace(go.Scatter(
            x=[st["x"]],
            y=[0],
            mode='markers',
            marker=dict(size=size, color=color, symbol=symbol),
            name=st["name"],
            hoverinfo='skip'
        ))
        
        # Station label
        fig.add_annotation(
            x=st["x"], y=0.3,
            text=f"<b>{st['name']}</b><br>{st['km']} km",
            showarrow=False,
            font=dict(size=10)
        )
        
        # Transformer symbol
        fig.add_trace(go.Scatter(
            x=[st["x"], st["x"]],
            y=[0, -0.5],
            mode='lines',
            line=dict(color='gray', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Transformer details
        fig.add_annotation(
            x=st["x"], y=-0.8,
            text=st["transformer"],
            showarrow=False,
            font=dict(size=8),
            bgcolor="lightgray",
            bordercolor="gray"
        )
        
        # Load information
        if st["load_mw"] > 0:
            fig.add_annotation(
                x=st["x"], y=-1.3,
                text=f"P: {st['load_mw']} MW<br>Q: {st['load_mvar']} MVAr",
                showarrow=False,
                font=dict(size=8),
                bgcolor="lightyellow",
                bordercolor="orange"
            )
            
        # GD indication
        if st.get("has_gd"):
            fig.add_annotation(
                x=st["x"], y=-1.8,
                text="🏭 GD 3 MW",
                showarrow=False,
                font=dict(size=10, color="green"),
                bgcolor="lightgreen",
                bordercolor="green"
            )
            
        # Voltage regulation
        if st["name"] in ["Pilcaniyeu", "Jacobacci", "Los Menucos"]:
            fig.add_annotation(
                x=st["x"], y=0.8,
                text="⚡ REG",
                showarrow=False,
                font=dict(size=10, color="red"),
                bgcolor="yellow",
                bordercolor="red"
            )
    
    # Add line segments with impedance info
    segments = [
        {"from": "Pilcaniyeu", "to": "Comallo", "x1": 0, "x2": 70, "conductor": "120 Al/Al"},
        {"from": "Comallo", "to": "Onelli", "x1": 70, "x2": 120, "conductor": "120 Al/Al"},
        {"from": "Onelli", "to": "Jacobacci", "x1": 120, "x2": 150, "conductor": "120 Al/Al"},
        {"from": "Jacobacci", "to": "Maquinchao", "x1": 150, "x2": 210, "conductor": "70 Al/Al"},
        {"from": "Maquinchao", "to": "Aguada", "x1": 210, "x2": 240, "conductor": "70 Al/Al"},
        {"from": "Aguada", "to": "Los Menucos", "x1": 240, "x2": 270, "conductor": "70 Al/Al"}
    ]
    
    for seg in segments:
        fig.add_annotation(
            x=(seg["x1"] + seg["x2"]) / 2,
            y=0.15,
            text=seg["conductor"],
            showarrow=False,
            font=dict(size=8, color="darkgreen")
        )
    
    # Update layout
    fig.update_layout(
        title={
            'text': "Diagrama Unifilar Sistema Línea Sur - 270 km",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(
            title="Distancia (km)",
            range=[-20, 290],
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title="",
            range=[-2.5, 1.5],
            showticklabels=False,
            showgrid=False
        ),
        height=600,
        showlegend=False,
        hovermode='closest',
        plot_bgcolor='white'
    )
    
    return fig

@callback(
    Output("f1-geo-map", "figure"),
    Input("f1-geo-map", "id")
)
def update_geo_map(_):
    """Create geographic map of the system."""
    dm = get_data_manager()
    
    fig = go.Figure()
    
    # Station coordinates and data
    # DataManagerV2 returns DataResult, so we need to access .data
    nodes_data = dm.get_nodes().data if dm.get_nodes().data else {}
    stations = []
    for node_key, node in nodes_data.items():
        if "coordinates" in node:
            stations.append({
                "name": node.get("name", node_key),
                "lat": node["coordinates"]["lat"],
                "lon": node["coordinates"]["lon"],
                "load": node.get("load_mw", 0)
            })
    
    # Sort by longitude (west to east)
    stations.sort(key=lambda x: x["lon"])
    
    # Draw line path
    if len(stations) > 1:
        lats = [s["lat"] for s in stations]
        lons = [s["lon"] for s in stations]
        
        fig.add_trace(go.Scattermapbox(
            mode="lines+markers",
            lon=lons,
            lat=lats,
            marker=dict(size=3, color='blue'),
            name="Línea 33 kV"
        ))
    
    # Draw stations
    lats = [s["lat"] for s in stations]
    lons = [s["lon"] for s in stations]
    names = [s["name"] for s in stations]
    sizes = [10 + s["load"] * 10 for s in stations]
    
    fig.add_trace(go.Scattermapbox(
        mode="markers+text",
        lon=lons,
        lat=lats,
        marker=dict(size=sizes, color='red'),
        text=names,
        textposition="top right",
        name="Estaciones",
        hovertext=names
    ))
    
    # Update layout
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=-41.0, lon=-69.5),
            zoom=7.8  # Aumentado para mejor enfoque inicial
        ),
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=False
    )
    
    return fig

@callback(
    Output("f1-station-table", "children"),
    Input("f1-station-table", "id")
)
def update_station_table(_):
    """Create station summary table."""
    dm = get_data_manager()
    
    # DataManagerV2 returns DataResult, so we need to access .data
    nodes_data = dm.get_nodes().data if dm.get_nodes().data else {}
    
    rows = []
    for node_key, node in nodes_data.items():
        if node.get("type") in ["substation", "switching_station"]:
            # Build hover text
            hover_text = f"<b>{node.get('name', node_key)}</b><br>"
            hover_text += f"Tipo: {node.get('type', 'N/D')}<br>"
            hover_text += f"Dist: {node.get('distance_from_origin_km', 'N/D')} km<br>"
            hover_text += f"Carga: {node.get('load_mw', 0)} MW<br>"
            
            if node.get('load_mw', 0) > 0 or node.get('load_mvar', 0) > 0:
                apparent_power = math.sqrt(node.get('load_mw', 0)**2 + node.get('load_mvar', 0)**2)
                if apparent_power > 0:
                    hover_text += f"FP: {node.get('load_mw', 0)/apparent_power:.3f}<br>"
            
            hover_text += f"Población: {node.get('population', 'N/D'):,}" if node.get('population') else "Población: N/D"
            
            status_badge = dbc.Badge("Normal", color="success")
            if node.get("criticality") == "high":
                status_badge = dbc.Badge("Crítico", color="danger")
            elif node.get("has_regulation"):
                status_badge = dbc.Badge("Con Reg.", color="warning")
                
            row = html.Tr([
                html.Td(node.get('name', node_key)[:15]),
                html.Td(f"{node.get('load_mw', 0):.2f}"),
                html.Td(status_badge)
            ], title=hover_text, style={"cursor": "help"})
            
            rows.append(row)
    
    table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Estación"),
                html.Th("MW"),
                html.Th("Estado")
            ])
        ]),
        html.Tbody(rows)
    ], striped=True, hover=True, size="sm", className="mb-0")
    
    return table