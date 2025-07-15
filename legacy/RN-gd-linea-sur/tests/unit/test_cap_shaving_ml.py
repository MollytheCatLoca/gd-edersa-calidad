#!/usr/bin/env python3
"""
Script para demostrar el comportamiento del cap shaving
Muestra exactamente qué verá el ML y el racional detrás
"""

import sys
from pathlib import Path
import numpy as np

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.simulation.simulate_complete import simulate_psfv_bess_complete

def explain_cap_shaving(cap_percent):
    """Explica el cap shaving para un porcentaje dado"""
    
    print(f"\n{'='*70}")
    print(f"CAP SHAVING AL {cap_percent}% - ¿QUÉ HACE EL BESS?")
    print(f"{'='*70}\n")
    
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
        soft_discharge=True  # Permite descarga suave cuando solar < 50% del cap
    )
    
    profiles = result['profiles']
    metrics = result['metrics']
    
    print(f"CONFIGURACIÓN:")
    print(f"  • PSFV: {psfv_mw} MW (pico máximo: {metrics['solar_peak_mw']:.3f} MW)")
    print(f"  • BESS: {bess_mw} MW / {bess_hours}h = {bess_mw * bess_hours} MWh")
    print(f"  • Límite de potencia: {cap_mw} MW ({cap_percent}% del PSFV nominal)")
    print(f"  • Estrategia: Cap Shaving con descarga suave")
    
    print(f"\nLÓGICA DE OPERACIÓN:")
    print(f"  1. Si Solar > {cap_mw} MW → BESS carga el exceso")
    print(f"  2. Si Solar < {cap_mw * 0.5:.2f} MW y SOC > 30% → BESS descarga suavemente")
    print(f"  3. Objetivo: Mantener salida a red ≤ {cap_mw} MW")
    
    print(f"\nRESULTADO ENERGÉTICO:")
    print(f"  • Generación solar: {metrics['solar_total_mwh']:.2f} MWh/día")
    print(f"  • Energía a red: {metrics['grid_total_mwh']:.2f} MWh ({metrics['grid_percent']:.1f}%)")
    print(f"  • Pérdidas BESS: {metrics['losses_total_mwh']:.3f} MWh ({metrics['losses_percent']:.1f}%)")
    print(f"  • Curtailment: {metrics['curtailed_total_mwh']:.3f} MWh ({metrics['curtailed_percent']:.1f}%)")
    
    print(f"\nOPERACIÓN DEL BESS:")
    print(f"  • Energía cargada: {metrics['battery_charge_mwh']:.3f} MWh")
    print(f"  • Energía descargada: {metrics['battery_discharge_mwh']:.3f} MWh")
    print(f"  • Ciclos equivalentes: {metrics['cycles_equivalent']:.2f}")
    print(f"  • Utilización: {metrics['bess_utilization']:.1f}% (SOC: {metrics['soc_min']:.0f}%-{metrics['soc_max']:.0f}%)")
    
    # Análisis hora por hora
    print(f"\nANÁLISIS HORA POR HORA:")
    print(f"{'Hora':<6} {'Solar':>8} {'BESS':>8} {'Red':>8} {'SOC':>6} | Acción")
    print("-" * 70)
    
    for h in range(24):
        solar = profiles['solar_mw'][h]
        bess = profiles['bess_mw'][h]
        grid = profiles['grid_mw'][h]
        soc = profiles['soc_pct'][h]
        
        # Determinar acción
        if solar > 0.01:  # Hay sol
            if bess < -0.01:  # BESS carga
                action = f"CARGA: Solar ({solar:.3f}) > Cap ({cap_mw}) → BESS carga {-bess:.3f} MW"
            elif bess > 0.01:  # BESS descarga
                action = f"DESCARGA: Solar ({solar:.3f}) < {cap_mw*0.5:.2f} → BESS aporta {bess:.3f} MW"
            else:
                if solar > cap_mw:
                    action = f"Sin acción aunque Solar > Cap (BESS lleno o límite alcanzado)"
                else:
                    action = f"Sin acción: Solar ({solar:.3f}) dentro de límites"
        else:
            if bess > 0.01:
                action = f"DESCARGA NOCTURNA: BESS aporta {bess:.3f} MW"
            else:
                action = "Sin generación ni BESS"
        
        if solar > 0.01 or bess != 0:  # Solo mostrar horas relevantes
            print(f"{h:02d}:00  {solar:8.3f} {bess:8.3f} {grid:8.3f} {soc:6.1f}% | {action}")
    
    # Features para ML
    print(f"\nFEATURES CLAVE PARA ML:")
    print(f"  • cap_ratio = {cap_percent/100:.2f} (límite como fracción del PSFV)")
    print(f"  • solar_peak_ratio = {metrics['solar_peak_mw']/psfv_mw:.3f} (pico real vs nominal)")
    print(f"  • exceso_total = {metrics['battery_charge_mwh']:.3f} MWh (cuánto se cargó)")
    print(f"  • horas_sobre_cap = {sum(1 for s in profiles['solar_mw'] if s > cap_mw)} horas")
    print(f"  • max_exceso_instantaneo = {max(0, max(s - cap_mw for s in profiles['solar_mw'])):.3f} MW")
    print(f"  • eficiencia_realizada = {metrics['realized_efficiency']:.1f}%")
    
    # Racional para ML
    print(f"\nRACIONAL PARA ML:")
    if metrics['battery_charge_mwh'] < 0.01:
        print(f"  → No hubo carga porque el pico solar ({metrics['solar_peak_mw']:.3f} MW) <= cap ({cap_mw} MW)")
        print(f"  → El BESS no se necesita con este límite")
    elif metrics['battery_discharge_mwh'] < 0.01:
        print(f"  → Solo hubo carga, no descarga")
        print(f"  → Posibles razones:")
        print(f"    • Solar nunca bajó de {cap_mw*0.5:.2f} MW durante el día")
        print(f"    • No hay demanda nocturna en este modelo simplificado")
    else:
        print(f"  → Operación completa: carga durante picos, descarga cuando baja el sol")
        print(f"  → Eficiencia round-trip: {metrics['realized_efficiency']:.1f}%")
    
    return result

def main():
    """Ejecuta análisis para diferentes niveles de cap"""
    print("\n" + "="*70)
    print("ANÁLISIS DE CAP SHAVING PARA ML")
    print("¿Cómo responde el BESS a diferentes límites de potencia?")
    print("="*70)
    
    # Casos de interés
    cap_percentages = [80, 60, 40, 20]
    
    for cap_percent in cap_percentages:
        explain_cap_shaving(cap_percent)
        input("\nPresiona ENTER para continuar con el siguiente caso...")
    
    print("\n" + "="*70)
    print("CONCLUSIONES PARA ML:")
    print("="*70)
    print("""
1. El BESS solo se activa si: solar_peak > cap_limit
2. La energía cargada = integral(max(0, solar - cap_limit))
3. La descarga depende de la estrategia 'soft_discharge'
4. Las pérdidas son proporcionales al throughput
5. El ML debe aprender:
   - Relación entre cap_ratio y utilización
   - Cómo afecta el tamaño del BESS
   - Trade-off entre curtailment y pérdidas
   - Valor económico de diferentes configuraciones
    """)

if __name__ == "__main__":
    main()