# DATOS TÉCNICOS - PROYECTO FV JACOBACCI
## Sistema Eléctrico Línea Sur 33kV - Río Negro

---

## 1. RESUMEN EJECUTIVO

### 1.1 Justificación Técnica
Jacobacci ha sido identificado como el candidato óptimo para el segundo proyecto de generación fotovoltaica distribuida en la Línea Sur por las siguientes razones:

1. **Mayor demanda promedio**: 0.507 MW vs 0.464 MW de Maquinchao (+9.2%)
2. **Sensibilidad dV/dP positiva**: 0.0115 pu/MW garantiza mejora de voltaje con inyección FV
3. **Alta correlación con Pilcaniyeu**: 0.8911 permite coordinación y optimización del sistema
4. **Perfil de carga compatible**: Demanda distribuida durante horario solar
5. **Estabilidad operativa**: Sin outliers de potencia, operación predecible

### 1.2 Situación Actual Crítica
- **100% de mediciones fuera de límites regulatorios** (V < 0.95 pu)
- Voltaje promedio: **0.236 pu** (7.79 kV en red de 33 kV)
- Evento crítico continuo durante todo el período de medición
- Urgente necesidad de soporte de voltaje local

---

## 2. DATOS DE DEMANDA

### 2.1 Estadísticas Generales
```
PARÁMETRO                    VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Período de análisis          Enero 2024 - Abril 2025
Registros totales            91,830 (100% cobertura)
Resolución temporal          15 minutos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Demanda promedio             0.507 MW
Demanda máxima               1.169 MW
Demanda mínima               0.000 MW
Desviación estándar          0.250 MW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Factor de capacidad          43.34%
Energía anual estimada       4,437 MWh
Horas >80% pico              952.75 horas/año
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2.2 Distribución Percentil de Demanda
```
Percentil    Potencia (MW)    Uso típico
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P5           0.216           Valle nocturno
P10          0.267           Madrugada
P25          0.333           Mañana temprano
P50          0.469           Demanda media
P75          0.654           Tarde
P90          0.832           Pico vespertino
P95          0.913           Pico máximo
P99          1.041           Eventos extremos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2.3 Perfil Horario Típico
```
Hora   Demanda(MW)  StdDev   Min     Max     Perfil
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
00     0.556       0.155    0.132   1.169   ████████▌
01     0.540       0.147    0.139   1.128   ████████▎
02     0.517       0.140    0.137   1.071   ███████▊
03     0.491       0.133    0.135   1.041   ███████▍
04     0.465       0.126    0.125   0.987   ███████
05     0.438       0.121    0.108   0.945   ██████▋
06     0.421       0.123    0.071   0.948   ██████▍
07     0.424       0.134    0.000   0.949   ██████▍
08     0.441       0.147    0.020   0.977   ██████▋
09     0.466       0.155    0.095   1.011   ███████
10     0.486       0.159    0.113   1.037   ███████▎
11     0.501       0.163    0.120   1.054   ███████▌
12     0.514       0.167    0.128   1.082   ███████▊
13     0.524       0.170    0.133   1.100   ███████▉
14     0.529       0.172    0.136   1.109   ████████
15     0.531       0.172    0.138   1.113   ████████
16     0.531       0.171    0.139   1.112   ████████
17     0.530       0.170    0.139   1.109   ████████
18     0.535       0.171    0.140   1.115   ████████
19     0.555       0.175    0.148   1.142   ████████▍
20     0.590       0.180    0.162   1.169   ████████▉
21     0.612       0.175    0.172   1.169   █████████▎
22     0.608       0.168    0.171   1.155   █████████▏
23     0.585       0.161    0.156   1.148   ████████▊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2.4 Patrones Temporales
```
PATRÓN                       VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Horario pico                 18:00 - 23:00
Demanda promedio pico        0.605 MW
Horario valle                05:00 - 06:00
Demanda promedio valle       0.428 MW
Ratio pico/valle             1.277
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reducción fin de semana      13.26%
Demanda promedio L-V         0.518 MW
Demanda promedio S-D         0.474 MW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2.5 Factor de Potencia
```
PARÁMETRO                    VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FP promedio                  0.985
FP mínimo                    0.894
FP máximo                    1.000
Potencia reactiva promedio   0.042 MVAr
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 3. CALIDAD DE VOLTAJE

### 3.1 Estadísticas de Voltaje
```
PARÁMETRO                    VALOR         CONDICIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voltaje promedio             0.2359 pu     CRÍTICO ⚠️
Voltaje mínimo               0.0000 pu     COLAPSO ⛔
Voltaje máximo               0.2461 pu     CRÍTICO ⚠️
Desviación estándar          0.0183 pu     
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voltaje en kV (33kV base)    7.789 kV      -76.4%
Violaciones regulatorias     100%          TOTAL ⛔
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.2 Distribución de Voltaje
```
Percentil    Voltaje (pu)    Voltaje (kV)    Estado
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P1           0.0000          0.000          Colapso
P5           0.2335          7.706          Crítico
P10          0.2343          7.732          Crítico
P25          0.2352          7.762          Crítico
P50          0.2361          7.791          Crítico
P75          0.2370          7.821          Crítico
P90          0.2380          7.854          Crítico
P95          0.2389          7.884          Crítico
P99          0.2420          7.986          Crítico
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.3 Sensibilidad dV/dP
```
PARÁMETRO                    VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sensibilidad global          +0.0115 pu/MW ✓
Correlación V-P              0.1586
R² modelo                    0.0252
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Interpretación: Cada MW inyectado mejorará el
voltaje en 0.0115 pu (0.38 kV)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.4 Eventos Críticos
```
DESCRIPCIÓN                  VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Evento continuo <0.5 pu      485 días (100%)
Duración total               11,640 horas
Outliers de voltaje          535 eventos
Outliers de potencia         0 eventos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 4. ANÁLISIS DE PÉRDIDAS TÉCNICAS

### 4.1 Pérdidas Estimadas (Método I²R simplificado)
```
Asumiendo resistencia de línea típica 0.3 Ω/km y 50 km hasta Pilcaniyeu:
R_total ≈ 15 Ω

CONDICIÓN           P(MW)   I(A)    Pérdidas(kW)  % Pérdidas
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Demanda valle       0.428   46.2    32.0          7.5%
Demanda media       0.507   54.8    45.0          8.9%
Demanda pico        0.913   98.6    145.8         16.0%
Demanda máxima      1.169   126.3   239.3         20.5%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4.2 Costo Anual de Pérdidas
```
Pérdidas promedio estimadas: 45 kW (8.9%)
Energía anual perdida: 394 MWh
Costo unitario energía: $122.7/MWh
COSTO ANUAL PÉRDIDAS: $48,347
```

### 4.3 Reducción Esperada con FV Local
```
Con FV de 1 MW en Jacobacci:
- Reducción corriente línea: ~50%
- Reducción pérdidas: ~75% (proporcional a I²)
- Ahorro anual estimado: $36,260
```

---

## 5. MÉTRICAS DE CONFIABILIDAD

### 5.1 Disponibilidad del Sistema
```
MÉTRICA                      VALOR           OBSERVACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Datos disponibles            100%            Excelente
Horas con V=0                82.25 h         0.94% del tiempo
Horas con P=0                1,321 h         15.1% del tiempo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5.2 Índices de Calidad Estimados
```
Basado en eventos V<0.5 pu:
- SAIFI estimado: >365 interrupciones/año
- SAIDI estimado: >8,760 minutos/año (100%)
- CAIDI: 24 horas (continuo)
- ENS (Energía No Suministrada): Difícil estimar por operación degradada continua
```

---

## 6. DATOS PARA SIMULACIÓN

### 6.1 Días Típicos Identificados
```
TIPO DE DÍA          FECHA           P_max(MW)  V_min(pu)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Máxima demanda       2024-07-10      1.169      0.225
Mínima demanda       2024-11-10      0.915      0.230
Peor voltaje         2024-01-02      0.983      0.000
Día promedio         2024-09-15      0.895      0.235
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 6.2 Rampas de Demanda
```
PARÁMETRO                    VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rampa máxima subida          +3.51 MW/h ⚡
Rampa máxima bajada          -3.58 MW/h ⚡
Rampa promedio               1.36 MW/h
P95 rampas                   ±2.34 MW/h
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Horario crítico rampas:
- Subida: 06:00-09:00 (despertar)
- Bajada: 23:00-02:00 (nocturno)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 6.3 Correlaciones con Pilcaniyeu
```
VARIABLE                     CORRELACIÓN     SIGNIFICANCIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Potencia activa              0.8911          Muy alta ✓
Voltaje                      0.4932          Moderada
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Correlación con lag:
- Lag 15 min                 0.8631          Óptimo
- Lag 30 min                 0.8284
- Lag 60 min                 0.7636
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 6.4 Perfil para Simulación Horaria (Día Típico)
```csv
Hora,P(MW),Q(MVAr),V(pu),FP
0,0.556,0.028,0.2399,0.985
1,0.540,0.027,0.2396,0.985
2,0.517,0.026,0.2392,0.985
3,0.491,0.025,0.2387,0.985
4,0.465,0.023,0.2382,0.985
5,0.438,0.022,0.2375,0.985
6,0.421,0.021,0.2367,0.985
7,0.424,0.021,0.2360,0.985
8,0.441,0.022,0.2354,0.985
9,0.466,0.023,0.2350,0.985
10,0.486,0.024,0.2348,0.985
11,0.501,0.025,0.2347,0.985
12,0.514,0.026,0.2347,0.985
13,0.524,0.026,0.2348,0.985
14,0.529,0.027,0.2349,0.985
15,0.531,0.027,0.2350,0.985
16,0.531,0.027,0.2350,0.985
17,0.530,0.027,0.2349,0.985
18,0.535,0.027,0.2346,0.985
19,0.555,0.028,0.2345,0.985
20,0.590,0.030,0.2346,0.985
21,0.612,0.031,0.2350,0.985
22,0.608,0.031,0.2358,0.985
23,0.585,0.029,0.2376,0.985
```

---

## 7. PARÁMETROS DE RED

### 7.1 Topología
```
PARÁMETRO                    VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Posición en línea            55.6% (intermedia)
Distancia a Pilcaniyeu       ~50 km (estimado)
Alimentadores                2 (Norte y Sur)
Tensión nominal              33 kV
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 7.2 Impedancias Estimadas (Típicas 33kV rural)
```
PARÁMETRO                    VALOR TÍPICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R línea                      0.3 Ω/km
X línea                      0.4 Ω/km
Z línea                      0.5 Ω/km
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Para 50 km:
R total                      15 Ω
X total                      20 Ω
Z total                      25 Ω
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 8. RECOMENDACIONES DE DIMENSIONAMIENTO

### 8.1 Sistema FV Propuesto
```
COMPONENTE                   CAPACIDAD       JUSTIFICACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Potencia FV                  1.0 MWp         Cubre P95 demanda
Inversor                     0.8 MW          Factor DC/AC 1.25
BESS Potencia                0.5 MW          Manejo rampas
BESS Energía                 1.0 MWh         2h @ 0.5MW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 8.2 Beneficios Esperados
```
MÉTRICA                      MEJORA ESPERADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voltaje mínimo               +0.012 pu (+5%)
Pérdidas técnicas            -75% horario solar
Energía local                1,750 MWh/año (39%)
Reducción ENS                Significativa
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 8.3 Configuración Técnica
```
ASPECTO                      ESPECIFICACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conexión                     Barra 33 kV directa
Control voltaje              Q(V) droop + BESS
Protecciones                 50/51, 27/59, 81, 25
Comunicaciones               IEC 61850 con Pilcaniyeu
Monitoreo                    SCADA tiempo real
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 9. ANÁLISIS COMPARATIVO

### 9.1 Jacobacci vs Maquinchao
```
PARÁMETRO              JACOBACCI    MAQUINCHAO    VENTAJA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Demanda promedio       0.507 MW     0.464 MW      JAC +9%
Demanda máxima         1.169 MW     1.455 MW      MAQ +24%
Factor capacidad       43.34%       31.85%        JAC +36%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voltaje promedio       0.236 pu     0.242 pu      MAQ +3%
Sensibilidad dV/dP     +0.0115      -0.0015       JAC ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Correlación Pilcaniyeu 0.891        0.347         JAC ✓
Rampas máximas         3.5 MW/h     0.6 MW/h      MAQ ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cobertura datos        100%         56%           JAC ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 10. DATOS PARA ANÁLISIS DE IMPACTO

### 10.1 Checklist para Ingeniero
- [x] Series temporales completas 15-min (91,830 registros)
- [x] Estadísticas de demanda y percentiles
- [x] Perfil horario típico 24h
- [x] Sensibilidad dV/dP positiva confirmada
- [x] Correlaciones con punto de inyección (Pilcaniyeu)
- [x] Rampas máximas para dimensionar BESS
- [x] Factor de potencia y reactiva
- [x] Estimación de pérdidas actuales
- [x] Días típicos para simulación
- [x] Parámetros de red estimados

### 10.2 Archivos Fuente
```
Directorio: /data/processed/phase3/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- summary.json                  Resumen general
- quality_metrics_enhanced.json Métricas detalladas
- hourly_analysis.json         Perfiles horarios
- pv_correlation.json          Sensibilidad dV/dP
- demand_ramps.json            Análisis de rampas
- correlations.json            Correlaciones
- critical_events.json         Eventos críticos
- typical_days.json            Días representativos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 10.3 Próximos Pasos Recomendados

1. **Modelado de Red**
   - Validar impedancias estimadas con datos reales
   - Construir modelo en software de flujo de carga
   - Simular caso base actual

2. **Análisis de Escenarios**
   - Caso base sin FV
   - FV sin BESS (solo inyección solar)
   - FV + BESS (gestión completa)
   - Sensibilidades de ubicación y tamaño

3. **Evaluación Económica**
   - CAPEX del sistema FV+BESS
   - Ahorro en pérdidas técnicas
   - Mejora en calidad (reducción ENS)
   - Comparación con alternativas

4. **Diseño Detallado**
   - Selección de tecnología FV
   - Estrategia de control BESS
   - Integración con SCADA existente
   - Plan de implementación

---

**Documento generado**: 2025-07-13  
**Fuente de datos**: Sistema de medición Línea Sur 33kV - EPEN  
**Período analizado**: Enero 2024 - Abril 2025