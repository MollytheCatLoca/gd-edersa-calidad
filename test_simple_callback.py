#!/usr/bin/env python3
"""
Test simple callback para identificar el error
"""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc

# Create app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Simple layout
app.layout = dbc.Container([
    html.H1("Test Simple Callback"),
    dbc.Button("Click Me", id="test-btn", color="primary"),
    dcc.Store(id="test-store"),
    html.Div(id="test-panel", style={"display": "none"}),
    html.Div(id="test-output")
])

@callback(
    Output("test-store", "data"),
    Output("test-panel", "style"),
    Input("test-btn", "n_clicks"),
    prevent_initial_call=True
)
def test_callback(n_clicks):
    print(f"Test callback called with n_clicks={n_clicks}")
    
    # Try returning simple valid data
    data = {"test": "data", "n_clicks": n_clicks}
    style = {"display": "block", "color": "green"}
    
    print(f"Returning data={data}, style={style}")
    return data, style

@callback(
    Output("test-output", "children"),
    Input("test-store", "data")
)
def update_output(data):
    if not data:
        return "No data yet"
    return f"Data received: {data}"

if __name__ == "__main__":
    app.run(debug=True, port=8051)