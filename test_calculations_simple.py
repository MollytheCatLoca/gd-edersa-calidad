"""
Prueba simplificada de cálculos - Sin numpy
==========================================
"""

def test_10mw_simple():
    """Prueba sistema de 10 MW con cálculos directos"""
    
    print("="*60)
    print("PRUEBA SISTEMA 10 MW - CÁLCULOS DIRECTOS")
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
    
    pv_capex = pv_mw * 800_000
    bess_capex = bess_mwh * 200_000
    statcom_capex = q_mvar * 40_000
    subtotal = pv_capex + bess_capex + statcom_capex
    bos = subtotal * 0.15
    capex_total = subtotal + bos
    
    print(f"  PV: ${pv_capex / 1e6:.1f}M")
    print(f"  BESS: ${bess_capex / 1e6:.1f}M")
    print(f"  STATCOM: ${statcom_capex / 1e6:.1f}M")
    print(f"  BOS (15%): ${bos / 1e6:.1f}M")
    print(f"  TOTAL: ${capex_total / 1e6:.1f}M")
    
    # =====================
    # 2. GENERACIÓN PV
    # =====================
    print(f"\n{'='*40}")
    print("2. GENERACIÓN SOLAR")
    print(f"{'='*40}")
    
    capacity_factor = 0.22
    hours_per_year = 8760
    annual_generation_mwh = pv_mw * hours_per_year * capacity_factor
    annual_generation_gwh = annual_generation_mwh / 1000
    
    print(f"  Capacidad: {pv_mw} MW")
    print(f"  Factor de planta: {capacity_factor*100:.0f}%")
    print(f"  Generación: {annual_generation_mwh:,.0f} MWh/año ({annual_generation_gwh:.1f} GWh/año)")
    print(f"  Horas equivalentes: {annual_generation_mwh/pv_mw:.0f} h/año")
    
    # =====================
    # 3. FLUJOS PV
    # =====================
    print(f"\n{'='*40}")
    print("3. FLUJOS ECONÓMICOS PV")
    print(f"{'='*40}")
    
    self_consumption_ratio = 0.7
    export_ratio = 0.3
    electricity_price = 75  # USD/MWh
    export_price = 70      # USD/MWh
    
    self_consumption_mwh = annual_generation_mwh * self_consumption_ratio
    export_mwh = annual_generation_mwh * export_ratio
    
    self_consumption_value = self_consumption_mwh * electricity_price
    export_value = export_mwh * export_price
    total_pv_value = self_consumption_value + export_value
    
    print(f"  Autoconsumo (70%): {self_consumption_mwh:,.0f} MWh × ${electricity_price} = ${self_consumption_value/1e6:.2f}M/año")
    print(f"  Exportación (30%): {export_mwh:,.0f} MWh × ${export_price} = ${export_value/1e6:.2f}M/año")
    print(f"  TOTAL PV: ${total_pv_value/1e6:.2f}M/año")
    
    # =====================
    # 4. BENEFICIOS DE RED
    # =====================
    print(f"\n{'='*40}")
    print("4. BENEFICIOS DE RED")
    print(f"{'='*40}")
    
    # 4.1 Reducción de pérdidas
    base_losses_mw = pv_mw * 0.08  # 8% pérdidas base
    loss_sensitivity = 0.05
    loss_reduction_mw = pv_mw * loss_sensitivity
    loss_reduction_mw = min(loss_reduction_mw, base_losses_mw * 0.5)  # Max 50%
    loss_reduction_value = loss_reduction_mw * 8760 * electricity_price
    
    print(f"  Reducción pérdidas: {loss_reduction_mw:.2f} MW × 8760h × ${electricity_price} = ${loss_reduction_value/1e6:.2f}M/año")
    
    # 4.2 Soporte reactivo
    q_kvar = q_mvar * 1000
    pf_penalty = 4.0  # USD/kVAr-mes
    q_value = q_kvar * pf_penalty * 12
    
    print(f"  Soporte reactivo: {q_kvar:.0f} kVAr × ${pf_penalty}/mes × 12 = ${q_value/1e6:.2f}M/año")
    
    # 4.3 Soporte de tensión
    voltage_improvement = 0.02  # 2%
    violation_hours = 500
    violation_cost = 500  # USD/hora
    improvement_factor = (pv_mw + 0.7 * q_mvar) / (pv_mw + q_mvar)
    hours_reduced = violation_hours * voltage_improvement * 50 * improvement_factor
    hours_reduced = min(hours_reduced, violation_hours * 0.8)
    voltage_value = hours_reduced * violation_cost
    
    print(f"  Soporte tensión: {hours_reduced:.0f} horas × ${violation_cost} = ${voltage_value/1e6:.2f}M/año")
    
    # 4.4 Confiabilidad
    users_affected = 5000
    saidi_minutes = 120
    saidi_cost = 50
    has_bess = bess_mwh > 0
    improvement_factor = 0.15 if has_bess else 0.08
    saidi_reduction = saidi_minutes * improvement_factor
    reliability_value = saidi_reduction * saidi_cost * (users_affected / 1000)
    
    print(f"  Confiabilidad: {saidi_reduction:.1f} min × ${saidi_cost} × {users_affected/1000:.1f}k users = ${reliability_value/1e6:.2f}M/año")
    
    # 4.5 Reducción demanda
    coincidence_factor = 0.7
    demand_charge = 12.0  # USD/kW-mes
    demand_reduction_kw = pv_mw * 1000 * coincidence_factor
    demand_value = demand_reduction_kw * demand_charge * 12
    
    print(f"  Reducción demanda: {demand_reduction_kw:.0f} kW × ${demand_charge}/mes × 12 = ${demand_value/1e6:.2f}M/año")
    
    # 4.6 Diferimiento inversiones
    upgrade_cost = pv_mw * 100_000
    deferral_years = 5
    discount_rate = 0.10
    pv_deferral = upgrade_cost * (1 - 1/(1 + discount_rate)**deferral_years)
    annuity_factor = discount_rate / (1 - (1 + discount_rate)**(-20))
    deferral_value = pv_deferral * annuity_factor
    
    print(f"  Diferimiento: ${upgrade_cost/1e6:.1f}M diferido {deferral_years} años = ${deferral_value/1e6:.2f}M/año")
    
    # Total beneficios red
    total_network = (loss_reduction_value + q_value + voltage_value + 
                    reliability_value + demand_value + deferral_value)
    
    print(f"  TOTAL RED: ${total_network/1e6:.2f}M/año")
    
    # =====================
    # 5. OPEX
    # =====================
    print(f"\n{'='*40}")
    print("5. COSTOS OPERATIVOS")
    print(f"{'='*40}")
    
    # Tasas OPEX ponderadas
    total_capacity = pv_mw + bess_mwh + q_mvar
    weighted_opex_rate = (pv_mw * 0.01 + bess_mwh * 0.015 + q_mvar * 0.02) / total_capacity
    annual_opex = capex_total * weighted_opex_rate
    
    print(f"  OPEX anual: ${annual_opex/1e3:.0f}k/año")
    print(f"  Como % del CAPEX: {annual_opex/capex_total*100:.1f}%")
    
    # =====================
    # 6. MÉTRICAS FINANCIERAS
    # =====================
    print(f"\n{'='*40}")
    print("6. MÉTRICAS FINANCIERAS")
    print(f"{'='*40}")
    
    # Ingresos totales
    total_annual_revenue = total_pv_value + total_network
    print(f"\n  Ingresos totales: ${total_annual_revenue/1e6:.2f}M/año")
    print(f"  OPEX: ${annual_opex/1e6:.2f}M/año")
    print(f"  Margen operativo: ${(total_annual_revenue - annual_opex)/1e6:.2f}M/año")
    
    # Métricas simplificadas
    net_annual_flow = total_annual_revenue - annual_opex
    simple_payback = capex_total / net_annual_flow if net_annual_flow > 0 else 999
    
    # NPV simplificado
    project_lifetime = 20
    discount_rate = 0.10
    inflation_rate = 0.04
    
    npv = -capex_total
    for year in range(1, project_lifetime + 1):
        annual_flow = net_annual_flow * (1 + inflation_rate) ** (year - 1)
        npv += annual_flow / (1 + discount_rate) ** year
    
    # IRR aproximada
    if simple_payback < project_lifetime:
        irr = (1 / simple_payback) * 0.85  # Aproximación
    else:
        irr = 0
    
    # LCOE
    total_generation = annual_generation_mwh * project_lifetime * 0.95  # Con degradación
    total_costs = capex_total + annual_opex * project_lifetime
    lcoe = total_costs / total_generation if total_generation > 0 else 0
    
    # B/C ratio
    bc_ratio = (npv + capex_total) / capex_total if capex_total > 0 else 0
    
    print(f"\n  NPV @ 10%: ${npv/1e6:.1f}M")
    print(f"  IRR: {irr*100:.1f}%")
    print(f"  Payback: {simple_payback:.1f} años")
    print(f"  LCOE: ${lcoe:.0f}/MWh")
    print(f"  B/C: {bc_ratio:.2f}")
    
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
    print(f"  Ingresos PV: ${total_pv_value/1e6:.2f}M/año")
    print(f"  Beneficios Red: ${total_network/1e6:.2f}M/año")
    print(f"  OPEX: ${annual_opex/1e6:.2f}M/año")
    print(f"  Flujo Neto: ${net_annual_flow/1e6:.2f}M/año")
    
    print(f"\nRENTABILIDAD:")
    print(f"  TIR: {irr*100:.1f}%")
    print(f"  Payback: {simple_payback:.1f} años")
    print(f"  NPV/CAPEX: {npv/capex_total:.1%}")
    
    # Validación simple
    print(f"\nVALIDACIÓN:")
    if simple_payback < 2:
        print(f"  ⚠️ Payback muy corto: {simple_payback:.1f} años")
    elif simple_payback > 15:
        print(f"  ⚠️ Payback muy largo: {simple_payback:.1f} años")
    else:
        print(f"  ✅ Payback razonable: {simple_payback:.1f} años")
        
    if irr > 0.30:
        print(f"  ⚠️ IRR muy alta: {irr*100:.0f}%")
    elif irr < 0.10:
        print(f"  ⚠️ IRR baja: {irr*100:.0f}%")
    else:
        print(f"  ✅ IRR razonable: {irr*100:.0f}%")
        
    if bc_ratio > 3:
        print(f"  ⚠️ B/C muy alto: {bc_ratio:.1f}")
    elif bc_ratio < 1.2:
        print(f"  ⚠️ B/C bajo: {bc_ratio:.1f}")
    else:
        print(f"  ✅ B/C razonable: {bc_ratio:.1f}")

if __name__ == "__main__":
    test_10mw_simple()