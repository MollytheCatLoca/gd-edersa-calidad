#!/usr/bin/env python3
"""
Run complete configuration matrix for PSFV+BESS testing
Tests all combinations of solar, BESS, and strategies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.pages.utils.data_manager import DataManager
import pandas as pd
import numpy as np
from datetime import datetime
import json
from typing import Dict, List, Any

def run_configuration_matrix():
    """Execute complete test matrix with all configurations"""
    
    print("=" * 80)
    print("PSFV+BESS Configuration Matrix Test")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Initialize data manager
    dm = DataManager()
    
    # Define test parameters
    stations = ['MAQUINCHAO', 'LOS MENUCOS', 'JACOBACCI']
    solar_sizes = [0.5, 1.0, 2.0, 3.0]  # MW
    bess_powers = [0.5, 1.0, 1.5, 2.0]  # MW
    bess_durations = [2, 4, 6]  # hours
    strategies = ['cap_shaving', 'flat_day', 'night_shift', 'ramp_limit']
    solar_technologies = ['SAT Bifacial', 'Fixed Monofacial']
    
    # Calculate total configurations
    total_configs = len(stations) * len(solar_sizes) * len(bess_powers) * len(bess_durations) * len(strategies) * len(solar_technologies)
    print(f"\nTotal configurations to test: {total_configs}")
    print(f"Estimated time: {total_configs * 0.1:.1f} seconds\n")
    
    # Results storage
    results = []
    errors = []
    config_count = 0
    
    # Progress tracking
    start_time = datetime.now()
    
    try:
        for station in stations:
            print(f"\n{'='*60}")
            print(f"Testing station: {station}")
            print(f"{'='*60}")
            
            for solar_tech in solar_technologies:
                for solar_mw in solar_sizes:
                    for bess_power in bess_powers:
                        for bess_duration in bess_durations:
                            for strategy in strategies:
                                config_count += 1
                                
                                # Skip unrealistic configurations
                                if bess_power > solar_mw * 2:
                                    continue
                                
                                config = {
                                    'station': station,
                                    'solar_mw': solar_mw,
                                    'solar_technology': solar_tech,
                                    'bess_power_mw': bess_power,
                                    'bess_duration_h': bess_duration,
                                    'bess_capacity_mwh': bess_power * bess_duration,
                                    'strategy': strategy,
                                    'config_id': config_count
                                }
                                
                                # Progress indicator
                                if config_count % 50 == 0:
                                    elapsed = (datetime.now() - start_time).total_seconds()
                                    progress = config_count / total_configs * 100
                                    print(f"\nProgress: {config_count}/{total_configs} ({progress:.1f}%) - {elapsed:.1f}s elapsed")
                                
                                try:
                                    # Run simulation
                                    result = dm.simulate_solar_with_bess(
                                        station=station,
                                        solar_mw=solar_mw,
                                        bess_power_mw=bess_power,
                                        bess_duration_h=bess_duration,
                                        strategy=strategy,
                                        solar_technology=solar_tech
                                    )
                                    
                                    if result['available']:
                                        metrics = result['annual_metrics']
                                        validation = metrics['validation']
                                        
                                        # Store results
                                        results.append({
                                            **config,
                                            'solar_energy_mwh': metrics['solar_energy_mwh'],
                                            'delivered_energy_mwh': metrics['delivered_energy_mwh'],
                                            'losses_mwh': metrics['losses_mwh'],
                                            'curtailed_mwh': metrics['curtailed_mwh'],
                                            'efficiency': validation['efficiency'],
                                            'valid': validation['valid'],
                                            'bess_cycles': metrics.get('bess_cycles', 0),
                                            'utilization': metrics.get('utilization', 0),
                                            'success': True
                                        })
                                        
                                        # Check for anomalies
                                        if validation['efficiency'] < 0.85:
                                            print(f"\n⚠️  Low efficiency: {config} -> {validation['efficiency']:.1%}")
                                        
                                        if not validation['valid']:
                                            print(f"\n❌ Invalid config: {config}")
                                            
                                    else:
                                        errors.append({
                                            **config,
                                            'error': 'Simulation not available',
                                            'success': False
                                        })
                                        
                                except Exception as e:
                                    errors.append({
                                        **config,
                                        'error': str(e),
                                        'success': False
                                    })
                                    print(f"\n❌ Error in config {config_count}: {e}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    
    # Summary statistics
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total configurations tested: {config_count}")
    print(f"Successful simulations: {len(results)}")
    print(f"Failed simulations: {len(errors)}")
    print(f"Success rate: {len(results)/config_count*100:.1f}%")
    print(f"Total time: {duration:.1f} seconds")
    print(f"Average time per config: {duration/config_count:.3f} seconds")
    
    # Save results
    if results:
        df_results = pd.DataFrame(results)
        
        # Analysis by station
        print("\n" + "-" * 60)
        print("RESULTS BY STATION")
        print("-" * 60)
        for station in stations:
            station_data = df_results[df_results['station'] == station]
            if not station_data.empty:
                print(f"\n{station}:")
                print(f"  Configurations: {len(station_data)}")
                print(f"  Avg efficiency: {station_data['efficiency'].mean():.1%}")
                print(f"  Valid configs: {station_data['valid'].sum()} ({station_data['valid'].mean()*100:.1f}%)")
                print(f"  Avg delivered: {station_data['delivered_energy_mwh'].mean():.0f} MWh/year")
        
        # Analysis by strategy
        print("\n" + "-" * 60)
        print("RESULTS BY STRATEGY")
        print("-" * 60)
        for strategy in strategies:
            strategy_data = df_results[df_results['strategy'] == strategy]
            if not strategy_data.empty:
                print(f"\n{strategy}:")
                print(f"  Configurations: {len(strategy_data)}")
                print(f"  Avg efficiency: {strategy_data['efficiency'].mean():.1%}")
                print(f"  Avg curtailed: {strategy_data['curtailed_mwh'].mean():.0f} MWh/year")
                print(f"  Avg cycles: {strategy_data['bess_cycles'].mean():.0f} cycles/year")
        
        # Best configurations
        print("\n" + "-" * 60)
        print("TOP 10 CONFIGURATIONS BY EFFICIENCY")
        print("-" * 60)
        top_configs = df_results.nlargest(10, 'efficiency')[
            ['station', 'solar_mw', 'bess_power_mw', 'bess_duration_h', 
             'strategy', 'efficiency', 'delivered_energy_mwh']
        ]
        print(top_configs.to_string(index=False))
        
        # Save to files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f'test_results/matrix_results_{timestamp}.csv'
        summary_file = f'test_results/matrix_summary_{timestamp}.json'
        
        # Create directory if needed
        os.makedirs('test_results', exist_ok=True)
        
        # Save detailed results
        df_results.to_csv(results_file, index=False)
        print(f"\n✅ Detailed results saved to: {results_file}")
        
        # Save summary
        summary = {
            'test_date': timestamp,
            'total_configs': config_count,
            'successful': len(results),
            'failed': len(errors),
            'duration_seconds': duration,
            'stations_tested': stations,
            'solar_sizes_mw': solar_sizes,
            'bess_powers_mw': bess_powers,
            'bess_durations_h': bess_durations,
            'strategies': strategies,
            'technologies': solar_technologies,
            'avg_efficiency': float(df_results['efficiency'].mean()),
            'valid_rate': float(df_results['valid'].mean()),
            'errors': errors[:10]  # First 10 errors only
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Summary saved to: {summary_file}")
    
    # Show errors if any
    if errors:
        print("\n" + "-" * 60)
        print(f"ERRORS ({len(errors)} total, showing first 5)")
        print("-" * 60)
        for error in errors[:5]:
            print(f"\nConfig: {error['config_id']}")
            print(f"  Station: {error['station']}")
            print(f"  Solar: {error['solar_mw']} MW")
            print(f"  BESS: {error['bess_power_mw']} MW x {error['bess_duration_h']}h")
            print(f"  Error: {error['error']}")
    
    print("\n" + "=" * 80)
    print("Configuration matrix test completed!")
    print("=" * 80)
    
    return results, errors


if __name__ == "__main__":
    results, errors = run_configuration_matrix()