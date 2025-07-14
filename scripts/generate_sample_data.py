#!/usr/bin/env python3
"""
Generate sample data for dashboard testing
This creates realistic sample data based on the system configuration
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import random

# Project root
project_root = Path(__file__).parent.parent

# System configuration from CLAUDE.md
STATIONS = {
    'Pilcaniyeu': {'distance_km': 0, 'load_mw': 0, 'is_source': True},
    'Comallo': {'distance_km': 70, 'load_mw': 0.30},
    'Jacobacci': {'distance_km': 150, 'load_mw': 1.45},
    'Maquinchao': {'distance_km': 210, 'load_mw': 0.50},
    'Los Menucos': {'distance_km': 270, 'load_mw': 1.40}
}

def generate_hourly_pattern():
    """Generate realistic hourly load pattern."""
    # Typical residential/commercial pattern
    base_pattern = [
        0.6, 0.5, 0.5, 0.5, 0.6, 0.7,  # 0-5 AM
        0.8, 0.9, 0.95, 0.9, 0.85, 0.8,  # 6-11 AM
        0.85, 0.9, 0.85, 0.8, 0.85, 0.9,  # 12-17 PM
        0.95, 1.0, 1.0, 0.95, 0.8, 0.7   # 18-23 PM
    ]
    return base_pattern

def generate_station_data(station_name, config, start_date, end_date):
    """Generate data for a single station."""
    print(f"Generating data for {station_name}...")
    
    # Create hourly timestamps
    timestamps = pd.date_range(start=start_date, end=end_date, freq='H')
    hourly_pattern = generate_hourly_pattern()
    
    # Base load
    if config.get('is_source'):
        # Pilcaniyeu aggregates all loads
        base_load = sum(s['load_mw'] for s in STATIONS.values() if 'load_mw' in s)
    else:
        base_load = config['load_mw']
    
    # Generate data
    data = []
    for ts in timestamps:
        hour = ts.hour
        day_of_week = ts.dayofweek
        
        # Load factor
        hourly_factor = hourly_pattern[hour]
        weekend_factor = 0.7 if day_of_week in [5, 6] else 1.0
        random_factor = 0.9 + 0.2 * random.random()
        
        # Power
        p_total = base_load * hourly_factor * weekend_factor * random_factor
        
        # Power factor and reactive power
        fp = 0.92 + 0.06 * random.random()  # 0.92-0.98
        q_total = p_total * np.tan(np.arccos(fp))
        
        # Voltage calculation
        if config.get('is_source'):
            v_pu = 1.0 + random.gauss(0, 0.005)
        else:
            # Voltage drop based on distance and load
            distance_factor = config['distance_km'] / 270
            load_factor = p_total / (base_load * 1.2) if base_load > 0 else 0
            base_drop = distance_factor * 0.41  # Max 41% at end
            dynamic_drop = load_factor * 0.1    # Additional 10% under high load
            v_pu = 1.0 - base_drop - dynamic_drop + random.gauss(0, 0.01)
        
        v_pu = max(0.59, min(1.05, v_pu))  # Clamp to realistic range
        
        # Individual phase voltages (small imbalance)
        v1 = 33000 * v_pu * (1 + random.gauss(0, 0.002))
        v2 = 33000 * v_pu * (1 + random.gauss(0, 0.002))
        v3 = 33000 * v_pu * (1 + random.gauss(0, 0.002))
        v_avg = (v1 + v2 + v3) / 3
        
        # Currents (simplified)
        s_total = np.sqrt(p_total**2 + q_total**2)
        i_avg = s_total * 1000 / (np.sqrt(3) * 33) if v_avg > 0 else 0
        i1 = i_avg * (1 + random.gauss(0, 0.02))
        i2 = i_avg * (1 + random.gauss(0, 0.02))
        i3 = i_avg * (1 + random.gauss(0, 0.02))
        
        record = {
            'timestamp': ts,
            'fecha': ts.date(),
            'hora': ts.time(),
            'station': station_name,
            'voltage_level': '33kV',
            'v1': v1,
            'v2': v2,
            'v3': v3,
            'v_avg': v_avg,
            'v_min': min(v1, v2, v3),
            'v_max': max(v1, v2, v3),
            'v_pu': v_avg / 33000,
            'i1': i1,
            'i2': i2,
            'i3': i3,
            'p_total': p_total,
            'q_total': q_total,
            'fp': fp,
            'hour': hour,
            'day_of_week': day_of_week,
            'is_weekend': day_of_week in [5, 6],
            'is_peak_hour': 18 <= hour <= 23,
            'v_within_limits': 0.95 <= v_avg/33000 <= 1.05
        }
        
        data.append(record)
    
    return pd.DataFrame(data)

def main():
    """Generate sample data for all stations."""
    print("="*60)
    print("GENERACIÓN DE DATOS DE MUESTRA")
    print("="*60)
    
    # Date range (1 month for testing)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31, 23, 59, 59)
    
    # Generate data for each station
    all_data = []
    for station, config in STATIONS.items():
        df = generate_station_data(station, config, start_date, end_date)
        all_data.append(df)
        print(f"  {station}: {len(df)} registros generados")
    
    # Combine all data
    consolidated = pd.concat(all_data, ignore_index=True)
    consolidated = consolidated.sort_values(['station', 'timestamp'])
    
    # Save data
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save parquet
    consolidated.to_parquet(processed_dir / "consolidated_data.parquet", index=False)
    print(f"\nDatos consolidados guardados: {len(consolidated)} registros")
    
    # Save CSV sample
    consolidated.head(1000).to_csv(processed_dir / "consolidated_data_sample.csv", index=False)
    
    # Generate quality metrics
    quality_metrics = {}
    for station in STATIONS.keys():
        station_data = consolidated[consolidated['station'] == station]
        quality_metrics[station] = {
            'total_raw_records': len(station_data),
            'total_clean_records': len(station_data),
            'records_removed': 0,
            'removal_percentage': 0,
            'date_range': {
                'start': str(station_data['timestamp'].min()),
                'end': str(station_data['timestamp'].max())
            },
            'voltage_quality': {
                'within_limits_pct': station_data['v_within_limits'].mean() * 100,
                'avg_voltage_pu': station_data['v_pu'].mean(),
                'min_voltage_pu': station_data['v_pu'].min(),
                'max_voltage_pu': station_data['v_pu'].max()
            },
            'power_stats': {
                'avg_power_mw': station_data['p_total'].mean(),
                'max_power_mw': station_data['p_total'].max(),
                'avg_power_factor': station_data['fp'].mean()
            }
        }
    
    with open(processed_dir / "quality_metrics.json", 'w') as f:
        json.dump(quality_metrics, f, indent=2)
    
    # Generate temporal analysis
    temporal_analysis = {
        'overall': {
            'total_days': 31,
            'records_per_day': len(consolidated) / 31,
            'stations_processed': list(STATIONS.keys())
        },
        'by_station': {}
    }
    
    for station in STATIONS.keys():
        station_data = consolidated[consolidated['station'] == station]
        hourly = station_data.groupby('hour')['p_total'].agg(['mean', 'max']).round(3)
        
        temporal_analysis['by_station'][station] = {
            'hourly_profile': {
                'p_total': {
                    'mean': {str(h): float(hourly.loc[h, 'mean']) for h in range(24)},
                    'max': {str(h): float(hourly.loc[h, 'max']) for h in range(24)}
                }
            },
            'peak_analysis': {
                'avg_peak_demand': station_data[station_data['is_peak_hour']]['p_total'].mean(),
                'max_peak_demand': station_data[station_data['is_peak_hour']]['p_total'].max()
            }
        }
    
    with open(processed_dir / "temporal_analysis.json", 'w') as f:
        json.dump(temporal_analysis, f, indent=2)
    
    print("\n" + "="*60)
    print("RESUMEN DE DATOS GENERADOS")
    print("="*60)
    print(f"Período: {start_date} a {end_date}")
    print(f"Estaciones: {len(STATIONS)}")
    print(f"Total registros: {len(consolidated):,}")
    print("\nCalidad de tensión por estación:")
    for station, metrics in quality_metrics.items():
        vq = metrics['voltage_quality']
        print(f"  {station}: {vq['within_limits_pct']:.1f}% dentro de límites, "
              f"V promedio: {vq['avg_voltage_pu']:.3f} pu")
    
    print("\n✓ Datos de muestra generados exitosamente")
    print("✓ El dashboard ya puede mostrar estos datos")
    
    return 0

if __name__ == "__main__":
    exit(main())