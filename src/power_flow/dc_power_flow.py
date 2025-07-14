"""
DC Power Flow Engine for Línea Sur Network
Simplified power flow for radial 33kV network
"""

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
from typing import Dict, Tuple, Optional, List
import logging
from datetime import datetime
from dataclasses import dataclass

from .line_parameters import LineParameters
from .network_builder import NetworkBuilder

logger = logging.getLogger(__name__)


@dataclass
class PowerFlowResult:
    """Results from DC power flow calculation."""
    converged: bool
    iterations: int
    angles_rad: Dict[str, float]
    angles_deg: Dict[str, float]
    flows_mw: Dict[str, float]
    losses_mw: Dict[str, float]
    voltages_pu: Dict[str, float]
    voltages_kv: Dict[str, float]
    slack_power_mw: float
    total_losses_mw: float
    execution_time_ms: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "converged": self.converged,
            "iterations": self.iterations,
            "angles_deg": self.angles_deg,
            "flows_mw": self.flows_mw,
            "losses_mw": self.losses_mw,
            "voltages_pu": self.voltages_pu,
            "slack_power_mw": self.slack_power_mw,
            "total_losses_mw": self.total_losses_mw,
            "execution_time_ms": self.execution_time_ms
        }


class DCPowerFlow:
    """
    DC Power Flow solver for radial distribution networks.
    
    Assumptions:
    - X >> R (reactance dominates)
    - sin(θ) ≈ θ (small angle approximation)
    - |V| ≈ 1.0 pu (flat voltage profile)
    
    Suitable for:
    - Quick power flow estimates
    - Screening studies
    - Real-time applications
    """
    
    def __init__(self, base_mva: float = 100.0, base_kv: float = 33.0,
                 dv_dp_sensitivity: float = -0.112,
                 slack_voltage_pu: float = 0.95,
                 use_measured_sensitivity: bool = False):
        """
        Initialize DC power flow solver.
        
        Args:
            base_mva: Base power for per-unit system
            base_kv: Base voltage for per-unit system
            dv_dp_sensitivity: Voltage sensitivity (pu/MW) from measurements
            slack_voltage_pu: Voltage at slack bus (default 0.95 for low voltage network)
            use_measured_sensitivity: Use measured -0.112 pu/MW as cumulative sensitivity
        """
        self.base_mva = base_mva
        self.base_kv = base_kv
        self.dv_dp_sensitivity = dv_dp_sensitivity
        self.slack_voltage_pu = slack_voltage_pu
        self.use_measured_sensitivity = use_measured_sensitivity
        
        # Calibrated sensitivities by line segment (pu/MW)
        # Adjusted to more realistic values for 33kV distribution
        # Original measured -0.112 seems to be cumulative from slack
        self.line_sensitivities = {
            "pilcaniyeu_comallo": -0.015,      # Main line (104 km)
            "comallo_jacobacci": -0.018,       # Medium distance (96 km)
            "jacobacci_maquinchao": -0.020,   # Long segment (75 km)
            "maquinchao_menucos": -0.022      # End of line (58 km)
        }
        
        # Local load sensitivity (additional voltage drop due to local load)
        self.local_sensitivity = -0.005  # pu/MW
        
        # Initialize network components
        self.line_params = LineParameters()
        self.network = NetworkBuilder(self.line_params)
        
        # Build matrices
        self.Y = self.network.build_ybus_dc(base_mva)
        self.B = self.network.build_b_matrix(self.Y)
        
        # Validate topology
        is_valid, issues = self.network.validate_topology()
        if not is_valid:
            logger.warning(f"Topology issues found: {issues}")
        
        logger.info(f"DC Power Flow initialized: {self.network.n_nodes} nodes, "
                   f"{len(self.line_params.lines)} lines")
    
    def solve(self, generation_mw: Dict[str, float], 
              loads_mw: Dict[str, float]) -> PowerFlowResult:
        """
        Solve DC power flow.
        
        Args:
            generation_mw: Dictionary of node_id -> generation in MW
            loads_mw: Dictionary of node_id -> load in MW
            
        Returns:
            PowerFlowResult with solution
        """
        start_time = datetime.now()
        
        # Form power injection vector (in per-unit)
        P = self._form_power_vector(generation_mw, loads_mw)
        
        # Remove slack bus row
        P_reduced = np.delete(P, self.network.slack_index)
        
        # Solve B * theta = P
        try:
            theta_reduced = spsolve(self.B, P_reduced)
            converged = True
        except Exception as e:
            logger.error(f"Failed to solve DC power flow: {e}")
            return self._failed_result()
        
        # Reconstruct full angle vector (slack = 0)
        theta = np.zeros(self.network.n_nodes)
        mask = np.ones(self.network.n_nodes, dtype=bool)
        mask[self.network.slack_index] = False
        theta[mask] = theta_reduced
        
        # Convert to dictionary
        angles_rad = {node_id: theta[idx] 
                     for node_id, idx in self.network.node_index.items()}
        angles_deg = {node_id: np.degrees(angle) 
                     for node_id, angle in angles_rad.items()}
        
        # Calculate line flows
        flows_mw = self._calculate_flows(theta)
        
        # First estimate voltages (needed for loss calculation)
        voltages_pu = self._estimate_voltages(flows_mw, loads_mw)
        voltages_kv = {node: v * self.base_kv for node, v in voltages_pu.items()}
        
        # Calculate improved losses considering voltage levels
        losses_mw = self._calculate_losses_improved(flows_mw, voltages_pu)
        total_losses = sum(losses_mw.values())
        
        # Calculate slack power
        slack_id = self.network.index_node[self.network.slack_index]
        total_gen = sum(generation_mw.values())
        total_load = sum(loads_mw.values())
        slack_gen = generation_mw.get(slack_id, 0.0)
        slack_power = total_load + total_losses - (total_gen - slack_gen)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        result = PowerFlowResult(
            converged=converged,
            iterations=1,  # DC power flow is direct
            angles_rad=angles_rad,
            angles_deg=angles_deg,
            flows_mw=flows_mw,
            losses_mw=losses_mw,
            voltages_pu=voltages_pu,
            voltages_kv=voltages_kv,
            slack_power_mw=slack_power,
            total_losses_mw=total_losses,
            execution_time_ms=execution_time
        )
        
        # Log summary
        logger.info(f"DC Power Flow solved in {execution_time:.1f}ms: "
                   f"Slack={slack_power:.2f}MW, Losses={total_losses:.2f}MW")
        
        return result
    
    def _form_power_vector(self, generation_mw: Dict[str, float],
                          loads_mw: Dict[str, float]) -> np.ndarray:
        """Form net power injection vector in per-unit."""
        P = np.zeros(self.network.n_nodes)
        
        # Add generation (positive injection)
        for node_id, gen in generation_mw.items():
            if node_id in self.network.node_index:
                idx = self.network.node_index[node_id]
                P[idx] += gen / self.base_mva
        
        # Subtract loads (negative injection)
        for node_id, load in loads_mw.items():
            if node_id in self.network.node_index:
                idx = self.network.node_index[node_id]
                P[idx] -= load / self.base_mva
        
        return P
    
    def _calculate_flows(self, theta: np.ndarray) -> Dict[str, float]:
        """
        Calculate line flows from angles.
        
        Flow from i to j: P_ij = (theta_i - theta_j) / x_ij
        """
        flows = {}
        
        for line_id, line in self.line_params.lines.items():
            # Get node indices
            i = self.network.node_index[line.from_node]
            j = self.network.node_index[line.to_node]
            
            # Calculate angle difference
            theta_diff = theta[i] - theta[j]
            
            # Calculate flow in per-unit
            x_pu = line.x_total / ((self.base_kv ** 2) / self.base_mva)
            flow_pu = theta_diff / x_pu
            
            # Convert to MW
            flows[line_id] = flow_pu * self.base_mva
        
        return flows
    
    def _estimate_voltages_corrected(self, flows_mw: Dict[str, float],
                          loads_mw: Dict[str, float]) -> Dict[str, float]:
        """
        Corrected voltage estimation with:
        - Realistic base voltage (0.95 pu at slack)
        - Calibrated sensitivities by line
        - Local load effects
        - Physical voltage limits
        """
        voltages = {}
        slack_id = self.network.index_node[self.network.slack_index]
        voltages[slack_id] = self.slack_voltage_pu  # Realistic slack voltage
        
        # Build parent map for tree traversal
        parent = {}
        visited = {slack_id}
        queue = [slack_id]
        
        # First pass: build tree structure
        while queue:
            current = queue.pop(0)
            for neighbor in self.network.graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
        
        # Second pass: calculate voltages in tree order
        for node in self.network.graph.nodes():
            if node == slack_id:
                continue
                
            if node in parent:
                parent_node = parent[node]
                parent_v = voltages[parent_node]
                
                # Find line between parent and node
                line = None
                line_id = None
                for lid, l in self.line_params.lines.items():
                    if (l.from_node == parent_node and l.to_node == node) or \
                       (l.from_node == node and l.to_node == parent_node):
                        line = l
                        line_id = lid
                        break
                
                if line:
                    # Get power flow through line
                    flow = abs(flows_mw.get(line_id, 0.0))
                    
                    # Use calibrated sensitivity for this line
                    sensitivity = self.line_sensitivities.get(line_id, self.dv_dp_sensitivity)
                    
                    # Calculate voltage drop due to flow
                    # Note: sensitivity is negative, so this will be negative
                    flow_drop = sensitivity * flow
                    
                    # Additional drop due to local load at node
                    local_load = loads_mw.get(node, 0.0)
                    load_drop = self.local_sensitivity * local_load
                    
                    # Apply drops (negative sensitivities mean voltage decreases)
                    voltages[node] = parent_v + flow_drop + load_drop
                    
                    # Debug logging
                    if node == "comallo":
                        logger.debug(f"Comallo voltage calc: {parent_v:.3f} + {flow_drop:.3f} + {load_drop:.3f} = {voltages[node]:.3f}")
                    
                    # Apply physical limits
                    voltages[node] = max(0.80, min(1.05, voltages[node]))
                else:
                    # If no line found, use parent voltage with small drop
                    voltages[node] = parent_v - 0.01
        
        return voltages
    
    def _estimate_voltages(self, flows_mw: Dict[str, float],
                          loads_mw: Dict[str, float]) -> Dict[str, float]:
        """Use corrected voltage estimation method."""
        if self.use_measured_sensitivity:
            return self._estimate_voltages_measured(flows_mw, loads_mw)
        else:
            return self._estimate_voltages_corrected(flows_mw, loads_mw)
    
    def _estimate_voltages_measured(self, flows_mw: Dict[str, float],
                                   loads_mw: Dict[str, float]) -> Dict[str, float]:
        """
        Estimate voltages using measured cumulative sensitivity.
        
        The -0.112 pu/MW sensitivity appears to be cumulative from slack to end nodes.
        This method distributes the voltage drop proportionally along the path.
        """
        voltages = {}
        slack_id = self.network.index_node[self.network.slack_index]
        voltages[slack_id] = self.slack_voltage_pu
        
        # Calculate electrical distance from slack
        distances = self._calculate_electrical_distances()
        max_distance = max(distances.values())
        
        # For each node, estimate voltage based on electrical distance and load
        for node in self.network.graph.nodes():
            if node == slack_id:
                continue
            
            # Get electrical distance (normalized)
            distance_factor = distances.get(node, 0) / max_distance if max_distance > 0 else 0
            
            # Total load downstream (simplified - just local load)
            local_load = loads_mw.get(node, 0.0)
            
            # Apply measured sensitivity scaled by distance
            # The further from slack, the more voltage drop
            voltage_drop = self.dv_dp_sensitivity * local_load * distance_factor
            
            # Calculate voltage
            voltages[node] = self.slack_voltage_pu + voltage_drop
            
            # Apply physical limits
            voltages[node] = max(0.80, min(1.05, voltages[node]))
        
        return voltages
    
    def _calculate_electrical_distances(self) -> Dict[str, float]:
        """Calculate electrical distance (total impedance) from slack to each node."""
        import networkx as nx
        
        distances = {}
        slack_id = self.network.index_node[self.network.slack_index]
        
        # For each node, find shortest path and sum impedances
        for node in self.network.graph.nodes():
            if node == slack_id:
                distances[node] = 0.0
                continue
            
            try:
                path = nx.shortest_path(self.network.graph, slack_id, node)
                total_distance = 0.0
                
                # Sum impedances along path
                for i in range(len(path) - 1):
                    from_node = path[i]
                    to_node = path[i + 1]
                    
                    # Find line between nodes
                    for line in self.line_params.lines.values():
                        if (line.from_node == from_node and line.to_node == to_node) or \
                           (line.from_node == to_node and line.to_node == from_node):
                            total_distance += abs(line.z_total)
                            break
                
                distances[node] = total_distance
            except nx.NetworkXNoPath:
                distances[node] = float('inf')
        
        return distances
    
    def _calculate_losses_improved(self, flows_mw: Dict[str, float],
                                  voltages_pu: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate losses considering R effect and actual voltage levels.
        
        Losses increase when voltage is low due to higher current for same power.
        """
        losses = {}
        power_factor = 0.9
        
        for line_id, flow_mw in flows_mw.items():
            line = self.line_params.get_line(line_id)
            if not line:
                continue
            
            # Get average voltage between line terminals
            v_from = voltages_pu.get(line.from_node, 1.0)
            v_to = voltages_pu.get(line.to_node, 1.0)
            v_avg_pu = (v_from + v_to) / 2
            v_avg_kv = v_avg_pu * self.base_kv
            
            # Current considering actual voltage
            # I = P / (sqrt(3) * V * PF)
            current_a = abs(flow_mw) * 1000 / (np.sqrt(3) * v_avg_kv * power_factor)
            
            # Losses = 3 * I² * R
            loss_mw = 3 * (current_a ** 2) * line.r_total / 1e6
            
            # Apply voltage correction factor
            # Lower voltage -> higher current -> more losses
            nominal_v = 1.0
            v_factor = (nominal_v / v_avg_pu) ** 2
            losses[line_id] = loss_mw * v_factor
        
        return losses
    
    def _failed_result(self) -> PowerFlowResult:
        """Return result for failed power flow."""
        empty_dict = {}
        return PowerFlowResult(
            converged=False,
            iterations=0,
            angles_rad=empty_dict,
            angles_deg=empty_dict,
            flows_mw=empty_dict,
            losses_mw=empty_dict,
            voltages_pu=empty_dict,
            voltages_kv=empty_dict,
            slack_power_mw=0.0,
            total_losses_mw=0.0,
            execution_time_ms=0.0
        )
    
    def validate_solution(self, result: PowerFlowResult,
                         generation_mw: Dict[str, float],
                         loads_mw: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate power flow solution.
        
        Checks:
        - Power balance
        - Voltage limits
        - Line loading
        """
        issues = []
        
        # Check power balance
        total_gen = sum(generation_mw.values()) + result.slack_power_mw
        total_load = sum(loads_mw.values())
        total_losses = result.total_losses_mw
        imbalance = abs(total_gen - total_load - total_losses)
        
        if imbalance > 0.1:  # 0.1 MW tolerance
            issues.append(f"Power imbalance: {imbalance:.3f} MW")
        
        # Check voltage limits
        for node, v_pu in result.voltages_pu.items():
            if v_pu < 0.90:
                issues.append(f"Low voltage at {node}: {v_pu:.3f} pu")
            elif v_pu > 1.05:
                issues.append(f"High voltage at {node}: {v_pu:.3f} pu")
        
        # Check line loading
        for line_id, flow in result.flows_mw.items():
            line = self.line_params.get_line(line_id)
            if line:
                max_mw = line.ampacity * self.base_kv * np.sqrt(3) * 0.9 / 1000
                if abs(flow) > max_mw:
                    issues.append(f"Line {line_id} overloaded: "
                                f"{abs(flow):.1f} MW > {max_mw:.1f} MW")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def get_network_stats(self) -> Dict:
        """Get network statistics."""
        return self.network.get_network_stats()