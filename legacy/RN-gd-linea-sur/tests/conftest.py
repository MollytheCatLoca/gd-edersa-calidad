"""
Pytest configuration and shared fixtures for BESS testing
"""

import pytest
import sys
import os
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dashboard.pages.utils import DataManager
from src.battery.bess_model import BESSModel
from src.battery.bess_validator import BESSValidator


@pytest.fixture
def data_manager():
    """Provide DataManager instance for tests"""
    return DataManager()


@pytest.fixture
def sample_solar_profile():
    """Generate a typical daily solar profile"""
    hours = np.arange(24)
    # Simple gaussian-like solar profile peaking at noon
    solar = np.maximum(0, 
        2.0 * np.exp(-((hours - 12) ** 2) / 18) * (hours >= 6) * (hours <= 18)
    )
    return solar


@pytest.fixture
def bess_config_small():
    """Small BESS configuration for testing"""
    return {
        'power_mw': 0.5,
        'duration_h': 2,
        'capacity_mwh': 1.0
    }


@pytest.fixture
def bess_config_medium():
    """Medium BESS configuration for testing"""
    return {
        'power_mw': 1.0,
        'duration_h': 4,
        'capacity_mwh': 4.0
    }


@pytest.fixture
def stations():
    """List of test stations"""
    return ['MAQUINCHAO', 'LOS MENUCOS', 'JACOBACCI', 'PILCANIYEU']


@pytest.fixture
def strategies():
    """List of BESS strategies"""
    return ['cap_shaving', 'flat_day', 'night_shift', 'ramp_limit']


@pytest.fixture
def tolerance():
    """Numerical tolerance for comparisons"""
    return 1e-6


# Additional fixtures for comprehensive BESS testing
@pytest.fixture
def standard_bess():
    """Standard BESS configuration for testing"""
    return BESSModel(
        power_mw=1.0,
        duration_hours=4.0,
        technology='modern_lfp',
        topology='parallel_ac',
        verbose=False
    )


@pytest.fixture
def validator():
    """Standard validator for testing"""
    return BESSValidator('modern_lfp')


@pytest.fixture
def daily_solar_profile():
    """Generate a standard daily solar profile"""
    hours = np.arange(24)
    solar = np.maximum(0, 3 * np.sin((hours - 6) * np.pi / 12))
    return solar


@pytest.fixture
def variable_solar_profile():
    """Generate a variable solar profile with noise"""
    hours = np.arange(24)
    base = np.maximum(0, 3 * np.sin((hours - 6) * np.pi / 12))
    np.random.seed(42)  # For reproducibility
    noise = np.random.normal(0, 0.3, 24)
    return np.maximum(0, base + noise)


@pytest.fixture
def clear_day_profile():
    """Generate a perfect clear day profile"""
    hours = np.arange(24)
    return np.maximum(0, 5 * np.sin((hours - 6) * np.pi / 12))


@pytest.fixture
def extreme_ramp_profile():
    """Generate profile with extreme ramps for testing"""
    profile = np.zeros(24)
    profile[0:6] = 0
    profile[6:12] = np.linspace(0, 8, 6)  # Fast ramp up
    profile[12:18] = 8  # Flat
    profile[18:24] = np.linspace(8, 0, 6)  # Fast ramp down
    return profile


@pytest.fixture
def zero_solar_profile():
    """Generate zero solar profile for edge case testing"""
    return np.zeros(24)


# Parametrized fixtures for comprehensive testing
@pytest.fixture(params=['standard', 'modern_lfp', 'premium'])
def technology(request):
    """Parametrized technology fixture"""
    return request.param


@pytest.fixture(params=['parallel_ac', 'series_dc', 'hybrid'])
def topology(request):
    """Parametrized topology fixture"""
    return request.param


@pytest.fixture(params=[0.25, 0.5, 1.0])
def timestep(request):
    """Parametrized timestep fixture"""
    return request.param


# Helper functions for tests
def create_bess_arrays(n_steps):
    """Create empty arrays for BESS simulation"""
    return {
        'grid': np.zeros(n_steps),
        'battery': np.zeros(n_steps),
        'soc': np.zeros(n_steps),
        'curtailed': np.zeros(n_steps),
        'losses': np.zeros(n_steps)
    }


def assert_energy_balance(solar, grid, battery, curtailed, dt=1.0, tolerance=1e-6):
    """Assert energy balance: solar = grid + curtailed - battery"""
    for i in range(len(solar)):
        balance = solar[i] - grid[i] - curtailed[i] + battery[i]
        assert abs(balance) < tolerance, f"Energy balance error at step {i}: {balance}"


def assert_no_nan_values(*arrays):
    """Assert no NaN values in arrays"""
    for arr in arrays:
        assert not np.isnan(arr).any(), f"NaN values found in array: {arr}"


def assert_soc_bounds(soc, soc_min, soc_max, tolerance=1e-6):
    """Assert SOC is within bounds"""
    assert np.all(soc >= soc_min - tolerance), f"SOC below minimum: {np.min(soc)} < {soc_min}"
    assert np.all(soc <= soc_max + tolerance), f"SOC above maximum: {np.max(soc)} > {soc_max}"


# Mark slow tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )