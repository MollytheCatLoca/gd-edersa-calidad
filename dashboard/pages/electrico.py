"""
Página de Análisis Eléctrico
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Registrar página
dash.register_page(__name__, path='/electrico', name='Análisis Eléctrico', order=4)

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
            html.H2("Análisis Eléctrico de la Red", className="mb-1"),
            html.P("Impedancia, caída de tensión y modos de falla", className="text-muted")
        ])
    ], className="mb-4"),
    
    # Alerta informativa
    dbc.Row([
        dbc.Col([
            create_alert_card(
                "Análisis basado en el marco teórico de sistemas de distribución eléctrica y características de transformadores",
                color="info",
                icon="fas fa-bolt",
                dismissable=False
            )
        ])
    ], className="mb-4"),
    
    # Métricas generales eléctricas
    dbc.Row([
        dbc.Col([
            html.Div(id="impedancia-promedio-container", children=[
                create_metric_card(
                    "Impedancia Promedio",
                    "0.0 Ω",
                    "fas fa-wave-square",
                    color="primary",
                    subtitle="Red completa"
                )
            ])
        ], xs=6, md=3),
        dbc.Col([
            html.Div(id="caida-maxima-container", children=[
                create_metric_card(
                    "Caída Tensión Máx",
                    "0.0%",
                    "fas fa-arrow-down",
                    color="warning",
                    subtitle="Peor caso"
                )
            ])
        ], xs=6, md=3),
        dbc.Col([
            html.Div(id="trafos-sobrecargados-container", children=[
                create_metric_card(
                    "Trafos Sobrecargados",
                    "0",
                    "fas fa-thermometer-full",
                    color="danger",
                    subtitle="Riesgo térmico"
                )
            ])
        ], xs=6, md=3),
        dbc.Col([
            html.Div(id="trafos-riesgo-container", children=[
                create_metric_card(
                    "Trafos en Riesgo",
                    "0",
                    "fas fa-exclamation-triangle",
                    color="warning",
                    subtitle="Total problemas"
                )
            ])
        ], xs=6, md=3)
    ], className="mb-4"),
    
    # Selector de sucursal/alimentador
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Sucursal:", className="fw-bold"),
                            dcc.Dropdown(
                                id="electrico-sucursal-select",
                                options=[],
                                value=None,
                                placeholder="Todas las sucursales",
                                clearable=True
                            )
                        ], md=4),
                        dbc.Col([
                            html.Label("Alimentador:", className="fw-bold"),
                            dcc.Dropdown(
                                id="electrico-alimentador-select",
                                options=[],
                                value=None,
                                placeholder="Todos los alimentadores",
                                clearable=True,
                                disabled=True
                            )
                        ], md=4),
                        dbc.Col([
                            html.Label("Variable a analizar:", className="fw-bold"),
                            dcc.RadioItems(
                                id="electrico-variable-select",
                                options=[
                                    {"label": "Impedancia", "value": "impedancia"},
                                    {"label": "Caída de Tensión", "value": "caida"},
                                    {"label": "Modos de Falla", "value": "falla"}
                                ],
                                value="impedancia",
                                inline=True,
                                className="mt-2"
                            )
                        ], md=4)
                    ])
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Visualizaciones principales
    dbc.Row([
        # Mapa de calor o scatter por variable
        dbc.Col([
            create_summary_card(
                "Distribución Espacial",
                dcc.Loading(
                    dcc.Graph(
                        id="electrico-mapa-calor",
                        style={"height": "500px"},
                        config={'displayModeBar': True}
                    ),
                    type="circle"
                ),
                icon="fas fa-map-marked-alt"
            )
        ], md=8),
        
        # Panel de estadísticas
        dbc.Col([
            create_summary_card(
                "Estadísticas de la Zona",
                html.Div(id="electrico-stats-zona", className="p-3"),
                icon="fas fa-chart-pie"
            )
        ], md=4)
    ], className="mb-4"),
    
    # Análisis detallados
    dbc.Row([
        # Histograma de distribución
        dbc.Col([
            create_summary_card(
                "Distribución de Valores",
                dcc.Loading(
                    dcc.Graph(
                        id="electrico-histograma",
                        style={"height": "350px"}
                    ),
                    type="circle"
                ),
                icon="fas fa-chart-bar"
            )
        ], md=6),
        
        # Correlación con calidad
        dbc.Col([
            create_summary_card(
                "Correlación con Calidad",
                dcc.Loading(
                    dcc.Graph(
                        id="electrico-correlacion",
                        style={"height": "350px"}
                    ),
                    type="circle"
                ),
                icon="fas fa-link"
            )
        ], md=6)
    ], className="mb-4"),
    
    # Análisis de modos de falla
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Análisis de Modos de Falla",
                html.Div(id="electrico-modos-falla"),
                icon="fas fa-diagnoses"
            )
        ])
    ])
])

# Callbacks
@callback(
    [Output("electrico-sucursal-select", "options"),
     Output("impedancia-promedio-container", "children"),
     Output("caida-maxima-container", "children"),
     Output("trafos-sobrecargados-container", "children"),
     Output("trafos-riesgo-container", "children")],
    Input("electrico-variable-select", "value")
)
def update_initial_data(_):
    """Carga datos iniciales y actualiza métricas generales"""
    try:
        df = load_transformadores_completo()
        
        # Opciones de sucursales
        sucursales = []
        if 'N_Sucursal' in df.columns:
            # Filtrar valores válidos (no nulos)
            sucursales = df['N_Sucursal'].dropna().unique()
            # Convertir a string para poder ordenar
            sucursales = [str(suc) for suc in sucursales if suc is not None]
            sucursales = sorted(sucursales)
        
        options = [{"label": suc, "value": suc} for suc in sucursales]
        
        # Calcular métricas generales
        impedancia_prom = "N/D"
        caida_max = "N/D"
        trafos_sobrecargados = 0
        trafos_riesgo = 0
        
        # Impedancia promedio estimada
        if 'impedancia_estimada' in df.columns:
            impedancia_prom = f"{df['impedancia_estimada'].mean():.3f} Ω"
        
        # Caída de tensión máxima
        if 'caida_tension_estimada' in df.columns:
            caida_max = f"{df['caida_tension_estimada'].max():.1f}%"
        
        # Transformadores con problemas
        if 'modo_falla_probable' in df.columns:
            modos_falla = df['modo_falla_probable'].value_counts()
            if 'Térmico' in modos_falla:
                trafos_sobrecargados = int(modos_falla['Térmico'])
            trafos_riesgo = len(df[df['modo_falla_probable'] != 'Sin falla'])
        
        # Crear las tarjetas de métricas actualizadas
        card1 = create_metric_card(
            "Impedancia Promedio",
            impedancia_prom,
            "fas fa-wave-square",
            color="primary",
            subtitle="Red completa"
        )
        
        card2 = create_metric_card(
            "Caída Tensión Máx",
            caida_max,
            "fas fa-arrow-down",
            color="warning",
            subtitle="Peor caso"
        )
        
        card3 = create_metric_card(
            "Trafos Sobrecargados",
            str(trafos_sobrecargados),
            "fas fa-thermometer-full",
            color="danger",
            subtitle="Riesgo térmico"
        )
        
        card4 = create_metric_card(
            "Trafos en Riesgo",
            str(trafos_riesgo),
            "fas fa-exclamation-triangle",
            color="warning",
            subtitle="Total problemas"
        )
        
        return options, card1, card2, card3, card4
        
    except Exception as e:
        print(f"Error en update_initial_data: {e}")
        error_card = create_metric_card("Error", "N/D", "fas fa-exclamation", color="danger")
        return [], error_card, error_card, error_card, error_card

@callback(
    [Output("electrico-alimentador-select", "options"),
     Output("electrico-alimentador-select", "disabled"),
     Output("electrico-alimentador-select", "value")],
    Input("electrico-sucursal-select", "value")
)
def update_alimentador_options(sucursal):
    """Actualiza opciones de alimentadores según sucursal"""
    if not sucursal:
        return [], True, None
    
    try:
        df = load_transformadores_completo()
        df_suc = df[df['N_Sucursal'] == sucursal]
        
        alimentadores = df_suc['Alimentador'].unique() if 'Alimentador' in df_suc.columns else []
        options = [{"label": alim, "value": alim} for alim in sorted(alimentadores)]
        
        return options, False, None
        
    except Exception as e:
        print(f"Error en update_alimentador_options: {e}")
        return [], True, None

@callback(
    Output("electrico-mapa-calor", "figure"),
    [Input("electrico-variable-select", "value"),
     Input("electrico-sucursal-select", "value"),
     Input("electrico-alimentador-select", "value")]
)
def update_mapa_calor(variable, sucursal, alimentador):
    """Actualiza mapa de calor según variable seleccionada"""
    try:
        df = load_transformadores_completo()
        
        # Filtrar por sucursal/alimentador
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        if alimentador:
            df = df[df['Alimentador'] == alimentador]
        
        # Verificar coordenadas
        if 'Coord_X' not in df.columns or 'Coord_Y' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(text="No hay coordenadas disponibles", showarrow=False)
            return fig
        
        # Filtrar solo con coordenadas válidas
        df = df.dropna(subset=['Coord_X', 'Coord_Y'])
        
        # Verificar que tengamos datos después del filtrado
        if len(df) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos con coordenadas válidas para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos para mostrar", showarrow=False)
            return fig
        
        # Seleccionar variable a visualizar
        if variable == "impedancia":
            if 'impedancia_estimada' not in df.columns:
                # Estimar impedancia simple
                df['impedancia_estimada'] = 0.01 + 0.1 / (df['Potencia'] / 100)
            
            color_col = 'impedancia_estimada'
            title = "Impedancia Estimada de Transformadores"
            color_label = "Impedancia (Ω)"
            colorscale = "Viridis"
            
        elif variable == "caida":
            if 'caida_tension_estimada' not in df.columns:
                # Estimar caída de tensión
                if 'dist_a_centroide_km' in df.columns:
                    df['caida_tension_estimada'] = df['dist_a_centroide_km'] * 2
                else:
                    # Asignar valor por defecto a todos los registros
                    df['caida_tension_estimada'] = 5.0
            
            color_col = 'caida_tension_estimada'
            title = "Caída de Tensión Estimada"
            color_label = "Caída (%)"
            colorscale = "Reds"
            
        else:  # modos de falla
            if 'modo_falla_probable' not in df.columns:
                # Asignar modo de falla basado en resultado
                df['modo_falla_probable'] = df['Resultado'].map({
                    'Correcta': 'Sin falla',
                    'Penalizada': 'Dieléctrico',
                    'Fallida': 'Térmico'
                })
            
            # Mapear a numérico para visualización
            falla_map = {'Sin falla': 0, 'Dieléctrico': 1, 'Térmico': 2}
            df['falla_num'] = df['modo_falla_probable'].map(falla_map)
            
            color_col = 'falla_num'
            title = "Modos de Falla Probables"
            color_label = "Modo de Falla"
            colorscale = [[0, 'green'], [0.5, 'orange'], [1, 'red']]
        
        # Crear scatter plot
        fig = px.scatter_mapbox(
            df,
            lat='Coord_Y',
            lon='Coord_X',
            color=color_col,
            size='Potencia',
            hover_data=['Codigoct', 'Potencia', 'Q_Usuarios', 'Resultado'],
            color_continuous_scale=colorscale,
            mapbox_style="open-street-map",
            title=title,
            zoom=10,
            height=500
        )
        
        fig.update_layout(
            coloraxis_colorbar=dict(title=color_label),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error en update_mapa_calor: {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Error: {str(e)[:50]}...", showarrow=False)
        return fig

@callback(
    Output("electrico-stats-zona", "children"),
    [Input("electrico-variable-select", "value"),
     Input("electrico-sucursal-select", "value"),
     Input("electrico-alimentador-select", "value")]
)
def update_stats_zona(variable, sucursal, alimentador):
    """Actualiza estadísticas de la zona seleccionada"""
    try:
        df = load_transformadores_completo()
        
        # Filtrar
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        if alimentador:
            df = df[df['Alimentador'] == alimentador]
        
        stats = []
        
        # Título de la zona
        zona = alimentador if alimentador else (sucursal if sucursal else "Red Completa")
        stats.append(html.H5(zona, className="mb-3"))
        stats.append(html.Hr())
        
        # Estadísticas básicas
        stats.append(html.P([
            html.Strong("Transformadores: "),
            f"{len(df):,}"
        ]))
        
        stats.append(html.P([
            html.Strong("Capacidad total: "),
            f"{df['Potencia'].sum()/1000:.1f} MVA"
        ]))
        
        stats.append(html.P([
            html.Strong("Usuarios: "),
            f"{df['Q_Usuarios'].sum():,}"
        ]))
        
        # Estadísticas específicas por variable
        if variable == "impedancia" and 'impedancia_estimada' in df.columns:
            stats.append(html.Hr())
            stats.append(html.H6("Impedancia"))
            stats.append(html.P([
                html.Strong("Media: "),
                f"{df['impedancia_estimada'].mean():.3f} Ω"
            ]))
            stats.append(html.P([
                html.Strong("Máxima: "),
                f"{df['impedancia_estimada'].max():.3f} Ω"
            ]))
            stats.append(html.P([
                html.Strong("Mínima: "),
                f"{df['impedancia_estimada'].min():.3f} Ω"
            ]))
            
        elif variable == "caida" and 'caida_tension_estimada' in df.columns:
            stats.append(html.Hr())
            stats.append(html.H6("Caída de Tensión"))
            stats.append(html.P([
                html.Strong("Media: "),
                f"{df['caida_tension_estimada'].mean():.1f}%"
            ]))
            stats.append(html.P([
                html.Strong("Máxima: "),
                f"{df['caida_tension_estimada'].max():.1f}%"
            ]))
            # Contar cuántos exceden 5%
            exceden = len(df[df['caida_tension_estimada'] > 5])
            stats.append(html.P([
                html.Strong("Exceden 5%: "),
                f"{exceden} ({exceden/len(df)*100:.1f}%)"
            ]))
            
        elif variable == "falla" and 'modo_falla_probable' in df.columns:
            stats.append(html.Hr())
            stats.append(html.H6("Modos de Falla"))
            fallas = df['modo_falla_probable'].value_counts()
            for modo, count in fallas.items():
                color = "text-success" if modo == "Sin falla" else ("text-warning" if modo == "Dieléctrico" else "text-danger")
                stats.append(html.P([
                    html.Strong(f"{modo}: ", className=color),
                    f"{count} ({count/len(df)*100:.1f}%)"
                ]))
        
        return html.Div(stats)
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="text-danger")

@callback(
    Output("electrico-histograma", "figure"),
    [Input("electrico-variable-select", "value"),
     Input("electrico-sucursal-select", "value"),
     Input("electrico-alimentador-select", "value")]
)
def update_histograma(variable, sucursal, alimentador):
    """Actualiza histograma de distribución"""
    try:
        df = load_transformadores_completo()
        
        # Filtrar
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        if alimentador:
            df = df[df['Alimentador'] == alimentador]
        
        if variable == "impedancia":
            if 'impedancia_estimada' not in df.columns:
                df['impedancia_estimada'] = 0.01 + 0.1 / (df['Potencia'] / 100)
            
            fig = px.histogram(
                df,
                x='impedancia_estimada',
                nbins=30,
                title="Distribución de Impedancia",
                labels={'impedancia_estimada': 'Impedancia (Ω)', 'count': 'Cantidad'}
            )
            
        elif variable == "caida":
            if 'caida_tension_estimada' not in df.columns:
                df['caida_tension_estimada'] = df['dist_a_centroide_km'] * 2 if 'dist_a_centroide_km' in df.columns else 5
            
            fig = px.histogram(
                df,
                x='caida_tension_estimada',
                nbins=30,
                title="Distribución de Caída de Tensión",
                labels={'caida_tension_estimada': 'Caída de Tensión (%)', 'count': 'Cantidad'}
            )
            
            # Agregar línea de límite 5%
            fig.add_vline(x=5, line_dash="dash", line_color="red", 
                         annotation_text="Límite 5%", annotation_position="top right")
            
        else:  # modos de falla
            if 'modo_falla_probable' not in df.columns:
                df['modo_falla_probable'] = df['Resultado'].map({
                    'Correcta': 'Sin falla',
                    'Penalizada': 'Dieléctrico',
                    'Fallida': 'Térmico'
                })
            
            falla_counts = df['modo_falla_probable'].value_counts()
            
            fig = go.Figure([
                go.Bar(
                    x=falla_counts.index,
                    y=falla_counts.values,
                    marker_color=['green', 'orange', 'red'][:len(falla_counts)],
                    text=falla_counts.values,
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="Distribución de Modos de Falla",
                xaxis_title="Modo de Falla",
                yaxis_title="Cantidad de Transformadores"
            )
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=40),
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Error: {str(e)}", showarrow=False)
        return fig

@callback(
    Output("electrico-correlacion", "figure"),
    [Input("electrico-variable-select", "value"),
     Input("electrico-sucursal-select", "value"),
     Input("electrico-alimentador-select", "value")]
)
def update_correlacion(variable, sucursal, alimentador):
    """Actualiza gráfico de correlación con calidad"""
    try:
        df = load_transformadores_completo()
        
        # Filtrar
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        if alimentador:
            df = df[df['Alimentador'] == alimentador]
        
        # Mapear calidad a numérico
        calidad_map = {'Correcta': 0, 'Penalizada': 1, 'Fallida': 2}
        df['calidad_num'] = df['Resultado'].map(calidad_map)
        
        if variable == "impedancia":
            if 'impedancia_estimada' not in df.columns:
                df['impedancia_estimada'] = 0.01 + 0.1 / (df['Potencia'] / 100)
            
            # Box plot por calidad
            fig = px.box(
                df,
                x='Resultado',
                y='impedancia_estimada',
                color='Resultado',
                color_discrete_map={'Correcta': 'green', 'Penalizada': 'orange', 'Fallida': 'red'},
                title="Impedancia vs Estado de Calidad",
                labels={'impedancia_estimada': 'Impedancia (Ω)'}
            )
            
        elif variable == "caida":
            if 'caida_tension_estimada' not in df.columns:
                df['caida_tension_estimada'] = df['dist_a_centroide_km'] * 2 if 'dist_a_centroide_km' in df.columns else 5
            
            fig = px.box(
                df,
                x='Resultado',
                y='caida_tension_estimada',
                color='Resultado',
                color_discrete_map={'Correcta': 'green', 'Penalizada': 'orange', 'Fallida': 'red'},
                title="Caída de Tensión vs Estado de Calidad",
                labels={'caida_tension_estimada': 'Caída de Tensión (%)'}
            )
            
        else:  # modos de falla
            # Matriz de confusión modo de falla vs calidad
            if 'modo_falla_probable' not in df.columns:
                df['modo_falla_probable'] = df['Resultado'].map({
                    'Correcta': 'Sin falla',
                    'Penalizada': 'Dieléctrico',
                    'Fallida': 'Térmico'
                })
            
            confusion = pd.crosstab(df['modo_falla_probable'], df['Resultado'])
            
            fig = px.imshow(
                confusion,
                labels=dict(x="Estado de Calidad", y="Modo de Falla", color="Cantidad"),
                title="Correlación Modo de Falla vs Calidad",
                color_continuous_scale="Blues",
                text_auto=True
            )
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=40),
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Error: {str(e)}", showarrow=False)
        return fig

@callback(
    Output("electrico-modos-falla", "children"),
    [Input("electrico-variable-select", "value"),
     Input("electrico-sucursal-select", "value"),
     Input("electrico-alimentador-select", "value")]
)
def update_modos_falla(variable, sucursal, alimentador):
    """Actualiza panel de análisis de modos de falla"""
    if variable != "falla":
        return html.Div([
            html.P("Seleccione 'Modos de Falla' para ver este análisis", className="text-muted")
        ])
    
    try:
        df = load_transformadores_completo()
        
        # Filtrar
        if sucursal:
            df = df[df['N_Sucursal'] == sucursal]
        if alimentador:
            df = df[df['Alimentador'] == alimentador]
        
        # Análisis de modos de falla
        content = []
        
        # Descripción de modos
        content.append(html.Div([
            html.H5("Modos de Falla en Transformadores", className="mb-3"),
            html.Hr(),
            
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.H6("🔥 Modo Térmico", className="alert-heading"),
                        html.P([
                            "Sobrecalentamiento por sobrecarga o fallas internas. ",
                            "Indicadores: Alta temperatura, degradación del aceite, gases combustibles."
                        ], className="mb-0")
                    ], color="danger")
                ], md=6),
                
                dbc.Col([
                    dbc.Alert([
                        html.H6("⚡ Modo Dieléctrico", className="alert-heading"),
                        html.P([
                            "Fallas de aislamiento por sobretensiones o envejecimiento. ",
                            "Indicadores: Descargas parciales, humedad en aceite, bajo rigidez dieléctrica."
                        ], className="mb-0")
                    ], color="warning")
                ], md=6)
            ], className="mb-4"),
            
            # Análisis por potencia
            html.H6("Análisis por Potencia de Transformador"),
            html.P("Distribución de modos de falla según capacidad:", className="text-muted")
        ]))
        
        # Tabla de análisis por rango de potencia
        if 'modo_falla_probable' not in df.columns:
            df['modo_falla_probable'] = df['Resultado'].map({
                'Correcta': 'Sin falla',
                'Penalizada': 'Dieléctrico',
                'Fallida': 'Térmico'
            })
        
        # Crear rangos de potencia
        df['rango_potencia'] = pd.cut(
            df['Potencia'],
            bins=[0, 100, 315, 630, 1000, 10000],
            labels=['<100 kVA', '100-315 kVA', '315-630 kVA', '630-1000 kVA', '>1000 kVA']
        )
        
        # Tabla resumen
        tabla_data = []
        for rango in df['rango_potencia'].cat.categories:
            df_rango = df[df['rango_potencia'] == rango]
            if len(df_rango) > 0:
                fallas = df_rango['modo_falla_probable'].value_counts()
                tabla_data.append({
                    'Rango': rango,
                    'Total': len(df_rango),
                    'Sin falla': fallas.get('Sin falla', 0),
                    'Térmico': fallas.get('Térmico', 0),
                    'Dieléctrico': fallas.get('Dieléctrico', 0),
                    '% Falla': f"{(1 - fallas.get('Sin falla', 0)/len(df_rango))*100:.1f}%"
                })
        
        if tabla_data:
            df_tabla = pd.DataFrame(tabla_data)
            
            tabla = dbc.Table.from_dataframe(
                df_tabla,
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                className="mt-3"
            )
            
            content.append(tabla)
        
        # Recomendaciones
        content.append(html.Div([
            html.Hr(),
            html.H6("Recomendaciones de Mantenimiento"),
            html.Ul([
                html.Li("Transformadores >630 kVA con falla térmica: Verificar carga y sistema de refrigeración"),
                html.Li("Transformadores <315 kVA con falla dieléctrica: Revisar protecciones contra sobretensiones"),
                html.Li("Implementar monitoreo continuo en transformadores críticos"),
                html.Li("Priorizar mantenimiento preventivo en zonas con alta tasa de fallas")
            ])
        ], className="mt-4"))
        
        return html.Div(content)
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="text-danger")