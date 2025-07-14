#!/usr/bin/env python3
"""
Test matrix for PSFV+BESS configurations using V2 strategies
Verifica que ahora sí se registran ciclos y pérdidas reales
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from dashboard.pages.utils.data_manager import DataManager
import json

def main():
    """Run a reduced test matrix with V2 strategies"""
    start_time = datetime.now()
    print("="*60)
    print(f"PSFV+BESS Configuration Matrix Test V2")
    print(f"Start: {start_time}")
    print("="*60)
    
    # Initialize data manager
    dm = DataManager()
    
    # Test parameters (reduced for quick testing)
    stations = ['MAQUINCHAO']  # Just one station
    solar_sizes = [1.0, 2.0]  # 2 sizes
    bess_powers = [0.5, 1.0]  # 2 powers
    bess_durations = [2, 4]  # 2 durations
    strategies_v1 = ['cap_shaving', 'night_shift']  # 2 V1 strategies
    strategies_v2 = ['solar_smoothing', 'time_shift_aggressive']  # 2 V2 strategies
    technologies = ['SAT Bifacial']  # Just bifacial
    
    # Combine strategies
    all_strategies = strategies_v1 + strategies_v2
    
    # Calculate total configurations
    total_configs = (len(stations) * len(solar_sizes) * len(bess_powers) * 
                    len(bess_durations) * len(all_strategies) * len(technologies))
    
    print(f"\nConfiguration Matrix:")
    print(f"- Stations: {len(stations)}")
    print(f"- Solar sizes: {len(solar_sizes)} MW")
    print(f"- BESS powers: {len(bess_powers)} MW")
    print(f"- BESS durations: {len(bess_durations)} h")
    print(f"- Strategies V1: {len(strategies_v1)}")
    print(f"- Strategies V2: {len(strategies_v2)}")
    print(f"- Technologies: {len(technologies)}")
    print(f"- Total configurations: {total_configs}")
    
    # Results storage
    results = []
    config_id = 0
    
    # Run configurations
    print("\nRunning simulations...")
    for station in stations:
        for solar_mw in solar_sizes:
            for technology in technologies:
                for bess_power in bess_powers:
                    for bess_duration in bess_durations:
                        # Skip unrealistic configs
                        if bess_power > solar_mw * 2:
                            continue
                            
                        bess_capacity = bess_power * bess_duration
                        
                        for strategy in all_strategies:
                            config_id += 1
                            
                            try:
                                # Determine strategy type
                                strategy_type = 'V2' if strategy in strategies_v2 else 'V1'
                                
                                # Run simulation
                                result = dm.simulate_solar_with_bess(
                                    station=station,
                                    solar_mw=solar_mw,
                                    technology=technology,
                                    bess_power_mw=bess_power,
                                    bess_duration_h=bess_duration,
                                    strategy=strategy
                                )
                                
                                # Check if simulation was successful
                                if not result.get('available', False):
                                    raise Exception(result.get('error', 'Unknown error'))
                                
                                # Extract metrics
                                metrics = result['annual_metrics']
                                
                                # Store result
                                results.append({
                                    'config_id': config_id,
                                    'station': station,
                                    'solar_mw': solar_mw,
                                    'technology': technology,
                                    'bess_power_mw': bess_power,
                                    'bess_duration_h': bess_duration,
                                    'bess_capacity_mwh': bess_capacity,
                                    'strategy': strategy,
                                    'strategy_type': strategy_type,
                                    'solar_energy_mwh': metrics['solar_generated_mwh'],
                                    'delivered_energy_mwh': metrics['energy_delivered_mwh'],
                                    'losses_mwh': metrics['bess_losses_mwh'],
                                    'curtailed_mwh': metrics['solar_curtailed_mwh'],
                                    'efficiency': metrics['system_efficiency'],
                                    'bess_cycles': metrics.get('bess_cycles_annual', 0),
                                    'utilization': metrics.get('bess_utilization', 0),
                                    'valid': True,  # Assume valid if simulation completed
                                    'success': True
                                })
                                
                                # Progress indicator
                                if config_id % 10 == 0:
                                    print(f"  Completed {config_id}/{total_configs} configurations...")
                                    
                            except Exception as e:
                                print(f"  Error in config {config_id}: {str(e)}")
                                results.append({
                                    'config_id': config_id,
                                    'station': station,
                                    'solar_mw': solar_mw,
                                    'technology': technology,
                                    'bess_power_mw': bess_power,
                                    'bess_duration_h': bess_duration,
                                    'bess_capacity_mwh': bess_capacity,
                                    'strategy': strategy,
                                    'strategy_type': strategy_type,
                                    'success': False,
                                    'error': str(e)
                                })
    
    # Create results DataFrame
    df = pd.DataFrame(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'test_results/matrix_v2_results_{timestamp}.csv'
    df.to_csv(results_file, index=False)
    
    # Analysis
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    successful = df[df['success'] == True]
    print(f"\nTotal configurations run: {len(df)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(df)*100:.1f}%)")
    
    if len(successful) > 0:
        # Compare V1 vs V2 strategies
        print("\n--- Strategy Comparison ---")
        strategy_summary = successful.groupby('strategy_type').agg({
            'bess_cycles': ['mean', 'min', 'max'],
            'losses_mwh': 'mean',
            'efficiency': 'mean',
            'utilization': 'mean'
        }).round(2)
        
        print("\nCycles by Strategy Type:")
        print(strategy_summary['bess_cycles'])
        
        print("\nAverage Metrics by Strategy Type:")
        print(f"{'Type':<5} {'Losses(MWh)':<12} {'Efficiency':<10} {'Utilization':<10}")
        print("-"*40)
        for idx in strategy_summary.index:
            losses = strategy_summary.loc[idx, ('losses_mwh', 'mean')]
            eff = strategy_summary.loc[idx, ('efficiency', 'mean')]
            util = strategy_summary.loc[idx, ('utilization', 'mean')]
            print(f"{idx:<5} {losses:<12.2f} {eff:<10.1%} {util:<10.1%}")
        
        # Detailed by strategy
        print("\n--- Detailed by Strategy ---")
        strategy_detail = successful.groupby('strategy').agg({
            'bess_cycles': 'mean',
            'losses_mwh': 'mean',
            'efficiency': 'mean',
            'utilization': 'mean'
        }).round(2)
        
        print(f"\n{'Strategy':<25} {'Cycles':<8} {'Losses':<10} {'Efficiency':<10} {'Utilization'}")
        print("-"*70)
        for strategy in strategy_detail.index:
            cycles = strategy_detail.loc[strategy, 'bess_cycles']
            losses = strategy_detail.loc[strategy, 'losses_mwh']
            eff = strategy_detail.loc[strategy, 'efficiency']
            util = strategy_detail.loc[strategy, 'utilization']
            s_type = 'V2' if strategy in strategies_v2 else 'V1'
            print(f"{strategy:<25} {cycles:<8.2f} {losses:<10.2f} {eff:<10.1%} {util:<10.1%} ({s_type})")
        
        # Check if V2 strategies have cycles
        v2_results = successful[successful['strategy_type'] == 'V2']
        if len(v2_results) > 0:
            v2_with_cycles = len(v2_results[v2_results['bess_cycles'] > 0.1])
            print(f"\n✓ V2 strategies with cycles: {v2_with_cycles}/{len(v2_results)} "
                  f"({v2_with_cycles/len(v2_results)*100:.0f}%)")
            
            avg_cycles_v1 = successful[successful['strategy_type'] == 'V1']['bess_cycles'].mean()
            avg_cycles_v2 = successful[successful['strategy_type'] == 'V2']['bess_cycles'].mean()
            
            if avg_cycles_v2 > avg_cycles_v1:
                print(f"✓ V2 strategies show {avg_cycles_v2/avg_cycles_v1:.1f}x more cycles than V1")
            else:
                print(f"⚠️  V2 strategies still showing low cycles: {avg_cycles_v2:.2f}")
    
    # Save summary report
    report_file = f'test_results/MATRIX_V2_REPORT_{timestamp}.md'
    with open(report_file, 'w') as f:
        f.write(f"# Test Results - PSFV+BESS V2 Strategies\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Summary\n")
        f.write(f"- Total configurations: {len(df)}\n")
        f.write(f"- Successful: {len(successful)}\n")
        f.write(f"- Data file: {results_file}\n\n")
        
        if len(successful) > 0:
            f.write("## Key Finding\n")
            if avg_cycles_v2 > 0.5:
                f.write(f"✅ **SUCCESS**: V2 strategies now show real BESS usage with average "
                       f"{avg_cycles_v2:.1f} cycles/year vs {avg_cycles_v1:.1f} for V1 strategies.\n")
            else:
                f.write(f"⚠️  **WARNING**: V2 strategies still show low cycles ({avg_cycles_v2:.2f})\n")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\nExecution time: {duration:.1f} seconds")
    print(f"Results saved to: {results_file}")
    print(f"Report saved to: {report_file}")
    
    print("\n✓ Matrix test V2 completed successfully!")


if __name__ == "__main__":
    main()