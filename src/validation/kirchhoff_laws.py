"""
Kirchhoff Laws Validator for Phase 5
Validates current conservation at each node
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

# Setup paths for imports
import sys
from pathlib import Path
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.network.topology import NetworkTopology
from dashboard.pages.utils.data_manager_v2 import DataManagerV2
from dashboard.pages.utils.models import DataResult, DataStatus

logger = logging.getLogger(__name__)


@dataclass
class KirchhoffViolation:
    """Details of a Kirchhoff law violation"""
    node_id: str
    law_type: str  # "current" or "voltage"
    imbalance: float  # A or kV
    imbalance_percent: float
    incoming: float
    outgoing: float
    severity: str  # "high", "medium", "low"


@dataclass 
class KirchhoffValidationResult:
    """Results from Kirchhoff laws validation"""
    is_valid: bool
    violations: List[KirchhoffViolation]
    max_imbalance_current: float  # A
    max_imbalance_voltage: float  # kV
    nodes_checked: int
    details: Dict[str, Any]


class KirchhoffValidator:
    """
    Validates Kirchhoff's laws in the network.
    
    - Current Law (KCL): Σ I_in = Σ I_out at each node
    - Voltage Law (KVL): Σ V = 0 around closed loops
    
    Special considerations for low voltage (< 0.95 pu) networks:
    - Higher currents due to low voltage
    - Increased measurement errors
    - Non-linear load effects
    """
    
    def __init__(self, current_tolerance: float = 0.01, voltage_tolerance: float = 0.001):
        """
        Initialize validator.
        
        Args:
            current_tolerance: Max allowed current imbalance (A)
            voltage_tolerance: Max allowed voltage imbalance (kV)
        """
        self.dm = DataManagerV2()
        self.current_tolerance = current_tolerance
        self.voltage_tolerance = voltage_tolerance
        
        # Load network topology
        system_data, status = self.dm.get_system_data()
        if status == DataStatus.REAL and system_data:
            self.network = NetworkTopology()
            # Initialize topology from data
            self.network.nodes_data = system_data.get("nodes", {})
            self.network.edges_data = system_data.get("edges", {})
            self.network._build_graph()
        else:
            logger.error("Could not load network topology")
            self.network = None
    
    def validate_current_law(self, node_id: str, 
                           line_flows: Dict[str, float],
                           load_current: float = 0.0,
                           generation_current: float = 0.0) -> Optional[KirchhoffViolation]:
        """
        Validate Kirchhoff's Current Law at a node.
        
        Args:
            node_id: Node to check
            line_flows: Dict of line_id -> current (A), positive = into node
            load_current: Load current at node (A)
            generation_current: Generation current at node (A)
            
        Returns:
            KirchhoffViolation if violation found, None otherwise
        """
        # Calculate total current in and out
        current_in = generation_current
        current_out = load_current
        
        # Add line flows
        for line_id, current in line_flows.items():
            if current > 0:
                current_in += current
            else:
                current_out += abs(current)
        
        # Calculate imbalance
        imbalance = abs(current_in - current_out)
        
        # Calculate percentage (avoid division by zero)
        total_current = max(current_in, current_out)
        if total_current > 0:
            imbalance_percent = (imbalance / total_current) * 100
        else:
            imbalance_percent = 0
        
        # Check if violation
        if imbalance > self.current_tolerance:
            severity = "high" if imbalance > 10 * self.current_tolerance else "medium"
            
            return KirchhoffViolation(
                node_id=node_id,
                law_type="current",
                imbalance=imbalance,
                imbalance_percent=imbalance_percent,
                incoming=current_in,
                outgoing=current_out,
                severity=severity
            )
        
        return None
    
    def validate_voltage_law(self, loop_path: List[str],
                           node_voltages: Dict[str, float],
                           line_voltage_drops: Dict[Tuple[str, str], float]) -> Optional[KirchhoffViolation]:
        """
        Validate Kirchhoff's Voltage Law around a loop.
        
        Args:
            loop_path: List of node IDs forming a closed loop
            node_voltages: Dict of node_id -> voltage (kV)
            line_voltage_drops: Dict of (from_node, to_node) -> voltage drop (kV)
            
        Returns:
            KirchhoffViolation if violation found, None otherwise
        """
        if len(loop_path) < 3:
            return None  # Not a valid loop
        
        # Calculate voltage sum around loop
        voltage_sum = 0.0
        
        for i in range(len(loop_path)):
            from_node = loop_path[i]
            to_node = loop_path[(i + 1) % len(loop_path)]
            
            # Get voltage drop across line
            if (from_node, to_node) in line_voltage_drops:
                voltage_sum += line_voltage_drops[(from_node, to_node)]
            elif (to_node, from_node) in line_voltage_drops:
                voltage_sum -= line_voltage_drops[(to_node, from_node)]
            else:
                logger.warning(f"Missing voltage drop for line {from_node}-{to_node}")
                return None
        
        # Check if violation
        imbalance = abs(voltage_sum)
        
        if imbalance > self.voltage_tolerance:
            # Create a representative violation
            return KirchhoffViolation(
                node_id=f"loop_{loop_path[0]}_{loop_path[-1]}",
                law_type="voltage",
                imbalance=imbalance,
                imbalance_percent=(imbalance / 33.0) * 100,  # As % of nominal 33kV
                incoming=0,  # Not applicable for voltage
                outgoing=0,
                severity="medium"
            )
        
        return None
    
    def validate_network(self, network_state: Dict[str, Any]) -> KirchhoffValidationResult:
        """
        Validate Kirchhoff's laws for entire network.
        
        Args:
            network_state: Dictionary containing:
                - node_currents: Dict[node_id, Dict] with load, generation, line flows
                - node_voltages: Dict[node_id, float] - kV
                - line_voltage_drops: Dict[(from, to), float] - kV
                
        Returns:
            KirchhoffValidationResult
        """
        if not self.network:
            return KirchhoffValidationResult(
                is_valid=False,
                violations=[],
                max_imbalance_current=0,
                max_imbalance_voltage=0,
                nodes_checked=0,
                details={"error": "Network topology not loaded"}
            )
        
        violations = []
        max_current_imbalance = 0.0
        max_voltage_imbalance = 0.0
        
        # Get data from network state
        node_currents = network_state.get("node_currents", {})
        node_voltages = network_state.get("node_voltages", {})
        line_voltage_drops = network_state.get("line_voltage_drops", {})
        
        # Validate current law at each node
        for node_id in self.network.get_all_nodes():
            if node_id in node_currents:
                node_data = node_currents[node_id]
                
                violation = self.validate_current_law(
                    node_id=node_id,
                    line_flows=node_data.get("line_flows", {}),
                    load_current=node_data.get("load_current", 0),
                    generation_current=node_data.get("generation_current", 0)
                )
                
                if violation:
                    violations.append(violation)
                    max_current_imbalance = max(max_current_imbalance, violation.imbalance)
        
        # For radial networks, we typically don't have loops
        # But check if network has any loops
        if not nx.is_tree(self.network.graph.to_undirected()):
            logger.info("Network has loops, checking KVL")
            # Would need to identify loops and validate KVL
            # For now, skip as Línea Sur is radial
        
        # Build result
        result = KirchhoffValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            max_imbalance_current=max_current_imbalance,
            max_imbalance_voltage=max_voltage_imbalance,
            nodes_checked=len(node_currents),
            details={
                "total_violations": len(violations),
                "current_violations": sum(1 for v in violations if v.law_type == "current"),
                "voltage_violations": sum(1 for v in violations if v.law_type == "voltage")
            }
        )
        
        # Log summary
        if result.is_valid:
            logger.info(f"Kirchhoff validation PASSED for {result.nodes_checked} nodes")
        else:
            logger.warning(f"Kirchhoff validation FAILED: {len(violations)} violations found")
            for v in violations[:5]:  # Log first 5
                logger.warning(f"  {v.node_id}: {v.imbalance:.3f}A imbalance ({v.imbalance_percent:.1f}%)")
        
        return result
    
    def validate_with_measurements(self, calculated_state: Dict[str, Any],
                                 measured_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Kirchhoff laws comparing calculated vs measured values.
        
        Useful for identifying measurement errors or model inaccuracies.
        """
        # Validate calculated state
        calc_result = self.validate_network(calculated_state)
        
        # Validate measured state
        meas_result = self.validate_network(measured_state)
        
        comparison = {
            "calculated": {
                "is_valid": calc_result.is_valid,
                "violations": len(calc_result.violations),
                "max_current_imbalance": calc_result.max_imbalance_current
            },
            "measured": {
                "is_valid": meas_result.is_valid,
                "violations": len(meas_result.violations),
                "max_current_imbalance": meas_result.max_imbalance_current
            },
            "analysis": []
        }
        
        # Analyze differences
        if calc_result.is_valid and not meas_result.is_valid:
            comparison["analysis"].append({
                "finding": "measurement_errors",
                "description": "Calculated state satisfies Kirchhoff but measurements don't",
                "suggestion": "Check measurement accuracy and synchronization"
            })
        
        if not calc_result.is_valid and meas_result.is_valid:
            comparison["analysis"].append({
                "finding": "model_errors",
                "description": "Measurements satisfy Kirchhoff but calculations don't",
                "suggestion": "Review model parameters and assumptions"
            })
        
        # Check specific nodes with issues
        calc_nodes = {v.node_id for v in calc_result.violations}
        meas_nodes = {v.node_id for v in meas_result.violations}
        
        common_nodes = calc_nodes & meas_nodes
        if common_nodes:
            comparison["analysis"].append({
                "finding": "systematic_errors",
                "description": f"Nodes with violations in both: {list(common_nodes)[:5]}",
                "suggestion": "These nodes may have systematic issues"
            })
        
        return comparison


# Convenience functions for specific use cases

def check_node_current_balance(node_id: str, p_mw: float, q_mvar: float, 
                              v_kv: float, line_currents: Dict[str, float]) -> bool:
    """
    Quick check of current balance at a node given power and voltage.
    
    Args:
        node_id: Node identifier
        p_mw: Active power (MW)
        q_mvar: Reactive power (MVAr)
        v_kv: Voltage (kV)
        line_currents: Line currents (A)
        
    Returns:
        True if balanced within tolerance
    """
    # Calculate current magnitude from power
    s_mva = np.sqrt(p_mw**2 + q_mvar**2)
    i_total = (s_mva * 1000) / (np.sqrt(3) * v_kv)  # A
    
    # Sum line currents
    i_lines = sum(abs(i) for i in line_currents.values())
    
    # Check balance
    imbalance = abs(i_total - i_lines)
    
    return imbalance < 0.01  # 10 mA tolerance