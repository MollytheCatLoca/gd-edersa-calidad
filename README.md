# GD-EDERSA-CALIDAD
## Análisis de Calidad de Servicio y Oportunidades de Generación Distribuida

### 🎯 Objetivo
Identificar ubicaciones óptimas para instalación de Generación Distribuida (GD) en la red EDERSA, basándose en el análisis de calidad de servicio de 14,025 transformadores.

### 📊 Estado del Proyecto

**Progreso**: 40% completado (Fases 0 y 1 finalizadas)

```
✅ Fase 0: Comprensión de Topología de Red - COMPLETADA
✅ Fase 1: Análisis de Inventario y Dashboard - COMPLETADA
🔄 Fase 2: Clustering y Priorización - EN PLANIFICACIÓN
⏳ Fase 3: Dimensionamiento Preliminar GD
⏳ Fase 4: Evaluación Económica y Recomendaciones
```

### 🚀 Inicio Rápido

```bash
# Activar entorno
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar dashboard avanzado
python dashboard/app_multipagina.py
```

Abrir http://127.0.0.1:8050/ en el navegador

### 📁 Estructura del Proyecto

```
gd-edersa-calidad/
├── scripts/
│   ├── preprocessing/     # Scripts de procesamiento inicial
│   ├── network_analysis/  # Análisis de topología de red
│   ├── electrical_analysis/ # Análisis eléctrico avanzado
│   └── clustering/        # Clustering y priorización (próximo)
├── data/
│   ├── raw/              # Excel original EDERSA
│   ├── processed/        # Datos procesados y enriquecidos
│   └── *.db              # Bases de datos SQLite
├── dashboard/            # Dashboard multi-página
│   ├── pages/           # 6 páginas interactivas
│   ├── components/      # Componentes reutilizables
│   └── utils/           # Utilidades y cache
├── reports/             # Reportes y visualizaciones
├── docs/               # Documentación completa
│   └── phases/         # Documentación por fases
└── tests/              # Tests unitarios
```

### 🔍 Metodología Implementada

1. **Análisis de Inventario** ✅: Procesamiento del Excel con 14,025 transformadores
2. **Evaluación de Calidad** ✅: Identificación de 1,236 transformadores problemáticos (45.9%)
3. **Análisis Topológico** ✅: Reconstrucción MST y cálculo de distancias eléctricas
4. **Análisis Eléctrico** ✅: Impedancias, caídas de tensión y modos de falla
5. **Clustering Preliminar** ✅: DBSCAN/K-Means con identificación de zonas GD
6. **Dashboard Interactivo** ✅: 6 páginas con visualizaciones avanzadas

### 📈 Resultados Clave (Fases 0-1)

#### Métricas Principales
- **2,690 transformadores** analizados (con coordenadas)
- **45.9% con problemas** de calidad (1,236 transformadores)
- **158,476 usuarios** totales en la muestra
- **128 alimentadores** caracterizados completamente
- **240 hotspots** de problemas identificados

#### Hallazgos Críticos
- **423 transformadores** con caída de tensión >5%
- **312 transformadores** con riesgo térmico alto
- **Top 10 alimentadores** críticos priorizados
- **120.5 MW** de capacidad GD estimada total
- **58,745 usuarios** potencialmente beneficiados

### 🛠️ Próximos Pasos (Fase 2)

1. **Refinamiento de clustering** con parámetros optimizados
2. **Análisis detallado** de cada cluster prioritario  
3. **Dimensionamiento específico** de GD por zona
4. **Simulación de impacto** en calidad de servicio
5. **Evaluación económica** preliminar

### 🖥️ Dashboard Interactivo

El proyecto incluye un dashboard completo con 6 páginas:

1. **Home**: Vista general y métricas principales
2. **Inventario**: Análisis detallado por sucursal/alimentador
3. **Topología**: Visualización MST y análisis de red
4. **Análisis Eléctrico**: Impedancias, caídas de tensión, modos de falla
5. **Vulnerabilidad**: Mapas de calor y priorización de riesgo
6. **Clustering**: Identificación de zonas óptimas para GD

### 📚 Documentación Completa

- [CLAUDE.md](./CLAUDE.md) - Documentación técnica principal
- [Fase 0 - Topología de Red](./docs/phases/FASE0_COMPLETA.md)
- [Fase 1 - Análisis y Dashboard](./docs/phases/FASE1_COMPLETA.md)
- [Fase 2 - Plan de Clustering](./docs/phases/FASE2_PLAN_DETALLADO.md)
- [Accesos Rápidos a Datos](./docs/ACCESOS_DATOS_CLAUDE.md)

### 👥 Equipo
- Análisis técnico: Equipo de Ingeniería
- Framework base: Adaptado de Proyecto Línea Sur RN
- Herramienta: Claude Code Assistant

### 📝 Licencia
Proyecto para EDERSA - Ente Distribuidor de Electricidad de Río Negro S.A.

---

**Última actualización**: 15 de Julio 2025
