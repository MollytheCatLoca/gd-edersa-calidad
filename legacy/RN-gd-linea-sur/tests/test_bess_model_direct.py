#!/usr/bin/env python3
"""
Direct test of BESSModel with V2 strategies
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
from src.battery.bess_model import BESSModel

def main():
    print("Direct test of BESSModel with V2 strategies\n")
    
    # Create simple solar profile (24 hours)
    hours = np.arange(24)
    solar = np.maximum(0, 2.0 * np.sin((hours - 6) * np.pi / 12))
    solar[hours < 6] = 0
    solar[hours > 18] = 0
    
    print(f"Solar profile: Peak={np.max(solar):.2f} MW, Total={np.sum(solar):.2f} MWh")
    
    # Test with V2 strategy
    bess = BESSModel(
        power_mw=1.0,
        duration_hours=4.0,
        technology='modern_lfp',
        verbose=True
    )
    
    print("\nTesting 'solar_smoothing' strategy...")
    result = bess.simulate_strategy(solar, strategy='solar_smoothing')
    
    print(f"\nResults:")
    print(f"- Solar generated: {np.sum(solar):.2f} MWh")
    print(f"- Energy delivered: {np.sum(result['grid_power']):.2f} MWh")
    print(f"- BESS losses: {np.sum(result['energy_losses']):.2f} MWh")
    print(f"- Solar curtailed: {np.sum(result['solar_curtailed']):.2f} MWh")
    print(f"- BESS cycles: {result['total_cycles']:.3f}")
    print(f"- Daily cycles: {result.get('daily_cycles', 0):.3f}")
    
    # Check BESS internal state
    print(f"\nBESS internal state:")
    print(f"- Total charged: {bess.total_energy_charged:.2f} MWh")
    print(f"- Total discharged: {bess.total_energy_discharged:.2f} MWh")
    print(f"- Total losses: {bess.total_energy_losses:.2f} MWh") 
    print(f"- Cycles: {bess.cycles:.3f}")
    
    # Test another V2 strategy
    print("\n" + "="*50)
    bess2 = BESSModel(
        power_mw=1.0,
        duration_hours=4.0,
        technology='modern_lfp',
        verbose=False
    )
    
    print("Testing 'time_shift_aggressive' strategy...")
    result2 = bess2.simulate_strategy(solar, strategy='time_shift_aggressive')
    
    print(f"\nResults:")
    print(f"- BESS cycles: {result2['total_cycles']:.3f}")
    print(f"- BESS losses: {np.sum(result2['energy_losses']):.2f} MWh")
    print(f"- Energy charged: {bess2.total_energy_charged:.2f} MWh")
    print(f"- Energy discharged: {bess2.total_energy_discharged:.2f} MWh")
    
    if result2['total_cycles'] > 0:
        print("\n✅ SUCCESS: V2 strategies are working and showing real BESS usage!")
    else:
        print("\n❌ ERROR: Still showing 0 cycles")


if __name__ == "__main__":
    main()