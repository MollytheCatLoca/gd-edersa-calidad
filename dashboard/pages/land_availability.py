"""
Página de Análisis de Disponibilidad de Terreno
"""

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Registrar página
dash.register_page(__name__, path='/land-availability', name='Land Availability', order=8)

# Importar utilidades
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.components.metrics_cards import (
    create_metric_card, create_summary_card, create_alert_card
)

# Cargar datos
def load_land_availability_data():
    """Carga los datos de disponibilidad de terreno"""
    base_path = Path(__file__).parent.parent.parent
    
    # Cargar análisis de terreno
    land_file = base_path / "reports" / "clustering" / "land_availability_detailed.csv"
    if land_file.exists():
        df_land = pd.read_csv(land_file)
    else:
        # Datos de ejemplo si no existe el archivo
        df_land = pd.DataFrame({
            'cluster_id': range(15),
            'mw_required': np.random.uniform(1, 35, 15),
            'hectares_required': np.random.uniform(1, 35, 15),
            'zone_type': np.random.choice(['urbana_densa', 'urbana_media', 'periurbana', 'rural'], 15),
            'base_land_score': np.random.uniform(0.1, 0.9, 15),
            'C7_land_availability': np.random.uniform(0.1, 0.9, 15),
            'feasibility_category': np.random.choice(['Alta', 'Media', 'Baja', 'Muy Baja'], 15),
            'alternative_solutions': [['Solar distribuido', 'Múltiples sitios'] for _ in range(15)]
        })
    
    # Cargar reporte JSON
    report_file = base_path / "reports" / "clustering" / "land_availability_report.json"
    if report_file.exists():
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
    else:
        report = {
            'summary': {
                'total_hectares_required': 120.5,
                'average_c7_score': 0.371,
                'clusters_high_feasibility': 0,
                'clusters_low_feasibility': 12
            },
            'by_zone_type': {
                'rural': {'n_clusters': 2, 'total_hectares': 20, 'avg_c7_score': 0.8},
                'periurbana': {'n_clusters': 5, 'total_hectares': 40, 'avg_c7_score': 0.5},
                'urbana_media': {'n_clusters': 6, 'total_hectares': 50, 'avg_c7_score': 0.3},
                'urbana_densa': {'n_clusters': 2, 'total_hectares': 10.5, 'avg_c7_score': 0.1}
            }
        }
    
    # Agregar coordenadas si no existen
    if 'centroid_lat' not in df_land.columns:
        base_lat = -39.0
        base_lon = -67.5
        df_land['centroid_lat'] = base_lat + np.random.uniform(-2, 2, len(df_land))
        df_land['centroid_lon'] = base_lon + np.random.uniform(-2, 2, len(df_land))
    
    return df_land, report

# Layout de la página
layout = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Análisis de Disponibilidad de Terreno", className="mb-1"),
            html.P("Evaluación de factibilidad para instalación de parques solares (1 ha/MW)", 
                   className="text-muted")
        ])
    ], className="mb-4"),
    
    # Alerta informativa
    dbc.Row([
        dbc.Col([
            create_alert_card(
                "El 67% de los clusters presentan restricciones moderadas a severas de disponibilidad de terreno, requiriendo estrategias innovadoras",
                color="warning",
                icon="fas fa-map",
                dismissable=True
            )
        ])
    ], className="mb-4"),
    
    # Métricas principales
    html.Div(id="land-metrics", className="mb-4"),
    
    # Tabs con diferentes vistas
    dbc.Tabs([
        dbc.Tab(label="Mapa de Factibilidad", tab_id="map"),
        dbc.Tab(label="Análisis por Zona", tab_id="zones"),
        dbc.Tab(label="Clusters Críticos", tab_id="critical"),
        dbc.Tab(label="Estrategias de Mitigación", tab_id="mitigation")
    ], id="land-tabs", active_tab="map", className="mb-4"),
    
    # Contenido de los tabs
    html.Div(id="land-tab-content")
])

@callback(
    Output("land-metrics", "children"),
    Input("land-tabs", "active_tab")  # Trigger on page load
)
def update_metrics(_):
    """Actualiza las métricas principales"""
    df_land, report = load_land_availability_data()
    
    metrics = dbc.Row([
        dbc.Col([
            create_metric_card(
                "Hectáreas Totales",
                f"{report['summary']['total_hectares_required']:.1f} ha",
                "Para 120.5 MW totales",
                icon="fas fa-map-marked-alt",
                color="primary"
            )
        ], md=3),
        dbc.Col([
            create_metric_card(
                "Score C7 Promedio",
                f"{report['summary']['average_c7_score']:.3f}",
                "Escala 0-1",
                icon="fas fa-chart-area",
                color="info"
            )
        ], md=3),
        dbc.Col([
            create_metric_card(
                "Alta Factibilidad",
                str(report['summary']['clusters_high_feasibility']),
                "clusters sin restricciones",
                icon="fas fa-check-circle",
                color="success"
            )
        ], md=3),
        dbc.Col([
            create_metric_card(
                "Baja Factibilidad",
                str(report['summary']['clusters_low_feasibility']),
                "clusters con restricciones",
                icon="fas fa-exclamation-triangle",
                color="danger"
            )
        ], md=3)
    ])
    
    return metrics

@callback(
    Output("land-tab-content", "children"),
    Input("land-tabs", "active_tab")
)
def update_tab_content(active_tab):
    """Actualiza el contenido según el tab activo"""
    df_land, report = load_land_availability_data()
    
    if active_tab == "map":
        return create_map_content(df_land)
    elif active_tab == "zones":
        return create_zones_content(df_land, report)
    elif active_tab == "critical":
        return create_critical_content(df_land)
    elif active_tab == "mitigation":
        return create_mitigation_content(df_land)

def create_map_content(df_land):
    """Crea mapa de factibilidad de terreno"""
    
    # Definir colores por categoría
    color_map = {
        'Alta': '#22c55e',
        'Media': '#eab308',
        'Baja': '#f97316',
        'Muy Baja': '#ef4444'
    }
    
    # Crear mapa
    fig_map = px.scatter_mapbox(
        df_land,
        lat='centroid_lat',
        lon='centroid_lon',
        size='hectares_required',
        color='feasibility_category',
        color_discrete_map=color_map,
        hover_data=['cluster_id', 'mw_required', 'zone_type', 'C7_land_availability'],
        title="Mapa de Factibilidad de Terreno por Cluster",
        labels={
            'hectares_required': 'Hectáreas',
            'feasibility_category': 'Factibilidad',
            'mw_required': 'MW Requeridos'
        },
        mapbox_style="open-street-map",
        zoom=6,
        height=600,
        size_max=30
    )
    
    # Actualizar layout
    fig_map.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return html.Div([
        dcc.Graph(figure=fig_map),
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "El tamaño del círculo representa las hectáreas requeridas. ",
                    "Los colores indican la factibilidad de conseguir el terreno necesario."
                ], color="info", className="mt-3")
            ])
        ])
    ])

def create_zones_content(df_land, report):
    """Crea análisis por tipo de zona"""
    
    # Preparar datos por zona
    zone_data = []
    zone_translations = {
        'rural': 'Rural',
        'periurbana': 'Periurbana',
        'urbana_media': 'Urbana Media',
        'urbana_densa': 'Urbana Densa'
    }
    
    for zone, stats in report['by_zone_type'].items():
        zone_data.append({
            'Zona': zone_translations.get(zone, zone),
            'Clusters': stats['n_clusters'],
            'Hectáreas': stats['total_hectares'],
            'Score C7': stats['avg_c7_score']
        })
    
    df_zones = pd.DataFrame(zone_data)
    
    # Gráfico de barras apiladas
    fig_bars = go.Figure()
    
    fig_bars.add_trace(go.Bar(
        name='Hectáreas Requeridas',
        x=df_zones['Zona'],
        y=df_zones['Hectáreas'],
        yaxis='y',
        marker_color='lightblue',
        text=df_zones['Hectáreas'],
        texttemplate='%{text:.1f} ha',
        textposition='inside'
    ))
    
    fig_bars.add_trace(go.Scatter(
        name='Score C7 Promedio',
        x=df_zones['Zona'],
        y=df_zones['Score C7'],
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='red', width=3),
        marker=dict(size=10)
    ))
    
    fig_bars.update_layout(
        title="Análisis por Tipo de Zona",
        xaxis_title="Tipo de Zona",
        yaxis=dict(
            title="Hectáreas Totales",
            titlefont=dict(color="blue"),
            tickfont=dict(color="blue")
        ),
        yaxis2=dict(
            title="Score C7 Promedio",
            titlefont=dict(color="red"),
            tickfont=dict(color="red"),
            overlaying='y',
            side='right',
            range=[0, 1]
        ),
        height=500,
        hovermode='x unified'
    )
    
    # Scatter plot de hectáreas vs score
    fig_scatter = px.scatter(
        df_land,
        x='hectares_required',
        y='C7_land_availability',
        color='zone_type',
        size='mw_required',
        title="Relación Hectáreas vs Disponibilidad",
        labels={
            'hectares_required': 'Hectáreas Requeridas',
            'C7_land_availability': 'Score C7 (Disponibilidad)',
            'zone_type': 'Tipo de Zona',
            'mw_required': 'MW'
        },
        height=400
    )
    
    fig_scatter.update_xaxis(type="log")
    fig_scatter.add_hline(y=0.5, line_dash="dash", line_color="red",
                         annotation_text="Umbral de factibilidad media")
    
    return dbc.Row([
        dbc.Col([
            dcc.Graph(figure=fig_bars)
        ], md=12),
        dbc.Col([
            dcc.Graph(figure=fig_scatter)
        ], md=12),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Insights por Zona", className="card-title"),
                    html.Ul([
                        html.Li("Zonas rurales: Alta disponibilidad pero pocos clusters"),
                        html.Li("Zonas periurbanas: Balance entre disponibilidad y cantidad"),
                        html.Li("Zonas urbanas medias: Mayor cantidad pero restricciones moderadas"),
                        html.Li("Zonas urbanas densas: Severas restricciones, requieren innovación")
                    ])
                ])
            ], className="mt-3")
        ], md=12)
    ])

def create_critical_content(df_land):
    """Crea análisis de clusters críticos"""
    
    # Identificar clusters críticos (baja factibilidad pero alta necesidad)
    df_critical = df_land[
        (df_land['feasibility_category'].isin(['Baja', 'Muy Baja'])) &
        (df_land['mw_required'] > 5)
    ].sort_values('mw_required', ascending=False)
    
    # Preparar datos para tabla
    df_table = df_critical.copy()
    df_table['MW'] = df_table['mw_required'].round(1)
    df_table['Hectáreas'] = df_table['hectares_required'].round(1)
    df_table['Score C7'] = df_table['C7_land_availability'].round(3)
    df_table['Alternativas'] = df_table['alternative_solutions'].apply(
        lambda x: ', '.join(x[:2]) if isinstance(x, list) else 'Ver estrategias'
    )
    
    # Crear tabla
    table = dash_table.DataTable(
        id='critical-clusters-table',
        columns=[
            {"name": "Cluster ID", "id": "cluster_id"},
            {"name": "MW Requeridos", "id": "MW"},
            {"name": "Hectáreas", "id": "Hectáreas"},
            {"name": "Tipo Zona", "id": "zone_type"},
            {"name": "Score C7", "id": "Score C7"},
            {"name": "Factibilidad", "id": "feasibility_category"},
            {"name": "Alternativas Sugeridas", "id": "Alternativas"}
        ],
        data=df_table.to_dict('records'),
        style_cell={
            'textAlign': 'center',
            'padding': '10px',
            'fontFamily': 'Arial',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': 'rgb(220, 38, 38)',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'feasibility_category', 'filter_query': '{feasibility_category} = "Muy Baja"'},
                'backgroundColor': 'rgba(239, 68, 68, 0.2)',
                'color': 'darkred',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'MW', 'filter_query': '{MW} > 10'},
                'fontWeight': 'bold',
                'color': 'darkblue'
            }
        ],
        style_table={'overflowX': 'auto'}
    )
    
    # Gráfico de clusters críticos
    fig_critical = go.Figure()
    
    fig_critical.add_trace(go.Bar(
        x=df_critical['cluster_id'].astype(str),
        y=df_critical['hectares_required'],
        name='Hectáreas Requeridas',
        marker_color='red',
        opacity=0.7
    ))
    
    fig_critical.add_trace(go.Scatter(
        x=df_critical['cluster_id'].astype(str),
        y=df_critical['C7_land_availability'] * 100,  # Convertir a escala 0-100
        name='Score C7 (%)',
        mode='lines+markers',
        line=dict(color='black', width=2),
        marker=dict(size=8)
    ))
    
    fig_critical.update_layout(
        title="Clusters Críticos: Alta Necesidad, Baja Disponibilidad",
        xaxis_title="Cluster ID",
        yaxis_title="Hectáreas / Score C7 (%)",
        hovermode='x unified',
        height=400
    )
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Clusters con Restricciones Severas de Terreno", className="mb-3"),
                html.P("Estos clusters requieren estrategias especiales debido a la dificultad de conseguir terreno suficiente.", 
                      className="text-muted")
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=fig_critical)
            ], md=12)
        ]),
        dbc.Row([
            dbc.Col([
                table
            ], md=12)
        ], className="mt-4"),
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H5("Impacto en el Proyecto", className="alert-heading"),
                    html.Hr(),
                    html.P(f"Se identificaron {len(df_critical)} clusters críticos que representan "
                          f"{df_critical['mw_required'].sum():.1f} MW de capacidad GD pero requieren "
                          f"{df_critical['hectares_required'].sum():.1f} hectáreas en zonas con restricciones.")
                ], color="danger", className="mt-4")
            ])
        ])
    ])

def create_mitigation_content(df_land):
    """Crea estrategias de mitigación por tipo de restricción"""
    
    # Definir estrategias por categoría
    strategies = {
        'Muy Baja': {
            'title': 'Estrategias para Zonas Urbanas Densas',
            'color': 'danger',
            'icon': 'fas fa-city',
            'solutions': [
                'Solar distribuido en techos comerciales/industriales',
                'Estacionamientos solares (solar carports)',
                'Integración en infraestructura existente',
                'Microrredes comunitarias',
                'Asociación con grandes consumidores'
            ]
        },
        'Baja': {
            'title': 'Estrategias para Zonas Urbanas Medias',
            'color': 'warning',
            'icon': 'fas fa-building',
            'solutions': [
                'División en múltiples sitios menores (2-5 ha)',
                'Aprovechamiento de terrenos baldíos',
                'Zonas industriales subutilizadas',
                'Perímetros urbanos en expansión',
                'Modelos de negocio compartidos'
            ]
        },
        'Media': {
            'title': 'Estrategias para Zonas Periurbanas',
            'color': 'info',
            'icon': 'fas fa-home',
            'solutions': [
                'Negociación estándar con propietarios',
                'Arrendamiento a largo plazo',
                'Desarrollo conjunto con actividades compatibles',
                'Aprovechamiento de franjas de servidumbre',
                'Integración con proyectos de desarrollo urbano'
            ]
        },
        'Alta': {
            'title': 'Estrategias para Zonas Rurales',
            'color': 'success',
            'icon': 'fas fa-tractor',
            'solutions': [
                'Implementación directa sin restricciones',
                'Agrovoltaica (combinación con agricultura)',
                'Arrendamiento de terrenos improductivos',
                'Desarrollo en etapas modulares',
                'Beneficios compartidos con comunidad rural'
            ]
        }
    }
    
    # Crear cards para cada estrategia
    strategy_cards = []
    for category, strategy in strategies.items():
        # Contar clusters en esta categoría
        n_clusters = len(df_land[df_land['feasibility_category'] == category])
        total_mw = df_land[df_land['feasibility_category'] == category]['mw_required'].sum()
        
        card = dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className=f"{strategy['icon']} me-2"),
                    html.Span(strategy['title'])
                ], className=f"bg-{strategy['color']} text-white"),
                dbc.CardBody([
                    html.P(f"{n_clusters} clusters | {total_mw:.1f} MW totales", 
                          className="text-muted mb-3"),
                    html.Ul([html.Li(sol) for sol in strategy['solutions']], 
                           className="mb-0")
                ])
            ], className="h-100")
        ], md=6, className="mb-4")
        
        strategy_cards.append(card)
    
    # Análisis económico de estrategias
    fig_economics = go.Figure()
    
    categories = ['Tradicional\n(1 sitio)', 'Múltiples\nSitios', 'Solar\nDistribuido', 'Híbrido\n(Mixto)']
    capex_relative = [1.0, 1.15, 1.25, 1.20]
    complexity = [0.3, 0.6, 0.8, 0.7]
    feasibility = [0.4, 0.7, 0.9, 0.8]
    
    fig_economics.add_trace(go.Bar(
        name='CAPEX Relativo',
        x=categories,
        y=capex_relative,
        marker_color='lightblue'
    ))
    
    fig_economics.add_trace(go.Scatter(
        name='Complejidad',
        x=categories,
        y=complexity,
        mode='lines+markers',
        line=dict(color='red', width=2),
        yaxis='y2'
    ))
    
    fig_economics.add_trace(go.Scatter(
        name='Factibilidad',
        x=categories,
        y=feasibility,
        mode='lines+markers',
        line=dict(color='green', width=2),
        yaxis='y2'
    ))
    
    fig_economics.update_layout(
        title="Comparación de Estrategias de Implementación",
        xaxis_title="Estrategia",
        yaxis=dict(
            title="CAPEX Relativo",
            range=[0, 1.5]
        ),
        yaxis2=dict(
            title="Score (0-1)",
            overlaying='y',
            side='right',
            range=[0, 1]
        ),
        height=400,
        hovermode='x unified'
    )
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Estrategias de Mitigación por Tipo de Restricción", className="mb-4"),
                html.P("Soluciones adaptadas según la disponibilidad de terreno en cada zona.", 
                      className="text-muted mb-4")
            ])
        ]),
        dbc.Row(strategy_cards),
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=fig_economics)
            ], md=12)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Recomendaciones Clave", className="card-title"),
                        html.Ol([
                            html.Li("Priorizar implementación en clusters con factibilidad Alta/Media"),
                            html.Li("Desarrollar modelos de negocio innovadores para zonas urbanas"),
                            html.Li("Considerar solar distribuido como alternativa viable en zonas densas"),
                            html.Li("Evaluar beneficios adicionales (sombra, agricultura, etc.) para mejorar aceptación"),
                            html.Li("Establecer alianzas estratégicas con propietarios de grandes superficies")
                        ])
                    ])
                ], className="mt-4")
            ])
        ])
    ])

# Callbacks adicionales pueden agregarse aquí según necesidad