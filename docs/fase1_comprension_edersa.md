# FASE 1: COMPRENSIÓN DEL SISTEMA EDERSA
## Análisis del Inventario de Transformadores y Calidad de Servicio

### 1. RESUMEN EJECUTIVO

La Fase 1 se enfoca en comprender la situación actual de calidad de servicio en la red EDERSA a través del análisis de 14,025 transformadores distribuidos en 14 sucursales y 133 alimentadores. El objetivo es identificar zonas críticas donde la Generación Distribuida (GD) puede tener mayor impacto en la mejora de la calidad.

**Alcance de la Fase:**
- Pre-procesamiento y validación del inventario de transformadores
- Análisis estadístico de calidad por zona
- Identificación de patrones geográficos y técnicos
- Priorización de áreas para intervención con GD
- Creación de dashboard interactivo para exploración de datos

### 2. DATOS DE ENTRADA

#### 2.1 Archivo Principal
- **Archivo**: `data/raw/Mediciones Originales EDERSA.xlsx`
- **Formato**: Excel con hoja única "Hoja 1"
- **Registros**: 14,025 transformadores
- **Período**: Snapshot actual (sin series temporales)

#### 2.2 Estructura de Columnas
| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| Codigoct | String | ID único del transformador | "T12345" |
| N_Sucursal | String | Nombre de la sucursal | "BARILOCHE" |
| Alimentador | String | Código del alimentador | "ALM-123" |
| Potencia | Float | Capacidad en kVA | 315.0 |
| Q_Usuarios | Integer | Cantidad de usuarios conectados | 45 |
| N_Localida | String | Localidad de ubicación | "Villa La Angostura" |
| Coord_X | Float | Coordenada X (longitud) | -71.123456 |
| Coord_Y | Float | Coordenada Y (latitud) | -40.123456 |
| Resultado | String | Estado de calidad | "Correcta"/"Penalizada"/"Fallida" |

### 3. PRE-PROCESAMIENTO REQUERIDO

#### 3.1 Validación de Datos
```python
# Script: scripts/preprocessing/01_validate_data.py

VALIDACIONES = {
    "completitud": {
        "campos_obligatorios": ["Codigoct", "N_Sucursal", "Alimentador", "Potencia", "Resultado"],
        "tolerancia_nulos": 0.05  # 5% máximo
    },
    "rangos": {
        "Potencia": {"min": 5, "max": 2000, "unidad": "kVA"},
        "Q_Usuarios": {"min": 0, "max": 5000},
        "Coord_X": {"min": -75, "max": -65},  # Argentina
        "Coord_Y": {"min": -45, "max": -35}   # Río Negro
    },
    "valores_permitidos": {
        "Resultado": ["Correcta", "Penalizada", "Fallida"]
    }
}

# Salida esperada:
# - data_quality_report.json
# - transformers_validated.parquet
# - validation_errors.csv
```

#### 3.2 Limpieza y Enriquecimiento
```python
# Script: scripts/preprocessing/02_clean_enrich_data.py

LIMPIEZA = {
    "normalización": {
        "N_Sucursal": "upper() y strip()",
        "Alimentador": "upper() y strip()",
        "N_Localida": "title() y strip()"
    },
    "imputación": {
        "Q_Usuarios": "mediana por alimentador si es nulo",
        "Coord_X/Y": "geocoding por localidad si es nulo"
    },
    "enriquecimiento": {
        "quality_score": "1.0 si Correcta, 0.5 si Penalizada, 0.0 si Fallida",
        "size_category": "Pequeño (<100 kVA), Mediano (100-500), Grande (>500)",
        "load_density": "Q_Usuarios / Potencia",
        "has_coordinates": "True si Coord_X y Coord_Y no son nulos"
    }
}

# Salida esperada:
# - transformers_clean.parquet
# - geocoding_results.json
# - enrichment_summary.json
```

#### 3.3 Agregaciones Base
```python
# Script: scripts/preprocessing/03_create_aggregations.py

AGREGACIONES = {
    "por_sucursal": {
        "metricas": [
            "count(transformadores)",
            "sum(potencia_kva)",
            "sum(usuarios)",
            "count(penalizados)",
            "mean(quality_score)",
            "percent(con_coordenadas)"
        ]
    },
    "por_alimentador": {
        "metricas": [
            "count(transformadores)",
            "sum(potencia_kva)",
            "sum(usuarios)",
            "count(penalizados)",
            "stddev(quality_score)"
        ]
    },
    "por_localidad": {
        "metricas": [
            "count(transformadores)",
            "sum(usuarios_afectados)",
            "centroid(coordenadas)"
        ]
    }
}

# Salida esperada:
# - aggregations/by_branch.parquet
# - aggregations/by_feeder.parquet
# - aggregations/by_locality.parquet
# - aggregations/summary_stats.json
```

#### 3.4 Análisis Geoespacial
```python
# Script: scripts/preprocessing/04_spatial_analysis.py

ANALISIS_ESPACIAL = {
    "clustering": {
        "algoritmo": "DBSCAN",
        "eps": 0.01,  # ~1 km
        "min_samples": 5
    },
    "hot_spots": {
        "metodo": "Getis-Ord Gi*",
        "variable": "tasa_penalizacion",
        "vecindad": "2 km"
    },
    "cobertura": {
        "buffer_transformador": "500 m",
        "calculo": "usuarios_cubiertos / usuarios_totales"
    }
}

# Salida esperada:
# - spatial/clusters.geojson
# - spatial/hotspots.geojson
# - spatial/coverage_map.tif
# - spatial/spatial_stats.json
```

### 4. ESTRUCTURA DE DATOS PROCESADOS

#### 4.1 Base de Datos SQLite
```sql
-- Archivo: data/processed/edersa.db

-- Tabla principal de transformadores
CREATE TABLE transformers (
    id INTEGER PRIMARY KEY,
    codigo TEXT UNIQUE NOT NULL,
    sucursal TEXT NOT NULL,
    alimentador TEXT NOT NULL,
    potencia_kva REAL NOT NULL,
    usuarios INTEGER,
    localidad TEXT,
    coord_x REAL,
    coord_y REAL,
    resultado TEXT,
    quality_score REAL,
    size_category TEXT,
    load_density REAL,
    has_coordinates BOOLEAN,
    cluster_id INTEGER,
    hotspot_score REAL
);

-- Vista agregada por sucursal
CREATE VIEW branch_summary AS
SELECT 
    sucursal,
    COUNT(*) as total_transformers,
    SUM(potencia_kva) as total_kva,
    SUM(usuarios) as total_users,
    SUM(CASE WHEN resultado != 'Correcta' THEN 1 ELSE 0 END) as penalized_count,
    AVG(quality_score) as avg_quality_score,
    SUM(CASE WHEN resultado != 'Correcta' THEN usuarios ELSE 0 END) as affected_users
FROM transformers
GROUP BY sucursal;

-- Índices para performance
CREATE INDEX idx_sucursal ON transformers(sucursal);
CREATE INDEX idx_alimentador ON transformers(alimentador);
CREATE INDEX idx_resultado ON transformers(resultado);
CREATE INDEX idx_spatial ON transformers(coord_x, coord_y);
```

#### 4.2 Archivos Parquet para Análisis
```
data/processed/
├── transformers_master.parquet      # Dataset completo limpio
├── quality_analysis/
│   ├── by_branch.parquet           # Análisis por sucursal
│   ├── by_feeder.parquet           # Análisis por alimentador
│   ├── by_locality.parquet         # Análisis por localidad
│   └── critical_zones.parquet      # Top zonas críticas
├── spatial/
│   ├── transformer_points.geojson   # Puntos georeferenciados
│   ├── cluster_polygons.geojson     # Polígonos de clusters
│   └── heatmap_data.parquet        # Datos para mapa de calor
└── metrics/
    ├── system_overview.json         # KPIs generales
    ├── data_quality.json           # Reporte de calidad de datos
    └── preprocessing_log.json       # Log de procesamiento
```

### 5. MÉTRICAS CLAVE A CALCULAR

#### 5.1 Nivel Sistema
```python
METRICAS_SISTEMA = {
    "total_transformadores": 14025,
    "total_capacidad_mva": "sum(potencia_kva) / 1000",
    "total_usuarios": "sum(usuarios)",
    "transformadores_penalizados": "count(donde resultado != 'Correcta')",
    "tasa_penalizacion": "penalizados / total",
    "usuarios_afectados": "sum(usuarios donde resultado != 'Correcta')",
    "capacidad_afectada_mva": "sum(potencia_kva donde resultado != 'Correcta') / 1000",
    "transformadores_georeferenciados": "count(donde has_coordinates = True)",
    "sucursales_criticas": "count(sucursales con tasa_penalizacion > 0.4)"
}
```

#### 5.2 Índices de Criticidad
```python
# Índice compuesto para priorización
CRITICALITY_INDEX = {
    "formula": "0.4 * tasa_penalizacion + 0.3 * usuarios_afectados_norm + 0.3 * capacidad_afectada_norm",
    "pesos": {
        "calidad": 0.4,
        "impacto_usuarios": 0.3,
        "impacto_capacidad": 0.3
    },
    "normalización": "min-max por variable"
}
```

### 6. ANÁLISIS A REALIZAR

#### 6.1 Análisis Exploratorio
1. **Distribución de transformadores**
   - Por sucursal y alimentador
   - Por rango de potencia
   - Por densidad de usuarios

2. **Patrones de calidad**
   - Correlación tamaño vs calidad
   - Análisis temporal si hay datos históricos
   - Factores asociados a penalizaciones

3. **Análisis geográfico**
   - Concentración espacial de problemas
   - Distancia entre transformadores problemáticos
   - Accesibilidad y ruralidad

#### 6.2 Análisis de Impacto
1. **Impacto en usuarios**
   - Usuarios afectados por zona
   - Criticidad por tipo de usuario (si disponible)
   - Cobertura geográfica de problemas

2. **Impacto en capacidad**
   - MVA comprometidos por zona
   - Reserva de capacidad afectada
   - Potencial de mejora con GD

3. **Impacto económico estimado**
   - Costo estimado de penalizaciones
   - Pérdida de ingresos
   - Costo de intervenciones tradicionales

### 7. ENTREGABLES DE LA FASE

#### 7.1 Scripts de Pre-procesamiento
```bash
scripts/preprocessing/
├── 01_validate_data.py          # Validación inicial
├── 02_clean_enrich_data.py      # Limpieza y enriquecimiento
├── 03_create_aggregations.py    # Agregaciones
├── 04_spatial_analysis.py       # Análisis espacial
├── 05_create_database.py        # Crear SQLite
└── run_all_preprocessing.sh     # Script maestro
```

#### 7.2 Dashboard Interactivo
```
dashboard/pages/
├── fase1_comprension_edersa.py  # Dashboard principal
└── components_edersa/
    ├── tab1_overview.py         # Vista general
    ├── tab2_quality_analysis.py # Análisis de calidad
    ├── tab3_branch_analysis.py  # Por sucursal
    ├── tab4_feeder_analysis.py  # Por alimentador
    ├── tab5_geographic.py       # Mapa interactivo
    └── tab6_critical_zones.py   # Zonas críticas
```

#### 7.3 Reportes
1. **Reporte técnico** (este documento actualizado con resultados)
2. **Presentación ejecutiva** (PDF con hallazgos clave)
3. **Data book** (Excel con todas las tablas y análisis)

#### 7.4 Base de Datos
- SQLite con datos procesados y vistas
- Documentación del esquema
- Queries de ejemplo

### 8. CRONOGRAMA ESTIMADO

| Actividad | Duración | Entregable |
|-----------|----------|------------|
| Validación y limpieza de datos | 1 día | Scripts 01-02, reporte de calidad |
| Agregaciones y análisis | 1 día | Scripts 03-04, base de datos |
| Desarrollo dashboard | 2 días | Dashboard funcional |
| Análisis y documentación | 1 día | Reportes y presentación |
| **TOTAL FASE 1** | **5 días** | **Todos los entregables** |

### 9. CRITERIOS DE ÉXITO

1. **Calidad de datos**
   - >95% de registros válidos
   - >80% de transformadores georeferenciados
   - 0 duplicados

2. **Análisis completo**
   - 100% de sucursales analizadas
   - Top 20 zonas críticas identificadas
   - Índices de criticidad calculados

3. **Dashboard funcional**
   - Carga en <3 segundos
   - Navegación intuitiva
   - Exportación de datos

4. **Documentación**
   - Reporte técnico completo
   - Código documentado
   - Guía de usuario del dashboard

### 10. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Baja calidad de coordenadas | Alta | Alto | Geocoding automático + validación manual |
| Inconsistencias en nombres | Media | Medio | Normalización + tabla de equivalencias |
| Datos faltantes críticos | Baja | Alto | Imputación conservadora + flag de calidad |
| Performance con 14k registros | Media | Medio | Índices DB + agregaciones pre-calculadas |

### 11. PRÓXIMOS PASOS (POST FASE 1)

1. **Fase 2: Modelado de GD**
   - Dimensionamiento preliminar por zona
   - Tecnologías aplicables (solar, híbrido)
   - Restricciones técnicas

2. **Fase 3: Evaluación de Impacto**
   - Simulación de mejoras con GD
   - Análisis costo-beneficio
   - Priorización de proyectos

3. **Fase 4: Plan de Implementación**
   - Roadmap de despliegue
   - Especificaciones técnicas
   - Modelo de financiamiento

---

*Documento creado: Julio 2025*  
*Actualización: Pendiente resultados del pre-procesamiento*