"""
Página de Análisis de Inventario y Calidad
"""

import dash
from dash import html, dcc, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Registrar página
dash.register_page(__name__, path='/inventario', name='Inventario y Calidad', order=2)

# Importar utilidades
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.components.metrics_cards import (
    create_metric_card, create_summary_card, create_progress_card
)
from dashboard.utils.data_loader import (
    load_transformadores_completo, get_summary_metrics,
    filter_transformadores
)

# Layout de la página
layout = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Análisis de Inventario y Calidad", className="mb-1"),
            html.P("Exploración detallada del inventario de transformadores", className="text-muted")
        ])
    ], className="mb-4"),
    
    # Filtros locales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Filtrar por Sucursal:", className="fw-bold"),
                            dcc.Dropdown(
                                id="inventario-sucursal-filter",
                                options=[{"label": "Todas", "value": "all"}],
                                value="all",
                                clearable=False
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Filtrar por Estado:", className="fw-bold"),
                            dcc.Dropdown(
                                id="inventario-estado-filter",
                                options=[
                                    {"label": "Todos", "value": "all"},
                                    {"label": "Correcta", "value": "Correcta"},
                                    {"label": "Penalizada", "value": "Penalizada"},
                                    {"label": "Fallida", "value": "Fallida"}
                                ],
                                value="all",
                                clearable=False
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Filtrar por Tamaño:", className="fw-bold"),
                            dcc.Dropdown(
                                id="inventario-size-filter",
                                options=[
                                    {"label": "Todos", "value": "all"},
                                    {"label": "Micro (<25 kVA)", "value": "Micro"},
                                    {"label": "Pequeño (25-100 kVA)", "value": "Pequeño"},
                                    {"label": "Mediano (100-315 kVA)", "value": "Mediano"},
                                    {"label": "Grande (>315 kVA)", "value": "Grande"}
                                ],
                                value="all",
                                clearable=False
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Buscar:", className="fw-bold"),
                            dbc.Input(
                                id="inventario-search",
                                placeholder="Código o localidad...",
                                type="text",
                                debounce=True
                            )
                        ], md=3)
                    ])
                ])
            ], className="mb-4")
        ])
    ]),
    
    # Métricas resumen filtradas
    dbc.Row([
        dbc.Col(html.Div(id="inventario-metrics"), width=12)
    ], className="mb-4"),
    
    # Gráficos de distribución
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Distribución por Sucursal",
                dcc.Loading(
                    dcc.Graph(id="inventario-bar-sucursal", style={"height": "400px"}),
                    type="circle"
                ),
                icon="fas fa-building"
            )
        ], md=6),
        dbc.Col([
            create_summary_card(
                "Distribución por Capacidad",
                dcc.Loading(
                    dcc.Graph(id="inventario-pie-capacidad", style={"height": "400px"}),
                    type="circle"
                ),
                icon="fas fa-bolt"
            )
        ], md=6)
    ], className="mb-4"),
    
    # Análisis de calidad
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Calidad por Sucursal",
                dcc.Loading(
                    dcc.Graph(id="inventario-heatmap-calidad", style={"height": "500px"}),
                    type="circle"
                ),
                icon="fas fa-th"
            )
        ], md=12)
    ], className="mb-4"),
    
    # Tabla detallada
    dbc.Row([
        dbc.Col([
            create_summary_card(
                "Detalle de Transformadores",
                html.Div([
                    html.Div(id="inventario-table-summary", className="mb-3"),
                    dcc.Loading(
                        html.Div(id="inventario-data-table"),
                        type="circle"
                    )
                ]),
                icon="fas fa-table"
            )
        ])
    ])
])

# Callbacks
@callback(
    Output("inventario-sucursal-filter", "options"),
    Input("inventario-estado-filter", "value")
)
def update_sucursal_options(_):
    """Actualiza opciones de sucursales"""
    try:
        df = load_transformadores_completo()
        if df.empty or 'N_Sucursal' not in df.columns:
            return [{"label": "Todas", "value": "all"}]
        
        # Obtener sucursales únicas y limpiar NaN
        sucursales = df['N_Sucursal'].dropna().unique()
        sucursales = sorted([s for s in sucursales if s and str(s).strip()])
        
        options = [{"label": "Todas", "value": "all"}]
        options.extend([{"label": str(s), "value": str(s)} for s in sucursales])
        
        return options
    except Exception as e:
        print(f"Error en update_sucursal_options: {e}")
        return [{"label": "Todas", "value": "all"}]

@callback(
    Output("inventario-metrics", "children"),
    [Input("inventario-sucursal-filter", "value"),
     Input("inventario-estado-filter", "value"),
     Input("inventario-size-filter", "value")]
)
def update_metrics(sucursal, estado, size):
    """Actualiza métricas según filtros"""
    df = filter_transformadores(
        branch=sucursal,
        quality=estado
    )
    
    if df.empty:
        return dbc.Alert("No hay datos para los filtros seleccionados", color="warning")
    
    # Filtro adicional por tamaño
    if size != "all" and 'size_category' in df.columns:
        df = df[df['size_category'] == size]
    
    # Calcular métricas
    total_trafos = len(df)
    total_usuarios = df['Q_Usuarios'].sum() if 'Q_Usuarios' in df.columns else 0
    capacidad_total = df['Potencia'].sum() / 1000 if 'Potencia' in df.columns else 0
    
    if 'Resultado' in df.columns:
        correctas = (df['Resultado'] == 'Correcta').sum()
        penalizadas = (df['Resultado'] == 'Penalizada').sum()
        fallidas = (df['Resultado'] == 'Fallida').sum()
        tasa_problemas = ((penalizadas + fallidas) / total_trafos * 100) if total_trafos > 0 else 0
    else:
        correctas = penalizadas = fallidas = 0
        tasa_problemas = 0
    
    return dbc.Row([
        dbc.Col([
            create_metric_card(
                "Transformadores",
                f"{total_trafos:,}",
                "fas fa-bolt",
                color="primary"
            )
        ], xs=6, md=3),
        dbc.Col([
            create_metric_card(
                "Usuarios Afectados",
                f"{total_usuarios:,}",
                "fas fa-users",
                color="info"
            )
        ], xs=6, md=3),
        dbc.Col([
            create_metric_card(
                "Capacidad Total",
                f"{capacidad_total:.1f} MVA",
                "fas fa-power-off",
                color="success"
            )
        ], xs=6, md=3),
        dbc.Col([
            create_metric_card(
                "Tasa de Problemas",
                f"{tasa_problemas:.1f}%",
                "fas fa-exclamation-triangle",
                color="warning" if tasa_problemas < 50 else "danger",
                subtitle=f"{fallidas} fallidas"
            )
        ], xs=6, md=3)
    ])

@callback(
    Output("inventario-bar-sucursal", "figure"),
    [Input("inventario-sucursal-filter", "value"),
     Input("inventario-estado-filter", "value"),
     Input("inventario-size-filter", "value")]
)
def update_bar_sucursal(sucursal, estado, size):
    """Actualiza gráfico de barras por sucursal"""
    df = filter_transformadores(branch=sucursal, quality=estado)
    
    if df.empty or 'N_Sucursal' not in df.columns:
        return go.Figure().add_annotation(text="No hay datos disponibles", showarrow=False)
    
    # Filtro adicional por tamaño
    if size != "all" and 'size_category' in df.columns:
        df = df[df['size_category'] == size]
    
    # Agrupar por sucursal
    summary = df.groupby('N_Sucursal').size().reset_index(name='cantidad')
    summary = summary.sort_values('cantidad', ascending=True)
    
    fig = go.Figure([
        go.Bar(
            x=summary['cantidad'],
            y=summary['N_Sucursal'],
            orientation='h',
            marker_color='#3b82f6',
            text=summary['cantidad'],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        xaxis_title="Cantidad de Transformadores",
        yaxis_title="",
        showlegend=False,
        height=400,
        margin=dict(l=20, r=20, t=20, b=40)
    )
    
    return fig

@callback(
    Output("inventario-pie-capacidad", "figure"),
    [Input("inventario-sucursal-filter", "value"),
     Input("inventario-estado-filter", "value"),
     Input("inventario-size-filter", "value")]
)
def update_pie_capacidad(sucursal, estado, size):
    """Actualiza gráfico de torta por capacidad"""
    df = filter_transformadores(branch=sucursal, quality=estado)
    
    if df.empty:
        return go.Figure().add_annotation(text="No hay datos disponibles", showarrow=False)
    
    # Crear categorías de capacidad si no existen
    if 'size_category' not in df.columns and 'Potencia' in df.columns:
        df['size_category'] = pd.cut(
            df['Potencia'],
            bins=[0, 25, 100, 315, float('inf')],
            labels=['Micro', 'Pequeño', 'Mediano', 'Grande']
        )
    
    if 'size_category' in df.columns:
        # Filtro adicional
        if size != "all":
            df = df[df['size_category'] == size]
        
        dist = df['size_category'].value_counts()
        
        colors = {
            'Micro': '#60a5fa',
            'Pequeño': '#3b82f6', 
            'Mediano': '#fbbf24',
            'Grande': '#ef4444'
        }
        
        fig = go.Figure([
            go.Pie(
                labels=dist.index,
                values=dist.values,
                hole=0.4,
                marker_colors=[colors.get(x, '#gray') for x in dist.index]
            )
        ])
        
        fig.update_layout(
            showlegend=True,
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            annotations=[dict(text='Capacidad', x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
    else:
        fig = go.Figure().add_annotation(text="No hay datos de capacidad", showarrow=False)
    
    return fig

@callback(
    Output("inventario-heatmap-calidad", "figure"),
    [Input("inventario-sucursal-filter", "value"),
     Input("inventario-estado-filter", "value"),
     Input("inventario-size-filter", "value")]
)
def update_heatmap_calidad(sucursal, estado, size):
    """Actualiza mapa de calor de calidad por sucursal"""
    df = load_transformadores_completo()
    
    if df.empty or 'N_Sucursal' not in df.columns or 'Resultado' not in df.columns:
        return go.Figure().add_annotation(text="No hay datos disponibles", showarrow=False)
    
    # Aplicar filtros básicos
    if sucursal != "all":
        df = df[df['N_Sucursal'] == sucursal]
    if estado != "all":
        df = df[df['Resultado'] == estado]
    if size != "all" and 'size_category' in df.columns:
        df = df[df['size_category'] == size]
    
    # Crear tabla pivote
    pivot = pd.crosstab(df['N_Sucursal'], df['Resultado'])
    
    # Calcular porcentajes
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    
    # Crear heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_pct.values,
        x=pivot_pct.columns,
        y=pivot_pct.index,
        colorscale='RdYlGn_r',
        text=pivot.values,
        texttemplate='%{text}',
        textfont={"size": 10},
        hovertemplate='Sucursal: %{y}<br>Estado: %{x}<br>Porcentaje: %{z:.1f}%<br>Cantidad: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        xaxis_title="Estado de Calidad",
        yaxis_title="Sucursal",
        height=500,
        margin=dict(l=150, r=20, t=20, b=40)
    )
    
    return fig

@callback(
    [Output("inventario-table-summary", "children"),
     Output("inventario-data-table", "children")],
    [Input("inventario-sucursal-filter", "value"),
     Input("inventario-estado-filter", "value"),
     Input("inventario-size-filter", "value"),
     Input("inventario-search", "value")]
)
def update_data_table(sucursal, estado, size, search):
    """Actualiza tabla de datos detallada"""
    df = filter_transformadores(branch=sucursal, quality=estado)
    
    if df.empty:
        return "No hay datos para mostrar", html.Div()
    
    # Filtros adicionales
    if size != "all" and 'size_category' in df.columns:
        df = df[df['size_category'] == size]
    
    # Búsqueda
    if search:
        search_lower = search.lower()
        # Buscar en múltiples columnas
        mask = False
        for col in ['Codigoct', 'Codigo', 'N_Localida', 'Alimentador']:
            if col in df.columns:
                mask |= df[col].astype(str).str.lower().str.contains(search_lower, na=False)
        df = df[mask]
    
    # Resumen
    summary = f"Mostrando {len(df):,} transformadores"
    
    if len(df) == 0:
        return summary, html.Div("No se encontraron resultados", className="text-muted")
    
    # Seleccionar columnas para mostrar
    columns_to_show = []
    column_names = {}
    
    # Mapeo de columnas
    col_mapping = {
        'Codigoct': 'Código',
        'Codigo': 'Código',
        'N_Sucursal': 'Sucursal',
        'N_Localida': 'Localidad',
        'Alimentador': 'Alimentador',
        'Potencia': 'Potencia (kVA)',
        'Q_Usuarios': 'Usuarios',
        'Resultado': 'Estado',
        'criticidad_compuesta': 'Criticidad',
        'prioridad_gd': 'Prioridad GD'
    }
    
    for col, name in col_mapping.items():
        if col in df.columns:
            columns_to_show.append(col)
            column_names[col] = name
    
    # Limitar registros para performance
    df_show = df[columns_to_show].head(500)
    
    # Crear tabla
    table = dash_table.DataTable(
        id='inventario-table',
        columns=[{"name": column_names.get(col, col), "id": col} for col in columns_to_show],
        data=df_show.to_dict('records'),
        page_size=20,
        page_action='native',
        sort_action='native',
        filter_action='native',
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{Resultado} = Fallida', 'column_id': 'Resultado'},
                'backgroundColor': '#fee2e2',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{Resultado} = Penalizada', 'column_id': 'Resultado'},
                'backgroundColor': '#fef3c7',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{Resultado} = Correcta', 'column_id': 'Resultado'},
                'backgroundColor': '#d1fae5',
                'color': 'black',
            }
        ],
        export_format='csv',
        export_headers='display'
    )
    
    if len(df) > 500:
        summary += f" (mostrando primeros 500)"
    
    return summary, table