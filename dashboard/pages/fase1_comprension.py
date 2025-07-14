"""
Fase 1 - Comprensión de la Red (Versión Modular)
Dashboard principal que importa componentes de otros módulos
"""

from dash import dcc, html, callback, Input, Output, State
import dash
import dash_bootstrap_components as dbc
from pathlib import Path

# Import data manager
from dashboard.pages.utils import get_data_manager

# Import tab components
from dashboard.pages.components.tab1_overview import render_overview_tab
from dashboard.pages.components.tab2_transformers_visual import render_transformers_tab
from dashboard.pages.components.tab3_lines import render_lines_tab
from dashboard.pages.components.tab4_loads import render_loads_tab
from dashboard.pages.components.tab5_regulation import render_regulation_tab
from dashboard.pages.components.tab6_distributed_generation import render_dg_tab

# Additional imports for tooltips
from dash.dependencies import State

# Register page
dash.register_page(__name__, path='/fase1-comprension', name='Fase 1: Comprensión', title='Comprensión de la Red')

# Get project root
project_root = Path(__file__).parent.parent.parent

# Define layout
layout = html.Div([
    # Header with title and data status
    dbc.Row([
        dbc.Col([
            html.H2("Sistema Eléctrico Línea Sur - Vista General", className="text-center mb-2"),
            html.P("Análisis técnico integral del sistema de 33 kV", className="text-center text-muted mb-3"),
        ], md=10),
        dbc.Col([
            # Data status indicator
            html.Div(id="f1-data-status-indicator", className="text-end mt-2")
        ], md=2)
    ]),
    
    # Key Metrics Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Longitud Total", className="text-muted mb-1"),
                    html.H3("270 km", className="text-primary mb-0"),
                    html.Small("Radial 33 kV", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Carga Total", className="text-muted mb-1"),
                    html.H3("3.80 MW", className="text-success mb-0"),
                    html.Small("1.05 MVAr | FP: 0.964", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Pérdidas Estimadas", className="text-muted mb-1"),
                    html.H3("~0.4 MW", className="text-warning mb-0"),
                    html.Small("~10% (típico)", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Caída Máxima V", className="text-muted mb-1"),
                    html.H3("20-41%", className="text-danger mb-0"),
                    html.Small("Crítico en extremo", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Capacidad Pico", className="text-muted mb-1"),
                    html.H3("NULA", className="text-danger mb-0"),
                    html.Small("Sin margen", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Reguladores", className="text-muted mb-1"),
                    html.H3("3", className="text-info mb-0"),
                    html.Small("Críticos", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=2),
    ], className="mb-4"),
    
    # Main tabs structure
    dbc.Tabs([
        # Tab 1: Vista General
        dbc.Tab(label="Vista General", tab_id="tab-overview"),
        
        # Tab 2: Transformadores
        dbc.Tab(label="Transformadores", tab_id="tab-transformers"),
        
        # Tab 3: Líneas
        dbc.Tab(label="Líneas y Conductores", tab_id="tab-lines"),
        
        # Tab 4: Cargas
        dbc.Tab(label="Cargas y Factor de Potencia", tab_id="tab-loads"),
        
        # Tab 5: Regulación
        dbc.Tab(label="Sistema de Regulación", tab_id="tab-regulation"),
        
        # Tab 6: GD (placeholder)
        dbc.Tab(label="Generación Distribuida", tab_id="tab-dg"),
        
        # Tab 7: Criticidad (placeholder)
        dbc.Tab(label="Análisis de Criticidad", tab_id="tab-criticality"),
        
        # Tab 8: Gaps (placeholder)
        dbc.Tab(label="Gaps de Información", tab_id="tab-gaps")
    ], id="f1-main-tabs", active_tab="tab-overview"),
    
    # Tab content container
    dbc.Container([
        html.Div(id="f1-tab-content")
    ], fluid=True, className="mt-4"),
    
    # Tooltip for data status
    dbc.Tooltip(
        id="f1-data-status-tooltip",
        target="f1-data-status-badge",
        placement="left"
    )
])

# Main callback to render tab content
@callback(
    Output("f1-tab-content", "children"),
    Input("f1-main-tabs", "active_tab")
)
def render_tab_content(active_tab):
    """Render content based on active tab."""
    
    if active_tab == "tab-overview":
        return render_overview_tab()
    elif active_tab == "tab-transformers":
        return render_transformers_tab()
    elif active_tab == "tab-lines":
        return render_lines_tab()
    elif active_tab == "tab-loads":
        return render_loads_tab()
    elif active_tab == "tab-regulation":
        return render_regulation_tab()
    elif active_tab == "tab-dg":
        return render_dg_tab()
    elif active_tab == "tab-criticality":
        return html.Div("Tab 7: Criticidad - En desarrollo")
    elif active_tab == "tab-gaps":
        return html.Div("Tab 8: Gaps - En desarrollo")
    
    return html.Div("Seleccione una pestaña")

# Callback for data status indicator
@callback(
    Output("f1-data-status-indicator", "children"),
    Input("f1-main-tabs", "active_tab")  # Update on tab change
)
def update_data_status(_):
    """Update data status indicator."""
    dm = get_data_manager()
    status_color = dm.get_status_color()
    status_text = dm.get_status_text()
    status_summary = dm.get_status_summary()
    
    # Create status badge with integrated tooltip info
    badge = dbc.Badge(
        [
            html.I(className="fas fa-database me-1"),
            status_text
        ],
        color=status_color,
        pill=True,
        id="f1-data-status-badge",
        style={"cursor": "help"},
        title=f"Sistema: {status_summary['status']['system']} | Usando {'datos reales' if not status_summary['is_using_fallback'] else 'datos de respaldo'}"
    )
    
    return badge