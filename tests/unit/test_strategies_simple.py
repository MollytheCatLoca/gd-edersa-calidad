#!/usr/bin/env python3
"""
Test available BESS strategies
"""

import sys
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dashboard.pages.utils.data_manager_v2 import get_data_manager

def test_available_strategies():
    """Test which strategies are working."""
    dm = get_data_manager()
    
    # Simple solar profile
    solar_profile = np.array([0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 3, 3, 3, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    
    strategies_to_test = [
        'cap_shaving',
        'flat_day', 
        'night_shift',
        'ramp_limit',
        'solar_smoothing',
        'time_shift_aggressive',
        'cycling_demo',
        'frequency_regulation',
        'arbitrage_aggressive',
        'unknown_strategy'  # Should pass through
    ]
    
    print("Testing available BESS strategies:")
    print("=" * 50)
    
    for strategy in strategies_to_test:
        try:
            result = dm.simulate_bess_strategy(
                solar_profile=solar_profile,
                strategy=strategy,
                power_mw=1.0,
                duration_hours=2.0
            )
            
            if result.status.value == 'real':
                metrics = result.data['metrics']
                print(f"✓ {strategy:20s}: efficiency={metrics['energy_efficiency']:.1%}, losses={metrics['total_losses_mwh']:.3f} MWh")
            else:
                print(f"❌ {strategy:20s}: {result.meta.get('error', 'unknown error')}")
                
        except Exception as e:
            print(f"❌ {strategy:20s}: Exception - {e}")

if __name__ == "__main__":
    test_available_strategies()