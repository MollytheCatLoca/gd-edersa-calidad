#!/usr/bin/env python3
"""
03_create_aggregations.py - Creación de agregaciones para análisis

Cuarto paso del pipeline de preprocesamiento.
- Agrega datos por sucursal y localidad
- Calcula métricas consolidadas
- Identifica zonas críticas
- Prepara datos para visualización

Autor: Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Configurar paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorios necesarios
LOGS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Configurar logging
log_file = LOGS_DIR / f"03_aggregations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def aggregate_by_location(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """
    Agrega transformadores por columna de agrupación (sucursal o localidad).
    """
    logger.info(f"  Agregando por {group_col}...")
    
    # Filtrar registros con valor válido en grupo
    df_valid = df[df[group_col].notna()].copy()
    
    # Función para calcular distribución de resultados
    def get_result_distribution(results):
        dist = results.value_counts(normalize=True)
        return {
            'pct_correcta': dist.get('Correcta', 0) * 100,
            'pct_penalizada': dist.get('Penalizada', 0) * 100,
            'pct_fallida': dist.get('Fallida', 0) * 100
        }
    
    # Agregaciones básicas
    agg_dict = {
        'Codigoct': 'count',  # Total transformadores
        'Potencia': ['sum', 'mean', 'median'],
        'Q_Usuarios': ['sum', 'mean'],
        'quality_score': ['mean', 'std'],
        'criticidad_compuesta': ['mean', 'max'],
        'prioridad_gd': ['mean', 'max'],
        'num_circuitos': 'sum',
        'potencia_imputada': 'sum'
    }
    
    # Agregar columnas opcionales si existen
    if 'usuarios_por_kva' in df.columns:
        agg_dict['usuarios_por_kva'] = 'mean'
    if 'factor_utilizacion_estimado' in df.columns:
        agg_dict['factor_utilizacion_estimado'] = 'mean'
    
    # Realizar agregación
    df_agg = df_valid.groupby(group_col).agg(agg_dict)
    
    # Aplanar columnas multi-nivel
    df_agg.columns = ['_'.join(col).strip() if col[1] else col[0] 
                       for col in df_agg.columns.values]
    
    # Renombrar columnas clave
    df_agg.rename(columns={
        'Codigoct_count': 'num_transformadores',
        'Potencia_sum': 'potencia_total_kva',
        'Potencia_mean': 'potencia_promedio_kva',
        'Potencia_median': 'potencia_mediana_kva',
        'Q_Usuarios_sum': 'usuarios_totales',
        'Q_Usuarios_mean': 'usuarios_promedio',
        'quality_score_mean': 'quality_score_promedio',
        'quality_score_std': 'quality_score_desviacion',
        'criticidad_compuesta_mean': 'criticidad_promedio',
        'criticidad_compuesta_max': 'criticidad_maxima',
        'prioridad_gd_mean': 'prioridad_gd_promedio',
        'prioridad_gd_max': 'prioridad_gd_maxima',
        'num_circuitos_sum': 'circuitos_totales',
        'potencia_imputada_sum': 'transformadores_imputados'
    }, inplace=True)
    
    # Agregar distribución de resultados
    result_dist = df_valid.groupby(group_col)['Resultado'].apply(
        lambda x: pd.Series(get_result_distribution(x))
    ).reset_index()
    
    # Agregar conteo por tipo de resultado
    result_counts = df_valid.groupby([group_col, 'Resultado']).size().unstack(fill_value=0)
    result_counts.columns = [f'num_{col.lower()}' for col in result_counts.columns]
    
    # Combinar todos los dataframes
    df_agg = df_agg.reset_index()
    df_agg = df_agg.merge(result_dist, on=group_col, how='left')
    df_agg = df_agg.merge(result_counts.reset_index(), on=group_col, how='left')
    
    # Rellenar valores NaN en porcentajes con 0
    for col in ['pct_correcta', 'pct_penalizada', 'pct_fallida']:
        if col in df_agg.columns:
            df_agg[col] = df_agg[col].fillna(0)
    
    # Calcular índice de calidad compuesto
    df_agg['indice_calidad'] = (
        df_agg.get('pct_correcta', 0) * 1.0 + 
        df_agg.get('pct_penalizada', 0) * 0.5 + 
        df_agg.get('pct_fallida', 0) * 0.0
    ) / 100
    
    # Agregar información geográfica si es por localidad
    if group_col == 'N_Localida' and 'zona_geografica' in df.columns:
        zona_info = df_valid.groupby(group_col)['zona_geografica'].agg(
            lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Sin datos'
        )
        df_agg = df_agg.merge(zona_info.reset_index(), on=group_col, how='left')
    
    # Categorizar por tamaño
    df_agg['categoria_tamano'] = pd.cut(
        df_agg['num_transformadores'],
        bins=[0, 10, 50, 100, 500, 10000],
        labels=['Muy Pequeña', 'Pequeña', 'Mediana', 'Grande', 'Muy Grande']
    )
    
    # Ordenar por criticidad
    df_agg = df_agg.sort_values('criticidad_promedio', ascending=False)
    
    return df_agg


def identify_critical_zones(df_sucursal: pd.DataFrame, df_localidad: pd.DataFrame) -> Dict:
    """
    Identifica zonas críticas basándose en múltiples criterios.
    """
    logger.info("\nIdentificando zonas críticas...")
    
    critical_zones = {
        'sucursales': {},
        'localidades': {},
        'summary': {}
    }
    
    # Criterios para sucursales críticas
    # 1. Por índice de calidad
    sucursales_baja_calidad = df_sucursal[
        df_sucursal['indice_calidad'] < 0.7
    ].sort_values('indice_calidad')
    
    # 2. Por criticidad promedio
    sucursales_alta_criticidad = df_sucursal[
        df_sucursal['criticidad_promedio'] > 0.5
    ].sort_values('criticidad_promedio', ascending=False)
    
    # 3. Por impacto (usuarios * criticidad)
    df_sucursal['impacto_usuarios'] = (
        df_sucursal['usuarios_totales'] * df_sucursal['criticidad_promedio']
    )
    sucursales_alto_impacto = df_sucursal.nlargest(10, 'impacto_usuarios')
    
    # Verificar columnas disponibles
    cols_baja_calidad = ['N_Sucursal', 'num_transformadores', 'indice_calidad', 'usuarios_totales']
    if 'pct_fallida' in sucursales_baja_calidad.columns:
        cols_baja_calidad.append('pct_fallida')
    
    critical_zones['sucursales'] = {
        'baja_calidad': sucursales_baja_calidad[cols_baja_calidad].head(10).to_dict('records'),
        
        'alta_criticidad': sucursales_alta_criticidad[
            ['N_Sucursal', 'criticidad_promedio', 'num_transformadores',
             'potencia_total_kva', 'usuarios_totales']
        ].head(10).to_dict('records'),
        
        'alto_impacto': sucursales_alto_impacto[
            ['N_Sucursal', 'impacto_usuarios', 'usuarios_totales',
             'criticidad_promedio', 'num_transformadores']
        ].to_dict('records')
    }
    
    # Similar para localidades
    localidades_alta_criticidad = df_localidad[
        df_localidad['criticidad_promedio'] > 0.5
    ].sort_values('criticidad_promedio', ascending=False)
    
    df_localidad['impacto_usuarios'] = (
        df_localidad['usuarios_totales'] * df_localidad['criticidad_promedio']
    )
    localidades_alto_impacto = df_localidad.nlargest(10, 'impacto_usuarios')
    
    critical_zones['localidades'] = {
        'alta_criticidad': localidades_alta_criticidad[
            ['N_Localida', 'criticidad_promedio', 'num_transformadores',
             'usuarios_totales']
        ].head(10).to_dict('records'),
        
        'alto_impacto': localidades_alto_impacto[
            ['N_Localida', 'impacto_usuarios', 'usuarios_totales',
             'num_transformadores']
        ].to_dict('records')
    }
    
    # Resumen general
    critical_zones['summary'] = {
        'sucursales_criticas': len(sucursales_alta_criticidad),
        'localidades_criticas': len(localidades_alta_criticidad),
        'transformadores_en_zonas_criticas': sucursales_alta_criticidad['num_transformadores'].sum(),
        'usuarios_afectados': sucursales_alta_criticidad['usuarios_totales'].sum(),
        'potencia_en_riesgo_mva': sucursales_alta_criticidad['potencia_total_kva'].sum() / 1000
    }
    
    return critical_zones


def create_geographic_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea resumen por zona geográfica.
    """
    if 'zona_geografica' not in df.columns:
        logger.warning("  No hay información de zona geográfica")
        return pd.DataFrame()
    
    logger.info("  Creando resumen geográfico...")
    
    geo_summary = df.groupby('zona_geografica').agg({
        'Codigoct': 'count',
        'Potencia': 'sum',
        'Q_Usuarios': 'sum',
        'quality_score': 'mean',
        'criticidad_compuesta': 'mean',
        'Resultado': lambda x: (x == 'Fallida').sum()
    }).reset_index()
    
    geo_summary.columns = [
        'zona_geografica', 'num_transformadores', 'potencia_total_kva',
        'usuarios_totales', 'quality_score_promedio', 'criticidad_promedio',
        'num_fallidas'
    ]
    
    geo_summary['pct_fallidas'] = (
        geo_summary['num_fallidas'] / geo_summary['num_transformadores'] * 100
    )
    
    return geo_summary.sort_values('criticidad_promedio', ascending=False)


def generate_aggregation_report(
    df_sucursal: pd.DataFrame,
    df_localidad: pd.DataFrame,
    df_geographic: pd.DataFrame,
    critical_zones: Dict
) -> Dict:
    """
    Genera reporte completo de agregaciones.
    """
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "sucursales_analizadas": len(df_sucursal),
            "localidades_analizadas": len(df_localidad),
            "zonas_geograficas": len(df_geographic) if not df_geographic.empty else 0
        },
        "sucursales": {
            "top_criticas": df_sucursal.nlargest(5, 'criticidad_promedio')[
                ['N_Sucursal', 'criticidad_promedio', 'num_transformadores', 'usuarios_totales']
            ].to_dict('records'),
            "mayor_capacidad": df_sucursal.nlargest(5, 'potencia_total_kva')[
                ['N_Sucursal', 'potencia_total_kva', 'num_transformadores']
            ].to_dict('records'),
            "estadisticas": {
                "transformadores_promedio": df_sucursal['num_transformadores'].mean(),
                "usuarios_promedio": df_sucursal['usuarios_totales'].mean(),
                "indice_calidad_promedio": df_sucursal['indice_calidad'].mean()
            }
        },
        "localidades": {
            "top_criticas": df_localidad.nlargest(5, 'criticidad_promedio')[
                ['N_Localida', 'criticidad_promedio', 'num_transformadores']
            ].to_dict('records'),
            "estadisticas": {
                "total": len(df_localidad),
                "con_problemas_graves": len(df_localidad[df_localidad['criticidad_promedio'] > 0.6])
            }
        },
        "zonas_criticas": critical_zones,
        "geographic_distribution": df_geographic.to_dict('records') if not df_geographic.empty else []
    }
    
    return report


def main():
    """Función principal del script."""
    logger.info("=" * 70)
    logger.info("INICIANDO CREACIÓN DE AGREGACIONES")
    logger.info("=" * 70)
    
    try:
        # Cargar dataset procesado
        input_file = DATA_PROCESSED / "transformers_analysis.parquet"
        logger.info(f"\nCargando datos desde: {input_file}")
        df = pd.read_parquet(input_file)
        logger.info(f"  Registros cargados: {len(df):,}")
        
        # 1. Agregación por sucursal
        logger.info("\n1. AGREGACIÓN POR SUCURSAL")
        df_sucursal = aggregate_by_location(df, 'N_Sucursal')
        logger.info(f"  Sucursales agregadas: {len(df_sucursal)}")
        
        # 2. Agregación por localidad
        logger.info("\n2. AGREGACIÓN POR LOCALIDAD")
        df_localidad = aggregate_by_location(df, 'N_Localida')
        logger.info(f"  Localidades agregadas: {len(df_localidad)}")
        
        # 3. Resumen geográfico
        logger.info("\n3. RESUMEN GEOGRÁFICO")
        df_geographic = create_geographic_summary(df)
        if not df_geographic.empty:
            logger.info(f"  Zonas geográficas: {len(df_geographic)}")
        
        # 4. Identificar zonas críticas
        logger.info("\n4. IDENTIFICACIÓN DE ZONAS CRÍTICAS")
        critical_zones = identify_critical_zones(df_sucursal, df_localidad)
        logger.info(f"  Sucursales críticas: {critical_zones['summary']['sucursales_criticas']}")
        logger.info(f"  Usuarios afectados: {critical_zones['summary']['usuarios_afectados']:,}")
        
        # 5. Guardar agregaciones
        logger.info("\n5. GUARDANDO AGREGACIONES")
        
        # Crear directorio de agregaciones
        agg_dir = DATA_PROCESSED / "aggregations"
        agg_dir.mkdir(exist_ok=True)
        
        # Guardar archivos
        df_sucursal.to_parquet(agg_dir / "by_sucursal.parquet", index=False)
        df_sucursal.to_csv(agg_dir / "by_sucursal.csv", index=False)
        logger.info(f"  Agregación por sucursal guardada")
        
        df_localidad.to_parquet(agg_dir / "by_localidad.parquet", index=False)
        df_localidad.to_csv(agg_dir / "by_localidad.csv", index=False)
        logger.info(f"  Agregación por localidad guardada")
        
        if not df_geographic.empty:
            df_geographic.to_csv(agg_dir / "by_geographic_zone.csv", index=False)
            logger.info(f"  Resumen geográfico guardado")
        
        # Guardar zonas críticas
        with open(agg_dir / "critical_zones.json", 'w', encoding='utf-8') as f:
            json.dump(critical_zones, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"  Zonas críticas guardadas")
        
        # 6. Generar reporte
        logger.info("\n6. GENERANDO REPORTE DE AGREGACIONES")
        report = generate_aggregation_report(
            df_sucursal, df_localidad, df_geographic, critical_zones
        )
        
        report_file = REPORTS_DIR / "03_aggregations_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"  Reporte guardado: {report_file}")
        
        # 7. Resumen final
        logger.info("\n" + "=" * 70)
        logger.info("AGREGACIONES COMPLETADAS")
        logger.info("=" * 70)
        logger.info(f"Sucursales procesadas: {len(df_sucursal)}")
        logger.info(f"Localidades procesadas: {len(df_localidad)}")
        logger.info(f"Zonas críticas identificadas: {critical_zones['summary']['sucursales_criticas']}")
        logger.info(f"\nLogs guardados en: {log_file}")
        logger.info("Próximo paso: Ejecutar 04_analyze_criticality.py")
        
    except Exception as e:
        logger.error(f"\nERROR FATAL: {str(e)}")
        logger.exception("Detalles del error:")
        sys.exit(1)


if __name__ == "__main__":
    main()