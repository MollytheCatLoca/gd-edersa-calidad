#!/usr/bin/env python3
"""
Verificar si el balance energético está corregido
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dashboard.pages.utils.solar_bess_simulator import SolarBESSSimulator
from dashboard.pages.utils.models import DataStatus

def verify_balance():
    """Verificar balance energético después del fix"""
    
    print("\n" + "="*60)
    print("VERIFICACIÓN DE BALANCE DESPUÉS DEL FIX")
    print("="*60)
    
    # Create simulator
    simulator = SolarBESSSimulator()
    
    # Test configuration
    configs = [
        ("Cap 30%", {"cap_mw": 0.3}),
        ("Cap 50%", {"cap_mw": 0.5}),
        ("Cap 70%", {"cap_mw": 0.7}),
    ]
    
    for name, params in configs:
        print(f"\n{name}:")
        print("-" * 40)
        
        result = simulator.simulate_solar_with_bess(
            station="Los Menucos",
            psfv_power_mw=1.0,
            bess_power_mw=1.0,
            bess_duration_h=2.0,
            strategy="cap_shaving",
            month=6,
            **params
        )
        
        if result.status == DataStatus.REAL and result.data:
            metrics = result.data.get('metrics', {})
            profiles = result.data.get('profiles', {})
            
            # Extract values
            solar_total = metrics.get('total_solar_mwh', 0)
            grid_total = metrics.get('total_net_mwh', 0)
            losses = metrics.get('energy_losses_mwh', 0)
            curtailed = metrics.get('solar_curtailed_mwh', 0)
            
            # Calculate ΔSOC
            soc_profile = profiles.get('soc_pct', [])
            if soc_profile:
                soc_initial = soc_profile[0]
                soc_final = soc_profile[-1]
                delta_soc = (soc_final - soc_initial) * 1.0 * 2.0 / 100  # MW * h / 100
            else:
                delta_soc = 0
            
            # Balance
            balance_total = grid_total + losses + curtailed + delta_soc
            error = abs(solar_total - balance_total)
            
            print(f"  Solar:       {solar_total:.3f} MWh")
            print(f"  Grid:        {grid_total:.3f} MWh")
            print(f"  Losses:      {losses:.3f} MWh")
            print(f"  Curtailed:   {curtailed:.3f} MWh")
            print(f"  ΔSOC:        {delta_soc:.3f} MWh")
            print(f"  Balance:     {balance_total:.3f} MWh")
            print(f"  Error:       {error:.6f} MWh {'✓' if error < 0.001 else '✗'}")
            
            # Debug: verificar unidades
            if error > 0.001:
                print(f"\n  DEBUG:")
                solar_profile = np.array(profiles.get('solar_mw', []))
                net_profile = np.array(profiles.get('net_mw', []))
                print(f"  Solar sum (MW):  {solar_profile.sum():.3f}")
                print(f"  Net sum (MW):    {net_profile.sum():.3f}")
                print(f"  Hours:           {len(solar_profile)}")

if __name__ == "__main__":
    verify_balance()