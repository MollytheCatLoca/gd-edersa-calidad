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
            
            # Nuevas páginas de Fase 2.5
            html.Hr(className="my-2"),
            html.Small("FASE 2.5 - Análisis Avanzado", className="text-muted text-uppercase d-block px-3 mb-2"),
            
            dbc.NavLink([
                html.I(className="fas fa-sun me-2"),
                "IAS 3.0 Analysis"
            ], href="/ias-v3", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-map me-2"),
                "Land Availability"
            ], href="/land-availability", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-clock me-2"),
                "24h Benefits"
            ], href="/benefits-24h", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-chart-line me-2"),
                "Executive Summary"
            ], href="/executive-summary", active="exact", className="mb-1"),
            
            # Nuevas páginas de Fase 3
            html.Hr(className="my-2"),
            html.Small("FASE 3 - Optimización", className="text-muted text-uppercase d-block px-3 mb-2"),
            
            dbc.NavLink([
                html.I(className="fas fa-cog me-2"),
                "Configuración"
            ], href="/optimization-config", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-calculator me-2"),
                "Análisis de Flujos"
            ], href="/optimization-analysis", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-balance-scale me-2"),
                "Comparación"
            ], href="/optimization-comparison", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-briefcase me-2"),
                "Portfolio"
            ], href="/optimization-portfolio", active="exact", className="mb-1"),
            
            dbc.NavLink([
                html.I(className="fas fa-chart-area me-2"),
                "Sensibilidad"
            ], href="/optimization-sensitivity", active="exact", className="mb-1"),
            
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
                html.I(className="fas fa-check-circle me-1"),
                "Fase 0, 1, 2 & 2.5 Completadas"
            ], className="text-muted"),
            html.Br(),
            html.Small([
                html.I(className="fas fa-spinner fa-spin me-1"),
                "Fase 3 En Progreso"
            ], className="text-muted"),
            html.Br(),
            html.Small([
                html.I(className="fas fa-database me-1"),
                "2,690 Transformadores"
            ], className="text-muted"),
            html.Br(),
            html.Small([
                html.I(className="fas fa-solar-panel me-1"),
                "120.5 MW GD Identificados"
            ], className="text-muted"),
            html.Br(),
            html.Small([
                html.I(className="fas fa-users me-1"),
                "158,476 Usuarios Beneficiados"
            ], className="text-muted")
        ], className="px-3 mb-3")
    ])
    
    return sidebar