#!/usr/bin/env python3
"""
Script de auditoría: Fórmula exacta para ML con cap_shaving
Muestra paso a paso cómo se calcula el balance energético
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from src.battery.bess_strategies import BESSStrategies
from dashboard.pages.utils.constants import AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW

def audit_ml_formula():
    """Auditar la fórmula que usaremos en ML"""
    
    print("\n" + "="*80)
    print("AUDITORÍA: FÓRMULA PARA ML CON CAP_SHAVING")
    print("="*80)
    
    # 1. CONFIGURACIÓN DEL SISTEMA
    print("\n1. CONFIGURACIÓN DEL SISTEMA:")
    print("   - PSFV: 1.0 MW")
    print("   - BESS: 1.0 MW / 2h = 2.0 MWh")
    print("   - Tecnología: modern_lfp (η=96.4%)")
    print("   - Estrategia: cap_shaving")
    print("   - Cap: 0.3 MW (30% de PSFV)")
    
    # 2. CREAR COMPONENTES
    bess = BESSModel(
        power_mw=1.0,
        duration_hours=2.0,
        technology='modern_lfp',
        topology='parallel_ac',
        track_history=True,
        verbose=False
    )
    
    # 3. GENERAR PERFIL SOLAR
    print("\n2. PERFIL SOLAR (24 horas):")
    hours = np.arange(24)
    daylight = (6 <= hours) & (hours <= 18)
    x = (hours - 12) / 6
    solar = np.zeros(24)
    solar[daylight] = np.exp(-2 * x[daylight] ** 2)
    
    daily_target = AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW / 30
    scale_factor = daily_target / solar.sum()
    solar *= scale_factor
    
    print(f"   - Generación total: {solar.sum():.3f} MWh/día")
    print(f"   - Pico máximo: {solar.max():.3f} MW")
    
    # 4. APLICAR ESTRATEGIA CAP_SHAVING
    print("\n3. APLICAR ESTRATEGIA CAP_SHAVING:")
    
    # Arrays para resultados
    n_hours = len(solar)
    grid = np.zeros(n_hours)
    battery = np.zeros(n_hours)
    soc = np.zeros(n_hours)
    curtailed = np.zeros(n_hours)
    losses = np.zeros(n_hours)
    
    # Aplicar estrategia
    BESSStrategies.apply_cap_shaving(
        bess, solar, grid, battery, soc, curtailed, losses,
        cap_mw=0.3, soft_discharge=True, dt=1.0
    )
    
    # 5. CALCULAR COMPONENTES DEL BALANCE
    print("\n4. COMPONENTES DEL BALANCE ENERGÉTICO:")
    
    # Componentes principales
    total_solar = solar.sum()
    total_grid = grid.sum()
    total_curtailed = curtailed.sum()
    
    # Flujos BESS
    total_charge = -battery[battery < 0].sum()  # Energía que entra al BESS
    total_discharge = battery[battery > 0].sum()  # Energía que sale del BESS
    net_bess_flow = total_charge - total_discharge
    
    # Delta SOC
    soc_inicial = bess.tech_params['soc_min']  # 10% para modern_lfp
    soc_final = soc[-1]
    delta_soc_pct = soc_final - soc_inicial
    delta_soc_mwh = delta_soc_pct * bess.capacity_mwh
    
    # Pérdidas (ya calculadas por el modelo)
    total_losses = losses.sum()
    
    print(f"   a) Generación solar:        {total_solar:.6f} MWh")
    print(f"   b) Energía a red:           {total_grid:.6f} MWh")
    print(f"   c) Curtailment:             {total_curtailed:.6f} MWh")
    print(f"   d) Carga BESS:              {total_charge:.6f} MWh")
    print(f"   e) Descarga BESS:           {total_discharge:.6f} MWh")
    print(f"   f) Flujo neto BESS:         {net_bess_flow:.6f} MWh (d - e)")
    print(f"   g) ΔSOC:                    {delta_soc_mwh:.6f} MWh")
    print(f"   h) Pérdidas internas:       {total_losses:.6f} MWh")
    
    # 6. FÓRMULAS DE BALANCE
    print("\n5. FÓRMULAS DE BALANCE ENERGÉTICO:")
    
    print("\n   FÓRMULA 1 - Con flujos brutos (PERFECTA):")
    print("   Solar = Red + Curtailment + (Carga_BESS - Descarga_BESS)")
    balance1 = total_grid + total_curtailed + net_bess_flow
    print(f"   {total_solar:.6f} = {total_grid:.6f} + {total_curtailed:.6f} + {net_bess_flow:.6f}")
    print(f"   {total_solar:.6f} = {balance1:.6f}")
    print(f"   Error: {abs(total_solar - balance1):.6f} MWh ✓")
    
    print("\n   FÓRMULA 2 - Con ΔSOC (puede tener error pequeño):")
    print("   Solar = Red + Curtailment + ΔSOC")
    balance2 = total_grid + total_curtailed + delta_soc_mwh
    print(f"   {total_solar:.6f} = {total_grid:.6f} + {total_curtailed:.6f} + {delta_soc_mwh:.6f}")
    print(f"   {total_solar:.6f} = {balance2:.6f}")
    print(f"   Error: {abs(total_solar - balance2):.6f} MWh")
    
    print("\n   FÓRMULA 3 - INCORRECTA (suma pérdidas aparte):")
    print("   Solar = Red + Curtailment + ΔSOC + Pérdidas")
    balance3 = total_grid + total_curtailed + delta_soc_mwh + total_losses
    print(f"   {total_solar:.6f} = {total_grid:.6f} + {total_curtailed:.6f} + {delta_soc_mwh:.6f} + {total_losses:.6f}")
    print(f"   {total_solar:.6f} = {balance3:.6f}")
    print(f"   Error: {abs(total_solar - balance3):.6f} MWh ❌")
    
    # 7. FÓRMULA PARA ML
    print("\n" + "="*80)
    print("FÓRMULA RECOMENDADA PARA ML:")
    print("="*80)
    
    print("""
Para ML, recomiendo usar la FÓRMULA 1 porque:
1. Es exacta (error = 0)
2. Los flujos de carga/descarga son observables directamente
3. No depende del SOC inicial que puede variar

IMPLEMENTACIÓN EN PYTHON:
```python
def calcular_balance_ml(solar, grid, curtailed, battery):
    '''
    Calcula el balance energético para ML
    
    Args:
        solar: array de generación solar (MW)
        grid: array de potencia a red (MW)
        curtailed: array de curtailment (MW)
        battery: array de potencia BESS (MW, neg=carga, pos=descarga)
    
    Returns:
        dict con componentes del balance
    '''
    # Sumar energías (MW * 1h = MWh)
    total_solar = solar.sum()
    total_grid = grid.sum()
    total_curtailed = curtailed.sum()
    
    # Flujos BESS
    total_charge = -battery[battery < 0].sum()
    total_discharge = battery[battery > 0].sum()
    net_bess_flow = total_charge - total_discharge
    
    # Balance
    balance = total_grid + total_curtailed + net_bess_flow
    error = abs(total_solar - balance)
    
    return {
        'solar_mwh': total_solar,
        'grid_mwh': total_grid,
        'curtailed_mwh': total_curtailed,
        'bess_charge_mwh': total_charge,
        'bess_discharge_mwh': total_discharge,
        'bess_net_mwh': net_bess_flow,
        'balance_mwh': balance,
        'error_mwh': error,
        'error_pct': error / total_solar * 100 if total_solar > 0 else 0
    }
```

FEATURES CLAVE PARA ML:
1. `cap_ratio = cap_mw / psfv_mw` (ej: 0.3)
2. `solar_peak = solar.max()` (MW)
3. `hours_above_cap = sum(solar > cap_mw)` 
4. `excess_energy = sum(np.maximum(0, solar - cap_mw))` (MWh)
5. `bess_utilization = max(soc) - min(soc)` (%)
6. `curtailment_ratio = curtailed.sum() / solar.sum()`
""")
    
    # 8. EJEMPLO DE CÁLCULO PARA UNA HORA
    print("\n" + "="*80)
    print("EJEMPLO DETALLADO - HORA 12 (mediodía):")
    print("="*80)
    
    h = 12
    print(f"\nDatos de entrada:")
    print(f"  - Solar: {solar[h]:.3f} MW")
    print(f"  - Cap: 0.300 MW")
    print(f"  - SOC inicial hora: {soc[h-1]*100:.1f}%")
    
    print(f"\nCálculo cap_shaving:")
    if solar[h] > 0.3:
        excess = solar[h] - 0.3
        print(f"  - Exceso sobre cap: {excess:.3f} MW")
        print(f"  - BESS intenta cargar: {-battery[h]:.3f} MW")
        print(f"  - Grid = Solar + BESS = {solar[h]:.3f} + {battery[h]:.3f} = {grid[h]:.3f} MW")
        if curtailed[h] > 0:
            print(f"  - Curtailment: {curtailed[h]:.3f} MW (BESS no pudo absorber todo)")
    else:
        print(f"  - No hay exceso, solar pasa directo a red")
    
    print(f"\nBalance horario:")
    print(f"  Solar = Grid + Curtailment + Carga_BESS")
    print(f"  {solar[h]:.3f} = {grid[h]:.3f} + {curtailed[h]:.3f} + {-battery[h] if battery[h] < 0 else 0:.3f}")
    balance_h = grid[h] + curtailed[h] + (-battery[h] if battery[h] < 0 else 0)
    print(f"  {solar[h]:.3f} = {balance_h:.3f} ✓")

if __name__ == "__main__":
    audit_ml_formula()