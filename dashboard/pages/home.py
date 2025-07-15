"""
Página principal - Vista general del sistema EDERSA
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Registrar página
dash.register_page(__name__, path='/', name='Vista General', order=1)

# Importar utilidades
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.components.metrics_cards import (
    create_metric_card, create_summary_card, 
    create_progress_card, create_alert_card
)
from dashboard.utils.data_loader import (
    get_summary_metrics, get_quality_distribution,
    get_vulnerability_distribution, get_top_critical_transformers,
    get_feeder_summary, get_valid_coordinates
)

# Layout de la página
layout = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Vista General del Sistema", className="mb-1"),
            html.P("Resumen ejecutivo del estado de la red EDERSA", className="text-muted")
        ])
    ], className="mb-4"),
    
    # Alertas importantes
    dbc.Row([
        dbc.Col([
            create_alert_card(
                "89 transformadores en estado crítico requieren atención inmediata",
                color="danger",
                icon="fas fa-exclamation-circle"
            )
        ])
    ], className="mb-4", id="alerts-row"),
    
    # Métricas principales
    dbc.Row([
        dbc.Col([
            html.Div(id="metric-transformadores")
        ], xs=12, sm=6, md=3),
        dbc.Col([
            html.Div(id="metric-usuarios")
        ], xs=12, sm=6, md=3),
        dbc.Col([
            html.Div(id="metric-capacidad")
        ], xs=12, sm=6, md=3),
        dbc.Col([
            html.Div(id="metric-problemas")
        ], xs=12, sm=6, md=3),
    ], className="mb-4"),
    
    # Gráficos principales
    dbc.Row([
        # Mapa de transformadores
        dbc.Col([
            create_summary_card(
                "Distribución Geográfica de Transformadores",
                dcc.Loading(
                    dcc.Graph(id="map-transformadores", style={"height": "500px"}),
                    type="circle"
                ),
                icon="fas fa-map-marked-alt"
            )
        ], md=8),
        
        # Distribución de calidad
        dbc.Col([
            create_summary_card(
                "Estado de Calidad",
                dcc.Loading(
                    dcc.Graph(id="pie-calidad", style={"height": "250px"}),
                    type="circle"
                ),
                icon="fas fa-chart-pie"
            ),
            create_summary_card(
                "Niveles de Vulnerabilidad",
                dcc.Loading(
                    dcc.Graph(id="bar-vulnerabilidad", style={"height": "230px"}),
                    type="circle"
                ),
                icon="fas fa-exclamation-triangle"
            )
        ], md=4)
    ], className="mb-4"),
    
    # Análisis por alimentador
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Top 10 Alimentadores Críticos",
                dcc.Loading(
                    dcc.Graph(id="bar-alimentadores", style={"height": "400px"}),
                    type="circle"
                ),
                icon="fas fa-network-wired"
            )
        ], md=6),
        
        # Transformadores críticos
        dbc.Col([
            create_summary_card(
                "Transformadores Más Vulnerables",
                html.Div(id="table-criticos"),
                icon="fas fa-list"
            )
        ], md=6)
    ], className="mb-4"),
    
    # Estadísticas adicionales
    dbc.Row([
        dbc.Col([
            html.Div(id="progress-cards")
        ])
    ])
])

# Callbacks
@callback(
    [Output("metric-transformadores", "children"),
     Output("metric-usuarios", "children"),
     Output("metric-capacidad", "children"),
     Output("metric-problemas", "children")],
    Input("alerts-row", "id")  # Trigger inicial
)
def update_metrics(_):
    """Actualiza las tarjetas de métricas principales"""
    metrics = get_summary_metrics()
    
    return [
        create_metric_card(
            "Transformadores",
            f"{metrics['total_transformadores']:,}",
            "fas fa-bolt",
            color="primary",
            subtitle=f"{metrics['alimentadores_total']} alimentadores"
        ),
        create_metric_card(
            "Usuarios",
            f"{metrics['total_usuarios']:,}",
            "fas fa-users",
            color="info"
        ),
        create_metric_card(
            "Capacidad Total",
            f"{metrics['capacidad_total_mva']:.1f} MVA",
            "fas fa-power-off",
            color="success"
        ),
        create_metric_card(
            "Tasa de Problemas",
            f"{metrics['tasa_problemas']:.1f}%",
            "fas fa-exclamation-triangle",
            color="warning" if metrics['tasa_problemas'] < 50 else "danger",
            subtitle=f"{metrics['transformadores_criticos']} críticos"
        )
    ]

@callback(
    Output("map-transformadores", "figure"),
    Input("alerts-row", "id")
)
def update_map(_):
    """Actualiza el mapa de transformadores"""
    try:
        df = get_valid_coordinates()
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de coordenadas disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                height=500,
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )
            return fig
        
        # Verificar que las columnas existan
        if 'Coord_X' not in df.columns or 'Coord_Y' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No se encontraron columnas de coordenadas",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(height=500)
            return fig
        
        # Colores por estado
        color_map = {
            'Correcta': '#10b981',
            'Penalizada': '#f59e0b', 
            'Fallida': '#ef4444'
        }
        
        # Preparar hover data con columnas que existen
        hover_cols = {}
        for col in ["Codigoct", "N_Sucursal", "Alimentador", "Potencia", "Q_Usuarios"]:
            if col in df.columns:
                hover_cols[col] = True
        
        # Calcular centro del mapa
        center_lat = df['Coord_Y'].mean()
        center_lon = df['Coord_X'].mean()
        
        fig = px.scatter_mapbox(
            df,
            lat="Coord_Y",
            lon="Coord_X",
            color="Resultado" if "Resultado" in df.columns else None,
            color_discrete_map=color_map,
            hover_data=hover_cols,
            zoom=7,
            center={"lat": center_lat, "lon": center_lon},
            height=500,
            title="",
            labels={"Resultado": "Estado"}
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_map: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error al generar el mapa: {str(e)[:50]}...",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(height=500)
        return fig

@callback(
    Output("pie-calidad", "figure"),
    Input("alerts-row", "id")
)
def update_pie_calidad(_):
    """Actualiza el gráfico de distribución de calidad"""
    dist = get_quality_distribution()
    
    if dist.empty:
        return go.Figure()
    
    colors = ['#10b981', '#f59e0b', '#ef4444']
    
    fig = go.Figure(data=[
        go.Pie(
            labels=dist['Resultado'],
            values=dist['count'],
            hole=0.4,
            marker_colors=colors
        )
    ])
    
    fig.update_layout(
        showlegend=True,
        height=250,
        margin=dict(l=20, r=20, t=30, b=20),
        annotations=[dict(text='Estados', x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    
    return fig

@callback(
    Output("bar-vulnerabilidad", "figure"),
    Input("alerts-row", "id")
)
def update_bar_vulnerabilidad(_):
    """Actualiza el gráfico de vulnerabilidad"""
    dist = get_vulnerability_distribution()
    
    if dist.empty:
        return go.Figure()
    
    colors = {
        'Crítica': '#ef4444',
        'Alta': '#f59e0b',
        'Media': '#eab308',
        'Baja': '#3b82f6',
        'Mínima': '#10b981'
    }
    
    fig = go.Figure([
        go.Bar(
            x=dist['nivel_vulnerabilidad'],
            y=dist['count'],
            marker_color=[colors.get(x, '#gray') for x in dist['nivel_vulnerabilidad']]
        )
    ])
    
    fig.update_layout(
        showlegend=False,
        height=230,
        margin=dict(l=20, r=20, t=30, b=40),
        xaxis_title="",
        yaxis_title="Cantidad"
    )
    
    return fig

@callback(
    Output("bar-alimentadores", "figure"),
    Input("alerts-row", "id")
)
def update_bar_alimentadores(_):
    """Actualiza el gráfico de alimentadores críticos"""
    try:
        summary = get_feeder_summary()
        
        if summary.empty or 'tasa_problemas' not in summary.columns:
            # Crear figura vacía con mensaje
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de alimentadores disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="gray")
            )
            fig.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=30, b=40)
            )
            return fig
        
        # Top 10 por tasa de problemas
        top_10 = summary.nlargest(10, 'tasa_problemas')
        
        if top_10.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No se encontraron alimentadores con problemas",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="gray")
            )
        else:
            fig = go.Figure([
                go.Bar(
                    y=top_10.index,
                    x=top_10['tasa_problemas'] * 100,
                    orientation='h',
                    marker_color='#ef4444',
                    text=[f"{x:.1f}%" for x in top_10['tasa_problemas'] * 100],
                    textposition='auto'
                )
            ])
        
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=30, b=40),
            xaxis_title="Tasa de Problemas (%)",
            yaxis_title="",
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_bar_alimentadores: {e}")
        # Figura de error
        fig = go.Figure()
        fig.add_annotation(
            text="Error al cargar datos de alimentadores",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(height=400)
        return fig

@callback(
    Output("table-criticos", "children"),
    Input("alerts-row", "id")
)
def update_table_criticos(_):
    """Actualiza la tabla de transformadores críticos"""
    df = get_top_critical_transformers(10)
    
    if df.empty:
        return html.P("No hay datos disponibles", className="text-muted")
    
    # Seleccionar solo columnas que existen
    cols_to_show = []
    for col in ['Codigoct', 'Codigo', 'N_Sucursal', 'Potencia', 'Q_Usuarios', 
                'criticidad_compuesta', 'indice_vulnerabilidad_compuesto']:
        if col in df.columns:
            cols_to_show.append(col)
    
    if not cols_to_show:
        return html.P("No hay columnas disponibles para mostrar", className="text-muted")
    
    # Limitar a 5 columnas para que quepa bien
    cols_to_show = cols_to_show[:5]
    
    # Crear tabla
    return dbc.Table.from_dataframe(
        df[cols_to_show],
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        size="sm"
    )

@callback(
    Output("progress-cards", "children"),
    Input("alerts-row", "id")
)
def update_progress_cards(_):
    """Actualiza las tarjetas de progreso"""
    metrics = get_summary_metrics()
    
    cards = []
    
    # Progreso por zona
    cards.append(
        dbc.Col([
            create_progress_card(
                "Análisis por Zona Geográfica",
                [
                    {"label": "Noroeste", "value": 1006, "max": 2690, "color": "primary"},
                    {"label": "Sureste", "value": 1006, "max": 2690, "color": "info"},
                    {"label": "Noreste", "value": 339, "max": 2690, "color": "warning"},
                    {"label": "Suroeste", "value": 338, "max": 2690, "color": "success"}
                ],
                icon="fas fa-map"
            )
        ], md=6)
    )
    
    # Progreso por tamaño
    cards.append(
        dbc.Col([
            create_progress_card(
                "Distribución por Capacidad",
                [
                    {"label": "Micro (<25 kVA)", "value": 1580, "max": 2690, "color": "info"},
                    {"label": "Pequeño (25-100 kVA)", "value": 520, "max": 2690, "color": "primary"},
                    {"label": "Mediano (100-315 kVA)", "value": 511, "max": 2690, "color": "warning"},
                    {"label": "Grande (>315 kVA)", "value": 79, "max": 2690, "color": "danger"}
                ],
                icon="fas fa-weight"
            )
        ], md=6)
    )
    
    return dbc.Row(cards)