#!/usr/bin/env python3
"""
02_clean_enrich_data.py - Limpieza y enriquecimiento de datos

Tercer paso del pipeline de preprocesamiento.
- Agrega circuitos por transformador
- Imputa valores faltantes
- Normaliza strings
- Calcula métricas y categorías
- Enriquece con análisis geoespacial

Autor: Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
import json
import logging
import sys
import yaml
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from scipy.spatial import distance_matrix
from sklearn.cluster import DBSCAN

# Suprimir warnings de pandas
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

# Configurar paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_FILE = PROJECT_ROOT / "config" / "preprocessing_config.yaml"

# Configurar logging
log_file = LOGS_DIR / f"02_cleaning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Carga la configuración del archivo YAML."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error cargando configuración: {e}")
        raise


def normalize_strings(df: pd.DataFrame, normalization_rules: Dict[str, List[str]]) -> pd.DataFrame:
    """Normaliza strings según reglas de configuración."""
    df_normalized = df.copy()
    
    for column, rules in normalization_rules.items():
        if column not in df_normalized.columns:
            continue
            
        logger.info(f"  Normalizando columna: {column}")
        
        for rule in rules:
            if rule == 'upper':
                df_normalized[column] = df_normalized[column].str.upper()
            elif rule == 'lower':
                df_normalized[column] = df_normalized[column].str.lower()
            elif rule == 'title':
                df_normalized[column] = df_normalized[column].str.title()
            elif rule == 'strip':
                df_normalized[column] = df_normalized[column].str.strip()
        
        # Reemplazar strings vacíos con NaN
        df_normalized[column] = df_normalized[column].replace('', np.nan)
        
    return df_normalized


def aggregate_by_transformer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega circuitos por transformador para análisis de calidad.
    Usa estrategia de PEOR CASO para la calidad.
    """
    logger.info("Agregando circuitos por transformador...")
    
    # Definir prioridad de resultados (peor primero)
    resultado_priority = {
        'Fallida': 0,
        'Penalizada': 1,
        'Correcta': 2,
        'No Instalado': 3,
        '???': 4
    }
    
    # Función para obtener el peor resultado
    def worst_result(results):
        valid_results = results.dropna()
        if len(valid_results) == 0:
            return np.nan
        # Ordenar por prioridad y tomar el primero (peor)
        return min(valid_results, key=lambda x: resultado_priority.get(x, 999))
    
    # Agregaciones
    agg_dict = {
        'Nro de circuito': 'nunique',  # Número de circuitos únicos
        'Potencia': 'first',  # Asumir que la potencia es del transformador completo
        'Q_Usuarios': 'first',  # TOMAR PRIMER VALOR - Los usuarios son del transformador, no del circuito
        'Resultado': worst_result,  # Peor caso
        'N_Sucursal': 'first',
        'Alimentador': 'first',
        'N_Localida': 'first',
        'Coord_X': 'first',
        'Coord_Y': 'first',
        'Tipoinstalacion': 'first'
    }
    
    # Agrupar por transformador
    df_agg = df.groupby('Codigoct').agg(agg_dict).reset_index()
    
    # Renombrar columna de número de circuitos
    df_agg.rename(columns={'Nro de circuito': 'num_circuitos'}, inplace=True)
    
    # Agregar información de mediciones
    mediciones_info = df.groupby('Codigoct').agg({
        'Nro de medicion': ['min', 'max', 'nunique'],
        'Resultado': 'count'  # Total de registros
    })
    mediciones_info.columns = ['min_medicion', 'max_medicion', 'num_mediciones', 'total_registros']
    
    # Unir con agregado principal
    df_agg = df_agg.merge(mediciones_info, on='Codigoct', how='left')
    
    # Agregar flag de múltiples circuitos
    df_agg['tiene_multi_circuitos'] = df_agg['num_circuitos'] > 1
    
    # Agregar flag de fue medido
    df_agg['fue_medido'] = df_agg['Resultado'].notna()
    
    logger.info(f"  Transformadores únicos: {len(df_agg)}")
    logger.info(f"  Con múltiples circuitos: {df_agg['tiene_multi_circuitos'].sum()}")
    
    return df_agg


def impute_zero_power(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Imputa valores de potencia 0 basándose en transformadores similares.
    """
    logger.info("Imputando transformadores con potencia 0...")
    
    df_imputed = df.copy()
    
    # Guardar valores originales
    df_imputed['potencia_original'] = df_imputed['Potencia']
    df_imputed['potencia_imputada'] = False
    
    # Identificar registros con potencia 0
    mask_zero_power = (df_imputed['Potencia'] == 0) | df_imputed['Potencia'].isna()
    n_zero_power = mask_zero_power.sum()
    
    if n_zero_power == 0:
        logger.info("  No hay transformadores con potencia 0")
        return df_imputed
    
    logger.info(f"  Transformadores con potencia 0 o nula: {n_zero_power}")
    
    # Crear grupos para imputación
    # Primero intentar por sucursal y rango de usuarios
    df_imputed['rango_usuarios'] = pd.cut(
        df_imputed['Q_Usuarios'],
        bins=[0, 10, 50, 100, 200, 500, 1000],
        labels=['0-10', '11-50', '51-100', '101-200', '201-500', '500+']
    )
    
    # Función para imputar por grupo
    def impute_by_group(group_cols):
        for idx in df_imputed[mask_zero_power].index:
            # Obtener valores del registro actual
            current_values = df_imputed.loc[idx, group_cols].to_dict()
            
            # Buscar transformadores similares con potencia válida
            mask_similar = pd.Series(True, index=df_imputed.index)
            for col, val in current_values.items():
                if pd.notna(val):
                    mask_similar &= (df_imputed[col] == val)
            
            # Excluir transformadores con potencia 0 y el actual
            mask_similar &= (df_imputed['Potencia'] > 0)
            mask_similar &= (df_imputed.index != idx)
            
            similar_transformers = df_imputed[mask_similar]
            
            if len(similar_transformers) >= 3:  # Mínimo 3 para calcular mediana
                median_power = similar_transformers['Potencia'].median()
                df_imputed.loc[idx, 'Potencia'] = median_power
                df_imputed.loc[idx, 'potencia_imputada'] = True
                logger.debug(f"    Imputado {df_imputed.loc[idx, 'Codigoct']}: {median_power} kVA")
                return True
        
        return False
    
    # Intentar diferentes niveles de agrupación
    imputation_groups = [
        ['N_Sucursal', 'rango_usuarios'],  # Más específico
        ['N_Sucursal'],  # Por sucursal
        ['rango_usuarios'],  # Por rango de usuarios
    ]
    
    for group_cols in imputation_groups:
        remaining = mask_zero_power & ~df_imputed['potencia_imputada']
        if remaining.sum() == 0:
            break
            
        logger.info(f"  Intentando imputación por: {group_cols}")
        n_before = remaining.sum()
        
        # Aplicar imputación
        for idx in df_imputed[remaining].index:
            current_values = {col: df_imputed.loc[idx, col] for col in group_cols if pd.notna(df_imputed.loc[idx, col])}
            
            mask_similar = pd.Series(True, index=df_imputed.index)
            for col, val in current_values.items():
                mask_similar &= (df_imputed[col] == val)
            
            mask_similar &= (df_imputed['Potencia'] > 0)
            similar_transformers = df_imputed[mask_similar]
            
            if len(similar_transformers) >= 3:
                median_power = similar_transformers['Potencia'].median()
                df_imputed.loc[idx, 'Potencia'] = median_power
                df_imputed.loc[idx, 'potencia_imputada'] = True
        
        n_after = (mask_zero_power & ~df_imputed['potencia_imputada']).sum()
        logger.info(f"    Imputados: {n_before - n_after}")
    
    # Para los que no se pudieron imputar, usar valor por defecto
    remaining_mask = mask_zero_power & ~df_imputed['potencia_imputada']
    if remaining_mask.sum() > 0:
        default_power = 100  # 100 kVA por defecto
        df_imputed.loc[remaining_mask, 'Potencia'] = default_power
        df_imputed.loc[remaining_mask, 'potencia_imputada'] = True
        logger.warning(f"  {remaining_mask.sum()} transformadores imputados con valor por defecto: {default_power} kVA")
    
    # Limpiar columna temporal
    df_imputed.drop('rango_usuarios', axis=1, inplace=True)
    
    return df_imputed


def calculate_technical_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula métricas técnicas y categorías."""
    logger.info("Calculando métricas técnicas...")
    
    df_metrics = df.copy()
    
    # Densidad de carga (usuarios por kVA)
    df_metrics['usuarios_por_kva'] = np.where(
        df_metrics['Potencia'] > 0,
        df_metrics['Q_Usuarios'] / df_metrics['Potencia'],
        0
    )
    
    # kVA por circuito
    df_metrics['kva_por_circuito'] = np.where(
        df_metrics.get('num_circuitos', 1) > 0,
        df_metrics['Potencia'] / df_metrics.get('num_circuitos', 1),
        df_metrics['Potencia']
    )
    
    # Categoría de tamaño
    df_metrics['size_category'] = pd.cut(
        df_metrics['Potencia'],
        bins=[0, 100, 300, 500, 1000, 10000],
        labels=['Micro', 'Pequeño', 'Mediano', 'Grande', 'Muy Grande']
    )
    # Convertir a string para evitar problemas con categorical
    df_metrics['size_category'] = df_metrics['size_category'].astype(str)
    
    # Factor de utilización estimado (basado en usuarios típicos)
    # Asumiendo 1.5 kW promedio por usuario residencial
    kw_por_usuario = 1.5
    factor_diversidad = 0.6  # Factor de diversidad típico
    
    df_metrics['carga_estimada_kw'] = df_metrics['Q_Usuarios'] * kw_por_usuario * factor_diversidad
    df_metrics['factor_utilizacion_estimado'] = np.where(
        df_metrics['Potencia'] > 0,
        df_metrics['carga_estimada_kw'] / (df_metrics['Potencia'] * 0.9),  # 0.9 factor de potencia
        0
    )
    
    # Limitar factor de utilización a valores razonables
    df_metrics['factor_utilizacion_estimado'] = df_metrics['factor_utilizacion_estimado'].clip(0, 1.5)
    
    # Quality score numérico
    quality_map = {
        'Correcta': 1.0,
        'Penalizada': 0.5,
        'Fallida': 0.0,
        'No Instalado': np.nan,
        '???': np.nan
    }
    df_metrics['quality_score'] = df_metrics['Resultado'].map(quality_map)
    
    # Categoría de carga
    df_metrics['categoria_carga'] = df_metrics.apply(
        lambda row: 'Residencial' if row['usuarios_por_kva'] > 0.5 
        else 'Comercial/Industrial' if row['usuarios_por_kva'] < 0.2
        else 'Mixto',
        axis=1
    )
    
    return df_metrics


def enrich_geospatial_data(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Enriquece datos con análisis geoespacial."""
    logger.info("Enriqueciendo datos geoespaciales...")
    
    df_geo = df.copy()
    
    # Filtrar solo registros con coordenadas válidas
    mask_valid_coords = df_geo['Coord_X'].notna() & df_geo['Coord_Y'].notna()
    
    if mask_valid_coords.sum() == 0:
        logger.warning("  No hay registros con coordenadas válidas")
        return df_geo
    
    # Redondear coordenadas a 6 decimales
    df_geo.loc[mask_valid_coords, 'Coord_X'] = df_geo.loc[mask_valid_coords, 'Coord_X'].round(6)
    df_geo.loc[mask_valid_coords, 'Coord_Y'] = df_geo.loc[mask_valid_coords, 'Coord_Y'].round(6)
    
    # Calcular cuadrantes (dividir en 4 zonas)
    x_median = df_geo.loc[mask_valid_coords, 'Coord_X'].median()
    y_median = df_geo.loc[mask_valid_coords, 'Coord_Y'].median()
    
    df_geo['zona_geografica'] = 'Sin coordenadas'
    
    mask_ne = mask_valid_coords & (df_geo['Coord_X'] >= x_median) & (df_geo['Coord_Y'] >= y_median)
    mask_nw = mask_valid_coords & (df_geo['Coord_X'] < x_median) & (df_geo['Coord_Y'] >= y_median)
    mask_se = mask_valid_coords & (df_geo['Coord_X'] >= x_median) & (df_geo['Coord_Y'] < y_median)
    mask_sw = mask_valid_coords & (df_geo['Coord_X'] < x_median) & (df_geo['Coord_Y'] < y_median)
    
    df_geo.loc[mask_ne, 'zona_geografica'] = 'Noreste'
    df_geo.loc[mask_nw, 'zona_geografica'] = 'Noroeste'
    df_geo.loc[mask_se, 'zona_geografica'] = 'Sureste'
    df_geo.loc[mask_sw, 'zona_geografica'] = 'Suroeste'
    
    # Calcular densidad local (transformadores en radio de 1km)
    # Aproximación: 1 grado ≈ 111 km en latitud
    radius_deg = 1 / 111  # ~1 km en grados
    
    logger.info("  Calculando densidad local...")
    df_geo['densidad_local'] = 0
    
    # Solo calcular para una muestra si hay muchos registros
    if len(df_geo) > 1000:
        sample_size = min(1000, len(df_geo[mask_valid_coords]))
        sample_indices = df_geo[mask_valid_coords].sample(sample_size).index
    else:
        sample_indices = df_geo[mask_valid_coords].index
    
    for idx in sample_indices:
        x = df_geo.loc[idx, 'Coord_X']
        y = df_geo.loc[idx, 'Coord_Y']
        
        # Contar transformadores cercanos
        nearby = df_geo[
            mask_valid_coords &
            (abs(df_geo['Coord_X'] - x) <= radius_deg) &
            (abs(df_geo['Coord_Y'] - y) <= radius_deg)
        ]
        
        # Calcular distancia euclidiana más precisa
        if len(nearby) > 1:
            distances = np.sqrt(
                ((nearby['Coord_X'] - x) * 111 * np.cos(np.radians(y)))**2 +
                ((nearby['Coord_Y'] - y) * 111)**2
            )
            count_within_1km = (distances <= 1).sum() - 1  # Excluir el mismo punto
            df_geo.loc[idx, 'densidad_local'] = count_within_1km
    
    # Clasificar tipo de zona por densidad
    df_geo['tipo_zona'] = pd.cut(
        df_geo['densidad_local'],
        bins=[-1, 5, 20, 1000],
        labels=['Rural', 'Periurbano', 'Urbano']
    )
    # Convertir a string para evitar problemas con categorical
    df_geo['tipo_zona'] = df_geo['tipo_zona'].astype(str)
    
    # Clustering espacial con DBSCAN
    logger.info("  Ejecutando clustering espacial...")
    coords_array = df_geo.loc[mask_valid_coords, ['Coord_X', 'Coord_Y']].values
    
    if len(coords_array) > 10:
        # DBSCAN con eps adaptativo
        eps = config['spatial']['clustering']['eps']
        min_samples = config['spatial']['clustering']['min_samples']
        
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords_array)
        
        df_geo.loc[mask_valid_coords, 'cluster_geografico_id'] = clustering.labels_
        
        # Estadísticas de clusters
        n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
        n_noise = list(clustering.labels_).count(-1)
        
        logger.info(f"    Clusters encontrados: {n_clusters}")
        logger.info(f"    Puntos sin cluster: {n_noise}")
    else:
        df_geo['cluster_geografico_id'] = -1
    
    return df_geo


def calculate_criticality_indices(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Calcula índices de criticidad compuestos."""
    logger.info("Calculando índices de criticidad...")
    
    df_crit = df.copy()
    
    # Obtener pesos de configuración
    weights = config.get('criticality', {}).get('weights', {
        'quality_rate': 0.4,
        'user_impact': 0.3,
        'capacity_impact': 0.3
    })
    
    # 1. Criticidad técnica (basada en calidad)
    df_crit['criticidad_tecnica'] = 1 - df_crit['quality_score'].fillna(0.5)
    
    # 2. Criticidad por usuarios
    # Normalizar usuarios (0-1)
    if df_crit['Q_Usuarios'].max() > 0:
        df_crit['usuarios_norm'] = df_crit['Q_Usuarios'] / df_crit['Q_Usuarios'].max()
    else:
        df_crit['usuarios_norm'] = 0
    
    df_crit['criticidad_usuarios'] = df_crit['usuarios_norm'] * (1 - df_crit['quality_score'].fillna(0.5))
    
    # 3. Criticidad geográfica (basada en aislamiento)
    # Mayor criticidad para zonas rurales con problemas
    zona_criticidad = {
        'Rural': 1.0,
        'Periurbano': 0.7,
        'Urbano': 0.5
    }
    df_crit['factor_zona'] = df_crit['tipo_zona'].map(zona_criticidad).fillna(0.5)
    df_crit['criticidad_geografica'] = df_crit['factor_zona'] * (1 - df_crit['quality_score'].fillna(0.5))
    
    # 4. Criticidad compuesta ponderada
    df_crit['criticidad_compuesta'] = (
        weights['quality_rate'] * df_crit['criticidad_tecnica'] +
        weights['user_impact'] * df_crit['criticidad_usuarios'] +
        weights['capacity_impact'] * df_crit['criticidad_geografica']
    )
    
    # Categorizar criticidad
    df_crit['nivel_criticidad'] = pd.cut(
        df_crit['criticidad_compuesta'],
        bins=[0, 0.3, 0.6, 1.0],
        labels=['Baja', 'Media', 'Alta']
    )
    # Convertir a string para evitar problemas con categorical
    df_crit['nivel_criticidad'] = df_crit['nivel_criticidad'].astype(str)
    
    # Prioridad para GD (mayor criticidad + mayor capacidad = mayor prioridad)
    df_crit['capacidad_norm'] = df_crit['Potencia'] / df_crit['Potencia'].max() if df_crit['Potencia'].max() > 0 else 0
    df_crit['prioridad_gd'] = df_crit['criticidad_compuesta'] * 0.7 + df_crit['capacidad_norm'] * 0.3
    
    return df_crit


def generate_cleaning_report(
    df_original: pd.DataFrame,
    df_cleaned: pd.DataFrame,
    cleaning_stats: Dict
) -> Dict:
    """Genera reporte de limpieza y enriquecimiento."""
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "original_records": len(df_original),
            "cleaned_records": len(df_cleaned),
            "transformers_unique": df_cleaned['Codigoct'].nunique() if 'Codigoct' in df_cleaned else 0
        },
        "cleaning_operations": cleaning_stats,
        "data_quality": {
            "potencia_imputada": int(df_cleaned['potencia_imputada'].sum()) if 'potencia_imputada' in df_cleaned else 0,
            "con_coordenadas": int(df_cleaned['Coord_X'].notna().sum()) if 'Coord_X' in df_cleaned else 0,
            "con_quality_score": int(df_cleaned['quality_score'].notna().sum()) if 'quality_score' in df_cleaned else 0
        },
        "enrichment_summary": {
            "campos_agregados": [
                'num_circuitos', 'usuarios_por_kva', 'size_category',
                'factor_utilizacion_estimado', 'quality_score', 'zona_geografica',
                'tipo_zona', 'criticidad_compuesta', 'prioridad_gd'
            ],
            "indices_calculados": {
                'criticidad_tecnica': df_cleaned['criticidad_tecnica'].describe().to_dict() if 'criticidad_tecnica' in df_cleaned else {},
                'criticidad_usuarios': df_cleaned['criticidad_usuarios'].describe().to_dict() if 'criticidad_usuarios' in df_cleaned else {},
                'criticidad_compuesta': df_cleaned['criticidad_compuesta'].describe().to_dict() if 'criticidad_compuesta' in df_cleaned else {}
            }
        },
        "geographic_analysis": {
            "zonas": df_cleaned['zona_geografica'].value_counts().to_dict() if 'zona_geografica' in df_cleaned else {},
            "tipo_zona": df_cleaned['tipo_zona'].value_counts().to_dict() if 'tipo_zona' in df_cleaned else {},
            "clusters": int(df_cleaned['cluster_geografico_id'].nunique()) if 'cluster_geografico_id' in df_cleaned else 0
        }
    }
    
    return report


def main():
    """Función principal del script."""
    logger.info("=" * 70)
    logger.info("INICIANDO LIMPIEZA Y ENRIQUECIMIENTO DE DATOS")
    logger.info("=" * 70)
    
    try:
        # Cargar configuración
        config = load_config()
        
        # Diccionario para estadísticas
        cleaning_stats = {}
        
        # Procesar ambos datasets
        for dataset_name, dataset_file in [
            ("A - Análisis de calidad", "dataset_a_quality_analysis.csv"),
            ("B - Inventario completo", "dataset_b_full_inventory.csv")
        ]:
            logger.info(f"\n{'='*50}")
            logger.info(f"PROCESANDO DATASET {dataset_name}")
            logger.info(f"{'='*50}")
            
            # Cargar dataset
            input_file = DATA_PROCESSED / dataset_file
            logger.info(f"\nCargando: {input_file}")
            df = pd.read_csv(input_file)
            logger.info(f"  Registros cargados: {len(df):,}")
            
            # Guardar copia original para comparación
            df_original = df.copy()
            
            # 1. Normalización de strings
            logger.info("\n1. NORMALIZACIÓN DE STRINGS")
            df = normalize_strings(df, config['cleaning']['string_normalization'])
            
            # 2. Agregación por transformador (solo para dataset A)
            if "quality_analysis" in dataset_file:
                logger.info("\n2. AGREGACIÓN POR TRANSFORMADOR")
                df_before_agg = len(df)
                df = aggregate_by_transformer(df)
                cleaning_stats[f"{dataset_name}_aggregation"] = {
                    "before": df_before_agg,
                    "after": len(df),
                    "reduction": df_before_agg - len(df)
                }
            
            # 3. Imputación de potencia 0
            logger.info("\n3. IMPUTACIÓN DE POTENCIA")
            df = impute_zero_power(df, config)
            cleaning_stats[f"{dataset_name}_power_imputation"] = {
                "imputed": int(df['potencia_imputada'].sum()) if 'potencia_imputada' in df else 0
            }
            
            # 4. Cálculo de métricas técnicas
            logger.info("\n4. CÁLCULO DE MÉTRICAS TÉCNICAS")
            df = calculate_technical_metrics(df)
            
            # 5. Enriquecimiento geoespacial
            logger.info("\n5. ENRIQUECIMIENTO GEOESPACIAL")
            df = enrich_geospatial_data(df, config)
            
            # 6. Cálculo de índices de criticidad (solo dataset con calidad)
            if 'quality_score' in df.columns and df['quality_score'].notna().any():
                logger.info("\n6. CÁLCULO DE ÍNDICES DE CRITICIDAD")
                df = calculate_criticality_indices(df, config)
            
            # 7. Guardar dataset procesado
            logger.info("\n7. GUARDANDO DATASET PROCESADO")
            
            # Determinar formato de salida
            if "quality_analysis" in dataset_file:
                output_file = DATA_PROCESSED / "transformers_analysis.parquet"
                df.to_parquet(output_file, index=False)
                logger.info(f"  Dataset guardado: {output_file}")
                
                # También guardar en CSV para compatibilidad
                output_csv = DATA_PROCESSED / "transformers_analysis.csv"
                df.to_csv(output_csv, index=False)
                logger.info(f"  CSV guardado: {output_csv}")
                
                # Guardar dataset para análisis
                df_analysis = df
                
            else:
                output_file = DATA_PROCESSED / "circuits_inventory.parquet"
                df.to_parquet(output_file, index=False)
                logger.info(f"  Dataset guardado: {output_file}")
                
                # Guardar dataset para inventario
                df_inventory = df
        
        # 8. Generar reporte consolidado
        logger.info("\n8. GENERANDO REPORTE DE LIMPIEZA")
        
        report = generate_cleaning_report(df_original, df_analysis, cleaning_stats)
        
        report_file = REPORTS_DIR / "02_cleaning_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"  Reporte guardado: {report_file}")
        
        # 9. Crear archivo GeoJSON para mapas
        logger.info("\n9. CREANDO ARCHIVO GEOJSON")
        
        # Usar dataset de análisis agregado para puntos únicos
        mask_geo = df_analysis['Coord_X'].notna() & df_analysis['Coord_Y'].notna()
        
        if mask_geo.sum() > 0:
            features = []
            for idx, row in df_analysis[mask_geo].iterrows():
                feature = {
                    "type": "Feature",
                    "properties": {
                        "codigo": row['Codigoct'],
                        "sucursal": row.get('N_Sucursal', ''),
                        "localidad": row.get('N_Localida', ''),
                        "potencia_kva": row['Potencia'],
                        "usuarios": row['Q_Usuarios'],
                        "resultado": row.get('Resultado', ''),
                        "quality_score": row.get('quality_score', None),
                        "criticidad": row.get('criticidad_compuesta', None),
                        "prioridad_gd": row.get('prioridad_gd', None)
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [row['Coord_X'], row['Coord_Y']]
                    }
                }
                features.append(feature)
            
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            geojson_file = DATA_PROCESSED / "spatial" / "transformers_geo.geojson"
            geojson_file.parent.mkdir(exist_ok=True)
            
            with open(geojson_file, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, indent=2)
            
            logger.info(f"  GeoJSON creado: {geojson_file}")
            logger.info(f"  Features: {len(features)}")
        
        # 10. Resumen final
        logger.info("\n" + "=" * 70)
        logger.info("LIMPIEZA Y ENRIQUECIMIENTO COMPLETADO")
        logger.info("=" * 70)
        logger.info(f"Transformadores únicos procesados: {df_analysis['Codigoct'].nunique()}")
        logger.info(f"Registros con criticidad alta: {(df_analysis['nivel_criticidad'] == 'Alta').sum() if 'nivel_criticidad' in df_analysis else 0}")
        logger.info(f"Potencias imputadas: {df_analysis['potencia_imputada'].sum() if 'potencia_imputada' in df_analysis else 0}")
        logger.info(f"\nLogs guardados en: {log_file}")
        logger.info("Próximo paso: Ejecutar 03_create_aggregations.py")
        
    except Exception as e:
        logger.error(f"\nERROR FATAL: {str(e)}")
        logger.exception("Detalles del error:")
        sys.exit(1)


if __name__ == "__main__":
    main()