# INSTRUCCIONES DE PROCESAMIENTO DE DATOS - FASE 3

## Enfoque Iterativo

Este proyecto utiliza un enfoque iterativo para procesar los datos:
1. Procesar UNA estación primero
2. Verificar que todo funcione correctamente
3. Procesar las demás estaciones gradualmente

## Paso 1: Procesar Primera Estación (Pilcaniyeu)

```bash
cd /Users/maxkeczeli/Proyects/estudio-gd-linea-sur
python3 scripts/process_one_station.py --station Pilcaniyeu
```

Este comando:
- Carga todos los archivos Excel de Pilcaniyeu (2024-2025)
- Limpia y valida los datos
- Genera archivos en `data/processed/`
- Tarda aproximadamente 1-2 minutos

## Paso 2: Verificar en Dashboard

```bash
# En otra terminal:
python3 dashboard/app_multipagina.py
```

Luego abrir en navegador: http://localhost:8050/fase3-datos

Verificar:
- ✓ Métricas de calidad visibles
- ✓ Gráfico de perfiles temporales funciona
- ✓ Tabla de calidad muestra datos

## Paso 3: Procesar Otras Estaciones (Opcional)

Si todo funciona bien con Pilcaniyeu:

```bash
# Procesar Jacobacci
python3 scripts/process_one_station.py --station Jacobacci

# Procesar Maquinchao
python3 scripts/process_one_station.py --station Maquinchao

# Procesar Los Menucos
python3 scripts/process_one_station.py --station "Los Menucos"
```

## Archivos Generados

Después del procesamiento encontrará en `data/processed/`:

- `consolidated_data.parquet` - Base de datos principal
- `consolidated_data_sample.csv` - Muestra de 1000 registros
- `quality_metrics.json` - Métricas de calidad por estación
- `temporal_analysis.json` - Análisis de patrones temporales

## Opciones Adicionales

### Procesar solo un año específico:
```bash
python3 scripts/process_one_station.py --station Pilcaniyeu --year 2024
```

### Ver ayuda:
```bash
python3 scripts/process_one_station.py --help
```

## Solución de Problemas

### "No se encontraron datos"
- Verificar que existan archivos en `data/Registros Línea Sur/[Estación]*/`
- Los nombres de carpetas deben coincidir (ej: "Pilcaniyeu2024", "Menucos2024")

### "Error loading Excel file"
- Algunos archivos pueden estar corruptos
- El script continuará con los demás archivos
- Revisar el log para identificar archivos problemáticos

### Dashboard no muestra datos
- Verificar que exista `data/processed/consolidated_data.parquet`
- Reiniciar el dashboard después de procesar
- Verificar la consola del navegador para errores

## Notas Importantes

1. **Procesamiento Incremental**: Cada vez que procesa una estación, se actualiza el archivo consolidado
2. **Sin duplicados**: Si procesa la misma estación dos veces, se reemplazan los datos anteriores
3. **Datos faltantes**: Es normal que algunos meses no tengan datos
4. **Tiempo estimado**: 
   - 1 estación: ~1-2 minutos
   - Todas las estaciones: ~5-10 minutos

## Flujo Recomendado

1. Empezar con Pilcaniyeu (tiene más datos)
2. Verificar dashboard
3. Si todo OK, procesar Jacobacci (segunda más importante)
4. Continuar con las demás según necesidad

¡El procesamiento es seguro y puede interrumpirse en cualquier momento!