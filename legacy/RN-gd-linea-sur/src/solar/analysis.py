"""
Complementarity Analysis between Solar Generation and Demand
Fase 4 - Análisis de complementariedad solar-demanda
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ComplementarityAnalyzer:
    """Analyzes complementarity between solar generation and electrical demand"""
    
    def __init__(self):
        """Initialize the analyzer"""
        pass
    
    def analyze_complementarity(self, solar_profile: pd.DataFrame, 
                              demand_profile: pd.DataFrame) -> Dict:
        """Analyze solar-demand complementarity
        
        Args:
            solar_profile: DataFrame with 'power_mw' column
            demand_profile: DataFrame with 'p_total' column
            
        Returns:
            Dictionary with complementarity metrics
        """
        # Align timestamps
        df = pd.DataFrame()
        df['solar'] = solar_profile['power_mw']
        df['demand'] = demand_profile['p_total']
        df = df.dropna()
        
        # Calculate metrics
        results = {
            'direct_consumption': self._calculate_direct_consumption(df),
            'curtailment': self._calculate_curtailment(df),
            'deficit': self._calculate_deficit(df),
            'bess_requirements': self._calculate_bess_requirements(df)
        }
        
        return results
    
    def _calculate_direct_consumption(self, df: pd.DataFrame) -> Dict:
        """Calculate energy consumed directly from solar"""
        direct = np.minimum(df['solar'], df['demand'])
        
        return {
            'energy_mwh': float(direct.sum()),
            'percentage': float(direct.sum() / df['solar'].sum() * 100)
        }
    
    def _calculate_curtailment(self, df: pd.DataFrame) -> Dict:
        """Calculate curtailed solar energy"""
        curtailed = np.maximum(df['solar'] - df['demand'], 0)
        
        return {
            'energy_mwh': float(curtailed.sum()),
            'percentage': float(curtailed.sum() / df['solar'].sum() * 100),
            'hours': int((curtailed > 0).sum())
        }
    
    def _calculate_deficit(self, df: pd.DataFrame) -> Dict:
        """Calculate energy deficit when solar < demand"""
        deficit = np.maximum(df['demand'] - df['solar'], 0)
        
        return {
            'energy_mwh': float(deficit.sum()),
            'percentage': float(deficit.sum() / df['demand'].sum() * 100),
            'hours': int((deficit > 0).sum())
        }
    
    def _calculate_bess_requirements(self, df: pd.DataFrame) -> Dict:
        """Calculate BESS requirements for different coverage levels"""
        curtailed = np.maximum(df['solar'] - df['demand'], 0)
        
        # Daily analysis
        daily_curtailed = curtailed.resample('D').sum()
        
        return {
            'coverage_80pct_mwh': float(daily_curtailed.quantile(0.8)),
            'coverage_90pct_mwh': float(daily_curtailed.quantile(0.9)),
            'coverage_95pct_mwh': float(daily_curtailed.quantile(0.95)),
            'max_daily_mwh': float(daily_curtailed.max())
        }