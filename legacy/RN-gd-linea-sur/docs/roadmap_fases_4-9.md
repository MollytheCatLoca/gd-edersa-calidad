# ROADMAP REDISEÑADO: FASES 4-9
## Evaluación de Impacto Técnico-Económico de PSFV con/sin BESS

### CONTEXTO DEL REDISEÑO

Basándonos en los hallazgos críticos de la Fase 3:
- Sistema 100% fuera de límites regulatorios
- Sensibilidad dV/dP alta (especialmente Maquinchao: -0.112 pu/MW)
- 547 eventos críticos a eliminar
- Pico nocturno 20-22h requiere BESS
- Horario solar coincide con demanda media

Las fases 4-9 se rediseñan completamente para enfocarse en la evaluación específica de PSFV.

---

## FASE 4: MODELADO DE RECURSO SOLAR Y PERFILES PSFV

### Objetivo
Caracterizar el recurso solar real de la zona y generar perfiles de generación PSFV precisos.

### Actividades Principales

#### 4.1 Obtención y Análisis de Recurso Solar
- **Fuentes de datos**:
  - NASA POWER API (datos históricos 10+ años)
  - PVGIS para la región específica
  - Correlación con estación meteorológica más cercana
- **Variables clave**:
  - GHI (Global Horizontal Irradiance)
  - DNI (Direct Normal Irradiance) 
  - DHI (Diffuse Horizontal Irradiance)
  - Temperatura ambiente horaria
- **Análisis estadístico**:
  - Promedio mensual/anual
  - Percentiles P10, P50, P90
  - Días típicos: despejado, nublado, parcialmente nublado

#### 4.2 Modelado de Generación PSFV
- **Modelo básico**: 
  ```
  P_pv = GHI × A × η_panel × η_inv × (1 - γ(T - 25°C)) × (1 - pérdidas)
  ```
- **Parámetros**:
  - η_panel: 18-20% (silicio monocristalino)
  - η_inv: 97-98%
  - γ: -0.4%/°C (coef. temperatura)
  - Pérdidas: 10-15% (sombreado, suciedad, cables, mismatch)
- **Factor de capacidad esperado**: 15-20% para la zona

#### 4.3 Análisis de Complementariedad Solar-Demanda
- Superposición horaria de perfiles
- Cuantificar:
  - Horas de exceso solar (curtailment sin BESS)
  - Horas de déficit (requieren BESS o red)
  - Energía aprovechable directamente
- Por estación y época del año

### Entregables
1. **Base de datos solar**: 8760 horas × N años
2. **Dashboard de recurso solar**: Visualización interactiva
3. **Perfiles de generación normalizados**: Por MW instalado
4. **Informe de complementariedad**: Match solar-demanda

### Duración Estimada: 2-3 semanas

---

## FASE 5: SIMULACIÓN DE ESCENARIOS PSFV

### Objetivo
Evaluar el impacto técnico de diferentes configuraciones PSFV en el sistema eléctrico.

### Escenarios a Simular

#### 5.1 Matriz de Escenarios
| Escenario | Ubicación | Tamaño PSFV | BESS | Notas |
|-----------|-----------|-------------|------|-------|
| Base | - | 0 MW | No | Situación actual |
| PV-1A | Maquinchao | 2 MW | No | Max sensibilidad |
| PV-1B | Maquinchao | 2 MW | 3 MWh | Con BESS |
| PV-2A | Los Menucos | 3 MW | No | Fin de línea |
| PV-2B | Los Menucos | 3 MW | 5 MWh | Con BESS |
| PV-3A | Jacobacci | 3 MW | No | Mayor carga |
| PV-3B | Jacobacci | 3 MW | 4 MWh | Con BESS |
| PV-4 | Multi-sitio | 2+2+2 MW | 8 MWh | Distribuido |

#### 5.2 Métricas de Evaluación
- **Mejora de tensión**: ΔV = sensibilidad × P_inyectada
- **Reducción eventos críticos**: De 547 a X
- **Reducción pérdidas**: MW y MWh/año
- **Energía curtailed**: Sin BESS
- **Factor de utilización PSFV**: Con/sin BESS

#### 5.3 Simulación Técnica
- Usar sensibilidades de Fase 3
- Flujo de carga simplificado hora a hora
- Considerar límites de inyección
- Estrategias de control BESS:
  - Peak shaving
  - Voltage support
  - Ramp rate control

### Entregables
1. **Matriz de resultados**: Todos los escenarios
2. **Dashboard de simulación**: Interactivo, what-if
3. **Curvas de mejora**: V vs P_psfv por ubicación
4. **Dimensionamiento óptimo BESS**: Por ubicación

### Duración Estimada: 3-4 semanas

---

## FASE 6: ANÁLISIS ECONÓMICO PSFV

### Objetivo
Evaluar la viabilidad económica de las alternativas PSFV identificadas.

### Componentes del Análisis

#### 6.1 CAPEX Detallado
| Componente | Rango USD | Unidad | Notas |
|------------|-----------|--------|-------|
| PSFV | 800-1000 | /kW | Incluye paneles e inversores |
| BESS | 300-400 | /kWh | LFP, incluye PCS |
| BOS | 15-20% | CAPEX | Balance of system |
| Conexión | 50-100 | /kW | Subestación y línea |
| Obra civil | 10-15% | CAPEX | Terreno, cercado, caminos |
| Logística | +20-30% | Total | Por ubicación remota |

#### 6.2 OPEX Anual
- O&M PSFV: 15-20 USD/kW-año
- O&M BESS: 5-10 USD/kWh-año
- Seguros: 0.5% CAPEX
- Monitoreo remoto: 5,000 USD/año
- Degradación: 0.5%/año (paneles), 2%/año (BESS)

#### 6.3 Beneficios Económicos
- **Energía generada**: MWh/año × precio
- **Reducción pérdidas**: ΔPérdidas × 8760h × precio
- **Mejora calidad**: Penalidades evitadas
- **Diferimiento inversiones**: VPN de transmisión evitada
- **Servicios auxiliares**: Si regulación lo permite

#### 6.4 Evaluación Financiera
- Horizonte: 20-25 años
- Tasas descuento: 8%, 10%, 12%
- Inflación: 3-4% anual
- Precio energía: Escalamiento 2-3% anual
- Métricas: VAN, TIR, Payback, LCOE

### Entregables
1. **Modelo económico**: Excel/Python parametrizable
2. **Análisis comparativo**: PSFV vs PSFV+BESS
3. **Ranking económico**: Por ubicación y configuración
4. **Análisis sensibilidad**: Variables críticas

### Duración Estimada: 2-3 semanas

---

## FASE 7: OPTIMIZACIÓN Y DISEÑO FINAL

### Objetivo
Determinar la configuración óptima PSFV+BESS considerando aspectos técnicos y económicos.

### Proceso de Optimización

#### 7.1 Función Objetivo Multi-criterio
```
Min: CTOTAL = CAPEX + VPN(OPEX) - VPN(Beneficios)
Sujeto a:
- Eventos críticos = 0
- V_min ≥ 0.95 pu ∀t
- P_psfv ≤ P_max_inyección
- E_bess ≥ E_requerida_pico
```

#### 7.2 Variables de Decisión
- Ubicación(es) de PSFV
- Tamaño PSFV por ubicación (MW)
- Tamaño BESS por ubicación (MWh)
- Estrategia de control

#### 7.3 Diseño Técnico Resultante
- **Layout PSFV**: Configuración strings, inversores
- **Arquitectura DC**: 1000-1500 Vdc
- **Sistema BESS**: Contenedores, HVAC, BMS
- **Protecciones**: DC/AC, sobretensiones, anti-isla
- **SCADA**: Integración con sistema existente
- **Comunicaciones**: Fibra óptica/radio

### Entregables
1. **Solución óptima**: Ubicación, tamaño, configuración
2. **Ingeniería básica**: Single lines, layouts, P&IDs
3. **Especificaciones técnicas**: Equipos principales
4. **Plan de implementación**: Fases y cronograma

### Duración Estimada: 3-4 semanas

---

## FASE 8: ANÁLISIS DE SENSIBILIDAD Y RIESGOS

### Objetivo
Evaluar la robustez de la solución ante variaciones e incertidumbres.

### Análisis de Sensibilidad

#### 8.1 Variables Técnicas
- Radiación solar: ±10% (año bueno/malo)
- Crecimiento demanda: 0%, 1.5%, 3% anual
- Degradación acelerada: Paneles 0.7%/año, BESS 3%/año
- Disponibilidad: 95%, 97%, 99%

#### 8.2 Variables Económicas
- CAPEX: -20%, base, +20%
- Precio energía: -15%, base, +15%
- Tasa descuento: 8%, 10%, 12%
- Tipo cambio: Devaluación 0%, 20%, 40%

#### 8.3 Matriz de Riesgos
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Sombreado no previsto | Media | Alto | Estudio detallado sitio |
| Cambio regulatorio | Media | Alto | Contratos largo plazo |
| Falla BESS temprana | Baja | Alto | Garantía extendida |
| Vandalismo | Media | Medio | Seguridad, seguros |

### Entregables
1. **Análisis tornado**: Variables más críticas
2. **Escenarios**: Optimista, base, pesimista
3. **Matriz de riesgos**: Con plan de mitigación
4. **Recomendaciones**: Para robustecer proyecto

### Duración Estimada: 1-2 semanas

---

## FASE 9: INFORME EJECUTIVO Y DASHBOARD FINAL

### Objetivo
Presentar resultados de forma clara para toma de decisiones y crear herramienta interactiva.

### Componentes

#### 9.1 Suite de Documentos
1. **Resumen Ejecutivo** (5 páginas):
   - Problema y solución
   - Inversión y retorno
   - Beneficios clave
   - Recomendación clara

2. **Informe Técnico Completo** (50-80 páginas):
   - Metodología detallada
   - Todos los análisis
   - Resultados y conclusiones
   - Anexos técnicos

3. **Presentación Ejecutiva** (20 slides):
   - Story-telling del problema
   - Solución propuesta
   - Números clave
   - Próximos pasos

#### 9.2 Dashboard Interactivo Final
- **Módulo 1**: Situación actual (Fase 1-3)
- **Módulo 2**: Recurso solar y perfiles
- **Módulo 3**: Simulador de escenarios
- **Módulo 4**: Evaluador económico
- **Módulo 5**: Solución óptima
- **Módulo 6**: Análisis de sensibilidad

#### 9.3 Material de Soporte
- Infografías de impacto
- One-pagers por stakeholder
- FAQ técnicas y económicas
- Videos demostrativos (opcional)

### Entregables
1. **Documentación completa**: PDF y editables
2. **Dashboard web**: Desplegado y documentado
3. **Presentaciones**: Adaptadas por audiencia
4. **Repositorio**: Código y datos organizados

### Duración Estimada: 2-3 semanas

---

## CRONOGRAMA GENERAL

| Fase | Duración | Inicio | Fin |
|------|----------|--------|-----|
| Fase 4 | 3 semanas | Semana 1 | Semana 3 |
| Fase 5 | 4 semanas | Semana 4 | Semana 7 |
| Fase 6 | 3 semanas | Semana 8 | Semana 10 |
| Fase 7 | 4 semanas | Semana 11 | Semana 14 |
| Fase 8 | 2 semanas | Semana 15 | Semana 16 |
| Fase 9 | 3 semanas | Semana 17 | Semana 19 |

**Duración total**: 19 semanas (~5 meses)

---

## RECURSOS NECESARIOS

### Datos
- API NASA POWER / PVGIS
- Hojas de datos equipos PSFV/BESS
- Tarifas eléctricas actualizadas
- Costos de construcción local

### Herramientas
- Python: pvlib, pandas, numpy
- Optimización: scipy, pyomo
- Económico: numpy-financial
- Dashboard: Dash/Plotly

### Expertise
- Ingeniería solar FV
- Sistemas BESS
- Análisis económico
- Integración SCADA

---

*Documento creado: Enero 2025*
*Roadmap para evaluación PSFV en Sistema Línea Sur*