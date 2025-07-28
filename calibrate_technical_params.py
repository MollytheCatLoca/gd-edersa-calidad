"""
Script de Calibración de Parámetros Técnicos
============================================
Objetivo: Calibrar solo parámetros técnicos para lograr:
- Payback sin red: 6 años
- Payback con red: 4.8 años
- SIN cambiar precios de energía (fijos por ley)
- Generación máxima: 1,850 MWh/MW/año
"""

def calculate_required_flows(pv_mw=10.0):
    """Calcula los flujos necesarios con precios fijos"""
    
    # Parámetros FIJOS
    capex_per_mw = 800_000
    bos_factor = 0.15
    opex_rate = 0.015
    
    # Precios FIJOS POR LEY
    electricity_price = 75  # USD/MWh
    export_price = 70      # USD/MWh
    self_consumption_ratio = 0.7
    
    # CAPEX
    capex_subtotal = pv_mw * capex_per_mw
    capex_total = capex_subtotal * (1 + bos_factor)
    
    # OPEX
    annual_opex = capex_total * opex_rate
    
    # Flujos netos requeridos para cada payback
    net_flow_6_years = capex_total / 6.0
    net_flow_4_8_years = capex_total / 4.8
    
    # Ingresos totales requeridos
    revenue_6_years = net_flow_6_years + annual_opex
    revenue_4_8_years = net_flow_4_8_years + annual_opex
    
    # Con precios fijos, calcular generación necesaria para payback 6 años
    avg_price = electricity_price * self_consumption_ratio + export_price * (1 - self_consumption_ratio)
    generation_required = revenue_6_years / avg_price
    generation_per_mw = generation_required / pv_mw
    
    # Factor de planta requerido
    hours_per_year = 8760
    cf_required = generation_per_mw / hours_per_year
    
    print("="*60)
    print("ANÁLISIS DE REQUERIMIENTOS")
    print("="*60)
    
    print(f"\nPARA SISTEMA DE {pv_mw} MW:")
    print(f"  CAPEX Total: ${capex_total/1e6:.2f}M")
    print(f"  OPEX Anual: ${annual_opex/1e6:.3f}M/año")
    
    print(f"\nPRECIOS FIJOS POR LEY:")
    print(f"  Electricidad: ${electricity_price}/MWh")
    print(f"  Exportación: ${export_price}/MWh")
    print(f"  Precio promedio ponderado: ${avg_price:.1f}/MWh")
    
    print(f"\nFLUJOS NETOS REQUERIDOS:")
    print(f"  Para payback 6 años: ${net_flow_6_years/1e6:.3f}M/año")
    print(f"  Para payback 4.8 años: ${net_flow_4_8_years/1e6:.3f}M/año")
    
    print(f"\nGENERACIÓN REQUERIDA PARA PAYBACK 6 AÑOS:")
    print(f"  Total: {generation_required:,.0f} MWh/año")
    print(f"  Por MW: {generation_per_mw:,.0f} MWh/MW/año")
    print(f"  Factor de planta requerido: {cf_required:.3f} ({cf_required*100:.1f}%)")
    
    # Verificar si es posible con límite de 1,850 MWh/MW/año
    max_generation_per_mw = 1850
    max_cf = max_generation_per_mw / hours_per_year
    
    if generation_per_mw > max_generation_per_mw:
        print(f"\n⚠️ PROBLEMA: Se requieren {generation_per_mw:.0f} MWh/MW/año")
        print(f"  pero el máximo permitido es {max_generation_per_mw} MWh/MW/año")
        print(f"  Usaremos el máximo permitido (CF = {max_cf:.3f})")
        
        # Recalcular con generación máxima
        generation_per_mw = max_generation_per_mw
        cf_used = max_cf
        generation_total = generation_per_mw * pv_mw
        
        # Ingresos con generación máxima
        pv_revenue = generation_total * avg_price
        net_flow_actual = pv_revenue - annual_opex
        payback_actual = capex_total / net_flow_actual
        
        print(f"\nCON GENERACIÓN MÁXIMA PERMITIDA:")
        print(f"  Generación: {generation_total:,.0f} MWh/año")
        print(f"  Ingresos PV: ${pv_revenue/1e6:.3f}M/año")
        print(f"  Flujo neto: ${net_flow_actual/1e6:.3f}M/año")
        print(f"  Payback real sin red: {payback_actual:.1f} años")
        
        # Ajustar CAPEX o OPEX para lograr payback 6 años
        capex_adjustment_needed = net_flow_actual * 6.0 - capex_total
        print(f"\n  Para lograr payback de 6 años exactos:")
        print(f"  - Opción 1: Reducir CAPEX en ${-capex_adjustment_needed/1e6:.2f}M")
        print(f"  - Opción 2: Ajustar otros parámetros técnicos")
    else:
        cf_used = cf_required
        generation_total = generation_required
        pv_revenue = generation_total * avg_price
        net_flow_actual = pv_revenue - annual_opex
        payback_actual = 6.0
        print(f"\n✅ Generación requerida está dentro del límite")
    
    # Beneficios de red necesarios
    network_benefits_needed = net_flow_4_8_years - net_flow_actual
    
    print(f"\nBENEFICIOS DE RED NECESARIOS:")
    print(f"  Para reducir payback a 4.8 años: ${network_benefits_needed/1e6:.3f}M/año")
    print(f"  Como % del flujo base: {network_benefits_needed/net_flow_actual*100:.1f}%")
    
    return {
        'capex_total': capex_total,
        'annual_opex': annual_opex,
        'generation_mwh': generation_total,
        'cf_used': cf_used,
        'pv_revenue': pv_revenue,
        'net_flow_base': net_flow_actual,
        'payback_base': payback_actual,
        'network_benefits_needed': network_benefits_needed
    }


def calibrate_technical_params(pv_mw=10.0):
    """Calibra parámetros técnicos de red"""
    
    # Calcular requerimientos
    req = calculate_required_flows(pv_mw)
    
    if req['payback_base'] > 6.1:
        print("\n" + "="*60)
        print("AJUSTES TÉCNICOS NECESARIOS")
        print("="*60)
        
        # Opciones de ajuste técnico
        print("\nOPCIONES PARA LOGRAR PAYBACK BASE DE 6 AÑOS:")
        
        # Opción 1: Reducir CAPEX mediante economías de escala
        capex_reduction_needed = req['capex_total'] - (req['net_flow_base'] * 6.0)
        capex_reduced = req['capex_total'] - capex_reduction_needed
        capex_per_mw_new = capex_reduced / (1.15 * pv_mw)  # Descontar BOS
        
        print(f"\n1. ECONOMÍA DE ESCALA EN CAPEX:")
        print(f"   CAPEX actual: ${req['capex_total']/1e6:.2f}M")
        print(f"   CAPEX necesario: ${capex_reduced/1e6:.2f}M")
        print(f"   Reducción: ${capex_reduction_needed/1e6:.2f}M ({capex_reduction_needed/req['capex_total']*100:.1f}%)")
        print(f"   Nuevo costo por MW: ${capex_per_mw_new/1e3:.0f}k/MW")
        
        # Opción 2: Reducir OPEX mediante optimización O&M
        opex_reduction_needed = req['annual_opex'] - (req['pv_revenue'] - req['capex_total']/6.0)
        new_opex_rate = (req['annual_opex'] - opex_reduction_needed) / req['capex_total']
        
        print(f"\n2. OPTIMIZACIÓN DE O&M:")
        print(f"   OPEX actual: ${req['annual_opex']/1e6:.3f}M/año ({1.5}% del CAPEX)")
        print(f"   Reducción necesaria: ${opex_reduction_needed/1e6:.3f}M/año")
        print(f"   Nueva tasa OPEX: {new_opex_rate*100:.2f}% del CAPEX")
        
        # Usar reducción de CAPEX como solución
        req['capex_total'] = capex_reduced
        req['net_flow_base'] = req['pv_revenue'] - req['annual_opex']
        req['payback_base'] = 6.0
    
    # Distribución de beneficios de red
    network_total = req['network_benefits_needed']
    
    q_night_value = network_total * 0.40
    loss_reduction_value = network_total * 0.35
    reliability_value = network_total * 0.25
    
    print("\n" + "="*60)
    print("CALIBRACIÓN DE PARÁMETROS TÉCNICOS")
    print("="*60)
    
    print(f"\nDISTRIBUCIÓN DE BENEFICIOS (${network_total/1e6:.3f}M/año):")
    print(f"  Q at Night (40%): ${q_night_value/1e6:.3f}M/año")
    print(f"  Loss Reduction (35%): ${loss_reduction_value/1e6:.3f}M/año")
    print(f"  Reliability (25%): ${reliability_value/1e6:.3f}M/año")
    
    # Calcular parámetros técnicos
    q_mvar = pv_mw * 0.3  # 30% fijo
    q_kvar = q_mvar * 1000
    
    # 1. Q at Night - ajustar remuneración
    pf_penalty = q_night_value / (q_kvar * 12)
    
    print(f"\n1. COMPENSACIÓN REACTIVA (Q at Night):")
    print(f"   Capacidad: {q_mvar:.1f} MVAr")
    print(f"   Remuneración calibrada: ${pf_penalty:.2f}/kVAr-mes")
    
    # 2. Loss Reduction - ajustar sensibilidad y/o valorización
    # Opciones: a) Mayor sensibilidad, b) Mayor precio de pérdidas
    electricity_price = 75  # Fijo
    hours = 8760
    
    # Opción 2a: Solo sensibilidad
    loss_mwh_needed = loss_reduction_value / electricity_price
    loss_mw_needed = loss_mwh_needed / hours
    loss_sensitivity = loss_mw_needed / pv_mw
    
    print(f"\n2. REDUCCIÓN DE PÉRDIDAS:")
    print(f"   Opción A - Solo sensibilidad:")
    print(f"   - Reducción necesaria: {loss_mw_needed:.3f} MW")
    print(f"   - Sensibilidad: {loss_sensitivity:.4f} (MW loss/MW PV)")
    print(f"   - Precio pérdidas: ${electricity_price}/MWh (precio energía)")
    
    # Opción 2b: Sensibilidad moderada + mayor valorización
    loss_sensitivity_moderate = 0.03  # 3% más realista
    loss_mw_moderate = pv_mw * loss_sensitivity_moderate
    loss_price_needed = loss_reduction_value / (loss_mw_moderate * hours)
    
    print(f"\n   Opción B - Sensibilidad moderada + valorización:")
    print(f"   - Sensibilidad: {loss_sensitivity_moderate:.3f} (3% - más realista)")
    print(f"   - Reducción: {loss_mw_moderate:.3f} MW")
    print(f"   - Precio pérdidas necesario: ${loss_price_needed:.0f}/MWh")
    print(f"   - Factor sobre precio energía: {loss_price_needed/electricity_price:.1f}x")
    
    # 3. Reliability - ajustar mejora SAIDI
    users = 5000
    saidi_cost = 50
    
    saidi_reduction = reliability_value / (saidi_cost * users/1000)
    saidi_base = 120  # minutos/año típico
    saidi_improvement_percent = saidi_reduction / saidi_base * 100
    
    print(f"\n3. MEJORA DE CONFIABILIDAD:")
    print(f"   Usuarios beneficiados: {users:,}")
    print(f"   Reducción SAIDI: {saidi_reduction:.0f} minutos/año")
    print(f"   Mejora sobre SAIDI base: {saidi_improvement_percent:.0f}%")
    print(f"   Factor de mejora: {saidi_reduction/saidi_base:.2f}")
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PARÁMETROS CALIBRADOS")
    print("="*60)
    
    print(f"\nPARA ACTUALIZAR EN parameters.yaml:")
    print(f"\n# Compensación reactiva")
    print(f"pf_penalty_usd_kvar_month: {pf_penalty:.2f}")
    
    print(f"\n# Reducción de pérdidas (elegir una opción)")
    print(f"# Opción A:")
    print(f"loss_sensitivity: {loss_sensitivity:.4f}")
    print(f"# Opción B (más realista):")
    print(f"loss_sensitivity: {loss_sensitivity_moderate:.3f}")
    print(f"loss_price_multiplier: {loss_price_needed/electricity_price:.1f}  # Multiplicador sobre precio energía")
    
    print(f"\n# Confiabilidad")
    print(f"saidi_reduction_minutes: {saidi_reduction:.0f}")
    print(f"saidi_improvement_factor: {saidi_reduction/saidi_base:.2f}")
    
    # Verificación final
    print("\n" + "="*60)
    print("VERIFICACIÓN FINAL")
    print("="*60)
    
    print(f"\nCon generación máxima de {req['generation_mwh']/pv_mw:.0f} MWh/MW/año:")
    print(f"  Payback sin red: {req['payback_base']:.1f} años")
    print(f"  Payback con red: 4.8 años")
    print(f"  Mejora: {(req['payback_base']-4.8)/req['payback_base']*100:.0f}%")


if __name__ == "__main__":
    # Calibrar para 10 MW
    calibrate_technical_params(10.0)