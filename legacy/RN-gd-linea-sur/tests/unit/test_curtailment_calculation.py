#!/usr/bin/env python3
"""
Test unitario para entender paso a paso cómo se calcula el curtailment
y dónde está el error de 0.156 MWh
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel

def explain_curtailment_calculation():
    """Explicar paso a paso el cálculo del curtailment"""
    
    print("\n" + "="*80)
    print("EXPLICACIÓN PASO A PASO DEL CÁLCULO DE CURTAILMENT")
    print("="*80)
    
    print("\n1. CONCEPTOS BÁSICOS:")
    print("   - Solar: Energía generada por los paneles")
    print("   - Cap: Límite máximo de potencia a la red")
    print("   - Excess: Solar - Cap (cuando solar > cap)")
    print("   - BESS: Batería que puede absorber el exceso")
    print("   - Curtailment: Energía desperdiciada cuando BESS no puede absorber todo")
    
    print("\n2. ALGORITMO EN CAP_SHAVING:")
    print("   ```python")
    print("   if p_solar > cap_mw:                      # Hay exceso")
    print("       excess = p_solar - cap_mw")
    print("       res = bess_model.step(-excess, dt)   # Intentar cargar")
    print("       battery[i] = res['actual_power']     # Potencia real aceptada")
    print("       grid[i] = p_solar + battery[i]       # battery es negativo")
    print("       ")
    print("       if grid[i] > cap_mw * 1.02:          # Si aún excede cap+2%")
    print("           curtailed[i] = grid[i] - cap_mw")
    print("           grid[i] = cap_mw")
    print("   ```")
    
    # Crear ejemplo concreto
    print("\n3. EJEMPLO CONCRETO:")
    
    # Configuración
    bess = BESSModel(
        power_mw=0.2,
        duration_hours=1.0,
        technology='modern_lfp',
        topology='parallel_ac',
        track_history=False,
        verbose=False
    )
    
    # Empezar con BESS casi lleno
    bess.soc = 0.90  # 90% SOC
    
    # Valores del ejemplo
    solar = 0.5
    cap = 0.3
    thr_rel = 0.02
    
    print(f"   Configuración:")
    print(f"   - Solar = {solar} MW")
    print(f"   - Cap = {cap} MW")
    print(f"   - BESS: {bess.power_mw} MW, SOC = {bess.soc*100:.1f}%")
    print(f"   - Tolerancia = {thr_rel*100}%")
    
    # Paso 1: Calcular exceso
    print(f"\n   PASO 1: Verificar si hay exceso")
    print(f"   - ¿{solar} > {cap}? {'SÍ' if solar > cap else 'NO'}")
    
    if solar > cap:
        excess = solar - cap
        print(f"   - Exceso = {solar} - {cap} = {excess} MW")
        
        # Paso 2: Intentar cargar BESS
        print(f"\n   PASO 2: Intentar cargar BESS con {excess} MW")
        print(f"   - BESS puede aceptar máx: {bess.get_charge_limit(dt=1.0):.3f} MW")
        
        res = bess.step(-excess, dt=1.0)
        battery = res['actual_power']
        losses = res['energy_loss']
        
        print(f"   - BESS acepta: {battery:.3f} MW (negativo = carga)")
        print(f"   - Pérdidas: {losses:.3f} MWh")
        print(f"   - SOC después: {bess.soc*100:.1f}%")
        
        # Paso 3: Calcular grid
        print(f"\n   PASO 3: Calcular potencia a red")
        grid = solar + battery
        print(f"   - Grid = Solar + Battery")
        print(f"   - Grid = {solar} + ({battery:.3f}) = {grid:.3f} MW")
        
        # Paso 4: Verificar si necesita curtailment
        print(f"\n   PASO 4: Verificar si grid excede cap + tolerancia")
        cap_max = cap * (1 + thr_rel)
        print(f"   - Cap máx = {cap} × {1 + thr_rel} = {cap_max:.3f} MW")
        print(f"   - ¿{grid:.3f} > {cap_max:.3f}? {'SÍ' if grid > cap_max else 'NO'}")
        
        if grid > cap_max:
            curtailed = grid - cap
            grid_final = cap
            print(f"   - Curtailment = {grid:.3f} - {cap} = {curtailed:.3f} MW")
            print(f"   - Grid final = {cap} MW")
        else:
            curtailed = 0
            grid_final = grid
            print(f"   - No hay curtailment")
            print(f"   - Grid final = {grid:.3f} MW")
        
        # Resumen
        print(f"\n   RESUMEN DE FLUJOS:")
        print(f"   - Solar:        {solar} MW")
        print(f"   - A red:        {grid_final:.3f} MW")
        print(f"   - BESS carga:   {-battery:.3f} MW")
        print(f"   - Curtailment:  {curtailed:.3f} MW")
        print(f"   - Pérdidas:     {losses:.3f} MW (internas al BESS)")
        
        # Balance
        print(f"\n   BALANCE: Solar = Grid + Curtailment + BESS_carga")
        balance = grid_final + curtailed + (-battery)
        print(f"   {solar} = {grid_final:.3f} + {curtailed:.3f} + {-battery:.3f} = {balance:.3f}")
        print(f"   Error: {abs(solar - balance):.6f} MW")

def test_multiple_scenarios():
    """Probar múltiples escenarios para encontrar el patrón del error"""
    
    print("\n\n" + "="*80)
    print("PRUEBA DE MÚLTIPLES ESCENARIOS")
    print("="*80)
    
    # Crear BESS
    bess = BESSModel(
        power_mw=1.0,
        duration_hours=2.0,
        technology='modern_lfp',
        topology='parallel_ac',
        track_history=True,
        verbose=False
    )
    
    # Escenarios a probar
    scenarios = [
        ("BESS vacío, poco exceso", 0.10, 0.4, 0.3),
        ("BESS vacío, mucho exceso", 0.10, 0.6, 0.3),
        ("BESS medio, poco exceso", 0.50, 0.4, 0.3),
        ("BESS medio, mucho exceso", 0.50, 0.6, 0.3),
        ("BESS casi lleno, poco exceso", 0.90, 0.4, 0.3),
        ("BESS casi lleno, mucho exceso", 0.90, 0.6, 0.3),
        ("BESS lleno, cualquier exceso", 0.95, 0.5, 0.3),
    ]
    
    print(f"\n{'Escenario':<30} {'SOC%':>5} {'Solar':>6} {'Cap':>6} {'BESS':>7} {'Grid':>6} {'Curt':>6} {'Error':>8}")
    print("-" * 80)
    
    for name, soc_init, solar, cap in scenarios:
        # Reset BESS
        bess.soc = soc_init
        
        # Aplicar lógica de cap_shaving
        if solar > cap:
            excess = solar - cap
            res = bess.step(-excess, dt=1.0)
            battery = res['actual_power']
            grid = solar + battery
            
            # Curtailment
            thr_rel = 0.02
            if grid > cap * (1 + thr_rel):
                curtailed = grid - cap
                grid = cap
            else:
                curtailed = 0
        else:
            battery = 0
            grid = solar
            curtailed = 0
        
        # Balance
        balance = grid + curtailed + (-battery)
        error = abs(solar - balance)
        
        print(f"{name:<30} {soc_init*100:>5.0f} {solar:>6.2f} {cap:>6.2f} "
              f"{battery:>7.3f} {grid:>6.3f} {curtailed:>6.3f} {error:>8.6f}")

def investigate_error_pattern():
    """Investigar el patrón del error de 0.156 MWh"""
    
    print("\n\n" + "="*80)
    print("INVESTIGACIÓN DEL ERROR DE 0.156 MWH")
    print("="*80)
    
    # Replicar las condiciones exactas donde aparece el error
    bess = BESSModel(
        power_mw=1.0,
        duration_hours=2.0,
        technology='modern_lfp',
        topology='parallel_ac',
        track_history=True,
        verbose=False
    )
    
    # Perfil que genera el error (basado en trace_energy_flow.py)
    print("\nSimulando horas críticas donde aparece curtailment:")
    
    # Hora 14: SOC 85.2%, Solar 0.570, Cap 0.300
    print("\nHORA 14:")
    bess.soc = 0.852
    solar = 0.570
    cap = 0.300
    
    excess = solar - cap  # 0.270
    res = bess.step(-excess, dt=1.0)
    battery = res['actual_power']  # -0.197 según trace
    grid = solar + battery
    
    print(f"  Solar: {solar}, Cap: {cap}, Excess: {excess}")
    print(f"  BESS requested: {-excess}, actual: {battery}")
    print(f"  Grid = {solar} + {battery:.3f} = {grid:.3f}")
    
    thr_rel = 0.02
    if grid > cap * (1 + thr_rel):
        curtailed = grid - cap
        print(f"  Curtailment = {grid:.3f} - {cap} = {curtailed:.3f}")
    
    # Verificar si el curtailment reportado (0.073) coincide
    print(f"  Curtailment esperado: 0.073")
    print(f"  Diferencia: {abs(curtailed - 0.073):.6f}")

if __name__ == "__main__":
    explain_curtailment_calculation()
    test_multiple_scenarios()
    investigate_error_pattern()