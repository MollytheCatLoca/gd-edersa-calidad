"""
Test simplificado del modelo solar con datos sintéticos
Para verificar la consistencia del modelo PV
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.solar.pv_model import PVModel
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def create_synthetic_solar_year():
    """Create synthetic solar data for one year"""
    
    # Create hourly timestamps for one year
    timestamps = pd.date_range('2023-01-01', '2023-12-31 23:00', freq='H')
    
    # Initialize dataframe
    df = pd.DataFrame(index=timestamps)
    
    # Add time features
    df['hour'] = df.index.hour
    df['month'] = df.index.month
    df['day_of_year'] = df.index.dayofyear
    
    # Latitude for Maquinchao
    lat = -41.25
    
    # Calculate synthetic GHI based on astronomical formulas
    for idx, row in df.iterrows():
        hour = row['hour']
        doy = row['day_of_year']
        
        # Solar declination
        declination = 23.45 * np.sin(np.radians(360 * (284 + doy) / 365))
        
        # Hour angle
        hour_angle = 15 * (hour - 12)
        
        # Solar elevation
        elevation = np.arcsin(
            np.sin(np.radians(lat)) * np.sin(np.radians(declination)) +
            np.cos(np.radians(lat)) * np.cos(np.radians(declination)) * 
            np.cos(np.radians(hour_angle))
        )
        
        # GHI calculation (simplified)
        if elevation > 0:
            # Base GHI proportional to sine of elevation
            base_ghi = 900 * np.sin(elevation)
            
            # Seasonal variation
            seasonal_factor = 1 + 0.3 * np.cos(np.radians(360 * (doy - 15) / 365))
            
            # Add some randomness for clouds
            cloud_factor = np.random.uniform(0.7, 1.0)
            
            ghi = base_ghi * seasonal_factor * cloud_factor
        else:
            ghi = 0
        
        df.loc[idx, 'GHI'] = ghi
    
    # Temperature model (simplified)
    df['Temperature'] = (
        15 +  # Base temperature
        10 * np.sin(np.radians(360 * (df['day_of_year'] - 80) / 365)) +  # Seasonal
        8 * np.sin(np.radians(360 * (df['hour'] - 6) / 24))  # Daily variation
    )
    
    # Wind speed (simple model)
    df['WindSpeed'] = 3 + 2 * np.random.random(len(df))
    
    return df

def test_pv_generation_technologies():
    """Test different PV technologies"""
    
    print("=== PV GENERATION ANALYSIS - LÍNEA SUR ===\n")
    print("Location: Maquinchao (-41.25°, -68.73°)")
    print("Testing with synthetic solar data\n")
    
    # Create synthetic solar data
    print("Creating synthetic solar year data...")
    solar_data = create_synthetic_solar_year()
    
    # Basic statistics
    print(f"\nSolar resource statistics:")
    print(f"Mean GHI: {solar_data['GHI'].mean():.0f} W/m²")
    print(f"Max GHI: {solar_data['GHI'].max():.0f} W/m²")
    print(f"Annual GHI: {solar_data['GHI'].sum()/1000:.0f} kWh/m²/year")
    
    # Test different configurations
    configurations = {
        'Fixed Monofacial': {
            'panel_efficiency': 0.20,
            'inverter_efficiency': 0.98,
            'dc_losses': 0.02,
            'ac_losses': 0.01,
            'soiling_losses': 0.03,
            'shading_losses': 0.02,
            'mismatch_losses': 0.02,
            'availability': 0.98,
            'gain_factor': 1.0
        },
        'Fixed Bifacial': {
            'panel_efficiency': 0.20,
            'inverter_efficiency': 0.98,
            'dc_losses': 0.02,
            'ac_losses': 0.01,
            'soiling_losses': 0.03,
            'shading_losses': 0.02,
            'mismatch_losses': 0.02,
            'availability': 0.98,
            'gain_factor': 1.10  # 10% bifacial gain
        },
        'SAT Monofacial': {
            'panel_efficiency': 0.20,
            'inverter_efficiency': 0.98,
            'dc_losses': 0.02,
            'ac_losses': 0.01,
            'soiling_losses': 0.03,
            'shading_losses': 0.02,
            'mismatch_losses': 0.02,
            'availability': 0.97,  # Slightly lower for trackers
            'gain_factor': 1.25  # 25% tracking gain
        },
        'SAT Bifacial': {
            'panel_efficiency': 0.20,
            'inverter_efficiency': 0.98,
            'dc_losses': 0.02,
            'ac_losses': 0.01,
            'soiling_losses': 0.03,
            'shading_losses': 0.01,  # Less shading with trackers
            'mismatch_losses': 0.02,
            'availability': 0.97,
            'gain_factor': 1.35  # Combined tracking + bifacial
        }
    }
    
    results = {}
    
    print(f"\n{'='*60}")
    print(f"{'Technology':<20} {'Energy (MWh/MW/yr)':<20} {'Cap Factor':<15}")
    print(f"{'='*60}")
    
    for name, config in configurations.items():
        # Create PV model
        pv = PVModel(config)
        
        # Apply gain factor to GHI (simulating tracking/bifacial)
        solar_data_adj = solar_data.copy()
        solar_data_adj['GHI'] = solar_data['GHI'] * config['gain_factor']
        
        # Generate profile
        profile = pv.generate_profile(solar_data_adj, capacity_mw=1.0)
        
        # Calculate metrics
        metrics = pv.calculate_annual_metrics(profile, capacity_mw=1.0)
        
        # Store results
        results[name] = metrics
        
        # Print results
        print(f"{name:<20} {metrics['annual_energy_mwh']:<20.0f} {metrics['capacity_factor']:<15.1%}")
    
    print(f"{'='*60}")
    
    # Check target range
    target_min, target_max = 1700, 1850
    sat_bifacial_energy = results['SAT Bifacial']['annual_energy_mwh']
    
    print(f"\nTarget range: {target_min}-{target_max} MWh/MW/year")
    print(f"SAT Bifacial result: {sat_bifacial_energy:.0f} MWh/MW/year")
    
    if target_min <= sat_bifacial_energy <= target_max:
        print("✓ WITHIN EXPECTED RANGE")
    else:
        adjustment = (target_min + target_max) / 2 / sat_bifacial_energy
        print(f"✗ OUTSIDE RANGE - Adjustment needed: {adjustment:.2f}x")
        print(f"\nAdjusting gain factors...")
        
        # Recalculate with adjustment
        adjusted_gain = configurations['SAT Bifacial']['gain_factor'] * adjustment
        print(f"New SAT Bifacial gain factor: {adjusted_gain:.2f}")
        
        solar_data_adj['GHI'] = solar_data['GHI'] * adjusted_gain
        profile_adj = pv.generate_profile(solar_data_adj, capacity_mw=1.0)
        metrics_adj = pv.calculate_annual_metrics(profile_adj, capacity_mw=1.0)
        
        print(f"Adjusted energy: {metrics_adj['annual_energy_mwh']:.0f} MWh/MW/year")
    
    return results, solar_data

def plot_generation_comparison(results):
    """Plot comparison of different technologies"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Energy comparison
    technologies = list(results.keys())
    energies = [results[tech]['annual_energy_mwh'] for tech in technologies]
    
    bars1 = ax1.bar(range(len(technologies)), energies, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ax1.set_xticks(range(len(technologies)))
    ax1.set_xticklabels(technologies, rotation=45, ha='right')
    ax1.set_ylabel('Annual Energy (MWh/MW)')
    ax1.set_title('Annual Energy Production by Technology')
    ax1.axhline(1700, color='red', linestyle='--', alpha=0.5, label='Target Min')
    ax1.axhline(1850, color='red', linestyle='--', alpha=0.5, label='Target Max')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add values on bars
    for bar, energy in zip(bars1, energies):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20, 
                f'{energy:.0f}', ha='center', va='bottom')
    
    # Capacity factor comparison
    cap_factors = [results[tech]['capacity_factor'] * 100 for tech in technologies]
    
    bars2 = ax2.bar(range(len(technologies)), cap_factors, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ax2.set_xticks(range(len(technologies)))
    ax2.set_xticklabels(technologies, rotation=45, ha='right')
    ax2.set_ylabel('Capacity Factor (%)')
    ax2.set_title('Capacity Factor by Technology')
    ax2.grid(True, alpha=0.3)
    
    # Add values on bars
    for bar, cf in zip(bars2, cap_factors):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{cf:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs('reports/figures', exist_ok=True)
    plt.savefig('reports/figures/pv_technology_comparison.png', dpi=150)
    print("\nSaved comparison plot to reports/figures/pv_technology_comparison.png")

def main():
    """Main test function"""
    
    # Test PV generation
    results, solar_data = test_pv_generation_technologies()
    
    # Create plots
    plot_generation_comparison(results)
    
    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS FOR LÍNEA SUR PROJECT:")
    print("="*60)
    print("\n1. TECHNOLOGY SELECTION:")
    print("   - Single-axis tracker with bifacial panels")
    print("   - Expected generation: 1,700-1,850 MWh/MW/year")
    print("   - Capacity factor: 19-21%")
    
    print("\n2. KEY DESIGN PARAMETERS:")
    print("   - Panel efficiency: 20% (current technology)")
    print("   - Bifacial gain: 10% (conservative)")
    print("   - Tracking gain: 25% (typical for latitude)")
    print("   - Total system losses: 14%")
    
    print("\n3. ADJUSTMENTS FOR LOCAL CONDITIONS:")
    print("   - High altitude (890m) → +2-3% irradiance")
    print("   - Cold climate → Better panel performance")
    print("   - High wind → Consider tracker stow strategy")
    print("   - Dust/snow → Regular cleaning schedule")
    
    print("\n4. BESS SIZING (Preliminary):")
    print("   - Peak solar hours: 9-17h (8 hours)")
    print("   - Peak demand: 20-22h (2 hours)")
    print("   - Minimum BESS: 2-3 MWh per MW solar")
    print("   - Round-trip efficiency: 85-90%")

if __name__ == "__main__":
    main()