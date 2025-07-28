#!/usr/bin/env python3
"""
Test MÍNIMO del error de callback de Dash
"""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc

# Crear app simple
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout mínimo - idéntico a optimization_analysis.py
app.layout = dbc.Container([
    html.H1("Test Mínimo del Error"),
    
    # Los mismos IDs que causan el error
    dbc.Button("Calcular Flujos", id="calculate-flows-btn", color="primary"),
    
    # Sliders como en el original
    html.Div([
        dcc.Slider(id="pv-ratio-slider", min=0, max=2, step=0.1, value=1.2),
        dcc.Slider(id="bess-hours-slider", min=0, max=8, step=0.5, value=4),
        dcc.Slider(id="q-night-ratio-slider", min=0, max=0.5, step=0.05, value=0.3),
    ]),
    
    # Store para cluster data
    dcc.Store(id="cluster-data-store", data=[{"potencia_kva": 630}]),
    
    # Los dos outputs problemáticos
    dcc.Store(id="calculation-results-store"),
    html.Div(id="results-panel", style={"display": "none"}),
    
    # Debug output
    html.Div(id="debug-output", style={"marginTop": "20px"})
])

# EL CALLBACK PROBLEMÁTICO - versión mínima
@callback(
    Output("calculation-results-store", "data"),
    Output("results-panel", "style"),
    Input("calculate-flows-btn", "n_clicks"),
    State("pv-ratio-slider", "value"),
    State("bess-hours-slider", "value"),  
    State("q-night-ratio-slider", "value"),
    State("cluster-data-store", "data"),
    prevent_initial_call=True
)
def calculate_flows(n_clicks, pv_ratio, bess_hours, q_ratio, cluster_data):
    """Callback mínimo que replica el error"""
    print("\n=== CALLBACK TRIGGERED ===")
    print(f"n_clicks: {n_clicks}")
    print(f"pv_ratio: {pv_ratio}")
    print(f"bess_hours: {bess_hours}")
    print(f"q_ratio: {q_ratio}")
    print(f"cluster_data: {cluster_data}")
    
    # Retornar datos válidos simples
    return {"test": "ok"}, {"display": "block"}

# Callback adicional para mostrar resultados
@callback(
    Output("debug-output", "children"),
    Input("calculation-results-store", "data")
)
def show_results(data):
    if not data:
        return "Sin datos aún..."
    return f"Datos recibidos: {data}"

if __name__ == "__main__":
    print("Iniciando app de prueba en http://127.0.0.1:8052/")
    print("Presiona el botón 'Calcular Flujos' para probar el callback")
    app.run(debug=True, port=8052)