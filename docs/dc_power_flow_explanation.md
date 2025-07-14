# ¿Por qué Modelo DC en una Red AC?

## La Red Real es AC
Sí, la red de Línea Sur opera en corriente alterna (AC) a 33 kV, 50 Hz. Todos los sistemas de potencia comerciales son AC.

## ¿Entonces por qué usar modelo DC?

### 1. Simplificación Matemática
El flujo de potencia AC completo requiere resolver ecuaciones no lineales:
```
P_i = Σ |V_i||V_j||Y_ij|cos(θ_i - θ_j - φ_ij)
Q_i = Σ |V_i||V_j||Y_ij|sin(θ_i - θ_j - φ_ij)
```

El modelo DC las simplifica a ecuaciones lineales:
```
P_i = Σ (θ_i - θ_j)/X_ij
```

### 2. Ventajas del Modelo DC

**Velocidad**
- AC: Iterativo (Newton-Raphson), 10-50 iteraciones
- DC: Directo (una inversión de matriz), < 1 ms

**Robustez**
- AC: Puede no converger
- DC: Siempre converge (sistema lineal)

**Suficiente para muchos análisis**
- Flujos de potencia activa (P)
- Análisis de contingencias rápido
- Screening de alternativas

### 3. Cuándo es Válido el Modelo DC

✅ **Válido cuando:**
- Ángulos pequeños (< 10-15°)
- X >> R (líneas de transmisión)
- Voltajes cercanos a 1.0 pu
- Solo interesa potencia activa

❌ **NO válido para:**
- Análisis de potencia reactiva (Q)
- Voltajes precisos
- Pérdidas exactas
- Redes de distribución con R alto

### 4. Nuestro Caso: Línea Sur

**Problemático porque:**
- Red de distribución 33 kV (R no despreciable)
- Voltajes muy bajos (< 0.95 pu)
- Necesitamos voltajes precisos

**Aún útil porque:**
- Primera aproximación rápida
- Identificar flujos de potencia
- Base para optimización

## Alternativas

### 1. AC Linealizado
Incluye primer orden de voltajes:
```
ΔP = J_P * [Δθ, ΔV]
ΔQ = J_Q * [Δθ, ΔV]
```

### 2. AC Completo
Newton-Raphson completo, más preciso pero más lento.

### 3. Modelo Híbrido (Recomendado)
- DC para screening rápido
- AC linealizado para análisis
- AC completo para casos finales

## Conclusión

Usamos DC como **primera aproximación** sabiendo sus limitaciones. Para Línea Sur con voltajes bajos, necesitamos ajustes significativos o migrar a AC linealizado.