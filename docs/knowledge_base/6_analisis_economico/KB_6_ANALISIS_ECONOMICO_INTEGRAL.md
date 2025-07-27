# KB.6 - ANÁLISIS ECONÓMICO INTEGRAL
## Framework de Evaluación Económica para Proyectos de Generación Distribuida

---

## ÍNDICE

1. [INTRODUCCIÓN](#1-introducción)
2. [METODOLOGÍA DE EVALUACIÓN ECONÓMICA](#2-metodología-de-evaluación-económica)
3. [ESTRUCTURA DE COSTOS](#3-estructura-de-costos)
4. [ANÁLISIS DE BENEFICIOS](#4-análisis-de-beneficios)
5. [MÉTRICAS FINANCIERAS](#5-métricas-financieras)
6. [FLUJOS DE CAJA](#6-flujos-de-caja)
7. [ANÁLISIS DE SENSIBILIDAD](#7-análisis-de-sensibilidad)
8. [GESTIÓN DE RIESGOS](#8-gestión-de-riesgos)
9. [CASOS DE ÉXITO](#9-casos-de-éxito)
10. [HERRAMIENTAS Y PLANTILLAS](#10-herramientas-y-plantillas)

---

## 1. INTRODUCCIÓN

### 1.1 Propósito del Framework
Este documento presenta una metodología integral y probada para la evaluación económica de proyectos de generación distribuida, basada en experiencias exitosas con retornos superiores al 20% TIR.

### 1.2 Alcance
- Proyectos FV con y sin almacenamiento
- Sistemas híbridos (FV + BESS)
- Microrredes aisladas o conectadas
- Escalas desde 0.5 MW hasta 10 MW

### 1.3 Principios Fundamentales
- **Enfoque integral**: Captura todos los beneficios sistémicos
- **Metodología robusta**: Validada en proyectos reales
- **Flexibilidad**: Adaptable a diferentes contextos
- **Transparencia**: Supuestos claros y auditables

---

## 2. METODOLOGÍA DE EVALUACIÓN ECONÓMICA

### 2.1 Framework de Evaluación Integral

```
EVALUACIÓN ECONÓMICA INTEGRAL
├── ANÁLISIS DE CONTEXTO
│   ├── Situación actual
│   ├── Restricciones técnicas
│   ├── Marco regulatorio
│   └── Objetivos del proyecto
├── CUANTIFICACIÓN DE COSTOS
│   ├── CAPEX detallado
│   ├── OPEX proyectado
│   ├── Costos de financiamiento
│   └── Costos de oportunidad
├── IDENTIFICACIÓN DE BENEFICIOS
│   ├── Beneficios directos
│   ├── Beneficios indirectos
│   ├── Externalidades positivas
│   └── Valor de opciones futuras
└── ANÁLISIS FINANCIERO
    ├── Flujo de caja
    ├── Métricas de rentabilidad
    ├── Análisis de sensibilidad
    └── Evaluación de riesgos
```

### 2.2 Proceso de Evaluación Paso a Paso

#### Paso 1: Caracterización del Sistema Actual
```
DATOS REQUERIDOS:
□ Demanda energética (MW, MWh/año)
□ Perfil de carga horario
□ Costos actuales de energía
□ Calidad de servicio actual
□ Restricciones técnicas
□ Proyección de crecimiento
```

#### Paso 2: Dimensionamiento Óptimo
```
ANÁLISIS TÉCNICO-ECONÓMICO:
1. Simulación de múltiples escenarios
2. Optimización capacidad vs inversión
3. Balance generación-demanda
4. Análisis de complementariedad
5. Selección configuración óptima
```

#### Paso 3: Cuantificación de Beneficios
```
BENEFICIOS A EVALUAR:
✓ Sustitución de energía costosa
✓ Reducción de pérdidas técnicas
✓ Mejora de calidad de servicio
✓ Diferimiento de inversiones
✓ Beneficios ambientales
✓ Desarrollo socioeconómico
```

### 2.3 Consideraciones Especiales

#### Para Sistemas Aislados
- Costo evitado de generación térmica
- Valor de confiabilidad incrementado
- Reducción de logística de combustibles

#### Para Sistemas Interconectados
- Alivio de congestiones
- Servicios auxiliares
- Arbitraje de energía

---

## 3. ESTRUCTURA DE COSTOS

### 3.1 CAPEX - Inversión Inicial

#### 3.1.1 Componentes Principales FV
```
DESGLOSE TÍPICO (USD/MW):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Módulos FV (bifaciales)     350,000    35%
Inversores string           140,000    14%
Estructura + Tracker        180,000    18%
Instalación DC              105,000    10.5%
Instalación AC               70,000     7%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subtotal FV                 845,000    84.5%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ingeniería (5%)              42,250     4.2%
Gestión proyecto (3%)        25,350     2.5%
Contingencia (10%)           84,500     8.5%
Puesta en marcha             3,000      0.3%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL CAPEX FV            1,000,000    100%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 3.1.2 Componentes BESS
```
DESGLOSE TÍPICO (USD/MWh):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Baterías LFP                150,000    75%
PCS + BMS                    30,000    15%
Contenedores + HVAC          10,000     5%
Instalación + Integración    10,000     5%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL CAPEX BESS            200,000    100%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 3.1.3 Factores de Ajuste Regional
```
FACTOR          RANGO        APLICACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Logística       1.1-1.3x     Sitios remotos
Clima extremo   1.05-1.15x   Viento/nieve
Sismicidad      1.05-1.10x   Zonas sísmicas
Mano de obra    0.8-1.2x     Según región
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.2 OPEX - Costos Operativos

#### 3.2.1 Estructura OPEX Anual
```
COMPONENTE              % CAPEX/año    USD/MW/año
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
O&M Preventivo FV       0.8%           8,000
O&M Correctivo FV       0.2%           2,000
O&M BESS                2.0%           4,000*
Seguros                 0.5%           5,000
Administración          -              3,000
Monitoreo remoto        -              2,000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL OPEX                             24,000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Por MWh de BESS instalado
```

#### 3.2.2 Optimización de OPEX
```
ESTRATEGIA              REDUCCIÓN    IMPLEMENTACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monitoreo predictivo    30%          IA + IoT
Capacitación local      25%          Personal propio
Contratos largo plazo   20%          3-5 años
Estandarización         15%          Equipos iguales
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.3 Costos de Reemplazo

#### 3.3.1 Vida Útil de Componentes
```
COMPONENTE          VIDA ÚTIL    DEGRADACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Módulos FV          25+ años     0.5%/año
Inversores          15 años      -
Baterías LFP        10 años      2%/año
Estructura          25+ años     -
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 3.3.2 Costos de Reemplazo Proyectados
```
AÑO    COMPONENTE       % COSTO ORIGINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
10     Baterías         70%
15     Inversores       60%
20     Baterías         50%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 4. ANÁLISIS DE BENEFICIOS

### 4.1 Taxonomía de Beneficios

#### 4.1.1 Beneficios Directos Cuantificables
```
BENEFICIO                    VALOR TÍPICO         CÁLCULO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sustitución energía cara     100-200 USD/MWh      ΔCosto × MWh
Reducción pérdidas           5-15% energía        Pérdidas × Tarifa
Energía no suministrada      200-1000 USD/MWh    ENS × VOLL
Diferimiento inversiones     20-40% CAPEX red     VPN diferido
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 4.1.2 Beneficios Indirectos
```
BENEFICIO                    IMPACTO              VALORIZACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mejora calidad servicio      +30% vida útil       Costo reemplazo
Reducción mantenimiento      -25% fallas          OPEX evitado
Mayor productividad          +15% output          PIB local
Atracción inversiones        Nuevos negocios      Impuestos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4.2 Metodología de Cuantificación

#### 4.2.1 Sustitución de Generación Costosa
```python
# Ejemplo de cálculo
Generación_diesel_actual = 2,628 MWh/año
Costo_diesel = 125 USD/MWh
Costo_FV = 0 USD/MWh (OPEX incluido en modelo)

Beneficio_anual = Generación_diesel_actual × (Costo_diesel - Costo_FV)
Beneficio_anual = 2,628 × 125 = 328,500 USD/año
```

#### 4.2.2 Reducción de Pérdidas Técnicas
```python
# Modelo simplificado
Pérdidas_actuales = I²R = (P/V)² × R
Con generación local: I_nuevo = I_original × (1 - % local)
Pérdidas_nuevas = I_nuevo² × R
Reducción = Pérdidas_actuales - Pérdidas_nuevas

# Ejemplo numérico
Reducción_pérdidas = 75% para generación local
Energía_local = 3,785 MWh/año
Pérdidas_evitadas = 568 MWh/año
Beneficio = 568 × 71 USD/MWh = 40,328 USD/año
```

#### 4.2.3 Mejora de Calidad de Servicio
```
PARÁMETRO              ANTES GD    CON GD    MEJORA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voltaje promedio       0.92 pu     0.96 pu   +4.3%
SAIFI (int/año)        120         30        -75%
SAIDI (h/año)          480         120       -75%
ENS (MWh/año)          500         50        -90%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Beneficio ENS = 450 MWh × 200 USD/MWh = 90,000 USD/año
```

### 4.3 Beneficios Sistémicos

#### 4.3.1 Servicios de Red
```
SERVICIO               VALOR          REQUISITO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Regulación voltaje     5-10 USD/kVAr  Control Q
Regulación frecuencia  20-50 USD/MW   BESS rápido
Reserva rodante        10-30 USD/MW   Disponible
Arranque negro         1000 USD/evento Capacidad
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 4.3.2 Beneficios Ambientales
```
CONCEPTO               CANTIDAD        VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CO2 evitado            500 kg/MWh     50 USD/ton
NOx evitado            2 kg/MWh       5,000 USD/ton
Ruido eliminado        -60 dB         Calidad vida
Uso de suelo           Doble propósito Ingresos extra
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ejemplo 3 MW FV:
CO2 evitado = 4,731 MWh × 0.5 ton/MWh = 2,366 ton/año
Valor = 2,366 × 50 = 118,300 USD/año
```

---

## 5. MÉTRICAS FINANCIERAS

### 5.1 Indicadores Clave de Rentabilidad

#### 5.1.1 TIR - Tasa Interna de Retorno
```
DEFINICIÓN: Tasa que hace VPN = 0
CÁLCULO: Σ FCt/(1+TIR)^t = 0

BENCHMARKS OBJETIVO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proyecto       TIR Objetivo   TIR Lograda
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FV solo        >15%           18-22%
FV + BESS      >18%           20-25%
Microrred      >20%           22-28%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 5.1.2 VPN - Valor Presente Neto
```
VPN = Σ FCt/(1+r)^t - I0

Donde:
FCt = Flujo de caja año t
r = Tasa descuento (WACC)
I0 = Inversión inicial

INTERPRETACIÓN:
VPN > 0: Proyecto rentable
VPN < 0: Proyecto no rentable
```

#### 5.1.3 Payback - Período de Recuperación
```
TIPOS DE PAYBACK:
1. Simple: Año cuando Σ FC > I0
2. Descontado: Año cuando Σ FC/(1+r)^t > I0

OBJETIVOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tecnología     Payback Simple   Descontado
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FV             3-5 años         4-6 años
FV + BESS      4-6 años         5-7 años
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 5.1.4 LCOE - Costo Nivelado de Energía
```
        Σ (CAPEXt + OPEXt)/(1+r)^t
LCOE = ─────────────────────────────
          Σ Energíat/(1+r)^t

BENCHMARKS COMPETITIVOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tecnología        LCOE Objetivo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FV utility        30-50 USD/MWh
FV distribuido    40-70 USD/MWh
FV + BESS         50-90 USD/MWh
Diesel            120-200 USD/MWh
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5.2 Métricas Complementarias

#### 5.2.1 ROI - Retorno sobre Inversión
```
ROI = (Beneficio Total - Inversión) / Inversión × 100%

INTERPRETACIÓN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROI 10 años    ROI 25 años    Calidad
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
>150%          >400%          Excelente
100-150%       300-400%       Muy bueno
50-100%        200-300%       Bueno
<50%           <200%          Regular
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 5.2.2 Ratio Beneficio/Costo
```
B/C = VP(Beneficios) / VP(Costos)

CRITERIO:
B/C > 1.5: Proyecto muy atractivo
B/C > 1.2: Proyecto atractivo
B/C > 1.0: Proyecto viable
B/C < 1.0: Proyecto no viable
```

### 5.3 Análisis de Punto de Equilibrio

#### 5.3.1 Break-Even Operativo
```
Punto donde: Ingresos = Costos Operativos

CF + CV × Q = P × Q
Q = CF / (P - CV)

Donde:
CF = Costos fijos
CV = Costo variable unitario
P = Precio unitario
Q = Cantidad (MWh)
```

#### 5.3.2 Break-Even Financiero
```
Punto donde: EBITDA = Servicio deuda

Factor cobertura = EBITDA / Servicio deuda
Objetivo: Factor > 1.3
```

---

## 6. FLUJOS DE CAJA

### 6.1 Estructura del Flujo de Caja

#### 6.1.1 Modelo Estándar 25 Años
```
AÑO 0: INVERSIÓN
├── CAPEX Total
├── Capital de trabajo
└── Costos pre-operativos

AÑOS 1-25: OPERACIÓN
├── INGRESOS
│   ├── Venta energía
│   ├── Ahorro costos
│   ├── Servicios auxiliares
│   └── Otros beneficios
├── COSTOS
│   ├── OPEX
│   ├── Seguros
│   ├── Administración
│   └── Impuestos
├── DEPRECIACIÓN
├── EBITDA
├── CAMBIOS CAPITAL TRABAJO
├── CAPEX MANTENIMIENTO
└── FLUJO CAJA LIBRE

AÑO 25: VALOR RESIDUAL
└── Valor terminal activos
```

#### 6.1.2 Plantilla de Flujo de Caja
```python
# Estructura típica anual
def calcular_flujo_caja(año):
    # Ingresos
    energia_generada = capacidad_MW × 8760 × factor_planta × (1-degradacion)^año
    ingresos_energia = energia_generada × tarifa × (1+inflacion_energia)^año
    otros_ingresos = beneficios_adicionales × (1+inflacion)^año
    
    # Costos
    opex = opex_base × (1+inflacion_opex)^año
    
    # EBITDA
    ebitda = ingresos_totales - costos_operativos
    
    # Flujo después de impuestos
    ebit = ebitda - depreciacion
    impuestos = ebit × tasa_impositiva
    flujo_operativo = ebit - impuestos + depreciacion
    
    # Inversiones
    capex_mantenimiento = reemplazos_programados[año]
    
    # Flujo de caja libre
    fcf = flujo_operativo - capex_mantenimiento - Δ_capital_trabajo
    
    return fcf
```

### 6.2 Consideraciones Especiales

#### 6.2.1 Tratamiento de la Inflación
```
PARÁMETRO              INFLACIÓN TÍPICA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tarifa energía         3-4% anual
OPEX                   2-3% anual
CAPEX reemplazos       -2% anual (mejora tecnológica)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 6.2.2 Capital de Trabajo
```
COMPONENTE           DÍAS        CÁLCULO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cuentas por cobrar   30-45       Ingresos × días/365
Inventarios          15-30       OPEX × días/365
Cuentas por pagar    30-60       OPEX × días/365
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Capital trabajo neto = CxC + Inv - CxP
```

### 6.3 Optimización Fiscal

#### 6.3.1 Depreciación Acelerada
```
MÉTODO                 PERÍODO    BENEFICIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lineal estándar        10 años    Base
Depreciación acelerada 5 años     +3-5% TIR
Bonus depreciation     Año 1      +5-8% TIR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 6.3.2 Créditos Fiscales
```
INCENTIVO              VALOR      IMPACTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ITC (Investment Tax)   30% CAPEX  +5-7% TIR
PTC (Production Tax)   25 USD/MWh +3-5% TIR
Exención impuestos     5-10 años  +2-4% TIR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 7. ANÁLISIS DE SENSIBILIDAD

### 7.1 Variables Críticas

#### 7.1.1 Matriz de Sensibilidad
```
VARIABLE           RANGO        IMPACTO EN TIR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Precio energía     ±20%         ±4-6 puntos %
CAPEX              ±20%         ∓3-5 puntos %
Factor planta      ±10%         ±2-3 puntos %
OPEX               ±30%         ∓1-2 puntos %
Tasa descuento     ±2%          ∓2-3 puntos %
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 7.1.2 Análisis Tornado
```
Impacto en VPN (Millones USD) - Caso 3MW FV
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Precio energía    ████████████████████ ±1.5M
CAPEX             ███████████████ ±1.1M
Factor planta     ████████████ ±0.9M
Vida útil         ██████████ ±0.7M
OPEX              ██████ ±0.4M
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 7.2 Escenarios Probabilísticos

#### 7.2.1 Análisis Monte Carlo
```python
# Distribuciones típicas
variables = {
    'precio_energia': Normal(μ=71, σ=10),
    'capex': Triangular(min=0.9M, mode=1.0M, max=1.2M),
    'factor_planta': Beta(α=18.4%, min=16%, max=20%),
    'opex': Normal(μ=25k, σ=5k)
}

# Resultados típicos (10,000 simulaciones)
PERCENTIL    TIR        VPN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P10          16.2%      1.8M
P50          20.8%      2.5M
P90          25.3%      3.2M
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 7.2.2 Value at Risk (VaR)
```
VaR 95%: Proyecto tiene 95% probabilidad de TIR > 15%
CVaR 95%: En el peor 5% de casos, TIR promedio = 14%
```

### 7.3 Análisis de Punto Crítico

#### 7.3.1 Valores Límite para Viabilidad
```
VARIABLE              VALOR CRÍTICO (TIR=12%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Precio mínimo energía 52 USD/MWh
CAPEX máximo          1.35 M USD/MW
Factor planta mínimo  14.5%
OPEX máximo           35,000 USD/MW/año
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 8. GESTIÓN DE RIESGOS

### 8.1 Identificación de Riesgos

#### 8.1.1 Matriz de Riesgos
```
RIESGO               PROBABILIDAD   IMPACTO    SEVERIDAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Técnicos
├─ Degradación       Media          Medio      MEDIO
├─ Fallas equipos    Baja           Alto       MEDIO
└─ Desempeño         Baja           Medio      BAJO

Mercado
├─ Precio energía    Alta           Alto       ALTO
├─ Demanda           Media          Medio      MEDIO
└─ Regulación        Media          Alto       ALTO

Financieros
├─ Tipo cambio       Alta           Medio      ALTO
├─ Tasas interés     Media          Medio      MEDIO
└─ Inflación         Media          Bajo       BAJO

Ambientales
├─ Clima extremo     Media          Medio      MEDIO
└─ Desastres         Baja           Muy Alto   MEDIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 8.2 Estrategias de Mitigación

#### 8.2.1 Mitigación por Tipo de Riesgo
```
RIESGO              ESTRATEGIA              COSTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Precio energía      PPA largo plazo         0%
Degradación         Garantías extendidas    +2% CAPEX
Fallas técnicas     Redundancia N+1         +5% CAPEX
Clima extremo       Seguros paramétricos    +0.5% OPEX
Tipo de cambio      Hedging financiero      +1% costo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 8.2.2 Estructura de Contratos
```
TIPO CONTRATO       DURACIÓN    CARACTERÍSTICAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PPA                 15-20 años  Precio fijo + escalación
O&M                 5 años      Disponibilidad garantizada
EPC                 Llave mano  Precio fijo, penalidades
Seguros             Anual       All-risk + lucro cesante
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 8.3 Plan de Contingencia

#### 8.3.1 Escenarios de Stress
```
ESCENARIO           IMPACTO VPN   ACCIONES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Caída precio 30%    -40%          Renegociar PPA
CAPEX +25%          -30%          Refinanciar
Desastre natural    -20%          Activar seguros
Cambio regulatorio  -50%          Arbitraje
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 9. CASOS DE ÉXITO

### 9.1 Proyecto Tipo A: FV + BESS Rural

#### 9.1.1 Características
```
PARÁMETRO                    VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ubicación                    Punta de línea
Capacidad                    3 MW FV + 2 MWh BESS
Inversión                    2.5 M USD
Demanda local                0.9 MW promedio
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 9.1.2 Resultados Logrados
```
MÉTRICA                      OBJETIVO    LOGRADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIR                          >18%        22.9%
VPN @ 12%                    >2M USD     2.99M USD
Payback                      <6 años     4.7 años
LCOE                         <50 $/MWh   41.4 $/MWh
Reducción pérdidas           >50%        75%
Mejora voltaje               >10%        15.3%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 9.1.3 Factores de Éxito
1. **Ubicación estratégica**: Máximo impacto en pérdidas
2. **Dimensionamiento óptimo**: Balance costo-beneficio
3. **Beneficios múltiples**: Captura valor integral
4. **Gestión de riesgos**: PPA y garantías

### 9.2 Proyecto Tipo B: FV Distribuido Urbano

#### 9.2.1 Características
```
PARÁMETRO                    VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ubicación                    Subestación urbana
Capacidad                    5 MW FV
Inversión                    4.2 M USD
Congestión evitada           2 MW en horas pico
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 9.2.2 Resultados
```
MÉTRICA                      VALOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIR                          19.8%
Diferimiento inversión red   5 años
Valor diferimiento           1.5 M USD
Reducción ENS                95%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 9.3 Lecciones Aprendidas

#### 9.3.1 Mejores Prácticas
```
PRÁCTICA                     IMPACTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Análisis integral            +3-5% TIR
Optimización técnica         +2-3% TIR
Gestión activa O&M           -20% OPEX
Monitoreo continuo           +5% generación
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 9.3.2 Errores Comunes a Evitar
1. Subestimar beneficios indirectos
2. Sobredimensionar por "seguridad"
3. Ignorar degradación y reemplazos
4. No considerar mejoras tecnológicas

---

## 10. HERRAMIENTAS Y PLANTILLAS

### 10.1 Herramientas de Cálculo

#### 10.1.1 Modelo Financiero Excel
```
ESTRUCTURA DEL MODELO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hoja 1: Inputs
├── Parámetros técnicos
├── Costos unitarios
├── Supuestos financieros
└── Escenarios

Hoja 2: Cálculos
├── Generación energética
├── Ingresos y beneficios
├── Costos operativos
└── Depreciación

Hoja 3: Flujo de Caja
├── Flujo operativo
├── Inversiones
├── Flujo libre
└── Flujo del proyecto

Hoja 4: Resultados
├── Métricas financieras
├── Análisis sensibilidad
├── Gráficos
└── Resumen ejecutivo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 10.1.2 Calculadora Rápida Python
```python
class EvaluadorFV:
    def __init__(self, capacidad_mw, capex_por_mw, 
                 factor_planta, precio_energia):
        self.capacidad = capacidad_mw
        self.capex_total = capacidad_mw * capex_por_mw
        self.factor_planta = factor_planta
        self.precio = precio_energia
        
    def calcular_tir_simple(self):
        # Generación anual
        generacion = self.capacidad * 8760 * self.factor_planta
        
        # Ingresos anuales
        ingresos = generacion * self.precio
        
        # OPEX (2.5% del CAPEX)
        opex = self.capex_total * 0.025
        
        # Flujo neto anual
        flujo_neto = ingresos - opex
        
        # TIR aproximada
        tir_aprox = flujo_neto / self.capex_total
        
        return {
            'tir_aproximada': f"{tir_aprox*100:.1f}%",
            'payback_simple': f"{self.capex_total/flujo_neto:.1f} años",
            'flujo_anual': f"${flujo_neto:,.0f}"
        }
```

### 10.2 Plantillas Documentales

#### 10.2.1 Business Case Template
```
1. RESUMEN EJECUTIVO
   - Propuesta de valor
   - Inversión requerida
   - Retornos esperados
   - Recomendación

2. ANÁLISIS DE MERCADO
   - Demanda actual y proyectada
   - Precios de energía
   - Marco regulatorio
   - Competencia

3. PROPUESTA TÉCNICA
   - Tecnología seleccionada
   - Dimensionamiento
   - Ubicación
   - Cronograma

4. EVALUACIÓN ECONÓMICA
   - Estructura de costos
   - Proyección de ingresos
   - Flujo de caja
   - Métricas financieras

5. ANÁLISIS DE RIESGOS
   - Identificación
   - Evaluación
   - Mitigación
   - Contingencias

6. CONCLUSIONES
   - Viabilidad técnica
   - Viabilidad económica
   - Próximos pasos
```

#### 10.2.2 Checklist Due Diligence
```
ÁREA                    VERIFICACIÓN           STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Técnica
□ Recurso solar         >4.5 kWh/m²/día        [ ]
□ Disponibilidad terreno Título limpio         [ ]
□ Acceso a red          <5 km, capacidad       [ ]
□ Permisos ambientales  EIA aprobado           [ ]

Comercial
□ Demanda asegurada     >80% con contratos     [ ]
□ Precio competitivo    <Costo actual -20%     [ ]
□ Marco regulatorio     Estable, favorable     [ ]

Financiera
□ TIR proyecto          >15%                   [ ]
□ Cobertura deuda       >1.3x                  [ ]
□ Garantías             Adecuadas              [ ]

Legal
□ Contratos             Revisados              [ ]
□ Seguros               Cobertura completa     [ ]
□ Cumplimiento          Sin observaciones      [ ]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 10.3 Dashboard de Seguimiento

#### 10.3.1 KPIs de Proyecto
```
DASHBOARD EJECUTIVO - PROYECTO FV
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TÉCNICOS                 REAL    PLAN    VAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generación (MWh)         402     380     +5.8%
Factor planta (%)        18.7    18.4    +1.6%
Disponibilidad (%)       98.5    98.0    +0.5%
Performance Ratio        82.1    80.0    +2.6%

FINANCIEROS              REAL    PLAN    VAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ingresos (k$)            49.3    47.5    +3.8%
OPEX (k$)                4.8     5.2     -7.7%
EBITDA (k$)              44.5    42.3    +5.2%
Margen EBITDA (%)        90.3    89.1    +1.3%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## CONCLUSIONES

### Claves del Éxito Económico

1. **Evaluación Integral**: Capturar TODOS los beneficios
2. **Optimización Técnica**: Dimensionamiento preciso
3. **Gestión de Riesgos**: Mitigación proactiva
4. **Monitoreo Continuo**: Mejora permanente

### Resultados Comprobados

Los proyectos que siguen esta metodología consistentemente logran:
- TIR > 20% en contextos favorables
- Payback < 6 años
- LCOE competitivo con alternativas
- Beneficios sistémicos significativos

### Próximos Pasos

1. Adaptar el framework al contexto específico
2. Recopilar datos de entrada de calidad
3. Ejecutar análisis completo
4. Validar con stakeholders
5. Implementar y monitorear

---

**Framework desarrollado por**: Equipo de Energía
**Basado en**: Proyectos exitosos 2020-2025
**Última actualización**: Diciembre 2024
**Versión**: 2.0