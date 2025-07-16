"""
Componentes de tarjetas de métricas reutilizables
"""

import dash_bootstrap_components as dbc
from dash import html

def create_metric_card(title, value, subtitle_or_icon=None, color="primary", subtitle=None, icon=None, trend=None):
    """
    Crea una tarjeta de métrica con ícono y valor
    
    Args:
        title: Título de la métrica
        value: Valor principal a mostrar
        subtitle_or_icon: Puede ser subtitle (string normal) o icon (string con "fa-")
        color: Color del tema (primary, success, warning, danger, info)
        subtitle: Texto adicional debajo del valor (explícito)
        icon: Clase de ícono FontAwesome (explícito)
        trend: Dict con 'value' y 'direction' ('up' o 'down')
    """
    # Determinar si el tercer argumento es subtitle o icon
    if subtitle_or_icon:
        if isinstance(subtitle_or_icon, str) and ("fa-" in subtitle_or_icon or "fas " in subtitle_or_icon):
            # Es un ícono
            if not icon:
                icon = subtitle_or_icon
        else:
            # Es un subtitle
            if not subtitle:
                subtitle = subtitle_or_icon
    
    # Valores por defecto
    if not icon:
        icon = "fas fa-chart-line"
    if not subtitle:
        subtitle = ""
    # Colores de gradiente según el tema
    gradients = {
        "primary": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "success": "linear-gradient(135deg, #4ade80 0%, #16a34a 100%)",
        "warning": "linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)",
        "danger": "linear-gradient(135deg, #f87171 0%, #dc2626 100%)",
        "info": "linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)"
    }
    
    # Construir contenido de la card
    children_list = [
        html.I(className=f"{icon} fa-2x mb-3", style={"opacity": "0.8"}),
        html.H2(value, className="metric-value mb-1"),
        html.P(title, className="metric-label mb-0"),
    ]
    
    # Agregar subtítulo si existe
    if subtitle:
        children_list.append(
            html.Small(subtitle, className="d-block mt-2", style={"opacity": "0.9"})
        )
    
    # Agregar tendencia si existe
    if trend:
        trend_icon = "fa-arrow-up" if trend['direction'] == 'up' else "fa-arrow-down"
        trend_color = "text-success" if trend['direction'] == 'up' else "text-danger"
        children_list.append(
            html.Div([
                html.I(className=f"fas {trend_icon} me-1"),
                html.Span(trend['value'])
            ], className=f"{trend_color} mt-2 small")
        )
    
    return dbc.Card(
        dbc.CardBody(
            html.Div(children_list, className="text-center text-white")
        ),
        style={
            "background": gradients.get(color, gradients["primary"]),
            "border": "none",
            "borderRadius": "10px",
            "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
        },
        className="h-100"
    )

def create_summary_card(title, content, icon=None):
    """
    Crea una tarjeta de resumen con contenido personalizado
    
    Args:
        title: Título de la tarjeta
        content: Contenido HTML de la tarjeta
        icon: Ícono opcional para el título
    """
    header = [html.H5(title, className="mb-0")]
    if icon:
        header.insert(0, html.I(className=f"{icon} me-2"))
    
    return dbc.Card([
        dbc.CardHeader(header),
        dbc.CardBody(content)
    ], className="custom-card h-100")

def create_stats_row(stats_dict):
    """
    Crea una fila de estadísticas pequeñas
    
    Args:
        stats_dict: Diccionario con {label: value} para cada estadística
    """
    cols = []
    for label, value in stats_dict.items():
        cols.append(
            dbc.Col([
                html.Div([
                    html.H4(value, className="mb-0"),
                    html.Small(label, className="text-muted")
                ], className="text-center")
            ], xs=6, md=True)
        )
    
    return dbc.Row(cols, className="text-center")

def create_progress_card(title, items, icon="fas fa-tasks"):
    """
    Crea una tarjeta con barras de progreso
    
    Args:
        title: Título de la tarjeta
        items: Lista de dict con 'label', 'value', 'max' y opcionalmente 'color'
        icon: Ícono para el título
    """
    progress_bars = []
    for item in items:
        percentage = (item['value'] / item['max']) * 100
        color = item.get('color', 'primary')
        
        progress_bars.extend([
            html.Div([
                html.Span(item['label'], className="small"),
                html.Span(f"{item['value']:,} / {item['max']:,}", className="small float-end text-muted")
            ], className="d-flex justify-content-between mb-1"),
            dbc.Progress(
                value=percentage,
                color=color,
                className="mb-3",
                style={"height": "10px"}
            )
        ])
    
    return create_summary_card(
        title,
        html.Div(progress_bars),
        icon
    )

def create_alert_card(message, *, color="warning", icon=None, dismissable=True):
    """
    Crea una tarjeta de alerta
    
    Args:
        message: Mensaje de la alerta
        color: Color del tema (keyword-only)
        icon: Ícono opcional (keyword-only)
        dismissable: Si se puede cerrar (keyword-only)
    """
    content = []
    if icon:
        content.append(html.I(className=f"{icon} me-2"))
    content.append(html.Span(message))
    
    return dbc.Alert(
        content,
        color=color,
        dismissable=dismissable,
        className="d-flex align-items-center"
    )