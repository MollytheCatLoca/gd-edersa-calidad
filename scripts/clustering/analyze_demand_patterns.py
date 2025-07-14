#!/usr/bin/env python3
"""
Phase 4: Clustering Analysis - Demand Patterns
Identify similar behavior patterns across stations
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

# Project root
project_root = Path(__file__).parent.parent.parent

def load_data():
    """Load consolidated data from Phase 3."""
    print("Loading consolidated data...")
    data_file = project_root / "data" / "processed" / "consolidated_data.csv"
    df = pd.read_csv(data_file, parse_dates=['timestamp'])
    print(f"Loaded {len(df):,} records")
    return df

def create_hourly_profiles(df):
    """Create normalized hourly profiles for each station."""
    print("\nCreating hourly profiles...")
    
    # Group by station and hour
    hourly_profiles = df.groupby(['station', 'hour']).agg({
        'p_total': ['mean', 'std', 'max'],
        'q_total': ['mean', 'std'],
        'v_pu': ['mean', 'std', 'min'],
        'fp': 'mean'
    }).round(3)
    
    # Flatten column names
    hourly_profiles.columns = ['_'.join(col).strip() for col in hourly_profiles.columns]
    hourly_profiles = hourly_profiles.reset_index()
    
    return hourly_profiles

def create_feature_matrix(hourly_profiles):
    """Create feature matrix for clustering."""
    print("\nCreating feature matrix...")
    
    stations = hourly_profiles['station'].unique()
    features_dict = {}
    
    for station in stations:
        station_data = hourly_profiles[hourly_profiles['station'] == station].sort_values('hour')
        
        # Create feature vector
        features = []
        
        # 1. Hourly power profile (normalized)
        p_mean = station_data['p_total_mean'].values
        p_mean_norm = p_mean / p_mean.max() if p_mean.max() > 0 else p_mean
        features.extend(p_mean_norm)  # 24 features
        
        # 2. Peak characteristics
        peak_hour = p_mean.argmax()
        peak_value = p_mean.max()
        valley_value = p_mean.min()
        peak_to_valley_ratio = peak_value / valley_value if valley_value > 0 else 0
        
        features.extend([
            peak_hour / 23,  # Normalized peak hour
            peak_to_valley_ratio,
            p_mean.std() / p_mean.mean() if p_mean.mean() > 0 else 0  # CV
        ])
        
        # 3. Voltage characteristics
        v_mean = station_data['v_pu_mean'].mean()
        v_std = station_data['v_pu_std'].mean()
        v_min = station_data['v_pu_min'].min()
        
        features.extend([
            v_mean,
            v_std,
            v_min
        ])
        
        # 4. Power factor
        fp_mean = station_data['fp_mean'].mean()
        features.append(fp_mean)
        
        features_dict[station] = features
    
    # Create DataFrame
    feature_names = (
        [f'p_h{i:02d}' for i in range(24)] +  # Hourly power
        ['peak_hour_norm', 'peak_valley_ratio', 'power_cv'] +  # Peak features
        ['v_mean', 'v_std', 'v_min'] +  # Voltage features
        ['fp_mean']  # Power factor
    )
    
    features_df = pd.DataFrame.from_dict(features_dict, orient='index', columns=feature_names)
    features_df.index.name = 'station'
    
    print(f"Feature matrix shape: {features_df.shape}")
    print(f"Features: {len(feature_names)}")
    
    return features_df, feature_names

def perform_clustering(features_df, n_clusters=2):
    """Perform K-means clustering."""
    print(f"\nPerforming K-means clustering with {n_clusters} clusters...")
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_df)
    
    # Perform clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(features_scaled)
    
    # Calculate silhouette score
    silhouette = silhouette_score(features_scaled, clusters)
    print(f"Silhouette score: {silhouette:.3f}")
    
    # Add cluster labels
    features_df['cluster'] = clusters
    
    return features_df, kmeans, scaler

def analyze_clusters(df, features_df):
    """Analyze characteristics of each cluster."""
    print("\nAnalyzing clusters...")
    
    # Get station metrics from original data
    station_metrics = df.groupby('station').agg({
        'p_total': ['mean', 'max'],
        'v_pu': ['mean', 'min'],
        'fp': 'mean'
    }).round(3)
    
    station_metrics.columns = ['_'.join(col).strip() for col in station_metrics.columns]
    
    # Add cluster labels
    station_metrics['cluster'] = features_df['cluster']
    
    # Add distance information
    distances = {
        'Pilcaniyeu': 0,
        'Jacobacci': 150,
        'Maquinchao': 210,
        'Los Menucos': 270
    }
    station_metrics['distance_km'] = [distances.get(idx, 0) for idx in station_metrics.index]
    
    print("\nCluster assignments:")
    print(station_metrics[['distance_km', 'cluster', 'p_total_mean', 'v_pu_mean']])
    
    # Cluster summary
    cluster_summary = station_metrics.groupby('cluster').agg({
        'p_total_mean': ['mean', 'std'],
        'v_pu_mean': ['mean', 'std'],
        'distance_km': ['mean', 'std']
    }).round(3)
    
    print("\nCluster summary:")
    print(cluster_summary)
    
    return station_metrics, cluster_summary

def perform_pca(features_df):
    """Perform PCA for visualization."""
    print("\nPerforming PCA...")
    
    # Remove cluster column for PCA
    features_only = features_df.drop('cluster', axis=1, errors='ignore')
    
    # Standardize
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_only)
    
    # PCA
    pca = PCA()
    pca_result = pca.fit_transform(features_scaled)
    
    # Explained variance
    exp_var = pca.explained_variance_ratio_
    cum_var = exp_var.cumsum()
    
    print(f"Explained variance by first 3 components: {exp_var[:3]}")
    print(f"Cumulative variance (3 components): {cum_var[2]:.1%}")
    
    # Create PCA DataFrame
    pca_df = pd.DataFrame(
        pca_result[:, :3],
        index=features_only.index,
        columns=['PC1', 'PC2', 'PC3']
    )
    
    if 'cluster' in features_df.columns:
        pca_df['cluster'] = features_df['cluster']
    
    return pca_df, pca

def create_visualizations(df, features_df, pca_df, station_metrics, pca):
    """Create clustering visualizations."""
    print("\nCreating visualizations...")
    
    output_dir = project_root / "reports" / "figures" / "clustering"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Hourly profiles by cluster
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    stations = features_df.index
    
    for i, station in enumerate(stations):
        ax = axes[i//2, i%2]
        
        # Get hourly data
        hourly_data = df[df['station'] == station].groupby('hour')['p_total'].agg(['mean', 'std'])
        
        # Plot with cluster color
        cluster = features_df.loc[station, 'cluster']
        color = 'blue' if cluster == 0 else 'red'
        
        ax.plot(hourly_data.index, hourly_data['mean'], 'o-', color=color, linewidth=2, markersize=8)
        ax.fill_between(hourly_data.index, 
                       hourly_data['mean'] - hourly_data['std'],
                       hourly_data['mean'] + hourly_data['std'],
                       alpha=0.3, color=color)
        
        ax.set_title(f'{station} (Cluster {cluster})', fontsize=12, fontweight='bold')
        ax.set_xlabel('Hour')
        ax.set_ylabel('Power (MW)')
        ax.grid(True, alpha=0.3)
        ax.set_xticks(range(0, 24, 3))
    
    plt.suptitle('Hourly Demand Profiles by Station and Cluster', fontsize=16)
    plt.tight_layout()
    plt.savefig(output_dir / 'hourly_profiles_by_cluster.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. PCA visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 2D PCA
    if 'cluster' in pca_df.columns:
        colors = ['blue', 'red', 'green', 'orange']
        for cluster in pca_df['cluster'].unique():
            mask = pca_df['cluster'] == cluster
            ax1.scatter(pca_df.loc[mask, 'PC1'], 
                       pca_df.loc[mask, 'PC2'],
                       c=colors[cluster], 
                       s=200, 
                       label=f'Cluster {cluster}',
                       edgecolors='black',
                       linewidth=2)
        
        # Add station labels
        for idx in pca_df.index:
            ax1.annotate(idx, 
                        (pca_df.loc[idx, 'PC1'], pca_df.loc[idx, 'PC2']),
                        xytext=(5, 5), 
                        textcoords='offset points',
                        fontsize=10,
                        fontweight='bold')
    
    ax1.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)')
    ax1.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)')
    ax1.set_title('PCA - Station Clustering')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Scree plot
    var_exp = pca.explained_variance_ratio_[:10]
    cum_var = var_exp.cumsum()
    
    ax2.bar(range(1, len(var_exp)+1), var_exp, alpha=0.7, label='Individual')
    ax2.plot(range(1, len(var_exp)+1), cum_var, 'ro-', linewidth=2, markersize=8, label='Cumulative')
    ax2.set_xlabel('Principal Component')
    ax2.set_ylabel('Variance Explained')
    ax2.set_title('PCA Scree Plot')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'pca_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Cluster characteristics heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Prepare data for heatmap
    heatmap_data = station_metrics[['distance_km', 'p_total_mean', 'p_total_max', 
                                   'v_pu_mean', 'v_pu_min', 'fp_mean', 'cluster']]
    
    # Normalize for visualization
    heatmap_norm = heatmap_data.copy()
    for col in heatmap_data.columns:
        if col != 'cluster':
            heatmap_norm[col] = (heatmap_data[col] - heatmap_data[col].min()) / (heatmap_data[col].max() - heatmap_data[col].min())
    
    # Sort by cluster
    heatmap_norm = heatmap_norm.sort_values('cluster')
    
    # Create heatmap
    sns.heatmap(heatmap_norm.drop('cluster', axis=1).T, 
                xticklabels=heatmap_norm.index,
                yticklabels=['Distance (km)', 'P avg (MW)', 'P max (MW)', 
                           'V avg (pu)', 'V min (pu)', 'FP avg'],
                cmap='RdYlBu_r',
                annot=True,
                fmt='.2f',
                cbar_kws={'label': 'Normalized Value'},
                linewidths=0.5)
    
    # Add cluster separators
    clusters = heatmap_norm['cluster'].values
    for i in range(1, len(clusters)):
        if clusters[i] != clusters[i-1]:
            ax.axvline(x=i, color='black', linewidth=3)
    
    plt.title('Station Characteristics by Cluster (Normalized)', fontsize=14)
    plt.tight_layout()
    plt.savefig(output_dir / 'cluster_characteristics_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualizations saved to {output_dir}")

def save_results(features_df, station_metrics, cluster_summary, pca_df):
    """Save clustering results."""
    output_dir = project_root / "data" / "processed" / "clustering"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save DataFrames
    features_df.to_csv(output_dir / "station_features.csv")
    station_metrics.to_csv(output_dir / "station_clusters.csv")
    cluster_summary.to_csv(output_dir / "cluster_summary.csv")
    pca_df.to_csv(output_dir / "pca_results.csv")
    
    # Save summary JSON
    summary = {
        'analysis_date': datetime.now().isoformat(),
        'n_stations': len(features_df),
        'n_clusters': len(features_df['cluster'].unique()) if 'cluster' in features_df.columns else 0,
        'features_used': list(features_df.columns),
        'cluster_assignments': {
            idx: int(row['cluster']) for idx, row in station_metrics.iterrows() if 'cluster' in station_metrics.columns
        }
    }
    
    with open(output_dir / "clustering_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nResults saved to {output_dir}")

def main():
    """Main clustering analysis."""
    print("="*60)
    print("PHASE 4: CLUSTERING ANALYSIS - DEMAND PATTERNS")
    print("="*60)
    
    # Load data
    df = load_data()
    
    # Create hourly profiles
    hourly_profiles = create_hourly_profiles(df)
    
    # Create feature matrix
    features_df, feature_names = create_feature_matrix(hourly_profiles)
    
    # Determine optimal number of clusters
    # With only 4 stations, we'll try 2 clusters
    n_clusters = 2
    
    # Perform clustering
    features_df, kmeans, scaler = perform_clustering(features_df, n_clusters)
    
    # Analyze clusters
    station_metrics, cluster_summary = analyze_clusters(df, features_df)
    
    # Perform PCA
    pca_df, pca = perform_pca(features_df)
    
    # Create visualizations
    create_visualizations(df, features_df, pca_df, station_metrics, pca)
    
    # Save results
    save_results(features_df, station_metrics, cluster_summary, pca_df)
    
    print("\n" + "="*60)
    print("CLUSTERING ANALYSIS COMPLETE")
    print("="*60)
    
    # Key findings
    print("\nKEY FINDINGS:")
    print("1. Station Clustering:")
    for station, row in station_metrics.iterrows():
        print(f"   - {station}: Cluster {row['cluster']} "
              f"(P={row['p_total_mean']:.2f} MW, V={row['v_pu_mean']:.3f} pu)")
    
    print("\n2. Cluster Characteristics:")
    if len(cluster_summary) > 0:
        for cluster in range(n_clusters):
            stations_in_cluster = [s for s, c in features_df['cluster'].items() if c == cluster]
            print(f"   - Cluster {cluster}: {stations_in_cluster}")
    
    print("\n3. Implications for DG:")
    print("   - Clusters identify stations with similar operational patterns")
    print("   - DG solutions can be standardized within clusters")
    print("   - Priority should be given to high-demand, low-voltage clusters")
    
    return 0

if __name__ == "__main__":
    main()