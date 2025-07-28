"""
Componentes reutilizables para las páginas de optimización FASE 3
================================================================
Provee componentes visuales consistentes y estilizados para todas
las páginas de la fase de optimización.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px

# Paleta de colores consistente
COLORS = {
    'primary': '#3B82F6',      # Azul
    'secondary': '#10B981',    # Verde
    'accent': '#8B5CF6',       # Púrpura
    'warning': '#F59E0B',      # Naranja
    'danger': '#EF4444',       # Rojo
    'info': '#06B6D4',         # Cyan
    'light': '#F3F4F6',        # Gris claro
    'dark': '#1F2937',         # Gris oscuro
    'white': '#FFFFFF',
    'success': '#059669'       # Verde oscuro
}

# Gradientes para cards
GRADIENTS = {
    'blue': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'green': 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
    'orange': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'purple': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
    'red': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'teal': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
}

def create_header_section(title, subtitle, icon="fas fa-chart-line"):
    """
    Crea una sección de header estilizada con gradiente
    """
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className=f"{icon} fa-2x mb-3", 
                              style={'color': COLORS['primary'], 'opacity': '0.8'}),
                        html.H2(title, className="mb-2 fw-bold"),
                        html.P(subtitle, className="text-muted mb-0 lead")
                    ])
                ], width=12)
            ])
        ], className="py-4")
    ], className="mb-4 shadow-sm border-0", 
    style={
        'background': 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
        'borderLeft': f'4px solid {COLORS["primary"]}'
    })

def create_metric_card_v3(title, value, subtitle="", icon="fas fa-chart-line", 
                         color="primary", gradient=True):
    """
    Crea una tarjeta de métrica mejorada con gradiente opcional
    """
    bg_style = {}
    text_color = "white"
    
    if gradient and color in ['blue', 'green', 'orange', 'purple', 'red', 'teal']:
        bg_style = {'background': GRADIENTS[color]}
    else:
        bg_style = {'backgroundColor': COLORS.get(color, COLORS['primary'])}
        
    if color in ['light', 'white']:
        text_color = "dark"
    
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.I(className=f"{icon} fa-2x mb-2", 
                          style={'opacity': '0.8'}),
                    html.P(title, className=f"text-{text_color} mb-1 small text-uppercase fw-bold"),
                    html.H3(value, className=f"text-{text_color} mb-0 fw-bold"),
                    html.P(subtitle, className=f"text-{text_color} mb-0 small", 
                          style={'opacity': '0.9'}) if subtitle else None
                ], width=12, className="text-center")
            ])
        ], className="py-4")
    ], className="h-100 border-0 shadow-sm metric-card-hover",
    style={**bg_style, 'transition': 'all 0.3s ease'})

def create_config_card(title, content, icon="fas fa-cog", color="light"):
    """
    Crea una tarjeta de configuración con header distintivo
    """
    return dbc.Card([
        dbc.CardHeader([
            html.I(className=f"{icon} me-2"),
            html.Span(title, className="fw-bold")
        ], className=f"bg-{color} border-0"),
        dbc.CardBody(content)
    ], className="mb-4 shadow-sm border-0")

def create_form_group(label, input_component, help_text="", icon=None):
    """
    Crea un grupo de formulario estilizado
    """
    label_content = [label]
    if icon:
        label_content = [html.I(className=f"{icon} me-2"), label]
    
    return html.Div([
        dbc.Label(label_content, className="fw-bold text-secondary"),
        input_component,
        dbc.FormText(help_text) if help_text else None
    ], className="mb-3")

def create_slider_with_value(id, min_val, max_val, step, value, marks, 
                           format_string="{}", unit="", color="primary"):
    """
    Crea un slider con display de valor mejorado
    """
    return html.Div([
        dcc.Slider(
            id=id,
            min=min_val,
            max=max_val,
            step=step,
            value=value,
            marks=marks,
            tooltip={"placement": "bottom", "always_visible": True},
            className=f"slider-{color}"
        ),
        html.Div([
            html.Span("Valor actual: ", className="text-muted"),
            html.Span(id=f"{id}-value", className="fw-bold text-primary"),
            html.Span(f" {unit}", className="text-muted") if unit else None
        ], className="text-center mt-2 small")
    ])

def create_scenario_card(scenario_data, index):
    """
    Crea una tarjeta para mostrar un escenario
    """
    status_color = "success" if scenario_data.get('calculated', False) else "warning"
    status_text = "Calculado" if scenario_data.get('calculated', False) else "Pendiente"
    
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5(scenario_data.get('name', f'Escenario {index}'), 
                           className="mb-0 fw-bold")
                ], width=8),
                dbc.Col([
                    dbc.Badge(status_text, color=status_color, className="float-end")
                ], width=4)
            ])
        ], className="bg-light"),
        dbc.CardBody([
            html.P([
                html.I(className="fas fa-map-marker-alt me-2 text-primary"),
                f"Cluster {scenario_data.get('cluster_id', 'N/A')}"
            ], className="mb-2"),
            html.P([
                html.I(className="fas fa-solar-panel me-2 text-warning"),
                f"PV: {scenario_data.get('pv_ratio', 0):.1f}x"
            ], className="mb-2"),
            html.P([
                html.I(className="fas fa-battery-full me-2 text-success"),
                f"BESS: {scenario_data.get('bess_hours', 0)}h"
            ], className="mb-2"),
            html.P([
                html.I(className="fas fa-bolt me-2 text-info"),
                f"Q: {scenario_data.get('q_ratio', 0):.0%}"
            ], className="mb-0")
        ])
    ], className="h-100 shadow-sm border-0 scenario-card-hover")

def create_sensitivity_chart(data, parameter_name, base_value):
    """
    Crea un gráfico de sensibilidad estilizado
    """
    fig = go.Figure()
    
    # Agregar línea de sensibilidad
    fig.add_trace(go.Scatter(
        x=data['variation'],
        y=data['npv'],
        mode='lines+markers',
        name='NPV',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=8, color=COLORS['primary']),
        hovertemplate='%{x:.0f}%: $%{y:.1f}M<extra></extra>'
    ))
    
    # Líneas de referencia
    fig.add_hline(y=base_value, line_dash="dash", line_color="gray", 
                  annotation_text="Caso Base")
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    
    # Áreas de color para zonas positivas/negativas
    fig.add_hrect(y0=0, y1=base_value*2, 
                  fillcolor="green", opacity=0.1, 
                  layer="below", line_width=0)
    fig.add_hrect(y0=-base_value, y1=0, 
                  fillcolor="red", opacity=0.1, 
                  layer="below", line_width=0)
    
    fig.update_layout(
        title=f"Sensibilidad del NPV a {parameter_name}",
        xaxis_title="Variación del Parámetro (%)",
        yaxis_title="NPV (MUSD)",
        template="plotly_white",
        hovermode='x unified',
        font=dict(family="system-ui, -apple-system, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_comparison_table(data, highlight_columns=None):
    """
    Crea una tabla de comparación estilizada
    """
    style_data_conditional = [
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgba(248, 249, 250, 0.5)'
        }
    ]
    
    if highlight_columns:
        for col in highlight_columns:
            style_data_conditional.append({
                'if': {'column_id': col},
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                'fontWeight': 'bold'
            })
    
    return {
        'style_cell': {
            'textAlign': 'center',
            'padding': '12px',
            'fontFamily': 'system-ui, -apple-system, sans-serif',
            'fontSize': '14px'
        },
        'style_header': {
            'backgroundColor': COLORS['primary'],
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        'style_data': {
            'backgroundColor': 'white',
            'color': 'black',
            'borderBottom': '1px solid #e5e7eb'
        },
        'style_data_conditional': style_data_conditional
    }

def create_alert_banner(message, type="info", dismissable=True):
    """
    Crea un banner de alerta estilizado
    """
    icon_map = {
        'info': 'fas fa-info-circle',
        'success': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'danger': 'fas fa-exclamation-circle'
    }
    
    return dbc.Alert([
        html.I(className=f"{icon_map.get(type, 'fas fa-info-circle')} me-2"),
        message
    ], color=type, dismissable=dismissable, className="shadow-sm border-0")

def create_loading_overlay():
    """
    Crea un overlay de carga estilizado
    """
    return dbc.Spinner([
        html.Div(className="p-5")
    ], color="primary", type="border", spinner_class_name="spinner-border-lg")

# Estilos CSS adicionales para incluir en app
OPTIMIZATION_STYLES = """
<style>
    /* Animaciones para cards */
    .metric-card-hover:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
    }
    
    .scenario-card-hover:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1) !important;
    }
    
    /* Sliders personalizados */
    .slider-primary .rc-slider-track {
        background-color: #3B82F6 !important;
    }
    
    .slider-primary .rc-slider-handle {
        border-color: #3B82F6 !important;
    }
    
    /* Inputs mejorados */
    .form-control:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 0.2rem rgba(59, 130, 246, 0.25);
    }
    
    /* Tabs personalizados */
    .nav-tabs .nav-link.active {
        color: #3B82F6;
        border-bottom: 3px solid #3B82F6;
    }
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
</style>
"""