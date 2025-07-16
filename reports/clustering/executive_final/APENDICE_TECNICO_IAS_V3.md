# APÉNDICE TÉCNICO - ANÁLISIS GD SOLAR EDERSA
## Metodología IAS 3.0 y Resultados Detallados

**Fecha de generación**: 16 de July de 2025

---

## 1. METODOLOGÍA IAS 3.0

### 1.1 Evolución del Índice de Aptitud Solar

El IAS 3.0 representa una evolución significativa respecto a las versiones anteriores:

- **IAS 1.0** (5 criterios): Enfoque tradicional en coincidencia solar-demanda
- **IAS 2.0** (6 criterios): Incorporación de Q at Night
- **IAS 3.0** (7 criterios): Adición de disponibilidad de terreno

### 1.2 Matriz de Pesos AHP Actualizada

| Criterio | Descripción | Peso |
|----------|-------------|------|
| C1 | Criticidad de red | 8.7% |
| C2 | Coincidencia solar-demanda | 20.1% |
| C3 | Vulnerabilidad eléctrica | 3.1% |
| C4 | Cargabilidad de activos | 5.6% |
| C5 | Riesgo de flujo reverso | 12.0% |
| C6 | Aptitud Q at Night | 30.1% |
| C7 | Disponibilidad de terreno | 20.4% |

### 1.3 Fórmula IAS 3.0

```
IAS_3.0 = 0.087×C1 + 0.201×C2 + 0.031×C3 + 0.056×C4 + 0.120×C5 + 0.301×C6 + 0.204×C7
```

## 2. RESULTADOS POR CLUSTER

### 2.1 Top 15 Clusters - Ranking IAS 3.0

| Rank | Cluster | IAS 3.0 | IAS Original | Δ Rank | Perfil | GD (MW) | Usuarios | C6 Score | C7 Score |
|------|---------|---------|--------------|--------|--------|---------|----------|----------|----------|
| 1 | 14 | 0.555 | 0.337 | +14 | Mixto | 0.9 | 635 | 5.7 | 6.6 |
| 2 | 9 | 0.550 | 0.353 | +11 | Mixto | 1.3 | 1,137 | 5.7 | 6.4 |
| 3 | 1 | 0.547 | 0.388 | +4 | Mixto | 1.6 | 1,920 | 5.7 | 6.3 |
| 4 | 8 | 0.517 | 0.365 | +5 | Mixto | 3.8 | 3,691 | 5.7 | 4.8 |
| 5 | 11 | 0.499 | 0.362 | +5 | Mixto | 5.6 | 4,106 | 5.7 | 3.9 |
| 6 | 2 | 0.496 | 0.354 | +6 | Mixto | 6.8 | 4,601 | 5.7 | 3.8 |
| 7 | 6 | 0.496 | 0.358 | +4 | Mixto | 6.8 | 3,623 | 5.7 | 3.8 |
| 8 | 12 | 0.493 | 0.345 | +6 | Mixto | 7.9 | 3,363 | 5.7 | 3.6 |
| 9 | 4 | 0.480 | 0.381 | -1 | Mixto | 12.7 | 7,162 | 5.7 | 3.0 |
| 10 | 0 | 0.454 | 0.417 | -4 | Mixto | 22.0 | 17,211 | 5.7 | 1.7 |
| 11 | 7 | 0.417 | 0.642 | -8 | Comercial | 1.8 | 6,400 | 2.9 | 4.0 |
| 12 | 5 | 0.392 | 0.636 | -8 | Comercial | 3.0 | 7,147 | 2.9 | 2.8 |
| 13 | 10 | 0.387 | 0.635 | -8 | Comercial | 4.1 | 8,540 | 2.9 | 2.6 |
| 14 | 13 | 0.376 | 0.645 | -12 | Comercial | 6.5 | 15,166 | 2.9 | 2.0 |
| 15 | 3 | 0.342 | 0.651 | -14 | Comercial | 35.7 | 73,774 | 2.9 | 0.4 |

## 3. ANÁLISIS DE BENEFICIOS TÉCNICOS 24H

### 3.1 Operación Diurna (Generación Solar)

Durante las horas de sol (6:00-18:00), los beneficios incluyen:

- **Reducción de flujo desde subestación**: Hasta 85% en clusters comerciales
- **Mejora de tensión**: 3-5% en puntos de conexión
- **Reducción de pérdidas**: 6-10% en alimentadores

### 3.2 Operación Nocturna (STATCOM)

Durante la noche (18:00-6:00), los inversores proporcionan:

- **Compensación reactiva**: Hasta 30% de capacidad nominal en VAr
- **Mejora de factor de potencia**: De 0.85 a 0.93 promedio
- **Soporte de tensión**: Crítico en zonas residenciales con picos nocturnos

### 3.3 Modos de Operación Identificados

| Modo de Operación | Clusters | Características |
|-------------------|----------|------------------|
| Balanced 24h | 10 | Beneficios significativos tanto día como noche |
| STATCOM-Optimized | 5 | Mayor valor en soporte nocturno que generación diurna |

## 4. RESTRICCIONES Y MITIGACIONES

### 4.1 Disponibilidad de Terreno

| Categoría | Clusters | Hectáreas Promedio | Estrategia de Mitigación |
|-----------|----------|--------------------|--------------------------| 
| Alta | 0 | <1 ha | Implementación directa |
| Media | 3 | 1-5 ha | Negociación estándar |
| Baja | 10 | 5-20 ha | Múltiples sitios o solar distribuido |
| Muy Baja | 2 | >20 ha | Innovación requerida (techos, parking) |

### 4.2 Capacidad de Red

- **Análisis pendiente**: Estudios de flujo de potencia detallados
- **Riesgo principal**: Limitaciones en transformadores de subestación
- **Mitigación**: Implementación gradual con monitoreo continuo

## 5. ESPECIFICACIONES TÉCNICAS RECOMENDADAS

### 5.1 Inversores

- **Capacidad Q at Night**: Mínimo 30% de Snom
- **Certificación**: IEEE 1547-2018, UL 1741-SA
- **Control**: Capacidad de operación remota vía DERMS
- **Modos**: Volt-Var, Volt-Watt, Factor de Potencia fijo
- **Comunicación**: IEC 61850 o DNP3

### 5.2 Sistema de Gestión (DERMS)

- **Arquitectura**: Centralizada con redundancia
- **Capacidad**: Gestión de 120 MW distribuidos
- **Funciones**: Despacho económico, control de tensión, gestión de reactiva
- **Integración**: SCADA existente de EDERSA

## 6. ANÁLISIS DE SENSIBILIDAD

### 6.1 Variación de Pesos en IAS 3.0

Se realizó análisis de sensibilidad variando ±20% los pesos de C6 y C7:

- **Reducir peso C6**: Favorece clusters comerciales/industriales
- **Aumentar peso C7**: Penaliza fuertemente clusters urbanos
- **Configuración actual**: Balance óptimo para valorar beneficios 24h

### 6.2 Impacto de Restricciones de Terreno

Escenarios analizados:

1. **Sin restricciones**: 15 clusters viables
2. **Restricción moderada** (actual): 13 clusters viables
3. **Restricción severa**: Solo 8 clusters viables

## 7. CONCLUSIONES TÉCNICAS

1. La metodología IAS 3.0 identifica correctamente oportunidades no visibles con enfoques tradicionales
2. El soporte reactivo nocturno puede representar hasta 40% del valor total del proyecto
3. Las restricciones de terreno son el factor limitante principal, no la viabilidad técnica
4. La implementación por fases permite aprendizaje y optimización continua

---

*Documento técnico generado automáticamente por el sistema de análisis GD-EDERSA*
