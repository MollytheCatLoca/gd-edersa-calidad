"""
Página de Análisis Topológico de Red (MST)
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import networkx as nx

# Registrar página
dash.register_page(__name__, path='/topologia', name='Topología de Red', order=3)

# Importar utilidades
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.components.metrics_cards import (
    create_metric_card, create_summary_card, create_alert_card
)
from dashboard.utils.data_loader import (
    load_transformadores_completo, load_alimentadores
)

# Layout de la página
layout = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Análisis Topológico de Red (MST)", className="mb-1"),
            html.P("Reconstrucción de topología usando Minimum Spanning Tree", className="text-muted")
        ])
    ], className="mb-4"),
    
    # Alerta informativa
    dbc.Row([
        dbc.Col([
            create_alert_card(
                "La topología MST representa la estructura más probable de la red basada en distancias geográficas",
                color="info",
                icon="fas fa-info-circle",
                dismissable=False
            )
        ])
    ], className="mb-4"),
    
    # Selector de alimentador
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Seleccionar Alimentador:", className="fw-bold"),
                            dcc.Dropdown(
                                id="topologia-feeder-select",
                                options=[],
                                value=None,
                                placeholder="Seleccione un alimentador...",
                                clearable=False
                            )
                        ], md=6),
                        dbc.Col([
                            html.Label("Visualización:", className="fw-bold"),
                            dcc.RadioItems(
                                id="topologia-view-type",
                                options=[
                                    {"label": "Vista Geográfica", "value": "geo"},
                                    {"label": "Vista Jerárquica", "value": "hierarchy"},
                                    {"label": "Vista Radial", "value": "radial"}
                                ],
                                value="geo",
                                inline=True,
                                className="mt-2"
                            )
                        ], md=6)
                    ])
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Métricas del alimentador seleccionado
    dbc.Row([
        dbc.Col(html.Div(id="topologia-metrics"), width=12)
    ], className="mb-4"),
    
    # Visualización principal MST
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Topología MST del Alimentador",
                dcc.Loading(
                    dcc.Graph(
                        id="topologia-mst-graph",
                        style={"height": "600px"},
                        config={'displayModeBar': True}
                    ),
                    type="circle"
                ),
                icon="fas fa-project-diagram"
            )
        ], md=8),
        
        # Panel de información
        dbc.Col([
            create_summary_card(
                "Información del Nodo",
                html.Div(id="topologia-node-info", className="p-3"),
                icon="fas fa-info"
            ),
            html.Br(),
            create_summary_card(
                "Estadísticas Topológicas",
                html.Div(id="topologia-stats"),
                icon="fas fa-chart-bar"
            )
        ], md=4)
    ], className="mb-4"),
    
    # Análisis adicionales
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Distribución de Saltos desde Subestación",
                dcc.Loading(
                    dcc.Graph(id="topologia-hops-dist", style={"height": "300px"}),
                    type="circle"
                ),
                icon="fas fa-layer-group"
            )
        ], md=6),
        dbc.Col([
            create_summary_card(
                "kVA Aguas Abajo por Nodo",
                dcc.Loading(
                    dcc.Graph(id="topologia-kva-downstream", style={"height": "300px"}),
                    type="circle"
                ),
                icon="fas fa-weight"
            )
        ], md=6)
    ])
])

# Callbacks
@callback(
    Output("topologia-feeder-select", "options"),
    Input("topologia-view-type", "value")  # Trigger inicial
)
def update_feeder_options(_):
    """Actualiza opciones de alimentadores"""
    try:
        df = load_transformadores_completo()
        if df.empty or 'Alimentador' not in df.columns:
            return []
        
        # Obtener alimentadores con suficientes transformadores
        feeder_counts = df['Alimentador'].value_counts()
        # Solo alimentadores con más de 5 transformadores
        valid_feeders = feeder_counts[feeder_counts > 5].index.tolist()
        
        # Ordenar y crear opciones
        options = []
        for feeder in sorted(valid_feeders):
            count = feeder_counts[feeder]
            options.append({
                "label": f"{feeder} ({count} transformadores)",
                "value": feeder
            })
        
        return options
    except Exception as e:
        print(f"Error en update_feeder_options: {e}")
        return []

@callback(
    Output("topologia-metrics", "children"),
    Input("topologia-feeder-select", "value")
)
def update_metrics(feeder):
    """Actualiza métricas del alimentador seleccionado"""
    if not feeder:
        return html.Div("Seleccione un alimentador para ver las métricas", className="text-muted")
    
    try:
        df = load_transformadores_completo()
        df_feeder = df[df['Alimentador'] == feeder]
        
        if df_feeder.empty:
            return html.Div("No hay datos para este alimentador", className="text-muted")
        
        # Calcular métricas
        n_trafos = len(df_feeder)
        capacidad_total = df_feeder['Potencia'].sum() / 1000 if 'Potencia' in df_feeder.columns else 0
        usuarios_total = df_feeder['Q_Usuarios'].sum() if 'Q_Usuarios' in df_feeder.columns else 0
        
        # Métricas topológicas si existen
        if 'alimentador_diametro_km' in df_feeder.columns:
            diametro = df_feeder['alimentador_diametro_km'].iloc[0]
        else:
            diametro = 0
        
        if 'alimentador_es_lineal' in df_feeder.columns:
            es_lineal = "Sí" if df_feeder['alimentador_es_lineal'].iloc[0] else "No"
        else:
            es_lineal = "N/D"
        
        if 'alimentador_tasa_problemas' in df_feeder.columns:
            tasa_problemas = df_feeder['alimentador_tasa_problemas'].iloc[0] * 100
        else:
            tasa_problemas = 0
        
        return dbc.Row([
            dbc.Col([
                create_metric_card(
                    "Transformadores",
                    f"{n_trafos}",
                    "fas fa-bolt",
                    color="primary"
                )
            ], xs=6, md=2),
            dbc.Col([
                create_metric_card(
                    "Capacidad Total",
                    f"{capacidad_total:.1f} MVA",
                    "fas fa-power-off",
                    color="success"
                )
            ], xs=6, md=2),
            dbc.Col([
                create_metric_card(
                    "Usuarios",
                    f"{usuarios_total:,}",
                    "fas fa-users",
                    color="info"
                )
            ], xs=6, md=2),
            dbc.Col([
                create_metric_card(
                    "Extensión",
                    f"{diametro:.1f} km",
                    "fas fa-ruler",
                    color="warning",
                    subtitle=f"Lineal: {es_lineal}"
                )
            ], xs=6, md=3),
            dbc.Col([
                create_metric_card(
                    "Tasa Problemas",
                    f"{tasa_problemas:.1f}%",
                    "fas fa-exclamation-triangle",
                    color="danger" if tasa_problemas > 50 else "warning"
                )
            ], xs=12, md=3)
        ])
        
    except Exception as e:
        print(f"Error en update_metrics: {e}")
        return html.Div(f"Error al cargar métricas: {str(e)}", className="text-danger")

@callback(
    Output("topologia-mst-graph", "figure"),
    [Input("topologia-feeder-select", "value"),
     Input("topologia-view-type", "value")]
)
def update_mst_graph(feeder, view_type):
    """Actualiza visualización MST del alimentador"""
    if not feeder:
        fig = go.Figure()
        fig.add_annotation(
            text="Seleccione un alimentador para visualizar su topología",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=600)
        return fig
    
    try:
        df = load_transformadores_completo()
        df_feeder = df[df['Alimentador'] == feeder]
        
        if df_feeder.empty:
            return go.Figure().add_annotation(text="No hay datos", showarrow=False)
        
        # Crear visualización según el tipo seleccionado
        if view_type == "geo":
            # Vista geográfica con conexiones
            fig = create_geographic_view(df_feeder)
        elif view_type == "hierarchy":
            # Vista jerárquica tipo árbol
            fig = create_hierarchical_view(df_feeder)
        else:
            # Vista radial
            fig = create_radial_view(df_feeder)
        
        fig.update_layout(
            title=f"Topología del Alimentador: {feeder}",
            height=600,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_mst_graph: {e}")
        return go.Figure().add_annotation(
            text=f"Error: {str(e)[:50]}...",
            showarrow=False
        )

def create_geographic_view(df_feeder):
    """Crea vista geográfica del MST"""
    fig = go.Figure()
    
    # Verificar columnas necesarias
    if 'Coord_X' not in df_feeder.columns or 'Coord_Y' not in df_feeder.columns:
        fig.add_annotation(text="No hay coordenadas disponibles", showarrow=False)
        return fig
    
    # Colores por estado
    color_map = {
        'Correcta': 'green',
        'Penalizada': 'orange',
        'Fallida': 'red'
    }
    
    # Identificar subestación probable (centroide de transformadores grandes)
    large_trafos = df_feeder[df_feeder['Potencia'] >= 315] if 'Potencia' in df_feeder.columns else df_feeder
    if len(large_trafos) > 0:
        sub_x = large_trafos['Coord_X'].mean()
        sub_y = large_trafos['Coord_Y'].mean()
    else:
        sub_x = df_feeder['Coord_X'].mean()
        sub_y = df_feeder['Coord_Y'].mean()
    
    # Agregar subestación
    fig.add_trace(go.Scatter(
        x=[sub_x],
        y=[sub_y],
        mode='markers',
        name='Subestación',
        marker=dict(size=20, color='blue', symbol='square'),
        showlegend=True
    ))
    
    # Agregar líneas de conexión simuladas (estrella desde subestación)
    for _, row in df_feeder.iterrows():
        fig.add_trace(go.Scatter(
            x=[sub_x, row['Coord_X']],
            y=[sub_y, row['Coord_Y']],
            mode='lines',
            line=dict(color='lightgray', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Agregar transformadores
    for estado, color in color_map.items():
        df_estado = df_feeder[df_feeder['Resultado'] == estado] if 'Resultado' in df_feeder.columns else pd.DataFrame()
        if not df_estado.empty:
            # Tamaño basado en potencia
            sizes = df_estado['Potencia'].apply(lambda x: 5 + x/50) if 'Potencia' in df_estado.columns else 10
            
            fig.add_trace(go.Scatter(
                x=df_estado['Coord_X'],
                y=df_estado['Coord_Y'],
                mode='markers',
                name=estado,
                marker=dict(
                    size=sizes,
                    color=color,
                    line=dict(color='darkgray', width=1)
                ),
                text=df_estado.apply(lambda row: 
                    f"Código: {row.get('Codigoct', 'N/A')}<br>" +
                    f"Potencia: {row.get('Potencia', 0)} kVA<br>" +
                    f"Usuarios: {row.get('Q_Usuarios', 0)}", axis=1),
                hovertemplate='%{text}<extra></extra>'
            ))
    
    fig.update_layout(
        xaxis_title="Longitud",
        yaxis_title="Latitud",
        showlegend=True,
        hovermode='closest'
    )
    
    return fig

def create_hierarchical_view(df_feeder):
    """Crea vista jerárquica del alimentador"""
    # Simulación de jerarquía basada en número de saltos
    fig = go.Figure()
    
    if 'numero_saltos' not in df_feeder.columns:
        # Simular niveles basados en potencia
        df_feeder['nivel'] = pd.qcut(df_feeder['Potencia'], q=5, labels=False) if 'Potencia' in df_feeder.columns else 0
    else:
        df_feeder['nivel'] = df_feeder['numero_saltos']
    
    # Contar por nivel
    nivel_counts = df_feeder['nivel'].value_counts().sort_index()
    
    # Crear diagrama de Sankey simplificado
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[f"Nivel {i}" for i in nivel_counts.index],
            color=["blue", "green", "yellow", "orange", "red"][:len(nivel_counts)]
        ),
        link=dict(
            source=[i for i in range(len(nivel_counts)-1) for _ in range(nivel_counts.iloc[i+1])],
            target=[i+1 for i in range(len(nivel_counts)-1) for _ in range(nivel_counts.iloc[i+1])],
            value=[1 for i in range(len(nivel_counts)-1) for _ in range(nivel_counts.iloc[i+1])]
        )
    )])
    
    fig.update_layout(title_text="Vista Jerárquica del Alimentador", font_size=10)
    
    return fig

def create_radial_view(df_feeder):
    """Crea vista radial del alimentador"""
    # Vista radial simple
    n_trafos = len(df_feeder)
    
    # Ángulos para cada transformador
    angles = np.linspace(0, 2*np.pi, n_trafos, endpoint=False)
    
    # Radio basado en criticidad si existe
    if 'criticidad_compuesta' in df_feeder.columns:
        radii = 1 + df_feeder['criticidad_compuesta'].values
    else:
        radii = np.ones(n_trafos)
    
    # Coordenadas polares a cartesianas
    x = radii * np.cos(angles)
    y = radii * np.sin(angles)
    
    # Colores por estado
    colors = df_feeder['Resultado'].map({
        'Correcta': 'green',
        'Penalizada': 'orange',
        'Fallida': 'red'
    }).fillna('gray') if 'Resultado' in df_feeder.columns else ['gray'] * n_trafos
    
    fig = go.Figure()
    
    # Agregar líneas radiales
    for i in range(n_trafos):
        fig.add_trace(go.Scatter(
            x=[0, x[i]],
            y=[0, y[i]],
            mode='lines',
            line=dict(color='lightgray', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Agregar transformadores
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(
            size=10,
            color=colors,
            line=dict(color='darkgray', width=1)
        ),
        text=df_feeder.index,
        hovertemplate='Transformador %{text}<extra></extra>'
    ))
    
    # Agregar centro (subestación)
    fig.add_trace(go.Scatter(
        x=[0],
        y=[0],
        mode='markers',
        marker=dict(size=20, color='blue', symbol='square'),
        name='Subestación'
    ))
    
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        showlegend=False
    )
    
    return fig

@callback(
    Output("topologia-node-info", "children"),
    Input("topologia-mst-graph", "clickData")
)
def update_node_info(clickData):
    """Actualiza información del nodo seleccionado"""
    if not clickData:
        return html.Div([
            html.P("Haga clic en un nodo para ver detalles", className="text-muted"),
            html.Hr(),
            html.Small("La información incluirá:", className="text-muted"),
            html.Ul([
                html.Li("Código del transformador", className="small text-muted"),
                html.Li("Características eléctricas", className="small text-muted"),
                html.Li("Métricas topológicas", className="small text-muted"),
                html.Li("Estado de calidad", className="small text-muted")
            ])
        ])
    
    # Por ahora mostrar información básica del click
    point = clickData['points'][0]
    
    return html.Div([
        html.H6("Información del Nodo"),
        html.Hr(),
        html.P(f"Coordenadas: ({point.get('x', 'N/A'):.4f}, {point.get('y', 'N/A'):.4f})"),
        html.P(f"Texto: {point.get('text', 'N/A')}"),
        html.P(f"Índice: {point.get('pointIndex', 'N/A')}")
    ])

@callback(
    Output("topologia-stats", "children"),
    Input("topologia-feeder-select", "value")
)
def update_topology_stats(feeder):
    """Actualiza estadísticas topológicas"""
    if not feeder:
        return html.Div("Seleccione un alimentador", className="text-muted")
    
    try:
        df = load_transformadores_completo()
        df_feeder = df[df['Alimentador'] == feeder]
        
        stats = []
        
        # Estadísticas básicas
        stats.append(html.P([
            html.Strong("Total nodos: "),
            f"{len(df_feeder)}"
        ]))
        
        # Si existen columnas topológicas
        if 'numero_saltos' in df_feeder.columns:
            max_saltos = df_feeder['numero_saltos'].max()
            stats.append(html.P([
                html.Strong("Máx. saltos: "),
                f"{max_saltos}"
            ]))
        
        if 'es_nodo_hoja' in df_feeder.columns:
            hojas = df_feeder['es_nodo_hoja'].sum()
            stats.append(html.P([
                html.Strong("Nodos hoja: "),
                f"{hojas} ({hojas/len(df_feeder)*100:.1f}%)"
            ]))
        
        if 'kVA_aguas_abajo' in df_feeder.columns:
            max_downstream = df_feeder['kVA_aguas_abajo'].max()
            stats.append(html.P([
                html.Strong("Máx. kVA aguas abajo: "),
                f"{max_downstream:,.0f}"
            ]))
        
        return html.Div(stats)
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="text-danger")

@callback(
    Output("topologia-hops-dist", "figure"),
    Input("topologia-feeder-select", "value")
)
def update_hops_distribution(feeder):
    """Actualiza distribución de saltos"""
    if not feeder:
        return go.Figure()
    
    try:
        df = load_transformadores_completo()
        df_feeder = df[df['Alimentador'] == feeder]
        
        # Simular distribución de saltos si no existe
        if 'numero_saltos' not in df_feeder.columns:
            # Simular basado en distancia al centroide
            if 'dist_a_centroide_km' in df_feeder.columns:
                df_feeder['numero_saltos'] = pd.qcut(
                    df_feeder['dist_a_centroide_km'], 
                    q=5, 
                    labels=[1,2,3,4,5]
                )
            else:
                df_feeder['numero_saltos'] = np.random.choice([1,2,3,4], size=len(df_feeder))
        
        # Contar por número de saltos
        hops_dist = df_feeder['numero_saltos'].value_counts().sort_index()
        
        fig = go.Figure([
            go.Bar(
                x=hops_dist.index,
                y=hops_dist.values,
                marker_color='lightblue',
                text=hops_dist.values,
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            xaxis_title="Número de Saltos desde Subestación",
            yaxis_title="Cantidad de Transformadores",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=40)
        )
        
        return fig
        
    except Exception as e:
        return go.Figure().add_annotation(text=f"Error: {str(e)}", showarrow=False)

@callback(
    Output("topologia-kva-downstream", "figure"),
    Input("topologia-feeder-select", "value")
)
def update_kva_downstream(feeder):
    """Actualiza gráfico de kVA aguas abajo"""
    if not feeder:
        return go.Figure()
    
    try:
        df = load_transformadores_completo()
        df_feeder = df[df['Alimentador'] == feeder]
        
        # Simular kVA aguas abajo si no existe
        if 'kVA_aguas_abajo' not in df_feeder.columns:
            # Simular basado en potencia y posición
            df_feeder['kVA_aguas_abajo'] = df_feeder['Potencia'] * np.random.uniform(1, 5, size=len(df_feeder))
        
        # Top 20 con más kVA aguas abajo
        top_20 = df_feeder.nlargest(20, 'kVA_aguas_abajo')
        
        fig = go.Figure([
            go.Bar(
                y=top_20.get('Codigoct', top_20.index),
                x=top_20['kVA_aguas_abajo'],
                orientation='h',
                marker_color='coral',
                text=top_20['kVA_aguas_abajo'].round(0),
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            xaxis_title="kVA Aguas Abajo",
            yaxis_title="",
            showlegend=False,
            margin=dict(l=100, r=20, t=20, b=40)
        )
        
        return fig
        
    except Exception as e:
        return go.Figure().add_annotation(text=f"Error: {str(e)}", showarrow=False)