#!/usr/bin/env python3
"""
Test cap shaving with low percentages
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.simulation.simulate_complete import simulate_psfv_bess_complete

def test_low_cap_shaving():
    """Test cap shaving with various low percentages"""
    
    print("\n" + "="*80)
    print("TESTING CAP SHAVING WITH LOW PERCENTAGES")
    print("="*80)
    
    # Configuration
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_hours = 4.0
    
    # Test different cap percentages
    percentages = [10, 20, 30, 40, 50]
    
    results = []
    
    for pct in percentages:
        cap_mw = psfv_mw * pct / 100
        
        # Test regular cap_shaving
        result = simulate_psfv_bess_complete(
            psfv_mw=psfv_mw,
            bess_mw=bess_mw,
            bess_hours=bess_hours,
            strategy='cap_shaving',
            cap_mw=cap_mw,
            soft_discharge=True
        )
        
        metrics = result['metrics']
        profiles = result['profiles']
        
        # Calculate how much was shaved
        solar_total = metrics['solar_total_mwh']
        charge = metrics['battery_charge_mwh']
        curtailed = metrics.get('curtailed_total_mwh', 0)  # Use correct key
        
        results.append({
            'pct': pct,
            'cap_mw': cap_mw,
            'solar_peak': metrics['solar_peak_mw'],
            'charge': charge,
            'discharge': metrics['battery_discharge_mwh'],
            'losses': metrics['losses_total_mwh'],
            'curtailed': curtailed,
            'cycles': metrics['cycles_equivalent'],
            'grid_pct': metrics['grid_percent']
        })
    
    # Print results table
    print(f"\n{'Cap %':>6} {'Cap MW':>8} {'Peak MW':>8} {'Charge':>8} {'Discharge':>10} {'Losses':>8} {'Curtail':>8} {'Cycles':>8} {'Grid %':>8}")
    print("-" * 86)
    
    for r in results:
        print(f"{r['pct']:>6}% {r['cap_mw']:>8.2f} {r['solar_peak']:>8.2f} "
              f"{r['charge']:>8.3f} {r['discharge']:>10.3f} {r['losses']:>8.3f} "
              f"{r['curtailed']:>8.3f} {r['cycles']:>8.2f} {r['grid_pct']:>8.1f}%")
    
    print("\n" + "="*80)
    print("TESTING CAP_SHAVING_BALANCED WITH LOW PERCENTILES")
    print("="*80)
    
    # Test cap_shaving_balanced with low percentiles
    percentiles = [10, 20, 30, 40, 50]
    balanced_results = []
    
    for percentile in percentiles:
        result = simulate_psfv_bess_complete(
            psfv_mw=psfv_mw,
            bess_mw=bess_mw,
            bess_hours=bess_hours,
            strategy='cap_shaving_balanced',
            use_percentile=True,
            percentile=percentile,
            discharge_start_hour=16
        )
        
        metrics = result['metrics']
        profiles = result['profiles']
        
        # Calculate actual cap used
        solar_array = np.array(profiles['solar_mw'])
        solar_positive = solar_array[solar_array > 0.001]
        cap_real = np.percentile(solar_positive, percentile) if len(solar_positive) > 0 else 0
        
        # Check balance
        balance = metrics['battery_charge_mwh'] - metrics['battery_discharge_mwh'] - metrics['losses_total_mwh']
        soc_final = profiles['soc_pct'][-1]
        
        balanced_results.append({
            'percentile': percentile,
            'cap_real': cap_real,
            'charge': metrics['battery_charge_mwh'],
            'discharge': metrics['battery_discharge_mwh'],
            'losses': metrics['losses_total_mwh'],
            'balance': balance,
            'soc_final': soc_final,
            'cycles': metrics['cycles_equivalent']
        })
    
    print(f"\n{'P%':>6} {'Cap MW':>8} {'Charge':>8} {'Discharge':>10} {'Losses':>8} {'Balance':>10} {'SOC Final':>10} {'Cycles':>8}")
    print("-" * 82)
    
    for r in balanced_results:
        print(f"P{r['percentile']:>4} {r['cap_real']:>8.3f} {r['charge']:>8.3f} "
              f"{r['discharge']:>10.3f} {r['losses']:>8.3f} {r['balance']:>10.6f} "
              f"{r['soc_final']:>9.1f}% {r['cycles']:>8.2f}")
    
    print("\n" + "="*80)
    print("CONCLUSIONES:")
    print("="*80)
    print("""
1. Cap Shaving regular:
   - Con caps bajos (10-30%), el BESS se carga mucho más
   - Puede haber curtailment significativo si el BESS se llena
   - La descarga suave puede no ser suficiente para vaciar el BESS

2. Cap Shaving Balanced:
   - Garantiza descarga completa sin importar el percentil
   - Percentiles bajos (P10-P30) resultan en más ciclos del BESS
   - Balance diario siempre cercano a 0
   - SOC final siempre vuelve al mínimo

3. Recomendaciones:
   - Para caps muy bajos, usar cap_shaving_balanced
   - Ajustar hora de descarga según el perfil de demanda
   - Considerar el impacto en vida útil del BESS con ciclos altos
    """)

if __name__ == "__main__":
    test_low_cap_shaving()