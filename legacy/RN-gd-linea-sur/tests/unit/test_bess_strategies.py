#!/usr/bin/env python3
"""
Script para probar diferentes configuraciones de BESS y estrategias
Muestra el comportamiento del sistema bajo distintos escenarios
"""

import sys
from pathlib import Path
import numpy as np
from tabulate import tabulate

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.simulation.simulate_complete import simulate_psfv_bess_complete

def print_section_header(title):
    """Imprime un header de sección"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def print_config(config):
    """Imprime configuración del sistema"""
    print(f"PSFV: {config['psfv_mw']} MW | BESS: {config['bess_mw']} MW / {config['bess_hours']}h = {config['bess_mwh']:.1f} MWh")
    print(f"Tecnología: {config['technology']} (η={config['roundtrip_efficiency']:.1%}) | C-rate: {config['c_rate']:.2f}")
    print(f"Estrategia: {config['strategy']} | Parámetros: {config['strategy_params']}")

def print_energy_balance(metrics, balance):
    """Imprime balance energético"""
    data = [
        ["Generación Solar", f"{metrics['solar_total_mwh']:.3f}", "100.0%", "Input total"],
        ["Energía a Red", f"{metrics['grid_total_mwh']:.3f}", f"{metrics['grid_percent']:.1f}%", "Output útil"],
        ["Pérdidas BESS", f"{metrics['losses_total_mwh']:.3f}", f"{metrics['losses_percent']:.1f}%", "Pérdidas round-trip"],
        ["Curtailment", f"{metrics['curtailed_total_mwh']:.3f}", f"{metrics['curtailed_percent']:.1f}%", "Energía rechazada"],
        ["Balance Error", f"{abs(balance['balance_error_mwh']):.6f}", "-", "OK" if balance['balance_ok'] else "ERROR"]
    ]
    print(tabulate(data, headers=["Concepto", "MWh/día", "%", "Nota"], tablefmt="grid"))

def print_bess_operation(metrics):
    """Imprime operación del BESS"""
    data = [
        ["Energía Cargada", f"{metrics['battery_charge_mwh']:.3f} MWh"],
        ["Energía Descargada", f"{metrics['battery_discharge_mwh']:.3f} MWh"],
        ["Throughput Total", f"{metrics['battery_throughput_mwh']:.3f} MWh"],
        ["Eficiencia Realizada", f"{metrics['realized_efficiency']:.1f}%"],
        ["Ciclos Equivalentes", f"{metrics['cycles_equivalent']:.2f}"],
        ["Utilización BESS", f"{metrics['bess_utilization']:.1f}%"],
        ["SOC Rango", f"{metrics['soc_min']:.0f}% - {metrics['soc_max']:.0f}%"]
    ]
    print(tabulate(data, headers=["Métrica", "Valor"], tablefmt="simple"))

def print_hourly_profile(profiles, show_hours=None):
    """Imprime perfil horario"""
    hours = profiles['hours']
    if show_hours:
        indices = [h for h in show_hours if h < len(hours)]
    else:
        # Mostrar horas clave: amanecer, mediodía, atardecer
        indices = [6, 8, 10, 12, 14, 16, 18, 20]
    
    data = []
    for i in indices:
        if i < len(hours):
            data.append([
                f"{hours[i]:02d}:00",
                f"{profiles['solar_mw'][i]:.3f}",
                f"{profiles['bess_mw'][i]:+.3f}",
                f"{profiles['grid_mw'][i]:.3f}",
                f"{profiles['soc_pct'][i]:.0f}%",
                f"{profiles['losses_mwh'][i]*1000:.1f}",
                f"{profiles['curtailed_mw'][i]:.3f}"
            ])
    
    print(tabulate(data, headers=["Hora", "Solar MW", "BESS MW", "Red MW", "SOC", "Pérd kWh", "Curt MW"], 
                   tablefmt="simple", floatfmt=".3f"))

def analyze_cap_shaving_ratios():
    """Analiza diferentes niveles de cap shaving"""
    print_section_header("ANÁLISIS CAP SHAVING - DIFERENTES LÍMITES")
    
    # Configuración base
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_hours = 4.0
    
    # Diferentes límites de cap shaving
    cap_percentages = [90, 80, 70, 60, 50, 40, 30]
    
    results_summary = []
    
    for cap_percent in cap_percentages:
        cap_mw = psfv_mw * cap_percent / 100
        
        result = simulate_psfv_bess_complete(
            psfv_mw=psfv_mw,
            bess_mw=bess_mw,
            bess_hours=bess_hours,
            strategy='cap_shaving',
            cap_mw=cap_mw,
            soft_discharge=True
        )
        
        metrics = result['metrics']
        
        results_summary.append([
            f"{cap_percent}%",
            f"{cap_mw:.2f}",
            f"{metrics['battery_charge_mwh']:.3f}",
            f"{metrics['battery_discharge_mwh']:.3f}",
            f"{metrics['losses_total_mwh']:.3f}",
            f"{metrics['curtailed_total_mwh']:.3f}",
            f"{metrics['grid_percent']:.1f}%",
            f"{metrics['cycles_equivalent']:.2f}"
        ])
    
    print("\nResumen comparativo:")
    print(tabulate(results_summary, 
                   headers=["Cap", "MW límite", "Carga", "Descarga", "Pérdidas", "Curtail", "% a Red", "Ciclos"],
                   tablefmt="grid"))

def analyze_different_strategies():
    """Compara diferentes estrategias"""
    print_section_header("COMPARACIÓN DE ESTRATEGIAS")
    
    # Configuración base
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_hours = 4.0
    
    strategies = [
        ('cap_shaving', {'cap_mw': 0.5}),  # 50% cap
        ('flat_day', {'flat_mw': 0.4, 'start_hour': 8, 'end_hour': 18}),
        ('night_shift', {'charge_hours': list(range(10, 16)), 'discharge_hours': list(range(18, 22))}),
        ('solar_smoothing', {'window_size': 3}),
        ('time_shift_aggressive', {}),
    ]
    
    for strategy_name, params in strategies:
        print(f"\n--- Estrategia: {strategy_name} ---")
        
        result = simulate_psfv_bess_complete(
            psfv_mw=psfv_mw,
            bess_mw=bess_mw,
            bess_hours=bess_hours,
            strategy=strategy_name,
            **params
        )
        
        print_config(result['config'])
        print("\nBalance Energético:")
        print_energy_balance(result['metrics'], result['balance'])
        print("\nOperación BESS:")
        print_bess_operation(result['metrics'])
        print("\nPerfil Horario (horas clave):")
        print_hourly_profile(result['profiles'])

def analyze_bess_sizes():
    """Analiza diferentes tamaños de BESS"""
    print_section_header("ANÁLISIS DE TAMAÑO DE BESS")
    
    psfv_mw = 1.0
    cap_mw = 0.5  # Límite 50%
    
    # Diferentes configuraciones de BESS
    bess_configs = [
        (0.5, 2),   # 0.5 MW / 2h = 1 MWh
        (1.0, 2),   # 1.0 MW / 2h = 2 MWh
        (1.0, 4),   # 1.0 MW / 4h = 4 MWh
        (2.0, 4),   # 2.0 MW / 4h = 8 MWh
        (0.5, 8),   # 0.5 MW / 8h = 4 MWh (bajo C-rate)
    ]
    
    results_summary = []
    
    for bess_mw, bess_hours in bess_configs:
        result = simulate_psfv_bess_complete(
            psfv_mw=psfv_mw,
            bess_mw=bess_mw,
            bess_hours=bess_hours,
            strategy='cap_shaving',
            cap_mw=cap_mw
        )
        
        metrics = result['metrics']
        config = result['config']
        
        results_summary.append([
            f"{bess_mw} MW / {bess_hours}h",
            f"{config['bess_mwh']:.1f}",
            f"{config['c_rate']:.2f}",
            f"{metrics['battery_charge_mwh']:.3f}",
            f"{metrics['battery_discharge_mwh']:.3f}",
            f"{metrics['curtailed_total_mwh']:.3f}",
            f"{metrics['grid_percent']:.1f}%",
            f"{metrics['bess_utilization']:.1f}%"
        ])
    
    print(f"\nComparación para PSFV {psfv_mw} MW con Cap Shaving al 50% ({cap_mw} MW):")
    print(tabulate(results_summary,
                   headers=["Config BESS", "MWh", "C-rate", "Carga", "Descarga", "Curtail", "% Red", "Util%"],
                   tablefmt="grid"))

def analyze_extreme_case():
    """Analiza un caso extremo para ver el comportamiento del BESS"""
    print_section_header("CASO EXTREMO - CAP SHAVING AL 30%")
    
    result = simulate_psfv_bess_complete(
        psfv_mw=1.0,
        bess_mw=1.0,
        bess_hours=4.0,
        strategy='cap_shaving',
        cap_mw=0.3,  # Solo 30% del pico
        verbose=True
    )
    
    print_config(result['config'])
    print("\nBalance Energético:")
    print_energy_balance(result['metrics'], result['balance'])
    print("\nOperación BESS:")
    print_bess_operation(result['metrics'])
    print("\nPerfil Horario Completo (6-20h):")
    print_hourly_profile(result['profiles'], show_hours=range(6, 21))
    
    # Análisis adicional
    profiles = result['profiles']
    print("\nAnálisis detallado:")
    print(f"- Horas con carga BESS: {sum(1 for p in profiles['bess_mw'] if p < -0.001)}")
    print(f"- Horas con descarga BESS: {sum(1 for p in profiles['bess_mw'] if p > 0.001)}")
    print(f"- Horas con curtailment: {sum(1 for p in profiles['curtailed_mw'] if p > 0.001)}")
    print(f"- Máxima carga instantánea: {-min(profiles['bess_mw']):.3f} MW")
    print(f"- Máxima descarga instantánea: {max(profiles['bess_mw']):.3f} MW")

def main():
    """Ejecuta todos los análisis"""
    print("\n" + "="*80)
    print(" ANÁLISIS COMPLETO DE ESTRATEGIAS BESS ".center(80, "="))
    print("="*80)
    
    # 1. Análisis de diferentes límites de cap shaving
    analyze_cap_shaving_ratios()
    
    # 2. Comparación de estrategias
    analyze_different_strategies()
    
    # 3. Análisis de tamaños de BESS
    analyze_bess_sizes()
    
    # 4. Caso extremo
    analyze_extreme_case()
    
    print("\n" + "="*80)
    print(" FIN DEL ANÁLISIS ".center(80, "="))
    print("="*80)

if __name__ == "__main__":
    main()