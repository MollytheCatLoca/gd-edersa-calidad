# Guía de Integración Dashboard: DataManagerV2 ↔ BESSModel
## Quick Start Guide para Desarrolladores

**Fecha:** Julio 2025  
**Versión:** 1.0  
**Target:** Integración en dashboard Fase 4

---

## 🚀 Quick Start (5 minutos)

### 1. **Setup Básico**
```python
# Imports esenciales
from dashboard.pages.utils.data_manager_v2 import get_data_manager
from dashboard.pages.utils.models import DataStatus
from dashboard.pages.utils.constants import BESS_TECHNOLOGIES, BESS_TOPOLOGIES

# Obtener manager (singleton)
dm = get_data_manager()
```

### 2. **Primera Simulación**
```python
import numpy as np

# Perfil solar típico (24 horas)
solar_profile = np.concatenate([
    np.zeros(6),  # Noche
    np.linspace(0, 2, 6),  # Amanecer
    np.full(6, 2.0),  # Día
    np.linspace(2, 0, 6)   # Atardecer
])

# Simular BESS
result = dm.simulate_bess_strategy(
    solar_profile=solar_profile,
    strategy="time_shift_aggressive",
    power_mw=2.0,
    duration_hours=4.0
)

# Verificar resultado
if result.status == DataStatus.REAL:
    print("✅ Simulación exitosa!")
    metrics = result.data['metrics']
    print(f"Eficiencia: {metrics['energy_efficiency']:.1%}")
    print(f"Pérdidas: {metrics['total_losses_mwh']:.2f} MWh")
else:
    print(f"❌ Error: {result.meta.get('error')}")
```

### 3. **Integración Dashboard Dash**
```python
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go

@app.callback(
    Output('bess-results', 'children'),
    Input('simulate-btn', 'n_clicks'),
    State('bess-power', 'value'),
    State('bess-duration', 'value'),
    State('bess-strategy', 'value')
)
def simulate_bess(n_clicks, power_mw, duration_h, strategy):
    if not n_clicks:
        return "Presiona 'Simular' para comenzar"
    
    dm = get_data_manager()
    
    # Tu perfil solar aquí
    solar_profile = get_solar_profile()  # Implementar según tu fuente
    
    result = dm.simulate_bess_strategy(
        solar_profile=solar_profile,
        strategy=strategy,
        power_mw=power_mw,
        duration_hours=duration_h
    )
    
    if result.status == DataStatus.REAL:
        return create_results_display(result.data)
    else:
        return html.Div(
            f"Error en simulación: {result.meta.get('error')}",
            className="alert alert-danger"
        )
```

---

## 🎯 APIs Principales

### 1. **Simulación de Estrategias**
```python
result = dm.simulate_bess_strategy(
    solar_profile=solar_array,      # np.array con generación solar (MW)
    strategy="time_shift_aggressive", # Estrategia a usar
    power_mw=2.0,                   # Potencia BESS (MW)
    duration_hours=4.0,             # Duración BESS (h)
    technology="modern_lfp",        # Tecnología BESS
    topology="parallel_ac"          # Topología BESS
)

# Estrategias disponibles:
# - "time_shift_aggressive"  ← Recomendada
# - "solar_smoothing"
# - "cycling_demo"
# - "frequency_regulation"
# - "arbitrage_aggressive"
```

### 2. **Optimización Automática**
```python
result = dm.optimize_bess_for_solar(
    solar_profile=solar_array,
    power_range=(1.0, 3.0),         # Rango potencia a evaluar
    duration_range=(2.0, 6.0),      # Rango duración a evaluar
    strategy="time_shift_aggressive",
    optimization_metric="energy_efficiency"  # o "curtailment_ratio"
)

# Obtener mejor configuración
if result.status == DataStatus.REAL:
    best_config = result.data["best_configuration"]
    best_power = best_config["power_mw"]
    best_duration = best_config["duration_hours"]
    best_efficiency = best_config["objective_value"]
```

### 3. **Control Dinámico**
```python
# Para control step-by-step avanzado
power_requests = np.array([-1.0, -1.5, 2.0, 1.5])  # MW, negativo=carga

result = dm.simulate_bess_dynamic_control(
    initial_soc=0.5,
    power_requests=power_requests,
    power_mw=2.0,
    duration_hours=4.0,
    dt=1.0  # Paso temporal en horas
)

if result.status == DataStatus.REAL:
    soc_trajectory = result.data['soc_trajectory']
    actual_power = result.data['actual_power']
```

### 4. **Validación de Configuración**
```python
result = dm.validate_bess_configuration(
    power_mw=2.0,
    duration_hours=4.0,
    technology="modern_lfp",
    topology="parallel_ac"
)

if result.status == DataStatus.REAL:
    validation = result.data
    if validation["configuration_valid"]:
        warnings = validation["warnings"]
        if warnings:
            for warning in warnings:
                print(f"⚠️ {warning}")
    else:
        print("❌ Configuración inválida")
```

---

## 🎨 Componentes UI Recomendados

### 1. **Selectores de Configuración**
```python
# Dropdown tecnología BESS
technology_dropdown = dcc.Dropdown(
    id='bess-technology',
    options=[
        {'label': 'Standard (Lead-Acid)', 'value': 'standard'},
        {'label': 'Modern LFP (LiFePO4)', 'value': 'modern_lfp'},
        {'label': 'Premium (LTO)', 'value': 'premium'}
    ],
    value='modern_lfp',
    clearable=False
)

# Slider potencia
power_slider = dcc.Slider(
    id='bess-power',
    min=0.5, max=5.0, step=0.5, value=2.0,
    marks={i: f'{i} MW' for i in [0.5, 1, 2, 3, 4, 5]},
    tooltip={"placement": "bottom", "always_visible": True}
)

# Slider duración
duration_slider = dcc.Slider(
    id='bess-duration',
    min=1, max=8, step=1, value=4,
    marks={i: f'{i}h' for i in range(1, 9)},
    tooltip={"placement": "bottom", "always_visible": True}
)

# Dropdown estrategia
strategy_dropdown = dcc.Dropdown(
    id='bess-strategy',
    options=[
        {'label': 'Time Shift (Recomendada)', 'value': 'time_shift_aggressive'},
        {'label': 'Solar Smoothing', 'value': 'solar_smoothing'},
        {'label': 'Cycling Demo', 'value': 'cycling_demo'},
        {'label': 'Frequency Regulation', 'value': 'frequency_regulation'},
        {'label': 'Arbitrage', 'value': 'arbitrage_aggressive'}
    ],
    value='time_shift_aggressive',
    clearable=False
)
```

### 2. **Display de Métricas**
```python
def create_metrics_cards(simulation_data):
    metrics = simulation_data['metrics']
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{metrics['energy_efficiency']:.1%}", 
                               className="text-primary"),
                        html.P("Eficiencia Energética", className="card-text")
                    ])
                ], className="text-center mb-3")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{metrics['total_losses_mwh']:.2f} MWh", 
                               className="text-warning"),
                        html.P("Pérdidas Totales", className="card-text")
                    ])
                ], className="text-center mb-3")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{metrics['curtailment_ratio']:.1%}", 
                               className="text-danger"),
                        html.P("Curtailment", className="card-text")
                    ])
                ], className="text-center mb-3")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{simulation_data.get('total_cycles', 0):.1f}", 
                               className="text-info"),
                        html.P("Ciclos BESS", className="card-text")
                    ])
                ], className="text-center mb-3")
            ], width=3)
        ])
    ])
```

### 3. **Gráficos Interactivos**
```python
def create_power_profile_chart(simulation_data):
    fig = go.Figure()
    
    hours = list(range(len(simulation_data['grid_power'])))
    
    # Perfil solar original
    fig.add_trace(go.Scatter(
        x=hours,
        y=simulation_data.get('solar_profile', simulation_data['grid_power']),
        name='Generación Solar',
        line=dict(color='gold', width=2),
        hovertemplate='Solar: %{y:.2f} MW<extra></extra>'
    ))
    
    # Potencia a la red (solar + batería)
    fig.add_trace(go.Scatter(
        x=hours,
        y=simulation_data['grid_power'],
        name='Potencia a Red',
        line=dict(color='blue', width=2),
        fill='tonexty',
        hovertemplate='Red: %{y:.2f} MW<extra></extra>'
    ))
    
    # Potencia de batería
    fig.add_trace(go.Scatter(
        x=hours,
        y=simulation_data['battery_power'],
        name='Potencia BESS',
        line=dict(color='red', width=2),
        hovertemplate='BESS: %{y:.2f} MW (+descarga/-carga)<extra></extra>'
    ))
    
    fig.update_layout(
        title="Perfiles de Potencia PSFV + BESS",
        xaxis_title="Tiempo (horas)",
        yaxis_title="Potencia (MW)",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_soc_chart(simulation_data):
    fig = go.Figure()
    
    hours = list(range(len(simulation_data['soc'])))
    soc_percent = [soc * 100 for soc in simulation_data['soc']]
    
    fig.add_trace(go.Scatter(
        x=hours,
        y=soc_percent,
        name='Estado de Carga',
        line=dict(color='green', width=3),
        fill='tozeroy',
        hovertemplate='SOC: %{y:.1f}%<extra></extra>'
    ))
    
    # Líneas de referencia
    fig.add_hline(y=90, line_dash="dash", line_color="red", 
                  annotation_text="SOC Máximo (90%)")
    fig.add_hline(y=20, line_dash="dash", line_color="orange", 
                  annotation_text="SOC Mínimo (20%)")
    
    fig.update_layout(
        title="Estado de Carga BESS",
        xaxis_title="Tiempo (horas)",
        yaxis_title="SOC (%)",
        yaxis=dict(range=[0, 100])
    )
    
    return fig
```

---

## 🔧 Patrones de Integración

### 1. **Patrón de Inicialización**
```python
# En el inicio de tu página/app
from dashboard.pages.utils.data_manager_v2 import get_data_manager

# Global o en clase
_data_manager = None

def get_dm():
    global _data_manager
    if _data_manager is None:
        _data_manager = get_data_manager()
    return _data_manager

# Uso en callbacks
@app.callback(...)
def my_callback(...):
    dm = get_dm()
    # resto del callback
```

### 2. **Patrón de Error Handling**
```python
def safe_bess_simulation(solar_profile, **bess_config):
    try:
        dm = get_data_manager()
        result = dm.simulate_bess_strategy(
            solar_profile=solar_profile,
            **bess_config
        )
        
        if result.status == DataStatus.ERROR:
            return {
                'success': False,
                'error': result.meta.get('error', 'Simulation failed'),
                'data': None
            }
        
        return {
            'success': True,
            'error': None,
            'data': result.data
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}",
            'data': None
        }

# Uso en callback
@app.callback(...)
def simulate_callback(...):
    result = safe_bess_simulation(solar_profile, power_mw=2.0, duration_hours=4.0)
    
    if result['success']:
        return create_success_display(result['data'])
    else:
        return html.Div(f"Error: {result['error']}", className="alert alert-danger")
```

### 3. **Patrón de Performance**
```python
# Para simulaciones largas o repetitivas
@lru_cache(maxsize=128)
def cached_bess_simulation(solar_profile_hash, power_mw, duration_hours, strategy):
    """Cache simulaciones para evitar recálculos"""
    dm = get_data_manager()
    
    # Reconstruir perfil solar desde hash (implementar según tu caso)
    solar_profile = reconstruct_profile_from_hash(solar_profile_hash)
    
    return dm.simulate_bess_strategy(
        solar_profile=solar_profile,
        strategy=strategy,
        power_mw=power_mw,
        duration_hours=duration_hours,
        track_history=False,  # Performance
        verbose=False         # Performance
    )

# Para perfiles muy largos
def chunked_simulation(long_solar_profile, chunk_size=720):  # 30 días
    """Dividir simulaciones largas en chunks para mejor UX"""
    chunks = [long_solar_profile[i:i+chunk_size] 
              for i in range(0, len(long_solar_profile), chunk_size)]
    
    results = []
    for i, chunk in enumerate(chunks):
        progress = (i + 1) / len(chunks) * 100
        print(f"Procesando chunk {i+1}/{len(chunks)} ({progress:.0f}%)")
        
        result = dm.simulate_bess_strategy(
            solar_profile=chunk,
            strategy="time_shift_aggressive",
            power_mw=2.0,
            duration_hours=4.0
        )
        
        if result.status == DataStatus.REAL:
            results.append(result.data)
    
    return consolidate_results(results)  # Implementar consolidación
```

---

## 📊 Ejemplos de Integración Completa

### 1. **Tab BESS Simple**
```python
def create_bess_tab():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("Configuración BESS"),
                
                html.Label("Potencia BESS (MW)"),
                power_slider,
                
                html.Label("Duración (horas)", className="mt-3"),
                duration_slider,
                
                html.Label("Estrategia", className="mt-3"),
                strategy_dropdown,
                
                dbc.Button("Simular", id="simulate-btn", 
                          color="primary", className="mt-3 w-100")
                
            ], width=4),
            
            dbc.Col([
                html.H3("Resultados"),
                html.Div(id="bess-results")
            ], width=8)
        ])
    ])

@app.callback(
    Output('bess-results', 'children'),
    Input('simulate-btn', 'n_clicks'),
    State('bess-power', 'value'),
    State('bess-duration', 'value'),
    State('bess-strategy', 'value')
)
def update_bess_results(n_clicks, power_mw, duration_h, strategy):
    if not n_clicks:
        return "Configura los parámetros y presiona 'Simular'"
    
    # Generar o cargar perfil solar
    solar_profile = generate_typical_solar_profile()  # Tu implementación
    
    # Simular
    simulation_result = safe_bess_simulation(
        solar_profile=solar_profile,
        strategy=strategy,
        power_mw=power_mw,
        duration_hours=duration_h
    )
    
    if simulation_result['success']:
        data = simulation_result['data']
        return html.Div([
            create_metrics_cards(data),
            dcc.Graph(figure=create_power_profile_chart(data)),
            dcc.Graph(figure=create_soc_chart(data))
        ])
    else:
        return dbc.Alert(
            f"Error en simulación: {simulation_result['error']}", 
            color="danger"
        )
```

### 2. **Comparador de Configuraciones**
```python
def create_comparison_tab():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Configuración A"),
                html.Label("Potencia (MW)"),
                dcc.Slider(id='config-a-power', min=0.5, max=5, value=1.5, step=0.5),
                html.Label("Duración (h)"),
                dcc.Slider(id='config-a-duration', min=1, max=8, value=2, step=1),
            ], width=6),
            
            dbc.Col([
                html.H4("Configuración B"),
                html.Label("Potencia (MW)"),
                dcc.Slider(id='config-b-power', min=0.5, max=5, value=2.5, step=0.5),
                html.Label("Duración (h)"),
                dcc.Slider(id='config-b-duration', min=1, max=8, value=4, step=1),
            ], width=6)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Button("Comparar", id="compare-btn", color="primary", className="w-100")
            ], width=12)
        ], className="mt-3"),
        
        html.Div(id="comparison-results", className="mt-4")
    ])

@app.callback(
    Output('comparison-results', 'children'),
    Input('compare-btn', 'n_clicks'),
    State('config-a-power', 'value'),
    State('config-a-duration', 'value'),
    State('config-b-power', 'value'),
    State('config-b-duration', 'value')
)
def compare_configurations(n_clicks, power_a, duration_a, power_b, duration_b):
    if not n_clicks:
        return ""
    
    solar_profile = generate_typical_solar_profile()
    
    # Simular ambas configuraciones
    result_a = safe_bess_simulation(
        solar_profile=solar_profile,
        strategy="time_shift_aggressive",
        power_mw=power_a,
        duration_hours=duration_a
    )
    
    result_b = safe_bess_simulation(
        solar_profile=solar_profile,
        strategy="time_shift_aggressive",
        power_mw=power_b,
        duration_hours=duration_b
    )
    
    if result_a['success'] and result_b['success']:
        return create_comparison_display(result_a['data'], result_b['data'])
    else:
        errors = []
        if not result_a['success']:
            errors.append(f"Config A: {result_a['error']}")
        if not result_b['success']:
            errors.append(f"Config B: {result_b['error']}")
        
        return dbc.Alert(
            "Errores en simulación: " + "; ".join(errors),
            color="danger"
        )

def create_comparison_display(data_a, data_b):
    metrics_a = data_a['metrics']
    metrics_b = data_b['metrics']
    
    comparison_table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Métrica"),
                html.Th("Configuración A"),
                html.Th("Configuración B"),
                html.Th("Diferencia")
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td("Eficiencia Energética"),
                html.Td(f"{metrics_a['energy_efficiency']:.1%}"),
                html.Td(f"{metrics_b['energy_efficiency']:.1%}"),
                html.Td(f"{(metrics_b['energy_efficiency'] - metrics_a['energy_efficiency'])*100:+.1f} pp")
            ]),
            html.Tr([
                html.Td("Pérdidas (MWh)"),
                html.Td(f"{metrics_a['total_losses_mwh']:.2f}"),
                html.Td(f"{metrics_b['total_losses_mwh']:.2f}"),
                html.Td(f"{metrics_b['total_losses_mwh'] - metrics_a['total_losses_mwh']:+.2f}")
            ])
        ])
    ], striped=True, bordered=True, hover=True)
    
    return html.Div([
        html.H4("Comparación de Configuraciones"),
        comparison_table
    ])
```

---

## ⚠️ Problemas Comunes y Soluciones

### 1. **Import Errors**
```python
# ❌ Error común
from dashboard.pages.utils.data_manager_v2 import DataManagerV2

# ✅ Correcto
from dashboard.pages.utils.data_manager_v2 import get_data_manager

# ❌ Error: crear múltiples instancias
dm1 = DataManagerV2()
dm2 = DataManagerV2()

# ✅ Correcto: usar singleton
dm = get_data_manager()
```

### 2. **Performance Issues**
```python
# ❌ Lento: tracking habilitado
result = dm.simulate_bess_strategy(
    solar_profile=large_profile,
    strategy="time_shift_aggressive",
    power_mw=2.0,
    duration_hours=4.0
)

# ✅ Rápido: optimizado para performance
result = dm.simulate_bess_strategy(
    solar_profile=large_profile,
    strategy="time_shift_aggressive",
    power_mw=2.0,
    duration_hours=4.0,
    track_history=False,  # ⚡ Crítico para performance
    verbose=False         # ⚡ Reduce logging
)
```

### 3. **Error Handling**
```python
# ❌ Sin manejo de errores
result = dm.simulate_bess_strategy(...)
metrics = result.data['metrics']  # Puede fallar

# ✅ Con manejo robusto
result = dm.simulate_bess_strategy(...)
if result.status == DataStatus.REAL:
    metrics = result.data['metrics']
    # Procesar resultado exitoso
elif result.status == DataStatus.ERROR:
    error_msg = result.meta.get('error', 'Unknown error')
    # Mostrar error al usuario
else:
    # Manejar otros estados (FALLBACK, etc.)
```

### 4. **Memory Issues**
```python
# Si hay problemas de memoria después de muchas simulaciones
from dashboard.pages.utils.data_manager_v2 import reset_data_manager
import gc

# Reset completo del sistema
reset_data_manager()
gc.collect()

# Obtener nuevo manager limpio
dm = get_data_manager()
```

---

## 🎯 Checklist de Integración

### ✅ Pre-integración
- [ ] Entorno virtual activado
- [ ] Imports funcionando correctamente
- [ ] Test básico de simulación ejecutado
- [ ] DataManager inicializado sin errores

### ✅ Durante Integración
- [ ] Singleton pattern implementado correctamente
- [ ] Error handling en todos los callbacks
- [ ] Performance optimizations aplicadas
- [ ] UI components creados
- [ ] Gráficos funcionando

### ✅ Post-integración
- [ ] Tests de integración UI ejecutados
- [ ] Performance testing realizado
- [ ] Error scenarios validados
- [ ] Documentación actualizada
- [ ] User acceptance testing

---

## 📞 Soporte

### Documentación Adicional
- **Técnica completa**: `/docs/fase4_integration_final_report.md`
- **API Reference**: BESSModel docstrings
- **Tests**: `/tests/integration/test_data_manager_v2_bess_integration.py`

### Debugging
```python
# Habilitar logging detallado
import logging
logging.getLogger('dashboard.pages.utils.data_manager_v2').setLevel(logging.DEBUG)

# Test de conectividad
from dashboard.pages.utils.data_manager_v2 import get_data_manager
dm = get_data_manager()
print("✅ DataManager OK" if dm else "❌ DataManager Error")
```

### Contacto
- **Sistema**: DataManagerV2 ↔ BESSModel Integration
- **Versión**: 1.0
- **Estado**: ✅ Production Ready

---

*Guía generada para facilitar la integración del sistema BESS en el dashboard. Sistema completamente validado y listo para producción.*