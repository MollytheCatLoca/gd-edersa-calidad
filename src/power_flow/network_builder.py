"""
Network Builder for DC Power Flow
Constructs network matrices and topology
"""

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix
from typing import Dict, List, Tuple, Optional, Set
import logging
from dataclasses import dataclass
import networkx as nx

from .line_parameters import LineParameters, Line

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """Represents a bus/node in the network."""
    id: str
    name: str
    type: str  # 'slack', 'pq', 'pv'
    voltage_kv: float = 33.0
    is_slack: bool = False
    
    def __hash__(self):
        return hash(self.id)


class NetworkBuilder:
    """
    Builds network matrices for DC power flow analysis.
    
    Handles:
    - Y-bus matrix construction
    - Node indexing
    - Topology analysis
    """
    
    def __init__(self, line_params: LineParameters):
        """Initialize with line parameters."""
        self.line_params = line_params
        self.nodes: Dict[str, Node] = {}
        self.node_index: Dict[str, int] = {}
        self.index_node: Dict[int, str] = {}
        self.n_nodes = 0
        self.slack_index = 0
        self.graph = nx.Graph()
        
        self._initialize_nodes()
        self._build_graph()
        
    def _initialize_nodes(self):
        """Initialize nodes from line data."""
        # Define Línea Sur nodes
        node_data = [
            {"id": "pilcaniyeu", "name": "ET Pilcaniyeu", "type": "slack", "is_slack": True},
            {"id": "comallo", "name": "Comallo", "type": "pq"},
            {"id": "jacobacci", "name": "Ing. Jacobacci", "type": "pq"},
            {"id": "maquinchao", "name": "Maquinchao", "type": "pq"},
            {"id": "los_menucos", "name": "Los Menucos", "type": "pq"}
        ]
        
        # Create nodes
        for i, data in enumerate(node_data):
            node = Node(**data)
            self.nodes[node.id] = node
            self.node_index[node.id] = i
            self.index_node[i] = node.id
            
            if node.is_slack:
                self.slack_index = i
        
        self.n_nodes = len(self.nodes)
        logger.info(f"Initialized {self.n_nodes} nodes, slack: {self.index_node[self.slack_index]}")
    
    def _build_graph(self):
        """Build NetworkX graph for topology analysis."""
        # Add nodes
        for node_id, node in self.nodes.items():
            self.graph.add_node(node_id, **{
                "name": node.name,
                "type": node.type,
                "index": self.node_index[node_id]
            })
        
        # Add edges from lines
        for line in self.line_params.lines.values():
            self.graph.add_edge(
                line.from_node,
                line.to_node,
                line_id=line.id,
                length_km=line.length_km,
                impedance=line.z_total
            )
    
    def build_ybus_dc(self, base_mva: float = 100.0) -> csr_matrix:
        """
        Build Y-bus matrix for DC power flow.
        
        For DC power flow:
        - Y_ij = -1/X_ij for line between i and j
        - Y_ii = sum of all Y_ij connected to i
        - All values in per-unit
        
        Args:
            base_mva: Base MVA for per-unit conversion
            
        Returns:
            Sparse Y-bus matrix
        """
        base_kv = 33.0
        base_impedance = (base_kv ** 2) / base_mva
        
        # Use lil_matrix for efficient construction
        Y = lil_matrix((self.n_nodes, self.n_nodes), dtype=np.float64)
        
        # Process each line
        for line in self.line_params.lines.values():
            i = self.node_index[line.from_node]
            j = self.node_index[line.to_node]
            
            # For DC power flow, use only reactance
            x_pu = line.x_total / base_impedance
            
            if x_pu > 0:  # Avoid division by zero
                y_ij = -1.0 / x_pu
                
                # Off-diagonal elements
                Y[i, j] = y_ij
                Y[j, i] = y_ij
                
                # Diagonal elements
                Y[i, i] -= y_ij
                Y[j, j] -= y_ij
        
        # Convert to CSR for efficient operations
        Y_csr = Y.tocsr()
        
        # Log matrix properties
        logger.info(f"Y-bus matrix: {self.n_nodes}x{self.n_nodes}, "
                   f"non-zeros: {Y_csr.nnz}, "
                   f"sparsity: {1 - Y_csr.nnz / (self.n_nodes**2):.2%}")
        
        return Y_csr
    
    def build_b_matrix(self, Y: csr_matrix) -> csr_matrix:
        """
        Build B matrix for DC power flow (Y-bus without slack row/column).
        
        Args:
            Y: Full Y-bus matrix
            
        Returns:
            Reduced B matrix
        """
        # Create index arrays excluding slack
        indices = list(range(self.n_nodes))
        indices.remove(self.slack_index)
        
        # Extract submatrix
        B = Y[np.ix_(indices, indices)]
        
        return B
    
    def get_incidence_matrix(self) -> np.ndarray:
        """
        Build node-branch incidence matrix.
        
        Returns:
            A matrix where A[i,j] = 1 if branch j leaves node i,
                                   -1 if branch j enters node i,
                                    0 otherwise
        """
        n_lines = len(self.line_params.lines)
        A = np.zeros((self.n_nodes, n_lines))
        
        for j, (line_id, line) in enumerate(self.line_params.lines.items()):
            i_from = self.node_index[line.from_node]
            i_to = self.node_index[line.to_node]
            
            A[i_from, j] = 1
            A[i_to, j] = -1
        
        return A
    
    def get_path_to_slack(self, node_id: str) -> List[str]:
        """
        Get path from node to slack bus.
        
        Args:
            node_id: Starting node
            
        Returns:
            List of node IDs in path (including start and end)
        """
        if node_id not in self.nodes:
            return []
        
        slack_id = self.index_node[self.slack_index]
        
        try:
            path = nx.shortest_path(self.graph, node_id, slack_id)
            return path
        except nx.NetworkXNoPath:
            logger.warning(f"No path from {node_id} to slack {slack_id}")
            return []
    
    def get_downstream_nodes(self, node_id: str) -> Set[str]:
        """
        Get all nodes downstream from given node (away from slack).
        
        Args:
            node_id: Starting node
            
        Returns:
            Set of downstream node IDs
        """
        if node_id not in self.nodes:
            return set()
        
        slack_id = self.index_node[self.slack_index]
        
        # Remove edge towards slack to find downstream
        temp_graph = self.graph.copy()
        path_to_slack = self.get_path_to_slack(node_id)
        
        if len(path_to_slack) >= 2:
            # Remove edge to upstream node
            upstream_node = path_to_slack[1]
            temp_graph.remove_edge(node_id, upstream_node)
        
        # Find all reachable nodes
        downstream = set(nx.node_connected_component(temp_graph, node_id))
        downstream.remove(node_id)  # Don't include the node itself
        
        return downstream
    
    def is_radial(self) -> bool:
        """Check if network is radial (tree structure)."""
        return nx.is_tree(self.graph)
    
    def get_network_stats(self) -> Dict[str, any]:
        """Get network statistics."""
        stats = {
            "n_nodes": self.n_nodes,
            "n_lines": len(self.line_params.lines),
            "is_radial": self.is_radial(),
            "diameter": nx.diameter(self.graph) if nx.is_connected(self.graph) else -1,
            "average_degree": sum(dict(self.graph.degree()).values()) / self.n_nodes,
            "total_length_km": self.line_params.get_total_line_length()
        }
        
        # Add node degrees
        stats["node_degrees"] = dict(self.graph.degree())
        
        return stats
    
    def validate_topology(self) -> Tuple[bool, List[str]]:
        """
        Validate network topology for power flow.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check connectivity
        if not nx.is_connected(self.graph):
            components = list(nx.connected_components(self.graph))
            issues.append(f"Network has {len(components)} disconnected components")
        
        # Check for islands without slack
        slack_id = self.index_node[self.slack_index]
        for component in nx.connected_components(self.graph):
            if slack_id not in component:
                issues.append(f"Component {component} has no slack bus")
        
        # Check for parallel lines (simplified)
        for node1 in self.graph.nodes():
            for node2 in self.graph.neighbors(node1):
                if self.graph.number_of_edges(node1, node2) > 1:
                    issues.append(f"Parallel lines between {node1} and {node2}")
        
        # Warn if not radial
        if not self.is_radial():
            issues.append("Network is not radial (contains loops)")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            logger.info("Network topology validation passed")
        else:
            for issue in issues:
                logger.warning(f"Topology issue: {issue}")
        
        return is_valid, issues