# FASE 2: MODELADO Y VISUALIZACIÓN DE TOPOLOGÍA
## Representación Digital del Sistema Eléctrico Línea Sur

### 1. RESUMEN EJECUTIVO

La Fase 2 completó el modelado digital del sistema de transmisión mediante NetworkX y desarrolló visualizaciones interactivas que distinguen claramente entre datos reales, teóricos y estimados. Se implementó la regla fundamental de usar el DataManager como única fuente de verdad para TODOS los datos.

**Logros Principales:**
- Sistema modelado como grafo dirigido con NetworkX
- Visualizaciones interactivas con distinción de tipos de datos
- DataManager expandido con datos teóricos para comparación futura
- GD Los Menucos (1.8 MW) integrada en visualizaciones
- Cero hardcoding - TODO viene del DataManager

### 2. INPUTS DE LA FASE 2

#### 2.1 Datos del Sistema (DataManager)
```python
# Fuentes de datos utilizadas:
- get_nodes()              # Nodos/estaciones del sistema
- get_edges()              # Líneas/tramos
- get_transformers()       # Transformadores
- get_gd_costs()          # Costos GD actual (1.8 MW)
- get_theoretical_voltages()  # Voltajes teóricos (nuevo)
- get_theoretical_losses()    # Pérdidas teóricas (nuevo)
- get_impedances()           # Impedancias líneas (nuevo)
```

#### 2.2 Librerías y Herramientas
- **NetworkX**: Modelado de red como grafo
- **Plotly**: Visualizaciones interactivas
- **Dash/DBC**: Framework del dashboard
- **NetworkTopology**: Clase personalizada para análisis
- **NetworkVisualizer**: Clase para visualizaciones

#### 2.3 Datos de Fase 1
- Topología completa del sistema
- Cargas por estación
- Ubicación GD Los Menucos
- Análisis de costos GD

### 3. PROCESAMIENTO Y MODELADO

#### 3.1 Modelo NetworkX
```python
# Estructura del grafo
Nodos: 7 estaciones (Pilcaniyeu → Los Menucos)
Aristas: 6 tramos con impedancias
Atributos nodo:
  - coordinates (lat, lon)
  - load_mw, load_mvar
  - distance_from_origin_km
  - population
  
Atributos arista:
  - length_km
  - conductor_type
  - impedance (R, X, Z)
```

#### 3.2 Cálculos Implementados
- Impedancias acumuladas por tramo
- Cargas downstream por nodo
- Validación de topología radial
- Identificación de caminos

### 4. OUTPUTS Y VISUALIZACIONES

#### 4.1 Mapa Interactivo del Sistema
- **Tipo**: Plotly Scattermap
- **Elementos**:
  - Nodos coloreados por criticidad
  - Líneas con grosor según conductor
  - Marcador especial GD (cuadrado púrpura)
  - Tooltips con información completa
- **Datos mostrados**:
  - GD Los Menucos: 1.8 MW @ 4h/día 🟢 DATO
  - Cargas por estación 🟢 DATO
  - Distancias 🟢 DATO

#### 4.2 Perfil de Tensión
- **Tipo**: Gráfico línea con zonas
- **Datos**:
  - Voltajes teóricos (0.15%/km) 🟡 TEORICO
  - Espacio para datos reales 🟢 DATO (Fase 3)
  - Límites regulatorios (0.95-1.05 pu)
  - Zona crítica sombreada
- **Nota clara**: "Valores estimados - datos reales en Fase 3"

#### 4.3 Distribución de Cargas
- **Tipo**: Gráfico barras horizontales
- **Datos**: MW y MVAr por estación 🟢 DATO
- **Ordenamiento**: Por magnitud de carga

#### 4.4 Análisis de Pérdidas
- **Tipo**: Gráfico barras con anotaciones
- **Datos teóricos** 🟡 TEORICO:
  - Pilcaniyeu-Comallo: 0.08 MW (20%)
  - Comallo-Jacobacci: 0.12 MW (30%)
  - Jacobacci-Maquinchao: 0.10 MW (25%)
  - Maquinchao-Los Menucos: 0.10 MW (25%)
  - **Total**: 0.40 MW (10%)
- **Nota**: "Para comparar con pérdidas reales"

#### 4.5 Panel Estado GD
- **Datos del DataManager**:
  - Potencia: 1.8 MW 🟢 DATO
  - Expansión planificada: 3.0 MW 🔵 REFERENCIA
  - Operación: 4h/día (FC 16.7%)
  - Costo: $138.6/MWh 🟢 DATO
- **Información adicional**:
  - Tecnología: Motogeneradores gas
  - Conexión: 13.2 kV
  - Limitación: Alto costo operativo

#### 4.6 Tabla Impedancias
- **Tipo**: Tabla HTML
- **Datos** 🔵 REFERENCIA:
  - Comallo: Z = 33.43 Ω
  - Jacobacci: Z = 71.64 Ω
  - Maquinchao: Z = 101.47 Ω
  - Los Menucos: Z = 142.35 Ω
- **Fuente**: Catálogo conductores ACSR

### 5. DATOS PARA PRÓXIMAS FASES

#### 5.1 Modelo de Red Completo
- Grafo NetworkX serializable
- Topología validada
- Impedancias calculadas
- Listo para flujos de potencia

#### 5.2 Base para Comparaciones
```python
# Datos teóricos registrados para comparar:
theoretical_voltages = {
    "PILCANIYEU": 1.000,  # Referencia
    "JACOBACCI": 0.775,   # Teórico
    "LOS MENUCOS": 0.595  # Teórico
}

# Cuando lleguen datos reales (Fase 3):
deviation = real_voltage - theoretical_voltage
```

#### 5.3 Puntos Candidatos Solar
Identificados visualmente:
- Jacobacci: Alta carga (1.45 MW)
- Maquinchao: Zona crítica
- Los Menucos: Final de línea

### 6. IMPLEMENTACIÓN TÉCNICA

#### 6.1 Arquitectura
```
fase2_topologia.py
├── create_network_figure()      # Mapa principal
├── create_voltage_profile()     # Perfil tensión
├── create_load_distribution()   # Distribución cargas
├── create_losses_visualization() # Pérdidas por tramo
├── populate_gd_panel()          # Callback panel GD
└── populate_impedances_table()  # Callback impedancias
```

#### 6.2 Uso del DataManager
```python
# TODOS los datos vienen del DataManager
dm = get_data_manager()

# Datos reales
gd_costs = dm.get_gd_costs()

# Datos teóricos
theoretical_voltages = dm.get_theoretical_voltages()
theoretical_losses = dm.get_theoretical_losses()

# Referencias
impedances = dm.get_impedances()

# PROHIBIDO: valores hardcodeados
```

#### 6.3 Callbacks Dinámicos
- Panel GD: Poblado desde DataManager
- Tabla impedancias: Datos desde DataManager
- Selector nodos: Análisis detallado

### 7. LECCIONES APRENDIDAS

#### 7.1 DataManager como Única Fuente
- **Crítico**: NUNCA hardcodear datos
- **Beneficio**: Trazabilidad completa
- **Futuro**: Fácil agregar datos reales

#### 7.2 Transparencia de Datos
- Usuarios ven qué es real vs teórico
- Builds confianza en el análisis
- Prepara para validación

#### 7.3 Visualización Efectiva
- Mapas interactivos comunican mejor
- Distinción visual de tipos de datos
- Tooltips informativos esenciales

### 8. PRÓXIMOS PASOS

#### 8.1 Fase 3: Datos Reales
- Cargar mediciones EPRE
- Comparar con teóricos
- Calcular desviaciones

#### 8.2 Fase 5: Machine Learning
- Usar modelo de red
- Predecir con GD solar
- Optimizar ubicaciones

#### 8.3 Fase 6: Flujos de Potencia
- Implementar Newton-Raphson
- O integrar pandapower
- Validar con mediciones

### 9. CONCLUSIONES

La Fase 2 logró:
1. **Modelado completo** del sistema eléctrico
2. **Visualizaciones claras** con distinción de datos
3. **DataManager expandido** con datos teóricos
4. **Base sólida** para análisis de alternativas solares
5. **Cero hardcoding** - práctica obligatoria implementada

El sistema está listo para recibir datos reales y comenzar análisis comparativos.

### 10. ARCHIVOS Y REFERENCIAS

#### 10.1 Archivos Creados/Modificados
- `/dashboard/pages/fase2_topologia.py` - Dashboard principal
- `/dashboard/pages/utils/data_manager.py` - Nuevos métodos teóricos
- `/src/network/topology.py` - Modelo NetworkX
- `/src/network/visualization.py` - Visualizaciones

#### 10.2 Datos en DataManager
- `get_theoretical_voltages()` - Voltajes con caída 0.15%/km
- `get_theoretical_losses()` - Pérdidas 10% estimadas
- `get_impedances()` - Valores de catálogo ACSR

#### 10.3 Documentación Relacionada
- `CLAUDE.md` - Actualizado con regla DataManager
- `fase1_comprension_red.md` - Datos de entrada
- `/docs/data_management.md` - Guía del DataManager

---

*Documento generado: Julio 2025*
*Fase 2 completada con modelado integral y visualización transparente*