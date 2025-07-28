# Plan de Integración: Factor de Necesidad de Red en Dashboard
## Para implementar en próxima sesión

### 1. Actualización de optimization_analysis.py

#### A. Nuevo Slider para Factor de Necesidad de Red

```python
# Agregar después del slider de Q nocturno (línea ~395)
create_form_group(
    "Factor de Necesidad de Red (%)",
    html.Div([
        dcc.Slider(
            id="network-need-slider",
            min=0,
            max=100,
            step=5,
            value=100,  # Por defecto asume red crítica
            marks={i: f'{i}%' for i in range(0, 101, 25)},
            tooltip={"placement": "bottom", "always_visible": True},
            className="mb-3"
        ),
        html.Div(id="network-need-display", className="text-center text-warning fw-bold"),
        html.Small([
            "0% = Red robusta sin problemas | ",
            "100% = Red crítica con problemas severos"
        ], className="text-muted")
    ]),
    "Ajusta los beneficios de red según el estado real de la infraestructura",
    icon="fas fa-network-wired"
),
```

#### B. Actualizar función calculate_cluster_flows()

```python
# Línea ~167, agregar parámetro network_need_factor
network_benefits = calculate_total_network_benefits(
    pv_mw=pv_mw,
    bess_mwh=bess_mwh,
    q_mvar=q_mvar,
    network_params=network_params_estimated,
    network_need_factor=network_need_factor  # NUEVO
)
```

#### C. Actualizar callbacks

```python
# Agregar Input para el slider (línea ~550)
Input("network-need-slider", "value"),

# En la función del callback, extraer el valor:
network_need_factor = network_need_slider_value / 100  # Convertir a 0-1

# Pasar a calculate_cluster_flows:
results = calculate_cluster_flows(
    pv_ratio, bess_hours, q_night_ratio,
    cluster_data, params, network_params,
    network_need_factor=network_need_factor  # NUEVO
)
```

### 2. Nuevos Componentes Visuales

#### A. Indicador de Estado de Red

```python
def create_network_status_indicator(need_factor):
    """Crea indicador visual del estado de la red"""
    if need_factor < 0.25:
        color = "success"
        icon = "fa-check-circle"
        text = "Red Robusta"
    elif need_factor < 0.75:
        color = "warning"
        icon = "fa-exclamation-triangle"
        text = "Red con Problemas Moderados"
    else:
        color = "danger"
        icon = "fa-times-circle"
        text = "Red Crítica"
    
    return dbc.Alert([
        html.I(className=f"fas {icon} me-2"),
        html.Strong(text),
        html.Span(f" - Factor de necesidad: {need_factor:.0%}")
    ], color=color, className="mb-3")
```

#### B. Tabla Comparativa de Impacto

```python
def create_need_factor_comparison_table(base_results, adjusted_results):
    """Crea tabla comparando resultados con/sin ajuste"""
    return dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Métrica"),
                html.Th("Sin ajuste (100%)"),
                html.Th(f"Con ajuste ({need_factor:.0%})"),
                html.Th("Diferencia")
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td("Beneficios de Red"),
                html.Td(f"${base_results['network_total']/1e6:.2f}M"),
                html.Td(f"${adjusted_results['network_total']/1e6:.2f}M"),
                html.Td(f"-${(base_results['network_total']-adjusted_results['network_total'])/1e6:.2f}M")
            ]),
            html.Tr([
                html.Td("Payback"),
                html.Td(f"{base_results['payback']:.1f} años"),
                html.Td(f"{adjusted_results['payback']:.1f} años"),
                html.Td(f"+{adjusted_results['payback']-base_results['payback']:.1f} años")
            ]),
            # Más filas según necesidad
        ])
    ], bordered=True, hover=True, responsive=True, striped=True)
```

### 3. Actualización de Gráficos

#### A. Modificar gráfico de beneficios de red

```python
# En la función que crea el gráfico de beneficios de red
# Agregar anotación mostrando el factor aplicado
fig.add_annotation(
    text=f"Factor de necesidad: {network_need_factor:.0%}",
    xref="paper", yref="paper",
    x=0.5, y=1.1,
    showarrow=False,
    font=dict(size=12, color="orange")
)
```

#### B. Nuevo gráfico de sensibilidad

```python
def create_need_factor_sensitivity_chart(base_config):
    """Crea gráfico mostrando payback vs factor de necesidad"""
    factors = [0, 0.25, 0.5, 0.75, 1.0]
    paybacks = []
    
    for factor in factors:
        results = calculate_cluster_flows(
            base_config['pv_ratio'],
            base_config['bess_hours'],
            base_config['q_night_ratio'],
            base_config['cluster_data'],
            base_config['params'],
            base_config['network_params'],
            network_need_factor=factor
        )
        paybacks.append(results['metrics']['payback_simple'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[f*100 for f in factors],
        y=paybacks,
        mode='lines+markers',
        name='Payback',
        line=dict(color='blue', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title="Sensibilidad del Payback al Factor de Necesidad",
        xaxis_title="Factor de Necesidad de Red (%)",
        yaxis_title="Payback (años)",
        hovermode='x unified'
    )
    
    return fig
```

### 4. Testing de la Integración

```python
# test_dashboard_network_need.py
def test_network_need_integration():
    """Test de integración del factor de necesidad en dashboard"""
    
    # Test 1: Verificar que slider actualiza correctamente
    # Test 2: Verificar que cálculos se ajustan
    # Test 3: Verificar visualizaciones
    # Test 4: Verificar casos extremos (0% y 100%)
```

### 5. Documentación para Usuario

Agregar tooltip o modal con explicación:

```markdown
## Factor de Necesidad de Red

Este parámetro ajusta los beneficios económicos de la red según 
el estado actual de la infraestructura:

- **0-25%**: Red robusta con buena calidad de servicio
  - Pocos problemas de tensión
  - Bajas pérdidas técnicas
  - Alta confiabilidad
  
- **25-75%**: Red con problemas moderados
  - Violaciones ocasionales de tensión
  - Pérdidas técnicas moderadas
  - Confiabilidad aceptable
  
- **75-100%**: Red crítica con problemas severos
  - Violaciones frecuentes de tensión
  - Altas pérdidas técnicas
  - Baja confiabilidad

El factor se aplica proporcionalmente a todos los beneficios 
de red (Q at Night, reducción de pérdidas, confiabilidad).
```

### 6. Pasos de Implementación

1. **Backup actual**: Guardar versión actual de optimization_analysis.py
2. **Implementar slider**: Agregar UI del factor de necesidad
3. **Actualizar lógica**: Modificar calculate_cluster_flows
4. **Agregar visualizaciones**: Indicador de estado y tabla comparativa
5. **Testing local**: Verificar funcionamiento correcto
6. **Documentar cambios**: Actualizar documentación del dashboard
7. **Commit final**: "feat: Integrar Factor de Necesidad de Red en dashboard"

### 7. Consideraciones Adicionales

- **Persistencia**: Guardar factor seleccionado en Store para mantener entre cálculos
- **Presets**: Botones rápidos para "Red Robusta" (25%), "Red Media" (50%), "Red Crítica" (100%)
- **Exportación**: Incluir factor de necesidad en reportes CSV/Excel
- **Validación**: Advertir si el factor parece inconsistente con datos del cluster