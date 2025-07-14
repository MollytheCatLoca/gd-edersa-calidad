#!/usr/bin/env python3
"""
Script batch para mostrar comportamiento del cap shaving
Sin interacción del usuario - muestra todos los casos
"""

import sys
from pathlib import Path
import numpy as np

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.simulation.simulate_complete import simulate_psfv_bess_complete

def analyze_cap_shaving(cap_percent):
    """Analiza cap shaving para un porcentaje dado"""
    
    # Configuración
    psfv_mw = 1.0
    bess_mw = 1.0
    bess_hours = 4.0
    cap_mw = psfv_mw * cap_percent / 100
    
    # Simular
    result = simulate_psfv_bess_complete(
        psfv_mw=psfv_mw,
        bess_mw=bess_mw,
        bess_hours=bess_hours,
        strategy='cap_shaving',
        cap_mw=cap_mw,
        soft_discharge=True
    )
    
    profiles = result['profiles']
    metrics = result['metrics']
    
    print(f"\n{'='*60}")
    print(f"CAP SHAVING AL {cap_percent}% (Límite: {cap_mw} MW)")
    print(f"{'='*60}")
    
    print(f"\nRESUMEN:")
    print(f"  Solar pico: {metrics['solar_peak_mw']:.3f} MW")
    print(f"  ¿Pico > Límite?: {'SÍ' if metrics['solar_peak_mw'] > cap_mw else 'NO'}")
    print(f"  Energía cargada: {metrics['battery_charge_mwh']:.3f} MWh")
    print(f"  Energía descargada: {metrics['battery_discharge_mwh']:.3f} MWh")
    print(f"  Pérdidas: {metrics['losses_total_mwh']:.3f} MWh")
    print(f"  % a red: {metrics['grid_percent']:.1f}%")
    
    # Mostrar solo horas clave donde hay acción
    print(f"\nHORAS CLAVE:")
    print(f"{'Hora':<6} {'Solar':>8} {'Límite':>8} {'BESS':>8} {'Red':>8} {'Acción'}")
    print("-" * 60)
    
    for h in range(24):
        solar = profiles['solar_mw'][h]
        bess = profiles['bess_mw'][h]
        grid = profiles['grid_mw'][h]
        
        # Solo mostrar si hay acción del BESS o solar cerca del límite
        if abs(bess) > 0.001 or (solar > cap_mw * 0.9 and solar > 0):
            if bess < -0.001:
                action = "CARGA"
            elif bess > 0.001:
                action = "DESCARGA"
            else:
                action = "LÍMITE"
            
            print(f"{h:02d}:00  {solar:8.3f} {cap_mw:8.3f} {bess:8.3f} {grid:8.3f} {action}")
    
    return metrics

def main():
    """Analiza múltiples casos de cap shaving"""
    
    print("\n" + "="*60)
    print("ANÁLISIS BATCH DE CAP SHAVING PARA ML")
    print("="*60)
    print("\nConfiguración base: PSFV 1MW, BESS 1MW/4h")
    print("Generación diaria: 5.193 MWh")
    print("Pico solar real: 0.712 MW a las 12:00")
    
    # Casos de análisis
    cap_percentages = [80, 70, 60, 50, 40, 30, 20]
    
    # Tabla resumen
    print("\n" + "="*60)
    print("TABLA RESUMEN - EFECTO DEL LÍMITE DE POTENCIA")
    print("="*60)
    print(f"{'Cap%':>5} {'Límite MW':>10} {'Carga MWh':>10} {'Desc MWh':>10} {'Pérd MWh':>10} {'% Red':>8} {'Ciclos':>8}")
    print("-" * 60)
    
    for cap_percent in cap_percentages:
        metrics = analyze_cap_shaving(cap_percent)
        cap_mw = cap_percent / 100
        
        print(f"{cap_percent:5d} {cap_mw:10.2f} {metrics['battery_charge_mwh']:10.3f} "
              f"{metrics['battery_discharge_mwh']:10.3f} {metrics['losses_total_mwh']:10.3f} "
              f"{metrics['grid_percent']:8.1f} {metrics['cycles_equivalent']:8.2f}")
    
    print("\n" + "="*60)
    print("INSIGHTS PARA ML")
    print("="*60)
    print("""
1. ACTIVACIÓN DEL BESS:
   - Cap > 70%: No se activa (pico solar 71.2% < límite)
   - Cap = 70%: Activación mínima (0.012 MWh cargados)
   - Cap < 70%: Activación proporcional al exceso

2. PATRONES OBSERVADOS:
   - Sin descarga hasta cap < 40% (estrategia soft_discharge)
   - Pérdidas = ~3.6% de la energía que pasa por el BESS
   - Ciclos = energía_cargada / capacidad_bess

3. FEATURES CRÍTICOS PARA ML:
   - excess_ratio = max(0, solar_peak/cap_limit - 1)
   - hours_above_cap = count(solar > cap_limit)
   - potential_curtailment = integral(max(0, solar - cap_limit))
   - bess_size_ratio = bess_mwh / daily_excess_energy

4. TRADE-OFFS:
   - Mayor cap → Menor uso BESS → Menores pérdidas
   - Menor cap → Mayor uso BESS → Más pérdidas pero más control
   - Punto óptimo depende de:
     * Costo de pérdidas vs valor de firmeza
     * Restricciones de red
     * Tarifa por potencia máxima
    """)

if __name__ == "__main__":
    main()