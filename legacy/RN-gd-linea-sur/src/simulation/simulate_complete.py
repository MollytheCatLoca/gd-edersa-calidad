#!/usr/bin/env python3
"""
Función unificada para simulación completa PSFV + BESS
Proporciona una interfaz simple para obtener todos los resultados de simulación
"""

from typing import Dict, Optional, Any
import numpy as np
import sys
from pathlib import Path

# Agregar rutas necesarias
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from dashboard.pages.utils.constants import (
    BESSTechnology, 
    BESSTopology,
    AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW,
    MONTHLY_SOLAR_GENERATION_MWH_PER_MW
)

def simulate_psfv_bess_complete(
    psfv_mw: float,
    bess_mw: float,
    bess_hours: float,
    strategy: str = 'cap_shaving',
    month: Optional[int] = None,
    technology: str = 'modern_lfp',
    verbose: bool = False,
    **strategy_params
) -> Dict[str, Any]:
    """
    Simula un sistema PSFV + BESS completo y devuelve todos los resultados.
    
    Args:
        psfv_mw: Potencia del PSFV en MW
        bess_mw: Potencia del BESS en MW
        bess_hours: Duración del BESS en horas
        strategy: Estrategia de operación ('cap_shaving', 'flat_day', 'night_shift', etc.)
        month: Mes para simulación (1-12). Si es None, usa promedio anual
        technology: Tecnología del BESS ('standard', 'modern_lfp', 'premium')
        verbose: Si mostrar información detallada
        **strategy_params: Parámetros específicos de la estrategia
            - cap_shaving: cap_mw, soft_discharge
            - flat_day: flat_mw, start_hour, end_hour
            - night_shift: charge_hours, discharge_hours
            - ramp_limit: ramp_limit_mw_per_hour
    
    Returns:
        Dict con todos los resultados:
            - config: Configuración del sistema
            - profiles: Perfiles horarios (solar, bess, grid, soc, losses)
            - metrics: Métricas agregadas
            - balance: Balance energético
            - validation: Validación del sistema
    """
    
    # 1. Generar perfil solar
    solar_profile = _generate_solar_profile(psfv_mw, month)
    
    # 2. Configurar tecnología BESS
    tech_map = {
        'standard': BESSTechnology.STANDARD,
        'modern_lfp': BESSTechnology.MODERN_LFP,
        'premium': BESSTechnology.PREMIUM
    }
    bess_tech = tech_map.get(technology, BESSTechnology.MODERN_LFP)
    
    # 3. Crear modelo BESS
    bess = BESSModel(
        power_mw=bess_mw,
        duration_hours=bess_hours,
        technology=bess_tech,
        topology=BESSTopology.PARALLEL_AC,
        verbose=verbose
    )
    
    # 4. Simular estrategia
    results = bess.simulate_strategy(
        solar_profile=solar_profile,
        strategy=strategy,
        **strategy_params
    )
    
    # 5. Calcular métricas adicionales
    solar_total = solar_profile.sum()
    grid_total = results['grid_power'].sum()
    losses_total = results['energy_losses'].sum()
    curtailed_total = results['solar_curtailed'].sum()
    
    battery_charge = -results['battery_power'][results['battery_power'] < 0].sum()
    battery_discharge = results['battery_power'][results['battery_power'] > 0].sum()
    
    # 6. Compilar resultados completos
    return {
        'config': {
            'psfv_mw': psfv_mw,
            'bess_mw': bess_mw,
            'bess_hours': bess_hours,
            'bess_mwh': bess_mw * bess_hours,
            'technology': technology,
            'strategy': strategy,
            'strategy_params': strategy_params,
            'month': month,
            'roundtrip_efficiency': bess.eff_roundtrip,
            'c_rate': bess_mw / (bess_mw * bess_hours) if bess_hours > 0 else 0
        },
        
        'profiles': {
            'hours': list(range(24)),
            'solar_mw': solar_profile.tolist(),
            'bess_mw': results['battery_power'].tolist(),
            'grid_mw': results['grid_power'].tolist(),
            'soc_pct': (results['soc'] * 100).tolist(),
            'losses_mwh': results['energy_losses'].tolist(),
            'curtailed_mw': results['solar_curtailed'].tolist()
        },
        
        'metrics': {
            # Energías
            'solar_total_mwh': float(solar_total),
            'grid_total_mwh': float(grid_total),
            'losses_total_mwh': float(losses_total),
            'curtailed_total_mwh': float(curtailed_total),
            
            # Porcentajes
            'grid_percent': float(grid_total / solar_total * 100) if solar_total > 0 else 0,
            'losses_percent': float(losses_total / solar_total * 100) if solar_total > 0 else 0,
            'curtailed_percent': float(curtailed_total / solar_total * 100) if solar_total > 0 else 0,
            
            # BESS
            'battery_charge_mwh': float(battery_charge),
            'battery_discharge_mwh': float(battery_discharge),
            'battery_throughput_mwh': float(battery_charge + battery_discharge),
            'realized_efficiency': float(battery_discharge / battery_charge * 100) if battery_charge > 0 else 0,
            'cycles_equivalent': float(results.get('total_cycles', 0)),
            'daily_cycles': float(results.get('daily_cycles', 0)),
            
            # Picos
            'solar_peak_mw': float(solar_profile.max()),
            'grid_peak_mw': float(results['grid_power'].max()),
            'bess_max_charge_mw': float(-results['battery_power'].min()) if results['battery_power'].min() < 0 else 0,
            'bess_max_discharge_mw': float(results['battery_power'].max()),
            
            # Factor de capacidad
            'capacity_factor': float(solar_total / (psfv_mw * 24) * 100) if psfv_mw > 0 else 0,
            
            # Utilización BESS
            'bess_utilization': float((results['soc'].max() - results['soc'].min()) * 100),
            'soc_min': float(results['soc'].min() * 100),
            'soc_max': float(results['soc'].max() * 100),
        },
        
        'balance': {
            'input_mwh': float(solar_total),
            'output_mwh': float(grid_total),
            'losses_mwh': float(losses_total),
            'curtailed_mwh': float(curtailed_total),
            'balance_error_mwh': float(solar_total - grid_total - losses_total - curtailed_total),
            'balance_ok': abs(solar_total - grid_total - losses_total - curtailed_total) < 0.001
        },
        
        'validation': results.get('validation', {}),
        
        'summary': _generate_summary(solar_total, grid_total, losses_total, curtailed_total, 
                                    battery_charge, battery_discharge, results)
    }

def _generate_solar_profile(power_mw: float, month: Optional[int] = None) -> np.ndarray:
    """Genera perfil solar diario"""
    if month is None:
        # Usar promedio anual
        daily_energy = AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW / 30
    else:
        # Usar mes específico
        monthly_energy = MONTHLY_SOLAR_GENERATION_MWH_PER_MW.get(month, 150.0)
        days = 30  # Simplificación
        daily_energy = monthly_energy / days
    
    # Perfil horario típico
    hours = np.arange(24)
    daylight = (6 <= hours) & (hours <= 18)
    
    profile = np.zeros(24)
    x = (hours - 12) / 6
    profile[daylight] = np.exp(-2 * x[daylight]**2)
    
    # Normalizar y escalar
    if profile.sum() > 0:
        profile = profile * daily_energy / profile.sum()
    
    return profile * power_mw

def _generate_summary(solar: float, grid: float, losses: float, 
                     curtailed: float, charge: float, discharge: float,
                     results: Dict) -> str:
    """Genera resumen textual de resultados"""
    summary = []
    summary.append(f"Generación solar: {solar:.2f} MWh/día")
    summary.append(f"Energía a red: {grid:.2f} MWh ({grid/solar*100:.1f}%)")
    
    if losses > 0.001:
        summary.append(f"Pérdidas BESS: {losses:.2f} MWh ({losses/solar*100:.1f}%)")
    
    if curtailed > 0.001:
        summary.append(f"Curtailment: {curtailed:.2f} MWh ({curtailed/solar*100:.1f}%)")
    
    if charge > 0.001:
        summary.append(f"BESS cargó {charge:.2f} MWh, descargó {discharge:.2f} MWh")
        summary.append(f"Ciclos equivalentes: {results.get('total_cycles', 0):.2f}")
    
    return " | ".join(summary)


# Función de conveniencia para pruebas rápidas
def quick_test():
    """Prueba rápida de la función"""
    result = simulate_psfv_bess_complete(
        psfv_mw=1.0,
        bess_mw=1.0,
        bess_hours=4.0,
        strategy='cap_shaving',
        cap_mw=0.7,  # Límite 70%
        verbose=True
    )
    
    print("=== RESUMEN DE SIMULACIÓN ===")
    print(result['summary'])
    print(f"\nBalance energético OK: {result['balance']['balance_ok']}")
    
    return result


if __name__ == "__main__":
    quick_test()