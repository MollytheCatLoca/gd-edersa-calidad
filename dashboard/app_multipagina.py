"""
Dashboard Multi-página EDERSA - Sistema de Análisis de Calidad
=============================================================

Dashboard principal que organiza el análisis en diferentes vistas:
- Vista general del sistema
- Análisis de inventario
- Análisis topológico (MST)
- Análisis eléctrico
- Análisis de vulnerabilidad
- Clustering preliminar

Basado en los hallazgos de Fase 0 y el análisis eléctrico extendido.
"""

import dash
from dash import Dash, html, dcc, page_container
import dash_bootstrap_components as dbc
from pathlib import Path
import sys

# Agregar el proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Importar componentes
from dashboard.components.navbar import create_navbar
from dashboard.components.sidebar import create_sidebar

# Inicializar aplicación Dash con páginas
app = Dash(
    __name__, 
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    pages_folder="pages",
    title="EDERSA - Análisis de Calidad y GD"
)

# Configurar el servidor para deployment
server = app.server

# Estilos CSS personalizados
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Estilos globales */
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                background-color: #f8f9fa;
            }
            
            /* Sidebar fijo */
            .sidebar {
                position: fixed;
                top: 56px;
                bottom: 0;
                left: 0;
                z-index: 100;
                padding: 48px 0 0;
                box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
                width: 280px;
                background-color: #fff;
                overflow-y: auto;
            }
            
            /* Contenido principal */
            .main-content {
                margin-left: 280px;
                padding: 20px;
                margin-top: 56px;
            }
            
            /* Cards mejoradas */
            .custom-card {
                border: none;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: box-shadow 0.3s ease;
            }
            
            .custom-card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            /* Métricas */
            .metric-card {
                text-align: center;
                padding: 1.5rem;
                border-radius: 8px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .metric-value {
                font-size: 2.5rem;
                font-weight: bold;
                margin: 0;
            }
            
            .metric-label {
                font-size: 0.875rem;
                opacity: 0.9;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .sidebar {
                    width: 100%;
                    height: auto;
                    position: relative;
                }
                .main-content {
                    margin-left: 0;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout de la aplicación
app.layout = html.Div([
    # Almacenamiento en el cliente para estado global
    dcc.Store(id='selected-feeder-store', storage_type='session'),
    dcc.Store(id='selected-branch-store', storage_type='session'),
    dcc.Store(id='filters-store', storage_type='session'),
    
    # Barra de navegación superior
    create_navbar(),
    
    # Contenedor principal con sidebar y contenido
    html.Div([
        # Sidebar con navegación
        html.Div(
            create_sidebar(),
            className="sidebar"
        ),
        
        # Área de contenido principal
        html.Div([
            # Contenedor de páginas (Dash Pages maneja esto)
            page_container
        ], className="main-content")
    ])
])

# Callback para mantener sincronizados los filtros globales
# (se implementarán en cada página según necesidad)

if __name__ == '__main__':
    app.run(debug=True, port=8050)