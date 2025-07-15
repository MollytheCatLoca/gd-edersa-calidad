#!/usr/bin/env python3
"""
Simple test to check simulate_solar_with_bess structure
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.pages.utils.data_manager import DataManager
import json

def main():
    print("Testing simulate_solar_with_bess...")
    
    # Initialize data manager
    dm = DataManager()
    
    # Test one configuration
    result = dm.simulate_solar_with_bess(
        station='MAQUINCHAO',
        solar_mw=1.0,
        technology='SAT Bifacial',
        bess_power_mw=0.5,
        bess_duration_h=4,
        strategy='solar_smoothing'  # V2 strategy
    )
    
    print("\nResult structure:")
    print(f"Available: {result.get('available', False)}")
    
    if result.get('available'):
        print("\nTop-level keys:")
        for key in result.keys():
            print(f"  - {key}")
        
        print("\nAnnual metrics keys:")
        if 'annual_metrics' in result:
            for key, value in result['annual_metrics'].items():
                print(f"  - {key}: {value}")
        
        # Check if cycles are > 0
        metrics = result['annual_metrics']
        cycles = metrics.get('bess_cycles_annual', 0)
        utilization = metrics.get('bess_utilization', 0)
        
        print(f"\n✓ BESS Cycles: {cycles:.2f}")
        print(f"✓ BESS Utilization: {utilization:.1%}")
        
        if cycles > 0:
            print("\n🎉 SUCCESS: V2 strategy shows real BESS usage!")
        else:
            print("\n⚠️  WARNING: Still showing 0 cycles")
    else:
        print(f"\nError: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    main()