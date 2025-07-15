"""
Fase 3 - Procesamiento de Datos (Versión Completa con 12 Tabs)
Análisis comprehensivo de datos del sistema eléctrico
"""

from dash import dcc, html, callback, Input, Output
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from dashboard.pages.utils import get_data_manager
from dashboard.pages.utils.constants import UI_COLORS

# Register page
dash.register_page(__name__, path='/fase3-datos', name='Fase 3: Datos', title='Procesamiento de Datos')

# Tab 1: Resumen General
def create_tab1_overview():
    """Tab 1: Resumen general del procesamiento."""
    dm = get_data_manager()
    summary_result = dm.get_comprehensive_summary()
    
    if not summary_result.data:
        return html.Div([
            dbc.Alert("Error cargando resumen de datos", color="danger"),
            html.Pre(str(summary_result.meta))
        ])
    
    summary = summary_result.data
    
    # Metric cards
    metric_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{summary['total_records']:,}", className="text-primary mb-0"),
                    html.P("Registros Procesados", className="mb-0"),
                    html.Small("🟢 DATO REAL", className="text-success")
                ])
            ], className="text-center h-100")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(str(len(summary['stations_processed'])), className="text-info mb-0"),
                    html.P("Estaciones", className="mb-0"),
                    html.Small(", ".join(summary['stations_processed']), className="text-muted")
                ])
            ], className="text-center h-100")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{summary['date_ranges']['Pilcaniyeu']['days']} días", className="text-warning mb-0"),
                    html.P("Período Total", className="mb-0"),
                    html.Small("Enero-Octubre 2024", className="text-muted")
                ])
            ], className="text-center h-100")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("100%", className="text-danger mb-0"),
                    html.P("Fuera de Límites", className="mb-0"),
                    html.Small("V < 0.95 pu", className="text-danger")
                ])
            ], className="text-center h-100")
        ], md=3)
    ], className="mb-4")
    
    # Date ranges table
    date_df = pd.DataFrame([
        {
            'Estación': station,
            'Inicio': pd.to_datetime(data['start']).strftime('%Y-%m-%d'),
            'Fin': pd.to_datetime(data['end']).strftime('%Y-%m-%d'),
            'Días': data['days'],
            'Registros': f"{data['records']:,}"
        }
        for station, data in summary['date_ranges'].items()
    ])
    
    date_table = dbc.Table.from_dataframe(
        date_df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True
    )
    
    return html.Div([
        html.H4("Resumen General del Procesamiento", className="mb-3"),
        metric_cards,
        
        dbc.Card([
            dbc.CardHeader("Rangos de Datos por Estación"),
            dbc.CardBody([
                date_table,
                html.Small([
                    "Procesamiento completado: ",
                    html.Span(pd.to_datetime(summary['generated_at']).strftime('%Y-%m-%d %H:%M'), 
                            className="fw-bold")
                ], className="text-muted")
            ])
        ])
    ])

# Tab 2: Calidad de Datos
def create_tab2_quality():
    """Tab 2: Métricas de calidad de datos."""
    dm = get_data_manager()
    quality_result = dm.get_enhanced_quality_metrics()
    
    if not quality_result.data:
        return html.Div([
            dbc.Alert("Error cargando métricas de calidad", color="danger")
        ])
    
    quality = quality_result.data
    
    # Check if data has the expected structure
    if 'by_station' in quality:
        station_data = quality['by_station']
    else:
        station_data = quality
    
    # Create quality metrics table
    quality_data = []
    for station, metrics in station_data.items():
        if isinstance(metrics, dict) and 'voltage_quality' in metrics:
            quality_data.append({
                'Estación': station,
                'V Promedio (pu)': f"{metrics['voltage_quality']['avg_voltage_pu']:.3f}",
                'V Mínimo (pu)': f"{metrics['voltage_quality']['min_voltage_pu']:.3f}",
                'V Máximo (pu)': f"{metrics['voltage_quality']['max_voltage_pu']:.3f}",
                'Dentro Límites': f"{metrics['voltage_quality'].get('within_limits_pct', 0):.1f}%",
                'P Promedio (MW)': f"{metrics.get('power_stats', {}).get('avg_power_mw', 0):.2f}",
                'FP Promedio': f"{metrics.get('power_stats', {}).get('avg_power_factor', 0):.3f}"
            })
    
    quality_df = pd.DataFrame(quality_data)
    
    # Create voltage quality visualization
    fig = go.Figure()
    
    # Filter out non-dict entries and get valid stations
    valid_stations = [s for s in station_data.keys() if isinstance(station_data[s], dict) and 'voltage_quality' in station_data[s]]
    
    if not valid_stations:
        return html.Div([
            html.H4("Métricas de Calidad de Datos", className="mb-3"),
            dbc.Alert("No hay datos de calidad disponibles para visualizar", color="warning")
        ])
    
    stations = valid_stations
    avg_voltages = [station_data[s]['voltage_quality']['avg_voltage_pu'] for s in stations]
    min_voltages = [station_data[s]['voltage_quality']['min_voltage_pu'] for s in stations]
    max_voltages = [station_data[s]['voltage_quality']['max_voltage_pu'] for s in stations]
    
    fig.add_trace(go.Bar(
        name='V Promedio',
        x=stations,
        y=avg_voltages,
        marker_color=UI_COLORS['voltage_measured']
    ))
    
    # Add min/max as error bars
    fig.add_trace(go.Scatter(
        name='V Mínimo',
        x=stations,
        y=min_voltages,
        mode='markers',
        marker=dict(symbol='diamond', size=10, color=UI_COLORS['danger'])
    ))
    
    fig.add_trace(go.Scatter(
        name='V Máximo',
        x=stations,
        y=max_voltages,
        mode='markers',
        marker=dict(symbol='triangle-up', size=10, color=UI_COLORS['success'])
    ))
    
    fig.add_hline(y=0.95, line_dash="dash", line_color=UI_COLORS['voltage_limit'],
                 annotation_text="Límite inferior (0.95 pu)")
    
    fig.update_layout(
        title="Calidad de Tensión por Estación",
        xaxis_title="Estación",
        yaxis_title="Tensión (pu)",
        yaxis_range=[0, 1.1],
        height=400,
        template="plotly_white",
        showlegend=True
    )
    
    return html.Div([
        html.H4("Métricas de Calidad de Datos", className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Resumen de Calidad por Estación"),
                    dbc.CardBody([
                        dbc.Table.from_dataframe(
                            quality_df,
                            striped=True,
                            bordered=True,
                            hover=True,
                            responsive=True,
                            size='sm'
                        )
                    ])
                ])
            ], md=12)
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig, config={'displayModeBar': False})
            ])
        ]),
        
        dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "100% de las mediciones están fuera de los límites regulatorios (< 0.95 pu). ",
            "El sistema opera en condiciones críticas permanentes."
        ], color="danger", className="mt-3")
    ])

# Tab 3: Patrones Temporales
def create_tab3_temporal():
    """Tab 3: Análisis de patrones temporales."""
    dm = get_data_manager()
    temporal_result = dm.get_temporal_patterns_full()
    
    if not temporal_result.data:
        return html.Div([
            dbc.Alert("Error cargando patrones temporales", color="danger")
        ])
    
    temporal = temporal_result.data
    
    # Check for by_station key
    if 'by_station' not in temporal:
        return html.Div([
            dbc.Alert("Estructura de datos incorrecta: falta 'by_station'", color="danger")
        ])
    
    # Create hourly demand profile
    fig_hourly = go.Figure()
    
    try:
        for station in temporal['by_station']:
            station_data = temporal['by_station'][station]
            if 'hourly_profile' in station_data and 'p_total' in station_data['hourly_profile']:
                hourly_data = station_data['hourly_profile']['p_total']['mean']
                hours = list(range(24))
                values = [hourly_data[str(h)] for h in hours]
                
                fig_hourly.add_trace(go.Scatter(
                    x=hours,
                    y=values,
                    mode='lines+markers',
                    name=station,
                    line=dict(width=2)
                ))
    except Exception as e:
        print(f"Error creating hourly profile: {e}")
        import traceback
        traceback.print_exc()
    
    fig_hourly.update_layout(
        title="Perfil Horario de Demanda",
        xaxis_title="Hora del día",
        yaxis_title="Potencia (MW)",
        xaxis=dict(tickmode='linear', tick0=0, dtick=2),
        height=400,
        template="plotly_white",
        hovermode='x unified'
    )
    
    # Add peak hours shading
    fig_hourly.add_vrect(x0=18, x1=23, fillcolor="rgba(255,0,0,0.1)",
                        annotation_text="Horas pico", annotation_position="top")
    
    # Weekly patterns
    weekly_stats = []
    for station in temporal['by_station']:
        station_data = temporal['by_station'][station]
        if 'day_of_week_patterns' in station_data and 'weekend_reduction' in station_data:
            dow_patterns = station_data['day_of_week_patterns']
            weekend_data = station_data['weekend_reduction']
            
            # Check if p_total exists in day_of_week_patterns
            if 'p_total' in dow_patterns:
                p_total_by_day = dow_patterns['p_total']
                
                # Calculate weekday average (Monday=0 to Friday=4)
                weekday_avg = sum(p_total_by_day.get(str(i), 0) for i in range(5)) / 5
                # Calculate weekend average (Saturday=5, Sunday=6)
                weekend_avg = sum(p_total_by_day.get(str(i), 0) for i in range(5, 7)) / 2
                
                # weekend_data is a float representing the reduction percentage
                reduction_pct = weekend_data * 100 if isinstance(weekend_data, (int, float)) else 0
                
                weekly_stats.append({
                    'Estación': station,
                    'P Laborable (MW)': f"{weekday_avg:.2f}",
                    'P Fin de Semana (MW)': f"{weekend_avg:.2f}",
                    'Reducción FDS': f"{reduction_pct:.1f}%"
                })
    
    weekly_df = pd.DataFrame(weekly_stats) if weekly_stats else pd.DataFrame()
    
    # Monthly evolution
    fig_monthly = go.Figure()
    
    for station in temporal['by_station']:
        if 'monthly_patterns' in temporal['by_station'][station]:
            monthly = temporal['by_station'][station]['monthly_patterns']
            # Check if p_total exists
            if 'p_total' in monthly:
                p_total_by_month = monthly['p_total']
                months = list(p_total_by_month.keys())
                values = [p_total_by_month[m] for m in months]
                
                # Convert month numbers to names
                month_names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                              'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
                month_labels = [month_names[int(m)-1] if int(m) <= 12 else m for m in months]
                
                fig_monthly.add_trace(go.Bar(
                    name=station,
                    x=month_labels,
                    y=values
                ))
    
    fig_monthly.update_layout(
        title="Evolución Mensual de Demanda",
        xaxis_title="Mes",
        yaxis_title="Demanda Promedio (MW)",
        height=350,
        template="plotly_white",
        barmode='group'
    )
    
    return html.Div([
        html.H4("Análisis de Patrones Temporales", className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=fig_hourly, config={'displayModeBar': False})
                    ])
                ])
            ], md=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Patrones Semanales"),
                    dbc.CardBody([
                        dbc.Table.from_dataframe(
                            weekly_df,
                            striped=True,
                            bordered=True,
                            hover=True,
                            responsive=True
                        ) if not weekly_df.empty else html.P("No hay datos semanales disponibles")
                    ])
                ])
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=fig_monthly, config={'displayModeBar': False})
                    ])
                ])
            ], md=6)
        ])
    ])

# Tab 4: Correlaciones
def create_tab4_correlations():
    """Tab 4: Análisis de correlaciones entre estaciones."""
    dm = get_data_manager()
    corr_result = dm.get_correlations()
    
    if not corr_result.data:
        return html.Div([
            dbc.Alert("Error cargando correlaciones", color="danger")
        ])
    
    corr_data = corr_result.data
    
    # Check data structure
    if 'correlations' not in corr_data:
        return html.Div([
            html.H4("Análisis de Correlaciones", className="mb-3"),
            dbc.Alert("Estructura de datos incorrecta", color="warning")
        ])
    
    # Get voltage correlations from the correct path
    correlations = corr_data['correlations']
    v_corr = correlations.get('voltage_pearson', {}).get('matrix', {})
    
    if not v_corr:
        return html.Div([
            html.H4("Análisis de Correlaciones", className="mb-3"),
            dbc.Alert("No hay datos de correlaciones de voltaje disponibles", color="warning")
        ])
    
    stations = list(v_corr.keys())
    
    # Create correlation matrix
    corr_matrix = []
    for s1 in stations:
        row = []
        for s2 in stations:
            if s1 == s2:
                row.append(1.0)
            elif s2 in v_corr[s1]:
                row.append(v_corr[s1][s2])
            elif s1 in v_corr.get(s2, {}):
                row.append(v_corr[s2][s1])
            else:
                row.append(0)
        corr_matrix.append(row)
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=stations,
        y=stations,
        colorscale='RdBu',
        zmid=0,
        text=[[f"{val:.2f}" for val in row] for row in corr_matrix],
        texttemplate="%{text}",
        textfont={"size": 10},
        colorbar=dict(title="Correlación")
    ))
    
    fig_heatmap.update_layout(
        title="Correlación de Tensiones entre Estaciones",
        height=500,
        template="plotly_white"
    )
    
    # Power-Voltage correlation scatter
    pv_scatter_data = []
    
    # Get P-V correlation data from the dedicated file
    pv_result = dm.get_demand_voltage_correlation()
    if pv_result.data and 'correlations' in pv_result.data:
        pv_corr_data = pv_result.data['correlations']
        
        for station in stations:
            if station in pv_corr_data and isinstance(pv_corr_data[station], dict):
                pv_corr = pv_corr_data[station]
                if 'overall' in pv_corr:
                    pv_scatter_data.append({
                        'Estación': station,
                        'Correlación P-V': pv_corr['overall'],
                        'Sensibilidad dV/dP': pv_corr.get('sensitivity_dv_dp', 0)
                    })
    
    if pv_scatter_data:
        pv_df = pd.DataFrame(pv_scatter_data)
        
        fig_pv = go.Figure()
        fig_pv.add_trace(go.Bar(
            x=pv_df['Estación'],
            y=pv_df['Sensibilidad dV/dP'],
            name='Sensibilidad dV/dP (pu/MW)',
            marker_color=UI_COLORS['primary']
        ))
        
        fig_pv.update_layout(
            title="Sensibilidad Tensión-Potencia por Estación",
            xaxis_title="Estación",
            yaxis_title="dV/dP (pu/MW)",
            height=350,
            template="plotly_white"
        )
    
    return html.Div([
        html.H4("Análisis de Correlaciones", className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=fig_heatmap, config={'displayModeBar': False})
                    ])
                ])
            ], md=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Interpretación"),
                    dbc.CardBody([
                        html.P("Correlaciones de tensión entre estaciones:"),
                        html.Ul([
                            html.Li("Valores cercanos a 1: Fuerte correlación positiva"),
                            html.Li("Valores cercanos a 0: Sin correlación"),
                            html.Li("Valores negativos: Correlación inversa")
                        ]),
                        html.Hr(),
                        html.P([
                            "La alta correlación (>0.8) entre estaciones indica que ",
                            "los problemas de tensión se propagan por toda la línea."
                        ], className="text-muted")
                    ])
                ])
            ], md=4)
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig_pv, config={'displayModeBar': False}) if pv_scatter_data else 
                html.P("No hay datos de correlación P-V disponibles")
            ])
        ])
    ])

# Tab 5: Análisis Horario
def create_tab5_hourly():
    """Tab 5: Análisis detallado por hora."""
    dm = get_data_manager()
    hourly_result = dm.get_hourly_voltage_analysis()
    
    if not hourly_result.data:
        return html.Div([
            dbc.Alert("Error cargando análisis horario", color="danger")
        ])
    
    hourly = hourly_result.data
    
    # Check data structure
    if 'hourly_stats' not in hourly:
        return html.Div([
            dbc.Alert("Estructura de datos incorrecta en análisis horario", color="danger")
        ])
    
    hourly_stats = hourly['hourly_stats']
    
    # Create voltage heatmap by hour and station
    stations = list(hourly_stats.keys())
    hours = list(range(24))
    
    # Prepare data for heatmap
    voltage_matrix = []
    for hour in hours:
        row = []
        for station in stations:
            if str(hour) in hourly_stats[station]:
                # The data has 'mean' not 'avg_voltage'
                row.append(hourly_stats[station][str(hour)]['mean'])
            else:
                row.append(0)
        voltage_matrix.append(row)
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=voltage_matrix,
        x=stations,
        y=[f"{h:02d}:00" for h in hours],
        colorscale='RdYlBu',
        zmid=0.95,
        colorbar=dict(title="Tensión (pu)"),
        text=[[f"{val:.2f}" for val in row] for row in voltage_matrix],
        texttemplate="%{text}",
        textfont={"size": 8}
    ))
    
    fig_heatmap.update_layout(
        title="Mapa de Calor: Tensión por Hora y Estación",
        xaxis_title="Estación",
        yaxis_title="Hora del día",
        height=600,
        template="plotly_white"
    )
    
    # Violations by hour
    violations_by_hour = {}
    for hour in hours:
        count = 0
        for station in stations:
            if str(hour) in hourly_stats[station]:
                # Check if there are violations
                if hourly_stats[station][str(hour)].get('violations', 0) > 0:
                    count += 1
        violations_by_hour[hour] = count
    
    fig_violations = go.Figure()
    fig_violations.add_trace(go.Bar(
        x=list(violations_by_hour.keys()),
        y=list(violations_by_hour.values()),
        marker_color=['red' if h >= 18 and h <= 23 else 'orange' for h in violations_by_hour.keys()]
    ))
    
    fig_violations.update_layout(
        title="Estaciones con Violaciones por Hora",
        xaxis_title="Hora del día",
        yaxis_title="Número de estaciones con V < 0.95 pu",
        height=300,
        template="plotly_white"
    )
    
    return html.Div([
        html.H4("Análisis Horario de Tensiones", className="mb-3"),
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig_heatmap, config={'displayModeBar': False})
            ])
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig_violations, config={'displayModeBar': False})
            ])
        ]),
        
        dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Las horas 18-23 (pico) muestran las peores condiciones de tensión en todas las estaciones."
        ], color="info", className="mt-3")
    ])

# Tab 6: Sensibilidad V-P
def create_tab6_sensitivity():
    """Tab 6: Análisis de sensibilidad tensión-potencia."""
    dm = get_data_manager()
    pv_result = dm.get_demand_voltage_correlation()
    
    if not pv_result.data:
        return html.Div([
            dbc.Alert("Error cargando correlación P-V", color="danger")
        ])
    
    pv_data = pv_result.data
    
    # Check data structure
    if 'correlations' not in pv_data:
        return html.Div([
            html.H4("Análisis de Sensibilidad Tensión-Potencia", className="mb-3"),
            dbc.Alert("Estructura de datos incorrecta", color="warning")
        ])
    
    # Sensitivity bar chart
    stations = []
    sensitivities = []
    correlations = []
    
    corr_data = pv_data['correlations']
    for station, data in corr_data.items():
        if isinstance(data, dict) and 'sensitivity_dv_dp' in data and 'overall' in data:
            stations.append(station)
            sensitivities.append(data['sensitivity_dv_dp'])
            correlations.append(data['overall'])
    
    if not stations:
        return html.Div([
            html.H4("Análisis de Sensibilidad Tensión-Potencia", className="mb-3"),
            dbc.Alert("No hay datos de sensibilidad P-V disponibles", color="warning")
        ])
    
    fig_sensitivity = go.Figure()
    fig_sensitivity.add_trace(go.Bar(
        x=stations,
        y=sensitivities,
        name='Sensibilidad dV/dP',
        marker_color=UI_COLORS['primary'],
        text=[f"{s:.3f}" for s in sensitivities],
        textposition='outside'
    ))
    
    fig_sensitivity.update_layout(
        title="Sensibilidad dV/dP por Estación",
        xaxis_title="Estación",
        yaxis_title="dV/dP (pu/MW)",
        height=400,
        template="plotly_white"
    )
    
    # Correlation quality
    fig_corr = go.Figure()
    fig_corr.add_trace(go.Scatter(
        x=stations,
        y=correlations,
        mode='markers+lines',
        marker=dict(size=12, color=UI_COLORS['success']),
        line=dict(width=2),
        name='Correlación P-V'
    ))
    
    fig_corr.update_layout(
        title="Calidad de Correlación P-V",
        xaxis_title="Estación",
        yaxis_title="Coeficiente de Correlación",
        yaxis_range=[-1, 0],
        height=350,
        template="plotly_white"
    )
    
    # Impact table
    impact_data = []
    for station, sens in zip(stations, sensitivities):
        impact_data.append({
            'Estación': station,
            'Sensibilidad': f"{sens:.3f} pu/MW",
            'Impacto 1 MW': f"{abs(sens)*100:.1f}%",
            'Impacto 2 MW': f"{abs(sens)*200:.1f}%",
            'Impacto 3 MW': f"{abs(sens)*300:.1f}%"
        })
    
    impact_df = pd.DataFrame(impact_data)
    
    return html.Div([
        html.H4("Análisis de Sensibilidad Tensión-Potencia", className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=fig_sensitivity, config={'displayModeBar': False})
                    ])
                ])
            ], md=7),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Impacto de GD en Tensión"),
                    dbc.CardBody([
                        dbc.Table.from_dataframe(
                            impact_df,
                            striped=True,
                            bordered=True,
                            hover=True,
                            responsive=True,
                            size='sm'
                        ),
                        html.Small([
                            "Valores negativos indican que aumentar potencia reduce tensión. ",
                            "Maquinchao muestra la mayor sensibilidad."
                        ], className="text-muted mt-2")
                    ])
                ])
            ], md=5)
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig_corr, config={'displayModeBar': False})
            ])
        ])
    ])

# Tab 7: Eventos Críticos
def create_tab7_critical():
    """Tab 7: Análisis de eventos críticos."""
    dm = get_data_manager()
    events_result = dm.get_critical_events_analysis()
    
    if not events_result.data:
        return html.Div([
            dbc.Alert("Error cargando eventos críticos", color="danger")
        ])
    
    events = events_result.data
    
    # Check data structure
    if 'critical_events' not in events:
        return html.Div([
            html.H4("Análisis de Eventos Críticos", className="mb-3"),
            dbc.Alert("Estructura de datos incorrecta", color="warning")
        ])
    
    critical_events = events['critical_events']
    
    # Calculate summary from station data
    total_events = 0
    total_hours = 0
    max_duration = 0
    all_durations = []
    
    for station, data in critical_events.items():
        if isinstance(data, dict) and 'events_below_0.5pu' in data:
            station_events = data['events_below_0.5pu']
            total_events += station_events.get('count', 0)
            total_hours += station_events.get('total_duration_hours', 0)
            max_duration = max(max_duration, station_events.get('max_duration_hours', 0))
            if station_events.get('count', 0) > 0:
                all_durations.append(station_events.get('avg_duration_hours', 0))
    
    avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0
    
    # Summary metrics
    metric_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(str(total_events), className="text-danger mb-0"),
                    html.P("Eventos Críticos Totales", className="mb-0"),
                    html.Small("V < 0.5 pu por > 15 min", className="text-muted")
                ])
            ], className="text-center")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{max_duration:.1f}h", className="text-warning mb-0"),
                    html.P("Duración Máxima", className="mb-0"),
                    html.Small("Evento más largo", className="text-muted")
                ])
            ], className="text-center")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{avg_duration:.1f}h", className="text-info mb-0"),
                    html.P("Duración Promedio", className="mb-0"),
                    html.Small("Por evento", className="text-muted")
                ])
            ], className="text-center")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{total_hours:.0f}h", className="text-primary mb-0"),
                    html.P("Horas Críticas Totales", className="mb-0"),
                    html.Small("En período analizado", className="text-muted")
                ])
            ], className="text-center")
        ], md=3)
    ], className="mb-4")
    
    # Events by station
    station_events = []
    for station, data in critical_events.items():
        if isinstance(data, dict) and 'events_below_0.5pu' in data:
            event_data = data['events_below_0.5pu']
            station_events.append({
                'station': station,
                'count': event_data.get('count', 0),
                'total_hours': event_data.get('total_duration_hours', 0),
                'avg_duration': event_data.get('avg_duration_hours', 0)
            })
    
    df_events = pd.DataFrame(station_events)
    
    fig_events = go.Figure()
    fig_events.add_trace(go.Bar(
        x=df_events['station'],
        y=df_events['count'],
        name='Número de Eventos',
        marker_color=UI_COLORS['danger'],
        yaxis='y'
    ))
    
    fig_events.add_trace(go.Scatter(
        x=df_events['station'],
        y=df_events['total_hours'],
        name='Horas Totales',
        mode='lines+markers',
        marker=dict(size=10),
        line=dict(width=3),
        yaxis='y2'
    ))
    
    fig_events.update_layout(
        title="Eventos Críticos por Estación",
        xaxis_title="Estación",
        yaxis=dict(title="Número de Eventos", side='left'),
        yaxis2=dict(title="Horas Totales", side='right', overlaying='y'),
        height=400,
        template="plotly_white",
        hovermode='x unified'
    )
    
    return html.Div([
        html.H4("Análisis de Eventos Críticos", className="mb-3"),
        metric_cards,
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig_events, config={'displayModeBar': False})
            ])
        ], className="mb-4"),
        
        dbc.Alert([
            html.H5("Definición de Evento Crítico", className="alert-heading"),
            html.P([
                "Un evento crítico se define como un período donde la tensión cae por debajo de ",
                html.Strong("0.5 pu (50% del nominal)"),
                " durante más de ",
                html.Strong("15 minutos consecutivos"),
                ". Estos eventos representan condiciones operativas extremadamente peligrosas."
            ]),
            html.Hr(),
            html.P([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Se detectaron {total_events} eventos críticos, ",
                f"totalizando {total_hours:.0f} horas de operación crítica."
            ], className="mb-0")
        ], color="danger")
    ])

# Tab 8: Rampas de Demanda
def create_tab8_ramps():
    """Tab 8: Análisis de rampas de demanda."""
    dm = get_data_manager()
    ramps_result = dm.get_demand_ramps_analysis()
    
    if not ramps_result.data:
        return html.Div([
            dbc.Alert("Error cargando análisis de rampas", color="danger")
        ])
    
    ramps = ramps_result.data
    
    # Check if data has the expected structure
    if 'ramp_analysis' in ramps:
        ramps = ramps['ramp_analysis']
    elif 'available' in ramps:
        # Data might be wrapped in a structure
        actual_ramps = {}
        for key, value in ramps.items():
            if key not in ['available', 'generated_at'] and isinstance(value, dict):
                actual_ramps[key] = value
        ramps = actual_ramps if actual_ramps else ramps
    
    # Ramp statistics table
    ramp_stats = []
    for station, data in ramps.items():
        if isinstance(data, dict) and 'overall_stats' in data:
            stats = data['overall_stats']
            ramp_stats.append({
                'Estación': station,
                'Rampa Máx (+)': f"{stats['max_ramp_up']:.3f} MW/h",
                'Rampa Máx (-)': f"{stats['max_ramp_down']:.3f} MW/h",
                'Promedio (+)': f"{stats.get('avg_ramp_up', stats.get('avg_ramp_magnitude', 0)):.3f} MW/h",
                'Promedio (-)': f"{stats.get('avg_ramp_down', -stats.get('avg_ramp_magnitude', 0)):.3f} MW/h",
                'P95 (+)': f"{stats['p95_ramp_up']:.3f} MW/h"
            })
    
    ramp_df = pd.DataFrame(ramp_stats)
    
    # Ramp distribution visualization
    fig_ramps = go.Figure()
    
    for station in ramps:
        if isinstance(ramps[station], dict) and 'hourly_ramps' in ramps[station]:
            hourly = ramps[station]['hourly_ramps']
            hours = list(range(24))
            # Use 'mean' instead of 'avg_ramp'
            avg_ramps = [hourly.get(str(h), {}).get('mean', 0) for h in hours]
            
            fig_ramps.add_trace(go.Scatter(
                x=hours,
                y=avg_ramps,
                mode='lines+markers',
                name=station,
                line=dict(width=2)
            ))
    
    fig_ramps.update_layout(
        title="Rampas Promedio por Hora del Día",
        xaxis_title="Hora",
        yaxis_title="Rampa Promedio (MW/h)",
        xaxis=dict(tickmode='linear', tick0=0, dtick=2),
        height=400,
        template="plotly_white",
        hovermode='x unified'
    )
    
    # Add critical ramp zones
    fig_ramps.add_hline(y=0.5, line_dash="dash", line_color="orange",
                       annotation_text="Rampa moderada")
    fig_ramps.add_hline(y=1.0, line_dash="dash", line_color="red",
                       annotation_text="Rampa alta")
    
    return html.Div([
        html.H4("Análisis de Rampas de Demanda", className="mb-3"),
        
        dbc.Card([
            dbc.CardHeader("Estadísticas de Rampas por Estación"),
            dbc.CardBody([
                dbc.Table.from_dataframe(
                    ramp_df,
                    striped=True,
                    bordered=True,
                    hover=True,
                    responsive=True,
                    size='sm'
                ),
                html.Small([
                    "Rampas positivas indican aumento de demanda, negativas indican reducción. ",
                    "P95 representa el percentil 95 de las rampas."
                ], className="text-muted")
            ])
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig_ramps, config={'displayModeBar': False})
            ])
        ]),
        
        dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Las rampas máximas de hasta 1 MW/h requieren sistemas de respuesta rápida. ",
            "BESS debe poder responder en menos de 5 minutos para cubrir estas variaciones."
        ], color="info", className="mt-3")
    ])

# Tab 9: Curvas de Duración
def create_tab9_duration():
    """Tab 9: Curvas de duración de carga."""
    dm = get_data_manager()
    duration_result = dm.get_load_duration_curves()
    
    if not duration_result.data:
        return html.Div([
            dbc.Alert("Error cargando curvas de duración", color="danger")
        ])
    
    duration = duration_result.data
    
    # Check data structure
    if 'duration_curves' in duration:
        duration = duration['duration_curves']
    
    # Create duration curves
    fig = go.Figure()
    num_points = 0  # To track number of points for x-axis
    
    for station, data in duration.items():
        if isinstance(data, dict) and 'demand_curve' in data:
            demand_curve = data['demand_curve']
            if 'percentages' in demand_curve and 'values' in demand_curve:
                x_values = demand_curve['percentages']
                y_values = demand_curve['values']
                
                # Sort by values (descending) to create duration curve
                sorted_pairs = sorted(zip(y_values, x_values), reverse=True)
                y_sorted, x_sorted = zip(*sorted_pairs)
                
                num_points = len(x_sorted)
                
                fig.add_trace(go.Scatter(
                    x=list(range(len(x_sorted))),
                    y=y_sorted,
                    mode='lines',
                    name=station,
                    line=dict(width=2),
                    hovertemplate='%{y:.2f} MW<br>%{customdata:.0f}% del tiempo<extra></extra>',
                    customdata=x_sorted
                ))
    
    if num_points > 0:
        fig.update_layout(
            title="Curvas de Duración de Carga",
            xaxis_title="Porcentaje del tiempo (%)",
            yaxis_title="Potencia (MW)",
            xaxis=dict(
                tickmode='array',
                tickvals=[0, num_points*0.1, num_points*0.5, num_points*0.9, num_points-1],
                ticktext=['0%', '10%', '50%', '90%', '100%']
            ),
        height=500,
        template="plotly_white",
        hovermode='x unified'
    )
    
    # Key percentiles table
    percentile_data = []
    for station, data in duration.items():
        if isinstance(data, dict) and 'demand_curve' in data:
            dc = data['demand_curve']
            values = dc.get('values', [])
            if values:
                sorted_values = sorted(values, reverse=True)
                n = len(sorted_values)
                
                # Get capacity factor from statistics if available
                capacity_factor = 0
                if 'statistics' in data:
                    capacity_factor = data['statistics'].get('capacity_factor', 0)
                
                percentile_data.append({
                    'Estación': station,
                    'P10 (MW)': f"{sorted_values[int(n*0.1)]:.2f}" if n > 10 else "N/A",
                    'P50 (MW)': f"{sorted_values[int(n*0.5)]:.2f}" if n > 2 else "N/A",
                    'P90 (MW)': f"{sorted_values[int(n*0.9)]:.2f}" if n > 10 else "N/A",
                    'P95 (MW)': f"{sorted_values[int(n*0.95)]:.2f}" if n > 20 else "N/A",
                    'P99 (MW)': f"{sorted_values[int(n*0.99)]:.2f}" if n > 100 else "N/A",
                    'Factor Carga': f"{capacity_factor:.2f}"
                })
    
    percentile_df = pd.DataFrame(percentile_data)
    
    return html.Div([
        html.H4("Curvas de Duración de Carga", className="mb-3"),
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig, config={'displayModeBar': False})
            ])
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardHeader("Percentiles Clave de Demanda"),
            dbc.CardBody([
                dbc.Table.from_dataframe(
                    percentile_df,
                    striped=True,
                    bordered=True,
                    hover=True,
                    responsive=True
                ),
                html.Small([
                    "P10: Demanda superada el 10% del tiempo (pico). ",
                    "P50: Demanda mediana. ",
                    "P90: Demanda base (90% del tiempo)."
                ], className="text-muted")
            ])
        ])
    ])

# Tab 10: Días Típicos
def create_tab10_typical():
    """Tab 10: Perfiles de días típicos - TODAS las estaciones."""
    dm = get_data_manager()
    typical_result = dm.get_typical_days_profiles()
    
    if not typical_result.data:
        return html.Div([
            dbc.Alert("Error cargando días típicos", color="danger")
        ])
    
    typical = typical_result.data
    
    # Check data structure
    if 'typical_days' in typical:
        typical = typical['typical_days']
    
    # Create content for all stations, one below the other
    stations = list(typical.keys())
    all_stations_content = []
    
    # Add header
    all_stations_content.extend([
        html.H4("Perfiles de Días Típicos - Todas las Estaciones", className="mb-3"),
        
        dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Análisis de días típicos mostrando patrones de demanda por tipo de día (laboral, fin de semana, verano, invierno) para TODAS las estaciones del sistema."
        ], color="info", className="mb-3")
    ])
    
    # Add each station's content
    for i, station in enumerate(stations):
        # Add separator between stations (except for the first one)
        if i > 0:
            all_stations_content.append(html.Hr(className="my-4"))
        
        # Add station content
        all_stations_content.append(
            html.Div([
                html.H5(f"Estación: {station}", className="text-primary mb-3"),
                create_typical_day_plot(station, typical)
            ])
        )
    
    return html.Div(all_stations_content)

# Tab 11: Hallazgos Críticos
def create_tab11_findings():
    """Tab 11: Resumen de hallazgos críticos."""
    findings = [
        {
            'category': 'Tensión',
            'finding': 'Colapso de tensión permanente',
            'detail': '100% del tiempo V < 0.95 pu. Promedio 0.42 pu (58% caída)',
            'impact': 'Sistema operando fuera de especificación',
            'severity': 'critical'
        },
        {
            'category': 'Tensión',
            'finding': 'Caída extrema en fin de línea',
            'detail': 'Los Menucos: 76% caída promedio (0.237 pu)',
            'impact': 'Equipos en riesgo de daño permanente',
            'severity': 'critical'
        },
        {
            'category': 'Eventos',
            'finding': '547 eventos críticos detectados',
            'detail': 'V < 0.5 pu por más de 15 minutos',
            'impact': 'Riesgo de colapso total del sistema',
            'severity': 'critical'
        },
        {
            'category': 'Sensibilidad',
            'finding': 'Alta sensibilidad dV/dP',
            'detail': 'Hasta -0.112 pu/MW en Maquinchao',
            'impact': 'Pequeños cambios generan grandes efectos',
            'severity': 'high'
        },
        {
            'category': 'Rampas',
            'finding': 'Rampas de hasta 1 MW/h',
            'detail': 'Cambios rápidos en demanda',
            'impact': 'Requiere respuesta < 5 minutos',
            'severity': 'high'
        },
        {
            'category': 'Patrones',
            'finding': 'Pico nocturno 20-22h',
            'detail': 'Demanda 2x mayor que promedio diario',
            'impact': 'Sin generación solar disponible',
            'severity': 'medium'
        },
        {
            'category': 'Correlación',
            'finding': 'Alta correlación entre estaciones',
            'detail': 'Correlación > 0.8 en tensiones',
            'impact': 'Problemas se propagan por toda la línea',
            'severity': 'medium'
        },
        {
            'category': 'Positivo',
            'finding': 'Factor de potencia adecuado',
            'detail': 'FP promedio 0.964',
            'impact': 'No requiere compensación reactiva',
            'severity': 'low'
        }
    ]
    
    # Group findings by severity
    critical_findings = [f for f in findings if f['severity'] == 'critical']
    high_findings = [f for f in findings if f['severity'] == 'high']
    medium_findings = [f for f in findings if f['severity'] == 'medium']
    low_findings = [f for f in findings if f['severity'] == 'low']
    
    def create_finding_card(finding):
        color_map = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'success'
        }
        
        return dbc.Card([
            dbc.CardBody([
                html.H6(finding['finding'], className="card-title"),
                html.P(finding['detail'], className="card-text"),
                html.Small([
                    html.I(className="fas fa-arrow-right me-2"),
                    finding['impact']
                ], className="text-muted")
            ])
        ], color=color_map[finding['severity']], outline=True, className="mb-2")
    
    return html.Div([
        html.H4("Resumen de Hallazgos Críticos", className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.H5("🔴 Críticos", className="text-danger mb-3"),
                *[create_finding_card(f) for f in critical_findings]
            ], md=6),
            
            dbc.Col([
                html.H5("🟡 Alta Prioridad", className="text-warning mb-3"),
                *[create_finding_card(f) for f in high_findings],
                
                html.H5("🔵 Media Prioridad", className="text-info mb-3 mt-4"),
                *[create_finding_card(f) for f in medium_findings],
                
                html.H5("🟢 Aspectos Positivos", className="text-success mb-3 mt-4"),
                *[create_finding_card(f) for f in low_findings]
            ], md=6)
        ])
    ])

# Tab 12: Recomendaciones
def create_tab12_recommendations():
    """Tab 12: Recomendaciones para diseño de GD."""
    
    recommendations = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎯 Ubicación Óptima GD"),
                dbc.CardBody([
                    html.H5("Prioridad 1: Maquinchao", className="text-danger"),
                    html.Ul([
                        html.Li("Máxima sensibilidad dV/dP: -0.112 pu/MW"),
                        html.Li("Ubicación estratégica (km 210)"),
                        html.Li("Dimensionamiento: 2-3 MW")
                    ]),
                    
                    html.H5("Prioridad 2: Los Menucos", className="text-warning mt-3"),
                    html.Ul([
                        html.Li("Fin de línea - peores tensiones"),
                        html.Li("Ya existe GD: expandir a 5 MW"),
                        html.Li("BESS crítico por distancia")
                    ]),
                    
                    html.H5("Prioridad 3: Jacobacci", className="text-info mt-3"),
                    html.Ul([
                        html.Li("Mayor carga nominal (1.45 MW)"),
                        html.Li("Punto medio del sistema"),
                        html.Li("Dimensionamiento: 3-4 MW")
                    ])
                ])
            ])
        ], md=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⚡ Dimensionamiento BESS"),
                dbc.CardBody([
                    html.H6("Requerimientos Mínimos:", className="mb-3"),
                    
                    dbc.Table([
                        html.Tbody([
                            html.Tr([
                                html.Td("Potencia"),
                                html.Td("±1 MW/h rampa máxima", className="text-end")
                            ]),
                            html.Tr([
                                html.Td("Energía"),
                                html.Td("3-5 MWh por sitio", className="text-end")
                            ]),
                            html.Tr([
                                html.Td("Duración"),
                                html.Td("2-4 horas mínimo", className="text-end")
                            ]),
                            html.Tr([
                                html.Td("Respuesta"),
                                html.Td("< 5 minutos", className="text-end")
                            ]),
                            html.Tr([
                                html.Td("Ciclos diarios"),
                                html.Td("1-2 ciclos profundos", className="text-end")
                            ])
                        ])
                    ], bordered=True, size='sm'),
                    
                    html.P([
                        html.Strong("Estrategia: "),
                        "Time-shift agresivo para cubrir pico nocturno 20-22h"
                    ], className="mt-3")
                ])
            ])
        ], md=6)
    ], className="mb-4")
    
    # Design parameters summary
    design_params = dbc.Card([
        dbc.CardHeader("📊 Parámetros de Diseño Clave"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Demanda Base (P90)", className="text-muted"),
                    html.P("Sistema: 3.3 MW total", className="mb-0"),
                    html.Small("Garantizar cobertura 90% del tiempo")
                ], md=3),
                
                dbc.Col([
                    html.H6("Demanda Media (P50)", className="text-muted"),
                    html.P("Sistema: 5.5 MW total", className="mb-0"),
                    html.Small("Operación típica esperada")
                ], md=3),
                
                dbc.Col([
                    html.H6("Demanda Pico (P10)", className="text-muted"),
                    html.P("Sistema: 8.9 MW total", className="mb-0"),
                    html.Small("Capacidad máxima requerida")
                ], md=3),
                
                dbc.Col([
                    html.H6("Factor Utilización GD", className="text-muted"),
                    html.P("60-70% esperado", className="mb-0"),
                    html.Small("Con BESS y control óptimo")
                ], md=3)
            ])
        ])
    ])
    
    # Implementation roadmap
    roadmap = dbc.Card([
        dbc.CardHeader("🗺️ Hoja de Ruta de Implementación"),
        dbc.CardBody([
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Span("Fase 1", className="badge bg-danger me-2"),
                        html.Strong("GD Maquinchao (3 MW) + BESS (3 MWh)")
                    ])
                ], className="d-flex align-items-center"),
                dbc.ListGroupItem([
                    html.Div([
                        html.Span("Fase 2", className="badge bg-warning me-2"),
                        html.Strong("Expansión Los Menucos a 5 MW + BESS (5 MWh)")
                    ])
                ], className="d-flex align-items-center"),
                dbc.ListGroupItem([
                    html.Div([
                        html.Span("Fase 3", className="badge bg-info me-2"),
                        html.Strong("GD Jacobacci (4 MW) + BESS (4 MWh)")
                    ])
                ], className="d-flex align-items-center"),
                dbc.ListGroupItem([
                    html.Div([
                        html.Span("Fase 4", className="badge bg-success me-2"),
                        html.Strong("Sistema SCADA integrado y control coordinado")
                    ])
                ], className="d-flex align-items-center")
            ], flush=True)
        ])
    ], className="mt-4")
    
    return html.Div([
        html.H4("Recomendaciones para Diseño de GD", className="mb-3"),
        
        dbc.Alert([
            html.H5("💡 Recomendación Principal", className="alert-heading"),
            html.P([
                "Implementar GD distribuida en múltiples puntos con BESS para gestión 24h. ",
                "La naturaleza radial y extensa de la línea requiere solución distribuida, ",
                "no centralizada. Control coordinado es esencial por alta correlación entre estaciones."
            ])
        ], color="primary", className="mb-4"),
        
        recommendations,
        design_params,
        roadmap
    ])

# Helper function for typical day plot
def create_typical_day_plot(station, typical):
    """Create typical day plot for a station."""
    if station not in typical:
        return html.Div(f"No hay datos para {station}")
    
    station_data = typical[station]
    
    # Create figure with subplots for different day types
    fig = go.Figure()
    
    colors = {
        'weekday': UI_COLORS['primary'],
        'weekend': UI_COLORS['success'],
        'summer': UI_COLORS['warning'],
        'winter': UI_COLORS['info']
    }
    
    day_types = {
        'max_demand_day': {'name': 'Día Demanda Máxima', 'color': UI_COLORS['danger']},
        'min_demand_day': {'name': 'Día Demanda Mínima', 'color': UI_COLORS['success']},
        'average_day': {'name': 'Día Promedio', 'color': UI_COLORS['primary']},
        'worst_voltage_day': {'name': 'Día Peor Tensión', 'color': UI_COLORS['warning']}
    }
    
    for day_key, day_info in day_types.items():
        if day_key in station_data:
            day_data = station_data[day_key]
            hours = list(range(24))
            
            # Handle different data structures
            if 'hourly_demand' in day_data:
                # Regular days (max, min, worst voltage)
                hourly_data = day_data['hourly_demand']
                power_values = [hourly_data.get(str(h), 0) for h in hours]
            elif 'hourly_demand_mean' in day_data:
                # Average day has different structure
                hourly_data = day_data['hourly_demand_mean']
                power_values = [hourly_data.get(str(h), 0) for h in hours]
            else:
                continue
            
            fig.add_trace(go.Scatter(
                x=hours,
                y=power_values,
                mode='lines+markers',
                name=day_info['name'],
                line=dict(color=day_info['color'], width=2)
            ))
    
    fig.update_layout(
        title=f"Perfiles de Días Típicos - {station}",
        xaxis_title="Hora del día",
        yaxis_title="Potencia (MW)",
        xaxis=dict(tickmode='linear', tick0=0, dtick=2),
        height=400,
        template="plotly_white",
        hovermode='x unified'
    )
    
    # Add peak hours shading
    fig.add_vrect(x0=18, x1=23, fillcolor="rgba(255,0,0,0.1)",
                 annotation_text="Horas pico", annotation_position="top")
    
    # Statistics table
    stats_data = []
    for day_key, day_info in day_types.items():
        if day_key in station_data:
            day_data = station_data[day_key]
            
            # Handle average day differently
            if day_key == 'average_day':
                # Calculate stats from hourly means
                if 'hourly_demand_mean' in day_data:
                    hourly_values = list(day_data['hourly_demand_mean'].values())
                    peak = max(hourly_values) if hourly_values else 0
                    avg = sum(hourly_values) / len(hourly_values) if hourly_values else 0
                    
                    # Get min voltage from hourly_voltage_mean if available
                    min_v = 0
                    if 'hourly_voltage_mean' in day_data:
                        voltage_values = list(day_data['hourly_voltage_mean'].values())
                        min_v = min(voltage_values) if voltage_values else 0
                    
                    stats_data.append({
                        'Tipo de Día': day_info['name'],
                        'Fecha': 'Promedio histórico',
                        'P Pico (MW)': f"{peak:.2f}",
                        'P Promedio (MW)': f"{avg:.2f}",
                        'V Mínima (pu)': f"{min_v:.3f}"
                    })
            else:
                # Regular days
                stats_data.append({
                    'Tipo de Día': day_info['name'],
                    'Fecha': day_data.get('date', 'N/A'),
                    'P Pico (MW)': f"{day_data.get('peak_demand', 0):.2f}",
                    'P Promedio (MW)': f"{day_data.get('avg_demand', 0):.2f}",
                    'V Mínima (pu)': f"{day_data.get('min_voltage', 0):.3f}"
                })
    
    stats_df = pd.DataFrame(stats_data)
    
    return html.Div([
        dcc.Graph(figure=fig, config={'displayModeBar': False}),
        
        html.Hr(),
        
        html.H5("Estadísticas por Tipo de Día", className="mt-3"),
        dbc.Table.from_dataframe(
            stats_df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        ) if stats_data else html.P("No hay estadísticas disponibles")
    ])

# Main layout
layout = html.Div([
    dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("Fase 3: Procesamiento y Análisis de Datos", className="mb-3"),
                html.P([
                    "Análisis comprehensivo de 210,156 registros del sistema eléctrico. ",
                    html.Span("100% datos reales medidos", className="text-success fw-bold"),
                    " - Sistema SCADA/EPRE (Enero-Octubre 2024)"
                ], className="text-muted mb-4")
            ])
        ]),
        
        # Main alert
        dbc.Alert([
            html.I(className="fas fa-database me-2"),
            html.Strong("Procesamiento Completo: "),
            "12 análisis diferentes aplicados a los datos. ",
            "Todos los valores mostrados son mediciones reales del sistema."
        ], color="primary", className="mb-4"),
        
        # All sections one below the other
        html.Div(id="fase3-content")
        
    ], fluid=True)
])

# Generate content after page loads
def generate_content():
    """Generate all sections content with error handling."""
    sections = []
    
    # List of section functions with their names
    section_functions = [
        ("Resumen General", create_tab1_overview),
        ("Calidad de Datos", create_tab2_quality),
        ("Patrones Temporales", create_tab3_temporal),
        ("Correlaciones", create_tab4_correlations),
        ("Análisis Horario", create_tab5_hourly),
        ("Sensibilidad V-P", create_tab6_sensitivity),
        ("Eventos Críticos", create_tab7_critical),
        ("Rampas de Demanda", create_tab8_ramps),
        ("Curvas de Duración", create_tab9_duration),
        ("Días Típicos", create_tab10_typical),
        ("Hallazgos Críticos", create_tab11_findings),
        ("Recomendaciones", create_tab12_recommendations)
    ]
    
    for i, (name, func) in enumerate(section_functions):
        try:
            # Add separator for all sections except the first
            if i > 0:
                sections.append(html.Hr(className="my-5"))
            
            # Try to generate section content
            content = func()
            sections.append(html.Div(content))
            
        except Exception as e:
            # If error, show a warning message
            sections.append(
                dbc.Alert([
                    html.H5(f"Sección: {name}", className="alert-heading"),
                    html.P(f"Error cargando esta sección: {str(e)}"),
                    html.Small("Los datos podrían no estar disponibles en este momento.", className="text-muted")
                ], color="warning")
            )
    
    return sections

# Update layout to use the content generation
layout.children[0].children.append(
    dcc.Interval(id="load-content-interval", interval=100, n_intervals=0, max_intervals=1)
)

# Callback to load content after page loads
@callback(
    Output("fase3-content", "children"),
    Input("load-content-interval", "n_intervals")
)
def load_content(n):
    """Load all content sections with error handling."""
    if n is None:
        return []
    
    return generate_content()