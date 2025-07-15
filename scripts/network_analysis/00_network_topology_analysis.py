#!/usr/bin/env python3
"""
FASE 0: Análisis de Topología de Red
=====================================
Objetivo: Mapear y entender la estructura de la red eléctrica EDERSA

Este script analiza:
1. Estructura alimentador-transformador
2. Distribución geográfica de alimentadores
3. Características básicas de la red
4. Patrones de distribución espacial
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import warnings
from datetime import datetime
from scipy.spatial import distance_matrix
from scipy.stats import skew, kurtosis
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')

# Configuración
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
REPORTS_DIR = BASE_DIR / 'reports'
NETWORK_DIR = PROCESSED_DIR / 'network_analysis'

# Crear directorios si no existen
NETWORK_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Cargar datos de transformadores"""
    df = pd.read_csv(PROCESSED_DIR / 'transformers_analysis.csv')
    print(f"\n📊 Datos cargados: {len(df)} transformadores")
    return df

def analyze_feeders(df):
    """Analizar características de cada alimentador"""
    
    feeder_stats = []
    
    for feeder in df['Alimentador'].unique():
        if pd.isna(feeder):
            continue
            
        feeder_df = df[df['Alimentador'] == feeder]
        
        # Estadísticas básicas
        stats = {
            'alimentador': feeder,
            'num_transformadores': len(feeder_df),
            'potencia_total_mva': feeder_df['Potencia'].sum() / 1000,
            'usuarios_totales': feeder_df['Q_Usuarios'].sum(),
            
            # Distribución de estados
            'num_correcta': len(feeder_df[feeder_df['Resultado'] == 'Correcta']),
            'num_penalizada': len(feeder_df[feeder_df['Resultado'] == 'Penalizada']),
            'num_fallida': len(feeder_df[feeder_df['Resultado'] == 'Fallida']),
            'tasa_problemas': len(feeder_df[feeder_df['Resultado'] != 'Correcta']) / len(feeder_df),
            
            # Sucursales y localidades
            'sucursales': list(feeder_df['N_Sucursal'].unique()),
            'num_sucursales': feeder_df['N_Sucursal'].nunique(),
            'localidades': list(feeder_df['N_Localida'].unique()),
            'num_localidades': feeder_df['N_Localida'].nunique(),
        }
        
        # Análisis geográfico si hay coordenadas
        coords_df = feeder_df.dropna(subset=['Coord_X', 'Coord_Y'])
        if len(coords_df) >= 2:
            coords = coords_df[['Coord_X', 'Coord_Y']].values
            
            # Extensión geográfica
            stats['coord_x_min'] = coords[:, 0].min()
            stats['coord_x_max'] = coords[:, 0].max()
            stats['coord_y_min'] = coords[:, 1].min()
            stats['coord_y_max'] = coords[:, 1].max()
            stats['extension_x_deg'] = stats['coord_x_max'] - stats['coord_x_min']
            stats['extension_y_deg'] = stats['coord_y_max'] - stats['coord_y_min']
            
            # Estimación de área y longitud
            # Aproximación: 1 grado ≈ 111 km en latitud, variable en longitud
            lat_media = coords[:, 1].mean()
            km_por_grado_lon = 111 * np.cos(np.radians(lat_media))
            km_por_grado_lat = 111
            
            stats['extension_x_km'] = stats['extension_x_deg'] * km_por_grado_lon
            stats['extension_y_km'] = stats['extension_y_deg'] * km_por_grado_lat
            stats['area_bbox_km2'] = stats['extension_x_km'] * stats['extension_y_km']
            
            # Centro de gravedad
            stats['centroid_x'] = coords[:, 0].mean()
            stats['centroid_y'] = coords[:, 1].mean()
            
            # Dispersión
            stats['std_x'] = coords[:, 0].std()
            stats['std_y'] = coords[:, 1].std()
            
            # Densidad
            if stats['area_bbox_km2'] > 0:
                stats['densidad_trafos_km2'] = len(coords_df) / stats['area_bbox_km2']
            else:
                stats['densidad_trafos_km2'] = np.inf
            
            # Análisis de forma/patrón
            if len(coords) >= 3:
                # Distancias entre todos los pares
                dist_matrix = distance_matrix(coords, coords)
                np.fill_diagonal(dist_matrix, np.inf)
                
                # Distancia al vecino más cercano para cada transformador
                min_distances = dist_matrix.min(axis=1)
                stats['dist_vecino_min_deg'] = min_distances.min()
                stats['dist_vecino_promedio_deg'] = min_distances.mean()
                stats['dist_vecino_max_deg'] = min_distances.max()
                
                # Convertir a km
                stats['dist_vecino_promedio_km'] = stats['dist_vecino_promedio_deg'] * np.sqrt(
                    (km_por_grado_lon**2 + km_por_grado_lat**2) / 2
                )
                
                # Distancia máxima (diámetro)
                max_dist_idx = np.unravel_index(dist_matrix.argmax(), dist_matrix.shape)
                stats['diametro_deg'] = dist_matrix[max_dist_idx]
                stats['diametro_km'] = stats['diametro_deg'] * np.sqrt(
                    (km_por_grado_lon**2 + km_por_grado_lat**2) / 2
                )
                
                # Índice de forma (ratio entre las extensiones)
                if stats['extension_y_deg'] > 0:
                    stats['ratio_forma'] = stats['extension_x_deg'] / stats['extension_y_deg']
                else:
                    stats['ratio_forma'] = np.inf
                
                # Análisis de linealidad
                # Si ratio_forma es muy alto o muy bajo, sugiere distribución lineal
                stats['es_lineal'] = stats['ratio_forma'] > 3 or stats['ratio_forma'] < 0.33
                
                # Compacidad (qué tan agrupados están vs el bbox)
                area_convex_hull = estimate_convex_hull_area(coords)
                if stats['area_bbox_km2'] > 0:
                    stats['compacidad'] = area_convex_hull / stats['area_bbox_km2']
                else:
                    stats['compacidad'] = 0
        
        else:
            # Sin suficientes coordenadas
            stats.update({
                'coord_x_min': np.nan, 'coord_x_max': np.nan,
                'coord_y_min': np.nan, 'coord_y_max': np.nan,
                'extension_x_deg': 0, 'extension_y_deg': 0,
                'extension_x_km': 0, 'extension_y_km': 0,
                'area_bbox_km2': 0, 'centroid_x': np.nan,
                'centroid_y': np.nan, 'std_x': 0, 'std_y': 0,
                'densidad_trafos_km2': np.nan,
                'dist_vecino_promedio_km': np.nan,
                'diametro_km': 0, 'ratio_forma': np.nan,
                'es_lineal': False, 'compacidad': np.nan
            })
        
        feeder_stats.append(stats)
    
    return pd.DataFrame(feeder_stats)

def estimate_convex_hull_area(coords):
    """Estimar área del convex hull (simplificado)"""
    from scipy.spatial import ConvexHull
    try:
        hull = ConvexHull(coords)
        # Aproximación del área usando la fórmula del shoelace
        x = coords[hull.vertices, 0]
        y = coords[hull.vertices, 1]
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        
        # Convertir a km²
        lat_media = coords[:, 1].mean()
        km_por_grado_lon = 111 * np.cos(np.radians(lat_media))
        km_por_grado_lat = 111
        area_km2 = area * km_por_grado_lon * km_por_grado_lat
        
        return area_km2
    except:
        return 0

def analyze_network_patterns(df, feeder_stats):
    """Analizar patrones generales de la red"""
    
    patterns = {
        'resumen_general': {
            'total_alimentadores': len(feeder_stats),
            'total_transformadores': len(df),
            'total_usuarios': df['Q_Usuarios'].sum(),
            'potencia_total_mva': df['Potencia'].sum() / 1000,
            'tasa_problemas_global': len(df[df['Resultado'] != 'Correcta']) / len(df),
        },
        
        'distribucion_tamanos': {
            'alimentadores_pequenos': len(feeder_stats[feeder_stats['num_transformadores'] < 10]),
            'alimentadores_medianos': len(feeder_stats[(feeder_stats['num_transformadores'] >= 10) & 
                                                       (feeder_stats['num_transformadores'] < 50)]),
            'alimentadores_grandes': len(feeder_stats[feeder_stats['num_transformadores'] >= 50]),
        },
        
        'estadisticas_alimentadores': {
            'transformadores_promedio': feeder_stats['num_transformadores'].mean(),
            'transformadores_mediana': feeder_stats['num_transformadores'].median(),
            'transformadores_std': feeder_stats['num_transformadores'].std(),
            'usuarios_promedio': feeder_stats['usuarios_totales'].mean(),
            'extension_promedio_km': feeder_stats['diametro_km'].mean(),
            'densidad_promedio_km2': feeder_stats['densidad_trafos_km2'].mean(),
        },
        
        'patrones_geograficos': {
            'alimentadores_lineales': len(feeder_stats[feeder_stats['es_lineal'] == True]),
            'alimentadores_compactos': len(feeder_stats[feeder_stats['compacidad'] > 0.7]),
            'alimentadores_dispersos': len(feeder_stats[feeder_stats['compacidad'] < 0.3]),
        },
        
        'correlaciones_observadas': {}
    }
    
    # Calcular correlaciones
    numeric_cols = ['num_transformadores', 'potencia_total_mva', 'usuarios_totales',
                   'tasa_problemas', 'diametro_km', 'densidad_trafos_km2']
    
    for col in numeric_cols:
        if col in feeder_stats.columns:
            valid_data = feeder_stats[col].dropna()
            if len(valid_data) > 0:
                patterns['correlaciones_observadas'][f'{col}_vs_tasa_problemas'] = \
                    feeder_stats[[col, 'tasa_problemas']].corr().iloc[0, 1]
    
    return patterns

def enrich_transformers_data(df, feeder_stats):
    """Enriquecer datos de transformadores con información del alimentador"""
    
    # Crear diccionario de estadísticas por alimentador
    feeder_dict = feeder_stats.set_index('alimentador').to_dict('index')
    
    # Agregar columnas al dataframe de transformadores
    for col in ['diametro_km', 'densidad_trafos_km2', 'centroid_x', 'centroid_y', 
                'es_lineal', 'tasa_problemas']:
        df[f'alimentador_{col}'] = df['Alimentador'].map(
            lambda x: feeder_dict.get(x, {}).get(col, np.nan) if pd.notna(x) else np.nan
        )
    
    # Calcular distancia de cada transformador al centroide de su alimentador
    df['dist_a_centroide_km'] = df.apply(
        lambda row: calculate_distance_to_centroid(row) if pd.notna(row['Coord_X']) else np.nan,
        axis=1
    )
    
    # Posición relativa en el alimentador (0 = centro, 1 = borde)
    df['posicion_relativa'] = df.groupby('Alimentador')['dist_a_centroide_km'].transform(
        lambda x: x / x.max() if x.max() > 0 else 0
    )
    
    return df

def calculate_distance_to_centroid(row):
    """Calcular distancia al centroide del alimentador"""
    if pd.isna(row['alimentador_centroid_x']) or pd.isna(row['Coord_X']):
        return np.nan
    
    lat_media = (row['Coord_Y'] + row['alimentador_centroid_y']) / 2
    km_por_grado_lon = 111 * np.cos(np.radians(lat_media))
    km_por_grado_lat = 111
    
    dx = (row['Coord_X'] - row['alimentador_centroid_x']) * km_por_grado_lon
    dy = (row['Coord_Y'] - row['alimentador_centroid_y']) * km_por_grado_lat
    
    return np.sqrt(dx**2 + dy**2)

def generate_visualizations(df, feeder_stats):
    """Generar visualizaciones de la red"""
    
    try:
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Histograma de tamaños de alimentadores
        ax = axes[0, 0]
        ax.hist(feeder_stats['num_transformadores'], bins=30, edgecolor='black', alpha=0.7)
        ax.axvline(feeder_stats['num_transformadores'].median(), color='red', 
                   linestyle='--', label=f'Mediana: {feeder_stats["num_transformadores"].median():.0f}')
        ax.set_xlabel('Número de Transformadores')
        ax.set_ylabel('Número de Alimentadores')
        ax.set_title('Distribución de Tamaños de Alimentadores')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. Tasa de problemas vs tamaño
        ax = axes[0, 1]
        ax.scatter(feeder_stats['num_transformadores'], 
                   feeder_stats['tasa_problemas'] * 100,
                   alpha=0.6, s=60)
        ax.set_xlabel('Número de Transformadores')
        ax.set_ylabel('Tasa de Problemas (%)')
        ax.set_title('Tasa de Problemas vs Tamaño del Alimentador')
        ax.grid(True, alpha=0.3)
        
        # 3. Extensión geográfica (sin escala log por problemas con los datos)
        ax = axes[1, 0]
        valid_feeders = feeder_stats[(feeder_stats['diametro_km'] > 0) & 
                                    (feeder_stats['diametro_km'] < 1000) &  # Filtrar valores extremos
                                    (feeder_stats['densidad_trafos_km2'] > 0) & 
                                    (feeder_stats['densidad_trafos_km2'] < 100)]  # Filtrar valores extremos
        
        if len(valid_feeders) > 0:
            ax.scatter(valid_feeders['diametro_km'], 
                       valid_feeders['densidad_trafos_km2'],
                       alpha=0.6, s=60)
            ax.set_xlabel('Diámetro del Alimentador (km)')
            ax.set_ylabel('Densidad (transformadores/km²)')
            ax.set_title('Extensión vs Densidad de Alimentadores')
        else:
            ax.text(0.5, 0.5, 'Sin datos válidos para mostrar', 
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Extensión vs Densidad de Alimentadores')
        ax.grid(True, alpha=0.3)
        
        # 4. Top 10 alimentadores por tamaño
        ax = axes[1, 1]
        top10 = feeder_stats.nlargest(10, 'num_transformadores')
        ax.barh(range(len(top10)), top10['num_transformadores'])
        ax.set_yticks(range(len(top10)))
        ax.set_yticklabels(top10['alimentador'], fontsize=8)
        ax.set_xlabel('Número de Transformadores')
        ax.set_title('Top 10 Alimentadores por Tamaño')
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / 'network_topology_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Visualizaciones guardadas en: {REPORTS_DIR / 'network_topology_analysis.png'}")
    except Exception as e:
        print(f"⚠️ Error generando visualizaciones: {e}")
        print("Continuando con el análisis...")

def save_results(df, feeder_stats, patterns):
    """Guardar resultados del análisis"""
    
    # Guardar estadísticas de alimentadores
    feeder_stats.to_csv(NETWORK_DIR / 'alimentadores_caracterizados.csv', index=False)
    print(f"✅ Estadísticas de alimentadores guardadas: {NETWORK_DIR / 'alimentadores_caracterizados.csv'}")
    
    # Guardar transformadores enriquecidos
    df.to_csv(NETWORK_DIR / 'transformadores_con_topologia.csv', index=False)
    print(f"✅ Transformadores enriquecidos guardados: {NETWORK_DIR / 'transformadores_con_topologia.csv'}")
    
    # Guardar patrones de red
    with open(NETWORK_DIR / 'patrones_red.json', 'w', encoding='utf-8') as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False, default=str)
    print(f"✅ Patrones de red guardados: {NETWORK_DIR / 'patrones_red.json'}")
    
    # Generar reporte
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        'timestamp': timestamp,
        'resumen_ejecutivo': {
            'total_alimentadores': patterns['resumen_general']['total_alimentadores'],
            'total_transformadores': patterns['resumen_general']['total_transformadores'],
            'alimentadores_grandes': feeder_stats[feeder_stats['num_transformadores'] >= 50].shape[0],
            'alimentadores_problematicos': feeder_stats[feeder_stats['tasa_problemas'] > 0.5].shape[0],
            'extension_promedio_km': patterns['estadisticas_alimentadores']['extension_promedio_km'],
        },
        'hallazgos_clave': {
            'alimentadores_lineales': patterns['patrones_geograficos']['alimentadores_lineales'],
            'correlacion_tamano_problemas': patterns['correlaciones_observadas'].get(
                'num_transformadores_vs_tasa_problemas', 'No calculada'
            ),
            'top_5_alimentadores_criticos': feeder_stats.nlargest(5, 'tasa_problemas')[
                ['alimentador', 'num_transformadores', 'tasa_problemas', 'usuarios_totales']
            ].to_dict('records'),
            'top_5_alimentadores_grandes': feeder_stats.nlargest(5, 'num_transformadores')[
                ['alimentador', 'num_transformadores', 'diametro_km', 'usuarios_totales']
            ].to_dict('records'),
        }
    }
    
    with open(REPORTS_DIR / '00_network_topology_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"✅ Reporte guardado: {REPORTS_DIR / '00_network_topology_report.json'}")

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("FASE 0: ANÁLISIS DE TOPOLOGÍA DE RED")
    print("="*60)
    
    # Cargar datos
    df = load_data()
    
    # Analizar alimentadores
    print("\n📊 Analizando alimentadores...")
    feeder_stats = analyze_feeders(df)
    print(f"✅ {len(feeder_stats)} alimentadores analizados")
    
    # Analizar patrones de red
    print("\n🔍 Identificando patrones de red...")
    patterns = analyze_network_patterns(df, feeder_stats)
    
    # Enriquecer datos de transformadores
    print("\n🔧 Enriqueciendo datos de transformadores...")
    df_enriched = enrich_transformers_data(df, feeder_stats)
    
    # Generar visualizaciones
    print("\n📈 Generando visualizaciones...")
    generate_visualizations(df_enriched, feeder_stats)
    
    # Guardar resultados
    print("\n💾 Guardando resultados...")
    save_results(df_enriched, feeder_stats, patterns)
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DEL ANÁLISIS")
    print("="*60)
    print(f"📊 Total alimentadores: {patterns['resumen_general']['total_alimentadores']}")
    print(f"📊 Total transformadores: {patterns['resumen_general']['total_transformadores']}")
    print(f"📊 Tasa global de problemas: {patterns['resumen_general']['tasa_problemas_global']:.1%}")
    print(f"📊 Alimentadores lineales: {patterns['patrones_geograficos']['alimentadores_lineales']}")
    print(f"📊 Extensión promedio: {patterns['estadisticas_alimentadores']['extension_promedio_km']:.1f} km")
    
    print("\n✅ Análisis de topología completado exitosamente!")

if __name__ == "__main__":
    main()