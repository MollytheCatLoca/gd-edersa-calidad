#!/usr/bin/env python3
"""
Script de diagnóstico para identificar el error de balance energético
Compara resultados directos de BESSModel vs simulador del dashboard
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from src.battery.bess_strategies import BESSStrategies
from dashboard.pages.utils.solar_bess_simulator import SolarBESSSimulator
from dashboard.pages.utils.constants import MONTHLY_SOLAR_GENERATION_MWH_PER_MW
from dashboard.pages.utils.models import DataStatus

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

def test_direct_bess_model(cap_percent=30, psfv_mw=1.0, bess_mw=1.0, bess_hours=2.0):
    """Test directo con BESSModel"""
    print("\n" + "="*60)
    print("TEST 1: BESS MODEL DIRECTO")
    print("="*60)
    
    cap_mw = psfv_mw * cap_percent / 100
    
    # Crear BESS
    bess = BESSModel(
        power_mw=bess_mw,
        duration_hours=bess_hours,
        technology='premium',
        topology='parallel_ac',
        track_history=True,
        verbose=False
    )
    
    # Generar perfil solar
    solar = generate_solar_profile(psfv_mw)
    
    # Simular estrategia
    results = bess.simulate_strategy(
        solar_profile=solar,
        strategy='cap_shaving',
        cap_mw=cap_mw,
        soft_discharge=True
    )
    
    # Extraer métricas
    solar_total = solar.sum()
    grid_total = results['grid_power'].sum()
    losses_total = results['energy_losses'].sum()
    curtailed_total = results['solar_curtailed'].sum()
    
    # ΔSOC
    soc_initial = results['soc'][0]
    soc_final = results['soc'][-1]
    delta_soc_energy = (soc_final - soc_initial) * bess.capacity_mwh
    
    # Balance
    balance_total = grid_total + losses_total + curtailed_total + delta_soc_energy
    error = abs(solar_total - balance_total)
    
    print(f"\nMÉTRICAS DIRECTAS:")
    print(f"  Solar total:     {solar_total:.6f} MWh")
    print(f"  Grid total:      {grid_total:.6f} MWh")
    print(f"  Losses:          {losses_total:.6f} MWh")
    print(f"  Curtailment:     {curtailed_total:.6f} MWh")
    print(f"  ΔSOC energy:     {delta_soc_energy:.6f} MWh")
    print(f"  Balance check:   {balance_total:.6f} MWh")
    print(f"  Error:           {error:.6f} MWh")
    
    return {
        'solar': solar_total,
        'grid': grid_total,
        'losses': losses_total,
        'curtailed': curtailed_total,
        'delta_soc': delta_soc_energy,
        'error': error,
        'soc_initial': soc_initial,
        'soc_final': soc_final
    }

def test_simulator(cap_percent=30, psfv_mw=1.0, bess_mw=1.0, bess_hours=2.0):
    """Test con el simulador del dashboard"""
    print("\n" + "="*60)
    print("TEST 2: SIMULADOR DEL DASHBOARD")
    print("="*60)
    
    cap_mw = psfv_mw * cap_percent / 100
    
    # Crear simulador
    simulator = SolarBESSSimulator()
    
    # Simular
    result = simulator.simulate_solar_with_bess(
        station="Los Menucos",
        psfv_power_mw=psfv_mw,
        bess_power_mw=bess_mw,
        bess_duration_h=bess_hours,
        strategy="cap_shaving",
        month=6,
        cap_mw=cap_mw
    )
    
    if result.status != DataStatus.REAL or not result.data:
        print("ERROR: Simulación falló")
        return None
    
    # Extraer métricas
    metrics = result.data.get('metrics', {})
    profiles = result.data.get('profiles', {})
    
    solar_profile = np.array(profiles.get('solar_mw', []))
    grid_profile = np.array(profiles.get('net_mw', []))
    bess_profile = np.array(profiles.get('bess_mw', []))
    soc_profile = np.array(profiles.get('soc_pct', []))
    losses_profile = np.array(profiles.get('losses_mwh', []))
    
    # Calcular totales
    solar_total = solar_profile.sum()
    grid_total = grid_profile.sum()
    losses_total = metrics.get('energy_losses_mwh', 0)
    curtailed_total = metrics.get('solar_curtailed_mwh', 0)
    
    # ΔSOC
    if len(soc_profile) > 0:
        soc_initial = soc_profile[0]
        soc_final = soc_profile[-1]
        delta_soc_energy = (soc_final - soc_initial) * bess_mw * bess_hours / 100
    else:
        soc_initial = soc_final = 0
        delta_soc_energy = 0
    
    # Balance
    balance_total = grid_total + losses_total + curtailed_total + delta_soc_energy
    error = abs(solar_total - balance_total)
    
    print(f"\nMÉTRICAS SIMULADOR:")
    print(f"  Solar total:     {solar_total:.6f} MWh")
    print(f"  Grid total:      {grid_total:.6f} MWh (metrics: {metrics.get('total_net_mwh', 0):.6f})")
    print(f"  Losses:          {losses_total:.6f} MWh")
    print(f"  Curtailment:     {curtailed_total:.6f} MWh")
    print(f"  ΔSOC energy:     {delta_soc_energy:.6f} MWh")
    print(f"  Balance check:   {balance_total:.6f} MWh")
    print(f"  Error:           {error:.6f} MWh")
    
    # Verificar si losses_profile suma correctamente
    losses_from_profile = losses_profile.sum() if len(losses_profile) > 0 else 0
    print(f"\n  Losses from profile sum: {losses_from_profile:.6f} MWh")
    print(f"  Losses from metrics:     {losses_total:.6f} MWh")
    print(f"  Difference:              {abs(losses_from_profile - losses_total):.6f} MWh")
    
    return {
        'solar': solar_total,
        'grid': grid_total,
        'losses': losses_total,
        'curtailed': curtailed_total,
        'delta_soc': delta_soc_energy,
        'error': error,
        'soc_initial': soc_initial,
        'soc_final': soc_final,
        'losses_profile_sum': losses_from_profile
    }

def compare_results(direct, simulator):
    """Compara resultados y encuentra diferencias"""
    print("\n" + "="*60)
    print("COMPARACIÓN DE RESULTADOS")
    print("="*60)
    
    print(f"\n{'Métrica':<20} {'Directo':>12} {'Simulador':>12} {'Diferencia':>12}")
    print("-" * 60)
    
    for key in ['solar', 'grid', 'losses', 'curtailed', 'delta_soc', 'error']:
        if key in direct and key in simulator:
            diff = simulator[key] - direct[key]
            print(f"{key:<20} {direct[key]:>12.6f} {simulator[key]:>12.6f} {diff:>12.6f}")
    
    print(f"\nSOC inicial:         {direct['soc_initial']:>12.3f} {simulator['soc_initial']:>12.3f}")
    print(f"SOC final:           {direct['soc_final']:>12.3f} {simulator['soc_final']:>12.3f}")
    
    # Análisis de diferencias
    print("\n" + "="*60)
    print("ANÁLISIS DE DIFERENCIAS")
    print("="*60)
    
    if abs(simulator['error'] - direct['error']) > 0.001:
        print("\n⚠️  HAY UNA DIFERENCIA SIGNIFICATIVA EN EL ERROR DE BALANCE")
        
        # Verificar cada componente
        if abs(simulator['solar'] - direct['solar']) > 0.001:
            print(f"  - Solar total difiere en {simulator['solar'] - direct['solar']:.6f} MWh")
        
        if abs(simulator['grid'] - direct['grid']) > 0.001:
            print(f"  - Grid total difiere en {simulator['grid'] - direct['grid']:.6f} MWh")
        
        if abs(simulator['losses'] - direct['losses']) > 0.001:
            print(f"  - Pérdidas difieren en {simulator['losses'] - direct['losses']:.6f} MWh")
            if 'losses_profile_sum' in simulator:
                print(f"    - Profile sum: {simulator['losses_profile_sum']:.6f} vs metrics: {simulator['losses']:.6f}")
        
        if abs(simulator['curtailed'] - direct['curtailed']) > 0.001:
            print(f"  - Curtailment difiere en {simulator['curtailed'] - direct['curtailed']:.6f} MWh")
        
        if abs(simulator['delta_soc'] - direct['delta_soc']) > 0.001:
            print(f"  - ΔSOC difiere en {simulator['delta_soc'] - direct['delta_soc']:.6f} MWh")
    else:
        print("\n✓ Los resultados son consistentes entre ambos métodos")

def main():
    """Ejecuta el diagnóstico completo"""
    print("\n" + "="*80)
    print("DIAGNÓSTICO DE ERROR DE BALANCE ENERGÉTICO")
    print("Configuración: PSFV 1MW, BESS 1MW/2h, Cap Shaving 30%")
    print("="*80)
    
    # Ejecutar tests
    direct_results = test_direct_bess_model(cap_percent=30)
    simulator_results = test_simulator(cap_percent=30)
    
    if direct_results and simulator_results:
        compare_results(direct_results, simulator_results)
    
    print("\n" + "="*80)
    print("CONCLUSIÓN:")
    if direct_results['error'] < 0.001:
        print("✓ El modelo directo tiene balance energético correcto")
    
    if simulator_results and simulator_results['error'] > 0.01:
        print("✗ El simulador del dashboard tiene un error de balance significativo")
        print(f"  Error: {simulator_results['error']:.6f} MWh")
        print("\n  Posibles causas:")
        print("  1. Diferencia en el cálculo de pérdidas")
        print("  2. Diferencia en el perfil solar generado")
        print("  3. Problema con el mapeo de estrategias")
        print("  4. Error en la agregación de métricas")

if __name__ == "__main__":
    main()