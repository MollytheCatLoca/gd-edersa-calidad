"""
Navigation bar component for multi-page dashboard
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def create_navbar():
    """Create the navigation bar with links to all phases."""
    
    navbar = dbc.Navbar(
        dbc.Container([
            # Logo/Brand
            dbc.Row([
                dbc.Col([
                    html.A(
                        dbc.Row([
                            dbc.Col(html.I(className="fas fa-bolt fa-2x text-warning")),
                            dbc.Col(dbc.NavbarBrand("Línea Sur GD", className="ms-2 fs-4")),
                        ], align="center", className="g-0"),
                        href="/",
                        style={"textDecoration": "none"}
                    )
                ])
            ], align="center"),
            
            # Navigation items
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Inicio", href="/", className="mx-2")),
                
                # Dropdown for phases
                dbc.DropdownMenu(
                    children=[
                        dbc.DropdownMenuItem("Fase 1: Comprensión", href="/fase1-comprension"),
                        dbc.DropdownMenuItem("Fase 2: Topología ✨", href="/fase2-topologia-v2"),
                        dbc.DropdownMenuItem("Fase 3: Datos", href="/fase3-datos"),
                        dbc.DropdownMenuItem("Fase 4: Laboratorio BESS", href="/fase4-bess-lab"),
                        dbc.DropdownMenuItem("Fase 5: ML", href="/fase5-ml"),
                        dbc.DropdownMenuItem("Fase 6: Flujos", href="/fase6-flujos"),
                        dbc.DropdownMenuItem("Fase 7: Económico", href="/fase7-economico"),
                        dbc.DropdownMenuItem("Fase 8: Optimización", href="/fase8-optimizacion"),
                        dbc.DropdownMenuItem("Fase 9: Informes", href="/fase9-informes"),
                    ],
                    nav=True,
                    in_navbar=True,
                    label="Fases del Estudio",
                    className="mx-2"
                ),
                
                # Export button
                dbc.NavItem(
                    dbc.Button(
                        [html.I(className="fas fa-download me-2"), "Exportar"],
                        color="success",
                        size="sm",
                        className="ms-3"
                    )
                ),
            ], className="ms-auto", navbar=True)
        ]),
        color="dark",
        dark=True,
        className="mb-4"
    )
    
    return navbar