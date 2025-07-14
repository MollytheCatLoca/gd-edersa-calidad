"""
Unit tests for BESS Validator
Focus on daily metrics conversion and efficiency validation
"""

import pytest
import numpy as np
from src.battery.bess_validator import BESSValidator, calculate_zero_curtail_bess


class TestBESSValidator:
    """Test suite for BESS energy validation"""
    
    def test_initialization_technologies(self):
        """Test validator initialization with different technologies"""
        # Standard technology
        validator_std = BESSValidator(technology='standard')
        assert validator_std.technology == 'standard'
        assert validator_std.min_efficiency == 0.90
        
        # Modern LFP
        validator_lfp = BESSValidator(technology='modern_lfp')
        assert validator_lfp.technology == 'modern_lfp'
        assert validator_lfp.min_efficiency == 0.93
        
        # Premium
        validator_premium = BESSValidator(technology='premium')
        assert validator_premium.technology == 'premium'
        assert validator_premium.min_efficiency == 0.95
        
        # Unknown technology defaults to modern_lfp
        validator_unknown = BESSValidator(technology='unknown')
        assert validator_unknown.technology == 'modern_lfp'
        
    def test_validate_energy_delivery_basic(self):
        """Test basic energy delivery validation"""
        validator = BESSValidator(technology='modern_lfp')
        
        # Case 1: Good efficiency
        result = validator.validate_energy_delivery(
            solar_energy=100,
            delivered_energy=94,
            curtailed_energy=0
        )
        
        assert result['valid'] == True
        assert result['efficiency'] == 0.94
        assert result['losses'] == 6
        assert result['metrics']['efficiency_percent'] == 94.0
        
        # Case 2: Poor efficiency
        result = validator.validate_energy_delivery(
            solar_energy=100,
            delivered_energy=85,
            curtailed_energy=0
        )
        
        assert result['valid'] == False
        assert result['efficiency'] == 0.85
        assert 'suggestion' in result
        
    def test_validate_energy_delivery_with_curtailment(self):
        """Test validation with curtailed energy"""
        validator = BESSValidator(technology='modern_lfp')
        
        # Solar = 100, Delivered = 90, Curtailed = 5, Losses = 5
        result = validator.validate_energy_delivery(
            solar_energy=100,
            delivered_energy=90,
            curtailed_energy=5
        )
        
        assert result['valid'] == False  # 90% < 93% required
        assert result['efficiency'] == 0.90
        assert result['losses'] == 5
        assert result['curtailed'] == 5
        
        # Check energy balance
        total = result['metrics']['delivered_energy_mwh'] + \
                result['metrics']['losses_mwh'] + \
                result['metrics']['curtailed_mwh']
        assert abs(total - 100) < 0.01
        
    def test_validate_strategy_result_annual_to_daily(self):
        """Test that annual profiles are converted to daily metrics"""
        validator = BESSValidator(technology='modern_lfp')
        
        # Create annual profile (8760 hours)
        solar_profile = np.ones(8760) * 0.5  # 0.5 MW constant
        grid_power = np.ones(8760) * 0.45    # 0.45 MW delivered
        battery_power = np.zeros(8760)
        solar_curtailed = np.zeros(8760)
        
        bess_result = {
            'grid_power': grid_power,
            'battery_power': battery_power,
            'solar_curtailed': solar_curtailed
        }
        
        result = validator.validate_strategy_result(
            solar_profile=solar_profile,
            bess_result=bess_result,
            strategy_name='test',
            bess_config={'power_mw': 1, 'duration_h': 4}
        )
        
        # Check metrics are daily
        metrics = result['metrics']
        
        # Annual: 0.5 MW * 8760h = 4380 MWh
        # Daily: 4380 / 365 = 12 MWh
        assert abs(metrics['solar_energy_mwh'] - 12.0) < 0.1
        assert abs(metrics['delivered_energy_mwh'] - 10.8) < 0.1  # 0.45 * 24
        
        # Efficiency should be calculated on total values
        assert abs(result['efficiency'] - 0.90) < 0.01  # 0.45/0.5
        
    def test_validate_strategy_result_daily_profile(self):
        """Test validation with daily profile (24 hours)"""
        validator = BESSValidator(technology='modern_lfp')
        
        # Create daily profile
        hours = np.arange(24)
        solar_profile = np.maximum(0, 
            2.0 * np.exp(-((hours - 12) ** 2) / 18) * (hours >= 6) * (hours <= 18)
        )
        
        # Simulate BESS result
        grid_power = solar_profile * 0.95  # 95% efficient
        
        bess_result = {
            'grid_power': grid_power,
            'battery_power': np.zeros(24),
            'solar_curtailed': np.zeros(24)
        }
        
        result = validator.validate_strategy_result(
            solar_profile=solar_profile,
            bess_result=bess_result,
            strategy_name='passthrough',
            bess_config={'power_mw': 0, 'duration_h': 0}
        )
        
        # Should use values as-is for daily profile
        solar_total = np.sum(solar_profile)
        assert abs(result['metrics']['solar_energy_mwh'] - solar_total) < 0.01
        
    def test_strategy_specific_metrics(self):
        """Test strategy-specific validation metrics"""
        validator = BESSValidator(technology='modern_lfp')
        
        # Test cap shaving strategy
        solar_profile = np.array([0, 0, 0, 0, 0, 0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0,
                                 3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0, 0, 0, 0, 0, 0])
        
        # Cap at 2 MW
        grid_power = np.minimum(solar_profile, 2.0)
        
        bess_result = {
            'grid_power': grid_power,
            'battery_power': np.zeros(24),
            'solar_curtailed': np.maximum(0, solar_profile - 2.0)
        }
        
        result = validator.validate_strategy_result(
            solar_profile=solar_profile,
            bess_result=bess_result,
            strategy_name='cap_shaving',
            bess_config={'power_mw': 1, 'duration_h': 4, 'cap_mw': 2.0}
        )
        
        # Check strategy metrics
        strategy_metrics = result['strategy_metrics']
        assert 'cap_violations' in strategy_metrics
        assert 'cap_compliance' in strategy_metrics
        assert strategy_metrics['cap_compliance'] == 100  # No violations
        
    def test_ml_features_extraction(self):
        """Test ML feature extraction"""
        validator = BESSValidator(technology='modern_lfp')
        
        # Simple daily profile
        solar_profile = np.array([0]*6 + [0.5, 1, 1.5, 2, 2, 2, 2, 1.5, 1, 0.5] + [0]*8)
        
        bess_result = {
            'grid_power': solar_profile * 0.9,
            'battery_power': np.zeros(24),
            'solar_curtailed': np.zeros(24)
        }
        
        result = validator.validate_strategy_result(
            solar_profile=solar_profile,
            bess_result=bess_result,
            strategy_name='cap_shaving',
            bess_config={'power_mw': 1, 'duration_h': 4}
        )
        
        features = result['ml_features']
        
        # Check features exist
        assert 'solar_peak_mw' in features
        assert 'solar_mean_mw' in features
        assert 'bess_power_mw' in features
        assert 'bess_solar_ratio' in features
        
        # Check technology encoding
        assert features['tech_modern'] == 1
        assert features['tech_standard'] == 0
        assert features['tech_premium'] == 0
        
        # Check hourly features
        for h in range(24):
            assert f'solar_h{h}' in features
            
    def test_suggest_bess_sizing(self):
        """Test BESS sizing suggestions"""
        validator = BESSValidator(technology='modern_lfp')
        
        # Daily solar profile
        hours = np.arange(24)
        solar_profile = np.maximum(0, 
            5.0 * np.exp(-((hours - 12) ** 2) / 18) * (hours >= 6) * (hours <= 18)
        )
        
        suggestions = validator.suggest_bess_sizing(
            solar_profile=solar_profile,
            target_efficiency=0.95
        )
        
        assert 'solar_peak_mw' in suggestions
        assert 'suggestions' in suggestions
        assert len(suggestions['suggestions']) == 3  # Three options
        
        # Check suggestions are reasonable
        for option in suggestions['suggestions']:
            assert 0 < option['power_mw'] <= suggestions['solar_peak_mw']
            assert option['duration_h'] in [2, 4, 6]
            assert option['capacity_mwh'] == option['power_mw'] * option['duration_h']
            assert 'use_case' in option
            
    def test_calculate_zero_curtail_bess(self):
        """Test zero curtailment BESS calculation"""
        # Solar profile with peak above desired cap
        solar_profile = np.array([0]*6 + [1, 2, 3, 4, 5, 5, 5, 4, 3, 2, 1] + [0]*7)
        
        # Calculate BESS for cap strategy
        result = calculate_zero_curtail_bess(
            solar_profile=solar_profile,
            strategy='cap',
            target_params={'cap_mw': 3.0},
            technology='modern_lfp'
        )
        
        assert result['power_mw'] > 0
        assert result['duration_h'] > 0
        assert abs(result['capacity_mwh'] - result['power_mw'] * result['duration_h']) < 0.02
        assert result['technology'] == 'modern_lfp'
        assert result['efficiency'] == 0.93
        
        # BESS should be sized to handle excess above 3 MW
        assert result['power_mw'] >= 2.0  # At least 2 MW to handle 5-3 MW excess
        
    def test_validation_with_different_losses(self):
        """Test validation correctly identifies different loss scenarios"""
        validator = BESSValidator(technology='modern_lfp')
        
        # Case 1: Losses within acceptable range
        result1 = validator.validate_energy_delivery(
            solar_energy=100,
            delivered_energy=93.5,
            curtailed_energy=0
        )
        assert result1['valid'] == True
        assert result1['losses'] == 6.5
        
        # Case 2: Excessive losses
        result2 = validator.validate_energy_delivery(
            solar_energy=100,
            delivered_energy=85,
            curtailed_energy=0
        )
        assert result2['valid'] == False
        assert 'Reducir pérdidas' in result2['suggestion']
        
        # Case 3: Losses due to curtailment
        result3 = validator.validate_energy_delivery(
            solar_energy=100,
            delivered_energy=85,
            curtailed_energy=10
        )
        assert result3['valid'] == False
        assert 'curtailment' in result3['suggestion']