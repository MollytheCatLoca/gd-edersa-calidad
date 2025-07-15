"""
Barra de navegación superior para el dashboard EDERSA
"""

import dash_bootstrap_components as dbc
from dash import html
from datetime import datetime

def create_navbar():
    """
    Crea la barra de navegación superior con logo, título y métricas clave
    """
    navbar = dbc.Navbar(
        dbc.Container([
            # Logo y título
            dbc.Row([
                dbc.Col([
                    html.A(
                        dbc.Row([
                            dbc.Col(html.I(className="fas fa-bolt fa-2x"), width="auto"),
                            dbc.Col(dbc.NavbarBrand("EDERSA - Análisis de Calidad", className="ms-2")),
                        ], align="center", className="g-0"),
                        href="/",
                        style={"textDecoration": "none"}
                    )
                ], width="auto"),
                
                # Indicadores en tiempo real
                dbc.Col([
                    dbc.Nav([
                        dbc.NavItem([
                            html.Div([
                                html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                                html.Span("555 Transformadores Críticos", className="text-white")
                            ])
                        ], className="me-4"),
                        dbc.NavItem([
                            html.Div([
                                html.I(className="fas fa-users text-info me-2"),
                                html.Span("158,476 Usuarios", className="text-white")
                            ])
                        ], className="me-4"),
                        dbc.NavItem([
                            html.Div([
                                html.I(className="fas fa-bolt text-success me-2"),
                                html.Span("401.7 MVA", className="text-white")
                            ])
                        ]),
                    ], navbar=True)
                ], width=True, className="text-end"),
                
                # Fecha/Hora
                dbc.Col([
                    html.Div([
                        html.I(className="far fa-clock me-2"),
                        html.Span(datetime.now().strftime("%d/%m/%Y"), className="text-white-50")
                    ])
                ], width="auto")
            ], className="flex-grow-1 align-items-center"),
        ], fluid=True),
        color="dark",
        dark=True,
        sticky="top",
        className="mb-0"
    )
    
    return navbar