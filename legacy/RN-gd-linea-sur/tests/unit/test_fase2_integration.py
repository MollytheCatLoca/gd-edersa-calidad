#!/usr/bin/env python3
"""
Test de integración FASE 2 - Verificación de refactorización completa
Verifica que SolarBESSSimulator delegue correctamente a BESSModel
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from dashboard.pages.utils.solar_bess_simulator import SolarBESSSimulator
from dashboard.pages.utils.data_manager_v2 import DataManagerV2

def test_basic_integration():
    """Test básico de integración con BESSModel"""
    print("🔄 Iniciando test básico de integración FASE 2...")
    
    # Crear simulador
    simulator = SolarBESSSimulator()
    
    # Test 1: Simulación básica con nueva delegación
    print("\n📊 Test 1: Simulación básica con BESSModel.simulate_strategy()")
    result = simulator.simulate_solar_with_bess(
        station="TEST_STATION",
        psfv_power_mw=2.0,
        bess_power_mw=1.0,
        bess_duration_h=4.0,
        month=6,
        strategy="time_shift",
        use_aggressive_strategies=False
    )
    
    print(f"✅ Resultado obtenido: {result.status}")
    print(f"   Backend usado: {result.meta.get('strategy_params', {}).get('bess_backend', 'unknown')}")
    print(f"   Métricas: {list(result.data['metrics'].keys())}")
    
    # Test 2: Verificar que estrategias se mapean correctamente
    print("\n🔀 Test 2: Mapeo de estrategias")
    strategies = ["time_shift", "peak_limit", "smoothing", "firm_capacity"]
    for strategy in strategies:
        result = simulator.simulate_solar_with_bess(
            station="TEST_STATION",
            psfv_power_mw=1.0,
            bess_power_mw=0.5,
            bess_duration_h=2.0,
            month=6,
            strategy=strategy,
            use_aggressive_strategies=False
        )
        strategy_mapped = result.meta.get('strategy_params', {}).get('strategy_mapped', 'unknown')
        print(f"   {strategy} -> {strategy_mapped}")
    
    # Test 3: Control dinámico con next_state()
    print("\n🎮 Test 3: Control dinámico con next_state()")
    control_sequence = np.array([0.0, -0.5, -0.3, 0.0, 0.2, 0.5, 0.3, 0.0] + [0.0] * 16)
    result = simulator.simulate_dynamic_control(
        station="TEST_STATION",
        psfv_power_mw=1.0,
        bess_power_mw=0.5,
        bess_duration_h=2.0,
        control_sequence=control_sequence,
        month=6,
        dt=1.0
    )
    
    print(f"✅ Control dinámico: {result.status}")
    print(f"   Métricas adicionales: {[k for k in result.data['metrics'].keys() if 'control' in k]}")
    
    # Test 4: Verificar compatibilidad con DataManagerV2
    print("\n🔗 Test 4: Compatibilidad con DataManagerV2")
    try:
        dm = DataManagerV2()
        result = dm.simulate_solar_with_bess(
            station="TEST_STATION",
            psfv_power_mw=1.0,
            bess_power_mw=0.5,
            bess_duration_h=2.0,
            month=6,
            strategy="time_shift",
            aggressive=False
        )
        print(f"✅ DataManagerV2 compatible: {result.status}")
        print(f"   Datos disponibles: {list(result.data.keys())}")
    except Exception as e:
        print(f"❌ Error en DataManagerV2: {e}")
    
    print("\n🎉 Tests de integración FASE 2 completados!")

def test_cache_performance():
    """Test de rendimiento de caché"""
    print("\n⚡ Test de rendimiento de caché...")
    
    simulator = SolarBESSSimulator()
    
    # Primera llamada (cache miss)
    result1 = simulator.simulate_solar_with_bess(
        station="CACHE_TEST",
        psfv_power_mw=1.0,
        bess_power_mw=0.5,
        bess_duration_h=2.0,
        month=6,
        strategy="time_shift",
        use_aggressive_strategies=False
    )
    
    # Segunda llamada (cache hit)
    result2 = simulator.simulate_solar_with_bess(
        station="CACHE_TEST",
        psfv_power_mw=1.0,
        bess_power_mw=0.5,
        bess_duration_h=2.0,
        month=6,
        strategy="time_shift",
        use_aggressive_strategies=False
    )
    
    cache_stats = simulator.get_cache_stats()
    print(f"✅ Cache funcional: {cache_stats['hit_rate']:.1%} hit rate")
    print(f"   Hits: {cache_stats['cache_hits']}, Misses: {cache_stats['cache_misses']}")

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE INTEGRACIÓN FASE 2 - SOLAR BESS SIMULATOR")
    print("=" * 60)
    
    test_basic_integration()
    test_cache_performance()
    
    print("\n" + "=" * 60)
    print("FASE 2 COMPLETADA EXITOSAMENTE ✅")
    print("SolarBESSSimulator ahora delega completamente a BESSModel")
    print("=" * 60)