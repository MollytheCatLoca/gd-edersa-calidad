#!/usr/bin/env python3
"""
Test script for solar integration in DataManager
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.pages.utils.data_manager import DataManager

def test_solar_integration():
    """Test the new solar functions in DataManager"""
    
    print("="*70)
    print("TESTING SOLAR INTEGRATION IN DATAMANAGER")
    print("="*70)
    
    # Initialize DataManager
    dm = DataManager()
    
    # Test 1: Single station profile
    print("\n1. TESTING SINGLE STATION PROFILE")
    print("-"*50)
    
    profile = dm.get_solar_generation_profile(
        station='Maquinchao',
        capacity_mw=2.5,
        technology='SAT Bifacial'
    )
    
    if profile['available']:
        print(f"Station: {profile['station']}")
        print(f"Technology: {profile['technology']}")
        print(f"Capacity: {profile['capacity_mw']} MW")
        print(f"Annual Generation: {profile['annual_generation_mwh']} MWh")
        print(f"Capacity Factor: {profile['capacity_factor']*100:.1f}%")
        print(f"Peak Power: {profile['peak_power_mw']} MW")
        
        print("\nMonthly Generation (MWh):")
        for month, gen in profile['monthly_generation_mwh'].items():
            print(f"  Month {month:2d}: {gen:6.1f} MWh")
    
    # Test 2: Different technologies
    print("\n\n2. COMPARING TECHNOLOGIES (1 MW each)")
    print("-"*50)
    
    technologies = ['Fixed Monofacial', 'Fixed Bifacial', 'SAT Monofacial', 'SAT Bifacial']
    
    for tech in technologies:
        profile = dm.get_solar_generation_profile(
            station='Jacobacci',
            capacity_mw=1.0,
            technology=tech
        )
        
        if profile['available']:
            print(f"{tech:<20}: {profile['annual_generation_mwh']:>6.0f} MWh/year "
                  f"(CF: {profile['capacity_factor']*100:>4.1f}%)")
    
    # Test 3: System impact analysis
    print("\n\n3. SYSTEM IMPACT ANALYSIS")
    print("-"*50)
    
    # Configure multiple solar plants
    solar_config = {
        'Pilcaniyeu': {'capacity_mw': 2.0, 'technology': 'Fixed Bifacial'},
        'Jacobacci': {'capacity_mw': 3.0, 'technology': 'SAT Monofacial'},
        'Maquinchao': {'capacity_mw': 4.0, 'technology': 'SAT Bifacial'},
        'Los Menucos': {'capacity_mw': 2.5, 'technology': 'SAT Bifacial'}
    }
    
    impact = dm.get_solar_impact_analysis(solar_config)
    
    if impact['available']:
        print("\nStation Results:")
        for station, results in impact['station_results'].items():
            print(f"\n{station}:")
            print(f"  Capacity: {results['capacity_mw']} MW ({results['technology']})")
            print(f"  Annual Gen: {results['annual_generation_mwh']} MWh")
            print(f"  Avg Voltage Improvement: {results['avg_voltage_improvement_pu']} pu")
            print(f"  Peak Voltage Improvement: {results['peak_voltage_improvement_pu']} pu")
        
        print("\n\nSystem-wide Impact:")
        sys_impact = impact['system_impact']
        print(f"  Total Solar Capacity: {sys_impact['total_solar_capacity_mw']} MW")
        print(f"  Total Annual Generation: {sys_impact['total_annual_generation_mwh']} MWh")
        print(f"  Average Voltage Improvement: {sys_impact['avg_voltage_improvement_pu']} pu")
        print(f"  Estimated Loss Reduction: {sys_impact['estimated_loss_reduction_pct']}%")
        print(f"  Critical Events Reduction: {sys_impact['critical_events_reduction_pct']}%")
    
    # Test 4: Hourly profile example
    print("\n\n4. HOURLY PROFILE EXAMPLE (January)")
    print("-"*50)
    
    profile = dm.get_solar_generation_profile(
        station='Los Menucos',
        capacity_mw=1.0,
        technology='SAT Bifacial'
    )
    
    if profile['available']:
        january_profile = profile['hourly_profiles'][1]  # January
        print("Hour | Power (MW)")
        print("-"*20)
        for hour, power in enumerate(january_profile):
            if power > 0:  # Only show daylight hours
                print(f"{hour:4d} | {power:7.3f}")
    
    print("\n" + "="*70)
    print("TESTS COMPLETED SUCCESSFULLY")
    print("="*70)

if __name__ == "__main__":
    test_solar_integration()