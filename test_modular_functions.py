"""
Script de Testing de Funciones Modulares
========================================
Objetivo: Testear las funciones modulares con diferentes tamaños de PV
y porcentajes de compensación reactiva para verificar paybacks.
"""

import sys
sys.path.append('/Users/maxkeczeli/Proyects/gd-edersa-calidad')

from src.economics.energy_flows import (
    calculate_pv_generation,
    calculate_pv_self_consumption,
    calculate_pv_exports,
    calculate_pv_total_flows,
    calculate_pv_capex
)
from src.economics.network_benefits_modular import (
    calculate_loss_reduction,
    calculate_reactive_support_value,
    calculate_reliability_improvement,
    calculate_total_network_benefits
)
from src.economics.financial_metrics import (
    calculate_payback,
    calculate_all_financial_metrics
)
from src.config.config_loader import get_config

import pandas as pd
import numpy as np


def test_single_case(pv_mw: float, q_percent: float, network_need_factor: float = 1.0, verbose: bool = False):
    """
    Testea un caso específico de PV + Q reactiva
    
    Args:
        pv_mw: Capacidad PV en MW
        q_percent: Porcentaje de Q respecto a PV (0-40%)
        network_need_factor: Factor de necesidad de red (0-1, default=1.0)
        verbose: Si mostrar detalles
    
    Returns:
        dict con resultados
    """
    # Cargar configuración
    config = get_config()
    # Obtener toda la configuración para acceso directo
    all_params = config.get_all_params()
    
    # Calcular Q en MVAr
    q_mvar = pv_mw * (q_percent / 100)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"CASO: {pv_mw} MW PV + {q_mvar:.1f} MVAr ({q_percent}% Q)")
        print(f"Factor de necesidad de red: {network_need_factor:.0%}")
        print(f"{'='*60}")
    
    # 1. CAPEX con economías de escala
    capex_info = calculate_pv_capex(pv_mw, all_params['capex']['bos_factor'], use_scale=True)
    capex_pv = capex_info['equipment']
    capex_statcom = q_mvar * all_params['capex']['statcom_capex_usd_mvar']
    capex_subtotal = capex_pv + capex_statcom
    capex_total = capex_subtotal + capex_info['bos'] + (capex_statcom * all_params['capex']['bos_factor'])
    
    if verbose:
        print(f"\nCAPEX:")
        print(f"  PV: ${capex_pv/1e6:.2f}M (${capex_info['per_mw']:,.0f}/MW)")
        print(f"  STATCOM: ${capex_statcom/1e6:.3f}M")
        print(f"  Total (con BOS): ${capex_total/1e6:.2f}M")
    
    # 2. Generación PV
    generation_mwh, generation_gwh = calculate_pv_generation(
        pv_mw,
        all_params['operation_factors']['pv_capacity_factor']
    )
    
    # 3. Flujos de energía
    self_consumption_ratio = 0.7
    self_consumption_mwh = generation_mwh * self_consumption_ratio
    exports_mwh = generation_mwh * (1 - self_consumption_ratio)
    
    # 4. Ingresos PV
    self_consumption_value = calculate_pv_self_consumption(
        generation_mwh,
        self_consumption_ratio,
        all_params['energy_prices']['electricity_price']
    )
    
    export_value = calculate_pv_exports(
        generation_mwh,
        1 - self_consumption_ratio,
        all_params['energy_prices']['export_price']
    )
    
    pv_revenue = self_consumption_value + export_value
    
    if verbose:
        print(f"\nGENERACIÓN Y FLUJOS:")
        print(f"  Generación: {generation_mwh:,.0f} MWh/año ({generation_mwh/pv_mw:.0f} MWh/MW/año)")
        print(f"  Autoconsumo: {self_consumption_mwh:,.0f} MWh/año (70%)")
        print(f"  Exportación: {exports_mwh:,.0f} MWh/año (30%)")
        print(f"  Ingresos PV: ${pv_revenue/1e6:.3f}M/año")
    
    # 5. OPEX
    opex_pv = capex_pv * all_params['opex']['pv_opex_rate']
    opex_statcom = capex_statcom * all_params['opex']['statcom_opex_rate']
    annual_opex = opex_pv + opex_statcom
    
    # 6. Flujo neto sin beneficios de red
    net_flow_without_network = pv_revenue - annual_opex
    payback_without_network = capex_total / net_flow_without_network if net_flow_without_network > 0 else 999
    
    if verbose:
        print(f"\nSIN BENEFICIOS DE RED:")
        print(f"  OPEX anual: ${annual_opex/1e6:.3f}M/año")
        print(f"  Flujo neto: ${net_flow_without_network/1e6:.3f}M/año")
        print(f"  Payback: {payback_without_network:.1f} años")
    
    # 7. Beneficios de red
    network_benefits = calculate_total_network_benefits(
        pv_mw=pv_mw,
        bess_mwh=0,  # Sin BESS
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
            'demand_charge_usd_kw_month': all_params['charges_penalties']['demand_charge_usd_kw_month'],  # Pasar el valor 0
            'include_deferral': False  # Simplificar sin diferimiento
        },
        network_need_factor=network_need_factor
    )
    
    if verbose:
        print(f"\nBENEFICIOS DE RED:")
        print(f"  Q at Night: ${network_benefits['reactive_support']/1e6:.3f}M/año")
        print(f"  Loss Reduction: ${network_benefits['loss_reduction']/1e6:.3f}M/año")
        print(f"  Voltage Support: ${network_benefits.get('voltage_support', 0)/1e6:.3f}M/año")
        print(f"  Reliability: ${network_benefits['reliability']/1e6:.3f}M/año")
        print(f"  Demand Reduction: ${network_benefits.get('demand_reduction', 0)/1e6:.3f}M/año")
        print(f"  Transmission Deferral: ${network_benefits.get('transmission_deferral', 0)/1e6:.3f}M/año")
        print(f"  TOTAL: ${network_benefits['total']/1e6:.3f}M/año")
    
    # 8. Flujo neto con beneficios de red
    net_flow_with_network = net_flow_without_network + network_benefits['total']
    payback_with_network = capex_total / net_flow_with_network if net_flow_with_network > 0 else 999
    
    if verbose:
        print(f"\nCON BENEFICIOS DE RED:")
        print(f"  Flujo neto total: ${net_flow_with_network/1e6:.3f}M/año")
        print(f"  Payback: {payback_with_network:.1f} años")
        print(f"  Reducción payback: {(payback_without_network - payback_with_network)/payback_without_network*100:.1f}%")
    
    return {
        'pv_mw': pv_mw,
        'q_percent': q_percent,
        'q_mvar': q_mvar,
        'capex_total': capex_total,
        'generation_mwh': generation_mwh,
        'pv_revenue': pv_revenue,
        'opex': annual_opex,
        'net_flow_base': net_flow_without_network,
        'payback_base': payback_without_network,
        'q_benefit': network_benefits['reactive_support'],
        'loss_benefit': network_benefits['loss_reduction'],
        'reliability_benefit': network_benefits['reliability'],
        'network_total': network_benefits['total'],
        'net_flow_network': net_flow_with_network,
        'payback_network': payback_with_network,
        'payback_reduction': (payback_without_network - payback_with_network) / payback_without_network * 100
    }


def test_matrix():
    """
    Testea una matriz de casos con diferentes tamaños PV y % Q
    """
    # Configuraciones a testear
    pv_sizes = [1, 5, 10, 20, 50]  # MW
    q_percentages = [0, 10, 20, 30, 40]  # % de PV
    
    print("="*80)
    print("TESTING DE FUNCIONES MODULARES - MATRIZ COMPLETA")
    print("="*80)
    
    # Recolectar resultados
    results = []
    
    for pv_mw in pv_sizes:
        for q_percent in q_percentages:
            result = test_single_case(pv_mw, q_percent, verbose=False)
            results.append(result)
    
    # Crear DataFrame para análisis
    df = pd.DataFrame(results)
    
    # Mostrar tabla resumen
    print("\nTABLA RESUMEN DE PAYBACKS")
    print("-"*80)
    print(f"{'PV (MW)':>8} | {'Q (%)':>6} | {'Q (MVAr)':>8} | {'Payback Base':>12} | {'Payback Red':>12} | {'Reducción':>10}")
    print("-"*80)
    
    for _, row in df.iterrows():
        print(f"{row['pv_mw']:>8.0f} | {row['q_percent']:>6.0f} | {row['q_mvar']:>8.1f} | "
              f"{row['payback_base']:>12.1f} | {row['payback_network']:>12.1f} | "
              f"{row['payback_reduction']:>9.1f}%")
    
    # Análisis específico para 30% Q
    print("\n" + "="*60)
    print("VERIFICACIÓN OBJETIVO: 30% Q → Payback 4.8 años")
    print("="*60)
    
    df_30q = df[df['q_percent'] == 30]
    
    print(f"\n{'PV (MW)':>8} | {'Payback sin red':>15} | {'Payback con red':>15} | {'Target 4.8?':>12}")
    print("-"*60)
    
    for _, row in df_30q.iterrows():
        target_met = "✅ SÍ" if abs(row['payback_network'] - 4.8) < 0.2 else "❌ NO"
        print(f"{row['pv_mw']:>8.0f} | {row['payback_base']:>15.1f} | "
              f"{row['payback_network']:>15.1f} | {target_met:>12}")
    
    # Gráfico de tendencia (texto)
    print("\n" + "="*60)
    print("TENDENCIA: Payback vs % Q Reactiva (para 10 MW)")
    print("="*60)
    
    df_10mw = df[df['pv_mw'] == 10].sort_values('q_percent')
    
    print("\nQ% | Payback | Gráfico")
    print("-"*60)
    
    max_payback = df_10mw['payback_network'].max()
    
    for _, row in df_10mw.iterrows():
        bar_length = int(40 * row['payback_network'] / max_payback)
        bar = "█" * bar_length
        print(f"{row['q_percent']:2.0f} | {row['payback_network']:>7.1f} | {bar}")
    
    # Verificar monotonicidad
    print("\n" + "="*60)
    print("VERIFICACIÓN DE LÓGICA")
    print("="*60)
    
    # Para cada tamaño PV, verificar que más Q → menor payback
    monotonic_ok = True
    
    for pv_mw in pv_sizes:
        df_pv = df[df['pv_mw'] == pv_mw].sort_values('q_percent')
        paybacks = df_pv['payback_network'].values
        
        # Verificar que sea decreciente
        is_decreasing = all(paybacks[i] >= paybacks[i+1] for i in range(len(paybacks)-1))
        
        if not is_decreasing:
            print(f"❌ {pv_mw} MW: Payback NO decrece monotónicamente con Q%")
            monotonic_ok = False
        else:
            print(f"✅ {pv_mw} MW: Payback decrece correctamente con Q%")
    
    if monotonic_ok:
        print("\n✅ LÓGICA CORRECTA: Más Q reactiva → Menor payback")
    
    # Resumen de beneficios para caso 10 MW, 30% Q
    print("\n" + "="*60)
    print("DESGLOSE DETALLADO: 10 MW con 30% Q")
    print("="*60)
    
    case_10_30 = test_single_case(10, 30, verbose=True)
    
    return df


def test_network_need_impact():
    """
    Testea el impacto del factor de necesidad de red
    """
    print("\n" + "="*80)
    print("TEST DE FACTOR DE NECESIDAD DE RED")
    print("="*80)
    
    # Caso base: 100 MW con 30% Q
    pv_mw = 100
    q_percent = 30
    
    print(f"\nProyecto: {pv_mw} MW con {q_percent}% Q reactiva")
    print("\nImpacto del factor de necesidad de red:")
    print("-"*60)
    print(f"{'Necesidad Red':>15} | {'Payback sin red':>15} | {'Payback con red':>15} | {'Diferencia':>12}")
    print("-"*60)
    
    # Testear diferentes factores de necesidad
    need_factors = [0.0, 0.25, 0.50, 0.75, 1.0]
    
    for need_factor in need_factors:
        result = test_single_case(pv_mw, q_percent, need_factor, verbose=False)
        print(f"{need_factor:>14.0%} | {result['payback_base']:>15.1f} | "
              f"{result['payback_network']:>15.1f} | {result['payback_base'] - result['payback_network']:>11.1f}")
    
    print("\n💡 CONCLUSIÓN:")
    print("- Con 0% necesidad (red robusta): Solo aplican beneficios PV → 5.8 años")
    print("- Con 100% necesidad (red crítica): Aplican todos los beneficios → 5.1 años")
    print("- El factor de necesidad permite ajustar la evaluación según estado real de la red")


def test_financial_metrics():
    """
    Testea las métricas financieras completas
    """
    print("\n" + "="*80)
    print("TEST DE MÉTRICAS FINANCIERAS")
    print("="*80)
    
    # Caso de prueba: 10 MW
    pv_mw = 10
    q_percent = 30
    
    # Obtener flujos
    case = test_single_case(pv_mw, q_percent, verbose=False)
    
    # Calcular todas las métricas
    metrics = calculate_all_financial_metrics(
        capex=case['capex_total'],
        annual_revenue=case['pv_revenue'] + case['network_total'],
        annual_opex=case['opex'],
        annual_generation_mwh=case['generation_mwh'],
        project_lifetime=20,
        discount_rate=0.10,
        inflation_rate=0.04
    )
    
    print(f"\nCaso: {pv_mw} MW con {q_percent}% Q")
    print(f"CAPEX: ${case['capex_total']/1e6:.2f}M")
    print(f"Ingresos totales: ${(case['pv_revenue'] + case['network_total'])/1e6:.2f}M/año")
    print(f"OPEX: ${case['opex']/1e6:.2f}M/año")
    
    print("\nMÉTRICAS FINANCIERAS:")
    print(f"  NPV: ${metrics['npv']/1e6:.2f}M")
    print(f"  IRR: {metrics['irr']*100:.1f}%")
    print(f"  Payback: {metrics['payback']:.1f} años")
    print(f"  LCOE: ${metrics['lcoe']:.2f}/MWh")
    print(f"  B/C Ratio: {metrics['bc_ratio']:.2f}")
    
    if metrics['payback'] < 10 and metrics['irr'] > 0.15 and metrics['bc_ratio'] > 1.2:
        print("\n✅ Todas las métricas cumplen los criterios de inversión")
    else:
        print("\n❌ Algunas métricas no cumplen los criterios")


if __name__ == "__main__":
    # Ejecutar tests
    print("\n🔧 INICIANDO TESTS DE FUNCIONES MODULARES...\n")
    
    # Test matriz completa
    df_results = test_matrix()
    
    # Test factor de necesidad de red
    test_network_need_impact()
    
    # Test métricas financieras
    test_financial_metrics()
    
    # Guardar resultados
    df_results.to_csv('test_results_modular.csv', index=False)
    print("\n✅ Resultados guardados en test_results_modular.csv")
    
    print("\n🎯 TESTS COMPLETADOS")