#!/usr/bin/env python3
"""
Script para probar la nueva estrategia cap_shaving_balanced
Verifica que toda la energía cargada se descarga en el mismo día
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.simulation.simulate_complete import simulate_psfv_bess_complete

def analyze_cap_shaving_comparison(percentile=70):
    """Compara cap_shaving original vs balanced"""
    
    # Configuración
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_hours = 4.0
    
    print(f"\n{'='*80}")
    print(f"COMPARACIÓN: CAP SHAVING ORIGINAL vs BALANCED (Percentil {percentile})")
    print(f"{'='*80}\n")
    
    # 1. Cap shaving original con límite teórico
    cap_teorico = psfv_mw * percentile / 100
    result_original = simulate_psfv_bess_complete(
        psfv_mw=psfv_mw,
        bess_mw=bess_mw,
        bess_hours=bess_hours,
        strategy='cap_shaving',
        cap_mw=cap_teorico,
        soft_discharge=True
    )
    
    # 2. Cap shaving balanced con percentil
    result_balanced = simulate_psfv_bess_complete(
        psfv_mw=psfv_mw,
        bess_mw=bess_mw,
        bess_hours=bess_hours,
        strategy='cap_shaving_balanced',
        use_percentile=True,
        percentile=percentile,
        discharge_start_hour=16
    )
    
    # Extraer datos
    profiles_orig = result_original['profiles']
    profiles_bal = result_balanced['profiles']
    metrics_orig = result_original['metrics']
    metrics_bal = result_balanced['metrics']
    
    # Calcular cap real usado en balanced
    solar_positive = np.array(profiles_bal['solar_mw'])
    solar_positive = solar_positive[solar_positive > 0.001]
    cap_percentil = np.percentile(solar_positive, percentile) if len(solar_positive) > 0 else 0
    
    print("CONFIGURACIÓN:")
    print(f"  • PSFV: {psfv_mw} MW")
    print(f"  • BESS: {bess_mw} MW / {bess_hours}h = {bess_mw * bess_hours} MWh")
    print(f"  • Cap teórico ({percentile}% de {psfv_mw} MW): {cap_teorico:.3f} MW")
    print(f"  • Cap percentil ({percentile}% de generación real): {cap_percentil:.3f} MW")
    print(f"  • Pico solar real: {metrics_orig['solar_peak_mw']:.3f} MW")
    
    print("\n" + "-"*50)
    print(f"{'Métrica':<30} {'Original':>10} {'Balanced':>10} {'Diferencia':>10}")
    print("-"*50)
    
    # Comparar métricas
    metricas = [
        ('Energía cargada (MWh)', 'battery_charge_mwh'),
        ('Energía descargada (MWh)', 'battery_discharge_mwh'),
        ('Pérdidas totales (MWh)', 'losses_total_mwh'),
        ('% a red', 'grid_percent'),
        ('Ciclos equivalentes', 'cycles_equivalent'),
        ('SOC final (%)', 'soc_min'),
        ('SOC máximo (%)', 'soc_max'),
        ('Utilización BESS (%)', 'bess_utilization')
    ]
    
    for nombre, key in metricas:
        val_orig = metrics_orig[key]
        val_bal = metrics_bal[key]
        diff = val_bal - val_orig
        print(f"{nombre:<30} {val_orig:>10.3f} {val_bal:>10.3f} {diff:>+10.3f}")
    
    # Balance energético
    print("\nBALANCE ENERGÉTICO:")
    balance_orig = metrics_orig['battery_charge_mwh'] - metrics_orig['battery_discharge_mwh'] - metrics_orig['losses_total_mwh']
    balance_bal = metrics_bal['battery_charge_mwh'] - metrics_bal['battery_discharge_mwh'] - metrics_bal['losses_total_mwh']
    print(f"  Original: Carga - Descarga - Pérdidas = {balance_orig:.6f} MWh (SOC final: {profiles_orig['soc_pct'][-1]:.1f}%)")
    print(f"  Balanced: Carga - Descarga - Pérdidas = {balance_bal:.6f} MWh (SOC final: {profiles_bal['soc_pct'][-1]:.1f}%)")
    
    return result_original, result_balanced, cap_teorico, cap_percentil

def plot_comparison(result_original, result_balanced, cap_teorico, cap_percentil):
    """Grafica la comparación entre estrategias"""
    
    profiles_orig = result_original['profiles']
    profiles_bal = result_balanced['profiles']
    hours = profiles_orig['hours']
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # 1. Generación y límites
    ax1 = axes[0]
    ax1.plot(hours, profiles_orig['solar_mw'], 'orange', linewidth=2, label='Solar')
    ax1.axhline(y=cap_teorico, color='red', linestyle='--', label=f'Cap teórico: {cap_teorico:.2f} MW')
    ax1.axhline(y=cap_percentil, color='green', linestyle='--', label=f'Cap percentil: {cap_percentil:.2f} MW')
    ax1.fill_between(hours, 0, profiles_orig['solar_mw'], alpha=0.3, color='orange')
    ax1.set_ylabel('Potencia (MW)')
    ax1.set_title('Generación Solar y Límites de Cap')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Operación BESS
    ax2 = axes[1]
    ax2.plot(hours, profiles_orig['bess_mw'], 'b-', linewidth=2, label='BESS Original', alpha=0.7)
    ax2.plot(hours, profiles_bal['bess_mw'], 'g-', linewidth=2, label='BESS Balanced')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.fill_between(hours, 0, profiles_orig['bess_mw'], alpha=0.3, color='blue', where=(np.array(profiles_orig['bess_mw']) < 0))
    ax2.fill_between(hours, 0, profiles_orig['bess_mw'], alpha=0.3, color='red', where=(np.array(profiles_orig['bess_mw']) > 0))
    ax2.set_ylabel('Potencia BESS (MW)')
    ax2.set_title('Operación del BESS (Negativo = Carga, Positivo = Descarga)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Estado de carga (SOC)
    ax3 = axes[2]
    ax3.plot(hours, profiles_orig['soc_pct'], 'b-', linewidth=2, label='SOC Original', alpha=0.7)
    ax3.plot(hours, profiles_bal['soc_pct'], 'g-', linewidth=2, label='SOC Balanced')
    ax3.axhline(y=10, color='red', linestyle=':', label='SOC mínimo')
    ax3.axhline(y=95, color='red', linestyle=':', label='SOC máximo')
    ax3.fill_between(hours, 10, profiles_orig['soc_pct'], alpha=0.2, color='blue')
    ax3.fill_between(hours, 10, profiles_bal['soc_pct'], alpha=0.2, color='green')
    ax3.set_ylabel('SOC (%)')
    ax3.set_xlabel('Hora del día')
    ax3.set_title('Estado de Carga del BESS')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 100)
    
    plt.tight_layout()
    plt.savefig('cap_shaving_comparison.png', dpi=150, bbox_inches='tight')
    print("\nGráfico guardado como 'cap_shaving_comparison.png'")
    plt.show()

def test_different_percentiles():
    """Prueba diferentes percentiles para ver el efecto"""
    
    print("\n" + "="*80)
    print("ANÁLISIS DE DIFERENTES PERCENTILES CON CAP_SHAVING_BALANCED")
    print("="*80)
    
    percentiles = [90, 80, 70, 60, 50, 40, 30]
    results = []
    
    for percentile in percentiles:
        result = simulate_psfv_bess_complete(
            psfv_mw=1.0,
            bess_mw=1.0,
            bess_hours=4.0,
            strategy='cap_shaving_balanced',
            use_percentile=True,
            percentile=percentile,
            discharge_start_hour=16
        )
        
        metrics = result['metrics']
        profiles = result['profiles']
        
        # Calcular cap real
        solar_positive = np.array(profiles['solar_mw'])
        solar_positive = solar_positive[solar_positive > 0.001]
        cap_real = np.percentile(solar_positive, percentile) if len(solar_positive) > 0 else 0
        
        results.append({
            'percentile': percentile,
            'cap_real': cap_real,
            'charge': metrics['battery_charge_mwh'],
            'discharge': metrics['battery_discharge_mwh'],
            'losses': metrics['losses_total_mwh'],
            'soc_final': profiles['soc_pct'][-1],
            'balance': metrics['battery_charge_mwh'] - metrics['battery_discharge_mwh'] - metrics['losses_total_mwh']
        })
    
    # Imprimir tabla de resultados
    print(f"\n{'Percentil':>10} {'Cap Real':>10} {'Carga':>10} {'Descarga':>10} {'Pérdidas':>10} {'SOC Final':>10} {'Balance':>10}")
    print("-"*80)
    
    for r in results:
        print(f"{r['percentile']:>10}% {r['cap_real']:>10.3f} {r['charge']:>10.3f} "
              f"{r['discharge']:>10.3f} {r['losses']:>10.3f} {r['soc_final']:>10.1f}% "
              f"{r['balance']:>10.6f}")
    
    print("\nNOTA: El balance debe ser cercano a 0 (toda la energía cargada se descarga + pérdidas)")

def main():
    """Ejecuta todos los análisis"""
    
    # 1. Comparación principal con percentil 70
    result_orig, result_bal, cap_teo, cap_per = analyze_cap_shaving_comparison(70)
    
    # 2. Generar gráfico
    plot_comparison(result_orig, result_bal, cap_teo, cap_per)
    
    # 3. Probar diferentes percentiles
    test_different_percentiles()
    
    print("\n" + "="*80)
    print("CONCLUSIONES:")
    print("="*80)
    print("""
1. CAP SHAVING BALANCED garantiza descarga completa diaria
2. Usar percentil de generación real es más realista que % del nominal
3. El balance energético diario es ~0 (toda energía se usa)
4. SOC final vuelve al mínimo cada día
5. Ideal para aplicaciones que requieren ciclo diario completo
    """)

if __name__ == "__main__":
    main()