"""
Unit tests for BESSModel class
"""

import pytest
import numpy as np
from src.battery.bess_model import BESSModel


class TestBESSModelInit:
    """Tests for BESSModel initialization and configuration"""
    
    def test_init_valid_parameters(self):
        """Test initialization with valid parameters"""
        bess = BESSModel(
            power_mw=1.0, 
            duration_hours=4.0, 
            technology='modern_lfp', 
            topology='series_dc',
            verbose=False
        )
        
        assert bess.capacity_mwh == 4.0
        assert bess.power_mw == 1.0
        assert bess.power_mw_eff == pytest.approx(0.98, rel=1e-3)  # 2% penalty
        assert bess.soc == bess.tech_params['soc_min']
        assert bess.technology == 'modern_lfp'
        assert bess.topology == 'series_dc'
    
    def test_init_invalid_parameters(self):
        """Test that ValueError is raised with invalid parameters"""
        with pytest.raises(ValueError, match="power_mw and duration_hours must be > 0"):
            BESSModel(power_mw=0, duration_hours=4.0)
        
        with pytest.raises(ValueError, match="power_mw and duration_hours must be > 0"):
            BESSModel(power_mw=1.0, duration_hours=-1)
        
        with pytest.raises(ValueError, match="power_mw and duration_hours must be > 0"):
            BESSModel(power_mw=-1, duration_hours=4.0)
    
    def test_technology_efficiencies(self):
        """Test efficiency values for different technologies"""
        expected_efficiencies = {
            'standard': 0.90,
            'modern_lfp': 0.93,
            'premium': 0.95
        }
        
        for tech, expected_rt in expected_efficiencies.items():
            bess = BESSModel(1.0, 4.0, technology=tech, verbose=False)
            assert bess.eff_roundtrip == pytest.approx(expected_rt, rel=1e-3)
    
    def test_topology_power_derating(self):
        """Test power derating for different topologies"""
        topologies_penalties = {
            'parallel_ac': 0.00,
            'series_dc': 0.02,
            'hybrid': 0.01
        }
        
        for topology, penalty in topologies_penalties.items():
            bess = BESSModel(1.0, 4.0, topology=topology, verbose=False)
            expected_power_eff = 1.0 * (1 - penalty)
            assert bess.power_mw_eff == pytest.approx(expected_power_eff, rel=1e-6)
    
    def test_unknown_technology_defaults(self):
        """Test that unknown technology defaults to modern_lfp"""
        bess = BESSModel(1.0, 4.0, technology='unknown', verbose=False)
        assert bess.technology == 'modern_lfp'
        assert bess.eff_roundtrip == pytest.approx(0.93, rel=1e-3)
    
    def test_unknown_topology_defaults(self):
        """Test that unknown topology defaults to parallel_ac"""
        bess = BESSModel(1.0, 4.0, topology='unknown', verbose=False)
        assert bess.topology == 'parallel_ac'
        assert bess.power_mw_eff == 1.0


class TestBESSModelLimits:
    """Tests for charge/discharge limits"""
    
    @pytest.mark.parametrize("dt", [0.25, 0.5, 1.0, 2.0])
    def test_charge_limit_with_timestep(self, dt):
        """Test that charge limits scale properly with timestep"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        bess.soc = 0.5  # 50% SOC
        
        limit = bess.get_charge_limit(dt)
        
        # Should not exceed C-rate, power rating, or headroom
        max_by_crate = bess.tech_params['c_rate_max'] * bess.capacity_mwh
        max_by_headroom = (bess.tech_params['soc_max'] - 0.5) * bess.capacity_mwh / dt
        max_by_power = bess.power_mw_eff
        
        expected_limit = min(max_by_crate, max_by_headroom, max_by_power)
        assert limit == pytest.approx(expected_limit, rel=1e-6)
    
    @pytest.mark.parametrize("dt", [0.25, 0.5, 1.0, 2.0])
    def test_discharge_limit_with_timestep(self, dt):
        """Test that discharge limits scale properly with timestep"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        bess.soc = 0.5  # 50% SOC
        
        limit = bess.get_discharge_limit(dt)
        
        # Should not exceed C-rate, power rating, or available energy
        max_by_crate = bess.tech_params['c_rate_max'] * bess.capacity_mwh
        max_by_available = (0.5 - bess.tech_params['soc_min']) * bess.capacity_mwh / dt
        max_by_power = bess.power_mw_eff
        
        expected_limit = min(max_by_crate, max_by_available, max_by_power)
        assert limit == pytest.approx(expected_limit, rel=1e-6)
    
    def test_charge_limit_at_max_soc(self):
        """Test charge limit is zero at maximum SOC"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        bess.soc = bess.tech_params['soc_max']
        
        assert bess.get_charge_limit() == 0.0
    
    def test_discharge_limit_at_min_soc(self):
        """Test discharge limit is zero at minimum SOC"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        bess.soc = bess.tech_params['soc_min']
        
        assert bess.get_discharge_limit() == 0.0


class TestBESSModelStep:
    """Tests for step() operation"""
    
    def test_step_charge_energy_balance(self):
        """Test energy balance during charging"""
        bess = BESSModel(1.0, 4.0, technology='modern_lfp', verbose=False)
        initial_energy = bess.energy_stored
        
        result = bess.step(-0.5, dt=1.0)  # Charge 0.5 MW for 1 hour
        
        # Energy stored = power × time × efficiency
        expected_delta = 0.5 * 1.0 * bess.tech_params['η_charge']
        assert bess.energy_stored == pytest.approx(initial_energy + expected_delta, rel=1e-6)
        
        # Check result dictionary
        assert result['actual_power'] == pytest.approx(-0.5, rel=1e-6)
        assert result['energy_loss'] == pytest.approx(0.5 * 1.0 * (1 - bess.tech_params['η_charge']), rel=1e-6)
    
    def test_step_discharge_energy_balance(self):
        """Test energy balance during discharging"""
        bess = BESSModel(1.0, 4.0, technology='modern_lfp', verbose=False)
        bess.soc = 0.8  # Start at 80% SOC
        initial_energy = bess.energy_stored
        
        result = bess.step(0.5, dt=1.0)  # Discharge 0.5 MW for 1 hour
        
        # Check that energy decreased (allow for floating point precision)
        assert bess.energy_stored <= initial_energy
        
        # Check result dictionary
        assert result['actual_power'] == pytest.approx(0.5, rel=1e-6)
        # Loss formula: P × dt × (1/η - 1)
        expected_loss = 0.5 * 1.0 * (1/bess.tech_params['η_discharge'] - 1)
        assert result['energy_loss'] == pytest.approx(expected_loss, rel=1e-6)
    
    def test_step_soc_clipping(self):
        """Test SOC clipping at bounds"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        
        # Test charging beyond maximum
        bess.soc = bess.tech_params['soc_max']
        result = bess.step(-1.0, dt=1.0)
        assert bess.soc <= bess.tech_params['soc_max']
        assert abs(result['actual_power']) < 0.1  # Very small or zero
        
        # Test discharging beyond minimum
        bess.soc = bess.tech_params['soc_min']
        result = bess.step(1.0, dt=1.0)
        assert bess.soc >= bess.tech_params['soc_min']
        assert abs(result['actual_power']) < 0.1  # Very small or zero


class TestBESSModelCycles:
    """Tests for cycle counting"""
    
    def test_cycle_counting_basic(self):
        """Test basic cycle counting"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        
        # Perform operations that should sum to 1 cycle
        bess.step(-1.0, dt=2.0)  # Charge 2 MWh
        bess.step(1.0, dt=2.0)   # Discharge 2 MWh
        
        # Total throughput = 4 MWh, usable capacity = ~3.4 MWh (85% of 4 MWh)
        expected_cycles = 4.0 / (2 * bess.usable_capacity_mwh)
        assert bess.cycles == pytest.approx(expected_cycles, rel=0.1)
    
    def test_cycle_counting_threshold(self):
        """Test that small energy movements don't count as cycles"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        
        # Very small charge (below threshold)
        bess.step(-0.001, dt=0.005)  # 0.005 kWh < 10 kWh threshold
        
        assert bess.cycles == 0.0
        assert bess.total_energy_charged == 0.0
        assert bess.total_energy_discharged == 0.0


class TestBESSModelVectorized:
    """Tests for vectorized next_state API"""
    
    def test_next_state_scalar_inputs(self):
        """Test next_state with scalar inputs"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        
        soc_new, p_act, loss = bess.next_state(0.5, -0.5, dt=1.0)
        
        assert isinstance(soc_new, float)
        assert isinstance(p_act, float)
        assert isinstance(loss, float)
        assert 0 <= soc_new <= 1
        assert p_act <= 0  # Charging (negative)
        assert loss >= 0
    
    def test_next_state_array_inputs(self):
        """Test next_state with array inputs"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        
        soc_array = np.array([0.3, 0.5, 0.7])
        p_req_array = np.array([-0.5, 0.0, 0.5])
        
        soc_new, p_act, loss = bess.next_state(soc_array, p_req_array, dt=0.5)
        
        assert soc_new.shape == soc_array.shape
        assert p_act.shape == p_req_array.shape
        assert loss.shape == soc_array.shape
        assert not np.isnan(soc_new).any()
        assert not np.isnan(p_act).any()
        assert not np.isnan(loss).any()
        assert np.all(bess.tech_params['soc_min'] <= soc_new)
        assert np.all(soc_new <= bess.tech_params['soc_max'])
    
    def test_next_state_dtype_preservation(self):
        """Test that next_state preserves dtype with arrays"""
        bess = BESSModel(1.0, 4.0, verbose=False)
        
        soc_array = np.array([0.5], dtype=np.float32)
        p_req_array = np.array([-0.5], dtype=np.float32)
        
        soc_new, p_act, loss = bess.next_state(soc_array, p_req_array, dt=1.0, dtype=np.float32)
        
        assert soc_new.dtype == np.float32
        assert p_act.dtype == np.float32
        assert loss.dtype == np.float32