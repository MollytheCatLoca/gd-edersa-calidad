# Estudio de Generación Distribuida - Línea Sur Río Negro

## 🎯 Resumen Ejecutivo

Análisis técnico-económico integral para optimizar el sistema de transmisión de 33 kV de la Línea Sur de Río Negro mediante Generación Distribuida (GD) fotovoltaica con almacenamiento (BESS).

### 🔴 Problema Crítico
- **270 km** de línea radial con caídas de tensión del **76%** (0.24 pu)
- **100%** de mediciones fuera de límites regulatorios
- **164 horas/año** con colapso total de voltaje
- Capacidad **NULA** para nuevas cargas

### ✅ Solución Propuesta
Instalación estratégica de sistemas FV+BESS en puntos críticos:

| Ubicación | FV (MW) | BESS (MWh) | TIR | Beneficio Principal |
|-----------|---------|------------|-----|---------------------|
| **Los Menucos** | 3.0 | 2.0 | 22.9% | Elimina generación diesel |
| **Jacobacci** | 1.0 | 1.0 | 24.8% | Mayor demanda post-Menucos |

## 🚀 Inicio Rápido

```bash
# Clonar repositorio
git clone [url-repo]
cd estudio-gd-linea-sur

# Instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar dashboard interactivo
cd dashboard
python app_multipagina.py
```

Abrir http://localhost:8050 en el navegador

## 📊 Dashboard Interactivo

El proyecto incluye un dashboard completo con análisis por fases:

- **Fase 1**: Comprensión del sistema eléctrico actual
- **Fase 2**: Modelado topológico de la red
- **Fase 3**: Procesamiento de datos históricos (210,156 registros)
- **Fase 4**: Laboratorio solar + BESS con simulaciones

## 📁 Estructura del Proyecto

```
estudio-gd-linea-sur/
├── src/                    # Código fuente principal
│   ├── topology/          # Modelado de red
│   ├── solar/             # Simulación FV
│   └── bess/              # Modelos de baterías
├── dashboard/              # Aplicación web interactiva
├── data/                   # Datos procesados y análisis
├── docs/                   # Documentación completa
│   ├── CLAUDE.md          # Guía técnica detallada
│   ├── technical_analysis/ # Análisis de voltaje y pérdidas
│   └── economic_analysis/  # Evaluaciones financieras
├── scripts/                # Scripts de análisis
└── tests/                  # Tests y resultados

```

## 💡 Resultados Clave

### Los Menucos (Punta de línea)
- **Inversión**: USD 3.06M (3MW FV + 2MWh BESS)
- **Beneficios año 1**: USD 818,590
- **Payback**: 4.7 años
- **Mejora voltaje**: 0.237 → 0.273 pu (+15%)

### Jacobacci (Nodo intermedio)
- **Demanda**: 0.507 MW promedio (máx 1.17 MW)
- **Sensibilidad dV/dP**: +0.0115 pu/MW
- **ENS actual**: 117.55 MWh/año

## 📈 Análisis Disponibles

### Técnicos
- Flujos de potencia DC con pérdidas
- Análisis de sensibilidad dV/dP por nodo
- Curvas de duración y patrones temporales
- Simulación horaria con FV+BESS

### Económicos
- VAN, TIR, LCOE por escenario
- Análisis de sensibilidad
- Reducción de pérdidas técnicas
- Valorización de mejora de calidad

## 🛠️ Herramientas Principales

- **Python 3.12+** con pandas, numpy, scipy
- **Dash/Plotly** para visualización interactiva
- **PandaPower** para análisis de red (opcional)
- **XGBoost** para predicciones ML

## 📚 Documentación

- [Guía Técnica Completa](docs/CLAUDE.md) - Metodología de 9 fases
- [Análisis Económico Los Menucos](docs/economic_analysis/los_menucos_analisis_economico.md)
- [Datos Técnicos Jacobacci](docs/technical_analysis/jacobacci_technical_data.md)
- [Impacto Mejora de Voltaje](docs/technical_analysis/analisis_mejora_voltaje_los_menucos.md)

## 🔍 Datos Procesados

- **Período**: Enero 2024 - Abril 2025 (15 meses)
- **Resolución**: 15 minutos
- **Estaciones**: Pilcaniyeu, Jacobacci, Maquinchao, Los Menucos
- **Calidad**: 100% cobertura temporal, validación completa

## 🎯 Próximos Pasos

1. **Ingeniería de detalle** para Los Menucos
2. **Gestión regulatoria** con CAMMESA
3. **Estructuración financiera** del proyecto
4. **Licitación EPC** y construcción

## 👥 Contribuir

1. Fork el repositorio
2. Crear branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto es parte del estudio técnico para EPEN (Ente Provincial de Energía del Neuquén).

---

**Contacto**: [Información de contacto]  
**Última actualización**: Julio 2025