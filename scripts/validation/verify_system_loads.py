#!/usr/bin/env python3
"""
Verificar las cargas reales del sistema desde DataManager
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from dashboard.pages.utils import get_data_manager

def verify_loads():
    """Verificar cargas reales del sistema."""
    dm = get_data_manager()
    
    # Obtener datos del sistema
    system_data = dm.get_system_data()
    nodes_data = dm.get_nodes()
    
    print("=== VERIFICACIÓN DE CARGAS DEL SISTEMA ===\n")
    
    # Resumen del sistema
    if system_data and isinstance(system_data, tuple) and len(system_data) > 0:
        data = system_data[0] if isinstance(system_data[0], dict) else system_data[1]
        summary = data.get('system_summary', {})
        total_load = summary.get('total_load', {})
        print(f"Carga Total del Sistema: {total_load.get('active_power_mw', 'N/A')} MW")
        print(f"Potencia Reactiva Total: {total_load.get('reactive_power_mvar', 'N/A')} MVAr")
        print(f"Factor de Potencia: {total_load.get('power_factor', 'N/A')}")
        print()
    
    # Cargas por nodo
    print("Cargas por Nodo:")
    print("-" * 50)
    
    total_mw = 0
    total_mvar = 0
    
    if hasattr(nodes_data, 'ok') and nodes_data.ok():
        nodes = nodes_data.data
    elif isinstance(nodes_data, dict):
        nodes = nodes_data
    else:
        nodes = {}
        
    if isinstance(nodes, dict):
        for node_id, node_info in nodes.items():
            load_mw = node_info.get('load_mw', 0)
            load_mvar = node_info.get('load_mvar', 0)
            total_mw += load_mw
            total_mvar += load_mvar
            
            print(f"{node_id.upper():15} {load_mw:6.2f} MW   {load_mvar:6.2f} MVAr")
    else:
        # Si es lista
        for node in nodes:
            node_id = node.get('id', 'Unknown')
            load_mw = node.get('load_mw', 0)
            load_mvar = node.get('load_mvar', 0)
            total_mw += load_mw
            total_mvar += load_mvar
            
            print(f"{node_id.upper():15} {load_mw:6.2f} MW   {load_mvar:6.2f} MVAr")
    
    print("-" * 50)
    print(f"{'TOTAL':15} {total_mw:6.2f} MW   {total_mvar:6.2f} MVAr")
    print()
    
    # Generación
    print("Generación Distribuida:")
    print("-" * 50)
    gd_costs = dm.get_gd_costs()
    print(f"Los Menucos GD: {gd_costs['potencia_mw']} MW")
    print(f"Horas/día: {gd_costs['horas_dia_base']} horas")
    print(f"Costo: ${gd_costs['costo_por_mwh']}/MWh")
    print()
    
    # Balance
    print("Balance del Sistema:")
    print("-" * 50)
    print(f"Carga Total: {total_mw:.2f} MW")
    print(f"Generación Local: {gd_costs['potencia_mw']} MW")
    print(f"Importación desde Red: {total_mw - gd_costs['potencia_mw']:.2f} MW")
    
    return total_mw, gd_costs['potencia_mw']

if __name__ == "__main__":
    verify_loads()