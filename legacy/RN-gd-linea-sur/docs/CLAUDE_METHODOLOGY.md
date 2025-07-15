# METODOLOGÍA CLAUDE - Framework para Análisis de Sistemas Eléctricos con GD

## 📋 Tabla de Contenidos
1. [Introducción](#introducción)
2. [Arquitectura de Software](#arquitectura-de-software)
3. [Flujo de Trabajo por Fases](#flujo-de-trabajo-por-fases)
4. [Directrices de Desarrollo](#directrices-de-desarrollo)
5. [Preparación de Datos para ML](#preparación-de-datos-para-ml)
6. [Buenas Prácticas](#buenas-prácticas)
7. [Plantillas y Herramientas](#plantillas-y-herramientas)

---

## 🎯 Introducción

CLAUDE (Comprehensive Layout for Analysis of Utilities with Distributed Energy) es una metodología estructurada para analizar sistemas eléctricos y evaluar la integración de generación distribuida (GD) con almacenamiento de energía (BESS).

### Casos de Uso
- Análisis de redes de distribución con problemas de calidad
- Evaluación técnico-económica de recursos distribuidos
- Optimización de ubicación y dimensionamiento de GD+BESS
- Estudios de factibilidad para microrredes
- Análisis de pérdidas y mejora de voltaje

### Requisitos Previos
- Python 3.10+
- Conocimiento básico de sistemas eléctricos
- Datos históricos del sistema (ideal: 12+ meses, resolución ≤15 min)

---

## 🏗️ Arquitectura de Software

### Estructura Modular Estándar

```
proyecto/
├── src/
│   ├── data_loaders.py      # Carga y validación de datos
│   ├── data_analytics.py     # Análisis y KPIs
│   ├── simulators.py         # Simulaciones del dominio
│   ├── data_manager.py       # Coordinación y API
│   ├── constants.py          # Constantes del proyecto
│   └── models.py             # Tipos de datos e interfaces
├── dashboard/                # Visualización interactiva
├── data/                     # Datos crudos y procesados
├── docs/                     # Documentación
└── tests/                    # Pruebas unitarias
```

### Principios de Diseño

#### 1. Separación de Responsabilidades
- **data_loaders.py**: Solo I/O y validación
- **data_analytics.py**: Cálculos y transformaciones
- **simulators.py**: Lógica específica del dominio
- **data_manager.py**: Orquestación sin lógica de negocio

#### 2. Ubicación de Funcionalidades

| Tipo de Función | Módulo | Ejemplos |
|-----------------|---------|----------|
| Carga/IO | `data_loaders.py` | Lectura CSV/Excel, validación Pydantic |
| Analítica | `data_analytics.py` | KPIs, estadísticas, agregaciones |
| Simulación | `simulators.py` | Modelos FV, BESS, flujos de potencia |
| Coordinación | `data_manager.py` | APIs, composición de resultados |
| Configuración | `constants.py` | Parámetros, umbrales, paths |

#### 3. Reglas de Evolución

**REGLA FUNDAMENTAL**: No insertar lógica de dominio en `data_manager.py`

**Checklist antes de añadir funciones:**
- [ ] Buscar si existe funcionalidad similar
- [ ] Verificar ubicación correcta según tabla
- [ ] Estimar complejidad (<150 LOC por función)
- [ ] Añadir tests y documentación
- [ ] Actualizar constants/models si necesario

---

## 📊 Flujo de Trabajo por Fases

### Fase 1: Comprensión del Sistema
**Objetivo**: Entender el problema y contexto

**Entradas**:
- Diagrama unifilar
- Datos de cargas y generación
- Restricciones operativas

**Salidas**:
- Documento de comprensión del sistema
- Identificación de puntos críticos
- Hipótesis iniciales

### Fase 2: Modelado Topológico
**Objetivo**: Representación digital de la red

**Entradas**:
- Parámetros de líneas y transformadores
- Topología de la red
- Puntos de medición

**Salidas**:
- Modelo topológico (JSON/GraphML)
- Matrices de admitancia
- Visualización de la red

### Fase 3: Procesamiento de Datos
**Objetivo**: Preparar datos para análisis

**Pipeline Estándar**:
```python
1. Validación y limpieza
2. Detección de anomalías
3. Imputación de faltantes
4. Feature engineering
5. Agregaciones temporales
6. Exportación en formatos ML
```

**Salidas Típicas**:
- `summary.json`: Estadísticas generales
- `quality_metrics.json`: Calidad de datos
- `temporal_patterns.json`: Patrones temporales
- `features.parquet`: Dataset para ML

### Fase 4: Análisis de Recursos Renovables
**Objetivo**: Modelar y simular GD+BESS

**Componentes**:
- Modelado de generación FV
- Estrategias de control BESS
- Análisis de coincidencia demanda-generación

### Fase 5: Evaluación Técnica
**Objetivo**: Simular impacto en la red

**Análisis**:
- Flujos de potencia (AC/DC)
- Mejora de perfiles de voltaje
- Reducción de pérdidas
- Análisis de sensibilidad

### Fase 6: Evaluación Económica
**Objetivo**: Viabilidad financiera

**Métricas**:
- CAPEX/OPEX
- VAN, TIR, Payback
- LCOE
- Análisis de sensibilidad

---

## 🛠️ Directrices de Desarrollo

### Patrones de Nombrado
```python
# Prefijos estándar
load_*()      # Funciones de carga
calc_*()      # Cálculos
simulate_*()  # Simulaciones
optimize_*()  # Optimización
export_*()    # Exportación
```

### Estructura de Resultados
```python
@dataclass
class DataResult:
    data: Any
    meta: Dict[str, Any]  # Debe incluir: source, version, timestamp
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
```

### Logging y Debug
```python
# Patrón estándar
logger.debug(f"{__name__}.{func_name}: Processing {len(data)} records")

# Para funciones con cache
logger.debug(f"Cache {'hit' if cached else 'miss'} for {hash(input_key)}")
```

---

## 🤖 Preparación de Datos para ML

### Features Estándar

#### Temporales
- `hour`, `day_of_week`, `month`, `is_weekend`, `is_holiday`
- `season`, `is_peak_hour`, `time_since_midnight`

#### Eléctricas
- `voltage_pu`, `power_mw`, `reactive_mvar`, `power_factor`
- `voltage_unbalance`, `thd_voltage`, `frequency_deviation`

#### Derivadas
- Rolling statistics (mean, std, min, max)
- Rampas y gradientes
- Lags (15min, 1h, 24h)
- Correlaciones cruzadas

### Formatos de Almacenamiento
- **Parquet**: Para datasets grandes (>100MB)
- **HDF5**: Para series temporales multidimensionales
- **JSON**: Para metadatos y configuraciones
- **CSV**: Para intercambio y visualización rápida

---

## ✅ Buenas Prácticas

### Gestión de Entornos
```bash
# Siempre usar entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Mantener requirements.txt actualizado
pip freeze > requirements.txt
```

### Control de Calidad
1. **Tests**: Mínimo 80% cobertura
2. **Documentación**: Docstrings en todas las funciones públicas
3. **Type hints**: Usar tipado estático
4. **Linting**: Black + Flake8
5. **CI/CD**: Tests automáticos en cada PR

### Gestión de Complejidad
- Si función > 150 LOC → dividir
- Si módulo > 500 LOC → considerar split
- Si dependencia nueva → justificar en PR

---

## 📁 Plantillas y Herramientas

### Plantilla de Proyecto
```bash
# Script de inicialización
curl -O https://raw.githubusercontent.com/[repo]/init_claude_project.py
python init_claude_project.py --name "mi_proyecto"
```

### Dashboard Base
```python
# dashboard/app.py
import dash
from dash import dcc, html
import plotly.graph_objects as go

app = dash.Dash(__name__)

# Layouts por fase
from pages import fase1, fase2, fase3, fase4, fase5, fase6

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Callback para navegación multi-página
@app.callback(...)
def display_page(pathname):
    # Lógica de routing
    pass
```

### Configuración Típica
```python
# src/constants.py
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Parámetros Eléctricos
NOMINAL_VOLTAGE_KV = 33.0
VOLTAGE_LIMITS = {"min": 0.95, "max": 1.05}  # p.u.
BASE_MVA = 100

# Parámetros Temporales
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATA_FREQUENCY = "15min"

# Umbrales de Calidad
MAX_MISSING_DATA_PCT = 5.0
MIN_POWER_FACTOR = 0.85
```

---

## 🚀 Comenzar un Nuevo Proyecto

1. **Clonar estructura base**
```bash
git clone https://github.com/[template-repo] mi_proyecto
cd mi_proyecto
```

2. **Configurar constantes específicas**
```python
# Editar src/constants.py con parámetros del sistema
```

3. **Implementar cargadores de datos**
```python
# Adaptar data_loaders.py al formato de datos disponible
```

4. **Seguir las fases**
- Completar cada fase antes de avanzar
- Documentar decisiones y supuestos
- Validar resultados con expertos del dominio

---

## 📚 Referencias y Recursos

- [Caso de Estudio: Línea Sur](./CLAUDE.md) - Implementación completa
- [Guía de Implementación](./project/IMPLEMENTATION_GUIDE.md) - Paso a paso
- [FAQ y Troubleshooting](./FAQ.md) - Problemas comunes

---

**Versión**: 1.0.0  
**Última actualización**: Julio 2025  
**Licencia**: MIT