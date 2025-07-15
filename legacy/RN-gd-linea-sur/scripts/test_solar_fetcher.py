"""
Test script for Solar Data Fetcher
Verifica la consistencia de datos solares y calcula generación esperada
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.solar.data_fetcher import SolarDataFetcher
from src.solar.pv_model import PVModel
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def test_solar_resource():
    """Test solar data fetching and analyze resource quality"""
    
    print("=== SOLAR RESOURCE ANALYSIS FOR LÍNEA SUR ===\n")
    
    # Initialize fetcher
    fetcher = SolarDataFetcher()
    
    # Test one station first
    station = "Maquinchao"  # Best location according to Phase 3
    print(f"Testing station: {station}")
    print(f"Coordinates: {fetcher.STATIONS[station]}")
    
    try:
        # Fetch NASA POWER data
        print("\nFetching NASA POWER data (this may take a moment)...")
        df_daily = fetcher.fetch_nasa_power_data(station, 2020, 2023)
        
        # Basic statistics
        print("\n=== DAILY SOLAR RESOURCE STATISTICS ===")
        print(f"Data points: {len(df_daily)}")
        print(f"\nGHI (Global Horizontal Irradiance):")
        print(f"  Mean: {df_daily['GHI'].mean():.1f} W/m²")
        print(f"  Max: {df_daily['GHI'].max():.1f} W/m²")
        print(f"  Min: {df_daily['GHI'].min():.1f} W/m²")
        
        # Annual radiation
        annual_ghi_kwh = df_daily['GHI'].sum() * 24 / 1000 / len(df_daily) * 365
        print(f"\nAnnual GHI: {annual_ghi_kwh:.0f} kWh/m²/year")
        
        # Process to hourly
        print("\nProcessing to hourly data...")
        df_hourly = fetcher.process_solar_data(station)
        
        # Day type statistics
        day_types = df_hourly['day_type'].value_counts(normalize=True) * 100
        print(f"\nDay type distribution:")
        for dtype, pct in day_types.items():
            print(f"  {dtype}: {pct:.1f}%")
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
    
    return df_daily, df_hourly

def analyze_pv_generation(df_hourly):
    """Analyze PV generation with different technologies"""
    
    print("\n\n=== PV GENERATION ANALYSIS ===")
    
    # 1. Fixed tilt system (standard)
    print("\n1. FIXED TILT SYSTEM (Standard monofacial)")
    pv_fixed = PVModel({
        'panel_efficiency': 0.20,  # 20% for good panels
        'inverter_efficiency': 0.98,  # 98% modern inverters
        'total_losses': 0.14  # 14% total losses
    })
    
    profile_fixed = pv_fixed.generate_profile(df_hourly, capacity_mw=1.0)
    metrics_fixed = pv_fixed.calculate_annual_metrics(profile_fixed, capacity_mw=1.0)
    
    print(f"  Annual energy: {metrics_fixed['annual_energy_mwh']:.0f} MWh/MW")
    print(f"  Capacity factor: {metrics_fixed['capacity_factor']:.1%}")
    print(f"  Peak output: {metrics_fixed['peak_output_mw']:.2f} MW")
    
    # 2. Fixed tilt bifacial
    print("\n2. FIXED TILT BIFACIAL (+10% gain)")
    bifacial_gain = 1.10  # 10% bifacial gain
    energy_bifacial_fixed = metrics_fixed['annual_energy_mwh'] * bifacial_gain
    print(f"  Annual energy: {energy_bifacial_fixed:.0f} MWh/MW")
    print(f"  Capacity factor: {energy_bifacial_fixed/8760:.1%}")
    
    # 3. Single-axis tracker (SAT) monofacial
    print("\n3. SINGLE-AXIS TRACKER (Monofacial)")
    tracker_gain = 1.25  # 25% gain from tracking
    energy_sat_mono = metrics_fixed['annual_energy_mwh'] * tracker_gain
    print(f"  Annual energy: {energy_sat_mono:.0f} MWh/MW")
    print(f"  Capacity factor: {energy_sat_mono/8760:.1%}")
    
    # 4. Single-axis tracker bifacial (BEST TECHNOLOGY)
    print("\n4. SINGLE-AXIS TRACKER BIFACIAL (State of the art)")
    # Tracker + bifacial synergy
    sat_bifacial_gain = 1.35  # 35% combined gain
    energy_sat_bifacial = metrics_fixed['annual_energy_mwh'] * sat_bifacial_gain
    print(f"  Annual energy: {energy_sat_bifacial:.0f} MWh/MW")
    print(f"  Capacity factor: {energy_sat_bifacial/8760:.1%}")
    
    # Check if within expected range
    print(f"\n{'='*50}")
    print(f"TARGET RANGE: 1700-1850 MWh/MW/year")
    print(f"ACHIEVED: {energy_sat_bifacial:.0f} MWh/MW/year")
    
    if 1700 <= energy_sat_bifacial <= 1850:
        print("✓ WITHIN EXPECTED RANGE")
    else:
        print("✗ OUTSIDE EXPECTED RANGE")
        adjustment = 1750 / energy_sat_bifacial
        print(f"  Adjustment factor needed: {adjustment:.2f}")
    
    return {
        'fixed_mono': metrics_fixed['annual_energy_mwh'],
        'fixed_bifacial': energy_bifacial_fixed,
        'sat_mono': energy_sat_mono,
        'sat_bifacial': energy_sat_bifacial
    }

def plot_daily_profiles(df_hourly):
    """Plot typical daily profiles by season"""
    
    # Sample days
    summer_day = df_hourly[df_hourly.index.month == 1].iloc[:24]  # January (summer)
    winter_day = df_hourly[df_hourly.index.month == 7].iloc[:24]  # July (winter)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # GHI profiles
    hours = range(24)
    ax1.plot(hours, summer_day['GHI'].values, 'r-', label='Summer (Jan)', linewidth=2)
    ax1.plot(hours, winter_day['GHI'].values, 'b-', label='Winter (Jul)', linewidth=2)
    ax1.set_ylabel('GHI (W/m²)')
    ax1.set_title('Typical Daily Solar Profiles - Maquinchao')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Temperature profiles
    ax2.plot(hours, summer_day['Temperature'].values, 'r-', label='Summer (Jan)', linewidth=2)
    ax2.plot(hours, winter_day['Temperature'].values, 'b-', label='Winter (Jul)', linewidth=2)
    ax2.set_ylabel('Temperature (°C)')
    ax2.set_xlabel('Hour of Day')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('reports/figures/solar_daily_profiles.png', dpi=150)
    print("\nSaved daily profiles plot to reports/figures/solar_daily_profiles.png")

def main():
    """Main test function"""
    
    # Test fetcher
    df_daily, df_hourly = test_solar_resource()
    
    if df_hourly is not None:
        # Analyze generation
        generation_results = analyze_pv_generation(df_hourly)
        
        # Create plots
        os.makedirs('reports/figures', exist_ok=True)
        plot_daily_profiles(df_hourly)
        
        # Summary for all stations
        print(f"\n\n{'='*60}")
        print("RECOMMENDED CONFIGURATION FOR LÍNEA SUR:")
        print(f"{'='*60}")
        print("Technology: Single-axis tracker with bifacial panels")
        print(f"Expected generation: {generation_results['sat_bifacial']:.0f} MWh/MW/year")
        print(f"Capacity factor: {generation_results['sat_bifacial']/8760:.1%}")
        print("\nKey assumptions:")
        print("- Bifacial gain: 10% (conservative for high albedo)")
        print("- Tracker gain: 25% (typical for latitude -41°)")
        print("- System losses: 14% (DC, AC, soiling, availability)")
        print("- Panel efficiency: 20% (current technology)")
        
        # BESS sizing preview
        print("\n\nPRELIMINARY BESS SIZING:")
        peak_summer = df_hourly[df_hourly.index.month.isin([12,1,2])].groupby(df_hourly.index.hour)['GHI'].mean()
        solar_hours = peak_summer[peak_summer > 100].index
        print(f"Solar generation hours (summer): {solar_hours.min()}h to {solar_hours.max()}h")
        print(f"Coverage needed for peak (20-22h): 2-4 hours")
        print(f"Suggested BESS: 2-3 MWh per MW solar")

if __name__ == "__main__":
    main()