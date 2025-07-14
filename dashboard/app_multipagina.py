"""
Dashboard Multi-página para el Sistema Eléctrico Línea Sur

Este dashboard organiza el análisis en las 9 fases del proyecto.
"""

import dash
from dash import Dash, html, dcc, page_container
import dash_bootstrap_components as dbc
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import components
from dashboard.components.navbar import create_navbar
from dashboard.components.sidebar import create_sidebar

# Initialize Dash app with pages
app = Dash(
    __name__, 
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    pages_folder="pages"
)

# Define app layout
app.layout = html.Div([
    # Navigation bar
    create_navbar(),
    
    # Main container with sidebar and content
    html.Div([
        # Sidebar
        create_sidebar(),
        
        # Main content area
        html.Div([
            # Page container
            page_container
        ], style={
            "marginLeft": "300px",
            "padding": "20px"
        })
    ])
])

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Custom styles */
            .navbar-brand {
                font-weight: bold;
            }
            
            .card {
                transition: transform 0.2s;
            }
            
            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            
            .progress {
                background-color: #e9ecef;
            }
            
            /* Responsive adjustments */
            @media (max-width: 768px) {
                div[style*="marginLeft: 300px"] {
                    margin-left: 0 !important;
                }
                
                div[style*="position: fixed"] {
                    position: relative !important;
                    width: 100% !important;
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

# Run the app
if __name__ == '__main__':
    print("Starting multi-page dashboard...")
    print("Open http://localhost:8050 in your browser")
    print("\nAvailable pages:")
    print("  - Home: http://localhost:8050/")
    print("  - Fase 1 Comprensión: http://localhost:8050/fase1-comprension")
    print("  - Fase 2 Topología: http://localhost:8050/fase2-topologia")
    print("  - Fase 3 Datos: http://localhost:8050/fase3-datos")
    print("  - Fase 4 Solar+BESS: http://localhost:8050/fase4-bess-lab")
    print("  - More phases coming soon...")
    
    app.run(debug=True, host='0.0.0.0', port=8050)