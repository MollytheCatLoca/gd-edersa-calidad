# FASE 1: COMPRENSIÓN PROFUNDA DE LA RED
## Análisis del Sistema Eléctrico Línea Sur y Generación Distribuida Actual

### 1. RESUMEN EJECUTIVO

La Fase 1 completó el análisis integral del sistema de transmisión de 33 kV de la Línea Sur de Río Negro, identificando sus características técnicas, limitaciones operativas y evaluando el sistema de Generación Distribuida (GD) existente en Los Menucos.

**Hallazgos Críticos:**
- Sistema radial de 270 km operando al límite de su capacidad
- Caída de tensión documentada del 20-41% (crítica)
- GD actual de 3 MW con costo operativo de $138.6/MWh @ 4h/día
- Potencial de reducción de costos a $87/MWh operando 8h/día

### 2. DATOS DE ENTRADA (INPUTS)

#### 2.1 Topología del Sistema
- **Fuente**: Unifilar Línea Sur (PDF procesado)
- **Extensión**: 270 km desde ET Pilcaniyeu hasta ET Los Menucos
- **Configuración**: Radial siguiendo Ruta Nacional 23
- **Tensión nominal**: 33 kV

#### 2.2 Estaciones Transformadoras
| ET | km | Transformación | P (MW) | Q (MVAr) | FP |
|---|---|---|---|---|---|
| Pilcaniyeu | 0 | 132/33 kV | - | - | - |
| Comallo | 70 | 33/13.2 kV | 0.30 | 0.10 | 0.949 |
| Onelli | 120 | 33/13.2 kV | 0.10 | 0.04 | 0.928 |
| Jacobacci | 150 | 33/13.2 kV | 1.45 | 0.60 | 0.924 |
| Maquinchao | 210 | 33/13.2 kV | 0.50 | 0.10 | 0.981 |
| Aguada de Guerra | 240 | 33 kV | 0.05 | 0.01 | 0.981 |
| Los Menucos | 270 | 33/13.2 kV | 1.40 | 0.20 | 0.990 |
| **TOTAL** | - | - | **3.80** | **1.05** | **0.964** |

#### 2.3 Sistema de Regulación
- **Pilcaniyeu**: RBC 132/33 kV (cabecera)
- **Jacobacci**: Regulador serie 33/33 kV (km 150)
- **Los Menucos**: Regulador serie 13.2/13.2 kV (km 270)
- **Rango combinado**: ±30% (insuficiente para condiciones actuales)

#### 2.4 Generación Distribuida Los Menucos
- **Potencia**: 2 × 1.5 MW = 3 MW total
- **Tecnología**: Motogeneradores a gas natural
- **Conexión**: 13.2 kV en barra ET Los Menucos
- **Operación actual**: 4 horas/día, FC = 0.8
- **Estado**: En operación (alquilados)

### 3. ANÁLISIS REALIZADOS

#### 3.1 Análisis de Topología
- Mapeo completo de nodos y tramos
- Identificación de longitudes entre ETs
- Caracterización de transformadores
- Evaluación del sistema de regulación

#### 3.2 Análisis de Cargas
- Carga total sistema: 3.80 MW / 1.05 MVAr
- Factor de potencia promedio: 0.964 (bueno)
- Distribución geográfica desbalanceada
- Concentración en Jacobacci (38%) y Los Menucos (37%)

#### 3.3 Análisis Económico GD
- Costos operativos actuales desglosados
- Clasificación fijos vs variables
- Análisis de sensibilidad por horas de operación
- Comparación con precio de compra EdERSA

### 4. RESULTADOS CLAVE (OUTPUTS)

#### 4.1 Métricas del Sistema
- **Longitud total**: 270 km
- **Carga total**: 3.80 MW (1.05 MVAr)
- **Pérdidas estimadas**: ~0.4 MW (10%)
- **Caída de tensión máxima**: 20-41%
- **Capacidad disponible pico**: NULA

#### 4.2 Costos GD Los Menucos (USD)
| Concepto | Mensual | Anual | % |
|----------|---------|-------|---|
| Alquiler equipos | 25,000 | 300,000 | 61.8% |
| OPEX | 7,730 | 92,754 | 19.1% |
| Combustible | 6,480 | 77,754 | 16.0% |
| O&M | 1,250 | 15,000 | 3.1% |
| **TOTAL** | **40,460** | **485,508** | 100% |

#### 4.3 Indicadores Unitarios
- **Costo por MWh**: $138.6 USD/MWh (@ 4h/día)
- **Costo por kW instalado**: $13.49 USD/kW-mes
- **Generación anual**: 3,504 MWh
- **Factor de utilización**: 13.3%

#### 4.4 Curva de Costos vs Horas Operación
| Horas/día | USD/MWh | Reducción |
|-----------|---------|-----------|
| 2 | 277.2 | - |
| 4 | 138.6 | Base |
| 6 | 103.9 | -25% |
| 8 | 87.2 | -37% |
| 10 | 78.3 | -44% |
| 12 | 72.7 | -48% |

### 5. DATOS ÚTILES PARA PRÓXIMAS FASES

#### 5.1 Parámetros Base del Sistema
```python
# Sistema eléctrico
TENSION_NOMINAL_KV = 33
LONGITUD_TOTAL_KM = 270
CARGA_TOTAL_MW = 3.80
CARGA_REACTIVA_MVAR = 1.05
FACTOR_POTENCIA = 0.964

# Puntos críticos identificados
TRAMOS_LARGOS = {
    "Pilcaniyeu-Comallo": 70,  # km
    "Jacobacci-Maquinchao": 60,  # km
    "Maquinchao-Los Menucos": 60  # km
}

# Estaciones con mayor carga
CARGAS_PRINCIPALES = {
    "Jacobacci": 1.45,  # MW (38%)
    "Los Menucos": 1.40,  # MW (37%)
    "Maquinchao": 0.50  # MW (13%)
}
```

#### 5.2 Costos de Referencia GD
```python
# Costos actuales validados
COSTO_ALQUILER_KW_MES = 8.33  # USD/kW-mes
COSTO_GAS_NATURAL = 0.11137  # USD/m³
CONSUMO_ESPECIFICO_GAS = 0.282  # m³/kWh
PRECIO_COMPRA_EDERSA = 60  # USD/MWh

# Alternativas para comparación
CONSUMO_GASOIL = 0.249  # L/kWh
PRECIO_GASOIL = 1.0  # USD/L
COSTO_GASOIL_MWH = 249  # USD/MWh (calculado)
```

#### 5.3 Restricciones Operativas
- Regulación insuficiente con equipos actuales
- Sin capacidad para nuevas cargas en horario pico
- Dependencia crítica de 3 reguladores
- GD Los Menucos opera solo 4h/día por costos

### 6. FUNCIONES Y HERRAMIENTAS CREADAS

#### 6.1 DataManager - Gestión Centralizada
```python
# Obtener datos de costos GD
gd_costs = dm.get_gd_costs()

# Calcular costo por MWh para cualquier escenario
result = dm.calculate_gd_cost_per_mwh(
    hours_per_day=8,  # horas operación
    fc=0.85,          # factor capacidad (opcional)
    gas_price=0.12    # precio gas (opcional)
)
# Returns: {
#   "cost_per_mwh": 87.2,
#   "annual_generation_mwh": 7446,
#   "annual_cost_usd": 649262,
#   "cost_breakdown": {...},
#   "cost_breakdown_percent": {...}
# }
```

#### 6.2 Dashboard - TAB6 Generación Distribuida
- Análisis completo de costos actuales
- Calculadora interactiva de escenarios
- Curva de costos vs horas de operación
- Visualización de estructura de costos

### 7. CONCLUSIONES Y RECOMENDACIONES

#### 7.1 Estado Crítico del Sistema
1. Sistema operando fuera de límites regulatorios
2. Sin margen para crecimiento de demanda
3. Pérdidas técnicas elevadas por baja tensión
4. Urgencia de implementar soluciones

#### 7.2 Oportunidades Identificadas
1. **Optimización GD actual**: Aumentar a 8h/día reduciría costo 37%
2. **Puntos para nueva GD**: Jacobacci y Maquinchao (alta carga y criticidad)
3. **Reducción de pérdidas**: GD distribuida mejoraría perfiles de tensión
4. **Diferimiento inversiones**: GD puede postergar ampliación transmisión

#### 7.3 Próximos Pasos (Fase 2+)
1. Modelado detallado de flujos de potencia
2. Análisis de ubicación óptima para GD adicional
3. Evaluación tecnologías (solar, híbrido)
4. Análisis beneficio-costo integral

### 8. ARCHIVOS Y REFERENCIAS

#### 8.1 Archivos de Datos
- `/data/processed/sistema_linea_sur.json` - Topología completa
- `/dashboard/pages/utils/data_manager.py` - Funciones de cálculo
- `/dashboard/pages/components/tab6_distributed_generation.py` - Análisis GD

#### 8.2 Documentación Relacionada
- `CLAUDE.md` - Documentación técnica del proyecto
- `README.md` - Resumen ejecutivo
- `/data/4 Unifilar Linea Sur.pdf` - Diagrama unifilar original

---

*Documento generado: Julio 2025*
*Fase 1 completada con análisis integral del sistema y costos GD*