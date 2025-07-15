#!/usr/bin/env python3
"""
Comparar el cálculo del curtailment entre BESSModel directo y simulador
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

def test_bess_model_direct():
    """Test directo con BESSModel para ver qué devuelve"""
    print("\n" + "="*60)
    print("TEST DIRECTO CON BESSMODEL")
    print("="*60)
    
    # Configuración idéntica al simulador
    bess = BESSModel(
        power_mw=1.0,
        duration_hours=2.0,
        technology='modern_lfp',  # Mismo que simulador
        topology='parallel_ac',
        track_history=False,
        verbose=False
    )
    
    # Generar perfil solar simple
    solar = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                      0.1, 0.2, 0.3, 0.5, 0.6, 0.7,  # Mañana
                      0.7, 0.6, 0.5, 0.3, 0.2, 0.1,  # Tarde
                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # Noche
    
    # Aplicar estrategia
    results = bess.simulate_strategy(
        solar_profile=solar,
        strategy='cap_shaving',
        cap_mw=0.3,
        soft_discharge=True
    )
    
    # Extraer resultados
    grid = results['grid_power']
    battery = results['battery_power']
    soc = results['soc']
    curtailed = results['solar_curtailed']
    losses = results['energy_losses']
    
    print("\nRESULTADOS HORA POR HORA:")
    print(f"{'Hr':>3} {'Solar':>6} {'Grid':>6} {'BESS':>7} {'Curt':>6} {'Loss':>6} {'SOC':>5}")
    print("-" * 45)
    
    for h in range(24):
        if solar[h] > 0.01 or abs(battery[h]) > 0.01:
            print(f"{h:3d} {solar[h]:6.3f} {grid[h]:6.3f} {battery[h]:7.3f} "
                  f"{curtailed[h]:6.3f} {losses[h]:6.3f} {soc[h]*100:5.1f}")
    
    print("\nTOTALES:")
    print(f"  Solar:       {solar.sum():.3f} MWh")
    print(f"  Grid:        {grid.sum():.3f} MWh")
    print(f"  Curtailed:   {curtailed.sum():.3f} MWh")
    print(f"  Losses:      {losses.sum():.3f} MWh")
    
    # Balance
    balance = grid.sum() + curtailed.sum() + (soc[-1] - soc[0]) * bess.capacity_mwh + losses.sum()
    error = abs(solar.sum() - balance)
    print(f"\nBALANCE: Solar = Grid + Curt + ΔSOC + Losses")
    print(f"  {solar.sum():.3f} = {grid.sum():.3f} + {curtailed.sum():.3f} + "
          f"{(soc[-1] - soc[0]) * bess.capacity_mwh:.3f} + {losses.sum():.3f}")
    print(f"  Error: {error:.6f} MWh")
    
    return {
        'solar': solar.sum(),
        'grid': grid.sum(),
        'curtailed': curtailed.sum(),
        'losses': losses.sum(),
        'soc_change': (soc[-1] - soc[0]) * bess.capacity_mwh
    }

def test_simulator():
    """Test con el simulador para comparar"""
    print("\n\n" + "="*60)
    print("TEST CON SIMULADOR")
    print("="*60)
    
    simulator = SolarBESSSimulator()
    
    # Forzar a usar un perfil solar simple similar
    # Necesito hackear un poco porque el simulador genera su propio perfil
    result = simulator.simulate_solar_with_bess(
        station="Los Menucos",
        psfv_power_mw=1.0,
        bess_power_mw=1.0,
        bess_duration_h=2.0,
        strategy="cap_shaving",
        month=6,
        cap_mw=0.3
    )
    
    if result.status != DataStatus.REAL:
        print("Error en simulación")
        return None
    
    profiles = result.data.get('profiles', {})
    metrics = result.data.get('metrics', {})
    
    print("\nMÉTRICAS DEL SIMULADOR:")
    print(f"  Solar total:     {metrics.get('total_solar_mwh', 0):.3f} MWh")
    print(f"  Grid total:      {metrics.get('total_net_mwh', 0):.3f} MWh")
    print(f"  Curtailed:       {metrics.get('solar_curtailed_mwh', 0):.3f} MWh")
    print(f"  Losses:          {metrics.get('energy_losses_mwh', 0):.3f} MWh")
    
    # ΔSOC
    soc_profile = profiles.get('soc_pct', [])
    if soc_profile:
        soc_change = (soc_profile[-1] - soc_profile[0]) * 1.0 * 2.0 / 100
        print(f"  ΔSOC:            {soc_change:.3f} MWh")
        
        # Balance
        balance = (metrics.get('total_net_mwh', 0) + 
                  metrics.get('solar_curtailed_mwh', 0) + 
                  soc_change + 
                  metrics.get('energy_losses_mwh', 0))
        error = abs(metrics.get('total_solar_mwh', 0) - balance)
        print(f"\nBALANCE: {metrics.get('total_solar_mwh', 0):.3f} = "
              f"{metrics.get('total_net_mwh', 0):.3f} + "
              f"{metrics.get('solar_curtailed_mwh', 0):.3f} + "
              f"{soc_change:.3f} + {metrics.get('energy_losses_mwh', 0):.3f}")
        print(f"  Error: {error:.6f} MWh")
    
    return {
        'solar': metrics.get('total_solar_mwh', 0),
        'grid': metrics.get('total_net_mwh', 0),
        'curtailed': metrics.get('solar_curtailed_mwh', 0),
        'losses': metrics.get('energy_losses_mwh', 0),
        'soc_change': soc_change if 'soc_change' in locals() else 0
    }

def main():
    """Ejecutar comparación"""
    direct = test_bess_model_direct()
    simulator = test_simulator()
    
    if direct and simulator:
        print("\n\n" + "="*60)
        print("COMPARACIÓN DE RESULTADOS")
        print("="*60)
        
        print(f"\n{'Métrica':<15} {'Directo':>10} {'Simulador':>10} {'Diferencia':>10}")
        print("-" * 50)
        
        for key in ['solar', 'grid', 'curtailed', 'losses', 'soc_change']:
            diff = simulator[key] - direct[key]
            print(f"{key:<15} {direct[key]:>10.3f} {simulator[key]:>10.3f} {diff:>10.3f}")
        
        # Análisis específico del curtailment
        if abs(simulator['curtailed'] - direct['curtailed']) > 0.01:
            print(f"\n⚠️  DIFERENCIA SIGNIFICATIVA EN CURTAILMENT")
            print(f"  Simulador reporta {simulator['curtailed']:.3f} MWh")
            print(f"  Cálculo directo da {direct['curtailed']:.3f} MWh")
            print(f"  Diferencia: {simulator['curtailed'] - direct['curtailed']:.3f} MWh")

if __name__ == "__main__":
    main()