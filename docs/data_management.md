# SISTEMA DE GESTIÓN DE DATOS - ESTUDIO GD LÍNEA SUR
## Documentación del DataManager y Arquitectura de Datos

---

## 1. INTRODUCCIÓN Y FILOSOFÍA

### 1.1 Principio Fundamental: "Single Source of Truth"
El módulo `data_manager.py` es la **ÚNICA FUENTE DE VERDAD** para todos los datos del sistema. Ningún componente del dashboard debe cargar datos directamente desde archivos JSON o procesados. Todo acceso a datos DEBE pasar por el DataManager.

### 1.2 Motivación
- **Consistencia**: Garantizar que todos los componentes vean los mismos datos
- **Transparencia**: Siempre saber si estamos usando datos reales o de respaldo
- **Mantenibilidad**: Un solo punto de cambio para la lógica de carga
- **Trazabilidad**: Logging centralizado de acceso a datos
- **Resiliencia**: Manejo robusto de errores con fallback automático

---

## 2. ARQUITECTURA DEL DATAMANAGER

### 2.1 Ubicación y Estructura
```
dashboard/
└── pages/
    ├── utils/
    │   ├── __init__.py
    │   └── data_manager.py    # ← ÚNICA FUENTE DE VERDAD
    └── components/
        ├── tab1_overview.py   # Usa data_manager
        ├── tab2_transformers.py # Usa data_manager
        ├── tab3_lines.py      # Usa data_manager
        ├── tab4_loads.py      # Usa data_manager
        └── tab5_regulation.py # Usa data_manager
```

### 2.2 Patrón Singleton
El DataManager implementa el patrón Singleton para garantizar una única instancia:

```python
# Siempre obtener la misma instancia
from ..utils import get_data_manager
dm = get_data_manager()
```

### 2.3 Estados de Datos (DataStatus)
```python
class DataStatus(Enum):
    REAL = "real"           # Datos reales cargados exitosamente
    PARTIAL = "partial"     # Algunos datos reales, otros faltantes
    FALLBACK = "fallback"   # Usando datos de respaldo
    ERROR = "error"         # Error al cargar datos
```

---

## 3. FLUJO DE DATOS

### 3.1 Diagrama de Flujo de Carga

```
┌─────────────────────────────────────────────────────────────┐
│                    INICIALIZACIÓN                           │
│              (automática al crear instancia)                │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │    _load_all_data()       │
        └─────────────┬─────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────────┐
        │             │             │                  │
        ▼             ▼             ▼                  ▼
┌───────────┐ ┌───────────┐ ┌────────────┐  ┌───────────────┐
│  SYSTEM   │ │TRANSFORM. │ │HISTORICAL  │  │UPDATE OVERALL │
│   DATA    │ │  DETAILS  │ │   DATA     │  │    STATUS     │
└─────┬─────┘ └─────┬─────┘ └─────┬──────┘  └───────────────┘
      │             │             │
      ▼             ▼             ▼
┌───────────┐ ┌───────────┐ ┌────────────┐
│ Try: JSON │ │ Try: JSON │ │Placeholder │
│ Validate  │ │ Fallback  │ │   Future   │
│ Fallback  │ │  System   │ │            │
└───────────┘ └───────────┘ └────────────┘
```

### 3.2 Rutas de Archivos

```
proyecto/
├── data/
│   ├── processed/
│   │   ├── sistema_linea_sur.json      # Principal
│   │   └── transformadores_detalle.json # Secundario
│   └── fallback/
│       └── (futuro: fallback_data.json)
└── dashboard/
    └── pages/
        └── utils/
            └── data_manager.py         # Carga estos archivos
```

### 3.3 Prioridad de Datos
1. **Datos Reales**: Archivos JSON en `/data/processed/`
2. **Datos Parciales**: Combinación de fuentes (ej: transformadores del archivo sistema)
3. **Datos Fallback**: Mínimos hardcodeados para mantener funcionamiento

---

## 4. USO EN COMPONENTES

### 4.1 Importación Correcta

```python
# ✅ CORRECTO - Usar DataManager
from ..utils import get_data_manager

def render_tab():
    dm = get_data_manager()
    nodes = dm.get_nodes()
    
# ❌ INCORRECTO - Carga directa
import json
with open('sistema_linea_sur.json') as f:
    data = json.load(f)  # NUNCA HACER ESTO
```

### 4.2 Métodos de Acceso Disponibles

```python
dm = get_data_manager()

# Métodos de acceso directo (retornan diccionarios)
nodes = dm.get_nodes()              # Dict[str, Any] - Nodos del sistema
edges = dm.get_edges()              # Dict[str, Any] - Tramos/líneas
transformers = dm.get_transformers() # Dict[str, Any] - Transformadores
summary = dm.get_system_summary()    # Dict[str, Any] - Resumen sistema
metadata = dm.get_metadata()         # Dict[str, Any] - Metadata

# Métodos con información de estado (retornan tupla)
system_data, status = dm.get_system_data()      # (data, DataStatus)
trans_data, status = dm.get_transformer_details() # (data, DataStatus)

# Métodos de estado y control
status_summary = dm.get_status_summary() # Estado completo
status_color = dm.get_status_color()     # Color para UI
status_text = dm.get_status_text()       # Texto para UI
dm.reload_data()                         # Forzar recarga
```

### 4.3 Ejemplo: Manejo de Estados

```python
def render_component():
    dm = get_data_manager()
    
    # Verificar si usa fallback
    status_summary = dm.get_status_summary()
    if status_summary['is_using_fallback']:
        warning = dbc.Alert(
            "⚠️ Usando datos de respaldo. Algunos valores pueden no estar actualizados.",
            color="warning"
        )
    else:
        warning = None
    
    # Obtener datos específicos con verificación
    system_data, status = dm.get_system_data()
    if status == DataStatus.ERROR:
        return html.Div("Error cargando datos")
    
    nodes = dm.get_nodes()
    # ... usar datos normalmente
```

### 4.4 Estado Visual en Dashboard

El dashboard muestra automáticamente un indicador visual:
- 🟢 **Verde** (success): Datos reales cargados
- 🟡 **Amarillo** (warning): Datos parciales
- 🔴 **Rojo** (danger): Usando datos de respaldo
- ⚫ **Negro** (dark): Error crítico de datos

---

## 5. LÓGICA DE VALIDACIÓN Y FALLBACK

### 5.1 Proceso de Validación

```python
def _validate_system_data(self, data: Dict[str, Any]) -> bool:
    """Valida estructura mínima requerida"""
    required_keys = ["nodes", "edges", "transformers"]
    return all(key in data for key in required_keys)
```

### 5.2 Estructura de Datos Fallback

```python
# Fallback mínimo para sistema
{
    "metadata": {
        "name": "Sistema Eléctrico Línea Sur (FALLBACK)",
        "operator": "EdERSA",
        "total_length_km": 270,
        "last_updated": "FALLBACK DATA"
    },
    "nodes": {
        # Solo nodos críticos
        "pilcaniyeu": {...},
        "jacobacci": {...},
        "los_menucos": {...}
    },
    "edges": {},  # Vacío en fallback
    "transformers": {},  # Vacío en fallback
    "system_summary": {
        "total_load": {
            "active_power_mw": 3.80,
            "reactive_power_mvar": 1.05,
            "power_factor": 0.964
        }
    }
}
```

### 5.3 Logging y Trazabilidad

```python
# Éxito
logger.info(f"Successfully loaded system data from {file_path}")

# Advertencia con fallback
logger.warning(f"Failed to load system data: {e}")

# Estado actual
logger.info(f"DataManager initialized with status: {self.data_status['overall']}")
```

---

## 6. MANTENIMIENTO Y EXTENSIÓN

### 6.1 Agregar Nueva Fuente de Datos

Para agregar una nueva fuente (ej: datos de mediciones):

```python
# 1. En __init__, agregar storage
self._measurements_data = None

# 2. Agregar a status tracking
self.data_status["measurements"] = DataStatus.ERROR
self.load_attempts["measurements"] = 0
self.last_load["measurements"] = None

# 3. Crear método de carga
def _load_measurements_data(self) -> None:
    """Load historical measurements"""
    self.load_attempts["measurements"] += 1
    try:
        file_path = self.data_path / "measurements.json"
        with open(file_path, 'r') as f:
            self._measurements_data = json.load(f)
        self.data_status["measurements"] = DataStatus.REAL
    except Exception as e:
        logger.warning(f"Failed to load measurements: {e}")
        self._measurements_data = {}
        self.data_status["measurements"] = DataStatus.FALLBACK

# 4. Agregar a _load_all_data()
def _load_all_data(self):
    # ... existing loads ...
    self._load_measurements_data()

# 5. Crear método público
def get_measurements(self) -> Dict[str, Any]:
    """Get measurements data"""
    return self._measurements_data or {}
```

### 6.2 Actualización en Tiempo Real

```python
# En cualquier componente
def handle_refresh_click():
    dm = get_data_manager()
    dm.reload_data()  # Recarga todos los archivos
    # Actualizar UI...
```

### 6.3 Debugging y Diagnóstico

```python
# Obtener resumen completo de estado
status = dm.get_status_summary()
print(f"Estados: {status['status']}")
print(f"Intentos de carga: {status['load_attempts']}")
print(f"Última carga: {status['last_load']}")
print(f"Usando fallback: {status['is_using_fallback']}")
```

---

## 7. INTEGRACIÓN CON CLAUDE.md

### 7.1 Sección Requerida en CLAUDE.md

```markdown
### GESTIÓN DE DATOS - PRÁCTICA OBLIGATORIA

**REGLA FUNDAMENTAL**: El DataManager es la ÚNICA fuente de verdad para datos.

**SIEMPRE**:
- Importar: `from ..utils import get_data_manager`
- Obtener instancia: `dm = get_data_manager()`
- Acceder a datos vía métodos: `nodes = dm.get_nodes()`

**NUNCA**:
- Importar `json` en componentes
- Abrir archivos directamente con `open()`
- Cargar datos sin pasar por DataManager

**Documentación completa**: `/docs/data_management.md`

**Verificación rápida**:
```python
# ✅ CORRECTO
dm = get_data_manager()
data = dm.get_nodes()

# ❌ INCORRECTO
with open('data.json') as f:
    data = json.load(f)
```
```

### 7.2 Checklist para Code Review

- [ ] No importa `json` (excepto en data_manager.py)
- [ ] No usa `open()` para archivos de datos
- [ ] Importa `get_data_manager`
- [ ] Usa métodos del DataManager correctamente
- [ ] Maneja estados de error/fallback si crítico
- [ ] No duplica lógica de carga de datos

---

## 8. PATRONES Y MEJORES PRÁCTICAS

### 8.1 Patrón Básico de Componente

```python
# components/mi_componente.py
from dash import html, dcc
import plotly.graph_objects as go
from ..utils import get_data_manager

def render_mi_componente():
    # 1. Obtener DataManager
    dm = get_data_manager()
    
    # 2. Obtener datos necesarios
    nodes = dm.get_nodes()
    edges = dm.get_edges()
    summary = dm.get_system_summary()
    
    # 3. Procesar datos
    total_load = summary.get('total_load', {})
    power_mw = total_load.get('active_power_mw', 0)
    
    # 4. Crear visualización
    return html.Div([
        html.H3(f"Carga Total: {power_mw:.2f} MW"),
        dcc.Graph(figure=create_figure(nodes, edges))
    ])
```

### 8.2 Componente con Manejo de Estado

```python
def render_critical_component():
    dm = get_data_manager()
    
    # Verificar estado crítico
    system_data, status = dm.get_system_data()
    
    if status == DataStatus.ERROR:
        return dbc.Alert(
            "Error crítico cargando datos del sistema",
            color="danger"
        )
    
    if status == DataStatus.FALLBACK:
        warning = dbc.Alert(
            "Usando datos de respaldo limitados",
            color="warning",
            dismissable=True
        )
    else:
        warning = None
    
    # Continuar con lógica normal
    nodes = dm.get_nodes()
    
    return html.Div([
        warning,
        # ... resto del componente
    ])
```

### 8.3 Callback con DataManager

```python
@callback(
    Output("mi-grafico", "figure"),
    Input("mi-dropdown", "value")
)
def update_graph(selected_node):
    dm = get_data_manager()  # Obtener en cada callback
    
    nodes = dm.get_nodes()
    if selected_node not in nodes:
        return go.Figure()  # Gráfico vacío
    
    node_data = nodes[selected_node]
    # ... crear figura
```

---

## 9. TROUBLESHOOTING

### 9.1 Problemas Comunes

**Problema**: Badge siempre rojo (fallback)
- **Causa**: Archivos JSON no encontrados
- **Solución**: Verificar rutas en `/data/processed/`

**Problema**: Datos no se actualizan
- **Causa**: Singleton mantiene datos en memoria
- **Solución**: Llamar `dm.reload_data()`

**Problema**: Error de importación
- **Causa**: Path relativo incorrecto
- **Solución**: Usar `from ..utils import get_data_manager`

### 9.2 Logs de Diagnóstico

```bash
# Ver logs del DataManager
grep "DataManager" logs/app.log

# Ver intentos de carga
grep "load.*data" logs/app.log

# Ver fallos
grep "WARNING.*Failed" logs/app.log
```

---

## 10. CONCLUSIÓN

El DataManager es fundamental para la integridad del sistema. Su uso correcto garantiza:

1. **Confiabilidad**: Dashboard siempre funcional
2. **Transparencia**: Usuario informado del estado
3. **Mantenibilidad**: Un punto de cambio
4. **Consistencia**: Todos ven lo mismo
5. **Performance**: Carga optimizada

### REGLA DE ORO
> Si necesitas datos, usa DataManager. Sin excepciones.

### RECORDATORIO PARA CLAUDE
> Al trabajar con este proyecto, SIEMPRE verificar que los componentes usen DataManager. Es requisito obligatorio documentado en CLAUDE.md.

---

*Última actualización: Julio 2025*  
*Versión: 1.0*  
*Autor: Sistema de Documentación Automática*