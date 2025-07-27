# KB.6 - GUÍAS OPERATIVAS Y SOSTENIBILIDAD
## Protocolos de Operación, Mantenimiento y Replicabilidad del Modelo

---

## ÍNDICE

1. [INTRODUCCIÓN](#1-introducción)
2. [PROTOCOLOS DE OPERACIÓN](#2-protocolos-de-operación)
3. [MANTENIMIENTO PREVENTIVO](#3-mantenimiento-preventivo)
4. [MANTENIMIENTO CORRECTIVO](#4-mantenimiento-correctivo)
5. [MONITOREO Y CONTROL](#5-monitoreo-y-control)
6. [GESTIÓN DE REPUESTOS](#6-gestión-de-repuestos)
7. [CAPACITACIÓN TÉCNICA](#7-capacitación-técnica)
8. [SOSTENIBILIDAD DEL MODELO](#8-sostenibilidad-del-modelo)
9. [REPLICABILIDAD](#9-replicabilidad)
10. [MEJORA CONTINUA](#10-mejora-continua)

---

## 1. INTRODUCCIÓN

### 1.1 Objetivo del Documento
Este documento establece las guías operativas integrales para garantizar la operación eficiente, el mantenimiento adecuado y la sostenibilidad a largo plazo de los sistemas de generación distribuida implementados en la Línea Sur.

### 1.2 Alcance
- Operación diaria de sistemas fotovoltaicos
- Mantenimiento preventivo y correctivo
- Monitoreo y control remoto
- Gestión de recursos humanos y técnicos
- Estrategias de sostenibilidad
- Modelo de replicabilidad

### 1.3 Usuarios Objetivo
- Personal técnico de EDERSA
- Operadores locales
- Supervisores de mantenimiento
- Gestores de proyecto
- Tomadores de decisión

---

## 2. PROTOCOLOS DE OPERACIÓN

### 2.1 Operación Normal

#### 2.1.1 Arranque del Sistema
```
PROCEDIMIENTO DE ARRANQUE DIARIO
1. Verificación visual del sistema
2. Revisión de alarmas nocturnas
3. Comprobación de comunicaciones
4. Verificación de parámetros operativos
5. Registro en bitácora
```

#### 2.1.2 Operación Continua
- **Monitoreo remoto**: Cada 15 minutos
- **Verificación local**: Cada 4 horas
- **Registro de producción**: Horario
- **Análisis de desviaciones**: Inmediato

#### 2.1.3 Parada del Sistema
```
PROCEDIMIENTO DE PARADA
1. Notificación al centro de control
2. Reducción gradual de carga
3. Desconexión de inversores
4. Apertura de seccionadores DC
5. Activación de modo seguro
```

### 2.2 Operación en Contingencia

#### 2.2.1 Falla de Red
- Activación automática de modo isla
- Gestión de cargas prioritarias
- Coordinación con almacenamiento
- Comunicación con usuarios

#### 2.2.2 Condiciones Climáticas Adversas
- **Viento > 100 km/h**: Modo supervivencia
- **Granizo**: Posición de protección
- **Tormentas eléctricas**: Desconexión preventiva
- **Nieve**: Protocolo de limpieza

### 2.3 Coordinación con la Red

#### 2.3.1 Sincronización
- Verificación de parámetros de red
- Ajuste de fase y frecuencia
- Rampa de conexión suave
- Confirmación de estabilidad

#### 2.3.2 Gestión de Potencia
- Control de factor de potencia
- Limitación de armónicos
- Respuesta a consignas remotas
- Participación en regulación

---

## 3. MANTENIMIENTO PREVENTIVO

### 3.1 Plan de Mantenimiento Anual

#### 3.1.1 Mantenimiento Diario
| Tarea | Responsable | Tiempo | Herramientas |
|-------|-------------|---------|--------------|
| Inspección visual | Operador local | 30 min | Lista de verificación |
| Limpieza básica | Operador local | 45 min | Kit de limpieza |
| Registro de datos | Operador local | 15 min | Planilla/App |

#### 3.1.2 Mantenimiento Semanal
| Tarea | Responsable | Tiempo | Herramientas |
|-------|-------------|---------|--------------|
| Limpieza de paneles | Técnico | 2 horas | Equipo especializado |
| Verificación de conexiones | Técnico | 1 hora | Multímetro, torquímetro |
| Test de comunicaciones | Técnico | 30 min | Laptop, software |

#### 3.1.3 Mantenimiento Mensual
| Tarea | Responsable | Tiempo | Herramientas |
|-------|-------------|---------|--------------|
| Termografía | Especialista | 3 horas | Cámara térmica |
| Análisis de rendimiento | Ingeniero | 2 horas | Software análisis |
| Calibración de sensores | Especialista | 2 horas | Equipos calibración |

#### 3.1.4 Mantenimiento Semestral
| Tarea | Responsable | Tiempo | Herramientas |
|-------|-------------|---------|--------------|
| Revisión estructural | Ing. Civil | 4 horas | Instrumentos medición |
| Pruebas eléctricas completas | Ing. Eléctrico | 6 horas | Analizador de redes |
| Actualización de firmware | Especialista IT | 2 horas | Software específico |

### 3.2 Mantenimiento Específico por Componente

#### 3.2.1 Paneles Fotovoltaicos
```
PROTOCOLO DE MANTENIMIENTO - PANELES
Frecuencia: Mensual
1. Inspección visual de microfisuras
2. Medición de aislamiento (>40 MΩ)
3. Verificación de diodos bypass
4. Limpieza con agua desmineralizada
5. Revisión de anclajes y sellados
```

#### 3.2.2 Inversores
```
PROTOCOLO DE MANTENIMIENTO - INVERSORES
Frecuencia: Trimestral
1. Limpieza de filtros de aire
2. Verificación de ventiladores
3. Análisis de armónicos (<5% THD)
4. Prueba de protecciones
5. Respaldo de configuración
```

#### 3.2.3 Sistema de Monitoreo
```
PROTOCOLO DE MANTENIMIENTO - MONITOREO
Frecuencia: Mensual
1. Calibración de piranómetros
2. Verificación de dataloggers
3. Test de comunicaciones
4. Actualización de base de datos
5. Generación de reportes
```

### 3.3 Herramientas y Equipos

#### 3.3.1 Kit Básico de Mantenimiento
- Multímetro categoría IV
- Pinza amperimétrica DC/AC
- Megóhmetro 1000V
- Torquímetro 5-50 Nm
- Cámara termográfica
- Kit de limpieza especializado

#### 3.3.2 Equipos Especializados
- Analizador de curvas I-V
- Electroluminiscencia portátil
- Drone con cámara térmica
- Analizador de calidad de energía
- Osciloscopio portátil

---

## 4. MANTENIMIENTO CORRECTIVO

### 4.1 Diagnóstico de Fallas

#### 4.1.1 Árbol de Decisión para Diagnóstico
```
FALLA DETECTADA
    |
    ├── ¿Producción = 0?
    │   ├── SÍ → Verificar DC
    │   │   ├── Fusibles
    │   │   ├── Conexiones
    │   │   └── Diodos
    │   └── NO → Verificar rendimiento
    │       ├── < 80% esperado
    │       ├── Sombreado
    │       └── Degradación
    |
    └── ¿Alarma activa?
        ├── SÍ → Consultar manual
        └── NO → Análisis detallado
```

#### 4.1.2 Fallas Comunes y Soluciones
| Falla | Causa Probable | Solución | Tiempo |
|-------|----------------|----------|---------|
| Baja producción | Suciedad | Limpieza | 2h |
| String apagado | Fusible | Reemplazo | 30min |
| Inversor offline | Sobrecalentamiento | Limpieza filtros | 1h |
| Comunicación perdida | Cable/Config | Revisión/Reset | 1h |

### 4.2 Procedimientos de Reparación

#### 4.2.1 Reemplazo de Panel
```
PROCEDIMIENTO SEGURO
1. Desenergizar string completo
2. Verificar ausencia de tensión
3. Desconectar conectores MC4
4. Retirar panel dañado
5. Instalar panel nuevo
6. Verificar polaridad
7. Reconectar y probar
Tiempo estimado: 45 minutos
```

#### 4.2.2 Reparación de Inversor
```
NIVELES DE INTERVENCIÓN
Nivel 1 (Local): Reset, limpieza
Nivel 2 (Técnico): Cambio de fusibles, ventiladores
Nivel 3 (Especialista): Tarjetas electrónicas
Nivel 4 (Fábrica): Componentes de potencia
```

### 4.3 Gestión de Garantías

#### 4.3.1 Documentación Requerida
- Número de serie del equipo
- Fecha de instalación
- Descripción detallada de falla
- Mediciones realizadas
- Fotografías del problema
- Historial de mantenimiento

#### 4.3.2 Proceso de Reclamación
1. Notificación inicial (24h)
2. Envío de documentación (48h)
3. Evaluación del fabricante (5-10 días)
4. Autorización de reemplazo
5. Logística de envío
6. Instalación y pruebas

---

## 5. MONITOREO Y CONTROL

### 5.1 Sistema SCADA

#### 5.1.1 Arquitectura del Sistema
```
NIVEL 1: Campo
├── Sensores meteorológicos
├── Medidores de energía
├── Estados de equipos
└── Alarmas locales

NIVEL 2: Comunicación
├── Red celular 4G
├── Respaldo satelital
└── Protocolo Modbus TCP

NIVEL 3: Centro de Control
├── Servidores SCADA
├── Base de datos histórica
├── Interface HMI
└── Sistema de alarmas
```

#### 5.1.2 Variables Monitoreadas
| Variable | Unidad | Frecuencia | Alarma |
|----------|---------|------------|---------|
| Irradiancia | W/m² | 1 min | <100 en horario solar |
| Temperatura módulo | °C | 5 min | >85°C |
| Producción DC | kW | 1 min | <80% esperado |
| Producción AC | kW | 1 min | Desviación >10% |
| Factor de potencia | - | 1 min | <0.95 |

### 5.2 Análisis de Rendimiento

#### 5.2.1 KPIs Principales
```
Performance Ratio (PR)
PR = Energía real / Energía teórica
Objetivo: >80%

Disponibilidad
D = Horas operación / Horas totales
Objetivo: >98%

Factor de capacidad
FC = Energía real / Energía nominal
Objetivo: >18%
```

#### 5.2.2 Reportes Automáticos
- **Diario**: Producción, alarmas, eventos
- **Semanal**: Rendimiento, disponibilidad
- **Mensual**: Análisis detallado, tendencias
- **Anual**: Balance completo, degradación

### 5.3 Gestión de Alarmas

#### 5.3.1 Categorización
| Prioridad | Tipo | Tiempo Respuesta | Ejemplo |
|-----------|------|------------------|---------|
| Crítica | Seguridad | Inmediato | Falla de aislamiento |
| Alta | Producción | <1 hora | Inversor offline |
| Media | Rendimiento | <4 horas | PR bajo |
| Baja | Información | <24 horas | Mantenimiento programado |

#### 5.3.2 Protocolo de Respuesta
1. Notificación automática (SMS/Email)
2. Confirmación de recepción
3. Diagnóstico remoto
4. Decisión de intervención
5. Despacho de personal
6. Resolución y cierre

---

## 6. GESTIÓN DE REPUESTOS

### 6.1 Inventario Crítico

#### 6.1.1 Stock Mínimo Local
| Componente | Cantidad | Justificación |
|------------|----------|---------------|
| Fusibles DC | 20 unid | Alta rotación |
| Conectores MC4 | 50 pares | Mantenimiento |
| Paneles FV | 2% instalado | Reemplazos |
| Ventiladores inversor | 2 unid | Crítico |
| Tarjetas comunicación | 1 unid | Crítico |

#### 6.1.2 Stock Regional (Viedma)
| Componente | Cantidad | Lead time |
|------------|----------|-----------|
| Inversor completo | 1 unid | 24h |
| Transformador aux | 1 unid | 48h |
| String box | 2 unid | 24h |
| Estructura soporte | 100m | 48h |

### 6.2 Gestión de Inventarios

#### 6.2.1 Sistema de Control
```
SOFTWARE DE GESTIÓN
- Código único por ítem
- Trazabilidad completa
- Alertas de stock mínimo
- Historial de consumo
- Proyección de necesidades
```

#### 6.2.2 Proceso de Reposición
1. Alerta automática stock mínimo
2. Generación orden de compra
3. Aprobación según monto
4. Gestión con proveedores
5. Recepción y verificación
6. Actualización de sistema

### 6.3 Proveedores Estratégicos

#### 6.3.1 Clasificación
- **Nivel A**: Fabricantes originales
- **Nivel B**: Distribuidores autorizados
- **Nivel C**: Proveedores alternativos

#### 6.3.2 Acuerdos de Servicio
- Tiempo de respuesta garantizado
- Stock dedicado
- Precios preferenciales
- Soporte técnico incluido
- Capacitación continua

---

## 7. CAPACITACIÓN TÉCNICA

### 7.1 Programa de Formación

#### 7.1.1 Niveles de Capacitación
```
NIVEL 1: OPERADOR LOCAL
- Operación básica
- Seguridad
- Mantenimiento diario
- Reporte de fallas
Duración: 40 horas

NIVEL 2: TÉCNICO MANTENIMIENTO
- Diagnóstico de fallas
- Mantenimiento preventivo
- Uso de instrumentos
- Protocolos de seguridad
Duración: 80 horas

NIVEL 3: ESPECIALISTA
- Configuración de equipos
- Análisis avanzado
- Gestión de repuestos
- Optimización
Duración: 120 horas
```

#### 7.1.2 Contenido Curricular
| Módulo | Horas | Teoría | Práctica |
|--------|-------|---------|----------|
| Fundamentos FV | 8 | 6 | 2 |
| Seguridad eléctrica | 16 | 8 | 8 |
| Operación sistemas | 24 | 12 | 12 |
| Mantenimiento | 32 | 16 | 16 |
| Troubleshooting | 24 | 8 | 16 |
| Gestión y reportes | 16 | 12 | 4 |

### 7.2 Recursos Didácticos

#### 7.2.1 Material de Apoyo
- Manuales técnicos en español
- Videos tutoriales
- Simuladores de fallas
- Check-lists laminados
- Aplicación móvil de consulta

#### 7.2.2 Infraestructura de Capacitación
- Aula con proyector
- Banco de pruebas
- Equipos de medición
- EPP para prácticas
- Sistema FV demostrativo

### 7.3 Certificación y Actualización

#### 7.3.1 Proceso de Certificación
1. Asistencia mínima 90%
2. Evaluación teórica (70%)
3. Evaluación práctica (80%)
4. Certificado con validez 2 años
5. Registro en base de datos

#### 7.3.2 Actualización Continua
- Webinars mensuales
- Boletines técnicos
- Casos de estudio
- Intercambio de experiencias
- Recertificación bianual

---

## 8. SOSTENIBILIDAD DEL MODELO

### 8.1 Sostenibilidad Técnica

#### 8.1.1 Estrategias de Largo Plazo
```
ASEGURAMIENTO TÉCNICO
1. Estandarización de equipos
2. Contratos de mantenimiento
3. Desarrollo de capacidades locales
4. Alianzas con universidades
5. I+D continuo
```

#### 8.1.2 Gestión del Envejecimiento
- Monitoreo de degradación
- Mantenimiento predictivo
- Reemplazo programado
- Actualización tecnológica
- Extensión de vida útil

### 8.2 Sostenibilidad Económica

#### 8.2.1 Modelo de Financiamiento
| Concepto | % del Total | Fuente |
|----------|-------------|---------|
| Inversión inicial | 100% | PERMER II |
| O&M años 1-5 | 60% | PERMER II |
| O&M años 6-10 | 40% | Tarifa + EDERSA |
| O&M años 11-25 | 100% | Tarifa + EDERSA |

#### 8.2.2 Optimización de Costos
```
REDUCCIÓN DE COSTOS O&M
- Mantenimiento predictivo: -30%
- Capacitación local: -25%
- Compras conjuntas: -20%
- Estandarización: -15%
- Monitoreo remoto: -40%
```

### 8.3 Sostenibilidad Social

#### 8.3.1 Involucramiento Comunitario
- Empleo local prioritario
- Programa de pasantías
- Visitas educativas
- Comunicación transparente
- Participación en decisiones

#### 8.3.2 Beneficios Sociales
```
IMPACTO SOCIAL MEDIBLE
- Empleos directos: 2 por MW
- Empleos indirectos: 5 por MW
- Capacitación técnica: 20 personas/año
- Mejora calidad de servicio: 99%
- Reducción de cortes: 90%
```

### 8.4 Sostenibilidad Ambiental

#### 8.4.1 Gestión Ambiental
| Aspecto | Medida | Indicador |
|---------|---------|-----------|
| Emisiones evitadas | 500 tCO2/año/MW | Certificados |
| Uso del suelo | Doble propósito | % aprovechado |
| Biodiversidad | Corredores fauna | Especies |
| Residuos | Reciclaje 95% | Kg reciclados |
| Agua | Sistema cerrado | Litros/MWh |

#### 8.4.2 Economía Circular
```
CICLO DE VIDA CIRCULAR
1. Diseño para reciclaje
2. Uso eficiente de recursos
3. Mantenimiento extendido
4. Reacondicionamiento
5. Reciclaje al final de vida
   - Silicio: 95% recuperable
   - Aluminio: 100% recuperable
   - Cobre: 98% recuperable
   - Vidrio: 95% recuperable
```

---

## 9. REPLICABILIDAD

### 9.1 Modelo de Replicación

#### 9.1.1 Condiciones para Replicabilidad
```
CRITERIOS DE SELECCIÓN DE SITIOS
Técnicos:
- Irradiación > 4.5 kWh/m²/día
- Espacio disponible > 2 Ha/MW
- Acceso a red MT < 5 km
- Demanda local > 50% generación

Económicos:
- TIR proyecto > 8%
- Costo evitado > 150 USD/MWh
- Financiamiento disponible

Sociales:
- Aceptación comunitaria
- Compromiso municipal
- Capacidad de gestión local
```

#### 9.1.2 Adaptación del Modelo
| Parámetro | Rango de Adaptación | Consideraciones |
|-----------|---------------------|-----------------|
| Potencia | 0.5 - 5 MW | Según demanda local |
| Tecnología | Fija/Seguidor | Análisis costo-beneficio |
| Almacenamiento | 0-4 horas | Según calidad de red |
| O&M | Local/Remoto | Según accesibilidad |

### 9.2 Herramientas de Replicación

#### 9.2.1 Kit de Replicación
```
DOCUMENTOS MAESTROS
1. Estudio de factibilidad tipo
2. Ingeniería básica estándar
3. Especificaciones técnicas
4. Modelo económico-financiero
5. Plan de implementación
6. Manual de O&M
7. Plan de capacitación
```

#### 9.2.2 Software de Diseño
- PVsyst: Dimensionamiento
- Homer: Optimización
- AutoCAD: Planos
- MS Project: Cronograma
- Modelo financiero Excel

### 9.3 Casos de Éxito

#### 9.3.1 Matriz de Replicación Regional
| Localidad | Potencia | Año | Resultado |
|-----------|----------|-----|-----------|
| Ing. Jacobacci | 1 MW | 2024 | Operativo |
| Los Menucos | 1 MW | 2024 | Operativo |
| Ramos Mexía | 0.5 MW | 2025 | Planificado |
| Comallo | 0.5 MW | 2025 | Planificado |
| Ñorquincó | 0.3 MW | 2026 | En estudio |

#### 9.3.2 Lecciones Aprendidas
```
FACTORES DE ÉXITO
1. Involucramiento temprano comunidad
2. Capacitación antes de puesta en marcha
3. Contratos O&M claros
4. Monitoreo desde día 1
5. Comunicación transparente
```

### 9.4 Escalamiento Regional

#### 9.4.1 Plan de Expansión 2024-2030
```
FASES DE EXPANSIÓN
Fase 1 (2024-2025): 5 MW
- Jacobacci y Menucos operativos
- Expansión a 4 localidades más

Fase 2 (2026-2027): 10 MW adicionales
- Corredor completo Línea Sur
- Integración con almacenamiento

Fase 3 (2028-2030): 20 MW adicionales
- Microrredes interconectadas
- Centro de control regional
```

#### 9.4.2 Impacto Proyectado
| Indicador | 2024 | 2027 | 2030 |
|-----------|------|------|------|
| Potencia instalada | 2 MW | 15 MW | 35 MW |
| Población beneficiada | 5,000 | 25,000 | 50,000 |
| Emisiones evitadas | 1,000 tCO2 | 7,500 tCO2 | 17,500 tCO2 |
| Empleos creados | 10 | 75 | 175 |

---

## 10. MEJORA CONTINUA

### 10.1 Sistema de Gestión de Calidad

#### 10.1.1 Ciclo PDCA Aplicado
```
PLAN
- Objetivos anuales de mejora
- KPIs específicos
- Recursos asignados
- Cronograma de actividades

DO
- Implementación de mejoras
- Capacitación del personal
- Registro de datos
- Seguimiento de indicadores

CHECK
- Auditorías trimestrales
- Análisis de desviaciones
- Benchmarking
- Satisfacción de usuarios

ACT
- Acciones correctivas
- Actualización de procedimientos
- Reconocimiento de logros
- Planificación siguiente ciclo
```

#### 10.1.2 Indicadores de Mejora
| KPI | Línea Base | Meta 2025 | Meta 2030 |
|-----|------------|-----------|-----------|
| Performance Ratio | 78% | 82% | 85% |
| Disponibilidad | 96% | 98% | 99% |
| MTTR (horas) | 24 | 12 | 6 |
| Costo O&M ($/MWh) | 25 | 20 | 15 |
| Satisfacción usuarios | 85% | 90% | 95% |

### 10.2 Innovación Tecnológica

#### 10.2.1 Áreas de Innovación
```
TECNOLOGÍAS EMERGENTES
1. Módulos bifaciales
   - Ganancia: +15-20%
   - Evaluación: 2025

2. Optimizadores DC
   - Ganancia: +5-8%
   - Piloto: 2024

3. IA para predicción
   - Beneficio: -20% mantenimiento
   - Implementación: 2025

4. Robots limpieza
   - Ahorro: 70% costo limpieza
   - Análisis: 2026
```

#### 10.2.2 Programa I+D
- Convenio con universidades
- Presupuesto: 2% de O&M
- Proyectos piloto anuales
- Transferencia tecnológica
- Publicaciones técnicas

### 10.3 Gestión del Conocimiento

#### 10.3.1 Base de Conocimiento
```
SISTEMA DE DOCUMENTACIÓN
├── Manuales técnicos
├── Procedimientos
├── Casos de estudio
├── Lecciones aprendidas
├── Mejores prácticas
├── Videos tutoriales
└── FAQ actualizado
```

#### 10.3.2 Comunidad de Práctica
- Foros técnicos mensuales
- Grupo WhatsApp operadores
- Newsletter trimestral
- Conferencia anual
- Premios a la innovación

### 10.4 Benchmarking y Mejores Prácticas

#### 10.4.1 Benchmarking Internacional
| Métrica | EDERSA | Chile | España | Objetivo |
|---------|---------|--------|---------|----------|
| PR promedio | 78% | 81% | 83% | 82% |
| Costo O&M | 25 $/MWh | 22 $/MWh | 18 $/MWh | 20 $/MWh |
| Disponibilidad | 96% | 97.5% | 98.5% | 98% |
| Degradación anual | 0.7% | 0.6% | 0.5% | 0.6% |

#### 10.4.2 Adopción de Mejores Prácticas
1. **Mantenimiento predictivo con IA**
   - Reducción de fallas: 40%
   - Implementación: Q2 2025

2. **Gestión de vegetación optimizada**
   - Pastoreo controlado
   - Beneficio dual: limpieza + ingresos

3. **Almacenamiento distribuido**
   - Baterías en puntos críticos
   - Mejora de calidad: 99.9%

4. **Certificación de operadores**
   - Programa regional
   - Estándar internacional

---

## CONCLUSIONES

### Factores Críticos de Éxito
1. **Capacitación continua del personal local**
2. **Mantenimiento preventivo riguroso**
3. **Monitoreo en tiempo real efectivo**
4. **Gestión proactiva de repuestos**
5. **Mejora continua basada en datos**

### Visión a Futuro
La implementación exitosa de estas guías operativas garantizará no solo la sostenibilidad técnica y económica de los proyectos actuales, sino que establecerá un modelo replicable y escalable para la expansión de la generación distribuida en toda la región, contribuyendo significativamente a los objetivos de desarrollo sostenible y acceso universal a energía limpia.

### Próximos Pasos
1. Validación de procedimientos en campo
2. Capacitación del personal inicial
3. Implementación del sistema de monitoreo
4. Establecimiento de métricas base
5. Inicio del ciclo de mejora continua

---

**Documento preparado por:**
- Equipo Técnico EDERSA
- Consultores Especialistas en O&M Solar
- Revisión: Gerencia de Planificación

**Fecha:** Diciembre 2024
**Versión:** 1.0
**Próxima revisión:** Junio 2025