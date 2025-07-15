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

### Base de Datos
```python
# SQLite database
db_path = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/data/edersa_transformadores.db"
```

### Reportes
```python
# Reportes JSON del pipeline
validation_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/01_validation_report.json"
cleaning_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/02_cleaning_report.json"
aggregations_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/03_aggregations_report.json"
criticality_report = "/Users/maxkeczeli/Proyects/gd-edersa-calidad/reports/04_criticality_report.json"
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

---
**Documento creado para facilitar el acceso rápido a todos los datos procesados del proyecto EDERSA**