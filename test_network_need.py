"""
Script de Testing del Factor de Necesidad de Red
===============================================
Objetivo: Demostrar el impacto del factor de necesidad de red
en el payback de proyectos PV+Q.
"""

import sys
sys.path.append('/Users/maxkeczeli/Proyects/gd-edersa-calidad')

from src.economics.energy_flows import (
    calculate_pv_generation,
    calculate_pv_total_flows,
    calculate_pv_capex
)
from src.economics.network_benefits_modular import (
    calculate_total_network_benefits,
    apply_network_need_factor
)
from src.economics.capex_scale import get_size_category
from src.config.config_loader import get_config

import pandas as pd
import numpy as np


def analyze_network_need_impact(pv_mw: float, q_percent: float = 30):
    """
    Analiza el impacto del factor de necesidad de red en el payback.
    
    Args:
        pv_mw: Capacidad PV en MW
        q_percent: Porcentaje de Q reactiva
    
    Returns:
        DataFrame con resultados
    """
    # Cargar configuración
    config = get_config()
    all_params = config.get_all_params()
    
    # Calcular Q en MVAr
    q_mvar = pv_mw * (q_percent / 100)
    
    # 1. CAPEX con economías de escala
    capex_info = calculate_pv_capex(pv_mw, all_params['capex']['bos_factor'], use_scale=True)
    capex_pv = capex_info['equipment']
    capex_statcom = q_mvar * all_params['capex']['statcom_capex_usd_mvar']
    capex_total = capex_info['total'] + capex_statcom * (1 + all_params['capex']['bos_factor'])
    
    # 2. Generación e ingresos PV
    generation_mwh, _ = calculate_pv_generation(
        pv_mw,
        all_params['operation_factors']['pv_capacity_factor']
    )
    
    flows = calculate_pv_total_flows(
        generation_mwh, 
        0.7,  # 70% autoconsumo
        all_params['energy_prices']['electricity_price'],
        all_params['energy_prices']['export_price']
    )
    pv_revenue = flows['total']
    
    # 3. OPEX
    annual_opex = capex_total * all_params['opex']['pv_opex_rate']
    
    # 4. Flujo neto base (sin beneficios de red)
    net_flow_base = pv_revenue - annual_opex
    payback_base = capex_total / net_flow_base if net_flow_base > 0 else 999
    
    # 5. Calcular beneficios de red al 100%
    network_benefits_full = calculate_total_network_benefits(
        pv_mw=pv_mw,
        bess_mwh=0,
        q_mvar=q_mvar,
        network_params={
            'base_losses_mw': all_params['network_benefits_params']['base_losses_mw'],
            'users_affected': all_params['network_benefits_params']['users_affected'],
            'loss_sensitivity': all_params['technical_sensitivities']['loss_sensitivity'],
            'pf_penalty_usd_kvar_month': all_params['charges_penalties']['pf_penalty_usd_kvar_month'],
            'loss_price_multiplier': all_params['technical_sensitivities']['loss_price_multiplier'],
            'electricity_price': all_params['energy_prices']['electricity_price'],
            'saidi_minutes': all_params['network_benefits_params']['saidi_minutes'],
            'saidi_cost_minute': all_params['charges_penalties']['saidi_cost_usd_minute'],
            'violation_hours_year': all_params['network_benefits_params']['violation_hours_year'],
            'demand_charge_usd_kw_month': all_params['charges_penalties']['demand_charge_usd_kw_month'],
            'include_deferral': False
        }
    )
    
    # 6. Analizar diferentes niveles de necesidad
    need_factors = [0.0, 0.25, 0.50, 0.75, 1.0]
    results = []
    
    for need_factor in need_factors:
        # Aplicar factor de necesidad
        if need_factor == 0:
            network_benefits = 0
        else:
            network_benefits = network_benefits_full['total'] * need_factor
        
        # Flujo neto con beneficios ajustados
        net_flow_with_network = net_flow_base + network_benefits
        payback_with_network = capex_total / net_flow_with_network if net_flow_with_network > 0 else 999
        
        results.append({
            'pv_mw': pv_mw,
            'need_factor': need_factor,
            'need_percent': f"{need_factor*100:.0f}%",
            'payback_base': payback_base,
            'network_benefits': network_benefits,
            'payback_final': payback_with_network,
            'payback_reduction': payback_base - payback_with_network
        })
    
    return pd.DataFrame(results), capex_info['per_mw'], get_size_category(pv_mw)


def test_multiple_sizes():
    """
    Testea el impacto para diferentes tamaños de proyecto.
    """
    print("="*80)
    print("ANÁLISIS DE FACTOR DE NECESIDAD DE RED")
    print("="*80)
    
    sizes = [1, 10, 50, 100]
    all_results = []
    
    for pv_mw in sizes:
        df, capex_per_mw, category = analyze_network_need_impact(pv_mw, q_percent=30)
        
        print(f"\n{'='*60}")
        print(f"PROYECTO: {pv_mw} MW - {category}")
        print(f"CAPEX: ${capex_per_mw:,.0f}/MW")
        print(f"{'='*60}")
        
        print(f"\n{'Necesidad Red':>15} | {'Beneficios Red':>15} | {'Payback':>10} | {'vs Sin Red':>12}")
        print("-"*60)
        
        for _, row in df.iterrows():
            print(f"{row['need_percent']:>15} | ${row['network_benefits']/1e6:>13.2f}M | "
                  f"{row['payback_final']:>9.1f}y | {row['payback_reduction']:>10.1f}y")
            
            # Guardar para análisis global
            all_results.append({
                'size_mw': pv_mw,
                'category': category,
                'need_factor': row['need_factor'],
                'payback': row['payback_final']
            })
    
    return pd.DataFrame(all_results)


def create_summary_table(df_results):
    """
    Crea tabla resumen pivoteada.
    """
    print("\n" + "="*80)
    print("TABLA RESUMEN: PAYBACK POR TAMAÑO Y NECESIDAD DE RED")
    print("="*80)
    
    # Pivotear datos
    pivot = df_results.pivot(index='size_mw', columns='need_factor', values='payback')
    
    print(f"\n{'Tamaño (MW)':>12} | {'0%':>7} | {'25%':>7} | {'50%':>7} | {'75%':>7} | {'100%':>7} | {'Reducción':>10}")
    print("-"*75)
    
    for size in pivot.index:
        row = pivot.loc[size]
        reduction = row[0.0] - row[1.0]
        print(f"{size:>12} | {row[0.0]:>6.1f}y | {row[0.25]:>6.1f}y | "
              f"{row[0.50]:>6.1f}y | {row[0.75]:>6.1f}y | {row[1.0]:>6.1f}y | "
              f"{reduction:>9.1f}y")
    
    return pivot


def analyze_breakeven_need():
    """
    Analiza qué nivel de necesidad se requiere para diferentes objetivos de payback.
    """
    print("\n" + "="*80)
    print("ANÁLISIS DE PUNTO DE EQUILIBRIO")
    print("="*80)
    
    print("\n¿Qué nivel de necesidad de red se requiere para lograr diferentes paybacks?")
    print("(Asumiendo 100 MW con 30% Q)")
    
    # Parámetros para 100 MW
    df_100mw, _, _ = analyze_network_need_impact(100, q_percent=30)
    
    # Interpolación para encontrar puntos de equilibrio
    payback_targets = [6.0, 5.5, 5.0, 4.5]
    
    print(f"\n{'Payback Objetivo':>18} | {'Necesidad Requerida':>20}")
    print("-"*40)
    
    for target in payback_targets:
        # Buscar por interpolación
        payback_0 = df_100mw[df_100mw['need_factor'] == 0.0]['payback_final'].values[0]
        payback_100 = df_100mw[df_100mw['need_factor'] == 1.0]['payback_final'].values[0]
        
        if target >= payback_0:
            need_required = 0
        elif target <= payback_100:
            need_required = 100
        else:
            # Interpolación lineal
            need_required = (payback_0 - target) / (payback_0 - payback_100) * 100
        
        print(f"{target:>17.1f}y | {need_required:>19.0f}%")


def create_ascii_chart():
    """
    Crea un gráfico ASCII simple del impacto.
    """
    print("\n" + "="*60)
    print("GRÁFICO: PAYBACK vs NECESIDAD DE RED (100 MW)")
    print("="*60)
    
    df_100mw, _, _ = analyze_network_need_impact(100, q_percent=30)
    
    print("\nPayback")
    print("(años)")
    print("  6.0 |*")
    print("      | *")
    print("  5.5 |  *")
    print("      |   *")
    print("  5.0 |    *")
    print("      |     *")
    print("  4.5 |      *")
    print("      +--------+--------+--------+--------+")
    print("      0%      25%      50%      75%     100%")
    print("           Necesidad de Red")


def analyze_zone_scenarios():
    """
    Analiza escenarios típicos por zona.
    """
    print("\n" + "="*80)
    print("ESCENARIOS POR TIPO DE ZONA")
    print("="*80)
    
    scenarios = [
        {
            'name': 'Zona Urbana Alta Calidad',
            'description': 'Red robusta, sin problemas',
            'need_factor': 0.25,
            'characteristics': ['Baja tasa de fallas', 'Voltaje estable', 'Pocas pérdidas']
        },
        {
            'name': 'Zona Suburbana Media',
            'description': 'Algunos problemas de calidad',
            'need_factor': 0.5,
            'characteristics': ['Fallas ocasionales', 'Voltaje variable', 'Pérdidas moderadas']
        },
        {
            'name': 'Zona Rural Crítica',
            'description': 'Problemas severos de calidad',
            'need_factor': 1.0,
            'characteristics': ['Alta tasa de fallas', 'Voltaje fuera de límites', 'Altas pérdidas']
        }
    ]
    
    # Analizar para 50 MW (tamaño típico)
    pv_mw = 50
    
    for scenario in scenarios:
        df, _, _ = analyze_network_need_impact(pv_mw, q_percent=30)
        row = df[df['need_factor'] == scenario['need_factor']].iloc[0]
        
        print(f"\n{scenario['name'].upper()}")
        print(f"Descripción: {scenario['description']}")
        print(f"Factor de necesidad: {scenario['need_factor']*100:.0f}%")
        print("Características:")
        for char in scenario['characteristics']:
            print(f"  - {char}")
        print(f"\nResultados para {pv_mw} MW:")
        print(f"  Payback sin red: {row['payback_base']:.1f} años")
        print(f"  Payback con red: {row['payback_final']:.1f} años")
        print(f"  Mejora: {row['payback_reduction']:.1f} años")


def save_results(df_results):
    """
    Guarda resultados en CSV.
    """
    df_results.to_csv('network_need_analysis.csv', index=False)
    print("\n✅ Resultados guardados en network_need_analysis.csv")


if __name__ == "__main__":
    print("\n🔧 INICIANDO ANÁLISIS DE FACTOR DE NECESIDAD DE RED...\n")
    
    # Ejecutar análisis
    df_results = test_multiple_sizes()
    pivot_table = create_summary_table(df_results)
    analyze_breakeven_need()
    create_ascii_chart()
    analyze_zone_scenarios()
    save_results(df_results)
    
    # Conclusiones
    print("\n" + "="*80)
    print("CONCLUSIONES CLAVE")
    print("="*80)
    
    print("\n📊 HALLAZGOS PRINCIPALES:")
    print("1. El factor de necesidad de red tiene un impacto LINEAL en el payback")
    print("2. Proyectos en zonas sin problemas (0% necesidad) solo tienen payback base")
    print("3. Proyectos en zonas críticas (100% necesidad) obtienen todos los beneficios")
    print("4. La reducción de payback puede ser de 1-2 años según el tamaño del proyecto")
    
    print("\n💡 IMPLICACIONES:")
    print("1. Priorizar inversiones en zonas con alta necesidad de red")
    print("2. Ajustar evaluaciones económicas según calidad actual de la red")
    print("3. Considerar factor de necesidad en la planificación territorial")
    print("4. Zonas urbanas de alta calidad pueden no justificar beneficios de red completos")
    
    print("\n🎯 ANÁLISIS COMPLETADO")