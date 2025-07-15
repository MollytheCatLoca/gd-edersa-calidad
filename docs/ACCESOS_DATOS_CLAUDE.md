# 🔑 ACCESOS RÁPIDOS A DATOS - PROYECTO EDERSA

Este documento contiene todos los paths y accesos a datos importantes para uso en CLAUDE y análisis futuros.

## 📁 Paths de Archivos Principales

### Datos Crudos
```python
# Excel original
excel_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/Mediciones Originales EDERSA.xlsx"

# CSV convertido
csv_raw_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/raw/mediciones_edersa.csv"
```

### Datos Procesados
```python
# Transformadores limpios y enriquecidos
transformadores_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/transformadores_cleaned.csv"

# Agregaciones
sucursales_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/sucursales_agregadas.csv"
localidades_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/localidades_agregadas.csv"
zonas_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/zonas_geograficas.csv"

# Recomendaciones GD
gd_recommendations_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/gd_recommendations.json"

# Registros excluidos
excluded_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/excluded_records.csv"
```

### Datos de Análisis de Red (FASE 0)
```python
# Análisis de topología
alimentadores_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/alimentadores_caracterizados.csv"
transformadores_topologia_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/transformadores_con_topologia.csv"

# Análisis espacial
patrones_espaciales_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/patrones_espaciales_alimentadores.csv"
correlacion_distancia_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/correlacion_distancia_calidad.csv"
clusters_espaciales_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/clusters_espaciales_problemas.csv"

# Análisis de calidad
independencia_fallas_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/tests_independencia_fallas.csv"
patrones_temporales_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/patrones_temporales.csv"
problemas_sistemicos_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/problemas_sistemicos.csv"
```

### Base de Datos
```python
# SQLite database
db_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/edersa_transformadores.db"
```

### Datos de Análisis Eléctrico (FASE 0 EXTENDIDA)
```python
# Topología MST reconstruida
mst_topology_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/electrical_analysis/transformadores_mst_topology.csv"

# Análisis eléctrico
electrical_distance_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/electrical_analysis/transformadores_distancia_electrica.csv"
load_estimation_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/electrical_analysis/transformadores_carga_estimada.csv"
risk_indices_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/electrical_analysis/transformadores_indices_riesgo.csv"

# Datasets ML
ml_X_train = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/electrical_analysis/ml_datasets/X_train.csv"
ml_y_train = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/electrical_analysis/ml_datasets/y_train.csv"
ml_metadata = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/electrical_analysis/ml_datasets/metadata.json"
ml_feature_importance = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/electrical_analysis/ml_datasets/feature_importance.csv"
```

### Reportes
```python
# Reportes JSON del pipeline Fase 1
validation_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/01_validation_report.json"
cleaning_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/02_cleaning_report.json"
aggregations_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/03_aggregations_report.json"
criticality_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/04_criticality_report.json"

# Reportes JSON de Fase 0
topology_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/00_network_topology_report.json"
spatial_correlation_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/01_spatial_correlation_report.json"
quality_correlation_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/02_quality_correlation_report.json"
fase0_completa_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/fase0_caracterizacion_completa.json"

# Resúmenes ejecutivos
resumen_ejecutivo_json = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/resumen_ejecutivo_fase0.json"
resumen_ejecutivo_md = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/resumen_ejecutivo_fase0.md"

# PDF integrado
caracterizacion_pdf = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/caracterizacion_red_edersa.pdf"
```

## 🗄️ Estructura de Base de Datos

### Tablas Disponibles
1. **transformadores** (2,690 registros)
2. **sucursales** (42 registros)
3. **localidades** (81 registros)
4. **zonas_geograficas** (5 registros)
5. **oportunidades_gd** (831 registros)

### Campos Clave en Transformadores
```sql
-- Campos principales
Codigo                    -- ID único del transformador
N_Sucursal               -- Sucursal a la que pertenece
N_Localida               -- Localidad
Potencia                 -- Potencia en kVA
Q_Usuarios               -- Cantidad de usuarios
Resultado                -- Estado: Correcta/Penalizada/Fallida
Coord_X, Coord_Y         -- Coordenadas geográficas

-- Campos calculados
num_circuitos            -- Número de circuitos del transformador
quality_score            -- Score de calidad (0-1)
criticidad_compuesta     -- Índice de criticidad compuesto
prioridad_gd            -- Prioridad para GD: Muy Alta/Alta/Media/Baja
zona_geografica         -- Noroeste/Noreste/Suroeste/Sureste
tipo_zona               -- Rural/Periurbano/Urbano
size_category           -- Micro/Pequeño/Mediano/Grande
```

## 📊 Consultas SQL Útiles

### Transformadores Críticos
```sql
-- Top 10 transformadores más críticos
SELECT Codigo, N_Sucursal, N_Localida, Potencia, Q_Usuarios, 
       Resultado, criticidad_compuesta, prioridad_gd
FROM transformadores 
WHERE criticidad_compuesta > 0.5 
ORDER BY criticidad_compuesta DESC
LIMIT 10;
```

### Análisis por Sucursal
```sql
-- Sucursales con más problemas
SELECT N_Sucursal, 
       COUNT(*) as total_transformadores,
       SUM(CASE WHEN Resultado = 'Fallida' THEN 1 ELSE 0 END) as fallidas,
       SUM(Q_Usuarios) as usuarios_totales,
       AVG(criticidad_compuesta) as criticidad_promedio
FROM transformadores
GROUP BY N_Sucursal
HAVING fallidas > 0
ORDER BY fallidas DESC;
```

### Oportunidades GD
```sql
-- Mejores oportunidades para GD
SELECT codigo, sucursal, localidad, score, prioridad,
       capacidad_actual_kva, usuarios, tipo_gd_recomendado,
       capacidad_gd_kw
FROM oportunidades_gd 
WHERE prioridad = 'Muy Alta'
ORDER BY score DESC
LIMIT 20;
```

### Análisis Geográfico
```sql
-- Distribución por zona
SELECT zona_geografica,
       COUNT(*) as total,
       SUM(CASE WHEN Resultado = 'Fallida' THEN 1 ELSE 0 END) as fallidas,
       AVG(quality_score) as calidad_promedio,
       SUM(Q_Usuarios) as usuarios_totales
FROM transformadores
WHERE zona_geografica != 'Sin coordenadas'
GROUP BY zona_geografica
ORDER BY fallidas DESC;
```

## 🐍 Código Python para Acceso Rápido

### Leer Transformadores
```python
import pandas as pd
import sqlite3

# Desde CSV
df_transformadores = pd.read_csv('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/transformadores_cleaned.csv')

# Desde Base de datos
conn = sqlite3.connect('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/edersa_transformadores.db')
df_transformadores = pd.read_sql_query("SELECT * FROM transformadores", conn)
conn.close()
```

### Leer Recomendaciones GD
```python
import json

with open('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/gd_recommendations.json', 'r') as f:
    gd_recommendations = json.load(f)

# Top 5 oportunidades
top_5 = gd_recommendations[:5]
```

### Análisis Rápido
```python
# Cargar y analizar
df = pd.read_csv('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/transformadores_cleaned.csv')

# Resumen por estado
print(df['Resultado'].value_counts())

# Transformadores críticos
criticos = df[df['criticidad_compuesta'] > 0.5]
print(f"Transformadores críticos: {len(criticos)}")

# Por sucursal
por_sucursal = df.groupby('N_Sucursal').agg({
    'Codigo': 'count',
    'Q_Usuarios': 'sum',
    'criticidad_compuesta': 'mean'
}).round(3)
```

## 🔧 Scripts de Procesamiento

### Pipeline Completo
```bash
cd /Users/maxkeczeli/Proyects/gd-edersa-calidad
bash scripts/preprocessing/run_complete_pipeline.sh
```

### Scripts Individuales
```bash
# Directorio base
cd /Users/maxkeczeli/Proyects/gd-edersa-calidad/scripts/preprocessing/

# Ejecutar en orden:
python 00_excel_to_csv.py
python 01_validate_data.py
python 02_clean_enrich_data.py
python 03_create_aggregations.py
python 04_analyze_criticality.py
python 05_create_database.py
```

## 🚀 Dashboard

### Ejecutar Dashboard
```bash
cd /Users/maxkeczeli/Proyects/gd-edersa-calidad
venv/bin/python dashboard/app_edersa.py
```

### Acceso Web
```
http://localhost:8050
```

## 📈 Métricas Clave del Sistema

- **Total Transformadores**: 2,690
- **Total Circuitos**: 14,012
- **Usuarios Totales**: 158,476
- **Capacidad Total**: 401.7 MVA
- **Transformadores Críticos**: 555
- **Oportunidades GD Alta Prioridad**: 831
- **Inversión Estimada**: $32.9M USD

## 🔍 Filtros y Categorías

### Por Estado de Calidad
- Correcta: 1,655 (61.5%)
- Penalizada: 480 (17.8%)
- Fallida: 555 (20.6%)

### Por Tamaño
- Micro (< 25 kVA): 1,580
- Pequeño (25-100 kVA): 520
- Mediano (100-315 kVA): 511
- Grande (> 315 kVA): 79

### Por Zona Geográfica
- Noroeste: 1,006
- Sureste: 1,006
- Noreste: 339
- Suroeste: 338
- Sin coordenadas: 1

### Por Tipo de Zona
- Rural: 2,281
- Periurbano: 308
- Urbano: 101

## 🔍 Hallazgos de Fase 0 - Caracterización de Red

### Análisis Inicial

### Patrones Espaciales Identificados
- **64 alimentadores** con patrón aleatorio
- **23 alimentadores** con patrón regular  
- **18 alimentadores** con patrón lineal
- **5 alimentadores** con autocorrelación positiva de fallas

### Problemas Sistémicos
- **54 alimentadores** con problemas sistémicos identificados
- **41 alimentadores** con calidad degradada sistémica
- **13 alimentadores** con fallas generalizadas
- **240 hotspots** de problemas localizados

### Variables Correlacionadas con Problemas
| Variable | Correlación | Significancia |
|----------|-------------|---------------|
| Potencia | 0.308 | p<0.001 |
| Q_Usuarios | 0.304 | p<0.001 |
| num_circuitos | 0.253 | p<0.001 |
| factor_utilizacion | 0.146 | p<0.001 |
| usuarios_por_kva | 0.145 | p<0.001 |

### Top 10 Alimentadores Críticos (Score Compuesto)
1. **MITRE**: 5,793 usuarios, 69.7% problemas
2. **LINEA SUR**: 4,687 usuarios, 29.6% problemas
3. **FLOR DEL VALLE**: 4,822 usuarios, 84.2% problemas
4. **8 CENTRAL CIPOLLETTI**: 4,110 usuarios, 75.8% problemas
5. **STEFENELLI**: 3,290 usuarios, 68.5% problemas
6. **002 CENTRO**: 4,079 usuarios, 79.3% problemas
7. **BRENTANA**: 3,969 usuarios, 70.6% problemas
8. **RURAL**: 3,956 usuarios, 13.6% problemas
9. **2 CENTRAL CIPOLLETTI**: 3,564 usuarios, 74.2% problemas
10. **001 JAMAICA**: 1,824 usuarios, 43.3% problemas

## 📊 Consultas Avanzadas - Fase 0

### Cargar datos enriquecidos con topología
```python
# Transformadores con toda la información de topología
df_topo = pd.read_csv('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/transformadores_con_topologia.csv')

# Filtrar por alimentadores críticos
criticos = df_topo[df_topo['Alimentador'].isin([
    'MITRE', 'FLOR DEL VALLE', '8 CENTRAL CIPOLLETTI', 'STEFENELLI'
])]

# Analizar por patrón espacial
df_patterns = pd.read_csv('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/patrones_espaciales_alimentadores.csv')
lineales = df_patterns[df_patterns['es_lineal'] == True]
```

### Identificar zonas de intervención
```python
# Cargar problemas sistémicos
df_systemic = pd.read_csv('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/problemas_sistemicos.csv')

# Alimentadores que requieren intervención urgente
urgentes = df_systemic[
    df_systemic['tipo_problema'].str.contains('Sistémico') & 
    (df_systemic['num_transformadores'] > 20) &
    (df_systemic['tasa_problemas'] > 0.5)
]

# Hotspots de problemas
df_hotspots = pd.read_csv('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/network_analysis/clusters_espaciales_problemas.csv')
hotspots_criticos = df_hotspots[df_hotspots['transformadores_problema_en_hotspot'] >= 5]
```

### Análisis Eléctrico Extendido

### Features Eléctricas Clave
```python
# Cargar dataset con todas las features eléctricas
df_electrical = pd.read_csv('/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/processed/electrical_analysis/transformadores_indices_riesgo.csv')

# Filtrar por vulnerabilidad crítica
criticos = df_electrical[df_electrical['nivel_vulnerabilidad'] == 'Crítica']

# Analizar por modo de falla
termicos = df_electrical[df_electrical['modo_falla_probable'] == 'Térmico']
dielectricos = df_electrical[df_electrical['modo_falla_probable'] == 'Dieléctrico']
```

### Top Features ML (por importancia)
1. **indice_vulnerabilidad_compuesto**: 0.0821
2. **caida_tension_percent**: 0.0754
3. **kVA_aguas_abajo**: 0.0692
4. **indice_estres_termico_v2**: 0.0631
5. **Z_acumulada**: 0.0589

### Estadísticas Eléctricas
- **Caída tensión promedio**: 3.8%
- **Transformadores fuera límite (>5%)**: 423 (15.7%)
- **Factor potencia promedio**: 0.87
- **Vulnerabilidad crítica**: 89 transformadores (3.3%)

### Scripts de Análisis Eléctrico
```bash
cd /Users/maxkeczeli/Proyects/gd-edersa-calidad/scripts/network_analysis/

# Ejecutar análisis eléctrico completo:
python 04_mst_topology_reconstruction.py
python 05_electrical_distance_calculation.py
python 06_load_estimation_features.py
python 07_failure_mode_features.py
python 08_ml_ready_dataset.py
```

---
**Documento actualizado con hallazgos de Fase 0 Extendida - Análisis Eléctrico EDERSA**