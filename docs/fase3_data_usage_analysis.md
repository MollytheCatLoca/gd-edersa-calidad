# Análisis del Uso de Datos en Fase 3: Procesamiento y Preparación para ML

## Resumen Ejecutivo

La Fase 3 del proyecto representa el núcleo analítico del sistema, procesando y preparando datos masivos del sistema eléctrico para su visualización inmediata y futura aplicación en modelos de Machine Learning.

### Métricas Clave:
- **Volumen Total**: 210,156 registros procesados
- **Estaciones Monitoreadas**: 4 (Pilcaniyeu, Jacobacci, Maquinchao, Los Menucos)
- **Período de Análisis**: Enero 2024 - Abril 2025
- **Tipos de Análisis**: 12 módulos especializados
- **Datos para ML**: ~40MB en formato Parquet optimizado

### Hallazgo Crítico:
**100% de las mediciones están fuera de los límites regulatorios (V < 0.95 pu)**, lo que convierte este dataset en un caso de estudio único para ML en sistemas eléctricos en condiciones extremas.

## 1. Inventario Detallado de Fuentes de Datos

### 1.1 Archivos JSON - Análisis Descriptivo

| Archivo | Tamaño | Contenido Principal | Uso en Dashboard |
|---------|---------|-------------------|------------------|
| `summary.json` | 4.9K | Resumen general, rangos de fechas | Tab 1: Overview |
| `quality_metrics_enhanced.json` | 5.5K | Calidad de datos, estadísticas V/P | Tab 2: Calidad |
| `temporal_patterns_full.json` | 26K | Patrones horarios/diarios/mensuales | Tab 3: Temporal |
| `correlations.json` | 2.8K | Correlaciones V entre estaciones | Tab 4: Correlaciones |
| `hourly_analysis.json` | 32K | Estadísticas horarias detalladas | Tab 5: Análisis Horario |
| `pv_correlation.json` | 1.8K | Sensibilidad dV/dP | Tab 6: Sensibilidad |
| `critical_events.json` | 6.4K | Eventos V < 0.5 pu | Tab 7: Eventos Críticos |
| `demand_ramps.json` | 26K | Análisis de rampas MW/h | Tab 8: Rampas |
| `duration_curves.json` | 8.2K | Curvas de duración | Tab 9: Duración |
| `typical_days.json` | 35K | Perfiles día típico | Tab 10: Días Típicos |

### 1.2 Archivos Parquet - Features para ML

| Estación | Tamaño | Registros | Período |
|----------|---------|-----------|---------|
| Pilcaniyeu | 10M | 46,107 | 485 días |
| Jacobacci | 16M | 91,830 | 485 días |
| Maquinchao | 5.3M | 26,112 | 272 días |
| Los Menucos | 9.3M | 46,107 | 485 días |

**Archivo adicional**: `feature_scaler.pkl` - Escalador sklearn para normalización

## 2. Arquitectura del Flujo de Datos

### 2.1 Pipeline de Procesamiento

```
SCADA/EPRE (Origen)
    ↓
Raw Data (CSV)
    ↓
Data Processing Pipeline
    ├── Limpieza y Validación
    ├── Cálculo de Métricas
    └── Feature Engineering
         ↓
Almacenamiento Procesado
    ├── JSON (Análisis/Visualización)
    └── Parquet (ML Features)
         ↓
Consumidores
    ├── Dashboard Dash (Fase 3)
    └── Modelos ML (Futuro)
```

### 2.2 Métodos del Data Manager

```python
# Mapeo de funciones a archivos de datos
data_manager_methods = {
    'get_comprehensive_summary()': 'summary.json',
    'get_enhanced_quality_metrics()': 'quality_metrics_enhanced.json',
    'get_temporal_patterns_full()': 'temporal_patterns_full.json',
    'get_correlations()': 'correlations.json',
    'get_hourly_voltage_analysis()': 'hourly_analysis.json',
    'get_demand_voltage_correlation()': 'pv_correlation.json',
    'get_critical_events_analysis()': 'critical_events.json',
    'get_demand_ramps_analysis()': 'demand_ramps.json',
    'get_load_duration_curves()': 'duration_curves.json',
    'get_typical_days_profiles()': 'typical_days.json'
}
```

## 3. Estructura de Datos para ML

### 3.1 Features Extraídas

#### Features Temporales
- `hour`: Hora del día (0-23)
- `day_of_week`: Día de la semana (0-6)
- `month`: Mes (1-12)
- `is_weekend`: Booleano
- `is_peak_hour`: Booleano (18-23h)

#### Features de Voltaje
- `v_mean`: Voltaje promedio (pu)
- `v_std`: Desviación estándar
- `v_min`: Mínimo en ventana
- `v_max`: Máximo en ventana
- `v_violations`: Contador V < 0.95

#### Features de Potencia
- `p_total`: Potencia activa (MW)
- `q_total`: Potencia reactiva (MVAr)
- `s_total`: Potencia aparente (MVA)
- `power_factor`: Factor de potencia

#### Features Derivadas
- `ramp_rate`: Tasa de cambio MW/h
- `rolling_mean_1h`: Media móvil 1 hora
- `rolling_std_1h`: Desv. estándar móvil
- `lag_15min`: Valor t-1
- `lag_1h`: Valor t-4
- `lag_24h`: Valor t-96

### 3.2 Volumen y Características

```
Total Features por Registro: ~30 columnas
Resolución Temporal: 15 minutos
Total Registros: 210,156
Tamaño Comprimido: ~40MB (Parquet)
Tamaño Descomprimido: ~150MB
```

## 4. Insights Clave para Estrategia ML

### 4.1 Patrones Identificados

#### Sensibilidad del Sistema
- **dV/dP máxima**: -0.112 pu/MW (Maquinchao)
- **Interpretación**: 1 MW adicional reduce voltaje en 11.2%
- **Implicación ML**: Feature crítica para predicción de estabilidad

#### Correlaciones
- **Entre estaciones**: >0.8 para voltajes
- **P-V local**: -0.83 a -0.98 (correlación negativa fuerte)
- **Implicación ML**: Modelos multi-estación serán más precisos

#### Patrones Temporales
- **Pico demanda**: 20-22h (100% consistente)
- **Reducción fin de semana**: 10-15%
- **Variación estacional**: ±20% verano/invierno

### 4.2 Eventos Críticos

```
Eventos V < 0.5 pu: 547 totales
Duración promedio: 1.4 horas
Duración máxima: 4.25 horas
Horas críticas totales: 769
```

### 4.3 Rampas de Demanda

```
Rampa máxima up: 2.72 MW/h
Rampa máxima down: -2.70 MW/h
P95 rampas: ±0.47 MW/h
Tiempo respuesta requerido: <5 minutos
```

## 5. Recomendaciones para Modelos ML

### 5.1 Predicción de Demanda (Corto Plazo)

**Arquitectura Sugerida**: LSTM + Attention
```python
features_demanda = [
    'hour', 'day_of_week', 'is_weekend',
    'lag_15min', 'lag_1h', 'lag_24h',
    'rolling_mean_1h', 'temperature'  # si disponible
]
```

**Métricas Objetivo**:
- MAPE < 5% (15 min ahead)
- MAPE < 10% (1 hora ahead)

### 5.2 Predicción de Voltaje

**Arquitectura Sugerida**: XGBoost con features engineered
```python
features_voltaje = [
    'p_total', 'q_total', 'power_factor',
    'hour', 'ramp_rate',
    'neighbor_station_voltage',  # por alta correlación
    'sensitivity_dvdp'  # pre-calculada
]
```

**Métricas Objetivo**:
- MAE < 0.02 pu
- Detección eventos críticos: Recall > 95%

### 5.3 Optimización BESS

**Enfoque**: Reinforcement Learning (PPO/SAC)
```python
state_space = {
    'soc_bess': float,  # 0-1
    'current_demand': float,
    'predicted_demand_1h': float,
    'current_voltage': float,
    'hour': int,
    'electricity_price': float  # si disponible
}

action_space = {
    'charge_discharge_rate': float  # -1 a 1
}
```

### 5.4 Detección de Anomalías

**Arquitectura Sugerida**: Autoencoder + Isolation Forest
```python
baseline_features = [
    'v_mean', 'v_std', 'p_total', 'q_total',
    'power_factor', 'ramp_rate'
]
```

**Umbrales de Anomalía**:
- Reconstrucción error > 2σ
- Isolation score < -0.5

## 6. Consideraciones de Implementación

### 6.1 Pipeline de Datos en Tiempo Real

```python
# Pseudo-código para integración
class RealTimeMLPipeline:
    def __init__(self):
        self.scaler = load('feature_scaler.pkl')
        self.model_demand = load('demand_predictor.pkl')
        self.model_voltage = load('voltage_predictor.pkl')
        
    def process_new_data(self, raw_data):
        # 1. Validación
        validated = self.validate_data(raw_data)
        
        # 2. Feature Engineering
        features = self.extract_features(validated)
        
        # 3. Normalización
        scaled = self.scaler.transform(features)
        
        # 4. Predicción
        demand_pred = self.model_demand.predict(scaled)
        voltage_pred = self.model_voltage.predict(scaled)
        
        # 5. Post-procesamiento
        return self.post_process(demand_pred, voltage_pred)
```

### 6.2 Métricas de Monitoreo

1. **Data Quality**:
   - Completitud: >95%
   - Latencia: <1 minuto
   - Drift detection: KS test

2. **Model Performance**:
   - Predicción demanda: MAPE
   - Predicción voltaje: MAE
   - Eventos críticos: Precision/Recall

3. **Business Metrics**:
   - Violaciones evitadas
   - Eficiencia BESS
   - Costo operacional

## 7. Roadmap de Implementación ML

### Fase 1: Modelos Baseline (1-2 meses)
- [ ] Predictor demanda simple (ARIMA/Prophet)
- [ ] Detector anomalías básico
- [ ] Dashboard métricas ML

### Fase 2: Modelos Avanzados (2-3 meses)
- [ ] LSTM para predicción demanda
- [ ] XGBoost para voltaje
- [ ] Sistema de alertas

### Fase 3: Optimización (3-4 meses)
- [ ] RL para BESS
- [ ] Ensemble models
- [ ] AutoML pipeline

### Fase 4: Producción (4-6 meses)
- [ ] API REST para predicciones
- [ ] Integración SCADA
- [ ] Monitoreo continuo

## 8. Conclusiones

La Fase 3 ha establecido una base sólida de datos procesados y features engineering que facilita la implementación de modelos ML. Los principales diferenciadores de este dataset son:

1. **Condiciones Extremas**: 100% fuera de límites proporciona casos únicos
2. **Alta Resolución**: 15 minutos permite capturar dinámicas rápidas
3. **Multi-estación**: Correlaciones permiten modelos distribuidos
4. **Features Ricas**: 30+ variables pre-procesadas

El siguiente paso natural es implementar modelos predictivos que aprovechen estos datos para:
- Anticipar condiciones críticas
- Optimizar recursos (BESS/GD)
- Reducir violaciones regulatorias
- Mejorar calidad de servicio

---

**Documento generado**: 2025-07-10  
**Autor**: Sistema de Análisis Automático  
**Versión**: 1.0