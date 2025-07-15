"""
Base classes for BESS topology modeling
Defines abstract interfaces for parallel and series configurations
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class BESSUnit:
    """Single BESS unit with basic properties"""
    
    def __init__(self, 
                 unit_id: str,
                 power_mw: float, 
                 capacity_mwh: float,
                 soc_initial: float = 0.5):
        """
        Initialize a single BESS unit
        
        Args:
            unit_id: Unique identifier
            power_mw: Rated power in MW
            capacity_mwh: Energy capacity in MWh
            soc_initial: Initial state of charge (0-1)
        """
        self.unit_id = unit_id
        self.power_mw = power_mw
        self.capacity_mwh = capacity_mwh
        
        # State variables
        self.soc = soc_initial
        self.energy_stored = soc_initial * capacity_mwh
        self.is_online = True
        
        # Technical limits
        self.soc_min = 0.10
        self.soc_max = 0.95
        self.efficiency_charge = 0.975
        self.efficiency_discharge = 0.975
        
        # Operational history
        self.cycles = 0
        self.energy_throughput = 0
        
    def get_available_power_charge(self) -> float:
        """Get available charging power considering SOC limits"""
        if not self.is_online:
            return 0
        
        energy_space = (self.soc_max - self.soc) * self.capacity_mwh
        return min(self.power_mw, energy_space)  # Limited by 1-hour timestep
    
    def get_available_power_discharge(self) -> float:
        """Get available discharging power considering SOC limits"""
        if not self.is_online:
            return 0
            
        energy_available = (self.soc - self.soc_min) * self.capacity_mwh
        return min(self.power_mw, energy_available)
    
    def charge(self, power: float, dt: float = 1.0) -> float:
        """
        Charge the unit
        
        Args:
            power: Charging power in MW (positive)
            dt: Time step in hours
            
        Returns:
            Actual power charged
        """
        if not self.is_online or power <= 0:
            return 0
            
        # Limit by available power
        power_limited = min(power, self.get_available_power_charge())
        
        # Energy with losses
        energy_in = power_limited * dt
        energy_stored = energy_in * self.efficiency_charge
        
        # Update state
        self.energy_stored += energy_stored
        self.soc = self.energy_stored / self.capacity_mwh
        self.energy_throughput += energy_in
        
        return power_limited
    
    def discharge(self, power: float, dt: float = 1.0) -> float:
        """
        Discharge the unit
        
        Args:
            power: Discharging power in MW (positive)
            dt: Time step in hours
            
        Returns:
            Actual power discharged
        """
        if not self.is_online or power <= 0:
            return 0
            
        # Limit by available power
        power_limited = min(power, self.get_available_power_discharge())
        
        # Energy with losses
        energy_out = power_limited * dt
        energy_from_battery = energy_out / self.efficiency_discharge
        
        # Update state
        self.energy_stored -= energy_from_battery
        self.soc = self.energy_stored / self.capacity_mwh
        self.energy_throughput += energy_out
        
        # Count cycles (simplified: full discharge = 1 cycle)
        self.cycles += energy_from_battery / self.capacity_mwh
        
        return power_limited
    
    def set_online(self, status: bool) -> None:
        """Set unit online/offline status"""
        self.is_online = status
        if not status:
            logger.warning(f"Unit {self.unit_id} set to offline")


class BESSTopology(ABC):
    """Abstract base class for BESS topology configurations"""
    
    def __init__(self, units: List[BESSUnit]):
        """
        Initialize topology with list of BESS units
        
        Args:
            units: List of BESSUnit objects
        """
        self.units = units
        self.n_units = len(units)
        
    @abstractmethod
    def get_total_power_capacity(self) -> float:
        """Get total power capacity of the system"""
        pass
    
    @abstractmethod
    def get_total_energy_capacity(self) -> float:
        """Get total energy capacity of the system"""
        pass
    
    @abstractmethod
    def get_available_power_charge(self) -> float:
        """Get currently available charging power"""
        pass
    
    @abstractmethod
    def get_available_power_discharge(self) -> float:
        """Get currently available discharging power"""
        pass
    
    @abstractmethod
    def get_system_soc(self) -> float:
        """Get equivalent system state of charge"""
        pass
    
    @abstractmethod
    def get_system_efficiency(self) -> Tuple[float, float]:
        """Get system charge and discharge efficiency"""
        pass
    
    @abstractmethod
    def charge(self, power_request: float, dt: float = 1.0) -> Dict[str, float]:
        """
        Charge the system
        
        Args:
            power_request: Total charging power requested (MW)
            dt: Time step (hours)
            
        Returns:
            Dict with actual power charged and distribution
        """
        pass
    
    @abstractmethod
    def discharge(self, power_request: float, dt: float = 1.0) -> Dict[str, float]:
        """
        Discharge the system
        
        Args:
            power_request: Total discharging power requested (MW)
            dt: Time step (hours)
            
        Returns:
            Dict with actual power discharged and distribution
        """
        pass
    
    @abstractmethod
    def get_operational_status(self) -> Dict[str, any]:
        """Get detailed operational status of the system"""
        pass
    
    def get_online_units(self) -> List[BESSUnit]:
        """Get list of online units"""
        return [unit for unit in self.units if unit.is_online]
    
    def set_unit_status(self, unit_id: str, online: bool) -> bool:
        """
        Set unit online/offline status
        
        Args:
            unit_id: Unit identifier
            online: True for online, False for offline
            
        Returns:
            True if successful, False if unit not found
        """
        for unit in self.units:
            if unit.unit_id == unit_id:
                unit.set_online(online)
                return True
        return False