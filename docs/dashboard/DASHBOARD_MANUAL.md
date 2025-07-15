# MANUAL DE USUARIO - DASHBOARD EDERSA

## 📊 Dashboard de Análisis de Calidad y Oportunidades GD

### 🚀 Inicio Rápido

#### Requisitos
- Python 3.10 o superior
- Navegador web moderno (Chrome, Firefox, Safari)
- 4GB RAM mínimo recomendado

#### Instalación y Ejecución
```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias (si es primera vez)
pip install -r requirements.txt

# Ejecutar dashboard
python dashboard/app_multipagina.py
```

#### Acceso
Abrir navegador en: **http://127.0.0.1:8050/**

---

## 🗺️ Navegación General

### Barra Lateral
- **Logo EDERSA**: Click para volver a inicio
- **Menú de páginas**: 6 opciones disponibles
- **Filtros globales**: Aplicables a todas las páginas
  - Sucursal
  - Estado de calidad
  - Nivel de vulnerabilidad

### Características Comunes
- **Responsive**: Se adapta a diferentes tamaños de pantalla
- **Interactivo**: Todos los gráficos permiten zoom, pan y hover
- **Exportable**: Botón de cámara en cada gráfico para guardar imagen
- **Actualizaciones**: Los filtros actualizan todas las visualizaciones

---

## 📄 Páginas del Dashboard

### 1. 🏠 HOME - Vista General

#### Propósito
Proporciona una visión ejecutiva del estado de la red EDERSA.

#### Componentes
1. **Métricas Principales** (parte superior)
   - Total transformadores
   - Usuarios totales
   - Capacidad instalada (MVA)
   - Tasa de problemas (%)
   - Transformadores críticos
   - Alimentadores totales

2. **Gráfico de Torta - Distribución de Calidad**
   - Verde: Correcta
   - Naranja: Penalizada
   - Rojo: Fallida
   - Click en leyenda para ocultar/mostrar

3. **Gráfico de Barras - Vulnerabilidad por Sucursal**
   - Barras apiladas por nivel de vulnerabilidad
   - Hover para ver detalles
   - Click para filtrar

4. **Tabla - Top 10 Alimentadores Críticos**
   - Ordenable por cualquier columna
   - Muestra score de criticidad
   - Usuarios afectados y tasa de falla

#### Uso Típico
- Revisión diaria del estado general
- Identificación rápida de problemas
- Presentaciones ejecutivas

---

### 2. 📦 INVENTARIO - Análisis Detallado

#### Propósito
Exploración profunda del inventario de transformadores por zona.

#### Componentes
1. **Selector de Vista**
   - Por Sucursal
   - Por Alimentador
   - Por Localidad

2. **Mapa Interactivo**
   - Puntos coloreados por estado
   - Tamaño por potencia/usuarios
   - Zoom con scroll o botones
   - Click para información detallada

3. **Gráficos de Distribución**
   - Capacidad instalada por zona
   - Distribución de usuarios
   - Estados de calidad

4. **Tabla Detallada**
   - Exportable a Excel
   - Búsqueda por texto
   - Paginación automática

#### Funcionalidades Especiales
- **Filtro por rango de potencia**: Slider para kVA
- **Búsqueda de transformador**: Por código
- **Agrupación dinámica**: Cambia según nivel de zoom

#### Uso Típico
- Planificación de mantenimiento
- Análisis de capacidad por zona
- Identificación de transformadores específicos

---

### 3. 🌐 TOPOLOGÍA - Análisis de Red

#### Propósito
Visualizar la estructura topológica de la red usando MST (Minimum Spanning Tree).

#### Componentes
1. **Selector de Alimentador**
   - Dropdown con contador de transformadores
   - Solo alimentadores con >5 transformadores

2. **Visualización de Red**
   - **Vista Geográfica**: Ubicaciones reales con conexiones
   - **Vista Jerárquica**: Árbol de distribución
   - **Vista Radial**: Distribución desde subestación

3. **Panel de Información**
   - Click en nodo para ver detalles
   - Código, potencia, usuarios
   - Número de saltos desde subestación

4. **Gráficos de Análisis**
   - Distribución de saltos
   - kVA aguas abajo por nodo

#### Interpretación
- **Líneas grises**: Conexiones eléctricas estimadas
- **Cuadrado azul**: Subestación (estimada)
- **Círculos**: Transformadores (color = estado)
- **Tamaño**: Proporcional a potencia

#### Uso Típico
- Análisis de flujo de potencia
- Identificación de cuellos de botella
- Planificación de expansión

---

### 4. ⚡ ANÁLISIS ELÉCTRICO

#### Propósito
Evaluar características eléctricas y modos de falla potenciales.

#### Componentes
1. **Selector de Variable**
   - Impedancia
   - Caída de Tensión
   - Modos de Falla

2. **Mapa de Calor**
   - Gradiente de colores por variable
   - Verde = bueno, Rojo = problemático
   - Actualización según selección

3. **Estadísticas de Zona**
   - Media, máxima, mínima
   - Porcentaje fuera de límites
   - Comparación con normas

4. **Gráficos de Análisis**
   - Histograma de distribución
   - Correlación con calidad
   - Box plots comparativos

#### Panel de Modos de Falla
- **🔥 Térmico**: Sobrecalentamiento
- **⚡ Dieléctrico**: Fallas de aislamiento
- Tabla por rango de potencia
- Recomendaciones de mantenimiento

#### Interpretación
- **Caída >5%**: Fuera de norma
- **Impedancia alta**: Mayor pérdida
- **Modo térmico**: Revisar carga
- **Modo dieléctrico**: Revisar protecciones

#### Uso Típico
- Diagnóstico de problemas
- Priorización de mantenimiento
- Justificación técnica para GD

---

### 5. 🛡️ VULNERABILIDAD

#### Propósito
Evaluación integral de vulnerabilidad combinando múltiples factores.

#### Componentes
1. **Métricas de Vulnerabilidad**
   - Contadores por nivel
   - Usuarios en riesgo
   - Índice promedio (0-1)

2. **Filtros Avanzados**
   - Por nivel de vulnerabilidad
   - Slider de índice (0-1)
   - Combinables con filtros globales

3. **Mapa de Vulnerabilidad**
   - Escala de colores continua
   - Tamaño = usuarios afectados
   - Hover para detalles

4. **Análisis Detallado**
   - Factores contribuyentes (%)
   - Correlación con calidad
   - Comparación por sucursal

5. **Top 10 Transformadores Críticos**
   - Tabla interactiva
   - Índice de criticidad
   - Información completa

#### Niveles de Vulnerabilidad
- **🔴 Crítica**: Acción inmediata
- **🟠 Alta**: Prioridad alta
- **🟡 Media**: Monitoreo regular
- **🟢 Baja**: Operación normal
- **🔵 Mínima**: Sin problemas

#### Uso Típico
- Priorización de inversiones
- Planes de contingencia
- Reportes de riesgo

---

### 6. 🎯 CLUSTERING - Zonas para GD

#### Propósito
Identificar agrupaciones óptimas de transformadores para instalación de GD.

#### Componentes
1. **Parámetros de Clustering**
   - **Método**: DBSCAN o K-Means
   - **Radio** (DBSCAN): 0.1-5 km
   - **Clusters** (K-Means): 3-20
   - **Filtro de estado**: Todos/Problemáticos/Fallidos

2. **Botón "Ejecutar Clustering"**
   - Procesa con parámetros seleccionados
   - Actualiza todas las visualizaciones

3. **Mapa de Clusters**
   - Colores distintos por cluster
   - Centroides marcados en rojo
   - Click para información

4. **Panel de Recomendación GD**
   - Capacidad sugerida (MW)
   - Configuración (Solar+BESS)
   - Beneficios esperados
   - Área requerida

5. **Análisis Comparativo**
   - Características por cluster (radar)
   - Priorización por impacto
   - Tabla resumen detallada

#### Interpretación de Resultados
- **Prioridad = Usuarios × Tasa Falla**
- **GD Recomendada = 30% capacidad cluster**
- **Clusters densos = Mayor viabilidad**

#### Uso Típico
- Identificación de sitios para GD
- Dimensionamiento preliminar
- Análisis costo-beneficio
- Planificación de proyectos piloto

---

## 💡 Tips y Mejores Prácticas

### Navegación Eficiente
1. Use filtros globales para mantener contexto
2. Ctrl+Click en gráficos para comparar
3. Doble click en gráfico para resetear zoom
4. Exporte imágenes para reportes

### Análisis Recomendado
1. **Inicio**: Home para vista general
2. **Profundizar**: Inventario por zona problemática
3. **Diagnóstico**: Análisis eléctrico de la zona
4. **Priorización**: Vulnerabilidad para ranking
5. **Solución**: Clustering para ubicar GD

### Performance
- Filtrar reduce datos procesados
- Cerrar pestañas no usadas
- Refrescar si hay lag
- Cache automático de 10 min

### Exportación de Datos
- Click derecho → Guardar imagen
- Tablas: Copiar/pegar a Excel
- Screenshots para presentaciones
- Print PDF desde navegador

---

## 🔧 Solución de Problemas

### Dashboard no carga
1. Verificar que el servidor esté corriendo
2. Revisar consola por errores
3. Limpiar caché del navegador
4. Reiniciar servidor

### Gráficos vacíos
1. Verificar filtros (pueden estar muy restrictivos)
2. Comprobar que hay datos para la selección
3. Revisar mensajes de error en gráfico

### Lentitud
1. Reducir cantidad de datos con filtros
2. Usar Chrome/Firefox actualizados
3. Cerrar otras aplicaciones
4. Considerar más RAM

### Errores comunes
- **"No data"**: Ajustar filtros
- **"Server error"**: Reiniciar dashboard
- **Página en blanco**: Verificar URL

---

## 📞 Soporte

### Logs y Debugging
```bash
# Ver logs en tiempo real
tail -f dashboard.log

# Modo debug (más información)
python dashboard/app_multipagina.py --debug
```

### Contacto
- Documentación técnica: `/docs/`
- Issues: Reportar en sistema de tickets
- Actualizaciones: Verificar repositorio

---

## 🔄 Actualizaciones Frecuentes

### Datos
- Los datos se cargan al iniciar
- No hay actualización automática
- Reiniciar para datos nuevos

### Nuevas Funcionalidades
- Verificar changelog
- Actualizar dependencias
- Revisar documentación

---

*Manual actualizado: 15 de Julio 2025*  
*Versión Dashboard: 1.0*