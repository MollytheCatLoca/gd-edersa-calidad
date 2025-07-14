"""
Script para verificar que la energía se conserva correctamente en los flujos híbridos
y que la suma de flujos nunca excede la generación solar
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.battery.bess_model import BESSModel
import matplotlib.pyplot as plt

def create_test_solar_profile():
    """Crear perfil solar de prueba para 24 horas"""
    hours = np.arange(24)
    solar_profile = np.zeros(24)
    
    for h in hours:
        if 6 <= h <= 18:  # Solo durante el día
            # Función gaussiana centrada en mediodía
            solar_profile[h] = 3.0 * np.exp(-0.5 * ((h - 12) / 3) ** 2)
    
    return solar_profile

def test_energy_conservation():
    """Probar que la energía se conserva correctamente"""
    
    # Crear perfil solar de prueba
    solar_profile = create_test_solar_profile()
    solar_energy_total = sum(solar_profile)
    
    print("=" * 80)
    print("PRUEBA DE CONSERVACIÓN DE ENERGÍA EN FLUJOS HÍBRIDOS")
    print("=" * 80)
    print(f"Energía solar total: {solar_energy_total:.2f} MWh")
    print("")
    
    # Configuración BESS para la prueba
    bess_power = 2.0  # MW
    bess_duration = 4  # horas
    ramp_duration = 0.5  # 30 minutos
    start_hour = 14  # Trapecio en la tarde (cuando aún hay sol)
    
    print(f"BESS: {bess_power} MW / {bess_duration}h = {bess_power*bess_duration} MWh")
    print(f"Trapecio preferido: inicio {start_hour}:00h")
    print("")
    
    # Crear modelo BESS
    bess = BESSModel(bess_power, bess_duration)
    
    # Simular estrategia híbrida
    result = bess.simulate_operation(
        solar_profile, 
        strategy='energy_constrained_firm',
        start_hour=start_hour,
        min_duration=2,
        ramp_duration=ramp_duration,
        min_soc_start=0.3
    )
    
    # Verificar flujos híbridos
    if result.get('hybrid_flows_available', False):
        direct_flow = result['grid_direct_flow']
        trapezoid_flow = result['grid_trapezoid_flow']
        
        print("📊 ANÁLISIS HORA POR HORA:")
        print("-" * 80)
        print(f"{'Hora':>4} | {'Solar':>6} | {'Directo':>7} | {'Trapecio':>8} | {'Total':>6} | {'Diff':>6} | {'Check':>6}")
        print("-" * 80)
        
        violations = []
        
        for h in range(24):
            solar_h = solar_profile[h]
            direct_h = direct_flow[h]
            trap_h = trapezoid_flow[h]
            total_h = direct_h + trap_h
            diff_h = total_h - solar_h
            
            # Verificar que no excedamos el solar
            check = "✅" if abs(diff_h) < 0.01 else "❌"
            if abs(diff_h) >= 0.01:
                violations.append((h, solar_h, total_h, diff_h))
            
            if solar_h > 0 or total_h > 0:  # Solo mostrar horas con actividad
                print(f"{h:4d} | {solar_h:6.2f} | {direct_h:7.2f} | {trap_h:8.2f} | {total_h:6.2f} | {diff_h:+6.2f} | {check:>6}")
        
        print("-" * 80)
        
        # Resumen de energías
        energy_solar = sum(solar_profile)
        energy_direct = sum(direct_flow)
        energy_trap = sum(trapezoid_flow)
        energy_total = energy_direct + energy_trap
        
        print("\n📊 RESUMEN DE ENERGÍAS:")
        print("-" * 60)
        print(f"Energía solar original:     {energy_solar:.2f} MWh")
        print(f"Flujo directo (PSFV→Red):   {energy_direct:.2f} MWh ({energy_direct/energy_solar*100:.1f}%)")
        print(f"Flujo trapecio (BESS→Red):  {energy_trap:.2f} MWh ({energy_trap/energy_solar*100:.1f}%)")
        print(f"Total entregado a red:      {energy_total:.2f} MWh ({energy_total/energy_solar*100:.1f}%)")
        print(f"Pérdidas BESS (5%):         {energy_solar - energy_total:.2f} MWh")
        print("")
        
        # Verificaciones
        print("🎯 VERIFICACIONES:")
        print("-" * 60)
        
        # 1. Conservación de energía
        efficiency = energy_total / energy_solar * 100
        conservation_ok = 94 <= efficiency <= 96
        print(f"1. Conservación de energía: {efficiency:.1f}% {'✅' if conservation_ok else '❌'}")
        
        # 2. No exceder solar en ninguna hora
        no_violations = len(violations) == 0
        print(f"2. Flujos ≤ Solar en todas las horas: {'✅' if no_violations else '❌'}")
        
        if violations:
            print("\n   ⚠️  VIOLACIONES DETECTADAS:")
            for h, solar, total, diff in violations:
                print(f"   Hora {h}: Solar={solar:.2f}, Total={total:.2f}, Exceso={diff:.2f}")
        
        # 3. BESS balance
        battery_power = result['battery_power']
        print(f"\nDEBUG: battery_power length = {len(battery_power)}")
        print(f"DEBUG: First 24 values: {battery_power[:24] if len(battery_power) >= 24 else battery_power}")
        battery_charge = sum(-bp for bp in battery_power if bp < 0)
        battery_discharge = sum(bp for bp in battery_power if bp > 0)
        bess_efficiency = (battery_discharge / battery_charge * 100) if battery_charge > 0 else 0
        
        print(f"3. Eficiencia BESS: {bess_efficiency:.1f}% {'✅' if 94 <= bess_efficiency <= 96 else '❌'}")
        print(f"   Carga total: {battery_charge:.2f} MWh")
        print(f"   Descarga total: {battery_discharge:.2f} MWh")
        
        # Análisis detallado de energía
        print("\n📊 BALANCE ENERGÉTICO DETALLADO:")
        print("-" * 60)
        energy_charged_hours = [i for i, bp in enumerate(battery_power) if bp < 0]
        if energy_charged_hours:
            print(f"Horas de carga: {min(energy_charged_hours)}-{max(energy_charged_hours)}")
            print(f"Energía cargada: {battery_charge:.2f} MWh")
            print(f"Energía esperada después de pérdidas: {battery_charge * 0.95:.2f} MWh")
            print(f"Energía real descargada: {battery_discharge:.2f} MWh")
            print(f"Diferencia: {battery_discharge - battery_charge * 0.95:.2f} MWh")
        
        # Crear gráfico de verificación
        create_verification_chart(solar_profile, direct_flow, trapezoid_flow, violations)
        
        # Resultado final
        print("\n" + "=" * 80)
        if conservation_ok and no_violations and 94 <= bess_efficiency <= 96:
            print("✅ ¡TODAS LAS VERIFICACIONES PASARON!")
            print("   La energía se conserva correctamente y los flujos nunca exceden el solar.")
        else:
            print("❌ HAY PROBLEMAS EN LA CONSERVACIÓN DE ENERGÍA")
            print("   Revisar la implementación de los flujos híbridos.")
        
    else:
        print("❌ Los flujos híbridos no están disponibles")

def create_verification_chart(solar_profile, direct_flow, trapezoid_flow, violations):
    """Crear gráfico de verificación con énfasis en violaciones"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
    hours = np.arange(24)
    
    # Gráfico principal
    ax1.fill_between(hours, direct_flow, alpha=0.6, color='lightgreen', label='Directo (PSFV→Red)')
    ax1.fill_between(hours, direct_flow, 
                     [direct_flow[i] + trapezoid_flow[i] for i in range(24)],
                     alpha=0.6, color='lightblue', label='Trapecio (BESS→Red)')
    ax1.plot(hours, solar_profile, 'gold', linewidth=3, label='Solar Original', linestyle='--')
    
    # Marcar violaciones
    if violations:
        violation_hours = [v[0] for v in violations]
        violation_values = [v[2] for v in violations]
        ax1.scatter(violation_hours, violation_values, color='red', s=100, 
                   marker='x', linewidth=3, label='Violaciones', zorder=5)
    
    ax1.set_ylabel('Potencia (MW)')
    ax1.set_title('Verificación de Conservación de Energía')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 23)
    
    # Gráfico de diferencias
    total_flow = [direct_flow[i] + trapezoid_flow[i] for i in range(24)]
    differences = [total_flow[i] - solar_profile[i] for i in range(24)]
    
    colors = ['green' if abs(d) < 0.01 else 'red' for d in differences]
    ax2.bar(hours, differences, color=colors, alpha=0.7)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_xlabel('Hora del día')
    ax2.set_ylabel('Diferencia (MW)')
    ax2.set_title('Diferencia: (Directo + Trapecio) - Solar')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 23)
    ax2.set_ylim(min(-0.5, min(differences)*1.2), max(0.5, max(differences)*1.2))
    
    plt.tight_layout()
    plt.savefig('reports/figures/energy_conservation_check.png', dpi=150, bbox_inches='tight')
    print(f"\n📈 Gráfico guardado en: reports/figures/energy_conservation_check.png")

def main():
    """Función principal"""
    
    # Crear directorio de reportes si no existe
    os.makedirs('reports/figures', exist_ok=True)
    
    # Ejecutar prueba
    test_energy_conservation()

if __name__ == "__main__":
    main()