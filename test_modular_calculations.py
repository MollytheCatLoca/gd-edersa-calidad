"""
Script de prueba para validar cálculos modulares
================================================
Ejecuta todos los módulos con 10 MW y parámetros típicos
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.economics.energy_flows import (
    calculate_pv_generation,
    calculate_pv_total_flows
)
from src.economics.network_benefits_modular import (
    calculate_total_network_benefits,
    estimate_network_parameters
)
from src.economics.financial_metrics import (
    calculate_capex_total,
    calculate_annual_opex,
    calculate_all_financial_metrics
)

def test_10mw_system():
    """Prueba sistema de 10 MW con parámetros típicos"""
    
    print("="*60)
    print("PRUEBA SISTEMA 10 MW - CÁLCULOS MODULARES")
    print("="*60)
    
    # Configuración del sistema
    pv_mw = 10.0
    bess_mwh = 5.0  # 0.5h de almacenamiento
    q_mvar = 3.0    # 30% de capacidad reactiva
    
    print(f"\nCONFIGURACIÓN:")
    print(f"  PV: {pv_mw} MW")
    print(f"  BESS: {bess_mwh} MWh")
    print(f"  Q at Night: {q_mvar} MVAr")
    
    # =====================
    # 1. CAPEX
    # =====================
    print(f"\n{'='*40}")
    print("1. CÁLCULO DE CAPEX")
    print(f"{'='*40}")
    
    capex_total = calculate_capex_total(
        pv_mw=pv_mw,
        bess_mwh=bess_mwh,
        q_mvar=q_mvar,
        pv_capex_usd_mw=800000,      # $800k/MW
        bess_capex_usd_mwh=200000,    # $200k/MWh
        statcom_capex_usd_mvar=40000, # $40k/MVAr
        bos_factor=0.15               # 15% BOS
    )
    
    print(f"  PV: ${pv_mw * 800000 / 1e6:.1f}M")
    print(f"  BESS: ${bess_mwh * 200000 / 1e6:.1f}M")
    print(f"  STATCOM: ${q_mvar * 40000 / 1e6:.1f}M")
    print(f"  BOS (15%): ${(capex_total/1.15*0.15) / 1e6:.1f}M")
    print(f"  TOTAL: ${capex_total / 1e6:.1f}M")
    
    # =====================
    # 2. GENERACIÓN PV
    # =====================
    print(f"\n{'='*40}")
    print("2. GENERACIÓN SOLAR")
    print(f"{'='*40}")
    
    annual_generation_mwh, annual_generation_gwh = calculate_pv_generation(
        pv_mw=pv_mw,
        capacity_factor=0.22,  # 22% típico Argentina
        hours_per_year=8760
    )
    
    print(f"  Capacidad: {pv_mw} MW")
    print(f"  Factor de planta: 22%")
    print(f"  Generación: {annual_generation_mwh:,.0f} MWh/año ({annual_generation_gwh:.1f} GWh/año)")
    print(f"  Horas equivalentes: {annual_generation_mwh/pv_mw:.0f} h/año")
    
    # =====================
    # 3. FLUJOS PV
    # =====================
    print(f"\n{'='*40}")
    print("3. FLUJOS ECONÓMICOS PV")
    print(f"{'='*40}")
    
    pv_flows = calculate_pv_total_flows(
        generation_mwh=annual_generation_mwh,
        self_consumption_ratio=0.7,  # 70% autoconsumo
        electricity_price=75,        # $75/MWh
        export_price=70             # $70/MWh
    )
    
    print(f"  Autoconsumo (70%): {annual_generation_mwh * 0.7:,.0f} MWh × $75 = ${pv_flows['self_consumption']/1e6:.2f}M/año")
    print(f"  Exportación (30%): {annual_generation_mwh * 0.3:,.0f} MWh × $70 = ${pv_flows['exports']/1e6:.2f}M/año")
    print(f"  TOTAL PV: ${pv_flows['total']/1e6:.2f}M/año")
    
    # =====================
    # 4. BENEFICIOS DE RED
    # =====================
    print(f"\n{'='*40}")
    print("4. BENEFICIOS DE RED")
    print(f"{'='*40}")
    
    # Parámetros típicos de red
    network_params = {
        'base_losses_mw': pv_mw * 0.08,  # 8% de pérdidas base
        'users_affected': 5000,
        'loss_sensitivity': 0.05,
        'pf_penalty_usd_kvar_month': 4.0,
        'voltage_improvement_pu': 0.02,
        'violation_hours_year': 500,
        'violation_cost_hour': 500,
        'saidi_minutes': 120,
        'saidi_cost_minute': 50,
        'coincidence_factor': 0.7,
        'demand_charge_usd_kw_month': 12.0,
        'include_deferral': True,
        'upgrade_cost_usd_mw': 100000,
        'deferral_years': 5,
        'discount_rate': 0.10
    }
    
    network_benefits = calculate_total_network_benefits(
        pv_mw=pv_mw,
        bess_mwh=bess_mwh,
        q_mvar=q_mvar,
        network_params=network_params
    )
    
    print(f"  Reducción pérdidas: ${network_benefits['loss_reduction']/1e6:.2f}M/año")
    print(f"  Soporte reactivo: ${network_benefits['reactive_support']/1e6:.2f}M/año")
    print(f"  Soporte tensión: ${network_benefits['voltage_support']/1e6:.2f}M/año")
    print(f"  Confiabilidad: ${network_benefits['reliability']/1e6:.2f}M/año")
    print(f"  Reducción demanda: ${network_benefits['demand_reduction']/1e6:.2f}M/año")
    print(f"  Diferimiento: ${network_benefits['transmission_deferral']/1e6:.2f}M/año")
    print(f"  TOTAL RED: ${network_benefits['total']/1e6:.2f}M/año")
    
    # =====================
    # 5. OPEX
    # =====================
    print(f"\n{'='*40}")
    print("5. COSTOS OPERATIVOS")
    print(f"{'='*40}")
    
    annual_opex = calculate_annual_opex(
        capex_total=capex_total,
        pv_mw=pv_mw,
        bess_mwh=bess_mwh,
        q_mvar=q_mvar,
        opex_rate_pv=0.01,      # 1% CAPEX
        opex_rate_bess=0.015,   # 1.5% CAPEX
        opex_rate_statcom=0.02  # 2% CAPEX
    )
    
    print(f"  OPEX anual: ${annual_opex/1e3:.0f}k/año")
    print(f"  Como % del CAPEX: {annual_opex/capex_total*100:.1f}%")
    
    # =====================
    # 6. MÉTRICAS FINANCIERAS
    # =====================
    print(f"\n{'='*40}")
    print("6. MÉTRICAS FINANCIERAS")
    print(f"{'='*40}")
    
    # Ingresos totales
    total_annual_revenue = pv_flows['total'] + network_benefits['total']
    print(f"\n  Ingresos totales: ${total_annual_revenue/1e6:.2f}M/año")
    print(f"  Margen operativo: ${(total_annual_revenue - annual_opex)/1e6:.2f}M/año")
    
    # Calcular métricas
    financial_metrics = calculate_all_financial_metrics(
        capex=capex_total,
        annual_revenue=total_annual_revenue,
        annual_opex=annual_opex,
        annual_generation_mwh=annual_generation_mwh,
        project_lifetime=20,
        discount_rate=0.10,
        inflation_rate=0.04
    )
    
    print(f"\n  NPV @ 10%: ${financial_metrics['npv']/1e6:.1f}M")
    print(f"  IRR: {financial_metrics['irr']*100:.1f}%")
    print(f"  Payback: {financial_metrics['payback']:.1f} años")
    print(f"  LCOE: ${financial_metrics['lcoe']:.0f}/MWh")
    print(f"  B/C: {financial_metrics['bc_ratio']:.2f}")
    
    # =====================
    # 7. RESUMEN EJECUTIVO
    # =====================
    print(f"\n{'='*40}")
    print("7. RESUMEN EJECUTIVO")
    print(f"{'='*40}")
    
    print(f"\nINVERSIÓN:")
    print(f"  CAPEX Total: ${capex_total/1e6:.1f}M")
    print(f"  CAPEX por MW: ${capex_total/pv_mw/1e3:.0f}k/MW")
    
    print(f"\nOPERACIÓN ANUAL:")
    print(f"  Generación: {annual_generation_gwh:.1f} GWh/año")
    print(f"  Ingresos PV: ${pv_flows['total']/1e6:.2f}M/año")
    print(f"  Beneficios Red: ${network_benefits['total']/1e6:.2f}M/año")
    print(f"  OPEX: ${annual_opex/1e6:.2f}M/año")
    print(f"  Flujo Neto: ${(total_annual_revenue - annual_opex)/1e6:.2f}M/año")
    
    print(f"\nRENTABILIDAD:")
    print(f"  TIR: {financial_metrics['irr']*100:.1f}%")
    print(f"  Payback: {financial_metrics['payback']:.1f} años")
    print(f"  NPV/CAPEX: {financial_metrics['npv']/capex_total:.1%}")
    
    # Validación
    from src.economics.financial_metrics import validate_financial_metrics
    warnings = validate_financial_metrics(financial_metrics)
    if warnings:
        print(f"\n⚠️  ADVERTENCIAS:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print(f"\n✅ Todas las métricas están en rangos razonables")

if __name__ == "__main__":
    test_10mw_system()