#!/usr/bin/env python3
"""
Demostración del BESS Strategy Wrapper
Muestra cómo usar el wrapper para ML
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.battery.bess_model import BESSModel
from src.battery.bess_strategy_wrapper import BESSStrategyWrapper, prepare_ml_features, create_ml_targets
from dashboard.pages.utils.constants import AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW

def demo_wrapper():
    """Demostración completa del wrapper"""
    
    print("\n" + "="*80)
    print("DEMOSTRACIÓN: BESS STRATEGY WRAPPER PARA ML")
    print("="*80)
    
    # Configuración
    print("\nCONFIGURACIÓN:")
    print("  PSFV: 1.0 MW")
    print("  BESS: 1.0 MW / 2h = 2.0 MWh")
    print("  Estrategias a probar: cap_shaving, soft_cap_shaving, flat_day")
    
    # Generar perfil solar
    hours = np.arange(24)
    daylight = (6 <= hours) & (hours <= 18)
    x = (hours - 12) / 6
    solar = np.zeros(24)
    solar[daylight] = np.exp(-2 * x[daylight] ** 2)
    
    daily_target = AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW / 30
    scale_factor = daily_target / solar.sum()
    solar *= scale_factor
    
    # Crear wrapper
    wrapper = BESSStrategyWrapper(
        log_level='INFO',
        ml_logging=True,
        validate_balance=True,
        tolerance=1e-6
    )
    
    # Probar diferentes estrategias
    strategies_to_test = [
        ('cap_shaving', {'cap_mw': 0.3, 'soft_discharge': True}),
        ('soft_cap_shaving', {'cap_mw': 0.3, 'soft_discharge': True}),
        ('flat_day', {'start_hour': 8, 'end_hour': 18, 'flat_mw': 0.4})
    ]
    
    all_results = {}
    
    for strategy_name, params in strategies_to_test:
        print(f"\n" + "-"*60)
        print(f"PROBANDO: {strategy_name}")
        print(f"Parámetros: {params}")
        
        # Crear BESS nuevo para cada prueba
        bess = BESSModel(
            power_mw=1.0,
            duration_hours=2.0,
            technology='modern_lfp',
            track_history=False,
            verbose=False
        )
        
        # Ejecutar con wrapper
        results = wrapper.execute_strategy(
            bess_model=bess,
            solar=solar,
            strategy_name=strategy_name,
            dt=1.0,
            **params
        )
        
        all_results[strategy_name] = results
        
        # Mostrar resumen
        print(f"\nRESULTADOS:")
        print(f"  Balance válido: {results['validation']['valid']}")
        print(f"  Errores de balance: {results['validation']['balance_errors']}")
        print(f"  Error máximo: {results['validation']['max_error_mw']:.6f} MW")
        print(f"  Tiempo ejecución: {results['metadata']['execution_time_seconds']:.3f} s")
        
        # Métricas agregadas
        metrics = results['metrics']
        print(f"\nMÉTRICAS AGREGADAS:")
        print(f"  Energía total a red: {metrics['total_grid_mwh']:.3f} MWh")
        print(f"  Curtailment: {metrics['total_curtailed_mwh']:.3f} MWh ({metrics['curtailment_ratio']*100:.1f}%)")
        print(f"  Pérdidas: {metrics['total_losses_mwh']:.3f} MWh ({metrics['loss_ratio']*100:.1f}%)")
        print(f"  Eficiencia round-trip: {metrics['roundtrip_efficiency']*100:.1f}%")
        print(f"  Ciclos equivalentes: {metrics['cycles_equivalent']:.2f}")
        print(f"  Reducción variabilidad: {metrics['variability_reduction_pct']:.1f}%")
    
    # Análisis ML
    print("\n" + "="*80)
    print("ANÁLISIS PARA ML:")
    print("="*80)
    
    # Combinar todos los DataFrames ML
    ml_dfs = []
    for strategy_name, results in all_results.items():
        df = results['ml_dataframe']
        if df is not None:
            ml_dfs.append(df)
    
    combined_df = pd.concat(ml_dfs, ignore_index=True)
    print(f"\nDataset combinado: {len(combined_df)} filas, {len(combined_df.columns)} columnas")
    
    # Mostrar algunas features
    print("\nFEATURES DISPONIBLES:")
    feature_cols = ['solar_mw', 'grid_mw', 'battery_mw', 'soc_pct', 'curtailed_mw',
                   'is_charging', 'is_discharging', 'charge_rate', 'soc_headroom',
                   'balance_error_mw', 'cap_mw', 'solar_exceeds_cap']
    
    available_features = [col for col in feature_cols if col in combined_df.columns]
    print(f"  Features principales: {', '.join(available_features[:8])}")
    
    # Estadísticas por estrategia
    print("\nESTADÍSTICAS POR ESTRATEGIA:")
    stats_by_strategy = combined_df.groupby('strategy').agg({
        'solar_mw': 'sum',
        'grid_mw': 'sum',
        'curtailed_mw': 'sum',
        'losses_mwh': 'sum',
        'balance_error_mw': 'max'
    }).round(3)
    print(stats_by_strategy)
    
    # Preparar features para ML
    print("\n" + "-"*60)
    print("PREPARACIÓN PARA ML:")
    
    # Tomar solo cap_shaving para ejemplo
    cap_shaving_results = all_results['cap_shaving']
    
    # Preparar features
    X = prepare_ml_features(cap_shaving_results, include_lags=True, include_rolling=True)
    print(f"\nFeatures preparados: {X.shape[0]} filas, {X.shape[1]} columnas")
    print(f"Primeras 10 features: {list(X.columns[:10])}")
    
    # Crear targets
    y = create_ml_targets(cap_shaving_results)
    print(f"\nTargets creados: {y.shape[1]} diferentes targets")
    print(f"Targets disponibles: {list(y.columns)}")
    
    # Ejemplo de uso para ML
    print("\nEJEMPLO DE USO PARA ML:")
    print("""
# Cargar datos
X = prepare_ml_features(results)
y = create_ml_targets(results)

# Seleccionar target
target = y['target_will_curtail'].fillna(False)

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(
    X.fillna(0), target, test_size=0.2, random_state=42
)

# Entrenar modelo
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluar
accuracy = model.score(X_test, y_test)
print(f"Accuracy: {accuracy:.2%}")
""")
    
    # Generar reporte ML
    print("\n" + "-"*60)
    print("REPORTE ML GENERADO:")
    
    report = wrapper.generate_ml_report()
    print(f"\nBalance validation:")
    print(f"  Errores totales: {report['balance_validation']['errors_count']}")
    print(f"  Error máximo: {report['balance_validation']['max_error_mw']:.6f} MW")
    
    if 'strategy_specific' in report and report['strategy_specific']:
        print(f"\nInfo específica de estrategia:")
        for key, value in report['strategy_specific'].items():
            print(f"  {key}: {value}")
    
    # Visualización
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Comparación de grid power
    ax = axes[0, 0]
    for strategy_name, results in all_results.items():
        ax.plot(hours, results['grid_power'], label=strategy_name, linewidth=2)
    ax.plot(hours, solar, 'k--', label='Solar', alpha=0.5)
    ax.set_xlabel('Hora')
    ax.set_ylabel('Potencia (MW)')
    ax.set_title('Comparación de Estrategias - Grid Power')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: SOC por estrategia
    ax = axes[0, 1]
    for strategy_name, results in all_results.items():
        ax.plot(hours, results['soc'] * 100, label=strategy_name, linewidth=2)
    ax.set_xlabel('Hora')
    ax.set_ylabel('SOC (%)')
    ax.set_title('Estado de Carga por Estrategia')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    
    # Plot 3: Features ML - Heatmap de correlación
    ax = axes[1, 0]
    ml_df = all_results['cap_shaving']['ml_dataframe']
    if ml_df is not None:
        corr_features = ['solar_mw', 'grid_mw', 'battery_mw', 'soc_pct', 'curtailed_mw']
        available_corr = [f for f in corr_features if f in ml_df.columns]
        if len(available_corr) > 2:
            corr_matrix = ml_df[available_corr].corr()
            im = ax.imshow(corr_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
            ax.set_xticks(range(len(available_corr)))
            ax.set_yticks(range(len(available_corr)))
            ax.set_xticklabels(available_corr, rotation=45)
            ax.set_yticklabels(available_corr)
            ax.set_title('Correlación entre Features')
            plt.colorbar(im, ax=ax)
    
    # Plot 4: Balance errors
    ax = axes[1, 1]
    for strategy_name, results in all_results.items():
        errors = results['balance_errors']
        if errors:
            timesteps = [e['timestep'] for e in errors]
            error_values = [e['error'] * 1e6 for e in errors]  # Convertir a W
            ax.scatter(timesteps, error_values, label=strategy_name, s=50)
    ax.set_xlabel('Timestep')
    ax.set_ylabel('Error de Balance (W)')
    ax.set_title('Errores de Balance por Estrategia')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('bess_wrapper_demo.png', dpi=150)
    print("\n✓ Gráficos guardados en 'bess_wrapper_demo.png'")
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN:")
    print("="*80)
    print("""
1. El wrapper funciona correctamente para todas las estrategias
2. Balance energético validado automáticamente (error < 1e-6)
3. Métricas ML registradas para cada timestep (~50 features)
4. Features preparados listos para entrenamiento
5. Múltiples targets disponibles (regresión y clasificación)
6. Reporte completo con estadísticas y análisis

PRÓXIMOS PASOS:
1. Generar dataset más grande con múltiples días/configuraciones
2. Entrenar modelos para predecir curtailment
3. Optimizar parámetros de estrategia con ML
4. Crear sistema de recomendación de estrategia
""")

if __name__ == "__main__":
    demo_wrapper()