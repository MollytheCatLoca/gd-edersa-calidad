#!/usr/bin/env python3
"""
Test script para verificar cálculos de optimización
"""

import pandas as pd
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

# Test 1: Load cluster data
print("=== TEST 1: Loading cluster data ===")
cluster_file = BASE_DIR / 'reports/clustering/optimization/clusters_optimization_data.parquet'
df = pd.read_parquet(cluster_file)
print(f"Loaded {len(df)} clusters")
print(f"Columns: {df.columns.tolist()[:10]}...")

# Test 2: Get first cluster data
print("\n=== TEST 2: First cluster data ===")
cluster_data = df.iloc[0].to_dict()
print(f"Cluster ID: {cluster_data['cluster_id']}")
print(f"Peak demand: {cluster_data['peak_demand_mw']} MW")

# Test 3: Test calculate_flows_realtime function
print("\n=== TEST 3: Testing calculate_flows_realtime ===")
try:
    from dashboard.pages.optimization_analysis import calculate_flows_realtime
    
    pv_mw = cluster_data['peak_demand_mw'] * 1.0  # ratio 1.0
    bess_mwh = 0
    q_mvar = pv_mw * 0.1
    
    print(f"Inputs: pv_mw={pv_mw}, bess_mwh={bess_mwh}, q_mvar={q_mvar}")
    
    results = calculate_flows_realtime(cluster_data, pv_mw, bess_mwh, q_mvar)
    
    print(f"\nResults keys: {list(results.keys())}")
    print(f"CAPEX total: ${results['capex']['total']/1e6:.1f}M")
    print(f"NPV: ${results['metrics']['npv_usd']/1e6:.1f}M")
    print(f"TIR: {results['metrics']['irr_percent']:.1f}%")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test config loader
print("\n=== TEST 4: Testing config loader ===")
try:
    from src.config.config_loader import get_config
    config = get_config()
    params = config.get_economic_params()
    print(f"Config loaded successfully")
    print(f"PV CAPEX: ${params['capex']['pv_capex_usd_mw']/1e6:.1f}M/MW")
except Exception as e:
    print(f"ERROR loading config: {e}")
    import traceback
    traceback.print_exc()