"""
Unit tests for DataManager BESS functions
"""

import pytest
import numpy as np
import pandas as pd


class TestDataManagerBESS:
    """Test suite for DataManager BESS-related functions"""
    
    def test_solar_generation_profile_structure(self, data_manager):
        """Test that solar generation profile returns correct structure"""
        result = data_manager.get_solar_generation_profile(
            station='MAQUINCHAO',
            capacity_mw=1.0,
            technology='SAT Bifacial'
        )
        
        # Check structure
        assert result['available'] == True
        assert 'station' in result
        assert 'capacity_mw' in result
        assert 'technology' in result
        assert 'hourly_profiles' in result
        assert 'monthly_generation_mwh' in result
        assert 'annual_generation_mwh' in result
        assert 'capacity_factor' in result
        
        # Check data types
        assert isinstance(result['hourly_profiles'], dict)
        assert isinstance(result['monthly_generation_mwh'], dict)
        assert isinstance(result['annual_generation_mwh'], (int, float))
        
        # Check hourly profiles have 24 hours for each month
        for month in range(1, 13):
            assert month in result['hourly_profiles']
            assert len(result['hourly_profiles'][month]) == 24
            
    def test_solar_generation_values_reasonable(self, data_manager):
        """Test that solar generation values are physically reasonable"""
        result = data_manager.get_solar_generation_profile(
            station='MAQUINCHAO',
            capacity_mw=1.0,
            technology='SAT Bifacial'
        )
        
        # Check capacity factor is reasonable (10-30% for solar)
        assert 0.10 <= result['capacity_factor'] <= 0.30
        
        # Check annual generation is reasonable
        # 1 MW * 8760 hours * 0.30 CF = 2628 MWh (max theoretical)
        assert 0 < result['annual_generation_mwh'] <= 2628
        
        # Check hourly values don't exceed capacity
        for month, hourly in result['hourly_profiles'].items():
            assert all(0 <= h <= 1.0 for h in hourly)
            
        # Check night hours are zero
        for month, hourly in result['hourly_profiles'].items():
            # Hours 0-5 should always be zero
            assert all(h == 0 for h in hourly[0:6])
            # Hours 22-23 should be zero (solar might extend to 21:00 in summer)
            assert all(h == 0 for h in hourly[22:24])
            
    def test_simulate_solar_with_bess_basic(self, data_manager):
        """Test basic solar+BESS simulation"""
        result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=1.0,
            bess_power_mw=0.5,
            bess_duration_h=2,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        assert result['available'] == True
        assert result['station'] == 'MAQUINCHAO'
        assert result['solar_capacity_mw'] == 1.0
        assert result['bess_power_mw'] == 0.5
        assert result['bess_duration_h'] == 2
        assert result['bess_capacity_mwh'] == 1.0  # 0.5 MW * 2h
        
    def test_simulate_solar_with_bess_energy_balance(self, data_manager):
        """Test energy conservation in solar+BESS simulation"""
        result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=2.0,
            bess_power_mw=1.0,
            bess_duration_h=4,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        if result['available']:
            metrics = result['annual_metrics']
            
            # Energy balance: Solar = Grid + Losses + Curtailed
            solar_total = metrics['solar_energy_mwh']
            grid_total = metrics['delivered_energy_mwh']
            losses_total = metrics['losses_mwh']
            curtailed_total = metrics['curtailed_mwh']
            
            # Check energy conservation (within 0.1% tolerance)
            energy_accounted = grid_total + losses_total + curtailed_total
            assert abs(solar_total - energy_accounted) / solar_total < 0.001
            
            # Check efficiency is reasonable (>90% for modern BESS)
            if solar_total > 0:
                efficiency = grid_total / solar_total
                assert 0.85 <= efficiency <= 1.0
                
    def test_simulate_solar_with_bess_daily_metrics(self, data_manager):
        """Test that metrics are properly converted to daily values"""
        result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=1.0,
            bess_power_mw=0.5,
            bess_duration_h=2,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        if result['available']:
            metrics = result['annual_metrics']
            
            # Daily metrics should be reasonable
            # For 1 MW solar, expect ~4-5 MWh/day average
            daily_solar = metrics['solar_energy_mwh'] / 365
            assert 2 <= daily_solar <= 6
            
            # Daily delivered should be close to daily solar
            daily_delivered = metrics['delivered_energy_mwh'] / 365
            assert 2 <= daily_delivered <= 6
            
            # Losses should be small (< 10% of solar)
            daily_losses = metrics['losses_mwh'] / 365
            assert daily_losses < daily_solar * 0.1
            
    def test_optimize_bess_for_solar(self, data_manager):
        """Test BESS optimization function"""
        result = data_manager.optimize_bess_for_solar(
            station='MAQUINCHAO',
            solar_mw=2.0,
            objective='minimize_variability',
            strategy='smoothing',
            technology='SAT Bifacial'
        )
        
        assert result['available'] == True
        assert 'recommended_config' in result
        assert 'top_configurations' in result
        
        # Check recommended config is reasonable
        config = result['recommended_config']
        assert 0 < config['power_mw'] <= 2.0  # Not more than solar
        assert 1 <= config['duration_h'] <= 6
        assert config['capacity_mwh'] == config['power_mw'] * config['duration_h']
        
        # Check metrics are present
        metrics = config['metrics']
        assert 'variability_reduction' in metrics
        assert 'utilization' in metrics
        assert 'efficiency' in metrics
        
    def test_different_strategies_produce_different_results(self, data_manager):
        """Test that different strategies produce different grid profiles"""
        configs = []
        
        for strategy in ['cap_shaving', 'flat_day', 'night_shift']:
            result = data_manager.simulate_solar_with_bess(
                station='MAQUINCHAO',
                solar_mw=1.0,
                bess_power_mw=0.5,
                bess_duration_h=4,
                strategy=strategy,
                solar_technology='SAT Bifacial'
            )
            
            if result['available']:
                configs.append({
                    'strategy': strategy,
                    'metrics': result['annual_metrics']
                })
        
        # Check that different strategies produce different results
        assert len(configs) >= 2
        
        # Compare delivered energy between strategies
        delivered_values = [c['metrics']['delivered_energy_mwh'] for c in configs]
        # They should be similar but not identical
        assert max(delivered_values) - min(delivered_values) > 0.01
        
    def test_zero_bess_equals_solar_only(self, data_manager):
        """Test that zero BESS configuration equals solar-only"""
        # Solar only
        solar_only = data_manager.get_solar_generation_profile(
            station='MAQUINCHAO',
            capacity_mw=1.0,
            technology='SAT Bifacial'
        )
        
        # Solar with zero BESS
        with_zero_bess = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=1.0,
            bess_power_mw=0.0,
            bess_duration_h=0,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        if solar_only['available'] and with_zero_bess['available']:
            # Annual generation should be identical
            assert abs(
                solar_only['annual_generation_mwh'] - 
                with_zero_bess['annual_metrics']['solar_energy_mwh']
            ) < 0.1
            
    @pytest.mark.parametrize("station", ['MAQUINCHAO', 'LOS MENUCOS', 'JACOBACCI'])
    def test_multiple_stations(self, data_manager, station):
        """Test that all stations work correctly"""
        result = data_manager.simulate_solar_with_bess(
            station=station,
            solar_mw=1.0,
            bess_power_mw=0.5,
            bess_duration_h=2,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        assert result['available'] == True
        assert result['station'] == station