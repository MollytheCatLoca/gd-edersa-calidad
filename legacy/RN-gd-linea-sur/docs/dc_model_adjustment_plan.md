# Plan de Ajuste del Modelo DC Power Flow

## Diagnóstico del Problema

### Síntomas Observados:
1. **Voltajes negativos**: Físicamente imposible
2. **Sensibilidad 3x mayor**: -0.336 vs -0.112 pu/MW esperado
3. **Pérdidas excesivas**: 31% vs 10% típico

### Causas Probables:
1. **Modelo DC puro inadecuado** para red con:
   - R/X ratio alto (distribución)
   - Voltajes muy bajos (< 0.95 pu)
   - Líneas largas (333 km total)

2. **Sensibilidad lineal insuficiente**:
   - Asume voltaje constante
   - No captura efectos de carga

## Plan de Ajuste - 3 Fases

### Fase 1: Corrección Inmediata del Modelo DC (2 días)

#### 1.1 Revisar Estimación de Voltajes
```python
def _estimate_voltages_corrected(self, flows_mw, loads_mw):
    """
    Método corregido con:
    - Voltaje base realista (0.95 pu en slack)
    - Límites físicos
    - Acumulación correcta de caídas
    """
    # Slack en 0.95 pu (no 1.0)
    voltages[slack] = 0.95
    
    # BFS con caída acumulativa
    for node in bfs_order:
        parent_v = voltages[parent[node]]
        
        # Caída por flujo Y por carga local
        flow_drop = sensitivity * abs(flow_to_node)
        load_drop = local_sensitivity * loads[node]
        
        # Aplicar caída (no suma)
        voltages[node] = parent_v + flow_drop + load_drop
        
        # Límites físicos
        voltages[node] = max(0.80, min(1.05, voltages[node]))
```

#### 1.2 Calibrar Sensibilidades por Tramo
```python
# Sensibilidades diferenciadas por zona
sensitivities = {
    "pilcaniyeu_comallo": -0.08,      # Línea principal
    "comallo_jacobacci": -0.10,       # Media distancia
    "jacobacci_maquinchao": -0.112,   # Medido
    "maquinchao_menucos": -0.115      # Fin de línea
}
```

#### 1.3 Incluir Efecto de R en Pérdidas
```python
def calculate_losses_improved(self, flows_mw):
    """
    Pérdidas considerando R y factor de carga
    """
    for line in lines:
        # Corriente estimada
        I = flow_mw / (sqrt(3) * V * PF)
        
        # Pérdidas I²R reales
        losses = 3 * I² * R / 1000
        
        # Factor de corrección por voltaje bajo
        v_factor = (V_nominal / V_actual)²
        losses *= v_factor
```

### Fase 2: Modelo AC Linealizado (3 días)

#### 2.1 Implementar Jacobiano Simplificado
```python
class LinearizedACPowerFlow:
    """
    Incluye primer orden de V y θ
    """
    def build_jacobian(self):
        # J = [∂P/∂θ  ∂P/∂V]
        #     [∂Q/∂θ  ∂Q/∂V]
        
        # Para red radial, simplificar
        J_Ptheta = -B  # Como DC
        J_PV = diag(P/V)  # Sensibilidad a voltaje
        
        return J_simplified
```

#### 2.2 Iteración con Corrección de Voltaje
```python
def solve_linearized(self, P, Q):
    # Paso 1: DC power flow para ángulos
    theta = solve_dc(P)
    
    # Paso 2: Corregir voltajes
    for iteration in range(3):
        V_new = V_old + J_V * (P_calc - P_spec)
        if converged:
            break
    
    return theta, V
```

### Fase 3: Calibración con Datos Reales (2 días)

#### 3.1 Cargar Eventos Críticos de Fase 3
```python
def calibrate_with_measurements():
    # Cargar eventos donde conocemos V real
    events = load_critical_events()
    
    # Para cada evento
    for event in events:
        # Ejecutar modelo
        v_calc = run_power_flow(event.loads)
        
        # Calcular error
        error = v_calc - event.v_measured
        
        # Ajustar parámetros
        adjust_sensitivities(error)
```

#### 3.2 Análisis de Regresión
```python
def fit_sensitivity_model():
    """
    Ajustar modelo: V = f(P, distancia, hora)
    """
    # Datos históricos
    data = load_phase3_analysis()
    
    # Features
    X = [power, distance_from_slack, hour, is_peak]
    y = voltage_drop
    
    # Regresión
    model = RandomForestRegressor()
    model.fit(X, y)
    
    # Nuevas sensibilidades
    return model.predict
```

#### 3.3 Validación Cruzada
```python
def cross_validate():
    # 80% training, 20% test
    # Métricas: MAE, RMSE voltaje
    # Target: < 5% error
```

## Implementación Alternativa: Híbrido DC-AC

### Concepto: Usar DC + Correcciones
```python
class HybridPowerFlow:
    def solve(self, P, Q):
        # 1. DC rápido para flujos
        flows = dc_power_flow(P)
        
        # 2. Corrección de voltajes con fórmulas AC
        V = calculate_voltage_drop_ac(flows, Q)
        
        # 3. Una iteración AC si necesario
        if max_error > tolerance:
            V, theta = one_ac_iteration(P, Q, V)
        
        return flows, V
```

## Cronograma

### Semana 1
- **Lunes-Martes**: Fase 1 - Correcciones DC
- **Miércoles-Viernes**: Fase 2 - AC Linealizado

### Semana 2  
- **Lunes-Martes**: Fase 3 - Calibración
- **Miércoles**: Testing y validación
- **Jueves-Viernes**: Documentación y integración

## Métricas de Éxito

1. **Error de voltaje < 5%** vs mediciones
2. **Sensibilidad dentro de ±20%** del valor medido
3. **Pérdidas realistas** (5-12% de carga)
4. **Tiempo cálculo < 100ms** para DC mejorado
5. **Tiempo cálculo < 500ms** para AC linealizado

## Decisión de Arquitectura

### Opción A: Mejorar DC (Recomendado para Fase 5.2)
- ✅ Rápido de implementar
- ✅ Mantiene velocidad
- ❌ Precisión limitada

### Opción B: Migrar a AC Linealizado
- ✅ Más preciso
- ✅ Incluye reactivos
- ❌ Más complejo

### Opción C: AC Completo (Futuro)
- ✅ Máxima precisión
- ❌ Lento
- ❌ Puede no converger

## Recomendación

Para Fase 5.2, implementar **Opción A mejorada** con:
1. Voltaje base 0.95 pu
2. Sensibilidades calibradas
3. Límites físicos
4. Pérdidas con factor R

Esto permitirá continuar con evaluación económica mientras se desarrolla AC linealizado en paralelo.