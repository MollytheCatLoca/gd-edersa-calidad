#!/usr/bin/env python3
"""
Script: 03_process_all_data.py
Purpose: Process all electrical measurement data through ETL pipeline
Author: Claude AI Assistant
Date: 2025-07-06
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_processing.processor import DataProcessor


def setup_logging(log_file: str = None):
    """Setup logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=handlers
    )


def main():
    """Main function to process all data."""
    parser = argparse.ArgumentParser(description='Process all electrical measurement data')
    parser.add_argument('--year', type=int, help='Specific year to process (e.g., 2024)')
    parser.add_argument('--log-file', help='Path to log file')
    parser.add_argument('--skip-save', action='store_true', help='Skip saving results')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_file)
    logger = logging.getLogger(__name__)
    
    logger.info("="*80)
    logger.info("FASE 3: PROCESAMIENTO EXHAUSTIVO DE DATOS")
    logger.info("="*80)
    logger.info(f"Start time: {datetime.now()}")
    
    try:
        # Initialize processor
        processor = DataProcessor(project_root)
        
        # Process all stations
        logger.info("Starting ETL pipeline...")
        consolidated_data = processor.process_all_stations(
            year=args.year,
            save_results=not args.skip_save
        )
        
        if consolidated_data.empty:
            logger.error("No data was processed!")
            return 1
        
        # Generate additional analysis
        logger.info("\nGenerating daily profiles...")
        daily_profiles = processor.generate_daily_profiles()
        
        logger.info("\nAnalyzing voltage violations...")
        violations = processor.analyze_voltage_violations()
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("PROCESSING SUMMARY")
        logger.info("="*80)
        
        logger.info(f"\nTotal records processed: {len(consolidated_data):,}")
        logger.info(f"Date range: {consolidated_data['timestamp'].min()} to {consolidated_data['timestamp'].max()}")
        logger.info(f"Stations processed: {', '.join(consolidated_data['station'].unique())}")
        
        # Quality summary
        logger.info("\nDATA QUALITY SUMMARY:")
        for station, stats in processor.quality_report.items():
            logger.info(f"\n{station}:")
            logger.info(f"  - Raw records: {stats['total_raw_records']:,}")
            logger.info(f"  - Clean records: {stats['total_clean_records']:,}")
            logger.info(f"  - Removal rate: {stats['removal_percentage']:.1f}%")
            
            if 'voltage_quality' in stats:
                vq = stats['voltage_quality']
                logger.info(f"  - Voltage within limits: {vq['within_limits_pct']:.1f}%")
                logger.info(f"  - Average voltage: {vq['avg_voltage_pu']:.3f} pu")
        
        # Temporal patterns summary
        logger.info("\nTEMPORAL PATTERNS:")
        if 'overall' in processor.temporal_analysis:
            overall = processor.temporal_analysis['overall']
            logger.info(f"  - Total days: {overall['total_days']}")
            logger.info(f"  - Records per day: {overall['records_per_day']:.0f}")
        
        # Violations summary
        if violations:
            logger.info("\nVOLTAGE VIOLATIONS SUMMARY:")
            for station, viol_df in violations.items():
                if not viol_df.empty:
                    logger.info(f"\n{station}:")
                    logger.info(f"  - Total violation periods: {len(viol_df)}")
                    logger.info(f"  - Total violation time: {viol_df['duration_minutes'].sum():.0f} minutes")
                    logger.info(f"  - Worst voltage: {viol_df['min_voltage_pu'].min():.3f} pu")
        
        # Output locations
        if not args.skip_save:
            logger.info("\nOUTPUT FILES:")
            logger.info(f"  - Consolidated data: data/processed/consolidated_data.parquet")
            logger.info(f"  - Quality report: data/processed/quality_metrics.json")
            logger.info(f"  - Temporal analysis: data/processed/temporal_analysis.json")
            logger.info(f"  - Daily profiles: data/processed/daily_profiles.parquet")
        
        logger.info("\n" + "="*80)
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in ETL pipeline: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())