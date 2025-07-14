"""
BESS Strategies - Optimized for minimal energy losses
Each strategy minimizes BESS usage to achieve specific objectives

Note: All strategies support variable timesteps (dt) for sub-hourly simulations.
Default dt=1.0 assumes hourly steps.
"""

import numpy as np
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class BESSStrategies:
    """
    Optimized BESS operation strategies that minimize energy losses.
    Key principle: Use BESS only when necessary, pass solar directly when possible.
    """
    
    @staticmethod
    def apply_cap_shaving(bess_model, solar, grid, battery, soc, curtailed, losses,
                         cap_mw=None, soft_discharge=True, dt=1.0, **kwargs):
        """
        Cap shaving strategy - limit grid injection to cap_mw.
        
        Optimization: Only store excess above cap, discharge only if beneficial.
        
        Args:
            dt: Time step in hours (default 1.0 for hourly, 0.25 for 15-min)
        """
        if cap_mw is None:
            cap_mw = np.max(solar) * 0.7
        
        for i in range(len(solar)):
            soc[i] = bess_model.soc
            
            if solar[i] > cap_mw:
                # Only charge the excess above cap
                excess = solar[i] - cap_mw
                result = bess_model.step(-excess, dt=dt)
                
                battery[i] = result['actual_power']
                losses[i] = result['energy_loss']
                
                # Calculate actual grid output after battery action
                actual_excess_absorbed = -battery[i]  # Positive value
                remaining_excess = excess - actual_excess_absorbed
                
                # Set grid to cap plus any unabsorbed excess
                grid[i] = cap_mw + remaining_excess
                
                # Curtail if still above cap (battery couldn't absorb all)
                if grid[i] > cap_mw * 1.01:  # 1% tolerance
                    curtailed[i] = grid[i] - cap_mw
                    grid[i] = cap_mw
                    
            elif soft_discharge and solar[i] < cap_mw * 0.5 and bess_model.get_discharge_limit(dt) > 0.1:
                # Optional: gentle discharge during low solar to smooth output
                # Only discharge if we have significant stored energy
                if bess_model.soc > 0.3:  # Don't discharge below 30% for cap shaving
                    deficit = min(cap_mw * 0.5 - solar[i], bess_model.get_discharge_limit(dt) * 0.3)
                    result = bess_model.step(deficit, dt=dt)
                    
                    battery[i] = result['actual_power']
                    losses[i] = result['energy_loss']
                    grid[i] = solar[i] + battery[i]
                else:
                    # Pass through - no BESS action
                    grid[i] = solar[i]
                    battery[i] = 0
                    losses[i] = 0
            else:
                # Pass through when solar is below cap and no discharge needed
                grid[i] = solar[i]
                battery[i] = 0
                losses[i] = 0
    
    @staticmethod
    def apply_flat_day(bess_model, solar, grid, battery, soc, curtailed, losses,
                      flat_mw=None, start_hour=8, end_hour=18, dt=1.0, **kwargs):
        """
        Flat day strategy - constant output during specified window.
        
        Optimization: Pre-calculate energy needs and charge minimally.
        
        Note: Assumes solar profile represents a single day (24h/dt steps).
        For multi-day profiles, processes each day independently.
        """
        # Pre-analysis: Calculate energy balance per day
        steps_per_day = int(24 / dt)
        window_steps = [int(h / dt) for h in range(start_hour, end_hour)]
        
        # For single day profile
        if len(solar) <= steps_per_day:
            solar_in_window = sum(solar[s] for s in window_steps if s < len(solar)) * dt
        else:
            # Multi-day: average across days
            n_days = len(solar) // steps_per_day
            solar_in_window = sum(solar[d*steps_per_day + s] for d in range(n_days) 
                                for s in window_steps if d*steps_per_day + s < len(solar)) * dt / n_days
        
        if flat_mw is None:
            # Set flat power to a level that minimizes BESS usage
            total_solar = sum(solar) * dt
            available_with_efficiency = total_solar * 0.95  # Account for some losses
            window_duration = (end_hour - start_hour)  # hours
            flat_mw = available_with_efficiency / window_duration if window_duration > 0 else 0
        
        # Calculate energy deficit/surplus in window
        window_duration = end_hour - start_hour
        energy_needed_in_window = flat_mw * window_duration
        energy_deficit = max(0, energy_needed_in_window - solar_in_window)
        
        # Only use BESS if there's a real deficit
        if energy_deficit > 0.1:  # Meaningful deficit
            # We need to charge outside window and discharge inside
            for i in range(len(solar)):
                soc[i] = bess_model.soc
                step_in_day = i % steps_per_day
                hour = step_in_day * dt
                
                if start_hour <= hour < end_hour:
                    # Window hours - try to maintain flat output
                    if solar[i] >= flat_mw:
                        # Solar exceeds target - minimal charging of excess
                        excess = solar[i] - flat_mw
                        if excess > 0.1 and bess_model.get_charge_limit(dt) > 0.1:
                            # Only charge significant excess
                            result = bess_model.step(-excess, dt=dt)
                            battery[i] = result['actual_power']
                            losses[i] = result['energy_loss']
                        else:
                            battery[i] = 0
                            losses[i] = 0
                            # Small excess is curtailed to maintain flat output
                            curtailed[i] = excess
                        
                        grid[i] = flat_mw
                        
                    else:
                        # Solar below target - discharge to compensate
                        deficit = flat_mw - solar[i]
                        if deficit > 0.1 and bess_model.get_discharge_limit(dt) > 0.1:
                            result = bess_model.step(deficit, dt=dt)
                            battery[i] = result['actual_power']
                            losses[i] = result['energy_loss']
                            grid[i] = solar[i] + battery[i]
                        else:
                            # Can't maintain flat - pass through
                            grid[i] = solar[i]
                            battery[i] = 0
                            losses[i] = 0
                else:
                    # Outside window - charge only if needed for window deficit
                    if solar[i] > 0.1 and bess_model.soc < 0.8 and energy_deficit > 0:
                        # Calculate how much we still need to charge
                        energy_still_needed = energy_deficit * (1 - bess_model.soc + 0.1)
                        charge_power = min(solar[i], bess_model.get_charge_limit(dt), energy_still_needed / dt)
                        
                        if charge_power > 0.1:
                            result = bess_model.step(-charge_power, dt=dt)
                            battery[i] = result['actual_power']
                            losses[i] = result['energy_loss']
                            grid[i] = solar[i] + battery[i]  # Rest goes to grid
                        else:
                            # Pass through
                            grid[i] = solar[i]
                            battery[i] = 0
                            losses[i] = 0
                    else:
                        # Pass through - no charging needed
                        grid[i] = solar[i]
                        battery[i] = 0
                        losses[i] = 0
        else:
            # No significant deficit - pass through most energy
            for i in range(len(solar)):
                soc[i] = bess_model.soc
                step_in_day = i % steps_per_day
                hour = step_in_day * dt
                
                if start_hour <= hour < end_hour and abs(solar[i] - flat_mw) > 0.1:
                    # Minor adjustments only
                    if solar[i] > flat_mw:
                        curtailed[i] = solar[i] - flat_mw
                        grid[i] = flat_mw
                    else:
                        grid[i] = solar[i]
                    battery[i] = 0
                    losses[i] = 0
                else:
                    # Pass through
                    grid[i] = solar[i]
                    battery[i] = 0
                    losses[i] = 0
    
    @staticmethod
    def apply_night_shift(bess_model, solar, grid, battery, soc, curtailed, losses,
                         charge_hours=None, discharge_hours=None, dt=1.0, **kwargs):
        """
        Night shift strategy - minimal charging during day, discharge at night.
        
        Optimization: Only charge what can be discharged at night.
        """
        if charge_hours is None:
            charge_hours = list(range(10, 15))  # 10 AM to 2 PM (peak solar)
        if discharge_hours is None:
            discharge_hours = list(range(19, 22))  # 7 PM to 9 PM (peak demand)
        
        # Calculate night demand capacity
        discharge_duration = len(discharge_hours)  # hours
        max_night_delivery = bess_model.power_mw * discharge_duration
        max_energy_needed = min(max_night_delivery, bess_model.capacity_mwh * 0.85)
        
        # Track how much we've charged for night use
        energy_charged_for_night = 0
        
        for i in range(len(solar)):
            soc[i] = bess_model.soc
            steps_per_day = int(24 / dt)
            step_in_day = i % steps_per_day
            hour = int(step_in_day * dt)
            
            if hour in charge_hours and solar[i] > 0.5:
                # Charge only what we need for night discharge
                if energy_charged_for_night < max_energy_needed:
                    # Calculate remaining need
                    still_needed = max_energy_needed - energy_charged_for_night
                    charge_power = min(
                        solar[i] * 0.8,  # Don't take all solar
                        bess_model.get_charge_limit(dt),
                        still_needed / dt  # Convert energy to power
                    )
                    
                    if charge_power > 0.1:
                        result = bess_model.step(-charge_power, dt=dt)
                        battery[i] = result['actual_power']
                        losses[i] = result['energy_loss']
                        energy_charged_for_night += -battery[i] * dt  # Track energy charged
                        
                        # Most solar goes to grid
                        grid[i] = solar[i] + battery[i]
                    else:
                        # Pass through
                        grid[i] = solar[i]
                        battery[i] = 0
                        losses[i] = 0
                else:
                    # Already charged enough - pass through
                    grid[i] = solar[i]
                    battery[i] = 0
                    losses[i] = 0
                    
            elif hour in discharge_hours:
                # Discharge for night support
                if bess_model.get_discharge_limit(dt) > 0.1:
                    # Discharge at steady rate
                    discharge_power = min(
                        bess_model.power_mw * 0.6,  # Moderate discharge
                        bess_model.get_discharge_limit(dt)
                    )
                    result = bess_model.step(discharge_power, dt=dt)
                    battery[i] = result['actual_power']
                    losses[i] = result['energy_loss']
                else:
                    battery[i] = 0
                    losses[i] = 0
                
                # Add to any solar still available
                grid[i] = solar[i] + battery[i]
                
            else:
                # Outside charge/discharge windows - pass through
                grid[i] = solar[i]
                battery[i] = 0
                losses[i] = 0
    
    @staticmethod
    def apply_ramp_limit(bess_model, solar, grid, battery, soc, curtailed, losses,
                        ramp_limit_mw_per_hour=None, dt=1.0, **kwargs):
        """
        Ramp limiting strategy - limit rate of change.
        
        Optimization: Only use BESS for ramp violations, not general smoothing.
        """
        if ramp_limit_mw_per_hour is None:
            solar_peak = np.max(solar)
            ramp_limit_mw_per_hour = solar_peak * 0.15  # 15% of peak per hour
        
        prev_grid = 0
        
        for i in range(len(solar)):
            soc[i] = bess_model.soc
            
            if i == 0:
                # First hour - no ramp constraint
                grid[i] = solar[i]
                battery[i] = 0
                losses[i] = 0
            else:
                # Calculate natural ramp and scale to per-hour rate
                natural_ramp = (solar[i] - prev_grid) / dt  # MW/hour
                
                if abs(natural_ramp) <= ramp_limit_mw_per_hour:
                    # Within limit - pass through
                    grid[i] = solar[i]
                    battery[i] = 0
                    losses[i] = 0
                else:
                    # Ramp violation - use BESS minimally
                    if natural_ramp > 0:
                        # Ramping up too fast
                        allowed_ramp = ramp_limit_mw_per_hour * dt  # Scale back to MW for this timestep
                        target_grid = prev_grid + allowed_ramp
                        excess = solar[i] - target_grid
                        
                        if excess > 0.1 and bess_model.get_charge_limit(dt) > 0.1:
                            result = bess_model.step(-excess, dt=dt)
                            battery[i] = result['actual_power']
                            losses[i] = result['energy_loss']
                            grid[i] = solar[i] + battery[i]
                        else:
                            # Can't charge - curtail
                            curtailed[i] = excess
                            grid[i] = target_grid
                            battery[i] = 0
                            losses[i] = 0
                            
                    else:
                        # Ramping down too fast
                        allowed_ramp = -ramp_limit_mw_per_hour * dt  # Scale back to MW for this timestep
                        target_grid = max(0, prev_grid + allowed_ramp)
                        deficit = target_grid - solar[i]
                        
                        if deficit > 0.1 and bess_model.get_discharge_limit(dt) > 0.1:
                            result = bess_model.step(deficit, dt=dt)
                            battery[i] = result['actual_power']
                            losses[i] = result['energy_loss']
                            grid[i] = solar[i] + battery[i]
                        else:
                            # Can't discharge enough - accept violation
                            grid[i] = solar[i]
                            battery[i] = 0
                            losses[i] = 0
            
            prev_grid = grid[i]
    
    @staticmethod
    def apply_peak_shaving(bess_model, solar, grid, battery, soc, curtailed, losses,
                          peak_threshold=None, dt=1.0, **kwargs):
        """
        Peak shaving strategy - reduce peak demand on the grid.
        
        Similar to cap_shaving but focused on demand peaks rather than generation.
        """
        if peak_threshold is None:
            peak_threshold = np.percentile(solar[solar > 0], 80)  # 80th percentile
        
        # Pre-scan to identify peak hours
        peak_hours = [i for i, s in enumerate(solar) if s > peak_threshold]
        
        for i in range(len(solar)):
            soc[i] = bess_model.soc
            
            if i in peak_hours:
                # Peak hour - shave the peak
                excess = solar[i] - peak_threshold
                if excess > 0.1 and bess_model.get_charge_limit(dt) > 0.1:
                    result = bess_model.step(-excess, dt=dt)
                    battery[i] = result['actual_power']
                    losses[i] = result['energy_loss']
                    grid[i] = solar[i] + battery[i]
                else:
                    grid[i] = solar[i]
                    battery[i] = 0
                    losses[i] = 0
                    
            elif solar[i] < peak_threshold * 0.3 and bess_model.soc > 0.2:
                # Low generation - optional discharge
                if bess_model.get_discharge_limit(dt) > 0.1:
                    discharge = min(
                        peak_threshold * 0.3 - solar[i],
                        bess_model.get_discharge_limit(dt) * 0.5
                    )
                    result = bess_model.step(discharge, dt=dt)
                    battery[i] = result['actual_power']
                    losses[i] = result['energy_loss']
                    grid[i] = solar[i] + battery[i]
                else:
                    grid[i] = solar[i]
                    battery[i] = 0
                    losses[i] = 0
            else:
                # Normal operation - pass through
                grid[i] = solar[i]
                battery[i] = 0
                losses[i] = 0