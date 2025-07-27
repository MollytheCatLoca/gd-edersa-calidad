# KB.1 - MARCO TEÓRICO Y FUNDAMENTOS
## Análisis de Redes Eléctricas Débiles con Generación Distribuida

---

## ÍNDICE

1. [INTRODUCCIÓN](#1-introducción)
2. [TEORÍA DE REDES ELÉCTRICAS DÉBILES](#2-teoría-de-redes-eléctricas-débiles)
3. [GENERACIÓN DISTRIBUIDA EN SISTEMAS DÉBILES](#3-generación-distribuida-en-sistemas-débiles)
4. [ALMACENAMIENTO DE ENERGÍA Y SERVICIOS DE RED](#4-almacenamiento-de-energía-y-servicios-de-red)
5. [MARCO REGULATORIO Y NORMATIVO](#5-marco-regulatorio-y-normativo)
6. [REFERENCIAS](#6-referencias)

---

## 1. INTRODUCCIÓN

### 1.1 Objetivo del Documento

Este documento establece los fundamentos teóricos para el análisis de sistemas eléctricos débiles y la integración de generación distribuida (GD) con almacenamiento, proporcionando las bases conceptuales para evaluaciones técnico-económicas reproducibles.

### 1.2 Alcance

El marco teórico abarca:
- Caracterización de redes eléctricas débiles
- Impacto de la generación distribuida
- Servicios de red avanzados
- Almacenamiento en puntas de línea
- Criterios de calidad y confiabilidad

### 1.3 Definiciones Clave

**Red Eléctrica Débil**: Sistema con alta impedancia, baja potencia de cortocircuito y sensibilidad significativa a variaciones de carga/generación.

**Generación Distribuida (GD)**: Fuentes de generación conectadas directamente a la red de distribución, típicamente <10 MW.

**Servicios Auxiliares**: Funciones que mantienen la confiabilidad y calidad del sistema (regulación de frecuencia, voltaje, reservas).

---

## 2. TEORÍA DE REDES ELÉCTRICAS DÉBILES

### 2.1 Definición y Características

#### 2.1.1 Parámetros Fundamentales

Una red se considera "débil" cuando cumple:

```
SCR (Short Circuit Ratio) = Scc / Sgen < 10
X/R ratio > 5
Sensibilidad dV/dP > 0.05 pu/MW
```

Donde:
- **Scc**: Potencia de cortocircuito en el punto de conexión [MVA]
- **Sgen**: Potencia de generación instalada [MVA]
- **X/R**: Relación reactancia/resistencia de la línea

#### 2.1.2 Características Operativas

**Tabla 2.1: Comparación Red Fuerte vs Red Débil**

| Parámetro | Red Fuerte | Red Débil | Impacto Operativo |
|-----------|------------|-----------|-------------------|
| SCR | >20 | <10 | Estabilidad voltaje |
| Regulación V | <5% | >10% | Calidad servicio |
| Sensibilidad dV/dP | <0.01 pu/MW | >0.05 pu/MW | Control generación |
| Constante inercia | Alta | Baja | Estabilidad frecuencia |

### 2.2 Problemática Típica de Líneas Rurales

#### 2.2.1 Caída de Voltaje

La caída de voltaje en una línea se calcula mediante:

**Ecuación 2.1: Caída de Voltaje Aproximada**
```
ΔV = (P·R + Q·X) / V₀
```

Donde:
- ΔV: Caída de voltaje [kV]
- P: Potencia activa [MW]
- Q: Potencia reactiva [MVAr]
- R: Resistencia de línea [Ω]
- X: Reactancia de línea [Ω]
- V₀: Voltaje nominal [kV]

**Ejemplo Línea Sur**: Con P=2.5 MW, R=15 Ω, X=20 Ω, V₀=33 kV
```
ΔV = (2.5×15 + 0.5×20) / 33 = 1.44 kV (4.4%)
```

#### 2.2.2 Pérdidas Técnicas Elevadas

**Ecuación 2.2: Pérdidas por Efecto Joule**
```
Ppérdidas = 3 × I² × R = 3 × (S/(√3×V))² × R
```

Para líneas largas rurales:
```
Ppérdidas(%) = (P² + Q²) × R × L / (V² × P) × 100
```

Donde L es la longitud de línea [km]

### 2.3 Límites Operativos y Regulatorios

#### 2.3.1 Límites de Voltaje (Argentina - ENRE)

**Tabla 2.2: Límites Regulatorios de Voltaje**

| Nivel Tensión | Condición Normal | Condición Contingencia |
|--------------|------------------|------------------------|
| 132-500 kV | ±5% | ±10% |
| 33-66 kV | ±7% | ±10% |
| 13.2 kV | ±8% | ±10% |
| BT (<1kV) | ±8% | ±10% |

#### 2.3.2 Índices de Calidad

**Ecuación 2.3: SAIFI (System Average Interruption Frequency Index)**
```
SAIFI = Σ(Ni) / NT = Interrupciones totales / Usuarios totales
```

**Ecuación 2.4: SAIDI (System Average Interruption Duration Index)**
```
SAIDI = Σ(ri × Ni) / NT = Minutos sin servicio / Usuarios totales
```

Límites típicos Argentina:
- SAIFI urbano: <6 int/año
- SAIFI rural: <12 int/año
- SAIDI urbano: <10 h/año
- SAIDI rural: <25 h/año

### 2.4 Modelado de Redes Débiles

#### 2.4.1 Modelo π Equivalente

Para líneas medianas (50-250 km):

**Figura 2.1: Modelo π de Línea**
```
    I₁ →        R + jX         ← I₂
V₁ ●━━━━━━━━━━━━━━━━━━━━━━━━━━━● V₂
    │                            │
    │ Y/2                    Y/2 │
    ⏚                            ⏚
```

Donde:
- Y = G + jB (admitancia shunt)
- Típicamente G ≈ 0 para líneas aéreas

#### 2.4.2 Matriz de Sensibilidad

**Ecuación 2.5: Sensibilidad Voltaje-Potencia**
```
[ΔV] = [S] × [ΔP]
```

Donde [S] es la matriz de sensibilidad ∂V/∂P

Para el caso Jacobacci: S = 0.0115 pu/MW

---

## 3. GENERACIÓN DISTRIBUIDA EN SISTEMAS DÉBILES

### 3.1 Impacto de la GD en Voltaje

#### 3.1.1 Elevación de Voltaje Local

**Ecuación 3.1: Cambio de Voltaje por GD**
```
ΔV_GD = (P_GD × R - Q_GD × X) / V₀
```

Notar el signo negativo para Q_GD cuando genera reactiva.

**Ejemplo**: GD de 1 MW en Jacobacci
```
ΔV = (1.0 × 15) / 33 = 0.45 kV = 0.0136 pu ✓
```

#### 3.1.2 Límite de Penetración

**Ecuación 3.2: Penetración Máxima sin Violación**
```
P_GD_max = (V_max - V_min) × V₀ / R
```

Para V_max = 1.05 pu, V_min = 0.92 pu:
```
P_GD_max = (1.05 - 0.92) × 33 / 15 = 0.286 MW por punto
```

### 3.2 Reducción de Pérdidas por Generación Local

#### 3.2.1 Pérdidas con GD Distribuida

**Ecuación 3.3: Factor de Reducción de Pérdidas**
```
FRP = 1 - (1 - α)² 
```

Donde α = P_GD / P_carga (penetración GD)

Para α = 0.5 (50% generación local):
```
FRP = 1 - (1 - 0.5)² = 0.75 (75% reducción)
```

#### 3.2.2 Ubicación Óptima de GD

**Ecuación 3.4: Posición Óptima (Método 2/3)**
```
d_opt = (2/3) × L
```

Para minimizar pérdidas totales en alimentador uniforme.

### 3.3 Estabilidad con Alta Penetración GD

#### 3.3.1 Límite de Estabilidad Estático

**Ecuación 3.5: Margen de Estabilidad**
```
MS = (P_max - P_op) / P_op × 100%
```

Donde:
```
P_max = V₁ × V₂ × sin(δ_max) / X
```

Típicamente δ_max = 30° para margen seguro.

#### 3.3.2 Respuesta Inercial Virtual

Para GD basada en inversores:

**Ecuación 3.6: Constante Inercial Virtual**
```
H_virtual = (1/2) × J × ω² / S_base
```

Típicamente H_virtual = 2-4 s para inversores grid-forming.

### 3.4 Coordinación de Múltiples Generadores

#### 3.4.1 Control Droop para Reparto de Carga

**Ecuación 3.7: Característica Droop P-f**
```
f = f₀ - m_p × (P - P₀)
```

**Ecuación 3.8: Característica Droop Q-V**
```
V = V₀ - m_q × (Q - Q₀)
```

Donde:
- m_p: Pendiente droop frecuencia [Hz/MW]
- m_q: Pendiente droop voltaje [pu/MVAr]

Valores típicos: m_p = 1%, m_q = 4%

---

## 4. ALMACENAMIENTO DE ENERGÍA Y SERVICIOS DE RED

### 4.1 BESS en Puntas de Línea

#### 4.1.1 Dimensionamiento Básico

**Ecuación 4.1: Energía Requerida**
```
E_BESS = P_carga × t_autonomía / (η_BESS × DoD)
```

Donde:
- η_BESS: Eficiencia roundtrip (~90%)
- DoD: Depth of Discharge (~80%)

**Ejemplo Los Menucos**: P=1.5 MW, t=1.33 h
```
E_BESS = 1.5 × 1.33 / (0.9 × 0.8) = 2.77 MWh → 3 MWh
```

#### 4.1.2 Vida Útil y Degradación

**Ecuación 4.2: Ciclos Equivalentes**
```
N_eq = Σ(DoD_i^k × n_i)
```

Donde k ≈ 2 para baterías Li-ion.

Para 10,000 ciclos @ 80% DoD:
```
Vida_años = 10,000 / 365 = 27.4 años
```

### 4.2 Operación en Isla y Grid-Forming

#### 4.2.1 Requisitos Grid-Forming

**Tabla 4.1: Comparación Grid-Following vs Grid-Forming**

| Parámetro | Grid-Following | Grid-Forming |
|-----------|----------------|--------------|
| Referencia | Red externa | Interna |
| Inercia | No provee | Virtual |
| Black-start | No | Sí |
| V & f | Sigue | Impone |

#### 4.2.2 Control en Isla

**Ecuación 4.3: Balance de Potencia**
```
P_GD + P_BESS = P_carga + P_pérdidas
```

Control PI para regulación:
```
P_BESS = Kp × (f_ref - f) + Ki × ∫(f_ref - f)dt
```

### 4.3 Servicios Auxiliares - Valorización

#### 4.3.1 Regulación Primaria de Frecuencia

**Ecuación 4.4: Respuesta Primaria**
```
ΔP_reg = -R × Δf × P_nom
```

Donde R = 4% (droop) típico.

Valor típico: 1-2 USD/MW/h disponible

#### 4.3.2 Soporte de Voltaje Dinámico

**Ecuación 4.5: Capacidad Reactiva**
```
Q_max = √(S²_inv - P²_GD)
```

Para S_inv = 1.2 MVA, P_GD = 0 (noche):
```
Q_max = 1.2 MVAr (100% capacidad)
```

### 4.4 Q at Night - Innovación Clave

#### 4.4.1 Fundamento Técnico

Durante la noche (P_GD = 0), el inversor opera como STATCOM puro.

**Ecuación 4.6: Reducción de Pérdidas por Q**
```
ΔP_pérdidas = P_carga² × R × [(1/cos²φ₁) - (1/cos²φ₂)] / V²
```

**Ejemplo**: FP 0.985 → 0.999
```
Reducción = 1 - (0.999/0.985)² = 2.8%
```

#### 4.4.2 Control Q(V) Nocturno

**Ecuación 4.7: Ley de Control**
```
Q = Q₀ + Kq × (V_ref - V_medido)
```

Con Kq = -10 MVAr/pu típico.

---

## 5. MARCO REGULATORIO Y NORMATIVO

### 5.1 Normativa Argentina

#### 5.1.1 Procedimientos CAMMESA

- **Procedimiento Técnico N°1**: Calidad de servicio
- **Procedimiento Técnico N°8**: GD < 10 MW
- **Los Procedimientos**: Despacho y operación

#### 5.1.2 Resoluciones ENRE

- **Res. ENRE 555/01**: Calidad de producto técnico
- **Res. ENRE 552/16**: Generación distribuida
- **Res. SE 269/20**: Régimen GD usuarios

### 5.2 Estándares Internacionales

#### 5.2.1 IEEE Standards

- **IEEE 1547**: Interconexión de GD
- **IEEE 519**: Límites armónicos
- **IEEE 929**: Inversores fotovoltaicos

#### 5.2.2 IEC Standards

- **IEC 61727**: Sistemas FV - Conexión a red
- **IEC 62116**: Anti-islanding
- **IEC 61000**: Compatibilidad electromagnética

### 5.3 Criterios de Diseño

#### 5.3.1 Factores de Seguridad

**Tabla 5.1: Factores de Seguridad Típicos**

| Componente | Factor | Justificación |
|------------|--------|---------------|
| Inversores | 1.2 | Sobredimensión para Q |
| BESS energía | 1.25 | Degradación y reserva |
| Estructura | 1.5 | Vientos patagónicos |
| Cableado | 1.25 | Temperatura y pérdidas |

#### 5.3.2 Vida Útil de Diseño

- Sistema FV: 25 años
- Inversores: 15-20 años
- BESS: 10-15 años (o 10,000 ciclos)
- BOP: 25-30 años

---

## 6. REFERENCIAS

### 6.1 Referencias Técnicas

1. Kundur, P. (1994). "Power System Stability and Control". McGraw-Hill.
2. Jenkins, N. et al. (2000). "Distributed Generation". IET.
3. CIGRE WG C6.22 (2015). "Microgrids Evolution Roadmap".
4. IEEE Task Force (2018). "Stability Definitions and Characterization of Dynamic Behavior".

### 6.2 Normativa

5. CAMMESA (2020). "Los Procedimientos - Versión actualizada".
6. ENRE (2016). "Marco regulatorio generación distribuida".
7. IEEE (2018). "1547-2018 Standard for Interconnection".
8. IEC (2020). "61727 Photovoltaic systems characteristics".

### 6.3 Casos de Estudio

9. EDERSA (2024). "Análisis Línea Sur 33kV - Río Negro".
10. NREL (2019). "Grid Integration of Distributed Solar".
11. IRENA (2020). "Innovation landscape for renewable power".

---

## ANEXO A: PARÁMETROS TÍPICOS LÍNEAS 33kV

**Tabla A.1: Parámetros Líneas Aéreas 33kV**

| Conductor | R [Ω/km] | X [Ω/km] | B [μS/km] |
|-----------|----------|----------|-----------|
| 35 mm² Al | 0.850 | 0.420 | 2.7 |
| 50 mm² Al | 0.640 | 0.410 | 2.8 |
| 70 mm² Al | 0.460 | 0.400 | 2.9 |
| 95 mm² Al | 0.340 | 0.390 | 3.0 |
| 120 mm² Al | 0.270 | 0.380 | 3.1 |

## ANEXO B: COSTOS UNITARIOS REFERENCIALES

**Tabla B.1: CAPEX Típico Componentes (2024)**

| Componente | Costo Unitario | Unidad |
|------------|----------------|---------|
| Módulos FV | 0.25-0.35 | USD/Wp |
| Inversores string | 50-80 | USD/kVA |
| BESS Li-ion | 200-300 | USD/kWh |
| Estructura fija | 0.10-0.15 | USD/Wp |
| Instalación | 0.15-0.25 | USD/Wp |

---

*Fin del Documento KB.1 - Marco Teórico y Fundamentos*

*Próximo: KB.2 - Sistema de Análisis y Metodología*