# ANÁLISIS DE CALIDAD Y OPORTUNIDADES GD - EDERSA
## Documentación Técnica del Proyecto

### 1. CONTEXTO Y OBJETIVO

#### PROBLEMA IDENTIFICADO
EDERSA opera una red de distribución con 14,025 transformadores que presentan problemas significativos de calidad de servicio:
- **34% de transformadores** con resultados "Penalizada" o "Fallida"
- **~180,000 usuarios afectados** por problemas de calidad
- **14 sucursales** con diferentes niveles de criticidad
- **133 alimentadores** distribuidos geográficamente

#### HIPÓTESIS PRINCIPAL
**La instalación estratégica de Generación Distribuida (GD) puede mejorar significativamente la calidad de servicio en zonas críticas, siendo más costo-efectiva que soluciones tradicionales de refuerzo de red.**

#### DIFERENCIAS CON PROYECTO LÍNEA SUR
- **Línea Sur**: Red radial de 33kV con problemas de voltaje (V < 0.95 pu)
- **EDERSA**: Red completa con múltiples niveles de tensión y problemas de calidad diversos
- **Datos**: Línea Sur tenía series temporales; EDERSA tiene inventario y resultados de calidad
- **Enfoque**: Línea Sur optimizaba voltaje; EDERSA optimiza calidad integral

### 2. METODOLOGÍA ADAPTADA

Basada en metodología CLAUDE del proyecto Línea Sur, adaptada para análisis de calidad sin series temporales.

#### FASE 0: PREPARACIÓN Y COMPRENSIÓN (ACTUAL)
**Objetivo**: Establecer base del proyecto y entender alcance

**Actividades**:
- ✅ Clonar y analizar proyecto legacy Línea Sur
- ✅ Identificar componentes reutilizables
- ✅ Crear documentación inicial
- ⏳ Configurar entorno de desarrollo

**Entregables**:
- CLAUDE.md (este documento)
- Estructura de proyecto definida
- Plan de implementación por fases

#### FASE 1: ANÁLISIS DE INVENTARIO Y CALIDAD
**Objetivo**: Procesar y entender datos de transformadores

**Actividades Planificadas**:
- Procesar Excel con 14,025 transformadores
- Análisis estadístico de resultados de calidad
- Mapeo geográfico de transformadores con coordenadas
- Identificación de patrones por sucursal/alimentador
- Cálculo de métricas de impacto

**Entregables Esperados**:
- Base de datos procesada (SQLite/Parquet)
- Reporte de calidad por zona
- Visualizaciones de distribución geográfica
- Ranking de criticidad

**Componentes a Reutilizar**:
- `data_loaders.py` - Adaptado para Excel EDERSA
- `data_analytics.py` - Para cálculo de KPIs
- Dashboard base - Para visualizaciones

#### FASE 2: CLUSTERING Y PRIORIZACIÓN
**Objetivo**: Identificar zonas prioritarias para GD

**Actividades Planificadas**:
- Clustering geográfico de transformadores problemáticos
- Análisis de densidad de problemas
- Evaluación de impacto en usuarios
- Identificación de "hot spots" para GD

**Entregables Esperados**:
- Mapa de clusters críticos
- Matriz de priorización (criticidad vs viabilidad)
- Top 10 ubicaciones candidatas para GD

**Adaptaciones Necesarias**:
- Nuevo módulo de clustering espacial
- Métricas de calidad específicas EDERSA
- Algoritmos de priorización multi-criterio

#### FASE 3: DIMENSIONAMIENTO PRELIMINAR GD
**Objetivo**: Estimar capacidades de GD sin series temporales

**Actividades Planificadas**:
- Estimación de demanda por capacidad de transformadores
- Aplicación de perfiles típicos de carga
- Dimensionamiento conservador de GD
- Análisis de sensibilidad

**Entregables Esperados**:
- Capacidades estimadas por zona
- Factores de planta esperados
- Requerimientos de potencia y energía

**Componentes a Adaptar**:
- `pv_model.py` - Simplificado sin datos meteorológicos
- `bess_model.py` - Para estimaciones preliminares
- Perfiles de demanda típicos

#### FASE 4: SIMULACIÓN Y EVALUACIÓN TÉCNICA
**Objetivo**: Evaluar impacto técnico de GD propuesta

**Actividades Planificadas**:
- Simulación simplificada de mejora de calidad
- Estimación de reducción de problemas
- Análisis de cobertura geográfica
- Evaluación de redundancia y confiabilidad

**Entregables Esperados**:
- Métricas de mejora esperada
- Cobertura de usuarios beneficiados
- Análisis de sensibilidad técnica

**Simplificaciones**:
- Sin flujo de potencia detallado
- Modelos agregados por zona
- Supuestos conservadores

#### FASE 5: EVALUACIÓN ECONÓMICA Y RECOMENDACIONES
**Objetivo**: Justificar inversión y priorizar implementación

**Actividades Planificadas**:
- Estimación de CAPEX/OPEX por ubicación
- Cálculo de beneficios (reducción penalizaciones)
- Análisis costo-beneficio
- Roadmap de implementación

**Entregables Esperados**:
- Business case por ubicación
- Ranking económico de proyectos
- Plan de implementación por etapas
- Recomendaciones ejecutivas

**Métricas Clave**:
- Costo por usuario mejorado
- Payback por proyecto
- VPN a 20 años
- Reducción de penalizaciones

### 3. COMPONENTES REUTILIZABLES DEL LEGACY

#### ARQUITECTURA BASE
```
src/
├── inventory/          # NUEVO - Manejo de inventario EDERSA
├── quality/           # NUEVO - Análisis de calidad
├── clustering/        # NUEVO - Clustering geográfico
├── battery/           # REUTILIZABLE - Modelos BESS
├── solar/            # ADAPTABLE - Modelos PV simplificados
├── economics/        # REUTILIZABLE - Evaluación económica
└── visualization/    # REUTILIZABLE - Gráficos y mapas
```

#### MÓDULOS A REUTILIZAR DIRECTAMENTE
1. **BESS Model** (`battery/bess_model.py`)
   - Tecnologías de baterías
   - Estrategias de control
   - Validación de energía

2. **Economic Evaluator** (`economics/economic_evaluator.py`)
   - Cálculo de VPN, TIR
   - LCOE
   - Análisis de sensibilidad

3. **Dashboard Framework** (`dashboard/app_multipagina.py`)
   - Estructura multi-página
   - Componentes Plotly/Dash
   - Layouts responsivos

#### MÓDULOS A ADAPTAR
1. **PV Model** (`solar/pv_model.py`)
   - Simplificar sin datos meteorológicos
   - Usar factores de planta típicos
   - Perfiles estándar por zona

2. **Data Loaders** (`data_processing/loader.py`)
   - Adaptar para Excel EDERSA
   - Nuevos esquemas de validación
   - Procesamiento de coordenadas

3. **Analytics** (`analysis/temporal.py`)
   - Enfocar en análisis espacial
   - Métricas de calidad vs tiempo
   - KPIs específicos EDERSA

### 4. ESTRUCTURA DE DATOS EDERSA

#### ESQUEMA DE TRANSFORMADORES
```python
@dataclass
class Transformer:
    codigo: str              # ID único
    sucursal: str           # Sucursal (14 total)
    alimentador: str        # Alimentador (133 total)
    potencia_kva: float     # Capacidad
    usuarios: int           # Usuarios conectados
    localidad: str          # Ubicación
    coord_x: Optional[float]  # Coordenada X
    coord_y: Optional[float]  # Coordenada Y
    resultado: str          # Correcta/Penalizada/Fallida
    quality_score: float    # 1.0/0.5/0.0
```

#### MÉTRICAS DE CALIDAD
```python
# Por zona (sucursal/alimentador)
- total_transformers: Cantidad total
- penalized_count: Transformadores con problemas
- penalized_rate: Tasa de penalización
- affected_users: Usuarios afectados
- criticality_index: Índice compuesto de criticidad
```

### 5. HERRAMIENTAS Y TECNOLOGÍAS

#### STACK TECNOLÓGICO
- **Python 3.10+**: Lenguaje principal
- **Pandas/NumPy**: Procesamiento de datos
- **Plotly/Dash**: Dashboard interactivo
- **Folium**: Mapas geográficos
- **Scikit-learn**: Clustering y ML
- **SQLite**: Base de datos local
- **Parquet**: Almacenamiento eficiente

#### DEPENDENCIAS CLAVE
```python
# Core
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0  # Para Excel

# Visualización
plotly>=5.14.0
dash>=2.10.0
folium>=0.14.0

# Análisis
scikit-learn>=1.2.0
scipy>=1.10.0
```

### 6. CONVENCIONES Y ESTÁNDARES

#### ESTRUCTURA DE ARCHIVOS
```
data/
├── raw/
│   └── Mediciones Originales EDERSA.xlsx
├── processed/
│   ├── transformers/
│   ├── quality/
│   └── geographic/
└── results/
    ├── clusters/
    └── recommendations/
```

#### NOMENCLATURA
- Funciones: `snake_case`
- Clases: `PascalCase`
- Constantes: `UPPER_SNAKE_CASE`
- Archivos: `lower_snake_case.py`

#### LOGGING
```python
logger = logging.getLogger(__name__)
logger.info(f"Procesados {n} transformadores")
logger.warning(f"Sin coordenadas: {missing}")
logger.error(f"Error en {transformer.codigo}: {e}")
```

### 7. PRÓXIMOS PASOS INMEDIATOS

1. **Configurar entorno**
   - Crear requirements.txt específico
   - Configurar pytest
   - Setup pre-commit hooks

2. **Implementar Fase 1**
   - Loader para Excel EDERSA
   - Análisis estadístico básico
   - Primera versión del dashboard

3. **Validar approach**
   - Reunión con stakeholders
   - Confirmar métricas de éxito
   - Ajustar plan según feedback

### 8. RIESGOS Y MITIGACIONES

#### RIESGOS IDENTIFICADOS
1. **Falta de series temporales**
   - Mitigación: Usar perfiles típicos y factores conservadores

2. **Calidad de coordenadas geográficas**
   - Mitigación: Validación y geocoding de respaldo

3. **Diversidad de problemas de calidad**
   - Mitigación: Foco inicial en casos más críticos

### 9. DOCUMENTACIÓN DE REFERENCIA

#### DOCUMENTOS CLAVE DEL PROYECTO

1. **Documentación de Fase 0 Completa**
   ```
   /Users/maxkeczeli/Proyects/gd-edersa-calidad/docs/phases/FASE0_COMPLETA.md
   ```
   - Estado completo de Fase 0 con análisis de red
   - Incluye extensión de análisis eléctrico basado en teoría
   - Features eléctricas generadas y estadísticas

2. **Accesos Rápidos a Datos**
   ```
   /Users/maxkeczeli/Proyects/gd-edersa-calidad/docs/ACCESOS_DATOS_CLAUDE.md
   ```
   - Todos los paths de archivos importantes
   - Consultas SQL y Python útiles
   - Métricas clave del sistema

3. **Marco Teórico de Sistemas de Distribución**
   ```
   /Users/maxkeczeli/Proyects/gd-edersa-calidad/docs/analysis/Sistema_Distribucion_Electica.md
   ```
   - Teoría completa de redes de distribución
   - Fórmulas de caída de tensión y flujo de potencia
   - Modos de falla de transformadores
   - Base para el análisis eléctrico implementado

#### NOTA IMPORTANTE
Ante cualquier duda sobre:
- Topología de red y análisis MST → Consultar marco teórico
- Cálculos de impedancia y caída de tensión → Ver sección 2 del marco teórico
- Modos de falla (térmico/dieléctrico) → Ver sección 3 del marco teórico
- Paths de archivos y acceso a datos → Consultar ACCESOS_DATOS_CLAUDE.md

4. **Escalabilidad a 14,025 transformadores**
   - Mitigación: Procesamiento por lotes y cache agresivo

### 9. CRITERIOS DE ÉXITO

- **Técnicos**: Identificar top 10 ubicaciones con ROI > 15%
- **Calidad**: Potencial de reducir usuarios afectados en 50%
- **Económicos**: Proyectos con payback < 5 años
- **Implementación**: Roadmap claro y priorizado

### 10. NOTAS DE EVOLUCIÓN

Este documento es vivo y se actualizará después de cada fase completada. Las secciones marcadas como "Planificadas" se convertirán en "Completadas" con resultados reales y lecciones aprendidas.

**Última actualización**: Fase 1 - Completada (15 de Julio 2025)
**Próxima revisión**: Al completar Fase 2

### 11. ESTADO ACTUAL DEL PROYECTO

#### FASES COMPLETADAS ✅

**FASE 0 - Comprensión de Topología de Red**
- 128 alimentadores caracterizados
- 240 hotspots identificados
- Análisis de correlaciones espaciales completado
- Documentación: `/docs/phases/FASE0_COMPLETA.md`

**FASE 1 - Análisis de Inventario y Dashboard**
- 2,690 transformadores procesados con 70+ features
- Dashboard interactivo con 6 páginas funcionales
- Análisis eléctrico avanzado integrado
- Clustering preliminar implementado
- Documentación: `/docs/phases/FASE1_COMPLETA.md`

#### HERRAMIENTAS DISPONIBLES

**Dashboard Multi-página**
```bash
source venv/bin/activate
python dashboard/app_multipagina.py
# Acceder en: http://127.0.0.1:8050/
```

**Páginas del Dashboard**:
1. `/` - Vista general y métricas
2. `/inventario` - Análisis detallado por zona
3. `/topologia` - Visualización MST de red
4. `/electrico` - Impedancias y modos de falla
5. `/vulnerabilidad` - Mapas de calor y priorización
6. `/clustering` - Identificación de zonas GD

#### RESULTADOS CLAVE
- **45.9%** de transformadores con problemas
- **423** transformadores con caída tensión >5%
- **240** hotspots identificados
- **120.5 MW** capacidad GD estimada
- **58,745** usuarios beneficiables

#### PRÓXIMOS PASOS (FASE 2)
1. Refinamiento de clustering con parámetros optimizados
2. Análisis detallado de top 10-20 clusters
3. Dimensionamiento específico por zona
4. Evaluación de impacto en calidad