# INSTRUCCIONES PARA EJECUTAR EL DASHBOARD

## Instalación de dependencias (PRIMER PASO)

```bash
cd /Users/maxkeczeli/Proyects/estudio-gd-linea-sur
pip install dash dash-bootstrap-components plotly pandas networkx folium
```

## Dashboard Multi-página (NUEVO - RECOMENDADO)

Para ejecutar el nuevo dashboard con múltiples páginas organizadas por fases:

```bash
cd /Users/maxkeczeli/Proyects/estudio-gd-linea-sur
python3 dashboard/app_multipagina.py
```

Luego abrir en el navegador: http://localhost:8050

### Páginas disponibles:
- **Inicio**: http://localhost:8050/
- **Fase 2 - Topología**: http://localhost:8050/fase2-topologia
- **Fase 3 - Procesamiento de Datos**: http://localhost:8050/fase3-datos
- Más fases próximamente...

## Dashboard Original (versión anterior)

Si desea ejecutar la versión anterior de una sola página:

```bash
python3 dashboard/app.py
```

## Notas importantes:
- El dashboard multipágina es la versión actualizada con mejor organización
- Incluye barra de navegación y sidebar con progreso del proyecto
- Las visualizaciones de topología están en la página de Fase 2