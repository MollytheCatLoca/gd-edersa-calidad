#!/usr/bin/env python3
"""
Debug detallado del balance energético
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from dashboard.pages.utils.solar_bess_simulator import SolarBESSSimulator
from dashboard.pages.utils.models import DataStatus

def debug_balance():
    """Debug detallado del problema de balance con cap 30%"""
    
    print("\n" + "="*60)
    print("DEBUG DETALLADO - CAP SHAVING 30%")
    print("="*60)
    
    # 1. Simular con el simulador
    simulator = SolarBESSSimulator()
    result = simulator.simulate_solar_with_bess(
        station="Los Menucos",
        psfv_power_mw=1.0,
        bess_power_mw=1.0,
        bess_duration_h=2.0,
        strategy="cap_shaving",
        month=6,
        cap_mw=0.3
    )
    
    if result.status != DataStatus.REAL or not result.data:
        print("ERROR: Simulación falló")
        return
    
    # Extraer todos los datos
    profiles = result.data.get('profiles', {})
    metrics = result.data.get('metrics', {})
    bess_data = result.data.get('bess_data', {})
    
    # Arrays
    solar = np.array(profiles.get('solar_mw', []))
    net = np.array(profiles.get('net_mw', []))
    bess = np.array(profiles.get('bess_mw', []))
    soc = np.array(profiles.get('soc_pct', []))
    losses = np.array(profiles.get('losses_mwh', []))
    
    print("\nPERFILES HORARIOS (primeras 18 horas con actividad):")
    print(f"{'Hora':>4} {'Solar':>7} {'BESS':>7} {'Net':>7} {'Loss':>7} {'SOC%':>6}")
    print("-" * 45)
    
    for h in range(18):
        if solar[h] > 0.01 or abs(bess[h]) > 0.01:
            print(f"{h:4d} {solar[h]:7.3f} {bess[h]:7.3f} {net[h]:7.3f} {losses[h]:7.3f} {soc[h]:6.1f}")
    
    print("\nCÁLCULO DE CURTAILMENT:")
    # Calcular curtailment manualmente
    # Curtailment = Solar - Net - Battery_charge + Battery_discharge - Losses
    battery_charge = -bess[bess < 0].sum()  # Positivo
    battery_discharge = bess[bess > 0].sum()  # Positivo
    
    curtailment_calc = solar.sum() - net.sum() - battery_charge + battery_discharge - losses.sum()
    
    print(f"  Solar total:        {solar.sum():.3f} MWh")
    print(f"  Net total:          {net.sum():.3f} MWh")
    print(f"  Battery charge:     {battery_charge:.3f} MWh")
    print(f"  Battery discharge:  {battery_discharge:.3f} MWh")
    print(f"  Losses total:       {losses.sum():.3f} MWh")
    print(f"  Curtailment calc:   {curtailment_calc:.3f} MWh")
    print(f"  Curtailment metric: {metrics.get('solar_curtailed_mwh', 0):.3f} MWh")
    
    # Verificar balance
    print("\nVERIFICACIÓN DE BALANCE:")
    soc_initial = soc[0]
    soc_final = soc[-1]
    delta_soc = (soc_final - soc_initial) * 1.0 * 2.0 / 100
    
    print(f"  ΔSOC: ({soc_final:.1f}% - {soc_initial:.1f}%) × 2 MWh / 100 = {delta_soc:.3f} MWh")
    
    # Balance: Solar = Net + Losses + Curtailment + ΔSOC
    balance_components = {
        'Net': net.sum(),
        'Losses': losses.sum(),
        'Curtailment (calc)': curtailment_calc,
        'Curtailment (metric)': metrics.get('solar_curtailed_mwh', 0),
        'ΔSOC': delta_soc
    }
    
    print("\nCOMPONENTES DEL BALANCE:")
    for name, value in balance_components.items():
        print(f"  {name:<20}: {value:.6f} MWh")
    
    # Calcular balance con ambos curtailments
    balance_calc = net.sum() + losses.sum() + curtailment_calc + delta_soc
    balance_metric = net.sum() + losses.sum() + metrics.get('solar_curtailed_mwh', 0) + delta_soc
    
    print(f"\n  Balance (calc):     {balance_calc:.6f} MWh")
    print(f"  Balance (metric):   {balance_metric:.6f} MWh")
    print(f"  Solar:              {solar.sum():.6f} MWh")
    print(f"  Error (calc):       {abs(solar.sum() - balance_calc):.6f} MWh")
    print(f"  Error (metric):     {abs(solar.sum() - balance_metric):.6f} MWh")

if __name__ == "__main__":
    debug_balance()