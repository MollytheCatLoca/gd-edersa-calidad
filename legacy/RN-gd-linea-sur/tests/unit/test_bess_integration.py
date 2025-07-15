#!/usr/bin/env python3
"""
Test script to verify BESS integration FASE 1 implementation
Verifies:
1. Constants are correctly moved to constants.py
2. BESSModel uses centralized constants
3. DataManager can access BESS constants
4. SolarBESSSimulator works with new structure
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard', 'pages', 'utils'))

def test_constants_import():
    """Test that constants can be imported correctly"""
    print("Testing constants import...")
    
    try:
        from constants import (
            BESS_TECHNOLOGIES, BESS_TOPOLOGIES, BESS_CONSTANTS,
            BESSTechnology, BESSTopology, BESSStrategy
        )
        print("✓ Constants imported successfully")
        
        # Test enums
        assert BESSTechnology.MODERN_LFP == "modern_lfp"
        assert BESSTopology.PARALLEL_AC == "parallel_ac"
        assert BESSStrategy.TIME_SHIFT == "time_shift"
        print("✓ Enums work correctly")
        
        # Test constants structure
        assert "modern_lfp" in BESS_TECHNOLOGIES
        assert "parallel_ac" in BESS_TOPOLOGIES
        assert "CYCLE_ENERGY_THRESHOLD_MWH" in BESS_CONSTANTS
        print("✓ Constants structure is correct")
        
        return True
        
    except Exception as e:
        print(f"✗ Constants import failed: {e}")
        return False

def test_bess_model_integration():
    """Test BESSModel integration with centralized constants"""
    print("\nTesting BESSModel integration...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'battery'))
        from bess_model import BESSModel
        
        # Test creation with string parameters
        bess = BESSModel(
            power_mw=2.0,
            duration_hours=4.0,
            technology="modern_lfp",
            topology="parallel_ac"
        )
        print("✓ BESSModel created with string parameters")
        
        # Test creation with enum parameters
        from constants import BESSTechnology, BESSTopology
        bess_enum = BESSModel(
            power_mw=2.0,
            duration_hours=4.0,
            technology=BESSTechnology.PREMIUM,
            topology=BESSTopology.HYBRID
        )
        print("✓ BESSModel created with enum parameters")
        
        # Test that constants are used
        assert bess.CYCLE_ENERGY_THRESHOLD_MWH == 0.01
        print("✓ BESSModel uses centralized constants")
        
        return True
        
    except Exception as e:
        print(f"✗ BESSModel integration failed: {e}")
        return False

def test_data_manager_integration():
    """Test DataManagerV2 BESS methods"""
    print("\nTesting DataManagerV2 integration...")
    
    try:
        from data_manager_v2 import get_data_manager
        
        dm = get_data_manager()
        
        # Test BESS constants access
        bess_const_result = dm.get_bess_constants()
        assert bess_const_result.status.value == "real"
        assert "CYCLE_ENERGY_THRESHOLD_MWH" in bess_const_result.data
        print("✓ DataManagerV2 can access BESS constants")
        
        # Test BESS technologies access
        tech_result = dm.get_bess_technologies()
        assert tech_result.status.value == "real"
        assert "modern_lfp" in tech_result.data
        print("✓ DataManagerV2 can access BESS technologies")
        
        # Test BESS topologies access
        topo_result = dm.get_bess_topologies()
        assert topo_result.status.value == "real"
        assert "parallel_ac" in topo_result.data
        print("✓ DataManagerV2 can access BESS topologies")
        
        # Test parameter access
        params_result = dm.get_bess_technology_params("modern_lfp")
        assert params_result.status.value == "real"
        assert "η_charge" in params_result.data
        print("✓ DataManagerV2 can access specific technology parameters")
        
        # Test topology parameters
        topo_params_result = dm.get_bess_topology_params("parallel_ac")
        assert topo_params_result.status.value == "real"
        assert "efficiency_penalty" in topo_params_result.data
        print("✓ DataManagerV2 can access specific topology parameters")
        
        return True
        
    except Exception as e:
        print(f"✗ DataManagerV2 integration failed: {e}")
        return False

def test_solar_bess_simulator():
    """Test SolarBESSSimulator with new structure"""
    print("\nTesting SolarBESSSimulator integration...")
    
    try:
        from solar_bess_simulator import SolarBESSSimulator
        
        sim = SolarBESSSimulator()
        
        # Test basic solar simulation
        result = sim.simulate_psfv_only("MAQUINCHAO", 2.0, month=6)
        assert result.status.value == "real"
        print("✓ SolarBESSSimulator basic simulation works")
        
        # Test solar+BESS simulation
        result = sim.simulate_solar_with_bess(
            "MAQUINCHAO", 2.0, 1.0, 4.0, 
            strategy="time_shift"
        )
        assert result.status.value == "real"
        print("✓ SolarBESSSimulator solar+BESS simulation works")
        
        return True
        
    except Exception as e:
        print(f"✗ SolarBESSSimulator integration failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("BESS Integration FASE 1 Tests")
    print("=" * 50)
    
    tests = [
        test_constants_import,
        test_bess_model_integration,
        test_data_manager_integration,
        test_solar_bess_simulator
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All tests passed! FASE 1 integration successful.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())