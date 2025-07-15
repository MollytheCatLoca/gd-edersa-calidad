#!/usr/bin/env python3
"""
Simple processing script for one station with robust error handling
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import json
import argparse
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_processing.simple_loader import load_epre_file
from src.data_processing.cleaner import DataCleaner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_station_simple(station_name='Pilcaniyeu'):
    """Process a single station with simple approach."""
    logger.info("="*60)
    logger.info(f"PROCESAMIENTO SIMPLE - {station_name}")
    logger.info("="*60)
    
    # Station folder mapping
    folder_map = {
        'Pilcaniyeu': 'Pilcaniyeu',
        'Jacobacci': 'Jacobacci',
        'Maquinchao': 'Maquinchao',
        'Los Menucos': 'Menucos'
    }
    
    folder_name = folder_map.get(station_name, station_name)
    
    # Find all Excel files for the station
    base_path = project_root / "data" / "Registros Línea Sur"
    station_files = []
    
    # Look in year folders
    for year_folder in base_path.glob(f"{folder_name}*"):
        if year_folder.is_dir():
            for month_folder in year_folder.glob("*"):
                if month_folder.is_dir():
                    station_files.extend(month_folder.glob("*.xls*"))
    
    logger.info(f"Archivos encontrados: {len(station_files)}")
    
    if not station_files:
        logger.error(f"No se encontraron archivos para {station_name}")
        return False
    
    # Process files
    all_data = []
    successful = 0
    
    for file_path in sorted(station_files)[:5]:  # Start with just 5 files
        logger.info(f"\nProcesando: {file_path.name}")
        df = load_epre_file(file_path)
        
        if not df.empty:
            all_data.append(df)
            successful += 1
            logger.info(f"  ✓ {len(df)} registros")
        else:
            logger.warning(f"  ✗ Sin datos válidos")
    
    if not all_data:
        logger.error("No se pudo procesar ningún archivo")
        return False
    
    # Combine all data
    logger.info(f"\nCombinando {successful} archivos...")
    combined_data = pd.concat(all_data, ignore_index=True)
    combined_data = combined_data.sort_values('timestamp')
    
    # Basic cleaning
    cleaner = DataCleaner()
    clean_data = cleaner.add_quality_metrics(combined_data)
    
    # Save results
    save_simple_results(station_name, combined_data, clean_data)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("RESUMEN")
    logger.info("="*60)
    logger.info(f"Archivos procesados: {successful}/{len(station_files[:5])}")
    logger.info(f"Registros totales: {len(clean_data):,}")
    
    if 'timestamp' in clean_data.columns:
        logger.info(f"Período: {clean_data['timestamp'].min()} a {clean_data['timestamp'].max()}")
    
    if 'v_avg' in clean_data.columns:
        logger.info(f"Tensión promedio: {clean_data['v_avg'].mean():.1f} V")
    
    if 'p_total' in clean_data.columns:
        logger.info(f"Potencia promedio: {clean_data['p_total'].mean():.2f} MW")
    
    logger.info("\n✓ Procesamiento completado")
    return True


def save_simple_results(station_name, raw_data, clean_data):
    """Save results in simplified format."""
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main data
    output_file = processed_dir / f"{station_name.lower()}_data.parquet"
    clean_data.to_parquet(output_file, index=False)
    logger.info(f"\nDatos guardados en: {output_file}")
    
    # Also save as consolidated for dashboard compatibility
    consolidated_file = processed_dir / "consolidated_data.parquet"
    if consolidated_file.exists():
        # Append to existing
        existing = pd.read_parquet(consolidated_file)
        existing = existing[existing['station'] != station_name]  # Remove old data for this station
        combined = pd.concat([existing, clean_data], ignore_index=True)
        combined.to_parquet(consolidated_file, index=False)
    else:
        clean_data.to_parquet(consolidated_file, index=False)
    
    # Save CSV sample
    sample_file = processed_dir / "consolidated_data_sample.csv"
    clean_data.head(1000).to_csv(sample_file, index=False)
    
    # Create simple quality metrics
    quality_metrics = {
        station_name: {
            'total_raw_records': len(raw_data),
            'total_clean_records': len(clean_data),
            'records_removed': len(raw_data) - len(clean_data),
            'removal_percentage': (1 - len(clean_data)/len(raw_data)) * 100 if len(raw_data) > 0 else 0,
            'date_range': {
                'start': str(clean_data['timestamp'].min()) if 'timestamp' in clean_data.columns else None,
                'end': str(clean_data['timestamp'].max()) if 'timestamp' in clean_data.columns else None
            }
        }
    }
    
    # Add voltage stats if available
    if 'v_avg' in clean_data.columns:
        v_nominal = 33000 if '33' in clean_data['voltage_level'].iloc[0] else 13200
        clean_data['v_pu'] = clean_data['v_avg'] / v_nominal
        clean_data['v_within_limits'] = (clean_data['v_pu'] >= 0.95) & (clean_data['v_pu'] <= 1.05)
        
        quality_metrics[station_name]['voltage_quality'] = {
            'within_limits_pct': clean_data['v_within_limits'].mean() * 100,
            'avg_voltage_pu': clean_data['v_pu'].mean(),
            'min_voltage_pu': clean_data['v_pu'].min(),
            'max_voltage_pu': clean_data['v_pu'].max()
        }
    
    # Add power stats if available
    if 'p_total' in clean_data.columns:
        quality_metrics[station_name]['power_stats'] = {
            'avg_power_mw': clean_data['p_total'].mean(),
            'max_power_mw': clean_data['p_total'].max(),
            'avg_power_factor': clean_data['fp'].mean() if 'fp' in clean_data.columns else None
        }
    
    # Save or update quality metrics
    quality_file = processed_dir / "quality_metrics.json"
    if quality_file.exists():
        with open(quality_file, 'r') as f:
            existing_metrics = json.load(f)
        existing_metrics.update(quality_metrics)
        quality_metrics = existing_metrics
    
    with open(quality_file, 'w') as f:
        json.dump(quality_metrics, f, indent=2, default=str)
    
    # Create simple temporal analysis
    temporal_analysis = {
        'overall': {
            'stations_processed': [station_name],
            'total_records': len(clean_data)
        },
        'by_station': {}
    }
    
    if 'timestamp' in clean_data.columns:
        clean_data['hour'] = clean_data['timestamp'].dt.hour
        
        # Hourly profile
        if 'p_total' in clean_data.columns:
            hourly = clean_data.groupby('hour')['p_total'].agg(['mean', 'max']).round(3)
            
            temporal_analysis['by_station'][station_name] = {
                'hourly_profile': {
                    'p_total': {
                        'mean': {str(h): float(hourly.loc[h, 'mean']) if h in hourly.index else 0 for h in range(24)},
                        'max': {str(h): float(hourly.loc[h, 'max']) if h in hourly.index else 0 for h in range(24)}
                    }
                }
            }
    
    # Save or update temporal analysis
    temporal_file = processed_dir / "temporal_analysis.json"
    if temporal_file.exists():
        with open(temporal_file, 'r') as f:
            existing_temporal = json.load(f)
        # Update with new station
        if 'by_station' not in existing_temporal:
            existing_temporal['by_station'] = {}
        existing_temporal['by_station'].update(temporal_analysis['by_station'])
        existing_temporal['overall']['stations_processed'] = list(set(
            existing_temporal['overall'].get('stations_processed', []) + [station_name]
        ))
        temporal_analysis = existing_temporal
    
    with open(temporal_file, 'w') as f:
        json.dump(temporal_analysis, f, indent=2, default=str)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Procesamiento simple de datos')
    parser.add_argument(
        '--station',
        default='Pilcaniyeu',
        choices=['Pilcaniyeu', 'Jacobacci', 'Maquinchao', 'Los Menucos'],
        help='Estación a procesar'
    )
    
    args = parser.parse_args()
    
    success = process_station_simple(args.station)
    
    if success:
        logger.info("\n✓ Para ver resultados en dashboard:")
        logger.info("  python3 dashboard/app_multipagina.py")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())