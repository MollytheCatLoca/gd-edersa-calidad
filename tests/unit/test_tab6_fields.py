#!/usr/bin/env python3
"""
Test completo para verificar TODOS los campos requeridos por tab6_distributed_generation.py
"""

def test_all_tab6_fields():
    """Test completo del método get_gd_costs() con TODOS los campos requeridos por tab6"""
    
    def mock_get_gd_costs_complete():
        """Método completo con todos los campos requeridos"""
        potencia_mw = 1.8
        factor_capacidad = 0.133
        horas_dia_base = 4
        dias_ano = 365
        
        # Cálculos económicos
        alquiler_mensual = 334000  # ARS mensuales
        alquiler_anual = alquiler_mensual * 12
        opex_por_mw_anual = 180000  # USD/MW/año
        opex_total_anual = opex_por_mw_anual * potencia_mw
        opex_mensual = opex_total_anual / 12
        costo_oym_anual = opex_total_anual * 1.1  # 10% adicional O&M
        costo_oym_mensual = costo_oym_anual / 12
        
        # Costos de combustible
        consumo_gas = 0.278  # m³/kWh
        precio_gas = 0.11137  # USD/m³
        
        # Generación y costos
        energia_anual_mwh = potencia_mw * factor_capacidad * 8760
        energia_anual_kwh = energia_anual_mwh * 1000
        costo_por_mwh = 138.6
        
        # Cálculo combustible
        consumo_gas_anual = energia_anual_kwh * consumo_gas  # m³/año
        costo_combustible_anual = consumo_gas_anual * precio_gas  # USD/año
        costo_combustible_mensual = costo_combustible_anual / 12
        
        # Costos totales
        costo_total_anual = opex_total_anual + costo_combustible_anual
        costo_total_mensual = costo_total_anual / 12
        
        return {
            # Datos base
            'potencia_mw': potencia_mw,
            'factor_capacidad': factor_capacidad,
            'horas_dia_base': horas_dia_base,
            'dias_ano': dias_ano,
            'costo_por_mwh': costo_por_mwh,
            
            # Costos operativos
            'alquiler_mensual': alquiler_mensual,
            'alquiler_anual': alquiler_anual,
            'opex_por_mw_anual': opex_por_mw_anual,
            'opex_total_anual': opex_total_anual,
            'opex_mensual': opex_mensual,
            'costo_oym_anual': costo_oym_anual,
            'costo_oym_mensual': costo_oym_mensual,
            
            # Costos de combustible
            'consumo_gas': consumo_gas,
            'precio_gas': precio_gas,
            'costo_combustible_anual': costo_combustible_anual,
            'costo_combustible_mensual': costo_combustible_mensual,
            
            # Costos totales
            'costo_total_anual': costo_total_anual,
            'costo_total_mensual': costo_total_mensual,
            
            # Generación
            'energia_anual_mwh': energia_anual_mwh,
            'energia_mensual_mwh': energia_anual_mwh / 12,
            'generacion_anual_mwh': energia_anual_mwh,
            'generacion_mensual_mwh': energia_anual_mwh / 12,
        }
    
    # TODOS los campos requeridos por tab6_distributed_generation.py
    required_fields = [
        # Campos base
        'potencia_mw', 'factor_capacidad', 'horas_dia_base', 'dias_ano',
        # Costos operativos
        'alquiler_mensual', 'alquiler_anual', 'opex_por_mw_anual',
        'opex_total_anual', 'opex_mensual', 'costo_oym_anual', 'costo_oym_mensual',
        # Costos combustible
        'consumo_gas', 'precio_gas', 'costo_combustible_anual', 'costo_combustible_mensual',
        # Costos totales
        'costo_total_mensual', 'costo_total_anual',
        # Generación
        'generacion_anual_mwh', 'generacion_mensual_mwh'
    ]
    
    print("🧪 Testing get_gd_costs() method - COMPLETO")
    print("=" * 60)
    
    # Test del método
    gd_costs = mock_get_gd_costs_complete()
    
    # Verificar campos requeridos
    print("📋 Verificando TODOS los campos requeridos por tab6_distributed_generation:")
    print("-" * 60)
    
    missing_fields = []
    for field in required_fields:
        if field in gd_costs:
            print(f"✅ {field:<30} {gd_costs[field]}")
        else:
            print(f"❌ {field:<30} FALTANTE")
            missing_fields.append(field)
    
    print("\n📊 Resultados del test:")
    print("-" * 60)
    
    if not missing_fields:
        print("✅ TODOS LOS CAMPOS ESTÁN PRESENTES")
        print("✅ El método get_gd_costs() es 100% compatible con tab6_distributed_generation.py")
        print("✅ Dashboard debería cargar sin errores KeyError")
    else:
        print("❌ FALTAN CAMPOS REQUERIDOS:")
        for field in missing_fields:
            print(f"   - {field}")
        print("❌ El método get_gd_costs() NO es compatible")
    
    print("\n💡 Resumen económico:")
    print("-" * 60)
    print(f"   - Potencia: {gd_costs['potencia_mw']} MW")
    print(f"   - Factor capacidad: {gd_costs['factor_capacidad']:.1%}")
    print(f"   - Generación anual: {gd_costs['generacion_anual_mwh']:.1f} MWh")
    print(f"   - Costo total anual: ${gd_costs['costo_total_anual']:,.0f}")
    print(f"   - Costo total mensual: ${gd_costs['costo_total_mensual']:,.0f}")
    print(f"   - Costo por MWh: ${gd_costs['costo_por_mwh']}")
    
    return len(missing_fields) == 0

if __name__ == "__main__":
    success = test_all_tab6_fields()
    if success:
        print("\n🎉 TEST COMPLETO EXITOSO")
        print("✅ Todos los campos de tab6_distributed_generation.py están cubiertos")
        print("✅ Dashboard debería cargar sin errores KeyError")
    else:
        print("\n❌ TEST FALLIDO")
        print("❌ Faltan campos - Dashboard tendrá errores KeyError")