# ANÁLISIS TÉCNICO-ECONÓMICO DE GENERACIÓN DISTRIBUIDA
## LÍNEA SUR RÍO NEGRO - SISTEMA 33 kV

### RESUMEN EJECUTIVO

El sistema de transmisión radial de 33 kV de la Línea Sur presenta severas deficiencias operativas:
- Caída de tensión extrema: hasta 61% entre Pilcaniyeu y estaciones remotas
- Tensiones mínimas críticas: 0.225 pu en Los Menucos (7.4 kV en sistema 13.2 kV)
- Sistema operando al límite con reguladores de tensión en múltiples puntos
- Pérdidas técnicas elevadas en línea de 270 km

### 1. DIAGNÓSTICO DEL SISTEMA ACTUAL

#### 1.1 Perfiles de Tensión (Datos reales medidos)
| Estación | Tensión Nominal | V_mín (kV) | V_mín (pu) | Horas < 0.95 pu |
|----------|----------------|------------|------------|-----------------|
| Pilcaniyeu | 33 kV | 19.5 | 0.592 | 200+ |
| Jacobacci | 13.2 kV | 7.6 | 0.230 | 200+ |
| Maquinchao | 13.2 kV | 7.8 | 0.235 | 200+ |
| Los Menucos | 13.2 kV | 7.4 | 0.225 | 200+ |

#### 1.2 Demanda y Factor de Potencia
| Estación | P_avg (MW) | Q_avg (MVAr) | FP_avg | Criticidad |
|----------|------------|--------------|--------|------------|
| Pilcaniyeu | 2.79 | 0.10 | 0.993 | Media |
| Jacobacci | 0.50 | 0.17 | 0.898 | Alta |
| Maquinchao | 0.35 | 0.12 | 0.941 | Alta |
| Los Menucos | 0.93 | 0.21 | 0.966 | Crítica |

#### 1.3 Pérdidas en el Sistema
- Tramo Pilcaniyeu-Jacobacci (150 km): 2.29 MW (82% de pérdidas)
- Pérdidas totales estimadas: 1.86 MW
- Pérdida específica promedio: 6.9 kW/km

### 2. PUNTOS CRÍTICOS PARA GENERACIÓN DISTRIBUIDA

#### Ranking por Criticidad (Score máximo: 8)

**1. JACOBACCI (Score: 6/8)**
- Tensión crítica: 0.230 pu
- Bajo factor de potencia: 0.898
- Alta demanda reactiva: 0.17 MVAr
- **GD Recomendada: 0.2 - 0.3 MW**

**2. LOS MENUCOS (Score: 5/8)**
- Tensión más baja del sistema: 0.225 pu
- Mayor demanda: 0.93 MW
- Extremo de línea (270 km)
- **GD Recomendada: 0.3 - 0.5 MW**

**3. MAQUINCHAO (Score: 3/8)**
- Tensión baja: 0.235 pu
- Factor de potencia: 0.941
- **GD Recomendada: 0.1 - 0.2 MW**

### 3. ANÁLISIS ECONÓMICO - CASO LOS MENUCOS

#### 3.1 Costos Actuales de Generación (Referencia 2024)
- **Alquiler equipos**: USD 516-1,170/día según potencia
- **Combustible gas**: USD 0.11137/m³
- **Consumo específico**: 0.278-0.286 m³/kWh
- **Costo total generación**: ~ 334-370 MM ARS/mes (febrero-marzo 2024)

#### 3.2 Configuración Actual Los Menucos
- 2 motogeneradores a gas de 1.5 MW c/u (3 MW total)
- Conexión en 13.2 kV
- Operación para control de tensión y reserva fría
- Factor de utilización: ~30% (0.93 MW promedio sobre 3 MW instalados)

### 4. RECOMENDACIONES TÉCNICAS

#### 4.1 Implementación por Fases

**FASE 1 - CRÍTICA (0-6 meses)**
- Los Menucos: 0.5 MW adicionales (optimizar existente)
- Jacobacci: 0.3 MW nueva instalación
- Tecnología: Grupos electrógenos a gas natural

**FASE 2 - ALTA PRIORIDAD (6-12 meses)**
- Maquinchao: 0.2 MW
- Evaluación solar + BESS para horario diurno

**FASE 3 - MEJORA CONTINUA (12-24 meses)**
- Sistemas híbridos en puntos estratégicos
- Automatización y control remoto centralizado

#### 4.2 Beneficios Esperados
- Mejora de tensión: llevar a >0.95 pu en todos los puntos
- Reducción pérdidas: ~30-40% en tramos críticos
- Aumento capacidad: habilitar 20-30% más de demanda
- Confiabilidad: respaldo ante contingencias

### 5. CONCLUSIONES

1. **Urgencia**: El sistema opera en condiciones inaceptables de calidad de servicio
2. **Solución probada**: Los Menucos demuestra viabilidad de GD
3. **Inversión modular**: Implementación por fases reduce riesgo
4. **Retorno**: Reducción pérdidas y diferimiento inversiones en transmisión

### 6. PRÓXIMOS PASOS

1. Estudio detallado de flujos de carga con GD propuesta
2. Evaluación ambiental y permisos
3. Licitación equipamiento Fase 1
4. Plan de O&M y capacitación personal
5. Sistema SCADA para monitoreo integrado

---
*Análisis basado en registros EPRE 2024-2025 y costos reales Los Menucos*