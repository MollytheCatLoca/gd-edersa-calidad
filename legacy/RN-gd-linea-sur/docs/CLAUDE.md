# ESTUDIO DE GENERACIÓN DISTRIBUIDA - LÍNEA SUR RÍO NEGRO
## Documentación Técnica del Proyecto

(Existing content remains unchanged)

### 13. DIRECTRICES DE EVOLUCIÓN DE SOFTWARE

#### DIRECTRIZ INTERNA PARA EVOLUCIÓN DE DATA_MANAGER_V2.PY

**OBJETIVO**
Mantener coherencia modular, evitar duplicaciones y contener la complejidad mientras ampliamos el BESS Suite y el resto del ecosistema Data Manager.

**UBICACIÓN Y TAXONOMÍA DE NUEVAS FUNCIONALIDADES**

- Carga / I-O → `data_loaders.py`. Ejemplos: nuevos formatos, validadores Pydantic, control de versiones de esquema.
- Analítica → `data_analytics.py`. Ejemplos: KPIs, modelos ML ligeros, pipelines de post-processing.
- Simulación PSFV + BESS → `solar_bess_simulator.py`. Ejemplos: estrategias adicionales, degradación, optimización.
- Coordinación / API pública → `data_manager_v2.py`. Solo wrappers thread-safe, composición de resultados, health-checks.
- Constantes e interfaces → `constants.py`, `models.py`. Ampliar enums y TypedDicts.

**REGLA DURA**: No insertar lógica de dominio en `data_manager_v2.py`; solo delegación y orquestación.

**CHECKLIST ANTES DE AÑADIR FUNCIÓN NUEVA**
a) Buscar colisiones (grep o búsqueda IDE).
b) Ver si puede refactorizarse o parametrizarse en un método existente.
c) Verificar uso de constants, models y el contenedor de inyección.
d) Estimar LOC y costo cognitivo; si >150 LOC o crea nuevo estado, discutir en PR Design Discussion.
e) Añadir tests y docstrings; actualizar documentación de fase o RFC correspondiente.

**PATRÓN DE NOMBRADO Y ANOTACIONES**
- Prefijos: `load_`, `calc_`, `simulate_`, `optimize_`, `export_`.
- Anotar exhaustivamente (→ DataResult, → ValidationResult, etc.).
- El meta de todo DataResult debe tener source, version y phase.

**DEBUG Y OBSERVABILIDAD**
- Usar `logger.debug` con módulo y función.
- Registrar hash de entrada cuando se use LRU cache para auditar hits/misses.

**ESTRATEGIA DE CRECIMIENTO CONTROLADO**
Si la propuesta supera THRESHOLD_COMPLEJIDAD (≈200 LOC o nueva dependencia externa) se abre RFC en #architecture y se agenda Code Walkthrough de 15 min. Métricas de acoplamiento y cobertura se revisan trimestralmente para plantear extracción a micro-paquetes.

**IDEAS EXTRA PARA EL BESS LAB**
- Modo "explain": devolver JSON con pasos intermedios (pérdidas, round-trip, SOC hora a hora).
- Heat-map interactivo de ΔV/ΔP vs tiempo para validar sensibilidad de `data_analytics`.
- Benchmark automático en CI: lanzar todas las estrategias y comparar KPIs contra golden set.

**TL;DR**

- Coloca el código donde toca según la tabla.
- Busca y reutiliza antes de escribir.
- Documenta y prueba cada aporte.
- Vigila complejidad y duplicidad para que el repo siga siendo mantenible y escalable.

**Fuentes**: Preguntar a ChatGPT

### 14. USO DE DATOS EN FASE 3 - PREPARACIÓN PARA ML

#### RESUMEN DE DATOS PROCESADOS
La Fase 3 procesa y prepara 210,156 registros del sistema eléctrico para análisis y ML:

**Volumen de Datos:**
- 4 estaciones: Pilcaniyeu, Jacobacci, Maquinchao, Los Menucos
- Período: Enero 2024 - Abril 2025
- Resolución: 15 minutos
- 100% de mediciones fuera de límites regulatorios (V < 0.95 pu)

**Archivos de Análisis (JSON):**
- `summary.json`: Resumen general y rangos de fechas
- `quality_metrics_enhanced.json`: Calidad de datos y estadísticas
- `temporal_patterns_full.json`: Patrones horarios/diarios/mensuales
- `correlations.json`: Correlaciones entre estaciones
- `hourly_analysis.json`: Estadísticas horarias detalladas
- `pv_correlation.json`: Sensibilidad dV/dP (hasta -0.112 pu/MW)
- `critical_events.json`: 547 eventos críticos (V < 0.5 pu)
- `demand_ramps.json`: Rampas hasta 2.7 MW/h
- `duration_curves.json`: Curvas de duración y percentiles
- `typical_days.json`: Perfiles de días típicos

**Features para ML (Parquet):**
- ~40MB total en formato comprimido
- 30+ features por registro incluyendo:
  - Temporales: hora, día, mes, is_weekend, is_peak_hour
  - Voltaje: mean, std, min, max, violations
  - Potencia: P, Q, S, factor de potencia
  - Derivadas: rampas, rolling stats, lags (15min, 1h, 24h)

**Insights Clave para ML:**
1. Alta sensibilidad dV/dP permite predicción precisa de estabilidad
2. Correlación >0.8 entre estaciones sugiere modelos multi-estación
3. Patrones temporales consistentes (pico 20-22h)
4. Rampas requieren respuesta <5 minutos para BESS

**Documentación Detallada:**
Ver `/docs/fase3_data_usage_analysis.md` para análisis completo y recomendaciones de modelos ML.

### 15. BUENAS PRÁCTICAS DE DESARROLLO

- SIEMPRE USA VENV CUANDO CORRES EN BASH ... SINO NO VA A CORRER
- cuando corres python en consola .. dejame ver el contenido

### 16. OBJETIVO PRINCIPAL DEL ANÁLISIS DE RED (FASE 5)

#### PROBLEMA IDENTIFICADO
La red de 33kV Línea Sur opera con niveles de tensión críticos:
- 100% de mediciones < 0.95 pu (límite regulatorio)
- Eventos críticos con V < 0.5 pu registrados
- Sensibilidad dV/dP = -0.112 pu/MW en Maquinchao

#### HIPÓTESIS A VALIDAR
**Es más económico mejorar los niveles de tensión mediante recursos FV distribuidos que mediante inversiones tradicionales o expansión de GD térmica.**

#### ALTERNATIVAS A EVALUAR

1. **Tradicional (CAPEX intensivo)**
   - Nuevas líneas o reconductoring
   - Compensación reactiva (capacitores)
   - Cambiadores de tap bajo carga
   - Costo estimado: Alto CAPEX, bajo OPEX

2. **Expansión GD Térmica**
   - Ampliar de 1.8 MW a 3 MW en Los Menucos
   - Costo: $122.7/MWh
   - Disponibilidad: 4h/día (13.3% FC)
   - Limitación: Horario fijo, no coincide con pico

3. **Recursos FV Distribuidos (HIPÓTESIS)**
   - Múltiples puntos de inyección
   - Coincidencia con demanda diurna
   - Reducción pérdidas por generación local
   - Costo estimado: CAPEX medio, OPEX bajo

#### MÉTRICAS DE COMPARACIÓN
- VPN a 25 años de cada alternativa
- Costo por pu de mejora de voltaje ($/Δpu)
- Reducción de pérdidas técnicas
- Mejora en índices de calidad (SAIFI, SAIDI)
- Capacidad de crecimiento futuro

#### METODOLOGÍA FASE 5
1. Establecer caso base actual (V < 0.95 pu)
2. Calcular costo de pérdidas y ENS actual
3. Simular cada alternativa con dt=1h día típico
4. Calcular mejora ΔV y reducción pérdidas
5. Evaluar VPN de cada solución
6. Análisis de sensibilidad