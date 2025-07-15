"""
Network Topology for Phase 5
Simple representation of the Línea Sur network
"""

import networkx as nx
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NetworkTopology:
    """
    Represents the electrical network topology.
    For Línea Sur: Radial 33kV network
    """
    
    def __init__(self):
        """Initialize empty network."""
        self.graph = nx.DiGraph()
        self.nodes_data: Dict[str, Any] = {}
        self.edges_data: Dict[str, Any] = {}
        
    def _build_graph(self):
        """Build NetworkX graph from nodes and edges data."""
        # Add nodes
        for node_id, node_info in self.nodes_data.items():
            self.graph.add_node(node_id, **node_info)
            
        # Add edges  
        for edge_id, edge_info in self.edges_data.items():
            # Parse edge_id like "pilcaniyeu-comallo"
            if "-" in edge_id:
                from_node, to_node = edge_id.split("-", 1)
                self.graph.add_edge(from_node, to_node, **edge_info)
                
        logger.info(f"Built network with {self.graph.number_of_nodes()} nodes "
                   f"and {self.graph.number_of_edges()} edges")
                   
    def get_all_nodes(self) -> List[str]:
        """Get list of all node IDs."""
        return list(self.graph.nodes())
        
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighboring nodes."""
        return list(self.graph.neighbors(node_id))
        
    def is_radial(self) -> bool:
        """Check if network is radial (tree structure)."""
        return nx.is_tree(self.graph.to_undirected())