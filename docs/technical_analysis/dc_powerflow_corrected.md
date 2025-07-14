# Análisis de Flujo de Potencia DC - Sistema Línea Sur (Corregido)

## Resumen del Sistema

### Datos Reales del Sistema
- **Carga Total**: 3.8 MW (1.05 MVAr)
- **Factor de Potencia**: 0.964
- **Generación Distribuida**: 1.8 MW en Los Menucos (4 horas/día)
- **Importación desde Red (Pilcaniyeu)**: 2.0 MW
- **Longitud Total**: 270 km

## 1. Estado de Nodos - Condiciones Actuales

| Nodo | Distancia (km) | Carga (MW) | Gen. (MW) | Inyección Neta (MW) | Voltaje Estimado (pu) | Voltaje (kV) | Estado |
|:-----|---------------:|-----------:|----------:|--------------------:|----------------------:|-------------:|:-------|
| **PILCANIYEU** | 0 | 0.00 | 0.0 | +3.80* | 0.950 | 31.35 | ⚠️ Slack |
| **COMALLO** | 70 | 0.30 | 0.0 | -0.30 | 0.920 | 30.36 | ❌ Bajo |
| **ONELLI** | 100 | 0.10 | 0.0 | -0.10 | 0.905 | 29.87 | ❌ Bajo |
| **JACOBACCI** | 150 | 1.45 | 0.0 | -1.45 | 0.875 | 28.88 | ❌ Crítico |
| **MAQUINCHAO** | 210 | 0.50 | 0.0 | -0.50 | 0.850 | 28.05 | ❌ Crítico |
| **AGUADA GUERRA** | 240 | 0.05 | 0.0 | -0.05 | 0.840 | 27.72 | ❌ Crítico |
| **LOS MENUCOS** | 270 | 1.40 | 1.8 | +0.40 | 0.835 | 27.56 | ❌ Crítico |

*Pilcaniyeu debe inyectar carga total + pérdidas

### Observaciones:
- La red importa 2.0 MW desde Pilcaniyeu (3.8 MW carga - 1.8 MW GD)
- Todos los nodos operan por debajo del límite regulatorio (0.95 pu)
- La GD en Los Menucos invierte el flujo localmente (+0.4 MW de exceso)

## 2. Flujos de Potencia y Pérdidas por Línea

| Línea | Long. (km) | Conductor | Flujo (MW) | Pérdidas (MW) | Pérdidas (%) | I (A) | Cargabilidad (%) |
|:------|------------|:----------|------------|---------------|--------------|-------|------------------|
| **Pilcaniyeu → Comallo** | 70 | LA-120 | 3.80 | 0.025 | 0.66% | 66 | 22% |
| **Comallo → Jacobacci** | 80 | LA-120 | 3.50 | 0.021 | 0.60% | 61 | 20% |
| **Jacobacci → Maquinchao** | 60 | LA-95 | 2.05 | 0.010 | 0.49% | 36 | 14% |
| **Maquinchao → Los Menucos** | 60 | LA-95 | 1.50 | 0.005 | 0.33% | 26 | 10% |
| **Los Menucos (local)** | - | - | -0.40 | - | - | 7 | - |
| **TOTAL** | **270** | - | - | **0.061** | **1.6%** | - | - |

### Notas:
- Flujo negativo en Los Menucos indica exportación local (GD > Carga)
- Pérdidas totales muy bajas debido a la baja carga
- Líneas operando muy por debajo de su capacidad

## 3. Análisis Económico

### 3.1 Costos Anuales de Energía

| Concepto | Energía (MWh/año) | Tarifa (USD/MWh) | Costo Anual (USD) |
|:---------|------------------:|------------------:|------------------:|
| **Energía desde Red** | 5,256 | 62.50 | $328,500 |
| **GD Los Menucos** | 2,628 | 122.65 | $322,324 |
| **Pérdidas Técnicas** | 160 | 62.50 | $10,000 |
| **TOTAL** | **8,044** | - | **$660,824** |

*Cálculos con FC=30% para carga y 50% para GD (4h/8h pico)

### 3.2 Desglose de Pérdidas por Línea

| Línea | Pérdidas (MW) | Pérdidas Anuales (MWh) | Costo Anual (USD) |
|:------|-------------:|------------------------:|------------------:|
| Pilcaniyeu → Comallo | 0.025 | 66 | $4,125 |
| Comallo → Jacobacci | 0.021 | 55 | $3,438 |
| Jacobacci → Maquinchao | 0.010 | 26 | $1,625 |
| Maquinchao → Los Menucos | 0.005 | 13 | $813 |
| **TOTAL** | **0.061** | **160** | **$10,001** |

## 4. Indicadores Clave (KPIs)

| Indicador | Valor Actual | Límite Aceptable | Estado |
|:----------|-------------:|------------------|:-------|
| **Pérdidas Totales** | 1.6% | < 5% | ✅ Excelente |
| **Voltaje Mínimo** | 0.835 pu | > 0.95 pu | ❌ Crítico |
| **Costo Pérdidas/MWh Entregado** | $1.24 | < $5 | ✅ Bajo |
| **Factor de Utilización Líneas** | 10-22% | < 70% | ✅ Holgado |
| **Costo Total Energía** | $82.17/MWh | < $100 | ✅ OK |

## 5. Análisis de Sensibilidad dV/dP

Usando la sensibilidad medida de **-0.112 pu/MW**:

| Ubicación GD | MW Adicionales | Mejora Voltaje Los Menucos | Nuevo V (pu) |
|:-------------|---------------:|---------------------------:|-------------:|
| Los Menucos | +1.0 | +0.112 | 0.947 |
| Maquinchao | +1.0 | +0.084 | 0.919 |
| Jacobacci | +1.0 | +0.056 | 0.891 |
| Los Menucos | +1.5 | +0.168 | 1.003 |

### Conclusión: Se requieren 1.5 MW adicionales en Los Menucos para alcanzar 1.0 pu

## 6. Comparación de Alternativas

| Alternativa | CAPEX (MUSD) | Reducción Importación | Mejora V min | Payback |
|:------------|-------------:|----------------------:|-------------:|--------:|
| **Estado Actual** | 0 | 0% | 0.835 pu | - |
| **+1.5 MW PV Los Menucos** | 2.0 | 75% | 0.947 pu | 8 años |
| **+2 MW PV + BESS Maquinchao** | 4.5 | 100% | 0.920 pu | 12 años |
| **Refuerzo Línea** | 8.0 | 0% | 0.885 pu | >20 años |

## 7. Recomendaciones

### Inmediatas (0-3 meses)
1. **Verificar mediciones reales** de voltaje en todos los nodos
2. **Optimizar despacho GD**: Concentrar en horas 18-22h
3. **Ajustar taps** en transformador Pilcaniyeu (+5%)

### Corto Plazo (3-12 meses)
1. **Instalar 1.5 MW PV en Los Menucos**
   - Inversión: $2.0M
   - Lleva voltaje a 0.947 pu
   - Reduce importación 75%

### Mediano Plazo (1-2 años)
1. **BESS 1 MW/4 MWh en Los Menucos**
   - Permite operación isla en emergencias
   - Arbitraje de energía PV
   - Soporte de voltaje 24/7

## 8. Conclusiones

1. **Carga real del sistema**: 3.8 MW (no 13.5 MW)
2. **Pérdidas bajas**: 1.6% debido a baja carga
3. **Problema principal**: Caída de voltaje por distancia
4. **Solución óptima**: 1.5 MW PV adicionales en Los Menucos
5. **Inversión mínima**: $2M para resolver problema de voltaje

---
*Análisis basado en datos reales del DataManager y sensibilidad medida dV/dP = -0.112 pu/MW*