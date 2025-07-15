#!/usr/bin/env python3
"""
FASE 0: Análisis de Correlación Espacial
========================================
Objetivo: Analizar patrones espaciales y correlaciones dentro de alimentadores

Este script analiza:
1. Distribución espacial de transformadores por alimentador
2. Patrones de agrupamiento (clustering espacial)
3. Correlación entre distancia y estado de calidad
4. Identificación de patrones lineales vs radiales
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import warnings
from datetime import datetime
from scipy.spatial import distance_matrix, ConvexHull
from scipy.stats import pearsonr, spearmanr
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Ellipse
import matplotlib.patches as mpatches

warnings.filterwarnings('ignore')

# Configuración
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
NETWORK_DIR = PROCESSED_DIR / 'network_analysis'
REPORTS_DIR = BASE_DIR / 'reports'
FIGURES_DIR = REPORTS_DIR / 'figures'

# Crear directorios si no existen
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Cargar datos enriquecidos de transformadores y alimentadores"""
    transformers_df = pd.read_csv(NETWORK_DIR / 'transformadores_con_topologia.csv')
    feeders_df = pd.read_csv(NETWORK_DIR / 'alimentadores_caracterizados.csv')
    
    print(f"\n📊 Datos cargados:")
    print(f"   - {len(transformers_df)} transformadores con topología")
    print(f"   - {len(feeders_df)} alimentadores caracterizados")
    
    return transformers_df, feeders_df

def analyze_spatial_distribution(transformers_df, feeder):
    """Analizar distribución espacial de transformadores en un alimentador"""
    
    # Filtrar transformadores del alimentador con coordenadas válidas
    feeder_trafos = transformers_df[
        (transformers_df['Alimentador'] == feeder) & 
        (transformers_df['Coord_X'].notna()) &
        (transformers_df['Coord_Y'].notna())
    ].copy()
    
    if len(feeder_trafos) < 3:
        return None
    
    coords = feeder_trafos[['Coord_X', 'Coord_Y']].values
    
    # Análisis básico
    analysis = {
        'alimentador': feeder,
        'num_transformadores': len(feeder_trafos),
        'num_correcta': len(feeder_trafos[feeder_trafos['Resultado'] == 'Correcta']),
        'num_penalizada': len(feeder_trafos[feeder_trafos['Resultado'] == 'Penalizada']),
        'num_fallida': len(feeder_trafos[feeder_trafos['Resultado'] == 'Fallida']),
    }
    
    # 1. Análisis de vecindad (K-nearest neighbors)
    if len(coords) >= 5:
        nbrs = NearestNeighbors(n_neighbors=min(5, len(coords)))
        nbrs.fit(coords)
        distances, indices = nbrs.kneighbors(coords)
        
        # Distancia promedio a los k vecinos más cercanos
        analysis['dist_promedio_k_vecinos'] = distances[:, 1:].mean()  # Excluir distancia a sí mismo
        analysis['dist_std_k_vecinos'] = distances[:, 1:].std()
        
        # Índice de dispersión (coeficiente de variación)
        if analysis['dist_promedio_k_vecinos'] > 0:
            analysis['indice_dispersion'] = analysis['dist_std_k_vecinos'] / analysis['dist_promedio_k_vecinos']
        else:
            analysis['indice_dispersion'] = 0
    
    # 2. Análisis de linealidad
    if len(coords) >= 3:
        # Ajustar línea de regresión
        X = coords[:, 0].reshape(-1, 1)
        y = coords[:, 1]
        reg = LinearRegression().fit(X, y)
        
        # R-squared como medida de linealidad
        y_pred = reg.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        if ss_tot > 0:
            r_squared = 1 - (ss_res / ss_tot)
        else:
            r_squared = 0
        
        analysis['r_squared_linealidad'] = r_squared
        analysis['es_lineal'] = r_squared > 0.7  # Umbral para considerar lineal
        
        # Ángulo de la línea
        analysis['angulo_principal'] = np.degrees(np.arctan(reg.coef_[0]))
    
    # 3. Análisis de agrupamiento (clustering coefficient)
    if len(coords) >= 10:
        # Calcular clustering coefficient basado en densidad local
        dist_matrix = distance_matrix(coords, coords)
        np.fill_diagonal(dist_matrix, np.inf)
        
        # Radio de vecindad (percentil 20 de todas las distancias)
        radius = np.percentile(dist_matrix[dist_matrix < np.inf], 20)
        
        # Contar vecinos dentro del radio para cada punto
        neighbors_count = np.sum(dist_matrix < radius, axis=1)
        analysis['clustering_coefficient'] = np.mean(neighbors_count) / (len(coords) - 1)
    
    # 4. Análisis de correlación espacial de fallas
    if len(feeder_trafos) >= 10:
        # Crear matriz de estado (1 = problema, 0 = correcto)
        estado_binario = (feeder_trafos['Resultado'] != 'Correcta').astype(int).values
        
        # Calcular autocorrelación espacial (Moran's I simplificado)
        W = 1 / (dist_matrix + 1e-10)  # Matriz de pesos (inverso de distancia)
        np.fill_diagonal(W, 0)
        W = W / W.sum()  # Normalizar
        
        # Moran's I
        n = len(estado_binario)
        y_mean = estado_binario.mean()
        y_dev = estado_binario - y_mean
        
        numerator = np.sum(W * np.outer(y_dev, y_dev))
        denominator = np.sum(y_dev ** 2)
        
        if denominator > 0:
            morans_i = (n / np.sum(W)) * (numerator / denominator)
            analysis['morans_i'] = morans_i
            analysis['autocorrelacion_espacial'] = 'positiva' if morans_i > 0.1 else 'ninguna' if morans_i > -0.1 else 'negativa'
        else:
            analysis['morans_i'] = 0
            analysis['autocorrelacion_espacial'] = 'no_calculable'
    
    # 5. Patrón de distribución
    if analysis.get('es_lineal', False):
        analysis['patron_distribucion'] = 'lineal'
    elif analysis.get('clustering_coefficient', 0) > 0.3:
        analysis['patron_distribucion'] = 'agrupado'
    elif analysis.get('indice_dispersion', 0) < 0.5:
        analysis['patron_distribucion'] = 'regular'
    else:
        analysis['patron_distribucion'] = 'aleatorio'
    
    return analysis

def analyze_distance_quality_correlation(transformers_df):
    """Analizar correlación entre distancia al centroide y calidad"""
    
    correlations = []
    
    # Analizar por alimentador
    for feeder in transformers_df['Alimentador'].unique():
        if pd.isna(feeder):
            continue
            
        feeder_data = transformers_df[
            (transformers_df['Alimentador'] == feeder) &
            (transformers_df['dist_a_centroide_km'].notna())
        ].copy()
        
        if len(feeder_data) < 10:
            continue
        
        # Crear variable binaria de problemas
        feeder_data['tiene_problema'] = (feeder_data['Resultado'] != 'Correcta').astype(int)
        
        # Calcular correlación
        if feeder_data['dist_a_centroide_km'].std() > 0:
            corr, p_value = spearmanr(
                feeder_data['dist_a_centroide_km'],
                feeder_data['tiene_problema']
            )
            
            correlations.append({
                'alimentador': feeder,
                'num_transformadores': len(feeder_data),
                'correlacion_distancia_problema': corr,
                'p_value': p_value,
                'significativo': p_value < 0.05,
                'interpretacion': 'Mayor distancia = más problemas' if corr > 0.2 else 
                                'Mayor distancia = menos problemas' if corr < -0.2 else 
                                'Sin correlación clara'
            })
    
    return pd.DataFrame(correlations)

def identify_spatial_clusters(transformers_df):
    """Identificar clusters espaciales de problemas"""
    
    clusters_info = []
    
    for feeder in transformers_df['Alimentador'].unique():
        if pd.isna(feeder):
            continue
            
        feeder_data = transformers_df[
            (transformers_df['Alimentador'] == feeder) &
            (transformers_df['Coord_X'].notna())
        ].copy()
        
        if len(feeder_data) < 5:
            continue
        
        # Solo transformadores con problemas
        problem_trafos = feeder_data[feeder_data['Resultado'] != 'Correcta']
        
        if len(problem_trafos) < 3:
            continue
        
        coords_all = feeder_data[['Coord_X', 'Coord_Y']].values
        coords_problems = problem_trafos[['Coord_X', 'Coord_Y']].values
        
        # Calcular densidad de problemas en diferentes radios
        radii = [0.01, 0.05, 0.1]  # En grados (~1km, 5km, 10km)
        
        for radius in radii:
            # Para cada transformador con problema, contar vecinos problemáticos
            problem_neighbors = []
            
            for i, coord in enumerate(coords_problems):
                # Distancia a todos los otros transformadores con problemas
                distances = np.sqrt(np.sum((coords_problems - coord)**2, axis=1))
                n_neighbors = np.sum(distances <= radius) - 1  # Excluir el mismo punto
                problem_neighbors.append(n_neighbors)
            
            if len(problem_neighbors) > 0:
                max_neighbors = max(problem_neighbors)
                if max_neighbors >= 2:  # Al menos 2 vecinos problemáticos
                    hotspot_idx = problem_neighbors.index(max_neighbors)
                    hotspot_coord = coords_problems[hotspot_idx]
                    
                    clusters_info.append({
                        'alimentador': feeder,
                        'radio_km': radius * 111,  # Aproximación
                        'coord_x_hotspot': hotspot_coord[0],
                        'coord_y_hotspot': hotspot_coord[1],
                        'transformadores_problema_en_hotspot': max_neighbors + 1,
                        'densidad_problema_hotspot': (max_neighbors + 1) / (np.pi * (radius * 111)**2)
                    })
    
    return pd.DataFrame(clusters_info)

def generate_spatial_visualizations(transformers_df, spatial_patterns, selected_feeders):
    """Generar visualizaciones de patrones espaciales"""
    
    # Seleccionar alimentadores representativos para visualizar
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    for idx, feeder in enumerate(selected_feeders[:4]):
        ax = axes[idx]
        
        feeder_data = transformers_df[
            (transformers_df['Alimentador'] == feeder) &
            (transformers_df['Coord_X'].notna())
        ].copy()
        
        if len(feeder_data) == 0:
            ax.text(0.5, 0.5, f'Sin datos para {feeder}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Alimentador: {feeder}')
            continue
        
        # Colores por estado
        colors = {'Correcta': 'green', 'Penalizada': 'yellow', 'Fallida': 'red'}
        
        for estado, color in colors.items():
            data = feeder_data[feeder_data['Resultado'] == estado]
            if len(data) > 0:
                ax.scatter(data['Coord_X'], data['Coord_Y'], 
                         c=color, s=50, alpha=0.6, 
                         edgecolors='black', linewidth=0.5,
                         label=f'{estado} ({len(data)})')
        
        # Agregar centroide
        if 'alimentador_centroid_x' in feeder_data.columns:
            centroid_x = feeder_data['alimentador_centroid_x'].iloc[0]
            centroid_y = feeder_data['alimentador_centroid_y'].iloc[0]
            if not pd.isna(centroid_x):
                ax.scatter(centroid_x, centroid_y, 
                         c='blue', s=200, marker='*', 
                         edgecolors='black', linewidth=2,
                         label='Centroide', zorder=5)
        
        # Agregar información del patrón
        pattern_info = spatial_patterns[spatial_patterns['alimentador'] == feeder]
        if not pattern_info.empty:
            pattern = pattern_info.iloc[0]
            info_text = f"Patrón: {pattern.get('patron_distribucion', 'N/A')}"
            if 'morans_i' in pattern:
                info_text += f"\nMoran's I: {pattern['morans_i']:.3f}"
            ax.text(0.02, 0.98, info_text, 
                   transform=ax.transAxes, 
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                   verticalalignment='top', fontsize=8)
        
        ax.set_xlabel('Longitud')
        ax.set_ylabel('Latitud')
        ax.set_title(f'Alimentador: {feeder}')
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Igualar aspecto
        ax.set_aspect('equal', adjustable='box')
    
    plt.suptitle('Patrones Espaciales en Alimentadores Seleccionados', fontsize=14)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'spatial_patterns_feeders.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Segunda figura: Resumen de patrones
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Distribución de patrones
    pattern_counts = spatial_patterns['patron_distribucion'].value_counts()
    ax1.pie(pattern_counts.values, labels=pattern_counts.index, 
            autopct='%1.1f%%', startangle=90)
    ax1.set_title('Distribución de Patrones Espaciales')
    
    # Autocorrelación espacial
    autocorr_counts = spatial_patterns['autocorrelacion_espacial'].value_counts()
    colors_autocorr = {'positiva': 'red', 'ninguna': 'gray', 'negativa': 'blue', 
                      'no_calculable': 'lightgray'}
    bars = ax2.bar(autocorr_counts.index, autocorr_counts.values,
                   color=[colors_autocorr.get(x, 'gray') for x in autocorr_counts.index])
    ax2.set_xlabel('Tipo de Autocorrelación Espacial')
    ax2.set_ylabel('Número de Alimentadores')
    ax2.set_title('Autocorrelación Espacial de Fallas')
    
    # Agregar valores en las barras
    for bar, value in zip(bars, autocorr_counts.values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(value), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'spatial_patterns_summary.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Visualizaciones guardadas en: {FIGURES_DIR}")

def save_results(spatial_patterns, distance_correlations, spatial_clusters):
    """Guardar resultados del análisis espacial"""
    
    # Guardar patrones espaciales
    spatial_patterns.to_csv(NETWORK_DIR / 'patrones_espaciales_alimentadores.csv', index=False)
    print(f"✅ Patrones espaciales guardados: {NETWORK_DIR / 'patrones_espaciales_alimentadores.csv'}")
    
    # Guardar correlaciones distancia-calidad
    if not distance_correlations.empty:
        distance_correlations.to_csv(NETWORK_DIR / 'correlacion_distancia_calidad.csv', index=False)
        print(f"✅ Correlaciones distancia-calidad guardadas: {NETWORK_DIR / 'correlacion_distancia_calidad.csv'}")
    
    # Guardar clusters espaciales
    if not spatial_clusters.empty:
        spatial_clusters.to_csv(NETWORK_DIR / 'clusters_espaciales_problemas.csv', index=False)
        print(f"✅ Clusters espaciales guardados: {NETWORK_DIR / 'clusters_espaciales_problemas.csv'}")
    
    # Generar reporte resumen
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Estadísticas de patrones
    pattern_stats = spatial_patterns['patron_distribucion'].value_counts().to_dict()
    autocorr_stats = spatial_patterns['autocorrelacion_espacial'].value_counts().to_dict()
    
    # Correlaciones significativas
    if not distance_correlations.empty:
        sig_correlations = distance_correlations[
            distance_correlations['significativo'] == True
        ]['interpretacion'].value_counts().to_dict()
    else:
        sig_correlations = {}
    
    report = {
        'timestamp': timestamp,
        'resumen_ejecutivo': {
            'alimentadores_analizados': len(spatial_patterns),
            'patrones_identificados': pattern_stats,
            'autocorrelacion_espacial': autocorr_stats,
            'correlaciones_significativas': len(distance_correlations[
                distance_correlations['significativo'] == True
            ]) if not distance_correlations.empty else 0,
        },
        'hallazgos_principales': {
            'alimentadores_lineales': len(spatial_patterns[
                spatial_patterns['es_lineal'] == True
            ]),
            'alimentadores_agrupados': pattern_stats.get('agrupado', 0),
            'autocorrelacion_positiva': autocorr_stats.get('positiva', 0),
            'interpretacion_correlaciones': sig_correlations,
        },
        'hotspots_identificados': len(spatial_clusters) if not spatial_clusters.empty else 0,
        'ejemplos_patrones': {
            'mas_lineal': spatial_patterns.nlargest(1, 'r_squared_linealidad')[
                ['alimentador', 'r_squared_linealidad', 'num_transformadores']
            ].to_dict('records')[0] if 'r_squared_linealidad' in spatial_patterns.columns else None,
            'mas_agrupado': spatial_patterns.nlargest(1, 'clustering_coefficient')[
                ['alimentador', 'clustering_coefficient', 'num_transformadores']
            ].to_dict('records')[0] if 'clustering_coefficient' in spatial_patterns.columns else None,
            'mayor_autocorrelacion': spatial_patterns.nlargest(1, 'morans_i')[
                ['alimentador', 'morans_i', 'autocorrelacion_espacial']
            ].to_dict('records')[0] if 'morans_i' in spatial_patterns.columns else None,
        }
    }
    
    with open(REPORTS_DIR / '01_spatial_correlation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"✅ Reporte guardado: {REPORTS_DIR / '01_spatial_correlation_report.json'}")

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("FASE 0: ANÁLISIS DE CORRELACIÓN ESPACIAL")
    print("="*60)
    
    # Cargar datos
    transformers_df, feeders_df = load_data()
    
    # Analizar patrones espaciales por alimentador
    print("\n🔍 Analizando patrones espaciales por alimentador...")
    spatial_patterns = []
    
    for feeder in transformers_df['Alimentador'].unique():
        if pd.isna(feeder):
            continue
        
        analysis = analyze_spatial_distribution(transformers_df, feeder)
        if analysis:
            spatial_patterns.append(analysis)
    
    spatial_patterns_df = pd.DataFrame(spatial_patterns)
    print(f"✅ {len(spatial_patterns_df)} alimentadores analizados espacialmente")
    
    # Analizar correlación distancia-calidad
    print("\n📊 Analizando correlación entre distancia y calidad...")
    distance_correlations = analyze_distance_quality_correlation(transformers_df)
    if not distance_correlations.empty:
        print(f"✅ {len(distance_correlations)} correlaciones calculadas")
        print(f"   - Significativas: {len(distance_correlations[distance_correlations['significativo']])}")
    
    # Identificar clusters espaciales de problemas
    print("\n🎯 Identificando clusters espaciales de problemas...")
    spatial_clusters = identify_spatial_clusters(transformers_df)
    if not spatial_clusters.empty:
        print(f"✅ {len(spatial_clusters)} hotspots identificados")
    
    # Seleccionar alimentadores para visualización
    # Priorizar: diferentes patrones, tamaños medianos-grandes, con datos
    selected_feeders = []
    
    # Un lineal
    linear_feeders = spatial_patterns_df[
        (spatial_patterns_df['es_lineal'] == True) & 
        (spatial_patterns_df['num_transformadores'] >= 20)
    ].nlargest(1, 'r_squared_linealidad')
    if not linear_feeders.empty:
        selected_feeders.append(linear_feeders.iloc[0]['alimentador'])
    
    # Un agrupado
    clustered_feeders = spatial_patterns_df[
        (spatial_patterns_df['patron_distribucion'] == 'agrupado') &
        (spatial_patterns_df['num_transformadores'] >= 20)
    ]
    if not clustered_feeders.empty:
        selected_feeders.append(clustered_feeders.iloc[0]['alimentador'])
    
    # Uno con alta autocorrelación
    if 'morans_i' in spatial_patterns_df.columns:
        autocorr_feeders = spatial_patterns_df[
            (spatial_patterns_df['autocorrelacion_espacial'] == 'positiva') &
            (spatial_patterns_df['num_transformadores'] >= 20)
        ].nlargest(1, 'morans_i')
        if not autocorr_feeders.empty:
            selected_feeders.append(autocorr_feeders.iloc[0]['alimentador'])
    
    # Completar con los más grandes
    large_feeders = spatial_patterns_df.nlargest(10, 'num_transformadores')
    for _, row in large_feeders.iterrows():
        if row['alimentador'] not in selected_feeders:
            selected_feeders.append(row['alimentador'])
        if len(selected_feeders) >= 4:
            break
    
    # Generar visualizaciones
    print("\n📈 Generando visualizaciones...")
    generate_spatial_visualizations(transformers_df, spatial_patterns_df, selected_feeders)
    
    # Guardar resultados
    print("\n💾 Guardando resultados...")
    save_results(spatial_patterns_df, distance_correlations, spatial_clusters)
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DEL ANÁLISIS ESPACIAL")
    print("="*60)
    
    if not spatial_patterns_df.empty:
        print(f"\n📊 Patrones de distribución encontrados:")
        for pattern, count in spatial_patterns_df['patron_distribucion'].value_counts().items():
            print(f"   - {pattern}: {count} alimentadores")
    
    if 'autocorrelacion_espacial' in spatial_patterns_df.columns:
        print(f"\n📊 Autocorrelación espacial de fallas:")
        for tipo, count in spatial_patterns_df['autocorrelacion_espacial'].value_counts().items():
            print(f"   - {tipo}: {count} alimentadores")
    
    if not distance_correlations.empty:
        sig_count = len(distance_correlations[distance_correlations['significativo']])
        print(f"\n📊 Correlaciones distancia-problema:")
        print(f"   - Significativas: {sig_count}/{len(distance_correlations)}")
    
    print("\n✅ Análisis de correlación espacial completado exitosamente!")

if __name__ == "__main__":
    main()