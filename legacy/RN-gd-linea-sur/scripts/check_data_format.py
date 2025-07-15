#!/usr/bin/env python3
"""
Script to check the actual format of EPRE Excel files
"""

import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Test file
test_file = project_root / "data" / "Registros Línea Sur" / "Pilcaniyeu2024" / "0124" / "ET4PI_33  202401.xls"

if not test_file.exists():
    print(f"File not found: {test_file}")
    sys.exit(1)

print(f"Checking file: {test_file.name}")
print("="*60)

# Read without any processing
df_raw = pd.read_excel(test_file, header=None)

print(f"Shape: {df_raw.shape}")
print("\nFirst 15 rows:")
print(df_raw.head(15))

print("\n" + "="*60)
print("Looking for data start...")

# Find where actual data starts
for i in range(min(20, len(df_raw))):
    row = df_raw.iloc[i]
    print(f"Row {i}: {row[0]} | {row[1] if len(row) > 1 else 'N/A'} | Type: {type(row[0])}")
    
    # Check if this looks like a date
    if pd.notna(row[0]):
        try:
            # Try to parse as date
            if isinstance(row[0], (int, float)) or '/' in str(row[0]) or '-' in str(row[0]):
                print(f"  -> Possible date row at {i}")
        except:
            pass

print("\n" + "="*60)
print("Checking with pandas read_excel auto-detection:")

# Try with pandas auto-detection
df_auto = pd.read_excel(test_file)
print(f"Auto-detected shape: {df_auto.shape}")
print("\nColumn names:")
print(df_auto.columns.tolist())
print("\nFirst 5 rows:")
print(df_auto.head())

print("\nData types:")
print(df_auto.dtypes)