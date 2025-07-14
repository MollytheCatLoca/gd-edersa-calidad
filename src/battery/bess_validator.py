"""
BESS Energy Validator
Validates energy delivery compliance for different BESS technologies
Ensures strategies meet minimum efficiency requirements
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class BESSValidator:
    """
    Validates BESS operation results against energy delivery requirements.
    Different technologies have different efficiency thresholds.
    
    Note: All power values are in MW and all energy values are in MWh.
    Time step (dt) is applied as multiplicator to convert power to energy.
    """
    
    # Technology specifications with round-trip efficiency and max losses
    TECHNOLOGY_SPECS = {
        'standard': {
            'name': 'Standard (Lead-Acid/Old Li-ion)',
            'η_rt': 0.90,
            'max_loss': 0.10,
            'description': 'Tecnología estándar, 90% eficiencia round-trip'
        },
        'modern_lfp': {
            'name': 'Modern LFP (LiFePO4)',
            'η_rt': 0.93,
            'max_loss': 0.07,
            'description': 'Baterías LFP modernas, 93% eficiencia round-trip'
        },
        'premium': {
            'name': 'Premium (LTO/Advanced)',
            'η_rt': 0.95,
            'max_loss': 0.05,
            'description': 'Tecnología premium, 95% eficiencia round-trip'
        }
    }
    
    def __init__(self, technology: str = 'modern_lfp'):
        """
        Initialize validator with specific technology.
        
        Args:
            technology: BESS technology type ('standard', 'modern_lfp', 'premium')
        """
        if technology not in self.TECHNOLOGY_SPECS:
            logger.warning(f"Unknown technology '{technology}', defaulting to 'modern_lfp'")
            technology = 'modern_lfp'
            
        self.technology = technology
        self.tech_spec = self.TECHNOLOGY_SPECS[technology]
        self.min_efficiency = self.tech_spec['η_rt']
        self.max_loss = self.tech_spec['max_loss']
        
        # Set logger level to INFO only if not already configured
        if logger.level == 0 or logger.level == logging.NOTSET:
            logger.setLevel(logging.INFO)
        
        logger.info(f"BESSValidator initialized for {self.tech_spec['name']}")
        logger.info(f"Minimum efficiency: {self.min_efficiency:.1%}, Max losses: {self.max_loss:.1%}")
    
    def validate_energy_delivery(self, 
                               solar_energy: float,
                               delivered_energy: float,
                               curtailed_energy: float = 0) -> Dict[str, Any]:
        """
        Validate if energy delivery meets efficiency requirements.
        
        Args:
            solar_energy: Total solar energy generated (MWh)
            delivered_energy: Energy delivered to grid (MWh)
            curtailed_energy: Energy curtailed/wasted (MWh)
            
        Returns:
            Dictionary with validation results and suggestions
        """
        # Calculate actual efficiency
        if solar_energy <= 0:
            return {
                'valid': False,
                'reason': 'No hay generación solar para validar',
                'efficiency': 0,
                'losses': 0,
                'metrics': {}
            }
        
        # Energy balance with protection against negative losses
        losses = max(0, solar_energy - delivered_energy - curtailed_energy)
        actual_efficiency = delivered_energy / solar_energy
        loss_fraction = max(0, losses / solar_energy)
        
        # Validate against technology limits
        # Check both efficiency and absolute loss fraction
        is_valid = actual_efficiency >= self.min_efficiency
        is_valid &= loss_fraction <= self.max_loss
        
        # Prepare result
        result = {
            'valid': is_valid,
            'efficiency': actual_efficiency,
            'losses': losses,
            'loss_fraction': loss_fraction,
            'curtailed': curtailed_energy,
            'technology': self.technology,
            'metrics': {
                'solar_energy_mwh': round(solar_energy, 2),
                'delivered_energy_mwh': round(delivered_energy, 2),
                'losses_mwh': round(losses, 2),
                'curtailed_mwh': round(curtailed_energy, 2),
                'efficiency_percent': round(actual_efficiency * 100, 1),
                'loss_percent': round(loss_fraction * 100, 1)
            }
        }
        
        # Add reason and suggestion if not valid
        if not is_valid:
            reasons = []
            if actual_efficiency < self.min_efficiency:
                reasons.append(f"Eficiencia {actual_efficiency:.1%} < {self.min_efficiency:.1%}")
            if loss_fraction > self.max_loss:
                reasons.append(f"Pérdidas {loss_fraction:.1%} > {self.max_loss:.1%} máximo")
            
            result['reason'] = f"{' y '.join(reasons)} para {self.tech_spec['name']}"
            result['suggestion'] = self._generate_suggestion(
                solar_energy, delivered_energy, losses, curtailed_energy
            )
        else:
            result['reason'] = f"Cumple con eficiencia mínima de {self.min_efficiency:.1%}"
            
        return result
    
    def validate_strategy_result(self, 
                               solar_profile: np.ndarray,
                               bess_result: Dict[str, np.ndarray],
                               strategy_name: str,
                               bess_config: Dict[str, float],
                               dt: float = 1.0) -> Dict[str, Any]:
        """
        Validate complete BESS operation results.
        
        Args:
            solar_profile: Solar generation profile (MW)
            bess_result: BESS simulation results dictionary
            strategy_name: Name of the strategy used
            bess_config: BESS configuration (power_mw, duration_h)
            dt: Time step in hours (default 1.0)
            
        Returns:
            Comprehensive validation results
        """
        # Extract arrays
        grid_power = bess_result.get('grid_power', np.zeros_like(solar_profile))
        battery_power = bess_result.get('battery_power', np.zeros_like(solar_profile))
        solar_curtailed = bess_result.get('solar_curtailed', np.zeros_like(solar_profile))
        
        # Check for NaN values from failed strategies
        if np.isnan(grid_power).any() or np.isnan(battery_power).any() or np.isnan(solar_curtailed).any():
            raise ValueError('NaN values in strategy results - strategy execution failed')
        
        # Calculate energies using timestep
        solar_energy = np.sum(solar_profile) * dt
        delivered_energy = np.sum(grid_power) * dt
        curtailed_energy = np.sum(solar_curtailed) * dt
        
        # Convert to daily values if dealing with annual profiles
        days_in_profile = len(solar_profile) * dt / 24
        if days_in_profile > 300:  # Annual profile
            daily_divisor = 365
            solar_energy_daily = solar_energy / daily_divisor
            delivered_energy_daily = delivered_energy / daily_divisor
            curtailed_energy_daily = curtailed_energy / daily_divisor
        else:
            # Already daily or short period - use as is
            solar_energy_daily = solar_energy
            delivered_energy_daily = delivered_energy
            curtailed_energy_daily = curtailed_energy
        
        # Basic energy validation - use daily values for display
        energy_validation = self.validate_energy_delivery(
            solar_energy_daily, delivered_energy_daily, curtailed_energy_daily
        )
        
        # Additional strategy-specific validations
        # Pass dt for proper ramp rate calculations
        bess_config_with_dt = {**bess_config, 'dt': dt}
        strategy_metrics = self._validate_strategy_specifics(
            solar_profile, bess_result, strategy_name, bess_config_with_dt
        )
        
        # Combine results
        result = {
            **energy_validation,
            'strategy': strategy_name,
            'bess_config': bess_config_with_dt,  # Return config with dt included
            'strategy_metrics': strategy_metrics,
            'dt': dt  # Also add dt as top-level key for clarity
        }
        
        # Fix efficiency calculation to use total values (not daily)
        # but keep metrics in daily values for display
        if solar_energy > 0:
            result['efficiency'] = delivered_energy / solar_energy
            # Recalculate validity based on true efficiency
            result['valid'] = result['efficiency'] >= self.min_efficiency
            if not result['valid']:
                result['reason'] = (
                    f"Eficiencia {result['efficiency']:.1%} < {self.min_efficiency:.1%} "
                    f"requerida para {self.technology}"
                )
            else:
                result['reason'] = f"Cumple con eficiencia mínima de {self.min_efficiency:.1%}"
        
        # ML-ready features
        result['ml_features'] = self._extract_ml_features(
            solar_profile, bess_result, strategy_name, bess_config, dt
        )
        
        return result
    
    def _generate_suggestion(self, solar_energy: float, delivered_energy: float,
                           losses: float, curtailed_energy: float) -> str:
        """Generate improvement suggestions based on validation failure."""
        
        suggestions = []
        
        # Check if losses are too high
        if losses > solar_energy * self.max_loss:
            excess_losses = losses - (solar_energy * self.max_loss)
            suggestions.append(
                f"Reducir pérdidas en {excess_losses:.1f} MWh "
                f"({excess_losses/solar_energy*100:.1f}%)"
            )
            
        # Check if there's significant curtailment
        if curtailed_energy > solar_energy * 0.02:  # More than 2%
            suggestions.append(
                f"Evitar curtailment de {curtailed_energy:.1f} MWh "
                f"({curtailed_energy/solar_energy*100:.1f}%)"
            )
            
        # Suggest BESS sizing
        required_efficiency = self.min_efficiency
        required_delivery = solar_energy * required_efficiency
        shortfall = required_delivery - delivered_energy
        
        if shortfall > 0:
            # Estimate BESS size needed
            # Assuming we need to store the shortfall with some margin
            suggested_energy = shortfall / 0.9  # Account for BESS efficiency
            suggested_power = suggested_energy / 4  # Assume 4h duration
            
            # Estimate solar peak from daily energy (assuming 6 effective hours)
            estimated_solar_peak = solar_energy / 6
            min_power = 0.1 * estimated_solar_peak
            suggested_power = max(suggested_power, min_power)
            
            suggestions.append(
                f"Aumentar BESS a ~{suggested_power:.1f} MW / {suggested_energy:.1f} MWh "
                f"para alcanzar {required_efficiency:.0%} eficiencia"
            )
            
        # Technology upgrade suggestion
        if self.technology != 'premium':
            next_tech = 'modern_lfp' if self.technology == 'standard' else 'premium'
            next_spec = self.TECHNOLOGY_SPECS[next_tech]
            potential_efficiency = delivered_energy / solar_energy / self.min_efficiency * next_spec['η_rt']
            
            if potential_efficiency >= next_spec['η_rt']:
                suggestions.append(
                    f"Considerar tecnología {next_spec['name']} "
                    f"para alcanzar {next_spec['η_rt']:.0%} eficiencia"
                )
        
        return " | ".join(suggestions) if suggestions else "Optimizar parámetros de la estrategia"
    
    def _validate_strategy_specifics(self, solar_profile: np.ndarray,
                                   bess_result: Dict[str, np.ndarray],
                                   strategy_name: str,
                                   bess_config: Dict[str, Any]) -> Dict[str, float]:
        """Validate strategy-specific requirements.
        
        Note: bess_config may contain 'dt' for timestep-aware calculations.
        """
        
        metrics = {}
        grid_power = bess_result.get('grid_power', solar_profile)
        battery_power = bess_result.get('battery_power', np.zeros_like(solar_profile))
        
        if strategy_name == 'cap_shaving':
            # Check if cap was respected
            cap_limit = bess_config.get('cap_mw', None)
            if cap_limit is not None:
                violations = np.sum(grid_power > cap_limit * 1.01)  # 1% tolerance
                max_exceed = np.max(grid_power) - cap_limit if np.max(grid_power) > cap_limit else 0
                metrics['cap_violations'] = violations
                metrics['cap_compliance'] = 100 * (1 - violations / len(grid_power))
                metrics['max_cap_exceed_mw'] = max_exceed
            else:
                # No cap parameter provided - omit metric for ML compatibility
                # Don't add cap_compliance key at all
                metrics['cap_note'] = 'No cap_mw parameter provided'
            
        elif strategy_name == 'ramp_limit':
            # Check ramp rate compliance
            ramp_limit = bess_config.get('ramp_mw_per_hour', 1.0)
            dt = bess_config.get('dt', 1.0)  # Get timestep for proper scaling
            # Scale ramps to MW/hour
            ramps = np.abs(np.diff(grid_power)) / dt
            # Tolerance should not scale with dt
            violations = np.sum(ramps > ramp_limit * 1.01)
            max_ramp = np.max(ramps) if len(ramps) > 0 else 0
            metrics['ramp_violations'] = violations
            metrics['ramp_compliance'] = 100 * (1 - violations / len(ramps)) if len(ramps) > 0 else 100
            metrics['max_ramp_mw_per_hour'] = max_ramp
            metrics['max_ramp_exceed_mw_per_hour'] = max(0, max_ramp - ramp_limit)
            
        elif strategy_name == 'firm_capacity':
            # Check firm power delivery
            firm_hours = bess_config.get('firm_hours', [])
            firm_power = bess_config.get('firm_mw', 0)
            if firm_hours and firm_power > 0:  # Only check if there's a real constraint
                firm_delivery = [grid_power[h] for h in firm_hours if h < len(grid_power)]
                metrics['firm_delivery_avg'] = np.mean(firm_delivery) if firm_delivery else 0
                metrics['firm_compliance'] = 100 * np.sum(np.array(firm_delivery) >= firm_power) / len(firm_delivery) if firm_delivery else 0
            elif firm_hours:
                # Have hours but no power requirement
                metrics['firm_note'] = 'No firm power constraint (firm_mw=0)'
                
        # Common metrics for all strategies with protection against division by zero
        solar_peak = max(np.max(solar_profile), 1e-6)
        solar_std = max(np.std(solar_profile), 1e-6)
        metrics['peak_reduction'] = 100 * (1 - np.max(grid_power) / solar_peak)
        metrics['variability_reduction'] = 100 * (1 - np.std(grid_power) / solar_std)
        
        # BESS utilization
        bess_active_hours = np.sum(np.abs(battery_power) > 0.01)
        metrics['bess_utilization'] = 100 * bess_active_hours / len(battery_power)
        
        # Capacity factor
        if 'capacity_mwh' in bess_config and bess_config['capacity_mwh'] > 0:
            total_throughput = np.sum(np.abs(battery_power))
            metrics['daily_cycles'] = total_throughput / (2 * bess_config['capacity_mwh'])
        
        return metrics
    
    def _extract_ml_features(self, solar_profile: np.ndarray,
                           bess_result: Dict[str, np.ndarray],
                           strategy_name: str,
                           bess_config: Dict[str, float],
                           dt: float = 1.0) -> Dict[str, float]:
        """Extract features for ML training.
        
        Note: dt is used to convert power profiles to energy values.
        """
        
        # Normalize solar profile
        solar_peak = np.max(solar_profile) if np.max(solar_profile) > 0 else 1
        solar_normalized = solar_profile / solar_peak
        
        # Resample to 24 hourly values if needed
        if len(solar_normalized) > 24:
            # Use array_split for robust resampling even if not exact multiple
            chunks = np.array_split(solar_normalized, 24)
            solar_normalized = np.array([chunk.mean() for chunk in chunks])
        elif len(solar_normalized) < 24:
            # Pad by repeating last value (avoids artificial zeros)
            padding_needed = 24 - len(solar_normalized)
            last_value = solar_normalized[-1] if len(solar_normalized) > 0 else 0
            solar_normalized = np.pad(solar_normalized, (0, padding_needed), mode='constant', constant_values=last_value)
        
        features = {
            # Solar characteristics
            'solar_peak_mw': solar_peak,
            'solar_mean_mw': np.mean(solar_profile),
            'solar_std_mw': np.std(solar_profile),
            'solar_energy_mwh': np.sum(solar_profile) * dt,
            
            # BESS characteristics
            'bess_power_mw': bess_config.get('power_mw', 0),
            'bess_duration_h': bess_config.get('duration_h', 0),
            'bess_capacity_mwh': bess_config.get('capacity_mwh', 0),
            # Use percentile 80 for more stable ratio (avoids outliers)
            'bess_solar_ratio': bess_config.get('power_mw', 0) / (np.percentile(solar_profile[solar_profile > 0], 80) if np.any(solar_profile > 0) else 1e-3),
            
            # Technology encoding
            'tech_standard': 1 if self.technology == 'standard' else 0,
            'tech_modern': 1 if self.technology == 'modern_lfp' else 0,
            'tech_premium': 1 if self.technology == 'premium' else 0,
            
            # Strategy encoding
            'strategy_cap': 1 if strategy_name == 'cap_shaving' else 0,
            'strategy_flat': 1 if strategy_name == 'flat_day' else 0,
            'strategy_shift': 1 if strategy_name == 'night_shift' else 0,
            'strategy_ramp': 1 if strategy_name == 'ramp_limit' else 0,
            
            # Solar profile shape (24 hourly values normalized)
            **{f'solar_h{i}': solar_normalized[i] if i < len(solar_normalized) else 0 
               for i in range(24)}
        }
        
        return features
    
    def suggest_bess_sizing(self, solar_profile: np.ndarray,
                          target_efficiency: float = None,
                          dt: float = 1.0) -> Dict[str, float]:
        """
        Suggest BESS sizing to meet efficiency requirements.
        
        Args:
            solar_profile: Solar generation profile (MW)
            target_efficiency: Target efficiency (defaults to technology minimum)
            dt: Time step in hours (default 1.0)
            
        Returns:
            Suggested BESS configuration
        """
        if target_efficiency is None:
            target_efficiency = self.min_efficiency
            
        solar_energy = np.sum(solar_profile) * dt
        solar_peak = np.max(solar_profile)
        
        # Simple heuristic for BESS sizing
        # Assume we need to shift 20% of energy with some losses
        energy_to_shift = solar_energy * 0.2
        bess_efficiency = np.sqrt(self.min_efficiency)  # One-way efficiency
        
        # Typical configurations
        suggestions = []
        
        # Option 1: High power, short duration (for ramp control)
        suggestions.append({
            'power_mw': round(solar_peak * 0.3, 1),
            'duration_h': 2,
            'capacity_mwh': round(solar_peak * 0.3 * 2, 1),
            'use_case': 'Control de rampas y picos'
        })
        
        # Option 2: Medium power, medium duration (for time shift)
        suggestions.append({
            'power_mw': round(solar_peak * 0.5, 1),
            'duration_h': 4,
            'capacity_mwh': round(solar_peak * 0.5 * 4, 1),
            'use_case': 'Time-shift y arbitraje'
        })
        
        # Option 3: Lower power, long duration (for firm capacity)
        suggestions.append({
            'power_mw': round(solar_peak * 0.3, 1),
            'duration_h': 6,
            'capacity_mwh': round(solar_peak * 0.3 * 6, 1),
            'use_case': 'Capacidad firme nocturna'
        })
        
        return {
            'solar_peak_mw': solar_peak,
            'solar_energy_daily_mwh': solar_energy,
            'target_efficiency': target_efficiency,
            'technology': self.technology,
            'suggestions': suggestions,
            'note': 'All power in MW, all energy in MWh'
        }


def calculate_zero_curtail_bess(solar_profile: np.ndarray,
                              strategy: str = 'cap',
                              target_params: Dict = None,
                              technology: str = 'modern_lfp',
                              dt: float = 1.0) -> Dict[str, float]:
    """
    Calculate minimum BESS size for zero curtailment.
    Based on Section 9 of the reference document.
    
    Note: All power values in MW, energy values in MWh.
    Assumes solar_profile contains only positive values (no imports).
    
    Args:
        solar_profile: Solar generation profile (MW)
        strategy: 'cap' or 'flat'
        target_params: Strategy parameters (cap_mw or flat_mw)
        technology: BESS technology for efficiency
        dt: Time step in hours (default 1.0)
        
    Returns:
        Required BESS configuration
    """
    # Protect against None target_params
    target_params = target_params or {}
    # Get technology efficiency
    tech_spec = BESSValidator.TECHNOLOGY_SPECS.get(technology, BESSValidator.TECHNOLOGY_SPECS['modern_lfp'])
    η_rt = tech_spec['η_rt']
    η_one_way = np.sqrt(η_rt)
    
    # Use provided dt instead of hardcoding
    
    # Calculate reference profile based on strategy
    if strategy == 'cap':
        cap_mw = target_params.get('cap_mw', np.max(solar_profile) * 0.7)
        p_ref = np.minimum(solar_profile, cap_mw)
    elif strategy == 'flat':
        flat_mw = target_params.get('flat_mw', np.mean(solar_profile))
        start_h = target_params.get('start_hour', 8)
        end_h = target_params.get('end_hour', 18)
        p_ref = np.zeros_like(solar_profile)
        p_ref[start_h:end_h] = flat_mw
    else:
        # Unknown strategy - log warning
        logger.warning(f"Strategy '{strategy}' not recognized, using solar profile as-is")
        p_ref = solar_profile  # No modification
    
    # Calculate power difference
    delta_p = solar_profile - p_ref
    
    # Integrate to find energy requirements
    e_cumsum = 0
    e_max = 0  # Maximum energy needed
    p_charge_max = 0  # Maximum charge power
    p_discharge_max = 0  # Maximum discharge power
    
    for dp in delta_p:
        e_cumsum += dp * dt
        # Only clip to 0 if we don't allow negative energy (normal case)
        # For strategies that might export, this would need modification
        if e_cumsum < 0:
            e_cumsum = 0  # Reset to zero, can't go negative
        e_max = max(e_max, e_cumsum)
        
        if dp > 0:  # Charging
            p_charge_max = max(p_charge_max, dp)
        else:  # Discharging
            p_discharge_max = max(p_discharge_max, -dp)
    
    # BESS requirements
    # Account for efficiency losses in power sizing
    # Note: Only charge power is penalized by efficiency in this conservative approach
    p_charge_required = p_charge_max / η_one_way  # Need more power to overcome charge losses
    p_discharge_required = p_discharge_max  # Discharge power is direct (not penalized)
    p_bess_required = max(p_charge_required, p_discharge_required)
    e_bess_required = e_max / η_one_way  # Account for charging losses
    
    # Add 10% margin for real-world variations
    p_bess_required *= 1.1
    e_bess_required *= 1.1
    
    # Calculate duration
    duration_h = e_bess_required / p_bess_required if p_bess_required > 0 else 0
    
    return {
        'power_mw': round(p_bess_required, 2),
        'duration_h': round(duration_h, 1),
        'capacity_mwh': round(e_bess_required, 2),
        'technology': technology,
        'efficiency': η_rt,
        'strategy': strategy,
        'daily_cycles': e_max * 2 / e_bess_required if e_bess_required > 0 else 0,
        'note': 'Conservative sizing: charge power includes efficiency penalty'
    }


# Configure logging only when run as main
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)