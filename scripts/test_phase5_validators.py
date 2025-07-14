#!/usr/bin/env python3
"""
Test script for Phase 5 validators
Validates the power balance, Kirchhoff laws, and low voltage analyzers
"""

import sys
from pathlib import Path
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.validation.power_balance import PowerBalanceValidator
from src.validation.kirchhoff_laws import KirchhoffValidator
from src.validation.low_voltage_analyzer import LowVoltageAnalyzer
from dashboard.pages.utils.data_manager_v2 import DataManagerV2


def test_power_balance_validator():
    """Test power balance validation with realistic network state."""
    print("\n" + "="*60)
    print("TESTING POWER BALANCE VALIDATOR")
    print("="*60)
    
    validator = PowerBalanceValidator()
    
    # Create a realistic network state for Línea Sur
    network_state = {
        "generation": {
            "pilcaniyeu": 0.0,  # No local generation
            "gd_los_menucos": 1.8  # GD operating
        },
        "loads": {
            "pilcaniyeu": 2.5,
            "jacobacci": 1.8,
            "maquinchao": 3.2,
            "los_menucos": 2.1
        },
        "line_losses": {
            "pilca_jacob": 0.15,
            "jacob_maqui": 0.12,
            "maqui_menu": 0.08
        },
        "transformer_losses": {
            "xfmr_pilca": 0.02,
            "xfmr_jacob": 0.015,
            "xfmr_maqui": 0.025,
            "xfmr_menu": 0.018
        }
    }
    
    # Test 1: Balanced case (need to import from system)
    import_from_system = sum(network_state["loads"].values()) + \
                        sum(network_state["line_losses"].values()) + \
                        sum(network_state["transformer_losses"].values()) - \
                        sum(network_state["generation"].values())
    
    network_state["generation"]["system_import"] = import_from_system
    
    result = validator.validate(network_state)
    
    print(f"\nTest 1 - Balanced Case:")
    print(f"  Total Generation: {result.total_generation:.3f} MW")
    print(f"  Total Load: {result.total_load:.3f} MW")
    print(f"  Total Losses: {result.total_losses:.3f} MW")
    print(f"  Imbalance: {result.imbalance:.6f} MW ({result.imbalance_percent*100:.4f}%)")
    print(f"  Valid: {result.is_valid}")
    
    # Test 2: Imbalanced case
    network_state["generation"]["system_import"] -= 0.5  # Remove 0.5 MW
    
    result2 = validator.validate(network_state)
    
    print(f"\nTest 2 - Imbalanced Case:")
    print(f"  Imbalance: {result2.imbalance:.3f} MW ({result2.imbalance_percent*100:.2f}%)")
    print(f"  Valid: {result2.is_valid}")
    print(f"  Violations: {len(result2.violations)}")
    for v in result2.violations:
        print(f"    - {v['message']}")
    
    # Test 3: High losses case (typical for low voltage)
    network_state["line_losses"]["pilca_jacob"] = 0.5  # Very high losses
    
    result3 = validator.validate(network_state)
    
    print(f"\nTest 3 - High Losses Case:")
    print(f"  Total Losses: {result3.total_losses:.3f} MW")
    print(f"  Loss Percentage: {(result3.total_losses/result3.total_generation)*100:.1f}%")
    print(f"  Violations: {[v['type'] for v in result3.violations]}")
    
    return all([result.is_valid, not result2.is_valid, len(result3.violations) > 0])


def test_kirchhoff_validator():
    """Test Kirchhoff's laws validation."""
    print("\n" + "="*60)
    print("TESTING KIRCHHOFF LAWS VALIDATOR")
    print("="*60)
    
    validator = KirchhoffValidator()
    
    # Test 1: Single node current balance
    print("\nTest 1 - Single Node Current Balance:")
    
    # Node with 3.2 MW load at 0.89 pu (30.37 kV)
    p_mw = 3.2
    q_mvar = 1.5  # Assuming 0.9 PF
    v_kv = 30.37  # 0.92 * 33 kV
    
    # Calculate current
    s_mva = np.sqrt(p_mw**2 + q_mvar**2)
    i_load = (s_mva * 1000) / (np.sqrt(3) * v_kv)
    
    print(f"  Load: {p_mw} MW, {q_mvar} MVAr")
    print(f"  Voltage: {v_kv} kV ({v_kv/33:.3f} pu)")
    print(f"  Load Current: {i_load:.1f} A")
    
    # Balanced case
    line_flows = {
        "line_in": i_load,
        "line_out": 0
    }
    
    violation = validator.validate_current_law(
        "test_node",
        line_flows,
        load_current=i_load,
        generation_current=0
    )
    
    print(f"  Balanced case - Violation: {violation is None}")
    
    # Imbalanced case
    line_flows["line_in"] = i_load * 0.95  # 5% less
    
    violation2 = validator.validate_current_law(
        "test_node",
        line_flows,
        load_current=i_load,
        generation_current=0
    )
    
    if violation2:
        print(f"  Imbalanced case - Violation detected: {violation2.imbalance:.2f} A")
    
    # Test 2: Network-wide validation
    print("\nTest 2 - Network Validation:")
    
    network_state = {
        "node_currents": {
            "maquinchao": {
                "load_current": i_load,
                "generation_current": 0,
                "line_flows": {
                    "from_jacobacci": i_load,
                    "to_menucos": 0
                }
            }
        },
        "node_voltages": {
            "maquinchao": v_kv
        },
        "line_voltage_drops": {}
    }
    
    result = validator.validate_network(network_state)
    
    print(f"  Nodes checked: {result.nodes_checked}")
    print(f"  Valid: {result.is_valid}")
    print(f"  Max current imbalance: {result.max_imbalance_current:.3f} A")
    
    return violation is None and violation2 is not None


def test_low_voltage_analyzer():
    """Test low voltage analysis."""
    print("\n" + "="*60)
    print("TESTING LOW VOLTAGE ANALYZER")
    print("="*60)
    
    analyzer = LowVoltageAnalyzer()
    
    # Create realistic network state with low voltages
    network_state = {
        "node_voltages": {
            "pilcaniyeu": 0.95,  # At limit
            "jacobacci": 0.92,   # Below limit
            "maquinchao": 0.89,  # Critical
            "los_menucos": 0.91, # Below limit
            "comallo": 0.88     # Very critical
        },
        "node_loads": {
            "pilcaniyeu": 2.5,
            "jacobacci": 1.8,
            "maquinchao": 3.2,
            "los_menucos": 2.1,
            "comallo": 0.8
        },
        "duration_hours": 1.0
    }
    
    # Analyze violations
    result = analyzer.analyze_voltage_violations(network_state)
    
    print(f"\nVoltage Analysis Results:")
    print(f"  Total nodes: {result.total_nodes}")
    print(f"  Nodes below 0.95 pu: {result.nodes_below_095} ({result.nodes_below_095/result.total_nodes*100:.0f}%)")
    print(f"  Nodes below 0.90 pu: {result.nodes_below_090}")
    print(f"  Critical nodes: {result.critical_nodes}")
    print(f"  Worst node: {result.worst_node} at {result.worst_voltage_pu:.3f} pu")
    print(f"  Total energy at risk: {result.total_energy_at_risk_mwh:.2f} MWh")
    print(f"  Total cost of violations: ${result.total_cost_violations_usd:,.0f}")
    
    # Show top violations
    print(f"\nTop Voltage Violations:")
    for v in sorted(result.violations, key=lambda x: x.voltage_pu)[:3]:
        print(f"  {v.node_id}: {v.voltage_pu:.3f} pu ({v.severity}) - Cost: ${v.estimated_cost_usd:.0f}")
    
    # Test improvement options
    print(f"\nImprovement Options:")
    for opt in result.improvement_options[:3]:
        print(f"  {opt.node_id} - {opt.method}: ΔV={opt.delta_v_pu:.3f} pu, "
              f"Cost=${opt.cost_usd:,.0f} (${opt.cost_per_pu:,.0f}/pu)")
    
    # Test temporal analysis
    print(f"\nTesting 24-hour Analysis...")
    
    # Create hourly states with varying voltages
    hourly_states = []
    for hour in range(24):
        # Voltage drops during peak hours (18-22)
        if 18 <= hour <= 22:
            v_factor = 0.95  # 5% worse during peak
        else:
            v_factor = 1.0
        
        hour_state = {
            "node_voltages": {k: v * v_factor for k, v in network_state["node_voltages"].items()},
            "node_loads": network_state["node_loads"],
            "duration_hours": 1.0
        }
        hourly_states.append(hour_state)
    
    temporal_analysis = analyzer.analyze_temporal_patterns(hourly_states)
    
    print(f"  Worst hour: {temporal_analysis['worst_hour']}h")
    print(f"  Worst voltage in day: {temporal_analysis['worst_voltage_day']:.3f} pu")
    print(f"  Total daily cost: ${temporal_analysis['total_cost_day_usd']:,.0f}")
    print(f"  Peak violation hours: {temporal_analysis['peak_violation_hours']}")
    
    return result.nodes_below_095 == 4  # All nodes except Pilcaniyeu


def main():
    """Run all validator tests."""
    print("\n" + "="*60)
    print("PHASE 5.1 VALIDATOR TESTS")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    
    # Check if DataManager works
    dm = DataManagerV2()
    config = dm.get_power_flow_config()
    if config.ok():
        print(f"\n✓ DataManager connected - Power flow config loaded")
        print(f"  Max iterations: {config.data.get('max_iterations')}")
        print(f"  Tolerance: {config.data.get('tolerance')}")
    else:
        print("\n✗ DataManager connection failed")
        return
    
    # Run tests
    tests_passed = 0
    
    try:
        if test_power_balance_validator():
            print("\n✓ Power Balance Validator: PASSED")
            tests_passed += 1
        else:
            print("\n✗ Power Balance Validator: FAILED")
    except Exception as e:
        print(f"\n✗ Power Balance Validator: ERROR - {e}")
    
    try:
        if test_kirchhoff_validator():
            print("\n✓ Kirchhoff Laws Validator: PASSED")
            tests_passed += 1
        else:
            print("\n✗ Kirchhoff Laws Validator: FAILED")
    except Exception as e:
        print(f"\n✗ Kirchhoff Laws Validator: ERROR - {e}")
    
    try:
        if test_low_voltage_analyzer():
            print("\n✓ Low Voltage Analyzer: PASSED")
            tests_passed += 1
        else:
            print("\n✗ Low Voltage Analyzer: FAILED")
    except Exception as e:
        print(f"\n✗ Low Voltage Analyzer: ERROR - {e}")
    
    # Summary
    print("\n" + "="*60)
    print(f"SUMMARY: {tests_passed}/3 tests passed")
    print("="*60)
    
    if tests_passed == 3:
        print("\n🎉 All validators working correctly!")
        print("\nNext steps:")
        print("- Implement economic evaluation framework")
        print("- Set up Redis cache")
        print("- Create integration with real network data")
    else:
        print("\n⚠️  Some validators need attention")


if __name__ == "__main__":
    main()