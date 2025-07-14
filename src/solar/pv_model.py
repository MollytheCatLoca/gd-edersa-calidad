"""
PV Generation Model
Fase 4 - Modelado de generación fotovoltaica
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class PVModel:
    """Model for calculating PV generation from solar resource data
    
    Based on simplified but realistic model:
    P = GHI × A × η_panel × η_inv × (1 - γ(T - 25°C)) × (1 - losses)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize PV model with system parameters
        
        Args:
            config: Optional configuration dictionary
        """
        if config is None:
            config = {}
        
        # Panel parameters
        self.panel_efficiency = config.get('panel_efficiency', 0.19)  # 19% for monocrystalline
        self.temp_coefficient = config.get('temp_coefficient', -0.004)  # -0.4%/°C
        self.noct = config.get('noct', 45)  # Nominal Operating Cell Temperature
        
        # System parameters
        self.inverter_efficiency = config.get('inverter_efficiency', 0.97)  # 97%
        self.dc_losses = config.get('dc_losses', 0.02)  # 2% DC wiring losses
        self.ac_losses = config.get('ac_losses', 0.01)  # 1% AC losses
        self.soiling_losses = config.get('soiling_losses', 0.03)  # 3% soiling
        self.shading_losses = config.get('shading_losses', 0.02)  # 2% shading
        self.mismatch_losses = config.get('mismatch_losses', 0.02)  # 2% mismatch
        self.availability = config.get('availability', 0.98)  # 98% availability
        
        # Installation parameters
        self.tilt = config.get('tilt', None)  # If None, use latitude
        self.azimuth = config.get('azimuth', 0)  # 0 = North (Southern hemisphere)
        
        # Calculate total losses
        self.total_losses = (
            self.dc_losses + self.ac_losses + self.soiling_losses + 
            self.shading_losses + self.mismatch_losses + (1 - self.availability)
        )
        
        logger.info(f"PV Model initialized with total losses: {self.total_losses:.1%}")
    
    def calculate_power(self, ghi: Union[float, np.ndarray, pd.Series], 
                       temperature: Union[float, np.ndarray, pd.Series],
                       wind_speed: Optional[Union[float, np.ndarray, pd.Series]] = None,
                       capacity_mw: float = 1.0) -> Union[float, np.ndarray, pd.Series]:
        """Calculate PV power output
        
        Args:
            ghi: Global Horizontal Irradiance (W/m²)
            temperature: Ambient temperature (°C)
            wind_speed: Wind speed (m/s), optional for better temperature modeling
            capacity_mw: Installed capacity in MW
            
        Returns:
            Power output in MW
        """
        # Calculate cell temperature
        if wind_speed is not None:
            # Ross model with wind correction
            temp_cell = temperature + (self.noct - 20) * ghi / 800 * (1 - wind_speed / 8)
        else:
            # Simple NOCT model
            temp_cell = temperature + (self.noct - 20) * ghi / 800
        
        # Temperature derating
        temp_derate = 1 + self.temp_coefficient * (temp_cell - 25)
        temp_derate = np.maximum(temp_derate, 0.5)  # Limit to 50% minimum
        
        # Power calculation (kW per m²)
        power_per_m2 = (
            ghi / 1000 *  # Convert to kW/m²
            self.panel_efficiency *
            self.inverter_efficiency *
            temp_derate *
            (1 - self.total_losses)
        )
        
        # Scale to installed capacity
        # Assume ~5000 m² per MW (200 W/m² panels)
        area_per_mw = 5000  # m²/MW
        power_mw = power_per_m2 * area_per_mw * capacity_mw / 1000
        
        # Clip negative values
        if isinstance(power_mw, (np.ndarray, pd.Series)):
            power_mw = np.maximum(power_mw, 0)
        else:
            power_mw = max(power_mw, 0)
        
        return power_mw
    
    def generate_profile(self, solar_data: pd.DataFrame, capacity_mw: float = 1.0) -> pd.DataFrame:
        """Generate PV generation profile from solar resource data
        
        Args:
            solar_data: DataFrame with columns 'GHI', 'Temperature', optionally 'WindSpeed'
            capacity_mw: Installed capacity in MW
            
        Returns:
            DataFrame with PV generation profile
        """
        # Check required columns
        required_cols = ['GHI', 'Temperature']
        if not all(col in solar_data.columns for col in required_cols):
            raise ValueError(f"Solar data must contain columns: {required_cols}")
        
        # Calculate power
        wind_speed = solar_data.get('WindSpeed', None)
        power = self.calculate_power(
            solar_data['GHI'],
            solar_data['Temperature'],
            wind_speed,
            capacity_mw
        )
        
        # Create output dataframe
        result = pd.DataFrame(index=solar_data.index)
        result['power_mw'] = power
        result['ghi'] = solar_data['GHI']
        result['temperature'] = solar_data['Temperature']
        
        # Add capacity factor
        result['capacity_factor'] = result['power_mw'] / capacity_mw
        
        # Add time-based features
        if isinstance(result.index, pd.DatetimeIndex):
            result['hour'] = result.index.hour
            result['month'] = result.index.month
            result['dayofyear'] = result.index.dayofyear
        
        return result
    
    def calculate_annual_metrics(self, profile: pd.DataFrame, capacity_mw: float = 1.0) -> Dict:
        """Calculate annual performance metrics
        
        Args:
            profile: Generation profile DataFrame
            capacity_mw: Installed capacity in MW
            
        Returns:
            Dictionary with annual metrics
        """
        # Energy generation
        hours_per_year = len(profile)
        energy_mwh = profile['power_mw'].sum()
        
        # Capacity factor
        capacity_factor = energy_mwh / (capacity_mw * hours_per_year)
        
        # Peak output
        peak_output = profile['power_mw'].max()
        
        # Operating hours (> 5% capacity)
        operating_hours = (profile['power_mw'] > 0.05 * capacity_mw).sum()
        
        # Monthly generation
        monthly_energy = profile.groupby(profile.index.month)['power_mw'].sum()
        
        # Seasonal variation
        summer_months = [12, 1, 2]  # Southern hemisphere
        winter_months = [6, 7, 8]
        
        summer_energy = monthly_energy[monthly_energy.index.isin(summer_months)].sum()
        winter_energy = monthly_energy[monthly_energy.index.isin(winter_months)].sum()
        seasonal_ratio = summer_energy / winter_energy if winter_energy > 0 else np.inf
        
        metrics = {
            'annual_energy_mwh': float(energy_mwh),
            'capacity_factor': float(capacity_factor),
            'peak_output_mw': float(peak_output),
            'operating_hours': int(operating_hours),
            'equivalent_hours': float(energy_mwh / capacity_mw),
            'seasonal_ratio': float(seasonal_ratio),
            'monthly_energy_mwh': monthly_energy.to_dict()
        }
        
        return metrics
    
    def calculate_degradation(self, year: int, degradation_rate: float = 0.005) -> float:
        """Calculate performance degradation factor
        
        Args:
            year: Year of operation (1 = first year)
            degradation_rate: Annual degradation rate (default 0.5%/year)
            
        Returns:
            Degradation factor (1.0 for year 1, decreasing thereafter)
        """
        return (1 - degradation_rate) ** (year - 1)
    
    def optimize_tilt(self, solar_data: pd.DataFrame, latitude: float,
                     tilt_range: Tuple[float, float] = (20, 50)) -> Dict:
        """Find optimal tilt angle for maximum annual generation
        
        Args:
            solar_data: Solar resource data
            latitude: Site latitude in degrees
            tilt_range: Range of tilt angles to test
            
        Returns:
            Dictionary with optimal tilt and generation results
        """
        # Test different tilt angles
        tilts = np.linspace(tilt_range[0], tilt_range[1], 31)
        results = []
        
        for tilt in tilts:
            # Approximate tilt effect on GHI (simplified)
            # In reality, would need to separate GHI into direct and diffuse
            tilt_factor = 1 + 0.1 * np.cos(np.radians(abs(latitude) - tilt))
            
            # Adjust GHI
            adjusted_ghi = solar_data['GHI'] * tilt_factor
            
            # Calculate generation
            power = self.calculate_power(
                adjusted_ghi,
                solar_data['Temperature'],
                solar_data.get('WindSpeed', None),
                1.0
            )
            
            annual_energy = power.sum()
            results.append({
                'tilt': tilt,
                'annual_energy_mwh': annual_energy,
                'tilt_factor': tilt_factor
            })
        
        # Find optimal
        results_df = pd.DataFrame(results)
        optimal_idx = results_df['annual_energy_mwh'].idxmax()
        optimal = results_df.iloc[optimal_idx].to_dict()
        
        # Rule of thumb comparison
        rule_of_thumb_tilt = abs(latitude)
        
        return {
            'optimal_tilt': optimal['tilt'],
            'optimal_energy_mwh': optimal['annual_energy_mwh'],
            'rule_of_thumb_tilt': rule_of_thumb_tilt,
            'all_results': results_df
        }
    
    def estimate_curtailment(self, profile: pd.DataFrame, grid_limit_mw: float) -> Dict:
        """Estimate curtailed energy due to grid limitations
        
        Args:
            profile: Generation profile
            grid_limit_mw: Maximum injection limit
            
        Returns:
            Dictionary with curtailment statistics
        """
        # Calculate curtailed power
        curtailed_power = np.maximum(profile['power_mw'] - grid_limit_mw, 0)
        
        # Curtailment statistics
        total_curtailed_mwh = curtailed_power.sum()
        total_generated_mwh = profile['power_mw'].sum()
        curtailment_rate = total_curtailed_mwh / total_generated_mwh if total_generated_mwh > 0 else 0
        
        # Hours with curtailment
        curtailment_hours = (curtailed_power > 0).sum()
        
        # Peak curtailment
        peak_curtailment = curtailed_power.max()
        
        # Curtailment by month
        monthly_curtailment = curtailed_power.groupby(profile.index.month).sum()
        
        return {
            'total_curtailed_mwh': float(total_curtailed_mwh),
            'curtailment_rate': float(curtailment_rate),
            'curtailment_hours': int(curtailment_hours),
            'peak_curtailment_mw': float(peak_curtailment),
            'monthly_curtailment_mwh': monthly_curtailment.to_dict(),
            'avoided_with_bess_mwh': float(total_curtailed_mwh * 0.85)  # Assume 85% BESS efficiency
        }


if __name__ == "__main__":
    # Test the PV model
    pv = PVModel()
    
    # Test single calculation
    ghi = 800  # W/m²
    temp = 25  # °C
    power = pv.calculate_power(ghi, temp, capacity_mw=1.0)
    print(f"Power output at {ghi} W/m², {temp}°C: {power:.3f} MW")
    
    # Test with array
    hours = np.arange(24)
    ghi_profile = 1000 * np.maximum(0, np.sin(np.pi * (hours - 6) / 12))
    temp_profile = 20 + 10 * np.sin(np.pi * (hours - 6) / 12)
    
    power_profile = pv.calculate_power(ghi_profile, temp_profile, capacity_mw=2.0)
    daily_energy = power_profile.sum()
    
    print(f"\nDaily energy for 2 MW plant: {daily_energy:.1f} MWh")
    print(f"Peak output: {power_profile.max():.2f} MW")
    print(f"Capacity factor: {daily_energy / (2 * 24):.1%}")