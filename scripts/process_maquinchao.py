#!/usr/bin/env python3
"""
Process Maquinchao station data
Located at 210 km from source
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root
project_root = Path(__file__).parent.parent


def process_epre_file(file_path):
    """Process a single EPRE Excel file with the correct format."""
    logger.info(f"Processing: {file_path.name}")
    
    try:
        # Read with header at row 2 (0-indexed)
        df = pd.read_excel(file_path, header=2)
        
        # The first column contains datetime as string like "2024010100:00"
        # Rename columns to standard names
        df.columns = ['datetime_str', 'p', 'q', 'v1', 'v2', 'v3', 'i1', 'i2', 'i3']
        
        # Parse the datetime string
        # Format is YYYYMMDDHH:MM
        df['timestamp'] = pd.to_datetime(
            df['datetime_str'].astype(str),
            format='%Y%m%d%H:%M',
            errors='coerce'
        )
        
        # Drop rows where timestamp parsing failed
        df = df[df['timestamp'].notna()]
        
        # Convert numeric columns
        numeric_cols = ['p', 'q', 'v1', 'v2', 'v3', 'i1', 'i2', 'i3']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate additional metrics
        df['v_avg'] = df[['v1', 'v2', 'v3']].mean(axis=1)
        df['v_min'] = df[['v1', 'v2', 'v3']].min(axis=1)
        df['v_max'] = df[['v1', 'v2', 'v3']].max(axis=1)
        
        # Convert to MW (assuming P is in kW)
        df['p_total'] = df['p'] / 1000  # kW to MW
        df['q_total'] = df['q'] / 1000  # kVAr to MVAr
        
        # Calculate power factor
        df['s_total'] = np.sqrt(df['p_total']**2 + df['q_total']**2)
        df['fp'] = np.where(df['s_total'] > 0, np.abs(df['p_total']) / df['s_total'], 0)
        
        # Add metadata
        df['station'] = 'Maquinchao'
        df['voltage_level'] = '33kV'
        
        # Add per-unit voltage (assuming 33kV system)
        v_nominal = 33000
        df['v_pu'] = df['v_avg'] / v_nominal
        
        # Quality metrics
        df['v_within_limits'] = (df['v_pu'] >= 0.95) & (df['v_pu'] <= 1.05)
        
        # Time features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6])
        df['is_peak_hour'] = df['hour'].between(18, 23)
        
        # Clean up
        df = df.drop(columns=['datetime_str'])
        
        logger.info(f"  Processed {len(df)} valid records")
        logger.info(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        logger.info(f"  V avg: {df['v_avg'].mean():.0f} V ({df['v_pu'].mean():.3f} pu)")
        logger.info(f"  P avg: {df['p_total'].mean():.2f} MW")
        
        return df
        
    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {e}")
        return pd.DataFrame()


def main():
    """Process Maquinchao data files."""
    logger.info("="*60)
    logger.info("PROCESAMIENTO MAQUINCHAO (210 km)")
    logger.info("="*60)
    
    # Find Maquinchao files
    base_path = project_root / "data" / "Registros Línea Sur"
    maquinchao_files = []
    
    for year_folder in base_path.glob("Maquinchao*"):
        if year_folder.is_dir():
            for month_folder in year_folder.glob("*"):
                if month_folder.is_dir():
                    maquinchao_files.extend(month_folder.glob("ET2MA*.xls*"))
    
    logger.info(f"Archivos encontrados: {len(maquinchao_files)}")
    
    if not maquinchao_files:
        logger.error("No se encontraron archivos")
        return 1
    
    # Process all files
    all_data = []
    
    for file_path in sorted(maquinchao_files):
        df = process_epre_file(file_path)
        if not df.empty:
            all_data.append(df)
    
    if not all_data:
        logger.error("No se pudo procesar ningún archivo")
        return 1
    
    # Combine all data
    logger.info(f"\nCombinando {len(all_data)} archivos...")
    new_data = pd.concat(all_data, ignore_index=True)
    new_data = new_data.sort_values('timestamp')
    
    # Load existing data and append
    processed_dir = project_root / "data" / "processed"
    consolidated_file = processed_dir / "consolidated_data.csv"
    
    if consolidated_file.exists():
        logger.info("Agregando a datos existentes...")
        existing_data = pd.read_csv(consolidated_file, parse_dates=['timestamp'])
        # Remove old Maquinchao data if exists
        existing_data = existing_data[existing_data['station'] != 'Maquinchao']
        # Combine
        consolidated = pd.concat([existing_data, new_data], ignore_index=True)
        consolidated = consolidated.sort_values(['station', 'timestamp'])
    else:
        consolidated = new_data
    
    # Save consolidated data
    consolidated.to_csv(consolidated_file, index=False)
    logger.info(f"Datos guardados: {consolidated_file}")
    
    # Update quality metrics
    quality_file = processed_dir / "quality_metrics.json"
    if quality_file.exists():
        with open(quality_file, 'r') as f:
            quality_metrics = json.load(f)
    else:
        quality_metrics = {}
    
    # Calculate Maquinchao metrics
    maquinchao_data = new_data
    quality_metrics['Maquinchao'] = {
        'total_raw_records': len(maquinchao_data),
        'total_clean_records': len(maquinchao_data),
        'records_removed': 0,
        'removal_percentage': 0,
        'date_range': {
            'start': str(maquinchao_data['timestamp'].min()),
            'end': str(maquinchao_data['timestamp'].max())
        },
        'voltage_quality': {
            'within_limits_pct': maquinchao_data['v_within_limits'].mean() * 100,
            'avg_voltage_pu': maquinchao_data['v_pu'].mean(),
            'min_voltage_pu': maquinchao_data['v_pu'].min(),
            'max_voltage_pu': maquinchao_data['v_pu'].max()
        },
        'power_stats': {
            'avg_power_mw': maquinchao_data['p_total'].mean(),
            'max_power_mw': maquinchao_data['p_total'].max(),
            'avg_power_factor': maquinchao_data['fp'].mean()
        }
    }
    
    with open(quality_file, 'w') as f:
        json.dump(quality_metrics, f, indent=2, default=str)
    
    # Update temporal analysis
    temporal_file = processed_dir / "temporal_analysis.json"
    if temporal_file.exists():
        with open(temporal_file, 'r') as f:
            temporal_analysis = json.load(f)
    else:
        temporal_analysis = {'overall': {}, 'by_station': {}}
    
    # Update overall stats
    temporal_analysis['overall']['stations_processed'] = list(consolidated['station'].unique())
    temporal_analysis['overall']['total_records'] = len(consolidated)
    
    # Maquinchao temporal analysis
    hourly = maquinchao_data.groupby('hour')['p_total'].agg(['mean', 'max']).round(3)
    
    temporal_analysis['by_station']['Maquinchao'] = {
        'hourly_profile': {
            'p_total': {
                'mean': {str(h): float(hourly.loc[h, 'mean']) if h in hourly.index else 0 for h in range(24)},
                'max': {str(h): float(hourly.loc[h, 'max']) if h in hourly.index else 0 for h in range(24)}
            }
        },
        'peak_analysis': {
            'avg_peak_demand': maquinchao_data[maquinchao_data['is_peak_hour']]['p_total'].mean(),
            'max_peak_demand': maquinchao_data[maquinchao_data['is_peak_hour']]['p_total'].max()
        }
    }
    
    with open(temporal_file, 'w') as f:
        json.dump(temporal_analysis, f, indent=2, default=str)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DEL PROCESAMIENTO - MAQUINCHAO")
    logger.info("="*60)
    logger.info(f"Archivos procesados: {len(all_data)}")
    logger.info(f"Total registros Maquinchao: {len(maquinchao_data):,}")
    logger.info(f"Período: {maquinchao_data['timestamp'].min()} a {maquinchao_data['timestamp'].max()}")
    logger.info(f"Tensión promedio: {maquinchao_data['v_avg'].mean():.0f} V ({maquinchao_data['v_pu'].mean():.3f} pu)")
    logger.info(f"Potencia promedio: {maquinchao_data['p_total'].mean():.2f} MW")
    logger.info(f"Potencia máxima: {maquinchao_data['p_total'].max():.2f} MW")
    logger.info(f"Factor de potencia promedio: {maquinchao_data['fp'].mean():.3f}")
    logger.info(f"% tiempo dentro de límites: {maquinchao_data['v_within_limits'].mean()*100:.1f}%")
    
    # Show complete voltage drop progression
    logger.info("\n" + "="*60)
    logger.info("PROGRESIÓN COMPLETA DE CAÍDA DE TENSIÓN")
    logger.info("="*60)
    
    # Load all quality metrics to show progression
    with open(quality_file, 'r') as f:
        all_metrics = json.load(f)
    
    stations_order = ['Pilcaniyeu', 'Jacobacci', 'Maquinchao', 'Los Menucos']
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
    
    logger.info("Estación      Dist(km)  V(pu)   Caída%  P(MW)  P_nom(MW)  Utiliz%")
    logger.info("-" * 70)
    
    for station in stations_order:
        if station in all_metrics:
            metrics = all_metrics[station]
            v_pu = metrics['voltage_quality']['avg_voltage_pu']
            p_avg = metrics['power_stats']['avg_power_mw']
            p_max = metrics['power_stats']['max_power_mw']
            dist = distances.get(station, 0)
            p_nom = nominal_loads.get(station, 0)
            utiliz = (p_avg / p_nom * 100) if p_nom > 0 else 0
            
            logger.info(f"{station:12} {dist:8} {v_pu:7.3f} {(1-v_pu)*100:6.0f}% {p_avg:6.2f} {p_nom:9.2f} {utiliz:7.0f}%")
    
    # Total system stats
    logger.info("\n" + "="*60)
    logger.info("ESTADÍSTICAS TOTALES DEL SISTEMA")
    logger.info("="*60)
    total_records = len(consolidated)
    total_nominal = sum(nominal_loads.values())
    total_actual = sum(all_metrics[s]['power_stats']['avg_power_mw'] for s in all_metrics if s != 'Pilcaniyeu')
    
    logger.info(f"Total registros procesados: {total_records:,}")
    logger.info(f"Capacidad nominal total: {total_nominal:.2f} MW")
    logger.info(f"Demanda actual total: {total_actual:.2f} MW")
    logger.info(f"Utilización del sistema: {total_actual/total_nominal*100:.0f}%")
    
    logger.info("\n✓ Procesamiento completado exitosamente")
    logger.info("✓ Sistema completo analizado - 4 estaciones principales")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())