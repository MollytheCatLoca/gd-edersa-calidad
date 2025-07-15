# ESPECIFICACIONES TÉCNICAS DE TRANSFORMADORES
## Sistema Eléctrico Línea Sur

### 1. RESUMEN EJECUTIVO

El sistema Línea Sur cuenta con transformadores de potencia y distribución en cada estación, más transformadores de generación en Los Menucos. Debido a la falta de información específica de placa, se han estimado los parámetros basándose en:
- Cargas servidas en cada estación
- Prácticas estándar de la industria
- Niveles de tensión involucrados
- Información parcial del unifilar

---

### 2. TRANSFORMADORES DE POTENCIA

#### 2.1 ET PILCANIYEU - Transformador 132/33 kV

**Identificación:**
- Código: T_PI
- Ubicación: ET Pilcaniyeu
- Función: Interconexión con Sistema ALIPIBA

**Parámetros Estimados:**
| Parámetro | Valor | Unidad | Observación |
|-----------|--------|--------|-------------|
| Potencia Nominal | 15-20 | MVA | Estimado según demanda total sistema |
| Tensión Primaria | 132 | kV | Nominal |
| Tensión Secundaria | 33 | kV | Nominal |
| Impedancia de CC | 10-12 | % | Típico para este nivel |
| Pérdidas en Cobre | 80-100 | kW | @ potencia nominal |
| Pérdidas en Hierro | 15-20 | kW | En vacío |
| Corriente de Vacío | 0.5-1.0 | % | De corriente nominal |
| Grupo de Conexión | YNyn0 | - | Típico para interconexión |

**Regulación:**
- Tipo: Regulador Bajo Carga (RBC/OLTC)
- Rango: ±10% (±8 pasos de 1.25%)
- Total pasos: 17 (posición central + 8 arriba + 8 abajo)
- Control: Automático por tensión secundaria

**Capacidades de Sobrecarga:**
| Duración | Sobrecarga | Condición |
|----------|------------|-----------|
| Continua | 100% | Normal |
| 2 horas | 120% | Emergencia |
| 30 min | 140% | Emergencia extrema |

---

### 3. TRANSFORMADORES DE DISTRIBUCIÓN

#### 3.1 Especificaciones Generales 33/13.2 kV

**Características Comunes:**
- Tensión Primaria: 33 kV
- Tensión Secundaria: 13.2 kV
- Grupo de Conexión: Dyn11 (típico distribución)
- Regulación: Conmutador sin carga ±2x2.5%
- Refrigeración: ONAN (natural)

#### 3.2 Dimensionamiento por Estación

| Estación | Código | S nominal (MVA) | Justificación | Factor Uso |
|----------|--------|-----------------|---------------|-------------|
| Comallo | T_CO | 2.5-3.0 | Carga 0.316 MVA | 10-13% |
| Onelli | T_ON | 1.0-1.5 | Carga 0.108 MVA | 7-11% |
| Jacobacci | T_JA | 5.0-7.5 | Carga 1.569 MVA | 21-31% |
| Maquinchao | T_MA | 2.5-3.0 | Carga 0.510 MVA | 17-20% |
| Los Menucos | T_LM | 5.0-7.5 | Carga 1.414 MVA | 19-28% |

#### 3.3 Parámetros Eléctricos Típicos

**Para transformadores 1-3 MVA:**
| Parámetro | Valor | Unidad |
|-----------|--------|--------|
| Impedancia CC | 6.0-6.5 | % |
| Pérdidas Cu | 15-25 | kW |
| Pérdidas Fe | 2-4 | kW |
| Corriente vacío | 1.5-2.0 | % |

**Para transformadores 5-7.5 MVA:**
| Parámetro | Valor | Unidad |
|-----------|--------|--------|
| Impedancia CC | 6.5-7.0 | % |
| Pérdidas Cu | 30-45 | kW |
| Pérdidas Fe | 5-8 | kW |
| Corriente vacío | 1.0-1.5 | % |

---

### 4. TRANSFORMADORES DE GENERACIÓN - LOS MENUCOS

#### 4.1 Transformadores Elevadores Generadores

**Identificación:**
- Cantidad: 2 unidades
- Códigos: T_GEN1, T_GEN2
- Función: Conexión generadores térmicos a red

**Especificaciones (según unifilar):**
| Parámetro | Valor | Unidad | Estado |
|-----------|--------|--------|--------|
| Potencia Nominal | 2000 | kVA | Confirmado |
| Tensión Primaria | 13.8 | kV | Confirmado |
| Tensión Secundaria | 0.4 | kV | Confirmado |
| Impedancia CC | 6 | % | Confirmado |
| Grupo Conexión | Yd11 | - | Confirmado |
| Refrigeración | ONAN | - | Estándar |

**Consideraciones Operativas:**
- Diseñados para generadores de 1800 kVA
- Factor de sobrecarga: 110% por 2 horas
- Protecciones: Diferencial, sobrecorriente, temperatura

---

### 5. REGULADORES DE TENSIÓN

#### 5.1 Regulador Serie ET Jacobacci

**Especificaciones:**
| Parámetro | Valor | Unidad |
|-----------|--------|--------|
| Tipo | Serie | - |
| Tensión | 33/33 | kV |
| Potencia | >2 | MVA |
| Regulación | ±10 | % |
| Pasos | 33 | - |
| Paso unitario | 0.625 | % |
| Control | Automático | - |

#### 5.2 Regulador Serie ET Los Menucos

**Especificaciones:**
| Parámetro | Valor | Unidad |
|-----------|--------|--------|
| Tipo | Serie | - |
| Tensión | 13.2/13.2 | kV |
| Potencia | >2 | MVA |
| Regulación | ±10 | % |
| Pasos | 33 | - |
| Paso unitario | 0.625 | % |
| Control | Automático | - |

---

### 6. CÁLCULOS DE IMPEDANCIA EN EL SISTEMA

#### 6.1 Impedancias en Por Unidad (base 100 MVA)

**Transformador 132/33 kV (20 MVA, 11%):**
```
Zpu = 0.11 × (100/20) = 0.55 pu
Rpu ≈ 0.055 pu (asumiendo X/R = 10)
Xpu ≈ 0.547 pu
```

**Transformadores 33/13.2 kV (5 MVA, 6.5%):**
```
Zpu = 0.065 × (100/5) = 1.30 pu
Rpu ≈ 0.13 pu (asumiendo X/R = 10)
Xpu ≈ 1.293 pu
```

#### 6.2 Caídas de Tensión en Transformadores

**A carga nominal y FP 0.95:**
| Transformador | ΔV (%) | Observación |
|---------------|---------|-------------|
| 132/33 kV | 2.2-2.6 | Aceptable |
| 33/13.2 kV (5 MVA) | 1.3-1.5 | Aceptable |
| 33/13.2 kV (2.5 MVA) | 2.6-3.0 | Límite |

---

### 7. MANTENIMIENTO Y VIDA ÚTIL

#### 7.1 Plan de Mantenimiento Típico

**Mantenimiento Predictivo:**
- Análisis de aceite: Anual
- Termografía: Semestral
- Análisis de gases disueltos: Anual
- Medición de aislamiento: Bianual

**Mantenimiento Preventivo:**
- Inspección visual: Mensual
- Limpieza bushings: Trimestral
- Verificación protecciones: Anual
- Prueba cambiador taps: Anual

#### 7.2 Vida Útil Esperada

| Componente | Vida Útil (años) | Factor Crítico |
|------------|------------------|----------------|
| Transformador | 30-40 | Temperatura |
| Cambiador taps | 20-25 | Operaciones |
| Bushings | 25-30 | Contaminación |
| Aceite | 15-20 | Oxidación |

---

### 8. CONSIDERACIONES PARA INTEGRACIÓN DE GD

#### 8.1 Capacidad de Cortocircuito

**Estimación niveles de falla:**
- En 33 kV Pilcaniyeu: ~500-800 MVA
- En 13.2 kV Jacobacci: ~30-50 MVA
- En 13.2 kV Los Menucos: ~20-30 MVA

#### 8.2 Impacto de GD en Transformadores

**Flujos bidireccionales:**
- Transformadores diseñados para flujo unidireccional
- GD puede causar flujo reverso
- Verificar protecciones para operación bidireccional

**Regulación de tensión:**
- GD puede interferir con control de taps
- Necesario coordinar control de tensión
- Posible reajuste de parámetros de control

#### 8.3 Límites de Penetración GD

| Estación | Trafo MVA | GD Máx Recom. (MW) | Criterio |
|----------|-----------|---------------------|----------|
| Jacobacci | 5-7.5 | 3-4 | 60% S nominal |
| Maquinchao | 2.5-3 | 1.5-2 | 60% S nominal |
| Los Menucos | 5-7.5 | 3-4 | 60% S nominal |

---

### 9. RECOMENDACIONES

#### 9.1 Información Faltante Crítica

1. **Solicitar a EdERSA:**
   - Datos de placa de todos los transformadores
   - Resultados últimas pruebas de rutina
   - Histórico de fallas y mantenimientos
   - Ajustes actuales de protecciones

2. **Realizar mediciones:**
   - Impedancias reales de transformadores
   - Pérdidas en vacío y carga
   - Respuesta en frecuencia (SFRA)

#### 9.2 Estudios Recomendados

1. **Estudio de cortocircuito** actualizado con GD
2. **Coordinación de protecciones** con flujos bidireccionales
3. **Análisis de armónicos** con inversores FV
4. **Estudio de estabilidad transitoria** con GD

#### 9.3 Prioridades de Reemplazo

Basado en cargas y criticidad:
1. Verificar capacidad real Jacobacci (31% uso estimado)
2. Evaluar estado Los Menucos (28% uso + generación)
3. Considerar upgrade Maquinchao si se instala GD

---

### 10. CONCLUSIONES

1. **Capacidad instalada** aparentemente adecuada pero sin confirmación
2. **Información de placa** necesaria para análisis precisos
3. **Regulación de tensión** es el problema principal, no capacidad
4. **Transformadores pueden acomodar GD** con estudios previos
5. **Vida útil restante** desconocida sin datos de mantenimiento

---

*Documento Técnico - Especificaciones de Transformadores*  
*Sistema Línea Sur - EdERSA*  
*Fecha: Julio 2025*  
*Nota: Valores estimados pendientes de confirmación con datos de placa*