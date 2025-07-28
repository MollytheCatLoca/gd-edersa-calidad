#!/usr/bin/env python3
"""
Test del error específico del callback
"""

# Test 1: Import config_loader at module level
try:
    from src.config.config_loader import get_config
    print("✓ Import at module level works")
    config = get_config()
    print("✓ get_config() works")
    params = config.get_economic_params()
    print(f"✓ get_economic_params() works, got {len(params)} params")
except Exception as e:
    print(f"✗ Error at module level: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Import inside function
def test_import_in_function():
    try:
        from src.config.config_loader import get_config
        print("✓ Import inside function works")
        config = get_config()
        print("✓ get_config() inside function works")
        params = config.get_economic_params()
        print(f"✓ get_economic_params() inside function works, got {len(params)} params")
        return True
    except Exception as e:
        print(f"✗ Error inside function: {e}")
        import traceback
        traceback.print_exc()
        return False

print("\nTesting import inside function:")
test_import_in_function()

# Test 3: Check if it's a path issue
import sys
from pathlib import Path
print(f"\nPython path includes:")
for p in sys.path[:5]:
    print(f"  - {p}")

print(f"\nCurrent working directory: {Path.cwd()}")
print(f"Config file exists: {(Path.cwd() / 'config' / 'parameters.yaml').exists()}")