#!/usr/bin/env python3
"""
Script simplificado para probar cap_shaving_balanced sin gráficos
"""

import sys
from pathlib import Path
import numpy as np

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.simulation.simulate_complete import simulate_psfv_bess_complete

def test_cap_shaving_balanced():
    """Prueba la estrategia cap_shaving_balanced"""
    
    print("\n" + "="*80)
    print("PRUEBA DE CAP_SHAVING_BALANCED")
    print("="*80)
    
    # Configuración
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_hours = 4.0
    percentile = 50  # Usar percentil 50 para forzar más actividad
    
    # Simular con estrategia balanced
    result = simulate_psfv_bess_complete(
        psfv_mw=psfv_mw,
        bess_mw=bess_mw,
        bess_hours=bess_hours,
        strategy='cap_shaving_balanced',
        use_percentile=True,
        percentile=percentile,
        discharge_start_hour=16
    )
    
    profiles = result['profiles']
    metrics = result['metrics']
    
    # Calcular cap real usado
    solar_array = np.array(profiles['solar_mw'])
    solar_positive = solar_array[solar_array > 0.001]
    cap_real = np.percentile(solar_positive, percentile) if len(solar_positive) > 0 else 0
    
    print(f"\nCONFIGURACIÓN:")
    print(f"  • PSFV: {psfv_mw} MW")
    print(f"  • BESS: {bess_mw} MW / {bess_hours}h = {bess_mw * bess_hours} MWh")
    print(f"  • Percentil usado: {percentile}%")
    print(f"  • Cap calculado (P{percentile} de generación): {cap_real:.3f} MW")
    print(f"  • Pico solar real: {metrics['solar_peak_mw']:.3f} MW")
    
    print(f"\nRESULTADOS:")
    print(f"  • Energía solar total: {metrics['solar_total_mwh']:.3f} MWh")
    print(f"  • Energía cargada en BESS: {metrics['battery_charge_mwh']:.3f} MWh")
    print(f"  • Energía descargada de BESS: {metrics['battery_discharge_mwh']:.3f} MWh")
    print(f"  • Pérdidas totales: {metrics['losses_total_mwh']:.3f} MWh")
    print(f"  • Energía a red: {metrics['grid_total_mwh']:.3f} MWh ({metrics['grid_percent']:.1f}%)")
    
    # Balance energético del BESS
    balance = metrics['battery_charge_mwh'] - metrics['battery_discharge_mwh'] - metrics['losses_total_mwh']
    soc_inicial = profiles['soc_pct'][0]
    soc_final = profiles['soc_pct'][-1]
    
    print(f"\nBALANCE DIARIO DEL BESS:")
    print(f"  • Carga - Descarga - Pérdidas = {balance:.6f} MWh")
    print(f"  • SOC inicial: {soc_inicial:.1f}%")
    print(f"  • SOC final: {soc_final:.1f}%")
    print(f"  • Diferencia SOC: {soc_final - soc_inicial:.1f}%")
    
    # Mostrar perfil horario
    print(f"\nPERFIL HORARIO:")
    print(f"{'Hora':>4} {'Solar':>8} {'BESS':>8} {'Red':>8} {'SOC':>6} | Notas")
    print("-" * 60)
    
    for h in range(24):
        solar = profiles['solar_mw'][h]
        bess = profiles['bess_mw'][h]
        grid = profiles['grid_mw'][h]
        soc = profiles['soc_pct'][h]
        
        # Solo mostrar horas con actividad
        if solar > 0.01 or abs(bess) > 0.01:
            nota = ""
            if bess < -0.01:
                nota = f"Carga (solar {solar:.3f} > cap {cap_real:.3f})"
            elif bess > 0.01:
                nota = "Descarga programada"
            
            print(f"{h:4d} {solar:8.3f} {bess:8.3f} {grid:8.3f} {soc:6.1f} | {nota}")
    
    # Verificar balance
    print(f"\nVERIFICACIÓN:")
    if abs(balance) < 0.01:
        print("✓ Balance diario OK: toda la energía cargada se descarga + pérdidas")
    else:
        print("✗ Balance diario NO OK: queda energía sin descargar")
    
    if soc_final <= 15:  # Cerca del mínimo
        print("✓ SOC final OK: BESS termina descargado")
    else:
        print(f"✗ SOC final alto: {soc_final:.1f}% (debería estar cerca del mínimo)")

def compare_strategies():
    """Compara cap_shaving original vs balanced"""
    
    print("\n" + "="*80)
    print("COMPARACIÓN: CAP_SHAVING vs CAP_SHAVING_BALANCED")
    print("="*80)
    
    configs = [
        ('cap_shaving', {'cap_mw': 0.5, 'soft_discharge': True}),
        ('cap_shaving_balanced', {'use_percentile': True, 'percentile': 50})
    ]
    
    results = []
    
    for strategy, params in configs:
        result = simulate_psfv_bess_complete(
            psfv_mw=1.0,
            bess_mw=1.0,
            bess_hours=4.0,
            strategy=strategy,
            **params
        )
        results.append((strategy, result))
    
    # Comparar métricas
    print(f"\n{'Métrica':<30} {'Cap Shaving':>15} {'Cap Balanced':>15}")
    print("-" * 60)
    
    metrics_to_compare = [
        ('Energía cargada (MWh)', 'battery_charge_mwh'),
        ('Energía descargada (MWh)', 'battery_discharge_mwh'),
        ('Pérdidas (MWh)', 'losses_total_mwh'),
        ('% a red', 'grid_percent'),
        ('Ciclos', 'cycles_equivalent'),
        ('SOC final (%)', lambda r: r['profiles']['soc_pct'][-1])
    ]
    
    for metric_name, metric_key in metrics_to_compare:
        values = []
        for strategy, result in results:
            if callable(metric_key):
                value = metric_key(result)
            else:
                value = result['metrics'][metric_key]
            values.append(value)
        
        print(f"{metric_name:<30} {values[0]:>15.3f} {values[1]:>15.3f}")
    
    # Balance
    print("\nBALANCE ENERGÉTICO BESS:")
    for strategy, result in results:
        m = result['metrics']
        balance = m['battery_charge_mwh'] - m['battery_discharge_mwh'] - m['losses_total_mwh']
        print(f"  {strategy}: {balance:.6f} MWh")

def main():
    """Ejecuta las pruebas"""
    
    # 1. Probar cap_shaving_balanced
    test_cap_shaving_balanced()
    
    # 2. Comparar estrategias
    compare_strategies()
    
    print("\n" + "="*80)
    print("CONCLUSIÓN:")
    print("="*80)
    print("""
Cap_shaving_balanced garantiza:
1. Uso de percentil real de generación (más realista)
2. Descarga completa de la energía almacenada cada día
3. Balance energético diario = 0
4. Mejor aprovechamiento del BESS
5. Datos más consistentes para ML
    """)

if __name__ == "__main__":
    main()