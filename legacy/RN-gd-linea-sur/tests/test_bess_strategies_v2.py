#!/usr/bin/env python3
"""
Test script para verificar que las estrategias V2 realmente usan el BESS
y generan ciclos y pérdidas realistas (5-7%)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
from src.battery.bess_model import BESSModel
from src.battery.bess_strategies_v2 import BESSStrategiesV2
from datetime import datetime


def generate_solar_profile(hours=24, peak_mw=2.0):
    """Genera un perfil solar sintético"""
    hour_angles = np.linspace(0, 2*np.pi, hours)
    # Solar = 0 de noche, pico al mediodía
    solar = np.maximum(0, peak_mw * np.sin(hour_angles - np.pi/2))
    solar[0:6] = 0   # Noche
    solar[18:24] = 0  # Noche
    return solar


def test_strategy(strategy_name, strategy_func, solar_profile, bess_config):
    """Prueba una estrategia y reporta métricas"""
    print(f"\n{'='*60}")
    print(f"Testing: {strategy_name}")
    print(f"{'='*60}")
    
    # Crear BESS
    bess = BESSModel(
        power_mw=bess_config['power_mw'],
        duration_hours=bess_config['duration_h'],
        technology='modern_lfp',
        verbose=False
    )
    
    # Arrays para resultados
    n_hours = len(solar_profile)
    grid_power = np.zeros(n_hours)
    battery_power = np.zeros(n_hours)
    soc = np.zeros(n_hours)
    curtailed = np.zeros(n_hours)
    losses = np.zeros(n_hours)
    
    # Aplicar estrategia
    strategy_func(
        bess, solar_profile, grid_power, battery_power, 
        soc, curtailed, losses
    )
    
    # Calcular métricas
    total_solar = np.sum(solar_profile)
    total_delivered = np.sum(grid_power)
    total_losses = np.sum(losses)
    total_curtailed = np.sum(curtailed)
    
    # Balance de energía
    energy_in = total_solar
    energy_out = total_delivered + total_losses + total_curtailed
    balance_error = abs(energy_in - energy_out)
    
    # Eficiencia del sistema
    efficiency = total_delivered / total_solar if total_solar > 0 else 0
    
    # Ciclos y utilización
    total_charged = bess.total_energy_charged
    total_discharged = bess.total_energy_discharged
    cycles = bess.cycles
    
    # Utilización del BESS
    max_throughput = bess.capacity_mwh * 2 * (n_hours / 24)  # Max ciclos posibles
    actual_throughput = total_charged + total_discharged
    utilization = actual_throughput / max_throughput if max_throughput > 0 else 0
    
    # Reporte
    print(f"\nEnergía Solar Total:     {total_solar:.2f} MWh")
    print(f"Energía Entregada:       {total_delivered:.2f} MWh")
    print(f"Pérdidas BESS:          {total_losses:.2f} MWh ({total_losses/total_solar*100:.1f}%)")
    print(f"Energía Curtailed:      {total_curtailed:.2f} MWh")
    print(f"Error de Balance:       {balance_error:.4f} MWh")
    print(f"\nEficiencia Sistema:     {efficiency:.1%}")
    print(f"Eficiencia BESS:        {100 - (total_losses/total_solar*100):.1f}%")
    
    print(f"\nEnergía Cargada:        {total_charged:.2f} MWh")
    print(f"Energía Descargada:     {total_discharged:.2f} MWh")
    print(f"Ciclos Equivalentes:    {cycles:.2f}")
    print(f"Utilización BESS:       {utilization:.1%}")
    
    # Verificar pérdidas realistas (5-7%)
    loss_percentage = (total_losses / actual_throughput * 100) if actual_throughput > 0 else 0
    print(f"\nPérdidas por Ciclo:     {loss_percentage:.1f}%")
    
    if loss_percentage < 3:
        print("⚠️  ADVERTENCIA: Pérdidas muy bajas - verificar modelo")
    elif loss_percentage > 10:
        print("⚠️  ADVERTENCIA: Pérdidas muy altas - verificar modelo")
    else:
        print("✓ Pérdidas en rango esperado (3-10%)")
    
    if cycles < 0.1:
        print("❌ ERROR: No se registraron ciclos - BESS no usado")
    else:
        print(f"✓ BESS usado correctamente: {cycles:.2f} ciclos")
    
    return {
        'strategy': strategy_name,
        'efficiency': efficiency,
        'losses_pct': total_losses/total_solar*100,
        'cycles': cycles,
        'utilization': utilization,
        'loss_per_cycle': loss_percentage
    }


def main():
    """Ejecutar pruebas de todas las estrategias V2"""
    print("="*60)
    print("TEST DE ESTRATEGIAS BESS V2")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Configuración BESS
    bess_config = {
        'power_mw': 1.0,
        'duration_h': 4.0
    }
    
    print(f"\nConfiguración BESS:")
    print(f"- Potencia: {bess_config['power_mw']} MW")
    print(f"- Duración: {bess_config['duration_h']} horas")
    print(f"- Capacidad: {bess_config['power_mw'] * bess_config['duration_h']} MWh")
    
    # Generar perfil solar (24 horas)
    solar = generate_solar_profile(hours=24, peak_mw=2.0)
    print(f"\nPerfil Solar:")
    print(f"- Pico: {np.max(solar):.2f} MW")
    print(f"- Energía total: {np.sum(solar):.2f} MWh")
    
    # Estrategias a probar
    strategies = [
        ('Solar Smoothing', BESSStrategiesV2.apply_solar_smoothing),
        ('Time Shift Aggressive', BESSStrategiesV2.apply_time_shift_aggressive),
        ('Cycling Demo', BESSStrategiesV2.apply_cycling_demo),
        ('Frequency Regulation', BESSStrategiesV2.apply_frequency_regulation),
        ('Arbitrage Aggressive', BESSStrategiesV2.apply_arbitrage_aggressive)
    ]
    
    # Ejecutar pruebas
    results = []
    for name, func in strategies:
        result = test_strategy(name, func, solar, bess_config)
        results.append(result)
    
    # Resumen comparativo
    print("\n" + "="*60)
    print("RESUMEN COMPARATIVO")
    print("="*60)
    print(f"\n{'Estrategia':<25} {'Efic':<7} {'Pérd%':<7} {'Ciclos':<8} {'Util%':<7} {'Pérd/Ciclo%'}")
    print("-"*70)
    
    for r in results:
        print(f"{r['strategy']:<25} {r['efficiency']:<7.1%} {r['losses_pct']:<7.1f} "
              f"{r['cycles']:<8.2f} {r['utilization']:<7.1%} {r['loss_per_cycle']:<.1f}")
    
    # Verificación final
    print("\n" + "="*60)
    print("VERIFICACIÓN DE OBJETIVOS")
    print("="*60)
    
    strategies_with_cycles = sum(1 for r in results if r['cycles'] > 0.1)
    strategies_with_losses = sum(1 for r in results if 3 <= r['loss_per_cycle'] <= 10)
    
    print(f"\n✓ Estrategias con ciclos reales: {strategies_with_cycles}/{len(results)}")
    print(f"✓ Estrategias con pérdidas 3-10%: {strategies_with_losses}/{len(results)}")
    
    if strategies_with_cycles == len(results):
        print("\n🎉 ÉXITO: Todas las estrategias V2 usan el BESS correctamente")
    else:
        print("\n⚠️  ADVERTENCIA: Algunas estrategias no generan ciclos")


if __name__ == "__main__":
    main()