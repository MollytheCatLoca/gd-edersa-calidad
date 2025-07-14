#!/usr/bin/env python3
"""
Comprehensive Data Processing for Electrical Grid Analysis
Processes consolidated data and generates all metrics needed for Phase 3 and ML

Author: Claude
Date: July 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import warnings
from scipy import stats
from typing import Dict, List, Tuple, Any
import pyarrow.parquet as pq
from sklearn.preprocessing import StandardScaler
import pickle

warnings.filterwarnings('ignore')

# Project root
project_root = Path(__file__).parent.parent
data_dir = project_root / "data" / "processed"
output_dir = data_dir / "comprehensive_metrics"
ml_features_dir = output_dir / "ml_features"

# Create output directories
output_dir.mkdir(exist_ok=True)
ml_features_dir.mkdir(exist_ok=True)

# Station configuration
STATIONS = ['Pilcaniyeu', 'Jacobacci', 'Maquinchao', 'Los Menucos']
DISTANCES = {
    'Pilcaniyeu': 0,
    'Jacobacci': 150,
    'Maquinchao': 210,
    'Los Menucos': 270
}

NOMINAL_LOADS = {
    'Pilcaniyeu': 0,
    'Jacobacci': 1.45,
    'Maquinchao': 0.50,
    'Los Menucos': 1.40
}

def load_data() -> pd.DataFrame:
    """Load consolidated data."""
    print("Loading consolidated data...")
    data_file = data_dir / "consolidated_data.csv"
    df = pd.read_csv(data_file, parse_dates=['timestamp'])
    print(f"Loaded {len(df):,} records")
    return df

def calculate_processed_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive summary of processed data."""
    print("\n1. Calculating processed data summary...")
    
    # Date ranges by station
    date_ranges = {}
    quality_metrics = {}
    
    for station in STATIONS:
        station_df = df[df['station'] == station]
        if len(station_df) > 0:
            date_ranges[station] = {
                'start': station_df['timestamp'].min().isoformat(),
                'end': station_df['timestamp'].max().isoformat(),
                'days': (station_df['timestamp'].max() - station_df['timestamp'].min()).days,
                'records': len(station_df)
            }
            
            # Basic quality metrics
            quality_metrics[station] = {
                'total_raw_records': len(station_df),
                'total_clean_records': len(station_df),
                'missing_values': station_df.isnull().sum().to_dict(),
                'voltage_quality': {
                    'avg_voltage_pu': float(station_df['v_pu'].mean()),
                    'min_voltage_pu': float(station_df['v_pu'].min()),
                    'max_voltage_pu': float(station_df['v_pu'].max()),
                    'within_limits_pct': float((station_df['v_within_limits'] == True).mean() * 100)
                },
                'power_stats': {
                    'avg_power_mw': float(station_df['p_total'].mean()),
                    'max_power_mw': float(station_df['p_total'].max()),
                    'min_power_mw': float(station_df['p_total'].min()),
                    'avg_power_factor': float(station_df['fp'].mean())
                }
            }
    
    summary = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'total_records': len(df),
        'stations_processed': list(date_ranges.keys()),
        'date_ranges': date_ranges,
        'quality_metrics': quality_metrics,
        'aggregate': {
            'total_days': (df['timestamp'].max() - df['timestamp'].min()).days,
            'avg_records_per_day': len(df) / ((df['timestamp'].max() - df['timestamp'].min()).days + 1),
            'total_raw_records': len(df),
            'removal_rate': 0.0  # No removal in this case
        }
    }
    
    return summary

def calculate_data_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Enhanced data quality metrics."""
    print("\n2. Calculating enhanced data quality metrics...")
    
    quality_metrics = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'by_station': {},
        'aggregate': {}
    }
    
    for station in STATIONS:
        station_df = df[df['station'] == station]
        if len(station_df) == 0:
            continue
            
        # Data completeness
        expected_intervals = pd.date_range(
            start=station_df['timestamp'].min(),
            end=station_df['timestamp'].max(),
            freq='15T'
        )
        completeness = len(station_df) / len(expected_intervals) * 100
        
        # Outlier detection
        v_outliers = np.abs(stats.zscore(station_df['v_pu'].fillna(station_df['v_pu'].mean()))) > 3
        p_outliers = np.abs(stats.zscore(station_df['p_total'].fillna(station_df['p_total'].mean()))) > 3
        
        quality_metrics['by_station'][station] = {
            'total_raw_records': len(station_df),
            'total_clean_records': len(station_df),
            'records_removed': 0,
            'date_range': {
                'start': station_df['timestamp'].min().isoformat(),
                'end': station_df['timestamp'].max().isoformat()
            },
            'completeness_pct': float(completeness),
            'outliers': {
                'voltage_outliers': int(v_outliers.sum()),
                'power_outliers': int(p_outliers.sum())
            },
            'voltage_quality': {
                'avg_voltage_pu': float(station_df['v_pu'].mean()),
                'min_voltage_pu': float(station_df['v_pu'].min()),
                'max_voltage_pu': float(station_df['v_pu'].max()),
                'std_voltage_pu': float(station_df['v_pu'].std()),
                'within_limits_pct': float((station_df['v_within_limits'] == True).mean() * 100),
                'percentiles': {
                    'p5': float(station_df['v_pu'].quantile(0.05)),
                    'p25': float(station_df['v_pu'].quantile(0.25)),
                    'p50': float(station_df['v_pu'].quantile(0.50)),
                    'p75': float(station_df['v_pu'].quantile(0.75)),
                    'p95': float(station_df['v_pu'].quantile(0.95))
                }
            },
            'power_stats': {
                'avg_power_mw': float(station_df['p_total'].mean()),
                'max_power_mw': float(station_df['p_total'].max()),
                'min_power_mw': float(station_df['p_total'].min()),
                'std_power_mw': float(station_df['p_total'].std()),
                'avg_reactive_mvar': float(station_df['q_total'].mean()),
                'avg_power_factor': float(station_df['fp'].mean()),
                'percentiles': {
                    'p5': float(station_df['p_total'].quantile(0.05)),
                    'p25': float(station_df['p_total'].quantile(0.25)),
                    'p50': float(station_df['p_total'].quantile(0.50)),
                    'p75': float(station_df['p_total'].quantile(0.75)),
                    'p95': float(station_df['p_total'].quantile(0.95))
                }
            }
        }
    
    # Aggregate metrics
    quality_metrics['aggregate'] = {
        'total_raw_records': len(df),
        'total_clean_records': len(df),
        'removal_rate': 0.0,
        'overall_completeness': float(np.mean([
            m['completeness_pct'] 
            for m in quality_metrics['by_station'].values()
        ])),
        'overall_voltage_quality': {
            'system_avg_voltage_pu': float(df['v_pu'].mean()),
            'system_min_voltage_pu': float(df['v_pu'].min()),
            'system_within_limits_pct': float((df['v_within_limits'] == True).mean() * 100)
        }
    }
    
    return quality_metrics

def calculate_temporal_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive temporal patterns."""
    print("\n3. Calculating temporal patterns...")
    
    temporal_patterns = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'by_station': {},
        'overall': {}
    }
    
    # Add temporal features if not present
    if 'hour' not in df.columns:
        df['hour'] = df['timestamp'].dt.hour
    if 'day_of_week' not in df.columns:
        df['day_of_week'] = df['timestamp'].dt.dayofweek
    if 'month' not in df.columns:
        df['month'] = df['timestamp'].dt.month
    
    for station in STATIONS:
        station_df = df[df['station'] == station]
        if len(station_df) == 0:
            continue
        
        # Hourly profile
        hourly_profile = {
            'p_total': {
                'mean': station_df.groupby('hour')['p_total'].mean().to_dict(),
                'max': station_df.groupby('hour')['p_total'].max().to_dict(),
                'min': station_df.groupby('hour')['p_total'].min().to_dict(),
                'std': station_df.groupby('hour')['p_total'].std().to_dict()
            },
            'v_pu': {
                'mean': station_df.groupby('hour')['v_pu'].mean().to_dict(),
                'min': station_df.groupby('hour')['v_pu'].min().to_dict()
            }
        }
        
        # Day of week patterns
        dow_patterns = {
            'p_total': station_df.groupby('day_of_week')['p_total'].mean().to_dict(),
            'v_pu': station_df.groupby('day_of_week')['v_pu'].mean().to_dict()
        }
        
        # Monthly patterns
        monthly_patterns = {
            'p_total': station_df.groupby('month')['p_total'].mean().to_dict(),
            'v_pu': station_df.groupby('month')['v_pu'].mean().to_dict()
        }
        
        # Peak analysis
        peak_hours = station_df[station_df['is_peak_hour'] == True]
        off_peak = station_df[station_df['is_peak_hour'] == False]
        
        peak_analysis = {
            'peak_hours': [18, 19, 20, 21, 22, 23],
            'avg_peak_demand': float(peak_hours['p_total'].mean()) if len(peak_hours) > 0 else 0,
            'avg_off_peak_demand': float(off_peak['p_total'].mean()) if len(off_peak) > 0 else 0,
            'peak_to_off_peak_ratio': float(peak_hours['p_total'].mean() / off_peak['p_total'].mean()) if len(off_peak) > 0 and off_peak['p_total'].mean() > 0 else 0
        }
        
        temporal_patterns['by_station'][station] = {
            'hourly_profile': hourly_profile,
            'day_of_week_patterns': dow_patterns,
            'monthly_patterns': monthly_patterns,
            'peak_analysis': peak_analysis,
            'weekend_reduction': float(
                1 - (station_df[station_df['is_weekend'] == True]['p_total'].mean() / 
                     station_df[station_df['is_weekend'] == False]['p_total'].mean())
            ) if len(station_df[station_df['is_weekend'] == False]) > 0 else 0
        }
    
    # Overall patterns
    temporal_patterns['overall'] = {
        'total_days': (df['timestamp'].max() - df['timestamp'].min()).days,
        'stations_processed': list(temporal_patterns['by_station'].keys()),
        'total_records': len(df),
        'system_peak_hour': int(df.groupby('hour')['p_total'].sum().idxmax()),
        'system_min_hour': int(df.groupby('hour')['p_total'].sum().idxmin())
    }
    
    return temporal_patterns

def calculate_correlation_matrices(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate correlation matrices between stations."""
    print("\n4. Calculating correlation matrices...")
    
    correlations = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'correlations': {}
    }
    
    # Prepare wide format data
    power_data = df.pivot_table(
        index='timestamp',
        columns='station',
        values='p_total',
        aggfunc='mean'
    )
    
    voltage_data = df.pivot_table(
        index='timestamp',
        columns='station',
        values='v_pu',
        aggfunc='mean'
    )
    
    # Power correlations
    if len(power_data.columns) > 1:
        power_corr = power_data.corr()
        correlations['correlations']['power_pearson'] = {
            'matrix': power_corr.to_dict(),
            'stations': power_corr.columns.tolist()
        }
    
    # Voltage correlations
    if len(voltage_data.columns) > 1:
        voltage_corr = voltage_data.corr()
        correlations['correlations']['voltage_pearson'] = {
            'matrix': voltage_corr.to_dict(),
            'stations': voltage_corr.columns.tolist()
        }
    
    # Lag analysis - simplified
    lag_analysis = {}
    for lag_minutes in [15, 30, 60]:
        lag_samples = lag_minutes // 15  # Convert to samples
        lag_corr = {}
        
        for col in power_data.columns:
            if col != 'Pilcaniyeu':  # Compare against upstream station
                correlation = power_data['Pilcaniyeu'].corr(
                    power_data[col].shift(-lag_samples)
                )
                lag_corr[f'Pilcaniyeu-{col}'] = float(correlation) if not pd.isna(correlation) else 0
        
        lag_analysis[f'lag_{lag_minutes}min'] = lag_corr
    
    correlations['correlations']['lag_analysis'] = {
        'description': 'Correlation of Pilcaniyeu with downstream stations at different lags',
        'lags_tested': lag_analysis,
        'best_lag_minutes': {
            pair: max(
                [(lag, corr[pair]) for lag, corr in lag_analysis.items() if pair in corr],
                key=lambda x: abs(x[1])
            )[0].replace('lag_', '').replace('min', '') if any(pair in corr for corr in lag_analysis.values()) else 0
            for pair in ['Pilcaniyeu-Jacobacci', 'Pilcaniyeu-Maquinchao', 'Pilcaniyeu-Los Menucos']
        }
    }
    
    return correlations

def calculate_hourly_voltage_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Detailed hourly voltage analysis."""
    print("\n5. Calculating hourly voltage analysis...")
    
    analysis = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'hourly_stats': {},
        'total_records': len(df)
    }
    
    for station in STATIONS:
        station_df = df[df['station'] == station]
        if len(station_df) == 0:
            continue
        
        hourly_stats = {}
        for hour in range(24):
            hour_data = station_df[station_df['hour'] == hour]['v_pu']
            if len(hour_data) > 0:
                hourly_stats[hour] = {
                    'mean': float(hour_data.mean()),
                    'std': float(hour_data.std()),
                    'min': float(hour_data.min()),
                    'max': float(hour_data.max()),
                    'p25': float(hour_data.quantile(0.25)),
                    'p50': float(hour_data.quantile(0.50)),
                    'p75': float(hour_data.quantile(0.75)),
                    'count': len(hour_data),
                    'violations': int((hour_data < 0.95).sum()),
                    'severe_violations': int((hour_data < 0.5).sum())
                }
        
        analysis['hourly_stats'][station] = hourly_stats
    
    return analysis

def calculate_demand_voltage_correlation(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate demand-voltage correlation and sensitivity."""
    print("\n6. Calculating demand-voltage correlation...")
    
    pv_correlation = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'correlations': {}
    }
    
    for station in STATIONS:
        station_df = df[df['station'] == station]
        if len(station_df) < 100:  # Need sufficient data
            continue
        
        # Overall correlation
        overall_corr = station_df['p_total'].corr(station_df['v_pu'])
        
        # Correlation by time period
        morning = station_df[(station_df['hour'] >= 6) & (station_df['hour'] < 12)]
        afternoon = station_df[(station_df['hour'] >= 12) & (station_df['hour'] < 18)]
        evening = station_df[(station_df['hour'] >= 18) & (station_df['hour'] < 22)]
        night = station_df[(station_df['hour'] >= 22) | (station_df['hour'] < 6)]
        
        # Linear regression for sensitivity
        from sklearn.linear_model import LinearRegression
        lr = LinearRegression()
        X = station_df[['p_total']].fillna(station_df['p_total'].mean())
        y = station_df['v_pu'].fillna(station_df['v_pu'].mean())
        lr.fit(X, y)
        sensitivity = lr.coef_[0]  # dV/dP
        
        # Demand at different voltage levels
        low_v_mask = station_df['v_pu'] < 0.5
        mid_v_mask = (station_df['v_pu'] >= 0.5) & (station_df['v_pu'] < 0.6)
        normal_v_mask = station_df['v_pu'] >= 0.6
        
        pv_correlation['correlations'][station] = {
            'overall': float(overall_corr) if not pd.isna(overall_corr) else 0,
            'morning': float(morning['p_total'].corr(morning['v_pu'])) if len(morning) > 10 else 0,
            'afternoon': float(afternoon['p_total'].corr(afternoon['v_pu'])) if len(afternoon) > 10 else 0,
            'evening': float(evening['p_total'].corr(evening['v_pu'])) if len(evening) > 10 else 0,
            'night': float(night['p_total'].corr(night['v_pu'])) if len(night) > 10 else 0,
            'sensitivity_dv_dp': float(sensitivity),
            'r_squared': float(lr.score(X, y)),
            'demand_at_low_v': {
                'v_below_0.5': float(station_df[low_v_mask]['p_total'].mean()) if low_v_mask.any() else 0,
                'v_below_0.6': float(station_df[mid_v_mask]['p_total'].mean()) if mid_v_mask.any() else 0,
                'v_above_0.6': float(station_df[normal_v_mask]['p_total'].mean()) if normal_v_mask.any() else 0
            }
        }
    
    return pv_correlation

def calculate_critical_events_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze critical voltage events."""
    print("\n7. Calculating critical events analysis...")
    
    critical_events = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'critical_events': {}
    }
    
    for station in STATIONS:
        station_df = df[df['station'] == station].copy()
        if len(station_df) == 0:
            continue
        
        # Sort by timestamp
        station_df = station_df.sort_values('timestamp')
        
        # Find events below 0.5 pu
        low_v_mask = station_df['v_pu'] < 0.5
        
        # Group consecutive low voltage periods
        station_df['event_group'] = (low_v_mask != low_v_mask.shift()).cumsum()
        
        events_05 = []
        for group_id, group in station_df[low_v_mask].groupby('event_group'):
            if len(group) >= 1:  # At least 15 minutes
                event = {
                    'start': group['timestamp'].min().isoformat(),
                    'end': group['timestamp'].max().isoformat(),
                    'duration_minutes': float((group['timestamp'].max() - group['timestamp'].min()).total_seconds() / 60),
                    'min_voltage': float(group['v_pu'].min()),
                    'avg_voltage': float(group['v_pu'].mean()),
                    'avg_demand': float(group['p_total'].mean()),
                    'max_demand': float(group['p_total'].max())
                }
                events_05.append(event)
        
        # Sort by duration
        events_05.sort(key=lambda x: x['duration_minutes'], reverse=True)
        
        # Events below 0.3 pu
        very_low_mask = station_df['v_pu'] < 0.3
        events_03_count = (very_low_mask != very_low_mask.shift()).cumsum()[very_low_mask].nunique()
        
        # Worst 100 events
        worst_events = station_df.nsmallest(100, 'v_pu')
        
        critical_events['critical_events'][station] = {
            'events_below_0.5pu': {
                'count': len(events_05),
                'total_duration_hours': float(sum(e['duration_minutes'] for e in events_05) / 60),
                'max_duration_hours': float(max([e['duration_minutes'] for e in events_05]) / 60) if events_05 else 0,
                'avg_duration_hours': float(np.mean([e['duration_minutes'] for e in events_05]) / 60) if events_05 else 0,
                'events': events_05[:10]  # Top 10 longest
            },
            'events_below_0.3pu': {
                'count': int(events_03_count),
                'total_minutes': float(very_low_mask.sum() * 15)
            },
            'worst_100_events': {
                'min_voltage': float(worst_events['v_pu'].min()),
                'avg_voltage': float(worst_events['v_pu'].mean()),
                'hour_distribution': worst_events['hour'].value_counts().to_dict()
            }
        }
    
    return critical_events

def calculate_demand_ramps_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze demand ramps."""
    print("\n8. Calculating demand ramps analysis...")
    
    ramps_analysis = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'ramp_analysis': {}
    }
    
    for station in STATIONS:
        station_df = df[df['station'] == station].copy()
        if len(station_df) < 10:
            continue
        
        # Sort by timestamp
        station_df = station_df.sort_values('timestamp')
        
        # Calculate ramps (MW/hour)
        station_df['ramp'] = station_df['p_total'].diff() * 4  # 15-min intervals to hourly
        
        # Remove NaN and extreme outliers
        ramps = station_df['ramp'].dropna()
        ramps = ramps[np.abs(ramps) < ramps.std() * 5]
        
        # Ramps by hour
        hourly_ramps = {}
        for hour in range(24):
            hour_ramps = station_df[station_df['hour'] == hour]['ramp'].dropna()
            if len(hour_ramps) > 0:
                hourly_ramps[hour] = {
                    'mean': float(hour_ramps.mean()),
                    'max_up': float(hour_ramps.max()),
                    'max_down': float(hour_ramps.min()),
                    'std': float(hour_ramps.std()),
                    'p95_up': float(hour_ramps.quantile(0.95)),
                    'p95_down': float(hour_ramps.quantile(0.05))
                }
        
        # Critical periods
        morning_ramps = station_df[(station_df['hour'] >= 6) & (station_df['hour'] <= 9)]['ramp'].dropna()
        evening_ramps = station_df[(station_df['hour'] >= 18) & (station_df['hour'] <= 21)]['ramp'].dropna()
        
        ramps_analysis['ramp_analysis'][station] = {
            'overall_stats': {
                'max_ramp_up': float(ramps.max()) if len(ramps) > 0 else 0,
                'max_ramp_down': float(ramps.min()) if len(ramps) > 0 else 0,
                'avg_ramp_magnitude': float(ramps.abs().mean()) if len(ramps) > 0 else 0,
                'p95_ramp_up': float(ramps.quantile(0.95)) if len(ramps) > 0 else 0,
                'p95_ramp_down': float(ramps.quantile(0.05)) if len(ramps) > 0 else 0
            },
            'hourly_ramps': hourly_ramps,
            'critical_periods': {
                'morning_6_9h': {
                    'max_ramp_up': float(morning_ramps.max()) if len(morning_ramps) > 0 else 0,
                    'avg_ramp': float(morning_ramps.mean()) if len(morning_ramps) > 0 else 0
                },
                'evening_18_21h': {
                    'max_ramp_up': float(evening_ramps.max()) if len(evening_ramps) > 0 else 0,
                    'avg_ramp': float(evening_ramps.mean()) if len(evening_ramps) > 0 else 0
                }
            }
        }
    
    return ramps_analysis

def calculate_load_duration_curves(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate load duration curves."""
    print("\n9. Calculating load duration curves...")
    
    duration_curves = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'duration_curves': {}
    }
    
    percentages = list(range(0, 101, 5))  # 0%, 5%, 10%, ..., 100%
    
    for station in STATIONS:
        station_df = df[df['station'] == station]
        if len(station_df) == 0:
            continue
        
        # Sort demand and voltage
        sorted_demand = station_df['p_total'].sort_values(ascending=False).reset_index(drop=True)
        sorted_voltage = station_df['v_pu'].sort_values(ascending=False).reset_index(drop=True)
        
        # Calculate percentiles
        demand_percentiles = []
        voltage_percentiles = []
        
        for pct in percentages:
            idx = int(len(sorted_demand) * pct / 100)
            idx = min(idx, len(sorted_demand) - 1)
            demand_percentiles.append(float(sorted_demand.iloc[idx]))
            voltage_percentiles.append(float(sorted_voltage.iloc[idx]))
        
        # Calculate statistics
        hours_above_80pct_peak = (station_df['p_total'] > station_df['p_total'].max() * 0.8).sum() * 0.25
        hours_below_05pu = (station_df['v_pu'] < 0.5).sum() * 0.25
        hours_below_06pu = (station_df['v_pu'] < 0.6).sum() * 0.25
        
        # Energy below limit (approximate)
        below_limit_mask = station_df['v_pu'] < 0.95
        energy_below_limit = (station_df[below_limit_mask]['p_total'] * 0.25).sum()  # MWh
        
        duration_curves['duration_curves'][station] = {
            'demand_curve': {
                'percentages': percentages,
                'values': demand_percentiles
            },
            'voltage_curve': {
                'percentages': percentages,
                'values': voltage_percentiles
            },
            'statistics': {
                'hours_above_80pct_peak': float(hours_above_80pct_peak),
                'hours_below_0.5pu': float(hours_below_05pu),
                'hours_below_0.6pu': float(hours_below_06pu),
                'energy_below_limit_mwh': float(energy_below_limit),
                'capacity_factor': float(station_df['p_total'].mean() / station_df['p_total'].max()) if station_df['p_total'].max() > 0 else 0
            }
        }
    
    return duration_curves

def calculate_typical_days_profiles(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate typical day profiles."""
    print("\n10. Calculating typical days profiles...")
    
    typical_days = {
        'available': True,
        'generated_at': datetime.now().isoformat(),
        'typical_days': {}
    }
    
    for station in STATIONS:
        station_df = df[df['station'] == station].copy()
        if len(station_df) == 0:
            continue
        
        # Add date column
        station_df['date'] = station_df['timestamp'].dt.date
        
        # Find days with max/min demand
        daily_stats = station_df.groupby('date').agg({
            'p_total': ['mean', 'max'],
            'v_pu': ['mean', 'min']
        })
        
        # Max demand day
        max_demand_date = daily_stats[('p_total', 'max')].idxmax()
        max_demand_day_df = station_df[station_df['date'] == max_demand_date]
        
        # Min demand day
        min_demand_date = daily_stats[('p_total', 'mean')].idxmin()
        min_demand_day_df = station_df[station_df['date'] == min_demand_date]
        
        # Worst voltage day
        worst_voltage_date = daily_stats[('v_pu', 'min')].idxmin()
        worst_voltage_day_df = station_df[station_df['date'] == worst_voltage_date]
        
        # Average profiles
        avg_hourly_demand = station_df.groupby('hour')['p_total'].agg(['mean', 'std'])
        avg_hourly_voltage = station_df.groupby('hour')['v_pu'].agg(['mean', 'std'])
        
        typical_days['typical_days'][station] = {
            'max_demand_day': {
                'date': str(max_demand_date),
                'peak_demand': float(max_demand_day_df['p_total'].max()),
                'avg_demand': float(max_demand_day_df['p_total'].mean()),
                'min_voltage': float(max_demand_day_df['v_pu'].min()),
                'hourly_demand': max_demand_day_df.groupby('hour')['p_total'].mean().to_dict(),
                'hourly_voltage': max_demand_day_df.groupby('hour')['v_pu'].mean().to_dict()
            },
            'min_demand_day': {
                'date': str(min_demand_date),
                'peak_demand': float(min_demand_day_df['p_total'].max()),
                'avg_demand': float(min_demand_day_df['p_total'].mean()),
                'avg_voltage': float(min_demand_day_df['v_pu'].mean()),
                'hourly_demand': min_demand_day_df.groupby('hour')['p_total'].mean().to_dict(),
                'hourly_voltage': min_demand_day_df.groupby('hour')['v_pu'].mean().to_dict()
            },
            'worst_voltage_day': {
                'date': str(worst_voltage_date),
                'min_voltage': float(worst_voltage_day_df['v_pu'].min()),
                'avg_voltage': float(worst_voltage_day_df['v_pu'].mean()),
                'avg_demand': float(worst_voltage_day_df['p_total'].mean()),
                'hourly_demand': worst_voltage_day_df.groupby('hour')['p_total'].mean().to_dict(),
                'hourly_voltage': worst_voltage_day_df.groupby('hour')['v_pu'].mean().to_dict()
            },
            'average_day': {
                'hourly_demand_mean': avg_hourly_demand['mean'].to_dict(),
                'hourly_demand_std': avg_hourly_demand['std'].to_dict(),
                'hourly_voltage_mean': avg_hourly_voltage['mean'].to_dict(),
                'hourly_voltage_std': avg_hourly_voltage['std'].to_dict()
            }
        }
    
    return typical_days

def prepare_ml_features(df: pd.DataFrame) -> None:
    """Prepare features for machine learning."""
    print("\n11. Preparing ML features...")
    
    for station in STATIONS:
        print(f"  Processing {station}...")
        station_df = df[df['station'] == station].copy()
        if len(station_df) < 100:
            continue
        
        # Sort by timestamp
        station_df = station_df.sort_values('timestamp').reset_index(drop=True)
        
        # Basic features
        features = station_df[['timestamp', 'v_pu', 'p_total', 'q_total', 'fp']].copy()
        
        # Temporal features
        features['hour'] = station_df['hour']
        features['day_of_week'] = station_df['day_of_week']
        features['month'] = station_df['timestamp'].dt.month
        features['is_weekend'] = station_df['is_weekend'].astype(int)
        features['is_peak_hour'] = station_df['is_peak_hour'].astype(int)
        
        # Cyclical encoding
        features['hour_sin'] = np.sin(2 * np.pi * features['hour'] / 24)
        features['hour_cos'] = np.cos(2 * np.pi * features['hour'] / 24)
        features['dow_sin'] = np.sin(2 * np.pi * features['day_of_week'] / 7)
        features['dow_cos'] = np.cos(2 * np.pi * features['day_of_week'] / 7)
        features['month_sin'] = np.sin(2 * np.pi * features['month'] / 12)
        features['month_cos'] = np.cos(2 * np.pi * features['month'] / 12)
        
        # Rolling statistics (15min, 1h, 24h)
        for window, samples in [(4, 1), (4, 4), (96, 24)]:  # 15min=1, 1h=4, 24h=96 samples
            features[f'v_rolling_mean_{samples}h'] = features['v_pu'].rolling(window, min_periods=1).mean()
            features[f'v_rolling_std_{samples}h'] = features['v_pu'].rolling(window, min_periods=1).std()
            features[f'p_rolling_mean_{samples}h'] = features['p_total'].rolling(window, min_periods=1).mean()
            features[f'p_rolling_std_{samples}h'] = features['p_total'].rolling(window, min_periods=1).std()
        
        # Lagged features
        for lag in [1, 4, 8]:  # 15min, 1h, 2h
            features[f'v_lag_{lag}'] = features['v_pu'].shift(lag)
            features[f'p_lag_{lag}'] = features['p_total'].shift(lag)
        
        # Rate of change
        features['v_rate_change'] = features['v_pu'].diff()
        features['p_rate_change'] = features['p_total'].diff()
        
        # Station-specific features
        features['distance_km'] = DISTANCES[station]
        features['nominal_load_mw'] = NOMINAL_LOADS[station]
        features['load_factor'] = features['p_total'] / features['p_total'].max() if features['p_total'].max() > 0 else 0
        
        # Fill NaN values
        features = features.fillna(method='ffill').fillna(0)
        
        # Save to parquet
        output_file = ml_features_dir / f"{station.lower()}_features.parquet"
        features.to_parquet(output_file, index=False)
        print(f"    Saved {len(features)} records to {output_file}")
    
    # Save feature scaler
    print("  Fitting StandardScaler...")
    all_features = []
    numeric_cols = ['v_pu', 'p_total', 'q_total', 'fp', 'hour', 'day_of_week', 'month',
                   'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'month_sin', 'month_cos']
    
    for station in STATIONS:
        file_path = ml_features_dir / f"{station.lower()}_features.parquet"
        if file_path.exists():
            station_features = pd.read_parquet(file_path)
            all_features.append(station_features[numeric_cols])
    
    if all_features:
        combined = pd.concat(all_features)
        scaler = StandardScaler()
        scaler.fit(combined)
        
        # Save scaler
        with open(ml_features_dir / 'feature_scaler.pkl', 'wb') as f:
            pickle.dump(scaler, f)
        print("  Saved feature scaler")

def save_results(results: Dict[str, Any]) -> None:
    """Save all results to JSON files."""
    print("\n12. Saving results...")
    
    files_to_save = {
        'summary.json': results['summary'],
        'quality_metrics_enhanced.json': results['quality_metrics'],
        'temporal_patterns_full.json': results['temporal_patterns'],
        'correlations.json': results['correlations'],
        'hourly_analysis.json': results['hourly_analysis'],
        'pv_correlation.json': results['pv_correlation'],
        'critical_events.json': results['critical_events'],
        'demand_ramps.json': results['demand_ramps'],
        'duration_curves.json': results['duration_curves'],
        'typical_days.json': results['typical_days']
    }
    
    for filename, data in files_to_save.items():
        output_file = output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved {filename}")

def main():
    """Main processing function."""
    print("="*80)
    print("COMPREHENSIVE DATA PROCESSING FOR ELECTRICAL GRID ANALYSIS")
    print("="*80)
    
    # Load data
    df = load_data()
    
    # Calculate all metrics
    results = {
        'summary': calculate_processed_data_summary(df),
        'quality_metrics': calculate_data_quality_metrics(df),
        'temporal_patterns': calculate_temporal_patterns(df),
        'correlations': calculate_correlation_matrices(df),
        'hourly_analysis': calculate_hourly_voltage_analysis(df),
        'pv_correlation': calculate_demand_voltage_correlation(df),
        'critical_events': calculate_critical_events_analysis(df),
        'demand_ramps': calculate_demand_ramps_analysis(df),
        'duration_curves': calculate_load_duration_curves(df),
        'typical_days': calculate_typical_days_profiles(df)
    }
    
    # Prepare ML features
    prepare_ml_features(df)
    
    # Save results
    save_results(results)
    
    print("\n" + "="*80)
    print("Processing completed successfully!")
    print(f"Results saved to: {output_dir}")
    print("="*80)

if __name__ == "__main__":
    main()