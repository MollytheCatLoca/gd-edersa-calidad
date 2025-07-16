#!/usr/bin/env python3
"""
FASE 2.5 - Script 12: Refinamiento de Clustering con IAS 3.0
===========================================================
Re-optimización del clustering considerando los nuevos criterios de
Q at Night y disponibilidad de terreno. Busca agrupar transformadores
que maximicen el IAS 3.0 conjunto.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import hdbscan
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import MarkerCluster
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
CLUSTERING_DIR = REPORTS_DIR / "clustering"
REFINEMENT_V3_DIR = CLUSTERING_DIR / "refinement_v3"
REFINEMENT_V3_DIR.mkdir(exist_ok=True)

class ClusteringRefinementV3:
    """
    Refinamiento de clustering optimizado para IAS 3.0.
    Considera aspectos diurnos y nocturnos de manera integrada.
    """
    
    def __init__(self):
        """Inicializa el refinador con parámetros IAS 3.0"""
        self.feature_weights = {
            # Features espaciales (mantener clusters geográficamente coherentes)
            'coord_x': 1.0,
            'coord_y': 1.0,
            
            # Features eléctricas (importancia media)
            'impedancia_estimada': 0.5,
            'vulnerabilidad_termica': 0.5,
            'factor_utilizacion': 0.5,
            
            # Features IAS 3.0 (alta importancia)
            'perfil_residencial_score': 1.5,  # Para Q at Night
            'perfil_comercial_score': 1.0,    # Para coincidencia solar
            'zona_urbana_score': 1.2,         # Para disponibilidad terreno
            'potencia_total': 0.8,            # Para dimensionamiento
            
            # Features de calidad (importancia moderada)
            'tasa_falla': 0.7,
            'usuarios_afectados_norm': 0.7
        }
        
    def prepare_features_v3(self, df_transformers):
        """
        Prepara features optimizadas para IAS 3.0.
        """
        logger.info("Preparando features para clustering IAS 3.0...")
        
        # Crear scores de perfil para Q at Night
        df_transformers['perfil_residencial_score'] = 0
        df_transformers.loc[
            df_transformers['perfil_dominante'] == 'Residencial', 
            'perfil_residencial_score'
        ] = 1.0
        df_transformers.loc[
            df_transformers['perfil_dominante'] == 'Rural', 
            'perfil_residencial_score'
        ] = 0.8
        df_transformers.loc[
            df_transformers['perfil_dominante'] == 'Mixto', 
            'perfil_residencial_score'
        ] = 0.6
        
        # Score comercial/industrial para coincidencia solar
        df_transformers['perfil_comercial_score'] = 0
        df_transformers.loc[
            df_transformers['perfil_dominante'] == 'Comercial', 
            'perfil_comercial_score'
        ] = 1.0
        df_transformers.loc[
            df_transformers['perfil_dominante'] == 'Industrial', 
            'perfil_comercial_score'
        ] = 0.9
        
        # Score de zona urbana (inverso para disponibilidad de terreno)
        df_transformers['zona_urbana_score'] = 0
        # Basado en la clasificación de localidades del script 10
        urbanas_densas = ['CIPOLLETTI', 'GENERAL ROCA', 'VILLA REGINA', 
                         'CINCO SALTOS', 'ALLEN', 'NEUQUEN']
        urbanas_medias = ['CATRIEL', 'INGENIERO HUERGO', 'MAINQUE', 
                         'CERVANTES', 'GENERAL ENRIQUE GODOY']
        
        df_transformers['zona_urbana_score'] = 0.5  # Default periurbana
        
        for localidad in urbanas_densas:
            mask = df_transformers['Localidad'].str.upper().str.contains(localidad, na=False)
            df_transformers.loc[mask, 'zona_urbana_score'] = 1.0
            
        for localidad in urbanas_medias:
            mask = df_transformers['Localidad'].str.upper().str.contains(localidad, na=False)
            df_transformers.loc[mask, 'zona_urbana_score'] = 0.8
        
        # Detectar zonas rurales
        rural_keywords = ['RURAL', 'CHACRA', 'COLONIA', 'CAMPO']
        for keyword in rural_keywords:
            mask = df_transformers['Localidad'].str.upper().str.contains(keyword, na=False)
            df_transformers.loc[mask, 'zona_urbana_score'] = 0.2
        
        # Normalizar potencia
        df_transformers['potencia_total'] = df_transformers['Potencia Nom.(kVA)'] / 1000  # MVA
        
        # Normalizar usuarios afectados
        df_transformers['usuarios_afectados_norm'] = (
            df_transformers['Usu. Total'] / df_transformers['Usu. Total'].max()
        )
        
        # Preparar matriz de features
        feature_columns = list(self.feature_weights.keys())
        
        # Verificar columnas disponibles
        available_features = []
        for feat in feature_columns:
            if feat in df_transformers.columns:
                available_features.append(feat)
            elif feat == 'coord_x':
                if 'Coord_X' in df_transformers.columns:
                    df_transformers['coord_x'] = df_transformers['Coord_X']
                    available_features.append('coord_x')
                elif 'Longitud' in df_transformers.columns:
                    df_transformers['coord_x'] = df_transformers['Longitud']
                    available_features.append('coord_x')
            elif feat == 'coord_y':
                if 'Coord_Y' in df_transformers.columns:
                    df_transformers['coord_y'] = df_transformers['Coord_Y']
                    available_features.append('coord_y')
                elif 'Latitud' in df_transformers.columns:
                    df_transformers['coord_y'] = df_transformers['Latitud']
                    available_features.append('coord_y')
            else:
                logger.warning(f"Feature {feat} no disponible")
        
        # Crear matriz de features
        X = df_transformers[available_features].copy()
        
        # Imputar valores faltantes
        X = X.fillna(X.median())
        
        # Aplicar pesos
        for feat in available_features:
            if feat in self.feature_weights:
                X[feat] = X[feat] * self.feature_weights[feat]
        
        # Escalar features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, available_features, scaler
    
    def optimize_clustering_v3(self, X, min_clusters=10, max_clusters=20):
        """
        Optimiza parámetros de clustering para IAS 3.0.
        """
        logger.info(f"Optimizando clustering para {min_clusters}-{max_clusters} clusters...")
        
        results = []
        
        # 1. K-means con diferentes k
        for k in range(min_clusters, max_clusters + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            
            if len(np.unique(labels)) > 1:
                silhouette = silhouette_score(X, labels)
                davies_bouldin = davies_bouldin_score(X, labels)
                calinski = calinski_harabasz_score(X, labels)
                
                results.append({
                    'algorithm': 'KMeans',
                    'params': {'n_clusters': k},
                    'n_clusters': len(np.unique(labels)),
                    'silhouette': silhouette,
                    'davies_bouldin': davies_bouldin,
                    'calinski': calinski,
                    'labels': labels
                })
        
        # 2. DBSCAN con grid search
        eps_values = np.linspace(0.5, 3.0, 10)
        min_samples_values = [20, 30, 50, 70, 100]
        
        for eps in eps_values:
            for min_samples in min_samples_values:
                dbscan = DBSCAN(eps=eps, min_samples=min_samples)
                labels = dbscan.fit_predict(X)
                
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                
                if min_clusters <= n_clusters <= max_clusters and n_clusters > 1:
                    # Filtrar ruido para métricas
                    mask = labels != -1
                    if mask.sum() > 0:
                        silhouette = silhouette_score(X[mask], labels[mask])
                        davies_bouldin = davies_bouldin_score(X[mask], labels[mask])
                        calinski = calinski_harabasz_score(X[mask], labels[mask])
                        
                        results.append({
                            'algorithm': 'DBSCAN',
                            'params': {'eps': eps, 'min_samples': min_samples},
                            'n_clusters': n_clusters,
                            'n_noise': (labels == -1).sum(),
                            'silhouette': silhouette,
                            'davies_bouldin': davies_bouldin,
                            'calinski': calinski,
                            'labels': labels
                        })
        
        # 3. HDBSCAN
        for min_cluster_size in [50, 100, 150, 200]:
            clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
            labels = clusterer.fit_predict(X)
            
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            
            if min_clusters <= n_clusters <= max_clusters and n_clusters > 1:
                mask = labels != -1
                if mask.sum() > 0:
                    silhouette = silhouette_score(X[mask], labels[mask])
                    davies_bouldin = davies_bouldin_score(X[mask], labels[mask])
                    calinski = calinski_harabasz_score(X[mask], labels[mask])
                    
                    results.append({
                        'algorithm': 'HDBSCAN',
                        'params': {'min_cluster_size': min_cluster_size},
                        'n_clusters': n_clusters,
                        'n_noise': (labels == -1).sum(),
                        'silhouette': silhouette,
                        'davies_bouldin': davies_bouldin,
                        'calinski': calinski,
                        'labels': labels
                    })
        
        # Convertir a DataFrame para análisis
        df_results = pd.DataFrame(results)
        
        # Calcular score compuesto (normalizado)
        df_results['silhouette_norm'] = (
            (df_results['silhouette'] - df_results['silhouette'].min()) / 
            (df_results['silhouette'].max() - df_results['silhouette'].min())
        )
        
        df_results['davies_bouldin_norm'] = 1 - (
            (df_results['davies_bouldin'] - df_results['davies_bouldin'].min()) / 
            (df_results['davies_bouldin'].max() - df_results['davies_bouldin'].min())
        )
        
        df_results['calinski_norm'] = (
            (df_results['calinski'] - df_results['calinski'].min()) / 
            (df_results['calinski'].max() - df_results['calinski'].min())
        )
        
        # Score compuesto con pesos
        df_results['composite_score'] = (
            0.4 * df_results['silhouette_norm'] + 
            0.3 * df_results['davies_bouldin_norm'] + 
            0.3 * df_results['calinski_norm']
        )
        
        # Penalizar si hay mucho ruido (para DBSCAN/HDBSCAN)
        if 'n_noise' in df_results.columns:
            noise_penalty = df_results['n_noise'] / len(X)
            df_results['composite_score'] = df_results['composite_score'] * (1 - noise_penalty * 0.5)
        
        # Seleccionar mejor configuración
        best_idx = df_results['composite_score'].idxmax()
        best_config = df_results.iloc[best_idx]
        
        logger.info(f"Mejor configuración: {best_config['algorithm']} con score {best_config['composite_score']:.3f}")
        
        return df_results, best_config

def analyze_cluster_ias_potential(df_transformers, labels):
    """
    Analiza el potencial IAS 3.0 de cada cluster.
    """
    logger.info("Analizando potencial IAS 3.0 por cluster...")
    
    df_transformers['cluster_refined'] = labels
    
    # Calcular métricas por cluster
    cluster_analysis = []
    
    for cluster_id in np.unique(labels):
        if cluster_id == -1:  # Skip noise
            continue
            
        mask = df_transformers['cluster_refined'] == cluster_id
        cluster_data = df_transformers[mask]
        
        # Métricas básicas
        n_transformers = len(cluster_data)
        potencia_total = cluster_data['Potencia Nom.(kVA)'].sum() / 1000  # MVA
        usuarios_total = cluster_data['Usu. Total'].sum()
        
        # Potencial solar (basado en perfiles comerciales/industriales)
        comercial_industrial_pct = (
            cluster_data['perfil_dominante'].isin(['Comercial', 'Industrial']).sum() / 
            n_transformers
        )
        
        # Potencial nocturno (basado en perfiles residenciales)
        residencial_rural_pct = (
            cluster_data['perfil_dominante'].isin(['Residencial', 'Rural']).sum() / 
            n_transformers
        )
        
        # Disponibilidad de terreno (basado en zona)
        zona_urbana_avg = cluster_data['zona_urbana_score'].mean()
        terreno_score = 1 - zona_urbana_avg  # Inverso: menos urbano = más terreno
        
        # Criticidad
        if 'resultado_score' in cluster_data.columns:
            falla_rate = cluster_data['resultado_score'].mean()
        else:
            falla_rate = 0.5  # Default medio
        
        # Coordenadas del centroide
        if 'Coord_X' in cluster_data.columns:
            centroid_x = cluster_data['Coord_X'].mean()
            centroid_y = cluster_data['Coord_Y'].mean()
            coord_x_col = 'Coord_X'
            coord_y_col = 'Coord_Y'
        else:
            centroid_x = cluster_data['Longitud'].mean()
            centroid_y = cluster_data['Latitud'].mean()
            coord_x_col = 'Longitud'
            coord_y_col = 'Latitud'
        
        # Radio del cluster
        distances = np.sqrt(
            (cluster_data[coord_x_col] - centroid_x)**2 + 
            (cluster_data[coord_y_col] - centroid_y)**2
        )
        radio_km = distances.max() * 111  # Aproximación grados a km
        
        # Score potencial IAS 3.0 simplificado
        ias_potential = (
            0.3 * comercial_industrial_pct +  # Potencial diurno
            0.3 * residencial_rural_pct +      # Potencial nocturno
            0.2 * terreno_score +              # Disponibilidad terreno
            0.2 * (1 - falla_rate)             # Criticidad
        )
        
        cluster_analysis.append({
            'cluster_id': int(cluster_id),
            'n_transformers': n_transformers,
            'potencia_mva': round(potencia_total, 2),
            'usuarios_total': int(usuarios_total),
            'comercial_industrial_pct': round(comercial_industrial_pct, 3),
            'residencial_rural_pct': round(residencial_rural_pct, 3),
            'terreno_score': round(terreno_score, 3),
            'criticidad': round(1 - falla_rate, 3),
            'ias_potential': round(ias_potential, 3),
            'centroid_lat': centroid_y,
            'centroid_lon': centroid_x,
            'radio_km': round(radio_km, 2),
            'gd_estimada_mw': round(potencia_total * 0.3, 2)  # 30% de capacidad
        })
    
    df_clusters = pd.DataFrame(cluster_analysis)
    df_clusters = df_clusters.sort_values('ias_potential', ascending=False)
    
    return df_clusters, df_transformers

def create_refined_clustering_map(df_transformers, df_clusters):
    """
    Crea mapa de clustering refinado para IAS 3.0.
    """
    logger.info("Creando mapa de clustering refinado...")
    
    # Centro del mapa
    if 'Coord_Y' in df_transformers.columns:
        center_lat = df_transformers['Coord_Y'].mean()
        center_lon = df_transformers['Coord_X'].mean()
        coord_x_col = 'Coord_X'
        coord_y_col = 'Coord_Y'
    else:
        center_lat = df_transformers['Latitud'].mean()
        center_lon = df_transformers['Longitud'].mean()
        coord_x_col = 'Longitud'
        coord_y_col = 'Latitud'
    
    # Crear mapa
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Colores para clusters
    colors = plt.cm.tab20(np.linspace(0, 1, len(df_clusters)))
    color_map = {
        row['cluster_id']: f'#{int(colors[i][0]*255):02x}{int(colors[i][1]*255):02x}{int(colors[i][2]*255):02x}'
        for i, (_, row) in enumerate(df_clusters.iterrows())
    }
    
    # Agregar transformadores
    for _, transformer in df_transformers.iterrows():
        if transformer['cluster_refined'] == -1:  # Ruido
            color = 'gray'
            cluster_info = 'Ruido (no asignado)'
        else:
            color = color_map.get(transformer['cluster_refined'], 'black')
            cluster_data = df_clusters[df_clusters['cluster_id'] == transformer['cluster_refined']].iloc[0]
            cluster_info = f"Cluster {transformer['cluster_refined']} (IAS Pot: {cluster_data['ias_potential']:.3f})"
        
        folium.CircleMarker(
            location=[transformer[coord_y_col], transformer[coord_x_col]],
            radius=3,
            popup=f"""
            <b>{transformer['CODIGO']}</b><br>
            <b>Cluster:</b> {cluster_info}<br>
            <b>Perfil:</b> {transformer['perfil_dominante']}<br>
            <b>Potencia:</b> {transformer['Potencia Nom.(kVA)']} kVA<br>
            <b>Usuarios:</b> {transformer['Usu. Total']}<br>
            <b>Localidad:</b> {transformer['Localidad']}
            """,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6
        ).add_to(m)
    
    # Agregar centroides de clusters
    for _, cluster in df_clusters.head(10).iterrows():  # Top 10
        folium.Marker(
            location=[cluster['centroid_lat'], cluster['centroid_lon']],
            icon=folium.Icon(
                color='green' if cluster['ias_potential'] > 0.6 else 'orange',
                icon='star'
            ),
            popup=f"""
            <b>Cluster {cluster['cluster_id']}</b><br>
            <b>IAS Potencial:</b> {cluster['ias_potential']:.3f}<br>
            <b>Transformadores:</b> {cluster['n_transformers']}<br>
            <b>Potencia Total:</b> {cluster['potencia_mva']:.2f} MVA<br>
            <b>Usuarios:</b> {cluster['usuarios_total']:,}<br>
            <b>GD Estimada:</b> {cluster['gd_estimada_mw']:.2f} MW<br>
            <hr>
            <b>Mix Comercial/Ind:</b> {cluster['comercial_industrial_pct']:.1%}<br>
            <b>Mix Residencial:</b> {cluster['residencial_rural_pct']:.1%}<br>
            <b>Score Terreno:</b> {cluster['terreno_score']:.3f}
            """
        ).add_to(m)
        
        # Agregar círculo de radio
        folium.Circle(
            location=[cluster['centroid_lat'], cluster['centroid_lon']],
            radius=cluster['radio_km'] * 1000,  # metros
            color=color_map[cluster['cluster_id']],
            fill=False,
            weight=2,
            opacity=0.5
        ).add_to(m)
    
    # Guardar mapa
    map_path = REFINEMENT_V3_DIR / "refined_clustering_map.html"
    m.save(str(map_path))
    logger.info(f"Mapa guardado en: {map_path}")
    
    return m

def create_analysis_visualizations(df_results, df_clusters):
    """
    Crea visualizaciones del análisis de refinamiento.
    """
    logger.info("Creando visualizaciones de análisis...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Análisis de Refinamiento de Clustering para IAS 3.0', fontsize=16)
    
    # 1. Comparación de algoritmos
    ax = axes[0, 0]
    algorithm_summary = df_results.groupby('algorithm').agg({
        'composite_score': ['mean', 'max', 'std'],
        'n_clusters': 'mean'
    }).round(3)
    
    x = np.arange(len(algorithm_summary))
    width = 0.25
    
    bars1 = ax.bar(x - width, algorithm_summary[('composite_score', 'mean')], 
                    width, label='Score Promedio', alpha=0.7)
    bars2 = ax.bar(x, algorithm_summary[('composite_score', 'max')], 
                    width, label='Score Máximo', alpha=0.7)
    bars3 = ax.bar(x + width, algorithm_summary[('n_clusters', 'mean')]/20, 
                    width, label='Clusters Prom/20', alpha=0.7)
    
    ax.set_xlabel('Algoritmo')
    ax.set_ylabel('Score')
    ax.set_title('Comparación de Algoritmos de Clustering')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithm_summary.index)
    ax.legend()
    
    # 2. Distribución de potencial IAS por cluster
    ax = axes[0, 1]
    df_clusters_sorted = df_clusters.sort_values('ias_potential', ascending=False).head(15)
    
    bars = ax.barh(range(len(df_clusters_sorted)), df_clusters_sorted['ias_potential'])
    
    # Colorear por potencial
    for i, (bar, potential) in enumerate(zip(bars, df_clusters_sorted['ias_potential'])):
        if potential > 0.6:
            bar.set_color('green')
        elif potential > 0.4:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    ax.set_yticks(range(len(df_clusters_sorted)))
    ax.set_yticklabels([f"C{id}" for id in df_clusters_sorted['cluster_id']])
    ax.set_xlabel('Potencial IAS 3.0')
    ax.set_title('Top 15 Clusters por Potencial IAS 3.0')
    ax.axvline(x=0.5, color='black', linestyle='--', alpha=0.5)
    
    # 3. Análisis de componentes del potencial
    ax = axes[1, 0]
    components = ['comercial_industrial_pct', 'residencial_rural_pct', 
                  'terreno_score', 'criticidad']
    component_labels = ['Solar Diurno', 'Q Nocturno', 'Terreno', 'Criticidad']
    
    # Promedios ponderados por usuarios
    weighted_avgs = []
    for comp in components:
        weighted_avg = (df_clusters[comp] * df_clusters['usuarios_total']).sum() / df_clusters['usuarios_total'].sum()
        weighted_avgs.append(weighted_avg)
    
    bars = ax.bar(component_labels, weighted_avgs, 
                   color=['#FFD700', '#4B0082', '#228B22', '#DC143C'])
    ax.set_ylabel('Score Promedio Ponderado')
    ax.set_title('Componentes del Potencial IAS 3.0')
    ax.set_ylim(0, 1)
    
    # Agregar valores
    for bar, val in zip(bars, weighted_avgs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.3f}', ha='center', va='bottom')
    
    # 4. Scatter de potencia vs usuarios coloreado por potencial
    ax = axes[1, 1]
    scatter = ax.scatter(df_clusters['potencia_mva'], 
                        df_clusters['usuarios_total'],
                        c=df_clusters['ias_potential'],
                        s=df_clusters['gd_estimada_mw']*20,
                        cmap='RdYlGn',
                        alpha=0.7)
    
    ax.set_xlabel('Potencia Total (MVA)')
    ax.set_ylabel('Usuarios Totales')
    ax.set_title('Clusters: Potencia vs Usuarios (color=IAS Pot, tamaño=GD MW)')
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # Anotar top 5
    for _, cluster in df_clusters.head(5).iterrows():
        ax.annotate(f"C{cluster['cluster_id']}", 
                   (cluster['potencia_mva'], cluster['usuarios_total']),
                   xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    plt.colorbar(scatter, ax=ax, label='Potencial IAS 3.0')
    
    plt.tight_layout()
    
    # Guardar
    fig_path = REFINEMENT_V3_DIR / "clustering_refinement_analysis.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Visualizaciones guardadas en: {fig_path}")

def generate_refinement_report(df_results, best_config, df_clusters):
    """
    Genera reporte de refinamiento de clustering.
    """
    logger.info("Generando reporte de refinamiento...")
    
    report = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'methodology': 'Clustering Refinement for IAS 3.0',
            'algorithms_tested': df_results['algorithm'].unique().tolist(),
            'total_configurations': len(df_results)
        },
        'best_configuration': {
            'algorithm': best_config['algorithm'],
            'parameters': best_config['params'],
            'n_clusters': int(best_config['n_clusters']),
            'metrics': {
                'silhouette': float(best_config['silhouette']),
                'davies_bouldin': float(best_config['davies_bouldin']),
                'calinski_harabasz': float(best_config['calinski']),
                'composite_score': float(best_config['composite_score'])
            }
        },
        'cluster_summary': {
            'total_clusters': len(df_clusters),
            'avg_ias_potential': float(df_clusters['ias_potential'].mean()),
            'high_potential_clusters': int((df_clusters['ias_potential'] > 0.6).sum()),
            'total_gd_potential_mw': float(df_clusters['gd_estimada_mw'].sum())
        },
        'top_10_clusters': [],
        'component_analysis': {
            'solar_diurno_weight': 0.3,
            'q_nocturno_weight': 0.3,
            'terreno_weight': 0.2,
            'criticidad_weight': 0.2
        },
        'recommendations': []
    }
    
    # Top 10 clusters
    for _, cluster in df_clusters.head(10).iterrows():
        report['top_10_clusters'].append({
            'cluster_id': int(cluster['cluster_id']),
            'ias_potential': float(cluster['ias_potential']),
            'n_transformers': int(cluster['n_transformers']),
            'potencia_mva': float(cluster['potencia_mva']),
            'usuarios': int(cluster['usuarios_total']),
            'gd_mw': float(cluster['gd_estimada_mw']),
            'strengths': [],
            'weaknesses': []
        })
        
        # Identificar fortalezas y debilidades
        cluster_dict = report['top_10_clusters'][-1]
        
        if cluster['comercial_industrial_pct'] > 0.6:
            cluster_dict['strengths'].append('Excelente coincidencia solar-demanda')
        if cluster['residencial_rural_pct'] > 0.6:
            cluster_dict['strengths'].append('Alto potencial para Q at Night')
        if cluster['terreno_score'] > 0.7:
            cluster_dict['strengths'].append('Buena disponibilidad de terreno')
        if cluster['criticidad'] > 0.7:
            cluster_dict['strengths'].append('Alta necesidad de mejora')
            
        if cluster['comercial_industrial_pct'] < 0.3:
            cluster_dict['weaknesses'].append('Baja coincidencia solar')
        if cluster['residencial_rural_pct'] < 0.3:
            cluster_dict['weaknesses'].append('Limitado beneficio nocturno')
        if cluster['terreno_score'] < 0.3:
            cluster_dict['weaknesses'].append('Restricciones de terreno')
    
    # Recomendaciones
    report['recommendations'] = [
        f"Priorizar {len(df_clusters[df_clusters['ias_potential'] > 0.6])} clusters con potencial IAS > 0.6",
        "Implementar estrategia diferenciada: solar+tracker en clusters comerciales, STATCOM nocturno en residenciales",
        f"Potencial total identificado: {df_clusters['gd_estimada_mw'].sum():.1f} MW distribuidos en {len(df_clusters)} clusters",
        "Validar disponibilidad de terreno en clusters top 5 antes de proceder",
        "Considerar hibridación de soluciones en clusters mixtos para maximizar beneficios 24h"
    ]
    
    # Guardar reporte
    report_path = REFINEMENT_V3_DIR / "clustering_refinement_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Reporte guardado en: {report_path}")
    
    return report

def main():
    """Función principal"""
    logger.info("=== INICIANDO REFINAMIENTO DE CLUSTERING PARA IAS 3.0 ===")
    
    # Cargar datos de transformadores con perfiles
    transformer_file = DATA_DIR / "processed" / "transformers_ias_clustering.parquet"
    if not transformer_file.exists():
        logger.error("No se encontró archivo de transformadores. Ejecutar scripts previos.")
        return
        
    df_transformers = pd.read_parquet(transformer_file)
    logger.info(f"Cargados {len(df_transformers)} transformadores")
    
    # Preparar para clustering
    refinement = ClusteringRefinementV3()
    X_scaled, features, scaler = refinement.prepare_features_v3(df_transformers)
    
    logger.info(f"Features utilizadas: {features}")
    logger.info(f"Matriz de features: {X_scaled.shape}")
    
    # Optimizar clustering
    df_results, best_config = refinement.optimize_clustering_v3(
        X_scaled, 
        min_clusters=12, 
        max_clusters=20
    )
    
    # Aplicar mejor configuración
    labels = best_config['labels']
    
    # Analizar clusters
    df_clusters, df_transformers = analyze_cluster_ias_potential(df_transformers, labels)
    
    # Estadísticas resumen
    logger.info("\n=== RESUMEN DE CLUSTERING REFINADO ===")
    logger.info(f"Algoritmo seleccionado: {best_config['algorithm']}")
    logger.info(f"Número de clusters: {best_config['n_clusters']}")
    logger.info(f"Score compuesto: {best_config['composite_score']:.3f}")
    
    if 'n_noise' in best_config:
        logger.info(f"Transformadores en ruido: {best_config['n_noise']}")
    
    logger.info(f"\nPotencial IAS 3.0 promedio: {df_clusters['ias_potential'].mean():.3f}")
    logger.info(f"Clusters con alto potencial (>0.6): {(df_clusters['ias_potential'] > 0.6).sum()}")
    
    # Top 5 clusters
    logger.info("\nTop 5 clusters por potencial IAS 3.0:")
    for _, cluster in df_clusters.head(5).iterrows():
        logger.info(f"  Cluster {cluster['cluster_id']}: "
                   f"Potencial={cluster['ias_potential']:.3f}, "
                   f"Transformadores={cluster['n_transformers']}, "
                   f"GD={cluster['gd_estimada_mw']:.1f} MW")
    
    # Crear visualizaciones
    create_refined_clustering_map(df_transformers, df_clusters)
    create_analysis_visualizations(df_results, df_clusters)
    
    # Generar reporte
    report = generate_refinement_report(df_results, best_config, df_clusters)
    
    # Guardar resultados
    # Transformadores con asignación refinada
    output_transformers = DATA_DIR / "processed" / "transformers_refined_ias_v3.parquet"
    df_transformers.to_parquet(output_transformers)
    logger.info(f"\nTransformadores guardados en: {output_transformers}")
    
    # Resumen de clusters
    output_clusters = REFINEMENT_V3_DIR / "refined_clusters_ias_v3.csv"
    df_clusters.to_csv(output_clusters, index=False)
    logger.info(f"Clusters guardados en: {output_clusters}")
    
    logger.info("\n=== REFINAMIENTO DE CLUSTERING COMPLETADO ===")

if __name__ == "__main__":
    main()