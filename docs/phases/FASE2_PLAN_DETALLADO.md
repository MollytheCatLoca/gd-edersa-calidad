# FASE 2: CLUSTERING Y PRIORIZACIÓN - PLAN DETALLADO

**Fecha de Inicio**: 15 de Julio 2025  
**Duración Estimada**: 2-3 días  
**Estado**: PLANIFICACIÓN

## 🎯 Objetivos de la Fase

1. **Identificar zonas críticas** mediante clustering geográfico avanzado
2. **Priorizar ubicaciones** para instalación de GD usando criterios múltiples
3. **Analizar patrones espaciales** de problemas de calidad
4. **Cuantificar impacto potencial** por zona de intervención
5. **Generar recomendaciones accionables** para despliegue de GD

## 📊 Datos de Entrada (desde Fase 1)

### Transformadores Procesados
- **Total**: 2,690 transformadores con coordenadas
- **Críticos**: 555 transformadores (criticidad > 0.5)
- **Fallidos**: 555 transformadores en estado "Fallida"
- **Usuarios afectados**: 58,745 en zonas críticas

### Distribución Geográfica Actual
- **Noroeste**: 1,006 transformadores (25.3% fallidos)
- **Noreste**: 339 transformadores (28.3% fallidos)
- **Sureste**: 1,006 transformadores (15.0% fallidos)
- **Suroeste**: 338 transformadores (15.7% fallidos)

## 🔧 Metodología Propuesta

### 1. Clustering Geográfico Avanzado
```python
# Algoritmos a implementar:
- DBSCAN: Para identificar clusters de densidad variable
- K-means con Elbow Method: Para número óptimo de clusters
- Hierarchical Clustering: Para análisis multi-escala
- HDBSCAN: Para clusters de forma irregular
```

### 2. Métricas de Clustering
- **Densidad de problemas**: Transformadores fallidos/km²
- **Impacto agregado**: Usuarios afectados por cluster
- **Índice de concentración**: Gini coefficient de distribución
- **Conectividad**: Distancia entre transformadores del cluster
- **Homogeneidad**: Varianza intra-cluster de criticidad

### 3. Criterios de Priorización Multi-objetivo
```
Score_prioridad = α₁ * Criticidad_técnica + 
                  α₂ * Usuarios_afectados + 
                  α₃ * Densidad_geográfica + 
                  α₄ * Viabilidad_técnica + 
                  α₅ * Potencial_mejora
```

Donde:
- α₁ = 0.25 (peso criticidad)
- α₂ = 0.30 (peso usuarios)
- α₃ = 0.20 (peso densidad)
- α₄ = 0.15 (peso viabilidad)
- α₅ = 0.10 (peso mejora)

## 📋 Plan de Implementación

### Día 1: Análisis de Clustering

#### Script 06: Clustering Espacial
```bash
scripts/clustering/06_spatial_clustering.py
```
**Funcionalidades**:
- Cargar transformadores con coordenadas
- Aplicar múltiples algoritmos de clustering
- Comparar resultados y métricas
- Seleccionar método óptimo
- Guardar clusters identificados

**Salidas esperadas**:
- `clusters_identificados.csv`
- `metricas_clustering.json`
- Visualizaciones de clusters

#### Script 07: Análisis de Densidad
```bash
scripts/clustering/07_density_analysis.py
```
**Funcionalidades**:
- Calcular densidad kernel (KDE)
- Identificar "hot spots" de problemas
- Análisis de vecindad (nearest neighbors)
- Mapas de calor de criticidad

**Salidas esperadas**:
- `density_maps.json`
- `hotspots_identificados.csv`
- Mapas de calor georeferenciados

### Día 2: Priorización y Análisis

#### Script 08: Matriz de Priorización
```bash
scripts/clustering/08_priority_matrix.py
```
**Funcionalidades**:
- Calcular scores multi-criterio
- Generar matriz criticidad vs viabilidad
- Ranking de clusters por prioridad
- Análisis de sensibilidad de pesos

**Salidas esperadas**:
- `matriz_priorizacion.csv`
- `ranking_clusters.json`
- `analisis_sensibilidad.json`

#### Script 09: Análisis de Impacto
```bash
scripts/clustering/09_impact_analysis.py
```
**Funcionalidades**:
- Cuantificar usuarios beneficiados por cluster
- Estimar mejora de calidad esperada
- Calcular cobertura geográfica
- Análisis de redundancia entre clusters

**Salidas esperadas**:
- `impacto_por_cluster.csv`
- `cobertura_geografica.json`
- `beneficios_esperados.json`

### Día 3: Visualización y Recomendaciones

#### Script 10: Dashboard de Clustering
```bash
scripts/clustering/10_update_dashboard.py
```
**Funcionalidades**:
- Agregar pestaña de clustering al dashboard
- Mapas interactivos de clusters
- Gráficos de priorización
- Tablas de recomendaciones

#### Script 11: Generar Reporte Ejecutivo
```bash
scripts/clustering/11_executive_report.py
```
**Funcionalidades**:
- Top 10 ubicaciones para GD
- Fichas técnicas por cluster
- Análisis costo-beneficio preliminar
- Roadmap de implementación

## 📊 Entregables Esperados

### 1. Clusters Identificados
- **Número esperado**: 15-25 clusters principales
- **Tamaño promedio**: 20-50 transformadores por cluster
- **Cobertura**: 80% de transformadores críticos

### 2. Ranking de Prioridades
```
Top 10 Clusters Prioritarios:
1. Cluster_ID | Sucursal | Transformadores | Usuarios | Score
2. ...
```

### 3. Mapas y Visualizaciones
- Mapa de clusters con códigos de color
- Heatmap de densidad de problemas
- Matriz de priorización interactiva
- Gráficos de impacto por zona

### 4. Métricas de Éxito
- **Cobertura de usuarios críticos**: >70%
- **Reducción de dispersión**: <30% vs análisis individual
- **Clusters viables técnicamente**: >80%
- **ROI potencial**: >15% anual

## 🔄 Estructura de Datos Nueva

### Tabla: clusters_geograficos
```sql
CREATE TABLE clusters_geograficos (
    cluster_id INTEGER PRIMARY KEY,
    nombre VARCHAR(100),
    sucursal_principal VARCHAR(100),
    num_transformadores INTEGER,
    num_usuarios INTEGER,
    criticidad_promedio REAL,
    centroid_x REAL,
    centroid_y REAL,
    radio_km REAL,
    score_prioridad REAL,
    tipo_zona VARCHAR(50)
);
```

### Tabla: transformadores_clusters
```sql
CREATE TABLE transformadores_clusters (
    codigo_transformador VARCHAR(50),
    cluster_id INTEGER,
    distancia_centroid REAL,
    es_nucleo BOOLEAN,
    FOREIGN KEY (cluster_id) REFERENCES clusters_geograficos(cluster_id)
);
```

### Tabla: metricas_clusters
```sql
CREATE TABLE metricas_clusters (
    cluster_id INTEGER,
    densidad_problemas REAL,
    indice_concentracion REAL,
    conectividad_promedio REAL,
    homogeneidad REAL,
    viabilidad_tecnica REAL,
    potencial_mejora REAL,
    FOREIGN KEY (cluster_id) REFERENCES clusters_geograficos(cluster_id)
);
```

## 🛠️ Herramientas y Librerías

### Nuevas Dependencias
```python
# Clustering
scikit-learn>=1.3.0  # DBSCAN, K-means, AgglomerativeClustering
hdbscan>=0.8.33      # HDBSCAN algorithm
scipy>=1.11.0        # Spatial analysis, KDE

# Visualización espacial
folium>=0.14.0       # Mapas interactivos
geopandas>=0.13.0    # Análisis geoespacial
shapely>=2.0.0       # Geometrías

# Análisis
networkx>=3.1        # Análisis de conectividad
statsmodels>=0.14.0  # Estadísticas espaciales
```

## 📈 KPIs de la Fase

1. **Reducción de complejidad**
   - De 2,690 puntos individuales a ~20 clusters
   - Mantener >90% de información relevante

2. **Mejora en toma de decisiones**
   - Tiempo de análisis: De días a horas
   - Claridad en prioridades: Score cuantitativo

3. **Cobertura de impacto**
   - Usuarios cubiertos: >70% de afectados
   - Área geográfica: <40% del territorio

4. **Viabilidad técnica**
   - Clusters con acceso vial: >85%
   - Distancia a subestaciones: <50km promedio

## 🔍 Consideraciones Especiales

### Restricciones Geográficas
- Zonas protegidas o inaccesibles
- Limitaciones de infraestructura vial
- Disponibilidad de terrenos

### Aspectos Sociales
- Comunidades vulnerables prioritarias
- Zonas de alto impacto económico
- Servicios críticos (hospitales, escuelas)

### Limitaciones Técnicas
- Capacidad de las subestaciones
- Restricciones de la red de MT
- Disponibilidad de comunicaciones

## 🚀 Próximos Pasos (Post-Fase 2)

1. **Fase 3**: Dimensionamiento preliminar de GD por cluster
2. **Fase 4**: Simulación técnica de mejoras
3. **Fase 5**: Evaluación económica detallada

---

**Nota**: Este plan es adaptable según los resultados obtenidos durante la implementación. Los pesos de priorización pueden ajustarse según criterios de EDERSA.