"""
Line Parameters for Línea Sur 33kV Network
Real parameters based on conductor types and distances
"""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
import logging

# Setup paths for imports
import sys
from pathlib import Path
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dashboard.pages.utils.constants import ELECTRICAL_PARAMS

logger = logging.getLogger(__name__)


@dataclass
class Line:
    """Represents a transmission line in the network."""
    id: str
    from_node: str
    to_node: str
    length_km: float
    conductor_type: str
    r_ohm_per_km: float
    x_ohm_per_km: float
    b_microsiemens_per_km: float
    ampacity: float
    
    @property
    def r_total(self) -> float:
        """Total resistance in ohms."""
        return self.r_ohm_per_km * self.length_km
    
    @property
    def x_total(self) -> float:
        """Total reactance in ohms."""
        return self.x_ohm_per_km * self.length_km
    
    @property
    def z_total(self) -> complex:
        """Total impedance in ohms."""
        return complex(self.r_total, self.x_total)
    
    @property
    def y_shunt_total(self) -> complex:
        """Total shunt admittance in siemens."""
        b_total = self.b_microsiemens_per_km * self.length_km * 1e-6
        return complex(0, b_total)
    
    def power_loss_mw(self, current_a: float, power_factor: float = 0.9) -> float:
        """Calculate power losses in MW given current."""
        # P_loss = 3 * I^2 * R (for 3-phase)
        return 3 * (current_a ** 2) * self.r_total / 1e6


class LineParameters:
    """
    Manages line parameters for Línea Sur network.
    
    Real line data:
    - Pilcaniyeu - Comallo: 104 km
    - Comallo - Jacobacci: 96 km
    - Jacobacci - Maquinchao: 75 km
    - Maquinchao - Los Menucos: 58 km
    """
    
    def __init__(self):
        """Initialize with conductor types from constants."""
        self.conductor_types = ELECTRICAL_PARAMS.get("conductor_types", {})
        self.lines = self._initialize_lines()
        logger.info(f"Initialized {len(self.lines)} transmission lines")
    
    def _initialize_lines(self) -> Dict[str, Line]:
        """Initialize all lines in the network."""
        lines = {}
        
        # Define network topology with real distances
        line_data = [
            {
                "id": "pilcaniyeu_comallo",
                "from_node": "pilcaniyeu",
                "to_node": "comallo",
                "length_km": 104,
                "conductor_type": "ACSR_95"  # Main feeder
            },
            {
                "id": "comallo_jacobacci",
                "from_node": "comallo",
                "to_node": "jacobacci", 
                "length_km": 96,
                "conductor_type": "ACSR_95"
            },
            {
                "id": "jacobacci_maquinchao",
                "from_node": "jacobacci",
                "to_node": "maquinchao",
                "length_km": 75,
                "conductor_type": "ACSR_50"  # Smaller conductor
            },
            {
                "id": "maquinchao_menucos",
                "from_node": "maquinchao",
                "to_node": "los_menucos",
                "length_km": 58,
                "conductor_type": "ACSR_50"
            }
        ]
        
        # Create Line objects
        for data in line_data:
            conductor = self.conductor_types.get(data["conductor_type"], {})
            if not conductor:
                logger.warning(f"Conductor type {data['conductor_type']} not found, using defaults")
                conductor = {
                    "r_ohm_per_km": 0.4,
                    "x_ohm_per_km": 0.4,
                    "b_microsiemens_per_km": 2.5,
                    "ampacity": 200
                }
            
            line = Line(
                id=data["id"],
                from_node=data["from_node"],
                to_node=data["to_node"],
                length_km=data["length_km"],
                conductor_type=data["conductor_type"],
                r_ohm_per_km=conductor["r_ohm_per_km"],
                x_ohm_per_km=conductor["x_ohm_per_km"],
                b_microsiemens_per_km=conductor["b_microsiemens_per_km"],
                ampacity=conductor["ampacity"]
            )
            
            lines[line.id] = line
            
            # Log line parameters
            logger.debug(f"Line {line.id}: R={line.r_total:.2f}Ω, X={line.x_total:.2f}Ω, "
                        f"Z={abs(line.z_total):.2f}Ω, Length={line.length_km}km")
        
        return lines
    
    def get_line(self, line_id: str) -> Optional[Line]:
        """Get line by ID."""
        return self.lines.get(line_id)
    
    def get_lines_from_node(self, node_id: str) -> list[Line]:
        """Get all lines connected to a node."""
        return [line for line in self.lines.values() 
                if line.from_node == node_id or line.to_node == node_id]
    
    def calculate_voltage_drop(self, line_id: str, current_a: float, 
                             power_factor: float = 0.9) -> float:
        """
        Calculate voltage drop in kV for a line.
        
        Simplified formula: ΔV ≈ I * (R*cos(φ) + X*sin(φ)) * length
        """
        line = self.get_line(line_id)
        if not line:
            return 0.0
        
        # Power factor angles
        cos_phi = power_factor
        sin_phi = np.sqrt(1 - power_factor**2)
        
        # Voltage drop in volts (line-to-line)
        delta_v = current_a * (line.r_total * cos_phi + line.x_total * sin_phi)
        
        # Convert to kV
        return delta_v / 1000
    
    def get_total_line_length(self) -> float:
        """Get total length of all lines in km."""
        return sum(line.length_km for line in self.lines.values())
    
    def get_network_impedance_matrix(self) -> Dict[str, Dict[str, complex]]:
        """
        Get impedance matrix for all lines.
        Returns dict of dict with impedances between nodes.
        """
        z_matrix = {}
        
        for line in self.lines.values():
            # Initialize if needed
            if line.from_node not in z_matrix:
                z_matrix[line.from_node] = {}
            if line.to_node not in z_matrix:
                z_matrix[line.to_node] = {}
            
            # Set impedances (symmetric)
            z_matrix[line.from_node][line.to_node] = line.z_total
            z_matrix[line.to_node][line.from_node] = line.z_total
        
        return z_matrix
    
    def estimate_losses_mw(self, line_flows_mw: Dict[str, float]) -> Dict[str, float]:
        """
        Estimate losses for each line given power flows.
        
        Uses I²R losses with estimated current from power flow.
        Assumes 33kV and 0.9 power factor.
        """
        losses = {}
        base_kv = 33.0
        power_factor = 0.9
        
        for line_id, flow_mw in line_flows_mw.items():
            line = self.get_line(line_id)
            if not line:
                continue
            
            # Estimate current from power flow
            # I = P / (sqrt(3) * V * PF)
            current_a = abs(flow_mw) * 1000 / (np.sqrt(3) * base_kv * power_factor)
            
            # Calculate losses
            losses[line_id] = line.power_loss_mw(current_a, power_factor)
        
        return losses
    
    def get_line_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of all line parameters."""
        summary = {}
        
        for line_id, line in self.lines.items():
            summary[line_id] = {
                "length_km": line.length_km,
                "r_total_ohm": line.r_total,
                "x_total_ohm": line.x_total,
                "z_magnitude_ohm": abs(line.z_total),
                "ampacity_a": line.ampacity,
                "max_power_mw": line.ampacity * 33 * np.sqrt(3) * 0.9 / 1000
            }
        
        return summary


# Convenience function
def get_linea_sur_lines() -> LineParameters:
    """Get initialized LineParameters for Línea Sur network."""
    return LineParameters()