"""
Fase 2 - Modelado y Visualización de Topología
"""

from dash import dcc, html, Input, Output, State, callback
import dash
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.network import NetworkTopology, NetworkVisualizer
import dash_bootstrap_components as dbc
from dashboard.pages.utils import get_data_manager

# Register page
dash.register_page(__name__, path='/fase2-topologia', name='Fase 2: Topología', title='Topología del Sistema')

# Initialize the network and data manager
dm = get_data_manager()
network = NetworkTopology()

# Load network data from DataManager
nodes_result = dm.get_nodes()
edges_result = dm.get_edges()

if nodes_result.ok() and edges_result.ok():
    # Check if data is already a dict or needs conversion
    if isinstance(nodes_result.data, dict):
        network.nodes_data = nodes_result.data
    else:
        network.nodes_data = {node['id']: node for node in nodes_result.data}
    
    if isinstance(edges_result.data, dict):
        network.edges_data = edges_result.data
    else:
        network.edges_data = {edge['id']: edge for edge in edges_result.data}
    
    network._build_graph()
else:
    # Fallback to empty network if data not available
    print("Warning: Could not load network data from DataManager")

visualizer = NetworkVisualizer(network)

# Define color palette
colors = {
    'background': '#f8f9fa',
    'text': '#212529',
    'primary': '#0d6efd',
    'success': '#198754',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#0dcaf0'
}

# Helper functions from original app
def create_network_figure():
    """Create the main network visualization."""
    # Get GD data from DataManager
    gd_costs = dm.get_gd_costs()
    
    pos = {}
    for node in network.graph.nodes():
        node_data = network.graph.nodes[node]
        # Try different coordinate formats
        if 'coordinates' in node_data:
            coords = node_data['coordinates']
            if isinstance(coords, dict) and 'lon' in coords and 'lat' in coords:
                pos[node] = (coords['lon'], coords['lat'])
            elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
                pos[node] = (coords[0], coords[1])
        elif 'position' in node_data:
            # Alternative: position attribute
            position = node_data['position']
            if isinstance(position, (list, tuple)) and len(position) >= 2:
                pos[node] = (position[0], position[1])
        else:
            # Default positions if coordinates not available
            default_positions = {
                'pilcaniyeu': (-70.56, -41.09),
                'comallo': (-70.26, -41.03),
                'jacobacci': (-69.55, -41.33),
                'maquinchao': (-68.73, -41.25),
                'los_menucos': (-68.08, -40.84)
            }
            pos[node] = default_positions.get(node.lower(), (-69.0, -41.0))
    
    # Create edge traces
    edge_traces = []
    for edge in network.graph.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        edge_data = edge[2] if len(edge) > 2 else {}
        conductor_type = edge_data.get('conductor_type', '')
        if '120' in str(conductor_type):
            color = 'blue'
            width = 4
        else:
            color = 'darkblue'
            width = 3
        
        # For now, just create lines with multiple points
        edge_trace = go.Scattermapbox(
            lon=[x0, x1, None],  # None creates a break
            lat=[y0, y1, None],
            mode='lines+markers',
            marker=dict(size=2, color=color),
            hoverinfo='text',
            hovertext=f"{edge_data.get('length_km', 'N/A')} km - {edge_data.get('conductor_type', 'N/A')}",
            showlegend=False
        )
        edge_traces.append(edge_trace)
    
    # Create node trace
    node_lon = []
    node_lat = []
    node_text = []
    node_size = []
    node_color = []
    
    for node in network.graph.nodes():
        lon, lat = pos[node]
        node_lon.append(lon)
        node_lat.append(lat)
        
        node_data = network.graph.nodes[node]
        text = f"<b>{node_data.get('name', node.upper())}</b><br>"
        text += f"Carga: {node_data.get('load_mw', 0):.2f} MW<br>"
        if 'distance_from_origin_km' in node_data:
            text += f"Distancia: {node_data['distance_from_origin_km']} km"
        if node_data.get('population'):
            text += f"<br>Población: {node_data['population']:,}"
        node_text.append(text)
        
        size = 15 + node_data.get('load_mw', 0) * 10
        node_size.append(size)
        
        if node_data.get('criticality') == 'high':
            node_color.append(colors['danger'])
        elif node_data.get('load_mw', 0) > 0.5:
            node_color.append(colors['warning'])
        else:
            node_color.append(colors['success'])
    
    node_trace = go.Scattermapbox(
        lon=node_lon,
        lat=node_lat,
        mode='markers+text',
        marker=dict(
            size=node_size,
            color=node_color,
            sizemode='diameter'
        ),
        text=[n.get('name', node_id.upper()) for node_id, n in network.graph.nodes(data=True)],
        textposition="top center",
        hoverinfo='text',
        hovertext=node_text,
        showlegend=False
    )
    
    # Add GD marker for Los Menucos
    gd_trace = None
    gd_node_id = None
    # Look for Los Menucos node (case insensitive)
    for node_id in network.graph.nodes:
        if 'menucos' in node_id.lower():
            gd_node_id = node_id
            break
    
    if gd_node_id and gd_node_id in pos:
        gd_pos = pos[gd_node_id]
        gd_trace = go.Scattermapbox(
            lon=[gd_pos[0]],
            lat=[gd_pos[1] - 0.05],  # Slightly offset
            mode='markers+text',
            marker=dict(
                size=20,
                color='purple',
                symbol='square'
            ),
            text=['GD 1.8 MW'],
            textposition="bottom center",
            hoverinfo='text',
            hovertext=f"<b>Generación Distribuida</b><br>" +
                      f"Potencia actual: {gd_costs['potencia_mw']} MW<br>" +
                      f"Expansión planificada: {gd_costs['potencia_expansion_mw']} MW<br>" +
                      f"Operación: {gd_costs['horas_dia_base']}h/día<br>" +
                      f"Costo: ${gd_costs['costo_por_mwh']}/MWh<br>" +
                      f"<b>🟢 DATO</b> (Facturas 2024)",
            showlegend=False
        )
    
    traces = edge_traces + [node_trace]
    if gd_trace:
        traces.append(gd_trace)
    
    fig = go.Figure(data=traces)
    
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(
                lat=np.mean([pos[node][1] for node in network.graph.nodes()]),
                lon=np.mean([pos[node][0] for node in network.graph.nodes()])
            ),
            zoom=7.8  # Aumentado para mejor enfoque inicial
        ),
        showlegend=False,
        height=600,
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    
    return fig

def create_voltage_profile():
    """Create voltage profile chart with data source indicators."""
    # Get data from DataManager
    dm = get_data_manager()
    theoretical_voltages = dm.get_theoretical_voltages()
    real_measurements = dm.get_real_measurements()
    
    nodes = sorted(network.graph.nodes(), 
                  key=lambda n: network.graph.nodes[n].get('distance_from_origin_km', 0))
    
    distances = []
    voltages_estimated = []
    voltages_real = []
    names = []
    
    for node in nodes:
        node_data = network.graph.nodes[node]
        node_name = node_data.get('name', node.upper()).upper()
        dist = node_data.get('distance_from_origin_km', 0)
        
        distances.append(dist)
        names.append(node_data.get('name', node.upper()))
        
        # Get theoretical voltage from DataManager
        if node_name in theoretical_voltages['voltages']:
            v_theoretical = theoretical_voltages['voltages'][node_name]['value']
        else:
            # Calculate if not in DataManager (shouldn't happen)
            v_theoretical = max(0.7, 1.0 - dist * theoretical_voltages['drop_rate_per_km'])
        
        voltages_estimated.append(v_theoretical)
        
        # Get real voltage if available
        if real_measurements['voltages']['available'] and node_name in real_measurements['voltages']:
            real_v = real_measurements['voltages'][node_name]['value']
        else:
            real_v = None
        
        voltages_real.append(real_v)
    
    fig = go.Figure()
    
    # Add estimated voltage line
    fig.add_trace(go.Scatter(
        x=distances,
        y=voltages_estimated,
        mode='lines+markers',
        name='Tensión Estimada 🟡',
        line=dict(color='orange', dash='dash'),
        marker=dict(size=8),
        hovertemplate='<b>%{text}</b><br>Distancia: %{x} km<br>Tensión: %{y:.3f} pu<br>🟡 ESTIMADO<extra></extra>',
        text=names
    ))
    
    # Add real voltage points where available
    real_distances = [d for i, d in enumerate(distances) if voltages_real[i] is not None]
    real_voltages_filtered = [v for v in voltages_real if v is not None]
    real_names = [names[i] for i, v in enumerate(voltages_real) if v is not None]
    
    if real_distances:
        fig.add_trace(go.Scatter(
            x=real_distances,
            y=real_voltages_filtered,
            mode='markers',
            name='Tensión Medida 🟢',
            marker=dict(size=12, color='green', symbol='circle'),
            hovertemplate='<b>%{text}</b><br>Distancia: %{x} km<br>Tensión: %{y:.3f} pu<br>🟢 DATO REAL<extra></extra>',
            text=real_names
        ))
    
    # Add regulatory limit line
    fig.add_trace(go.Scatter(
        x=[0, 270],
        y=[0.95, 0.95],
        mode='lines',
        name='Límite Regulatorio (0.95 pu)',
        line=dict(color='red', dash='dot', width=2),
        hovertemplate='Límite mínimo: 0.95 pu<extra></extra>'
    ))
    
    fig.add_hline(y=1.05, line_dash="dash", line_color="red", 
                  annotation_text="Límite superior (1.05 pu)")
    fig.add_hline(y=0.95, line_dash="dash", line_color="red",
                  annotation_text="Límite inferior (0.95 pu)")
    fig.add_hline(y=1.0, line_dash="dot", line_color="green",
                  annotation_text="Nominal (1.0 pu)")
    
    # Add fill for critical zone
    fig.add_trace(go.Scatter(
        x=distances + distances[::-1],
        y=[0.95]*len(distances) + voltages_estimated[::-1],
        fill='toself',
        fillcolor='rgba(255,0,0,0.2)',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip',
        name='Zona Crítica'
    ))
    
    fig.update_layout(
        title="Perfil de Tensión del Sistema",
        xaxis_title="Distancia desde Pilcaniyeu (km)",
        yaxis_title="Tensión (pu)",
        yaxis_range=[0.65, 1.1],
        height=400,
        template="plotly_white",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        annotations=[
            dict(
                xref="paper", yref="paper",
                x=0.02, y=0.02,
                xanchor="left", yanchor="bottom",
                text="⚠️ NOTA: Valores estimados con caída típica 0.15%/km<br>Los datos reales de tensión están disponibles en Fase 3",
                showarrow=False,
                font=dict(size=10),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="orange",
                borderwidth=1
            )
        ]
    )
    
    return fig

def create_load_distribution():
    """Create load distribution chart."""
    nodes_data = []
    for node in network.graph.nodes():
        node_info = network.graph.nodes[node]
        nodes_data.append({
            'Estación': node_info.get('name', node.upper()),
            'Carga (MW)': node_info.get('load_mw', 0),
            'Carga (MVAr)': node_info.get('load_mvar', 0),
            'Población': node_info.get('population', 0)
        })
    
    df = pd.DataFrame(nodes_data)
    df = df[df['Carga (MW)'] > 0].sort_values('Carga (MW)', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df['Estación'],
        x=df['Carga (MW)'],
        name='MW',
        orientation='h',
        marker_color=colors['primary']
    ))
    
    fig.add_trace(go.Bar(
        y=df['Estación'],
        x=df['Carga (MVAr)'],
        name='MVAr',
        orientation='h',
        marker_color=colors['info']
    ))
    
    fig.update_layout(
        title="Distribución de Cargas por Estación",
        xaxis_title="Potencia",
        barmode='group',
        height=400,
        template="plotly_white"
    )
    
    return fig

def create_losses_visualization():
    """Create power losses visualization by segment."""
    # Get data from DataManager
    dm = get_data_manager()
    theoretical_losses = dm.get_theoretical_losses()
    
    segments = []
    losses_mw = []
    percentages = []
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for i, segment in enumerate(theoretical_losses['segments']):
        segments.append(segment['name'])
        losses_mw.append(segment['loss_mw'])
        percentages.append(segment['loss_percentage'])
    
    total_loss = theoretical_losses['total']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=segments,
        y=losses_mw,
        text=[f'{l:.2f} MW<br>({p}%)' for l, p in zip(losses_mw, percentages)],
        textposition='outside',
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>Pérdidas: %{y:.2f} MW<br>🟡 ' + theoretical_losses['segments'][0]['type'] + '<extra></extra>'
    ))
    
    fig.update_layout(
        title="Pérdidas Estimadas por Tramo",
        yaxis_title="Pérdidas (MW)",
        xaxis_title="Tramo",
        height=350,
        template="plotly_white",
        annotations=[
            dict(
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                xanchor="left", yanchor="top",
                text=f"Total: {total_loss['loss_mw']} MW ({total_loss['loss_percentage']}%) 🟡 {total_loss['type']}",
                showarrow=False,
                font=dict(size=12, color="red"),
                bgcolor="rgba(255,255,255,0.8)"
            )
        ]
    )
    
    return fig

# Define layout
layout = html.Div([
    # Header
    html.Div([
        html.H2("Fase 2: Modelado y Visualización de Topología", className="mb-3"),
        html.P("Representación digital del sistema eléctrico con análisis de impedancias y cargas.", 
               className="text-muted mb-4")
    ]),
    
    # Legend for data types
    dbc.Alert([
        html.H6("Leyenda de Tipos de Datos:", className="alert-heading"),
        html.Div([
            html.Span("🟢 DATO REAL ", style={'color': 'green', 'fontWeight': 'bold'}),
            html.Span("(medido/documentado) | ", className="mx-2"),
            html.Span("🟡 ESTIMADO ", style={'color': 'orange', 'fontWeight': 'bold'}),
            html.Span("(calculado/aproximado) | ", className="mx-2"),
            html.Span("🔵 REFERENCIA ", style={'color': 'blue', 'fontWeight': 'bold'}),
            html.Span("(catálogo/teórico)", className="mx-2")
        ])
    ], color="info", className="mb-4"),
    
    # Main content
    html.Div([
        # Map section
        html.Div([
            html.H4("Mapa Interactivo del Sistema", className="mb-3"),
            dcc.Graph(
                id='network-map-f2',
                figure=create_network_figure(),
                style={'height': '600px'}
            )
        ], className="card p-3 mb-4"),
        
        # Charts row
        html.Div([
            # Voltage profile
            html.Div([
                dcc.Graph(
                    id='voltage-profile-f2',
                    figure=create_voltage_profile()
                )
            ], className="col-md-6"),
            
            # Load distribution
            html.Div([
                dcc.Graph(
                    id='load-distribution-f2',
                    figure=create_load_distribution()
                )
            ], className="col-md-6"),
        ], className="row"),
        
        # Losses visualization
        html.Div([
            html.H4("Análisis de Pérdidas Técnicas", className="mb-3"),
            dcc.Graph(
                id='losses-distribution-f2',
                figure=create_losses_visualization()
            )
        ], className="card p-3 mb-4"),
        
        # GD Los Menucos Panel
        html.Div([
            html.H4("Estado de la Generación Distribuida - Los Menucos", className="mb-3"),
            dbc.Card([
                dbc.CardBody(id="gd-panel-content")
            ], className="mb-4")
        ]),
        
        # Technical summary
        html.Div([
            html.H4("Resumen Técnico", className="mb-3"),
            html.Div([
                html.Div([
                    html.H5("Impedancias Acumuladas", className="card-title"),
                    html.P("🔵 REFERENCIA - Valores calculados según catálogo de conductores", 
                          className="text-muted small"),
                    html.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("Estación"),
                                html.Th("Distancia (km) 🟢"),
                                html.Th("R (Ω) 🔵"),
                                html.Th("X (Ω) 🔵"),
                                html.Th("Z (Ω) 🔵")
                            ])
                        ]),
                        html.Tbody(id="impedances-table-body")
                    ], className="table table-striped")
                ], className="card-body")
            ], className="card")
        ], className="mt-4"),
        
        # Analysis tools
        html.Div([
            html.H4("Herramientas de Análisis", className="mb-3"),
            html.Div([
                html.Div([
                    html.Label("Seleccionar nodo para análisis detallado:"),
                    dcc.Dropdown(
                        id='node-selector-f2',
                        options=[
                            {'label': network.graph.nodes[n].get('name', n.upper()), 'value': n}
                            for n in network.graph.nodes()
                        ],
                        value='jacobacci',
                        className="mb-3"
                    ),
                    html.Div(id='node-details-f2')
                ], className="card-body")
            ], className="card")
        ], className="mt-4")
    ], className="container-fluid")
], className="p-4")

# Callbacks
@callback(
    Output('node-details-f2', 'children'),
    Input('node-selector-f2', 'value')
)
def update_node_details(node_id):
    if not node_id:
        return html.Div()
    
    node_data = network.graph.nodes.get(node_id, {})
    # For now, we'll skip downstream calculation as the method doesn't exist
    downstream = {'total_mw': 0, 'total_mvar': 0, 'power_factor': 1.0}
    
    details = html.Div([
        html.H5(f"Detalles: {node_data.get('name', node_id.upper())}"),
        html.Hr(),
        html.P([
            html.Strong("Carga local: "),
            f"{node_data.get('load_mw', 0):.2f} MW + {node_data.get('load_mvar', 0):.2f} MVAr"
        ]),
        html.P([
            html.Strong("Carga downstream total: "),
            f"{downstream['total_mw']:.2f} MW + {downstream['total_mvar']:.2f} MVAr"
        ]),
        html.P([
            html.Strong("Factor de potencia downstream: "),
            f"{downstream['power_factor']:.3f}"
        ]),
        html.P([
            html.Strong("Distancia desde origen: "),
            f"{node_data.get('distance_from_origin_km', 0)} km"
        ])
    ])
    
    return details

# Callback for GD panel content
@callback(
    Output('gd-panel-content', 'children'),
    Input('gd-panel-content', 'id')
)
def populate_gd_panel(_):
    """Populate GD panel with data from DataManager."""
    dm = get_data_manager()
    gd_costs = dm.get_gd_costs()
    
    # Calculate FC
    fc = (gd_costs['horas_dia_base'] / 24) * gd_costs['factor_capacidad'] * 100
    
    content = [
        dbc.Row([
            dbc.Col([
                html.H6("Potencia Instalada", className="text-muted"),
                html.H3(f"{gd_costs['potencia_mw']} MW", className="text-primary"),
                html.Small(f"🟢 {gd_costs['data_sources']['potencia_mw']['tipo']} ({gd_costs['data_sources']['potencia_mw']['fuente']})", 
                          className="text-success")
            ], md=3),
            dbc.Col([
                html.H6("Expansión Planificada", className="text-muted"),
                html.H3(f"{gd_costs['potencia_expansion_mw']} MW", className="text-info"),
                html.Small("🔵 REFERENCIA", className="text-info")
            ], md=3),
            dbc.Col([
                html.H6("Operación Actual", className="text-muted"),
                html.H3(f"{gd_costs['horas_dia_base']} h/día", className="text-warning"),
                html.Small(f"FC: {fc:.1f}%", className="text-muted")
            ], md=3),
            dbc.Col([
                html.H6("Costo Operativo", className="text-muted"),
                html.H3(f"${gd_costs['costo_por_mwh']}/MWh", className="text-danger"),
                html.Small("🟢 DATO (Calculado)", className="text-success")
            ], md=3)
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.P([
                    html.Strong("Tecnología: "),
                    "Motogeneradores a gas natural"
                ]),
                html.P([
                    html.Strong("Conexión: "),
                    "13.2 kV en barra ET Los Menucos"
                ])
            ], md=6),
            dbc.Col([
                html.P([
                    html.Strong("Impacto en red: "),
                    "Mejora tensión local (🟡 ESTIMADO)"
                ]),
                html.P([
                    html.Strong("Limitación: "),
                    "Alto costo operativo limita horas de uso"
                ])
            ], md=6)
        ])
    ]
    
    return content

# Callback for impedances table
@callback(
    Output('impedances-table-body', 'children'),
    Input('impedances-table-body', 'id')
)
def populate_impedances_table(_):
    """Populate impedances table with data from DataManager."""
    dm = get_data_manager()
    impedances = dm.get_impedances()
    
    rows = []
    accumulated = impedances['accumulated']
    
    # Define stations in order with their distances
    stations = [
        ("COMALLO", "Comallo", 70),
        ("JACOBACCI", "Jacobacci", 150),
        ("MAQUINCHAO", "Maquinchao", 210),
        ("LOS MENUCOS", "Los Menucos", 270)
    ]
    
    for station_key, station_name, distance in stations:
        if station_key in accumulated:
            imp = accumulated[station_key]
            row = html.Tr([
                html.Td(station_name),
                html.Td(str(distance)),
                html.Td(f"{imp['R_ohm']:.2f}"),
                html.Td(f"{imp['X_ohm']:.2f}"),
                html.Td(f"{imp['Z_ohm']:.2f}")
            ])
            rows.append(row)
    
    return rows