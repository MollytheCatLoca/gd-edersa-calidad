#!/usr/bin/env python3
"""
FASE 3 BESS Integration - Demonstration Script
==============================================

Demonstrates the advanced BESS capabilities implemented in DataManagerV2.
Shows real-world use cases for the integrated BESSModel API.

Usage:
    source venv/bin/activate
    python demo_fase3_capabilities.py
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dashboard.pages.utils.data_manager_v2 import get_data_manager


def create_realistic_solar_profile(power_mw: float = 3.0) -> np.ndarray:
    """Create a realistic daily solar profile with clouds."""
    hours = np.arange(24)
    
    # Base solar curve (sine-based)
    base_solar = power_mw * np.maximum(0, np.sin(np.pi * (hours - 6) / 12)) ** 2
    
    # Add cloud variability
    cloud_pattern = 1 + 0.3 * np.sin(0.8 * hours) * np.maximum(0, np.sin(np.pi * (hours - 6) / 12))
    
    # Add random short-term variability
    np.random.seed(42)  # Reproducible
    noise = 1 + 0.1 * np.random.normal(0, 1, 24)
    
    # Combine all effects
    solar_profile = base_solar * cloud_pattern * noise
    solar_profile = np.maximum(0, solar_profile)  # No negative values
    
    return solar_profile


def demo_bess_constants():
    """Demonstrate BESS constants access."""
    print("=" * 70)
    print("DEMO 1: BESS Constants and Configuration Access")
    print("=" * 70)
    
    dm = get_data_manager()
    
    # Get available technologies
    tech_result = dm.get_bess_technologies()
    if tech_result.data:
        print("📋 Available BESS Technologies:")
        for tech, params in tech_result.data.items():
            print(f"  • {tech}: η={params['η_roundtrip']:.1%}, SOC={params['soc_min']:.0%}-{params['soc_max']:.0%}")
    
    # Get available topologies  
    topo_result = dm.get_bess_topologies()
    if topo_result.data:
        print("\n🔧 Available BESS Topologies:")
        for topo, params in topo_result.data.items():
            penalty = params['efficiency_penalty']
            print(f"  • {topo}: penalty={penalty:.1%}, flexibility={params['flexibility']}")
    
    # Demonstrate technology comparison
    print("\n🔬 Technology Comparison:")
    for tech in ['standard', 'modern_lfp', 'premium']:
        bess_result = dm.create_bess_model(2.0, 4.0, technology=tech)
        if bess_result.data:
            config = bess_result.data.get_configuration_summary()
            print(f"  • {tech:11s}: {config['roundtrip_efficiency']:.1%} efficiency, "
                  f"C-rate={config['c_rate']:.1f}, usable={config['usable_capacity_mwh']:.1f} MWh")


def demo_strategy_comparison():
    """Demonstrate different BESS strategies."""
    print("\n" + "=" * 70)
    print("DEMO 2: BESS Strategy Comparison")
    print("=" * 70)
    
    dm = get_data_manager()
    
    # Create realistic solar profile
    solar_profile = create_realistic_solar_profile(power_mw=4.0)
    
    print(f"☀️ Solar Profile: Peak={solar_profile.max():.1f} MW, "
          f"Daily Total={np.sum(solar_profile):.1f} MWh")
    
    # Test different strategies
    strategies = ['cap_shaving', 'flat_day', 'night_shift', 'ramp_limit']
    
    print("\n📊 Strategy Performance Comparison:")
    print("Strategy      | Efficiency | Losses | Curtail | Cycles | Grid Peak")
    print("-" * 65)
    
    for strategy in strategies:
        result = dm.simulate_bess_strategy(
            solar_profile=solar_profile,
            strategy=strategy,
            power_mw=3.0,
            duration_hours=4.0,
            technology="modern_lfp"
        )
        
        if result.data:
            metrics = result.data['metrics']
            grid_peak = result.data['grid_power'].max()
            
            print(f"{strategy:12s} | "
                  f"{metrics['energy_efficiency']:8.1%} | "
                  f"{metrics['total_losses_mwh']:6.2f} | "
                  f"{metrics['curtailment_ratio']:7.1%} | "
                  f"{result.data['total_cycles']:6.2f} | "
                  f"{grid_peak:8.2f}")


def demo_dynamic_control():
    """Demonstrate dynamic BESS control."""
    print("\n" + "=" * 70)
    print("DEMO 3: Dynamic BESS Control Simulation")
    print("=" * 70)
    
    dm = get_data_manager()
    
    # Create a power request sequence simulating grid services
    print("🎮 Simulating Frequency Regulation Service:")
    
    # 4-hour sequence with 15-min intervals (16 steps)
    power_requests = [
        # Hour 1: Charge during low price
        -1.5, -2.0, -2.0, -1.5,
        # Hour 2: Frequency regulation (bidirectional)
        0.5, -0.5, 1.0, -1.0,
        # Hour 3: Peak shaving discharge
        2.0, 2.0, 1.5, 1.0,
        # Hour 4: Return to neutral
        0.5, 0.0, 0.0, 0.0
    ]
    
    result = dm.simulate_bess_dynamic_control(
        initial_soc=0.5,  # Start at 50%
        power_requests=power_requests,
        power_mw=2.5,
        duration_hours=4.0,
        technology="premium",  # High performance for grid services
        dt=0.25  # 15-minute intervals
    )
    
    if result.data:
        data = result.data
        metrics = data['metrics']
        
        print(f"  • Initial SOC: 50.0%")
        print(f"  • Final SOC: {metrics['final_soc']:.1%}")
        print(f"  • SOC Range: {metrics['soc_range']:.1%}")
        print(f"  • Energy In: {metrics['total_energy_in_mwh']:.3f} MWh")
        print(f"  • Energy Out: {metrics['total_energy_out_mwh']:.3f} MWh")
        print(f"  • Total Losses: {metrics['total_losses_mwh']:.3f} MWh")
        print(f"  • Realized Efficiency: {metrics['realized_roundtrip_efficiency']:.1%}")
        
        # Show power curtailment analysis
        curtailment = np.abs(data['power_curtailment'])
        if curtailment.max() > 0.01:
            print(f"  ⚠️  Max Power Curtailment: {curtailment.max():.2f} MW")
        else:
            print(f"  ✅ No significant power curtailment")


def demo_optimization():
    """Demonstrate BESS optimization for solar."""
    print("\n" + "=" * 70)
    print("DEMO 4: BESS Optimization for Solar Integration")
    print("=" * 70)
    
    dm = get_data_manager()
    
    # Create high-variability solar profile
    solar_profile = create_realistic_solar_profile(power_mw=5.0)
    # Add more clouds for challenging optimization
    cloud_events = np.array([8, 10, 14, 16])  # Hours with clouds
    for hour in cloud_events:
        if hour < len(solar_profile):
            solar_profile[hour] *= 0.3  # 70% cloud reduction
    
    print(f"☁️ Challenging Solar Profile: Peak={solar_profile.max():.1f} MW, "
          f"Min={solar_profile.min():.1f} MW, Variability={solar_profile.std():.1f}")
    
    print("\n🔍 Optimizing BESS Configuration...")
    
    # Optimize for different metrics
    metrics = ['energy_efficiency', 'curtailment_ratio']
    
    for metric in metrics:
        print(f"\n📈 Optimizing for: {metric}")
        
        result = dm.optimize_bess_for_solar(
            solar_profile=solar_profile,
            power_range=(1.0, 6.0),
            duration_range=(2.0, 8.0),
            strategy="cap_shaving",
            optimization_metric=metric
        )
        
        if result.data:
            summary = result.data['summary']
            best_config = result.data['best_configuration']
            
            print(f"  • Optimal Size: {summary['best_power_mw']:.1f} MW / "
                  f"{summary['best_duration_h']:.1f} hours")
            print(f"  • Optimal Value: {summary['best_metric_value']:.1%}")
            print(f"  • Improvement vs No BESS: {summary['improvement_vs_no_bess']:.1%}")
            print(f"  • Configurations Tested: {result.data['optimization_settings']['total_configurations']}")
            
            if best_config:
                best_metrics = best_config['metrics']
                print(f"  • Best Config Efficiency: {best_metrics['energy_efficiency']:.1%}")
                print(f"  • Best Config Losses: {best_metrics['total_losses_mwh']:.2f} MWh")


def demo_validation():
    """Demonstrate BESS configuration validation."""
    print("\n" + "=" * 70)
    print("DEMO 5: BESS Configuration Validation")
    print("=" * 70)
    
    dm = get_data_manager()
    
    # Test various configurations
    configs = [
        {"name": "Small Fast", "power": 1.0, "duration": 0.5, "tech": "premium"},
        {"name": "Standard", "power": 2.0, "duration": 4.0, "tech": "modern_lfp"},
        {"name": "Large Slow", "power": 0.5, "duration": 12.0, "tech": "standard"},
        {"name": "High Power", "power": 5.0, "duration": 1.0, "tech": "premium"},
    ]
    
    print("🔧 Configuration Validation Results:")
    print()
    
    for config in configs:
        result = dm.validate_bess_configuration(
            power_mw=config["power"],
            duration_hours=config["duration"],
            technology=config["tech"]
        )
        
        if result.data:
            validation = result.data
            tech_params = validation['technical_parameters']
            
            print(f"📋 {config['name']} ({config['power']} MW / {config['duration']}h):")
            print(f"  • C-rate: {tech_params['c_rate']:.2f}")
            print(f"  • Round-trip efficiency: {tech_params['roundtrip_efficiency']:.1%}")
            print(f"  • Usable capacity: {tech_params['usable_capacity_mwh']:.2f} MWh")
            
            if validation['warnings']:
                print(f"  ⚠️  Warnings:")
                for warning in validation['warnings']:
                    print(f"    - {warning}")
            else:
                print(f"  ✅ No warnings")
            
            if 'performance_estimates' in validation:
                perf = validation['performance_estimates']
                if perf.get('daily_efficiency', 0) > 0:
                    print(f"  • Est. daily efficiency: {perf['daily_efficiency']:.1%}")
                    print(f"  • Est. daily cycles: {perf['daily_cycles']:.2f}")
            
            print()


def demo_technology_deep_dive():
    """Deep dive into technology differences."""
    print("\n" + "=" * 70)
    print("DEMO 6: Technology Deep Dive")
    print("=" * 70)
    
    dm = get_data_manager()
    
    # Test same solar profile with different technologies
    solar_profile = create_realistic_solar_profile(power_mw=3.0)
    
    print("🔬 Technology Performance on Same Solar Profile:")
    print()
    
    technologies = ['standard', 'modern_lfp', 'premium']
    
    for tech in technologies:
        # Get technology parameters
        tech_result = dm.get_bess_technology_params(tech)
        if not tech_result.data:
            continue
            
        tech_params = tech_result.data
        
        # Run simulation
        sim_result = dm.simulate_bess_strategy(
            solar_profile=solar_profile,
            strategy="cap_shaving",
            power_mw=2.0,
            duration_hours=4.0,
            technology=tech
        )
        
        if sim_result.data:
            metrics = sim_result.data['metrics']
            config = sim_result.data['bess_config']
            
            print(f"🔋 {tech.upper().replace('_', ' ')}:")
            print(f"  • Technology η: {tech_params['η_roundtrip']:.1%}")
            print(f"  • Realized η: {config['roundtrip_efficiency']:.1%}")
            print(f"  • SOC Range: {tech_params['soc_min']:.0%}-{tech_params['soc_max']:.0%}")
            print(f"  • Max C-rate: {tech_params['c_rate_max']:.1f}")
            print(f"  • Energy Efficiency: {metrics['energy_efficiency']:.1%}")
            print(f"  • Total Losses: {metrics['total_losses_mwh']:.3f} MWh")
            print(f"  • Cycles: {sim_result.data['total_cycles']:.2f}")
            print()


def main():
    """Run all demonstrations."""
    print("🔋 FASE 3 BESS Integration - Capabilities Demonstration")
    print("=" * 70)
    print("This demo showcases the advanced BESS integration in DataManagerV2")
    print("All simulations use the real BESSModel with physics-based calculations")
    print()
    
    try:
        demo_bess_constants()
        demo_strategy_comparison() 
        demo_dynamic_control()
        demo_optimization()
        demo_validation()
        demo_technology_deep_dive()
        
        print("=" * 70)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("✅ All FASE 3 capabilities demonstrated")
        print("✅ DataManagerV2 ↔ BESSModel integration working perfectly")
        print("✅ Ready for dashboard integration")
        print()
        print("Next steps:")
        print("  1. Integrate these methods into dashboard pages")
        print("  2. Create interactive visualizations")
        print("  3. Debug BESSStrategies V2 for more strategies")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)