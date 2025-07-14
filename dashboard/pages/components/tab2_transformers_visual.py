"""
Tab 2: Visualización Completa de Transformadores
Versión visual y profesional con todos los datos reales
"""

from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from pathlib import Path
from dashboard.pages.utils import get_data_manager, DataStatus

def render_transformers_tab():
    """Render the enhanced transformers tab with real data."""
    # Get data from data manager
    dm = get_data_manager()
    
    # Get transformers data
    transformers_result = dm.get_transformers()
    transformers_data = transformers_result.data if transformers_result.data else {}
    
    # Get nodes data for additional info
    nodes_result = dm.get_nodes()
    nodes_data = nodes_result.data if nodes_result.data else {}
    
    # Process transformer data for visualization
    transformer_list = []
    total_capacity_mva = 0
    
    for location_key, location_data in transformers_data.items():
        if not isinstance(location_data, dict):
            continue
            
        # Skip seccionamiento points
        if location_data.get('tipo') == 'Seccionamiento':
            continue
            
        location_name = location_data.get('ubicacion', location_key)
        coords = location_data.get('coordenadas', {})
        
        # Handle single transformer
        if 'transformador_principal' in location_data:
            t_data = location_data['transformador_principal']
            power_mva = t_data.get('potencia_mva', 0)
            
            # Handle kVA units
            if 'potencia_kva' in t_data and power_mva == 0:
                power_mva = t_data['potencia_kva'] / 1000.0
                
            total_capacity_mva += power_mva
            
            transformer_list.append({
                'location': location_name,
                'type': 'Principal',
                'power_mva': power_mva,
                'voltage': t_data.get('relacion', 'N/D'),
                'connection': t_data.get('conexion', 'N/D'),
                'impedance': t_data.get('impedancia', {}).get('estimada', 'N/D'),
                'regulation': t_data.get('regulacion', {}).get('tipo', 'N/A'),
                'lat': coords.get('lat', 0),
                'lon': coords.get('lon', 0),
                'category': _categorize_transformer(t_data.get('tipo', ''))
            })
            
        # Handle multiple transformers (Los Menucos)
        if 'transformadores' in location_data:
            tfmr_group = location_data['transformadores']
            
            # Distribution transformer
            if 'distribucion' in tfmr_group:
                dist_data = tfmr_group['distribucion']
                power_mva = dist_data.get('potencia_total_estimada', 0)
                total_capacity_mva += power_mva
                
                transformer_list.append({
                    'location': location_name,
                    'type': 'Distribución',
                    'power_mva': power_mva,
                    'voltage': dist_data.get('relacion', 'N/D'),
                    'connection': dist_data.get('conexion', 'N/D'),
                    'impedance': 'N/D',
                    'regulation': 'Taps fijos',
                    'lat': coords.get('lat', 0),
                    'lon': coords.get('lon', 0),
                    'category': 'Distribución'
                })
                
            # Generation transformers
            if 'generacion' in tfmr_group and isinstance(tfmr_group['generacion'], list):
                for gen_tfmr in tfmr_group['generacion']:
                    power_mva = gen_tfmr.get('potencia_mva', 0)
                    total_capacity_mva += power_mva
                    
                    transformer_list.append({
                        'location': f"{location_name} - GD",
                        'type': 'Generación',
                        'power_mva': power_mva,
                        'voltage': gen_tfmr.get('relacion', 'N/D'),
                        'connection': gen_tfmr.get('conexion', 'N/D'),
                        'impedance': 'N/D',
                        'regulation': 'N/A',
                        'lat': coords.get('lat', 0),
                        'lon': coords.get('lon', 0),
                        'category': 'Generación'
                    })
    
    # Create DataFrame for easier manipulation
    df_transformers = pd.DataFrame(transformer_list)
    
    # Calculate statistics
    num_power = len(df_transformers[df_transformers['category'] == 'Potencia'])
    num_dist = len(df_transformers[df_transformers['category'] == 'Distribución'])
    num_gen = len(df_transformers[df_transformers['category'] == 'Generación'])
    
    # Build layout
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H3([
                    html.I(className="fas fa-bolt me-2"),
                    "Sistema de Transformación - Línea Sur"
                ], className="text-primary mb-3"),
                html.P("Análisis completo del equipamiento de transformación del sistema radial de 33 kV", 
                       className="text-muted")
            ])
        ]),
        
        html.Hr(),
        
        # Key metrics cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Capacidad Total", className="text-muted mb-1"),
                        html.H2(f"{total_capacity_mva:.2f} MVA", className="text-primary mb-0"),
                        html.Small("Sistema completo", className="text-muted")
                    ])
                ], className="text-center shadow-sm h-100")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Transformadores", className="text-muted mb-1"),
                        html.H2(str(len(df_transformers)), className="text-success mb-0"),
                        html.Small(f"{num_power} pot. | {num_dist} dist. | {num_gen} gen.", 
                                 className="text-muted")
                    ])
                ], className="text-center shadow-sm h-100")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Regulación", className="text-muted mb-1"),
                        html.H2("OLTC + Taps", className="text-info mb-0"),
                        html.Small("Control de tensión", className="text-muted")
                    ])
                ], className="text-center shadow-sm h-100")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Estado General", className="text-muted mb-1"),
                        html.H2([html.I(className="fas fa-check-circle text-success")], 
                               className="mb-0"),
                        html.Small("Operativo", className="text-muted")
                    ])
                ], className="text-center shadow-sm h-100")
            ], md=3),
        ], className="mb-4"),
        
        # Section 1: Mapa de Ubicaciones
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-map-marked-alt me-2"),
                    "Ubicación Geográfica de Transformadores"
                ], className="mb-3"),
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id="transformers-map",
                            figure=create_transformers_map(df_transformers),
                            style={'height': '500px'}
                        )
                    ])
                ], className="shadow")
            ])
        ], className="mb-4"),
        
        # Section 2: Especificaciones Técnicas
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-table me-2"),
                    "Especificaciones Técnicas Detalladas"
                ], className="mb-3"),
                dbc.Card([
                    dbc.CardBody([
                        create_specifications_table(df_transformers)
                    ])
                ], className="shadow")
            ])
        ], className="mb-4"),
        
        # Section 3: Análisis de Capacidad
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-chart-bar me-2"),
                    "Análisis de Capacidad"
                ], className="mb-3")
            ])
        ], className="mb-2"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id="capacity-distribution",
                            figure=create_capacity_chart(df_transformers),
                            style={'height': '400px'}
                        )
                    ])
                ], className="shadow")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id="transformer-types",
                            figure=create_type_distribution(df_transformers),
                            style={'height': '400px'}
                        )
                    ])
                ], className="shadow")
            ], md=6)
        ], className="mb-4"),
        
        # Section 4: Sistema de Regulación
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-sliders-h me-2"),
                    "Sistema de Regulación de Tensión"
                ], className="mb-3"),
                create_regulation_details(transformers_data)
            ])
        ], className="mb-4"),
        
        # Footer with data status
        html.Hr(className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.Small([
                    html.I(className="fas fa-database me-1"),
                    f"Datos desde: {transformers_result.meta.get('source', 'Unknown')} | ",
                    f"Estado: {transformers_result.status.value if transformers_result.status else 'Unknown'}",
                ], className="text-muted")
            ])
        ])
    ])


def _categorize_transformer(tipo_str):
    """Categorize transformer based on type string."""
    tipo_lower = tipo_str.lower()
    if 'potencia' in tipo_lower:
        return 'Potencia'
    elif 'pequeño' in tipo_lower:
        return 'Distribución'
    elif 'distribución' in tipo_lower:
        return 'Distribución'
    elif 'generación' in tipo_lower or 'elevador' in tipo_lower:
        return 'Generación'
    else:
        return 'Distribución'


def create_transformers_map(df):
    """Create map visualization of transformers."""
    fig = go.Figure()
    
    # Add transformer markers
    for category in ['Potencia', 'Distribución', 'Generación']:
        df_cat = df[df['category'] == category]
        
        color = {
            'Potencia': 'darkblue',
            'Distribución': 'blue',
            'Generación': 'green'
        }[category]
        
        size = {
            'Potencia': 20,
            'Distribución': 12,
            'Generación': 15
        }[category]
        
        fig.add_trace(go.Scattermapbox(
            lat=df_cat['lat'],
            lon=df_cat['lon'],
            mode='markers',
            marker=dict(
                size=size,
                color=color,
            ),
            text=[f"{row['location']}<br>{row['power_mva']} MVA<br>{row['voltage']}" 
                  for _, row in df_cat.iterrows()],
            name=category,
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
    
    # Add lines between transformers (simplified)
    lats = df.sort_values('lon')['lat'].tolist()
    lons = df.sort_values('lon')['lon'].tolist()
    
    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='lines+markers',
        marker=dict(size=2, color='gray'),
        name='Línea 33 kV',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=-41.1, lon=-69.5),
            zoom=7.5
        ),
        showlegend=True,
        height=500,
        title="Ubicación Geográfica de Transformadores"
    )
    
    return fig


def create_specifications_table(df):
    """Create detailed specifications table."""
    # Prepare data for table
    table_data = []
    
    for _, row in df.iterrows():
        impedance_str = f"{row['impedance']}%" if row['impedance'] != 'N/D' else 'N/D'
        
        table_data.append({
            'Ubicación': row['location'],
            'Tipo': row['category'],
            'Potencia': f"{row['power_mva']} MVA",
            'Tensión': row['voltage'],
            'Conexión': row['connection'],
            'Impedancia': impedance_str,
            'Regulación': row['regulation']
        })
    
    df_table = pd.DataFrame(table_data)
    
    return dbc.Table.from_dataframe(
        df_table,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mb-0",
        style={"fontSize": "0.9rem"}
    )


def create_capacity_chart(df):
    """Create capacity distribution chart."""
    # Group by location for stacked view
    df_grouped = df.groupby(['location', 'category'])['power_mva'].sum().reset_index()
    
    fig = px.bar(
        df_grouped,
        x='location',
        y='power_mva',
        color='category',
        title='Distribución de Capacidad por Estación',
        labels={'power_mva': 'Capacidad (MVA)', 'location': 'Estación'},
        color_discrete_map={
            'Potencia': '#1f77b4',
            'Distribución': '#7fcdbb',
            'Generación': '#2ca02c'
        }
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=True,
        yaxis_type='log'  # Log scale due to large differences
    )
    
    return fig


def create_type_distribution(df):
    """Create transformer type distribution pie chart."""
    type_counts = df['category'].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            hole=0.4,
            marker_colors=['#1f77b4', '#7fcdbb', '#2ca02c']
        )
    ])
    
    fig.update_layout(
        title="Distribución por Tipo de Transformador",
        annotations=[
            dict(
                text=f'{len(df)}<br>Total',
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )
        ]
    )
    
    return fig


def create_regulation_details(transformers_data):
    """Create regulation system details."""
    regulation_items = []
    
    # Find transformers with regulation
    for location_key, location_data in transformers_data.items():
        if not isinstance(location_data, dict):
            continue
            
        location_name = location_data.get('ubicacion', location_key)
        
        if 'transformador_principal' in location_data:
            t_data = location_data['transformador_principal']
            reg_data = t_data.get('regulacion', {})
            
            if reg_data:
                reg_type = reg_data.get('tipo', 'N/A')
                
                # Determine icon and color based on type
                if 'RBC' in reg_type or 'OLTC' in reg_type:
                    icon = "fas fa-cog"
                    color = "success"
                    badge_text = "Automático"
                else:
                    icon = "fas fa-sliders-h"
                    color = "info"
                    badge_text = "Manual"
                
                regulation_items.append(
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.H5([
                                        html.I(className=f"{icon} me-2"),
                                        location_name
                                    ], className=f"text-{color}"),
                                    html.P([
                                        dbc.Badge(reg_type, color=color, className="me-2"),
                                        dbc.Badge(badge_text, color="secondary")
                                    ]),
                                    html.Ul([
                                        html.Li(f"Rango: {reg_data.get('rango', 'N/D')}"),
                                        html.Li(f"Pasos: {reg_data.get('pasos', reg_data.get('posiciones', 'N/D'))}"),
                                        html.Li(f"Control: {reg_data.get('control', 'Manual')}")
                                    ])
                                ])
                            ])
                        ])
                    ], className="mb-3")
                )
    
    return dbc.Card([
        dbc.CardBody([
            html.H4("Equipamiento de Regulación de Tensión", className="mb-3"),
            html.P("Sistemas instalados para control de tensión en el sistema radial"),
            html.Hr(),
            html.Div(regulation_items)
        ])
    ], className="mt-3")