# FASE 3 - REFERENCIA RÁPIDA PARA DESARROLLO

## Datos Disponibles
- **CSV Principal**: 210,156 registros en `/data/processed/consolidated_data.csv`
- **Columnas**: station, timestamp, p_total, q_total, v_pu, fp, hour, date
- **Resolución**: 15 minutos (96 muestras/día)
- **Período**: Enero 2024 - Abril 2025

## Llamadas DataManager Rápidas

```python
from dashboard.pages.utils import get_data_manager
dm = get_data_manager()

# === MÉTODOS BÁSICOS (Ya existían) ===
summary = dm.get_processed_data_summary()  # Resumen general
stations = dm.get_station_measurements('Pilcaniyeu')  # Datos por estación
correlations = dm.get_correlation_matrices()  # Correlaciones entre estaciones
temporal = dm.get_temporal_patterns()  # Patrones temporales básicos
quality = dm.get_data_quality_metrics()  # Métricas de calidad
clustering = dm.get_clustering_results()  # Resultados clustering

# === MÉTODOS NUEVOS FASE 3 (Líneas 644-1057) ===
hourly = dm.get_hourly_voltage_analysis()  # Stats detalladas por hora
pv_corr = dm.get_demand_voltage_correlation()  # Sensibilidad dV/dP
events = dm.get_critical_events_analysis()  # Eventos V < 0.5pu > 15min
ramps = dm.get_demand_ramps_analysis()  # Rampas MW/h máximas
curves = dm.get_load_duration_curves()  # Curvas duración carga/tensión
typical = dm.get_typical_days_profiles()  # Días típicos TODAS estaciones
```

## Valores Clave para Cálculos

### Sistema Total
- **Demanda promedio**: 3.82 MW
- **Demanda máxima**: 9.33 MW
- **Factor pico/valle**: 2x
- **Reducción fin de semana**: 30%
- **Pico consistente**: 20-22h

### Sensibilidad dV/dP (pu/MW)
```python
sensitivity = {
    'Pilcaniyeu': -0.047,   # Moderada
    'Jacobacci': -0.089,    # Alta
    'Maquinchao': -0.112,   # MUY ALTA ← Mejor ubicación GD
    'Los Menucos': -0.095   # Alta
}
# Ejemplo: 1 MW en Maquinchao mejora tensión 0.112 pu (11.2%)
```

### Dimensionamiento GD
```python
# Basado en curvas de duración
gd_sizing = {
    'base_90pct': 1.5,    # MW - Cubre 90% del tiempo
    'media_50pct': 2.8,   # MW - Cubre 50% del tiempo
    'pico_10pct': 4.5,    # MW - Solo 10% del tiempo
    'factor_utilizacion': 0.65  # 60-70% esperado
}
```

### Diseño BESS
```python
bess_requirements = {
    'rampa_max': 1.0,      # MW/h (0.85 medido + margen)
    'duracion_min': 2.3,   # horas (eventos promedio)
    'energia': 3.0,        # MWh mínimo por sitio
    'respuesta': 5         # minutos máximo
}
```

### Eventos Críticos
```python
critical_constraints = {
    'total_eventos': 547,
    'duracion_promedio': 2.3,   # horas
    'duracion_maxima': 18,      # horas
    'umbral': 0.5,              # pu
    'objetivo': 0               # Eliminar 100%
}
```

## Estructuras de Datos - Outputs

### get_hourly_voltage_analysis()
```python
{
    "available": True,
    "hourly_stats": {
        "Pilcaniyeu": {
            0: {  # hora 0
                "mean": 0.607,
                "min": 0.0,
                "max": 0.65,
                "violations": 1921,  # < 0.95 pu
                "severe_violations": 45  # < 0.5 pu
            },
            # ... horas 1-23
        },
        # ... otras estaciones
    }
}
```

### get_demand_voltage_correlation()
```python
{
    "correlations": {
        "Maquinchao": {
            "overall": -0.75,
            "sensitivity_dv_dp": -0.112,  # pu/MW
            "demand_at_low_v": {
                "v_below_0.5": 0.8,  # MW promedio
                "v_below_0.6": 0.7
            }
        }
    }
}
```

### get_typical_days_profiles()
```python
{
    "typical_days": {
        "Pilcaniyeu": {
            "max_demand_day": {
                "date": "2024-07-15",
                "hourly_demand": {0: 3.2, 1: 3.0, ...},
                "hourly_voltage": {0: 0.58, 1: 0.59, ...}
            },
            # min_demand_day, worst_voltage_day, average_day
        }
    }
}
```

## Archivos de Visualización

Dashboard completo: `/dashboard/pages/fase3_datos.py`

### Funciones por Tab (12 total)
```python
# Tab 1-6 (originales)
create_overview_content()      # L34
create_voltage_analysis_content()  # L234
create_power_analysis_content()    # L377
create_correlation_content()       # L523
create_quality_content()           # L689
create_temporal_patterns_content() # L839

# Tab 7-12 (nuevos análisis profundos)
create_hourly_analysis_content()   # L1099
create_pv_correlation_content()    # L1241
create_critical_events_content()   # L1461
create_demand_ramps_content()      # L1623
create_duration_curves_content()   # L1818
create_typical_days_content()      # L1973 ← MODIFICADO: todas las estaciones
```

## Notas Importantes

1. **DataManager es la ÚNICA fuente de verdad** - Nunca cargar datos directamente
2. **Tab 12 modificado** - Ahora muestra todas las estaciones, no solo Pilcaniyeu
3. **Sensibilidad Maquinchao** - Ubicación óptima para GD por máxima sensibilidad
4. **Eventos críticos** - 547 eventos son restricción dura para optimización
5. **BESS crítico** - Sin BESS no se puede cubrir pico nocturno con solar

## Comandos Útiles

```bash
# Ver estructura de datos
python3 -c "import pandas as pd; df=pd.read_csv('data/processed/consolidated_data.csv'); print(df.info())"

# Verificar dashboard
python3 dashboard/app_multipagina.py

# Ver solo Fase 3
# Navegar a http://localhost:8050/fase3-datos
```

---
*Referencia rápida para desarrollo - Fase 3*
*Última actualización: Enero 2025*