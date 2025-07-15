"""
Fase 2 - Modelado y Visualización de Topología (Version 2.0)
Sin hardcoding, todos los datos desde DataManager y constants
"""

from dash import dcc, html, Input, Output, callback
import dash
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import functools
import json
import dash_bootstrap_components as dbc

from dashboard.pages.utils import get_data_manager
from dashboard.pages.utils.constants import SYSTEM, NETWORK, GD_CONSTANTS, UI_COLORS

# Register page
dash.register_page(
    __name__, 
    path='/fase2-topologia-v2', 
    name='Fase 2: Topología v2', 
    title='Topología del Sistema'
)

# Project root
project_root = Path(__file__).parent.parent.parent

# Lazy loading for network topology
@functools.lru_cache()
def get_network_data():
    """Load network data from JSON with caching"""
    json_path = project_root / 'data' / 'processed' / 'sistema_linea_sur.json'
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e), "nodes": {}, "edges": []}

def create_system_summary():
    """Create system summary cards"""
    dm = get_data_manager()
    network_data = get_network_data()
    
    # Get system metrics
    num_nodes = len(network_data.get('nodes', {}))
    num_edges = len(network_data.get('edges', []))
    total_length = NETWORK['TOTAL_LENGTH_KM']
    
    # Get load data from nodes
    total_load_mw = sum(
        node.get('load_mw', 0) 
        for node in network_data.get('nodes', {}).values()
    )
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Longitud Total", className="text-muted mb-1"),
                    html.H3(f"{total_length} km", className="text-primary mb-0"),
                    html.Small("Sistema radial 33 kV", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Estaciones", className="text-muted mb-1"),
                    html.H3(str(num_nodes), className="text-info mb-0"),
                    html.Small(f"{num_edges} tramos", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Carga Total", className="text-muted mb-1"),
                    html.H3(f"{total_load_mw:.1f} MW", className="text-success mb-0"),
                    html.Small("Sistema completo", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Gen. Distribuida", className="text-muted mb-1"),
                    html.H3(f"{GD_CONSTANTS['potencia_mw']} MW", className="text-warning mb-0"),
                    html.Small(GD_CONSTANTS['ubicacion'], className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=3)
    ], className="mb-4")

def create_network_map():
    """Create network map visualization with proper data sources"""
    dm = get_data_manager()
    gd_costs = dm.get_gd_costs()
    network_data = get_network_data()
    
    if 'error' in network_data:
        return go.Figure().add_annotation(
            text=f"Error: {network_data['error']}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    nodes = network_data.get('nodes', {})
    edges = network_data.get('edges', [])
    
    # Create edge traces
    edge_traces = []
    for edge in edges:
        if 'source' in edge and 'target' in edge:
            source_node = nodes.get(edge['source'])
            target_node = nodes.get(edge['target'])
            
            if source_node and target_node:
                # Use colors from constants
                conductor_type = edge.get('conductor_type', '')
                if '120' in str(conductor_type):
                    color = UI_COLORS['conductor_primary']
                    width = 4
                else:
                    color = UI_COLORS['conductor_secondary']
                    width = 3
                
                edge_trace = go.Scattermapbox(
                    lon=[source_node['coordinates']['lon'], target_node['coordinates']['lon']],
                    lat=[source_node['coordinates']['lat'], target_node['coordinates']['lat']],
                    mode='lines',
                    line=dict(width=width, color=color),
                    hoverinfo='text',
                    hovertext=f"{edge.get('length_km', 'N/A')} km - {conductor_type}",
                    showlegend=False
                )
                edge_traces.append(edge_trace)
    
    # Create node trace
    node_data_list = []
    for node_id, node_data in nodes.items():
        if 'coordinates' in node_data:
            load_mw = node_data.get('load_mw', 0)
            
            # Color based on load using constants
            if node_data.get('criticality') == 'high' or load_mw > 1.0:
                color = UI_COLORS['node_critical']
            elif load_mw > 0.5:
                color = UI_COLORS['node_medium_load']
            else:
                color = UI_COLORS['node_low_load']
            
            node_data_list.append({
                'lon': node_data['coordinates']['lon'],
                'lat': node_data['coordinates']['lat'],
                'name': node_data.get('name', node_id),
                'load_mw': load_mw,
                'distance': node_data.get('distance_from_origin_km', 'N/A'),
                'population': node_data.get('population', 0),
                'color': color,
                'size': 15 + load_mw * 10
            })
    
    if node_data_list:
        df_nodes = pd.DataFrame(node_data_list)
        
        node_trace = go.Scattermapbox(
            lon=df_nodes['lon'],
            lat=df_nodes['lat'],
            mode='markers+text',
            marker=dict(
                size=df_nodes['size'],
                color=df_nodes['color'],
                sizemode='diameter'
            ),
            text=df_nodes['name'],
            textposition="top center",
            hoverinfo='text',
            hovertext=[
                f"<b>{row['name']}</b><br>" +
                f"Carga: {row['load_mw']:.2f} MW<br>" +
                f"Distancia: {row['distance']} km<br>" +
                f"Población: {row['population']:,}" if row['population'] > 0 else 
                f"<b>{row['name']}</b><br>" +
                f"Carga: {row['load_mw']:.2f} MW<br>" +
                f"Distancia: {row['distance']} km"
                for _, row in df_nodes.iterrows()
            ],
            showlegend=False
        )
    else:
        node_trace = go.Scattermapbox()
    
    # Add GD marker
    gd_trace = None
    los_menucos = nodes.get('los_menucos') or nodes.get('LOS_MENUCOS')
    if los_menucos and 'coordinates' in los_menucos:
        gd_trace = go.Scattermapbox(
            lon=[los_menucos['coordinates']['lon']],
            lat=[los_menucos['coordinates']['lat'] - 0.05],
            mode='markers+text',
            marker=dict(
                size=20,
                color=UI_COLORS['gd_marker'],
                symbol='square'
            ),
            text=[f"GD {gd_costs['potencia_mw']} MW"],  # Dynamic from DataManager
            textposition="bottom center",
            hoverinfo='text',
            hovertext=f"<b>Generación Distribuida</b><br>" +
                      f"Potencia: {gd_costs['potencia_mw']} MW<br>" +
                      f"Operación: {gd_costs['horas_dia_base']}h/día<br>" +
                      f"Factor capacidad: {gd_costs['factor_capacidad']}<br>" +
                      f"Costo: ${gd_costs['costo_por_mwh']:.2f}/MWh",
            showlegend=False
        )
    
    # Combine all traces
    traces = edge_traces + [node_trace]
    if gd_trace:
        traces.append(gd_trace)
    
    fig = go.Figure(data=traces)
    
    # Update layout
    if node_data_list:
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(
                    lat=np.mean([n['lat'] for n in node_data_list]),
                    lon=np.mean([n['lon'] for n in node_data_list])
                ),
                zoom=7.8
            ),
            showlegend=False,
            height=600,
            margin={"r":0,"t":30,"l":0,"b":0},
            title={
                'text': "Mapa del Sistema Eléctrico - Línea Sur",
                'y':0.98,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            }
        )
    
    return fig

def create_voltage_profile():
    """Create voltage profile using constants and DataManager"""
    dm = get_data_manager()
    theoretical_voltages = dm.get_theoretical_voltages()
    real_measurements = dm.get_real_measurements()
    network_data = get_network_data()
    
    nodes = network_data.get('nodes', {})
    
    # Prepare data
    profile_data = []
    for node_id, node_data in nodes.items():
        if 'distance_from_origin_km' in node_data:
            distance = node_data['distance_from_origin_km']
            name = node_data.get('name', node_id)
            
            # Get theoretical voltage
            v_theoretical = theoretical_voltages['voltages'].get(
                name.upper(), 
                {'value': 1.0 - distance * theoretical_voltages['drop_rate_per_km']}
            )['value']
            
            profile_data.append({
                'distance': distance,
                'name': name,
                'v_theoretical': v_theoretical,
                'v_real': None  # Will be updated if available
            })
    
    # Sort by distance
    profile_data.sort(key=lambda x: x['distance'])
    
    fig = go.Figure()
    
    # Add theoretical voltage line
    fig.add_trace(go.Scatter(
        x=[d['distance'] for d in profile_data],
        y=[d['v_theoretical'] for d in profile_data],
        mode='lines+markers',
        name='Tensión Teórica 🟡',
        line=dict(color=UI_COLORS['voltage_theoretical'], dash='dash'),
        marker=dict(size=8),
        hovertemplate='<b>%{text}</b><br>Distancia: %{x} km<br>Tensión: %{y:.3f} pu<extra></extra>',
        text=[d['name'] for d in profile_data]
    ))
    
    # Add regulatory limits using SYSTEM constants
    fig.add_hline(
        y=SYSTEM['VOLTAGE_MAX_PU'], 
        line_dash="dash", 
        line_color=UI_COLORS['voltage_limit'],
        annotation_text=f"Límite superior ({SYSTEM['VOLTAGE_MAX_PU']} pu)"
    )
    
    fig.add_hline(
        y=SYSTEM['VOLTAGE_MIN_PU'], 
        line_dash="dash", 
        line_color=UI_COLORS['voltage_limit'],
        annotation_text=f"Límite inferior ({SYSTEM['VOLTAGE_MIN_PU']} pu)"
    )
    
    fig.add_hline(
        y=1.0, 
        line_dash="dot", 
        line_color=UI_COLORS['voltage_nominal'],
        annotation_text="Nominal (1.0 pu)"
    )
    
    # Add critical zone fill
    fig.add_trace(go.Scatter(
        x=[0, NETWORK['TOTAL_LENGTH_KM']],
        y=[SYSTEM['VOLTAGE_MIN_PU'], SYSTEM['VOLTAGE_MIN_PU']],
        fill=None,
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=[d['distance'] for d in profile_data] + [NETWORK['TOTAL_LENGTH_KM'], 0],
        y=[d['v_theoretical'] for d in profile_data] + [SYSTEM['VOLTAGE_MIN_PU'], SYSTEM['VOLTAGE_MIN_PU']],
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.2)',
        mode='none',
        showlegend=False,
        hoverinfo='skip',
        name='Zona Crítica'
    ))
    
    fig.update_layout(
        title="Perfil de Tensión del Sistema",
        xaxis_title="Distancia desde Pilcaniyeu (km)",
        yaxis_title="Tensión (pu)",
        xaxis_range=[0, NETWORK['TOTAL_LENGTH_KM']],
        yaxis_range=[0.65, 1.1],
        height=400,
        template="plotly_white",
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )
    
    return fig

def create_load_distribution():
    """Create load distribution chart"""
    network_data = get_network_data()
    nodes = network_data.get('nodes', {})
    
    # Prepare load data
    load_data = []
    for node_id, node_data in nodes.items():
        load_mw = node_data.get('load_mw', 0)
        if load_mw > 0:
            load_data.append({
                'Estación': node_data.get('name', node_id),
                'Carga (MW)': load_mw,
                'Carga (MVAr)': node_data.get('load_mvar', 0),
                'Factor Potencia': load_mw / np.sqrt(load_mw**2 + node_data.get('load_mvar', 0)**2) if load_mw > 0 else 0
            })
    
    if not load_data:
        return go.Figure().add_annotation(
            text="No hay datos de carga disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    df = pd.DataFrame(load_data).sort_values('Carga (MW)', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df['Estación'],
        x=df['Carga (MW)'],
        name='MW',
        orientation='h',
        marker_color=UI_COLORS['primary'],
        text=df['Carga (MW)'].round(2),
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        y=df['Estación'],
        x=df['Carga (MVAr)'],
        name='MVAr',
        orientation='h',
        marker_color=UI_COLORS['info'],
        text=df['Carga (MVAr)'].round(2),
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Distribución de Cargas por Estación",
        xaxis_title="Potencia",
        barmode='group',
        height=400,
        template="plotly_white",
        showlegend=True
    )
    
    return fig

def create_losses_visualization():
    """Create losses visualization"""
    dm = get_data_manager()
    theoretical_losses = dm.get_theoretical_losses()
    
    if not theoretical_losses or 'segments' not in theoretical_losses:
        return go.Figure().add_annotation(
            text="No hay datos de pérdidas disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Prepare data
    segments = []
    losses_mw = []
    percentages = []
    
    for segment in theoretical_losses['segments']:
        segments.append(segment['name'])
        losses_mw.append(segment['loss_mw'])
        percentages.append(segment['loss_percentage'])
    
    # Create bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=segments,
        y=losses_mw,
        text=[f'{l:.2f} MW<br>({p}%)' for l, p in zip(losses_mw, percentages)],
        textposition='outside',
        marker_color=[UI_COLORS['danger'], UI_COLORS['warning'], UI_COLORS['info'], UI_COLORS['success']],
        hovertemplate='<b>%{x}</b><br>Pérdidas: %{y:.2f} MW<br>%{text}<extra></extra>'
    ))
    
    # Add total annotation
    total_loss = theoretical_losses['total']
    fig.add_annotation(
        text=f"Total: {total_loss['loss_mw']} MW ({total_loss['loss_percentage']}%)",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=14, color=UI_COLORS['danger']),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor=UI_COLORS['danger'],
        borderwidth=1
    )
    
    fig.update_layout(
        title="Pérdidas Estimadas por Tramo",
        yaxis_title="Pérdidas (MW)",
        xaxis_title="Tramo",
        height=350,
        template="plotly_white",
        showlegend=False
    )
    
    return fig

def create_gd_panel():
    """Create GD information panel"""
    dm = get_data_manager()
    gd_costs = dm.get_gd_costs()
    
    # Calculate utilization factor
    factor_utilizacion = (gd_costs['horas_dia_base'] / 24) * gd_costs['factor_capacidad'] * 100
    
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Potencia Instalada", className="text-muted"),
                    html.H4(f"{gd_costs['potencia_mw']} MW", className="text-primary"),
                    html.Small(f"De {GD_CONSTANTS['potencia_total_mw']} MW totales")
                ], md=3),
                
                dbc.Col([
                    html.H6("Operación", className="text-muted"),
                    html.H4(f"{gd_costs['horas_dia_base']}h/día", className="text-warning"),
                    html.Small(f"Factor utilización: {factor_utilizacion:.1f}%")
                ], md=3),
                
                dbc.Col([
                    html.H6("Costo Operativo", className="text-muted"),
                    html.H4(f"${gd_costs['costo_por_mwh']:.1f}/MWh", className="text-danger"),
                    html.Small("Calculado con datos reales")
                ], md=3),
                
                dbc.Col([
                    html.H6("Tecnología", className="text-muted"),
                    html.H4(f"{GD_CONSTANTS['conexion_kv']} kV", className="text-info"),
                    html.Small(GD_CONSTANTS['tecnologia'])
                ], md=3)
            ])
        ])
    ], className="shadow")

def create_impedances_table():
    """Create impedances table"""
    dm = get_data_manager()
    impedances = dm.get_impedances()
    
    if not impedances or 'accumulated' not in impedances:
        return html.Div("No hay datos de impedancias disponibles")
    
    # Prepare table data
    table_data = []
    accumulated = impedances['accumulated']
    
    # Define stations in order
    stations = [
        ("COMALLO", "Comallo", 70),
        ("ONELLI", "Onelli", 120),
        ("JACOBACCI", "Jacobacci", 150),
        ("MAQUINCHAO", "Maquinchao", 210),
        ("AGUADA", "Aguada de Guerra", 240),
        ("LOS MENUCOS", "Los Menucos", 270)
    ]
    
    for station_key, station_name, distance in stations:
        if station_key in accumulated:
            imp = accumulated[station_key]
            table_data.append({
                'Estación': station_name,
                'Distancia (km)': distance,
                'R (Ω)': f"{imp['R_ohm']:.2f}",
                'X (Ω)': f"{imp['X_ohm']:.2f}",
                'Z (Ω)': f"{imp['Z_ohm']:.2f}"
            })
    
    if not table_data:
        return html.Div("No hay datos de impedancias acumuladas")
    
    df = pd.DataFrame(table_data)
    
    return html.Div([
        html.Table([
            html.Thead([
                html.Tr([
                    html.Th(col) for col in df.columns
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(df.iloc[i][col]) for col in df.columns
                ]) for i in range(len(df))
            ])
        ], className="table table-striped table-hover")
    ])

# Define layout
layout = html.Div([
    dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("Sistema Eléctrico Línea Sur - Topología", className="mb-3"),
                html.P(
                    "Análisis técnico de la red de 33 kV con modelado de impedancias y cargas",
                    className="text-muted mb-4"
                )
            ])
        ]),
        
        # System summary
        create_system_summary(),
        
        # Network map
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id='network-map-v2',
                            figure=create_network_map(),
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow mb-4")
            ])
        ]),
        
        # Voltage and load charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id='voltage-profile-v2',
                            figure=create_voltage_profile(),
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id='load-distribution-v2',
                            figure=create_load_distribution(),
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow")
            ], md=6)
        ], className="mb-4"),
        
        # Losses visualization
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Análisis de Pérdidas Técnicas", className="mb-3"),
                        dcc.Graph(
                            id='losses-chart-v2',
                            figure=create_losses_visualization(),
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow mb-4")
            ])
        ]),
        
        # GD Panel
        dbc.Row([
            dbc.Col([
                html.H4("Generación Distribuida - Los Menucos", className="mb-3"),
                create_gd_panel()
            ])
        ], className="mb-4"),
        
        # Impedances table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Impedancias Acumuladas del Sistema", className="mb-3"),
                        html.P(
                            "🔵 REFERENCIA - Valores calculados según catálogo de conductores",
                            className="text-muted small mb-3"
                        ),
                        create_impedances_table()
                    ])
                ], className="shadow")
            ])
        ], className="mb-4"),
        
        # Footer
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.Small([
                    "Datos obtenidos desde: ",
                    html.Code("DataManagerV2"),
                    " | Constantes desde: ",
                    html.Code("constants.py"),
                    " | Red desde: ",
                    html.Code("sistema_linea_sur.json")
                ], className="text-muted")
            ])
        ])
        
    ], fluid=True)
], className="p-4", style={'backgroundColor': UI_COLORS['background']})