#!/usr/bin/env python3
"""
Simple test to verify BESS constants are centralized correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard', 'pages', 'utils'))

def test_bess_constants():
    """Test that BESS constants are properly centralized"""
    print("Testing BESS constants centralization...")
    
    from constants import (
        BESS_CONSTANTS, BESS_TECHNOLOGIES, BESS_TOPOLOGIES,
        BESSTechnology, BESSTopology, BESSStrategy
    )
    
    # Test basic constants
    assert "CYCLE_ENERGY_THRESHOLD_MWH" in BESS_CONSTANTS
    assert BESS_CONSTANTS["CYCLE_ENERGY_THRESHOLD_MWH"] == 0.01
    print("✓ BESS_CONSTANTS contains cycle threshold")
    
    # Test technologies
    assert "modern_lfp" in BESS_TECHNOLOGIES
    assert "standard" in BESS_TECHNOLOGIES
    assert "premium" in BESS_TECHNOLOGIES
    print("✓ BESS_TECHNOLOGIES contains all expected technologies")
    
    # Test technology parameters
    lfp_params = BESS_TECHNOLOGIES["modern_lfp"]
    assert "η_charge" in lfp_params
    assert "η_discharge" in lfp_params
    assert "η_roundtrip" in lfp_params
    assert "soc_min" in lfp_params
    assert "soc_max" in lfp_params
    assert "c_rate_max" in lfp_params
    assert "description" in lfp_params
    print("✓ BESS technology parameters are complete")
    
    # Test topologies
    assert "parallel_ac" in BESS_TOPOLOGIES
    assert "series_dc" in BESS_TOPOLOGIES
    assert "hybrid" in BESS_TOPOLOGIES
    print("✓ BESS_TOPOLOGIES contains all expected topologies")
    
    # Test topology parameters
    ac_params = BESS_TOPOLOGIES["parallel_ac"]
    assert "efficiency_penalty" in ac_params
    assert "flexibility" in ac_params
    assert "description" in ac_params
    print("✓ BESS topology parameters are complete")
    
    # Test enums
    assert BESSTechnology.MODERN_LFP == "modern_lfp"
    assert BESSTopology.PARALLEL_AC == "parallel_ac"
    assert BESSStrategy.TIME_SHIFT == "time_shift"
    print("✓ BESS enums work correctly")
    
    # Test enum values match dictionary keys
    for tech in BESSTechnology:
        assert tech.value in BESS_TECHNOLOGIES, f"Technology enum {tech.value} not in BESS_TECHNOLOGIES"
    print("✓ Technology enum values match dictionary keys")
    
    for topo in BESSTopology:
        assert topo.value in BESS_TOPOLOGIES, f"Topology enum {topo.value} not in BESS_TOPOLOGIES"
    print("✓ Topology enum values match dictionary keys")
    
    # Test immutability
    try:
        BESS_CONSTANTS["NEW_KEY"] = "should fail"
        assert False, "Should not be able to modify BESS_CONSTANTS"
    except TypeError:
        print("✓ BESS_CONSTANTS is immutable")
    
    print("\n🎉 All BESS constants tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_bess_constants()
        print("\n✓ FASE 1 BESS integration constants are working correctly!")
    except Exception as e:
        print(f"\n❌ FASE 1 BESS integration failed: {e}")
        sys.exit(1)