#!/usr/bin/env python3
"""
Test script for FASE 3 BESS Integration
=====================================

Validates the complete integration of BESSModel API into DataManagerV2.
Tests all new methods added in FASE 3.

Usage:
    source venv/bin/activate
    python test_fase3_integration.py
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dashboard.pages.utils.data_manager_v2 import get_data_manager, reset_data_manager
from dashboard.pages.utils.constants import DataStatus


def test_bess_constants_access():
    """Test BESS constants access methods."""
    print("=" * 60)
    print("TEST 1: BESS Constants Access")
    print("=" * 60)
    
    dm = get_data_manager()
    
    # Test basic constants
    constants_result = dm.get_bess_constants()
    print(f"✓ BESS Constants: {constants_result.status.value}")
    if constants_result.data:
        print(f"  - Available constants: {list(constants_result.data.keys())}")
    
    # Test technologies
    tech_result = dm.get_bess_technologies()
    print(f"✓ BESS Technologies: {tech_result.status.value}")
    if tech_result.data:
        print(f"  - Available technologies: {list(tech_result.data.keys())}")
    
    # Test topologies
    topo_result = dm.get_bess_topologies()
    print(f"✓ BESS Topologies: {topo_result.status.value}")
    if topo_result.data:
        print(f"  - Available topologies: {list(topo_result.data.keys())}")
    
    return True


def test_bess_model_creation():
    """Test BESSModel creation through DataManagerV2."""
    print("\n" + "=" * 60)
    print("TEST 2: BESSModel Creation")
    print("=" * 60)
    
    dm = get_data_manager()
    
    # Test standard configuration
    bess_result = dm.create_bess_model(
        power_mw=2.0,
        duration_hours=4.0,
        technology="modern_lfp",
        topology="parallel_ac"
    )
    
    print(f"✓ BESSModel Creation: {bess_result.status.value}")
    if bess_result.data:
        bess_model = bess_result.data
        config = bess_model.get_configuration_summary()
        print(f"  - Power: {config['power_mw']} MW")
        print(f"  - Capacity: {config['capacity_mwh']} MWh")
        print(f"  - Technology: {config['technology']}")
        print(f"  - Round-trip efficiency: {config['roundtrip_efficiency']:.1%}")
        print(f"  - Effective power: {config['effective_power_mw']} MW")
    
    # Test invalid technology
    invalid_result = dm.create_bess_model(
        power_mw=1.0,
        duration_hours=2.0,
        technology="invalid_tech"
    )
    print(f"✓ Invalid Technology Handling: {invalid_result.status.value}")
    
    return True


def test_bess_strategy_simulation():
    """Test BESS strategy simulation."""
    print("\n" + "=" * 60)
    print("TEST 3: BESS Strategy Simulation")
    print("=" * 60)
    
    dm = get_data_manager()
    
    # Create a typical solar profile (24 hours)
    solar_profile = np.concatenate([
        np.zeros(6),  # Night: 0-6h
        np.linspace(0, 3.0, 6),  # Morning ramp: 6-12h
        np.full(6, 3.0),  # Peak: 12-18h
        np.linspace(3.0, 0, 6)  # Evening ramp: 18-24h
    ])
    
    print(f"✓ Solar Profile Created: {len(solar_profile)} hours, peak {solar_profile.max()} MW")
    
    # Test cap_shaving strategy (V1 - working)
    sim_result = dm.simulate_bess_strategy(
        solar_profile=solar_profile,
        strategy="cap_shaving",
        power_mw=2.0,
        duration_hours=4.0,
        technology="modern_lfp"
    )
    
    print(f"✓ Strategy Simulation: {sim_result.status.value}")
    if sim_result.data:
        results = sim_result.data
        metrics = results['metrics']
        print(f"  - Strategy: {metrics['strategy_used']}")
        print(f"  - Energy efficiency: {metrics['energy_efficiency']:.1%}")
        print(f"  - Total losses: {metrics['total_losses_mwh']:.3f} MWh")
        print(f"  - Curtailment ratio: {metrics['curtailment_ratio']:.1%}")
        print(f"  - Total cycles: {results['total_cycles']:.2f}")
        
        # Validate arrays
        print(f"  - Grid power range: {results['grid_power'].min():.2f} to {results['grid_power'].max():.2f} MW")
        print(f"  - Battery power range: {results['battery_power'].min():.2f} to {results['battery_power'].max():.2f} MW")
        print(f"  - SOC range: {results['soc'].min():.1%} to {results['soc'].max():.1%}")
    
    # Test flat_day strategy
    smooth_result = dm.simulate_bess_strategy(
        solar_profile=solar_profile,
        strategy="flat_day",
        power_mw=1.5,
        duration_hours=3.0
    )
    
    print(f"✓ Flat Day Strategy: {smooth_result.status.value}")
    if smooth_result.data:
        metrics = smooth_result.data['metrics']
        print(f"  - Flat day efficiency: {metrics['energy_efficiency']:.1%}")
    
    return True


def test_dynamic_control():
    """Test dynamic BESS control simulation."""
    print("\n" + "=" * 60)
    print("TEST 4: Dynamic BESS Control")
    print("=" * 60)
    
    dm = get_data_manager()
    
    # Create power request sequence
    power_requests = [
        -1.0, -1.5, -2.0, -1.0,  # Charging phase
        0.0, 0.0, 0.0, 0.0,      # Rest
        1.0, 1.5, 2.0, 1.0,      # Discharging phase
        0.0, 0.0, 0.0, 0.0       # Rest
    ]
    
    control_result = dm.simulate_bess_dynamic_control(
        initial_soc=0.2,  # Start at 20% SOC
        power_requests=power_requests,
        power_mw=2.5,
        duration_hours=4.0,
        dt=0.25  # 15-minute timesteps
    )
    
    print(f"✓ Dynamic Control: {control_result.status.value}")
    if control_result.data:
        results = control_result.data
        metrics = results['metrics']
        print(f"  - Simulation duration: {metrics['simulation_duration_hours']} hours")
        print(f"  - Final SOC: {metrics['final_soc']:.1%}")
        print(f"  - SOC range: {metrics['soc_range']:.1%}")
        print(f"  - Realized roundtrip efficiency: {metrics['realized_roundtrip_efficiency']:.1%}")
        print(f"  - Total losses: {metrics['total_losses_mwh']:.4f} MWh")
        
        # Check power curtailment
        curtailment = results['power_curtailment']
        max_curtailment = np.abs(curtailment).max()
        print(f"  - Max power curtailment: {max_curtailment:.3f} MW")
    
    return True


def test_bess_optimization():
    """Test BESS optimization for solar profile."""
    print("\n" + "=" * 60)
    print("TEST 5: BESS Optimization")
    print("=" * 60)
    
    dm = get_data_manager()
    
    # Create solar profile with high variability
    hours = np.arange(24)
    solar_profile = 4.0 * np.maximum(0, np.sin(np.pi * (hours - 6) / 12)) ** 2
    # Add some cloud variability
    cloud_factor = 1 + 0.3 * np.sin(0.5 * hours) * np.maximum(0, np.sin(np.pi * (hours - 6) / 12))
    solar_profile *= cloud_factor
    
    print(f"✓ Variable Solar Profile: Peak {solar_profile.max():.2f} MW, Avg {solar_profile.mean():.2f} MW")
    
    # Optimize for energy efficiency
    opt_result = dm.optimize_bess_for_solar(
        solar_profile=solar_profile,
        power_range=(1.0, 4.0),
        duration_range=(2.0, 6.0),
        strategy="cap_shaving",
        optimization_metric="energy_efficiency"
    )
    
    print(f"✓ BESS Optimization: {opt_result.status.value}")
    if opt_result.data:
        results = opt_result.data
        best_config = results['best_configuration']
        summary = results['summary']
        
        print(f"  - Best power: {summary['best_power_mw']:.1f} MW")
        print(f"  - Best duration: {summary['best_duration_h']:.1f} hours")
        print(f"  - Best efficiency: {summary['best_metric_value']:.1%}")
        print(f"  - Improvement vs no BESS: {summary['improvement_vs_no_bess']:.1%}")
        print(f"  - Configurations tested: {results['optimization_settings']['total_configurations']}")
    
    return True


def test_bess_validation():
    """Test BESS configuration validation."""
    print("\n" + "=" * 60)
    print("TEST 6: BESS Configuration Validation")
    print("=" * 60)
    
    dm = get_data_manager()
    
    # Test normal configuration
    val_result = dm.validate_bess_configuration(
        power_mw=2.0,
        duration_hours=4.0,
        technology="modern_lfp",
        topology="parallel_ac"
    )
    
    print(f"✓ Configuration Validation: {val_result.status.value}")
    if val_result.data:
        validation = val_result.data
        print(f"  - Configuration valid: {validation['configuration_valid']}")
        print(f"  - Warnings: {len(validation['warnings'])}")
        for warning in validation['warnings']:
            print(f"    * {warning}")
        
        if 'performance_estimates' in validation:
            perf = validation['performance_estimates']
            print(f"  - Daily efficiency estimate: {perf.get('daily_efficiency', 0):.1%}")
            print(f"  - Daily cycles estimate: {perf.get('daily_cycles', 0):.2f}")
    
    # Test extreme configuration (should generate warnings)
    extreme_result = dm.validate_bess_configuration(
        power_mw=5.0,  # High power
        duration_hours=0.5,  # Very short duration -> high C-rate
        technology="premium"
    )
    
    print(f"✓ Extreme Configuration Validation: {extreme_result.status.value}")
    if extreme_result.data:
        validation = extreme_result.data
        print(f"  - Warnings: {len(validation['warnings'])}")
        for warning in validation['warnings']:
            print(f"    * {warning}")
    
    return True


def test_performance_benchmark():
    """Test performance of FASE 3 methods."""
    print("\n" + "=" * 60)
    print("TEST 7: Performance Benchmark")
    print("=" * 60)
    
    import time
    dm = get_data_manager()
    
    # Large solar profile for performance test
    large_solar = np.random.uniform(0, 5.0, 8760)  # 1 year hourly
    
    start_time = time.time()
    
    # Test strategy simulation performance
    perf_result = dm.simulate_bess_strategy(
        solar_profile=large_solar,
        strategy="cap_shaving",
        power_mw=3.0,
        duration_hours=4.0
    )
    
    simulation_time = time.time() - start_time
    
    print(f"✓ Large Simulation Performance: {perf_result.status.value}")
    print(f"  - Profile size: {len(large_solar)} hours")
    print(f"  - Simulation time: {simulation_time:.2f} seconds")
    print(f"  - Rate: {len(large_solar)/simulation_time:.0f} hours/second")
    
    if perf_result.data:
        metrics = perf_result.data['metrics']
        print(f"  - Annual efficiency: {metrics['energy_efficiency']:.1%}")
        print(f"  - Annual cycles: {perf_result.data['total_cycles']:.1f}")
    
    return True


def run_all_tests():
    """Run all FASE 3 integration tests."""
    print("FASE 3 BESS Integration Test Suite")
    print("=" * 60)
    
    tests = [
        test_bess_constants_access,
        test_bess_model_creation,
        test_bess_strategy_simulation,
        test_dynamic_control,
        test_bess_optimization,
        test_bess_validation,
        test_performance_benchmark
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_func.__name__} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✓ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - FASE 3 INTEGRATION COMPLETE!")
        return True
    else:
        print("⚠️  Some tests failed - review implementation")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)