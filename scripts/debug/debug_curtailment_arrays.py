#!/usr/bin/env python3
"""
Depurar arrays completos de curtailment para encontrar la discrepancia
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from src.battery.bess_strategies import BESSStrategies

def debug_curtailment_arrays():
    """Depurar los arrays de curtailment paso a paso"""
    
    print("\n" + "="*80)
    print("DEBUG DE ARRAYS DE CURTAILMENT")
    print("="*80)
    
    # Crear dos BESS idénticos
    bess1 = BESSModel(
        power_mw=1.0,
        duration_hours=2.0,
        technology='modern_lfp',
        topology='parallel_ac',
        track_history=True,
        verbose=False
    )
    
    bess2 = BESSModel(
        power_mw=1.0,
        duration_hours=2.0,
        technology='modern_lfp',
        topology='parallel_ac',
        track_history=True,
        verbose=False
    )
    
    # Crear perfil solar idéntico al simulador
    from dashboard.pages.utils.constants import AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW
    hours = np.arange(24)
    daylight = (6 <= hours) & (hours <= 18)
    x = (hours - 12) / 6
    solar = np.zeros(24)
    solar[daylight] = np.exp(-2 * x[daylight] ** 2)
    
    # Escalar para alcanzar target diario
    daily_target = AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW / 30
    scale_factor = daily_target / solar.sum()
    solar *= scale_factor
    
    print(f"Perfil solar generado:")
    print(f"  Total: {solar.sum():.3f} MWh")
    print(f"  Pico: {solar.max():.3f} MW")
    
    # Método 1: Usando simulate_strategy
    print("\n" + "-"*60)
    print("MÉTODO 1: simulate_strategy()")
    results1 = bess1.simulate_strategy(
        solar_profile=solar,
        strategy='cap_shaving',
        cap_mw=0.3,
        soft_discharge=True
    )
    
    curt1 = results1['solar_curtailed']
    print(f"  Curtailment total: {curt1.sum():.6f} MWh")
    print(f"  Horas con curtailment: {np.count_nonzero(curt1)}")
    if np.any(curt1 > 0):
        print(f"  Detalle por hora:")
        for h in range(24):
            if curt1[h] > 0.001:
                print(f"    Hora {h}: {curt1[h]:.6f} MWh")
    
    # Método 2: Llamada directa a la estrategia
    print("\n" + "-"*60)
    print("MÉTODO 2: apply_cap_shaving() directo")
    
    n_hours = len(solar)
    grid2 = np.zeros(n_hours)
    battery2 = np.zeros(n_hours)
    soc2 = np.zeros(n_hours)
    curt2 = np.zeros(n_hours)
    losses2 = np.zeros(n_hours)
    
    BESSStrategies.apply_cap_shaving(
        bess2, solar, grid2, battery2, soc2, curt2, losses2,
        cap_mw=0.3, soft_discharge=True, dt=1.0
    )
    
    print(f"  Curtailment total: {curt2.sum():.6f} MWh")
    print(f"  Horas con curtailment: {np.count_nonzero(curt2)}")
    if np.any(curt2 > 0):
        print(f"  Detalle por hora:")
        for h in range(24):
            if curt2[h] > 0.001:
                print(f"    Hora {h}: {curt2[h]:.6f} MWh")
    
    # Comparar arrays
    print("\n" + "-"*60)
    print("COMPARACIÓN DE ARRAYS:")
    diff = curt1 - curt2
    print(f"  Diferencia total: {diff.sum():.6f} MWh")
    print(f"  Diferencia máxima: {np.abs(diff).max():.6f} MWh")
    
    if np.any(np.abs(diff) > 0.0001):
        print("  ⚠️  HAY DIFERENCIAS ENTRE MÉTODOS:")
        for h in range(24):
            if abs(diff[h]) > 0.0001:
                print(f"    Hora {h}: método1={curt1[h]:.6f}, método2={curt2[h]:.6f}, diff={diff[h]:.6f}")
    
    # Análisis detallado de horas con curtailment
    print("\n" + "-"*60)
    print("ANÁLISIS DETALLADO DE HORAS CON CURTAILMENT:")
    
    for h in range(24):
        if curt2[h] > 0.001 or (solar[h] > 0.3 and battery2[h] > -0.1):
            print(f"\nHora {h}:")
            print(f"  Solar: {solar[h]:.3f} MW")
            print(f"  BESS: {battery2[h]:.3f} MW")
            print(f"  Grid: {grid2[h]:.3f} MW")
            print(f"  Curtailment: {curt2[h]:.3f} MW")
            print(f"  SOC: {soc2[h]*100:.1f}%")
            
            # Verificar lógica
            if solar[h] > 0.3:
                excess = solar[h] - 0.3
                grid_calc = solar[h] + battery2[h]
                print(f"  Verificación:")
                print(f"    Exceso solicitado: {excess:.3f} MW")
                print(f"    BESS aceptó: {battery2[h]:.3f} MW")
                print(f"    Grid calculado: {solar[h]:.3f} + {battery2[h]:.3f} = {grid_calc:.3f}")
                print(f"    Cap × 1.02 = {0.3 * 1.02:.3f}")
                
                if grid_calc > 0.3 * 1.02:
                    curt_calc = grid_calc - 0.3
                    print(f"    Curtailment calculado: {grid_calc:.3f} - 0.3 = {curt_calc:.3f}")
                    print(f"    ¿Coincide? {'SÍ' if abs(curt_calc - curt2[h]) < 0.001 else 'NO'}")
    
    # Balance energético
    print("\n" + "-"*60)
    print("VERIFICACIÓN DE BALANCE:")
    
    total_solar = solar.sum()
    total_grid = grid2.sum()
    total_curt = curt2.sum()
    total_charge = -battery2[battery2 < 0].sum()
    total_discharge = battery2[battery2 > 0].sum()
    total_losses = losses2.sum()
    delta_soc = (soc2[-1] - soc2[0]) * bess2.capacity_mwh
    
    print(f"  Solar total:      {total_solar:.6f} MWh")
    print(f"  Grid total:       {total_grid:.6f} MWh")
    print(f"  Curtailment:      {total_curt:.6f} MWh")
    print(f"  ΔSOC:             {delta_soc:.6f} MWh")
    print(f"  Pérdidas:         {total_losses:.6f} MWh")
    
    balance = total_grid + total_curt + delta_soc + total_losses
    error = abs(total_solar - balance)
    
    print(f"\n  Balance: Solar = Grid + Curt + ΔSOC + Losses")
    print(f"  {total_solar:.6f} = {total_grid:.6f} + {total_curt:.6f} + {delta_soc:.6f} + {total_losses:.6f}")
    print(f"  = {balance:.6f}")
    print(f"  Error: {error:.6f} MWh")
    
    if error > 0.001:
        print(f"\n  ⚠️  ERROR EN BALANCE > 0.001 MWh")
        print(f"  Investigar por qué no cierra el balance")

if __name__ == "__main__":
    debug_curtailment_arrays()