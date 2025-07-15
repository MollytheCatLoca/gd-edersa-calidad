import pandas as pd
import numpy as np
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_csv_data(file_path):
    """Load CSV measurement data from EPRE format"""
    try:
        # Skip header rows and read data
        df = pd.read_csv(file_path, skiprows=5, encoding='latin-1', sep=';')
        
        # Clean column names
        df.columns = ['P_activa_kW', 'Q_reactiva_kVAr', 'V1_V', 'V2_V', 'V3_V', 
                     'I1_A', 'I2_A', 'I3_A', 'Fecha', 'Descripcion']
        
        # Remove empty description column
        df = df.drop('Descripcion', axis=1)
        
        # Convert to datetime
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y %H:%M:%S')
        
        # Convert voltage from V to kV
        df['V1_kV'] = df['V1_V'] / 1000
        df['V2_kV'] = df['V2_V'] / 1000
        df['V3_kV'] = df['V3_V'] / 1000
        df['V_avg_kV'] = (df['V1_kV'] + df['V2_kV'] + df['V3_kV']) / 3
        
        # Convert power from kW to MW
        df['P_activa_MW'] = df['P_activa_kW'] / 1000
        df['Q_reactiva_MVAr'] = df['Q_reactiva_kVAr'] / 1000
        
        # Calculate apparent power
        df['S_aparente_MVA'] = np.sqrt(df['P_activa_MW']**2 + df['Q_reactiva_MVAr']**2)
        
        # Calculate power factor
        df['FP'] = df['P_activa_MW'] / df['S_aparente_MVA']
        
        # Average current
        df['I_avg_A'] = (df['I1_A'] + df['I2_A'] + df['I3_A']) / 3
        
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def analyze_voltage_profile(df, station_name, nominal_voltage=33):
    """Analyze voltage profile and calculate deviations"""
    results = {
        'station': station_name,
        'v_min_kV': df['V_avg_kV'].min(),
        'v_max_kV': df['V_avg_kV'].max(),
        'v_mean_kV': df['V_avg_kV'].mean(),
        'v_std_kV': df['V_avg_kV'].std(),
        'v_min_pu': df['V_avg_kV'].min() / nominal_voltage,
        'v_max_pu': df['V_avg_kV'].max() / nominal_voltage,
        'v_mean_pu': df['V_avg_kV'].mean() / nominal_voltage,
        'hours_below_0.95pu': (df['V_avg_kV'] < 0.95 * nominal_voltage).sum() * 0.25,
        'hours_below_0.90pu': (df['V_avg_kV'] < 0.90 * nominal_voltage).sum() * 0.25,
    }
    return results

def analyze_demand_profile(df, station_name):
    """Analyze demand patterns"""
    results = {
        'station': station_name,
        'p_max_MW': df['P_activa_MW'].max(),
        'p_min_MW': df['P_activa_MW'].min(),
        'p_mean_MW': df['P_activa_MW'].mean(),
        'q_max_MVAr': df['Q_reactiva_MVAr'].max(),
        'q_min_MVAr': df['Q_reactiva_MVAr'].min(),
        'q_mean_MVAr': df['Q_reactiva_MVAr'].mean(),
        'fp_min': df['FP'].min(),
        'fp_mean': df['FP'].mean(),
    }
    
    # Add hourly profile
    df['hour'] = df['Fecha'].dt.hour
    hourly_profile = df.groupby('hour')['P_activa_MW'].mean()
    results['hourly_profile'] = hourly_profile.to_dict()
    
    return results

def process_all_stations():
    """Process all available station data"""
    base_path = Path('/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/Registros Línea Sur')
    
    # Define stations and their files
    stations = {
        'Pilcaniyeu_33kV': base_path / 'Pilcaniyeu2024/1121/ET4PI_33.csv',
        'Pilcaniyeu_13kV': base_path / 'Pilcaniyeu2024/1121/ET4PI_13.csv',
    }
    
    voltage_results = []
    demand_results = []
    
    for station_name, file_path in stations.items():
        if file_path.exists():
            print(f"\nProcessing {station_name}...")
            df = load_csv_data(file_path)
            if df is not None:
                # Determine nominal voltage
                nominal_v = 33 if '33' in station_name else 13.2
                
                # Analyze voltage
                v_results = analyze_voltage_profile(df, station_name, nominal_v)
                voltage_results.append(v_results)
                
                # Analyze demand
                d_results = analyze_demand_profile(df, station_name)
                demand_results.append(d_results)
                
                # Create visualizations
                create_station_plots(df, station_name)
    
    return pd.DataFrame(voltage_results), pd.DataFrame(demand_results)

def create_station_plots(df, station_name):
    """Create analysis plots for a station"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f'Analysis: {station_name}', fontsize=16)
    
    # Plot 1: Voltage profile over time
    axes[0, 0].plot(df['Fecha'], df['V_avg_kV'], 'b-', alpha=0.7)
    axes[0, 0].axhline(y=33*0.95, color='r', linestyle='--', label='95% Nominal')
    axes[0, 0].axhline(y=33*0.90, color='r', linestyle=':', label='90% Nominal')
    axes[0, 0].set_ylabel('Voltage (kV)')
    axes[0, 0].set_title('Voltage Profile')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Power demand over time
    axes[0, 1].plot(df['Fecha'], df['P_activa_MW'], 'g-', label='Active Power')
    axes[0, 1].plot(df['Fecha'], df['Q_reactiva_MVAr'], 'r-', label='Reactive Power')
    axes[0, 1].set_ylabel('Power (MW/MVAr)')
    axes[0, 1].set_title('Power Demand')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Hourly demand profile
    hourly_avg = df.groupby(df['Fecha'].dt.hour)['P_activa_MW'].mean()
    axes[1, 0].bar(hourly_avg.index, hourly_avg.values, color='skyblue')
    axes[1, 0].set_xlabel('Hour of Day')
    axes[1, 0].set_ylabel('Average Power (MW)')
    axes[1, 0].set_title('Daily Load Profile')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Power factor
    axes[1, 1].plot(df['Fecha'], df['FP'], 'purple', alpha=0.7)
    axes[1, 1].axhline(y=0.95, color='g', linestyle='--', label='Target PF')
    axes[1, 1].set_ylabel('Power Factor')
    axes[1, 1].set_title('Power Factor Profile')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_ylim([0.8, 1.0])
    
    plt.tight_layout()
    plt.savefig(f'analysis_{station_name}.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    # Process all stations
    voltage_df, demand_df = process_all_stations()
    
    # Display results
    print("\n=== VOLTAGE ANALYSIS RESULTS ===")
    print(voltage_df.to_string())
    
    print("\n=== DEMAND ANALYSIS RESULTS ===")
    print(demand_df.to_string())
    
    # Save results
    voltage_df.to_csv('voltage_analysis_results.csv', index=False)
    demand_df.to_csv('demand_analysis_results.csv', index=False)