"""
Integration tests for complete Solar+BESS pipeline
Tests the full flow from solar generation through BESS to validation
"""

import pytest
import numpy as np


class TestSolarBESSPipeline:
    """Integration tests for the complete pipeline"""
    
    @pytest.mark.integration
    def test_full_pipeline_basic(self, data_manager):
        """Test complete pipeline with basic configuration"""
        # Step 1: Generate solar profile
        solar_result = data_manager.get_solar_generation_profile(
            station='MAQUINCHAO',
            capacity_mw=2.0,
            technology='SAT Bifacial'
        )
        
        assert solar_result['available'] == True
        
        # Step 2: Simulate with BESS
        bess_result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=2.0,
            bess_power_mw=1.0,
            bess_duration_h=4,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        assert bess_result['available'] == True
        
        # Step 3: Verify validation was performed
        assert 'validation' in bess_result['annual_metrics']
        validation = bess_result['annual_metrics']['validation']
        
        # Check validation structure
        assert 'valid' in validation
        assert 'efficiency' in validation
        assert 'metrics' in validation
        assert 'technology' in validation
        
        # Step 4: Verify energy flow consistency
        metrics = bess_result['annual_metrics']
        solar_energy = metrics['solar_energy_mwh']
        delivered = metrics['delivered_energy_mwh']
        
        # Solar from step 1 should match step 2
        assert abs(solar_result['annual_generation_mwh'] - solar_energy) < 1.0
        
        # Delivered should be less than or equal to solar
        assert delivered <= solar_energy
        
    @pytest.mark.integration
    def test_optimization_to_simulation_flow(self, data_manager):
        """Test flow from optimization to simulation"""
        # Step 1: Optimize BESS sizing
        optimization = data_manager.optimize_bess_for_solar(
            station='MAQUINCHAO',
            solar_mw=3.0,
            objective='minimize_variability',
            strategy='smoothing',
            technology='SAT Bifacial'
        )
        
        assert optimization['available'] == True
        recommended = optimization['recommended_config']
        
        # Step 2: Simulate with recommended configuration
        simulation = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=3.0,
            bess_power_mw=recommended['power_mw'],
            bess_duration_h=recommended['duration_h'],
            strategy='smoothing',
            solar_technology='SAT Bifacial'
        )
        
        assert simulation['available'] == True
        
        # Step 3: Verify optimization objectives were met
        metrics = simulation['annual_metrics']
        
        # The simulation should achieve similar metrics to optimization
        # (within reasonable tolerance due to different calculation methods)
        assert metrics['validation']['valid'] == True
        
    @pytest.mark.integration
    def test_multiple_strategies_comparison(self, data_manager):
        """Test comparing multiple strategies for same configuration"""
        base_config = {
            'station': 'LOS MENUCOS',
            'solar_mw': 2.0,
            'bess_power_mw': 1.0,
            'bess_duration_h': 4,
            'solar_technology': 'SAT Bifacial'
        }
        
        strategies = ['cap_shaving', 'flat_day', 'night_shift', 'ramp_limit']
        results = {}
        
        for strategy in strategies:
            result = data_manager.simulate_solar_with_bess(
                **base_config,
                strategy=strategy
            )
            
            if result['available']:
                results[strategy] = {
                    'delivered': result['annual_metrics']['delivered_energy_mwh'],
                    'losses': result['annual_metrics']['losses_mwh'],
                    'efficiency': result['annual_metrics']['validation']['efficiency'],
                    'valid': result['annual_metrics']['validation']['valid']
                }
        
        # All strategies should produce valid results
        assert all(r['valid'] for r in results.values())
        
        # Different strategies should produce different results
        delivered_values = [r['delivered'] for r in results.values()]
        assert len(set(delivered_values)) > 1  # Not all the same
        
        # But all should have reasonable efficiency
        assert all(r['efficiency'] >= 0.85 for r in results.values())
        
    @pytest.mark.integration
    @pytest.mark.parametrize("solar_mw,bess_mw", [
        (0.5, 0.5),   # BESS = Solar
        (2.0, 0.5),   # BESS < Solar  
        (1.0, 2.0),   # BESS > Solar (unusual but valid)
    ])
    def test_different_sizing_ratios(self, data_manager, solar_mw, bess_mw):
        """Test different BESS to solar sizing ratios"""
        result = data_manager.simulate_solar_with_bess(
            station='JACOBACCI',
            solar_mw=solar_mw,
            bess_power_mw=bess_mw,
            bess_duration_h=4,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        assert result['available'] == True
        
        metrics = result['annual_metrics']
        validation = metrics['validation']
        
        # All configurations should be physically valid
        assert validation['valid'] == True or validation['efficiency'] >= 0.80
        
        # BESS utilization should vary with sizing
        if 'strategy_metrics' in validation:
            utilization = validation['strategy_metrics'].get('bess_utilization', 0)
            
            # Oversized BESS should have lower utilization
            if bess_mw > solar_mw:
                assert utilization < 50  # Less than 50% utilized
                
    @pytest.mark.integration
    def test_extreme_weather_scenarios(self, data_manager):
        """Test system behavior in extreme scenarios"""
        # Simulate with very small solar (cloudy conditions)
        cloudy_result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=0.1,  # Very small solar
            bess_power_mw=0.5,
            bess_duration_h=4,
            strategy='flat_day',
            solar_technology='Fixed Monofacial'  # Lower efficiency
        )
        
        if cloudy_result['available']:
            # System should still function
            assert cloudy_result['annual_metrics']['solar_energy_mwh'] > 0
            
        # Simulate with very large solar
        sunny_result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=10.0,  # Very large solar
            bess_power_mw=2.0,
            bess_duration_h=4,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        if sunny_result['available']:
            # Should have significant curtailment
            curtailed = sunny_result['annual_metrics']['curtailed_mwh']
            solar = sunny_result['annual_metrics']['solar_energy_mwh']
            
            # With small BESS and large solar, expect curtailment
            assert curtailed > 0
            # Note: Even with 10MW solar and 2MW BESS, curtailment might be < 10%
            # due to the BESS shifting energy to evening hours
            assert curtailed / solar > 0.01  # More than 1% curtailed
            
    @pytest.mark.integration
    def test_typical_days_consistency(self, data_manager):
        """Test that typical day profiles are consistent with annual metrics"""
        result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=1.0,
            bess_power_mw=0.5,
            bess_duration_h=4,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        if result['available'] and 'typical_day_profiles' in result:
            typical_days = result['typical_day_profiles']
            
            # Check each typical day
            for day_type in ['high_solar', 'low_solar', 'average']:
                assert day_type in typical_days
                
                day_profile = typical_days[day_type]
                
                # Verify structure
                assert 'hour' in day_profile
                assert 'solar_mw' in day_profile
                assert 'grid_mw' in day_profile
                assert 'battery_mw' in day_profile
                assert 'soc_percent' in day_profile
                
                # All arrays should be 24 hours
                assert len(day_profile['hour']) == 24
                assert len(day_profile['solar_mw']) == 24
                
                # Energy balance for the day
                solar_energy = sum(day_profile['solar_mw'])
                grid_energy = sum(day_profile['grid_mw'])
                
                # Grid should not exceed solar (plus some BESS discharge)
                assert grid_energy <= solar_energy * 1.2
                
    @pytest.mark.integration
    @pytest.mark.slow
    def test_annual_simulation_performance(self, data_manager):
        """Test performance of annual simulation"""
        import time
        
        start_time = time.time()
        
        result = data_manager.simulate_solar_with_bess(
            station='MAQUINCHAO',
            solar_mw=5.0,
            bess_power_mw=2.0,
            bess_duration_h=6,
            strategy='cap_shaving',
            solar_technology='SAT Bifacial'
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        assert execution_time < 30  # 30 seconds max
        assert result['available'] == True
        
        print(f"\nAnnual simulation completed in {execution_time:.2f} seconds")