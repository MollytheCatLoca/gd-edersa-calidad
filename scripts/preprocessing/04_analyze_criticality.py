#!/usr/bin/env python3
"""
04_analyze_criticality.py - Análisis detallado de criticidad

Quinto paso del pipeline de preprocesamiento.
- Análisis profundo de zonas críticas
- Identificación de patrones de falla
- Recomendaciones para GD
- Preparación de datos para dashboard

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
from typing import Dict, List, Tuple, Any, Optional
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Configurar paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorios necesarios
LOGS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Configurar logging
log_file = LOGS_DIR / f"04_criticality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def analyze_failure_patterns(df: pd.DataFrame) -> Dict:
    """
    Analiza patrones de falla en transformadores.
    """
    logger.info("  Analizando patrones de falla...")
    
    patterns = {
        'by_size': {},
        'by_load': {},
        'by_location_type': {},
        'correlations': {}
    }
    
    # Análisis por tamaño
    if 'size_category' in df.columns:
        size_analysis = df.groupby('size_category').agg({
            'Resultado': lambda x: (x == 'Fallida').mean() * 100,
            'quality_score': 'mean',
            'Codigoct': 'count'
        }).round(2)
        size_analysis.columns = ['pct_fallida', 'quality_promedio', 'total']
        patterns['by_size'] = size_analysis.to_dict('index')
    
    # Análisis por carga
    if 'usuarios_por_kva' in df.columns:
        df['load_category'] = pd.qcut(
            df['usuarios_por_kva'], 
            q=[0, 0.25, 0.5, 0.75, 1.0],
            labels=['Baja', 'Media-Baja', 'Media-Alta', 'Alta']
        )
        
        load_analysis = df.groupby('load_category').agg({
            'Resultado': lambda x: (x == 'Fallida').mean() * 100,
            'quality_score': 'mean',
            'Codigoct': 'count'
        }).round(2)
        load_analysis.columns = ['pct_fallida', 'quality_promedio', 'total']
        patterns['by_load'] = load_analysis.to_dict('index')
    
    # Análisis por tipo de zona
    if 'tipo_zona' in df.columns:
        zone_analysis = df.groupby('tipo_zona').agg({
            'Resultado': lambda x: (x == 'Fallida').mean() * 100,
            'criticidad_compuesta': 'mean',
            'Codigoct': 'count',
            'Q_Usuarios': 'sum'
        }).round(2)
        zone_analysis.columns = ['pct_fallida', 'criticidad_promedio', 'total', 'usuarios']
        patterns['by_location_type'] = zone_analysis.to_dict('index')
    
    # Correlaciones con falla
    numeric_cols = [
        'Potencia', 'Q_Usuarios', 'usuarios_por_kva', 
        'factor_utilizacion_estimado', 'densidad_local'
    ]
    
    # Crear variable binaria de falla
    df['es_fallida'] = (df['Resultado'] == 'Fallida').astype(int)
    
    correlations = {}
    for col in numeric_cols:
        if col in df.columns:
            valid_data = df[[col, 'es_fallida']].dropna()
            if len(valid_data) > 10:
                corr, p_value = stats.pointbiserialr(
                    valid_data['es_fallida'], 
                    valid_data[col]
                )
                correlations[col] = {
                    'correlation': round(corr, 4),
                    'p_value': round(p_value, 4),
                    'significant': p_value < 0.05
                }
    
    patterns['correlations'] = correlations
    
    return patterns


def identify_gd_opportunities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifica oportunidades específicas para GD.
    """
    logger.info("  Identificando oportunidades para GD...")
    
    # Crear score de oportunidad GD
    df_gd = df.copy()
    
    # Factores que aumentan la oportunidad GD
    # 1. Alta criticidad
    df_gd['score_criticidad'] = df_gd['criticidad_compuesta']
    
    # 2. Capacidad disponible
    df_gd['score_capacidad'] = df_gd['Potencia'] / df_gd['Potencia'].max()
    
    # 3. Zona rural (mayor beneficio)
    zone_scores = {'Rural': 1.0, 'Periurbano': 0.7, 'Urbano': 0.5}
    df_gd['score_zona'] = df_gd['tipo_zona'].map(zone_scores).fillna(0.5)
    
    # 4. Múltiples usuarios (mayor impacto)
    df_gd['score_usuarios'] = np.clip(df_gd['Q_Usuarios'] / 100, 0, 1)
    
    # 5. Factor de utilización moderado (espacio para GD)
    df_gd['score_utilizacion'] = 1 - np.clip(
        df_gd['factor_utilizacion_estimado'], 0, 1
    )
    
    # Score compuesto ponderado
    weights = {
        'criticidad': 0.35,
        'capacidad': 0.20,
        'zona': 0.20,
        'usuarios': 0.15,
        'utilizacion': 0.10
    }
    
    df_gd['gd_opportunity_score'] = (
        weights['criticidad'] * df_gd['score_criticidad'] +
        weights['capacidad'] * df_gd['score_capacidad'] +
        weights['zona'] * df_gd['score_zona'] +
        weights['usuarios'] * df_gd['score_usuarios'] +
        weights['utilizacion'] * df_gd['score_utilizacion']
    )
    
    # Categorizar oportunidades
    df_gd['gd_priority'] = pd.cut(
        df_gd['gd_opportunity_score'],
        bins=[0, 0.3, 0.5, 0.7, 1.0],
        labels=['Baja', 'Media', 'Alta', 'Muy Alta']
    )
    
    # Capacidad GD recomendada (20-30% de capacidad del transformador)
    df_gd['gd_capacity_recommended_kw'] = df_gd['Potencia'] * 0.25 * 0.9  # 25% * FP
    
    # Tipo de GD recomendado
    def recommend_gd_type(row):
        if row['tipo_zona'] == 'Rural' and row['Potencia'] < 200:
            return 'Solar pequeña escala'
        elif row['Potencia'] >= 500:
            return 'Solar + BESS'
        elif row['factor_utilizacion_estimado'] > 0.8:
            return 'BESS para peak shaving'
        else:
            return 'Solar estándar'
    
    df_gd['gd_type_recommended'] = df_gd.apply(recommend_gd_type, axis=1)
    
    return df_gd


def cluster_critical_transformers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa transformadores críticos usando técnicas de clustering.
    """
    logger.info("  Agrupando transformadores críticos...")
    
    # Filtrar solo transformadores con problemas
    df_critical = df[df['criticidad_compuesta'] > 0.3].copy()
    
    if len(df_critical) < 10:
        logger.warning("    Pocos transformadores críticos para clustering")
        return df
    
    # Seleccionar features para clustering
    feature_cols = [
        'Potencia', 'Q_Usuarios', 'usuarios_por_kva',
        'factor_utilizacion_estimado', 'criticidad_compuesta',
        'quality_score'
    ]
    
    # Preparar datos
    features_available = [col for col in feature_cols if col in df_critical.columns]
    X = df_critical[features_available].fillna(df_critical[features_available].median())
    
    # Normalizar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # PCA para visualización
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    df_critical['pca_1'] = X_pca[:, 0]
    df_critical['pca_2'] = X_pca[:, 1]
    
    # Crear grupos basados en criticidad y tamaño
    df_critical['critical_group'] = pd.cut(
        df_critical['criticidad_compuesta'],
        bins=[0.3, 0.5, 0.7, 1.0],
        labels=['Moderada', 'Alta', 'Crítica']
    )
    
    # Merge back to original
    df_result = df.copy()
    critical_cols = ['pca_1', 'pca_2', 'critical_group']
    
    for col in critical_cols:
        if col in df_critical.columns:
            df_result = df_result.merge(
                df_critical[['Codigoct', col]], 
                on='Codigoct', 
                how='left'
            )
    
    return df_result


def generate_gd_recommendations(df_gd: pd.DataFrame, top_n: int = 20) -> List[Dict]:
    """
    Genera recomendaciones específicas de GD.
    """
    logger.info("  Generando recomendaciones de GD...")
    
    # Top transformadores por oportunidad
    top_opportunities = df_gd.nlargest(top_n, 'gd_opportunity_score')
    
    recommendations = []
    for _, row in top_opportunities.iterrows():
        rec = {
            'codigo': row['Codigoct'],
            'sucursal': row.get('N_Sucursal', 'N/A'),
            'localidad': row.get('N_Localida', 'N/A'),
            'score': round(row['gd_opportunity_score'], 3),
            'prioridad': row['gd_priority'],
            'capacidad_actual_kva': row['Potencia'],
            'usuarios': int(row['Q_Usuarios']),
            'criticidad': round(row['criticidad_compuesta'], 3),
            'calidad_actual': row['Resultado'],
            'tipo_gd_recomendado': row['gd_type_recommended'],
            'capacidad_gd_kw': round(row['gd_capacity_recommended_kw'], 1),
            'beneficios_esperados': []
        }
        
        # Estimar beneficios
        if row['Resultado'] == 'Fallida':
            rec['beneficios_esperados'].append('Mejora significativa de calidad de servicio')
        if row['tipo_zona'] == 'Rural':
            rec['beneficios_esperados'].append('Reducción de pérdidas en líneas largas')
        if row['factor_utilizacion_estimado'] > 0.7:
            rec['beneficios_esperados'].append('Alivio de sobrecarga')
        if row['Q_Usuarios'] > 50:
            rec['beneficios_esperados'].append(f'Beneficio a {int(row["Q_Usuarios"])} usuarios')
        
        recommendations.append(rec)
    
    return recommendations


def calculate_impact_metrics(df: pd.DataFrame, df_gd: pd.DataFrame) -> Dict:
    """
    Calcula métricas de impacto potencial de GD.
    """
    logger.info("  Calculando métricas de impacto...")
    
    # Transformadores que mejorarían con GD
    high_opportunity = df_gd[df_gd['gd_opportunity_score'] > 0.6]
    
    metrics = {
        'transformadores_beneficiados': len(high_opportunity),
        'usuarios_beneficiados': int(high_opportunity['Q_Usuarios'].sum()),
        'capacidad_total_mva': round(high_opportunity['Potencia'].sum() / 1000, 2),
        'capacidad_gd_potencial_mw': round(
            high_opportunity['gd_capacity_recommended_kw'].sum() / 1000, 2
        ),
        'mejora_calidad_estimada': {},
        'distribucion_geografica': {},
        'inversion_estimada': {}
    }
    
    # Mejora de calidad estimada
    current_failures = (high_opportunity['Resultado'] == 'Fallida').sum()
    current_penalized = (high_opportunity['Resultado'] == 'Penalizada').sum()
    
    metrics['mejora_calidad_estimada'] = {
        'transformadores_fallidos_actual': int(current_failures),
        'transformadores_penalizados_actual': int(current_penalized),
        'mejora_esperada_pct': 70,  # Estimación conservadora
        'transformadores_mejorados': int((current_failures + current_penalized) * 0.7)
    }
    
    # Distribución geográfica
    if 'tipo_zona' in high_opportunity.columns:
        zone_dist = high_opportunity['tipo_zona'].value_counts()
        metrics['distribucion_geografica'] = zone_dist.to_dict()
    
    # Estimación de inversión (valores referenciales)
    costo_por_kw = {
        'Solar pequeña escala': 1200,
        'Solar estándar': 1000,
        'Solar + BESS': 1500,
        'BESS para peak shaving': 800
    }
    
    inversion_total = 0
    for gd_type, costo in costo_por_kw.items():
        mask = high_opportunity['gd_type_recommended'] == gd_type
        kw_total = high_opportunity.loc[mask, 'gd_capacity_recommended_kw'].sum()
        inversion = kw_total * costo
        metrics['inversion_estimada'][gd_type] = {
            'kw_total': round(kw_total, 1),
            'costo_unitario_usd_kw': costo,
            'inversion_total_usd': round(inversion, 0)
        }
        inversion_total += inversion
    
    metrics['inversion_estimada']['total_usd'] = round(inversion_total, 0)
    metrics['inversion_estimada']['total_millones_usd'] = round(inversion_total / 1e6, 2)
    
    return metrics


def generate_criticality_report(
    patterns: Dict,
    recommendations: List[Dict],
    impact_metrics: Dict,
    df_summary: pd.DataFrame
) -> Dict:
    """
    Genera reporte completo de criticidad.
    """
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "executive_summary": {
            "transformadores_analizados": len(df_summary),
            "transformadores_criticos": len(df_summary[df_summary['criticidad_compuesta'] > 0.5]),
            "oportunidades_gd_identificadas": len(recommendations),
            "inversion_estimada_musd": impact_metrics['inversion_estimada']['total_millones_usd'],
            "usuarios_beneficiados": impact_metrics['usuarios_beneficiados']
        },
        "failure_patterns": patterns,
        "gd_recommendations": {
            "top_opportunities": recommendations[:10],  # Top 10 para el reporte
            "summary_by_type": {},
            "geographic_distribution": impact_metrics['distribucion_geografica']
        },
        "expected_impact": impact_metrics,
        "key_insights": []
    }
    
    # Resumen por tipo de GD
    gd_summary = pd.DataFrame(recommendations).groupby('tipo_gd_recomendado').agg({
        'codigo': 'count',
        'capacidad_gd_kw': 'sum',
        'usuarios': 'sum'
    }).round(1)
    gd_summary.columns = ['cantidad', 'capacidad_total_kw', 'usuarios_totales']
    report['gd_recommendations']['summary_by_type'] = gd_summary.to_dict('index')
    
    # Insights clave
    insights = []
    
    # Insight sobre patrones de falla
    if 'by_size' in patterns and patterns['by_size']:
        worst_size = max(patterns['by_size'].items(), 
                        key=lambda x: x[1].get('pct_fallida', 0))
        if worst_size[1]['pct_fallida'] > 20:
            insights.append(
                f"Transformadores {worst_size[0]} tienen mayor tasa de falla "
                f"({worst_size[1]['pct_fallida']}%)"
            )
    
    # Insight sobre zonas
    if 'by_location_type' in patterns and patterns['by_location_type']:
        rural_data = patterns['by_location_type'].get('Rural', {})
        if rural_data.get('criticidad_promedio', 0) > 0.5:
            insights.append(
                f"Zonas rurales presentan alta criticidad promedio "
                f"({rural_data['criticidad_promedio']:.2f})"
            )
    
    # Insight sobre inversión
    if impact_metrics['inversion_estimada']['total_millones_usd'] > 0:
        roi_usuarios = (impact_metrics['usuarios_beneficiados'] / 
                       impact_metrics['inversion_estimada']['total_millones_usd'])
        insights.append(
            f"Inversión de ${impact_metrics['inversion_estimada']['total_millones_usd']:.1f}M "
            f"beneficiaría a {int(roi_usuarios)} usuarios por millón invertido"
        )
    
    report['key_insights'] = insights
    
    return report


def main():
    """Función principal del script."""
    logger.info("=" * 70)
    logger.info("INICIANDO ANÁLISIS DE CRITICIDAD")
    logger.info("=" * 70)
    
    try:
        # Cargar datos
        input_file = DATA_PROCESSED / "transformers_analysis.parquet"
        logger.info(f"\nCargando datos desde: {input_file}")
        df = pd.read_parquet(input_file)
        logger.info(f"  Registros cargados: {len(df):,}")
        
        # 1. Análisis de patrones de falla
        logger.info("\n1. ANÁLISIS DE PATRONES DE FALLA")
        failure_patterns = analyze_failure_patterns(df)
        logger.info(f"  Patrones analizados: {len(failure_patterns)}")
        
        # 2. Identificación de oportunidades GD
        logger.info("\n2. IDENTIFICACIÓN DE OPORTUNIDADES GD")
        df_gd = identify_gd_opportunities(df)
        high_priority = (df_gd['gd_priority'].isin(['Alta', 'Muy Alta'])).sum()
        logger.info(f"  Oportunidades de alta prioridad: {high_priority}")
        
        # 3. Clustering de transformadores críticos
        logger.info("\n3. CLUSTERING DE TRANSFORMADORES CRÍTICOS")
        df_clustered = cluster_critical_transformers(df_gd)
        
        # 4. Generación de recomendaciones
        logger.info("\n4. GENERACIÓN DE RECOMENDACIONES GD")
        recommendations = generate_gd_recommendations(df_gd, top_n=50)
        logger.info(f"  Recomendaciones generadas: {len(recommendations)}")
        
        # 5. Cálculo de métricas de impacto
        logger.info("\n5. CÁLCULO DE MÉTRICAS DE IMPACTO")
        impact_metrics = calculate_impact_metrics(df, df_gd)
        logger.info(f"  Usuarios beneficiados: {impact_metrics['usuarios_beneficiados']:,}")
        logger.info(f"  Inversión estimada: ${impact_metrics['inversion_estimada']['total_millones_usd']:.1f}M USD")
        
        # 6. Guardar resultados
        logger.info("\n6. GUARDANDO RESULTADOS")
        
        # Guardar dataset enriquecido con scores GD
        output_file = DATA_PROCESSED / "transformers_gd_analysis.parquet"
        df_gd.to_parquet(output_file, index=False)
        logger.info(f"  Dataset con análisis GD guardado: {output_file}")
        
        # Guardar recomendaciones detalladas
        recommendations_file = DATA_PROCESSED / "gd_recommendations.json"
        with open(recommendations_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"  Recomendaciones guardadas: {recommendations_file}")
        
        # 7. Generar reporte
        logger.info("\n7. GENERANDO REPORTE DE CRITICIDAD")
        report = generate_criticality_report(
            failure_patterns, recommendations, impact_metrics, df_gd
        )
        
        report_file = REPORTS_DIR / "04_criticality_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"  Reporte guardado: {report_file}")
        
        # 8. Resumen final
        logger.info("\n" + "=" * 70)
        logger.info("ANÁLISIS DE CRITICIDAD COMPLETADO")
        logger.info("=" * 70)
        logger.info(f"Transformadores críticos: {(df_gd['criticidad_compuesta'] > 0.5).sum()}")
        logger.info(f"Oportunidades GD alta prioridad: {high_priority}")
        logger.info(f"Capacidad GD potencial: {impact_metrics['capacidad_gd_potencial_mw']:.1f} MW")
        logger.info(f"\nLogs guardados en: {log_file}")
        logger.info("Próximo paso: Ejecutar 05_create_database.py")
        
    except Exception as e:
        logger.error(f"\nERROR FATAL: {str(e)}")
        logger.exception("Detalles del error:")
        sys.exit(1)


if __name__ == "__main__":
    main()