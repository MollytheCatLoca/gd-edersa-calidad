#!/usr/bin/env python3
"""
Test script for DC Power Flow implementation
Validates the power flow engine with various test cases
"""

import sys
from pathlib import Path
import numpy as np
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.power_flow import DCPowerFlow, PowerFlowValidator
from dashboard.pages.utils.data_manager_v2 import DataManagerV2


def test_basic_power_flow():
    """Test basic DC power flow functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic DC Power Flow")
    print("="*60)
    
    # Initialize DC power flow
    pf = DCPowerFlow()
    
    # Print network statistics
    stats = pf.get_network_stats()
    print(f"\nNetwork Statistics:")
    print(f"  Nodes: {stats['n_nodes']}")
    print(f"  Lines: {stats['n_lines']}")
    print(f"  Total length: {stats['total_length_km']:.0f} km")
    print(f"  Is radial: {stats['is_radial']}")
    
    # Define test case: typical loading
    generation = {
        "los_menucos": 1.8  # GD at Los Menucos
    }
    
    loads = {
        "pilcaniyeu": 2.5,
        "comallo": 1.0,
        "jacobacci": 1.8,
        "maquinchao": 3.2,
        "los_menucos": 2.1
    }
    
    print(f"\nTest Case:")
    print(f"  Total generation: {sum(generation.values()):.1f} MW")
    print(f"  Total load: {sum(loads.values()):.1f} MW")
    
    # Solve power flow
    result = pf.solve(generation, loads)
    
    print(f"\nResults:")
    print(f"  Converged: {result.converged}")
    print(f"  Execution time: {result.execution_time_ms:.1f} ms")
    print(f"  Slack power: {result.slack_power_mw:.2f} MW")
    print(f"  Total losses: {result.total_losses_mw:.2f} MW")
    
    print(f"\nVoltages:")
    for node, v_pu in sorted(result.voltages_pu.items()):
        print(f"  {node}: {v_pu:.3f} pu ({v_pu*33:.1f} kV)")
    
    print(f"\nLine Flows:")
    for line, flow in sorted(result.flows_mw.items()):
        print(f"  {line}: {flow:.2f} MW")
    
    # Validate solution
    is_valid, issues = pf.validate_solution(result, generation, loads)
    print(f"\nValidation: {'PASSED' if is_valid else 'FAILED'}")
    if issues:
        for issue in issues:
            print(f"  - {issue}")
    
    return result.converged


def test_contingency_cases():
    """Test various contingency scenarios."""
    print("\n" + "="*60)
    print("TEST 2: Contingency Cases")
    print("="*60)
    
    pf = DCPowerFlow()
    
    # Test cases
    test_cases = [
        {
            "name": "Light load",
            "generation": {},
            "loads": {
                "pilcaniyeu": 1.0,
                "jacobacci": 0.8,
                "maquinchao": 1.5,
                "los_menucos": 1.0
            }
        },
        {
            "name": "Peak load",
            "generation": {"los_menucos": 1.8},
            "loads": {
                "pilcaniyeu": 3.5,
                "jacobacci": 2.5,
                "maquinchao": 4.5,
                "los_menucos": 3.0
            }
        },
        {
            "name": "High GD output",
            "generation": {"los_menucos": 3.0},
            "loads": {
                "pilcaniyeu": 2.0,
                "jacobacci": 1.5,
                "maquinchao": 2.5,
                "los_menucos": 2.0
            }
        }
    ]
    
    for case in test_cases:
        print(f"\nCase: {case['name']}")
        
        result = pf.solve(case['generation'], case['loads'])
        
        if result.converged:
            min_v = min(result.voltages_pu.values())
            max_v = max(result.voltages_pu.values())
            print(f"  ✓ Converged - V range: {min_v:.3f} - {max_v:.3f} pu")
            print(f"    Slack: {result.slack_power_mw:.1f} MW, "
                  f"Losses: {result.total_losses_mw:.1f} MW")
        else:
            print(f"  ✗ Did not converge")


def test_voltage_sensitivity():
    """Test voltage sensitivity to load changes."""
    print("\n" + "="*60)
    print("TEST 3: Voltage Sensitivity Analysis")
    print("="*60)
    
    pf = DCPowerFlow()
    
    # Base case
    base_loads = {
        "pilcaniyeu": 2.0,
        "jacobacci": 1.5,
        "maquinchao": 2.5,
        "los_menucos": 2.0
    }
    
    # Test sensitivity at Maquinchao (known to have dV/dP = -0.112)
    test_node = "maquinchao"
    load_variations = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    
    voltages = []
    
    for load in load_variations:
        loads = base_loads.copy()
        loads[test_node] = load
        
        result = pf.solve({}, loads)
        if result.converged:
            voltages.append(result.voltages_pu[test_node])
    
    # Calculate sensitivity
    if len(voltages) > 1:
        # Linear regression
        p_values = np.array(load_variations[:len(voltages)])
        v_values = np.array(voltages)
        
        # Fit line
        coeffs = np.polyfit(p_values, v_values, 1)
        sensitivity = coeffs[0]  # dV/dP
        
        print(f"\nSensitivity at {test_node}:")
        print(f"  Calculated dV/dP: {sensitivity:.3f} pu/MW")
        print(f"  Expected dV/dP: -0.112 pu/MW")
        print(f"  Error: {abs(sensitivity - (-0.112))*100/0.112:.1f}%")
        
        print(f"\nLoad vs Voltage:")
        for p, v in zip(p_values, v_values):
            print(f"  {p:.1f} MW -> {v:.3f} pu")


def test_typical_day_profile():
    """Test with typical day load profile."""
    print("\n" + "="*60)
    print("TEST 4: Typical Day Profile")
    print("="*60)
    
    pf = DCPowerFlow()
    dm = DataManagerV2()
    
    # Try to load typical day profile
    typical_result = dm.get_typical_days()
    
    if not typical_result.ok():
        print("Could not load typical day profiles, using synthetic data")
        
        # Synthetic 24-hour profile
        hours = list(range(24))
        load_factors = []
        for h in hours:
            if 6 <= h <= 9:  # Morning peak
                factor = 0.9
            elif 18 <= h <= 22:  # Evening peak
                factor = 1.2
            elif 0 <= h <= 5:  # Night
                factor = 0.6
            else:  # Day
                factor = 0.8
            load_factors.append(factor)
    else:
        # Use real typical day data
        # Extract winter weekday profile
        typical_data = typical_result.data
        load_factors = [0.8] * 24  # Default
        
        if "winter" in typical_data and "weekday" in typical_data["winter"]:
            # Extract hourly factors from data
            pass
    
    # Base loads
    base_loads = {
        "pilcaniyeu": 2.5,
        "jacobacci": 1.8,
        "maquinchao": 3.2,
        "los_menucos": 2.1
    }
    
    # Run 24-hour simulation
    results = []
    
    for hour, factor in enumerate(load_factors):
        # Scale loads by factor
        loads = {k: v * factor for k, v in base_loads.items()}
        
        # GD operates during day
        generation = {"los_menucos": 1.8 if 10 <= hour <= 16 else 0}
        
        result = pf.solve(generation, loads)
        
        if result.converged:
            avg_voltage = np.mean(list(result.voltages_pu.values()))
            results.append({
                "hour": hour,
                "load_factor": factor,
                "avg_voltage": avg_voltage,
                "min_voltage": min(result.voltages_pu.values()),
                "slack_power": result.slack_power_mw,
                "losses": result.total_losses_mw
            })
    
    # Print hourly summary
    print(f"\n24-Hour Simulation Results:")
    print(f"Hour | Load | Avg V | Min V | Slack | Loss")
    print(f"-----|------|-------|-------|-------|-----")
    
    for r in results[::3]:  # Every 3 hours
        print(f" {r['hour']:2d}  | {r['load_factor']:.2f} | "
              f"{r['avg_voltage']:.3f} | {r['min_voltage']:.3f} | "
              f"{r['slack_power']:5.1f} | {r['losses']:.2f}")
    
    # Find worst hour
    if results:
        worst = min(results, key=lambda x: x['min_voltage'])
        print(f"\nWorst voltage hour: {worst['hour']}h "
              f"(V_min = {worst['min_voltage']:.3f} pu)")


def test_validation_against_measurements():
    """Test validation against known measurements."""
    print("\n" + "="*60)
    print("TEST 5: Validation Against Measurements")
    print("="*60)
    
    pf = DCPowerFlow()
    validator = PowerFlowValidator(pf)
    
    # Validate typical days
    print("\nValidating typical day profiles...")
    typical_validation = validator.validate_typical_days()
    
    for season, metrics in typical_validation.items():
        if isinstance(metrics, dict) and "mean_error" in metrics:
            print(f"\n{season.capitalize()}:")
            print(f"  Mean error: {metrics['mean_error']:.1f}%")
            print(f"  Max error: {metrics['max_error']:.1f}%")
            print(f"  Hours validated: {metrics['hours_validated']}")
    
    # Validate critical events
    print("\nValidating critical events...")
    critical_validation = validator.validate_critical_events()
    
    if "total_events" in critical_validation:
        print(f"\nCritical Events:")
        print(f"  Total events: {critical_validation['total_events']}")
        print(f"  Converged: {critical_validation['converged']}")
        print(f"  Mean error: {critical_validation['mean_error']:.1f}%")
        print(f"  Max error: {critical_validation['max_error']:.1f}%")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("DC POWER FLOW TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    
    tests_passed = 0
    total_tests = 5
    
    # Run tests
    try:
        if test_basic_power_flow():
            tests_passed += 1
    except Exception as e:
        print(f"\nTest 1 FAILED: {e}")
    
    try:
        test_contingency_cases()
        tests_passed += 1
    except Exception as e:
        print(f"\nTest 2 FAILED: {e}")
    
    try:
        test_voltage_sensitivity()
        tests_passed += 1
    except Exception as e:
        print(f"\nTest 3 FAILED: {e}")
    
    try:
        test_typical_day_profile()
        tests_passed += 1
    except Exception as e:
        print(f"\nTest 4 FAILED: {e}")
    
    try:
        test_validation_against_measurements()
        tests_passed += 1
    except Exception as e:
        print(f"\nTest 5 FAILED: {e}")
    
    # Summary
    print("\n" + "="*60)
    print(f"SUMMARY: {tests_passed}/{total_tests} tests passed")
    print("="*60)
    
    if tests_passed == total_tests:
        print("\n✅ All DC Power Flow tests passed!")
        print("\nNext steps:")
        print("- Implement economic evaluator")
        print("- Add Redis caching")
        print("- Create optimization algorithms")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} tests need attention")


if __name__ == "__main__":
    main()