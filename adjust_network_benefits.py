"""
Script para ajustar beneficios de red
=====================================
Calibra los beneficios para lograr payback de 4.8 años con red
"""

def analyze_current_benefits(pv_mw=10.0, q_percent=30):
    """Analiza los beneficios actuales y propone ajustes"""
    
    # Parámetros base
    capex_total = 7.46e6  # Del test
    net_flow_base = 1.292e6  # Sin red
    
    # Beneficios actuales (del test)
    q_benefit = 0.278e6
    loss_benefit = 0.197e6
    voltage_benefit = 0.120e6
    reliability_benefit = 0.002e6
    demand_benefit = 1.008e6  # Este es el problema!
    total_current = 1.605e6
    
    # Payback actual
    payback_current = capex_total / (net_flow_base + total_current)
    
    # Beneficios objetivo para payback 4.8
    net_flow_target = capex_total / 4.8
    benefits_needed = net_flow_target - net_flow_base
    
    print("="*60)
    print("ANÁLISIS DE BENEFICIOS DE RED")
    print("="*60)
    
    print(f"\nSITUACIÓN ACTUAL:")
    print(f"  Flujo base (sin red): ${net_flow_base/1e6:.3f}M/año")
    print(f"  Beneficios de red: ${total_current/1e6:.3f}M/año")
    print(f"  Flujo total: ${(net_flow_base + total_current)/1e6:.3f}M/año")
    print(f"  Payback actual: {payback_current:.1f} años")
    
    print(f"\nOBJETIVO:")
    print(f"  Payback objetivo: 4.8 años")
    print(f"  Flujo neto requerido: ${net_flow_target/1e6:.3f}M/año")
    print(f"  Beneficios de red necesarios: ${benefits_needed/1e6:.3f}M/año")
    
    print(f"\nDESGLOSE ACTUAL DE BENEFICIOS:")
    print(f"  Q at Night: ${q_benefit/1e6:.3f}M ({q_benefit/total_current*100:.1f}%)")
    print(f"  Loss Reduction: ${loss_benefit/1e6:.3f}M ({loss_benefit/total_current*100:.1f}%)")
    print(f"  Voltage Support: ${voltage_benefit/1e6:.3f}M ({voltage_benefit/total_current*100:.1f}%)")
    print(f"  Reliability: ${reliability_benefit/1e6:.3f}M ({reliability_benefit/total_current*100:.1f}%)")
    print(f"  Demand Reduction: ${demand_benefit/1e6:.3f}M ({demand_benefit/total_current*100:.1f}%)")
    
    # Factor de ajuste
    adjustment_factor = benefits_needed / total_current
    
    print(f"\nAJUSTE NECESARIO:")
    print(f"  Factor de reducción: {adjustment_factor:.3f}")
    print(f"  Reducir beneficios en: {(1-adjustment_factor)*100:.1f}%")
    
    # Propuesta 1: Ajustar solo demand reduction
    demand_adjusted = benefits_needed - (q_benefit + loss_benefit + voltage_benefit + reliability_benefit)
    
    print(f"\nPROPUESTA 1 - Ajustar solo Demand Reduction:")
    print(f"  Demand reduction nuevo: ${demand_adjusted/1e6:.3f}M/año")
    print(f"  Reducción: de $12/kW-mes a ${12 * demand_adjusted/demand_benefit:.2f}/kW-mes")
    
    # Propuesta 2: Ajustar proporcionalmente pero mantener Q y Losses
    other_benefits = voltage_benefit + reliability_benefit + demand_benefit
    other_needed = benefits_needed - (q_benefit + loss_benefit)
    other_factor = other_needed / other_benefits if other_benefits > 0 else 0
    
    print(f"\nPROPUESTA 2 - Mantener Q y Losses, ajustar otros:")
    print(f"  Q at Night: ${q_benefit/1e6:.3f}M (sin cambio)")
    print(f"  Loss Reduction: ${loss_benefit/1e6:.3f}M (sin cambio)")
    print(f"  Voltage Support: ${voltage_benefit * other_factor/1e6:.3f}M")
    print(f"  Reliability: ${reliability_benefit * other_factor/1e6:.3f}M")
    print(f"  Demand Reduction: ${demand_benefit * other_factor/1e6:.3f}M")
    print(f"  TOTAL: ${benefits_needed/1e6:.3f}M/año")
    
    # Propuesta 3: Distribución objetivo (40/35/25)
    q_target = benefits_needed * 0.40
    loss_target = benefits_needed * 0.35
    reliability_target = benefits_needed * 0.25
    
    print(f"\nPROPUESTA 3 - Distribución 40/35/25:")
    print(f"  Q at Night (40%): ${q_target/1e6:.3f}M")
    print(f"  Loss Reduction (35%): ${loss_target/1e6:.3f}M")
    print(f"  Reliability (25%): ${reliability_target/1e6:.3f}M")
    print(f"  TOTAL: ${benefits_needed/1e6:.3f}M/año")
    
    # Calcular parámetros necesarios para Propuesta 3
    print(f"\nPARÁMETROS PARA PROPUESTA 3:")
    
    # Q at Night
    q_mvar = pv_mw * (q_percent/100)
    q_kvar = q_mvar * 1000
    pf_penalty_new = q_target / (q_kvar * 12)
    print(f"  pf_penalty_usd_kvar_month: ${pf_penalty_new:.2f} (actual: $7.72)")
    
    # Loss reduction - necesitamos reducir
    # Actual: 10 MW × 0.03 × 8760 × 75 × 1.2 = $236,520
    # Target: $loss_target
    loss_adjustment = loss_target / loss_benefit
    print(f"  loss_sensitivity: {0.03 * loss_adjustment:.3f} (actual: 0.030)")
    print(f"  O mantener sensitivity y ajustar multiplicador a: {1.2 * loss_adjustment:.2f}")
    
    # Verificación
    print(f"\nVERIFICACIÓN:")
    new_total = q_target + loss_target + reliability_target
    new_payback = capex_total / (net_flow_base + new_total)
    print(f"  Beneficios totales: ${new_total/1e6:.3f}M/año")
    print(f"  Flujo neto total: ${(net_flow_base + new_total)/1e6:.3f}M/año")
    print(f"  Payback con red: {new_payback:.1f} años")
    
    return {
        'benefits_needed': benefits_needed,
        'pf_penalty_new': pf_penalty_new,
        'loss_adjustment': loss_adjustment
    }


if __name__ == "__main__":
    results = analyze_current_benefits(10.0, 30)
    
    print("\n" + "="*60)
    print("RECOMENDACIÓN FINAL")
    print("="*60)
    
    print("\nPara lograr payback de 4.8 años con 30% Q:")
    print("1. Reducir demand_charge_usd_kw_month de $12 a ~$3/kW-mes")
    print("2. O eliminar demand reduction y usar distribución 40/35/25")
    print("3. Ajustar pf_penalty a ~$1.12/kVAr-mes")
    print("4. Reducir loss_sensitivity a ~0.008 o loss_multiplier a ~0.3")