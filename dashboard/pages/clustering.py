"""
Página de Análisis de Clustering para Generación Distribuida
"""

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
import json

# Registrar página
dash.register_page(__name__, path='/clustering', name='Análisis de Clustering', order=6)

# Importar utilidades
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.components.metrics_cards import (
    create_metric_card, create_summary_card, create_alert_card
)
from dashboard.utils.data_loader import (
    load_transformadores_completo, get_valid_coordinates
)

# Layout de la página
layout = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Análisis de Clustering para GD", className="mb-1"),
            html.P("Identificación de zonas óptimas para Generación Distribuida mediante clustering espacial", 
                   className="text-muted")
        ])
    ], className="mb-4"),
    
    # Alerta informativa
    dbc.Row([
        dbc.Col([
            create_alert_card(
                "El análisis identifica agrupaciones de transformadores problemáticos para priorizar la instalación de GD",
                color="info",
                icon="fas fa-project-diagram",
                dismissable=False
            )
        ])
    ], className="mb-4"),
    
    # Métricas principales
    dbc.Row([
        dbc.Col([
            html.Div(id="cluster-count-container", children=[
                create_metric_card(
                    "Clusters Identificados",
                    "0",
                    "fas fa-layer-group",
                    color="primary",
                    subtitle="Zonas candidatas"
                )
            ])
        ], xs=6, sm=4, md=3),
        dbc.Col([
            html.Div(id="cluster-trafos-container", children=[
                create_metric_card(
                    "Trafos en Clusters",
                    "0",
                    "fas fa-bolt",
                    color="success",
                    subtitle="Agrupados"
                )
            ])
        ], xs=6, sm=4, md=3),
        dbc.Col([
            html.Div(id="cluster-usuarios-container", children=[
                create_metric_card(
                    "Usuarios Beneficiados",
                    "0",
                    "fas fa-users",
                    color="info",
                    subtitle="Total en clusters"
                )
            ])
        ], xs=6, sm=4, md=3),
        dbc.Col([
            html.Div(id="cluster-capacidad-container", children=[
                create_metric_card(
                    "Capacidad GD Estimada",
                    "0 MW",
                    "fas fa-solar-panel",
                    color="warning",
                    subtitle="Requerida"
                )
            ])
        ], xs=6, sm=4, md=3)
    ], className="mb-4"),
    
    # Controles de clustering
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Parámetros de Clustering", className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Método de Clustering:", className="fw-bold"),
                            dcc.RadioItems(
                                id="cluster-method",
                                options=[
                                    {"label": "DBSCAN (Densidad)", "value": "dbscan"},
                                    {"label": "K-Means", "value": "kmeans"}
                                ],
                                value="dbscan",
                                inline=True
                            )
                        ], md=4),
                        dbc.Col([
                            html.Label("Filtrar por Estado:", className="fw-bold"),
                            dcc.Dropdown(
                                id="cluster-estado-filter",
                                options=[
                                    {"label": "Todos", "value": "all"},
                                    {"label": "Solo Problemáticos (Penalizados + Fallidos)", "value": "problemas"},
                                    {"label": "Solo Fallidos", "value": "fallida"}
                                ],
                                value="fallida",
                                clearable=False
                            )
                        ], md=4),
                        dbc.Col([
                            html.Label("Sucursal:", className="fw-bold"),
                            dcc.Dropdown(
                                id="cluster-sucursal-filter",
                                options=[],
                                value=None,
                                placeholder="Todas las sucursales",
                                clearable=True
                            )
                        ], md=4)
                    ], className="mb-3"),
                    
                    # Parámetros específicos
                    html.Div(id="cluster-params-container", children=[
                        # Contenedores vacíos para los parámetros que se crearán dinámicamente
                        html.Div([
                            dcc.Input(id="cluster-eps", type="hidden", value=0.5),
                            dcc.Input(id="cluster-min-samples", type="hidden", value=5),
                            dcc.Input(id="cluster-n-clusters", type="hidden", value=8)
                        ], style={"display": "none"})
                    ]),
                    
                    # Botón de actualizar
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Ejecutar Clustering",
                                id="cluster-run-button",
                                color="primary",
                                size="lg",
                                className="w-100 mt-3"
                            )
                        ], md=6, className="mx-auto")
                    ])
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Visualizaciones principales
    dbc.Row([
        # Mapa de clusters
        dbc.Col([
            create_summary_card(
                "Mapa de Clusters Identificados",
                dcc.Loading(
                    dcc.Graph(
                        id="cluster-map",
                        style={"height": "600px"},
                        config={'displayModeBar': True}
                    ),
                    type="circle"
                ),
                icon="fas fa-map-marked-alt"
            )
        ], md=8),
        
        # Panel de información del cluster
        dbc.Col([
            create_summary_card(
                "Información del Cluster",
                html.Div(id="cluster-info", className="p-3"),
                icon="fas fa-info-circle"
            ),
            html.Br(),
            create_summary_card(
                "Recomendación GD",
                html.Div(id="cluster-gd-recommendation", className="p-3"),
                icon="fas fa-solar-panel"
            )
        ], md=4)
    ], className="mb-4"),
    
    # Análisis de clusters
    dbc.Row([
        # Características por cluster
        dbc.Col([
            create_summary_card(
                "Características por Cluster",
                dcc.Loading(
                    dcc.Graph(
                        id="cluster-characteristics",
                        style={"height": "400px"}
                    ),
                    type="circle"
                ),
                icon="fas fa-chart-radar"
            )
        ], md=6),
        
        # Priorización de clusters
        dbc.Col([
            create_summary_card(
                "Priorización de Clusters para GD",
                dcc.Loading(
                    dcc.Graph(
                        id="cluster-priority",
                        style={"height": "400px"}
                    ),
                    type="circle"
                ),
                icon="fas fa-sort-amount-down"
            )
        ], md=6)
    ], className="mb-4"),
    
    # Tabla resumen de clusters
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Resumen Detallado de Clusters",
                html.Div(id="cluster-summary-table"),
                icon="fas fa-table"
            )
        ])
    ]),
    
    # Store para guardar resultados de clustering
    dcc.Store(id="cluster-results-store"),
    
    # Componentes ocultos para evitar errores de callback
    html.Div([
        dcc.Input(id="cluster-eps-slider", type="hidden", value=0.5),
        dcc.Input(id="cluster-min-samples-slider", type="hidden", value=5),
        dcc.Input(id="cluster-n-clusters-slider", type="hidden", value=8)
    ], style={"display": "none"})
])

# Callbacks
@callback(
    [Output("cluster-sucursal-filter", "options"),
     Output("cluster-params-container", "children")],
    [Input("cluster-method", "value")]
)
def update_controls(method):
    """Actualiza controles según método seleccionado"""
    # Cargar opciones de sucursales
    try:
        df = load_transformadores_completo()
        sucursales = []
        if 'N_Sucursal' in df.columns:
            sucursales = df['N_Sucursal'].dropna().unique()
            sucursales = [str(suc) for suc in sucursales]
        
        options = [{"label": suc, "value": suc} for suc in sorted(sucursales)]
    except:
        options = []
    
    # Parámetros según método
    if method == "dbscan":
        params = html.Div([
            dbc.Row([
                dbc.Col([
                    html.Label("Radio de búsqueda (km):", className="fw-bold"),
                    dcc.Slider(
                        id="cluster-eps-slider",
                        min=0.1,
                        max=5,
                        step=0.1,
                        value=0.5,
                        marks={i/10: f"{i/10}km" for i in [1, 5, 10, 20, 30, 50]},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=6),
                dbc.Col([
                    html.Label("Mínimo de transformadores:", className="fw-bold"),
                    dcc.Slider(
                        id="cluster-min-samples-slider",
                        min=3,
                        max=20,
                        step=1,
                        value=5,
                        marks={i: str(i) for i in [3, 5, 10, 15, 20]},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=6)
            ]),
            # Mantener los inputs ocultos
            html.Div([
                dcc.Input(id="cluster-eps", type="hidden", value=0.5),
                dcc.Input(id="cluster-min-samples", type="hidden", value=5),
                dcc.Input(id="cluster-n-clusters", type="hidden", value=8)
            ], style={"display": "none"})
        ])
    else:  # kmeans
        params = html.Div([
            dbc.Row([
                dbc.Col([
                    html.Label("Número de clusters:", className="fw-bold"),
                    dcc.Slider(
                        id="cluster-n-clusters-slider",
                        min=3,
                        max=20,
                        step=1,
                        value=8,
                        marks={i: str(i) for i in [3, 5, 8, 10, 15, 20]},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=12)
            ]),
            # Mantener los inputs ocultos
            html.Div([
                dcc.Input(id="cluster-eps", type="hidden", value=0.5),
                dcc.Input(id="cluster-min-samples", type="hidden", value=5),
                dcc.Input(id="cluster-n-clusters", type="hidden", value=8)
            ], style={"display": "none"})
        ])
    
    return options, params

# Callback para sincronizar sliders con inputs ocultos
@callback(
    [Output("cluster-eps", "value"),
     Output("cluster-min-samples", "value"),
     Output("cluster-n-clusters", "value")],
    [Input("cluster-eps-slider", "value"),
     Input("cluster-min-samples-slider", "value"),
     Input("cluster-n-clusters-slider", "value")],
    prevent_initial_call=False
)
def sync_parameters(eps_slider, min_samples_slider, n_clusters_slider):
    """Sincroniza valores de sliders con inputs ocultos"""
    # Usar valores por defecto si los sliders no existen
    eps = eps_slider if eps_slider is not None else 0.5
    min_samples = min_samples_slider if min_samples_slider is not None else 5
    n_clusters = n_clusters_slider if n_clusters_slider is not None else 8
    
    return eps, min_samples, n_clusters

@callback(
    [Output("cluster-results-store", "data"),
     Output("cluster-count-container", "children"),
     Output("cluster-trafos-container", "children"),
     Output("cluster-usuarios-container", "children"),
     Output("cluster-capacidad-container", "children")],
    [Input("cluster-run-button", "n_clicks")],
    [State("cluster-method", "value"),
     State("cluster-estado-filter", "value"),
     State("cluster-sucursal-filter", "value"),
     State("cluster-eps", "value"),
     State("cluster-min-samples", "value"),
     State("cluster-n-clusters", "value")]
)
def run_clustering(n_clicks, method, estado_filter, sucursal, eps, min_samples, n_clusters):
    """Ejecuta el clustering y actualiza métricas"""
    if not n_clicks:
        # Valores por defecto
        card1 = create_metric_card("Clusters Identificados", "0", "fas fa-layer-group", 
                                  color="primary", subtitle="Zonas candidatas")
        card2 = create_metric_card("Trafos en Clusters", "0", "fas fa-bolt", 
                                  color="success", subtitle="Agrupados")
        card3 = create_metric_card("Usuarios Beneficiados", "0", "fas fa-users", 
                                  color="info", subtitle="Total en clusters")
        card4 = create_metric_card("Capacidad GD Estimada", "0 MW", "fas fa-solar-panel", 
                                  color="warning", subtitle="Requerida")
        return {}, card1, card2, card3, card4
    
    try:
        # Cargar datos
        df = load_transformadores_completo()
        
        # Filtrar por sucursal
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        
        # Filtrar por estado
        if estado_filter == "problemas":
            df = df[df['Resultado'].isin(['Penalizada', 'Fallida'])]
        elif estado_filter == "fallida":
            df = df[df['Resultado'] == 'Fallida']
        
        # Filtrar coordenadas válidas
        df = df.dropna(subset=['Coord_X', 'Coord_Y'])
        
        if len(df) < 10:
            raise ValueError("No hay suficientes datos para clustering")
        
        # Preparar datos para clustering
        coords = df[['Coord_X', 'Coord_Y']].values
        
        # NO convertir coordenadas - trabajar directamente con grados
        # En Argentina, 1 grado ≈ 111 km es demasiado grande
        coords_km = coords
        
        # Normalizar
        scaler = StandardScaler()
        coords_scaled = scaler.fit_transform(coords_km)
        
        # Ejecutar clustering
        if method == "dbscan":
            # Convertir eps de km a grados (aproximadamente)
            # En Argentina: 1 grado ≈ 111 km en latitud, ~85 km en longitud (a -40°)
            eps_degrees = eps / 100  # eps en km / 100 para obtener grados aproximados
            
            # Como ya normalizamos las coordenadas, ajustar eps
            eps_scaled = eps_degrees * np.mean(scaler.scale_)
            
            clustering = DBSCAN(eps=eps_scaled, min_samples=min_samples or 5)
        else:  # kmeans
            clustering = KMeans(n_clusters=n_clusters or 8, random_state=42)
        
        labels = clustering.fit_predict(coords_scaled)
        df['cluster'] = labels
        
        # Filtrar noise points (-1) para DBSCAN
        df_clustered = df[df['cluster'] >= 0]
        
        # Calcular métricas por cluster
        cluster_stats = []
        for cluster_id in df_clustered['cluster'].unique():
            cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
            
            # Calcular centroide
            centroid_x = cluster_data['Coord_X'].mean()
            centroid_y = cluster_data['Coord_Y'].mean()
            
            # Calcular métricas
            n_trafos = len(cluster_data)
            n_usuarios = cluster_data['Q_Usuarios'].sum() if 'Q_Usuarios' in cluster_data.columns else 0
            capacidad_total = cluster_data['Potencia'].sum() if 'Potencia' in cluster_data.columns else 0
            n_fallidas = (cluster_data['Resultado'] == 'Fallida').sum() if 'Resultado' in cluster_data.columns else 0
            
            # Estimar capacidad GD necesaria (30% de la capacidad total del cluster)
            gd_capacity = capacidad_total * 0.3 / 1000  # MW
            
            cluster_stats.append({
                'cluster_id': int(cluster_id),
                'centroid_x': centroid_x,
                'centroid_y': centroid_y,
                'n_transformadores': n_trafos,
                'n_usuarios': int(n_usuarios),
                'capacidad_total_kva': capacidad_total,
                'n_fallidas': n_fallidas,
                'tasa_falla': n_fallidas / n_trafos if n_trafos > 0 else 0,
                'gd_capacity_mw': gd_capacity,
                'prioridad': n_usuarios * (n_fallidas / n_trafos) if n_trafos > 0 else 0
            })
        
        # Ordenar por prioridad
        cluster_stats = sorted(cluster_stats, key=lambda x: x['prioridad'], reverse=True)
        
        # Calcular métricas totales
        n_clusters = len(cluster_stats)
        total_trafos = sum(c['n_transformadores'] for c in cluster_stats)
        total_usuarios = sum(c['n_usuarios'] for c in cluster_stats)
        total_gd = sum(c['gd_capacity_mw'] for c in cluster_stats)
        
        # Preparar resultado
        result = {
            'df': df.to_dict('records'),
            'cluster_stats': cluster_stats,
            'method': method,
            'n_clusters': n_clusters
        }
        
        # Actualizar tarjetas
        card1 = create_metric_card(
            "Clusters Identificados",
            str(n_clusters),
            "fas fa-layer-group",
            color="primary",
            subtitle="Zonas candidatas"
        )
        
        card2 = create_metric_card(
            "Trafos en Clusters",
            f"{total_trafos:,}",
            "fas fa-bolt",
            color="success",
            subtitle=f"{total_trafos/len(df)*100:.1f}% del total"
        )
        
        card3 = create_metric_card(
            "Usuarios Beneficiados",
            f"{total_usuarios:,}",
            "fas fa-users",
            color="info",
            subtitle="Total en clusters"
        )
        
        card4 = create_metric_card(
            "Capacidad GD Estimada",
            f"{total_gd:.1f} MW",
            "fas fa-solar-panel",
            color="warning",
            subtitle="Requerida"
        )
        
        return result, card1, card2, card3, card4
        
    except Exception as e:
        print(f"Error en run_clustering: {e}")
        error_card = create_metric_card("Error", "N/D", "fas fa-exclamation", color="danger")
        return {}, error_card, error_card, error_card, error_card

@callback(
    Output("cluster-map", "figure"),
    Input("cluster-results-store", "data")
)
def update_cluster_map(results):
    """Actualiza mapa de clusters"""
    if not results or 'df' not in results:
        fig = go.Figure()
        fig.add_annotation(
            text="Ejecute el clustering para ver resultados",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=600)
        return fig
    
    try:
        df = pd.DataFrame(results['df'])
        cluster_stats = results['cluster_stats']
        
        # Crear mapa
        fig = go.Figure()
        
        # Colores para clusters
        colors = px.colors.qualitative.Set3
        
        # Agregar transformadores por cluster
        for i, cluster_id in enumerate(sorted(df['cluster'].unique())):
            if cluster_id >= 0:  # Ignorar noise points
                cluster_data = df[df['cluster'] == cluster_id]
                
                fig.add_trace(go.Scattermapbox(
                    lat=cluster_data['Coord_Y'],
                    lon=cluster_data['Coord_X'],
                    mode='markers',
                    name=f'Cluster {cluster_id}',
                    marker=dict(
                        size=8,
                        color=colors[i % len(colors)]
                    ),
                    text=cluster_data.apply(lambda row: 
                        f"Cluster: {cluster_id}<br>" +
                        f"Código: {row.get('Codigoct', 'N/A')}<br>" +
                        f"Estado: {row.get('Resultado', 'N/A')}<br>" +
                        f"Usuarios: {row.get('Q_Usuarios', 0)}", axis=1),
                    hovertemplate='%{text}<extra></extra>'
                ))
        
        # Agregar centroides de clusters
        for stat in cluster_stats:
            fig.add_trace(go.Scattermapbox(
                lat=[stat['centroid_y']],
                lon=[stat['centroid_x']],
                mode='markers+text',
                name=f"Centro C{stat['cluster_id']}",
                marker=dict(
                    size=20,
                    color='red',
                    symbol='circle'
                ),
                text=[f"C{stat['cluster_id']}"],
                textposition="top center",
                showlegend=False,
                hovertext=f"Cluster {stat['cluster_id']}<br>" +
                         f"Transformadores: {stat['n_transformadores']}<br>" +
                         f"Usuarios: {stat['n_usuarios']:,}<br>" +
                         f"GD Recomendada: {stat['gd_capacity_mw']:.2f} MW"
            ))
        
        # Configurar mapa
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(
                    lat=df['Coord_Y'].mean(),
                    lon=df['Coord_X'].mean()
                ),
                zoom=10
            ),
            height=600,
            title=f"Clusters Identificados - Método: {results['method'].upper()}",
            showlegend=True,
            legend=dict(x=0, y=1)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_cluster_map: {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Error: {str(e)}", showarrow=False)
        return fig

@callback(
    Output("cluster-info", "children"),
    [Input("cluster-map", "clickData")],
    [State("cluster-results-store", "data")]
)
def update_cluster_info(clickData, results):
    """Actualiza información del cluster seleccionado"""
    if not clickData or not results:
        return html.Div([
            html.P("Haga clic en un cluster para ver detalles", className="text-muted"),
            html.Hr(),
            html.Small("La información incluirá:", className="text-muted"),
            html.Ul([
                html.Li("Número de transformadores", className="small text-muted"),
                html.Li("Usuarios afectados", className="small text-muted"),
                html.Li("Capacidad instalada", className="small text-muted"),
                html.Li("Tasa de fallas", className="small text-muted")
            ])
        ])
    
    try:
        # Obtener información del punto clickeado
        point = clickData['points'][0]
        curve_number = point.get('curveNumber', 0)
        
        # Buscar cluster correspondiente
        cluster_stats = results['cluster_stats']
        
        # Estimar cluster basado en curveNumber
        if curve_number < len(cluster_stats):
            stat = cluster_stats[curve_number]
        else:
            stat = cluster_stats[0]
        
        # Crear contenido
        content = [
            html.H5(f"Cluster {stat['cluster_id']}", className="mb-3"),
            html.Hr(),
            
            html.P([
                html.I(className="fas fa-bolt me-2"),
                html.Strong("Transformadores: "),
                f"{stat['n_transformadores']}"
            ]),
            
            html.P([
                html.I(className="fas fa-users me-2"),
                html.Strong("Usuarios: "),
                f"{stat['n_usuarios']:,}"
            ]),
            
            html.P([
                html.I(className="fas fa-power-off me-2"),
                html.Strong("Capacidad Total: "),
                f"{stat['capacidad_total_kva']:,.0f} kVA"
            ]),
            
            html.P([
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Strong("Tasa de Falla: "),
                f"{stat['tasa_falla']*100:.1f}%"
            ], className="text-danger" if stat['tasa_falla'] > 0.5 else ""),
            
            html.Hr(),
            
            html.P([
                html.I(className="fas fa-map-marker-alt me-2"),
                html.Strong("Centroide: "),
                html.Br(),
                f"Lat: {stat['centroid_y']:.4f}",
                html.Br(),
                f"Lon: {stat['centroid_x']:.4f}"
            ], className="small"),
            
            html.Hr(),
            
            html.Div([
                html.Strong("Prioridad: ", className="text-primary"),
                html.Span(f"{stat['prioridad']:.0f}", className="badge bg-primary")
            ])
        ]
        
        return html.Div(content)
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="text-danger")

@callback(
    Output("cluster-gd-recommendation", "children"),
    [Input("cluster-map", "clickData")],
    [State("cluster-results-store", "data")]
)
def update_gd_recommendation(clickData, results):
    """Actualiza recomendación de GD para cluster seleccionado"""
    if not clickData or not results:
        return html.Div([
            html.P("Seleccione un cluster para ver recomendaciones de GD", className="text-muted")
        ])
    
    try:
        # Obtener cluster seleccionado
        point = clickData['points'][0]
        curve_number = point.get('curveNumber', 0)
        
        cluster_stats = results['cluster_stats']
        if curve_number < len(cluster_stats):
            stat = cluster_stats[curve_number]
        else:
            stat = cluster_stats[0]
        
        # Calcular recomendaciones
        gd_mw = stat['gd_capacity_mw']
        n_inversores = max(1, int(gd_mw / 0.5))  # Inversores de 500 kW
        area_solar = gd_mw * 10000  # ~1 hectárea por MW
        
        content = [
            html.H5("Recomendación GD", className="mb-3 text-success"),
            html.Hr(),
            
            dbc.Alert([
                html.H6("Capacidad Recomendada", className="alert-heading"),
                html.H4(f"{gd_mw:.2f} MW", className="text-center my-3"),
                html.P(f"Para cubrir ~30% de la demanda del cluster", className="mb-0 text-center small")
            ], color="success"),
            
            html.H6("Configuración Sugerida:", className="mt-3"),
            html.Ul([
                html.Li([
                    html.Strong("Solar FV: "),
                    f"{gd_mw:.2f} MWp"
                ]),
                html.Li([
                    html.Strong("BESS: "),
                    f"{gd_mw*2:.1f} MWh (2h almacenamiento)"
                ]),
                html.Li([
                    html.Strong("Inversores: "),
                    f"{n_inversores} x 500 kW"
                ]),
                html.Li([
                    html.Strong("Área requerida: "),
                    f"~{area_solar/10000:.1f} hectáreas"
                ])
            ]),
            
            html.Hr(),
            
            html.H6("Beneficios Esperados:", className="mt-3"),
            html.Ul([
                html.Li(f"Mejora de calidad para {stat['n_usuarios']:,} usuarios"),
                html.Li(f"Reducción de pérdidas técnicas"),
                html.Li(f"Aumento de confiabilidad en la zona"),
                html.Li(f"Diferimiento de inversiones en red")
            ], className="small"),
            
            html.Div([
                dbc.Button(
                    "Exportar Análisis",
                    color="primary",
                    size="sm",
                    className="w-100 mt-3",
                    id=f"export-cluster-{stat['cluster_id']}"
                )
            ])
        ]
        
        return html.Div(content)
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="text-danger")

@callback(
    Output("cluster-characteristics", "figure"),
    Input("cluster-results-store", "data")
)
def update_cluster_characteristics(results):
    """Actualiza gráfico de características por cluster"""
    if not results or 'cluster_stats' not in results:
        return go.Figure()
    
    try:
        cluster_stats = results['cluster_stats']
        
        # Preparar datos para gráfico radar
        categories = ['Transformadores', 'Usuarios (k)', 'Capacidad (MVA)', 
                     'Tasa Falla (%)', 'GD (MW)']
        
        fig = go.Figure()
        
        # Agregar hasta 5 clusters principales
        for i, stat in enumerate(cluster_stats[:5]):
            values = [
                stat['n_transformadores'],
                stat['n_usuarios'] / 1000,  # En miles
                stat['capacidad_total_kva'] / 1000,  # En MVA
                stat['tasa_falla'] * 100,
                stat['gd_capacity_mw']
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=f"Cluster {stat['cluster_id']}"
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(max(stat['n_transformadores'] for stat in cluster_stats[:5]), 50)]
                )
            ),
            showlegend=True,
            title="Características de los Top 5 Clusters"
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_cluster_characteristics: {e}")
        return go.Figure()

@callback(
    Output("cluster-priority", "figure"),
    Input("cluster-results-store", "data")
)
def update_cluster_priority(results):
    """Actualiza gráfico de priorización"""
    if not results or 'cluster_stats' not in results:
        return go.Figure()
    
    try:
        cluster_stats = results['cluster_stats']
        
        # Crear DataFrame para visualización
        df_priority = pd.DataFrame(cluster_stats)
        
        # Gráfico de barras con prioridad
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=[f"Cluster {s['cluster_id']}" for s in cluster_stats[:10]],
            x=[s['prioridad'] for s in cluster_stats[:10]],
            orientation='h',
            marker=dict(
                color=[s['prioridad'] for s in cluster_stats[:10]],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Prioridad")
            ),
            text=[f"{s['prioridad']:.0f}" for s in cluster_stats[:10]],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Top 10 Clusters por Prioridad (Usuarios × Tasa de Falla)",
            xaxis_title="Índice de Prioridad",
            yaxis_title="",
            height=400
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_cluster_priority: {e}")
        return go.Figure()

@callback(
    Output("cluster-summary-table", "children"),
    Input("cluster-results-store", "data")
)
def update_summary_table(results):
    """Actualiza tabla resumen de clusters"""
    if not results or 'cluster_stats' not in results:
        return html.Div("Ejecute el clustering para ver el resumen", className="text-muted")
    
    try:
        cluster_stats = results['cluster_stats']
        
        # Preparar datos para tabla
        table_data = []
        for stat in cluster_stats[:10]:  # Top 10
            table_data.append({
                'Cluster': f"C{stat['cluster_id']}",
                'Transformadores': stat['n_transformadores'],
                'Usuarios': f"{stat['n_usuarios']:,}",
                'Capacidad (kVA)': f"{stat['capacidad_total_kva']:,.0f}",
                'Tasa Falla': f"{stat['tasa_falla']*100:.1f}%",
                'GD Rec. (MW)': f"{stat['gd_capacity_mw']:.2f}",
                'Prioridad': f"{stat['prioridad']:.0f}"
            })
        
        # Crear tabla
        table = dash_table.DataTable(
            data=table_data,
            columns=[{"name": i, "id": i} for i in table_data[0].keys()],
            style_cell={
                'textAlign': 'center',
                'padding': '10px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'Prioridad'},
                    'backgroundColor': '#e3f2fd',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{Tasa Falla} > 50%',
                        'column_id': 'Tasa Falla'
                    },
                    'backgroundColor': '#ffcccc',
                    'color': 'black',
                }
            ],
            page_size=10,
            sort_action="native"
        )
        
        return html.Div([
            html.P(f"Mostrando top 10 de {len(cluster_stats)} clusters identificados", 
                  className="text-muted mb-3"),
            table,
            html.Hr(),
            html.Div([
                html.Small("Nota: Los clusters están ordenados por prioridad (usuarios × tasa de falla)", 
                          className="text-muted")
            ])
        ])
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="text-danger")