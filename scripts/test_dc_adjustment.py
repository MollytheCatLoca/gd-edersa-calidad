#!/usr/bin/env python3
"""
Debug script to test DC power flow adjustments
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.power_flow import DCPowerFlow

def test_simple_case():
    """Test a simple case to debug voltage calculation."""
    print("Testing DC Power Flow Adjustments")
    print("="*60)
    
    # Initialize with explicit parameters
    pf = DCPowerFlow(
        base_mva=100.0, 
        base_kv=33.0,
        dv_dp_sensitivity=-0.112,
        slack_voltage_pu=0.95
    )
    
    # Simple test case
    generation = {}  # No local generation
    loads = {
        "pilcaniyeu": 2.0,
        "comallo": 1.0,
        "jacobacci": 1.5,
        "maquinchao": 2.5,
        "los_menucos": 1.8
    }
    
    print(f"\nTest Case:")
    print(f"  Slack voltage: {pf.slack_voltage_pu} pu")
    print(f"  Total load: {sum(loads.values())} MW")
    print(f"\nLine sensitivities:")
    for line_id, sens in pf.line_sensitivities.items():
        print(f"  {line_id}: {sens} pu/MW")
    
    # Solve
    result = pf.solve(generation, loads)
    
    print(f"\nResults:")
    print(f"  Converged: {result.converged}")
    print(f"  Slack power: {result.slack_power_mw:.2f} MW")
    print(f"  Total losses: {result.total_losses_mw:.2f} MW")
    
    print(f"\nLine Flows:")
    for line_id, flow in sorted(result.flows_mw.items()):
        print(f"  {line_id}: {flow:.2f} MW")
    
    print(f"\nVoltages:")
    for node, v_pu in sorted(result.voltages_pu.items()):
        print(f"  {node}: {v_pu:.3f} pu")
    
    # Check sensitivity at Maquinchao
    # From Pilcaniyeu to Maquinchao, total distance affects voltage
    expected_drop = abs(pf.line_sensitivities["jacobacci_maquinchao"]) * loads["maquinchao"]
    print(f"\nExpected voltage drop at Maquinchao due to local load: {expected_drop:.3f} pu")
    
    # Manual calculation check
    print("\nManual voltage calculation check:")
    print(f"  Pilcaniyeu (slack): {pf.slack_voltage_pu:.3f} pu")
    
    # Trace path to Maquinchao
    flow_pil_com = result.flows_mw["pilcaniyeu_comallo"]
    drop_pil_com = pf.line_sensitivities["pilcaniyeu_comallo"] * abs(flow_pil_com)
    v_comallo_calc = pf.slack_voltage_pu + drop_pil_com
    print(f"  Comallo: {pf.slack_voltage_pu:.3f} + ({pf.line_sensitivities['pilcaniyeu_comallo']:.3f} * {abs(flow_pil_com):.1f}) = {v_comallo_calc:.3f} pu")


if __name__ == "__main__":
    test_simple_case()