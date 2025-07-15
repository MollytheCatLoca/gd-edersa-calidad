"""
Tab 5: Sistema de Regulación
"""

from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
from dashboard.pages.utils import get_data_manager

def render_regulation_tab():
    """Render the regulation tab content."""
    # Get data from data manager
    dm = get_data_manager()
    
    # Count regulators from system data
    # get_system_data() returns tuple (data, status) in compatibility mode
    system_data, status = dm.get_system_data()
    regulators = system_data.get('regulators', {}) if system_data else {}
    num_regulators = len(regulators)
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Análisis del Sistema de Regulación de Tensión", className="mb-3"),
                html.Hr()
            ])
        ]),
        
        # Summary metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Total Reguladores", className="text-muted mb-1"),
                        html.H3(str(num_regulators if num_regulators > 0 else 3), className="text-primary mb-0"),
                        html.Small("Críticos para operación", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Rango Total", className="text-muted mb-1"),
                        html.H3("±30%", className="text-success mb-0"),
                        html.Small("Combinado", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Mejora Tensión", className="text-muted mb-1"),
                        html.H3("+26%", className="text-warning mb-0"),
                        html.Small("En extremo", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Estado", className="text-muted mb-1"),
                        html.H3("CRÍTICO", className="text-danger mb-0"),
                        html.Small("Sin reguladores: colapso", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=3)
        ], className="mb-4"),
        
        # Regulators table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-sliders-h me-2"),
                        "Detalle de Reguladores"
                    ]),
                    dbc.CardBody([
                        html.Div(id="f5-regulators-table")
                    ])
                ], className="shadow")
            ], md=12)
        ], className="mb-4"),
        
        # Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Impacto en Perfil de Tensión"),
                    dbc.CardBody([
                        dcc.Graph(id="f5-voltage-impact")
                    ])
                ], className="shadow")
            ], md=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Utilización de Rango"),
                    dbc.CardBody([
                        dcc.Graph(id="f5-tap-usage")
                    ])
                ], className="shadow")
            ], md=4)
        ])
    ])

@callback(
    Output("f5-regulators-table", "children"),
    Input("f5-regulators-table", "id")
)
def update_regulators_table(_):
    """Create regulators table."""
    dm = get_data_manager()
    system_data, _ = dm.get_system_data()
    regulators = system_data.get('regulators', {}) if system_data else {}
    # DataManagerV2 returns DataResult, so we need to access .data
    nodes_result = dm.get_nodes()
    nodes = nodes_result.data if nodes_result.data else {}
    
    data = []
    
    # Build table from actual regulator data
    for reg_key, reg_data in regulators.items():
        location = reg_data.get('location', '')
        node_name = nodes.get(location, {}).get('name', location.title())
        
        # Format type
        reg_type = reg_data.get('type', '')
        if 'oltc' in reg_type.lower() or 'on_load' in reg_type.lower():
            tipo = "OLTC"
        elif 'series' in reg_type.lower():
            tipo = "Serie"
        else:
            tipo = reg_type.replace('_', ' ').title()
        
        data.append({
            "Ubicación": node_name,
            "Tipo": tipo,
            "Tensión": reg_data.get('voltage_kv', 'N/D'),
            "Rango": f"±{reg_data.get('range_percent', 10)}%",
            "Pasos": reg_data.get('steps', 'N/D'),
            "Control": reg_data.get('control', 'automatic').capitalize(),
            "Estado": reg_data.get('status', 'operational').capitalize()
        })
    
    # If no regulators in data, use fallback
    if not data:
        data = [
            {
                "Ubicación": "Pilcaniyeu FALSO",
                "Tipo": "OLTC",
                "Tensión": "132/33 kV",
                "Rango": "±10%",
                "Pasos": "17",
                "Control": "Automático",
                "Estado": "Operativo"
            },
            {
                "Ubicación": "Jacobacci - FALSO",
                "Tipo": "Serie",
                "Tensión": "33/33 kV",
                "Rango": "±10%",
                "Pasos": "33",
                "Control": "Automático",
                "Estado": "Operativo"
            },
            {
                "Ubicación": "Los Menucos FALSO",
                "Tipo": "Serie",
                "Tensión": "13.2/13.2 kV",
                "Rango": "±10%",
                "Pasos": "33",
                "Control": "Automático",
                "Estado": "Operativo"
            }
        ]
    
    df = pd.DataFrame(data)
    return dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, responsive=True)

@callback(
    Output("f5-voltage-impact", "figure"),
    Input("f5-voltage-impact", "id")
)
def update_voltage_impact(_):
    """Show voltage impact chart."""
    distances = [0, 70, 120, 150, 210, 240, 270]
    stations = ['Pilcaniyeu', 'Comallo', 'Onelli', 'Jacobacci', 'Maquinchao', 'Aguada', 'Los Menucos']
    voltage_no_reg = [1.00, 0.92, 0.85, 0.80, 0.70, 0.65, 0.59]
    voltage_with_reg = [1.00, 0.97, 0.94, 0.95, 0.90, 0.87, 0.85]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=distances,
        y=voltage_no_reg,
        mode='lines+markers',
        name='Sin Regulación',
        line=dict(color='red', width=3, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=distances,
        y=voltage_with_reg,
        mode='lines+markers',
        name='Con Regulación',
        line=dict(color='blue', width=3)
    ))
    
    fig.add_hline(y=0.95, line_dash="dot", line_color="green",
                  annotation_text="Límite superior (0.95 pu)")
    fig.add_hline(y=0.90, line_dash="dot", line_color="orange",
                  annotation_text="Límite inferior (0.90 pu)")
    
    fig.update_layout(
        title="Impacto del Sistema de Regulación",
        xaxis_title="Distancia (km)",
        yaxis_title="Tensión (p.u.)",
        yaxis_range=[0.5, 1.05],
        height=400
    )
    
    return fig

@callback(
    Output("f5-tap-usage", "figure"),
    Input("f5-tap-usage", "id")
)
def update_tap_usage(_):
    """Show tap usage chart."""
    regulators = ['OLTC<br>Pilcaniyeu', 'Serie<br>Jacobacci', 'Serie<br>Los Menucos']
    usage = [62.5, 87.5, 100]
    colors = ['green', 'orange', 'red']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=regulators,
        y=usage,
        marker_color=colors,
        text=[f"{u}%" for u in usage],
        textposition='outside'
    ))
    
    fig.add_hline(y=70, line_dash="dash", line_color="orange",
                  annotation_text="70%")
    fig.add_hline(y=90, line_dash="dash", line_color="red",
                  annotation_text="90%")
    
    fig.update_layout(
        title="Utilización del Rango",
        yaxis_title="Utilización (%)",
        yaxis_range=[0, 110],
        height=400,
        showlegend=False
    )
    
    return fig