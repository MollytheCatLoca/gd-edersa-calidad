#!/usr/bin/env python3
"""
Script de prueba para verificar la simulación PSFV + BESS
Configuración: PSFV 1MW, BESS 1MW/4h, Cap Shaving 70%
"""

import sys
from pathlib import Path
import numpy as np

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from dashboard.pages.utils.constants import (
    BESSTechnology, 
    BESSTopology,
    AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW
)

def generate_solar_profile(power_mw: float = 1.0) -> np.ndarray:
    """Genera perfil solar diario realista usando el promedio anual"""
    # Usar el promedio mensual (1870 MWh/año)
    daily_energy = AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW / 30  # ~5.19 MWh/día
    
    # Perfil horario típico
    hours = np.arange(24)
    daylight = (6 <= hours) & (hours <= 18)
    
    # Curva gaussiana centrada al mediodía
    profile = np.zeros(24)
    x = (hours - 12) / 6
    profile[daylight] = np.exp(-2 * x[daylight]**2)
    
    # Normalizar para que sume la energía diaria objetivo
    if profile.sum() > 0:
        profile = profile * daily_energy / profile.sum()
    
    # Escalar por potencia instalada
    profile = profile * power_mw
    
    return profile

def test_cap_shaving_simulation():
    """Prueba simulación con cap shaving al 70%"""
    
    print("=== PRUEBA DE SIMULACIÓN PSFV + BESS ===")
    print()
    
    # Configuración
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_hours = 4.0
    cap_percent = 70
    cap_mw = psfv_mw * cap_percent / 100  # 0.7 MW
    
    print(f"Configuración:")
    print(f"- PSFV: {psfv_mw} MW")
    print(f"- BESS: {bess_mw} MW / {bess_hours} h = {bess_mw * bess_hours} MWh")
    print(f"- Estrategia: Cap Shaving al {cap_percent}% ({cap_mw} MW)")
    print()
    
    # Generar perfil solar
    solar_profile = generate_solar_profile(psfv_mw)
    
    print(f"Perfil solar:")
    print(f"- Energía total: {solar_profile.sum():.3f} MWh/día")
    print(f"- Pico máximo: {solar_profile.max():.3f} MW")
    print(f"- Factor de capacidad: {solar_profile.sum() / (psfv_mw * 24) * 100:.1f}%")
    print()
    
    # Crear BESS con tecnología moderna LFP
    bess = BESSModel(
        power_mw=bess_mw,
        duration_hours=bess_hours,
        technology=BESSTechnology.MODERN_LFP,
        topology=BESSTopology.PARALLEL_AC,
        verbose=True
    )
    
    print(f"BESS creado:")
    print(f"- Tecnología: {bess.technology}")
    print(f"- Eficiencia round-trip: {bess.eff_roundtrip:.1%}")
    print(f"- SOC límites: {bess.tech_params['soc_min']:.0%} - {bess.tech_params['soc_max']:.0%}")
    print()
    
    # Simular con cap_shaving
    print("Ejecutando simulación...")
    results = bess.simulate_strategy(
        solar_profile=solar_profile,
        strategy='cap_shaving',
        cap_mw=cap_mw,  # Pasar el límite específico
        soft_discharge=True,
        dt=1.0
    )
    
    # Analizar resultados
    print("\n=== RESULTADOS ===")
    print()
    
    # Energías
    solar_total = solar_profile.sum()
    grid_total = results['grid_power'].sum()
    losses_total = results['energy_losses'].sum()
    curtailed_total = results['solar_curtailed'].sum()
    
    print(f"Balance energético (MWh/día):")
    print(f"- Generación solar:  {solar_total:.3f} (100.0%)")
    print(f"- Energía a red:     {grid_total:.3f} ({grid_total/solar_total*100:.1f}%)")
    print(f"- Pérdidas BESS:     {losses_total:.3f} ({losses_total/solar_total*100:.1f}%)")
    print(f"- Curtailment:       {curtailed_total:.3f} ({curtailed_total/solar_total*100:.1f}%)")
    print(f"- Balance:           {solar_total - grid_total - losses_total - curtailed_total:.6f}")
    print()
    
    # Operación BESS
    battery_charge = -results['battery_power'][results['battery_power'] < 0].sum()
    battery_discharge = results['battery_power'][results['battery_power'] > 0].sum()
    
    print(f"Operación BESS:")
    print(f"- Energía cargada:   {battery_charge:.3f} MWh")
    print(f"- Energía descargada: {battery_discharge:.3f} MWh")
    print(f"- Pérdidas totales:   {losses_total:.3f} MWh")
    print(f"- Eficiencia realizada: {battery_discharge/battery_charge*100 if battery_charge > 0 else 0:.1f}%")
    print(f"- Ciclos equivalentes: {results['total_cycles']:.2f}")
    print()
    
    # Verificar cap shaving
    max_grid = results['grid_power'].max()
    hours_above_cap = sum(1 for p in results['grid_power'] if p > cap_mw * 1.02)  # 2% tolerancia
    
    print(f"Verificación Cap Shaving:")
    print(f"- Límite objetivo:    {cap_mw:.3f} MW")
    print(f"- Máximo en red:      {max_grid:.3f} MW")
    print(f"- Horas sobre límite: {hours_above_cap}")
    print()
    
    # Mostrar perfil horario
    print("Perfil horario:")
    print("Hora | Solar | BESS  | Red   | SOC  | Pérd.")
    print("-----|-------|-------|-------|------|------")
    for h in range(24):
        print(f" {h:2d}  | {solar_profile[h]:5.3f} | {results['battery_power'][h]:+5.3f} | "
              f"{results['grid_power'][h]:5.3f} | {results['soc'][h]*100:4.0f}% | {results['energy_losses'][h]*1000:4.1f}")
    
    return results

if __name__ == "__main__":
    results = test_cap_shaving_simulation()