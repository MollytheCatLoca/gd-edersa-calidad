#!/usr/bin/env python3
import xlrd
import statistics
from datetime import datetime
import os
import math

def read_station_data(file_path, max_rows=1000):
    """Read station measurement data from XLS file"""
    try:
        workbook = xlrd.open_workbook(file_path)
        sheet = workbook.sheet_by_index(0)
        
        # Find data start
        data_start = None
        for i in range(min(20, sheet.nrows)):
            try:
                if isinstance(sheet.cell_value(i, 1), (int, float)) and sheet.cell_value(i, 1) > 0:
                    data_start = i
                    break
            except:
                continue
        
        if data_start is None:
            return []
        
        data = []
        for row_idx in range(data_start, min(sheet.nrows, data_start + max_rows)):
            try:
                p_kw = float(sheet.cell_value(row_idx, 1))
                q_kvar = float(sheet.cell_value(row_idx, 2))
                v1 = float(sheet.cell_value(row_idx, 3))
                v2 = float(sheet.cell_value(row_idx, 4))
                v3 = float(sheet.cell_value(row_idx, 5)) if sheet.ncols > 5 else v2
                
                # Determine voltage level based on magnitude
                v_avg = (v1 + v2 + v3) / 3
                if v_avg > 15000:  # 33 kV system (phase voltage ~19 kV)
                    voltage_level = 33
                    v_ll_kv = v_avg * 1.732 / 1000  # Convert phase to line voltage
                else:  # 13.2 kV system (phase voltage ~7.6 kV)
                    voltage_level = 13.2
                    v_ll_kv = v_avg * 1.732 / 1000
                
                data.append({
                    'p_mw': p_kw / 1000,
                    'q_mvar': q_kvar / 1000,
                    'v_ll_kv': v_ll_kv,
                    'voltage_level': voltage_level
                })
            except:
                continue
        
        return data
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def analyze_line_section(from_data, to_data, section_name, distance_km):
    """Analyze a line section between two stations"""
    if not from_data or not to_data:
        return None
    
    # Get averages
    p_from = statistics.mean([d['p_mw'] for d in from_data])
    p_to = statistics.mean([d['p_mw'] for d in to_data])
    v_from = statistics.mean([d['v_ll_kv'] for d in from_data])
    v_to = statistics.mean([d['v_ll_kv'] for d in to_data])
    
    # Calculate losses
    p_loss = p_from - p_to
    loss_percent = (p_loss / p_from * 100) if p_from > 0 else 0
    
    # Voltage drop
    v_drop = v_from - v_to
    v_drop_percent = (v_drop / v_from * 100) if v_from > 0 else 0
    
    return {
        'section': section_name,
        'distance_km': distance_km,
        'p_from_mw': p_from,
        'p_to_mw': p_to,
        'p_loss_mw': p_loss,
        'loss_percent': loss_percent,
        'v_from_kv': v_from,
        'v_to_kv': v_to,
        'v_drop_kv': v_drop,
        'v_drop_percent': v_drop_percent,
        'loss_per_km': (p_loss / distance_km * 1000) if distance_km > 0 else 0  # kW/km
    }

def main():
    print("=== LÍNEA SUR - COMPREHENSIVE SYSTEM ANALYSIS ===")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    base_path = '/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data/Registros Línea Sur'
    
    # Define stations and their data files
    stations_data = {}
    
    # Load data for each station
    print("\n1. LOADING STATION DATA...")
    
    # Pilcaniyeu (33 kV)
    file_path = f'{base_path}/Pilcaniyeu2024/1224/ET4PI_33 122024.xls'
    if os.path.exists(file_path):
        data = read_station_data(file_path)
        if data:
            stations_data['Pilcaniyeu_33'] = data
            print(f"  Pilcaniyeu 33kV: {len(data)} records loaded")
    
    # Jacobacci feeders
    file_north = f'{base_path}/Jacobacci2025/0125/ET2IJ_NORTE 0125.xls'
    file_south = f'{base_path}/Jacobacci2025/0125/ET2IJ_SUR 0125.xls'
    
    jacob_data = []
    for f in [file_north, file_south]:
        if os.path.exists(f):
            data = read_station_data(f)
            jacob_data.extend(data)
    
    if jacob_data:
        stations_data['Jacobacci'] = jacob_data
        print(f"  Jacobacci (combined): {len(jacob_data)} records loaded")
    
    # Maquinchao
    file_path = f'{base_path}/Maquinchao2025/0225/ET2MA 0225.xls'
    if os.path.exists(file_path):
        data = read_station_data(file_path)
        if data:
            stations_data['Maquinchao'] = data
            print(f"  Maquinchao: {len(data)} records loaded")
    
    # Los Menucos
    file_path = f'{base_path}/Menucos2025/0225/ET2LM 0225.xls'
    if os.path.exists(file_path):
        data = read_station_data(file_path)
        if data:
            stations_data['Los_Menucos'] = data
            print(f"  Los Menucos: {len(data)} records loaded")
    
    # 2. STATION ANALYSIS
    print("\n2. STATION ANALYSIS SUMMARY")
    print(f"{'Station':<15} {'Voltage':<12} {'P_avg(MW)':<12} {'Q_avg(MVAr)':<12} {'V_min(kV)':<12} {'V_avg(kV)':<12} {'PF_avg':<10}")
    print("-" * 95)
    
    station_summary = {}
    
    for station, data in stations_data.items():
        if data:
            p_values = [d['p_mw'] for d in data]
            q_values = [d['q_mvar'] for d in data]
            v_values = [d['v_ll_kv'] for d in data]
            voltage_level = data[0]['voltage_level']
            
            # Calculate power factor
            pf_values = []
            for d in data:
                s = math.sqrt(d['p_mw']**2 + d['q_mvar']**2)
                pf = d['p_mw'] / s if s > 0 else 0
                pf_values.append(pf)
            
            summary = {
                'voltage_level': voltage_level,
                'p_avg': statistics.mean(p_values),
                'q_avg': statistics.mean(q_values),
                'v_min': min(v_values),
                'v_avg': statistics.mean(v_values),
                'pf_avg': statistics.mean(pf_values),
                'v_min_pu': min(v_values) / voltage_level,
                'hours_below_095': sum(1 for v in v_values if v < 0.95 * voltage_level) * 0.25
            }
            
            station_summary[station] = summary
            
            print(f"{station:<15} {voltage_level:<12.1f} {summary['p_avg']:<12.2f} {summary['q_avg']:<12.2f} "
                  f"{summary['v_min']:<12.1f} {summary['v_avg']:<12.1f} {summary['pf_avg']:<10.3f}")
    
    # 3. LINE SECTION ANALYSIS
    print("\n3. LINE SECTION ANALYSIS (33 kV System)")
    print("=" * 80)
    
    # Note: We need to estimate 33kV values from 13.2kV measurements
    # Power remains the same, voltage needs transformation ratio adjustment
    
    # Estimate transformer ratios and system configuration
    print("\nNote: Jacobacci, Maquinchao, and Los Menucos measurements are at 13.2 kV level")
    print("33 kV system values estimated using transformer ratio 33/13.2 = 2.5")
    
    # Create estimated 33kV data
    stations_33kv = {}
    
    # Pilcaniyeu already at 33kV
    if 'Pilcaniyeu_33' in stations_data:
        stations_33kv['Pilcaniyeu'] = stations_data['Pilcaniyeu_33']
    
    # Transform other stations to 33kV equivalent
    for station in ['Jacobacci', 'Maquinchao', 'Los_Menucos']:
        if station in stations_data:
            # For 33kV analysis, we keep power the same but adjust voltage
            stations_33kv[station] = [{
                'p_mw': d['p_mw'],
                'q_mvar': d['q_mvar'],
                'v_ll_kv': d['v_ll_kv'] * 2.5,  # Transform to 33kV side
                'voltage_level': 33
            } for d in stations_data[station]]
    
    # Analyze line sections
    sections = [
        ('Pilcaniyeu', 'Jacobacci', 'Pilcaniyeu-Jacobacci', 150),
        ('Jacobacci', 'Maquinchao', 'Jacobacci-Maquinchao', 70),
        ('Maquinchao', 'Los_Menucos', 'Maquinchao-Los Menucos', 50)
    ]
    
    print(f"\n{'Section':<25} {'Distance':<10} {'P_in(MW)':<10} {'P_out(MW)':<10} {'Loss(MW)':<10} {'Loss(%)':<10} {'kW/km':<10}")
    print("-" * 90)
    
    total_distance = 0
    total_loss = 0
    
    for from_st, to_st, section_name, distance in sections:
        if from_st in stations_33kv and to_st in stations_33kv:
            analysis = analyze_line_section(
                stations_33kv[from_st],
                stations_33kv[to_st],
                section_name,
                distance
            )
            
            if analysis:
                print(f"{analysis['section']:<25} {analysis['distance_km']:<10} "
                      f"{analysis['p_from_mw']:<10.2f} {analysis['p_to_mw']:<10.2f} "
                      f"{analysis['p_loss_mw']:<10.2f} {analysis['loss_percent']:<10.1f} "
                      f"{analysis['loss_per_km']:<10.1f}")
                
                total_distance += distance
                total_loss += analysis['p_loss_mw']
    
    if total_distance > 0:
        print("-" * 90)
        print(f"{'TOTAL':<25} {total_distance:<10} {'--':<10} {'--':<10} "
              f"{total_loss:<10.2f} {'--':<10} {total_loss/total_distance*1000:<10.1f}")
    
    # 4. CRITICAL POINTS FOR DG
    print("\n4. CRITICAL POINTS FOR DISTRIBUTED GENERATION")
    print("=" * 60)
    
    critical_stations = []
    
    for station, summary in station_summary.items():
        score = 0
        issues = []
        
        # Voltage criteria
        if summary['v_min_pu'] < 0.95:
            score += 3
            issues.append(f"Low voltage: {summary['v_min_pu']:.3f} pu")
        
        if summary['hours_below_095'] > 10:
            score += 2
            issues.append(f"Frequent violations: {summary['hours_below_095']:.0f} hours < 0.95pu")
        
        # Power factor
        if summary['pf_avg'] < 0.95:
            score += 2
            issues.append(f"Low PF: {summary['pf_avg']:.3f}")
        
        # Reactive power
        if abs(summary['q_avg']) > 0.3 * summary['p_avg']:
            score += 1
            issues.append(f"High Q: {summary['q_avg']:.2f} MVAr")
        
        if score > 0:
            critical_stations.append({
                'station': station,
                'score': score,
                'issues': issues,
                'p_avg': summary['p_avg'],
                'v_min_pu': summary['v_min_pu'],
                'voltage_level': summary['voltage_level']
            })
    
    # Sort by criticality
    critical_stations.sort(key=lambda x: x['score'], reverse=True)
    
    print("\nRanking by criticality (max score: 8):")
    
    for i, cs in enumerate(critical_stations, 1):
        print(f"\n{i}. {cs['station']} (Score: {cs['score']}/8)")
        print(f"   Voltage level: {cs['voltage_level']} kV")
        print(f"   Average demand: {cs['p_avg']:.2f} MW")
        print(f"   Issues:")
        for issue in cs['issues']:
            print(f"   - {issue}")
        
        # DG sizing recommendation
        dg_min = cs['p_avg'] * 0.3
        dg_max = cs['p_avg'] * 0.5
        print(f"   → Recommended DG: {dg_min:.1f} - {dg_max:.1f} MW")
    
    # 5. SAVE RESULTS
    with open('comprehensive_analysis_results.txt', 'w') as f:
        f.write("LÍNEA SUR - COMPREHENSIVE ANALYSIS RESULTS\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("STATION SUMMARY\n")
        for station, summary in station_summary.items():
            f.write(f"\n{station}:\n")
            for key, value in summary.items():
                f.write(f"  {key}: {value}\n")
        
        f.write("\n\nRECOMMENDATIONS FOR DG IMPLEMENTATION\n")
        for i, cs in enumerate(critical_stations, 1):
            f.write(f"\n{i}. {cs['station']}\n")
            f.write(f"   Priority Score: {cs['score']}/8\n")
            f.write(f"   Recommended DG: {cs['p_avg']*0.3:.1f} - {cs['p_avg']*0.5:.1f} MW\n")
    
    print("\n\nResults saved to: comprehensive_analysis_results.txt")

if __name__ == "__main__":
    main()