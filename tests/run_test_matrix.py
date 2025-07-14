#!/usr/bin/env python3
"""
Run comprehensive test matrix for PSFV+BESS configurations
Generates detailed audit report
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from itertools import product

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dashboard.pages.utils import DataManager


def run_configuration_matrix():
    """Run full matrix of PSFV+BESS configurations and generate report"""
    
    # Initialize DataManager
    dm = DataManager()
    
    # Define test matrix
    stations = ['MAQUINCHAO', 'LOS MENUCOS', 'JACOBACCI']
    psfv_sizes = [0.5, 1.0, 2.0, 5.0]  # MW
    bess_powers = [0.5, 1.0, 2.0]  # MW
    bess_durations = [1, 2, 4, 6]  # hours
    strategies = ['cap_shaving', 'flat_day', 'night_shift', 'ramp_limit']
    
    # Results storage
    results = []
    errors = []
    
    # Total configurations
    total_configs = len(stations) * len(psfv_sizes) * len(bess_powers) * len(bess_durations) * len(strategies)
    print(f"Running {total_configs} configurations...")
    print("="*60)
    
    config_count = 0
    
    # Run each configuration
    for station, psfv, bess_p, bess_d, strategy in product(
        stations, psfv_sizes, bess_powers, bess_durations, strategies
    ):
        config_count += 1
        
        # Skip if BESS power > PSFV (not typical)
        if bess_p > psfv * 0.8:
            continue
            
        config_str = f"{station}: {psfv}MW PSFV + {bess_p}MW/{bess_d}h BESS - {strategy}"
        print(f"[{config_count}/{total_configs}] Testing {config_str}", end="... ")
        
        try:
            # Run simulation
            result = dm.simulate_solar_with_bess(
                station=station,
                solar_mw=psfv,
                bess_power_mw=bess_p,
                bess_duration_h=bess_d,
                strategy=strategy,
                solar_technology='SAT Bifacial'
            )
            
            if result['available']:
                metrics = result['annual_metrics']
                validation = metrics['validation']
                
                # Extract key metrics
                results.append({
                    'station': station,
                    'psfv_mw': psfv,
                    'bess_power_mw': bess_p,
                    'bess_duration_h': bess_d,
                    'bess_capacity_mwh': bess_p * bess_d,
                    'strategy': strategy,
                    'solar_energy_mwh_annual': metrics['solar_energy_mwh'],
                    'delivered_energy_mwh_annual': metrics['delivered_energy_mwh'],
                    'losses_mwh_annual': metrics['losses_mwh'],
                    'curtailed_mwh_annual': metrics['curtailed_mwh'],
                    'efficiency_percent': validation['efficiency'] * 100,
                    'validation_passed': validation['valid'],
                    'daily_solar_mwh': metrics['solar_energy_mwh'] / 365,
                    'daily_delivered_mwh': metrics['delivered_energy_mwh'] / 365,
                    'daily_losses_mwh': metrics['losses_mwh'] / 365,
                    'bess_utilization': validation.get('strategy_metrics', {}).get('bess_utilization', 0)
                })
                
                status = "✓ PASS" if validation['valid'] else "✗ FAIL"
                print(f"{status} (η={validation['efficiency']:.1%})")
            else:
                errors.append({
                    'config': config_str,
                    'error': result.get('error', 'Unknown error')
                })
                print("✗ ERROR")
                
        except Exception as e:
            errors.append({
                'config': config_str,
                'error': str(e)
            })
            print(f"✗ EXCEPTION: {str(e)[:50]}")
    
    # Create results DataFrame
    df = pd.DataFrame(results)
    
    # Generate report
    print("\n" + "="*60)
    print("TEST MATRIX SUMMARY")
    print("="*60)
    
    if len(df) > 0:
        # Overall statistics
        print(f"\nTotal configurations tested: {len(df)}")
        print(f"Configurations passed: {df['validation_passed'].sum()} ({df['validation_passed'].mean()*100:.1f}%)")
        print(f"Configurations failed: {(~df['validation_passed']).sum()}")
        print(f"Errors encountered: {len(errors)}")
        
        # Efficiency statistics by strategy
        print("\nEFFICIENCY BY STRATEGY:")
        print("-"*40)
        efficiency_by_strategy = df.groupby('strategy')['efficiency_percent'].agg(['mean', 'std', 'min', 'max'])
        print(efficiency_by_strategy)
        
        # Best configurations per station
        print("\nBEST CONFIGURATIONS PER STATION:")
        print("-"*40)
        for station in stations:
            station_data = df[df['station'] == station]
            if len(station_data) > 0:
                best = station_data.loc[station_data['efficiency_percent'].idxmax()]
                print(f"\n{station}:")
                print(f"  PSFV: {best['psfv_mw']} MW")
                print(f"  BESS: {best['bess_power_mw']} MW / {best['bess_duration_h']}h")
                print(f"  Strategy: {best['strategy']}")
                print(f"  Efficiency: {best['efficiency_percent']:.1f}%")
                print(f"  Daily delivery: {best['daily_delivered_mwh']:.1f} MWh/day")
        
        # Energy conservation check
        print("\nENERGY CONSERVATION CHECK:")
        print("-"*40)
        df['energy_balance'] = df['delivered_energy_mwh_annual'] + df['losses_mwh_annual'] + df['curtailed_mwh_annual']
        df['conservation_error'] = abs(df['solar_energy_mwh_annual'] - df['energy_balance']) / df['solar_energy_mwh_annual'] * 100
        
        print(f"Max conservation error: {df['conservation_error'].max():.3f}%")
        print(f"Mean conservation error: {df['conservation_error'].mean():.3f}%")
        
        violations = df[df['conservation_error'] > 0.1]
        if len(violations) > 0:
            print(f"⚠️  {len(violations)} configurations violate energy conservation!")
        else:
            print("✓ All configurations pass energy conservation")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"tests/test_matrix_results_{timestamp}.csv"
        df.to_csv(results_file, index=False)
        print(f"\nDetailed results saved to: {results_file}")
        
        # Save summary report
        report = {
            'timestamp': timestamp,
            'total_configurations': len(df),
            'passed': int(df['validation_passed'].sum()),
            'failed': int((~df['validation_passed']).sum()),
            'errors': len(errors),
            'efficiency_by_strategy': efficiency_by_strategy.to_dict(),
            'error_details': errors
        }
        
        report_file = f"tests/test_matrix_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Summary report saved to: {report_file}")
        
    else:
        print("No successful configurations!")
        
    # Print errors if any
    if errors:
        print("\nERRORS ENCOUNTERED:")
        print("-"*40)
        for err in errors[:5]:  # Show first 5 errors
            print(f"Config: {err['config']}")
            print(f"Error: {err['error']}")
            print()
            
    return df, errors


if __name__ == "__main__":
    print("PSFV+BESS Configuration Matrix Test")
    print("="*60)
    
    df, errors = run_configuration_matrix()
    
    print("\nTest matrix complete!")
    
    # Return exit code based on results
    if len(df) > 0 and df['validation_passed'].mean() > 0.9:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure