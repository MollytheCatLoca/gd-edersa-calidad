# FASE 0 - COMPRENSIÓN DE LA TOPOLOGÍA DE RED - COMPLETADA ✅

**Fecha de Inicio**: 15 de Julio 2025  
**Fecha de Finalización**: 15 de Julio 2025  
**Estado**: COMPLETADA

## 🎯 Objetivos Alcanzados

1. ✅ Mapeo completo de la estructura alimentador-transformador
2. ✅ Análisis de patrones espaciales y correlaciones
3. ✅ Identificación de problemas sistémicos vs aleatorios
4. ✅ Caracterización completa de 128 alimentadores
5. ✅ Identificación de 10 alimentadores críticos prioritarios

## 📊 Métricas Clave de la Red

### Estructura General
- **Total Alimentadores**: 128
- **Total Transformadores**: 2,690
- **Total Usuarios**: 158,476
- **Capacidad Total**: 401.7 MVA
- **Tasa Global de Problemas**: 45.9%
- **Tasa de Fallas**: 20.6%

### Distribución de Estados
- **Correcta**: 1,454 transformadores (54.1%)
- **Penalizada**: 681 transformadores (25.3%)
- **Fallida**: 555 transformadores (20.6%)

## 🗂️ Estructura de Datos Generados

### 1. Datos Base Enriquecidos
```
📁 data/processed/network_analysis/
├── 📄 alimentadores_caracterizados.csv (128 alimentadores)
├── 📄 transformadores_con_topologia.csv (2,690 transformadores)
├── 📄 patrones_espaciales_alimentadores.csv (105 patrones)
├── 📄 correlacion_distancia_calidad.csv (82 correlaciones)
├── 📄 clusters_espaciales_problemas.csv (240 hotspots)
├── 📄 tests_independencia_fallas.csv (82 tests)
├── 📄 patrones_temporales.csv (128 patrones)
├── 📄 problemas_sistemicos.csv (101 clasificaciones)
└── 📄 patrones_red.json (resumen de patrones)
```

### 2. Reportes de Análisis
```
📁 reports/
├── 📄 00_network_topology_report.json
├── 📄 01_spatial_correlation_report.json
├── 📄 02_quality_correlation_report.json
├── 📄 fase0_caracterizacion_completa.json
├── 📄 resumen_ejecutivo_fase0.json
├── 📄 resumen_ejecutivo_fase0.md
└── 📄 caracterizacion_red_edersa.pdf
```

### 3. Visualizaciones
```
📁 reports/figures/
├── 📄 network_topology_analysis.png
├── 📄 spatial_patterns_feeders.png
├── 📄 spatial_patterns_summary.png
└── 📄 quality_correlations.png
```

## 🔑 Accesos a Datos Clave

### Transformadores con Topología Enriquecida
```python
# Archivo principal con todos los transformadores
transformers_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/transformadores_con_topologia.csv"

# Campos clave agregados:
- alimentador_diametro_km       # Extensión del alimentador
- alimentador_densidad_trafos_km2  # Densidad de transformadores
- alimentador_centroid_x/y      # Centro geográfico del alimentador
- alimentador_es_lineal         # Si tiene distribución lineal
- alimentador_tasa_problemas    # Tasa de problemas del alimentador
- dist_a_centroide_km          # Distancia al centro del alimentador
- posicion_relativa            # Posición relativa (0=centro, 1=borde)
```

### Alimentadores Caracterizados
```python
# Archivo con características de cada alimentador
feeders_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/alimentadores_caracterizados.csv"

# Campos principales:
- num_transformadores
- potencia_total_mva
- usuarios_totales
- tasa_problemas
- extension_x_km, extension_y_km
- area_bbox_km2
- diametro_km
- densidad_trafos_km2
- es_lineal
- compacidad
```

### Patrones Espaciales
```python
# Análisis de patrones espaciales por alimentador
spatial_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/patrones_espaciales_alimentadores.csv"

# Campos clave:
- patron_distribucion  # lineal/agrupado/regular/aleatorio
- r_squared_linealidad
- clustering_coefficient
- morans_i            # Autocorrelación espacial
- autocorrelacion_espacial  # positiva/ninguna/negativa
```

### Problemas Sistémicos
```python
# Clasificación de problemas por alimentador
systemic_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/problemas_sistemicos.csv"

# Campos:
- tipo_problema      # Sistémico/Parcial/Aleatorio
- patron_geografico  # Concentrado/Periférico/Distribuido
```

## 🔍 Hallazgos Principales

### 1. Patrones de Distribución Espacial
- **64 alimentadores** con patrón aleatorio
- **23 alimentadores** con patrón regular
- **18 alimentadores** con patrón lineal (probablemente siguiendo rutas)

### 2. Autocorrelación Espacial de Fallas
- **60 alimentadores** sin autocorrelación (fallas aleatorias)
- **17 alimentadores** con autocorrelación negativa
- **5 alimentadores** con autocorrelación positiva (fallas agrupadas)

### 3. Correlaciones Técnicas Significativas
```
Variable                  | Correlación con Problemas | p-value
-------------------------|---------------------------|----------
Potencia                 | 0.308                     | <0.001
Q_Usuarios               | 0.304                     | <0.001
num_circuitos           | 0.253                     | <0.001
factor_utilizacion      | 0.146                     | <0.001
usuarios_por_kva        | 0.145                     | <0.001
```

### 4. Clasificación de Problemas
- **41 alimentadores** con problemas sistémicos de calidad degradada
- **13 alimentadores** con problemas sistémicos de fallas generalizadas
- **16 alimentadores** con problemas parciales localizados
- **31 alimentadores** con casos aislados aleatorios

### 5. Top 10 Alimentadores Críticos

| # | Alimentador | Transformadores | Usuarios | Tasa Problemas | Tipo Problema |
|---|------------|-----------------|----------|----------------|---------------|
| 1 | MITRE | 46 | 5,793 | 69.7% | Sistémico - Calidad degradada |
| 2 | LINEA SUR | 98 | 4,687 | 29.6% | Parcial - Problemas localizados |
| 3 | FLOR DEL VALLE | 19 | 4,822 | 84.2% | Sistémico - Fallas generalizadas |
| 4 | 8 CENTRAL CIPOLLETTI | 33 | 4,110 | 75.8% | Sistémico - Calidad degradada |
| 5 | STEFENELLI | 54 | 3,290 | 68.5% | Sistémico - Calidad degradada |
| 6 | 002 CENTRO | 29 | 4,079 | 79.3% | Sistémico - Calidad degradada |
| 7 | BRENTANA | 17 | 3,969 | 70.6% | Sistémico - Calidad degradada |
| 8 | RURAL | 88 | 3,956 | 13.6% | Aleatorio - Casos aislados |
| 9 | 2 CENTRAL CIPOLLETTI | 31 | 3,564 | 74.2% | Sistémico - Calidad degradada |
| 10 | 001 JAMAICA | 60 | 1,824 | 43.3% | Parcial - Problemas localizados |

## 📊 Consultas SQL/Python Útiles

### Cargar datos completos con pandas
```python
import pandas as pd
import sqlite3

# Opción 1: Desde CSV
df_transformers = pd.read_csv('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/transformadores_con_topologia.csv')
df_feeders = pd.read_csv('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/alimentadores_caracterizados.csv')

# Opción 2: Desde base de datos (si aplica)
conn = sqlite3.connect('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/edersa_transformadores.db')
df = pd.read_sql_query("SELECT * FROM transformadores", conn)
```

### Filtrar alimentadores críticos
```python
# Alimentadores con problemas sistémicos
sistemic = df_feeders[df_feeders['tasa_problemas'] > 0.5]

# Alimentadores lineales con problemas
linear_problems = df_feeders[
    (df_feeders['es_lineal'] == True) & 
    (df_feeders['tasa_problemas'] > 0.3)
]

# Transformadores en zonas críticas
critical_trafos = df_transformers[
    df_transformers['Alimentador'].isin(
        ['MITRE', 'FLOR DEL VALLE', '8 CENTRAL CIPOLLETTI']
    )
]
```

### Análisis por zonas
```python
# Resumen por zona geográfica
by_zone = df_transformers.groupby('zona_geografica').agg({
    'Codigo': 'count',
    'Q_Usuarios': 'sum',
    'Resultado': lambda x: (x != 'Correcta').mean()
}).rename(columns={'Codigo': 'num_transformadores', 'Resultado': 'tasa_problemas'})
```

## 🎯 Implicaciones para Siguientes Fases

### Para Fase 2 - Clustering
1. **Usar alimentadores como base** para clustering inicial
2. **Priorizar alimentadores sistémicos** (54 identificados)
3. **Considerar patrones espaciales** al formar clusters:
   - Lineales: soluciones a lo largo de la línea
   - Agrupados: soluciones centralizadas
   - Aleatorios: evaluar caso por caso

### Para Dimensionamiento GD
1. **Variables correlacionadas** indican sobrecarga:
   - Alta potencia + muchos usuarios = mayor riesgo
   - Factor de utilización alto = necesidad de refuerzo
2. **Alimentadores con autocorrelación positiva** sugieren problemas de infraestructura común

### Consideraciones Técnicas
1. **Extensión promedio**: algunos alimentadores >100km (desafío para GD)
2. **Densidad variable**: desde 0.001 hasta >10 trafos/km²
3. **Multi-sucursal**: 4 alimentadores cruzan sucursales (coordinación necesaria)

## ✅ Validaciones Realizadas

1. **Consistencia de datos**: 2,690 transformadores únicos verificados
2. **Cobertura geográfica**: Solo 1 transformador sin coordenadas
3. **Integridad de mediciones**: Todos con al menos 1 medición
4. **Clasificación completa**: 100% de alimentadores clasificados

## 📝 Notas Técnicas

### Metodologías Aplicadas
- **DBSCAN** para clustering espacial
- **Moran's I** para autocorrelación espacial
- **Regresión lineal** para detectar patrones lineales
- **Chi-cuadrado** para independencia de fallas
- **Spearman** para correlaciones no paramétricas

### Limitaciones Identificadas
1. Algunos alimentadores con valores infinitos en extensión (datos extremos)
2. No hay información directa de caídas de tensión (dV/dt)
3. Patrones temporales limitados (solo rango de mediciones)

## 🔬 EXTENSIÓN FASE 0 - ANÁLISIS ELÉCTRICO BASADO EN TEORÍA

**Fecha de Extensión**: 15 de Julio 2025  
**Motivación**: Enriquecimiento con características eléctricas basadas en documento teórico de sistemas de distribución

### Objetivos Adicionales Alcanzados
1. ✅ Reconstrucción de topología eléctrica usando MST (Minimum Spanning Tree)
2. ✅ Cálculo de impedancias y caídas de tensión con fórmulas trifásicas
3. ✅ Estimación de cargas y factores de potencia por tipo de zona
4. ✅ Análisis de modos de falla (térmico y dieléctrico)
5. ✅ Preparación de dataset enriquecido para Machine Learning

### Scripts Adicionales Implementados

#### 04_mst_topology_reconstruction.py
- Reconstruye topología radial más probable por alimentador
- Identifica ubicación de subestaciones (3 estrategias)
- Calcula características topológicas avanzadas:
  - Número de saltos desde subestación
  - kVA y usuarios aguas abajo
  - Centralidad de intermediación
  - Identificación de nodos hoja

#### 05_electrical_distance_calculation.py
- Implementa tabla de impedancias del documento:
  - 1/0 AWG: R=0.55, X=0.48 Ω/km (rural)
  - 4/0 AWG: R=0.22, X=0.45 Ω/km (troncal)
- Calcula caída de tensión: ΔV = √3 × I × (R×cos(φ) + X×sin(φ))
- Evalúa sensibilidad a hundimientos dinámicos
- Genera índice de debilidad eléctrica

#### 06_load_estimation_features.py
- Clasifica tipo de carga por kVA/usuario:
  - < 0.5: residencial bajo consumo
  - 0.5-2.0: residencial típico
  - 2.0-5.0: mixto residencial/comercial
  - > 5.0: comercial/industrial
- Estima factores de potencia (0.75-0.92)
- Calcula factores de diversidad y utilización
- Evalúa riesgo de sobrecarga térmica

#### 07_failure_mode_features.py
- Índice de estrés térmico (Arrhenius):
  - Temperatura hot-spot estimada
  - Factor de pérdida de vida
  - Años de vida perdidos anualmente
- Índice de estrés dieléctrico:
  - Probabilidad de descargas parciales
  - Vulnerabilidad a transitorios
- Features de vecindario (radio 500m)
- Índice compuesto de vulnerabilidad

#### 08_ml_ready_dataset.py
- Integración de 70+ features eléctricas
- Balanceo de clases con SMOTE
- Normalización con StandardScaler
- División 70/15/15 (train/val/test)
- Análisis de importancia con Random Forest

### Datos Adicionales Generados

```
📁 data/processed/electrical_analysis/
├── 📄 transformadores_mst_topology.csv         # Topología MST reconstruida
├── 📄 transformadores_distancia_electrica.csv  # Impedancias y caídas de tensión
├── 📄 transformadores_carga_estimada.csv       # Cargas P, Q, FP estimados
├── 📄 transformadores_indices_riesgo.csv       # Índices de vulnerabilidad
├── 📁 ml_datasets/
│   ├── 📄 X_train.csv, X_val.csv, X_test.csv
│   ├── 📄 y_train.csv, y_val.csv, y_test.csv
│   ├── 📄 feature_importance.csv
│   ├── 📄 metadata.json
│   └── 📄 scaler.pkl
└── 📁 visualizations/
    ├── mst_topology_*.png
    ├── voltage_drop_profiles.png
    ├── load_analysis_overview.png
    ├── vulnerability_analysis.png
    └── ml_data_preparation.png
```

### Features Eléctricas Clave Generadas

**Topológicas MST:**
- `numero_saltos`: Distancia topológica desde subestación
- `kVA_aguas_abajo`: Carga total servida por el nodo
- `centralidad_intermediacion`: Importancia en la red
- `es_nodo_hoja`: Indicador de posición terminal

**Eléctricas:**
- `Z_acumulada`: Impedancia total hasta subestación (Ω)
- `caida_tension_percent`: Caída de tensión estimada (%)
- `indice_debilidad_electrica`: Normalizado 0-1
- `hundimiento_arranque_percent`: Sensibilidad a arranque de motores

**Carga y Utilización:**
- `tipo_carga`: residencial/comercial/industrial/rural_agricola
- `factor_potencia_estimado`: 0.75-0.92 según tipo
- `factor_utilizacion_pico`: Carga pico / capacidad nominal
- `indice_sobrecarga`: >1 indica sobrecarga

**Vulnerabilidad:**
- `indice_estres_termico_v2`: Estrés térmico compuesto
- `años_vida_perdidos_anual`: Por sobrecalentamiento
- `indice_estres_dielectrico`: Por problemas de tensión
- `indice_vulnerabilidad_compuesto`: Score global 0-1

### Estadísticas del Análisis Eléctrico

**Caída de Tensión:**
- Promedio: 3.8%
- Máxima: 15.2%
- Transformadores fuera de límite (>5%): 423 (15.7%)

**Factor de Potencia Estimado:**
- Promedio red: 0.87
- Zonas residenciales: 0.91
- Zonas industriales: 0.79

**Vulnerabilidad:**
- Crítica: 89 transformadores (3.3%)
- Alta: 267 transformadores (9.9%)
- Media: 578 transformadores (21.5%)

**Modos de Falla Probables:**
- Térmico: 1,087 (40.4%)
- Dieléctrico: 892 (33.2%)
- Mixto: 711 (26.4%)

### Top Features para ML (por importancia)

1. `indice_vulnerabilidad_compuesto`: 0.0821
2. `caida_tension_percent`: 0.0754
3. `kVA_aguas_abajo`: 0.0692
4. `indice_estres_termico_v2`: 0.0631
5. `Z_acumulada`: 0.0589
6. `factor_utilizacion_pico`: 0.0567
7. `numero_saltos`: 0.0523
8. `indice_estres_dielectrico`: 0.0498
9. `centralidad_intermediacion`: 0.0476
10. `tasa_problemas_vecindario`: 0.0443

### Validaciones Adicionales

1. **MST Conectividad**: 100% alimentadores con árbol válido
2. **Impedancias**: Valores dentro de rangos físicos esperados
3. **Conservación de Potencia**: kVA aguas abajo consistente
4. **Correlaciones**: Caída tensión correlaciona con fallas (r=0.42)

---

**Fase 0 Extendida completada exitosamente** ✅

Dataset enriquecido con 70+ features eléctricas listo para modelos ML de predicción de fallas basados en física de redes de distribución.