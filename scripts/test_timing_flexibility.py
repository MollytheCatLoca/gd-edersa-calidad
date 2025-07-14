"""
Script para probar que el trapecio se mueve según la hora preferida
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

def test_timing_flexibility():
    """Probar que el trapecio se mueve según la hora preferida"""
    
    # Crear perfil solar de prueba
    solar_profile = create_test_solar_profile()
    
    print("=" * 80)
    print("PRUEBA DE FLEXIBILIDAD DE TIMING DEL TRAPECIO")
    print("=" * 80)
    
    # Configuración BESS fija para la prueba
    bess_power = 2.0  # MW
    bess_duration = 4  # horas
    ramp_duration = 0.5  # 30 minutos
    
    print(f"BESS: {bess_power} MW / {bess_duration}h")
    print(f"Ancho trapecio: {bess_duration + 2*ramp_duration:.1f} horas")
    print("")
    
    # Diferentes horas preferidas para probar
    start_hours_to_test = [8, 10, 12, 14, 16, 18]
    
    results = {}
    
    for start_hour in start_hours_to_test:
        print(f"\n{'='*60}")
        print(f"🕐 PROBANDO INICIO EN HORA: {start_hour}:00")
        print(f"{'='*60}")
        
        # Crear modelo BESS
        bess = BESSModel(bess_power, bess_duration)
        
        # Simular estrategia
        result = bess.simulate_operation(
            solar_profile, 
            strategy='energy_constrained_firm',
            start_hour=start_hour,
            min_duration=2,  # No usado
            ramp_duration=ramp_duration,
            min_soc_start=0.3
        )
        
        # Encontrar donde realmente empezó el trapecio
        delivery_hours = np.where(result['grid_power'] > 0.1)[0]
        if len(delivery_hours) > 0:
            actual_start = delivery_hours[0]
            actual_end = delivery_hours[-1]
            actual_width = actual_end - actual_start + 1
            max_power = max(result['grid_power'])
        else:
            actual_start = -1
            actual_end = -1
            actual_width = 0
            max_power = 0
        
        total_energy = sum(result['grid_power'])
        
        print(f"Hora preferida: {start_hour}:00")
        print(f"Inicio real: {actual_start}:00")
        print(f"Fin real: {actual_end}:00")
        print(f"Ancho real: {actual_width} horas")
        print(f"Potencia máxima: {max_power:.2f} MW")
        print(f"Energía entregada: {total_energy:.2f} MWh")
        
        # Verificar si se respetó la preferencia
        if actual_start == start_hour:
            print("✅ Timing respetado perfectamente")
        elif abs(actual_start - start_hour) <= 1:
            print("🟡 Timing aproximado (diferencia ≤ 1h)")
        else:
            print(f"❌ Timing no respetado (diferencia: {abs(actual_start - start_hour)}h)")
        
        # Guardar resultados
        results[start_hour] = {
            'grid_power': result['grid_power'],
            'battery_power': result['battery_power'],
            'actual_start': actual_start,
            'actual_end': actual_end,
            'max_power': max_power,
            'total_energy': total_energy
        }
    
    # Crear gráfico comparativo
    create_timing_comparison_chart(results, solar_profile, start_hours_to_test)
    
    return results

def create_timing_comparison_chart(results, solar_profile, start_hours):
    """Crear gráfico mostrando cómo se mueve el trapecio"""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    hours = np.arange(24)
    colors = ['red', 'orange', 'green', 'blue', 'purple', 'brown']
    
    for i, start_hour in enumerate(start_hours):
        if i >= 6:
            break
            
        ax = axes[i]
        result = results[start_hour]
        
        # Solar de fondo
        ax.plot(hours, solar_profile, 'gold', linewidth=2, alpha=0.5, label='Solar')
        
        # Trapecio
        ax.plot(hours, result['grid_power'], colors[i], linewidth=4, 
               label=f'Trapecio (inicio {start_hour}:00)')
        
        # Battery operation
        battery_pos = np.maximum(0, result['battery_power'])
        battery_neg = np.minimum(0, result['battery_power'])
        ax.bar(hours, battery_pos, alpha=0.4, color='green', width=0.8)
        ax.bar(hours, battery_neg, alpha=0.4, color='red', width=0.8)
        
        # Marcar inicio real
        if result['actual_start'] >= 0:
            ax.axvline(x=result['actual_start'], color='red', linestyle='--', 
                      alpha=0.8, label=f'Inicio real: {result["actual_start"]}:00')
        
        ax.set_title(f'Hora Preferida: {start_hour}:00\n'
                    f'Inicio Real: {result["actual_start"]}:00 | '
                    f'P_max: {result["max_power"]:.1f}MW')
        
        ax.set_xlabel('Hora del día')
        ax.set_ylabel('Potencia (MW)')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_xlim(0, 23)
        ax.set_ylim(-1, 4)
    
    plt.suptitle('Flexibilidad de Timing del Trapecio Energético\n'
                'BESS 2MW/4h - Ancho fijo 5h', fontsize=16)
    plt.tight_layout()
    plt.savefig('reports/figures/timing_flexibility.png', dpi=150, bbox_inches='tight')
    print(f"\n📈 Gráfico guardado en: reports/figures/timing_flexibility.png")
    
    return fig

def main():
    """Función principal"""
    
    # Crear directorio de reportes si no existe
    os.makedirs('reports/figures', exist_ok=True)
    
    # Ejecutar prueba
    results = test_timing_flexibility()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DE FLEXIBILIDAD DE TIMING")
    print("=" * 80)
    
    for start_hour, result in results.items():
        actual = result['actual_start']
        diff = abs(actual - start_hour) if actual >= 0 else 999
        
        if diff == 0:
            status = "✅ PERFECTO"
        elif diff <= 1:
            status = "🟡 APROXIMADO"
        else:
            status = "❌ DESVIADO"
        
        print(f"Hora {start_hour:2d}:00 → Real {actual:2d}:00 | Diff: {diff:2.0f}h | {status}")
    
    print("\n🎯 El trapecio debe moverse según la hora preferida!")

if __name__ == "__main__":
    main()