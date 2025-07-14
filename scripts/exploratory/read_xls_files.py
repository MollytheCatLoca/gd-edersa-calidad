#!/usr/bin/env python3
import xlrd
import statistics
from datetime import datetime
import os

def read_xls_file(file_path, max_rows=100):
    """Read measurement data from XLS file using xlrd"""
    print(f"\nReading: {file_path}")
    
    try:
        # Open the workbook
        workbook = xlrd.open_workbook(file_path)
        sheet = workbook.sheet_by_index(0)
        
        print(f"  Sheet name: {sheet.name}")
        print(f"  Rows: {sheet.nrows}, Columns: {sheet.ncols}")
        
        # Find data start row - look for numeric data in column 1 (P column)
        data_start_row = None
        for row_idx in range(min(20, sheet.nrows)):
            try:
                # Check if column 1 (P) has numeric data
                cell_value = sheet.cell_value(row_idx, 1)
                if isinstance(cell_value, (int, float)) and cell_value > 0:
                    data_start_row = row_idx
                    break
            except:
                continue
        
        if data_start_row is None:
            print("  Could not find numeric data start")
            # Show first 10 rows to debug
            print("  First 10 rows:")
            for i in range(min(10, sheet.nrows)):
                row_data = []
                for j in range(min(5, sheet.ncols)):
                    try:
                        row_data.append(str(sheet.cell_value(i, j))[:20])
                    except:
                        row_data.append("--")
                print(f"    Row {i}: {row_data}")
            return []
        
        print(f"  Data starts at row {data_start_row}")
        
        # Read data
        data = []
        rows_read = 0
        
        for row_idx in range(data_start_row, min(sheet.nrows, data_start_row + max_rows)):
            try:
                # Read values from columns (date is in col 0, P in col 1, etc)
                date_value = sheet.cell_value(row_idx, 0)
                p_kw = float(sheet.cell_value(row_idx, 1))
                q_kvar = float(sheet.cell_value(row_idx, 2))
                v1 = float(sheet.cell_value(row_idx, 3))
                v2 = float(sheet.cell_value(row_idx, 4))
                
                # Some files have 3 voltage columns, some have currents too
                if sheet.ncols > 5:
                    v3 = float(sheet.cell_value(row_idx, 5))
                else:
                    v3 = v2  # Assume balanced if only 2 phases
                
                # Check if current columns exist
                if sheet.ncols > 8:
                    i1 = float(sheet.cell_value(row_idx, 6))
                    i2 = float(sheet.cell_value(row_idx, 7))
                    i3 = float(sheet.cell_value(row_idx, 8))
                else:
                    # Calculate current from power and voltage
                    v_avg_v = (v1 + v2 + v3) / 3
                    s_kva = (p_kw**2 + q_kvar**2)**0.5
                    i_avg = s_kva / (v_avg_v * 1.732 / 1000) if v_avg_v > 0 else 0
                    i1 = i2 = i3 = i_avg
                if isinstance(date_value, float):
                    # Excel date number
                    date_str = f"Excel date: {date_value}"
                else:
                    date_str = str(date_value)
                
                # Create record
                record = {
                    'p_mw': p_kw / 1000,
                    'q_mvar': q_kvar / 1000,
                    'v1_kv': v1 / 1000,
                    'v2_kv': v2 / 1000,
                    'v3_kv': v3 / 1000,
                    'v_avg_kv': (v1 + v2 + v3) / 3000,
                    'i1_a': i1,
                    'i2_a': i2,
                    'i3_a': i3,
                    'i_avg_a': (i1 + i2 + i3) / 3,
                    'date': date_str
                }
                
                # Calculate S and FP
                s_mva = (record['p_mw']**2 + record['q_mvar']**2)**0.5
                record['s_mva'] = s_mva
                record['fp'] = record['p_mw'] / s_mva if s_mva > 0 else 0
                
                data.append(record)
                rows_read += 1
                
                # Show first few records
                if rows_read <= 3:
                    print(f"    Record {rows_read}: P={record['p_mw']:.2f} MW, V={record['v_avg_kv']:.1f} kV, FP={record['fp']:.3f}")
                    
            except Exception as e:
                if rows_read < 3:
                    print(f"    Error reading row {row_idx}: {e}")
                continue
        
        print(f"  Total records read: {len(data)}")
        return data
        
    except Exception as e:
        print(f"  Error opening file: {e}")
        return []

def analyze_all_xls_files():
    """Analyze all available XLS files"""
    base_path = '/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/Registros Línea Sur'
    
    # Find all .xls files
    xls_files = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.xls') and not file.startswith('~'):
                xls_files.append(os.path.join(root, file))
    
    print(f"Found {len(xls_files)} XLS files")
    
    # Group by station
    stations = {}
    for file_path in xls_files:
        # Extract station name from path
        parts = file_path.split('/')
        if 'Pilcaniyeu' in file_path:
            if '_33' in file_path:
                station = 'Pilcaniyeu_33kV'
            elif '_13' in file_path:
                station = 'Pilcaniyeu_13kV'
            else:
                station = 'Pilcaniyeu'
        elif 'Jacobacci' in file_path:
            if 'NORTE' in file_path.upper():
                station = 'Jacobacci_Norte'
            elif 'SUR' in file_path.upper():
                station = 'Jacobacci_Sur'
            else:
                station = 'Jacobacci'
        elif 'Menucos' in file_path:
            station = 'Los_Menucos'
        elif 'Maquinchao' in file_path:
            station = 'Maquinchao'
        else:
            continue
            
        if station not in stations:
            stations[station] = []
        stations[station].append(file_path)
    
    # Analyze latest file for each station
    all_results = []
    
    for station, files in stations.items():
        # Sort files to get the latest
        files.sort()
        latest_file = files[-1]
        
        # Determine nominal voltage
        nominal_kv = 33 if '33' in station or station in ['Jacobacci_Norte', 'Jacobacci_Sur', 'Los_Menucos', 'Maquinchao'] else 13.2
        
        # Read and analyze
        data = read_xls_file(latest_file, max_rows=200)
        
        if data:
            # Calculate statistics
            p_values = [d['p_mw'] for d in data]
            v_values = [d['v_avg_kv'] for d in data]
            fp_values = [d['fp'] for d in data]
            
            results = {
                'station': station,
                'file': os.path.basename(latest_file),
                'records': len(data),
                'p_max_mw': max(p_values),
                'p_min_mw': min(p_values),
                'p_avg_mw': statistics.mean(p_values),
                'v_max_kv': max(v_values),
                'v_min_kv': min(v_values),
                'v_avg_kv': statistics.mean(v_values),
                'v_min_pu': min(v_values) / nominal_kv,
                'v_avg_pu': statistics.mean(v_values) / nominal_kv,
                'fp_min': min(fp_values),
                'fp_avg': statistics.mean(fp_values),
                'nominal_kv': nominal_kv
            }
            
            all_results.append(results)
    
    return all_results

def main():
    print("=== LÍNEA SUR - XLS FILE ANALYSIS ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    results = analyze_all_xls_files()
    
    if results:
        # Sort by distance from Pilcaniyeu
        station_order = ['Pilcaniyeu_33kV', 'Pilcaniyeu_13kV', 'Jacobacci_Norte', 'Jacobacci_Sur', 'Maquinchao', 'Los_Menucos']
        results_sorted = sorted(results, key=lambda x: station_order.index(x['station']) if x['station'] in station_order else 99)
        
        print("\n\n=== STATION ANALYSIS SUMMARY ===")
        print(f"{'Station':<20} {'File':<25} {'P_avg(MW)':<12} {'V_min(kV)':<12} {'V_min(pu)':<12} {'FP_avg':<10}")
        print("-" * 95)
        
        for r in results_sorted:
            print(f"{r['station']:<20} {r['file']:<25} {r['p_avg_mw']:<12.2f} {r['v_min_kv']:<12.1f} {r['v_min_pu']:<12.3f} {r['fp_avg']:<10.3f}")
        
        # Voltage drop analysis
        print("\n\n=== VOLTAGE DROP ANALYSIS ===")
        print("(From Pilcaniyeu to Los Menucos)")
        
        pilc_33 = next((r for r in results if r['station'] == 'Pilcaniyeu_33kV'), None)
        jacob_n = next((r for r in results if r['station'] == 'Jacobacci_Norte'), None)
        maqui = next((r for r in results if r['station'] == 'Maquinchao'), None)
        menucos = next((r for r in results if r['station'] == 'Los_Menucos'), None)
        
        if pilc_33:
            print(f"\nPilcaniyeu (Origin): {pilc_33['v_avg_kv']:.1f} kV ({pilc_33['v_avg_pu']:.3f} pu)")
            
            if jacob_n:
                drop_kv = pilc_33['v_avg_kv'] - jacob_n['v_avg_kv']
                drop_pct = (drop_kv / pilc_33['v_avg_kv']) * 100
                print(f"Jacobacci (150 km): {jacob_n['v_avg_kv']:.1f} kV ({jacob_n['v_avg_pu']:.3f} pu) - Drop: {drop_kv:.1f} kV ({drop_pct:.1f}%)")
            
            if maqui:
                drop_kv = pilc_33['v_avg_kv'] - maqui['v_avg_kv']
                drop_pct = (drop_kv / pilc_33['v_avg_kv']) * 100
                print(f"Maquinchao (220 km): {maqui['v_avg_kv']:.1f} kV ({maqui['v_avg_pu']:.3f} pu) - Drop: {drop_kv:.1f} kV ({drop_pct:.1f}%)")
            
            if menucos:
                drop_kv = pilc_33['v_avg_kv'] - menucos['v_avg_kv']
                drop_pct = (drop_kv / pilc_33['v_avg_kv']) * 100
                print(f"Los Menucos (270 km): {menucos['v_avg_kv']:.1f} kV ({menucos['v_avg_pu']:.3f} pu) - Drop: {drop_kv:.1f} kV ({drop_pct:.1f}%)")
        
        # Critical stations
        print("\n\n=== CRITICAL STATIONS FOR DG ===")
        critical = [(r, r['v_min_pu']) for r in results if r['v_min_pu'] < 0.95]
        critical.sort(key=lambda x: x[1])
        
        for r, v_pu in critical:
            print(f"\n{r['station']}:")
            print(f"  Minimum voltage: {r['v_min_kv']:.1f} kV ({v_pu:.3f} pu)")
            print(f"  Average demand: {r['p_avg_mw']:.2f} MW")
            print(f"  Power factor: {r['fp_avg']:.3f}")
            print(f"  → Recommended DG: {r['p_avg_mw'] * 0.3:.1f} - {r['p_avg_mw'] * 0.5:.1f} MW")

if __name__ == "__main__":
    main()