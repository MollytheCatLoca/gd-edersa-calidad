#!/usr/bin/env python3
"""
Phase 4: Correlation Analysis
Analyze correlations between stations and identify propagation patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Project root
project_root = Path(__file__).parent.parent.parent

def load_data():
    """Load consolidated data and prepare for correlation analysis."""
    print("Loading data for correlation analysis...")
    
    data_file = project_root / "data" / "processed" / "consolidated_data.csv"
    df = pd.read_csv(data_file, parse_dates=['timestamp'])
    
    print(f"Loaded {len(df):,} records")
    return df

def prepare_time_series(df):
    """Prepare time series data for each station."""
    print("\nPreparing time series data...")
    
    # Pivot data to have stations as columns
    # We'll analyze power, voltage, and reactive power
    
    # Power time series
    p_series = df.pivot_table(
        index='timestamp',
        columns='station',
        values='p_total',
        aggfunc='mean'
    )
    
    # Voltage time series
    v_series = df.pivot_table(
        index='timestamp',
        columns='station',
        values='v_pu',
        aggfunc='mean'
    )
    
    # Reactive power time series
    q_series = df.pivot_table(
        index='timestamp',
        columns='station',
        values='q_total',
        aggfunc='mean'
    )
    
    # Forward fill missing values (max 1 hour gap)
    p_series = p_series.fillna(method='ffill', limit=4)
    v_series = v_series.fillna(method='ffill', limit=4)
    q_series = q_series.fillna(method='ffill', limit=4)
    
    print(f"Time series shape: {p_series.shape}")
    print(f"Date range: {p_series.index.min()} to {p_series.index.max()}")
    
    return p_series, v_series, q_series

def calculate_correlations(p_series, v_series, q_series):
    """Calculate various correlation metrics between stations."""
    print("\nCalculating correlations...")
    
    correlations = {
        'power': {},
        'voltage': {},
        'reactive': {},
        'cross': {}
    }
    
    # 1. Power correlations
    correlations['power']['pearson'] = p_series.corr(method='pearson')
    correlations['power']['spearman'] = p_series.corr(method='spearman')
    
    # 2. Voltage correlations
    correlations['voltage']['pearson'] = v_series.corr(method='pearson')
    correlations['voltage']['spearman'] = v_series.corr(method='spearman')
    
    # 3. Reactive power correlations
    correlations['reactive']['pearson'] = q_series.corr(method='pearson')
    correlations['reactive']['spearman'] = q_series.corr(method='spearman')
    
    # 4. Cross-correlations (power vs voltage)
    stations = p_series.columns
    cross_corr = pd.DataFrame(index=stations, columns=stations)
    
    for st1 in stations:
        for st2 in stations:
            # Correlation between st1 power and st2 voltage
            mask = p_series[st1].notna() & v_series[st2].notna()
            if mask.sum() > 100:  # Need sufficient data
                corr = p_series[st1][mask].corr(v_series[st2][mask])
                cross_corr.loc[st1, st2] = corr
    
    correlations['cross']['power_voltage'] = cross_corr.astype(float)
    
    return correlations

def analyze_lag_correlations(p_series, v_series, max_lag_hours=4):
    """Analyze correlations with time lags to identify propagation."""
    print(f"\nAnalyzing lag correlations (up to {max_lag_hours} hours)...")
    
    stations = p_series.columns
    n_lags = max_lag_hours * 4  # 15-minute intervals
    
    # Initialize results
    lag_correlations = {
        'power': {},
        'voltage': {}
    }
    
    # Station pairs to analyze (considering physical order)
    station_pairs = [
        ('Pilcaniyeu', 'Jacobacci'),
        ('Jacobacci', 'Maquinchao'),
        ('Maquinchao', 'Los Menucos'),
        ('Pilcaniyeu', 'Los Menucos')  # Full line
    ]
    
    for upstream, downstream in station_pairs:
        if upstream in stations and downstream in stations:
            pair_key = f"{upstream}->{downstream}"
            
            # Power lag correlation
            p_lag_corr = []
            v_lag_corr = []
            
            for lag in range(-n_lags, n_lags + 1):
                # Shift downstream station by lag
                if lag < 0:
                    # Downstream leads upstream (unusual)
                    p_corr = p_series[upstream].corr(p_series[downstream].shift(-lag))
                    v_corr = v_series[upstream].corr(v_series[downstream].shift(-lag))
                else:
                    # Upstream leads downstream (expected)
                    p_corr = p_series[upstream].shift(lag).corr(p_series[downstream])
                    v_corr = v_series[upstream].shift(lag).corr(v_series[downstream])
                
                p_lag_corr.append(p_corr)
                v_lag_corr.append(v_corr)
            
            lag_correlations['power'][pair_key] = {
                'lags': list(range(-n_lags, n_lags + 1)),
                'correlations': p_lag_corr,
                'max_corr': max(p_lag_corr) if p_lag_corr else 0,
                'max_lag': (range(-n_lags, n_lags + 1))[p_lag_corr.index(max(p_lag_corr))] if p_lag_corr else 0
            }
            
            lag_correlations['voltage'][pair_key] = {
                'lags': list(range(-n_lags, n_lags + 1)),
                'correlations': v_lag_corr,
                'max_corr': max(v_lag_corr) if v_lag_corr else 0,
                'max_lag': (range(-n_lags, n_lags + 1))[v_lag_corr.index(max(v_lag_corr))] if v_lag_corr else 0
            }
    
    return lag_correlations

def analyze_extreme_events(df):
    """Analyze correlation during extreme events (low voltage, high demand)."""
    print("\nAnalyzing correlations during extreme events...")
    
    # Define extreme events
    # Low voltage event: any station < 0.2 pu
    # High demand event: any station > 90th percentile
    
    extreme_correlations = {}
    
    # 1. Low voltage events
    min_v_by_time = df.groupby('timestamp')['v_pu'].min()
    low_v_times = min_v_by_time[min_v_by_time < 0.2].index
    low_v_data = df[df['timestamp'].isin(low_v_times)].copy()
    
    if len(low_v_data) > 0:
        # Correlations during low voltage
        low_v_pivot = low_v_data.pivot_table(
            index='timestamp',
            columns='station',
            values='v_pu',
            aggfunc='mean'
        )
        extreme_correlations['low_voltage'] = low_v_pivot.corr()
    
    # 2. High demand events
    p90 = df.groupby('station')['p_total'].quantile(0.9)
    high_demand_rows = []
    
    for station in df['station'].unique():
        station_high = df[(df['station'] == station) & (df['p_total'] > p90[station])]
        high_demand_rows.append(station_high)
    
    high_demand_df = pd.concat(high_demand_rows)
    high_demand_times = high_demand_df['timestamp'].unique()
    
    high_d_data = df[df['timestamp'].isin(high_demand_times)]
    
    if len(high_d_data) > 0:
        # Correlations during high demand
        high_d_pivot = high_d_data.pivot_table(
            index='timestamp',
            columns='station',
            values='v_pu',
            aggfunc='mean'
        )
        extreme_correlations['high_demand'] = high_d_pivot.corr()
    
    return extreme_correlations

def create_correlation_visualizations(correlations, lag_correlations, extreme_correlations):
    """Create correlation analysis visualizations."""
    print("\nCreating correlation visualizations...")
    
    output_dir = project_root / "reports" / "figures" / "clustering"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Correlation matrices heatmap
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    
    # Power correlation
    sns.heatmap(correlations['power']['pearson'], annot=True, fmt='.3f', 
                cmap='coolwarm', center=0, vmin=-1, vmax=1,
                ax=axes[0,0], cbar_kws={'label': 'Correlation'})
    axes[0,0].set_title('Power Correlations (Pearson)', fontsize=12, fontweight='bold')
    
    # Voltage correlation
    sns.heatmap(correlations['voltage']['pearson'], annot=True, fmt='.3f',
                cmap='coolwarm', center=0, vmin=-1, vmax=1,
                ax=axes[0,1], cbar_kws={'label': 'Correlation'})
    axes[0,1].set_title('Voltage Correlations (Pearson)', fontsize=12, fontweight='bold')
    
    # Cross correlation (Power -> Voltage)
    sns.heatmap(correlations['cross']['power_voltage'], annot=True, fmt='.3f',
                cmap='coolwarm', center=0, vmin=-1, vmax=1,
                ax=axes[1,0], cbar_kws={'label': 'Correlation'})
    axes[1,0].set_title('Cross Correlation: Power → Voltage', fontsize=12, fontweight='bold')
    axes[1,0].set_xlabel('Station (Voltage)')
    axes[1,0].set_ylabel('Station (Power)')
    
    # Extreme event correlations
    if 'low_voltage' in extreme_correlations:
        sns.heatmap(extreme_correlations['low_voltage'], annot=True, fmt='.3f',
                    cmap='coolwarm', center=0, vmin=-1, vmax=1,
                    ax=axes[1,1], cbar_kws={'label': 'Correlation'})
        axes[1,1].set_title('Voltage Correlations During Low V Events', fontsize=12, fontweight='bold')
    else:
        axes[1,1].text(0.5, 0.5, 'No extreme events found', ha='center', va='center')
        axes[1,1].set_title('Extreme Event Correlations', fontsize=12)
    
    plt.suptitle('Station Correlation Analysis', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'correlation_matrices.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Lag correlation plots
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.ravel()
    
    # Plot voltage lag correlations
    for i, (pair, data) in enumerate(lag_correlations['voltage'].items()):
        if i < 4:
            ax = axes[i]
            lags_minutes = [lag * 15 for lag in data['lags']]  # Convert to minutes
            ax.plot(lags_minutes, data['correlations'], 'b-', linewidth=2)
            ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            
            # Mark maximum correlation
            max_lag_min = data['max_lag'] * 15
            ax.axvline(x=max_lag_min, color='red', linestyle=':', alpha=0.7,
                      label=f'Max @ {max_lag_min} min')
            
            ax.set_xlabel('Lag (minutes)')
            ax.set_ylabel('Correlation')
            ax.set_title(f'Voltage Propagation: {pair}', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.set_xlim(-60, 60)  # ±1 hour
    
    plt.suptitle('Voltage Propagation Analysis (Lag Correlations)', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'lag_correlations.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Correlation network diagram
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Station positions (approximate geographic layout)
    positions = {
        'Pilcaniyeu': (0, 0),
        'Jacobacci': (3, -0.5),
        'Maquinchao': (5, -0.3),
        'Los Menucos': (7, 0)
    }
    
    # Draw nodes
    for station, (x, y) in positions.items():
        circle = plt.Circle((x, y), 0.3, color='lightblue', ec='black', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, station, ha='center', va='center', fontweight='bold', fontsize=10)
    
    # Draw edges based on correlation strength
    v_corr = correlations['voltage']['pearson']
    threshold = 0.5  # Only show strong correlations
    
    for st1 in positions:
        for st2 in positions:
            if st1 != st2 and st1 in v_corr.index and st2 in v_corr.columns:
                corr_value = v_corr.loc[st1, st2]
                if abs(corr_value) > threshold:
                    x1, y1 = positions[st1]
                    x2, y2 = positions[st2]
                    
                    # Line width based on correlation strength
                    width = abs(corr_value) * 5
                    color = 'green' if corr_value > 0 else 'red'
                    alpha = abs(corr_value)
                    
                    ax.plot([x1, x2], [y1, y2], color=color, linewidth=width, 
                           alpha=alpha, zorder=1)
                    
                    # Add correlation value
                    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                    ax.text(mid_x, mid_y + 0.1, f'{corr_value:.2f}', 
                           ha='center', fontsize=8, bbox=dict(boxstyle='round,pad=0.3', 
                           facecolor='white', alpha=0.8))
    
    ax.set_xlim(-1, 8)
    ax.set_ylim(-2, 2)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Voltage Correlation Network\n(Green: Positive, Red: Negative, Width: Strength)', 
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'correlation_network.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Correlation visualizations saved to {output_dir}")

def save_correlation_results(correlations, lag_correlations, extreme_correlations):
    """Save correlation analysis results."""
    output_dir = project_root / "data" / "processed" / "clustering"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save correlation matrices
    for metric in ['power', 'voltage', 'reactive']:
        for method in ['pearson', 'spearman']:
            filename = f"correlation_{metric}_{method}.csv"
            correlations[metric][method].to_csv(output_dir / filename)
    
    # Save cross-correlation
    correlations['cross']['power_voltage'].to_csv(output_dir / "correlation_cross_power_voltage.csv")
    
    # Save lag correlation summary
    lag_summary = {
        'analysis_date': datetime.now().isoformat(),
        'propagation_times': {}
    }
    
    for metric in ['power', 'voltage']:
        lag_summary['propagation_times'][metric] = {}
        for pair, data in lag_correlations[metric].items():
            lag_summary['propagation_times'][metric][pair] = {
                'max_correlation': float(data['max_corr']),
                'lag_periods': int(data['max_lag']),
                'lag_minutes': int(data['max_lag'] * 15)
            }
    
    with open(output_dir / "lag_correlation_summary.json", 'w') as f:
        json.dump(lag_summary, f, indent=2)
    
    print(f"\nCorrelation results saved to {output_dir}")

def main():
    """Main correlation analysis."""
    print("="*60)
    print("PHASE 4: CORRELATION ANALYSIS")
    print("="*60)
    
    # Load data
    df = load_data()
    
    # Prepare time series
    p_series, v_series, q_series = prepare_time_series(df)
    
    # Calculate correlations
    correlations = calculate_correlations(p_series, v_series, q_series)
    
    # Analyze lag correlations
    lag_correlations = analyze_lag_correlations(p_series, v_series, max_lag_hours=1)
    
    # Analyze extreme events
    extreme_correlations = analyze_extreme_events(df)
    
    # Create visualizations
    create_correlation_visualizations(correlations, lag_correlations, extreme_correlations)
    
    # Save results
    save_correlation_results(correlations, lag_correlations, extreme_correlations)
    
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS COMPLETE")
    print("="*60)
    
    # Summary findings
    print("\nKEY FINDINGS:")
    
    # Voltage correlations
    v_corr = correlations['voltage']['pearson']
    print("\n1. Voltage Correlations:")
    for i in range(len(v_corr)):
        for j in range(i+1, len(v_corr)):
            st1, st2 = v_corr.index[i], v_corr.columns[j]
            corr_val = v_corr.iloc[i, j]
            print(f"   {st1} ↔ {st2}: {corr_val:.3f}")
    
    # Propagation times
    print("\n2. Voltage Propagation Times:")
    for pair, data in lag_correlations['voltage'].items():
        if data['max_lag'] != 0:
            print(f"   {pair}: {data['max_lag']*15} minutes lag (r={data['max_corr']:.3f})")
    
    print("\n3. Implications:")
    print("   - Strong voltage correlations indicate system-wide issues")
    print("   - Minimal propagation delays suggest tight electrical coupling")
    print("   - DG at any point will affect the entire system")
    print("   - Coordinated control strategy will be essential")
    
    return 0

if __name__ == "__main__":
    main()