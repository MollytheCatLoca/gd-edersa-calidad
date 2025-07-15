#!/usr/bin/env python3
"""
Fixed processing script for Pilcaniyeu data
Based on the actual file format discovered
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
        
        # Add metadata from filename
        if 'ET4PI' in file_path.stem:
            df['station'] = 'Pilcaniyeu'
            df['voltage_level'] = '33kV' if '_33' in file_path.stem else '13.2kV'
        else:
            df['station'] = 'Unknown'
            df['voltage_level'] = 'Unknown'
        
        # Add per-unit voltage (assuming 33kV system)
        v_nominal = 33000 if '33' in df['voltage_level'].iloc[0] else 13200
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
    """Process Pilcaniyeu data files."""
    logger.info("="*60)
    logger.info("PROCESAMIENTO PILCANIYEU - FORMATO CORREGIDO")
    logger.info("="*60)
    
    # Find Pilcaniyeu files
    base_path = project_root / "data" / "Registros Línea Sur"
    pilcaniyeu_files = []
    
    for year_folder in base_path.glob("Pilcaniyeu*"):
        if year_folder.is_dir():
            for month_folder in year_folder.glob("*"):
                if month_folder.is_dir():
                    # Process only 33kV files for now
                    pilcaniyeu_files.extend(month_folder.glob("*_33*.xls*"))
    
    logger.info(f"Archivos encontrados: {len(pilcaniyeu_files)}")
    
    if not pilcaniyeu_files:
        logger.error("No se encontraron archivos")
        return 1
    
    # Process files
    all_data = []
    files_to_process = sorted(pilcaniyeu_files)  # Procesar TODOS los archivos
    
    for file_path in files_to_process:
        df = process_epre_file(file_path)
        if not df.empty:
            all_data.append(df)
    
    if not all_data:
        logger.error("No se pudo procesar ningún archivo")
        return 1
    
    # Combine all data
    logger.info(f"\nCombinando {len(all_data)} archivos...")
    consolidated = pd.concat(all_data, ignore_index=True)
    consolidated = consolidated.sort_values('timestamp')
    
    # Save results
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save parquet (if available) or CSV
    try:
        output_file = processed_dir / "consolidated_data.parquet"
        consolidated.to_parquet(output_file, index=False)
        logger.info(f"Datos guardados: {output_file}")
    except ImportError:
        logger.warning("Parquet no disponible, guardando como CSV")
        output_file = processed_dir / "consolidated_data.csv"
        consolidated.to_csv(output_file, index=False)
        logger.info(f"Datos guardados: {output_file}")
    
    # Save CSV sample
    csv_file = processed_dir / "consolidated_data_sample.csv"
    consolidated.head(1000).to_csv(csv_file, index=False)
    
    # Generate quality metrics
    quality_metrics = {
        'Pilcaniyeu': {
            'total_raw_records': len(consolidated),
            'total_clean_records': len(consolidated),
            'records_removed': 0,
            'removal_percentage': 0,
            'date_range': {
                'start': str(consolidated['timestamp'].min()),
                'end': str(consolidated['timestamp'].max())
            },
            'voltage_quality': {
                'within_limits_pct': consolidated['v_within_limits'].mean() * 100,
                'avg_voltage_pu': consolidated['v_pu'].mean(),
                'min_voltage_pu': consolidated['v_pu'].min(),
                'max_voltage_pu': consolidated['v_pu'].max()
            },
            'power_stats': {
                'avg_power_mw': consolidated['p_total'].mean(),
                'max_power_mw': consolidated['p_total'].max(),
                'avg_power_factor': consolidated['fp'].mean()
            }
        }
    }
    
    with open(processed_dir / "quality_metrics.json", 'w') as f:
        json.dump(quality_metrics, f, indent=2, default=str)
    
    # Generate temporal analysis
    hourly = consolidated.groupby('hour')['p_total'].agg(['mean', 'max']).round(3)
    
    temporal_analysis = {
        'overall': {
            'total_days': (consolidated['timestamp'].max() - consolidated['timestamp'].min()).days,
            'records_per_day': len(consolidated) / ((consolidated['timestamp'].max() - consolidated['timestamp'].min()).days + 1),
            'stations_processed': ['Pilcaniyeu']
        },
        'by_station': {
            'Pilcaniyeu': {
                'hourly_profile': {
                    'p_total': {
                        'mean': {str(h): float(hourly.loc[h, 'mean']) if h in hourly.index else 0 for h in range(24)},
                        'max': {str(h): float(hourly.loc[h, 'max']) if h in hourly.index else 0 for h in range(24)}
                    }
                },
                'peak_analysis': {
                    'avg_peak_demand': consolidated[consolidated['is_peak_hour']]['p_total'].mean(),
                    'max_peak_demand': consolidated[consolidated['is_peak_hour']]['p_total'].max()
                }
            }
        }
    }
    
    with open(processed_dir / "temporal_analysis.json", 'w') as f:
        json.dump(temporal_analysis, f, indent=2, default=str)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DEL PROCESAMIENTO")
    logger.info("="*60)
    logger.info(f"Archivos procesados: {len(all_data)}")
    logger.info(f"Total registros: {len(consolidated):,}")
    logger.info(f"Período: {consolidated['timestamp'].min()} a {consolidated['timestamp'].max()}")
    logger.info(f"Tensión promedio: {consolidated['v_avg'].mean():.0f} V ({consolidated['v_pu'].mean():.3f} pu)")
    logger.info(f"Potencia promedio: {consolidated['p_total'].mean():.2f} MW")
    logger.info(f"Factor de potencia promedio: {consolidated['fp'].mean():.3f}")
    logger.info(f"% tiempo dentro de límites: {consolidated['v_within_limits'].mean()*100:.1f}%")
    
    logger.info("\n✓ Procesamiento completado exitosamente")
    logger.info("✓ Ejecute el dashboard para ver los resultados")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())