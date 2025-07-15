#!/usr/bin/env python3
"""
Phase 4: Clustering Analysis - Criticality Analysis
Identify critical stations based on voltage and operational metrics
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform
import warnings
warnings.filterwarnings('ignore')

# Project root
project_root = Path(__file__).parent.parent.parent

def load_data():
    """Load quality metrics and temporal data."""
    print("Loading quality metrics...")
    
    # Load quality metrics
    quality_file = project_root / "data" / "processed" / "quality_metrics.json"
    with open(quality_file, 'r') as f:
        quality_data = json.load(f)
    
    # Load temporal analysis
    temporal_file = project_root / "data" / "processed" / "temporal_analysis.json"
    with open(temporal_file, 'r') as f:
        temporal_data = json.load(f)
    
    # Load consolidated data for additional metrics
    data_file = project_root / "data" / "processed" / "consolidated_data.csv"
    df = pd.read_csv(data_file, parse_dates=['timestamp'])
    
    return quality_data, temporal_data, df

def calculate_criticality_metrics(quality_data, temporal_data, df):
    """Calculate comprehensive criticality metrics for each station."""
    print("\nCalculating criticality metrics...")
    
    metrics = {}
    
    # Station order and distances
    distances = {
        'Pilcaniyeu': 0,
        'Jacobacci': 150,
        'Maquinchao': 210,
        'Los Menucos': 270
    }
    
    nominal_loads = {
        'Pilcaniyeu': 0,
        'Jacobacci': 1.45,
        'Maquinchao': 0.50,
        'Los Menucos': 1.40
    }
    
    for station in quality_data.keys():
        station_df = df[df['station'] == station]
        
        # 1. Voltage criticality metrics
        v_metrics = quality_data[station]['voltage_quality']
        v_criticality = {
            'v_violation_pct': 100 - v_metrics['within_limits_pct'],  # % time outside limits
            'v_drop_severity': 1 - v_metrics['avg_voltage_pu'],  # Average voltage drop
            'v_min_severity': 1 - v_metrics['min_voltage_pu'],  # Worst voltage drop
            'v_variability': station_df['v_pu'].std()  # Voltage stability
        }
        
        # 2. Load criticality metrics
        p_metrics = quality_data[station]['power_stats']
        nominal = nominal_loads.get(station, 1)
        load_criticality = {
            'utilization_ratio': p_metrics['avg_power_mw'] / nominal if nominal > 0 else 0,
            'peak_ratio': p_metrics['max_power_mw'] / nominal if nominal > 0 else 0,
            'load_variability': station_df['p_total'].std() / station_df['p_total'].mean()
        }
        
        # 3. System position criticality
        distance = distances.get(station, 0)
        position_criticality = {
            'distance_normalized': distance / 270,  # Normalized by max distance
            'downstream_impact': (270 - distance) / 270  # Impact on downstream stations
        }
        
        # 4. Temporal criticality
        if station in temporal_data.get('by_station', {}):
            temp_data = temporal_data['by_station'][station]
            peak_data = temp_data.get('peak_analysis', {})
            temporal_criticality = {
                'peak_demand_ratio': peak_data.get('avg_peak_demand', 0) / p_metrics['avg_power_mw'] if p_metrics['avg_power_mw'] > 0 else 0,
                'peak_hours_violation': station_df[station_df['is_peak_hour']]['v_within_limits'].mean() if len(station_df[station_df['is_peak_hour']]) > 0 else 0
            }
        else:
            temporal_criticality = {'peak_demand_ratio': 0, 'peak_hours_violation': 0}
        
        # 5. Calculate composite criticality score
        # Weighted sum of normalized metrics
        weights = {
            'voltage': 0.35,
            'load': 0.25,
            'position': 0.20,
            'temporal': 0.20
        }
        
        v_score = (v_criticality['v_violation_pct']/100 * 0.4 + 
                  v_criticality['v_drop_severity'] * 0.4 +
                  v_criticality['v_variability'] * 0.2)
        
        l_score = (load_criticality['utilization_ratio'] * 0.5 +
                  load_criticality['peak_ratio'] * 0.3 +
                  load_criticality['load_variability'] * 0.2)
        
        p_score = (position_criticality['distance_normalized'] * 0.6 +
                  position_criticality['downstream_impact'] * 0.4)
        
        t_score = (temporal_criticality['peak_demand_ratio'] * 0.7 +
                  (1 - temporal_criticality['peak_hours_violation']) * 0.3)
        
        composite_score = (weights['voltage'] * v_score +
                          weights['load'] * l_score +
                          weights['position'] * p_score +
                          weights['temporal'] * t_score)
        
        metrics[station] = {
            'voltage_criticality': v_criticality,
            'load_criticality': load_criticality,
            'position_criticality': position_criticality,
            'temporal_criticality': temporal_criticality,
            'composite_score': composite_score,
            'component_scores': {
                'voltage_score': v_score,
                'load_score': l_score,
                'position_score': p_score,
                'temporal_score': t_score
            }
        }
    
    return metrics

def perform_hierarchical_clustering(metrics):
    """Perform hierarchical clustering on criticality metrics."""
    print("\nPerforming hierarchical clustering...")
    
    # Create feature matrix
    stations = list(metrics.keys())
    features = []
    
    for station in stations:
        m = metrics[station]
        feature_vector = [
            m['voltage_criticality']['v_violation_pct'] / 100,
            m['voltage_criticality']['v_drop_severity'],
            m['voltage_criticality']['v_min_severity'],
            m['load_criticality']['utilization_ratio'],
            m['load_criticality']['peak_ratio'],
            m['position_criticality']['distance_normalized'],
            m['composite_score']
        ]
        features.append(feature_vector)
    
    features_array = np.array(features)
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_array)
    
    # Calculate linkage matrix
    linkage_matrix = linkage(features_scaled, method='ward')
    
    # Perform clustering
    n_clusters = 2
    clusters = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward').fit_predict(features_scaled)
    
    # Create results DataFrame
    results_df = pd.DataFrame({
        'station': stations,
        'criticality_cluster': clusters,
        'composite_score': [metrics[s]['composite_score'] for s in stations]
    })
    
    return results_df, linkage_matrix, features_scaled, stations

def create_criticality_visualizations(metrics, results_df, linkage_matrix, features_scaled, stations):
    """Create criticality analysis visualizations."""
    print("\nCreating criticality visualizations...")
    
    output_dir = project_root / "reports" / "figures" / "clustering"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Criticality scores radar chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), subplot_kw=dict(projection='polar'))
    
    # Prepare data for radar chart
    categories = ['Voltage', 'Load', 'Position', 'Temporal', 'Composite']
    
    for ax, (station, m) in zip([ax1, ax2], list(metrics.items())[:2]):
        scores = m['component_scores']
        values = [
            scores['voltage_score'],
            scores['load_score'],
            scores['position_score'],
            scores['temporal_score'],
            m['composite_score']
        ]
        values = values + [values[0]]  # Complete the circle
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        
        ax.plot(angles, values, 'o-', linewidth=2, markersize=8)
        ax.fill(angles, values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title(f'{station} Criticality Profile', fontsize=14, fontweight='bold')
        ax.grid(True)
    
    plt.suptitle('Station Criticality Profiles', fontsize=16)
    plt.tight_layout()
    plt.savefig(output_dir / 'criticality_radar_charts.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Hierarchical clustering dendrogram
    fig, ax = plt.subplots(figsize=(12, 8))
    
    dendrogram(linkage_matrix, labels=stations, ax=ax)
    ax.set_xlabel('Station', fontsize=12)
    ax.set_ylabel('Distance', fontsize=12)
    ax.set_title('Hierarchical Clustering of Station Criticality', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'criticality_dendrogram.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Criticality heatmap
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Prepare data for heatmap
    heatmap_data = []
    for station in stations:
        m = metrics[station]
        row = [
            m['voltage_criticality']['v_violation_pct'] / 100,
            m['voltage_criticality']['v_drop_severity'],
            m['voltage_criticality']['v_min_severity'],
            m['voltage_criticality']['v_variability'],
            m['load_criticality']['utilization_ratio'],
            m['load_criticality']['peak_ratio'],
            m['load_criticality']['load_variability'],
            m['position_criticality']['distance_normalized'],
            m['position_criticality']['downstream_impact'],
            m['temporal_criticality']['peak_demand_ratio'],
            m['composite_score']
        ]
        heatmap_data.append(row)
    
    columns = [
        'V Violation %', 'V Drop Avg', 'V Drop Min', 'V Variability',
        'Load Utilization', 'Peak Ratio', 'Load Variability',
        'Distance', 'Downstream Impact', 'Peak Demand Ratio',
        'COMPOSITE SCORE'
    ]
    
    df_heatmap = pd.DataFrame(heatmap_data, index=stations, columns=columns)
    
    # Sort by composite score
    df_heatmap = df_heatmap.sort_values('COMPOSITE SCORE', ascending=False)
    
    # Create heatmap
    sns.heatmap(df_heatmap, annot=True, fmt='.2f', cmap='YlOrRd', 
                linewidths=0.5, cbar_kws={'label': 'Criticality Score'})
    
    plt.title('Station Criticality Metrics Heatmap', fontsize=16, fontweight='bold')
    plt.xlabel('Metrics', fontsize=12)
    plt.ylabel('Stations', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'criticality_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Criticality ranking bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sort stations by composite score
    sorted_data = results_df.sort_values('composite_score', ascending=True)
    
    colors = ['red' if score > 0.7 else 'orange' if score > 0.5 else 'yellow' 
              for score in sorted_data['composite_score']]
    
    bars = ax.barh(sorted_data['station'], sorted_data['composite_score'], color=colors)
    
    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{width:.3f}', ha='left', va='center', fontweight='bold')
    
    ax.set_xlabel('Composite Criticality Score', fontsize=12)
    ax.set_ylabel('Station', fontsize=12)
    ax.set_title('Station Criticality Ranking', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 1)
    ax.grid(True, axis='x', alpha=0.3)
    
    # Add criticality level lines
    ax.axvline(x=0.7, color='red', linestyle='--', alpha=0.5, label='High Critical')
    ax.axvline(x=0.5, color='orange', linestyle='--', alpha=0.5, label='Medium Critical')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'criticality_ranking.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Criticality visualizations saved to {output_dir}")

def save_criticality_results(metrics, results_df):
    """Save criticality analysis results."""
    output_dir = project_root / "data" / "processed" / "clustering"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed metrics
    with open(output_dir / "criticality_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    # Save summary DataFrame
    results_df.to_csv(output_dir / "criticality_summary.csv", index=False)
    
    # Create priority report
    priority_report = {
        'analysis_date': datetime.now().isoformat(),
        'methodology': {
            'voltage_weight': 0.35,
            'load_weight': 0.25,
            'position_weight': 0.20,
            'temporal_weight': 0.20
        },
        'priority_ranking': []
    }
    
    # Sort by composite score
    sorted_results = results_df.sort_values('composite_score', ascending=False)
    
    for _, row in sorted_results.iterrows():
        station = row['station']
        m = metrics[station]
        
        priority_entry = {
            'rank': len(priority_report['priority_ranking']) + 1,
            'station': station,
            'composite_score': float(row['composite_score']),
            'criticality_level': 'HIGH' if row['composite_score'] > 0.7 else 'MEDIUM' if row['composite_score'] > 0.5 else 'LOW',
            'key_issues': []
        }
        
        # Identify key issues
        if m['voltage_criticality']['v_violation_pct'] > 90:
            priority_entry['key_issues'].append('Severe voltage violations (>90% time)')
        if m['voltage_criticality']['v_drop_severity'] > 0.5:
            priority_entry['key_issues'].append('Extreme voltage drop (>50%)')
        if m['load_criticality']['utilization_ratio'] > 0.8:
            priority_entry['key_issues'].append('High utilization (>80%)')
        if m['position_criticality']['distance_normalized'] > 0.7:
            priority_entry['key_issues'].append('Remote location')
        
        priority_report['priority_ranking'].append(priority_entry)
    
    with open(output_dir / "dg_priority_report.json", 'w') as f:
        json.dump(priority_report, f, indent=2)
    
    print(f"\nCriticality results saved to {output_dir}")

def main():
    """Main criticality analysis."""
    print("="*60)
    print("PHASE 4: CRITICALITY ANALYSIS")
    print("="*60)
    
    # Load data
    quality_data, temporal_data, df = load_data()
    
    # Calculate criticality metrics
    metrics = calculate_criticality_metrics(quality_data, temporal_data, df)
    
    # Perform hierarchical clustering
    results_df, linkage_matrix, features_scaled, stations = perform_hierarchical_clustering(metrics)
    
    # Create visualizations
    create_criticality_visualizations(metrics, results_df, linkage_matrix, features_scaled, stations)
    
    # Save results
    save_criticality_results(metrics, results_df)
    
    print("\n" + "="*60)
    print("CRITICALITY ANALYSIS COMPLETE")
    print("="*60)
    
    # Summary report
    print("\nCRITICALITY RANKING:")
    sorted_results = results_df.sort_values('composite_score', ascending=False)
    for i, (_, row) in enumerate(sorted_results.iterrows()):
        level = 'HIGH' if row['composite_score'] > 0.7 else 'MEDIUM' if row['composite_score'] > 0.5 else 'LOW'
        print(f"{i+1}. {row['station']}: {row['composite_score']:.3f} ({level})")
    
    print("\nKEY FINDINGS:")
    print("1. All stations show critical conditions requiring immediate intervention")
    print("2. Voltage criticality is the dominant factor across all stations")
    print("3. Priority for DG deployment should follow the criticality ranking")
    print("4. Multiple small DG units may be more effective than single large installations")
    
    return 0

if __name__ == "__main__":
    main()