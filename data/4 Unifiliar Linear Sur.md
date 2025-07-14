## 1. IDENTIFICACIÓN DEL SISTEMA

**Denominación:** Sistema Eléctrico Línea Sur  
**Operador:** EdERSA (Empresa de Energía Río Negro S.A.)  
**Sistema de Origen:** SISTEMA ALIPIBA (Alicurá-Pilcaniyeu-Bariloche)  
**Punto de Conexión:** ET Pilcaniyeu 132 kV  
**Tensión Nominal:** 33 kV  
**Configuración:** Radial  
**Longitud Total:** 270 km  
**Año Base Unifilar:** Datos actualizados a 2025  
**Plano:** LÍNEA SUR Sistema Eléctrico  

---

## 2. REFERENCIAS Y ABREVIATURAS

| Símbolo | Descripción |
|---------|-------------|
| ET | Estación Transformadora |
| RBC | Regulador Bajo Carga |
| AP | Alumbrado Público |
| Alim. | Alimentador |
| MVAR | Mega Volt-Ampere Reactivo |
| MW | Mega Watt |
| kV | Kilo Voltio |
| SMEC | Sistema de Medición de Energía y Calidad |

---

## 3. DATOS TÉCNICOS DE BARRAS Y CARGAS

### Tabla de Cargas según Unifilar

| Barra | Nombre | Nº | Un [kV] | P [MW] | Q [MVAR] |
|-------|--------|-----|---------|---------|----------|
| Comallo | COMALLO | 1780 | 13.2 | 0.30 | 0.10 |
| Onelli | ONELLI | 1782 | 13.2 | 0.10 | 0.04 |
| Jacobacci | JACOBACCI | 1785 | 13.2 | 1.45 | 0.60 |
| Maquinchao | MAQUINCHAO | 1788 | 13.2 | 0.50 | 0.10 |
| Aguada de Guerra | AGUADA DE GUERRA | 1790 | 33 | 0.05 | 0.01 |
| Los Menucos | LOS MENUCOS | 1792 | 13.2 | 1.40 | 0.20 |

**TOTAL SISTEMA: P = 3.80 MW | Q = 1.05 MVAR**

---

## 4. ESTACIONES TRANSFORMADORAS - DETALLES TÉCNICOS

### 4.1 ET PILCANIYEU (ET4PI)
- **Coordenadas:** -41.12°S, -70.90°W
- **Transformación:** 132/33 kV
- **Transformador Principal:**
  - Potencia: 25 MVA
  - Conexión: Yd
  - Regulación: RBC (Regulador Bajo Carga) ±10%, 17 pasos
  - Control: Automático/Manual
- **Función:** Punto de inyección al sistema Línea Sur
- **Conexión:** Desde Sistema ALIPIBA 132 kV
- **Salida 33 kV:** 
  - Conductor: 120 Al/Al hacia Comallo (70 km)
  - Protección: Interruptor y seccionadores

### 4.2 ET COMALLO
- **Coordenadas:** -41.06°S, -70.27°W
- **Distancia desde origen:** 70 km
- **Transformación:** 33/13.2 kV
- **Transformador:**
  - Potencia: 1.5 MVA
  - Conexión: Dy11
  - Regulación: Taps fijos ±2x2.5%
- **Barra Nº:** 1780
- **Carga:** 0.30 MW + 0.10 MVAR
- **Conductores:**
  - Llegada: 120 Al/Al desde Pilcaniyeu
  - Salida: 120 Al/Al hacia Onelli (50 km)
- **Alimentadores 13.2 kV:**
  - Seccionamiento Pilcaniyeu Pueblo
  - Alimentador local Comallo

### 4.3 ET ONELLI
- **Coordenadas:** -41.14°S, -69.89°W
- **Distancia desde origen:** 120 km (50 km desde Comallo)
- **Transformación:** 33/13.2 kV
- **Transformador:**
  - Potencia: 40 kVA (0.04 MVA)
  - Conexión: Dyn11
  - Tipo: Transformador pequeño dedicado
- **Barra Nº:** 1782
- **Carga:** 0.10 MW + 0.04 MVAR
- **Conductor llegada:** 120 Al/Al desde Comallo
- **Alimentador especial:** INVAP (instalación nuclear)
- **Nota:** Estación pequeña para cargas específicas

### 4.4 ET INGENIERO JACOBACCI (ET2IJ)
- **Coordenadas:** -41.329°S, -69.550°W
- **Distancia desde origen:** 150 km
- **Transformación:** 33/13.2 kV
- **Transformador:**
  - Potencia: 5 MVA
  - Conexión: Dy11
  - Regulación: Taps fijos ±2x2.5%
- **Regulador Serie:** 33/33 kV en entrada
  - Rango: ±10%
  - Pasos: 33
  - Control: Automático
- **Barra Nº:** 1785
- **Carga:** 1.45 MW + 0.60 MVAR
- **Alimentadores 13.2 kV:** 
  - Alim. NORTE: Pueblo Jacobacci Norte
  - Alim. SUR: Pueblo Jacobacci Sur
  - Ambos con reconectadores automáticos
- **Observación:** Mayor centro de carga del sistema

### 4.5 ET MAQUINCHAO
- **Coordenadas:** -41.25°S, -68.73°W
- **Distancia desde origen:** ~210 km
- **Transformación:** 33/13.2 kV
- **Transformador:**
  - Potencia: 0.5 MVA
  - Conexión: Dy11
  - Regulación: Taps fijos
- **Barra Nº:** 1788
- **Carga:** 0.50 MW + 0.10 MVAR
- **Conductores:**
  - Llegada: 70 Al/Al desde Jacobacci
  - Salida: 70 Al/Al hacia Aguada de Guerra
- **Alimentador 13.2 kV:** Pueblo Maquinchao

### 4.6 AGUADA DE GUERRA
- **Coordenadas:** -41.00°S, -68.40°W
- **Distancia desde origen:** ~240 km
- **Configuración:** Seccionamiento 33 kV (sin transformación)
- **Barra Nº:** 1790
- **Carga:** 0.05 MW + 0.01 MVAR

### 4.7 ET LOS MENUCOS (ET2LM)
- **Coordenadas:** -40.843°S, -68.086°W
- **Distancia desde origen:** 270 km
- **Transformación:** 33/13.2 kV
- **Transformadores de distribución:**
  - Múltiples unidades (capacidad total ~6 MVA)
  - Conexión: Dy11
- **Generación Distribuida (2024):**
  - 2 Motogeneradores Edison de 1.5 MW c/u
  - Total: 3 MW a gas natural
  - Conexión: 13.2 kV via transformadores 0.4/13.2 kV (2 MVA c/u)
- **Regulador Serie:** 13.2/13.2 kV
  - Rango: ±10%
  - Control: Automático
- **Barra Nº:** 1792
- **Carga:** 1.40 MW + 0.20 MVAR
- **Alimentadores:** Múltiples salidas de distribución
- **Función:** Fin de línea con soporte de GD

---

## 4.8 RESUMEN DE TRANSFORMADORES

### Tabla de Capacidades de Transformación

| Estación | Tipo | Potencia | Tensión | Conexión | Regulación |
|----------|------|----------|---------|----------|------------|
| Pilcaniyeu | Potencia | 25 MVA | 132/33 kV | Yd | RBC ±10% |
| Comallo | Distribución | 1.5 MVA | 33/13.2 kV | Dy11 | Taps fijos |
| Onelli | Dedicado | 40 kVA | 33/13.2 kV | Dyn11 | Taps fijos |
| Jacobacci | Distribución | 5 MVA | 33/13.2 kV | Dy11 | Taps + Reg Serie |
| Maquinchao | Distribución | 0.5 MVA | 33/13.2 kV | Dy11 | Taps fijos |
| Los Menucos | Distribución | ~6 MVA | 33/13.2 kV | Dy11 | Taps + Reg Serie |
| Los Menucos GD | Elevador | 2x2 MVA | 0.4/13.2 kV | Yd11 | Para generadores |

### Salidas de Transformadores por Estación

| Estación | Salidas 13.2 kV | Observaciones |
|----------|-----------------|---------------|
| Comallo | 2 alimentadores | Seccionamiento Pilcaniyeu Pueblo + Local |
| Onelli | 1 alimentador | Dedicado a INVAP |
| Jacobacci | 2 alimentadores | Norte y Sur con reconectadores |
| Maquinchao | 1 alimentador | Pueblo Maquinchao |
| Los Menucos | Múltiples | Distribución + conexión GD |

---

## 5. EQUIPAMIENTO DE REGULACIÓN Y CONTROL

### 5.1 Reguladores de Tensión Instalados

| Ubicación | Tipo | Tensión | Función |
|-----------|------|---------|---------|
| Pilcaniyeu | RBC | 132/33 kV | Control tensión en origen |
| Ing. Jacobacci | Serie | 33/33 kV | Compensación caída intermedia |
| Los Menucos | Serie | 13.2/13.2 kV | Regulación tensión fin de línea |

### 5.2 Elementos de Maniobra y Protección
- Seccionadores en cada ET
- Interruptores en 33 kV y 13.2 kV
- Sistema SMEC para medición

---

## 6. ANÁLISIS DE DISTANCIAS Y TRAMOS

| Tramo | Distancia | % del Total | Observaciones |
|-------|-----------|-------------|---------------|
| Pilcaniyeu → Comallo | 70 km | 26% | - |
| Comallo → Onelli | 50 km | 18% | - |
| Onelli → Jacobacci | 30 km | 11% | Tramo corto |
| Jacobacci → Maquinchao | ~60 km | 22% | Estimado |
| Maquinchao → Aguada | ~30 km | 11% | Estimado |
| Aguada → Los Menucos | ~30 km | 11% | Fin de línea |

---

## 7. PROBLEMÁTICA OPERATIVA IDENTIFICADA

### 7.1 Caídas de Tensión
- **Documentada:** ~20% en tramo Pilcaniyeu-Jacobacci (150 km)
- **Crítica:** Sin reguladores no es posible mantener tensión en banda

### 7.2 Limitaciones del Sistema
- Capacidad NULA para nuevas cargas en horario pico
- Sistema radial sin alternativas de alimentación
- Dependencia absoluta de 3 reguladores de tensión

### 7.3 Características del Consumo
- Factor de potencia promedio: 0.964 (3.80/√(3.80²+1.05²))
- Alta concentración: 75% de carga en 2 puntos (Jacobacci + Los Menucos)
- Impacto significativo del alumbrado público

---

## 8. PROYECTO EXISTENTE - GENERACIÓN TÉRMICA LOS MENUCOS

### 8.1 Descripción (según unifilar)
- **Tipo:** 2 Motogeneradores a gas compacto
- **Modelo referencia:** Cat®XQ1475G
- **Potencia:** 1500 KW/1800 KVA cada uno
- **Potencia total:** 3.0 MW / 3.6 MVA
- **Combustible:** Gas natural

### 8.2 Conexión al Sistema
- **Transformadores:** 2 x 13.8/0.4 kV, 2000 KVA, Yd11
- **Tensión conexión:** 13.2 kV (barra ET Los Menucos)
- **Maniobra:** 2 reconectadores 13.2 kV
- **Seccionadores:** 2 x tripolar 13.2 kV - 200 A
- **Medición:** Bloque SMEC por unidad

### 8.3 Infraestructura Asociada
- Planta de gas (tanques y sistema de distribución)
- Obras civiles para grupos generadores
- Sistema de control y protecciones

### 8.4 Estado del Proyecto
- Ingeniería conceptual desarrollada
- Objetivo: Control tensión y reserva fría
- Ubicación: ET Los Menucos (fin de línea)

---

## 9. IMPACTO TÉCNICO DE GD SOLAR EN EL SISTEMA

### 9.1 Mejora de Perfiles de Tensión
- **Situación actual:** Caída 20% requiere 3 reguladores
- **Con GD Solar:** Caídas <10% con inyección distribuida
- **Reducción dependencia:** Menor stress en reguladores existentes

### 9.2 Análisis por Punto de Inyección

| Punto GD | MW Solar | Impacto Esperado |
|----------|----------|------------------|
| Jacobacci | 2-3 MWp | Estabiliza tensión zona central, reduce 8-10% caída |
| Los Menucos | 2-3 MWp | Compensa fin de línea, elimina sobrecarga regulador |
| Maquinchao | 1-2 MWp | Soporte intermedio, mejora factor potencia |
| Onelli | 1 MWp | Reduce caída tramo inicial largo |

### 9.4 Recurso Solar Línea Sur
- **Radiación Global Horizontal:** 1,650-1,750 kWh/m²/año
- **Temperatura media:** 10-12°C (favorable para FV)
- **Días despejados:** >200 días/año
- **Polvo/viento:** Factor de ensuciamiento considerable
- **Ventaja térmica:** Bajas temperaturas mejoran eficiencia FV

---

## 10. DATOS COMPLEMENTARIOS DEL SISTEMA

### 9.1 Población Abastecida
- **Total:** ~14,770 habitantes
- **Mayor centro urbano:** Ing. Jacobacci (6,261 hab.)
- **Densidad:** 55 hab/km de línea

### 9.2 Condiciones Ambientales
- **Clima:** Árido frío patagónico
- **Altitud media:** 850-900 msnm
- **Vientos:** Predominantes del oeste
- **Temperatura:** Extremas (-25°C a +35°C)

### 9.3 Infraestructura Asociada
- Paralelo a Ruta Nacional 23
- Cruce con línea férrea (ex-Tren Patagónico)
- Accesos de ripio a las ET rurales

---

## 10. ANÁLISIS DEL ESTADO ACTUAL

### 10.1 Diagnóstico Técnico
- **Caída de tensión documentada:** 20% (Pilcaniyeu-Jacobacci)
- **Dependencia crítica:** 3 reguladores para mantener tensión
- **Capacidad disponible:** NULA en horario pico
- **Configuración:** Radial sin alternativas
- **Antigüedad:** Sistema >30 años

### 10.2 Cálculos Derivados

#### Factor de Potencia por ET:
| ET | P [MW] | Q [MVAR] | S [MVA] | FP |
|----|--------|----------|---------|-----|
| Comallo | 0.30 | 0.10 | 0.316 | 0.949 |
| Onelli | 0.10 | 0.04 | 0.108 | 0.928 |
| Jacobacci | 1.45 | 0.60 | 1.569 | 0.924 |
| Maquinchao | 0.50 | 0.10 | 0.510 | 0.980 |
| Aguada | 0.05 | 0.01 | 0.051 | 0.980 |
| Los Menucos | 1.40 | 0.20 | 1.414 | 0.990 |
| **TOTAL** | **3.80** | **1.05** | **3.943** | **0.964** |

#### Distribución de Carga:
- Jacobacci + Los Menucos: 2.85 MW (75% del total)
- Resto del sistema: 0.95 MW (25% del total)
- Carga promedio por ET: 0.63 MW
- Desviación estándar: 0.59 MW (alta dispersión)

### 10.3 Limitaciones Identificadas
1. Sistema operando al límite técnico
2. Sin capacidad de crecimiento
3. Vulnerabilidad por topología radial
4. Alta concentración de carga en 2 puntos
5. Grandes distancias entre cargas

---

*Documento técnico de estado actual - Sistema Eléctrico Línea Sur*  
*Fuente: Unifilar EdERSA + Análisis de coordenadas GPS*  
*Actualizado: Julio 2025*  
*Nota: Este documento consolida información fáctica del sistema para análisis posterior*