#!/usr/bin/env python3
"""
FASE 2 - Script 08: Clustering Refinement
========================================
Refinamiento de clustering con optimización de parámetros y análisis de sensibilidad.
Implementa múltiples algoritmos y selecciona el óptimo basado en métricas.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sqlite3
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering, OPTICS
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA
import hdbscan
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import cdist
from scipy.cluster.hierarchy import dendrogram, linkage
import warnings
warnings.filterwarnings('ignore')
import logging

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
CLUSTERING_DIR.mkdir(exist_ok=True)

class ClusteringOptimizer:
    """
    Optimizador de clustering para identificar configuraciones óptimas.
    Evalúa múltiples algoritmos y parámetros.
    """
    
    def __init__(self, data, feature_columns):
        """
        Inicializa el optimizador.
        
        Args:
            data: DataFrame con los datos
            feature_columns: Lista de columnas a usar para clustering
        """
        self.data = data
        self.feature_columns = feature_columns
        self.X = data[feature_columns].values
        
        # Escalar features
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)
        
        # Almacenar resultados
        self.results = []
        
    def evaluate_clustering(self, labels, method_name, params):
        """
        Evalúa una solución de clustering con múltiples métricas.
        """
        # Filtrar ruido (-1) para métricas
        mask = labels != -1
        if mask.sum() < 2:
            return None
            
        n_clusters = len(set(labels[mask]))
        
        if n_clusters < 2:
            return None
            
        try:
            # Calcular métricas
            metrics = {
                'method': method_name,
                'params': params,
                'n_clusters': n_clusters,
                'n_noise': (labels == -1).sum(),
                'noise_ratio': (labels == -1).mean(),
                'silhouette': silhouette_score(self.X_scaled[mask], labels[mask]),
                'calinski_harabasz': calinski_harabasz_score(self.X_scaled[mask], labels[mask]),
                'davies_bouldin': davies_bouldin_score(self.X_scaled[mask], labels[mask])
            }
            
            # Calcular métricas adicionales específicas del dominio
            metrics.update(self._calculate_domain_metrics(labels))
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error calculando métricas para {method_name}: {e}")
            return None
    
    def _calculate_domain_metrics(self, labels):
        """
        Calcula métricas específicas del dominio eléctrico.
        """
        domain_metrics = {}
        
        # Asignar clusters a los datos
        self.data['cluster_temp'] = labels
        
        # Para cada cluster
        unique_labels = set(labels) - {-1}
        
        # Compacidad geográfica promedio
        geo_compactness = []
        ias_homogeneity = []
        size_balance = []
        
        for label in unique_labels:
            cluster_data = self.data[self.data['cluster_temp'] == label]
            
            if len(cluster_data) > 1:
                # Compacidad geográfica (distancia promedio al centroide)
                centroid = cluster_data[['Longitud', 'Latitud']].mean()
                distances = np.sqrt(
                    (cluster_data['Longitud'] - centroid['Longitud'])**2 + 
                    (cluster_data['Latitud'] - centroid['Latitud'])**2
                )
                geo_compactness.append(distances.mean())
                
                # Homogeneidad de IAS score
                if 'IAS_score' in cluster_data.columns:
                    ias_homogeneity.append(cluster_data['IAS_score'].std())
                
                # Balance de tamaño
                size_balance.append(len(cluster_data))
        
        if geo_compactness:
            domain_metrics['geo_compactness_mean'] = np.mean(geo_compactness)
            domain_metrics['geo_compactness_std'] = np.std(geo_compactness)
        
        if ias_homogeneity:
            domain_metrics['ias_homogeneity_mean'] = np.mean(ias_homogeneity)
        
        if size_balance:
            # Coeficiente de variación del tamaño
            domain_metrics['size_cv'] = np.std(size_balance) / np.mean(size_balance)
            domain_metrics['size_min'] = min(size_balance)
            domain_metrics['size_max'] = max(size_balance)
        
        # Limpiar columna temporal
        self.data.drop('cluster_temp', axis=1, inplace=True)
        
        return domain_metrics
    
    def optimize_dbscan(self):
        """
        Optimiza parámetros de DBSCAN.
        """
        logger.info("Optimizando DBSCAN...")
        
        # Rangos de parámetros a probar
        eps_range = np.linspace(0.01, 0.1, 10)  # En unidades escaladas
        min_samples_range = range(5, 20, 2)
        
        best_score = -1
        best_params = None
        
        for eps in eps_range:
            for min_samples in min_samples_range:
                # Ejecutar DBSCAN
                clusterer = DBSCAN(eps=eps, min_samples=min_samples)
                labels = clusterer.fit_predict(self.X_scaled)
                
                # Evaluar
                metrics = self.evaluate_clustering(labels, 'DBSCAN', 
                                                 {'eps': eps, 'min_samples': min_samples})
                
                if metrics:
                    self.results.append(metrics)
                    
                    # Score compuesto (maximizar silhouette, minimizar ruido)
                    score = metrics['silhouette'] * (1 - metrics['noise_ratio'])
                    
                    if score > best_score and metrics['n_clusters'] >= 10:
                        best_score = score
                        best_params = {'eps': eps, 'min_samples': min_samples}
        
        logger.info(f"Mejor DBSCAN: {best_params} con score {best_score:.3f}")
        return best_params
    
    def optimize_kmeans(self):
        """
        Optimiza número de clusters para K-means usando método del codo.
        """
        logger.info("Optimizando K-means...")
        
        k_range = range(5, 30)
        inertias = []
        silhouettes = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(self.X_scaled)
            
            inertias.append(kmeans.inertia_)
            
            metrics = self.evaluate_clustering(labels, 'KMeans', {'n_clusters': k})
            if metrics:
                self.results.append(metrics)
                silhouettes.append(metrics['silhouette'])
            else:
                silhouettes.append(0)
        
        # Encontrar codo usando segunda derivada
        if len(inertias) > 2:
            diffs = np.diff(inertias)
            diffs2 = np.diff(diffs)
            elbow_idx = np.argmax(diffs2) + 2  # +2 por los diffs
            optimal_k = k_range[elbow_idx]
        else:
            optimal_k = 15  # Default
        
        logger.info(f"K-means óptimo: {optimal_k} clusters")
        return {'n_clusters': optimal_k}
    
    def optimize_hierarchical(self):
        """
        Optimiza clustering jerárquico.
        """
        logger.info("Optimizando clustering jerárquico...")
        
        # Probar diferentes métodos de linkage
        linkage_methods = ['ward', 'average', 'complete']
        n_clusters_range = range(10, 25, 2)
        
        best_score = -1
        best_params = None
        
        for method in linkage_methods:
            for n_clusters in n_clusters_range:
                clusterer = AgglomerativeClustering(
                    n_clusters=n_clusters,
                    linkage=method
                )
                labels = clusterer.fit_predict(self.X_scaled)
                
                metrics = self.evaluate_clustering(labels, 'Hierarchical',
                                                 {'linkage': method, 'n_clusters': n_clusters})
                
                if metrics:
                    self.results.append(metrics)
                    
                    if metrics['silhouette'] > best_score:
                        best_score = metrics['silhouette']
                        best_params = {'linkage': method, 'n_clusters': n_clusters}
        
        logger.info(f"Mejor jerárquico: {best_params} con silhouette {best_score:.3f}")
        return best_params
    
    def optimize_hdbscan(self):
        """
        Optimiza HDBSCAN.
        """
        logger.info("Optimizando HDBSCAN...")
        
        min_cluster_size_range = range(10, 50, 5)
        min_samples_range = range(5, 20, 3)
        
        best_score = -1
        best_params = None
        
        for min_cluster_size in min_cluster_size_range:
            for min_samples in min_samples_range:
                clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=min_cluster_size,
                    min_samples=min_samples
                )
                labels = clusterer.fit_predict(self.X_scaled)
                
                metrics = self.evaluate_clustering(labels, 'HDBSCAN',
                                                 {'min_cluster_size': min_cluster_size,
                                                  'min_samples': min_samples})
                
                if metrics:
                    self.results.append(metrics)
                    
                    # Penalizar mucho ruido
                    score = metrics['silhouette'] * (1 - metrics['noise_ratio'] * 2)
                    
                    if score > best_score and metrics['n_clusters'] >= 8:
                        best_score = score
                        best_params = {'min_cluster_size': min_cluster_size,
                                     'min_samples': min_samples}
        
        logger.info(f"Mejor HDBSCAN: {best_params} con score {best_score:.3f}")
        return best_params
    
    def find_optimal_clustering(self):
        """
        Encuentra la configuración óptima de clustering.
        """
        logger.info("Buscando configuración óptima de clustering...")
        
        # Optimizar cada algoritmo
        dbscan_params = self.optimize_dbscan()
        kmeans_params = self.optimize_kmeans()
        hier_params = self.optimize_hierarchical()
        hdbscan_params = self.optimize_hdbscan()
        
        # Convertir resultados a DataFrame para análisis
        df_results = pd.DataFrame(self.results)
        
        # Calcular score compuesto
        # Normalizar métricas
        df_results['silhouette_norm'] = (df_results['silhouette'] - df_results['silhouette'].min()) / (df_results['silhouette'].max() - df_results['silhouette'].min())
        df_results['ch_norm'] = (df_results['calinski_harabasz'] - df_results['calinski_harabasz'].min()) / (df_results['calinski_harabasz'].max() - df_results['calinski_harabasz'].min())
        df_results['db_norm'] = 1 - (df_results['davies_bouldin'] - df_results['davies_bouldin'].min()) / (df_results['davies_bouldin'].max() - df_results['davies_bouldin'].min())
        
        # Score compuesto
        df_results['composite_score'] = (
            0.4 * df_results['silhouette_norm'] +
            0.3 * df_results['ch_norm'] +
            0.2 * df_results['db_norm'] +
            0.1 * (1 - df_results['noise_ratio'])
        )
        
        # Filtrar por requisitos mínimos
        df_valid = df_results[
            (df_results['n_clusters'] >= 10) &
            (df_results['n_clusters'] <= 25) &
            (df_results['noise_ratio'] < 0.2)
        ]
        
        if len(df_valid) == 0:
            df_valid = df_results
        
        # Encontrar mejor configuración
        best_idx = df_valid['composite_score'].idxmax()
        best_config = df_valid.loc[best_idx]
        
        logger.info(f"\nMejor configuración encontrada:")
        logger.info(f"  Método: {best_config['method']}")
        logger.info(f"  Parámetros: {best_config['params']}")
        logger.info(f"  Clusters: {best_config['n_clusters']}")
        logger.info(f"  Score compuesto: {best_config['composite_score']:.3f}")
        
        return best_config, df_results

def load_data_with_ias():
    """Carga datos con scores IAS calculados"""
    logger.info("Cargando datos con IAS scores...")
    
    # Buscar archivo procesado
    processed_file = DATA_DIR / "processed" / "transformers_ias_clustering.parquet"
    
    if processed_file.exists():
        df = pd.read_parquet(processed_file)
        logger.info(f"Cargados {len(df)} transformadores con IAS scores")
        return df
    else:
        logger.error("No se encontró archivo con IAS scores. Ejecutar script 06 primero.")
        return None

def apply_optimal_clustering(df, best_config):
    """
    Aplica la configuración óptima de clustering a los datos.
    """
    logger.info(f"Aplicando clustering óptimo: {best_config['method']}")
    
    # Preparar features
    feature_columns = ['Longitud', 'Latitud', 'IAS_score']
    X = df[feature_columns].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Aplicar algoritmo según configuración
    method = best_config['method']
    params = best_config['params']
    
    if method == 'DBSCAN':
        clusterer = DBSCAN(**params)
    elif method == 'KMeans':
        clusterer = KMeans(**params, random_state=42)
    elif method == 'Hierarchical':
        clusterer = AgglomerativeClustering(**params)
    elif method == 'HDBSCAN':
        clusterer = hdbscan.HDBSCAN(**params)
    else:
        raise ValueError(f"Método no reconocido: {method}")
    
    # Predecir clusters
    df['cluster_refined'] = clusterer.fit_predict(X_scaled)
    
    # Estadísticas
    n_clusters = len(set(df['cluster_refined'])) - (1 if -1 in df['cluster_refined'] else 0)
    n_noise = (df['cluster_refined'] == -1).sum()
    
    logger.info(f"Clusters generados: {n_clusters}")
    logger.info(f"Puntos de ruido: {n_noise} ({n_noise/len(df)*100:.1f}%)")
    
    return df

def visualize_optimization_results(df_results):
    """
    Visualiza resultados de la optimización de clustering.
    """
    logger.info("Creando visualizaciones de optimización...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Análisis de Optimización de Clustering', fontsize=16)
    
    # 1. Silhouette por método
    ax = axes[0, 0]
    df_results.boxplot(column='silhouette', by='method', ax=ax)
    ax.set_title('Silhouette Score por Método')
    ax.set_xlabel('Método')
    ax.set_ylabel('Silhouette Score')
    
    # 2. Número de clusters vs métricas
    ax = axes[0, 1]
    scatter = ax.scatter(df_results['n_clusters'], 
                        df_results['silhouette'],
                        c=df_results['composite_score'],
                        s=50,
                        cmap='viridis',
                        alpha=0.6)
    ax.set_xlabel('Número de Clusters')
    ax.set_ylabel('Silhouette Score')
    ax.set_title('Clusters vs Silhouette')
    plt.colorbar(scatter, ax=ax, label='Score Compuesto')
    
    # 3. Ruido vs calidad
    ax = axes[0, 2]
    ax.scatter(df_results['noise_ratio'] * 100, 
              df_results['composite_score'],
              alpha=0.6)
    ax.set_xlabel('Porcentaje de Ruido')
    ax.set_ylabel('Score Compuesto')
    ax.set_title('Trade-off: Ruido vs Calidad')
    ax.axvline(x=20, color='red', linestyle='--', alpha=0.5, label='Límite 20%')
    ax.legend()
    
    # 4. Heatmap de correlación de métricas
    ax = axes[1, 0]
    metrics_cols = ['silhouette', 'calinski_harabasz', 'davies_bouldin', 'n_clusters', 'noise_ratio']
    corr_matrix = df_results[metrics_cols].corr()
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', ax=ax)
    ax.set_title('Correlación entre Métricas')
    
    # 5. Top configuraciones
    ax = axes[1, 1]
    top_10 = df_results.nlargest(10, 'composite_score')
    y_pos = np.arange(len(top_10))
    
    bars = ax.barh(y_pos, top_10['composite_score'])
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{row['method'][:4]}-{row['n_clusters']}c" 
                        for _, row in top_10.iterrows()])
    ax.set_xlabel('Score Compuesto')
    ax.set_title('Top 10 Configuraciones')
    
    # Colorear por método
    colors = {'DBSCAN': 'blue', 'KMeans': 'green', 'Hierarchical': 'red', 'HDBSCAN': 'purple'}
    for i, (_, row) in enumerate(top_10.iterrows()):
        bars[i].set_color(colors.get(row['method'], 'gray'))
    
    # 6. Evolución de métricas por método
    ax = axes[1, 2]
    for method in df_results['method'].unique():
        method_data = df_results[df_results['method'] == method].sort_values('n_clusters')
        if len(method_data) > 1:
            ax.plot(method_data['n_clusters'], 
                   method_data['composite_score'], 
                   marker='o', 
                   label=method,
                   alpha=0.7)
    
    ax.set_xlabel('Número de Clusters')
    ax.set_ylabel('Score Compuesto')
    ax.set_title('Evolución del Score por Método')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar figura
    fig_path = CLUSTERING_DIR / "clustering_optimization_analysis.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Visualizaciones guardadas en: {fig_path}")

def visualize_refined_clusters(df):
    """
    Visualiza los clusters refinados.
    """
    logger.info("Visualizando clusters refinados...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig = plt.figure(figsize=(20, 12))
    
    # Layout
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # 1. Scatter plot 2D con PCA
    ax1 = fig.add_subplot(gs[0, :2])
    
    # PCA para visualización
    features = ['Longitud', 'Latitud', 'IAS_score']
    X = df[features].values
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(StandardScaler().fit_transform(X))
    
    # Colores para clusters
    unique_clusters = sorted(df['cluster_refined'].unique())
    colors = plt.cm.tab20(np.linspace(0, 1, len(unique_clusters)))
    
    for i, cluster in enumerate(unique_clusters):
        mask = df['cluster_refined'] == cluster
        if cluster == -1:
            label = 'Ruido'
            color = 'gray'
        else:
            label = f'Cluster {cluster}'
            color = colors[i]
        
        ax1.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                   c=[color], 
                   label=label,
                   alpha=0.6,
                   s=30)
    
    ax1.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} varianza)')
    ax1.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} varianza)')
    ax1.set_title('Clusters en Espacio PCA')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 2. Distribución de IAS por cluster
    ax2 = fig.add_subplot(gs[0, 2])
    
    cluster_data = []
    for cluster in unique_clusters:
        if cluster != -1:
            ias_values = df[df['cluster_refined'] == cluster]['IAS_score']
            cluster_data.append(ias_values)
    
    ax2.boxplot(cluster_data, labels=[f"C{i}" for i in unique_clusters if i != -1])
    ax2.set_xlabel('Cluster')
    ax2.set_ylabel('IAS Score')
    ax2.set_title('Distribución IAS por Cluster')
    ax2.grid(True, axis='y', alpha=0.3)
    
    # 3. Tamaño de clusters
    ax3 = fig.add_subplot(gs[1, 0])
    
    cluster_sizes = df['cluster_refined'].value_counts().sort_index()
    cluster_sizes = cluster_sizes[cluster_sizes.index != -1]
    
    bars = ax3.bar(range(len(cluster_sizes)), cluster_sizes.values)
    ax3.set_xlabel('Cluster ID')
    ax3.set_ylabel('Número de Transformadores')
    ax3.set_title('Tamaño de Clusters')
    ax3.set_xticks(range(len(cluster_sizes)))
    ax3.set_xticklabels(cluster_sizes.index)
    
    # Colorear por tamaño
    norm = plt.Normalize(cluster_sizes.min(), cluster_sizes.max())
    colors = plt.cm.RdYlGn_r(norm(cluster_sizes.values))
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    # 4. Matriz de características promedio
    ax4 = fig.add_subplot(gs[1, 1:])
    
    # Características a analizar
    feature_cols = ['IAS_score', 'C1_coincidencia', 'C2_capacidad_absorcion', 
                    'C3_debilidad_red', 'C4_cargabilidad', 'C5_calidad_servicio']
    
    # Calcular promedios por cluster
    cluster_features = []
    cluster_ids = []
    
    for cluster in sorted(unique_clusters):
        if cluster != -1:
            cluster_mean = df[df['cluster_refined'] == cluster][feature_cols].mean()
            cluster_features.append(cluster_mean.values)
            cluster_ids.append(f"Cluster {cluster}")
    
    cluster_features = np.array(cluster_features).T
    
    # Heatmap
    im = ax4.imshow(cluster_features, cmap='RdYlGn', aspect='auto')
    ax4.set_yticks(range(len(feature_cols)))
    ax4.set_yticklabels(['IAS', 'C1', 'C2', 'C3', 'C4', 'C5'])
    ax4.set_xticks(range(len(cluster_ids)))
    ax4.set_xticklabels(cluster_ids, rotation=45, ha='right')
    ax4.set_title('Características Promedio por Cluster')
    
    # Añadir valores
    for i in range(len(feature_cols)):
        for j in range(len(cluster_ids)):
            text = ax4.text(j, i, f'{cluster_features[i, j]:.2f}',
                           ha="center", va="center", color="black", fontsize=8)
    
    plt.colorbar(im, ax=ax4)
    
    plt.tight_layout()
    
    # Guardar figura
    fig_path = CLUSTERING_DIR / "refined_clusters_visualization.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Visualización guardada en: {fig_path}")

def generate_optimization_report(best_config, df_results, df_final):
    """
    Genera reporte de optimización de clustering.
    """
    logger.info("Generando reporte de optimización...")
    
    # Estadísticas de clusters finales
    cluster_stats = []
    
    for cluster_id in sorted(df_final['cluster_refined'].unique()):
        if cluster_id == -1:
            continue
            
        cluster_data = df_final[df_final['cluster_refined'] == cluster_id]
        
        stats = {
            'cluster_id': int(cluster_id),
            'size': len(cluster_data),
            'ias_mean': float(cluster_data['IAS_score'].mean()),
            'ias_std': float(cluster_data['IAS_score'].std()),
            'users_total': int(cluster_data['Usu. Total'].sum()),
            'power_mva': float(cluster_data['Potencia Nom.(kVA)'].sum() / 1000),
            'failure_rate': float((cluster_data['Resultado'] == 'Fallida').mean()),
            'dominant_profile': cluster_data['perfil_dominante'].mode()[0] if len(cluster_data['perfil_dominante'].mode()) > 0 else 'Mixto'
        }
        
        cluster_stats.append(stats)
    
    # Crear reporte
    report = {
        'optimization_summary': {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_configurations_tested': len(df_results),
            'optimal_method': best_config['method'],
            'optimal_params': best_config['params'],
            'optimal_clusters': int(best_config['n_clusters']),
            'optimal_score': float(best_config['composite_score'])
        },
        'method_comparison': {},
        'final_clustering': {
            'total_transformers': len(df_final),
            'total_clusters': len(cluster_stats),
            'noise_points': int((df_final['cluster_refined'] == -1).sum()),
            'noise_percentage': float((df_final['cluster_refined'] == -1).mean() * 100),
            'cluster_statistics': cluster_stats
        },
        'quality_metrics': {
            'silhouette_score': float(best_config['silhouette']),
            'calinski_harabasz_score': float(best_config['calinski_harabasz']),
            'davies_bouldin_score': float(best_config['davies_bouldin'])
        }
    }
    
    # Comparación por método
    for method in df_results['method'].unique():
        method_data = df_results[df_results['method'] == method]
        report['method_comparison'][method] = {
            'configurations_tested': len(method_data),
            'best_silhouette': float(method_data['silhouette'].max()),
            'avg_clusters': float(method_data['n_clusters'].mean()),
            'avg_noise_ratio': float(method_data['noise_ratio'].mean())
        }
    
    # Guardar reporte
    report_path = CLUSTERING_DIR / "clustering_optimization_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Reporte guardado en: {report_path}")
    
    # Guardar datos finales
    output_path = DATA_DIR / "processed" / "transformers_refined_clusters.parquet"
    df_final.to_parquet(output_path)
    logger.info(f"Datos con clusters refinados guardados en: {output_path}")
    
    return report

def main():
    """Función principal"""
    logger.info("=== INICIANDO REFINAMIENTO DE CLUSTERING ===")
    
    # Cargar datos con IAS
    df = load_data_with_ias()
    if df is None:
        return
    
    # Definir features para clustering
    feature_columns = ['Longitud', 'Latitud', 'IAS_score']
    
    # Si hay features eléctricas, incluirlas
    if 'voltage_drop_percent' in df.columns:
        feature_columns.extend(['voltage_drop_percent', 'impedance_total'])
    
    # Crear optimizador
    optimizer = ClusteringOptimizer(df, feature_columns)
    
    # Encontrar configuración óptima
    best_config, df_results = optimizer.find_optimal_clustering()
    
    # Aplicar clustering óptimo
    df_final = apply_optimal_clustering(df, best_config)
    
    # Visualizaciones
    visualize_optimization_results(df_results)
    visualize_refined_clusters(df_final)
    
    # Generar reporte
    report = generate_optimization_report(best_config, df_results, df_final)
    
    # Resumen ejecutivo
    logger.info("\n=== RESUMEN EJECUTIVO ===")
    logger.info(f"Configuraciones probadas: {len(df_results)}")
    logger.info(f"Método óptimo: {best_config['method']}")
    logger.info(f"Clusters finales: {best_config['n_clusters']}")
    logger.info(f"Score de calidad: {best_config['composite_score']:.3f}")
    logger.info(f"Silhouette score: {best_config['silhouette']:.3f}")
    
    logger.info("\n=== REFINAMIENTO COMPLETADO ===")

if __name__ == "__main__":
    main()