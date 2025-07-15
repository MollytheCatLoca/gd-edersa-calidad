"""
Sidebar con navegación para el dashboard EDERSA
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import dash

def create_sidebar():
    """
    Crea el sidebar con navegación y filtros globales
    """
    sidebar = html.Div([
        # Título de la sección
        html.Div([
            html.H5("Navegación", className="text-uppercase text-muted mb-3"),
        ], className="px-3 mt-3"),
        
        # Enlaces de navegación
        dbc.Nav([
            dbc.NavLink([
                html.I(className="fas fa-home me-2"),
                "Vista General"
            ], href="/", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-database me-2"),
                "Inventario y Calidad"
            ], href="/inventario", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-project-diagram me-2"),
                "Topología de Red (MST)"
            ], href="/topologia", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-bolt me-2"),
                "Análisis Eléctrico"
            ], href="/electrico", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Vulnerabilidad"
            ], href="/vulnerabilidad", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-map-marked-alt me-2"),
                "Clustering y GD"
            ], href="/clustering", active="exact", className="mb-1"),
        ], vertical=True, pills=True, className="px-3"),
        
        html.Hr(className="my-4"),
        
        # Filtros globales
        html.Div([
            html.H6("Filtros Globales", className="text-uppercase text-muted mb-3"),
            
            # Filtro por sucursal
            html.Div([
                html.Label("Sucursal:", className="small"),
                dcc.Dropdown(
                    id="global-branch-filter",
                    options=[
                        {"label": "Todas", "value": "all"},
                        {"label": "ALLEN", "value": "ALLEN"},
                        {"label": "BARILOCHE", "value": "BARILOCHE"},
                        {"label": "CHOELE CHOEL", "value": "CHOELE CHOEL"},
                        {"label": "CIPOLLETTI", "value": "CIPOLLETTI"},
                        {"label": "EL BOLSON", "value": "EL BOLSON"},
                        {"label": "GENERAL CONESA", "value": "GENERAL CONESA"},
                        {"label": "GENERAL ROCA", "value": "GENERAL ROCA"},
                        {"label": "INGENIERO JACOBACCI", "value": "INGENIERO JACOBACCI"},
                        {"label": "RIO COLORADO", "value": "RIO COLORADO"},
                        {"label": "SAN ANTONIO OESTE", "value": "SAN ANTONIO OESTE"},
                        {"label": "SIERRA GRANDE", "value": "SIERRA GRANDE"},
                        {"label": "VALCHETA", "value": "VALCHETA"},
                        {"label": "VIEDMA", "value": "VIEDMA"},
                        {"label": "VILLA REGINA", "value": "VILLA REGINA"},
                    ],
                    value="all",
                    clearable=False,
                    className="mb-3"
                )
            ]),
            
            # Filtro por estado
            html.Div([
                html.Label("Estado de Calidad:", className="small"),
                dcc.Dropdown(
                    id="global-quality-filter",
                    options=[
                        {"label": "Todos", "value": "all"},
                        {"label": "Correcta", "value": "Correcta"},
                        {"label": "Penalizada", "value": "Penalizada"},
                        {"label": "Fallida", "value": "Fallida"}
                    ],
                    value="all",
                    clearable=False,
                    className="mb-3"
                )
            ]),
            
            # Filtro por vulnerabilidad
            html.Div([
                html.Label("Nivel de Vulnerabilidad:", className="small"),
                dcc.Dropdown(
                    id="global-vulnerability-filter",
                    options=[
                        {"label": "Todos", "value": "all"},
                        {"label": "Crítica", "value": "Crítica"},
                        {"label": "Alta", "value": "Alta"},
                        {"label": "Media", "value": "Media"},
                        {"label": "Baja", "value": "Baja"},
                        {"label": "Mínima", "value": "Mínima"}
                    ],
                    value="all",
                    clearable=False,
                    className="mb-3"
                )
            ])
        ], className="px-3"),
        
        html.Hr(className="my-4"),
        
        # Información adicional
        html.Div([
            html.Small([
                html.I(className="fas fa-info-circle me-1"),
                "Fase 0 Completada"
            ], className="text-muted"),
            html.Br(),
            html.Small([
                html.I(className="fas fa-database me-1"),
                "2,690 Transformadores"
            ], className="text-muted"),
            html.Br(),
            html.Small([
                html.I(className="fas fa-network-wired me-1"),
                "128 Alimentadores"
            ], className="text-muted")
        ], className="px-3 mb-3")
    ])
    
    return sidebar