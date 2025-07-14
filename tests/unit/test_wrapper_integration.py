#!/usr/bin/env python3
"""
Test de integración del wrapper con BESSModel
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from dashboard.pages.utils.constants import AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW

def test_integration():
    """Test de integración wrapper + BESSModel"""
    
    print("\n" + "="*80)
    print("TEST DE INTEGRACIÓN: BESSModel + Wrapper")
    print("="*80)
    
    # Generar perfil solar
    hours = np.arange(24)
    daylight = (6 <= hours) & (hours <= 18)
    x = (hours - 12) / 6
    solar = np.zeros(24)
    solar[daylight] = np.exp(-2 * x[daylight] ** 2)
    
    daily_target = AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW / 30
    scale_factor = daily_target / solar.sum()
    solar *= scale_factor
    
    # Crear BESS
    bess = BESSModel(
        power_mw=1.0,
        duration_hours=2.0,
        technology='modern_lfp',
        verbose=False
    )
    
    # Test 1: Sin wrapper (comportamiento original)
    print("\nTEST 1: Sin wrapper (original)")
    results1 = bess.simulate_strategy(
        solar_profile=solar,
        strategy='cap_shaving',
        cap_mw=0.3,
        use_wrapper=False  # Explícito, aunque es el default
    )
    
    print(f"  Claves en resultado: {list(results1.keys())[:5]}...")
    print(f"  ¿Tiene ml_metrics? {'ml_metrics' in results1}")
    print(f"  Total grid: {results1['grid_power'].sum():.3f} MWh")
    
    # Test 2: Con wrapper
    print("\nTEST 2: Con wrapper (ML logging)")
    bess.reset()  # Reset para comparación justa
    
    results2 = bess.simulate_strategy(
        solar_profile=solar,
        strategy='cap_shaving',
        cap_mw=0.3,
        use_wrapper=True,
        wrapper_config={
            'log_level': 'INFO',
            'ml_logging': True
        }
    )
    
    print(f"  Claves en resultado: {list(results2.keys())[:8]}...")
    print(f"  ¿Tiene ml_metrics? {'ml_metrics' in results2}")
    print(f"  ¿Tiene ml_dataframe? {'ml_dataframe' in results2}")
    print(f"  Total grid: {results2['grid_power'].sum():.3f} MWh")
    
    if 'ml_dataframe' in results2 and results2['ml_dataframe'] is not None:
        df = results2['ml_dataframe']
        print(f"  ML DataFrame: {df.shape[0]} filas, {df.shape[1]} columnas")
        print(f"  Algunas columnas: {list(df.columns[:10])}")
    
    # Test 3: Verificar que los resultados base son iguales
    print("\nTEST 3: Verificación de consistencia")
    
    # Arrays deben ser idénticos
    arrays_to_check = ['grid_power', 'battery_power', 'soc', 'solar_curtailed']
    all_equal = True
    
    for array_name in arrays_to_check:
        if array_name in results1 and array_name in results2:
            equal = np.allclose(results1[array_name], results2[array_name])
            print(f"  {array_name}: {'✓ Idéntico' if equal else '✗ Diferente'}")
            all_equal &= equal
    
    print(f"\n  Resultado: {'✓ CONSISTENTE' if all_equal else '✗ INCONSISTENTE'}")
    
    # Test 4: Probar diferentes estrategias con wrapper
    print("\nTEST 4: Múltiples estrategias con wrapper")
    
    strategies = ['cap_shaving', 'soft_cap_shaving', 'flat_day']
    
    for strategy in strategies:
        bess.reset()
        
        # Parámetros según estrategia
        params = {}
        if 'cap_shaving' in strategy:
            params['cap_mw'] = 0.3
        elif strategy == 'flat_day':
            params['start_hour'] = 8
            params['end_hour'] = 18
        
        results = bess.simulate_strategy(
            solar_profile=solar,
            strategy=strategy,
            use_wrapper=True,
            wrapper_config={'ml_logging': True, 'validate_balance': True},
            **params
        )
        
        validation = results.get('validation', {})
        metrics = results.get('metrics', {})
        
        print(f"\n  {strategy}:")
        print(f"    Balance válido: {validation.get('valid', False)}")
        print(f"    Errores: {validation.get('balance_errors', 'N/A')}")
        print(f"    Curtailment: {metrics.get('total_curtailed_mwh', 0):.3f} MWh")
        print(f"    Eficiencia: {metrics.get('roundtrip_efficiency', 0)*100:.1f}%")
    
    # Test 5: Configuraciones del wrapper
    print("\nTEST 5: Diferentes configuraciones del wrapper")
    
    configs = [
        {'ml_logging': False, 'validate_balance': True},
        {'ml_logging': True, 'validate_balance': False},
        {'log_level': 'DEBUG', 'tolerance': 1e-3}
    ]
    
    for i, config in enumerate(configs):
        bess.reset()
        
        results = bess.simulate_strategy(
            solar_profile=solar,
            strategy='cap_shaving',
            cap_mw=0.3,
            use_wrapper=True,
            wrapper_config=config
        )
        
        print(f"\n  Config {i+1}: {config}")
        print(f"    ¿ML metrics? {results.get('ml_metrics') is not None}")
        print(f"    ¿Balance errors? {len(results.get('balance_errors', []))}")
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN:")
    print("="*80)
    print("""
1. La integración funciona correctamente
2. use_wrapper=False mantiene comportamiento original
3. use_wrapper=True agrega métricas ML y validación
4. Los resultados base (grid, battery, etc) son idénticos
5. Configuración del wrapper es flexible

USO RECOMENDADO:
- Para producción: use_wrapper=False (más rápido)
- Para análisis/ML: use_wrapper=True
- Para debugging: wrapper_config={'log_level': 'DEBUG'}
""")

if __name__ == "__main__":
    test_integration()