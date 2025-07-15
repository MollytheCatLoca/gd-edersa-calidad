"""
Página de Análisis de Vulnerabilidad
"""

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Registrar página
dash.register_page(__name__, path='/vulnerabilidad', name='Análisis de Vulnerabilidad', order=5)

# Importar utilidades
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.components.metrics_cards import (
    create_metric_card, create_summary_card, create_alert_card
)
from dashboard.utils.data_loader import (
    load_transformadores_completo, get_top_critical_transformers
)
from dashboard.utils.vulnerability_helper import (
    create_vulnerability_levels, get_vulnerability_colors, get_vulnerability_order
)

# Layout de la página
layout = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Análisis de Vulnerabilidad", className="mb-1"),
            html.P("Evaluación integral de vulnerabilidad de transformadores", className="text-muted")
        ])
    ], className="mb-4"),
    
    # Alerta informativa
    dbc.Row([
        dbc.Col([
            create_alert_card(
                "Análisis basado en múltiples factores: calidad de servicio, topología de red, características eléctricas y ubicación geográfica",
                color="info",
                icon="fas fa-shield-alt",
                dismissable=False
            )
        ])
    ], className="mb-4"),
    
    # Métricas principales
    dbc.Row([
        dbc.Col([
            html.Div(id="vuln-criticos-container", children=[
                create_metric_card(
                    "Críticos",
                    "0",
                    "fas fa-exclamation-circle",
                    color="danger",
                    subtitle="Nivel máximo"
                )
            ])
        ], xs=6, sm=4, md=2),
        dbc.Col([
            html.Div(id="vuln-altos-container", children=[
                create_metric_card(
                    "Alta",
                    "0",
                    "fas fa-exclamation-triangle",
                    color="warning",
                    subtitle="Vulnerabilidad"
                )
            ])
        ], xs=6, sm=4, md=2),
        dbc.Col([
            html.Div(id="vuln-medios-container", children=[
                create_metric_card(
                    "Media",
                    "0",
                    "fas fa-minus-circle",
                    color="info",
                    subtitle="Vulnerabilidad"
                )
            ])
        ], xs=6, sm=4, md=2),
        dbc.Col([
            html.Div(id="vuln-bajos-container", children=[
                create_metric_card(
                    "Baja",
                    "0",
                    "fas fa-check-circle",
                    color="success",
                    subtitle="Vulnerabilidad"
                )
            ])
        ], xs=6, sm=4, md=2),
        dbc.Col([
            html.Div(id="vuln-usuarios-container", children=[
                create_metric_card(
                    "Usuarios en Riesgo",
                    "0",
                    "fas fa-users",
                    color="primary",
                    subtitle="Alta/Crítica"
                )
            ])
        ], xs=6, sm=4, md=2),
        dbc.Col([
            html.Div(id="vuln-indice-promedio-container", children=[
                create_metric_card(
                    "Índice Promedio",
                    "0.0",
                    "fas fa-tachometer-alt",
                    color="secondary",
                    subtitle="0-1 escala"
                )
            ])
        ], xs=6, sm=4, md=2)
    ], className="mb-4"),
    
    # Filtros
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Sucursal:", className="fw-bold"),
                            dcc.Dropdown(
                                id="vuln-sucursal-select",
                                options=[],
                                value=None,
                                placeholder="Todas las sucursales",
                                clearable=True
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Nivel de Vulnerabilidad:", className="fw-bold"),
                            dcc.Dropdown(
                                id="vuln-nivel-select",
                                options=[
                                    {"label": "Todos", "value": "all"},
                                    {"label": "Crítica", "value": "Crítica"},
                                    {"label": "Alta", "value": "Alta"},
                                    {"label": "Media", "value": "Media"},
                                    {"label": "Baja", "value": "Baja"},
                                    {"label": "Mínima", "value": "Mínima"}
                                ],
                                value="all",
                                clearable=False
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Umbral Índice:", className="fw-bold"),
                            dcc.RangeSlider(
                                id="vuln-indice-slider",
                                min=0,
                                max=1,
                                step=0.1,
                                value=[0, 1],
                                marks={i/10: str(i/10) for i in range(11)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], md=6)
                    ])
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Visualizaciones principales
    dbc.Row([
        # Mapa de vulnerabilidad
        dbc.Col([
            create_summary_card(
                "Mapa de Vulnerabilidad",
                dcc.Loading(
                    dcc.Graph(
                        id="vuln-mapa",
                        style={"height": "500px"},
                        config={'displayModeBar': True}
                    ),
                    type="circle"
                ),
                icon="fas fa-map-marked-alt"
            )
        ], md=8),
        
        # Distribución por nivel
        dbc.Col([
            create_summary_card(
                "Distribución por Nivel",
                dcc.Loading(
                    dcc.Graph(
                        id="vuln-distribucion",
                        style={"height": "500px"}
                    ),
                    type="circle"
                ),
                icon="fas fa-chart-pie"
            )
        ], md=4)
    ], className="mb-4"),
    
    # Análisis de factores
    dbc.Row([
        # Factores contribuyentes
        dbc.Col([
            create_summary_card(
                "Factores Contribuyentes a la Vulnerabilidad",
                dcc.Loading(
                    dcc.Graph(
                        id="vuln-factores",
                        style={"height": "400px"}
                    ),
                    type="circle"
                ),
                icon="fas fa-chart-bar"
            )
        ], md=6),
        
        # Correlación con calidad
        dbc.Col([
            create_summary_card(
                "Vulnerabilidad vs Calidad de Servicio",
                dcc.Loading(
                    dcc.Graph(
                        id="vuln-vs-calidad",
                        style={"height": "400px"}
                    ),
                    type="circle"
                ),
                icon="fas fa-link"
            )
        ], md=6)
    ], className="mb-4"),
    
    # Top transformadores críticos
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Top 10 Transformadores Más Críticos",
                html.Div(id="vuln-top-criticos"),
                icon="fas fa-list-ol"
            )
        ])
    ], className="mb-4"),
    
    # Análisis por sucursal
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Análisis Comparativo por Sucursal",
                dcc.Loading(
                    dcc.Graph(
                        id="vuln-por-sucursal",
                        style={"height": "400px"}
                    ),
                    type="circle"
                ),
                icon="fas fa-building"
            )
        ])
    ])
])

# Callbacks
@callback(
    [Output("vuln-sucursal-select", "options"),
     Output("vuln-criticos-container", "children"),
     Output("vuln-altos-container", "children"),
     Output("vuln-medios-container", "children"),
     Output("vuln-bajos-container", "children"),
     Output("vuln-usuarios-container", "children"),
     Output("vuln-indice-promedio-container", "children")],
    Input("vuln-nivel-select", "value")
)
def update_initial_data(_):
    """Carga datos iniciales y actualiza métricas"""
    try:
        df = load_transformadores_completo()
        
        # Opciones de sucursales
        sucursales = []
        if 'N_Sucursal' in df.columns:
            sucursales = df['N_Sucursal'].dropna().unique()
            sucursales = [str(suc) for suc in sucursales if suc is not None]
            sucursales = sorted(sucursales)
        
        options = [{"label": suc, "value": suc} for suc in sucursales]
        
        # Calcular métricas de vulnerabilidad
        criticos = 0
        altos = 0
        medios = 0
        bajos = 0
        usuarios_riesgo = 0
        indice_promedio = 0.5
        
        # Calcular nivel_vulnerabilidad usando función auxiliar
        if 'nivel_vulnerabilidad' not in df.columns:
            df['nivel_vulnerabilidad'] = create_vulnerability_levels(df)
        
        if 'nivel_vulnerabilidad' in df.columns:
            nivel_counts = df['nivel_vulnerabilidad'].value_counts()
            criticos = nivel_counts.get('Crítica', 0)
            altos = nivel_counts.get('Alta', 0)
            medios = nivel_counts.get('Media', 0)
            bajos = nivel_counts.get('Baja', 0) + nivel_counts.get('Mínima', 0)
            
            # Usuarios en riesgo (Alta + Crítica)
            if 'Q_Usuarios' in df.columns:
                usuarios_riesgo = df[df['nivel_vulnerabilidad'].isin(['Alta', 'Crítica'])]['Q_Usuarios'].sum()
        
        # Índice promedio
        if 'criticidad_compuesta' in df.columns:
            indice_promedio = df['criticidad_compuesta'].mean()
        
        # Crear tarjetas actualizadas
        card1 = create_metric_card(
            "Críticos",
            str(criticos),
            "fas fa-exclamation-circle",
            color="danger",
            subtitle="Nivel máximo"
        )
        
        card2 = create_metric_card(
            "Alta",
            str(altos),
            "fas fa-exclamation-triangle",
            color="warning",
            subtitle="Vulnerabilidad"
        )
        
        card3 = create_metric_card(
            "Media",
            str(medios),
            "fas fa-minus-circle",
            color="info",
            subtitle="Vulnerabilidad"
        )
        
        card4 = create_metric_card(
            "Baja",
            str(bajos),
            "fas fa-check-circle",
            color="success",
            subtitle="Vulnerabilidad"
        )
        
        card5 = create_metric_card(
            "Usuarios en Riesgo",
            f"{usuarios_riesgo:,}",
            "fas fa-users",
            color="primary",
            subtitle="Alta/Crítica"
        )
        
        card6 = create_metric_card(
            "Índice Promedio",
            f"{indice_promedio:.2f}",
            "fas fa-tachometer-alt",
            color="secondary",
            subtitle="0-1 escala"
        )
        
        return options, card1, card2, card3, card4, card5, card6
        
    except Exception as e:
        print(f"Error en update_initial_data: {e}")
        error_card = create_metric_card("Error", "N/D", "fas fa-exclamation", color="danger")
        return [], error_card, error_card, error_card, error_card, error_card, error_card

@callback(
    Output("vuln-mapa", "figure"),
    [Input("vuln-sucursal-select", "value"),
     Input("vuln-nivel-select", "value"),
     Input("vuln-indice-slider", "value")]
)
def update_mapa_vulnerabilidad(sucursal, nivel, rango_indice):
    """Actualiza mapa de vulnerabilidad"""
    try:
        df = load_transformadores_completo()
        
        # Filtrar por sucursal
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        
        # Asegurar que existe nivel_vulnerabilidad
        if 'nivel_vulnerabilidad' not in df.columns:
            df['nivel_vulnerabilidad'] = create_vulnerability_levels(df)
        
        # Filtrar por nivel
        if nivel != "all":
            df = df[df['nivel_vulnerabilidad'] == nivel]
        
        # Filtrar por índice si existe
        if 'criticidad_compuesta' in df.columns:
            df = df[(df['criticidad_compuesta'] >= rango_indice[0]) & 
                   (df['criticidad_compuesta'] <= rango_indice[1])]
        
        # Verificar coordenadas
        if 'Coord_X' not in df.columns or 'Coord_Y' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(text="No hay coordenadas disponibles", showarrow=False)
            return fig
        
        df = df.dropna(subset=['Coord_X', 'Coord_Y'])
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos para mostrar", showarrow=False)
            return fig
        
        # Color por índice de vulnerabilidad o nivel
        if 'criticidad_compuesta' in df.columns:
            color_col = 'criticidad_compuesta'
            color_scale = 'RdYlGn_r'  # Invertido: rojo para alto, verde para bajo
            color_label = 'Índice de Vulnerabilidad'
        else:
            # Mapear niveles a números
            nivel_map = {'Mínima': 0, 'Baja': 1, 'Media': 2, 'Alta': 3, 'Crítica': 4}
            df['nivel_num'] = df['nivel_vulnerabilidad'].map(nivel_map).fillna(2)
            color_col = 'nivel_num'
            color_scale = [[0, 'green'], [0.25, 'lightgreen'], [0.5, 'yellow'], 
                          [0.75, 'orange'], [1, 'red']]
            color_label = 'Nivel de Vulnerabilidad'
        
        # Crear mapa
        fig = px.scatter_mapbox(
            df,
            lat='Coord_Y',
            lon='Coord_X',
            color=color_col,
            size='Q_Usuarios' if 'Q_Usuarios' in df.columns else None,
            hover_data=['Codigoct', 'Potencia', 'Q_Usuarios', 'Resultado', 'nivel_vulnerabilidad'],
            color_continuous_scale=color_scale,
            mapbox_style="open-street-map",
            title=f"Mapa de Vulnerabilidad - {sucursal if sucursal else 'Red Completa'}",
            zoom=10,
            height=500
        )
        
        fig.update_layout(
            coloraxis_colorbar=dict(title=color_label),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_mapa_vulnerabilidad: {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Error: {str(e)[:50]}...", showarrow=False)
        return fig

@callback(
    Output("vuln-distribucion", "figure"),
    [Input("vuln-sucursal-select", "value"),
     Input("vuln-nivel-select", "value")]
)
def update_distribucion(sucursal, nivel):
    """Actualiza gráfico de distribución por nivel"""
    try:
        df = load_transformadores_completo()
        
        # Filtrar por sucursal
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        
        # Asegurar nivel_vulnerabilidad
        if 'nivel_vulnerabilidad' not in df.columns:
            df['nivel_vulnerabilidad'] = create_vulnerability_levels(df)
        
        # Contar por nivel
        nivel_counts = df['nivel_vulnerabilidad'].value_counts()
        
        # Ordenar niveles y obtener colores
        orden = get_vulnerability_order()
        nivel_counts = nivel_counts.reindex(orden, fill_value=0)
        
        # Colores
        color_map = get_vulnerability_colors()
        colors = [color_map[nivel] for nivel in orden]
        
        # Crear pie chart
        fig = go.Figure(data=[
            go.Pie(
                labels=nivel_counts.index,
                values=nivel_counts.values,
                hole=0.4,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )
        ])
        
        # Agregar información en el centro
        total = nivel_counts.sum()
        fig.add_annotation(
            text=f"Total<br>{total:,}",
            x=0.5, y=0.5,
            font=dict(size=20),
            showarrow=False
        )
        
        fig.update_layout(
            title="Distribución por Nivel de Vulnerabilidad",
            showlegend=True,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_distribucion: {e}")
        return go.Figure()

@callback(
    Output("vuln-factores", "figure"),
    [Input("vuln-sucursal-select", "value"),
     Input("vuln-nivel-select", "value")]
)
def update_factores(sucursal, nivel):
    """Actualiza gráfico de factores contribuyentes"""
    try:
        df = load_transformadores_completo()
        
        # Filtrar
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        
        if nivel != "all" and 'nivel_vulnerabilidad' in df.columns:
            df = df[df['nivel_vulnerabilidad'] == nivel]
        
        # Calcular factores promedio
        factores = {}
        
        # Factor de calidad
        if 'Resultado' in df.columns:
            factores['Calidad de Servicio'] = (df['Resultado'] != 'Correcta').mean() * 100
        
        # Factor topológico
        if 'numero_saltos' in df.columns:
            factores['Distancia Topológica'] = (df['numero_saltos'] > 3).mean() * 100
        elif 'dist_a_centroide_km' in df.columns:
            factores['Distancia Geográfica'] = (df['dist_a_centroide_km'] > df['dist_a_centroide_km'].median()).mean() * 100
        
        # Factor de carga
        if 'usuarios_por_kva' in df.columns:
            factores['Densidad de Usuarios'] = (df['usuarios_por_kva'] > df['usuarios_por_kva'].quantile(0.75)).mean() * 100
        
        # Factor de potencia
        if 'Potencia' in df.columns:
            factores['Baja Capacidad'] = (df['Potencia'] < 100).mean() * 100
        
        # Factor de antigüedad (simulado)
        factores['Antigüedad Estimada'] = 35  # Valor ejemplo
        
        # Crear gráfico de barras
        if factores:
            fig = go.Figure([
                go.Bar(
                    x=list(factores.values()),
                    y=list(factores.keys()),
                    orientation='h',
                    marker_color='lightblue',
                    text=[f"{v:.1f}%" for v in factores.values()],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="Factores Contribuyentes a la Vulnerabilidad (%)",
                xaxis_title="Porcentaje de Transformadores Afectados",
                yaxis_title="",
                margin=dict(l=150, r=20, t=40, b=40)
            )
        else:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos de factores disponibles", showarrow=False)
        
        return fig
        
    except Exception as e:
        print(f"Error en update_factores: {e}")
        return go.Figure()

@callback(
    Output("vuln-vs-calidad", "figure"),
    [Input("vuln-sucursal-select", "value")]
)
def update_vuln_vs_calidad(sucursal):
    """Actualiza gráfico de vulnerabilidad vs calidad"""
    try:
        df = load_transformadores_completo()
        
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        
        # Asegurar columnas necesarias
        if 'nivel_vulnerabilidad' not in df.columns:
            df['nivel_vulnerabilidad'] = create_vulnerability_levels(df)
            
        if df.empty:
            return go.Figure()
        
        # Crear matriz de correlación
        confusion = pd.crosstab(
            df['nivel_vulnerabilidad'], 
            df['Resultado'],
            normalize='columns'
        ) * 100
        
        # Ordenar filas y columnas
        confusion = confusion.reindex(['Crítica', 'Alta', 'Media', 'Baja', 'Mínima'], fill_value=0)
        if 'Correcta' in confusion.columns:
            col_order = ['Correcta', 'Penalizada', 'Fallida']
            confusion = confusion[[col for col in col_order if col in confusion.columns]]
        
        # Crear heatmap
        fig = go.Figure(data=go.Heatmap(
            z=confusion.values,
            x=confusion.columns,
            y=confusion.index,
            colorscale='RdBu_r',
            text=confusion.values.round(1),
            texttemplate='%{text}%',
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Correlación: Nivel de Vulnerabilidad vs Estado de Calidad",
            xaxis_title="Estado de Calidad",
            yaxis_title="Nivel de Vulnerabilidad",
            margin=dict(l=100, r=20, t=40, b=40)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_vuln_vs_calidad: {e}")
        return go.Figure()

@callback(
    Output("vuln-top-criticos", "children"),
    [Input("vuln-sucursal-select", "value"),
     Input("vuln-nivel-select", "value")]
)
def update_top_criticos(sucursal, nivel):
    """Actualiza tabla de transformadores más críticos"""
    try:
        # Obtener top críticos
        df_top = get_top_critical_transformers(n=10)
        
        if df_top.empty:
            return html.Div("No hay datos disponibles", className="text-muted")
        
        # Filtrar por sucursal si aplica
        if sucursal and 'N_Sucursal' in df_top.columns:
            df_top = df_top[df_top['N_Sucursal'] == sucursal]
        
        # Renombrar columnas para mostrar
        column_map = {
            'Codigoct': 'Código',
            'N_Sucursal': 'Sucursal',
            'N_Localida': 'Localidad',
            'Alimentador': 'Alimentador',
            'Potencia': 'Potencia (kVA)',
            'Q_Usuarios': 'Usuarios',
            'Resultado': 'Estado',
            'criticidad_compuesta': 'Índice Crítico'
        }
        
        # Filtrar columnas existentes
        cols_to_show = [col for col in column_map.keys() if col in df_top.columns]
        df_show = df_top[cols_to_show].rename(columns=column_map)
        
        # Formatear valores numéricos
        if 'Índice Crítico' in df_show.columns:
            df_show['Índice Crítico'] = df_show['Índice Crítico'].round(3)
        
        # Crear tabla
        table = dash_table.DataTable(
            data=df_show.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_show.columns],
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'Estado', 'filter_query': '{Estado} = "Fallida"'},
                    'backgroundColor': '#ffcccc',
                    'color': 'black',
                },
                {
                    'if': {'column_id': 'Estado', 'filter_query': '{Estado} = "Penalizada"'},
                    'backgroundColor': '#fff3cd',
                    'color': 'black',
                },
                {
                    'if': {'column_id': 'Índice Crítico'},
                    'backgroundColor': '#e3f2fd',
                    'fontWeight': 'bold'
                }
            ],
            style_table={'overflowX': 'auto'},
            page_size=10
        )
        
        return html.Div([
            html.P(f"Mostrando {len(df_show)} transformadores más críticos", 
                  className="text-muted mb-3"),
            table
        ])
        
    except Exception as e:
        print(f"Error en update_top_criticos: {e}")
        return html.Div(f"Error: {str(e)}", className="text-danger")

@callback(
    Output("vuln-por-sucursal", "figure"),
    Input("vuln-nivel-select", "value")
)
def update_por_sucursal(nivel):
    """Actualiza análisis comparativo por sucursal"""
    try:
        df = load_transformadores_completo()
        
        if 'N_Sucursal' not in df.columns:
            return go.Figure()
        
        # Asegurar nivel_vulnerabilidad
        if 'nivel_vulnerabilidad' not in df.columns:
            df['nivel_vulnerabilidad'] = create_vulnerability_levels(df)
        
        # Calcular métricas por sucursal
        sucursal_stats = []
        
        for suc in df['N_Sucursal'].dropna().unique():
            df_suc = df[df['N_Sucursal'] == suc]
            
            # Calcular porcentaje de cada nivel
            total = len(df_suc)
            if total > 0:
                criticos = len(df_suc[df_suc['nivel_vulnerabilidad'] == 'Crítica']) / total * 100
                altos = len(df_suc[df_suc['nivel_vulnerabilidad'] == 'Alta']) / total * 100
                
                # Índice promedio si existe
                indice_prom = df_suc['criticidad_compuesta'].mean() if 'criticidad_compuesta' in df_suc.columns else 0.5
                
                sucursal_stats.append({
                    'Sucursal': str(suc),
                    'Críticos (%)': criticos,
                    'Altos (%)': altos,
                    'Críticos + Altos (%)': criticos + altos,
                    'Total': total,
                    'Índice Promedio': indice_prom
                })
        
        if not sucursal_stats:
            return go.Figure()
        
        df_stats = pd.DataFrame(sucursal_stats)
        df_stats = df_stats.sort_values('Críticos + Altos (%)', ascending=True)
        
        # Crear gráfico de barras apiladas
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Críticos',
            y=df_stats['Sucursal'],
            x=df_stats['Críticos (%)'],
            orientation='h',
            marker_color='red',
            text=df_stats['Críticos (%)'].round(1),
            textposition='inside'
        ))
        
        fig.add_trace(go.Bar(
            name='Altos',
            y=df_stats['Sucursal'],
            x=df_stats['Altos (%)'],
            orientation='h',
            marker_color='orange',
            text=df_stats['Altos (%)'].round(1),
            textposition='inside'
        ))
        
        # Agregar línea de índice promedio
        fig.add_trace(go.Scatter(
            name='Índice Promedio',
            y=df_stats['Sucursal'],
            x=df_stats['Índice Promedio'] * 100,  # Escalar a porcentaje
            mode='markers',
            marker=dict(size=10, color='blue', symbol='diamond'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Análisis de Vulnerabilidad por Sucursal",
            xaxis_title="Porcentaje de Transformadores",
            yaxis_title="",
            barmode='stack',
            height=600,
            margin=dict(l=100, r=20, t=40, b=40),
            legend=dict(x=0.7, y=1),
            yaxis2=dict(overlaying='y', side='right', visible=False)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_por_sucursal: {e}")
        return go.Figure()