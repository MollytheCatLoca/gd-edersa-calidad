#!/usr/bin/env python3
"""
Análisis detallado del flujo de potencia DC
Genera tabla con flujos, pérdidas y costos por nodo
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.power_flow.dc_power_flow import DCPowerFlow
from src.economics.economic_evaluator import EconomicEvaluator
from dashboard.pages.utils import get_data_manager
import pandas as pd
import numpy as np

def analyze_dc_powerflow():
    """Ejecuta análisis DC y genera tabla detallada."""
    
    # Inicializar componentes
    pf = DCPowerFlow()
    dm = get_data_manager()
    evaluator = EconomicEvaluator()
    
    # Obtener datos del sistema
    nodes_data = dm.get_nodes()
    edges_data = dm.get_edges()
    
    # Escenario de carga pico
    load_scenario = {
        "pilcaniyeu": 3.5,
        "jacobacci": 2.5,
        "maquinchao": 4.5,
        "los_menucos": 3.0
    }
    
    # GD actual en Los Menucos
    generation = {
        "los_menucos": 1.8  # MW
    }
    
    # Ejecutar flujo DC
    result = pf.solve(load_scenario, generation)
    
    # Preparar datos para la tabla
    nodes_info = []
    
    # Usar los nodos del resultado
    for node_id, angle_deg in result.angles_deg.items():
        # Datos del nodo
        node_data = {
            'Nodo': node_id.upper(),
            'Distancia (km)': 0,  # Se actualizará
            'Carga (MW)': load_scenario.get(node_id, 0),
            'Generación (MW)': generation.get(node_id, 0),
            'Inyección Neta (MW)': generation.get(node_id, 0) - load_scenario.get(node_id, 0),
            'Ángulo (°)': f"{angle_deg:.2f}",
            'Voltaje (pu)': f"{result.voltages_pu.get(node_id, 0):.4f}",
            'Voltaje (kV)': f"{result.voltages_pu.get(node_id, 0) * 33:.2f}"
        }
        
        nodes_info.append(node_data)
    
    # Actualizar distancias desde origen
    distances = {
        'pilcaniyeu': 0,
        'jacobacci': 150,
        'maquinchao': 210,
        'los_menucos': 270
    }
    
    for node in nodes_info:
        node_name = node['Nodo'].lower()
        node['Distancia (km)'] = distances.get(node_name, 0)
    
    # Crear DataFrame de nodos
    df_nodes = pd.DataFrame(nodes_info)
    
    # Analizar flujos por línea
    lines_info = []
    total_losses = 0
    
    for line_id, flow_mw in result.flows_mw.items():
        # Obtener datos de la línea
        # line_id está en formato "pilcaniyeu_comallo"
        parts = line_id.split('_')
        if len(parts) >= 2:
            from_node = parts[0]
            to_node = parts[1]
        else:
            # Formato alternativo con guión
            if '-' in line_id:
                from_node, to_node = line_id.split('-', 1)
            else:
                continue
        
        edge_id = f"{from_node}-{to_node}"
        edge_data = {}
        
        # Buscar en edges_data
        if edges_data.ok():
            if isinstance(edges_data.data, dict):
                edge_data = edges_data.data.get(edge_id, {})
            else:
                # Si es lista, buscar
                for edge in edges_data.data:
                    if edge.get('id') == edge_id:
                        edge_data = edge
                        break
        
        # Calcular pérdidas usando result.losses_mw
        losses_mw = result.losses_mw.get(line_id, 0)
        total_losses += losses_mw
        
        # Calcular costos
        energy_cost = 62.5  # USD/MWh
        hours_year = 8760
        capacity_factor = 0.3
        
        annual_energy = abs(flow_mw) * hours_year * capacity_factor
        annual_losses = losses_mw * hours_year * capacity_factor
        annual_cost = annual_losses * energy_cost
        
        # Obtener resistencia de la línea
        r_pu = edge_data.get('r_pu', 0.05)  # Valor por defecto si no está disponible
        
        line_data = {
            'Línea': f"{from_node.upper()} → {to_node.upper()}",
            'Longitud (km)': edge_data.get('length_km', 0),
            'Conductor': edge_data.get('conductor_type', 'N/A'),
            'R (pu)': f"{r_pu:.4f}",
            'Flujo (MW)': f"{flow_mw:.3f}",
            'Pérdidas (MW)': f"{losses_mw:.4f}",
            'Pérdidas (%)': f"{(losses_mw/abs(flow_mw)*100) if flow_mw != 0 else 0:.2f}",
            'Energía Anual (MWh)': f"{annual_energy:.0f}",
            'Pérdidas Anuales (MWh)': f"{annual_losses:.0f}",
            'Costo Pérdidas (USD/año)': f"${annual_cost:,.0f}"
        }
        
        lines_info.append(line_data)
    
    # Crear DataFrame de líneas
    df_lines = pd.DataFrame(lines_info)
    
    # Resumen económico
    summary = {
        'Carga Total (MW)': sum(load_scenario.values()),
        'Generación GD (MW)': sum(generation.values()),
        'Importación Red (MW)': sum(load_scenario.values()) - sum(generation.values()),
        'Pérdidas Totales (MW)': result.total_losses_mw,
        'Pérdidas (%)': result.total_losses_mw / sum(load_scenario.values()) * 100,
        'Voltaje Mínimo (pu)': min(result.voltages_pu.values()),
        'Voltaje Máximo (pu)': max(result.voltages_pu.values()),
        'Costo Anual Pérdidas (USD)': result.total_losses_mw * 8760 * 0.3 * 62.5,
        'Costo GD Actual (USD/MWh)': 122.7
    }
    
    # Generar salida Markdown
    output = []
    output.append("# Análisis de Flujo de Potencia DC - Sistema Línea Sur")
    output.append("\n## Resumen del Sistema")
    output.append(f"\n- **Carga Total**: {summary['Carga Total (MW)']:.1f} MW")
    output.append(f"- **Generación GD**: {summary['Generación GD (MW)']:.1f} MW")
    output.append(f"- **Importación desde Red**: {summary['Importación Red (MW)']:.1f} MW")
    output.append(f"- **Pérdidas Totales**: {summary['Pérdidas Totales (MW)']:.3f} MW ({summary['Pérdidas (%)']:.1f}%)")
    output.append(f"- **Rango de Voltaje**: {summary['Voltaje Mínimo (pu)']:.3f} - {summary['Voltaje Máximo (pu)']:.3f} pu")
    output.append(f"- **Costo Anual Pérdidas**: ${summary['Costo Anual Pérdidas (USD)']:,.0f} USD")
    
    output.append("\n## Estado de Nodos")
    output.append("\n" + df_nodes.to_markdown(index=False))
    
    output.append("\n## Flujos y Pérdidas por Línea")
    output.append("\n" + df_lines.to_markdown(index=False))
    
    output.append("\n## Análisis de Costos")
    output.append("\n### Costos Operativos Actuales")
    output.append(f"- **Energía de Red**: $62.50/MWh")
    output.append(f"- **GD Los Menucos**: $122.70/MWh")
    output.append(f"- **Costo Pérdidas Anuales**: ${summary['Costo Anual Pérdidas (USD)']:,.0f}")
    
    # Calcular costo total anual
    energy_from_grid = summary['Importación Red (MW)'] * 8760 * 0.3
    energy_from_gd = summary['Generación GD (MW)'] * 8760 * 0.3 * 0.5  # GD opera 50% del tiempo
    
    cost_grid = energy_from_grid * 62.5
    cost_gd = energy_from_gd * 122.7
    
    output.append(f"\n### Costo Total Anual de Energía")
    output.append(f"- **Energía desde Red**: {energy_from_grid:,.0f} MWh × $62.50 = ${cost_grid:,.0f}")
    output.append(f"- **Energía desde GD**: {energy_from_gd:,.0f} MWh × $122.70 = ${cost_gd:,.0f}")
    output.append(f"- **Total**: ${(cost_grid + cost_gd):,.0f}")
    
    output.append("\n## Observaciones Clave")
    output.append("\n1. **Voltajes Críticos**: Todos los nodos operan por debajo de 0.95 pu")
    output.append("2. **Pérdidas Elevadas**: Las pérdidas aumentan significativamente en los tramos finales")
    output.append("3. **GD Insuficiente**: La GD actual (1.8 MW) no es suficiente para mejorar significativamente los voltajes")
    output.append("4. **Costo GD**: El alto costo de la GD térmica ($122.7/MWh) limita su operación")
    
    # Guardar resultado
    output_text = "\n".join(output)
    
    with open(project_root / "dc_powerflow_analysis.md", "w") as f:
        f.write(output_text)
    
    print(output_text)
    
    return output_text

if __name__ == "__main__":
    analyze_dc_powerflow()