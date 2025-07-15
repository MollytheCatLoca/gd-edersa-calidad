# PLAN DETALLADO FASE 5: MODELIZACIÓN INTEGRAL DE LA RED

## 1. OBJETIVO GENERAL
Crear un modelo completo de la red eléctrica que integre flujos de potencia, costos nodales y parámetros de calidad de servicio, con análisis detallado de pérdidas técnicas y económicas.

## 2. ARQUITECTURA DEL SISTEMA

### 2.1 Estructura de Directorios
```
src/
├── power_flow/
│   ├── __init__.py
│   ├── dc_power_flow.py         # Motor de cálculo DC
│   ├── ac_power_flow.py         # Motor de cálculo AC (futuro)
│   ├── sensitivity_analysis.py   # Análisis dV/dP, dV/dQ
│   └── contingency_analysis.py   # Análisis N-1 detallado
│
├── node_analysis/
│   ├── __init__.py
│   ├── node_metrics.py          # Métricas por nodo
│   ├── service_quality.py       # Índices de calidad
│   ├── hosting_capacity.py      # Capacidad alojamiento GD
│   └── load_profiles.py         # Gestión perfiles de carga
│
├── economics/
│   ├── __init__.py
│   ├── nodal_costs.py           # Costos marginales nodales
│   ├── loss_allocation.py       # Asignación de pérdidas
│   ├── tariff_engine.py         # Motor tarifario
│   └── economic_dispatch.py     # Despacho económico
│
├── losses/
│   ├── __init__.py
│   ├── technical_losses.py      # Pérdidas técnicas I²R
│   ├── economic_losses.py       # Valorización pérdidas
│   └── loss_factors.py          # Factores de pérdidas
│
├── validation/
│   ├── __init__.py
│   ├── power_balance.py         # Verificar P_gen = P_load + P_losses
│   ├── kirchhoff_laws.py        # Validar leyes en cada nodo
│   ├── measurements.py          # Comparar con SCADA si disponible
│   └── convergence.py           # Monitorear convergencia numérica
│
├── performance/
│   ├── __init__.py
│   ├── cache_manager.py         # LRU cache + Redis
│   ├── parallel_compute.py      # Cálculos paralelos
│   └── data_imputation.py       # Manejo datos faltantes
│
└── visualization/
    ├── __init__.py
    ├── network_map.py           # Mapa geográfico
    ├── power_flow_viz.py        # Flujos animados
    ├── cost_heatmap.py          # Mapas de calor costos
    ├── real_time_alerts.py      # Sistema de alertas
    └── dashboard_components.py   # Componentes Dash

scripts/
├── run_power_flow.py            # Ejecución flujo de carga
├── calculate_nodal_costs.py     # Cálculo costos nodales
├── analyze_losses.py            # Análisis pérdidas
├── generate_reports.py          # Generación reportes
└── sensitivity_studies.py       # Estudios sensibilidad

dashboard/pages/
├── fase5_network_model.py       # Dashboard principal
├── components/
│   ├── network_overview.py      # Vista general red
│   ├── nodal_analysis.py        # Análisis por nodo
│   ├── loss_analysis.py         # Análisis pérdidas
│   └── economic_analysis.py     # Análisis económico

data/
└── phase5/
    ├── power_flow/              # Resultados flujo
    ├── nodal_costs/             # Costos por nodo
    ├── losses/                  # Análisis pérdidas
    └── reports/                 # Reportes generados
```

## 3. MODELOS TÉCNICOS DETALLADOS

### 3.1 Modelo de Flujo de Potencia DC
```python
# Ecuaciones básicas:
# P_ij = (V_i * V_j / X_ij) * sin(θ_i - θ_j) ≈ (θ_i - θ_j) / X_ij
# Para red radial 33kV con R/X típico ~1.5

Inputs:
- Topología: NetworkTopology (existente)
- Cargas: P, Q por nodo (typical_days.json)
- Generación: GD Los Menucos (1.8 MW)
- Impedancias: R, X por línea (topology.py)

Outputs:
- Flujos P, Q por línea
- Voltajes por nodo
- Ángulos de fase
- Pérdidas por tramo
```

### 3.2 Análisis de Sensibilidad
```python
# Usar datos reales fase 3:
dV/dP = -0.112 pu/MW (Maquinchao - caso crítico)
dV/dQ = -0.089 pu/MVAr (estimado)

# Matriz de sensibilidad para toda la red
S = [dV_i/dP_j] para todos los nodos i,j
```

### 3.3 Modelo de Pérdidas Técnicas
```python
# Pérdidas por línea:
P_loss_ij = I²_ij * R_ij
I_ij = S_ij / (√3 * V_ij)

# Pérdidas totales:
P_loss_total = Σ P_loss_ij

# Factor de pérdidas:
FP = P_loss_total / P_total * 100
```

### 3.4 Análisis de Contingencias N-1
```python
# contingency_analysis.py
CONTINGENCIAS_CRITICAS = {
    'N1_L1': {
        'elemento': 'Línea Pilcaniyeu-Jacobacci',
        'tipo': 'pérdida_línea',
        'impacto': 'Aislamiento Jacobacci-Maquinchao-Los Menucos',
        'mitigación': 'Transferencia carga a GD Los Menucos',
        'probabilidad': 0.02,  # 2% anual
        'duración_típica': 4  # horas
    },
    'N1_T1': {
        'elemento': 'Trafo 132/33kV Maquinchao',
        'tipo': 'pérdida_transformador',
        'impacto': 'Pérdida alimentación Maquinchao',
        'mitigación': 'Alimentación desde Los Menucos si posible',
        'probabilidad': 0.01,  # 1% anual
        'duración_típica': 12  # horas
    },
    'N1_G1': {
        'elemento': 'GD Los Menucos',
        'tipo': 'pérdida_generación',
        'impacto': 'Sobrecarga líneas, caída tensión 3-5%',
        'mitigación': 'Deslastre selectivo de carga',
        'probabilidad': 0.05,  # 5% anual
        'duración_típica': 2  # horas
    }
}

def analyze_contingency(network, contingency_id):
    """Analiza impacto de contingencia específica"""
    # 1. Remover elemento del modelo
    # 2. Recalcular flujo de potencia
    # 3. Verificar violaciones
    # 4. Calcular ENS (Energía No Suministrada)
    # 5. Evaluar costo contingencia
```

## 4. MODELOS ECONÓMICOS

### 4.1 Costos Nodales
```python
# Costo marginal en nodo i:
CMg_i = CMg_gen + Σ(λ_j * dP_loss_j/dP_i)

Donde:
- CMg_gen = $62.5/MWh (tarifa base)
- λ_j = Costo marginal en línea j
- dP_loss_j/dP_i = Sensibilidad pérdidas

# Para nodo con GD:
CMg_i_GD = min(CMg_gen, $122.7/MWh)
```

### 4.2 Asignación de Pérdidas
```python
# Método pro-rata:
Loss_node_i = P_loss_total * (P_i / P_total)

# Método incremental:
Loss_node_i = Σ(0.5 * dP_loss/dP_i * P_i)

# Costo pérdidas nodo:
C_loss_i = Loss_node_i * CMg_promedio
```

### 4.3 Modelo Tarifario
```python
# Tarifa efectiva nodo i:
T_eff_i = T_base + C_transmisión_i + C_pérdidas_i

Donde:
- T_base = $62.5/MWh
- C_transmisión_i = f(distancia, MW-km)
- C_pérdidas_i = pérdidas acumuladas * CMg
```

## 5. PARÁMETROS DE CALIDAD DE SERVICIO

### 5.1 Métricas por Nodo
```python
# Nivel de tensión:
- V_min, V_max, V_promedio
- Tiempo fuera de banda (%)
- Violaciones regulatorias

# Continuidad:
- SAIFI: Interrupciones/año
- SAIDI: Duración interrupciones
- ENS: Energía no suministrada

# Calidad de onda:
- THD voltaje
- Desbalance
- Flicker
```

### 5.2 Índices Compuestos
```python
# Índice Calidad Nodo (ICN):
ICN_i = w1*V_quality + w2*Continuity + w3*Cost_efficiency

# Criticidad del nodo:
Crit_i = Carga_i * Usuarios_i * Factor_social
```

### 5.3 Métricas Avanzadas
```python
# Capacidad de alojamiento GD por nodo
def calculate_hosting_capacity(node):
    """MW máximos de GD sin violar límites operativos"""
    thermal_limit_mw = get_thermal_headroom(node)
    voltage_limit_mw = get_voltage_headroom(node) / sensitivity_dvdp
    stability_limit_mw = calculate_stability_margin(node)
    
    return min(thermal_limit_mw, voltage_limit_mw, stability_limit_mw)

# Índice de estabilidad de voltaje (VSI)
def voltage_stability_index(node):
    """VSI = |V|² / (P*X - Q*R)
    VSI < 0.5: Sistema estable
    0.5 < VSI < 1.0: Precaución
    VSI > 1.0: Sistema inestable
    """
    V = node.voltage_pu
    P = node.active_power_mw
    Q = node.reactive_power_mvar
    R = node.upstream_resistance
    X = node.upstream_reactance
    
    return abs(V)**2 / abs(P*X - Q*R)

# Factor de utilización de línea
def line_utilization_factor(line):
    """Porcentaje de capacidad térmica utilizada"""
    return line.current_flow / line.thermal_limit * 100
```

## 6. ANÁLISIS DE PÉRDIDAS

### 6.1 Pérdidas Técnicas
```python
# Por componente:
- Líneas: I²R (principal)
- Transformadores: Vacío + Carga
- Reguladores: Pérdidas control

# Por nivel tensión:
- 132 kV: ~1-2%
- 33 kV: ~3-5%
- BT: ~2-3%
```

### 6.2 Pérdidas Económicas
```python
# Costo anual pérdidas:
C_loss_anual = Σ(P_loss_h * CMg_h) * 8760

# VPN pérdidas (25 años):
VPN_loss = Σ(C_loss_año_t / (1+r)^t)

# Costo unitario pérdidas:
CU_loss = C_loss_anual / Energía_total
```

## 7. CASOS DE ESTUDIO

### 7.1 Escenarios Base
1. **Operación actual**: Sin GD adicional
2. **Con GD Los Menucos**: 1.8 MW operando
3. **Expansión GD**: 3 MW en Los Menucos
4. **GD distribuida**: 1 MW c/u en 3 nodos

### 7.2 Análisis Temporal
- **Día típico verano**: Alta demanda día
- **Día típico invierno**: Alta demanda noche
- **Fin de semana**: Baja demanda
- **Día crítico**: Máxima demanda anual

### 7.3 Casos Especiales
- **Caso extremo verano**: 40°C ambiente, máxima irradiación solar, demanda A/C +30%
- **Mantenimiento programado**: Línea Pilcaniyeu-Jacobacci fuera de servicio 8h
- **Crecimiento explosivo**: Data center 5MW o granja minería cripto en Los Menucos

### 7.4 Sensibilidades
- Crecimiento demanda: +2%, +5%, +10%
- Precio energía: $60, $62.5, $65
- Factor capacidad GD: 10%, 13.3%, 20%
- Temperatura ambiente: 20°C, 30°C, 40°C (afecta capacidad líneas)

## 8. VISUALIZACIÓN Y REPORTES

### 8.1 Dashboard Principal
- **Mapa de red**: Flujos en tiempo real con animación
- **Tabla nodal**: Métricas clave por nodo con alertas
- **Gráficos temporales**: Evolución 24h animada
- **Indicadores KPI**: Pérdidas, costos, calidad, VSI
- **Hotspots pérdidas**: Identificación visual de pérdidas críticas
- **Gradiente económico**: Mapa de calor costos nodales
- **Alertas automáticas**: Violaciones límites en tiempo real

### 8.2 Reportes Automatizados
1. **Reporte técnico**: Flujos, voltajes, pérdidas
2. **Reporte económico**: Costos, tarifas, VPN
3. **Reporte calidad**: Índices, violaciones
4. **Reporte ejecutivo**: KPIs, recomendaciones

## 9. INTEGRACIÓN CON FASES ANTERIORES

### 9.1 Datos de Entrada
- **Fase 1**: Metadatos sistema
- **Fase 2**: Topología red (NetworkTopology)
- **Fase 3**: Perfiles carga, sensibilidades
- **Fase 4**: Perfiles solares (futuro)

### 9.2 Preparación para Fase 6
- Modelo base para optimización
- Métricas objetivo definidas
- Restricciones identificadas
- Casos base documentados

## 10. CRONOGRAMA IMPLEMENTACIÓN

### Semana 1: Infraestructura + Validación
- Setup arquitectura completa con nuevos módulos
- Implementar sistema de validación (power balance, Kirchhoff)
- Cache manager con Redis y LRU
- Tests unitarios para validación
- Data imputation para datos faltantes

### Semana 2: Motor de Cálculo + Contingencias
- Implementar DC power flow robusto
- Análisis N-1 completo (3 contingencias críticas)
- Cálculo pérdidas con validación
- Comparación con mediciones SCADA históricas
- Manejo de convergencia en nodos débiles (Maquinchao)

### Semana 3: Análisis Económico + Capacidad
- Costos nodales con validación regulatoria
- Hosting capacity por nodo
- Implementar VSI (Voltage Stability Index)
- Análisis sensibilidad pérdidas
- Modelo tarifario completo

### Semana 4: Dashboard + Preparación ML
- Dashboard con animaciones 24h
- Sistema alertas automáticas
- Visualización hotspots y gradientes
- Exportar datasets para ML (8760h × nodos × variables)
- Documentación completa y entrenamiento usuarios

## 11. ENTREGABLES

1. **Código fuente**: Modular, documentado, testeado
2. **Dashboard web**: Interactivo, responsive
3. **Reportes**: PDF/Excel automáticos
4. **Documentación**: Técnica y usuario
5. **Dataset**: Resultados para ML (Fase 6)

## 12. MÉTRICAS DE ÉXITO

### 12.1 Técnicas
- Error flujo potencia < 5%
- Convergencia < 10 iteraciones
- Tiempo cálculo < 1 segundo

### 12.2 Económicas
- Precisión costos nodales ± 2%
- Pérdidas totales validadas
- Tarifas coherentes con regulación

### 12.3 Calidad
- Cobertura código > 80%
- Documentación completa
- Dashboard intuitivo

## 13. RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Datos incompletos | Media | Alto | Usar interpolación/promedios |
| Convergencia flujo | Baja | Alto | Implementar métodos robustos |
| Performance dashboard | Media | Medio | Optimizar queries/cache |
| Complejidad UI | Media | Bajo | Diseño iterativo con usuarios |

## 14. REFERENCIAS TÉCNICAS

1. **Power Flow**:
   - Wood & Wollenberg, "Power Generation, Operation, and Control"
   - Grainger & Stevenson, "Power System Analysis"

2. **Costos Nodales**:
   - Schweppe et al., "Spot Pricing of Electricity"
   - Kirschen & Strbac, "Fundamentals of Power System Economics"

3. **Pérdidas**:
   - IEEE Std 1366-2012 (Reliability Indices)
   - CIRED Working Group on Losses

4. **Regulación Argentina**:
   - ENRE - Normativa calidad de servicio
   - CAMMESA - Procedimientos técnicos

## 15. PREPARACIÓN PARA ML/OPTIMIZACIÓN

### 15.1 Datasets a Exportar
```python
# Exportar para Fase 6:
export_files = {
    'matriz_sensibilidad_completa.pkl': 'Matriz dV/dP, dV/dQ completa',
    'escenarios_historicos.parquet': '8760h × N nodos × M variables',
    'restricciones_operativas.json': 'Límites técnicos y regulatorios',
    'variables_decision.yaml': 'Variables optimizables identificadas',
    'contingencias_evaluadas.h5': 'Resultados análisis N-1',
    'hosting_capacity_map.json': 'Capacidad GD por nodo'
}

# Dataset ML incluirá:
ml_features = {
    'temporales': ['hora', 'día_semana', 'mes', 'estación'],
    'nodales': ['P', 'Q', 'V', 'ángulo', 'VSI'],
    'topológicas': ['distancia_origen', 'impedancia_acum'],
    'económicas': ['costo_marginal', 'pérdidas_valor'],
    'calidad': ['violaciones', 'SAIFI', 'SAIDI']
}
```

### 15.2 Variables de Decisión
- Ubicación BESS (nodo)
- Tamaño BESS (MW/MWh)
- Ubicación GD adicional
- Estrategia despacho GD
- Tap transformadores

## 16. ASPECTOS CRÍTICOS A MONITOREAR

### 16.1 Nodos Problemáticos
- **Maquinchao**: Nodo débil, vigilar convergencia y VSI
- **Comallo**: Baja carga, posibles sobretensiones
- **Los Menucos**: Impacto GD en estabilidad local

### 16.2 Validaciones Clave
- **Factor pérdidas 33kV**: Validar 3-5% con datos reales EPRE
- **Costos nodales**: No superar límites tarifarios ENRE
- **Convergencia**: < 10 iteraciones, tolerancia 1e-6
- **Balance potencia**: Error < 0.1%

### 16.3 Performance Crítico
```python
# Targets de performance:
PERFORMANCE_TARGETS = {
    'tiempo_calculo_flujo': '< 1 segundo',
    'tiempo_contingencia': '< 5 segundos',
    'memoria_máxima': '< 2 GB',
    'cache_hit_rate': '> 80%',
    'dashboard_refresh': '< 2 segundos'
}
```

---

**Documento preparado por**: Sistema de Análisis - Estudio GD Línea Sur  
**Fecha**: 2025-07-11  
**Versión**: 2.0  
**Estado**: ACTUALIZADO CON FEEDBACK INGENIERO - APROBADO PARA IMPLEMENTACIÓN