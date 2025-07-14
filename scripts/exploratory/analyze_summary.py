#!/usr/bin/env python3
import subprocess
import sys

# Try to use pandas, install if needed
try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pandas", "numpy", "openpyxl", "xlrd"])
    import pandas as pd
    import numpy as np

def analyze_summary_data():
    """Analyze the summary data file"""
    file_path = '/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/Datos Mayo 2024-Julio 2024 (Con Res 286 EPRE) (incluido gastos Los Menuc....xls'
    
    try:
        # Try to read the Excel file
        xl_file = pd.ExcelFile(file_path)
        print(f"Excel file sheets: {xl_file.sheet_names}")
        
        # Read first sheet
        if xl_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=xl_file.sheet_names[0])
            print(f"\nShape: {df.shape}")
            print(f"\nColumns: {list(df.columns)}")
            print(f"\nFirst few rows:")
            print(df.head(10))
            
            # Try other sheets if available
            for sheet in xl_file.sheet_names[:3]:  # First 3 sheets
                print(f"\n\n=== Sheet: {sheet} ===")
                df = pd.read_excel(file_path, sheet_name=sheet)
                print(f"Shape: {df.shape}")
                print(f"Columns: {list(df.columns)[:10]}")  # First 10 columns
                if not df.empty:
                    print(df.head(5))
                    
    except Exception as e:
        print(f"Error reading summary file: {e}")

def analyze_cost_data():
    """Analyze Los Menucos cost data"""
    files = [
        '/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/Costo Los Menucos.xlsx',
        '/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/LOS MENUCOS.xlsx'
    ]
    
    for file_path in files:
        print(f"\n\n=== Analyzing: {file_path.split('/')[-1]} ===")
        try:
            xl_file = pd.ExcelFile(file_path)
            print(f"Sheets: {xl_file.sheet_names}")
            
            for sheet in xl_file.sheet_names:
                print(f"\n--- Sheet: {sheet} ---")
                df = pd.read_excel(file_path, sheet_name=sheet)
                print(f"Shape: {df.shape}")
                if not df.empty:
                    print(df.head())
                    
                    # Look for cost-related columns
                    cost_cols = [col for col in df.columns if any(term in str(col).lower() for term in ['cost', 'precio', 'usd', '$', 'monto', 'valor'])]
                    if cost_cols:
                        print(f"\nCost-related columns: {cost_cols}")
                        
        except Exception as e:
            print(f"Error: {e}")

def analyze_single_station_file():
    """Try to analyze a single station file with different approaches"""
    file_path = '/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/Registros Línea Sur/Pilcaniyeu2024/1024/ET4PI_33 1024.xls'
    
    print(f"\n\n=== Analyzing single station file ===")
    print(f"File: {file_path}")
    
    try:
        # Try different approaches
        # Approach 1: Standard read
        df = pd.read_excel(file_path)
        print(f"\nApproach 1 - Standard read:")
        print(f"Shape: {df.shape}")
        print(df.head(10))
        
    except Exception as e1:
        print(f"Standard read failed: {e1}")
        
        try:
            # Approach 2: Read with xlrd engine
            df = pd.read_excel(file_path, engine='xlrd')
            print(f"\nApproach 2 - xlrd engine:")
            print(f"Shape: {df.shape}")
            print(df.head(10))
            
        except Exception as e2:
            print(f"xlrd engine failed: {e2}")
            
            try:
                # Approach 3: Read all sheets
                xl_file = pd.ExcelFile(file_path)
                print(f"\nSheets available: {xl_file.sheet_names}")
                
                for sheet in xl_file.sheet_names:
                    print(f"\n--- Sheet: {sheet} ---")
                    df = pd.read_excel(file_path, sheet_name=sheet, header=None)
                    print(f"Shape: {df.shape}")
                    print(df.head(15))  # Show more rows to find data start
                    
            except Exception as e3:
                print(f"All approaches failed: {e3}")

if __name__ == "__main__":
    print("=== LÍNEA SUR DATA ANALYSIS ===\n")
    
    # Analyze summary data
    analyze_summary_data()
    
    # Analyze cost data
    analyze_cost_data()
    
    # Try single station file
    analyze_single_station_file()