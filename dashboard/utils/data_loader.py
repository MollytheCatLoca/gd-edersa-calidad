"""
Utilidades para carga eficiente de datos
"""

import pandas as pd
import sqlite3
from pathlib import Path
import json
from functools import lru_cache
import numpy as np

# Paths base
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Paths de archivos principales
PATHS = {
    # Usar archivos existentes mientras no tengamos los del análisis eléctrico
    'transformadores_completo': DATA_DIR / "processed/network_analysis/transformadores_con_topologia.csv",
    'transformadores_fallback': DATA_DIR / "processed/transformers_analysis.csv",
    'alimentadores': DATA_DIR / "processed/network_analysis/alimentadores_caracterizados.csv",
    'topologia_mst': DATA_DIR / "processed/electrical_analysis/transformadores_mst_topology.csv",
    'distancia_electrica': DATA_DIR / "processed/electrical_analysis/transformadores_distancia_electrica.csv",
    'carga_estimada': DATA_DIR / "processed/electrical_analysis/transformadores_carga_estimada.csv",
    'database': DATA_DIR / "edersa_transformadores.db",
    'metadata_ml': DATA_DIR / "processed/electrical_analysis/ml_datasets/metadata.json",
    'feature_importance': DATA_DIR / "processed/electrical_analysis/ml_datasets/feature_importance.csv"
}

@lru_cache(maxsize=10)
def load_transformadores_completo():
    """Carga el dataset completo de transformadores con todas las features"""
    try:
        df = pd.read_csv(PATHS['transformadores_completo'])
        print(f"✓ Cargados {len(df)} transformadores con {len(df.columns)} columnas")
        return df
    except Exception as e:
        print(f"Error cargando transformadores principal: {e}")
        # Intentar archivo fallback
        try:
            df = pd.read_csv(PATHS['transformadores_fallback'])
            print(f"✓ Cargados {len(df)} transformadores desde archivo fallback")
            # Asegurar que tenga columnas esperadas
            if 'nivel_vulnerabilidad' not in df.columns:
                df['nivel_vulnerabilidad'] = 'Media'  # Default
            if 'indice_vulnerabilidad_compuesto' not in df.columns:
                df['indice_vulnerabilidad_compuesto'] = 0.5  # Default
            if 'modo_falla_probable' not in df.columns:
                df['modo_falla_probable'] = 'Mixto'  # Default
            return df
        except Exception as e2:
            print(f"Error cargando fallback: {e2}")
            # Intentar cargar desde base de datos
            return load_from_database('transformadores')

@lru_cache(maxsize=5)
def load_alimentadores():
    """Carga los datos de alimentadores caracterizados"""
    try:
        df = pd.read_csv(PATHS['alimentadores'])
        return df
    except Exception as e:
        print(f"Error cargando alimentadores: {e}")
        return pd.DataFrame()

@lru_cache(maxsize=1)
def load_feature_importance():
    """Carga la importancia de features del análisis ML"""
    try:
        df = pd.read_csv(PATHS['feature_importance'])
        return df
    except Exception as e:
        print(f"Error cargando feature importance: {e}")
        return pd.DataFrame()

def load_from_database(table_name):
    """Carga datos desde la base de datos SQLite"""
    try:
        conn = sqlite3.connect(PATHS['database'])
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error cargando desde base de datos: {e}")
        return pd.DataFrame()

def get_summary_metrics():
    """Obtiene métricas resumen del sistema"""
    df = load_transformadores_completo()
    
    if df.empty:
        return {
            'total_transformadores': 0,
            'total_usuarios': 0,
            'capacidad_total_mva': 0,
            'tasa_problemas': 0,
            'transformadores_criticos': 0,
            'alimentadores_total': 0
        }
    
    metrics = {
        'total_transformadores': len(df),
        'total_usuarios': df['Q_Usuarios'].sum() if 'Q_Usuarios' in df.columns else 0,
        'capacidad_total_mva': df['Potencia'].sum() / 1000 if 'Potencia' in df.columns else 0,
        'tasa_problemas': (df['Resultado'] != 'Correcta').mean() * 100 if 'Resultado' in df.columns else 0,
        'transformadores_criticos': len(df[df.get('nivel_vulnerabilidad', '') == 'Crítica']) if 'nivel_vulnerabilidad' in df.columns else 0,
        'alimentadores_total': df['Alimentador'].nunique() if 'Alimentador' in df.columns else 0
    }
    
    return metrics

def get_quality_distribution():
    """Obtiene distribución de estados de calidad"""
    df = load_transformadores_completo()
    
    if df.empty or 'Resultado' not in df.columns:
        return pd.DataFrame()
    
    return df['Resultado'].value_counts().reset_index()

def get_vulnerability_distribution():
    """Obtiene distribución de niveles de vulnerabilidad"""
    df = load_transformadores_completo()
    
    if df.empty or 'nivel_vulnerabilidad' not in df.columns:
        return pd.DataFrame()
    
    # Orden específico
    order = ['Crítica', 'Alta', 'Media', 'Baja', 'Mínima']
    dist = df['nivel_vulnerabilidad'].value_counts()
    dist = dist.reindex(order, fill_value=0)
    
    return dist.reset_index()

def filter_transformadores(branch=None, quality=None, vulnerability=None, feeder=None):
    """
    Filtra transformadores según criterios
    
    Args:
        branch: Sucursal específica o 'all'
        quality: Estado de calidad o 'all'
        vulnerability: Nivel de vulnerabilidad o 'all'
        feeder: Alimentador específico o None
    """
    df = load_transformadores_completo()
    
    if df.empty:
        return df
    
    # Aplicar filtros
    if branch and branch != 'all' and 'N_Sucursal' in df.columns:
        df = df[df['N_Sucursal'] == branch]
    
    if quality and quality != 'all' and 'Resultado' in df.columns:
        df = df[df['Resultado'] == quality]
    
    if vulnerability and vulnerability != 'all' and 'nivel_vulnerabilidad' in df.columns:
        df = df[df['nivel_vulnerabilidad'] == vulnerability]
    
    if feeder and 'Alimentador' in df.columns:
        df = df[df['Alimentador'] == feeder]
    
    return df

def get_top_critical_transformers(n=10):
    """Obtiene los N transformadores más críticos"""
    df = load_transformadores_completo()
    
    if df.empty:
        return pd.DataFrame()
    
    # Determinar columna de código
    codigo_col = 'Codigo' if 'Codigo' in df.columns else 'Codigoct' if 'Codigoct' in df.columns else None
    
    # Ordenar por índice de vulnerabilidad compuesto
    if 'criticidad_compuesta' in df.columns:
        # Usar criticidad_compuesta que sí existe
        top_df = df.nlargest(n, 'criticidad_compuesta')
        cols = [codigo_col, 'N_Sucursal', 'N_Localida', 'Alimentador', 
                'Potencia', 'Q_Usuarios', 'Resultado', 'criticidad_compuesta']
        # Filtrar solo columnas que existen
        cols = [col for col in cols if col in df.columns]
        return top_df[cols]
    elif 'indice_vulnerabilidad_compuesto' in df.columns:
        return df.nlargest(n, 'indice_vulnerabilidad_compuesto')[
            [codigo_col, 'N_Sucursal', 'N_Localida', 'Alimentador', 
             'Potencia', 'Q_Usuarios', 'Resultado',
             'indice_vulnerabilidad_compuesto', 'modo_falla_probable']
        ]
    else:
        # Fallback: usar estado de calidad
        return df[df['Resultado'] == 'Fallida'].head(n)

def get_feeder_summary():
    """Obtiene resumen por alimentador"""
    df = load_transformadores_completo()
    feeders = load_alimentadores()
    
    if df.empty or 'Alimentador' not in df.columns:
        return pd.DataFrame()
    
    try:
        # Agregar por alimentador
        # Usar la primera columna disponible como contador
        count_col = 'Codigo' if 'Codigo' in df.columns else 'Codigoct' if 'Codigoct' in df.columns else df.columns[0]
        
        summary = df.groupby('Alimentador').agg({
            count_col: 'count',
            'Potencia': 'sum',
            'Q_Usuarios': 'sum',
            'Resultado': lambda x: (x != 'Correcta').mean() if 'Resultado' in df.columns else 0
        }).rename(columns={
            count_col: 'num_transformadores',
            'Potencia': 'potencia_total_kva',
            'Resultado': 'tasa_problemas'
        })
        
        # Agregar métricas adicionales si existen
        if 'indice_vulnerabilidad_compuesto' in df.columns:
            summary['vulnerabilidad_promedio'] = df.groupby('Alimentador')['indice_vulnerabilidad_compuesto'].mean()
        
        # Merge con datos de alimentadores si disponible
        if not feeders.empty and 'Alimentador' in feeders.columns:
            cols_to_merge = [col for col in ['Alimentador', 'extension_x_km', 'extension_y_km', 'es_lineal'] 
                           if col in feeders.columns]
            if len(cols_to_merge) > 1:
                summary = summary.merge(
                    feeders[cols_to_merge], 
                    on='Alimentador', 
                    how='left'
                )
        
        return summary.round(3)
    except Exception as e:
        print(f"Error en get_feeder_summary: {e}")
        return pd.DataFrame()

# Cache para coordenadas válidas
@lru_cache(maxsize=1)
def get_valid_coordinates():
    """Obtiene transformadores con coordenadas válidas para mapas"""
    df = load_transformadores_completo()
    
    if df.empty:
        return pd.DataFrame()
    
    # Filtrar coordenadas válidas
    mask = (
        df['Coord_X'].notna() & 
        df['Coord_Y'].notna() &
        (df['Coord_X'] != 0) &
        (df['Coord_Y'] != 0)
    )
    
    return df[mask]