#!/usr/bin/env python3
"""
Test script para identificar el error exacto del callback
NO USA HARDCODED - MUESTRA ERRORES EXPLÍCITOS
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

print("=== TEST OPTIMIZATION ERROR ===")

# Test 1: Can we import config_loader?
print("\n1. Testing config import:")
try:
    from src.config.config_loader import get_config
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Can we create config instance?
print("\n2. Testing config instance:")
try:
    config = get_config()
    print("✓ get_config() successful")
except Exception as e:
    print(f"✗ get_config() failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Can we get economic params?
print("\n3. Testing economic params:")
try:
    params = config.get_economic_params()
    print(f"✓ get_economic_params() successful, got {len(params)} params")
    print("\nParams retrieved:")
    for key, value in params.items():
        print(f"  - {key}: {value}")
except Exception as e:
    print(f"✗ get_economic_params() failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check config file directly
print("\n4. Checking config file:")
config_file = project_root / "config" / "parameters.yaml"
print(f"Config file path: {config_file}")
print(f"Config file exists: {config_file.exists()}")
if config_file.exists():
    print(f"Config file size: {config_file.stat().st_size} bytes")

# Test 5: Simulate callback parameters
print("\n5. Simulating callback parameters:")
try:
    # Simulate callback inputs
    n_clicks = 1
    pv_ratio = 1.2
    bess_hours = 4.0
    q_ratio = 0.3
    cluster_data = [{"potencia_kva": 630, "cluster_id": 1}]
    
    print(f"n_clicks: {n_clicks} (type: {type(n_clicks).__name__})")
    print(f"pv_ratio: {pv_ratio} (type: {type(pv_ratio).__name__})")
    print(f"bess_hours: {bess_hours} (type: {type(bess_hours).__name__})")
    print(f"q_ratio: {q_ratio} (type: {type(q_ratio).__name__})")
    print(f"cluster_data: {type(cluster_data).__name__} with {len(cluster_data)} items")
    
    # Calculate values
    total_kva = sum(t.get('potencia_kva', 0) for t in cluster_data)
    total_mw = total_kva / 1000 * 0.9
    
    pv_mw = total_mw * pv_ratio
    bess_mwh = pv_mw * bess_hours
    q_mvar = pv_mw * q_ratio
    
    print(f"\nCalculated values:")
    print(f"Total kVA: {total_kva}")
    print(f"Total MW: {total_mw:.2f}")
    print(f"PV MW: {pv_mw:.2f}")
    print(f"BESS MWh: {bess_mwh:.2f}")
    print(f"Q MVAr: {q_mvar:.2f}")
    
    # Calculate CAPEX
    capex_pv = pv_mw * params['pv_capex_usd_mw']
    capex_bess = bess_mwh * params['bess_capex_usd_mwh']
    capex_statcom = q_mvar * params['statcom_capex_usd_mvar']
    
    print(f"\nCAPEX calculation:")
    print(f"PV CAPEX: ${capex_pv:,.0f}")
    print(f"BESS CAPEX: ${capex_bess:,.0f}")
    print(f"STATCOM CAPEX: ${capex_statcom:,.0f}")
    print(f"Total CAPEX: ${capex_pv + capex_bess + capex_statcom:,.0f}")
    
    print("\n✓ All calculations successful!")
    
except Exception as e:
    print(f"\n✗ Calculation failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    
print("\n=== TEST COMPLETE ===")