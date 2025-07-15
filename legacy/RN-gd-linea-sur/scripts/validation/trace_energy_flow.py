#!/usr/bin/env python3
"""
Trazabilidad completa del flujo energético hora por hora
Para entender exactamente dónde está el error del curtailment
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from src.battery.bess_strategies import BESSStrategies
from dashboard.pages.utils.constants import MONTHLY_SOLAR_GENERATION_MWH_PER_MW

def generate_solar_profile(psfv_mw=1.0, month=6):
    """Genera perfil solar diario típico"""
    hours = np.arange(24)
    
    # Perfil base sinusoidal
    solar_base = np.maximum(0, 
        np.sin((hours - 6) * np.pi / 12) * np.where((hours >= 6) & (hours <= 18), 1, 0)
    )
    
    # Factor de escala para alcanzar generación mensual objetivo
    daily_target = MONTHLY_SOLAR_GENERATION_MWH_PER_MW[month] / 30  # MWh/día por MW
    scale_factor = daily_target / (solar_base.sum() if solar_base.sum() > 0 else 1)
    
    return solar_base * scale_factor * psfv_mw

def trace_energy_flow():
    """Traza el flujo energético hora por hora"""
    
    print("\n" + "="*80)
    print("TRAZABILIDAD ENERGÉTICA - CAP SHAVING 30%")
    print("="*80)
    
    # Configuración
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_hours = 2.0
    cap_mw = 0.3  # 30% cap
    
    # Crear BESS
    bess = BESSModel(
        power_mw=bess_mw,
        duration_hours=bess_hours,
        technology='modern_lfp',  # Usar mismo que simulador
        topology='parallel_ac',
        track_history=True,
        verbose=False
    )
    
    # Generar perfil solar (usar mismo método que simulador)
    # Simulador usa promedio anual
    from dashboard.pages.utils.constants import AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW
    hours = np.arange(24)
    daylight = (6 <= hours) & (hours <= 18)
    x = (hours - 12) / 6
    solar = np.zeros(24)
    solar[daylight] = np.exp(-2 * x[daylight] ** 2)
    
    # Escalar para alcanzar target diario
    daily_target = AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW / 30
    scale_factor = daily_target / solar.sum()
    solar *= scale_factor * psfv_mw
    
    print(f"\nCONFIGURACIÓN:")
    print(f"  PSFV: {psfv_mw} MW")
    print(f"  BESS: {bess_mw} MW / {bess_hours}h = {bess_mw*bess_hours} MWh")
    print(f"  Cap: {cap_mw} MW ({cap_mw/psfv_mw*100:.0f}%)")
    print(f"  Tecnología: {bess.technology} (η={bess.tech_params['η_roundtrip']:.1%})")
    print(f"  SOC inicial: {bess.soc*100:.1f}%")
    
    # Arrays para resultados
    n_hours = len(solar)
    grid = np.zeros(n_hours)
    battery = np.zeros(n_hours)
    soc_array = np.zeros(n_hours)
    curtailed = np.zeros(n_hours)
    losses = np.zeros(n_hours)
    
    # Aplicar estrategia
    BESSStrategies.apply_cap_shaving(
        bess, solar, grid, battery, soc_array, curtailed, losses,
        cap_mw=cap_mw, soft_discharge=True, dt=1.0
    )
    
    # Encabezado de tabla detallada
    print(f"\nFLUJO ENERGÉTICO HORA POR HORA:")
    print(f"{'Hr':>3} {'Solar':>6} {'Cap':>6} {'Excess':>7} {'BESS':>7} {'Grid':>6} {'Curt':>6} {'Loss':>6} {'SOC%':>5} {'Check':>6}")
    print("-" * 80)
    
    # Variables para totales
    total_solar = 0
    total_grid = 0
    total_charge = 0
    total_discharge = 0
    total_curtailed = 0
    total_losses = 0
    
    # Analizar hora por hora
    for h in range(n_hours):
        if solar[h] > 0.001 or abs(battery[h]) > 0.001:
            # Calcular exceso
            excess = max(0, solar[h] - cap_mw)
            
            # Verificar balance horario
            # Solar = Grid + Curtailment - Battery (negativo = carga)
            check = grid[h] + curtailed[h] - battery[h] - solar[h]
            
            print(f"{h:3d} {solar[h]:6.3f} {cap_mw:6.3f} {excess:7.3f} {battery[h]:7.3f} "
                  f"{grid[h]:6.3f} {curtailed[h]:6.3f} {losses[h]:6.3f} {soc_array[h]*100:5.1f} {check:6.3f}")
            
            # Acumular totales
            total_solar += solar[h]
            total_grid += grid[h]
            if battery[h] < 0:
                total_charge += -battery[h]
            else:
                total_discharge += battery[h]
            total_curtailed += curtailed[h]
            total_losses += losses[h]
    
    print("-" * 80)
    print(f"TOT {total_solar:6.3f}        {' '*7} {-total_charge+total_discharge:7.3f} "
          f"{total_grid:6.3f} {total_curtailed:6.3f} {total_losses:6.3f}")
    
    # Análisis de totales
    print(f"\nRESUMEN DE FLUJOS:")
    print(f"  Solar total:          {total_solar:.6f} MWh")
    print(f"  Grid total:           {total_grid:.6f} MWh")
    print(f"  BESS cargado:         {total_charge:.6f} MWh")
    print(f"  BESS descargado:      {total_discharge:.6f} MWh")
    print(f"  Curtailment total:    {total_curtailed:.6f} MWh")
    print(f"  Pérdidas totales:     {total_losses:.6f} MWh")
    
    # ΔSOC
    soc_initial = soc_array[0]
    soc_final = soc_array[-1]
    delta_soc_energy = (soc_final - soc_initial) * bess.capacity_mwh
    print(f"  ΔSOC energía:         {delta_soc_energy:.6f} MWh")
    
    # Verificar balance global
    print(f"\nBALANCE ENERGÉTICO GLOBAL:")
    print(f"  Solar = Grid + Curtailment + (Cargado - Descargado) + Pérdidas")
    print(f"  {total_solar:.6f} = {total_grid:.6f} + {total_curtailed:.6f} + "
          f"({total_charge:.6f} - {total_discharge:.6f}) + {total_losses:.6f}")
    
    balance_check = total_grid + total_curtailed + (total_charge - total_discharge) + total_losses
    error = abs(total_solar - balance_check)
    print(f"  Balance calculado:    {balance_check:.6f} MWh")
    print(f"  Error:                {error:.6f} MWh")
    
    # Balance alternativo con ΔSOC
    print(f"\nBALANCE CON ΔSOC:")
    print(f"  Solar = Grid + Curtailment + ΔSOC + Pérdidas")
    print(f"  {total_solar:.6f} = {total_grid:.6f} + {total_curtailed:.6f} + "
          f"{delta_soc_energy:.6f} + {total_losses:.6f}")
    
    balance_soc = total_grid + total_curtailed + delta_soc_energy + total_losses
    error_soc = abs(total_solar - balance_soc)
    print(f"  Balance con ΔSOC:     {balance_soc:.6f} MWh")
    print(f"  Error:                {error_soc:.6f} MWh")
    
    # Análisis de discrepancia
    if error > 0.001:
        print(f"\n⚠️  ERROR EN BALANCE > 0.001 MWh")
        print(f"  Revisar cálculo de curtailment y pérdidas")
    
    # Verificar relación pérdidas vs carga/descarga
    print(f"\nANÁLISIS DE PÉRDIDAS:")
    if total_charge > 0:
        loss_rate_charge = total_losses / total_charge * 100
        print(f"  Pérdidas/Carga:       {loss_rate_charge:.1f}%")
    
    # Para modern_lfp: η_charge = 0.964, η_discharge = 0.964
    # Pérdidas esperadas al cargar: (1 - 0.964) = 3.6%
    # Pérdidas esperadas al descargar: (1/0.964 - 1) = 3.7%
    expected_losses = total_charge * (1 - 0.964) + total_discharge * (1/0.964 - 1)
    print(f"  Pérdidas esperadas:   {expected_losses:.6f} MWh")
    print(f"  Pérdidas reales:      {total_losses:.6f} MWh")
    print(f"  Diferencia:           {abs(expected_losses - total_losses):.6f} MWh")

if __name__ == "__main__":
    trace_energy_flow()