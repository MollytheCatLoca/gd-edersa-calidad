# DataManager V2 - Refactored Architecture

## 📋 Overview

The DataManager V2 represents a complete refactoring of the original monolithic DataManager into a modular, thread-safe, and highly optimized architecture. This system provides centralized data management for the Dashboard with specialized modules for different responsibilities.

## 🏗️ Architecture

### Core Modules

```
dashboard/pages/utils/
├── constants.py              # Centralized constants and enumerations
├── models.py                 # Data models and type definitions
├── validation_schemas.py     # Pydantic validation schemas
├── data_loaders.py          # Data loading with retry and validation
├── data_analytics.py        # Statistical analysis and processing
├── solar_bess_simulator.py  # Solar PV and BESS simulations
├── data_manager_v2.py       # Main coordinator (thread-safe singleton)
├── data_manager.py          # Legacy version (kept for compatibility)
└── tests/                   # Test suite
    └── test_data_manager_v2.py
```

### Key Features

- **🔒 Thread-Safe**: All operations are thread-safe for multi-user environments
- **📊 Modular Design**: Specialized modules for different functionalities
- **🚀 Optimized Performance**: Vectorized operations and intelligent caching
- **✅ Robust Validation**: Pydantic schemas for data validation
- **🔄 Retry Logic**: Exponential backoff for resilient data loading
- **📈 Performance Monitoring**: Built-in metrics and profiling

## 🚀 Quick Start

### Basic Usage

```python
from dashboard.pages.utils.data_manager_v2 import get_data_manager

# Get singleton instance
dm = get_data_manager()

# Check system status
status = dm.get_system_status()
print(f"System status: {status.data['overall']}")

# Get network data
nodes = dm.get_nodes()
edges = dm.get_edges()
transformers = dm.get_transformers()

# Run analytics
voltage_analysis = dm.get_hourly_voltage_analysis()
correlations = dm.get_demand_voltage_correlation()
events = dm.get_critical_events_analysis()

# Simulate solar systems
solar_only = dm.simulate_psfv_only("MAQUINCHAO", power_mw=2.0, month=6)
solar_bess = dm.simulate_solar_with_bess(
    "MAQUINCHAO", 
    psfv_power_mw=2.0, 
    bess_power_mw=1.0, 
    bess_duration_h=4.0,
    strategy="time_shift"
)
```

### Using Individual Components

```python
from dashboard.pages.utils.data_loaders import DataLoader
from dashboard.pages.utils.data_analytics import DataAnalytics
from dashboard.pages.utils.solar_bess_simulator import SolarBESSimulator

# Use components directly
loader = DataLoader(project_root)
analytics = DataAnalytics()
simulator = SolarBESSimulator()

# Load data
system_data = loader.load_system_data()
historical_data = loader.load_historical_data()

# Analyze data
hourly_stats = analytics.get_hourly_voltage_analysis(historical_data.data)

# Simulate solar
solar_profile = simulator.simulate_psfv_only("MAQUINCHAO", 2.0, 6)
```

## 📊 Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   DataLoader    │    │  DataManager    │
│                 │───▶│                 │───▶│                 │
│ • JSON files    │    │ • Validation    │    │ • Coordination  │
│ • CSV files     │    │ • Retry logic   │    │ • Thread-safety │
│ • Fallbacks     │    │ • Caching       │    │ • API layer     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │ DataAnalytics   │◀────────────┤
                       │                 │             │
                       │ • Statistics    │             │
                       │ • Correlations  │             │
                       │ • Event detect  │             │
                       └─────────────────┘             │
                                                        │
                       ┌─────────────────┐             │
                       │SolarBESSimulator│◀────────────┘
                       │                 │
                       │ • PSFV models   │
                       │ • BESS control  │
                       │ • Optimization  │
                       └─────────────────┘
```

## 🔧 Configuration

### DataManager Configuration

```python
from dashboard.pages.utils.models import DataManagerConfig

config = DataManagerConfig(
    data_path="data/processed",
    fallback_path="data/fallback",
    cache_enabled=True,
    cache_size=128,
    max_retries=3,
    log_level="INFO",
    thread_safe=True,
    validation_enabled=True
)

dm = get_data_manager(config)
```

### Constants Configuration

```python
from dashboard.pages.utils.constants import SYSTEM, SOLAR, BESS

# System parameters
print(f"Nominal voltage: {SYSTEM['VOLTAGE_NOMINAL_KV']} kV")
print(f"Solar efficiency: {SOLAR['PANEL_EFFICIENCY']}")
print(f"BESS efficiency: {BESS['ROUND_TRIP_EFFICIENCY']}")
```

## 📈 Performance Optimizations

### Memory Optimization
- **Pre-allocation**: Numpy arrays pre-allocated for large datasets
- **Chunked Processing**: Large CSV files processed in chunks
- **Lazy Loading**: Data loaded only when needed
- **Memory Monitoring**: Built-in memory usage tracking

### Computation Optimization
- **Vectorization**: Numpy operations instead of loops
- **Caching**: LRU cache for expensive operations
- **Parallel Processing**: Thread-safe operations
- **Incremental Updates**: Only recompute changed data

### Example Performance Metrics
```python
dm = get_data_manager()

# Run some operations
nodes = dm.get_nodes()
analysis = dm.get_hourly_voltage_analysis()

# Get performance summary
perf = dm.get_perf_summary()
print(f"Operations: {perf['total']}")
print(f"Success rate: {perf['success_rate']:.2%}")
print(f"Average time: {perf['avg_time']:.3f}s")
```

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
pytest dashboard/pages/utils/tests/test_data_manager_v2.py -v

# Run specific test
pytest dashboard/pages/utils/tests/test_data_manager_v2.py::TestDataManagerV2::test_singleton_behavior -v

# Run with coverage
pytest --cov=dashboard/pages/utils dashboard/pages/utils/tests/ --cov-report=html
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflows
- **Performance Tests**: Load and stress testing
- **Thread Safety Tests**: Concurrent access validation

## 🔍 Validation

### Pydantic Schemas
The system uses Pydantic for robust data validation:

```python
from dashboard.pages.utils.validation_schemas import (
    validate_system_data,
    validate_solar_configuration,
    validate_bess_configuration
)

# Validate system data
result = validate_system_data(raw_data)
if result.is_valid:
    print("Data validation passed")
else:
    print(f"Validation errors: {result.errors}")

# Validate solar configuration
solar_config = {
    "power_mw": 2.0,
    "technology": "sat_bifacial",
    "tilt_angle": 35.0,
    "azimuth_angle": 180.0
}
result = validate_solar_configuration(solar_config)
```

## 📊 Monitoring

### Health Checks
```python
dm = get_data_manager()

# System health
health = dm.get_health_check()
print(f"Status: {health['data']['status']}")
print(f"Cache stats: {health['data']['cache_stats']}")

# Performance metrics
perf = dm.get_perf_summary()
print(f"Slowest operation: {perf['slowest']}")
```

### Logging
```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The system will log:
# - Data loading operations
# - Validation results
# - Performance warnings
# - Error conditions
```

## 🚨 Error Handling

### Data Status Levels
```python
from dashboard.pages.utils.constants import DataStatus

# Data status types:
# DataStatus.REAL     - Real data from files
# DataStatus.PARTIAL  - Some real data, some missing
# DataStatus.FALLBACK - Using fallback data
# DataStatus.ERROR    - Error loading data
```

### Error Recovery
```python
dm = get_data_manager()

# Check data status
nodes = dm.get_nodes()
if nodes.status == DataStatus.FALLBACK:
    print("Using fallback data - check data files")
elif nodes.status == DataStatus.ERROR:
    print("Error loading data - check logs")

# Reload data if needed
reload_result = dm.reload_data()
if reload_result["success"]:
    print("Data reloaded successfully")
```

## 🔄 Migration from V1

### Compatibility Layer
The system maintains compatibility with the original DataManager:

```python
# Legacy code continues to work
from dashboard.pages.utils.data_manager import DataManager

# But new code should use V2
from dashboard.pages.utils.data_manager_v2 import get_data_manager
```

### Migration Steps
1. **Update imports**: Change to V2 imports
2. **Update API calls**: Use new DataResult format
3. **Update error handling**: Use new status system
4. **Update tests**: Migrate to new test structure

## 📚 API Reference

### DataManagerV2 Methods

#### Data Access
- `get_nodes()` → `DataResult[List[NodeData]]`
- `get_edges()` → `DataResult[List[EdgeData]]`
- `get_transformers()` → `DataResult[Dict[str, TransformerData]]`

#### Analytics
- `get_hourly_voltage_analysis()` → `DataResult[Dict[str, Dict[int, Dict[str, float]]]]`
- `get_demand_voltage_correlation()` → `DataResult[Dict[str, Dict[str, Any]]]`
- `get_critical_events_analysis()` → `DataResult[Dict[str, Any]]`

#### Simulation
- `simulate_psfv_only(station, power_mw, month)` → `DataResult[Dict[str, Any]]`
- `simulate_solar_with_bess(station, psfv_power_mw, bess_power_mw, bess_duration_h, ...)` → `DataResult[Dict[str, Any]]`

#### Utilities
- `get_system_status()` → `APIResponse`
- `reload_data()` → `APIResponse`
- `get_perf_summary()` → `Dict[str, Any]`
- `clear_caches()` → `None`

## 💡 Best Practices

### Performance
- Use caching for expensive operations
- Monitor memory usage with large datasets
- Profile operations with timing decorator
- Clear caches periodically

### Error Handling
- Always check `DataResult.ok()` before using data
- Handle fallback scenarios gracefully
- Log errors appropriately
- Use retry logic for transient failures

### Threading
- Use singleton pattern for shared state
- Avoid blocking operations in main thread
- Use thread-safe operations when available
- Monitor for race conditions

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**
   ```python
   # Wrong
   from dashboard.pages.utils.data_manager import DataManager
   
   # Correct
   from dashboard.pages.utils.data_manager_v2 import get_data_manager
   ```

2. **Thread Safety Issues**
   ```python
   # Always use singleton
   dm = get_data_manager()  # Correct
   dm = DataManagerV2()     # Don't do this
   ```

3. **Data Status Issues**
   ```python
   result = dm.get_nodes()
   if result.ok():  # Check status first
       nodes = result.data
   else:
       print(f"Error: {result.meta}")
   ```

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('dashboard.pages.utils').setLevel(logging.DEBUG)

# Enable profiling
from dashboard.pages.utils.data_analytics import DataAnalytics
analytics = DataAnalytics(enable_profiling=True)
```

## 📞 Support

For questions or issues with the DataManager V2 system:

1. Check the logs for error messages
2. Review the test suite for usage examples
3. Consult the validation schemas for data requirements
4. Use the health check endpoint for system status

## 🔄 Future Enhancements

- **Async Support**: Add async/await support for I/O operations
- **Database Integration**: Add database backend support
- **Real-time Updates**: Add WebSocket support for real-time data
- **Distributed Caching**: Add Redis support for distributed caching
- **Metrics Export**: Add Prometheus metrics export