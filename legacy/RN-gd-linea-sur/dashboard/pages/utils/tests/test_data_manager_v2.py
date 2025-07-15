"""
Tests for DataManager V2 - Refactored Architecture
Basic test coverage for new modular components
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import pandas as pd
import numpy as np

# Import modules to test
from ..data_manager_v2 import DataManagerV2, get_data_manager, reset_data_manager
from ..constants import DataStatus, STATIONS
from ..models import DataResult, DataManagerConfig


class TestDataManagerV2:
    """Test suite for DataManagerV2"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Reset singleton before each test
        reset_data_manager()
    
    def test_singleton_behavior(self):
        """Test that DataManager follows singleton pattern"""
        dm1 = get_data_manager()
        dm2 = get_data_manager()
        
        assert dm1 is dm2, "DataManager should be singleton"
        assert id(dm1) == id(dm2), "Should be same instance"
    
    def test_thread_safety(self):
        """Test thread-safe singleton creation"""
        instances = []
        
        def create_instance():
            dm = get_data_manager()
            instances.append(dm)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All instances should be the same
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance, "All instances should be the same"
    
    def test_initialization_with_config(self):
        """Test initialization with custom configuration"""
        config = DataManagerConfig(
            data_path="test/data",
            cache_enabled=False,
            max_retries=5,
            thread_safe=True
        )
        
        dm = DataManagerV2(config)
        assert dm.config["cache_enabled"] == False
        assert dm.config["max_retries"] == 5
        assert dm.config["thread_safe"] == True
    
    def test_get_nodes_fallback(self):
        """Test getting nodes with fallback data"""
        dm = get_data_manager()
        
        # Mock the system data to be None to force fallback
        with patch.object(dm, '_system_data', None):
            result = dm.get_nodes()
            
            assert isinstance(result, DataResult)
            assert result.status == DataStatus.FALLBACK
            assert result.data == STATIONS
            assert result.meta["source"] == "constants"
    
    def test_get_edges_fallback(self):
        """Test getting edges with fallback generation"""
        dm = get_data_manager()
        
        # Mock the system data to be None to force fallback
        with patch.object(dm, '_system_data', None):
            result = dm.get_edges()
            
            assert isinstance(result, DataResult)
            assert result.status == DataStatus.FALLBACK
            assert isinstance(result.data, list)
            assert len(result.data) > 0
            
            # Check first edge structure
            first_edge = result.data[0]
            assert "from_node" in first_edge
            assert "to_node" in first_edge
            assert "length_km" in first_edge
    
    def test_get_system_summary(self):
        """Test system summary generation"""
        dm = get_data_manager()
        
        result = dm.get_system_summary()
        
        assert isinstance(result, DataResult)
        assert result.data is not None
        assert "total_stations" in result.data
        assert "total_length_km" in result.data
        assert "system_voltage_kv" in result.data
    
    def test_get_system_status(self):
        """Test system status API"""
        dm = get_data_manager()
        
        response = dm.get_system_status()
        
        assert response["success"] == True
        assert "overall_status" in response["data"]
        assert "component_status" in response["data"]
        assert "cache_stats" in response["data"]
    
    def test_get_health_check(self):
        """Test health check API"""
        dm = get_data_manager()
        
        response = dm.get_health_check()
        
        assert response["success"] == True
        assert "status" in response["data"]
        assert "data_status" in response["data"]
        assert "performance" in response["data"]
        assert "thread_safety" in response["data"]
    
    def test_performance_tracking(self):
        """Test performance metrics tracking"""
        dm = get_data_manager()
        
        # Call some operations to generate metrics
        dm.get_nodes()
        dm.get_edges()
        dm.get_system_summary()
        
        summary = dm.get_performance_summary()
        
        assert summary["total_operations"] > 0
        assert summary["success_rate"] >= 0.0
        assert "avg_execution_time" in summary
    
    def test_clear_cache(self):
        """Test cache clearing functionality"""
        dm = get_data_manager()
        
        # Generate some performance metrics
        dm.get_nodes()
        dm.get_edges()
        
        # Clear cache
        dm.clear_cache()
        
        # Performance metrics should be cleared
        summary = dm.get_performance_summary()
        assert summary["total_operations"] == 0
    
    def test_reload_data(self):
        """Test data reloading functionality"""
        dm = get_data_manager()
        
        response = dm.reload_data()
        
        assert response["success"] == True
        assert response["data"]["reloaded"] == True
    
    @patch('pandas.read_csv')
    def test_historical_data_methods_with_no_data(self, mock_read_csv):
        """Test analytics methods when no historical data is available"""
        dm = get_data_manager()
        
        # Mock historical data to be None
        with patch.object(dm, '_historical_data', None):
            result = dm.get_hourly_voltage_analysis()
            assert result.status == DataStatus.ERROR
            assert "No historical data available" in result.meta["error"]
            
            result = dm.get_demand_voltage_correlation()
            assert result.status == DataStatus.ERROR
            
            result = dm.get_critical_events_analysis()
            assert result.status == DataStatus.ERROR
    
    def test_solar_simulation_methods(self):
        """Test solar simulation methods"""
        dm = get_data_manager()
        
        # Test PSFV only simulation
        result = dm.simulate_psfv_only("MAQUINCHAO", 2.0, 6)
        assert isinstance(result, DataResult)
        assert result.data is not None
        assert result.data["power_installed_mw"] == 2.0
        assert result.data["station"] == "MAQUINCHAO"
        
        # Test PSFV with BESS simulation
        result = dm.simulate_solar_with_bess("MAQUINCHAO", 2.0, 1.0, 4.0)
        assert isinstance(result, DataResult)
        assert result.data is not None
        assert result.data["psfv_power_mw"] == 2.0
        assert result.data["bess_power_mw"] == 1.0
        
        # Test daily solar profile
        result = dm.get_daily_solar_profile("MAQUINCHAO", 2.0, "winter")
        assert isinstance(result, DataResult)
        assert result.data is not None
        assert result.data["season"] == "winter"


class TestDataLoader:
    """Test suite for DataLoader component"""
    
    def test_retry_mechanism(self):
        """Test retry mechanism with exponential backoff"""
        from ..data_loaders import DataLoader
        
        loader = DataLoader(Path("/tmp"))
        
        # Mock a function that fails twice then succeeds
        call_count = 0
        def mock_load_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Mock failure")
            return "success"
        
        # Should succeed after retries
        result = loader._load_with_retry("test_key", mock_load_func)
        assert result == "success"
        assert call_count == 3
    
    def test_fallback_system_data_generation(self):
        """Test fallback system data generation"""
        from ..data_loaders import DataLoader
        
        loader = DataLoader(Path("/tmp"))
        fallback_data = loader._get_fallback_system_data()
        
        assert "nodes" in fallback_data
        assert "edges" in fallback_data
        assert "transformers" in fallback_data
        assert "system_summary" in fallback_data
        assert fallback_data["data_source"] == "FALLBACK"


class TestDataAnalytics:
    """Test suite for DataAnalytics component"""
    
    def test_find_continuous_events_edge_cases(self):
        """Test continuous events detection with edge cases"""
        from ..data_analytics import DataAnalytics
        
        analytics = DataAnalytics()
        
        # Create test data with event at end
        test_data = pd.DataFrame({
            'voltage': [0.95, 0.96, 0.4, 0.3, 0.2],  # Event at end
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='H')
        })
        
        events = analytics._find_continuous_events(test_data, "TEST_STATION", 0.5)
        
        # Should detect one event that goes to the end
        assert len(events) == 1
        assert events[0]['station'] == "TEST_STATION"
        assert events[0]['min_voltage'] == 0.2
    
    def test_memory_optimization(self):
        """Test memory optimization features"""
        from ..data_analytics import DataAnalytics
        
        analytics = DataAnalytics()
        
        # Test with large dataset
        large_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10000, freq='H'),
            'station': ['TEST'] * 10000,
            'voltage': np.random.normal(0.95, 0.05, 10000),
            'power': np.random.normal(2.0, 0.5, 10000)
        })
        
        # Should not crash with memory issues
        result = analytics.get_hourly_voltage_analysis(large_data)
        assert result.status != DataStatus.ERROR


class TestSolarBESSSimulator:
    """Test suite for SolarBESSSimulator component"""
    
    def test_solar_profile_generation(self):
        """Test solar profile generation"""
        from ..solar_bess_simulator import SolarBESSSimulator
        
        simulator = SolarBESSSimulator()
        
        # Test profile generation
        profile = simulator._generate_hourly_solar_profile(6, 2.0)  # June, 2 MW
        
        assert len(profile) == 24
        assert np.max(profile) > 0  # Should have some generation
        assert profile[0] == 0  # Should be zero at midnight
        assert profile[12] > profile[6]  # Should be higher at noon than at 6 AM
    
    def test_cache_functionality(self):
        """Test caching functionality"""
        from ..solar_bess_simulator import SolarBESSSimulator
        
        simulator = SolarBESSSimulator()
        
        # First call should be cache miss
        result1 = simulator.simulate_psfv_only("TEST", 2.0, 6)
        assert simulator.cache_misses > 0
        
        # Second call should be cache hit
        initial_misses = simulator.cache_misses
        result2 = simulator.simulate_psfv_only("TEST", 2.0, 6)
        assert simulator.cache_misses == initial_misses  # No new miss
        assert simulator.cache_hits > 0
    
    def test_aggressive_strategies(self):
        """Test aggressive BESS strategies"""
        from ..solar_bess_simulator import SolarBESSSimulator
        
        simulator = SolarBESSSimulator()
        
        # Test normal vs aggressive strategies
        normal_result = simulator.simulate_solar_with_bess(
            "TEST", 2.0, 1.0, 4.0, use_aggressive_strategies=False
        )
        
        aggressive_result = simulator.simulate_solar_with_bess(
            "TEST", 2.0, 1.0, 4.0, use_aggressive_strategies=True
        )
        
        # Both should succeed but with different parameters
        assert normal_result.status != DataStatus.ERROR
        assert aggressive_result.status != DataStatus.ERROR
        assert normal_result.data["use_aggressive_strategies"] == False
        assert aggressive_result.data["use_aggressive_strategies"] == True


# Integration Tests
class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_full_workflow(self):
        """Test complete workflow from data loading to analysis"""
        dm = get_data_manager()
        
        # 1. Check system status
        status_response = dm.get_system_status()
        assert status_response["success"] == True
        
        # 2. Get network data
        nodes_result = dm.get_nodes()
        edges_result = dm.get_edges()
        
        assert nodes_result.is_valid() or nodes_result.is_fallback()
        assert edges_result.is_valid() or edges_result.is_fallback()
        
        # 3. Run solar simulation
        solar_result = dm.simulate_psfv_only("MAQUINCHAO", 2.0)
        assert solar_result.status != DataStatus.ERROR
        
        # 4. Run BESS simulation
        bess_result = dm.simulate_solar_with_bess("MAQUINCHAO", 2.0, 1.0, 4.0)
        assert bess_result.status != DataStatus.ERROR
        
        # 5. Check performance
        perf_summary = dm.get_performance_summary()
        assert perf_summary["total_operations"] > 0
    
    def test_error_handling_chain(self):
        """Test error handling throughout the system"""
        dm = get_data_manager()
        
        # Force some error conditions and verify graceful handling
        with patch.object(dm.data_loader, 'load_system_data', side_effect=Exception("Test error")):
            # Should still function with fallback data
            nodes_result = dm.get_nodes()
            assert nodes_result.status == DataStatus.FALLBACK
        
        # Health check should still work
        health = dm.get_health_check()
        assert health["success"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])