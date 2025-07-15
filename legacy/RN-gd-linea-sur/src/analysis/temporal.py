"""
Module: temporal
Purpose: Temporal analysis of electrical data
Author: Claude AI Assistant
Date: 2025-07-06
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class TemporalAnalyzer:
    """Performs temporal analysis on electrical measurement data."""
    
    def __init__(self, sampling_interval: int = 15):
        """
        Initialize TemporalAnalyzer.
        
        Parameters
        ----------
        sampling_interval : int
            Sampling interval in minutes (default: 15)
        """
        self.sampling_interval = sampling_interval
        
    def create_daily_profiles(self, df: pd.DataFrame, 
                            value_column: str) -> pd.DataFrame:
        """
        Create average daily profiles from time series data.
        
        Parameters
        ----------
        df : pd.DataFrame
            Time series data with datetime index
        value_column : str
            Column to analyze
            
        Returns
        -------
        pd.DataFrame
            Daily profile with hour as index
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
            
        # Extract hour and calculate mean
        hourly_profile = df.groupby(df.index.hour)[value_column].agg(['mean', 'std', 'min', 'max'])
        hourly_profile.index.name = 'hour'
        
        logger.info(f"Created daily profile for {value_column}")
        return hourly_profile
    
    def identify_peak_hours(self, df: pd.DataFrame, 
                          value_column: str,
                          percentile: float = 90) -> List[int]:
        """
        Identify peak demand hours.
        
        Parameters
        ----------
        df : pd.DataFrame
            Time series data
        value_column : str
            Column to analyze
        percentile : float
            Percentile threshold for peak identification
            
        Returns
        -------
        list
            Hours identified as peak periods
        """
        daily_profile = self.create_daily_profiles(df, value_column)
        threshold = daily_profile['mean'].quantile(percentile / 100)
        peak_hours = daily_profile[daily_profile['mean'] >= threshold].index.tolist()
        
        logger.info(f"Identified peak hours: {peak_hours}")
        return peak_hours
    
    def calculate_load_factor(self, df: pd.DataFrame, 
                            power_column: str) -> float:
        """
        Calculate load factor (average load / peak load).
        
        Parameters
        ----------
        df : pd.DataFrame
            Time series data
        power_column : str
            Power column name
            
        Returns
        -------
        float
            Load factor
        """
        avg_load = df[power_column].mean()
        peak_load = df[power_column].max()
        
        if peak_load > 0:
            load_factor = avg_load / peak_load
        else:
            load_factor = 0
            
        logger.info(f"Load factor: {load_factor:.3f}")
        return load_factor