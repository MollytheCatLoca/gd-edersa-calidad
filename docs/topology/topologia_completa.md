# TOPOLOGÍA COMPLETA - SISTEMA ELÉCTRICO LÍNEA SUR

## 1. INFORMACIÓN GENERAL DEL SISTEMA

### 1.1 Identificación
- **Denominación:** Sistema Eléctrico Línea Sur  
- **Operador:** EdERSA (Empresa de Energía Río Negro S.A.)  
- **Sistema de Origen:** SISTEMA ALIPIBA (Alicurá-Pilcaniyeu-Bariloche)  
- **Punto de Conexión:** ET Pilcaniyeu 132 kV  
- **Configuración:** Radial  
- **Longitud Total:** 270 km  
- **Tensiones Nominales:** 132/33/13.2 kV

### 1.2 Resumen de Cargas
- **Carga Total:** 3.80 MW + j1.05 MVAr
- **Potencia Aparente:** 3.943 MVA
- **Factor de Potencia Global:** 0.964

---

## 2. TOPOLOGÍA DE LA RED - NODOS Y ESTACIONES

### 2.1 Tabla de Estaciones Transformadoras

| ID | Estación | Coordenadas | Dist. Origen (km) | Tensión (kV) | Barra N° | P (MW) | Q (MVAr) | S (MVA) | FP |
|----|----------|-------------|-------------------|--------------|----------|--------|----------|---------|-----|
| ET1 | Pilcaniyeu | -41.12°S, -70.90°W | 0 | 132/33 | - | - | - | - | - |
| ET2 | Comallo | -41.06°S, -70.27°W | 70 | 33/13.2 | 1780 | 0.30 | 0.10 | 0.316 | 0.949 |
| ET3 | Onelli | -41.14°S, -69.89°W | 120 | 33/13.2 | 1782 | 0.10 | 0.04 | 0.108 | 0.928 |
| ET4 | Ing. Jacobacci | -41.329°S, -69.550°W | 150 | 33/13.2 | 1785 | 1.45 | 0.60 | 1.569 | 0.924 |
| ET5 | Maquinchao | -41.25°S, -68.73°W | 210 | 33/13.2 | 1788 | 0.50 | 0.10 | 0.510 | 0.980 |
| ET6 | Aguada de Guerra | -41.00°S, -68.40°W | 240 | 33 | 1790 | 0.05 | 0.01 | 0.051 | 0.980 |
| ET7 | Los Menucos | -40.843°S, -68.086°W | 270 | 33/13.2 | 1792 | 1.40 | 0.20 | 1.414 | 0.990 |

### 2.2 Características de los Nodos

#### ET Pilcaniyeu (ET4PI)
- **Función:** Punto de inyección al sistema desde 132 kV
- **Equipamiento:** RBC (Regulador Bajo Carga) 132/33 kV
- **Medición:** SMEC instalado
- **Alimentadores:** Línea Sur 33 kV

#### ET Comallo
- **Población abastecida:** ~1,041 habitantes
- **Función:** Distribución local
- **Alimentadores:** Pueblo Comallo

#### ET Onelli
- **Función:** Distribución local
- **Observación:** Abastece INVAP y Pilcaniyeu Pueblo
- **Carga menor del sistema**

#### ET Ingeniero Jacobacci (ET2IJ)
- **Población abastecida:** ~6,261 habitantes
- **Función:** Mayor centro de carga de la línea
- **Equipamiento:** Regulador serie 33/33 kV
- **Alimentadores:** Norte y Sur
- **Criticidad:** ALTA

#### ET Maquinchao
- **Población abastecida:** ~2,334 habitantes
- **Función:** Distribución local
- **Alimentadores:** Pueblo Maquinchao

#### Aguada de Guerra
- **Función:** Seccionamiento 33 kV
- **Tipo:** Punto de conexión sin transformación
- **Carga mínima**

#### ET Los Menucos (ET2LM)
- **Población abastecida:** ~5,187 habitantes
- **Función:** Fin de línea - Segunda mayor carga
- **Equipamiento:** 
  - Regulador serie 13.2/13.2 kV
  - 2 Motogeneradores 1.5 MW c/u (3 MW total)
- **Criticidad:** ALTA

---

## 3. LÍNEAS DE TRANSMISIÓN - PARÁMETROS

### 3.1 Tramos de Línea 33 kV

| Tramo | Desde | Hasta | Long. (km) | Conductor | R (Ω/km)* | X (Ω/km)* | B (μS/km)* | I máx (A)* |
|-------|-------|-------|------------|-----------|-----------|-----------|------------|------------|
| T1 | Pilcaniyeu | Comallo | 70 | 120 Al/Al | 0.245 | 0.410 | 2.75 | 270 |
| T2 | Comallo | Onelli | 50 | 120 Al/Al | 0.245 | 0.410 | 2.75 | 270 |
| T3 | Onelli | Jacobacci | 30 | 120 Al/Al** | 0.245 | 0.410 | 2.75 | 270 |
| T4 | Jacobacci | Maquinchao | 60 | 70 Al/Al | 0.420 | 0.425 | 2.65 | 190 |
| T5 | Maquinchao | Aguada | 30 | 70 Al/Al** | 0.420 | 0.425 | 2.65 | 190 |
| T6 | Aguada | Los Menucos | 30 | 70 Al/Al** | 0.420 | 0.425 | 2.65 | 190 |

*Valores típicos estimados para conductores ACSR de las secciones indicadas
**Tipo de conductor inferido por continuidad

### 3.2 Características de Conductores

#### Conductor 120 mm² Al/Al
- **Sección:** 120 mm²
- **Material:** Aluminio
- **Resistencia DC (20°C):** ~0.245 Ω/km
- **Reactancia (50 Hz):** ~0.410 Ω/km
- **Corriente máxima:** ~270 A
- **Uso:** Tramos Pilcaniyeu-Jacobacci (150 km)

#### Conductor 70 mm² Al/Al
- **Sección:** 70 mm²
- **Material:** Aluminio
- **Resistencia DC (20°C):** ~0.420 Ω/km
- **Reactancia (50 Hz):** ~0.425 Ω/km
- **Corriente máxima:** ~190 A
- **Uso:** Tramos Jacobacci-Los Menucos (120 km)

---

## 4. TRANSFORMADORES DE POTENCIA

### 4.1 Transformadores de Estación

| Estación | Relación | S nom (MVA)* | Vcc (%)* | Pérd. Cu (kW)* | Pérd. Fe (kW)* | Regulación | Conexión* |
|----------|----------|--------------|----------|----------------|----------------|------------|-----------|
| Pilcaniyeu | 132/33 kV | 15-20 | 10-12 | 80-100 | 15-20 | RBC ±10x1.25% | YNyn0 |
| Comallo | 33/13.2 kV | 2.5-5 | 6-7 | 20-30 | 3-5 | Fija | Dyn11 |
| Onelli | 33/13.2 kV | 1-2.5 | 6-7 | 15-20 | 2-3 | Fija | Dyn11 |
| Jacobacci | 33/13.2 kV | 5-7.5 | 6-7 | 30-40 | 5-7 | Fija | Dyn11 |
| Maquinchao | 33/13.2 kV | 2.5-5 | 6-7 | 20-30 | 3-5 | Fija | Dyn11 |
| Los Menucos | 33/13.2 kV | 5-7.5 | 6-7 | 30-40 | 5-7 | Fija | Dyn11 |

*Valores típicos estimados según cargas y niveles de tensión

### 4.2 Transformadores Generación Los Menucos

| Cantidad | Relación | S nom (kVA) | Vcc (%) | Grupo | Aplicación |
|----------|----------|-------------|---------|-------|------------|
| 2 | 13.8/0.4 kV | 2000 | 6 | Yd11 | Conexión generadores |

---

## 5. EQUIPAMIENTO DE REGULACIÓN Y COMPENSACIÓN

### 5.1 Reguladores de Tensión

| Ubicación | Tipo | Tensión | Rango | Pasos | Control | Estado |
|-----------|------|---------|-------|-------|---------|--------|
| Pilcaniyeu | RBC | 132/33 kV | ±10% | 17 (±8x1.25%) | Automático | Operativo |
| Jacobacci | Serie | 33/33 kV | ±10% | 33 (±16x0.625%) | Automático | Operativo |
| Los Menucos | Serie | 13.2/13.2 kV | ±10% | 33 (±16x0.625%) | Automático | Operativo |

### 5.2 Generación Distribuida Existente

#### Central Térmica Los Menucos
- **Tipo:** Motogeneradores a gas natural
- **Modelo:** Cat® XQ1475G o similar
- **Configuración:** 2 x 1500 kW / 1800 kVA
- **Potencia Total:** 3.0 MW / 3.6 MVA
- **Factor de Potencia:** 0.8 - 1.0 (ajustable)
- **Tensión Generación:** 400 V
- **Conexión a Red:** 13.2 kV vía transformadores elevadores
- **Control:** Modo tensión y/o potencia
- **Estado:** Operativo

---

## 6. ELEMENTOS DE MANIOBRA Y PROTECCIÓN

### 6.1 Interruptores y Seccionadores

| Estación | Elemento | Tensión | Corriente Nominal | Cantidad |
|----------|----------|---------|-------------------|----------|
| Todas | Interruptor | 33 kV | 630-1250 A | 1-2 por ET |
| Todas | Seccionador | 33 kV | 630 A | 2-3 por ET |
| Todas | Interruptor | 13.2 kV | 630 A | 1-2 por alim. |
| Los Menucos | Reconectador | 13.2 kV | 630 A | 2 (generación) |

### 6.2 Sistema de Medición

- **SMEC:** Sistema de Medición de Energía y Calidad en todas las ET
- **Variables medidas:** V, I, P, Q, FP, THD, energía
- **Registro:** Cada 15 minutos
- **Almacenamiento:** Local y remoto

---

## 7. ANÁLISIS DE IMPEDANCIAS DEL SISTEMA

### 7.1 Impedancias Serie Totales por Tramo

| Tramo | R total (Ω) | X total (Ω) | Z total (Ω) | Ángulo (°) |
|-------|-------------|-------------|--------------|------------|
| Pilcaniyeu-Comallo | 17.15 | 28.70 | 33.43 | 59.1 |
| Comallo-Onelli | 12.25 | 20.50 | 23.88 | 59.1 |
| Onelli-Jacobacci | 7.35 | 12.30 | 14.33 | 59.1 |
| Jacobacci-Maquinchao | 25.20 | 25.50 | 35.85 | 45.3 |
| Maquinchao-Aguada | 12.60 | 12.75 | 17.93 | 45.3 |
| Aguada-Los Menucos | 12.60 | 12.75 | 17.93 | 45.3 |

### 7.2 Impedancia Acumulada desde Origen

| Hasta | R acum (Ω) | X acum (Ω) | Z acum (Ω) | Caída est. (%)* |
|-------|-------------|-------------|-------------|-----------------|
| Comallo | 17.15 | 28.70 | 33.43 | 8-10 |
| Onelli | 29.40 | 49.20 | 57.31 | 12-15 |
| Jacobacci | 36.75 | 61.50 | 71.64 | 18-22 |
| Maquinchao | 61.95 | 87.00 | 106.78 | 25-30 |
| Aguada | 74.55 | 99.75 | 124.52 | 28-33 |
| Los Menucos | 87.15 | 112.50 | 142.35 | 32-38 |

*Para carga nominal del sistema (3.8 MW + 1.05 MVAr)

---

## 8. LIMITACIONES Y RESTRICCIONES OPERATIVAS

### 8.1 Restricciones de Tensión
- **Rango operativo normal:** 0.95 - 1.05 pu
- **Rango operativo actual:** 0.59 - 1.00 pu (VIOLACIÓN SEVERA)
- **Caída máxima documentada:** 41% (mediciones reales)

### 8.2 Restricciones de Capacidad
- **Capacidad térmica línea 120 Al/Al:** ~16 MVA @ 33 kV
- **Capacidad térmica línea 70 Al/Al:** ~11 MVA @ 33 kV
- **Carga actual máxima:** ~4 MVA
- **Margen disponible horario pico:** NULO

### 8.3 Restricciones de Regulación
- **Dependencia crítica:** 3 reguladores para mantener tensión
- **Sin reguladores:** Sistema colapsa por baja tensión
- **Límite práctico actual:** 3.8 MW de demanda total

---

## 9. PARÁMETROS PARA MODELADO

### 9.1 Datos Base del Sistema
```
Sbase = 100 MVA
Vbase_HV = 132 kV
Vbase_MV = 33 kV  
Vbase_LV = 13.2 kV
Frecuencia = 50 Hz
```

### 9.2 Impedancias en Por Unidad (p.u.)

| Elemento | R (p.u.) | X (p.u.) | B (p.u.) |
|----------|----------|----------|----------|
| Línea 120 Al/Al | 0.0225/km | 0.0377/km | 0.00299/km |
| Línea 70 Al/Al | 0.0386/km | 0.0391/km | 0.00288/km |
| Trafo 132/33 kV | 0.005 | 0.10-0.12 | - |
| Trafo 33/13.2 kV | 0.01 | 0.06-0.07 | - |

---

## 10. OBSERVACIONES Y NOTAS TÉCNICAS

### 10.1 Información Faltante Crítica
1. **Potencias nominales exactas** de transformadores
2. **Impedancias medidas** de líneas (valores actuales son típicos)
3. **Niveles de cortocircuito** en barras
4. **Ajustes de protecciones** actuales
5. **Curvas de carga** detalladas por estación

### 10.2 Supuestos Realizados
1. Impedancias de líneas basadas en valores típicos para conductores ACSR
2. Potencias de transformadores estimadas según cargas servidas
3. Factores de pérdidas estándar para el nivel de tensión
4. Conexiones de transformadores típicas para distribución

### 10.3 Recomendaciones
1. Solicitar a EdERSA datos de placa de transformadores
2. Realizar mediciones de impedancia de líneas
3. Actualizar estudio de cortocircuito
4. Documentar ajustes actuales de protecciones

---

## 11. DATOS PARA SIMULACIÓN

### 11.1 Escenario Base (Sin GD)
- Demanda total: 3.80 MW + 1.05 MVAr
- Generación Pilcaniyeu: 5.66 MW + 1.05 MVAr (incluye pérdidas)
- Pérdidas estimadas: 1.86 MW (32.9% de generación)

### 11.2 Puntos Candidatos para GD
1. **Jacobacci:** 2-3 MW (máxima prioridad)
2. **Los Menucos:** 2-3 MW adicionales (ya tiene 3 MW)
3. **Maquinchao:** 1-2 MW (prioridad media)
4. **Onelli:** 0.5-1 MW (prioridad baja)

### 11.3 Criterios de Dimensionamiento GD
- Cubrir demanda local + 20-30% margen
- Mejorar tensión a >0.95 pu
- Reducir pérdidas totales a <10%
- Factor de capacidad solar: 20-25%

---

*Documento técnico de topología completa*  
*Sistema Eléctrico Línea Sur - EdERSA*  
*Actualizado: Julio 2025*  
*Versión: 1.0*