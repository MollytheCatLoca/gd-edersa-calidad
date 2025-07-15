"""
Module: processor
Purpose: ETL pipeline for processing electrical measurement data
Author: Claude AI Assistant
Date: 2025-07-06
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, List, Dict, Optional, Tuple
import logging
from datetime import datetime
import json

from .loader import DataLoader
from .cleaner import DataCleaner

logger = logging.getLogger(__name__)


class DataProcessor:
    """Main ETL pipeline for processing electrical measurement data."""
    
    def __init__(self, base_path: Union[str, Path] = None):
        """
        Initialize DataProcessor.
        
        Parameters
        ----------
        base_path : str or Path, optional
            Base path for data files
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.loader = DataLoader(self.base_path)
        self.cleaner = DataCleaner()
        
        # Results storage
        self.consolidated_data = None
        self.quality_report = {}
        self.temporal_analysis = {}
    
    def process_all_stations(self, year: int = None, save_results: bool = True) -> pd.DataFrame:
        """
        Process all station data through complete ETL pipeline.
        
        Parameters
        ----------
        year : int, optional
            Specific year to process
        save_results : bool
            Whether to save processed results
            
        Returns
        -------
        pd.DataFrame
            Consolidated processed data
        """
        logger.info("Starting ETL pipeline for all stations...")
        start_time = datetime.now()
        
        # Load all station data
        all_station_data = self.loader.load_all_stations_data(year)
        
        if not all_station_data:
            logger.error("No data loaded for any station")
            return pd.DataFrame()
        
        # Process each station
        processed_data = []
        for station, df in all_station_data.items():
            logger.info(f"Processing {station}: {len(df)} records")
            
            # Clean data
            df_clean = self.cleaner.clean_measurement_data(df)
            
            # Add quality metrics
            df_clean = self.cleaner.add_quality_metrics(df_clean)
            
            # Store quality statistics
            self._calculate_quality_stats(station, df, df_clean)
            
            processed_data.append(df_clean)
        
        # Consolidate all data
        self.consolidated_data = pd.concat(processed_data, ignore_index=True)
        self.consolidated_data = self.consolidated_data.sort_values(['station', 'timestamp'])
        
        # Calculate temporal patterns
        self._analyze_temporal_patterns()
        
        # Save results if requested
        if save_results:
            self._save_results()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"ETL pipeline completed in {duration:.1f} seconds")
        logger.info(f"Total records processed: {len(self.consolidated_data)}")
        
        return self.consolidated_data
    
    def _calculate_quality_stats(self, station: str, df_raw: pd.DataFrame, df_clean: pd.DataFrame):
        """Calculate data quality statistics for a station."""
        total_raw = len(df_raw)
        total_clean = len(df_clean)
        removed = total_raw - total_clean
        
        stats = {
            'total_raw_records': total_raw,
            'total_clean_records': total_clean,
            'records_removed': removed,
            'removal_percentage': (removed / total_raw * 100) if total_raw > 0 else 0,
            'date_range': {
                'start': str(df_clean['timestamp'].min()) if 'timestamp' in df_clean.columns else None,
                'end': str(df_clean['timestamp'].max()) if 'timestamp' in df_clean.columns else None
            }
        }
        
        # Voltage quality stats
        if 'v_within_limits' in df_clean.columns:
            stats['voltage_quality'] = {
                'within_limits_pct': df_clean['v_within_limits'].mean() * 100,
                'avg_voltage_pu': df_clean['v_pu'].mean() if 'v_pu' in df_clean.columns else None,
                'min_voltage_pu': df_clean['v_pu'].min() if 'v_pu' in df_clean.columns else None,
                'max_voltage_pu': df_clean['v_pu'].max() if 'v_pu' in df_clean.columns else None
            }
        
        # Power stats
        if 'p_total' in df_clean.columns:
            stats['power_stats'] = {
                'avg_power_mw': df_clean['p_total'].mean(),
                'max_power_mw': df_clean['p_total'].max(),
                'avg_power_factor': df_clean['fp'].mean() if 'fp' in df_clean.columns else None
            }
        
        self.quality_report[station] = stats
    
    def _analyze_temporal_patterns(self):
        """Analyze temporal patterns in the consolidated data."""
        if self.consolidated_data is None or self.consolidated_data.empty:
            return
        
        df = self.consolidated_data
        
        # Overall temporal analysis
        self.temporal_analysis['overall'] = {
            'total_days': (df['timestamp'].max() - df['timestamp'].min()).days,
            'records_per_day': len(df) / ((df['timestamp'].max() - df['timestamp'].min()).days + 1)
        }
        
        # By station analysis
        station_patterns = {}
        for station in df['station'].unique():
            station_df = df[df['station'] == station]
            
            patterns = {}
            
            # Hourly patterns
            if 'hour' in station_df.columns and 'p_total' in station_df.columns:
                hourly = station_df.groupby('hour').agg({
                    'p_total': ['mean', 'std', 'max'],
                    'v_pu': 'mean' if 'v_pu' in station_df.columns else lambda x: None
                }).round(3)
                patterns['hourly_profile'] = hourly.to_dict()
            
            # Daily patterns
            if 'day_of_week' in station_df.columns:
                daily = station_df.groupby('day_of_week').agg({
                    'p_total': 'mean',
                    'is_peak_hour': 'sum' if 'is_peak_hour' in station_df.columns else lambda x: None
                }).round(3)
                patterns['daily_profile'] = daily.to_dict()
            
            # Monthly patterns
            if 'month' in station_df.columns:
                monthly = station_df.groupby('month').agg({
                    'p_total': 'mean',
                    'v_pu': 'mean' if 'v_pu' in station_df.columns else lambda x: None
                }).round(3)
                patterns['monthly_profile'] = monthly.to_dict()
            
            # Peak analysis
            if 'is_peak_hour' in station_df.columns:
                peak_df = station_df[station_df['is_peak_hour']]
                patterns['peak_analysis'] = {
                    'avg_peak_demand': peak_df['p_total'].mean() if 'p_total' in peak_df.columns else None,
                    'max_peak_demand': peak_df['p_total'].max() if 'p_total' in peak_df.columns else None,
                    'avg_peak_voltage_pu': peak_df['v_pu'].mean() if 'v_pu' in peak_df.columns else None
                }
            
            station_patterns[station] = patterns
        
        self.temporal_analysis['by_station'] = station_patterns
    
    def _save_results(self):
        """Save processed results to files."""
        processed_dir = self.base_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save consolidated data
        if self.consolidated_data is not None:
            parquet_path = processed_dir / "consolidated_data.parquet"
            self.consolidated_data.to_parquet(parquet_path, index=False, compression='snappy')
            logger.info(f"Saved consolidated data to {parquet_path}")
            
            # Also save a sample CSV for easy viewing
            sample_path = processed_dir / "consolidated_data_sample.csv"
            self.consolidated_data.head(1000).to_csv(sample_path, index=False)
            logger.info(f"Saved sample data to {sample_path}")
        
        # Save quality report
        if self.quality_report:
            quality_path = processed_dir / "quality_metrics.json"
            with open(quality_path, 'w') as f:
                json.dump(self.quality_report, f, indent=2, default=str)
            logger.info(f"Saved quality report to {quality_path}")
        
        # Save temporal analysis
        if self.temporal_analysis:
            temporal_path = processed_dir / "temporal_analysis.json"
            with open(temporal_path, 'w') as f:
                json.dump(self.temporal_analysis, f, indent=2, default=str)
            logger.info(f"Saved temporal analysis to {temporal_path}")
    
    def generate_daily_profiles(self) -> pd.DataFrame:
        """
        Generate typical daily profiles for each station.
        
        Returns
        -------
        pd.DataFrame
            Daily profiles by hour and station
        """
        if self.consolidated_data is None:
            logger.error("No consolidated data available. Run process_all_stations first.")
            return pd.DataFrame()
        
        df = self.consolidated_data
        
        # Calculate daily profiles
        profiles = df.groupby(['station', 'hour']).agg({
            'p_total': ['mean', 'std', 'min', 'max', 'count'],
            'q_total': ['mean', 'std'] if 'q_total' in df.columns else lambda x: [None, None],
            'v_pu': ['mean', 'std', 'min'] if 'v_pu' in df.columns else lambda x: [None, None, None],
            'fp': 'mean' if 'fp' in df.columns else lambda x: None
        }).round(3)
        
        # Flatten column names
        profiles.columns = ['_'.join(col).strip() for col in profiles.columns.values]
        profiles = profiles.reset_index()
        
        # Save profiles
        processed_dir = self.base_path / "data" / "processed"
        profiles_path = processed_dir / "daily_profiles.parquet"
        profiles.to_parquet(profiles_path, index=False)
        logger.info(f"Saved daily profiles to {profiles_path}")
        
        return profiles
    
    def analyze_voltage_violations(self) -> Dict[str, pd.DataFrame]:
        """
        Analyze voltage violations by station.
        
        Returns
        -------
        dict
            Dictionary with violation analysis by station
        """
        if self.consolidated_data is None:
            return {}
        
        df = self.consolidated_data
        violations = {}
        
        for station in df['station'].unique():
            station_df = df[df['station'] == station]
            
            if 'v_within_limits' not in station_df.columns:
                continue
            
            # Calculate violation statistics
            violation_df = station_df[~station_df['v_within_limits']].copy()
            
            if not violation_df.empty:
                # Group consecutive violations
                violation_df['violation_group'] = (
                    violation_df['v_within_limits'].diff().fillna(True).cumsum()
                )
                
                # Calculate duration of each violation period
                violation_periods = violation_df.groupby('violation_group').agg({
                    'timestamp': ['min', 'max', 'count'],
                    'v_pu': ['mean', 'min'],
                    'v_violation': 'mean'
                })
                
                violation_periods.columns = ['start_time', 'end_time', 'count', 
                                            'avg_voltage_pu', 'min_voltage_pu', 'avg_violation']
                
                # Calculate duration in minutes
                violation_periods['duration_minutes'] = (
                    (violation_periods['end_time'] - violation_periods['start_time']).dt.total_seconds() / 60
                )
                
                violations[station] = violation_periods
        
        return violations