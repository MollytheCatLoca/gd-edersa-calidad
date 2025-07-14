#!/usr/bin/env python3
"""
Test script to verify cap_shaving_balanced works in the dashboard
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dashboard.pages.utils.solar_bess_simulator import SolarBESSSimulator
from dashboard.pages.utils.models import DataStatus

def test_cap_shaving_balanced_in_dashboard():
    """Test cap_shaving_balanced strategy through the dashboard simulator"""
    
    print("\n" + "="*60)
    print("TESTING CAP_SHAVING_BALANCED IN DASHBOARD")
    print("="*60 + "\n")
    
    # Create simulator instance
    simulator = SolarBESSSimulator()
    
    # Test configuration
    station = "Los Menucos"
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_h = 4.0
    
    # Test 1: With percentile
    print("Test 1: Cap Shaving Balanced with Percentile")
    print("-" * 40)
    
    result = simulator.simulate_solar_with_bess(
        station=station,
        psfv_power_mw=psfv_mw,
        bess_power_mw=bess_mw,
        bess_duration_h=bess_h,
        strategy="cap_shaving_balanced",
        month=6,
        use_percentile=True,
        percentile=70,
        discharge_start_hour=16
    )
    
    if result.status == DataStatus.REAL and result.data:
        metrics = result.data.get('metrics', {})
        profiles = result.data.get('profiles', {})
        
        print(f"✓ Status: {result.status}")
        print(f"✓ Total generation: {metrics.get('total_generation_mwh', 0):.3f} MWh")
        print(f"✓ Energy to grid: {metrics.get('total_net_mwh', 0):.3f} MWh")
        print(f"✓ Energy losses: {metrics.get('energy_losses_mwh', 0):.3f} MWh")
        print(f"✓ Cycles: {metrics.get('cycles_count', 0):.2f}")
        print(f"✓ Efficiency: {metrics.get('efficiency_realized', 0)*100:.1f}%")
        
        # Check balance
        if 'bess_data' in result.data:
            bess_data = result.data['bess_data']
            charge = sum([-p for p in bess_data['power_net_mw'] if p < 0])
            discharge = sum([p for p in bess_data['power_net_mw'] if p > 0])
            print(f"\nBESS Balance:")
            print(f"  • Charged: {charge:.3f} MWh")
            print(f"  • Discharged: {discharge:.3f} MWh")
            print(f"  • Balance: {charge - discharge - metrics.get('energy_losses_mwh', 0):.6f} MWh")
    else:
        print(f"✗ Error: {result.meta.get('error', 'Unknown error')}")
    
    # Test 2: Without percentile (fixed cap)
    print("\n\nTest 2: Cap Shaving Balanced with Fixed Cap")
    print("-" * 40)
    
    result2 = simulator.simulate_solar_with_bess(
        station=station,
        psfv_power_mw=psfv_mw,
        bess_power_mw=bess_mw,
        bess_duration_h=bess_h,
        strategy="cap_shaving_balanced",
        month=6,
        use_percentile=False,
        cap_mw=0.5,
        discharge_start_hour=14
    )
    
    if result2.status == DataStatus.REAL and result2.data:
        metrics = result2.data.get('metrics', {})
        print(f"✓ Status: {result2.status}")
        print(f"✓ Energy to grid: {metrics.get('total_net_mwh', 0):.3f} MWh")
        print(f"✓ Energy losses: {metrics.get('energy_losses_mwh', 0):.3f} MWh")
        print(f"✓ Cycles: {metrics.get('cycles_count', 0):.2f}")
    else:
        print(f"✗ Error: {result2.meta.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    print("DASHBOARD INTEGRATION COMPLETE!")
    print("="*60)
    print("""
Next steps:
1. Navigate to http://localhost:8050/fase4-bess-lab
2. Select "Cap Shaving Balanced" from the strategy dropdown
3. Adjust percentile slider and discharge hour
4. Click "Simular y Validar" to see results
    """)

if __name__ == "__main__":
    test_cap_shaving_balanced_in_dashboard()