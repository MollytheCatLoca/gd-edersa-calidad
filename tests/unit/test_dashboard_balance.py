#!/usr/bin/env python3
"""
Script para verificar que el balance energético se muestra correctamente en el dashboard
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dashboard.pages.utils.solar_bess_simulator import SolarBESSSimulator
from dashboard.pages.utils.models import DataStatus

def test_dashboard_balance():
    """Test balance energético en dashboard con cap_shaving"""
    
    print("\n" + "="*60)
    print("VERIFICACIÓN BALANCE ENERGÉTICO EN DASHBOARD")
    print("="*60 + "\n")
    
    # Create simulator instance
    simulator = SolarBESSSimulator()
    
    # Test configuration - matching your example
    station = "Los Menucos"
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_h = 2.0
    
    # Test cap_shaving with 30% cap (should show significant ΔSOC)
    print("Test: Cap Shaving 30%")
    print("-" * 40)
    
    result = simulator.simulate_solar_with_bess(
        station=station,
        psfv_power_mw=psfv_mw,
        bess_power_mw=bess_mw,
        bess_duration_h=bess_h,
        strategy="cap_shaving",
        month=6,
        cap_mw=0.3  # 30% of 1MW
    )
    
    if result.status == DataStatus.REAL and result.data:
        metrics = result.data.get('metrics', {})
        profiles = result.data.get('profiles', {})
        bess_data = result.data.get('bess_data', {})
        
        # Extract data
        solar_profile = profiles.get('solar_mw', [])
        solar_total = sum(solar_profile) if solar_profile else metrics.get('total_generation_mwh', 0)
        grid_total = metrics.get('total_net_mwh', 0)
        losses = metrics.get('energy_losses_mwh', 0)
        curtailed = metrics.get('solar_curtailed_mwh', 0)
        
        # Calculate ΔSOC energy
        soc_profile = profiles.get('soc_pct', [])
        if soc_profile:
            soc_initial = soc_profile[0]
            soc_final = soc_profile[-1]
            delta_soc_energy = (soc_final - soc_initial) * bess_mw * bess_h / 100
        else:
            delta_soc_energy = 0
        
        # Calculate charge/discharge
        bess_profile = profiles.get('bess_mw', [])
        charge = sum([-b for b in bess_profile if b < 0])
        discharge = sum([b for b in bess_profile if b > 0])
        
        print(f"\nBALANCE ENERGÉTICO (como aparecerá en dashboard):")
        print(f"  Generación Solar:     {solar_total:.3f} MWh (100.0%)")
        if solar_total > 0:
            print(f"  Energía a Red:        {grid_total:.3f} MWh ({grid_total/solar_total*100:.1f}%)")
            print(f"  Pérdidas BESS:        {losses:.3f} MWh ({losses/solar_total*100:.1f}%)")
            print(f"  Curtailment:          {curtailed:.3f} MWh ({curtailed/solar_total*100:.1f}%)")
            print(f"  ΔSOC Energía:         {delta_soc_energy:.3f} MWh ({delta_soc_energy/solar_total*100:.1f}%)")
        else:
            print("  ERROR: No hay generación solar!")
        
        # Verify balance
        balance_total = grid_total + losses + curtailed + delta_soc_energy
        error = abs(solar_total - balance_total)
        
        print(f"\n  BALANCE: {solar_total:.3f} = {grid_total:.3f} + {losses:.3f} + {curtailed:.3f} + {delta_soc_energy:.3f}")
        print(f"  Error: {error:.6f} MWh")
        
        print(f"\nDetalles de Operación BESS:")
        print(f"  Tecnología: premium (95.0% eficiencia round-trip)")
        print(f"  Capacidad: {bess_mw} MW / {bess_h}h = {bess_mw * bess_h:.1f} MWh")
        print(f"  Energía cargada: {charge:.3f} MWh")
        print(f"  Energía descargada: {discharge:.3f} MWh")
        print(f"  Pérdidas totales: {losses:.3f} MWh ({losses/charge*100 if charge > 0 else 0:.1f}% de lo cargado)")
        print(f"  SOC inicial: {soc_initial:.1f}% → SOC final: {soc_final:.1f}%")
        
        # Analysis
        print(f"\n{'✓' if error < 0.001 else '✗'} Balance energético {'correcto' if error < 0.001 else 'con error'}")
        
        if delta_soc_energy > 0.1:
            print("\n⚠️  NOTA: El BESS queda con energía sin descargar (ΔSOC > 0)")
            print("   Esto es esperado con cap_shaving original y caps bajos")
            print("   El soft discharge es insuficiente para vaciar el BESS")
    else:
        print(f"✗ Error: {result.meta.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    print("Para ver en el dashboard:")
    print("1. Navegar a http://localhost:8050/fase4-bess-lab")
    print("2. Configurar PSFV: 1 MW, BESS: 1 MW / 2h")
    print("3. Seleccionar 'Cap Shaving' con 30%")
    print("4. La tabla de auditoría debe mostrar el balance completo con ΔSOC")
    print("="*60)

if __name__ == "__main__":
    test_dashboard_balance()