# Fase 5.2 - Semana 1: Motor de Flujo de Potencia DC

## Objetivo
Implementar un motor de flujo de potencia DC simplificado adaptado a la red radial de 33kV de Línea Sur, validado con datos reales de Fase 3.

## Día 1: Fundamentos y Estructura Base

### Tareas:
1. **Crear estructura de módulos**
   ```
   src/power_flow/
   ├── __init__.py
   ├── dc_power_flow.py      # Motor principal
   ├── network_builder.py    # Constructor de matrices
   ├── line_parameters.py    # Parámetros de líneas
   └── validation.py         # Validación contra mediciones
   ```

2. **Implementar clase base DCPowerFlow**
   - Constructor con topología de red
   - Métodos stub para build_ybus, solve, etc.
   - Logging y manejo de errores

3. **Definir parámetros de líneas**
   - Pilcaniyeu-Comallo: 104 km
   - Comallo-Jacobacci: 96 km  
   - Jacobacci-Maquinchao: 75 km
   - Maquinchao-Los Menucos: 58 km
   - Usar conductores de constants.py

### Entregables:
- [ ] Estructura de archivos creada
- [ ] Tests unitarios básicos
- [ ] Documentación de API

## Día 2: Construcción de Matriz Y-bus

### Teoría:
Para flujo DC: `Y_ij = -1/X_ij` (ignoramos resistencia)

### Tareas:
1. **Implementar build_ybus()**
   ```python
   def build_ybus(self):
       """
       Construye matriz Y para flujo DC
       Y_ii = Σ(1/X_ij) para j conectado a i
       Y_ij = -1/X_ij para línea i-j
       """
   ```

2. **Considerar transformadores**
   - ET Pilcaniyeu: 132/33 kV
   - Modelar como reactancia equivalente

3. **Validar matriz**
   - Simétrica
   - Diagonal dominante
   - Suma filas = 0 (excepto slack)

### Entregables:
- [ ] Método build_ybus completo
- [ ] Test con red de 5 nodos
- [ ] Visualización de matriz sparse

## Día 3: Solver de Flujo DC

### Ecuaciones:
```
P_i = Σ_j |V_i||V_j||Y_ij|sin(θ_i - θ_j)
```
Para DC: `V ≈ 1.0`, `sin(θ) ≈ θ`
```
P_i = Σ_j Y_ij(θ_i - θ_j)
```

### Tareas:
1. **Implementar solve()**
   ```python
   def solve(self, generation, loads):
       """
       Resuelve sistema lineal: B·θ = P
       Donde B es Y_bus sin fila/columna slack
       """
       # Formar vector P = P_gen - P_load
       # Eliminar slack bus
       # Resolver sistema lineal
       # Retornar ángulos
   ```

2. **Manejo de slack bus**
   - Pilcaniyeu como slack (θ = 0)
   - Balance de potencia automático

3. **Convergencia y estabilidad**
   - Verificar condicionamiento matriz
   - Manejo de casos singulares

### Entregables:
- [ ] Solver funcionando
- [ ] Comparación con PowerWorld/PSS
- [ ] Manejo de errores robusto

## Día 4: Cálculo de Flujos y Pérdidas

### Tareas:
1. **Implementar calculate_flows()**
   ```python
   def calculate_flows(self, angles):
       """
       Calcula flujos en líneas: P_ij = (θ_i - θ_j)/X_ij
       """
       flows = {}
       for line in self.lines:
           theta_diff = angles[line.from] - angles[line.to]
           flows[line.id] = theta_diff / line.reactance
       return flows
   ```

2. **Estimar pérdidas**
   - Aproximación: `Losses ≈ R * I²`
   - Usar flujos DC para estimar corriente

3. **Validar conservación de potencia**
   - Σ P_gen = Σ P_load + Σ P_losses
   - Tolerancia < 0.1%

### Entregables:
- [ ] Flujos en todas las líneas
- [ ] Estimación de pérdidas
- [ ] Report de balance

## Día 5: Estimación de Voltajes

### Usando sensibilidad dV/dP = -0.112 pu/MW

### Tareas:
1. **Implementar estimate_voltages()**
   ```python
   def estimate_voltages(self, flows, loads):
       """
       Estima caída de voltaje acumulada desde slack
       """
       voltages = {self.slack: 1.0}
       
       # BFS desde slack
       for node in self.bfs_order:
           upstream_v = voltages[self.parent[node]]
           flow_mw = flows[self.line_to[node]]
           delta_v = self.sensitivity * flow_mw
           voltages[node] = upstream_v + delta_v
           
       return voltages
   ```

2. **Calibrar con mediciones reales**
   - Ajustar sensibilidad por tramo
   - Considerar efectos locales

3. **Validar contra eventos críticos**
   - Cargar eventos de critical_events.json
   - Comparar voltajes calculados vs medidos

### Entregables:
- [ ] Perfil de voltajes completo
- [ ] Error vs mediciones < 5%
- [ ] Identificación nodos críticos

## Día 6: Integración con Datos Fase 3

### Tareas:
1. **Cargar topología real**
   ```python
   def load_from_phase3():
       """Carga red desde sistema_linea_sur.json"""
       # Nodos: Pilcaniyeu, Comallo, Jacobacci, etc.
       # Líneas con parámetros reales
       # Transformadores
   ```

2. **Cargar perfiles de demanda**
   - typical_days.json
   - Perfiles horarios por estación

3. **Validar con caso conocido**
   - Día con máxima caída (2024-07-15 20:00)
   - Comparar resultados

### Entregables:
- [ ] Integración completa con datos reales
- [ ] Simulación 24 horas
- [ ] Reporte de validación

## Día 7: Optimización y Performance

### Tareas:
1. **Profiling y optimización**
   - Identificar bottlenecks
   - Optimizar operaciones matriciales
   - Implementar caché básico

2. **Paralelización**
   - Múltiples escenarios en paralelo
   - Uso eficiente de NumPy

3. **Documentación final**
   - Guía de usuario
   - Ejemplos de uso
   - Limitaciones del modelo DC

### Entregables:
- [ ] Performance < 100ms por caso
- [ ] Suite de benchmarks
- [ ] Documentación completa

## Validación Final

### Criterios de Aceptación:
1. **Precisión**
   - Error en flujos < 10% vs AC
   - Error en voltajes < 5% vs mediciones

2. **Performance**  
   - Caso individual < 100ms
   - 24 horas (96 casos) < 5 segundos

3. **Robustez**
   - Maneja desconexiones
   - Converge en todos los casos históricos

4. **Integración**
   - Compatible con el resto del framework
   - APIs claras y documentadas

## Herramientas y Referencias

### Software:
- NumPy/SciPy para álgebra lineal
- NetworkX para topología
- Matplotlib para visualización
- PyTest para testing

### Referencias:
1. Wood & Wollenberg - "Power Generation, Operation and Control"
2. Grainger & Stevenson - "Power System Analysis"
3. Papers sobre DC OPF para redes de distribución

## Riesgos Técnicos

1. **Aproximación DC muy cruda**
   - Mitigación: Validar extensivamente
   - Plan B: Modelo AC linealizado

2. **Datos de líneas imprecisos**
   - Mitigación: Calibrar con mediciones
   - Análisis de sensibilidad

3. **Red no completamente radial**
   - Verificar topología real
   - Adaptar si hay mallas

## Código Ejemplo Base

```python
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve

class DCPowerFlow:
    def __init__(self, nodes, lines, base_mva=100):
        self.nodes = nodes
        self.lines = lines
        self.base_mva = base_mva
        self.n_nodes = len(nodes)
        self.slack_idx = 0  # Pilcaniyeu
        
    def solve_case(self, gen_mw, load_mw):
        """Resuelve un caso de flujo DC"""
        # 1. Build Y-bus
        Y = self.build_ybus()
        
        # 2. Form P injection vector
        P = (gen_mw - load_mw) / self.base_mva
        
        # 3. Remove slack
        B = Y[1:, 1:]
        P_reduced = P[1:]
        
        # 4. Solve
        theta_reduced = spsolve(B, P_reduced)
        
        # 5. Add slack angle (0)
        theta = np.zeros(self.n_nodes)
        theta[1:] = theta_reduced
        
        return theta
```

---

**Próximo paso**: Comenzar con Día 1 - Crear estructura y clase base