# GD-EDERSA-CALIDAD
## Análisis de Calidad de Servicio y Oportunidades de Generación Distribuida

### 🎯 Objetivo
Identificar ubicaciones óptimas para instalación de Generación Distribuida (GD) en la red EDERSA, basándose en el análisis de calidad de servicio de 14,025 transformadores.

### 📊 Datos Disponibles
- **Inventario completo** de transformadores EDERSA
- **Resultados de calidad** (Correcta/Penalizada/Fallida)
- **Ubicación geográfica** de cada transformador
- **Capacidad instalada** y usuarios por transformador

### 🚀 Inicio Rápido

```bash
# Activar entorno
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar dashboard
cd dashboard
python app_edersa.py
```

Abrir http://localhost:8051 en el navegador

### 📁 Estructura del Proyecto

```
gd-edersa-calidad/
├── src/
│   ├── inventory/        # Manejo de inventario de transformadores
│   ├── quality/          # Análisis de calidad de servicio
│   ├── clustering/       # Agrupación geográfica y por criticidad
│   └── optimization/     # Optimización de ubicaciones GD
├── data/
│   ├── raw/             # Excel original EDERSA
│   └── processed/       # Datos procesados
├── dashboard/           # Visualización interactiva
├── docs/               # Documentación
└── tests/              # Tests unitarios
```

### 🔍 Metodología

1. **Análisis de Inventario**: Procesamiento del Excel con 14,025 transformadores
2. **Evaluación de Calidad**: Identificación de 2,731 transformadores problemáticos
3. **Clustering Geográfico**: Agrupación por densidad y criticidad
4. **Priorización**: Ranking de zonas por impacto en usuarios
5. **Dimensionamiento GD**: Estimación preliminar sin series temporales

### 📈 Resultados Preliminares

- **34% de transformadores** con problemas de calidad
- **~180,000 usuarios afectados** (estimado)
- **14 sucursales** analizadas
- **133 alimentadores** evaluados

### 🛠️ Próximos Pasos

1. Solicitar **series temporales** de demanda
2. Obtener **topología de red** detallada
3. Integrar **costos de penalizaciones**
4. Realizar **simulaciones** de impacto GD

### 📚 Documentación Técnica

- [Análisis de Datos](docs/analysis/)
- [Metodología](docs/methodology/)
- [API Reference](docs/api/)

### 👥 Equipo
- Análisis técnico: [Tu nombre]
- Framework base: Proyecto Línea Sur RN

### 📝 Licencia
Proyecto para EDERSA - Ente Distribuidor de Electricidad de Río Negro S.A.

---

**Última actualización**: $(date +"%B %Y")
