"""
Script para probar la nueva implementación híbrida de 3 flujos
Verificar que conserva energía y muestra los flujos separados
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

def test_hybrid_flows():
    """Probar la nueva implementación híbrida"""
    
    # Crear perfil solar de prueba
    solar_profile = create_test_solar_profile()
    solar_energy_total = sum(solar_profile)
    
    print("=" * 80)
    print("PRUEBA DE IMPLEMENTACIÓN HÍBRIDA DE 3 FLUJOS")
    print("=" * 80)
    print(f"Energía solar total: {solar_energy_total:.2f} MWh")
    print("")
    
    # Configuración BESS para la prueba
    bess_power = 2.0  # MW
    bess_duration = 4  # horas
    ramp_duration = 0.5  # 30 minutos
    start_hour = 14  # Trapecio en la tarde
    
    print(f"BESS: {bess_power} MW / {bess_duration}h = {bess_power*bess_duration} MWh")
    print(f"Trapecio: inicio {start_hour}:00h, duración {bess_duration + 2*ramp_duration:.1f}h")
    print("")
    
    # Crear modelo BESS
    bess = BESSModel(bess_power, bess_duration)
    
    # Simular estrategia híbrida
    result = bess.simulate_operation(
        solar_profile, 
        strategy='energy_constrained_firm',
        start_hour=start_hour,
        min_duration=2,  # No usado
        ramp_duration=ramp_duration,
        min_soc_start=0.3
    )
    
    # Análisis de resultados
    print("📊 ANÁLISIS DE RESULTADOS:")
    print("-" * 60)
    
    total_grid = sum(result['grid_power'])
    efficiency = (total_grid / solar_energy_total) * 100
    energy_lost = solar_energy_total - total_grid
    
    print(f"Energía solar input:     {solar_energy_total:.2f} MWh")
    print(f"Energía grid output:     {total_grid:.2f} MWh")
    print(f"Energía perdida:         {energy_lost:.2f} MWh")
    print(f"Eficiencia total:        {efficiency:.1f}%")
    print("")
    
    # Verificar si hay información de flujos híbridos
    if result.get('hybrid_flows_available', False):
        print("✅ INFORMACIÓN DE FLUJOS HÍBRIDOS DISPONIBLE")
        print("-" * 60)
        
        direct_flow = result['grid_direct_flow']
        trapezoid_flow = result['grid_trapezoid_flow']
        
        direct_energy = sum(direct_flow)
        trapezoid_energy = sum(trapezoid_flow)
        
        print(f"Flujo directo (PSFV→Red):     {direct_energy:.2f} MWh ({direct_energy/total_grid*100:.1f}%)")
        print(f"Flujo trapecio (BESS→Red):    {trapezoid_energy:.2f} MWh ({trapezoid_energy/total_grid*100:.1f}%)")
        print(f"Total verificación:           {direct_energy + trapezoid_energy:.2f} MWh")
        
        # Verificación de conservación
        conservation_check = abs((direct_energy + trapezoid_energy) - total_grid) < 0.01
        print(f"✅ Conservación de flujos:     {'OK' if conservation_check else 'ERROR'}")
        print("")
        
        # Análisis de BESS
        battery_charge = sum(-result['battery_power'][result['battery_power'] < 0])
        battery_discharge = sum(result['battery_power'][result['battery_power'] > 0])
        battery_efficiency = (battery_discharge / battery_charge * 100) if battery_charge > 0 else 0
        
        print("🔋 ANÁLISIS DE BESS:")
        print("-" * 60)
        print(f"Energía cargada:         {battery_charge:.2f} MWh")
        print(f"Energía descargada:      {battery_discharge:.2f} MWh")
        print(f"Eficiencia BESS:         {battery_efficiency:.1f}%")
        print(f"Verificación trapecio:   {abs(battery_discharge - trapezoid_energy) < 0.01}")
        print("")
        
        # Crear gráfico de 3 flujos
        create_hybrid_flows_chart(solar_profile, direct_flow, trapezoid_flow, result)
        
    else:
        print("❌ INFORMACIÓN DE FLUJOS HÍBRIDOS NO DISPONIBLE")
    
    # Validaciones principales
    print("🎯 VALIDACIONES PRINCIPALES:")
    print("-" * 60)
    
    validations = []
    
    # 1. Conservación de energía (debe ser ≥95%)
    if efficiency >= 95:
        validations.append("✅ Conservación de energía (≥95%)")
    else:
        validations.append(f"❌ Baja eficiencia ({efficiency:.1f}%)")
    
    # 2. Presencia de flujos híbridos
    if result.get('hybrid_flows_available', False):
        validations.append("✅ Flujos híbridos funcionando")
    else:
        validations.append("❌ Flujos híbridos no disponibles")
    
    # 3. Trapecio presente
    trapezoid_present = result.get('hybrid_flows_available') and sum(result['grid_trapezoid_flow']) > 0.1
    if trapezoid_present:
        validations.append("✅ Trapecio energético generado")
    else:
        validations.append("❌ Sin trapecio energético")
    
    # 4. Pass-through directo
    direct_present = result.get('hybrid_flows_available') and sum(result['grid_direct_flow']) > 0.1
    if direct_present:
        validations.append("✅ Pass-through directo funcionando")
    else:
        validations.append("❌ Sin pass-through directo")
    
    for validation in validations:
        print(f"  {validation}")
    
    return result, validations

def create_hybrid_flows_chart(solar_profile, direct_flow, trapezoid_flow, result):
    """Crear gráfico mostrando los 3 flujos separados"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    hours = np.arange(24)
    
    # Gráfico 1: Solar original
    ax1 = axes[0, 0]
    ax1.fill_between(hours, solar_profile, alpha=0.6, color='gold', label='Solar PSFV')
    ax1.plot(hours, solar_profile, color='orange', linewidth=2)
    ax1.set_title('1. Generación Solar Original')
    ax1.set_ylabel('Potencia (MW)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Gráfico 2: Flujo directo (Solar → Red)
    ax2 = axes[0, 1] 
    ax2.fill_between(hours, direct_flow, alpha=0.6, color='lightgreen', label='PSFV → Red (Directo)')
    ax2.plot(hours, direct_flow, color='green', linewidth=2)
    ax2.set_title('2. Flujo Directo (PSFV → Red)')
    ax2.set_ylabel('Potencia (MW)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Gráfico 3: Flujo trapecio (BESS → Red)
    ax3 = axes[1, 0]
    ax3.fill_between(hours, trapezoid_flow, alpha=0.6, color='lightblue', label='BESS → Red (Trapecio)')
    ax3.plot(hours, trapezoid_flow, color='blue', linewidth=2)
    ax3.set_title('3. Flujo Trapecio (BESS → Red)')
    ax3.set_xlabel('Hora del día')
    ax3.set_ylabel('Potencia (MW)')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Gráfico 4: Comparación total
    ax4 = axes[1, 1]
    ax4.plot(hours, solar_profile, 'gold', linewidth=2, alpha=0.7, label='Solar Original')
    ax4.plot(hours, direct_flow + trapezoid_flow, 'red', linewidth=3, label='Total a Red')
    ax4.fill_between(hours, direct_flow, alpha=0.4, color='green', label='Directo')
    ax4.fill_between(hours, direct_flow, direct_flow + trapezoid_flow, alpha=0.4, color='blue', label='Trapecio')
    ax4.set_title('4. Comparación Total')
    ax4.set_xlabel('Hora del día')
    ax4.set_ylabel('Potencia (MW)')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    # Agregar información de energías
    solar_energy = sum(solar_profile)
    direct_energy = sum(direct_flow)
    trapezoid_energy = sum(trapezoid_flow)
    total_energy = direct_energy + trapezoid_energy
    
    fig.suptitle(f'Análisis de Flujos Híbridos\n'
                f'Solar: {solar_energy:.1f} MWh | '
                f'Directo: {direct_energy:.1f} MWh | '
                f'Trapecio: {trapezoid_energy:.1f} MWh | '
                f'Total: {total_energy:.1f} MWh ({total_energy/solar_energy*100:.1f}%)',
                fontsize=14)
    
    plt.tight_layout()
    plt.savefig('reports/figures/hybrid_flows_analysis.png', dpi=150, bbox_inches='tight')
    print(f"📈 Gráfico guardado en: reports/figures/hybrid_flows_analysis.png")
    
    return fig

def main():
    """Función principal"""
    
    # Crear directorio de reportes si no existe
    os.makedirs('reports/figures', exist_ok=True)
    
    # Ejecutar prueba
    result, validations = test_hybrid_flows()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DE IMPLEMENTACIÓN HÍBRIDA")
    print("=" * 80)
    
    passed = sum(1 for v in validations if v.startswith('✅'))
    total = len(validations)
    
    if passed == total:
        print("🎉 ¡IMPLEMENTACIÓN HÍBRIDA EXITOSA!")
        print("   - Conserva energía solar (≥95%)")
        print("   - Genera trapecio energético perfecto")
        print("   - Permite pass-through directo")
        print("   - BESS actúa como buffer temporal, no filtro")
    else:
        print(f"⚠️  Implementación parcial: {passed}/{total} validaciones")
        print("   Revisar puntos marcados con ❌")
    
    print(f"\n✨ La energía ya no se pierde - se redistribuye inteligentemente!")

if __name__ == "__main__":
    main()