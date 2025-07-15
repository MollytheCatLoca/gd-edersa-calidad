#!/usr/bin/env python3
"""
Process Los Menucos station data
The end of the line - 270 km from source
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
        df['station'] = 'Los Menucos'
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
    """Process Los Menucos data files."""
    logger.info("="*60)
    logger.info("PROCESAMIENTO LOS MENUCOS - FINAL DE LÍNEA (270 km)")
    logger.info("="*60)
    
    # Find Los Menucos files
    base_path = project_root / "data" / "Registros Línea Sur"
    menucos_files = []
    
    # Look for both "Menucos" and "Los Menucos" folders
    for year_folder in base_path.glob("*enucos*"):
        if year_folder.is_dir():
            for month_folder in year_folder.glob("*"):
                if month_folder.is_dir():
                    menucos_files.extend(month_folder.glob("ET2LM*.xls*"))
    
    logger.info(f"Archivos encontrados: {len(menucos_files)}")
    
    if not menucos_files:
        logger.error("No se encontraron archivos")
        return 1
    
    # Process all files
    all_data = []
    
    for file_path in sorted(menucos_files):
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
        # Remove old Los Menucos data if exists
        existing_data = existing_data[existing_data['station'] != 'Los Menucos']
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
    
    # Calculate Los Menucos metrics
    menucos_data = new_data
    quality_metrics['Los Menucos'] = {
        'total_raw_records': len(menucos_data),
        'total_clean_records': len(menucos_data),
        'records_removed': 0,
        'removal_percentage': 0,
        'date_range': {
            'start': str(menucos_data['timestamp'].min()),
            'end': str(menucos_data['timestamp'].max())
        },
        'voltage_quality': {
            'within_limits_pct': menucos_data['v_within_limits'].mean() * 100,
            'avg_voltage_pu': menucos_data['v_pu'].mean(),
            'min_voltage_pu': menucos_data['v_pu'].min(),
            'max_voltage_pu': menucos_data['v_pu'].max()
        },
        'power_stats': {
            'avg_power_mw': menucos_data['p_total'].mean(),
            'max_power_mw': menucos_data['p_total'].max(),
            'avg_power_factor': menucos_data['fp'].mean()
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
    
    # Los Menucos temporal analysis
    hourly = menucos_data.groupby('hour')['p_total'].agg(['mean', 'max']).round(3)
    
    temporal_analysis['by_station']['Los Menucos'] = {
        'hourly_profile': {
            'p_total': {
                'mean': {str(h): float(hourly.loc[h, 'mean']) if h in hourly.index else 0 for h in range(24)},
                'max': {str(h): float(hourly.loc[h, 'max']) if h in hourly.index else 0 for h in range(24)}
            }
        },
        'peak_analysis': {
            'avg_peak_demand': menucos_data[menucos_data['is_peak_hour']]['p_total'].mean(),
            'max_peak_demand': menucos_data[menucos_data['is_peak_hour']]['p_total'].max()
        }
    }
    
    with open(temporal_file, 'w') as f:
        json.dump(temporal_analysis, f, indent=2, default=str)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DEL PROCESAMIENTO - LOS MENUCOS")
    logger.info("="*60)
    logger.info(f"Archivos procesados: {len(all_data)}")
    logger.info(f"Total registros Los Menucos: {len(menucos_data):,}")
    logger.info(f"Período: {menucos_data['timestamp'].min()} a {menucos_data['timestamp'].max()}")
    logger.info(f"Tensión promedio: {menucos_data['v_avg'].mean():.0f} V ({menucos_data['v_pu'].mean():.3f} pu)")
    logger.info(f"Potencia promedio: {menucos_data['p_total'].mean():.2f} MW")
    logger.info(f"Potencia máxima: {menucos_data['p_total'].max():.2f} MW")
    logger.info(f"Factor de potencia promedio: {menucos_data['fp'].mean():.3f}")
    logger.info(f"% tiempo dentro de límites: {menucos_data['v_within_limits'].mean()*100:.1f}%")
    
    # Show voltage drop progression
    logger.info("\n" + "="*60)
    logger.info("PROGRESIÓN DE CAÍDA DE TENSIÓN EN EL SISTEMA")
    logger.info("="*60)
    
    # Load all quality metrics to show progression
    with open(quality_file, 'r') as f:
        all_metrics = json.load(f)
    
    stations_order = ['Pilcaniyeu', 'Jacobacci', 'Los Menucos']
    distances = {'Pilcaniyeu': 0, 'Jacobacci': 150, 'Los Menucos': 270}
    
    for station in stations_order:
        if station in all_metrics:
            metrics = all_metrics[station]
            v_pu = metrics['voltage_quality']['avg_voltage_pu']
            p_avg = metrics['power_stats']['avg_power_mw']
            dist = distances.get(station, 0)
            logger.info(f"  {station:12} ({dist:3d} km): V = {v_pu:.3f} pu ({(1-v_pu)*100:.0f}% caída), P = {p_avg:.2f} MW")
    
    logger.info(f"\nTOTAL SISTEMA: {len(consolidated):,} registros")
    logger.info("\n✓ Procesamiento completado exitosamente")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())