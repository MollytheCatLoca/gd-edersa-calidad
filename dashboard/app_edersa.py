"""
Dashboard EDERSA - Análisis de Calidad de Transformadores
Fase 1: Comprensión y Visualización de Datos

Este dashboard permite:
- Explorar el inventario de transformadores
- Analizar problemas de calidad por zona
- Identificar oportunidades para Generación Distribuida
- Visualizar métricas y estadísticas clave

Autor: Claude
Fecha: Julio 2025
"""

import dash
from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Configuración de paths
DB_PATH = Path(__file__).parent.parent / "data" / "database" / "edersa_quality.db"
MAPBOX_TOKEN = None  # Agregar token si se tiene

# Inicializar aplicación
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="EDERSA - Análisis de Calidad"
)

# Estilos personalizados
CARD_STYLE = {
    "box-shadow": "0 4px 6px 0 rgba(0, 0, 0, 0.1)",
    "margin-bottom": "1rem"
}

METRIC_CARD_STYLE = {
    "text-align": "center",
    "padding": "1rem",
    "border-radius": "0.5rem",
    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "color": "white"
}


def get_db_connection():
    """Obtiene conexión a la base de datos."""
    return sqlite3.connect(DB_PATH)


def load_summary_metrics():
    """Carga métricas resumen desde la base de datos."""
    conn = get_db_connection()
    query = """
    SELECT * FROM metricas_resumen 
    ORDER BY fecha_actualizacion DESC 
    LIMIT 1
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) > 0:
        return df.iloc[0].to_dict()
    return {}

def create_metric_card(title, value, subtitle=None, color="primary"):
    """Crea una tarjeta de métrica."""
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-2"),
            html.H3(value, className="mb-1"),
            html.Small(subtitle) if subtitle else None
        ])
    ], style=METRIC_CARD_STYLE)


def create_navbar():
    """Crea la barra de navegación."""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.NavbarBrand("EDERSA - Análisis de Calidad de Transformadores", className="fs-4")
                ], className="d-flex align-items-center")
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Nav([
                        dbc.NavItem(dbc.NavLink("Dashboard", active=True, href="/")),
                        dbc.NavItem(dbc.NavLink("Análisis", href="/analysis")),
                        dbc.NavItem(dbc.NavLink("Recomendaciones GD", href="/gd")),
                        dbc.NavItem(dbc.NavLink("Reportes", href="/reports"))
                    ], navbar=True)
                ])
            ])
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-4"
    )


# Layout principal
app.layout = html.Div([
    # Navbar
    create_navbar(),
    
    # Contenido principal
    dbc.Container([
        # URL para routing
        dcc.Location(id='url', refresh=False),
        
        # Contenido dinámico
        html.Div(id='page-content')
    ], fluid=True)
])


def create_overview_page():
    """Crea la página de resumen general."""
    metrics = load_summary_metrics()
    
    return html.Div([
        # Título
        dbc.Row([
            dbc.Col([
                html.H2("Panel de Control - Resumen General"),
                html.P("Análisis de calidad de transformadores y oportunidades de Generación Distribuida", 
                       className="text-muted")
            ])
        ], className="mb-4"),
        
        # Métricas principales
        dbc.Row([
            dbc.Col([
                create_metric_card(
                    "Total Transformadores",
                    f"{metrics.get('total_transformadores', 0):,}",
                    f"{metrics.get('total_circuitos', 0):,} circuitos"
                )
            ], md=3),
            dbc.Col([
                create_metric_card(
                    "Usuarios Totales",
                    f"{int(metrics.get('total_usuarios', 0)):,}",
                    "usuarios conectados"
                )
            ], md=3),
            dbc.Col([
                create_metric_card(
                    "Capacidad Total",
                    f"{metrics.get('capacidad_total_mva', 0):.1f} MVA",
                    "capacidad instalada"
                )
            ], md=3),
            dbc.Col([
                create_metric_card(
                    "Transformadores Críticos",
                    f"{metrics.get('transformadores_criticos', 0):,}",
                    "requieren atención",
                    color="danger"
                )
            ], md=3)
        ], className="mb-4"),
        
        # Gráficos principales
        dbc.Row([
            # Distribución de calidad
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Distribución de Calidad"),
                    dbc.CardBody([
                        dcc.Graph(id='quality-distribution-chart')
                    ])
                ], style=CARD_STYLE)
            ], md=6),
            
            # Criticidad por zona
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Criticidad por Zona"),
                    dbc.CardBody([
                        dcc.Graph(id='criticality-zones-chart')
                    ])
                ], style=CARD_STYLE)
            ], md=6)
        ], className="mb-4"),
        
        # Mapa geográfico y tabla de sucursales críticas
        dbc.Row([
            # Mapa
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Distribución Geográfica de Transformadores"),
                    dbc.CardBody([
                        dcc.Graph(id='transformers-map', style={'height': '500px'})
                    ])
                ], style=CARD_STYLE)
            ], md=8),
            
            # Tabla de sucursales críticas
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Sucursales Críticas"),
                    dbc.CardBody([
                        html.Div(id='critical-branches-table')
                    ])
                ], style=CARD_STYLE)
            ], md=4)
        ]),
        
        # Oportunidades GD
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Resumen de Oportunidades GD"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H5(f"{metrics.get('oportunidades_gd_alta_prioridad', 0):,}"),
                                html.P("Oportunidades Alta Prioridad", className="text-muted")
                            ], md=3),
                            dbc.Col([
                                html.H5(f"{metrics.get('capacidad_gd_potencial_mw', 0):.1f} MW"),
                                html.P("Capacidad GD Potencial", className="text-muted")
                            ], md=3),
                            dbc.Col([
                                html.H5(f"${metrics.get('inversion_estimada_musd', 0):.1f}M"),
                                html.P("Inversión Estimada (USD)", className="text-muted")
                            ], md=3),
                            dbc.Col([
                                html.H5(f"{metrics.get('usuarios_beneficiados_gd', 0):,}"),
                                html.P("Usuarios Beneficiados", className="text-muted")
                            ], md=3)
                        ])
                    ])
                ], style=CARD_STYLE)
            ])
        ], className="mt-4")
    ])


# Callbacks para gráficos
@app.callback(
    Output('quality-distribution-chart', 'figure'),
    Input('url', 'pathname')
)
def update_quality_distribution(pathname):
    """Actualiza gráfico de distribución de calidad."""
    conn = get_db_connection()
    
    query = """
    SELECT resultado, COUNT(*) as cantidad
    FROM transformadores
    WHERE resultado IS NOT NULL
    GROUP BY resultado
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Colores personalizados
    colors = {
        'Correcta': '#00cc44',
        'Penalizada': '#ff9900',
        'Fallida': '#cc0000'
    }
    
    fig = px.pie(
        df, 
        values='cantidad', 
        names='resultado',
        color='resultado',
        color_discrete_map=colors,
        hole=0.4
    )
    
    fig.update_layout(
        showlegend=True,
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    return fig


@app.callback(
    Output('criticality-zones-chart', 'figure'),
    Input('url', 'pathname')
)
def update_criticality_zones(pathname):
    """Actualiza gráfico de criticidad por zona."""
    conn = get_db_connection()
    
    query = """
    SELECT tipo_zona, AVG(criticidad_compuesta) as criticidad_promedio
    FROM transformadores
    WHERE tipo_zona IS NOT NULL
    GROUP BY tipo_zona
    ORDER BY criticidad_promedio DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    fig = px.bar(
        df,
        x='tipo_zona',
        y='criticidad_promedio',
        color='criticidad_promedio',
        color_continuous_scale='Reds',
        labels={'criticidad_promedio': 'Criticidad Promedio', 'tipo_zona': 'Tipo de Zona'}
    )
    
    fig.update_layout(
        showlegend=False,
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    return fig


@app.callback(
    Output('transformers-map', 'figure'),
    Input('url', 'pathname')
)
def update_transformers_map(pathname):
    """Actualiza mapa de transformadores."""
    conn = get_db_connection()
    
    query = """
    SELECT codigoct, coord_x, coord_y, n_sucursal, n_localida,
           potencia, q_usuarios, resultado, criticidad_compuesta
    FROM transformadores
    WHERE coord_x IS NOT NULL AND coord_y IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Colores según resultado
    color_map = {
        'Correcta': 'green',
        'Penalizada': 'orange',
        'Fallida': 'red'
    }
    df['color'] = df['resultado'].map(color_map).fillna('gray')
    
    # Crear mapa
    fig = go.Figure()
    
    # Agregar puntos
    fig.add_trace(go.Scattermapbox(
        lat=df['coord_y'],
        lon=df['coord_x'],
        mode='markers',
        marker=dict(
            size=8,
            color=df['color'],
            opacity=0.8
        ),
        text=df.apply(lambda row: f"""
        <b>{row['codigoct']}</b><br>
        Sucursal: {row['n_sucursal']}<br>
        Localidad: {row['n_localida']}<br>
        Potencia: {row['potencia']} kVA<br>
        Usuarios: {row['q_usuarios']}<br>
        Estado: {row['resultado']}<br>
        Criticidad: {row['criticidad_compuesta']:.2f}
        """, axis=1),
        hovertemplate='%{text}<extra></extra>'
    ))
    
    # Configurar layout del mapa
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(
                lat=df['coord_y'].mean(),
                lon=df['coord_x'].mean()
            ),
            zoom=6
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500
    )
    
    return fig


@app.callback(
    Output('critical-branches-table', 'children'),
    Input('url', 'pathname')
)
def update_critical_branches_table(pathname):
    """Actualiza tabla de sucursales críticas."""
    conn = get_db_connection()
    
    query = """
    SELECT n_sucursal, criticidad_promedio, num_transformadores, usuarios_totales
    FROM sucursales
    WHERE criticidad_promedio > 0.3
    ORDER BY criticidad_promedio DESC
    LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) == 0:
        return html.P("No hay sucursales críticas", className="text-muted")
    
    # Crear tabla
    return dbc.Table.from_dataframe(
        df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        size="sm"
    )


# Callback para routing
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """Maneja el routing de páginas."""
    if pathname == '/' or pathname is None:
        return create_overview_page()
    elif pathname == '/analysis':
        return create_analysis_page()
    elif pathname == '/gd':
        return create_gd_recommendations_page()
    elif pathname == '/reports':
        return create_reports_page()
    else:
        return html.Div([
            html.H3('404: Página no encontrada'),
            html.P(f'La ruta {pathname} no existe.'),
            dbc.Button("Volver al inicio", href="/", color="primary")
        ])


def create_analysis_page():
    """Crea la página de análisis detallado."""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H2("Análisis Detallado"),
                html.P("Explora los datos de transformadores con filtros avanzados")
            ])
        ], className="mb-4"),
        
        # Filtros
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Filtros"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Sucursal"),
                                dcc.Dropdown(
                                    id='filter-sucursal',
                                    options=[],
                                    multi=True,
                                    placeholder="Todas las sucursales"
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Estado"),
                                dcc.Dropdown(
                                    id='filter-estado',
                                    options=[
                                        {'label': 'Correcta', 'value': 'Correcta'},
                                        {'label': 'Penalizada', 'value': 'Penalizada'},
                                        {'label': 'Fallida', 'value': 'Fallida'}
                                    ],
                                    multi=True,
                                    placeholder="Todos los estados"
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Criticidad Mínima"),
                                dcc.Slider(
                                    id='filter-criticidad',
                                    min=0,
                                    max=1,
                                    step=0.1,
                                    value=0,
                                    marks={i/10: str(i/10) for i in range(11)}
                                )
                            ], md=4)
                        ])
                    ])
                ], style=CARD_STYLE)
            ])
        ], className="mb-4"),
        
        # Resultados
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Transformadores Filtrados"),
                    dbc.CardBody([
                        html.Div(id='filtered-transformers-table')
                    ])
                ], style=CARD_STYLE)
            ])
        ])
    ])


def create_gd_recommendations_page():
    """Crea la página de recomendaciones GD."""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H2("Recomendaciones de Generación Distribuida"),
                html.P("Oportunidades identificadas para mejorar la calidad del servicio")
            ])
        ], className="mb-4"),
        
        # Gráfico de oportunidades por tipo
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Distribución de Tipos de GD Recomendados"),
                    dbc.CardBody([
                        dcc.Graph(id='gd-types-chart')
                    ])
                ], style=CARD_STYLE)
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Inversión por Tipo de GD"),
                    dbc.CardBody([
                        dcc.Graph(id='gd-investment-chart')
                    ])
                ], style=CARD_STYLE)
            ], md=6)
        ], className="mb-4"),
        
        # Tabla de recomendaciones
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top 20 Oportunidades de GD"),
                    dbc.CardBody([
                        html.Div(id='gd-recommendations-table')
                    ])
                ], style=CARD_STYLE)
            ])
        ])
    ])


def create_reports_page():
    """Crea la página de reportes."""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H2("Reportes y Documentación"),
                html.P("Accede a reportes generados y documentación del proyecto")
            ])
        ], className="mb-4"),
        
        # Lista de reportes disponibles
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Reportes Disponibles"),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.H5("Reporte de Validación"),
                                html.P("Análisis inicial de calidad de datos"),
                                dbc.Button("Descargar", color="primary", size="sm")
                            ]),
                            dbc.ListGroupItem([
                                html.H5("Reporte de Limpieza"),
                                html.P("Procesamiento y enriquecimiento de datos"),
                                dbc.Button("Descargar", color="primary", size="sm")
                            ]),
                            dbc.ListGroupItem([
                                html.H5("Reporte de Criticidad"),
                                html.P("Análisis detallado de zonas críticas"),
                                dbc.Button("Descargar", color="primary", size="sm")
                            ]),
                            dbc.ListGroupItem([
                                html.H5("Reporte de Recomendaciones GD"),
                                html.P("Oportunidades de generación distribuida"),
                                dbc.Button("Descargar", color="primary", size="sm")
                            ])
                        ])
                    ])
                ], style=CARD_STYLE)
            ])
        ])
    ])


# Callbacks adicionales para páginas secundarias
@app.callback(
    Output('filter-sucursal', 'options'),
    Input('url', 'pathname')
)
def update_sucursal_options(pathname):
    """Actualiza opciones de filtro de sucursal."""
    if pathname != '/analysis':
        return []
    
    conn = get_db_connection()
    query = "SELECT DISTINCT n_sucursal FROM transformadores WHERE n_sucursal IS NOT NULL ORDER BY n_sucursal"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return [{'label': s, 'value': s} for s in df['n_sucursal']]


@app.callback(
    Output('gd-types-chart', 'figure'),
    Input('url', 'pathname')
)
def update_gd_types_chart(pathname):
    """Actualiza gráfico de tipos de GD."""
    if pathname != '/gd':
        return {}
    
    conn = get_db_connection()
    query = """
    SELECT gd_type_recommended as tipo, COUNT(*) as cantidad
    FROM transformadores
    WHERE gd_type_recommended IS NOT NULL
    GROUP BY gd_type_recommended
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    fig = px.bar(
        df,
        x='tipo',
        y='cantidad',
        color='tipo',
        labels={'cantidad': 'Cantidad de Transformadores', 'tipo': 'Tipo de GD'}
    )
    
    fig.update_layout(
        showlegend=False,
        height=300
    )
    
    return fig


@app.callback(
    Output('gd-recommendations-table', 'children'),
    Input('url', 'pathname')
)
def update_gd_recommendations_table(pathname):
    """Actualiza tabla de recomendaciones GD."""
    if pathname != '/gd':
        return []
    
    conn = get_db_connection()
    query = """
    SELECT 
        r.codigoct as "Código",
        t.n_sucursal as "Sucursal",
        t.n_localida as "Localidad",
        r.score as "Score GD",
        r.prioridad as "Prioridad",
        r.capacidad_actual_kva as "Capacidad (kVA)",
        r.capacidad_gd_kw as "GD Recom. (kW)",
        r.tipo_gd_recomendado as "Tipo GD"
    FROM recomendaciones_gd r
    JOIN transformadores t ON r.codigoct = t.codigoct
    ORDER BY r.score DESC
    LIMIT 20
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Formatear números
    df['Score GD'] = df['Score GD'].round(3)
    df['GD Recom. (kW)'] = df['GD Recom. (kW)'].round(1)
    
    return dbc.Table.from_dataframe(
        df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        size="sm"
    )


if __name__ == '__main__':
    print(f"Base de datos: {DB_PATH}")
    print(f"Existe: {DB_PATH.exists()}")
    
    app.run(debug=True, host='0.0.0.0', port=8050)
