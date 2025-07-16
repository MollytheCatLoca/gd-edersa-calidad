"""
Página de Análisis IAS 3.0 - Índice de Aptitud Solar con 7 Criterios
VERSIÓN CORREGIDA SIN PROBLEMAS DE RENDERIZADO
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
dash.register_page(__name__, path='/ias-v3', name='IAS 3.0 Analysis', order=7)

# Importar utilidades
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.components.metrics_cards import (
    create_metric_card, create_summary_card, create_alert_card
)

# Cargar datos
def load_ias_v3_data():
    """Carga los datos de IAS v3"""
    base_path = Path(__file__).parent.parent.parent
    
    # Cargar clusters con IAS v3
    cluster_file = base_path / "reports" / "clustering" / "ias_v3" / "cluster_ranking_ias_v3.csv"
    if cluster_file.exists():
        df_clusters = pd.read_csv(cluster_file)
    else:
        # Datos de ejemplo si no existe el archivo
        df_clusters = pd.DataFrame({
            'cluster_id': range(15),
            'ias_v3': np.random.uniform(0.4, 0.6, 15),
            'ias_promedio': np.random.uniform(0.35, 0.55, 15),
            'delta_ias': np.random.uniform(-0.1, 0.1, 15),
            'rank_change': np.random.randint(-5, 5, 15),
            'perfil_dominante': np.random.choice(['Comercial', 'Residencial', 'Mixto', 'Industrial'], 15),
            'gd_recomendada_mw': np.random.uniform(1, 35, 15),
            'n_usuarios': np.random.randint(1000, 70000, 15),
            'C1_criticidad': np.random.uniform(3, 8, 15),
            'C2_coincidencia': np.random.uniform(2, 9, 15),
            'C3_vulnerabilidad': np.random.uniform(3, 7, 15),
            'C4_cargabilidad': np.random.uniform(4, 8, 15),
            'C5_riesgo_rpf': np.random.uniform(2, 7, 15),
            'C6_q_at_night': np.random.uniform(4, 9, 15),
            'C7_land_availability': np.random.uniform(2, 8, 15)
        })
    
    # Cargar reporte JSON
    report_file = base_path / "reports" / "clustering" / "ias_v3" / "ias_v3_analysis_report.json"
    if report_file.exists():
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
    else:
        report = {
            'summary': {'avg_ias_v3': 0.467, 'avg_ias_original': 0.458, 'avg_delta': 0.009,
                       'clusters_improved': 8, 'clusters_worsened': 7},
            'metadata': {'criteria_weights': {'C1': 0.087, 'C2': 0.201, 'C3': 0.031,
                                            'C4': 0.056, 'C5': 0.120, 'C6': 0.301, 'C7': 0.204}}
        }
    
    return df_clusters, report

# Layout de la página
layout = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Análisis IAS 3.0", className="mb-1"),
            html.P("Índice de Aptitud Solar con 7 criterios incluyendo Q at Night y disponibilidad de terreno", 
                   className="text-muted")
        ])
    ], className="mb-4"),
    
    # Alerta informativa
    dbc.Row([
        dbc.Col([
            create_alert_card(
                "IAS 3.0 incorpora soporte reactivo nocturno (30.1% peso) y disponibilidad de terreno (20.4% peso), transformando la priorización de clusters",
                color="primary",
                icon="fas fa-sun",
                dismissable=True
            )
        ])
    ], className="mb-4"),
    
    # Métricas principales
    html.Div(id="ias-v3-metrics", className="mb-4"),
    
    # Tabs con diferentes vistas
    dbc.Tabs([
        dbc.Tab(label="Comparación IAS", tab_id="comparison"),
        dbc.Tab(label="Análisis de Criterios", tab_id="criteria"),
        dbc.Tab(label="Ranking Top 15", tab_id="ranking"),
        dbc.Tab(label="Mapa de Clusters", tab_id="map"),
        dbc.Tab(label="Impacto por Perfil", tab_id="profile")
    ], id="ias-tabs", active_tab="comparison", className="mb-4"),
    
    # Contenido de los tabs
    html.Div(id="ias-tab-content")
])

@callback(
    Output("ias-v3-metrics", "children"),
    Input("ias-tabs", "active_tab")  # Trigger on page load
)
def update_metrics(active_tab):
    """Actualiza las métricas principales"""
    df_clusters, report = load_ias_v3_data()
    
    metrics = dbc.Row([
        dbc.Col([
            create_metric_card(
                "IAS 3.0 Promedio",
                f"{report['summary']['avg_ias_v3']:.3f}",
                "vs " + f"{report['summary']['avg_ias_original']:.3f} original",
                icon="fas fa-sun",
                color="primary"
            )
        ], md=3),
        dbc.Col([
            create_metric_card(
                "Clusters Mejorados",
                str(report['summary']['clusters_improved']),
                f"de {len(df_clusters)} totales",
                icon="fas fa-arrow-up",
                color="success"
            )
        ], md=3),
        dbc.Col([
            create_metric_card(
                "Mayor Peso",
                "C6: Q at Night",
                "30.1% del score total",
                icon="fas fa-moon",
                color="info"
            )
        ], md=3),
        dbc.Col([
            create_metric_card(
                "Capacidad GD Total",
                f"{df_clusters['gd_recomendada_mw'].sum():.1f} MW",
                f"{df_clusters['n_usuarios'].sum():,} usuarios",
                icon="fas fa-solar-panel",
                color="warning"
            )
        ], md=3)
    ])
    
    return metrics

@callback(
    Output("ias-tab-content", "children"),
    Input("ias-tabs", "active_tab")
)
def update_tab_content(active_tab):
    """Actualiza el contenido según el tab activo"""
    df_clusters, report = load_ias_v3_data()
    
    if active_tab == "comparison":
        return create_comparison_content(df_clusters, report)
    elif active_tab == "criteria":
        return create_criteria_content(df_clusters, report)
    elif active_tab == "ranking":
        return create_ranking_content(df_clusters)
    elif active_tab == "map":
        return create_map_content(df_clusters)
    elif active_tab == "profile":
        return create_profile_content(df_clusters)

def create_comparison_content(df_clusters, report):
    """Crea contenido de comparación IAS original vs v3"""
    
    # Scatter plot IAS original vs v3
    fig_scatter = px.scatter(
        df_clusters,
        x='ias_promedio',
        y='ias_v3',
        size='gd_recomendada_mw',
        color='delta_ias',
        color_continuous_scale='RdYlGn',
        hover_data=['cluster_id', 'perfil_dominante', 'n_usuarios'],
        labels={
            'ias_promedio': 'IAS Original',
            'ias_v3': 'IAS 3.0',
            'delta_ias': 'Δ IAS',
            'gd_recomendada_mw': 'GD (MW)'
        },
        title="Comparación IAS Original vs IAS 3.0"
    )
    
    # Línea diagonal
    fig_scatter.add_trace(
        go.Scatter(x=[0, 1], y=[0, 1], mode='lines',
                  line=dict(dash='dash', color='gray'),
                  showlegend=False)
    )
    
    fig_scatter.update_layout(
        height=500,
        xaxis_range=[0.3, 0.7],
        yaxis_range=[0.3, 0.7]
    )
    
    # Gráfico de cambios en ranking
    df_sorted = df_clusters.sort_values('rank_change')
    colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in df_sorted['rank_change']]
    
    fig_ranking = go.Figure([
        go.Bar(
            y=[f"Cluster {id}" for id in df_sorted['cluster_id']],
            x=df_sorted['rank_change'],
            orientation='h',
            marker_color=colors,
            text=df_sorted['rank_change'],
            textposition='outside'
        )
    ])
    
    fig_ranking.update_layout(
        title="Cambios en Ranking (positivo = mejora)",
        xaxis_title="Cambio en Posición",
        yaxis_title="",
        height=600,
        showlegend=False
    )
    
    return dbc.Row([
        dbc.Col([
            dcc.Graph(id="comparison-scatter-graph", figure=fig_scatter)
        ], md=6),
        dbc.Col([
            dcc.Graph(id="comparison-ranking-graph", figure=fig_ranking)
        ], md=6)
    ])

def create_criteria_content(df_clusters, report):
    """Crea contenido de análisis de criterios - VERSIÓN SIMPLIFICADA"""
    
    # Preparar datos de pesos
    weights = report['metadata']['criteria_weights']
    criteria_data = pd.DataFrame([
        {'Criterio': 'C1: Criticidad', 'Peso': weights['C1']},
        {'Criterio': 'C2: Coincidencia', 'Peso': weights['C2']},
        {'Criterio': 'C3: Vulnerabilidad', 'Peso': weights['C3']},
        {'Criterio': 'C4: Cargabilidad', 'Peso': weights['C4']},
        {'Criterio': 'C5: Riesgo RPF', 'Peso': weights['C5']},
        {'Criterio': 'C6: Q at Night', 'Peso': weights['C6']},
        {'Criterio': 'C7: Terreno', 'Peso': weights['C7']}
    ])
    
    # Gráfico de pesos
    fig_weights = px.bar(
        criteria_data,
        x='Peso',
        y='Criterio',
        orientation='h',
        color='Peso',
        color_continuous_scale='Viridis',
        text='Peso',
        title="Pesos de Criterios en IAS 3.0"
    )
    
    fig_weights.update_traces(texttemplate='%{text:.1%}', textposition='outside')
    fig_weights.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Peso (%)",
        yaxis_title=""
    )
    
    # Heatmap de scores por cluster
    criteria_cols = ['C1_criticidad', 'C2_coincidencia', 'C3_vulnerabilidad',
                    'C4_cargabilidad', 'C5_riesgo_rpf', 'C6_q_at_night', 'C7_land_availability']
    
    # Normalizar scores a 0-1
    scores_matrix = df_clusters.nlargest(10, 'ias_v3')[criteria_cols].values / 10
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=scores_matrix.T,
        x=[f"Cluster {id}" for id in df_clusters.nlargest(10, 'ias_v3')['cluster_id']],
        y=['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7'],
        colorscale='RdYlGn',
        text=np.round(scores_matrix.T, 2),
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    fig_heatmap.update_layout(
        title="Scores por Criterio - Top 10 Clusters",
        height=500
    )
    
    # SIMPLIFICADO: Solo gráficos, sin divs adicionales
    return dbc.Row([
        dbc.Col([
            dcc.Graph(id="criteria-weights-graph", figure=fig_weights)
        ], md=5),
        dbc.Col([
            dcc.Graph(id="criteria-heatmap-graph", figure=fig_heatmap)
        ], md=7)
    ])

def create_ranking_content(df_clusters):
    """Crea tabla de ranking top 15"""
    
    # Preparar datos para la tabla
    df_top15 = df_clusters.nlargest(15, 'ias_v3').copy()
    
    # Formatear columnas
    df_top15['Ranking'] = range(1, 16)
    df_top15['IAS 3.0'] = df_top15['ias_v3'].round(3)
    df_top15['IAS Original'] = df_top15['ias_promedio'].round(3)
    df_top15['Δ Rank'] = df_top15['rank_change'].apply(lambda x: f"{x:+d}" if x != 0 else "0")
    df_top15['GD (MW)'] = df_top15['gd_recomendada_mw'].round(1)
    df_top15['Usuarios'] = df_top15['n_usuarios'].apply(lambda x: f"{x:,}")
    df_top15['C6 Score'] = df_top15['C6_q_at_night'].round(1)
    df_top15['C7 Score'] = df_top15['C7_land_availability'].round(1)
    
    # Seleccionar columnas para mostrar
    columns_to_show = ['Ranking', 'cluster_id', 'IAS 3.0', 'IAS Original', 'Δ Rank',
                      'perfil_dominante', 'GD (MW)', 'Usuarios', 'C6 Score', 'C7 Score']
    
    # Crear tabla
    table = dash_table.DataTable(
        id='ranking-table',
        columns=[{"name": col, "id": col} for col in columns_to_show],
        data=df_top15[columns_to_show].to_dict('records'),
        sort_action="native",
        style_cell={
            'textAlign': 'center',
            'padding': '10px',
            'fontFamily': 'Arial'
        },
        style_header={
            'backgroundColor': 'rgb(30, 58, 138)',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            },
            {
                'if': {'column_id': 'Δ Rank', 'filter_query': '{Δ Rank} > 0'},
                'color': 'green',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'Δ Rank', 'filter_query': '{Δ Rank} < 0'},
                'color': 'red',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'C6 Score', 'filter_query': '{C6 Score} > 7'},
                'backgroundColor': 'rgba(147, 51, 234, 0.2)'
            },
            {
                'if': {'column_id': 'C7 Score', 'filter_query': '{C7 Score} > 6'},
                'backgroundColor': 'rgba(34, 197, 94, 0.2)'
            }
        ],
        style_table={'overflowX': 'auto'}
    )
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Top 15 Clusters por IAS 3.0", className="mb-3"),
                html.P("Los clusters están ordenados por su score IAS 3.0. Note los cambios significativos en ranking para clusters con alto C6 (Q at Night).", 
                      className="text-muted mb-4")
            ])
        ]),
        dbc.Row([
            dbc.Col([
                table
            ])
        ])
    ])

def create_map_content(df_clusters):
    """Crea mapa de clusters con IAS v3"""
    
    # Generar coordenadas ficticias si no existen
    if 'centroid_lat' not in df_clusters.columns:
        # Centrar en área de Río Negro
        base_lat = -39.0
        base_lon = -67.5
        df_clusters['centroid_lat'] = base_lat + np.random.uniform(-2, 2, len(df_clusters))
        df_clusters['centroid_lon'] = base_lon + np.random.uniform(-2, 2, len(df_clusters))
    
    # Crear mapa
    fig_map = px.scatter_mapbox(
        df_clusters,
        lat='centroid_lat',
        lon='centroid_lon',
        size='gd_recomendada_mw',
        color='ias_v3',
        color_continuous_scale='RdYlGn',
        hover_data=['cluster_id', 'perfil_dominante', 'n_usuarios', 'C6_q_at_night', 'C7_land_availability'],
        title="Distribución Geográfica de Clusters - IAS 3.0",
        labels={'ias_v3': 'IAS 3.0', 'gd_recomendada_mw': 'GD (MW)'},
        mapbox_style="open-street-map",
        zoom=6,
        height=600
    )
    
    return html.Div([
        dcc.Graph(id="map-clusters-graph", figure=fig_map)
    ])

def create_profile_content(df_clusters):
    """Crea análisis por perfil de usuario - VERSIÓN SIMPLIFICADA"""
    
    # Agrupar por perfil
    profile_stats = df_clusters.groupby('perfil_dominante').agg({
        'ias_v3': ['mean', 'std', 'count'],
        'ias_promedio': 'mean',
        'delta_ias': 'mean',
        'C6_q_at_night': 'mean',
        'C7_land_availability': 'mean',
        'gd_recomendada_mw': 'sum'
    }).round(3)
    
    # Gráfico de comparación IAS por perfil
    profiles = profile_stats.index
    
    fig_comparison = go.Figure()
    
    fig_comparison.add_trace(go.Bar(
        name='IAS Original',
        x=profiles,
        y=profile_stats[('ias_promedio', 'mean')],
        marker_color='lightblue'
    ))
    
    fig_comparison.add_trace(go.Bar(
        name='IAS 3.0',
        x=profiles,
        y=profile_stats[('ias_v3', 'mean')],
        marker_color='darkblue'
    ))
    
    fig_comparison.update_layout(
        title="IAS Promedio por Perfil de Usuario",
        xaxis_title="Perfil Dominante",
        yaxis_title="IAS Score",
        barmode='group',
        height=400
    )
    
    # Radar chart de características por perfil
    categories = ['IAS 3.0', 'C6: Q Night', 'C7: Terreno', 'GD Total']
    
    fig_radar = go.Figure()
    
    for perfil in profiles:
        values = [
            profile_stats.loc[perfil, ('ias_v3', 'mean')] * 10,  # Escalar a 0-10
            profile_stats.loc[perfil, ('C6_q_at_night', 'mean')],
            profile_stats.loc[perfil, ('C7_land_availability', 'mean')],
            profile_stats.loc[perfil, ('gd_recomendada_mw', 'sum')] / df_clusters['gd_recomendada_mw'].max() * 10
        ]
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=perfil
        ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=True,
        title="Características por Perfil de Usuario",
        height=400
    )
    
    # SIMPLIFICADO: Solo gráficos
    return dbc.Row([
        dbc.Col([
            dcc.Graph(id="profile-comparison-graph", figure=fig_comparison)
        ], md=6),
        dbc.Col([
            dcc.Graph(id="profile-radar-graph", figure=fig_radar)
        ], md=6)
    ])

# Callbacks adicionales pueden agregarse aquí según necesidad