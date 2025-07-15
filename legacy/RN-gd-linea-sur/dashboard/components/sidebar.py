"""
Sidebar component showing project progress
"""

from dash import html
import dash_bootstrap_components as dbc

def create_sidebar():
    """Create sidebar with project progress and navigation."""
    
    # Phase progress data
    phases = [
        {"name": "Fase 1: Comprensión de la Red", "progress": 100, "status": "completed"},
        {"name": "Fase 2: Modelado y Visualización", "progress": 100, "status": "completed"},
        {"name": "Fase 3: Procesamiento de Datos", "progress": 100, "status": "completed"},
        {"name": "Fase 4: Laboratorio BESS", "progress": 100, "status": "completed"},
        {"name": "Fase 5: Machine Learning", "progress": 0, "status": "pending"},
        {"name": "Fase 6: Flujos de Potencia", "progress": 0, "status": "pending"},
        {"name": "Fase 7: Análisis Económico", "progress": 0, "status": "pending"},
        {"name": "Fase 8: Optimización", "progress": 0, "status": "pending"},
        {"name": "Fase 9: Informe Final", "progress": 0, "status": "pending"},
    ]
    
    # Create phase items
    phase_items = []
    for i, phase in enumerate(phases, 1):
        # Icon based on status
        if phase["status"] == "completed":
            icon = html.I(className="fas fa-check-circle text-success me-2")
            progress_color = "success"
        elif phase["status"] == "in-progress":
            icon = html.I(className="fas fa-spinner fa-spin text-warning me-2")
            progress_color = "warning"
        else:
            icon = html.I(className="far fa-circle text-secondary me-2")
            progress_color = "secondary"
        
        phase_item = html.Div([
            html.Div([
                icon,
                html.Span(phase["name"], className="small")
            ], className="d-flex align-items-center mb-1"),
            
            dbc.Progress(
                value=phase["progress"],
                color=progress_color,
                className="mb-3",
                style={"height": "5px"}
            )
        ])
        
        phase_items.append(phase_item)
    
    sidebar = html.Div([
        html.H5("Progreso del Estudio", className="text-center mb-4"),
        html.Hr(),
        
        # Overall progress
        html.Div([
            html.P("Progreso Total", className="mb-2 fw-bold"),
            dbc.Progress(
                [
                    dbc.Progress(value=44, color="success", bar=True),
                    dbc.Progress(value=0, color="warning", bar=True),
                    dbc.Progress(value=56, color="secondary", bar=True),
                ],
                className="mb-4"
            ),
            html.Small("44% Completado", className="text-muted")
        ], className="mb-4"),
        
        html.Hr(),
        
        # Phase list
        html.Div(phase_items),
        
        html.Hr(),
        
        # Quick stats
        html.Div([
            html.H6("Estadísticas Rápidas", className="mb-3"),
            html.Div([
                html.Small("Fases completadas: ", className="text-muted"),
                html.Strong("4/9")
            ], className="mb-2"),
            html.Div([
                html.Small("Tiempo estimado restante: ", className="text-muted"),
                html.Strong("45 días")
            ], className="mb-2"),
            html.Div([
                html.Small("Última actualización: ", className="text-muted"),
                html.Strong("Hoy")
            ])
        ])
    ], className="p-3 bg-light", style={
        "position": "fixed",
        "top": "70px",
        "left": 0,
        "bottom": 0,
        "width": "280px",
        "overflowY": "auto"
    })
    
    return sidebar