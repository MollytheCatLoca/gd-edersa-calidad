"""
Tab 2: Análisis de Transformadores
"""

from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
from dashboard.pages.utils import get_data_manager, DataStatus

def render_transformers_tab():
    """Render the transformers tab content."""
    # Get data from data manager
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    transformers_result = dm.get_transformers()
    transformers_data = transformers_result.data if transformers_result.data else {}
    
    # Force data load if needed
    if not transformers_data and transformers_result.status != DataStatus.FALLBACK:
        # Try to trigger load
        dm._load_initial_data()
        transformers_result = dm.get_transformers()
        transformers_data = transformers_result.data if transformers_result.data else {}
    
    # Count transformers with better fallback handling
    num_distribution = 0
    num_gen = 0
    total_transformers = 0
    
    # Try to count from data first
    if transformers_data and isinstance(transformers_data, dict):
        for location_key, location_data in transformers_data.items():
            if isinstance(location_data, dict):
                # Check for single transformer
                if 'transformador_principal' in location_data:
                    total_transformers += 1
                    tipo = location_data['transformador_principal'].get('tipo', '').lower()
                    if 'distribución' in tipo or 'pequeño' in tipo or 'potencia' in tipo:
                        num_distribution += 1
                        
                # Check for multiple transformers (like Los Menucos)
                if 'transformadores' in location_data:
                    if 'distribucion' in location_data['transformadores']:
                        total_transformers += 1
                        num_distribution += 1
                    if 'generacion' in location_data['transformadores']:
                        gen_list = location_data['transformadores']['generacion']
                        if isinstance(gen_list, list):
                            num_gen += len(gen_list)
                            total_transformers += len(gen_list)
    
    # If counts are still zero, just keep them as zero
    # The data will come from DataManager when available
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Análisis Detallado de Transformadores", className="mb-3"),
                html.Hr()
            ])
        ]),
        
        # Metrics cards for transformers
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Total Transformadores", className="text-muted mb-1"),
                        html.H3(str(total_transformers), className="text-primary mb-0"),
                        html.Small(f"{num_distribution} distribución + {num_gen} GD", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Capacidad 132/33", className="text-muted mb-1"),
                        html.H3("25 MVA", className="text-success mb-0"),
                        html.Small("ET Pilcaniyeu", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Capacidad 33/13.2", className="text-muted mb-1"),
                        html.H3("13.54 MVA", className="text-info mb-0"),
                        html.Small("Total distribución", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Con Regulación", className="text-muted mb-1"),
                        html.H3("1 OLTC", className="text-warning mb-0"),
                        html.Small("+ Taps fijos", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3)
        ], className="mb-4"),
        
        # Main transformer table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-bolt me-2"),
                        "Especificaciones Técnicas de Transformadores"
                    ]),
                    dbc.CardBody([
                        html.Div(id="f2-transformer-details-table")
                    ])
                ], className="shadow")
            ], md=12)
        ], className="mb-4"),
        
        # Visualizations row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Distribución de Capacidades"),
                    dbc.CardBody([
                        dcc.Graph(id="f2-transformer-capacity-chart")
                    ])
                ], className="shadow")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Utilización Estimada"),
                    dbc.CardBody([
                        dcc.Graph(id="f2-transformer-utilization-chart")
                    ])
                ], className="shadow")
            ], md=6)
        ])
    ])

@callback(
    Output("f2-transformer-details-table", "children"),
    Input("f2-transformer-details-table", "id")
)
def update_transformer_details_table(_):
    """Create detailed transformer specifications table."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    transformers_result = dm.get_transformers()
    transformers = transformers_result.data if transformers_result.data else {}
    nodes_result = dm.get_nodes()
    nodes = nodes_result.data if nodes_result.data else {}
    
    # Create transformer data from actual system data
    transformers_data = []
    
    # Parse transformer data if available
    if transformers and isinstance(transformers, dict):
        # Parse the new JSON structure
        for location_key, location_data in transformers.items():
            if not isinstance(location_data, dict):
                continue
                
            # Get location name from nodes
            location_name = location_data.get('ubicacion', location_key)
            node_key = location_key.lower().replace('et_', '').replace('_', '')
            node_name = nodes.get(node_key, {}).get('name', location_name)
            
            # Handle single transformer
            if 'transformador_principal' in location_data:
                t_data = location_data['transformador_principal']
                
                # Determine transformer type
                tipo_raw = t_data.get('tipo', '').lower()
                if 'potencia' in tipo_raw:
                    tipo = "Potencia"
                elif 'pequeño' in tipo_raw:
                    tipo = "Pequeño"
                else:
                    tipo = "Distribución"
                
                # Format power
                power = t_data.get('potencia_mva', 0)
                if 'potencia_kva' in t_data:
                    power = t_data['potencia_kva'] / 1000.0
                if power < 1:
                    power_str = f"{int(power * 1000)} kVA"
                else:
                    power_str = f"{power} MVA"
                
                # Format voltage
                voltage_str = t_data.get('relacion', 'N/D')
                
                # Format regulation
                reg_data = t_data.get('regulacion', {})
                if reg_data.get('tipo') == 'RBC (Regulador Bajo Carga)':
                    reg_str = f"OLTC ±{reg_data.get('rango', '±10%').replace('±', '')}"
                elif reg_data.get('tipo') == 'Taps fijos':
                    reg_str = f"Taps {reg_data.get('rango', 'N/D')}"
                else:
                    reg_str = "N/A"
                
                # Determine status
                if power < 0.1:
                    status = "🟡 Pequeño"
                else:
                    status = "🟢 Operativo"
                
                transformers_data.append({
                    "Ubicación": node_name,
                    "Tipo": tipo,
                    "Potencia": power_str,
                    "Tensión": voltage_str,
                    "Conexión": t_data.get('conexion', 'N/D'),
                    "Regulación": reg_str,
                    "Impedancia": f"{t_data.get('impedancia', {}).get('estimada', 'N/D')}%",
                    "Estado": status
                })
            
            # Handle multiple transformers (Los Menucos case)
            if 'transformadores' in location_data:
                tfmr_group = location_data['transformadores']
                
                # Distribution transformer
                if 'distribucion' in tfmr_group:
                    t_data = tfmr_group['distribucion']
                    transformers_data.append({
                        "Ubicación": node_name,
                        "Tipo": "Distribución",
                        "Potencia": f"{t_data.get('potencia_total_estimada', 'N/D')} MVA",
                        "Tensión": t_data.get('relacion', 'N/D'),
                        "Conexión": t_data.get('conexion', 'N/D'),
                        "Regulación": "Taps fijos",
                        "Impedancia": "N/D",
                        "Estado": "🟢 Operativo"
                    })
                
                # Generation transformers
                if 'generacion' in tfmr_group:
                    for gen_tfmr in tfmr_group['generacion']:
                        transformers_data.append({
                            "Ubicación": f"{node_name} - {gen_tfmr.get('asociado_a', 'Gen')}",
                            "Tipo": "Elevador Gen",
                            "Potencia": f"{gen_tfmr.get('potencia_mva', 'N/D')} MVA",
                            "Tensión": gen_tfmr.get('relacion', 'N/D'),
                            "Conexión": gen_tfmr.get('conexion', 'N/D'),
                            "Regulación": "N/A",
                            "Impedancia": "N/D",
                            "Estado": "🟢 Generación"
                        })
    
    df = pd.DataFrame(transformers_data)
    
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
    Output("f2-transformer-capacity-chart", "figure"),
    Input("f2-transformer-capacity-chart", "id")
)
def update_transformer_capacity_chart(_):
    """Create transformer capacity distribution chart."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    transformers_result = dm.get_transformers()
    transformers = transformers_result.data if transformers_result.data else {}
    nodes_result = dm.get_nodes()
    nodes = nodes_result.data if nodes_result.data else {}
    
    # Extract data for the chart
    locations = []
    capacities = []
    types = []
    
    # If no data, use known values
    if not transformers or not isinstance(transformers, dict):
        locations = ['Pilcaniyeu', 'Comallo', 'Jacobacci', 'Maquinchao', 'Los Menucos (3 trafos)']
        capacities = [25, 1.5, 5, 0.5, 10]  # Total capacity per location
        types = ['132/33 kV', '33/13.2 kV', '33/13.2 kV', '33/13.2 kV', '33/13.2 kV + Gen']
    else:
        # Parse transformers with new JSON structure
        for location_key, location_data in transformers.items():
            if not isinstance(location_data, dict):
                continue
                
            location_name = location_data.get('ubicacion', location_key)
            node_key = location_key.lower().replace('et_', '').replace('_', '')
            node_name = nodes.get(node_key, {}).get('name', location_name)
            
            total_capacity = 0
            voltage_str = ""
            transformer_count = 0
            
            # Handle single transformer
            if 'transformador_principal' in location_data:
                t_data = location_data['transformador_principal']
                power = t_data.get('potencia_mva', 0)
                if 'potencia_kva' in t_data:
                    power = t_data['potencia_kva'] / 1000.0
                total_capacity += power
                voltage_str = t_data.get('relacion', 'N/D')
                transformer_count += 1
            
            # Handle multiple transformers
            if 'transformadores' in location_data:
                tfmr_group = location_data['transformadores']
                
                if 'distribucion' in tfmr_group:
                    total_capacity += tfmr_group['distribucion'].get('potencia_total_estimada', 0)
                    voltage_str = tfmr_group['distribucion'].get('relacion', voltage_str)
                    transformer_count += 1
                    
                if 'generacion' in tfmr_group:
                    for gen_tfmr in tfmr_group['generacion']:
                        total_capacity += gen_tfmr.get('potencia_mva', 0)
                        transformer_count += len(tfmr_group['generacion'])
            
            if total_capacity > 0:
                if transformer_count > 1:
                    node_name = f"{node_name} ({transformer_count} trafos)"
                locations.append(node_name)
                capacities.append(total_capacity)
                types.append(voltage_str)
    
    fig = go.Figure()
    
    # Create bar chart
    fig.add_trace(go.Bar(
        x=locations,
        y=capacities,
        text=[f"{cap} MVA<br>{typ}" for cap, typ in zip(capacities, types)],
        textposition='outside',
        marker_color=['darkblue', 'blue', 'lightblue', 'blue', 'lightblue', 'blue', 'green'],
        hovertemplate='<b>%{x}</b><br>Capacidad: %{y} MVA<br>%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Distribución de Capacidad de Transformación por Estación",
        xaxis_title="Estación",
        yaxis_title="Capacidad (MVA)",
        yaxis_type="log",  # Logarithmic scale due to large differences
        height=400,
        showlegend=False
    )
    
    return fig

@callback(
    Output("f2-transformer-utilization-chart", "figure"),
    Input("f2-transformer-utilization-chart", "id")
)
def update_transformer_utilization_chart(_):
    """Create transformer utilization chart."""
    dm = get_data_manager()
    # DataManagerV2 returns DataResult, so we need to access .data
    transformers_result = dm.get_transformers()
    transformers_data = transformers_result.data if transformers_result.data else {}
    nodes_result = dm.get_nodes()
    nodes = nodes_result.data if nodes_result.data else {}
    
    # Build utilization data
    transformers = []
    loads = []
    capacities = []
    
    # Parse transformers with new JSON structure
    for location_key, location_data in transformers_data.items():
        if not isinstance(location_data, dict):
            continue
            
        # Skip seccionamiento points
        if location_data.get('tipo') == 'Seccionamiento':
            continue
            
        location_name = location_data.get('ubicacion', location_key)
        node_key = location_key.lower().replace('et_', '').replace('_', '')
        node = nodes.get(node_key, {})
        load_mw = node.get('load_mw', 0)
        
        # Only process if there's load
        if load_mw > 0:
            node_name = node.get('name', location_name)
            
            # Get transformer capacity
            capacity = 0
            if 'transformador_principal' in location_data:
                t_data = location_data['transformador_principal']
                capacity = t_data.get('potencia_mva', 0)
                if 'potencia_kva' in t_data:
                    capacity = t_data['potencia_kva'] / 1000.0
                    
            elif 'transformadores' in location_data and 'distribucion' in location_data['transformadores']:
                capacity = location_data['transformadores']['distribucion'].get('potencia_total_estimada', 0)
            
            if capacity > 0:
                transformers.append(f"{node_name}<br>{capacity} MVA")
                loads.append(load_mw)
                capacities.append(capacity)
    
    utilization = [(load/cap)*100 if cap > 0 else 0 for load, cap in zip(loads, capacities)]
    
    fig = go.Figure()
    
    # Create grouped bar chart
    fig.add_trace(go.Bar(
        name='Carga Actual',
        x=transformers,
        y=loads,
        yaxis='y',
        marker_color='blue',
        text=[f"{load} MW" for load in loads],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Capacidad',
        x=transformers,
        y=capacities,
        yaxis='y',
        marker_color='lightgray',
        opacity=0.5,
        text=[f"{cap} MVA" for cap in capacities],
        textposition='inside'
    ))
    
    # Add utilization percentage as scatter
    fig.add_trace(go.Scatter(
        name='Utilización %',
        x=transformers,
        y=utilization,
        yaxis='y2',
        mode='lines+markers+text',
        marker=dict(size=10, color='red'),
        line=dict(color='red', width=2),
        text=[f"{u:.1f}%" for u in utilization],
        textposition='top center'
    ))
    
    fig.update_layout(
        title="Utilización de Transformadores",
        xaxis_title="Transformador",
        yaxis=dict(title="Potencia (MW/MVA)", side='left'),
        yaxis2=dict(title="Utilización (%)", overlaying='y', side='right', range=[0, 110]),
        height=400,
        barmode='overlay',
        hovermode='x unified'
    )
    
    return fig