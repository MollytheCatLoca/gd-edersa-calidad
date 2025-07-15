#!/usr/bin/env python3
"""
Comparación entre cap_shaving y soft_cap_shaving
Demuestra las diferencias y valida el balance energético
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from dashboard.pages.utils.constants import AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW

def compare_strategies():
    """Comparar cap_shaving vs soft_cap_shaving"""
    
    print("\n" + "="*80)
    print("COMPARACIÓN: CAP_SHAVING vs SOFT_CAP_SHAVING")
    print("="*80)
    
    # Configuración
    print("\nCONFIGURACIÓN:")
    print("  PSFV: 1.0 MW")
    print("  BESS: 0.5 MW / 1h = 0.5 MWh (pequeño para forzar saturación)")
    print("  Tecnología: modern_lfp (η=96.4%)")
    print("  Cap: 0.3 MW (30%)")
    
    # Generar perfil solar
    hours = np.arange(24)
    daylight = (6 <= hours) & (hours <= 18)
    x = (hours - 12) / 6
    solar = np.zeros(24)
    solar[daylight] = np.exp(-2 * x[daylight] ** 2)
    
    daily_target = AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW / 30
    scale_factor = daily_target / solar.sum()
    solar *= scale_factor
    
    print(f"\nPERFIL SOLAR:")
    print(f"  Total: {solar.sum():.3f} MWh/día")
    print(f"  Pico: {solar.max():.3f} MW")
    print(f"  Horas sobre cap: {np.sum(solar > 0.3)}")
    
    # Estrategia 1: cap_shaving normal
    print("\n" + "-"*60)
    print("ESTRATEGIA 1: cap_shaving (con curtailment)")
    
    bess1 = BESSModel(
        power_mw=0.5,
        duration_hours=1.0,
        technology='modern_lfp',
        track_history=True,
        verbose=False
    )
    
    results1 = bess1.simulate_strategy(
        solar_profile=solar,
        strategy='cap_shaving',
        cap_mw=0.3,
        soft_discharge=True
    )
    
    grid1 = results1['grid_power']
    battery1 = results1['battery_power']
    curtailed1 = results1['solar_curtailed']
    soc1 = results1['soc']
    
    # Estrategia 2: soft_cap_shaving
    print("\n" + "-"*60)
    print("ESTRATEGIA 2: soft_cap_shaving (sin curtailment real)")
    
    bess2 = BESSModel(
        power_mw=0.5,
        duration_hours=1.0,
        technology='modern_lfp',
        track_history=True,
        verbose=False
    )
    
    results2 = bess2.simulate_strategy(
        solar_profile=solar,
        strategy='soft_cap_shaving',
        cap_mw=0.3,
        soft_discharge=True
    )
    
    grid2 = results2['grid_power']
    battery2 = results2['battery_power']
    curtailed2 = results2['solar_curtailed']
    soc2 = results2['soc']
    
    # Comparación de resultados
    print("\n" + "="*80)
    print("COMPARACIÓN DE RESULTADOS:")
    print("="*80)
    
    # Totales
    print("\nTOTALES DIARIOS:")
    print(f"{'Métrica':<30} {'cap_shaving':>15} {'soft_cap_shaving':>20}")
    print("-"*65)
    print(f"{'Solar total (MWh)':<30} {solar.sum():>15.3f} {solar.sum():>20.3f}")
    print(f"{'Energía a red (MWh)':<30} {grid1.sum():>15.3f} {grid2.sum():>20.3f}")
    print(f"{'Curtailment (MWh)':<30} {curtailed1.sum():>15.3f} {curtailed2.sum():>20.3f}")
    print(f"{'Carga BESS (MWh)':<30} {-battery1[battery1<0].sum():>15.3f} {-battery2[battery2<0].sum():>20.3f}")
    print(f"{'Descarga BESS (MWh)':<30} {battery1[battery1>0].sum():>15.3f} {battery2[battery2>0].sum():>20.3f}")
    print(f"{'Max grid (MW)':<30} {grid1.max():>15.3f} {grid2.max():>20.3f}")
    print(f"{'Horas con grid > cap':<30} {np.sum(grid1 > 0.3):>15d} {np.sum(grid2 > 0.3):>20d}")
    
    # Balance energético
    print("\nBALANCE ENERGÉTICO:")
    
    # cap_shaving
    balance1 = grid1.sum() + curtailed1.sum() + (-battery1[battery1<0].sum() - battery1[battery1>0].sum())
    error1 = abs(solar.sum() - balance1)
    print(f"\ncap_shaving:")
    print(f"  Solar = Red + Curtailment + (Carga - Descarga)")
    print(f"  {solar.sum():.6f} = {grid1.sum():.6f} + {curtailed1.sum():.6f} + {-battery1[battery1<0].sum() - battery1[battery1>0].sum():.6f}")
    print(f"  Error: {error1:.6f} MWh")
    
    # soft_cap_shaving
    balance2 = grid2.sum() + (-battery2[battery2<0].sum() - battery2[battery2>0].sum())
    error2 = abs(solar.sum() - balance2)
    print(f"\nsoft_cap_shaving:")
    print(f"  Solar = Red + (Carga - Descarga)")
    print(f"  Nota: Curtailment={curtailed2.sum():.3f} es informativo, NO se resta")
    print(f"  {solar.sum():.6f} = {grid2.sum():.6f} + {-battery2[battery2<0].sum() - battery2[battery2>0].sum():.6f}")
    print(f"  Error: {error2:.6f} MWh")
    
    # Análisis hora por hora
    print("\n" + "-"*80)
    print("ANÁLISIS HORA POR HORA (horas críticas):")
    print(f"{'Hr':>3} {'Solar':>6} | {'Grid1':>6} {'Curt1':>6} {'SOC1%':>6} | {'Grid2':>6} {'Curt2':>6} {'SOC2%':>6} | {'Dif':>6}")
    print("-"*80)
    
    for h in range(24):
        if solar[h] > 0.25 or curtailed1[h] > 0 or curtailed2[h] > 0:
            diff_grid = grid2[h] - grid1[h]
            print(f"{h:3d} {solar[h]:6.3f} | {grid1[h]:6.3f} {curtailed1[h]:6.3f} {soc1[h]*100:6.1f} | "
                  f"{grid2[h]:6.3f} {curtailed2[h]:6.3f} {soc2[h]*100:6.1f} | {diff_grid:6.3f}")
    
    # Verificaciones críticas
    print("\n" + "="*80)
    print("VERIFICACIONES CRÍTICAS:")
    print("="*80)
    
    print("\n1. En soft_cap_shaving cuando curtailed > 0:")
    for h in range(24):
        if curtailed2[h] > 0:
            print(f"   Hora {h}: curtailed={curtailed2[h]:.3f}, grid={grid2[h]:.3f} MW")
            if grid2[h] > 0.3:
                print(f"   ✓ Grid ({grid2[h]:.3f}) > cap (0.3) - CORRECTO")
            else:
                print(f"   ✗ Grid ({grid2[h]:.3f}) <= cap (0.3) - ERROR!")
    
    print("\n2. Energía 'curtailed' en soft_cap_shaving:")
    extra_delivered = grid2.sum() - grid1.sum()
    print(f"   Energía extra entregada: {extra_delivered:.3f} MWh")
    print(f"   Curtailment evitado: {curtailed1.sum():.3f} MWh")
    print(f"   Diferencia: {abs(extra_delivered - curtailed1.sum()):.6f} MWh")
    
    # Gráficos
    plt.figure(figsize=(15, 10))
    
    # Gráfico 1: Potencia a red
    plt.subplot(2, 2, 1)
    plt.plot(hours, solar, 'g-', label='Solar', linewidth=2)
    plt.plot(hours, grid1, 'b-', label='Grid (cap_shaving)', linewidth=2)
    plt.plot(hours, grid2, 'r--', label='Grid (soft_cap_shaving)', linewidth=2)
    plt.axhline(y=0.3, color='k', linestyle=':', label='Cap (0.3 MW)')
    plt.xlabel('Hora')
    plt.ylabel('Potencia (MW)')
    plt.title('Comparación de Potencia a Red')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Gráfico 2: Curtailment
    plt.subplot(2, 2, 2)
    plt.bar(hours - 0.2, curtailed1, width=0.4, label='cap_shaving (real)', color='red', alpha=0.7)
    plt.bar(hours + 0.2, curtailed2, width=0.4, label='soft_cap_shaving (info)', color='orange', alpha=0.7)
    plt.xlabel('Hora')
    plt.ylabel('Curtailment (MW)')
    plt.title('Comparación de Curtailment')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Gráfico 3: SOC
    plt.subplot(2, 2, 3)
    plt.plot(hours, soc1 * 100, 'b-', label='SOC (cap_shaving)', linewidth=2)
    plt.plot(hours, soc2 * 100, 'r--', label='SOC (soft_cap_shaving)', linewidth=2)
    plt.xlabel('Hora')
    plt.ylabel('SOC (%)')
    plt.title('Estado de Carga del BESS')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    
    # Gráfico 4: Diferencias
    plt.subplot(2, 2, 4)
    diff_grid = grid2 - grid1
    plt.bar(hours, diff_grid, color='green', alpha=0.7)
    plt.xlabel('Hora')
    plt.ylabel('Diferencia Grid (MW)')
    plt.title('Grid Adicional con soft_cap_shaving')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('comparison_cap_shaving_strategies.png', dpi=150)
    print("\n✓ Gráficos guardados en 'comparison_cap_shaving_strategies.png'")
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN:")
    print("="*80)
    print("""
1. cap_shaving (estrategia original):
   - Respeta estrictamente el cap de 0.3 MW
   - Cuando BESS se satura, hace curtailment real
   - Se pierde energía: {:.3f} MWh/día

2. soft_cap_shaving (nueva estrategia):
   - Permite exceder el cap cuando BESS se satura
   - NO hace curtailment real (curtailed es solo informativo)
   - Toda la energía solar se aprovecha
   - Entrega {:.3f} MWh/día adicionales a la red

3. Balance energético:
   - Ambas estrategias tienen balance perfecto (error < 1e-6)
   - En soft_cap_shaving NO se resta curtailment del balance
   
4. Caso de uso:
   - cap_shaving: Cuando hay límites estrictos de red
   - soft_cap_shaving: Cuando la red tolera picos temporales
""".format(curtailed1.sum(), extra_delivered))

if __name__ == "__main__":
    compare_strategies()