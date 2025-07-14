"""
BESS Model V2 - Enhanced with technologies and topologies
Supports different BESS technologies with realistic efficiencies
Implements validated strategies with energy balance
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
from .bess_validator import BESSValidator
from .bess_strategies import BESSStrategies
from .bess_strategies_v2 import BESSStrategiesV2

# Import centralized constants
try:
    from ...dashboard.pages.utils.constants import (
        BESS, BESS_TECHNOLOGIES, BESS_TOPOLOGIES,
        BESSTechnology, BESSTopology
    )
    CONSTANTS_AVAILABLE = True
except ImportError:
    # Fallback for when constants are not available
    CONSTANTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class BESSModel:
    """
    Enhanced BESS model with technology-specific parameters and topology support.
    """
    
    # Class constants - use centralized constants when available
    if CONSTANTS_AVAILABLE:
        CYCLE_ENERGY_THRESHOLD_MWH = BESS["CYCLE_ENERGY_THRESHOLD_MWH"]
        TECHNOLOGIES = BESS_TECHNOLOGIES
        TOPOLOGIES = BESS_TOPOLOGIES
    else:
        # Fallback constants when centralized constants are not available
        CYCLE_ENERGY_THRESHOLD_MWH = 0.01  # 10 kWh = 0.01 MWh threshold for cycle counting
        
        # Technology configurations
        TECHNOLOGIES = {
            'standard': {
                'η_charge': 0.949,      # sqrt(0.90)
                'η_discharge': 0.949,
                'η_roundtrip': 0.90,
                'soc_min': 0.20,        # 20% minimum (lead-acid friendly)
                'soc_max': 0.90,        # 90% maximum
                'c_rate_max': 0.5,      # Conservative C-rate
                'description': 'Standard technology (Lead-acid or old Li-ion)'
            },
            'modern_lfp': {
                'η_charge': 0.964,      # sqrt(0.93)
                'η_discharge': 0.964,
                'η_roundtrip': 0.93,
                'soc_min': 0.10,        # 10% minimum
                'soc_max': 0.95,        # 95% maximum
                'c_rate_max': 1.0,      # 1C typical for LFP
                'description': 'Modern LiFePO4 technology'
            },
            'premium': {
                'η_charge': 0.975,      # sqrt(0.95)
                'η_discharge': 0.975,
                'η_roundtrip': 0.95,
                'soc_min': 0.05,        # 5% minimum
                'soc_max': 0.95,        # 95% maximum
                'c_rate_max': 2.0,      # 2C for premium systems
                'description': 'Premium technology (LTO or advanced Li-ion)'
            }
        }
        
        # Topology configurations
        TOPOLOGIES = {
            'parallel_ac': {
                'efficiency_penalty': 0.00,  # No additional penalty
                'flexibility': 'high',
                'description': 'AC-coupled parallel configuration'
            },
            'series_dc': {
                'efficiency_penalty': 0.02,  # 2% penalty for DC-DC conversion
                'flexibility': 'medium',
                'description': 'DC-coupled series configuration'
            },
            'hybrid': {
                'efficiency_penalty': 0.01,  # 1% penalty
                'flexibility': 'high',
                'description': 'Hybrid AC/DC configuration'
            }
        }
    
    def __init__(self, 
                 power_mw: float,
                 duration_hours: float,
                 technology: str = 'modern_lfp',
                 topology: str = 'parallel_ac',
                 track_history: bool = True,
                 verbose: bool = True):
        """
        Initialize BESS with technology and topology specifications.
        
        Args:
            power_mw: Maximum charge/discharge power in MW
            duration_hours: Energy storage duration at rated power
            technology: BESS technology type
            topology: System topology configuration
            track_history: Whether to track operation history (disable for long simulations)
            verbose: Whether to log info messages (disable for ML training)
        """
        self.verbose = verbose
        # Validate inputs
        if power_mw <= 0 or duration_hours <= 0:
            raise ValueError("power_mw and duration_hours must be > 0")
            
        self.power_mw = power_mw
        self.duration_hours = duration_hours
        self.capacity_mwh = power_mw * duration_hours
        self.track_history = track_history
        
        # Validate and set technology
        if CONSTANTS_AVAILABLE:
            # Use enum validation when available
            try:
                if isinstance(technology, str):
                    # Try to convert string to enum
                    tech_enum = BESSTechnology(technology)
                    technology = tech_enum.value
                elif isinstance(technology, BESSTechnology):
                    technology = technology.value
            except ValueError:
                if self.verbose:
                    logger.warning(f"Unknown technology '{technology}', using 'modern_lfp'")
                technology = BESSTechnology.MODERN_LFP.value
        else:
            # Fallback validation
            if technology not in self.TECHNOLOGIES:
                if self.verbose:
                    logger.warning(f"Unknown technology '{technology}', using 'modern_lfp'")
                technology = 'modern_lfp'
        
        self.technology = technology
        self.tech_params = self.TECHNOLOGIES[technology].copy()
        
        # Validate and set topology
        if CONSTANTS_AVAILABLE:
            # Use enum validation when available
            try:
                if isinstance(topology, str):
                    # Try to convert string to enum
                    topo_enum = BESSTopology(topology)
                    topology = topo_enum.value
                elif isinstance(topology, BESSTopology):
                    topology = topology.value
            except ValueError:
                if self.verbose:
                    logger.warning(f"Unknown topology '{topology}', using 'parallel_ac'")
                topology = BESSTopology.PARALLEL_AC.value
        else:
            # Fallback validation
            if topology not in self.TOPOLOGIES:
                if self.verbose:
                    logger.warning(f"Unknown topology '{topology}', using 'parallel_ac'")
                topology = 'parallel_ac'
        
        self.topology = topology
        self.topo_params = self.TOPOLOGIES[topology].copy()
        
        # Apply topology penalty to efficiencies and freeze roundtrip
        penalty = self.topo_params['efficiency_penalty']
        self.tech_params['η_charge'] *= (1 - penalty)
        self.tech_params['η_discharge'] *= (1 - penalty)
        # Freeze effective roundtrip efficiency to avoid double penalties
        self.eff_roundtrip = self.tech_params['η_charge'] * self.tech_params['η_discharge']
        self.tech_params['η_roundtrip'] = self.eff_roundtrip
        
        # Apply topology penalty to power (for DC-coupled systems)
        # This reflects PCS (Power Conversion System) derating
        self.power_mw_eff = self.power_mw * (1 - penalty)
        
        # Initialize state
        self.reset()
        
        # Create validator with correct technology
        self.validator = BESSValidator(self.technology)
        
        # Calculate usable capacity
        self.usable_capacity_mwh = self.capacity_mwh * (
            self.tech_params['soc_max'] - self.tech_params['soc_min']
        )
        
        # Set logger level based on verbose flag
        if not self.verbose:
            logger.setLevel(logging.ERROR)
        
        # Log configuration only if verbose
        if self.verbose and logger.isEnabledFor(logging.INFO):
            logger.info(f"BESSModel initialized: {power_mw} MW / {duration_hours}h = {self.capacity_mwh} MWh")
            logger.info(f"Technology: {self.tech_params['description']}")
            logger.info(f"Topology: {self.topo_params['description']}")
            logger.info(f"Round-trip efficiency: {self.eff_roundtrip:.1%}")
    
    def reset(self, initial_soc: float = None):
        """Reset BESS to initial state."""
        if initial_soc is None:
            # Start at minimum SOC to maximize solar utilization
            initial_soc = self.tech_params['soc_min']
        
        self.soc = initial_soc
        self.energy_stored = self.soc * self.capacity_mwh if self.capacity_mwh > 0 else 0
        
        # Tracking variables
        self.total_energy_charged = 0
        self.total_energy_discharged = 0
        self.total_energy_losses = 0
        self.cycles = 0
        
        # Operation history (only if tracking enabled)
        self.operation_history = [] if self.track_history else None
    
    def get_charge_limit(self, dt: float = 1.0) -> float:
        """Get maximum charging power at current SOC.
        
        Args:
            dt: Time step in hours
        """
        if self.capacity_mwh == 0:
            return 0
        
        # SOC constraint - adjusted for timestep
        energy_headroom = max(0, (self.tech_params['soc_max'] - self.soc) * self.capacity_mwh)
        power_soc = energy_headroom / dt  # Power compatible with timestep
        
        # Technology constraint (includes both C-rate and effective power)
        c_rate_limit = self.tech_params['c_rate_max'] * self.capacity_mwh
        power_tech = min(c_rate_limit, self.power_mw_eff)
        
        return min(power_soc, power_tech)
    
    def get_discharge_limit(self, dt: float = 1.0) -> float:
        """Get maximum discharge power at current SOC.
        
        Args:
            dt: Time step in hours
        """
        if self.capacity_mwh == 0:
            return 0
        
        # SOC constraint - adjusted for timestep
        energy_available = max(0, (self.soc - self.tech_params['soc_min']) * self.capacity_mwh)
        power_soc = energy_available / dt  # Power compatible with timestep
        
        # Technology constraint (includes both C-rate and effective power)
        c_rate_limit = self.tech_params['c_rate_max'] * self.capacity_mwh
        power_tech = min(c_rate_limit, self.power_mw_eff)
        
        return min(power_soc, power_tech)
    
    def step(self, power_request: float, dt: float = 1.0) -> Dict[str, float]:
        """
        Execute one time step of BESS operation.
        
        Args:
            power_request: Power request in MW (negative=charge, positive=discharge)
            dt: Time step in hours
            
        Returns:
            Dictionary with actual power, losses, and new SOC
        """
        if self.capacity_mwh == 0:
            return {
                'actual_power': 0,
                'energy_loss': 0,
                'soc': 0,
                'limited_by': 'no_capacity'
            }
        
        # Use class constant for threshold
        ENERGY_THRESHOLD_MWH = self.CYCLE_ENERGY_THRESHOLD_MWH
        
        # Determine operation mode and limits
        if power_request < 0:  # Charging
            max_charge = self.get_charge_limit(dt)
            actual_power = max(-max_charge, power_request)
            limited_by = 'charge_limit' if abs(actual_power) < abs(power_request) else 'none'
            
            # Energy change with efficiency (loss always positive)
            energy_into_battery = -actual_power * dt * self.tech_params['η_charge']
            energy_loss = -actual_power * dt * (1 - self.tech_params['η_charge'])
            
        else:  # Discharging
            max_discharge = self.get_discharge_limit(dt)
            actual_power = min(max_discharge, power_request)
            limited_by = 'discharge_limit' if actual_power < power_request else 'none'
            
            # Energy change with efficiency (loss always positive)
            energy_from_battery = actual_power * dt / self.tech_params['η_discharge']
            energy_into_battery = -energy_from_battery
            # Correct loss calculation: loss = P*dt*(1/η - 1)
            energy_loss = actual_power * dt * (1/self.tech_params['η_discharge'] - 1)
        
        # Update state with clipping
        self.energy_stored += energy_into_battery
        self.energy_stored = np.clip(
            self.energy_stored,
            self.tech_params['soc_min'] * self.capacity_mwh,
            self.tech_params['soc_max'] * self.capacity_mwh
        )
        self.soc = self.energy_stored / self.capacity_mwh
        
        # Track energy flows (only if above threshold)
        delta_energy = abs(actual_power * dt)
        if delta_energy > ENERGY_THRESHOLD_MWH:
            if actual_power < 0:
                self.total_energy_charged += delta_energy
            else:
                self.total_energy_discharged += delta_energy
        self.total_energy_losses += energy_loss
        
        # Update cycles using usable capacity (avoid division by zero)
        if self.usable_capacity_mwh > 0:
            self.cycles = (self.total_energy_charged + self.total_energy_discharged) / (2 * self.usable_capacity_mwh)
        else:
            self.cycles = 0  # No meaningful cycles if no usable capacity
        
        # Store operation record (only if tracking enabled)
        if self.track_history and self.operation_history is not None:
            self.operation_history.append({
                'power': actual_power,
                'soc': self.soc,
                'energy_loss': energy_loss,
                'limited_by': limited_by
            })
        
        return {
            'actual_power': actual_power,
            'energy_loss': energy_loss,
            'soc': self.soc,
            'limited_by': limited_by
        }
    
    def simulate_strategy(self,
                         solar_profile: Union[np.ndarray, pd.Series],
                         strategy: str,
                         use_wrapper: bool = False,
                         wrapper_config: Optional[Dict] = None,
                         **kwargs) -> Dict[str, Union[np.ndarray, Dict]]:
        """
        Simulate BESS operation with a specific strategy.
        
        Args:
            solar_profile: Solar generation profile (MW)
            strategy: Strategy name
            use_wrapper: If True, use BESSStrategyWrapper for ML logging
            wrapper_config: Configuration for wrapper (log_level, ml_logging, etc)
            **kwargs: Strategy-specific parameters
            
        Returns:
            Simulation results with validation
        """
        # Use wrapper if requested
        if use_wrapper:
            from .bess_strategy_wrapper import BESSStrategyWrapper
            
            # Default wrapper config
            default_config = {
                'log_level': 'WARNING',
                'ml_logging': True,
                'validate_balance': True,
                'tolerance': 1e-6
            }
            if wrapper_config:
                default_config.update(wrapper_config)
            
            # Create wrapper and execute
            wrapper = BESSStrategyWrapper(**default_config)
            wrapper_results = wrapper.execute_strategy(
                bess_model=self,
                solar=solar_profile,
                strategy_name=strategy,
                **kwargs
            )
            
            # Return wrapper results (includes original arrays plus ML metrics)
            return wrapper_results
        
        # Original implementation (without wrapper)
        # Convert to numpy if needed
        if isinstance(solar_profile, pd.Series):
            solar_profile = solar_profile.values
        
        n_steps = len(solar_profile)
        
        # Initialize results with NaN to detect if strategy fails to fill them
        grid_power = np.full(n_steps, np.nan)
        battery_power = np.full(n_steps, np.nan)
        soc = np.full(n_steps, np.nan)
        solar_curtailed = np.full(n_steps, np.nan)
        energy_losses = np.full(n_steps, np.nan)
        
        # Reset BESS
        self.reset()
        
        # Apply strategy using optimized strategies
        # Estrategias V1 (minimizan uso del BESS)
        if strategy == 'cap_shaving':
            BESSStrategies.apply_cap_shaving(
                self, solar_profile, grid_power, battery_power, soc, 
                solar_curtailed, energy_losses, **kwargs
            )
        elif strategy == 'cap_shaving_balanced':
            BESSStrategies.apply_cap_shaving_balanced(
                self, solar_profile, grid_power, battery_power, soc, 
                solar_curtailed, energy_losses, **kwargs
            )
        elif strategy == 'soft_cap_shaving':
            BESSStrategies.apply_soft_cap_shaving(
                self, solar_profile, grid_power, battery_power, soc, 
                solar_curtailed, energy_losses, **kwargs
            )
        elif strategy == 'flat_day':
            BESSStrategies.apply_flat_day(
                self, solar_profile, grid_power, battery_power, soc,
                solar_curtailed, energy_losses, **kwargs
            )
        elif strategy == 'night_shift':
            BESSStrategies.apply_night_shift(
                self, solar_profile, grid_power, battery_power, soc,
                solar_curtailed, energy_losses, **kwargs
            )
        elif strategy == 'ramp_limit':
            BESSStrategies.apply_ramp_limit(
                self, solar_profile, grid_power, battery_power, soc,
                solar_curtailed, energy_losses, **kwargs
            )
        # Estrategias V2 (fuerzan uso del BESS para demostrar pérdidas)
        elif strategy == 'solar_smoothing':
            BESSStrategiesV2.apply_solar_smoothing(
                self, solar_profile, grid_power, battery_power, soc,
                solar_curtailed, energy_losses, **kwargs
            )
        elif strategy == 'time_shift_aggressive':
            BESSStrategiesV2.apply_time_shift_aggressive(
                self, solar_profile, grid_power, battery_power, soc,
                solar_curtailed, energy_losses, **kwargs
            )
        elif strategy == 'cycling_demo':
            BESSStrategiesV2.apply_cycling_demo(
                self, solar_profile, grid_power, battery_power, soc,
                solar_curtailed, energy_losses, **kwargs
            )
        elif strategy == 'frequency_regulation':
            BESSStrategiesV2.apply_frequency_regulation(
                self, solar_profile, grid_power, battery_power, soc,
                solar_curtailed, energy_losses, **kwargs
            )
        elif strategy == 'arbitrage_aggressive':
            BESSStrategiesV2.apply_arbitrage_aggressive(
                self, solar_profile, grid_power, battery_power, soc,
                solar_curtailed, energy_losses, **kwargs
            )
        else:
            # No BESS operation - fill arrays properly
            grid_power[:] = solar_profile
            battery_power[:] = 0
            soc[:] = self.soc
            solar_curtailed[:] = 0
            energy_losses[:] = 0
            if self.verbose:
                logger.warning(f"Unknown strategy '{strategy}', passing through solar")
        
        # Check if strategy filled the arrays properly
        if np.isnan(grid_power).any():
            raise ValueError(f"Strategy '{strategy}' failed to fill output arrays properly")
        
        # Prepare results
        results = {
            'grid_power': grid_power,
            'battery_power': battery_power,
            'soc': soc,
            'solar_curtailed': solar_curtailed,
            'energy_losses': energy_losses,
            'solar_delivered': solar_profile - solar_curtailed,
            'total_cycles': self.cycles
        }
        
        # Validate results
        validation = self.validator.validate_strategy_result(
            solar_profile, results, strategy, 
            {'power_mw': self.power_mw, 'duration_h': self.duration_hours, 
             'capacity_mwh': self.capacity_mwh, **kwargs}
        )
        
        results['validation'] = validation
        
        # Validate that the strategy produced results
        if validation and not validation.get('valid', True):
            if self.verbose:
                logger.warning(f"Validation failed: {validation.get('reason', 'Unknown')}")
            # Could raise here but let's keep it non-breaking for now
            # raise ValueError(f"Strategy validation failed: {validation.get('reason', 'Unknown')}")
        
        # Capture final cycles after simulation
        results['total_cycles'] = self.cycles
        results['daily_cycles'] = self.cycles / (len(solar_profile) / 24) if len(solar_profile) > 24 else 0
        
        return results
    
    def get_configuration_summary(self) -> Dict[str, Union[str, float]]:
        """Get summary of BESS configuration."""
        return {
            'power_mw': self.power_mw,
            'duration_h': self.duration_hours,
            'capacity_mwh': self.capacity_mwh,
            'technology': self.technology,
            'topology': self.topology,
            'roundtrip_efficiency': self.tech_params['η_roundtrip'],
            'usable_capacity_mwh': self.capacity_mwh * (
                self.tech_params['soc_max'] - self.tech_params['soc_min']
            ),
            'c_rate': self.power_mw / self.capacity_mwh if self.capacity_mwh > 0 else 0,
            'max_cycles_per_day': 24 * self.power_mw / self.capacity_mwh if self.capacity_mwh > 0 else 0,
            'effective_power_mw': self.power_mw_eff
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all parameters for dashboard display."""
        from datetime import datetime
        d = self.get_configuration_summary()
        d['technology_params'] = self.tech_params.copy()
        d['topology_params'] = self.topo_params.copy()
        d['current_state'] = {
            'soc': self.soc,
            'cycles': self.cycles,
            'total_losses_mwh': self.total_energy_losses,
            'total_charged_mwh': self.total_energy_charged,
            'total_discharged_mwh': self.total_energy_discharged,
            'timestamp': datetime.now().isoformat()
        }
        return d
    
    def next_state(self, soc: Union[float, np.ndarray], 
                   p_req: Union[float, np.ndarray], 
                   dt: float = 0.25,
                   dtype: type = np.float64) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Stateless state transition for RL/optimization.
        Vectorizable for batch processing.
        
        Args:
            soc: State of charge (scalar or array)
            p_req: Power request in MW (negative=charge, positive=discharge)
            dt: Time step in hours
            dtype: NumPy dtype for arrays (default np.float64, can use np.float32 for ML)
            
        Returns:
            Tuple of (new_soc, actual_power_mw, losses_mwh)
            where losses_mwh is energy lost in the time step.
            Output shape matches input shape (scalar→scalar, array→array)
        """
        # Convert to arrays for vectorization with specified dtype
        soc_arr = np.atleast_1d(np.asarray(soc, dtype=dtype))
        p_req_arr = np.atleast_1d(np.asarray(p_req, dtype=dtype))
        
        # Calculate charge/discharge limits based on SOC
        headroom = np.maximum(0, (self.tech_params['soc_max'] - soc_arr) * self.capacity_mwh)
        available = np.maximum(0, (soc_arr - self.tech_params['soc_min']) * self.capacity_mwh)
        
        # Power limits including C-rate constraint and effective power
        c_rate_limit = self.tech_params['c_rate_max'] * self.capacity_mwh
        p_charge_limit = np.minimum(
            np.minimum(self.power_mw_eff, headroom / dt),
            c_rate_limit
        )
        p_discharge_limit = np.minimum(
            np.minimum(self.power_mw_eff, available / dt),
            c_rate_limit
        )
        
        # Apply limits
        p_actual = np.where(
            p_req_arr < 0,
            np.maximum(-p_charge_limit, p_req_arr),  # Charging
            np.minimum(p_discharge_limit, p_req_arr)  # Discharging
        )
        
        # Calculate energy changes and losses
        energy_change = np.where(
            p_actual < 0,
            -p_actual * dt * self.tech_params['η_charge'],  # Charging with efficiency
            -p_actual * dt / self.tech_params['η_discharge']  # Discharging with efficiency
        )
        
        losses = np.where(
            p_actual < 0,
            -p_actual * dt * (1 - self.tech_params['η_charge']),  # Charge losses
            p_actual * dt * (1/self.tech_params['η_discharge'] - 1)  # Discharge losses: P*dt*(1/η - 1)
        )
        
        # Update SOC
        new_energy = (soc_arr * self.capacity_mwh) + energy_change
        new_energy = np.clip(
            new_energy,
            self.tech_params['soc_min'] * self.capacity_mwh,
            self.tech_params['soc_max'] * self.capacity_mwh
        )
        new_soc = new_energy / self.capacity_mwh if self.capacity_mwh > 0 else soc_arr
        
        # Return scalars if inputs were scalars
        if np.isscalar(soc) and np.isscalar(p_req):
            return float(new_soc[0]), float(p_actual[0]), float(losses[0])
        
        return new_soc, p_actual, losses