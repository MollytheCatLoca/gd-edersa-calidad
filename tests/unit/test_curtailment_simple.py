#!/usr/bin/env python3
"""
Test simple para entender el cálculo del curtailment
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel

def test_curtailment_logic():
    """Test simple del curtailment cuando BESS está lleno"""
    
    print("\n" + "="*60)
    print("TEST SIMPLE DE CURTAILMENT")
    print("="*60)
    
    # Crear BESS pequeño para que se llene rápido
    bess = BESSModel(
        power_mw=0.1,  # Solo 0.1 MW
        duration_hours=1.0,  # 0.1 MWh capacidad
        technology='modern_lfp',
        topology='parallel_ac',
        track_history=True,
        verbose=False
    )
    
    # Empezar cerca del máximo
    bess.soc = 0.90  # 90% SOC
    
    print(f"\nCONFIGURACIÓN:")
    print(f"  BESS: 0.1 MW / 1h = 0.1 MWh")
    print(f"  SOC inicial: {bess.soc*100:.1f}%")
    print(f"  Energía disponible para cargar: {(0.95-0.90)*0.1:.3f} MWh")
    
    # Simular una hora con exceso solar
    cap_mw = 0.3
    solar_mw = 0.5  # 0.2 MW de exceso
    
    print(f"\nSIMULACIÓN:")
    print(f"  Solar: {solar_mw} MW")
    print(f"  Cap: {cap_mw} MW")
    print(f"  Exceso: {solar_mw - cap_mw} MW")
    
    # Intentar cargar el exceso
    excess = solar_mw - cap_mw
    res = bess.step(-excess, dt=1.0)
    
    battery_power = res["actual_power"]
    energy_loss = res["energy_loss"]
    
    print(f"\nRESULTADO BESS:")
    print(f"  Potencia solicitada: {-excess:.3f} MW (carga)")
    print(f"  Potencia real: {battery_power:.3f} MW")
    print(f"  Pérdida energética: {energy_loss:.3f} MWh")
    print(f"  SOC final: {bess.soc*100:.1f}%")
    
    # Calcular grid según la estrategia
    grid = solar_mw + battery_power  # battery_power es negativo
    
    print(f"\nCÁLCULO DE GRID:")
    print(f"  Grid = Solar + Battery")
    print(f"  Grid = {solar_mw:.3f} + {battery_power:.3f} = {grid:.3f} MW")
    
    # Verificar si hay curtailment
    thr_rel = 0.02
    if grid > cap_mw * (1 + thr_rel):
        curtailed = grid - cap_mw
        grid = cap_mw
        print(f"\nCURTAILMENT:")
        print(f"  Grid > Cap × 1.02: {grid:.3f} > {cap_mw * 1.02:.3f}")
        print(f"  Curtailment = {curtailed:.3f} MW")
    else:
        curtailed = 0
        print(f"\nNO HAY CURTAILMENT")
    
    # Balance energético
    print(f"\nBALANCE ENERGÉTICO (dt=1h):")
    print(f"  Solar:              {solar_mw:.3f} MWh")
    print(f"  Grid:               {grid:.3f} MWh")
    print(f"  BESS carga:         {-battery_power:.3f} MWh")
    print(f"  Curtailment:        {curtailed:.3f} MWh")
    print(f"  Pérdidas:           {energy_loss:.3f} MWh")
    
    # Balance: Solar = Grid + Curtailment + BESS_carga
    balance = grid + curtailed + (-battery_power)
    print(f"\n  Solar = Grid + Curtailment + BESS_carga")
    print(f"  {solar_mw:.3f} = {grid:.3f} + {curtailed:.3f} + {-battery_power:.3f} = {balance:.3f}")
    print(f"  Error: {abs(solar_mw - balance):.6f} MWh")
    
    # ¿Dónde están las pérdidas en el balance?
    print(f"\nNOTA: Las pérdidas ({energy_loss:.3f} MWh) son internas al BESS")
    print(f"  - Energía que entra al BESS desde la red: {-battery_power:.3f} MWh")
    print(f"  - Energía almacenada en el BESS: {-battery_power - energy_loss:.3f} MWh")
    print(f"  - Las pérdidas NO deben sumarse al balance solar-grid")

def test_full_cycle():
    """Test ciclo completo carga-descarga para verificar balance"""
    
    print("\n\n" + "="*60)
    print("TEST CICLO COMPLETO")
    print("="*60)
    
    bess = BESSModel(
        power_mw=1.0,
        duration_hours=2.0,
        technology='modern_lfp',
        topology='parallel_ac',
        track_history=True,
        verbose=False
    )
    
    print(f"\nCiclo de 3 horas: Carga → Reposo → Descarga")
    
    # Hora 1: Cargar
    print(f"\nHORA 1 - CARGA:")
    res1 = bess.step(-1.0, dt=1.0)  # Cargar 1 MW por 1 hora
    print(f"  Energía de red:     {1.0:.3f} MWh")
    print(f"  Pérdidas:           {res1['energy_loss']:.3f} MWh")
    print(f"  Energía almacenada: {1.0 - res1['energy_loss']:.3f} MWh")
    print(f"  SOC: {bess.soc*100:.1f}%")
    
    # Hora 2: Reposo
    print(f"\nHORA 2 - REPOSO:")
    res2 = bess.step(0.0, dt=1.0)
    print(f"  Sin actividad")
    print(f"  SOC: {bess.soc*100:.1f}%")
    
    # Hora 3: Descargar
    print(f"\nHORA 3 - DESCARGA:")
    res3 = bess.step(0.8, dt=1.0)  # Descargar 0.8 MW por 1 hora
    print(f"  Energía a red:      {res3['actual_power']:.3f} MWh")
    print(f"  Pérdidas:           {res3['energy_loss']:.3f} MWh")
    print(f"  Energía del BESS:   {res3['actual_power'] + res3['energy_loss']:.3f} MWh")
    print(f"  SOC: {bess.soc*100:.1f}%")
    
    # Balance total
    total_in = 1.0
    total_out = res3['actual_power']
    total_losses = res1['energy_loss'] + res3['energy_loss']
    delta_stored = (bess.soc - 0.1) * bess.capacity_mwh  # SOC inicial era 10%
    
    print(f"\nBALANCE TOTAL DEL CICLO:")
    print(f"  Entrada:            {total_in:.3f} MWh")
    print(f"  Salida:             {total_out:.3f} MWh")
    print(f"  Pérdidas totales:   {total_losses:.3f} MWh")
    print(f"  ΔAlmacenado:        {delta_stored:.3f} MWh")
    print(f"\n  Entrada = Salida + Pérdidas + ΔAlmacenado")
    print(f"  {total_in:.3f} = {total_out:.3f} + {total_losses:.3f} + {delta_stored:.3f} = {total_out + total_losses + delta_stored:.3f}")
    print(f"  Error: {abs(total_in - total_out - total_losses - delta_stored):.6f} MWh")

if __name__ == "__main__":
    test_curtailment_logic()
    test_full_cycle()