#!/usr/bin/env python3
"""
Fase 0 - Script 7: Features de Modos de Falla y Vulnerabilidad
=============================================================

Este script crea features basadas en los modos de falla descritos en el documento:
- Estrés térmico (sobrecarga)
- Estrés dieléctrico (problemas de tensión)
- Features de vecindad y propagación
- Índices compuestos de vulnerabilidad
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import cdist
import warnings
warnings.filterwarnings('ignore')

# Configuración de rutas
BASE_DIR = Path("/Users/maxkeczeli/Proyects/gd-edersa-calidad")
INPUT_FILE = BASE_DIR / "data/processed/electrical_analysis/transformadores_carga_estimada.csv"
OUTPUT_DIR = BASE_DIR / "data/processed/electrical_analysis"

# Umbrales basados en estándares y documento teórico
THRESHOLDS = {
    'caida_tension': {
        'normal': 3.0,      # < 3% excelente
        'aceptable': 5.0,   # 3-5% aceptable
        'limite': 7.0,      # 5-7% en el límite
        'critico': 10.0     # > 10% crítico
    },
    'utilizacion': {
        'normal': 0.70,     # < 70% normal
        'alto': 0.85,       # 70-85% alto
        'sobrecarga': 1.0,  # 85-100% riesgo
        'critico': 1.2      # > 120% crítico
    },
    'temperatura': {
        # Basado en IEEE C57.91 - pérdida de vida acelerada
        'nominal': 65,      # °C sobre ambiente
        'alarma': 80,       # Inicio de envejecimiento acelerado
        'critico': 95       # Pérdida de vida severa
    }
}

def calculate_thermal_stress_index(row):
    """
    Calcular índice de estrés térmico basado en utilización y tipo de carga
    """
    # Factor base de utilización
    utilization = row['factor_utilizacion_pico']
    
    # Ajuste por tipo de carga (industrial = más ciclos térmicos)
    load_type_factor = {
        'industrial_pesado': 1.3,
        'industrial_ligero': 1.2,
        'rural_agricola': 1.15,
        'comercial': 1.05,
        'mixto': 1.0,
        'residencial': 0.95
    }
    type_factor = load_type_factor.get(row['tipo_carga'], 1.0)
    
    # Ajuste por factor de potencia bajo (más pérdidas I²R)
    fp_penalty = max(0, (0.9 - row['factor_potencia_estimado']) * 2)
    
    # Ajuste por impedancia de línea (más pérdidas en la red)
    z_factor = 1 + 0.1 * row.get('indice_debilidad_electrica', 0)
    
    # Índice compuesto
    thermal_index = utilization * type_factor * (1 + fp_penalty) * z_factor
    
    # Normalizar a escala 0-1
    thermal_stress = min(thermal_index / THRESHOLDS['utilizacion']['critico'], 1.0)
    
    # Clasificar nivel
    if thermal_index > THRESHOLDS['utilizacion']['critico']:
        level = 'Crítico'
    elif thermal_index > THRESHOLDS['utilizacion']['sobrecarga']:
        level = 'Sobrecarga'
    elif thermal_index > THRESHOLDS['utilizacion']['alto']:
        level = 'Alto'
    else:
        level = 'Normal'
    
    # Estimar temperatura hot-spot (simplificado)
    # ΔT = K * I² donde K depende del diseño del transformador
    temp_rise = 65 * (thermal_index ** 2)  # Temperatura sobre ambiente
    
    # Factor de pérdida de vida (Arrhenius simplificado)
    if temp_rise > THRESHOLDS['temperatura']['nominal']:
        life_loss_factor = 2 ** ((temp_rise - THRESHOLDS['temperatura']['nominal']) / 10)
    else:
        life_loss_factor = 1.0
    
    return {
        'indice_estres_termico_v2': thermal_stress,
        'nivel_estres_termico': level,
        'temperatura_estimada_rise': temp_rise,
        'factor_perdida_vida': life_loss_factor,
        'años_vida_perdidos_anual': max(0, (life_loss_factor - 1) * 0.5)  # Aproximación
    }

def calculate_dielectric_stress_index(row):
    """
    Calcular índice de estrés dieléctrico basado en calidad de tensión
    """
    # Factor base: caída de tensión
    voltage_drop = row['caida_tension_percent']
    
    # Sensibilidad a transitorios
    dynamic_sensitivity = row.get('hundimiento_arranque_percent', 0)
    
    # Factor por posición en la red (nodos hoja más vulnerables)
    position_factor = 1.2 if row.get('es_nodo_hoja', False) else 1.0
    
    # Factor por número de saltos (más lejos = más eventos acumulados)
    hops_factor = 1 + 0.05 * row.get('numero_saltos', 0)
    
    # Índice base de estrés dieléctrico
    if voltage_drop > THRESHOLDS['caida_tension']['critico']:
        base_stress = 1.0
    elif voltage_drop > THRESHOLDS['caida_tension']['limite']:
        base_stress = 0.8
    elif voltage_drop > THRESHOLDS['caida_tension']['aceptable']:
        base_stress = 0.6
    elif voltage_drop > THRESHOLDS['caida_tension']['normal']:
        base_stress = 0.4
    else:
        base_stress = 0.2
    
    # Ajuste por sensibilidad dinámica
    dynamic_factor = min(dynamic_sensitivity / 20, 1.0)  # Normalizado a 20%
    
    # Índice compuesto
    dielectric_stress = min(base_stress * position_factor * hops_factor * (1 + dynamic_factor), 1.0)
    
    # Probabilidad estimada de descargas parciales
    pd_probability = dielectric_stress ** 2  # No lineal
    
    # Clasificar nivel
    if dielectric_stress > 0.8:
        level = 'Crítico'
    elif dielectric_stress > 0.6:
        level = 'Alto'
    elif dielectric_stress > 0.4:
        level = 'Medio'
    else:
        level = 'Bajo'
    
    return {
        'indice_estres_dielectrico': dielectric_stress,
        'nivel_estres_dielectrico': level,
        'probabilidad_descargas_parciales': pd_probability,
        'vulnerabilidad_transitorios': dynamic_factor
    }

def calculate_neighborhood_features(df, radius_km=0.5):
    """
    Calcular features basadas en el vecindario espacial
    """
    print(f"  Calculando features de vecindario (radio={radius_km}km)...")
    
    # Preparar coordenadas
    coords = df[['Coord_Y', 'Coord_X']].values
    
    # Calcular matriz de distancias
    from sklearn.metrics.pairwise import haversine_distances
    from math import radians
    
    # Convertir a radianes
    coords_rad = np.radians(coords)
    
    # Calcular distancias (resultado en radianes)
    dist_matrix = haversine_distances(coords_rad)
    
    # Convertir a km (radio de la Tierra = 6371 km)
    dist_matrix = dist_matrix * 6371
    
    # Crear features de vecindario
    neighborhood_features = []
    
    for i in range(len(df)):
        # Encontrar vecinos dentro del radio
        neighbors_mask = (dist_matrix[i] <= radius_km) & (dist_matrix[i] > 0)
        neighbors_idx = np.where(neighbors_mask)[0]
        
        if len(neighbors_idx) == 0:
            features = {
                'num_vecinos_500m': 0,
                'tasa_fallas_vecindario': 0,
                'potencia_vecindario_mva': 0,
                'usuarios_vecindario': 0,
                'tipo_vecindario': 'aislado'
            }
        else:
            neighbors_data = df.iloc[neighbors_idx]
            
            # Calcular estadísticas del vecindario
            total_neighbors = len(neighbors_idx)
            failed_neighbors = (neighbors_data['Resultado'] == 'Fallida').sum()
            problem_neighbors = (neighbors_data['Resultado'] != 'Correcta').sum()
            
            features = {
                'num_vecinos_500m': total_neighbors,
                'tasa_fallas_vecindario': failed_neighbors / total_neighbors,
                'tasa_problemas_vecindario': problem_neighbors / total_neighbors,
                'potencia_vecindario_mva': neighbors_data['Potencia'].sum() / 1000,
                'usuarios_vecindario': neighbors_data['Q_Usuarios'].sum(),
                'tipo_vecindario': 'denso' if total_neighbors > 5 else 'disperso'
            }
        
        neighborhood_features.append(features)
    
    return pd.DataFrame(neighborhood_features)

def calculate_parent_influence(df):
    """
    Calcular influencia del transformador padre en el MST
    """
    # Crear diccionario de estados por código
    estado_dict = df.set_index('Codigo')['Resultado'].to_dict()
    
    parent_features = []
    
    for _, row in df.iterrows():
        padre = row.get('padre_mst')
        
        if pd.isna(padre) or padre == 'SUBSTATION':
            features = {
                'estado_padre': 'N/A',
                'padre_problematico': False,
                'riesgo_cascada': 0.0
            }
        else:
            estado_padre = estado_dict.get(padre, 'Desconocido')
            
            # Evaluar riesgo de cascada
            if estado_padre == 'Fallida':
                riesgo = 0.8
            elif estado_padre == 'Penalizada':
                riesgo = 0.5
            else:
                riesgo = 0.1
            
            features = {
                'estado_padre': estado_padre,
                'padre_problematico': estado_padre in ['Fallida', 'Penalizada'],
                'riesgo_cascada': riesgo
            }
        
        parent_features.append(features)
    
    return pd.DataFrame(parent_features)

def calculate_composite_vulnerability(row):
    """
    Calcular índice compuesto de vulnerabilidad
    """
    # Pesos para cada componente
    weights = {
        'termico': 0.35,
        'dielectrico': 0.35,
        'topologico': 0.15,
        'vecindario': 0.15
    }
    
    # Componentes normalizados
    thermal_component = row['indice_estres_termico_v2']
    dielectric_component = row['indice_estres_dielectrico']
    
    # Componente topológico
    topo_score = 0.0
    topo_score += 0.3 * min(row.get('numero_saltos', 0) / 10, 1.0)  # Distancia
    topo_score += 0.3 if row.get('es_nodo_hoja', False) else 0  # Posición
    topo_score += 0.4 * row.get('centralidad_intermediacion', 0)  # Importancia
    
    # Componente de vecindario
    neighborhood_score = 0.0
    neighborhood_score += 0.5 * row.get('tasa_problemas_vecindario', 0)
    neighborhood_score += 0.3 * row.get('riesgo_cascada', 0)
    neighborhood_score += 0.2 if row.get('tipo_vecindario', '') == 'denso' else 0
    
    # Índice compuesto
    vulnerability_index = (
        weights['termico'] * thermal_component +
        weights['dielectrico'] * dielectric_component +
        weights['topologico'] * topo_score +
        weights['vecindario'] * neighborhood_score
    )
    
    # Ajuste por estado actual (retroalimentación)
    if row['Resultado'] == 'Fallida':
        vulnerability_index = min(vulnerability_index * 1.2, 1.0)
    elif row['Resultado'] == 'Penalizada':
        vulnerability_index = min(vulnerability_index * 1.1, 1.0)
    
    # Clasificar nivel de vulnerabilidad
    if vulnerability_index > 0.8:
        vuln_level = 'Crítica'
        priority = 'Muy Alta'
    elif vulnerability_index > 0.6:
        vuln_level = 'Alta'
        priority = 'Alta'
    elif vulnerability_index > 0.4:
        vuln_level = 'Media'
        priority = 'Media'
    elif vulnerability_index > 0.2:
        vuln_level = 'Baja'
        priority = 'Baja'
    else:
        vuln_level = 'Mínima'
        priority = 'Muy Baja'
    
    # Modo de falla más probable
    if thermal_component > dielectric_component * 1.5:
        failure_mode = 'Térmico'
    elif dielectric_component > thermal_component * 1.5:
        failure_mode = 'Dieléctrico'
    else:
        failure_mode = 'Mixto'
    
    return {
        'indice_vulnerabilidad_compuesto': vulnerability_index,
        'nivel_vulnerabilidad': vuln_level,
        'prioridad_intervencion': priority,
        'modo_falla_probable': failure_mode,
        'score_componente_termico': thermal_component,
        'score_componente_dielectrico': dielectric_component,
        'score_componente_topologico': topo_score,
        'score_componente_vecindario': neighborhood_score
    }

def visualize_vulnerability_analysis(df, save_dir):
    """Generar visualizaciones del análisis de vulnerabilidad"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Distribución de modos de falla
    ax1 = axes[0, 0]
    failure_modes = df['modo_falla_probable'].value_counts()
    colors = {'Térmico': 'red', 'Dieléctrico': 'blue', 'Mixto': 'purple'}
    failure_modes.plot(kind='pie', ax=ax1, colors=[colors[x] for x in failure_modes.index],
                      autopct='%1.1f%%')
    ax1.set_title('Distribución de Modos de Falla Probables')
    ax1.set_ylabel('')
    
    # 2. Matriz de vulnerabilidad
    ax2 = axes[0, 1]
    scatter = ax2.scatter(df['indice_estres_termico_v2'], 
                         df['indice_estres_dielectrico'],
                         c=df['indice_vulnerabilidad_compuesto'],
                         cmap='RdYlGn_r', alpha=0.6, s=50)
    ax2.set_xlabel('Estrés Térmico')
    ax2.set_ylabel('Estrés Dieléctrico')
    ax2.set_title('Matriz de Vulnerabilidad')
    ax2.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax2, label='Vulnerabilidad')
    
    # Líneas de referencia
    ax2.axhline(y=0.6, color='orange', linestyle='--', alpha=0.5)
    ax2.axvline(x=0.6, color='orange', linestyle='--', alpha=0.5)
    
    # 3. Vulnerabilidad por alimentador
    ax3 = axes[1, 0]
    vuln_by_feeder = df.groupby('Alimentador')['indice_vulnerabilidad_compuesto'].mean()
    top_vulnerable = vuln_by_feeder.nlargest(15)
    top_vulnerable.plot(kind='barh', ax=ax3, color='darkred')
    ax3.set_xlabel('Índice de Vulnerabilidad Promedio')
    ax3.set_title('Top 15 Alimentadores más Vulnerables')
    ax3.axvline(x=0.6, color='orange', linestyle='--', label='Umbral alto')
    
    # 4. Distribución de niveles de vulnerabilidad
    ax4 = axes[1, 1]
    vuln_dist = df['nivel_vulnerabilidad'].value_counts()
    order = ['Crítica', 'Alta', 'Media', 'Baja', 'Mínima']
    vuln_dist = vuln_dist.reindex(order, fill_value=0)
    colors_vuln = ['darkred', 'red', 'orange', 'yellow', 'green']
    vuln_dist.plot(kind='bar', ax=ax4, color=colors_vuln)
    ax4.set_title('Distribución de Niveles de Vulnerabilidad')
    ax4.set_xlabel('Nivel de Vulnerabilidad')
    ax4.set_ylabel('Número de Transformadores')
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(save_dir / 'vulnerability_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Mapa de calor de componentes
    plt.figure(figsize=(12, 8))
    components = df[['score_componente_termico', 'score_componente_dielectrico',
                     'score_componente_topologico', 'score_componente_vecindario']]
    
    # Agregar por alimentador (top 20)
    comp_by_feeder = df.groupby('Alimentador')[components.columns].mean()
    top_feeders = df.groupby('Alimentador')['indice_vulnerabilidad_compuesto'].mean().nlargest(20).index
    comp_by_feeder = comp_by_feeder.loc[top_feeders]
    
    sns.heatmap(comp_by_feeder.T, cmap='RdYlGn_r', annot=True, fmt='.2f',
                xticklabels=True, yticklabels=['Térmico', 'Dieléctrico', 'Topológico', 'Vecindario'])
    plt.title('Componentes de Vulnerabilidad por Alimentador')
    plt.xlabel('Alimentador')
    plt.tight_layout()
    plt.savefig(save_dir / 'vulnerability_components_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()

def main():
    """Función principal"""
    print("=" * 80)
    print("ANÁLISIS DE MODOS DE FALLA Y VULNERABILIDAD")
    print("=" * 80)
    
    # Cargar datos
    print("Cargando datos...")
    df = pd.read_csv(INPUT_FILE)
    print(f"✓ {len(df)} transformadores cargados")
    
    # Calcular estrés térmico
    print("\nCalculando índices de estrés térmico...")
    thermal_features = df.apply(calculate_thermal_stress_index, axis=1)
    df_thermal = pd.DataFrame(list(thermal_features))
    df = pd.concat([df, df_thermal], axis=1)
    
    # Calcular estrés dieléctrico
    print("Calculando índices de estrés dieléctrico...")
    dielectric_features = df.apply(calculate_dielectric_stress_index, axis=1)
    df_dielectric = pd.DataFrame(list(dielectric_features))
    df = pd.concat([df, df_dielectric], axis=1)
    
    # Calcular features de vecindario
    print("Analizando vecindario espacial...")
    df_neighborhood = calculate_neighborhood_features(df)
    df = pd.concat([df, df_neighborhood], axis=1)
    
    # Calcular influencia del padre
    print("Evaluando influencia del transformador padre...")
    df_parent = calculate_parent_influence(df)
    df = pd.concat([df, df_parent], axis=1)
    
    # Calcular vulnerabilidad compuesta
    print("Calculando índice de vulnerabilidad compuesto...")
    vulnerability = df.apply(calculate_composite_vulnerability, axis=1)
    df_vulnerability = pd.DataFrame(list(vulnerability))
    df = pd.concat([df, df_vulnerability], axis=1)
    
    # Guardar resultados
    output_file = OUTPUT_DIR / "transformadores_indices_riesgo.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✓ Resultados guardados en: {output_file}")
    
    # Generar visualizaciones
    viz_dir = OUTPUT_DIR / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    visualize_vulnerability_analysis(df, viz_dir)
    print(f"✓ Visualizaciones guardadas en: {viz_dir}")
    
    # Generar reporte
    report = {
        'timestamp': datetime.now().isoformat(),
        'umbrales_utilizados': THRESHOLDS,
        'estadisticas_estres': {
            'termico': {
                'promedio': df['indice_estres_termico_v2'].mean(),
                'criticos': (df['nivel_estres_termico'] == 'Crítico').sum(),
                'sobrecarga': (df['nivel_estres_termico'] == 'Sobrecarga').sum(),
                'vida_perdida_promedio_años': df['años_vida_perdidos_anual'].mean()
            },
            'dielectrico': {
                'promedio': df['indice_estres_dielectrico'].mean(),
                'criticos': (df['nivel_estres_dielectrico'] == 'Crítico').sum(),
                'prob_descargas_promedio': df['probabilidad_descargas_parciales'].mean()
            }
        },
        'distribucion_vulnerabilidad': df['nivel_vulnerabilidad'].value_counts().to_dict(),
        'modos_falla_probables': df['modo_falla_probable'].value_counts().to_dict(),
        'estadisticas_vecindario': {
            'promedio_vecinos': df['num_vecinos_500m'].mean(),
            'tasa_contagio_promedio': df['tasa_problemas_vecindario'].mean(),
            'transformadores_aislados': (df['tipo_vecindario'] == 'aislado').sum()
        },
        'top_20_mas_vulnerables': df.nlargest(20, 'indice_vulnerabilidad_compuesto')[
            ['Codigo', 'Alimentador', 'Potencia', 'Q_Usuarios',
             'indice_vulnerabilidad_compuesto', 'modo_falla_probable',
             'nivel_estres_termico', 'nivel_estres_dielectrico',
             'prioridad_intervencion']
        ].to_dict('records'),
        'alimentadores_criticos_vulnerabilidad': df.groupby('Alimentador').agg({
            'indice_vulnerabilidad_compuesto': 'mean',
            'Codigo': 'count',
            'modo_falla_probable': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'N/A'
        }).nlargest(10, 'indice_vulnerabilidad_compuesto').to_dict('index')
    }
    
    report_file = OUTPUT_DIR / "failure_modes_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✓ Reporte guardado en: {report_file}")
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS")
    print("=" * 80)
    
    print("\nDistribución de Vulnerabilidad:")
    for nivel in ['Crítica', 'Alta', 'Media', 'Baja', 'Mínima']:
        count = (df['nivel_vulnerabilidad'] == nivel).sum()
        print(f"  - {nivel}: {count} ({(count/len(df))*100:.1f}%)")
    
    print("\nModos de Falla Probables:")
    for modo, count in df['modo_falla_probable'].value_counts().items():
        print(f"  - {modo}: {count} ({(count/len(df))*100:.1f}%)")
    
    print(f"\nEstrés Térmico:")
    print(f"  - Índice promedio: {df['indice_estres_termico_v2'].mean():.3f}")
    print(f"  - Transformadores críticos: {(df['nivel_estres_termico'] == 'Crítico').sum()}")
    print(f"  - Vida perdida promedio: {df['años_vida_perdidos_anual'].mean():.2f} años/año")
    
    print(f"\nEstrés Dieléctrico:")
    print(f"  - Índice promedio: {df['indice_estres_dielectrico'].mean():.3f}")
    print(f"  - Transformadores críticos: {(df['nivel_estres_dielectrico'] == 'Crítico').sum()}")
    
    # Top transformadores vulnerables
    print("\nTop 5 Transformadores Más Vulnerables:")
    top_vuln = df.nlargest(5, 'indice_vulnerabilidad_compuesto')
    for _, row in top_vuln.iterrows():
        print(f"  - {row['Codigo']} ({row['Alimentador']}): "
              f"Vulnerabilidad={row['indice_vulnerabilidad_compuesto']:.3f}, "
              f"Modo={row['modo_falla_probable']}, "
              f"Prioridad={row['prioridad_intervencion']}")

if __name__ == "__main__":
    main()