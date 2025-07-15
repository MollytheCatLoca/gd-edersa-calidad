#!/usr/bin/env python3
"""
BESS Performance Optimization Script
====================================

Script para optimizar el rendimiento del sistema DataManagerV2 ↔ BESSModel
y realizar benchmarks completos de performance.

Autor: Claude AI Assistant
Fecha: Julio 2025
Versión: 1.0
"""

import time
import logging
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import gc
import tracemalloc

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dashboard.pages.utils.data_manager_v2 import get_data_manager, reset_data_manager
from dashboard.pages.utils.constants import BESS_TECHNOLOGIES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BESSPerformanceOptimizer:
    """Optimizador de performance para el sistema BESS integrado"""
    
    def __init__(self):
        self.dm = None
        self.benchmark_results = []
        
    def setup(self):
        """Setup inicial del optimizador"""
        logger.info("Inicializando BESSPerformanceOptimizer...")
        reset_data_manager()
        self.dm = get_data_manager()
        
        # Force garbage collection
        gc.collect()
        
    def create_test_profiles(self) -> Dict[str, np.ndarray]:
        """Crear perfiles de prueba de diferentes tamaños"""
        profiles = {}
        
        # Perfil diario (24 horas)
        daily_profile = np.concatenate([
            np.zeros(6),  # Noche
            np.linspace(0, 2, 6),  # Amanecer
            np.full(6, 2.0),  # Día
            np.linspace(2, 0, 6)   # Atardecer
        ])
        profiles['daily'] = daily_profile
        
        # Perfil semanal (168 horas)
        weekly_profile = np.tile(daily_profile, 7)
        profiles['weekly'] = weekly_profile
        
        # Perfil mensual (720 horas)
        monthly_profile = np.tile(daily_profile, 30)
        profiles['monthly'] = monthly_profile
        
        # Perfil anual (8760 horas)
        # Usar un perfil más variable para el año
        base_year = np.random.uniform(0, 3, 8760)
        # Aplicar patrón diario
        for day in range(365):
            start_idx = day * 24
            end_idx = start_idx + 24
            daily_pattern = np.concatenate([
                np.zeros(6),
                np.linspace(0, 1, 6),
                np.full(6, 1.0),
                np.linspace(1, 0, 6)
            ])
            base_year[start_idx:end_idx] *= daily_pattern
        profiles['annual'] = base_year
        
        logger.info(f"Creados {len(profiles)} perfiles de prueba")
        return profiles
        
    def benchmark_bess_strategies(self, solar_profile: np.ndarray, 
                                config: Dict[str, Any]) -> Dict[str, Any]:
        """Benchmark de estrategias BESS"""
        strategies = [
            'time_shift_aggressive',
            'solar_smoothing', 
            'cycling_demo',
            'frequency_regulation',
            'arbitrage_aggressive'
        ]
        
        results = {}
        
        for strategy in strategies:
            logger.info(f"Benchmarking strategy: {strategy}")
            
            # Start memory and time tracking
            tracemalloc.start()
            start_time = time.time()
            
            try:
                result = self.dm.simulate_bess_strategy(
                    solar_profile=solar_profile,
                    strategy=strategy,
                    **config
                )
                
                execution_time = time.time() - start_time
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                if result.status.value == 'real':
                    results[strategy] = {
                        'success': True,
                        'execution_time': execution_time,
                        'memory_current': current / 1024 / 1024,  # MB
                        'memory_peak': peak / 1024 / 1024,  # MB
                        'profile_length': len(solar_profile),
                        'total_cycles': result.data.get('total_cycles', 0),
                        'energy_efficiency': result.data.get('metrics', {}).get('energy_efficiency', 0)
                    }
                else:
                    results[strategy] = {
                        'success': False,
                        'error': result.meta.get('error', 'Unknown error'),
                        'execution_time': execution_time
                    }
                    
            except Exception as e:
                tracemalloc.stop()
                results[strategy] = {
                    'success': False,
                    'error': str(e),
                    'execution_time': time.time() - start_time
                }
                
        return results
    
    def benchmark_bess_technologies(self, solar_profile: np.ndarray) -> Dict[str, Any]:
        """Benchmark de diferentes tecnologías BESS"""
        technologies = list(BESS_TECHNOLOGIES.keys())
        results = {}
        
        base_config = {
            'power_mw': 2.0,
            'duration_hours': 4.0,
            'strategy': 'time_shift_aggressive'
        }
        
        for tech in technologies:
            logger.info(f"Benchmarking technology: {tech}")
            
            start_time = time.time()
            tracemalloc.start()
            
            try:
                result = self.dm.simulate_bess_strategy(
                    solar_profile=solar_profile,
                    technology=tech,
                    **base_config
                )
                
                execution_time = time.time() - start_time
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                if result.status.value == 'real':
                    results[tech] = {
                        'success': True,
                        'execution_time': execution_time,
                        'memory_current': current / 1024 / 1024,
                        'memory_peak': peak / 1024 / 1024,
                        'energy_efficiency': result.data.get('metrics', {}).get('energy_efficiency', 0),
                        'roundtrip_efficiency': result.data.get('bess_config', {}).get('roundtrip_efficiency', 0)
                    }
                else:
                    results[tech] = {
                        'success': False,
                        'error': result.meta.get('error', 'Unknown error')
                    }
                    
            except Exception as e:
                tracemalloc.stop()
                results[tech] = {
                    'success': False,
                    'error': str(e)
                }
                
        return results
    
    def benchmark_optimization(self, solar_profile: np.ndarray) -> Dict[str, Any]:
        """Benchmark del proceso de optimización BESS"""
        logger.info("Benchmarking BESS optimization...")
        
        start_time = time.time()
        tracemalloc.start()
        
        try:
            result = self.dm.optimize_bess_for_solar(
                solar_profile=solar_profile,
                power_range=(1.0, 3.0),
                duration_range=(2.0, 6.0),
                strategy="time_shift_aggressive",
                optimization_metric="energy_efficiency"
            )
            
            execution_time = time.time() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            if result.status.value == 'real':
                best_config = result.data.get('best_configuration', {})
                return {
                    'success': True,
                    'execution_time': execution_time,
                    'memory_current': current / 1024 / 1024,
                    'memory_peak': peak / 1024 / 1024,
                    'configurations_tested': len(result.data.get('all_configurations', [])),
                    'best_power_mw': best_config.get('power_mw', 0),
                    'best_duration_h': best_config.get('duration_hours', 0),
                    'best_efficiency': best_config.get('objective_value', 0)
                }
            else:
                return {
                    'success': False,
                    'error': result.meta.get('error', 'Unknown error'),
                    'execution_time': execution_time
                }
                
        except Exception as e:
            tracemalloc.stop()
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def benchmark_dynamic_control(self, profile_length: int) -> Dict[str, Any]:
        """Benchmark del control dinámico BESS"""
        logger.info(f"Benchmarking dynamic control with {profile_length} steps...")
        
        # Create power request profile
        power_requests = np.concatenate([
            np.full(profile_length//2, -1.0),  # Charge half time
            np.full(profile_length//2, 1.5)   # Discharge half time
        ])
        
        start_time = time.time()
        tracemalloc.start()
        
        try:
            result = self.dm.simulate_bess_dynamic_control(
                initial_soc=0.5,
                power_requests=power_requests,
                power_mw=2.0,
                duration_hours=4.0,
                dt=1.0
            )
            
            execution_time = time.time() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            if result.status.value == 'real':
                metrics = result.data.get('metrics', {})
                return {
                    'success': True,
                    'execution_time': execution_time,
                    'memory_current': current / 1024 / 1024,
                    'memory_peak': peak / 1024 / 1024,
                    'profile_length': profile_length,
                    'final_soc': metrics.get('final_soc', 0),
                    'roundtrip_efficiency': metrics.get('realized_roundtrip_efficiency', 0)
                }
            else:
                return {
                    'success': False,
                    'error': result.meta.get('error', 'Unknown error'),
                    'execution_time': execution_time
                }
                
        except Exception as e:
            tracemalloc.stop()
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def run_full_benchmark(self) -> Dict[str, Any]:
        """Ejecutar benchmark completo del sistema"""
        logger.info("Iniciando benchmark completo del sistema BESS...")
        
        profiles = self.create_test_profiles()
        
        benchmark_results = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'system_info': {
                'python_version': sys.version,
                'numpy_version': np.__version__,
                'pandas_version': pd.__version__
            },
            'profiles': {},
            'strategies': {},
            'technologies': {},
            'optimization': {},
            'dynamic_control': {},
            'summary': {}
        }
        
        # Test different profile sizes
        for profile_name, profile_data in profiles.items():
            logger.info(f"Testing profile: {profile_name} ({len(profile_data)} points)")
            
            config = {
                'power_mw': 2.0,
                'duration_hours': 4.0
            }
            
            # Strategy benchmark
            strategy_results = self.benchmark_bess_strategies(profile_data, config)
            benchmark_results['strategies'][profile_name] = strategy_results
            
            # Only test technologies on shorter profiles for speed
            if len(profile_data) <= 720:  # Monthly or shorter
                tech_results = self.benchmark_bess_technologies(profile_data)
                benchmark_results['technologies'][profile_name] = tech_results
            
            # Only test optimization on daily profile for speed
            if profile_name == 'daily':
                opt_results = self.benchmark_optimization(profile_data)
                benchmark_results['optimization']['daily'] = opt_results
            
            # Store profile info
            benchmark_results['profiles'][profile_name] = {
                'length': len(profile_data),
                'mean': float(np.mean(profile_data)),
                'max': float(np.max(profile_data)),
                'min': float(np.min(profile_data))
            }
        
        # Dynamic control benchmarks
        for length in [24, 168, 720]:
            dc_results = self.benchmark_dynamic_control(length)
            benchmark_results['dynamic_control'][f'{length}_steps'] = dc_results
        
        # Calculate summary statistics
        self._calculate_summary_stats(benchmark_results)
        
        logger.info("Benchmark completo finalizado")
        return benchmark_results
    
    def _calculate_summary_stats(self, results: Dict[str, Any]):
        """Calcular estadísticas resumen del benchmark"""
        summary = {}
        
        # Strategy performance summary
        strategy_times = []
        strategy_success_rates = {}
        
        for profile_name, strategies in results['strategies'].items():
            profile_success = 0
            profile_total = len(strategies)
            
            for strategy_name, strategy_result in strategies.items():
                if strategy_result.get('success', False):
                    profile_success += 1
                    strategy_times.append(strategy_result['execution_time'])
                
                if strategy_name not in strategy_success_rates:
                    strategy_success_rates[strategy_name] = {'success': 0, 'total': 0}
                
                strategy_success_rates[strategy_name]['total'] += 1
                if strategy_result.get('success', False):
                    strategy_success_rates[strategy_name]['success'] += 1
            
            summary[f'{profile_name}_success_rate'] = profile_success / profile_total if profile_total > 0 else 0
        
        if strategy_times:
            summary['avg_strategy_time'] = np.mean(strategy_times)
            summary['max_strategy_time'] = np.max(strategy_times)
            summary['min_strategy_time'] = np.min(strategy_times)
        
        # Individual strategy success rates
        for strategy_name, stats in strategy_success_rates.items():
            summary[f'{strategy_name}_success_rate'] = stats['success'] / stats['total'] if stats['total'] > 0 else 0
        
        # Overall system performance
        summary['total_tests_run'] = sum(len(strategies) for strategies in results['strategies'].values())
        summary['overall_success_rate'] = np.mean([
            summary[key] for key in summary.keys() if key.endswith('_success_rate')
        ])
        
        results['summary'] = summary
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Guardar resultados del benchmark"""
        if filename is None:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bess_performance_benchmark_{timestamp}.json"
        
        output_dir = Path("reports") / "performance"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / filename
        
        import json
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Resultados guardados en: {output_file}")
        return output_file
    
    def print_summary(self, results: Dict[str, Any]):
        """Imprimir resumen de resultados"""
        summary = results.get('summary', {})
        
        print("\n" + "="*70)
        print("BESS PERFORMANCE BENCHMARK SUMMARY")
        print("="*70)
        
        print(f"Timestamp: {results.get('timestamp', 'Unknown')}")
        print(f"Total tests run: {summary.get('total_tests_run', 0)}")
        print(f"Overall success rate: {summary.get('overall_success_rate', 0):.1%}")
        
        print("\nProfile Performance:")
        for profile_name in results.get('profiles', {}).keys():
            success_rate = summary.get(f'{profile_name}_success_rate', 0)
            profile_info = results['profiles'][profile_name]
            print(f"  {profile_name:>8}: {success_rate:.1%} success, {profile_info['length']:>5} points")
        
        print("\nStrategy Success Rates:")
        strategies = ['time_shift_aggressive', 'solar_smoothing', 'cycling_demo', 
                     'frequency_regulation', 'arbitrage_aggressive']
        for strategy in strategies:
            success_rate = summary.get(f'{strategy}_success_rate', 0)
            print(f"  {strategy:>20}: {success_rate:.1%}")
        
        if 'avg_strategy_time' in summary:
            print(f"\nPerformance:")
            print(f"  Average execution time: {summary['avg_strategy_time']:.3f}s")
            print(f"  Min execution time: {summary['min_strategy_time']:.3f}s")
            print(f"  Max execution time: {summary['max_strategy_time']:.3f}s")
        
        print("\nOptimization Results:")
        if 'optimization' in results and 'daily' in results['optimization']:
            opt_result = results['optimization']['daily']
            if opt_result.get('success', False):
                print(f"  Configurations tested: {opt_result.get('configurations_tested', 0)}")
                print(f"  Best efficiency: {opt_result.get('best_efficiency', 0):.1%}")
                print(f"  Optimization time: {opt_result.get('execution_time', 0):.3f}s")
            else:
                print(f"  Optimization failed: {opt_result.get('error', 'Unknown error')}")
        
        print("="*70)


def main():
    """Función principal del script"""
    logger.info("Iniciando optimización de performance BESS...")
    
    optimizer = BESSPerformanceOptimizer()
    optimizer.setup()
    
    # Run full benchmark
    results = optimizer.run_full_benchmark()
    
    # Save and display results
    output_file = optimizer.save_results(results)
    optimizer.print_summary(results)
    
    logger.info(f"Benchmark completado. Resultados guardados en: {output_file}")
    
    return results


if __name__ == "__main__":
    main()