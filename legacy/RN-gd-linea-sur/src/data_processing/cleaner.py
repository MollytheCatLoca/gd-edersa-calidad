"""
Module: cleaner
Purpose: Data cleaning and validation utilities
Author: Claude AI Assistant
Date: 2025-07-06
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Union, List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Handles data cleaning and validation operations."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize DataCleaner.
        
        Parameters
        ----------
        config : dict, optional
            Configuration parameters for cleaning thresholds
        """
        self.config = config or {
            'voltage_min_pu': 0.5,
            'voltage_max_pu': 1.5,
            'voltage_nominal': {
                '33kV': 33000,
                '13.2kV': 13200,
                'NORTE': 33000,
                'SUR': 33000
            },
            'power_factor_min': 0.0,
            'power_factor_max': 1.0,
            'current_max': 1000,  # A
            'power_max': 50,  # MW
            'outlier_std_factor': 3
        }
    
    def clean_measurement_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean measurement data from EPRE format.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw measurement data
            
        Returns
        -------
        pd.DataFrame
            Cleaned data
        """
        df_clean = df.copy()
        
        # Remove duplicates
        df_clean = df_clean.drop_duplicates()
        
        # Handle missing values
        df_clean = self._handle_missing_values(df_clean)
        
        # Validate ranges
        df_clean = self._validate_ranges(df_clean)
        
        logger.info(f"Cleaned data: {len(df_clean)} rows remaining from {len(df)}")
        return df_clean
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset."""
        df_clean = df.copy()
        
        # Numeric columns to interpolate
        numeric_cols = ['v1', 'v2', 'v3', 'i1', 'i2', 'i3', 'p_total', 'q_total', 'fp']
        
        for col in numeric_cols:
            if col in df_clean.columns:
                # Interpolate missing values for short gaps (< 5 minutes)
                df_clean[col] = df_clean[col].interpolate(method='linear', limit=5)
                
                # For longer gaps, use forward/backward fill
                df_clean[col] = df_clean[col].fillna(method='ffill', limit=10)
                df_clean[col] = df_clean[col].fillna(method='bfill', limit=10)
        
        # Drop rows where critical values are still missing
        critical_cols = ['timestamp', 'v_avg', 'p_total']
        critical_cols = [col for col in critical_cols if col in df_clean.columns]
        
        initial_len = len(df_clean)
        df_clean = df_clean.dropna(subset=critical_cols)
        dropped = initial_len - len(df_clean)
        
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows with missing critical values")
        
        return df_clean
    
    def _validate_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate data ranges and remove outliers."""
        df_clean = df.copy()
        initial_len = len(df_clean)
        
        # Get voltage nominal for the measurement
        voltage_level = df_clean['voltage_level'].iloc[0] if 'voltage_level' in df_clean.columns else '33kV'
        v_nominal = self.config['voltage_nominal'].get(voltage_level, 33000)
        
        # Voltage validation
        voltage_cols = ['v1', 'v2', 'v3', 'v_avg']
        for col in voltage_cols:
            if col in df_clean.columns:
                v_min = v_nominal * self.config['voltage_min_pu']
                v_max = v_nominal * self.config['voltage_max_pu']
                
                # Mark outliers
                outliers = (df_clean[col] < v_min) | (df_clean[col] > v_max)
                if outliers.any():
                    logger.warning(f"{col}: {outliers.sum()} values outside range [{v_min:.0f}, {v_max:.0f}]")
                    df_clean.loc[outliers, col] = np.nan
        
        # Power factor validation
        if 'fp' in df_clean.columns:
            fp_outliers = (df_clean['fp'] < self.config['power_factor_min']) | \
                         (df_clean['fp'] > self.config['power_factor_max'])
            if fp_outliers.any():
                logger.warning(f"Power factor: {fp_outliers.sum()} values outside range [0, 1]")
                df_clean.loc[fp_outliers, 'fp'] = np.nan
        
        # Current validation
        current_cols = ['i1', 'i2', 'i3']
        for col in current_cols:
            if col in df_clean.columns:
                i_outliers = (df_clean[col] < 0) | (df_clean[col] > self.config['current_max'])
                if i_outliers.any():
                    logger.warning(f"{col}: {i_outliers.sum()} values outside range [0, {self.config['current_max']}]")
                    df_clean.loc[i_outliers, col] = np.nan
        
        # Power validation
        if 'p_total' in df_clean.columns:
            p_outliers = (df_clean['p_total'] < -self.config['power_max']) | \
                        (df_clean['p_total'] > self.config['power_max'])
            if p_outliers.any():
                logger.warning(f"Power: {p_outliers.sum()} values outside range")
                df_clean.loc[p_outliers, 'p_total'] = np.nan
        
        # Statistical outlier detection using z-score
        numeric_cols = ['v_avg', 'p_total', 'q_total']
        for col in numeric_cols:
            if col in df_clean.columns:
                # Calculate z-score
                mean = df_clean[col].mean()
                std = df_clean[col].std()
                if std > 0:
                    z_scores = np.abs((df_clean[col] - mean) / std)
                    outliers = z_scores > self.config['outlier_std_factor']
                    if outliers.any():
                        logger.info(f"{col}: {outliers.sum()} statistical outliers detected")
                        # Don't remove, just flag for review
        
        # Calculate per-unit values
        if 'v_avg' in df_clean.columns:
            df_clean['v_pu'] = df_clean['v_avg'] / v_nominal
        
        # Remove rows with too many invalid values
        df_clean = self._handle_missing_values(df_clean)
        
        final_len = len(df_clean)
        if final_len < initial_len:
            logger.info(f"Validation removed {initial_len - final_len} rows")
        
        return df_clean
    
    def add_quality_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add quality metrics to the dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Cleaned measurement data
            
        Returns
        -------
        pd.DataFrame
            Data with additional quality metrics
        """
        df = df.copy()
        
        # Voltage quality metrics
        if 'v_pu' in df.columns:
            # Voltage within limits (0.95 - 1.05 pu)
            df['v_within_limits'] = (df['v_pu'] >= 0.95) & (df['v_pu'] <= 1.05)
            
            # Voltage violation severity
            df['v_violation'] = 0
            df.loc[df['v_pu'] < 0.95, 'v_violation'] = 0.95 - df.loc[df['v_pu'] < 0.95, 'v_pu']
            df.loc[df['v_pu'] > 1.05, 'v_violation'] = df.loc[df['v_pu'] > 1.05, 'v_pu'] - 1.05
        
        # Power quality
        if all(col in df.columns for col in ['p_total', 'q_total']):
            # Apparent power
            df['s_total'] = np.sqrt(df['p_total']**2 + df['q_total']**2)
            
            # Recalculate power factor for validation
            df['fp_calc'] = np.where(df['s_total'] > 0, 
                                     np.abs(df['p_total']) / df['s_total'], 
                                     np.nan)
        
        # Time-based features
        if 'timestamp' in df.columns:
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            df['is_weekend'] = df['day_of_week'].isin([5, 6])
            
            # Peak hours (typically 18-23)
            df['is_peak_hour'] = df['hour'].between(18, 23)
        
        return df