#!/usr/bin/env python3
"""
Fase 0 - Script 5: Cálculo de Distancia Eléctrica y Caída de Tensión
===================================================================

Este script calcula las impedancias y caídas de tensión basándose en:
- La topología MST reconstruida
- Los valores de impedancia del documento teórico
- Las fórmulas de caída de tensión para sistemas trifásicos

Valores de referencia:
- 1/0 AWG: R=0.55, X=0.48 Ω/km (ramales rurales)
- 4/0 AWG: R=0.22, X=0.45 Ω/km (líneas troncales)
"""

import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configuración de rutas
BASE_DIR = Path("/Users/maxkeczeli/Proyects/gd-edersa-calidad")
INPUT_FILE = BASE_DIR / "data/processed/electrical_analysis/transformadores_mst_topology.csv"
OUTPUT_DIR = BASE_DIR / "data/processed/electrical_analysis"

# Parámetros eléctricos
VOLTAGE_NOM = 13.2  # kV nominal del sistema
ROUTING_FACTOR = 1.3  # Factor de corrección de enrutamiento

# Tabla de impedancias por tipo de conductor (Ω/km)
IMPEDANCE_TABLE = {
    'rural': {'R': 0.55, 'X': 0.48},      # 1/0 AWG para ramales rurales
    'troncal': {'R': 0.22, 'X': 0.45},    # 4/0 AWG para líneas troncales
    'urbano': {'R': 0.17, 'X': 0.42}      # 336.4 MCM para zonas urbanas
}

# Factor de potencia por tipo de zona
POWER_FACTOR = {
    'Rural': 0.90,
    'Periurbano': 0.87,
    'Urbano': 0.85,
    'default': 0.88
}

def load_data():
    """Cargar datos con topología MST"""
    print("Cargando datos...")
    df = pd.read_csv(INPUT_FILE)
    
    # Filtrar registros válidos
    df = df[df['numero_saltos'] >= 0].copy()
    
    print(f"✓ {len(df)} transformadores con topología válida")
    print(f"✓ {df['Alimentador'].nunique()} alimentadores")
    
    return df

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcular distancia en km entre dos puntos"""
    R = 6371  # Radio de la Tierra en km
    
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c

def classify_line_segment(parent_kva, child_kva, is_trunk, tipo_zona='Rural'):
    """
    Clasificar el tipo de segmento de línea para asignar impedancia
    """
    # Si es línea troncal (conecta directamente con subestación o tiene mucha carga aguas abajo)
    if is_trunk or parent_kva > 1000:
        return 'troncal'
    # Si es zona urbana
    elif tipo_zona == 'Urbano':
        return 'urbano'
    # Por defecto, rural
    else:
        return 'rural'

def calculate_electrical_distance(df_feeder):
    """
    Calcular distancia eléctrica acumulada para cada transformador
    """
    results = []
    
    # Crear diccionario para búsqueda rápida
    trafo_dict = df_feeder.set_index('Codigo').to_dict('index')
    
    for idx, row in df_feeder.iterrows():
        codigo = row['Codigo']
        padre = row['padre_mst']
        
        # Si es conectado directamente a subestación
        if padre == 'SUBSTATION' or pd.isna(padre):
            # Distancia desde subestación
            dist_geo = haversine_distance(
                row['Coord_Y'], row['Coord_X'],
                row['substation_y'], row['substation_x']
            )
            
            # Aplicar factor de enrutamiento
            dist_real = dist_geo * ROUTING_FACTOR
            
            # Clasificar segmento
            line_type = classify_line_segment(
                0,  # Subestación
                row['kVA_aguas_abajo'],
                True,  # Es troncal
                row.get('tipo_zona', 'Rural')
            )
            
            # Obtener impedancia
            R_km = IMPEDANCE_TABLE[line_type]['R']
            X_km = IMPEDANCE_TABLE[line_type]['X']
            
            # Impedancia total del segmento
            R_total = R_km * dist_real
            X_total = X_km * dist_real
            Z_total = np.sqrt(R_total**2 + X_total**2)
            
        else:
            # Buscar padre
            if padre in trafo_dict:
                padre_data = trafo_dict[padre]
                
                # Distancia entre padre e hijo
                dist_geo = haversine_distance(
                    row['Coord_Y'], row['Coord_X'],
                    padre_data['Coord_Y'], padre_data['Coord_X']
                )
                
                # Aplicar factor de enrutamiento
                dist_real = dist_geo * ROUTING_FACTOR
                
                # Clasificar segmento
                is_trunk = padre_data.get('numero_saltos', 0) <= 2
                line_type = classify_line_segment(
                    padre_data.get('kVA_aguas_abajo', 0),
                    row['kVA_aguas_abajo'],
                    is_trunk,
                    row.get('tipo_zona', 'Rural')
                )
                
                # Obtener impedancia del segmento
                R_km = IMPEDANCE_TABLE[line_type]['R']
                X_km = IMPEDANCE_TABLE[line_type]['X']
                
                R_segment = R_km * dist_real
                X_segment = X_km * dist_real
                
                # Impedancia acumulada (del padre + segmento)
                R_total = padre_data.get('R_acumulada', 0) + R_segment
                X_total = padre_data.get('X_acumulada', 0) + X_segment
                Z_total = np.sqrt(R_total**2 + X_total**2)
                
                dist_real = padre_data.get('distancia_electrica_km', 0) + dist_real
            else:
                # Si no se encuentra el padre, usar valores por defecto
                dist_real = 0
                R_total = 0
                X_total = 0
                Z_total = 0
                line_type = 'rural'
        
        # Agregar resultados
        results.append({
            'Codigo': codigo,
            'distancia_electrica_km': dist_real,
            'R_acumulada': R_total,
            'X_acumulada': X_total,
            'Z_acumulada': Z_total,
            'tipo_conductor': line_type
        })
        
        # Actualizar diccionario para hijos
        trafo_dict[codigo].update(results[-1])
    
    return pd.DataFrame(results)

def calculate_voltage_drop(row):
    """
    Calcular caída de tensión usando la fórmula trifásica:
    ΔV = √3 × I × (R×cos(φ) + X×sin(φ))
    """
    # Obtener factor de potencia
    fp = POWER_FACTOR.get(row.get('tipo_zona', 'Rural'), POWER_FACTOR['default'])
    
    # Calcular corriente nominal
    S_kva = row['Potencia']
    I_nom = S_kva / (np.sqrt(3) * VOLTAGE_NOM)  # Corriente en A
    
    # Aplicar factor de carga estimado (asumiendo 70% de carga promedio)
    factor_carga = 0.7
    I_actual = I_nom * factor_carga
    
    # Calcular componentes
    cos_phi = fp
    sin_phi = np.sqrt(1 - cos_phi**2)
    
    # Caída de tensión línea a línea (V)
    delta_V = np.sqrt(3) * I_actual * (
        row['R_acumulada'] * cos_phi + 
        row['X_acumulada'] * sin_phi
    )
    
    # Caída porcentual
    delta_V_percent = (delta_V / (VOLTAGE_NOM * 1000)) * 100
    
    # Tensión estimada en el transformador
    V_trafo = VOLTAGE_NOM - (delta_V / 1000)  # en kV
    
    # Índice de debilidad (0-1, donde 1 es muy débil)
    weakness_index = min(delta_V_percent / 10, 1.0)  # Normalizado a 10% máximo
    
    return {
        'corriente_estimada_A': I_actual,
        'caida_tension_V': delta_V,
        'caida_tension_percent': delta_V_percent,
        'tension_estimada_kV': V_trafo,
        'factor_potencia_estimado': fp,
        'indice_debilidad_electrica': weakness_index
    }

def calculate_dynamic_sensitivity(row):
    """
    Calcular sensibilidad a hundimientos dinámicos
    """
    # Factor de arranque típico para motores (5-7 veces corriente nominal)
    motor_start_factor = 6.0
    
    # Asumir 30% de carga tipo motor
    motor_fraction = 0.3
    
    # Corriente de arranque equivalente
    I_start = row['corriente_estimada_A'] * motor_fraction * motor_start_factor
    
    # Hundimiento de tensión durante arranque
    delta_V_start = np.sqrt(3) * I_start * row['Z_acumulada']
    delta_V_start_percent = (delta_V_start / (VOLTAGE_NOM * 1000)) * 100
    
    # Clasificar sensibilidad
    if delta_V_start_percent > 15:
        sensitivity = 'Muy Alta'
    elif delta_V_start_percent > 10:
        sensitivity = 'Alta'
    elif delta_V_start_percent > 5:
        sensitivity = 'Media'
    else:
        sensitivity = 'Baja'
    
    return {
        'hundimiento_arranque_percent': delta_V_start_percent,
        'sensibilidad_dinamica': sensitivity
    }

def process_feeder(feeder_name, df_feeder):
    """Procesar un alimentador completo"""
    print(f"\n  Procesando: {feeder_name} ({len(df_feeder)} transformadores)")
    
    # Calcular distancias eléctricas
    df_electrical = calculate_electrical_distance(df_feeder)
    
    # Merge con datos originales
    df_result = df_feeder.merge(df_electrical, on='Codigo', how='left')
    
    # Calcular caídas de tensión
    voltage_drops = df_result.apply(calculate_voltage_drop, axis=1)
    df_voltage = pd.DataFrame(list(voltage_drops))
    
    # Calcular sensibilidad dinámica
    dynamic_sens = df_result.apply(calculate_dynamic_sensitivity, axis=1)
    df_dynamic = pd.DataFrame(list(dynamic_sens))
    
    # Combinar todos los resultados
    df_final = pd.concat([df_result, df_voltage, df_dynamic], axis=1)
    
    # Estadísticas del alimentador
    stats = {
        'impedancia_max_ohm': df_final['Z_acumulada'].max(),
        'caida_tension_max_percent': df_final['caida_tension_percent'].max(),
        'transformadores_fuera_limite': (df_final['caida_tension_percent'] > 5).sum(),
        'debilidad_promedio': df_final['indice_debilidad_electrica'].mean()
    }
    
    return df_final, stats

def visualize_voltage_profile(df_results, save_path):
    """Visualizar perfil de tensión por alimentador"""
    # Seleccionar top alimentadores problemáticos
    voltage_by_feeder = df_results.groupby('Alimentador').agg({
        'caida_tension_percent': ['mean', 'max'],
        'Codigo': 'count'
    }).round(2)
    
    voltage_by_feeder.columns = ['caida_promedio', 'caida_maxima', 'num_trafos']
    voltage_by_feeder = voltage_by_feeder[voltage_by_feeder['num_trafos'] >= 10]
    top_feeders = voltage_by_feeder.nlargest(10, 'caida_maxima')
    
    # Crear visualización
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Gráfico 1: Distribución de caídas de tensión
    for feeder in top_feeders.index[:5]:
        data = df_results[df_results['Alimentador'] == feeder]
        data_sorted = data.sort_values('numero_saltos')
        ax1.plot(data_sorted['numero_saltos'], 
                data_sorted['caida_tension_percent'],
                marker='o', alpha=0.7, label=feeder[:20])
    
    ax1.axhline(y=5, color='red', linestyle='--', label='Límite 5%')
    ax1.set_xlabel('Número de Saltos desde Subestación')
    ax1.set_ylabel('Caída de Tensión (%)')
    ax1.set_title('Perfil de Caída de Tensión por Alimentador')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Gráfico 2: Mapa de calor de debilidad eléctrica
    pivot_data = df_results.pivot_table(
        values='indice_debilidad_electrica',
        index='Alimentador',
        columns='numero_saltos',
        aggfunc='mean'
    )
    
    # Seleccionar alimentadores con más datos
    pivot_data = pivot_data.loc[top_feeders.index[:15]]
    
    sns.heatmap(pivot_data, cmap='YlOrRd', cbar_kws={'label': 'Índice de Debilidad'},
                ax=ax2, vmin=0, vmax=1)
    ax2.set_title('Mapa de Debilidad Eléctrica por Posición en Red')
    ax2.set_xlabel('Número de Saltos desde Subestación')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    """Función principal"""
    print("=" * 80)
    print("CÁLCULO DE DISTANCIA ELÉCTRICA Y CAÍDA DE TENSIÓN")
    print("=" * 80)
    
    # Cargar datos
    df = load_data()
    
    # Procesar por alimentador
    all_results = []
    feeder_stats = {}
    
    for feeder in df['Alimentador'].unique():
        df_feeder = df[df['Alimentador'] == feeder].copy()
        
        if len(df_feeder) < 2:
            continue
        
        df_result, stats = process_feeder(feeder, df_feeder)
        all_results.append(df_result)
        feeder_stats[feeder] = stats
    
    # Combinar resultados
    df_final = pd.concat(all_results, ignore_index=True)
    
    # Guardar resultados
    output_file = OUTPUT_DIR / "transformadores_distancia_electrica.csv"
    df_final.to_csv(output_file, index=False)
    print(f"\n✓ Resultados guardados en: {output_file}")
    
    # Generar visualizaciones
    viz_dir = OUTPUT_DIR / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    viz_path = viz_dir / "voltage_drop_profiles.png"
    visualize_voltage_profile(df_final, viz_path)
    print(f"✓ Visualización guardada en: {viz_path}")
    
    # Generar reporte
    report = {
        'timestamp': datetime.now().isoformat(),
        'parametros_utilizados': {
            'tension_nominal_kV': VOLTAGE_NOM,
            'factor_enrutamiento': ROUTING_FACTOR,
            'impedancias_ohm_km': IMPEDANCE_TABLE,
            'factores_potencia': POWER_FACTOR
        },
        'estadisticas_globales': {
            'transformadores_analizados': len(df_final),
            'impedancia_maxima_ohm': df_final['Z_acumulada'].max(),
            'caida_tension_promedio_percent': df_final['caida_tension_percent'].mean(),
            'caida_tension_maxima_percent': df_final['caida_tension_percent'].max(),
            'transformadores_fuera_limite_5%': (df_final['caida_tension_percent'] > 5).sum(),
            'porcentaje_fuera_limite': ((df_final['caida_tension_percent'] > 5).sum() / len(df_final)) * 100
        },
        'distribucion_sensibilidad_dinamica': df_final['sensibilidad_dinamica'].value_counts().to_dict(),
        'top_10_puntos_debiles': df_final.nlargest(10, 'indice_debilidad_electrica')[
            ['Codigo', 'Alimentador', 'numero_saltos', 'Z_acumulada', 
             'caida_tension_percent', 'indice_debilidad_electrica']
        ].to_dict('records'),
        'alimentadores_criticos': {k: v for k, v in feeder_stats.items() 
                                 if v['caida_tension_max_percent'] > 7}
    }
    
    report_file = OUTPUT_DIR / "electrical_distance_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Reporte guardado en: {report_file}")
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS")
    print("=" * 80)
    print(f"• Transformadores analizados: {len(df_final):,}")
    print(f"• Impedancia máxima: {df_final['Z_acumulada'].max():.2f} Ω")
    print(f"• Caída de tensión promedio: {df_final['caida_tension_percent'].mean():.2f}%")
    print(f"• Caída de tensión máxima: {df_final['caida_tension_percent'].max():.2f}%")
    print(f"• Transformadores fuera de límite (>5%): {(df_final['caida_tension_percent'] > 5).sum()} "
          f"({((df_final['caida_tension_percent'] > 5).sum() / len(df_final)) * 100:.1f}%)")
    
    # Distribución de sensibilidad
    print("\nDistribución de Sensibilidad Dinámica:")
    sens_dist = df_final['sensibilidad_dinamica'].value_counts()
    for sens, count in sens_dist.items():
        print(f"  - {sens}: {count} ({(count/len(df_final))*100:.1f}%)")
    
    # Top puntos débiles
    print("\nTop 5 Puntos Más Débiles Eléctricamente:")
    top_weak = df_final.nlargest(5, 'indice_debilidad_electrica')
    for _, row in top_weak.iterrows():
        print(f"  - {row['Codigo']} ({row['Alimentador']}): "
              f"ΔV={row['caida_tension_percent']:.1f}%, "
              f"Z={row['Z_acumulada']:.1f}Ω, "
              f"Debilidad={row['indice_debilidad_electrica']:.3f}")

if __name__ == "__main__":
    main()