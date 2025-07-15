"""
Visualization functions for the Línea Sur network topology.

This module provides static and interactive visualization capabilities
for the electrical network using matplotlib, plotly and folium.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import networkx as nx
import folium
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd


class NetworkVisualizer:
    """Handles visualization of the network topology."""
    
    def __init__(self, network_topology):
        """
        Initialize visualizer with a NetworkTopology instance.
        
        Args:
            network_topology: Instance of NetworkTopology class
        """
        self.network = network_topology
        self.graph = network_topology.graph
        
        # Define color schemes
        self.voltage_colors = {
            132: '#FF0000',    # Red for 132 kV
            33: '#0000FF',     # Blue for 33 kV
            13.2: '#00AA00',   # Green for 13.2 kV
        }
        
        self.load_colors = {
            'high': '#FF0000',
            'medium': '#FFA500',
            'low': '#00FF00'
        }
    
    def plot_network_schematic(self, figsize=(16, 10), save_path=None):
        """
        Create a schematic diagram of the network.
        
        Args:
            figsize: Figure size tuple
            save_path: Path to save the figure
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Calculate positions based on distance from origin
        pos = {}
        for node in self.graph.nodes():
            distance = self.graph.nodes[node]['distance_km']
            # Arrange nodes in a line with some vertical offset for clarity
            y_offset = 0.1 * np.sin(distance * 0.05)  # Small sine wave for visual separation
            pos[node] = (distance, y_offset)
        
        # Draw edges with width proportional to thermal limit
        for edge in self.graph.edges(data=True):
            from_pos = pos[edge[0]]
            to_pos = pos[edge[1]]
            
            # Line width based on conductor type
            conductor = edge[2]['conductor_type']
            if '120' in conductor:
                linewidth = 3
            else:
                linewidth = 2
            
            ax.plot([from_pos[0], to_pos[0]], [from_pos[1], to_pos[1]], 
                   'k-', linewidth=linewidth, alpha=0.6)
            
            # Add edge labels (length)
            mid_x = (from_pos[0] + to_pos[0]) / 2
            mid_y = (from_pos[1] + to_pos[1]) / 2
            ax.text(mid_x, mid_y + 0.02, f"{edge[2]['length_km']} km", 
                   ha='center', fontsize=8, alpha=0.7)
        
        # Draw nodes
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            x, y = pos[node]
            
            # Node size based on load
            size = 100 + node_data['load_mw'] * 500
            
            # Node color based on criticality
            if node_data.get('criticality') == 'high':
                color = self.load_colors['high']
            elif node_data['load_mw'] > 0.5:
                color = self.load_colors['medium']
            else:
                color = self.load_colors['low']
            
            # Special markers for nodes with generation or regulation
            if node_data.get('has_generation'):
                ax.scatter(x, y, s=size, c=color, marker='s', 
                          edgecolors='black', linewidth=2, zorder=3)
            elif node_data.get('has_regulation'):
                ax.scatter(x, y, s=size, c=color, marker='^', 
                          edgecolors='black', linewidth=2, zorder=3)
            else:
                ax.scatter(x, y, s=size, c=color, marker='o', 
                          edgecolors='black', linewidth=1, zorder=3)
            
            # Node labels
            ax.text(x, y - 0.08, node_data['name'], 
                   ha='center', va='top', fontsize=10, fontweight='bold')
            
            # Load labels
            load_text = f"{node_data['load_mw']:.2f} MW"
            if node_data.get('population'):
                load_text += f"\n{node_data['population']:,} hab"
            ax.text(x, y + 0.08, load_text, 
                   ha='center', va='bottom', fontsize=8)
        
        # Add legend
        legend_elements = [
            mpatches.Patch(color=self.load_colors['high'], label='Alta criticidad'),
            mpatches.Patch(color=self.load_colors['medium'], label='Media carga'),
            mpatches.Patch(color=self.load_colors['low'], label='Baja carga'),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', 
                      markersize=10, label='Con generación'),
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='gray', 
                      markersize=10, label='Con regulación'),
        ]
        ax.legend(handles=legend_elements, loc='upper left')
        
        # Formatting
        ax.set_xlabel('Distancia desde Pilcaniyeu (km)', fontsize=12)
        ax.set_ylabel('Posición relativa', fontsize=12)
        ax.set_title('Diagrama Esquemático - Sistema Línea Sur 33 kV', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-0.3, 0.3)
        
        # Add system summary
        summary = self.network.get_network_summary()
        summary_text = (f"Carga Total: {summary['total_load_mw']:.2f} MW | "
                       f"Longitud: {summary['total_length_km']:.0f} km | "
                       f"Factor de Potencia: {summary['system_power_factor']:.3f}")
        ax.text(0.5, -0.25, summary_text, transform=ax.transAxes, 
               ha='center', fontsize=11, bbox=dict(boxstyle="round,pad=0.3", 
               facecolor="lightgray", alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, ax
    
    def plot_impedance_diagram(self, figsize=(14, 8), save_path=None):
        """
        Plot accumulated impedance along the line.
        
        Args:
            figsize: Figure size tuple
            save_path: Path to save the figure
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
        
        # Get nodes ordered by distance
        nodes = sorted(self.graph.nodes(), 
                      key=lambda n: self.graph.nodes[n]['distance_km'])
        
        distances = []
        r_accumulated = []
        x_accumulated = []
        z_accumulated = []
        node_labels = []
        
        for node in nodes:
            if node == 'pilcaniyeu':
                distances.append(0)
                r_accumulated.append(0)
                x_accumulated.append(0)
                z_accumulated.append(0)
            else:
                imp = self.network.calculate_accumulated_impedance('pilcaniyeu', node)
                distances.append(self.graph.nodes[node]['distance_km'])
                r_accumulated.append(imp['r_ohm'])
                x_accumulated.append(imp['x_ohm'])
                z_accumulated.append(imp['z_ohm'])
            
            node_labels.append(self.graph.nodes[node]['name'])
        
        # Plot R and X
        ax1.plot(distances, r_accumulated, 'r-', linewidth=2, label='R (Ω)', marker='o')
        ax1.plot(distances, x_accumulated, 'b-', linewidth=2, label='X (Ω)', marker='s')
        ax1.set_ylabel('Impedancia (Ω)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Impedancia Acumulada desde Pilcaniyeu', fontsize=14, fontweight='bold')
        
        # Plot Z magnitude
        ax2.plot(distances, z_accumulated, 'g-', linewidth=2, label='|Z| (Ω)', marker='D')
        ax2.set_xlabel('Distancia (km)', fontsize=12)
        ax2.set_ylabel('Impedancia Total (Ω)', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Add vertical lines at each station
        for i, (d, label) in enumerate(zip(distances, node_labels)):
            if i > 0:  # Skip pilcaniyeu
                ax1.axvline(d, color='gray', alpha=0.3, linestyle='--')
                ax2.axvline(d, color='gray', alpha=0.3, linestyle='--')
                ax2.text(d, ax2.get_ylim()[0], label, rotation=45, 
                        ha='right', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, (ax1, ax2)
    
    def plot_voltage_profile(self, voltages_pu: Dict[str, float], 
                           figsize=(14, 8), save_path=None):
        """
        Plot voltage profile along the line.
        
        Args:
            voltages_pu: Dictionary with node_id: voltage_pu pairs
            figsize: Figure size tuple
            save_path: Path to save the figure
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get nodes ordered by distance
        nodes = sorted(self.graph.nodes(), 
                      key=lambda n: self.graph.nodes[n]['distance_km'])
        
        distances = []
        voltages = []
        node_labels = []
        
        for node in nodes:
            distances.append(self.graph.nodes[node]['distance_km'])
            voltages.append(voltages_pu.get(node, 1.0))
            node_labels.append(self.graph.nodes[node]['name'])
        
        # Plot voltage profile
        ax.plot(distances, voltages, 'b-', linewidth=2, marker='o', markersize=8)
        
        # Add voltage limits
        ax.axhline(1.05, color='r', linestyle='--', alpha=0.5, label='Límite superior (1.05 pu)')
        ax.axhline(0.95, color='r', linestyle='--', alpha=0.5, label='Límite inferior (0.95 pu)')
        ax.axhline(1.0, color='g', linestyle='-', alpha=0.3, label='Nominal (1.0 pu)')
        
        # Fill violation areas
        ax.fill_between(distances, 0.95, voltages, 
                       where=[v < 0.95 for v in voltages], 
                       color='red', alpha=0.2, label='Violación')
        
        # Add station labels
        for d, v, label in zip(distances, voltages, node_labels):
            ax.text(d, v + 0.01, f'{v:.3f}', ha='center', va='bottom', fontsize=8)
            ax.text(d, 0.88, label, rotation=45, ha='right', va='top', fontsize=9)
        
        ax.set_xlabel('Distancia desde Pilcaniyeu (km)', fontsize=12)
        ax.set_ylabel('Tensión (pu)', fontsize=12)
        ax.set_title('Perfil de Tensión - Sistema Línea Sur', fontsize=14, fontweight='bold')
        ax.set_ylim(0.85, 1.1)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, ax
    
    def create_interactive_map(self, save_path=None):
        """
        Create an interactive Folium map of the network.
        
        Args:
            save_path: Path to save the HTML map
            
        Returns:
            Folium map object
        """
        # Calculate center of the map
        lats = [n['coordinates']['lat'] for n in self.graph.nodes.values()]
        lons = [n['coordinates']['lon'] for n in self.graph.nodes.values()]
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], 
                      zoom_start=8,
                      tiles='OpenStreetMap')
        
        # Add nodes as markers
        for node_id, node_data in self.graph.nodes(data=True):
            # Determine marker color based on criticality
            if node_data.get('criticality') == 'high':
                color = 'red'
            elif node_data['load_mw'] > 0.5:
                color = 'orange'
            else:
                color = 'green'
            
            # Create popup text
            popup_text = f"""
            <b>{node_data['name']}</b><br>
            Carga: {node_data['load_mw']:.2f} MW<br>
            Distancia: {node_data['distance_km']} km<br>
            """
            
            if node_data.get('population'):
                popup_text += f"Población: {node_data['population']:,}<br>"
            
            if node_data.get('has_generation'):
                popup_text += "✓ Con generación<br>"
            
            if node_data.get('has_regulation'):
                popup_text += "✓ Con regulación<br>"
            
            # Add marker
            folium.Marker(
                location=[node_data['coordinates']['lat'], 
                         node_data['coordinates']['lon']],
                popup=folium.Popup(popup_text, max_width=200),
                tooltip=node_data['name'],
                icon=folium.Icon(color=color, icon='bolt', prefix='fa')
            ).add_to(m)
        
        # Add lines between nodes
        for edge in self.graph.edges(data=True):
            from_coords = self.graph.nodes[edge[0]]['coordinates']
            to_coords = self.graph.nodes[edge[1]]['coordinates']
            
            # Line weight based on conductor type
            if '120' in edge[2]['conductor_type']:
                weight = 4
            else:
                weight = 3
            
            # Create line
            folium.PolyLine(
                locations=[[from_coords['lat'], from_coords['lon']],
                          [to_coords['lat'], to_coords['lon']]],
                color='blue',
                weight=weight,
                opacity=0.7,
                popup=f"{edge[2]['length_km']} km - {edge[2]['conductor_type']}"
            ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    top: 50px; right: 50px; width: 200px; height: 120px; 
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius: 5px">
        <p style="margin: 10px;"><b>Leyenda</b></p>
        <p style="margin: 10px;"><i class="fa fa-bolt" style="color:red"></i> Alta criticidad</p>
        <p style="margin: 10px;"><i class="fa fa-bolt" style="color:orange"></i> Media carga</p>
        <p style="margin: 10px;"><i class="fa fa-bolt" style="color:green"></i> Baja carga</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        if save_path:
            m.save(save_path)
        
        return m
    
    def create_plotly_network(self):
        """
        Create an interactive Plotly network diagram.
        
        Returns:
            Plotly figure object
        """
        # Get node positions
        pos = {}
        for node in self.graph.nodes():
            coords = self.graph.nodes[node]['coordinates']
            pos[node] = (coords['lon'], coords['lat'])
        
        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        
        # Create node traces
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        node_color = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Node info
            node_data = self.graph.nodes[node]
            text = f"{node_data['name']}<br>"
            text += f"Carga: {node_data['load_mw']:.2f} MW<br>"
            text += f"Distancia: {node_data['distance_km']} km"
            node_text.append(text)
            
            # Size based on load
            size = 15 + node_data['load_mw'] * 20
            node_size.append(size)
            
            # Color based on criticality
            if node_data.get('criticality') == 'high':
                node_color.append('red')
            elif node_data['load_mw'] > 0.5:
                node_color.append('orange')
            else:
                node_color.append('green')
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=False,
                color=node_color,
                size=node_size,
                line_width=2,
                line_color='black'
            )
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Red Eléctrica Línea Sur - Vista Interactiva',
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20, l=5, r=5, t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           plot_bgcolor='white'
                       ))
        
        return fig