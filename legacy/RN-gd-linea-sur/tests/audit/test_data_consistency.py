"""
Data Consistency Audit Tests
Ensures physical laws and data consistency across the entire system
"""

import pytest
import numpy as np
import pandas as pd
from itertools import product


class TestDataConsistencyAudit:
    """Comprehensive audit tests for PSFV+BESS data consistency"""
    
    @pytest.mark.audit
    def test_energy_conservation_full_pipeline(self, data_manager):
        """Test energy conservation through complete pipeline"""
        configurations = [
            {'solar': 1.0, 'bess_power': 0.5, 'bess_duration': 2},
            {'solar': 2.0, 'bess_power': 1.0, 'bess_duration': 4},
            {'solar': 5.0, 'bess_power': 2.0, 'bess_duration': 6},
        ]
        
        for config in configurations:
            result = data_manager.simulate_solar_with_bess(
                station='MAQUINCHAO',
                solar_mw=config['solar'],
                bess_power_mw=config['bess_power'],
                bess_duration_h=config['bess_duration'],
                strategy='cap_shaving',
                solar_technology='SAT Bifacial'
            )
            
            if result['available']:
                metrics = result['annual_metrics']
                
                # Energy conservation check
                solar_total = metrics['solar_energy_mwh']
                delivered = metrics['delivered_energy_mwh']
                losses = metrics['losses_mwh']
                curtailed = metrics['curtailed_mwh']
                
                # All energy must be accounted for
                accounted = delivered + losses + curtailed
                error = abs(solar_total - accounted) / solar_total
                
                assert error < 0.001, (
                    f"Energy conservation violated for config {config}:\n"
                    f"Solar: {solar_total:.2f} MWh\n"
                    f"Accounted: {accounted:.2f} MWh\n"
                    f"Error: {error*100:.2f}%"
                )
                
    @pytest.mark.audit
    def test_efficiency_bounds(self, data_manager):
        """Test that efficiencies stay within physical bounds"""
        # Test multiple configurations
        stations = ['MAQUINCHAO', 'LOS MENUCOS', 'JACOBACCI']
        strategies = ['cap_shaving', 'flat_day', 'night_shift']
        
        for station, strategy in product(stations, strategies):
            result = data_manager.simulate_solar_with_bess(
                station=station,
                solar_mw=1.0,
                bess_power_mw=0.5,
                bess_duration_h=4,
                strategy=strategy,
                solar_technology='SAT Bifacial'
            )
            
            if result['available']:
                metrics = result['annual_metrics']
                
                # Calculate efficiency
                if metrics['solar_energy_mwh'] > 0:
                    efficiency = metrics['delivered_energy_mwh'] / metrics['solar_energy_mwh']
                    
                    # Efficiency must be between 0 and 1
                    assert 0 <= efficiency <= 1.0, (
                        f"Invalid efficiency {efficiency:.2%} for {station}/{strategy}"
                    )
                    
                    # For small BESS, efficiency should be > 85%
                    assert efficiency >= 0.85, (
                        f"Efficiency too low {efficiency:.2%} for {station}/{strategy}"
                    )
                    
    @pytest.mark.audit
    def test_power_limits_never_exceeded(self, data_manager):
        """Test that power limits are respected throughout operation"""
        # Get detailed simulation with typical days
        result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=2.0,
            bess_power_mw=1.0,
            bess_duration_h=4,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        if result['available'] and 'typical_day_profiles' in result:
            bess_power_limit = result['bess_power_mw']
            solar_capacity = result['solar_capacity_mw']
            
            for day_type, profile in result['typical_day_profiles'].items():
                # Check BESS power never exceeds limit
                battery_power = np.array(profile['battery_mw'])
                assert np.all(np.abs(battery_power) <= bess_power_limit * 1.01), (
                    f"BESS power exceeded limit on {day_type} day"
                )
                
                # Check grid power is physically possible
                grid_power = np.array(profile['grid_mw'])
                assert np.all(grid_power >= 0), f"Negative grid power on {day_type}"
                assert np.all(grid_power <= (solar_capacity + bess_power_limit) * 1.1), (
                    f"Grid power exceeds possible maximum on {day_type}"
                )
                
    @pytest.mark.audit
    def test_soc_bounds(self, data_manager):
        """Test that State of Charge stays within bounds"""
        result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=1.0,
            bess_power_mw=0.5,
            bess_duration_h=4,
            strategy='flat_day',
            solar_technology='SAT Bifacial'
        )
        
        if result['available'] and 'typical_day_profiles' in result:
            for day_type, profile in result['typical_day_profiles'].items():
                soc = np.array(profile['soc_percent'])
                
                # SOC must be between 10% and 95%
                assert np.all(soc >= 10), f"SOC below minimum on {day_type}"
                assert np.all(soc <= 95), f"SOC above maximum on {day_type}"
                
                # SOC changes should be smooth (no jumps > 25% per hour)
                soc_changes = np.abs(np.diff(soc))
                assert np.all(soc_changes <= 25), (
                    f"SOC changes too rapidly on {day_type}: max {np.max(soc_changes):.1f}%/h"
                )
                
    @pytest.mark.audit
    def test_losses_are_positive_and_reasonable(self, data_manager):
        """Test that losses are always positive and within reasonable bounds"""
        configurations = [
            {'solar': 1.0, 'bess': 0.0},   # No BESS (baseline)
            {'solar': 1.0, 'bess': 0.5},   # Small BESS
            {'solar': 2.0, 'bess': 1.0},   # Medium BESS
            {'solar': 5.0, 'bess': 2.0},   # Large BESS
        ]
        
        for config in configurations:
            result = data_manager.simulate_solar_with_bess(
                station='MAQUINCHAO',
                solar_mw=config['solar'],
                bess_power_mw=config['bess'],
                bess_duration_h=4,
                strategy='cap_shaving',
                solar_technology='SAT Bifacial'
            )
            
            if result['available']:
                metrics = result['annual_metrics']
                losses = metrics['losses_mwh']
                solar = metrics['solar_energy_mwh']
                
                # Losses must be non-negative
                assert losses >= 0, f"Negative losses: {losses}"
                
                # Losses should be less than 10% for modern BESS
                if config['bess'] > 0 and solar > 0:
                    loss_fraction = losses / solar
                    assert loss_fraction <= 0.10, (
                        f"Excessive losses {loss_fraction:.1%} for config {config}"
                    )
                    
    @pytest.mark.audit
    @pytest.mark.parametrize("station,solar_mw,bess_mw,duration_h,strategy", [
        ('MAQUINCHAO', 0.5, 0.5, 1, 'cap_shaving'),
        ('MAQUINCHAO', 1.0, 0.5, 2, 'flat_day'),
        ('LOS MENUCOS', 2.0, 1.0, 4, 'night_shift'),
        ('JACOBACCI', 5.0, 2.0, 6, 'ramp_limit'),
    ])
    def test_matrix_configurations(self, data_manager, station, solar_mw, bess_mw, duration_h, strategy):
        """Test matrix of configurations for consistency"""
        result = data_manager.simulate_solar_with_bess(
            station=station,
            solar_mw=solar_mw,
            bess_power_mw=bess_mw,
            bess_duration_h=duration_h,
            strategy=strategy,
            solar_technology='SAT Bifacial'
        )
        
        if result['available']:
            metrics = result['annual_metrics']
            
            # Basic consistency checks
            assert metrics['solar_energy_mwh'] > 0
            assert metrics['delivered_energy_mwh'] > 0
            assert metrics['delivered_energy_mwh'] <= metrics['solar_energy_mwh']
            
            # Validation result should be present
            assert 'validation' in metrics
            validation = metrics['validation']
            
            # Check validation structure
            assert 'efficiency' in validation
            assert 'valid' in validation
            assert 'metrics' in validation
            
            # Daily values should be reasonable
            daily_solar = metrics['solar_energy_mwh'] / 365
            assert 0 < daily_solar < solar_mw * 24  # Can't exceed 24h at full power
            
    @pytest.mark.audit
    def test_monthly_data_consistency(self, data_manager):
        """Test that monthly data sums to annual totals"""
        result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=1.0,
            bess_power_mw=0.5,
            bess_duration_h=4,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        if result['available']:
            # Sum monthly values
            monthly_grid = result.get('monthly_grid_mwh', [])
            monthly_solar = result.get('monthly_solar_mwh', [])
            
            if monthly_grid and monthly_solar:
                annual_grid_from_monthly = sum(monthly_grid)
                annual_solar_from_monthly = sum(monthly_solar)
                
                # Compare with annual metrics
                annual_metrics = result['annual_metrics']
                
                # Monthly sums should match annual (within 1%)
                grid_error = abs(annual_grid_from_monthly - annual_metrics['delivered_energy_mwh'])
                solar_error = abs(annual_solar_from_monthly - annual_metrics['solar_energy_mwh'])
                
                assert grid_error / annual_metrics['delivered_energy_mwh'] < 0.01
                assert solar_error / annual_metrics['solar_energy_mwh'] < 0.01
                
    @pytest.mark.audit
    @pytest.mark.slow
    def test_comprehensive_audit_all_stations(self, data_manager, stations, strategies):
        """Comprehensive audit across all stations and strategies"""
        audit_results = []
        
        for station in stations:
            for strategy in strategies:
                result = data_manager.simulate_solar_with_bess(
                    station=station,
                    solar_mw=1.0,
                    bess_power_mw=0.5,
                    bess_duration_h=4,
                    strategy=strategy,
                    solar_technology='SAT Bifacial'
                )
                
                if result['available']:
                    metrics = result['annual_metrics']
                    
                    # Collect audit metrics
                    audit_results.append({
                        'station': station,
                        'strategy': strategy,
                        'efficiency': metrics['delivered_energy_mwh'] / metrics['solar_energy_mwh'],
                        'losses_percent': metrics['losses_mwh'] / metrics['solar_energy_mwh'] * 100,
                        'curtailment_percent': metrics['curtailed_mwh'] / metrics['solar_energy_mwh'] * 100,
                        'valid': metrics['validation']['valid']
                    })
        
        # Create audit DataFrame
        audit_df = pd.DataFrame(audit_results)
        
        # All configurations should be valid
        assert audit_df['valid'].all(), "Some configurations failed validation"
        
        # Efficiency should be consistent within each strategy
        for strategy in strategies:
            strategy_data = audit_df[audit_df['strategy'] == strategy]
            efficiency_std = strategy_data['efficiency'].std()
            assert efficiency_std < 0.05, f"Inconsistent efficiency for {strategy}"
            
        # Generate audit report
        print("\n=== AUDIT SUMMARY ===")
        print(audit_df.groupby('strategy')[['efficiency', 'losses_percent']].mean())
        print("====================\n")