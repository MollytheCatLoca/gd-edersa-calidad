#!/usr/bin/env python3
"""
Debug Excel file reading - find out what's really in the files
"""

import pandas as pd
from pathlib import Path
import sys

# Test with one specific file
test_file = Path("/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/Registros Línea Sur/Pilcaniyeu2024/0124/ET4PI_33  202401.xls")

print(f"Debugging file: {test_file.name}")
print("="*60)

# Try 1: Read with no parameters
print("\n1. Read with default parameters:")
try:
    df1 = pd.read_excel(test_file)
    print(f"Shape: {df1.shape}")
    print(f"Columns: {df1.columns.tolist()}")
    print("\nFirst 5 rows:")
    print(df1.head())
    print("\nData types:")
    print(df1.dtypes)
except Exception as e:
    print(f"Error: {e}")

# Try 2: Read without header
print("\n" + "="*60)
print("2. Read without header (header=None):")
try:
    df2 = pd.read_excel(test_file, header=None)
    print(f"Shape: {df2.shape}")
    print("\nFirst 10 rows, first 4 columns:")
    for i in range(min(10, len(df2))):
        row = df2.iloc[i]
        print(f"Row {i}: [{row[0]}, {row[1]}, {row[2] if len(row) > 2 else 'N/A'}, {row[3] if len(row) > 3 else 'N/A'}]")
except Exception as e:
    print(f"Error: {e}")

# Try 3: Try specific row as header
print("\n" + "="*60)
print("3. Try with specific header row:")
for header_row in [0, 1, 2, 3, 4, 5]:
    print(f"\nTrying header={header_row}:")
    try:
        df3 = pd.read_excel(test_file, header=header_row)
        print(f"  Columns: {df3.columns.tolist()[:5]}...")
        if len(df3) > 0:
            first_val = df3.iloc[0, 0]
            print(f"  First data value: {first_val} (type: {type(first_val)})")
    except Exception as e:
        print(f"  Error: {e}")

# Try 4: Skip rows
print("\n" + "="*60)
print("4. Try skipping rows:")
for skip in [3, 4, 5, 6]:
    print(f"\nSkipping {skip} rows:")
    try:
        df4 = pd.read_excel(test_file, skiprows=skip)
        print(f"  Shape: {df4.shape}")
        if len(df4) > 0:
            print(f"  First row: {df4.iloc[0].tolist()[:4]}...")
    except Exception as e:
        print(f"  Error: {e}")