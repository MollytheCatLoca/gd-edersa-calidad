#!/usr/bin/env python3
"""
Script: process_one_station.py
Purpose: Process data for a single station - iterative approach
Author: Claude AI Assistant
Date: 2025-07-06
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_processing.loader import DataLoader
from src.data_processing.cleaner import DataCleaner
from src.data_processing.processor import DataProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_single_station(station_name: str = 'Pilcaniyeu', year: int = None):
    """Process data for a single station."""
    logger.info("="*60)
    logger.info(f"PROCESAMIENTO DE ESTACIÓN: {station_name}")
    logger.info("="*60)
    
    # Initialize processor
    processor = DataProcessor(project_root)
    loader = DataLoader(project_root)
    cleaner = DataCleaner()
    
    try:
        # Load data for the station
        logger.info(f"Cargando datos de {station_name}...")
        station_data = loader.load_all_station_data(station_name, year)
        
        if station_data.empty:
            logger.error(f"No se encontraron datos para {station_name}")
            return False
        
        logger.info(f"Registros cargados: {len(station_data):,}")
        
        # Clean data
        logger.info("Limpiando datos...")
        clean_data = cleaner.clean_measurement_data(station_data)
        clean_data = cleaner.add_quality_metrics(clean_data)
        
        logger.info(f"Registros después de limpieza: {len(clean_data):,}")
        
        # Save or append to existing data
        processed_dir = project_root / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if consolidated data exists
        consolidated_path = processed_dir / "consolidated_data.parquet"
        
        if consolidated_path.exists():
            logger.info("Agregando a datos existentes...")
            existing_data = pd.read_parquet(consolidated_path)
            
            # Remove this station's old data if exists
            existing_data = existing_data[existing_data['station'] != station_name]
            
            # Combine with new data
            consolidated_data = pd.concat([existing_data, clean_data], ignore_index=True)
        else:
            logger.info("Creando nuevo archivo consolidado...")
            consolidated_data = clean_data
        
        # Sort by station and timestamp
        consolidated_data = consolidated_data.sort_values(['station', 'timestamp'])
        
        # Save consolidated data
        consolidated_data.to_parquet(consolidated_path, index=False)
        logger.info(f"Guardado en: {consolidated_path}")
        
        # Save CSV sample
        sample_path = processed_dir / "consolidated_data_sample.csv"
        consolidated_data.head(1000).to_csv(sample_path, index=False)
        
        # Update quality metrics
        update_quality_metrics(station_name, station_data, clean_data, processed_dir)
        
        # Update temporal analysis
        update_temporal_analysis(consolidated_data, processed_dir)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("RESUMEN DEL PROCESAMIENTO")
        logger.info("="*60)
        logger.info(f"Estación: {station_name}")
        logger.info(f"Registros originales: {len(station_data):,}")
        logger.info(f"Registros limpios: {len(clean_data):,}")
        logger.info(f"Tasa de remoción: {(1 - len(clean_data)/len(station_data))*100:.1f}%")
        
        if 'v_within_limits' in clean_data.columns:
            logger.info(f"Tensión dentro de límites: {clean_data['v_within_limits'].mean()*100:.1f}%")
        
        if 'p_total' in clean_data.columns:
            logger.info(f"Demanda promedio: {clean_data['p_total'].mean():.2f} MW")
            logger.info(f"Demanda máxima: {clean_data['p_total'].max():.2f} MW")
        
        logger.info("\n✓ Procesamiento completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error procesando {station_name}: {e}", exc_info=True)
        return False


def update_quality_metrics(station_name, raw_data, clean_data, processed_dir):
    """Update quality metrics file."""
    quality_path = processed_dir / "quality_metrics.json"
    
    # Load existing metrics if exists
    if quality_path.exists():
        with open(quality_path, 'r') as f:
            quality_metrics = json.load(f)
    else:
        quality_metrics = {}
    
    # Calculate metrics for this station
    station_metrics = {
        'total_raw_records': len(raw_data),
        'total_clean_records': len(clean_data),
        'records_removed': len(raw_data) - len(clean_data),
        'removal_percentage': (1 - len(clean_data)/len(raw_data)) * 100 if len(raw_data) > 0 else 0,
        'date_range': {
            'start': str(clean_data['timestamp'].min()) if 'timestamp' in clean_data.columns else None,
            'end': str(clean_data['timestamp'].max()) if 'timestamp' in clean_data.columns else None
        }
    }
    
    # Voltage quality
    if 'v_within_limits' in clean_data.columns:
        station_metrics['voltage_quality'] = {
            'within_limits_pct': clean_data['v_within_limits'].mean() * 100,
            'avg_voltage_pu': clean_data['v_pu'].mean() if 'v_pu' in clean_data.columns else None,
            'min_voltage_pu': clean_data['v_pu'].min() if 'v_pu' in clean_data.columns else None,
            'max_voltage_pu': clean_data['v_pu'].max() if 'v_pu' in clean_data.columns else None
        }
    
    # Power stats
    if 'p_total' in clean_data.columns:
        station_metrics['power_stats'] = {
            'avg_power_mw': clean_data['p_total'].mean(),
            'max_power_mw': clean_data['p_total'].max(),
            'avg_power_factor': clean_data['fp'].mean() if 'fp' in clean_data.columns else None
        }
    
    # Update metrics
    quality_metrics[station_name] = station_metrics
    
    # Save updated metrics
    with open(quality_path, 'w') as f:
        json.dump(quality_metrics, f, indent=2, default=str)
    
    logger.info(f"Métricas de calidad actualizadas: {quality_path}")


def update_temporal_analysis(consolidated_data, processed_dir):
    """Update temporal analysis file."""
    temporal_path = processed_dir / "temporal_analysis.json"
    
    # Overall analysis
    temporal_analysis = {
        'overall': {
            'total_days': (consolidated_data['timestamp'].max() - consolidated_data['timestamp'].min()).days,
            'records_per_day': len(consolidated_data) / ((consolidated_data['timestamp'].max() - consolidated_data['timestamp'].min()).days + 1),
            'stations_processed': list(consolidated_data['station'].unique())
        },
        'by_station': {}
    }
    
    # By station analysis
    for station in consolidated_data['station'].unique():
        station_df = consolidated_data[consolidated_data['station'] == station]
        
        station_analysis = {}
        
        # Hourly profile
        if 'hour' in station_df.columns and 'p_total' in station_df.columns:
            hourly = station_df.groupby('hour').agg({
                'p_total': ['mean', 'std', 'max'],
                'v_pu': 'mean' if 'v_pu' in station_df.columns else lambda x: None
            }).round(3)
            
            station_analysis['hourly_profile'] = {
                'p_total': {
                    'mean': {str(h): float(hourly.loc[h, ('p_total', 'mean')]) for h in range(24) if h in hourly.index},
                    'max': {str(h): float(hourly.loc[h, ('p_total', 'max')]) for h in range(24) if h in hourly.index}
                }
            }
        
        # Peak analysis
        if 'is_peak_hour' in station_df.columns:
            peak_df = station_df[station_df['is_peak_hour']]
            station_analysis['peak_analysis'] = {
                'avg_peak_demand': peak_df['p_total'].mean() if 'p_total' in peak_df.columns and not peak_df.empty else None,
                'max_peak_demand': peak_df['p_total'].max() if 'p_total' in peak_df.columns and not peak_df.empty else None
            }
        
        temporal_analysis['by_station'][station] = station_analysis
    
    # Save analysis
    with open(temporal_path, 'w') as f:
        json.dump(temporal_analysis, f, indent=2, default=str)
    
    logger.info(f"Análisis temporal actualizado: {temporal_path}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Procesar datos de una estación')
    parser.add_argument(
        '--station', 
        type=str, 
        default='Pilcaniyeu',
        choices=['Pilcaniyeu', 'Jacobacci', 'Maquinchao', 'Los Menucos', 'Comallo'],
        help='Nombre de la estación a procesar'
    )
    parser.add_argument('--year', type=int, help='Año específico (ej: 2024)')
    
    args = parser.parse_args()
    
    logger.info(f"Iniciando procesamiento - {datetime.now()}")
    
    success = process_single_station(args.station, args.year)
    
    if success:
        logger.info("\n✓ Para ver los resultados:")
        logger.info("  python3 dashboard/app_multipagina.py")
        logger.info("  Luego abrir: http://localhost:8050/fase3-datos")
        return 0
    else:
        logger.error("\n✗ Procesamiento falló")
        return 1


if __name__ == "__main__":
    sys.exit(main())