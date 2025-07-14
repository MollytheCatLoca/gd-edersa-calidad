"""
Fase 2 - Topología de la Red (DEBUG VERSION)
Muestra claramente el origen de cada dato
"""

from dash import dcc, html, Input, Output, callback, dash_table
import dash
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
import json
import dash_bootstrap_components as dbc
from dashboard.pages.utils import get_data_manager, DataStatus

# Register page
dash.register_page(
    __name__, 
    path='/fase2-topologia-debug', 
    name='Fase 2: Topología (DEBUG)', 
    title='Topología del Sistema - Debug'
)

# Get project root
project_root = Path(__file__).parent.parent.parent

def load_network_data():
    """Load network data from JSON file"""
    json_path = project_root / 'data' / 'processed' / 'sistema_linea_sur.json'
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

def create_data_source_table():
    """Create table showing where each data point comes from"""
    dm = get_data_manager()
    
    # Get all data sources
    nodes_result = dm.get_nodes()
    edges_result = dm.get_edges()
    gd_costs = dm.get_gd_costs()
    theoretical_voltages = dm.get_theoretical_voltages()
    theoretical_losses = dm.get_theoretical_losses()
    impedances = dm.get_impedances()
    
    # Load network JSON
    network_data = load_network_data()
    
    # Build data source table
    data_sources = []
    
    # Network topology data
    if 'nodes' in network_data:
        data_sources.append({
            'Variable': 'Nodos del sistema',
            'Valor': f"{len(network_data['nodes'])} nodos",
            'Origen': 'sistema_linea_sur.json',
            'Tipo': '🟢 DATO',
            'Path': 'data/processed/sistema_linea_sur.json'
        })
    
    if 'edges' in network_data:
        data_sources.append({
            'Variable': 'Líneas/Tramos',
            'Valor': f"{len(network_data['edges'])} tramos",
            'Origen': 'sistema_linea_sur.json',
            'Tipo': '🟢 DATO',
            'Path': 'data/processed/sistema_linea_sur.json'
        })
    
    # GD data
    data_sources.extend([
        {
            'Variable': 'GD Potencia',
            'Valor': f"{gd_costs['potencia_mw']} MW",
            'Origen': 'GD_CONSTANTS["potencia_mw"]',
            'Tipo': '🟢 DATO',
            'Path': 'dashboard/pages/utils/constants.py'
        },
        {
            'Variable': 'GD Horas/día',
            'Valor': f"{gd_costs['horas_dia_base']} h",
            'Origen': 'GD_CONSTANTS["horas_dia_base"]',
            'Tipo': '🟢 DATO',
            'Path': 'dashboard/pages/utils/constants.py'
        },
        {
            'Variable': 'GD Factor Capacidad',
            'Valor': f"{gd_costs['factor_capacidad']}",
            'Origen': 'GD_CONSTANTS["factor_capacidad"]',
            'Tipo': '🟢 DATO',
            'Path': 'dashboard/pages/utils/constants.py'
        },
        {
            'Variable': 'GD Costo/MWh',
            'Valor': f"${gd_costs['costo_por_mwh']:.2f}",
            'Origen': 'Calculado en get_gd_costs()',
            'Tipo': '🟢 DATO',
            'Path': 'dashboard/pages/utils/data_manager_v2.py'
        }
    ])
    
    # Voltage data
    if theoretical_voltages:
        data_sources.extend([
            {
                'Variable': 'Caída tensión/km',
                'Valor': f"{theoretical_voltages.get('drop_rate_per_km', 0.0015)*100:.2f}%/km",
                'Origen': 'DataManager.get_theoretical_voltages()',
                'Tipo': '🟡 ESTIMADO',
                'Path': 'dashboard/pages/utils/data_manager_v2.py'
            },
            {
                'Variable': 'Voltaje mínimo regulatorio',
                'Valor': '0.95 pu',
                'Origen': 'HARDCODED en create_voltage_profile()',
                'Tipo': '❌ HARDCODED',
                'Path': 'dashboard/pages/fase2_topologia.py:245'
            },
            {
                'Variable': 'Voltaje máximo regulatorio',
                'Valor': '1.05 pu',
                'Origen': 'HARDCODED en create_voltage_profile()',
                'Tipo': '❌ HARDCODED',
                'Path': 'dashboard/pages/fase2_topologia.py:252'
            }
        ])
    
    # Impedance data
    if impedances:
        for segment, data in impedances.get('segments', {}).items():
            data_sources.append({
                'Variable': f'Impedancia {segment}',
                'Valor': f"Z={data.get('z_total_ohm', 0):.1f}Ω",
                'Origen': 'DataManager.get_impedances()',
                'Tipo': '🔵 REFERENCIA',
                'Path': 'dashboard/pages/utils/data_manager_v2.py'
            })
    
    # Loss data
    if theoretical_losses:
        data_sources.append({
            'Variable': 'Pérdidas totales',
            'Valor': f"{theoretical_losses['total']['loss_mw']} MW ({theoretical_losses['total']['loss_percentage']}%)",
            'Origen': 'DataManager.get_theoretical_losses()',
            'Tipo': '🟡 ESTIMADO',
            'Path': 'dashboard/pages/utils/data_manager_v2.py'
        })
    
    # Colors
    data_sources.extend([
        {
            'Variable': 'Color conductor 120mm²',
            'Valor': 'blue',
            'Origen': 'HARDCODED en create_network_figure()',
            'Tipo': '❌ HARDCODED',
            'Path': 'dashboard/pages/fase2_topologia.py:60'
        },
        {
            'Variable': 'Color conductor otros',
            'Valor': 'darkblue',
            'Origen': 'HARDCODED en create_network_figure()',
            'Tipo': '❌ HARDCODED',
            'Path': 'dashboard/pages/fase2_topologia.py:63'
        },
        {
            'Variable': 'Longitud total sistema',
            'Valor': '270 km',
            'Origen': 'HARDCODED en create_voltage_profile()',
            'Tipo': '❌ HARDCODED',
            'Path': 'dashboard/pages/fase2_topologia.py:244'
        }
    ])
    
    return pd.DataFrame(data_sources)

def create_network_map():
    """Create the network map (keeping the working version)"""
    dm = get_data_manager()
    gd_costs = dm.get_gd_costs()
    network_data = load_network_data()
    
    if 'error' in network_data:
        return go.Figure().add_annotation(
            text=f"Error loading network: {network_data['error']}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Extract nodes and edges
    nodes = network_data.get('nodes', {})
    edges = network_data.get('edges', [])
    
    # Create edge traces
    edge_traces = []
    for edge in edges:
        if 'source' in edge and 'target' in edge:
            source_node = nodes.get(edge['source'])
            target_node = nodes.get(edge['target'])
            
            if source_node and target_node:
                edge_trace = go.Scattermapbox(
                    lon=[source_node['coordinates']['lon'], target_node['coordinates']['lon']],
                    lat=[source_node['coordinates']['lat'], target_node['coordinates']['lat']],
                    mode='lines',
                    line=dict(width=3, color='darkblue'),
                    hoverinfo='text',
                    hovertext=f"{edge.get('length_km', 'N/A')} km - {edge.get('conductor_type', 'N/A')}",
                    showlegend=False
                )
                edge_traces.append(edge_trace)
    
    # Create node trace
    node_lon = []
    node_lat = []
    node_text = []
    node_names = []
    
    for node_id, node_data in nodes.items():
        if 'coordinates' in node_data:
            node_lon.append(node_data['coordinates']['lon'])
            node_lat.append(node_data['coordinates']['lat'])
            node_names.append(node_data.get('name', node_id))
            
            # Build hover text
            text = f"<b>{node_data.get('name', node_id)}</b><br>"
            text += f"Carga: {node_data.get('load_mw', 0)} MW<br>"
            text += f"Distancia: {node_data.get('distance_from_origin_km', 'N/A')} km"
            node_text.append(text)
    
    node_trace = go.Scattermapbox(
        lon=node_lon,
        lat=node_lat,
        mode='markers+text',
        marker=dict(size=10, color='red'),
        text=node_names,
        textposition="top center",
        hoverinfo='text',
        hovertext=node_text,
        showlegend=False
    )
    
    # Add GD marker if Los Menucos exists
    gd_trace = None
    los_menucos = nodes.get('los_menucos') or nodes.get('LOS_MENUCOS') or nodes.get('Los Menucos')
    if los_menucos and 'coordinates' in los_menucos:
        gd_trace = go.Scattermapbox(
            lon=[los_menucos['coordinates']['lon']],
            lat=[los_menucos['coordinates']['lat'] - 0.05],
            mode='markers+text',
            marker=dict(size=15, color='purple', symbol='square'),
            text=[f"GD {gd_costs['potencia_mw']} MW"],
            textposition="bottom center",
            hoverinfo='text',
            hovertext=f"<b>Generación Distribuida</b><br>" +
                      f"Potencia: {gd_costs['potencia_mw']} MW<br>" +
                      f"Operación: {gd_costs['horas_dia_base']}h/día<br>" +
                      f"Costo: ${gd_costs['costo_por_mwh']:.2f}/MWh",
            showlegend=False
        )
    
    # Combine traces
    traces = edge_traces + [node_trace]
    if gd_trace:
        traces.append(gd_trace)
    
    fig = go.Figure(data=traces)
    
    # Update layout
    if node_lon and node_lat:
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(
                    lat=np.mean(node_lat),
                    lon=np.mean(node_lon)
                ),
                zoom=7.5
            ),
            showlegend=False,
            height=600,
            margin={"r":0,"t":0,"l":0,"b":0}
        )
    
    return fig

def create_topology_description():
    """Create a clear description of the network topology"""
    network_data = load_network_data()
    
    if 'error' in network_data:
        return html.Div("Error loading network data")
    
    nodes = network_data.get('nodes', {})
    edges = network_data.get('edges', [])
    
    # Create connections table
    connections = []
    for edge in edges:
        source = nodes.get(edge.get('source', ''), {})
        target = nodes.get(edge.get('target', ''), {})
        
        connections.append({
            'Desde': source.get('name', edge.get('source', 'N/A')),
            'Hasta': target.get('name', edge.get('target', 'N/A')),
            'Distancia (km)': edge.get('length_km', 'N/A'),
            'Conductor': edge.get('conductor_type', 'N/A'),
            'Resistencia (Ω)': edge.get('resistance_ohm', 'N/A'),
            'Reactancia (Ω)': edge.get('reactance_ohm', 'N/A')
        })
    
    df_connections = pd.DataFrame(connections)
    
    return html.Div([
        html.H5("Conexiones del Sistema"),
        dash_table.DataTable(
            data=df_connections.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_connections.columns],
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        )
    ])

def create_data_flow_diagram():
    """Create a diagram showing data flow"""
    return dbc.Card([
        dbc.CardBody([
            html.H5("Flujo de Datos", className="card-title"),
            html.Pre("""
constants.py
├── NETWORK_CONSTANTS
│   ├── TOTAL_LENGTH_KM: 270.0
│   ├── VOLTAGE_DROP_PU_PER_KM: 0.0015
│   └── LOSSES_MW_PER_KM: 0.0037
├── SYSTEM_CONSTANTS
│   ├── VOLTAGE_MIN_PU: 0.95
│   └── VOLTAGE_MAX_PU: 1.05
└── GD_CONSTANTS
    ├── potencia_mw: 1.8
    ├── horas_dia_base: 4
    └── factor_capacidad: 0.95

sistema_linea_sur.json
├── nodes (7 estaciones)
└── edges (6 tramos)

DataManagerV2
├── get_nodes() → Datos de nodos
├── get_edges() → Datos de líneas
├── get_gd_costs() → Costos GD calculados
├── get_theoretical_voltages() → Voltajes teóricos
├── get_theoretical_losses() → Pérdidas estimadas
└── get_impedances() → Impedancias de línea
            """, style={'fontSize': '12px', 'backgroundColor': '#f8f9fa'})
        ])
    ])

# Define layout
layout = html.Div([
    # Header
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Fase 2: Topología de la Red (DEBUG)", className="mb-3"),
                html.P("Vista de debug mostrando el origen de cada dato", className="text-muted"),
                dbc.Alert([
                    html.Strong("⚠️ MODO DEBUG: "),
                    "Esta página muestra el origen de cada variable para verificar el flujo de datos"
                ], color="warning", className="mb-4")
            ])
        ])
    ], fluid=True),
    
    # Data source table
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("📊 Origen de Datos", className="mb-3"),
                html.Div(id="data-source-table")
            ])
        ], className="mb-4")
    ], fluid=True),
    
    # Data flow diagram
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("🔄 Flujo de Datos", className="mb-3"),
                create_data_flow_diagram()
            ], md=6),
            dbc.Col([
                html.H4("📋 Estado de Carga de Datos", className="mb-3"),
                html.Div(id="data-status-cards")
            ], md=6)
        ], className="mb-4")
    ], fluid=True),
    
    # Network map
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("🗺️ Mapa de la Red", className="mb-3"),
                dcc.Graph(
                    id='network-map-debug',
                    figure=create_network_map(),
                    style={'height': '600px'}
                )
            ])
        ], className="mb-4")
    ], fluid=True),
    
    # Topology description
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("🔌 Descripción de la Topología", className="mb-3"),
                html.Div(id="topology-description")
            ])
        ], className="mb-4")
    ], fluid=True),
    
    # Raw data viewer
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("📄 Datos Crudos", className="mb-3"),
                dbc.Tabs([
                    dbc.Tab(label="sistema_linea_sur.json", tab_id="json-data"),
                    dbc.Tab(label="GD_CONSTANTS", tab_id="gd-constants"),
                    dbc.Tab(label="NETWORK_CONSTANTS", tab_id="network-constants"),
                ], id="raw-data-tabs", active_tab="json-data"),
                html.Div(id="raw-data-content", className="mt-3")
            ])
        ])
    ], fluid=True)
], className="p-4")

# Callbacks
@callback(
    Output("data-source-table", "children"),
    Input("data-source-table", "id")
)
def update_data_source_table(_):
    """Update data source table"""
    df = create_data_source_table()
    
    # Count by type
    type_counts = df['Tipo'].value_counts()
    
    # Create summary cards
    summary = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(type_counts.get('🟢 DATO', 0), className="text-success"),
                    html.P("Datos Reales", className="mb-0")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(type_counts.get('🟡 ESTIMADO', 0), className="text-warning"),
                    html.P("Estimados", className="mb-0")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(type_counts.get('🔵 REFERENCIA', 0), className="text-info"),
                    html.P("Referencias", className="mb-0")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(type_counts.get('❌ HARDCODED', 0), className="text-danger"),
                    html.P("Hardcoded", className="mb-0")
                ])
            ])
        ], md=3)
    ], className="mb-3")
    
    # Create table
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df.columns],
        style_cell={'textAlign': 'left', 'fontSize': '12px'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Tipo', 'filter_query': '{Tipo} contains "HARDCODED"'},
                'backgroundColor': '#ffcccc',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'Tipo', 'filter_query': '{Tipo} contains "DATO"'},
                'backgroundColor': '#ccffcc'
            },
            {
                'if': {'column_id': 'Tipo', 'filter_query': '{Tipo} contains "ESTIMADO"'},
                'backgroundColor': '#ffffcc'
            },
            {
                'if': {'column_id': 'Tipo', 'filter_query': '{Tipo} contains "REFERENCIA"'},
                'backgroundColor': '#ccccff'
            }
        ],
        filter_action="native",
        sort_action="native",
        page_size=20
    )
    
    return html.Div([summary, table])

@callback(
    Output("data-status-cards", "children"),
    Input("data-status-cards", "id")
)
def update_data_status(_):
    """Show data loading status"""
    dm = get_data_manager()
    
    # Get status of different data sources
    nodes_result = dm.get_nodes()
    edges_result = dm.get_edges()
    
    cards = []
    
    # Nodes status
    cards.append(
        dbc.Card([
            dbc.CardBody([
                html.H6("Nodos", className="card-subtitle mb-2 text-muted"),
                html.P(f"Estado: {nodes_result.status.value if hasattr(nodes_result, 'status') else 'N/A'}", 
                      className="mb-0"),
                html.Small(f"Fuente: {nodes_result.meta.get('source', 'Unknown') if hasattr(nodes_result, 'meta') else 'N/A'}")
            ])
        ], className="mb-2")
    )
    
    # Add more status cards as needed
    
    return html.Div(cards)

@callback(
    Output("topology-description", "children"),
    Input("topology-description", "id")
)
def update_topology_description(_):
    """Update topology description"""
    return create_topology_description()

@callback(
    Output("raw-data-content", "children"),
    Input("raw-data-tabs", "active_tab")
)
def update_raw_data(active_tab):
    """Show raw data based on selected tab"""
    if active_tab == "json-data":
        network_data = load_network_data()
        return html.Pre(
            json.dumps(network_data, indent=2)[:2000] + "... (truncated)",
            style={'fontSize': '10px', 'backgroundColor': '#f8f9fa', 'padding': '10px'}
        )
    
    elif active_tab == "gd-constants":
        try:
            from dashboard.pages.utils.constants import GD_CONSTANTS
            return html.Pre(
                json.dumps(dict(GD_CONSTANTS), indent=2),
                style={'fontSize': '10px', 'backgroundColor': '#f8f9fa', 'padding': '10px'}
            )
        except:
            return html.Div("Error loading GD_CONSTANTS")
    
    elif active_tab == "network-constants":
        try:
            from dashboard.pages.utils.constants import NETWORK, SYSTEM
            data = {
                "NETWORK": dict(NETWORK),
                "SYSTEM": dict(SYSTEM)
            }
            return html.Pre(
                json.dumps(data, indent=2),
                style={'fontSize': '10px', 'backgroundColor': '#f8f9fa', 'padding': '10px'}
            )
        except:
            return html.Div("Error loading NETWORK constants")
    
    return html.Div()