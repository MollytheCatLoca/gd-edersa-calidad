#!/usr/bin/env python3
"""
Test script for BESS integration in DataManager
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.pages.utils.data_manager import DataManager
import matplotlib.pyplot as plt
import pandas as pd

def test_bess_integration():
    """Test the new BESS functions in DataManager"""
    
    print("="*70)
    print("TESTING BESS INTEGRATION IN DATAMANAGER")
    print("="*70)
    
    # Initialize DataManager
    dm = DataManager()
    
    # Test 1: Solar+BESS profile simulation
    print("\n1. TESTING SOLAR+BESS OPERATION")
    print("-"*50)
    
    result = dm.get_solar_bess_profile(
        station='Maquinchao',
        solar_mw=10.0,
        bess_power_mw=3.0,
        bess_duration_h=4.0,
        strategy='smoothing'
    )
    
    if result['available']:
        print(f"Station: {result['station']}")
        print(f"Solar: {result['solar_capacity_mw']} MW")
        print(f"BESS: {result['bess_power_mw']} MW / {result['bess_duration_h']}h = {result['bess_capacity_mwh']} MWh")
        print(f"Strategy: {result['strategy']}")
        
        print("\nAnnual Metrics:")
        metrics = result['annual_metrics']
        print(f"  Solar Energy: {metrics['solar_energy_mwh']:.0f} MWh")
        print(f"  Grid Energy: {metrics['grid_energy_mwh']:.0f} MWh")
        print(f"  BESS Losses: {metrics['battery_losses_mwh']:.0f} MWh")
        print(f"  Efficiency: {metrics['efficiency_percent']:.1f}%")
        print(f"  Variability Reduction: {metrics['variability_reduction_percent']:.1f}%")
        print(f"  Battery Utilization: {metrics['battery_utilization_percent']:.1f}%")
        print(f"  Annual Cycles: {metrics['cycles']:.0f}")
        
        # Plot typical day
        typical_day = result['typical_day_profiles']['average']
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        hours = typical_day['hour']
        ax1.plot(hours, typical_day['solar_mw'], 'gold', linewidth=2, label='Solar')
        ax1.plot(hours, typical_day['grid_mw'], 'blue', linewidth=2, label='Grid Delivery')
        ax1.fill_between(hours, 0, typical_day['solar_mw'], alpha=0.3, color='gold')
        ax1.set_ylabel('Power (MW)')
        ax1.set_title('Typical Day - Solar vs Grid Delivery')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        ax2.bar(hours, typical_day['battery_mw'], color=['red' if p < 0 else 'green' for p in typical_day['battery_mw']])
        ax2_twin = ax2.twinx()
        ax2_twin.plot(hours, typical_day['soc_percent'], 'k--', linewidth=2, label='SOC')
        ax2.set_xlabel('Hour')
        ax2.set_ylabel('Battery Power (MW)', color='black')
        ax2_twin.set_ylabel('SOC (%)', color='black')
        ax2.set_title('BESS Operation')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linewidth=0.5)
        
        plt.tight_layout()
        plt.savefig('reports/figures/bess_typical_day.png', dpi=150)
        plt.close()
        
    # Test 2: BESS optimization
    print("\n\n2. TESTING BESS OPTIMIZATION")
    print("-"*50)
    
    opt_result = dm.optimize_bess_for_solar(
        station='Maquinchao',
        solar_mw=10.0,
        objective='minimize_variability',
        strategy='smoothing'
    )
    
    if opt_result['available']:
        print(f"\nOptimization for {opt_result['solar_capacity_mw']} MW Solar")
        print(f"Objective: {opt_result['objective']}")
        print(f"Strategy: {opt_result['strategy']}")
        
        print("\nRecommended Configuration:")
        rec = opt_result['recommended_config']
        print(f"  Power: {rec['power_mw']:.1f} MW")
        print(f"  Duration: {rec['duration_h']:.0f} hours")
        print(f"  Capacity: {rec['capacity_mwh']:.1f} MWh")
        print(f"  C-rate: {rec['power_mw']/rec['capacity_mwh']:.2f}")
        
        print("\nExpected Performance:")
        metrics = rec['metrics']
        print(f"  Variability Reduction: {metrics['variability_reduction']:.1f}%")
        print(f"  Battery Utilization: {metrics['utilization']:.1f}%")
        print(f"  System Efficiency: {metrics['efficiency']:.1f}%")
        print(f"  Annual Cycles: {metrics['annual_cycles']:.0f}")
        
        print("\nTop 5 Configurations:")
        print(f"{'Power':>6} {'Duration':>8} {'Capacity':>8} {'Var.Red':>8} {'Util':>6}")
        print("-"*42)
        for config in opt_result['top_configurations'][:5]:
            print(f"{config['power_mw']:>6.1f} {config['duration_h']:>8.0f} "
                  f"{config['capacity_mwh']:>8.1f} {config['variability_reduction_percent']:>8.1f} "
                  f"{config['battery_utilization_percent']:>6.1f}")
        
        # Plot optimization results
        df = pd.DataFrame(opt_result['all_results'])
        
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # Create scatter plot with color based on variability reduction
        scatter = ax.scatter(df['capacity_mwh'], df['variability_reduction_percent'],
                           c=df['battery_utilization_percent'], 
                           s=100, cmap='viridis', alpha=0.6, edgecolors='black')
        
        # Highlight recommended
        rec_row = df[df['score'] == df['score'].max()].iloc[0]
        ax.scatter(rec_row['capacity_mwh'], rec_row['variability_reduction_percent'],
                  s=200, marker='*', color='red', edgecolors='black', linewidth=2,
                  label='Recommended')
        
        ax.set_xlabel('BESS Capacity (MWh)')
        ax.set_ylabel('Variability Reduction (%)')
        ax.set_title('BESS Sizing Optimization Results')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Battery Utilization (%)')
        
        plt.tight_layout()
        plt.savefig('reports/figures/bess_optimization.png', dpi=150)
        plt.close()
    
    # Test 3: Different strategies comparison
    print("\n\n3. COMPARING BESS STRATEGIES")
    print("-"*50)
    
    strategies = ['smoothing', 'peak_limit', 'time_shift', 'firm_capacity']
    
    print(f"{'Strategy':<15} {'Var.Red%':>10} {'Util%':>10} {'Eff%':>10} {'Cycles':>10}")
    print("-"*55)
    
    for strategy in strategies:
        try:
            result = dm.get_solar_bess_profile(
                station='Maquinchao',
                solar_mw=10.0,
                bess_power_mw=3.0,
                bess_duration_h=4.0,
                strategy=strategy
            )
            
            if result['available']:
                metrics = result['annual_metrics']
                print(f"{strategy:<15} {metrics['variability_reduction_percent']:>10.1f} "
                      f"{metrics['battery_utilization_percent']:>10.1f} "
                      f"{metrics['efficiency_percent']:>10.1f} "
                      f"{metrics['cycles']:>10.0f}")
        except:
            print(f"{strategy:<15} {'Error':>10}")
    
    print("\n" + "="*70)
    print("BESS INTEGRATION TESTS COMPLETED")
    print("="*70)
    print("\nGenerated files:")
    print("- reports/figures/bess_typical_day.png")
    print("- reports/figures/bess_optimization.png")

if __name__ == "__main__":
    test_bess_integration()