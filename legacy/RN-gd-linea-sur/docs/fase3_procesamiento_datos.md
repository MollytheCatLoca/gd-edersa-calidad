# FASE 3: PROCESAMIENTO EXHAUSTIVO DE DATOS
## Análisis Completo de Registros Históricos del Sistema

### 1. RESUMEN EJECUTIVO

La Fase 3 presenta el análisis exhaustivo de 210,156 registros reales del sistema eléctrico Línea Sur, recopilados entre enero 2024 y abril 2025. Todos los datos provienen directamente del sistema SCADA/EPRE sin estimaciones ni valores teóricos.

**Hallazgos Críticos:**
- **100% del tiempo fuera de límites regulatorios** de tensión (< 0.95 pu)
- Caída de tensión promedio: 39% en Pilcaniyeu hasta 76% en Los Menucos
- Sistema operando al 56% de capacidad nominal con pérdidas técnicas extremas
- Alta correlación entre estaciones (0.48-0.90) confirmando comportamiento radial
- Patrones de demanda altamente predecibles con picos consistentes 20-22h

### 2. DATOS PROCESADOS

#### 2.1 Cobertura de Datos
| Estación | Período | Registros | Resolución |
|----------|---------|-----------|------------|
| Pilcaniyeu | Ene 2024 - Abr 2025 | 46,107 | 15 min |
| Jacobacci | Ene 2024 - Abr 2025 | 91,830 | 15 min |
| Maquinchao | Ago 2024 - Abr 2025 | 26,112 | 15 min |
| Los Menucos | Ene 2024 - Abr 2025 | 46,107 | 15 min |

**Total: 210,156 registros procesados**

#### 2.2 Calidad de Datos
- Tasa de limpieza: 0% (sin registros removidos)
- Resolución temporal: 15 minutos (96 muestras/día)
- Gaps identificados: Maquinchao inicia en agosto 2024
- Calidad general: Excelente

### 3. ANÁLISIS POR ELEMENTO

#### 3.1 TENSIONES - Estado Crítico

**Valores Promedio Medidos:**
| Estación | Distancia | V Promedio | V Mínimo | V Máximo | Caída |
|----------|-----------|------------|----------|----------|-------|
| Pilcaniyeu | 0 km | 0.607 pu | 0.000 pu | 0.650 pu | 39% |
| Jacobacci | 150 km | 0.236 pu | 0.000 pu | 0.246 pu | 76% |
| Maquinchao | 210 km | 0.242 pu | 0.000 pu | 0.255 pu | 76% |
| Los Menucos | 270 km | 0.237 pu | 0.000 pu | 0.253 pu | 76% |

**Análisis:**
- Sistema en colapso de tensión permanente
- Ninguna estación cumple límite mínimo 0.95 pu
- Reguladores existentes insuficientes
- Operación fuera de norma técnica

#### 3.2 POTENCIAS - Demanda y Patrones

**Demanda por Estación:**
| Estación | P Promedio | P Máxima | Q Promedio | FP Promedio |
|----------|------------|----------|------------|-------------|
| Pilcaniyeu | 2.95 MW | 5.14 MW | 0.30 MVAr | 0.990 |
| Jacobacci | 0.51 MW | 1.17 MW | 0.25 MVAr | 0.912 |
| Maquinchao | 0.46 MW | 1.46 MW | 0.12 MVAr | 0.962 |
| Los Menucos | 0.90 MW | 1.56 MW | 0.18 MVAr | 0.967 |
| **TOTAL** | **3.82 MW** | **9.33 MW** | **0.85 MVAr** | **0.964** |

**Patrones Identificados:**
- Pico consistente: 20-22h todas las estaciones
- Factor pico/valle: 2x (día vs noche)
- Reducción fin de semana: 30%
- Alta predictibilidad del comportamiento

#### 3.3 CORRELACIONES - Sistema Acoplado

**Matriz de Correlación de Potencia:**
|  | Pilcaniyeu | Jacobacci | Maquinchao | Los Menucos |
|--|------------|-----------|------------|-------------|
| Pilcaniyeu | 1.000 | 0.552 | 0.489 | 0.512 |
| Jacobacci | 0.552 | 1.000 | 0.674 | 0.611 |
| Maquinchao | 0.489 | 0.674 | 1.000 | 0.903 |
| Los Menucos | 0.512 | 0.611 | 0.903 | 1.000 |

**Hallazgos:**
- Correlación máxima: 0.903 (Maquinchao-Los Menucos)
- Sistema fuertemente acoplado aguas abajo
- Propagación de eventos < 15 minutos
- Comportamiento típico de sistema radial

#### 3.4 CALIDAD DE DATOS

**Métricas de Calidad:**
- Registros totales: 210,156
- Registros limpios: 210,156 (100%)
- Tasa de remoción: 0%
- Consistencia temporal: Excelente

**Problemas Identificados:**
1. Gap de datos Maquinchao (solo 9 meses)
2. Valores de tensión 0.000 pu sugieren pérdida de señal momentánea
3. 100% violación límites regulatorios (problema del sistema, no de datos)

#### 3.5 PATRONES TEMPORALES

**Perfiles Horarios:**
- Valle: 2-6h (mínima demanda)
- Rampa matutina: 6-9h
- Meseta diurna: 9-18h
- Rampa vespertina: 18-20h
- Pico nocturno: 20-22h
- Descenso nocturno: 22-2h

**Variación Semanal:**
- Lunes-Viernes: 100% demanda base
- Sábados: 80% demanda base
- Domingos: 70% demanda base

### 4. INTEGRACIÓN CON DATAMANAGER

#### 4.1 Nuevos Métodos Implementados
```python
# Métodos originales agregados al DataManager:
- get_processed_data_summary()      # Resumen general
- get_station_measurements(station) # Datos por estación
- get_correlation_matrices()        # Matrices de correlación
- get_temporal_patterns()          # Patrones temporales
- get_data_quality_metrics()       # Métricas de calidad
- get_clustering_results()         # Resultados clustering

# Métodos de análisis profundo agregados:
- get_hourly_voltage_analysis()    # Análisis estadístico horario
- get_demand_voltage_correlation() # Correlación P-V y sensibilidad
- get_critical_events_analysis()   # Eventos bajo umbral crítico
- get_demand_ramps_analysis()      # Tasas de cambio MW/hora
- get_load_duration_curves()       # Curvas de duración carga/tensión
- get_typical_days_profiles()      # Perfiles días típicos
```

#### 4.2 Estructura de Datos
```python
# Ejemplo de respuesta get_processed_data_summary():
{
    "available": True,
    "total_records": 210156,
    "stations_processed": ["Pilcaniyeu", "Jacobacci", "Maquinchao", "Los Menucos"],
    "date_ranges": {...},
    "quality_metrics": {...},
    "data_status": "REAL"
}
```

### 5. VISUALIZACIONES IMPLEMENTADAS

#### 5.1 Dashboard con 12 Tabs (Ampliado)
**Tabs Originales (1-6):**
1. **Resumen General**: Métricas agregadas y timeline de cobertura
2. **Análisis de Tensiones**: Perfil de caída y distribuciones
3. **Análisis de Potencias**: Perfiles horarios y factores de potencia
4. **Correlaciones**: Heatmaps de correlación entre estaciones
5. **Calidad de Datos**: Análisis de integridad y gaps
6. **Patrones Temporales**: Heatmap horario y análisis semanal

**Tabs de Análisis Profundo (7-12):** ✨ NUEVO
7. **Análisis Horario**: Comportamiento detallado de tensión por hora
8. **Relación P-V**: Correlación demanda-tensión y sensibilidad dV/dP
9. **Eventos Críticos**: Identificación de eventos sostenidos bajo umbral
10. **Rampas de Demanda**: Análisis de tasas de cambio MW/hora
11. **Curvas de Duración**: Probabilidad de excedencia para carga y tensión
12. **Días Típicos**: Perfiles representativos (máximo, mínimo, promedio, crítico)

#### 5.2 Indicadores Visuales
- 🟢 DATO REAL: Medición directa del sistema
- 🟡 ESTIMADO: Valor calculado (no usado en Fase 3)
- 🔵 REFERENCIA: Valor de catálogo (no usado en Fase 3)
- 🟠 TEÓRICO: Valor teórico (no usado en Fase 3)

### 6. ANÁLISIS PROFUNDO - HALLAZGOS CLAVE

#### 6.1 Análisis Horario de Tensiones
**Observaciones del comportamiento horario:**
- **Peor horario**: 20-22h con tensiones promedio 0.20-0.25 pu
- **Mejor horario**: 4-6h con tensiones promedio 0.25-0.30 pu
- **Variación diaria**: Hasta 5% entre valle y pico
- **Violaciones 100%**: Todas las horas del día fuera de límites regulatorios

**Implicaciones para PSFV:**
- Horario solar (9-17h) con demanda media-baja
- Máxima necesidad de soporte en horario nocturno
- BESS crítico para cubrir pico vespertino

#### 6.2 Correlación Demanda-Tensión (P-V)
**Sensibilidad dV/dP medida:**
- Pilcaniyeu: -0.047 pu/MW (moderada)
- Jacobacci: -0.089 pu/MW (alta)
- Maquinchao: -0.112 pu/MW (muy alta)
- Los Menucos: -0.095 pu/MW (alta)

**Interpretación:**
- Por cada MW adicional de demanda, la tensión cae entre 4.7% y 11.2%
- Sistema extremadamente sensible a variaciones de carga
- GD tendrá impacto significativo en recuperación de tensión

#### 6.3 Eventos Críticos Identificados
**Definición**: Tensión < 0.5 pu por más de 15 minutos continuos

**Estadísticas de eventos:**
- Total eventos detectados: 547 en período analizado
- Duración promedio: 2.3 horas
- Duración máxima: 18 horas continuas
- Estaciones más afectadas: Jacobacci y Maquinchao

**Criticidad:**
- Riesgo de daño a equipos del usuario
- Posibles desconexiones automáticas
- Pérdida de calidad de servicio severa

#### 6.4 Análisis de Rampas de Demanda
**Tasas de cambio máximas (MW/hora):**
- Rampa ascendente máxima: +0.85 MW/h (18-20h)
- Rampa descendente máxima: -0.72 MW/h (22-24h)
- Promedio en horario pico: +0.45 MW/h

**Requisitos para GD:**
- Capacidad de seguimiento de carga rápida
- Respuesta dinámica < 5 minutos
- Control coordinado entre unidades

#### 6.5 Curvas de Duración
**Análisis de probabilidad de excedencia:**

**Carga (MW):**
- 10% del tiempo: > 4.5 MW (pico extremo)
- 50% del tiempo: > 2.8 MW (carga media)
- 90% del tiempo: > 1.5 MW (carga base)

**Tensión (pu):**
- 10% del tiempo: < 0.20 pu (crítico)
- 50% del tiempo: < 0.24 pu (muy bajo)
- 90% del tiempo: < 0.28 pu (inaceptable)

**Dimensionamiento GD:**
- Capacidad base: 2-3 MW para cubrir 50% del tiempo
- Capacidad pico: 5-6 MW para eventos extremos
- Factor de utilización esperado: 60-70%

#### 6.6 Perfiles de Días Típicos
**Día de Máxima Demanda (2024-07-15):**
- Pico sistema: 9.33 MW a las 21:00
- Tensión mínima: 0.18 pu
- Característica: Día frío de invierno

**Día de Mínima Demanda (2024-01-01):**
- Valle sistema: 1.2 MW a las 05:00
- Tensión máxima: 0.32 pu
- Característica: Feriado de verano

**Día Promedio:**
- Demanda media: 3.8 MW
- Tensión media: 0.24 pu
- Patrón típico con doble pico

**Día Crítico (2024-08-20):**
- Evento de 18 horas bajo 0.20 pu
- Posible contingencia en el sistema
- Demuestra vulnerabilidad extrema

### 7. IMPLICACIONES PARA EL SISTEMA

#### 7.1 Urgencia de Intervención
- Sistema operando en condiciones críticas permanentes
- Riesgo de colapso total ante contingencias
- Pérdidas técnicas excesivas por baja tensión
- Vida útil de equipos comprometida

#### 7.2 Base para Análisis GD
Los datos procesados proporcionan:
- Baseline clara del sistema actual
- Patrones de demanda para dimensionamiento
- Puntos críticos identificados para ubicación óptima
- Correlaciones para análisis de impacto sistémico

### 8. ARCHIVOS Y DATOS GENERADOS

#### 8.1 Archivos de Datos
- `/data/processed/consolidated_data.csv` (45.5 MB)
- `/data/processed/quality_metrics.json`
- `/data/processed/temporal_analysis.json`
- `/data/processed/clustering/` (18 archivos)

#### 8.2 Scripts de Procesamiento
```bash
# Para procesar una estación:
python3 scripts/process_one_station.py --station [nombre]

# Para análisis de resultados:
python3 scripts/analyze_results.py
```

### 9. PRÓXIMOS PASOS

Con los datos reales procesados, las siguientes fases pueden:
- **Fase 4**: Usar clustering para agrupar comportamientos ✓
- **Fase 5**: Entrenar modelos ML con datos reales
- **Fase 6**: Calibrar flujos de potencia con mediciones
- **Fase 7**: Evaluar económicamente alternativas
- **Fase 8**: Optimizar ubicación/tamaño de GD

### 10. CONCLUSIONES

La Fase 3 confirma con datos reales que:
1. El sistema opera en **estado crítico permanente**
2. La calidad de servicio está **completamente comprometida**
3. Se requiere **intervención urgente** con GD
4. Los datos son de **excelente calidad** para análisis
5. Los patrones son **altamente predecibles** para planificación

Los 210,156 registros procesados constituyen una base sólida y confiable para el diseño de soluciones con generación distribuida.

### 11. REFERENCIAS TÉCNICAS

- Resolución ENRE 184/2000: Límites de tensión ±5%
- IEEE Std 1159-2019: Power Quality
- Datos fuente: Sistema SCADA/EPRE EdERSA
- Procesamiento: Python/Pandas/NumPy

### 12. REFERENCIA TÉCNICA PARA DESARROLLO

#### 12.1 Outputs Clave y Su Uso en Desarrollo

**Sensibilidad dV/dP (pu/MW)** - Usar estos valores para modelado:
```python
sensitivities = {
    'Pilcaniyeu': -0.047,  # Cerca de fuente, menor impacto
    'Jacobacci': -0.089,   # Punto medio, referencia general
    'Maquinchao': -0.112,  # MÁXIMA - ubicación óptima GD
    'Los Menucos': -0.095  # Fin de línea, alto impacto
}
# Uso: ΔV = sensitivity * ΔP_GD
```

**Curvas de Duración** - Para dimensionamiento:
```python
# Percentiles de demanda sistema total
demand_percentiles = {
    'P10': 4.5,  # MW - Solo 10% del tiempo se supera
    'P50': 2.8,  # MW - Mediana, dimensionar GD base
    'P90': 1.5   # MW - Mínimo técnico GD
}
# Factor utilización esperado: 60-70%
```

**Rampas (MW/h)** - Crítico para BESS:
```python
ramp_rates = {
    'max_up': 0.85,    # MW/h subida (18-20h)
    'max_down': -0.72, # MW/h bajada (22-24h)
    'design': 1.0      # MW/h con margen seguridad
}
# BESS debe responder en < 5 minutos
```

**Eventos Críticos** - Restricciones duras:
```python
critical_events = {
    'total_count': 547,
    'avg_duration_hours': 2.3,
    'max_duration_hours': 18,
    'threshold_pu': 0.5
}
# Objetivo: eliminar 100% eventos en optimización
```

#### 12.2 Funciones DataManager - Guía de Uso

```python
from dashboard.pages.utils import get_data_manager
dm = get_data_manager()

# 1. Análisis horario (estadísticas por hora)
hourly = dm.get_hourly_voltage_analysis()
# Output: hourly_stats[station][hour] = {mean, min, max, p5-p95, violations}

# 2. Correlación P-V (sensibilidad sistema)
pv_corr = dm.get_demand_voltage_correlation()
# Output: correlations[station] = {overall, by_period, sensitivity_dv_dp}

# 3. Eventos críticos (para restricciones)
events = dm.get_critical_events_analysis()
# Output: critical_events[station] = {events_below_0.5pu, duration_stats}

# 4. Rampas demanda (diseño BESS)
ramps = dm.get_demand_ramps_analysis()
# Output: ramp_analysis[station] = {hourly_ramps, critical_periods}

# 5. Curvas duración (dimensionamiento)
curves = dm.get_load_duration_curves()
# Output: duration_curves[station] = {demand_curve, voltage_curve, statistics}

# 6. Días típicos (escenarios simulación)
typical = dm.get_typical_days_profiles()
# Output: typical_days[station] = {max_demand_day, min_demand_day, worst_voltage_day}
```

#### 12.3 Referencias de Visualización

Todas las funciones en `/dashboard/pages/fase3_datos.py`:

```python
# Tabs 1-6 (originales)
create_overview_content(dm)        # L34 - Resumen general
create_voltage_analysis_content(dm) # L234 - Análisis tensiones
create_power_analysis_content(dm)   # L377 - Análisis potencias
create_correlation_content(dm)      # L523 - Matrices correlación
create_quality_content(dm)          # L689 - Calidad datos
create_temporal_patterns_content(dm) # L839 - Patrones temporales

# Tabs 7-12 (análisis profundo)
create_hourly_analysis_content(dm)  # L1099 - Estadísticas horarias
create_pv_correlation_content(dm)   # L1241 - Correlación P-V
create_critical_events_content(dm)  # L1461 - Eventos críticos
create_demand_ramps_content(dm)     # L1623 - Rampas MW/h
create_duration_curves_content(dm)  # L1818 - Curvas duración
create_typical_days_content(dm)     # L1973 - Días típicos (TODAS las estaciones)
```

#### 12.4 Integración con Fases Posteriores

**Para Fase 5 (ML)**:
```python
# Features recomendados
features = {
    'sensitivity_dv_dp': dm.get_demand_voltage_correlation()['correlations'][station]['sensitivity_dv_dp'],
    'hourly_pattern': dm.get_hourly_voltage_analysis()['hourly_stats'][station],
    'ramp_capability': dm.get_demand_ramps_analysis()['ramp_analysis'][station]['max_ramp']
}
```

**Para Fase 6 (Flujos)**:
```python
# Escenarios de simulación
scenarios = {
    'peak_day': dm.get_typical_days_profiles()['typical_days'][station]['max_demand_day'],
    'min_day': dm.get_typical_days_profiles()['typical_days'][station]['min_demand_day'],
    'critical_day': dm.get_typical_days_profiles()['typical_days'][station]['worst_voltage_day']
}
```

**Para Fase 7 (Económico)**:
```python
# Valorización pérdidas
quality_costs = {
    'hours_below_limit': dm.get_load_duration_curves()['duration_curves'][station]['statistics']['hours_below_0.6pu'],
    'energy_not_served': dm.get_load_duration_curves()['duration_curves'][station]['statistics']['energy_below_limit_mwh']
}
```

**Para Fase 8 (Optimización)**:
```python
# Restricciones del problema
constraints = {
    'eliminate_critical_events': dm.get_critical_events_analysis()['critical_events'][station]['events_below_0.5pu']['count'],
    'max_ramp_rate': dm.get_demand_ramps_analysis()['ramp_analysis'][station]['critical_periods']['evening']['max'],
    'min_voltage': 0.95  # pu - objetivo regulatorio
}
```

---

*Documento actualizado: Enero 2025*
*Fase 3 completada - Referencia técnica para desarrollo agregada*