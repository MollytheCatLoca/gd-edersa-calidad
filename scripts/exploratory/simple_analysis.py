import csv
import os
from datetime import datetime

def process_csv_file(file_path):
    """Process CSV file with basic Python"""
    print(f"\nProcessing: {file_path}")
    
    data = []
    with open(file_path, 'r', encoding='latin-1') as f:
        # Skip first 5 lines
        for _ in range(5):
            next(f)
        
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        print(f"Columns: {header[:9]}")  # First 9 columns
        
        for i, row in enumerate(reader):
            if i < 10:  # Show first 10 rows
                if len(row) >= 9:
                    try:
                        p_active = float(row[0])
                        q_reactive = float(row[1])
                        v1 = float(row[2])
                        v2 = float(row[3])
                        v3 = float(row[4])
                        i1 = float(row[5])
                        i2 = float(row[6])
                        i3 = float(row[7])
                        date_str = row[8]
                        
                        # Calculate averages
                        v_avg = (v1 + v2 + v3) / 3 / 1000  # Convert to kV
                        i_avg = (i1 + i2 + i3) / 3
                        p_mw = p_active / 1000  # Convert to MW
                        q_mvar = q_reactive / 1000
                        
                        print(f"Date: {date_str}, P: {p_mw:.3f} MW, Q: {q_mvar:.3f} MVAr, V: {v_avg:.2f} kV, I: {i_avg:.1f} A")
                        
                        data.append({
                            'date': date_str,
                            'p_mw': p_mw,
                            'q_mvar': q_mvar,
                            'v_kv': v_avg,
                            'i_a': i_avg
                        })
                    except Exception as e:
                        print(f"Error processing row {i}: {e}")
    
    return data

# Process available CSV files
csv_files = [
    '/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/Registros Línea Sur/Pilcaniyeu2024/1121/ET4PI_33.csv',
    '/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/Registros Línea Sur/Pilcaniyeu2024/1121/ET4PI_13.csv'
]

for file_path in csv_files:
    if os.path.exists(file_path):
        data = process_csv_file(file_path)