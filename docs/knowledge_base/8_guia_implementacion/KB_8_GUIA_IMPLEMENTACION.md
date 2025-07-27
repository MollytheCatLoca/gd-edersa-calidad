# KB.8 - GUÍA DE IMPLEMENTACIÓN
## Proceso Paso a Paso para Replicar Estudios de Generación Distribuida

---

## ÍNDICE

1. [INTRODUCCIÓN](#1-introducción)
2. [FASE 0: EVALUACIÓN PRELIMINAR](#2-fase-0-evaluación-preliminar)
3. [FASE 1: RECOPILACIÓN DE DATOS](#3-fase-1-recopilación-de-datos)
4. [FASE 2: ANÁLISIS TÉCNICO](#4-fase-2-análisis-técnico)
5. [FASE 3: EVALUACIÓN ECONÓMICA](#5-fase-3-evaluación-económica)
6. [FASE 4: DISEÑO DE SOLUCIÓN](#6-fase-4-diseño-de-solución)
7. [FASE 5: PLAN DE IMPLEMENTACIÓN](#7-fase-5-plan-de-implementación)
8. [HERRAMIENTAS Y RECURSOS](#8-herramientas-y-recursos)
9. [CRITERIOS DE DECISIÓN](#9-criterios-de-decisión)
10. [ADAPTACIÓN A DIFERENTES ESCENARIOS](#10-adaptación-a-diferentes-escenarios)

---

## 1. INTRODUCCIÓN

### 1.1 Propósito de la Guía
Esta guía proporciona un proceso estructurado y probado para evaluar, diseñar e implementar proyectos de generación distribuida, basado en experiencias exitosas con retornos superiores al 20%.

### 1.2 Usuarios Objetivo
- Planificadores de sistemas eléctricos
- Desarrolladores de proyectos renovables
- Consultores energéticos
- Tomadores de decisión en utilities
- Organismos de financiamiento

### 1.3 Resultados Esperados
Al seguir esta guía, podrá:
- Identificar oportunidades viables de GD
- Cuantificar beneficios integrales
- Diseñar soluciones óptimas
- Estructurar proyectos bancables
- Minimizar riesgos de implementación

---

## 2. FASE 0: EVALUACIÓN PRELIMINAR

### 2.1 Análisis de Viabilidad Rápida (Go/No-Go)

#### 2.1.1 Checklist de Pre-factibilidad
```
CRITERIO MÍNIMO                          VERIFICACIÓN    GO/NO-GO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Recurso solar >4.0 kWh/m²/día          [ ]            ______
□ Demanda local >0.3 MW                  [ ]            ______
□ Costo actual energía >80 USD/MWh       [ ]            ______
□ Problemas de calidad documentados      [ ]            ______
□ Espacio disponible >1 Ha/MW            [ ]            ______
□ Distancia a red <10 km                 [ ]            ______
□ Apoyo de stakeholders                  [ ]            ______
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mínimo 5/7 criterios cumplidos para continuar
```

#### 2.1.2 Cálculo Rápido de Viabilidad
```python
# Herramienta de screening inicial
def screening_inicial(datos_basicos):
    """
    Entrada requerida:
    - demanda_promedio_mw
    - costo_energia_actual_usd_mwh
    - recurso_solar_kwh_m2_dia
    - distancia_a_subestacion_km
    """
    
    # Dimensionamiento preliminar
    capacidad_fv = datos_basicos['demanda_promedio_mw'] * 1.5
    capex_estimado = capacidad_fv * 950_000  # USD/MW conservador
    
    # Beneficios aproximados
    factor_planta = datos_basicos['recurso_solar_kwh_m2_dia'] * 0.04
    generacion_anual = capacidad_fv * 8760 * factor_planta
    
    ahorro_anual = generacion_anual * datos_basicos['costo_energia_actual_usd_mwh'] * 0.7
    
    # Indicadores rápidos
    payback_simple = capex_estimado / ahorro_anual
    score_viabilidad = 10 / payback_simple
    
    return {
        'continuar': payback_simple < 8,
        'payback_estimado': round(payback_simple, 1),
        'score': round(score_viabilidad, 1),
        'proximos_pasos': 'Fase 1' if payback_simple < 8 else 'Revisar supuestos'
    }
```

### 2.2 Definición del Alcance

#### 2.2.1 Objetivos del Proyecto
```
OBJETIVO PRINCIPAL:
□ Reducir costos de energía
□ Mejorar calidad de servicio
□ Aumentar confiabilidad
□ Cumplir metas ambientales
□ Diferir inversiones en red

OBJETIVOS SECUNDARIOS:
□ Desarrollo socioeconómico local
□ Independencia energética
□ Innovación tecnológica
□ Posicionamiento estratégico
```

#### 2.2.2 Restricciones Identificadas
```
TIPO                    RESTRICCIÓN              ESTRATEGIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Técnicas               Capacidad de red          Limitar inyección
Financieras            Presupuesto limitado      Fases modulares
Regulatorias           Límites de GD             Optimizar tamaño
Ambientales            Áreas protegidas          Sitios alternativos
Sociales               Oposición local           Participación temprana
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 3. FASE 1: RECOPILACIÓN DE DATOS

### 3.1 Datos del Sistema Eléctrico

#### 3.1.1 Información Requerida
```
CATEGORÍA              DATOS NECESARIOS         FUENTE          PERÍODO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Demanda
├─ Perfil horario      kW cada 15 min          SCADA/Medidor   1 año
├─ Pico anual          kW máximo               Registros       3 años
├─ Factor de carga     %                       Calculado       -
└─ Crecimiento         % anual                 Histórico       5 años

Calidad
├─ Perfil voltaje      pu cada 15 min          Medidor PQ      1 año
├─ Interrupciones      SAIFI, SAIDI            Registros       3 años
├─ Armónicos           THD                     Medidor PQ      1 semana
└─ Factor potencia     cos φ                   SCADA           1 año

Red
├─ Topología           Unifilar                Operador        Actual
├─ Impedancias         R, X por tramo          Estudios        Actual
├─ Protecciones        Ajustes                 Operador        Actual
└─ Capacidad           MVA                     Placa/Estudios  Actual
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 3.1.2 Template de Recolección
```excel
PLANTILLA DE DATOS - SISTEMA ELÉCTRICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fecha    Hora    P(kW)    Q(kVAr)   V(pu)    I(A)    Eventos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
01/01    00:00   450      50        0.95     28.3    -
01/01    00:15   445      48        0.95     28.0    -
...      ...     ...      ...       ...      ...     ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mínimo 35,040 registros (1 año × 365 días × 96 intervalos/día)
```

### 3.2 Datos del Recurso Solar

#### 3.2.1 Fuentes de Información
```
FUENTE              RESOLUCIÓN    PRECISIÓN    COSTO       USO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Medición in-situ    1 min         ±2%          Alto        Definitivo
NASA POWER          Daily         ±10%         Gratis      Preliminar
PVGIS               Hourly        ±5%          Gratis      Diseño
Meteonorm           1 min         ±4%          Medio       Bankable
SolarGIS            30 min        ±3%          Alto        Bankable
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 3.2.2 Parámetros Críticos
```
PARÁMETRO                    UNIDAD      MÍNIMO REQUERIDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GHI (Global Horizontal)      kWh/m²/día  Promedio anual
DNI (Direct Normal)          kWh/m²/día  Si considera CPV
DHI (Diffuse Horizontal)     kWh/m²/día  Para bifacial
Temperatura ambiente         °C          Promedios mensuales
Velocidad viento            m/s         Para refrigeración
Albedo                      -           Para bifacial
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.3 Datos Económicos

#### 3.3.1 Costos Actuales
```
CONCEPTO                    UNIDAD      DATO REQUERIDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tarifa energía              USD/MWh     Promedio ponderado
Tarifa potencia             USD/kW-mes  Si aplica
Costo generación propia     USD/MWh     Diesel, gas, etc.
Penalidades calidad         USD/año     ENS, compensaciones
Costo de pérdidas           USD/MWh     Energía × % pérdidas
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 3.3.2 Proyecciones
```
VARIABLE                    FUENTE              VALOR TÍPICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Inflación energía           Regulador/Historia  3-5% anual
Crecimiento demanda         Planificación       2-4% anual
Tasa de descuento          Política empresa    10-15%
Tipo de cambio             Banco Central       Proyección
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.4 Validación de Datos

#### 3.4.1 Chequeos de Calidad
```python
def validar_datos_medicion(df_mediciones):
    """Validación automática de calidad de datos"""
    
    checks = {
        'completitud': len(df_mediciones) / (365*96) * 100,
        'outliers_potencia': detectar_outliers(df_mediciones['P_kW']),
        'outliers_voltaje': detectar_outliers(df_mediciones['V_pu']),
        'consistencia_pq': validar_factor_potencia(df_mediciones),
        'gaps_temporales': encontrar_gaps(df_mediciones.index)
    }
    
    reporte = generar_reporte_calidad(checks)
    return reporte

# Criterios de aceptación
CRITERIOS = {
    'completitud_minima': 95,  # %
    'outliers_maximos': 1,      # %
    'gaps_maximos': 24          # horas continuas
}
```

---

## 4. FASE 2: ANÁLISIS TÉCNICO

### 4.1 Caracterización del Sistema

#### 4.1.1 Análisis de Demanda
```
ANÁLISIS REQUERIDO          HERRAMIENTA         OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Perfil típico diario        Python/Excel        24h curve
Variación estacional        Análisis temporal   12 meses
Días típicos               Clustering          3-5 tipos
Proyección crecimiento     Regresión           % anual
Factor de coincidencia     Estadística         0.6-0.9
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 4.1.2 Análisis de Calidad
```
PARÁMETRO                  LÍMITE REGULATORIO   ACCIÓN SI EXCEDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voltaje                    0.95-1.05 pu         Compensación local
THD voltaje                <8%                  Filtros activos
Flicker                    Pst < 1              BESS/STATCOM
Desbalance                 <2%                  Balanceo cargas
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4.2 Simulación de Generación

#### 4.2.1 Modelado FV
```python
# Modelo simplificado de generación FV
def simular_generacion_fv(capacidad_mw, datos_solar, parametros):
    """
    Parámetros requeridos:
    - capacidad_mw: Potencia DC instalada
    - datos_solar: Serie temporal GHI
    - parametros: {
        'eficiencia_modulo': 0.21,
        'factor_temperatura': -0.0035,
        'perdidas_dc': 0.03,
        'perdidas_ac': 0.02,
        'disponibilidad': 0.98
      }
    """
    
    # Cálculo horario
    for hora in range(8760):
        # Irradiancia en plano inclinado
        GTI = calcular_GTI(datos_solar.GHI[hora], 
                          datos_solar.angulo_solar[hora])
        
        # Temperatura de célula
        T_cell = T_amb + (NOCT-20)/800 * GTI
        
        # Generación DC
        P_dc = capacidad_mw * (GTI/1000) * \
               (1 + parametros['factor_temperatura'] * (T_cell - 25))
        
        # Generación AC
        P_ac = P_dc * (1 - parametros['perdidas_dc']) * \
               eficiencia_inversor(P_dc/capacidad_mw) * \
               (1 - parametros['perdidas_ac'])
        
        generacion[hora] = P_ac * parametros['disponibilidad']
    
    return generacion
```

#### 4.2.2 Dimensionamiento Óptimo
```
MÉTODO                     OBJETIVO              HERRAMIENTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cobertura demanda          Autoconsumo máximo    Homer/PVsyst
Optimización económica     VPN máximo            Python/Excel
Restricción de red         Inyección limitada    DIgSILENT
Modular                    Crecimiento futuro    Análisis propio
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4.3 Análisis de Impacto en Red

#### 4.3.1 Flujo de Potencia
```
ESCENARIO                  ANÁLISIS             VERIFICAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sin GD (base)              Flujo AC             V, pérdidas
Con GD mínima              Flujo AC             ΔV, Δpérdidas
Con GD máxima              Flujo AC             V límites
Contingencia N-1           Flujo AC             Estabilidad
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 4.3.2 Cálculo de Beneficios Técnicos
```python
def calcular_beneficios_tecnicos(flujo_sin_gd, flujo_con_gd):
    """Cuantifica mejoras técnicas por GD"""
    
    beneficios = {
        # Reducción de pérdidas
        'reduccion_perdidas_mwh': 
            (flujo_sin_gd.perdidas - flujo_con_gd.perdidas) * 8760,
        
        # Mejora de voltaje
        'mejora_voltaje_promedio': 
            flujo_con_gd.v_promedio - flujo_sin_gd.v_promedio,
        
        # Liberación de capacidad
        'capacidad_liberada_mw': 
            flujo_sin_gd.cargabilidad_max - flujo_con_gd.cargabilidad_max,
        
        # ENS evitada (probabilística)
        'ens_evitada_mwh': 
            calcular_ens_probabilistica(mejora_confiabilidad)
    }
    
    return beneficios
```

---

## 5. FASE 3: EVALUACIÓN ECONÓMICA

### 5.1 Estructuración de Costos

#### 5.1.1 CAPEX Detallado
```
COMPONENTE              COSTO UNIT.     CANTIDAD    SUBTOTAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SISTEMA FV
Módulos bifaciales      0.25 $/W        X MW        = $___
Estructura tracker      180 $/kW        X MW        = $___
Inversores string       120 $/kW        X MW        = $___
Cableado DC            50 $/kW         X MW        = $___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subtotal equipos FV                                 = $___

SISTEMA BESS
Baterías LFP           150 $/kWh       X MWh       = $___
PCS                    100 $/kW        X MW        = $___
BMS + EMS              30 $/kWh        X MWh       = $___
Contenedor HVAC        20 $/kWh        X MWh       = $___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subtotal BESS                                       = $___

BALANCE OF SYSTEM
Transformador MT       80 $/kVA        X MVA       = $___
Celdas MT              50k $           X unid      = $___
SCADA                  100k $          1 sistema   = $___
Obra civil             5% equipos      -           = $___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subtotal BOS                                        = $___

SOFT COSTS
Ingeniería             5% total        -           = $___
Gestión proyecto       3% total        -           = $___
Permisos               2% total        -           = $___
Contingencia           10% total       -           = $___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAPEX TOTAL                                         = $___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 5.1.2 OPEX Proyectado
```
CONCEPTO                AÑO 1      ESCALACIÓN    AÑO 25
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
O&M preventivo          $__/MW     2%/año        $__/MW
O&M correctivo          $__/MW     2%/año        $__/MW
Seguros                 0.5% CAPEX 1%/año        $___
Administración          $__        3%/año        $___
Monitoreo remoto        $__/MW     2%/año        $__/MW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPEX TOTAL AÑO 1        $___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reemplazos programados:
- Inversores año 15: 60% costo inicial
- Baterías año 10 y 20: 70% y 50% costo inicial
```

### 5.2 Cuantificación de Beneficios

#### 5.2.1 Matriz de Beneficios
```python
def calcular_beneficios_integrales(proyecto):
    """Captura TODOS los beneficios del proyecto"""
    
    beneficios = {
        # DIRECTOS ENERGÉTICOS
        'sustitucion_energia_cara': 
            proyecto.generacion_kwh * (costo_actual - costo_fv),
        
        'reduccion_perdidas':
            perdidas_evitadas_kwh * costo_energia,
        
        # CALIDAD Y CONFIABILIDAD
        'ens_evitada':
            ens_reducida_kwh * costo_interrupcion,
        
        'mejora_calidad_voltaje':
            equipos_salvados * costo_reemplazo_anual,
        
        # DIFERIMIENTO INVERSIONES
        'diferimiento_red':
            vpn_inversion_diferida * tasa_descuento,
        
        # AMBIENTALES
        'creditos_carbono':
            co2_evitado_ton * precio_carbono,
        
        # SERVICIOS AUXILIARES
        'regulacion_voltaje':
            capacidad_mvar * tarifa_reactiva,
        
        'respuesta_demanda':
            mw_flexibles * tarifa_flexibilidad
    }
    
    return sum(beneficios.values())
```

#### 5.2.2 Escenarios de Beneficios
```
ESCENARIO          CONSERVADOR    BASE    OPTIMISTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Precio energía     -10%           =       +10%
Crecimiento dem.   1%/año         3%      5%
Captura beneficios 70%            85%     100%
Degradación FV     0.7%/año       0.5%    0.3%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIR esperada       15-18%         20-22%  24-28%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5.3 Modelo Financiero

#### 5.3.1 Estructura del Modelo
```
HOJA 1: INPUTS
├── Técnicos (capacidad, generación, degradación)
├── Económicos (precios, inflación, impuestos)
├── Financieros (estructura capital, tasas)
└── Escenarios (conservador, base, optimista)

HOJA 2: CÁLCULOS
├── Generación mensual/anual
├── Ingresos por categoría
├── Costos operativos
├── Depreciación y amortización
├── Cálculo de impuestos
└── Capital de trabajo

HOJA 3: FLUJO DE CAJA
├── EBITDA
├── Flujo operativo
├── Flujo de inversión
├── Flujo de financiamiento
├── Flujo de caja libre
└── Flujo del inversionista

HOJA 4: OUTPUTS
├── TIR proyecto y equity
├── VPN a diferentes tasas
├── Payback simple y descontado
├── LCOE
├── Ratios de cobertura
└── Análisis de sensibilidad

HOJA 5: DASHBOARD
├── Gráficos principales
├── Semáforo de viabilidad
├── Resumen ejecutivo
└── Comparación escenarios
```

#### 5.3.2 Métricas de Decisión
```
MÉTRICA              MÍNIMO      OBJETIVO    EXCELENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIR proyecto         12%         18%         >22%
TIR equity           15%         22%         >28%
VPN/Inversión        0.5         1.0         >1.5
Payback              <8 años     <6 años     <5 años
DSCR promedio        1.2         1.4         >1.6
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 6. FASE 4: DISEÑO DE SOLUCIÓN

### 6.1 Configuración Técnica Óptima

#### 6.1.1 Selección de Tecnología
```
CRITERIO              PESO    OPCIONES               DECISIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Módulos FV
├─ Eficiencia         30%     Mono/Poly/Bifacial     _______
├─ Costo              40%     Tier 1/2/3             _______
├─ Garantía           20%     25/30 años             _______
└─ Disponibilidad     10%     Local/Import           _______

Inversores
├─ Topología          25%     String/Central         _______
├─ Eficiencia         25%     Euro/CEC               _______
├─ Funciones grid     30%     Smart/Básico           _______
└─ Servicio local     20%     Si/No                  _______

BESS
├─ Química            30%     LFP/NMC                _______
├─ Vida útil          35%     Ciclos/Años            _______
├─ Densidad           15%     Wh/kg                  _______
└─ Seguridad          20%     Certificaciones        _______
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 6.1.2 Arquitectura del Sistema
```
CONFIGURACIÓN ÓPTIMA IDENTIFICADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sistema FV
├─ Módulos: Bifacial 540W, 25 años garantía
├─ Estructura: Tracker 1 eje N-S, +25% yield
├─ Inversores: String 100kW, 99% eficiencia
└─ DC/AC ratio: 1.3 para clipping óptimo

Sistema BESS
├─ Baterías: LFP 280Ah, 6000 ciclos
├─ PCS: Bidireccional 4 cuadrantes
├─ C-rate: 0.5C continuo, 1C pico
└─ DOD operativo: 90%

Integración
├─ SCADA: Protocolo IEC 61850
├─ Protecciones: 50/51, 27/59, 81, 25
├─ Calidad: Filtros activos THD <3%
└─ Comunicaciones: Fibra + 4G backup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 6.2 Ingeniería Básica

#### 6.2.1 Layout Preliminar
```
CRITERIOS DE DISEÑO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Separación filas: 2.5 × altura para tracker
Vialidad interna: 4m ancho mínimo
Área BESS: 200 m² por MWh
Sala control: 50 m² mínimo
Perímetro seguridad: 3m desde equipos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DISTRIBUCIÓN TÍPICA 1 MW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Norte ↑
┌─────────────────────────────────────────┐
│  Acceso                                 │ 10m
├─────────────────────────────────────────┤
│  ══════════════════════════════════     │
│  ══════════════════════════════════     │ 
│  ══════ MÓDULOS FV (0.7 MW) ══════     │ 120m
│  ══════════════════════════════════     │
│  ══════════════════════════════════     │
├─────────────────────────────────────────┤
│  Vial interno                           │ 5m
├─────────────────────────────────────────┤
│  ══════════════════════════════════     │
│  ══════ MÓDULOS FV (0.3 MW) ══════     │ 50m
│  ══════════════════════════════════     │
├─────────────────────────────────────────┤
│  □ BESS  □ Trafos  □ Sala              │ 20m
└─────────────────────────────────────────┘
         200m (2 hectáreas total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 6.2.2 Unifilar Simplificado
```
DIAGRAMA UNIFILAR CONCEPTUAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Red 33kV ────┬──── Medidor ────┬──── Cargas locales
             │                  │
             │                  │
         [52-1]             [52-2]
             │                  │
    ┌────────┴────────┐         │
    │  Trafo 33/0.8kV │         │
    │    2.5 MVA      │         │
    └────────┬────────┘         │
             │                  │
         [Barra 0.8kV]          │
             │                  │
    ┌────────┼────────┬─────────┤
    │        │        │         │
[Inversor][Inversor][BESS]  [Servicios]
    │        │        │         │
 [Strings][Strings][Baterías] [Aux]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 6.3 Estrategia de Control

#### 6.3.1 Modos de Operación
```
MODO              OBJETIVO           PRIORIDAD    CONTROL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Autoconsumo       Max local          1           P tracking
Peak shaving      Reducir picos      2           P límite
Arbitraje         Max ingresos       3           Precio
Soporte red       Estabilidad        4           V/f
Backup            Continuidad        5           Isla
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 6.3.2 Lógica de Control BESS
```python
def control_bess_optimizado(estado_actual, predicciones):
    """Lógica de control para maximizar beneficios"""
    
    # Inputs
    soc = estado_actual['soc']
    p_demanda = estado_actual['demanda_kw']
    p_fv = estado_actual['generacion_fv_kw']
    precio_hora = estado_actual['precio_energia']
    
    # Predicciones próximas 4 horas
    demanda_futura = predicciones['demanda_4h']
    fv_futura = predicciones['fv_4h']
    precios_futuros = predicciones['precios_4h']
    
    # Decisión de carga/descarga
    if p_fv > p_demanda and soc < 0.9:
        # Cargar con exceso FV
        p_bess = min(p_fv - p_demanda, p_bess_max_carga)
        
    elif precio_hora > percentil_80_precios and soc > 0.2:
        # Descarga en horas caras
        p_bess = -min(p_demanda, p_bess_max_descarga)
        
    elif p_demanda > p_max_contratada:
        # Peak shaving
        p_bess = -(p_demanda - p_max_contratada)
        
    else:
        # Standby
        p_bess = 0
    
    return p_bess
```

---

## 7. FASE 5: PLAN DE IMPLEMENTACIÓN

### 7.1 Cronograma Maestro

#### 7.1.1 Fases del Proyecto
```
FASE                        DURACIÓN    HITOS CLAVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. DESARROLLO (Mes 1-6)
├─ Ingeniería detalle       3 meses     Planos aprobados
├─ Permisos ambientales     4 meses     EIA aprobado
├─ Gestión predial          2 meses     Contratos firmados
└─ Licitación EPC           2 meses     Adjudicación

2. FINANCIAMIENTO (Mes 4-8)
├─ Estructuración           2 meses     Term sheet
├─ Due diligence           2 meses     DD completado
├─ Negociación             1 mes       Contratos
└─ Cierre financiero       1 mes       Desembolso

3. CONSTRUCCIÓN (Mes 9-14)
├─ Movilización            1 mes       Sitio activo
├─ Obra civil              2 meses     Bases listas
├─ Montaje mecánico        2 meses     Estructura OK
├─ Instalación eléctrica   2 meses     Cableado OK
└─ Integración BESS        1 mes       Sistema completo

4. PUESTA EN MARCHA (Mes 15-16)
├─ Pruebas individuales    2 semanas   Equipos OK
├─ Pruebas sistema         2 semanas   Integración OK
├─ Pruebas red             2 semanas   Grid code OK
└─ COD                     2 semanas   Operación comercial
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL: 16 meses desde inicio hasta COD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 7.1.2 Ruta Crítica
```
ACTIVIDADES CRÍTICAS (no pueden retrasarse):
1. Aprobación ambiental → 
2. Cierre financiero → 
3. Llegada equipos principales → 
4. Conexión a red → 
5. Pruebas de aceptación

BUFFER RECOMENDADO: +20% en duración total
```

### 7.2 Gestión de Riesgos

#### 7.2.1 Matriz de Riesgos del Proyecto
```
RIESGO                  PROB.   IMPACTO   MITIGACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Retraso permisos        Alta    Alto      Inicio temprano
Aumento costos          Media   Alto      Contingencia 10%
Clima adverso           Media   Medio     Buffer temporal
Calidad equipos         Baja    Alto      Inspección origen
Oposición social        Media   Alto      Socialización
Tipo de cambio          Alta    Medio     Cobertura forex
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 7.2.2 Plan de Contingencia
```python
contingencias = {
    'retraso_permisos': {
        'trigger': 'Retraso >30 días',
        'accion': 'Activar gestión alto nivel',
        'costo': '0',
        'responsable': 'Gerente Proyecto'
    },
    'sobrecosto_equipos': {
        'trigger': 'Aumento >10%',
        'accion': 'Renegociar o cambiar proveedor',
        'costo': 'Usar contingencia',
        'responsable': 'Procurement'
    },
    'falla_construccion': {
        'trigger': 'Accidente o defecto mayor',
        'accion': 'Activar seguros + plan B',
        'costo': 'Deducible seguro',
        'responsable': 'EPC + Aseguradora'
    }
}
```

### 7.3 Plan de Calidad

#### 7.3.1 Puntos de Control
```
ETAPA               VERIFICACIÓN           CRITERIO ACEPTACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Diseño              Revisión pares         Sin comentarios críticos
Equipos             Inspección fábrica     Certificados OK
Construcción        Supervisión diaria     Check-list 100%
Pre-commissioning   Pruebas protocolo      Valores en rango
Commissioning       Performance test       PR >80%, Disp >98%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 7.3.2 KPIs de Construcción
```
MÉTRICA                    OBJETIVO    MÍNIMO     FRECUENCIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Avance físico vs plan      100%        95%        Semanal
Seguridad (días sin acc)   365         30         Diario
Calidad (no conformidades) 0           <5         Semanal
Costo vs presupuesto       100%        <110%      Mensual
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 8. HERRAMIENTAS Y RECURSOS

### 8.1 Software Recomendado

#### 8.1.1 Análisis y Diseño
```
CATEGORÍA           SOFTWARE         LICENCIA    USO PRINCIPAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recurso solar       PVGIS            Gratis      Preliminar
                   PVsyst           Pago        Bankable
                   Helioscope       Pago        Diseño 3D

Análisis red        OpenDSS          Gratis      Académico
                   PowerFactory     Pago        Profesional
                   ETAP             Pago        Industrial

Financiero          Excel            Pago        Todos
                   Python           Gratis      Avanzado
                   Homer            Pago        Optimización

Gestión             MS Project       Pago        Cronograma
                   Primavera        Pago        Megaproyectos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 8.1.2 Plantillas Excel
```
PLANTILLA                          CONTENIDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1_Screening_Inicial.xlsx           Go/No-Go rápido
2_Analisis_Demanda.xlsx           Perfiles y proyección
3_Dimensionamiento_FV_BESS.xlsx   Optimización técnica
4_Modelo_Financiero_GD.xlsx       Flujo caja completo
5_Analisis_Sensibilidad.xlsx      Escenarios y riesgos
6_Dashboard_Proyecto.xlsx          Seguimiento integral
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Disponibles en: /recursos/plantillas/
```

### 8.2 Scripts Python

#### 8.2.1 Análisis de Datos
```python
# Script: analisis_demanda_solar.py
"""
Analiza datos de demanda y recurso solar
Genera dimensionamiento preliminar
"""

import pandas as pd
import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt

def cargar_y_validar_datos(archivo_demanda, archivo_solar):
    """Carga y valida calidad de datos"""
    # Implementación...
    pass

def analizar_perfiles(df_demanda, df_solar):
    """Genera perfiles típicos y correlaciones"""
    # Implementación...
    pass

def optimizar_capacidad(perfiles, restricciones):
    """Encuentra capacidad óptima FV+BESS"""
    # Implementación...
    pass

def generar_reporte(resultados):
    """Crea reporte PDF con gráficos"""
    # Implementación...
    pass

if __name__ == "__main__":
    # Flujo principal
    datos = cargar_y_validar_datos('demanda.csv', 'solar.csv')
    perfiles = analizar_perfiles(datos['demanda'], datos['solar'])
    optimo = optimizar_capacidad(perfiles, restricciones={})
    generar_reporte(optimo)
```

#### 8.2.2 Modelo Financiero Simplificado
```python
# Script: modelo_financiero_rapido.py
"""
Calcula métricas financieras principales
Genera análisis de sensibilidad
"""

class ProyectoGD:
    def __init__(self, capacidad_mw, capex_por_mw, 
                 factor_planta, precio_energia):
        self.capacidad = capacidad_mw
        self.capex = capacidad_mw * capex_por_mw
        self.cf = factor_planta
        self.precio = precio_energia
        
    def calcular_flujo_caja(self, años=25):
        """Genera flujo de caja proyecto"""
        flujos = []
        
        # Año 0 - Inversión
        flujos.append(-self.capex)
        
        # Años 1-25 - Operación
        for año in range(1, años+1):
            generacion = self.capacidad * 8760 * self.cf * \
                        (1 - 0.005)**(año-1)  # Degradación 0.5%
            
            ingresos = generacion * self.precio * \
                      (1.03)**(año-1)  # Inflación precio 3%
            
            opex = self.capex * 0.025 * (1.02)**(año-1)  # 2.5% CAPEX
            
            flujo_neto = ingresos - opex
            flujos.append(flujo_neto)
            
        return flujos
    
    def calcular_tir(self):
        """Calcula TIR del proyecto"""
        flujos = self.calcular_flujo_caja()
        return np.irr(flujos)
    
    def calcular_vpn(self, tasa_descuento=0.12):
        """Calcula VPN a tasa dada"""
        flujos = self.calcular_flujo_caja()
        return np.npv(tasa_descuento, flujos)
```

### 8.3 Checklist de Implementación

#### 8.3.1 Pre-construcción
```
DOCUMENTOS REQUERIDOS                    STATUS   FECHA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Ingeniería de detalle aprobada         [ ]      ___
□ Permisos ambientales                   [ ]      ___
□ Permisos de construcción               [ ]      ___
□ Acuerdos de servidumbre                [ ]      ___
□ Contrato EPC firmado                   [ ]      ___
□ Contrato O&M firmado                   [ ]      ___
□ Seguros contratados                    [ ]      ___
□ Financiamiento disponible              [ ]      ___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 8.3.2 Durante construcción
```
ACTIVIDAD SEMANAL                        S1  S2  S3  ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reunión de coordinación                  □   □   □
Reporte de avance                        □   □   □
Inspección de calidad                    □   □   □
Revisión de seguridad                    □   □   □
Control de costos                        □   □   □
Gestión de cambios                       □   □   □
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 9. CRITERIOS DE DECISIÓN

### 9.1 Árbol de Decisión Integral

```
                           INICIO PROYECTO GD
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              ¿Screening OK?                    │
                    │                           │
                   SÍ                          NO → Revisar
                    │                               alternativas
              Fase 1: Datos                         
                    │
              ¿Calidad >95%?
                    │
                   SÍ
                    │
              Fase 2: Análisis
                    │
         ┌──────────┴──────────┐
         │                     │
    ¿Beneficios               │
    técnicos OK?              │
         │                    │
        SÍ                   NO → Redimensionar
         │
    Fase 3: Económico
         │
    ┌────┴────┐
    │         │
TIR >15%     NO → Optimizar o
    │             rechazar
   SÍ
    │
Fase 4: Diseño
    │
Fase 5: Implementar
```

### 9.2 Matriz de Decisión Ponderada

```
CRITERIO                PESO    PUNTAJE(1-5)   PONDERADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TÉCNICOS (40%)
Recurso solar           10%     ___            ___
Demanda/Generación      10%     ___            ___
Calidad red actual      10%     ___            ___
Espacio disponible      10%     ___            ___

ECONÓMICOS (40%)
TIR proyecto            15%     ___            ___
Payback                 10%     ___            ___
Costo evitado           10%     ___            ___
Riesgo financiero       5%      ___            ___

SOCIO-AMBIENTALES (20%)
Aceptación social       10%     ___            ___
Impacto ambiental       5%      ___            ___
Desarrollo local        5%      ___            ___
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL                   100%                   ___/5.0

DECISIÓN: >3.5 Proceder | 3.0-3.5 Optimizar | <3.0 No viable
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 9.3 Semáforo de Viabilidad

```python
def semaforo_proyecto(metricas):
    """Genera semáforo de decisión GO/CAUTION/STOP"""
    
    # Definir umbrales
    umbrales = {
        'tir': {'verde': 18, 'amarillo': 15, 'rojo': 12},
        'payback': {'verde': 5, 'amarillo': 7, 'rojo': 10},
        'lcoe_vs_tarifa': {'verde': 0.8, 'amarillo': 0.95, 'rojo': 1.1},
        'dscr': {'verde': 1.4, 'amarillo': 1.25, 'rojo': 1.1}
    }
    
    # Evaluar cada métrica
    colores = {}
    for metrica, valor in metricas.items():
        if metrica in ['tir', 'dscr']:  # Más es mejor
            if valor >= umbrales[metrica]['verde']:
                colores[metrica] = 'VERDE'
            elif valor >= umbrales[metrica]['amarillo']:
                colores[metrica] = 'AMARILLO'
            else:
                colores[metrica] = 'ROJO'
        else:  # Menos es mejor
            if valor <= umbrales[metrica]['verde']:
                colores[metrica] = 'VERDE'
            elif valor <= umbrales[metrica]['amarillo']:
                colores[metrica] = 'AMARILLO'
            else:
                colores[metrica] = 'ROJO'
    
    # Decisión global
    if all(c == 'VERDE' for c in colores.values()):
        return 'GO - Proyecto altamente viable'
    elif any(c == 'ROJO' for c in colores.values()):
        return 'STOP - Revisar factibilidad'
    else:
        return 'CAUTION - Optimizar antes de proceder'
```

---

## 10. ADAPTACIÓN A DIFERENTES ESCENARIOS

### 10.1 Variaciones por Escala

#### 10.1.1 Micro GD (<100 kW)
```
ADAPTACIONES REQUERIDAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Simplificar estudios (no requiere flujo de carga)
• Conexión en BT, no MT
• Inversores residenciales
• Sin BESS o baterías pequeñas
• Tramitación simplificada
• Modelo net metering/billing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 10.1.2 Mini GD (100 kW - 1 MW)
```
CONSIDERACIONES ESPECIALES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Estudio de conexión básico
• Inversores string comerciales
• BESS opcional según caso
• Medición bidireccional
• Contrato de conexión estándar
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 10.1.3 GD Utility (>5 MW)
```
REQUISITOS ADICIONALES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Estudio de impacto completo
• Subestación dedicada
• SCADA obligatorio
• Grid code compliance total
• PPA o merchant
• Garantías de desempeño
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 10.2 Variaciones por Aplicación

#### 10.2.1 Industrial/Comercial
```
FOCO: Reducción de costos energéticos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dimensionamiento:   80-100% demanda base
BESS:              Peak shaving prioritario
Modelo negocio:    Autoconsumo + venta excedentes
Métricas clave:    Reducción factura, ROI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 10.2.2 Rural/Aislado
```
FOCO: Confiabilidad y calidad
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dimensionamiento:   120-150% demanda pico
BESS:              Obligatorio, 4-8h autonomía
Modelo negocio:    Sustitución diesel/red débil
Métricas clave:    Disponibilidad, LCOE vs diesel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 10.2.3 Residencial/Comunitario
```
FOCO: Independencia y sostenibilidad
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dimensionamiento:   Virtual net metering
BESS:              Compartido comunidad
Modelo negocio:    Cooperativa/agregación
Métricas clave:    % autoconsumo, payback
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 10.3 Lecciones por Geografía

#### 10.3.1 Zonas de Alta Irradiación (>5.5 kWh/m²/día)
```
OPTIMIZACIONES:
• Ratio DC/AC hasta 1.5
• Considerar CPV si DNI >2000
• Gestión térmica crítica
• Soiling importante
```

#### 10.3.2 Zonas Templadas (4-5 kWh/m²/día)
```
BALANCE ÓPTIMO:
• Bifacial con ganancia 10-15%
• Tracker E-O en latitudes altas
• BESS para arbitraje estacional
```

#### 10.3.3 Zonas Nubosas (<4 kWh/m²/día)
```
ADAPTACIONES:
• Sobredimensionar 20-30%
• Módulos mejor desempeño difusa
• Combinar con otras renovables
• Evaluar cuidadosamente viabilidad
```

---

## CONCLUSIONES

### Claves para el Éxito

1. **Evaluación integral**: Capturar TODOS los beneficios, no solo energía
2. **Datos de calidad**: Mínimo 1 año de mediciones confiables
3. **Dimensionamiento óptimo**: Ni sub ni sobredimensionar
4. **Gestión profesional**: Desde desarrollo hasta O&M
5. **Adaptación al contexto**: No hay solución única

### Errores Comunes a Evitar

1. Subestimar la complejidad de permisos
2. Ignorar la calidad de la red existente
3. No considerar crecimiento de demanda
4. Optimizar solo para TIR sin ver riesgos
5. Descuidar la aceptación social

### Siguientes Pasos Recomendados

1. Aplicar screening inicial a su proyecto
2. Si es viable, iniciar recopilación de datos
3. Usar las herramientas provistas para análisis
4. Validar resultados con expertos locales
5. Proceder con confianza basada en evidencia

---

**Guía desarrollada por**: Equipo de Implementación GD
**Basada en**: Proyectos exitosos 2020-2025
**Última actualización**: Diciembre 2024
**Versión**: 1.0
**Soporte**: contacto@energia-distribuida.com