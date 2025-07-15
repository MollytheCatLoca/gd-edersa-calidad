#!/usr/bin/env python3
"""
Script: test_data_processing.py
Purpose: Test data processing with a small subset of data
Author: Claude AI Assistant
Date: 2025-07-06
"""

import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_processing.loader import DataLoader
from src.data_processing.cleaner import DataCleaner


def test_single_file():
    """Test processing a single file."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    loader = DataLoader(project_root)
    cleaner = DataCleaner()
    
    # Find a test file
    test_dir = project_root / "data" / "Registros Línea Sur" / "Pilcaniyeu2024" / "0124"
    test_files = list(test_dir.glob("*.xls"))
    
    if not test_files:
        logger.error("No test files found")
        return
    
    test_file = test_files[0]
    logger.info(f"Testing with file: {test_file}")
    
    try:
        # Load file
        df = loader.load_measurement_file(test_file)
        logger.info(f"Loaded {len(df)} records")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Show sample data
        logger.info("\nSample data:")
        print(df.head())
        
        # Clean data
        df_clean = cleaner.clean_measurement_data(df)
        logger.info(f"\nAfter cleaning: {len(df_clean)} records")
        
        # Add quality metrics
        df_final = cleaner.add_quality_metrics(df_clean)
        logger.info(f"Final columns: {list(df_final.columns)}")
        
        # Show quality stats
        if 'v_pu' in df_final.columns:
            logger.info(f"\nVoltage stats:")
            logger.info(f"  Mean: {df_final['v_pu'].mean():.3f} pu")
            logger.info(f"  Min: {df_final['v_pu'].min():.3f} pu")
            logger.info(f"  Max: {df_final['v_pu'].max():.3f} pu")
            logger.info(f"  Within limits: {df_final['v_within_limits'].mean()*100:.1f}%")
        
        logger.info("\nTest completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)


if __name__ == "__main__":
    test_single_file()