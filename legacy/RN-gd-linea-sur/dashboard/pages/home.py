"""
Home page - Overview del proyecto
"""

from dash import dcc, html, callback
import dash
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Register page
dash.register_page(__name__, path='/', name='Home', title='Inicio')

# Define layout
layout = html.Div([
    # Header
    html.Div([
        html.H1("Sistema Eléctrico Línea Sur", className="text-center mb-2"),
        html.H3("Estudio de Generación Distribuida - Río Negro", className="text-center text-muted mb-4"),
    ]),
    
    # Executive Summary Card
    html.Div([
        html.Div([
            html.Div([
                html.H4("Resumen Ejecutivo", className="card-header"),
                html.Div([
                    html.P([
                        "El sistema de transmisión de 33 kV de la Línea Sur presenta ",
                        html.Strong("severas deficiencias operativas"),
                        " con caídas de tensión documentadas de hasta ",
                        html.Span("41%", className="text-danger fw-bold"),
                        " y capacidad ",
                        html.Span("NULA", className="text-danger fw-bold"),
                        " para nuevas cargas en horario pico."
                    ]),
                    html.P([
                        "Este estudio analiza la implementación de ",
                        html.Strong("Generación Distribuida (GD)"),
                        " como solución técnica y económicamente viable para mejorar la calidad de servicio."
                    ])
                ], className="card-body")
            ], className="card mb-4")
        ], className="col-12")
    ], className="row"),
    
    # KPI Cards
    html.Div([
        # Sistema
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-bolt fa-3x text-primary mb-3"),
                    html.H2("270 km"),
                    html.P("Longitud Total", className="text-muted"),
                    html.Small("7 Estaciones", className="text-secondary")
                ], className="card-body text-center")
            ], className="card h-100 shadow-sm")
        ], className="col-md-3 mb-4"),
        
        # Carga
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-plug fa-3x text-success mb-3"),
                    html.H2("3.80 MW"),
                    html.P("Carga Total", className="text-muted"),
                    html.Small("FP: 0.964", className="text-secondary")
                ], className="card-body text-center")
            ], className="card h-100 shadow-sm")
        ], className="col-md-3 mb-4"),
        
        # Problema
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-exclamation-triangle fa-3x text-danger mb-3"),
                    html.H2("41%"),
                    html.P("Caída Máxima", className="text-muted"),
                    html.Small("Límite: 5%", className="text-secondary")
                ], className="card-body text-center")
            ], className="card h-100 shadow-sm")
        ], className="col-md-3 mb-4"),
        
        # Pérdidas
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-fire fa-3x text-warning mb-3"),
                    html.H2("33%"),
                    html.P("Pérdidas", className="text-muted"),
                    html.Small("1.86 MW", className="text-secondary")
                ], className="card-body text-center")
            ], className="card h-100 shadow-sm")
        ], className="col-md-3 mb-4"),
    ], className="row"),
    
    # Progress Overview
    html.Div([
        html.H4("Progreso del Estudio", className="mb-3"),
        html.Div([
            # Phase progress bars
            html.Div([
                html.Div([
                    html.Div("Fase 1: Comprensión de la Red", className="d-flex justify-content-between"),
                    html.Div([
                        html.Div(className="progress-bar bg-success", style={"width": "100%"})
                    ], className="progress mb-3"),
                    
                    html.Div("Fase 2: Modelado y Visualización", className="d-flex justify-content-between"),
                    html.Div([
                        html.Div(className="progress-bar bg-success", style={"width": "100%"})
                    ], className="progress mb-3"),
                    
                    html.Div("Fase 3: Procesamiento de Datos", className="d-flex justify-content-between"),
                    html.Div([
                        html.Div(className="progress-bar bg-success", style={"width": "100%"})
                    ], className="progress mb-3"),
                    
                    html.Div("Fase 4: Modelo Solar + BESS", className="d-flex justify-content-between"),
                    html.Div([
                        html.Div(className="progress-bar bg-success", style={"width": "100%"})
                    ], className="progress mb-3"),
                    
                    html.Div("Fase 5: Machine Learning", className="d-flex justify-content-between"),
                    html.Div([
                        html.Div(className="progress-bar bg-secondary", style={"width": "0%"})
                    ], className="progress mb-3"),
                ], className="col-md-6"),
                
                html.Div([
                    html.Div("Fase 6: Flujos de Potencia", className="d-flex justify-content-between"),
                    html.Div([
                        html.Div(className="progress-bar bg-secondary", style={"width": "0%"})
                    ], className="progress mb-3"),
                    
                    html.Div("Fase 7: Análisis Económico", className="d-flex justify-content-between"),
                    html.Div([
                        html.Div(className="progress-bar bg-secondary", style={"width": "0%"})
                    ], className="progress mb-3"),
                    
                    html.Div("Fase 8: Optimización", className="d-flex justify-content-between"),
                    html.Div([
                        html.Div(className="progress-bar bg-secondary", style={"width": "0%"})
                    ], className="progress mb-3"),
                    
                    html.Div("Fase 9: Informe Final", className="d-flex justify-content-between"),
                    html.Div([
                        html.Div(className="progress-bar bg-secondary", style={"width": "0%"})
                    ], className="progress mb-3"),
                ], className="col-md-6"),
            ], className="row")
        ], className="card-body")
    ], className="card mb-4"),
    
    # Quick Actions
    html.Div([
        html.H4("Acceso Rápido", className="mb-3"),
        html.Div([
            html.Div([
                dcc.Link([
                    html.Button([
                        html.I(className="fas fa-map-marked-alt me-2"),
                        "Ver Mapa del Sistema"
                    ], className="btn btn-primary btn-lg w-100")
                ], href="/fase2-topologia")
            ], className="col-md-4 mb-3"),
            
            html.Div([
                dcc.Link([
                    html.Button([
                        html.I(className="fas fa-chart-line me-2"),
                        "Análisis de Datos"
                    ], className="btn btn-info btn-lg w-100")
                ], href="/fase3-datos")
            ], className="col-md-4 mb-3"),
            
            html.Div([
                dcc.Link([
                    html.Button([
                        html.I(className="fas fa-file-pdf me-2"),
                        "Generar Informe"
                    ], className="btn btn-success btn-lg w-100")
                ], href="/fase9-informes")
            ], className="col-md-4 mb-3"),
        ], className="row")
    ]),
    
    # Footer info
    html.Hr(),
    html.Div([
        html.P([
            html.Small([
                "Última actualización: ",
                datetime.now().strftime("%d/%m/%Y %H:%M"),
                " | Proyecto desarrollado para EdERSA - Empresa de Energía Río Negro S.A."
            ], className="text-muted")
        ], className="text-center")
    ])
], className="container-fluid p-4")