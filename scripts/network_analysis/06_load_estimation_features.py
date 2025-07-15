#!/usr/bin/env python3
"""
Fase 0 - Script 6: Estimación de Cargas y Features de Potencia
=============================================================

Este script estima las cargas activas y reactivas basándose en:
- Tipo de zona (Rural/Periurbano/Urbano)
- Ratio kVA por usuario como proxy del tipo de carga
- Factores de potencia típicos según el documento teórico
- Factores de diversidad y utilización
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configuración de rutas
BASE_DIR = Path("/Users/maxkeczeli/Proyects/gd-edersa-calidad")
INPUT_FILE = BASE_DIR / "data/processed/electrical_analysis/transformadores_distancia_electrica.csv"
OUTPUT_DIR = BASE_DIR / "data/processed/electrical_analysis"

# Factores de potencia por tipo de carga (basados en documento teórico)
POWER_FACTOR_BY_TYPE = {
    'residencial': 0.92,      # Principalmente iluminación y electrodomésticos
    'comercial': 0.87,        # Mezcla de iluminación, AC y equipos
    'industrial_ligero': 0.82, # Pequeños motores y equipos
    'industrial_pesado': 0.75, # Motores grandes
    'rural_agricola': 0.78,   # Bombas de riego y motores
    'mixto': 0.85            # Promedio general
}

# Factores de diversidad típicos
DIVERSITY_FACTORS = {
    'residencial': {
        'usuarios_1_5': 1.0,
        'usuarios_6_10': 0.85,
        'usuarios_11_20': 0.75,
        'usuarios_21_50': 0.65,
        'usuarios_50+': 0.55
    },
    'comercial': 0.70,
    'industrial': 0.85,
    'rural': 0.60
}

# Factor de utilización por hora del día (simplificado)
UTILIZATION_CURVE = {
    'residencial': {
        'pico_manana': 0.65,    # 7-9 AM
        'dia': 0.40,            # 9 AM - 6 PM
        'pico_tarde': 0.90,     # 6-11 PM
        'noche': 0.25,          # 11 PM - 7 AM
        'promedio': 0.55
    },
    'comercial': {
        'pico_manana': 0.70,
        'dia': 0.85,
        'pico_tarde': 0.75,
        'noche': 0.15,
        'promedio': 0.61
    },
    'industrial': {
        'pico_manana': 0.85,
        'dia': 0.90,
        'pico_tarde': 0.80,
        'noche': 0.40,
        'promedio': 0.74
    }
}

def classify_load_type(row):
    """
    Clasificar el tipo de carga basándose en kVA/usuario y tipo de zona
    """
    kva_per_user = row['Potencia'] / max(row['Q_Usuarios'], 1)
    tipo_zona = row.get('tipo_zona', 'Rural')
    
    # Clasificación basada en kVA por usuario
    if kva_per_user < 0.5:
        # Muy bajo: probablemente residencial de bajos recursos
        load_type = 'residencial'
        load_profile = 'bajo_consumo'
    elif kva_per_user < 2.0:
        # Típico residencial
        load_type = 'residencial'
        load_profile = 'residencial_tipico'
    elif kva_per_user < 5.0:
        # Mixto residencial/comercial
        load_type = 'mixto'
        load_profile = 'mixto_res_com'
    elif kva_per_user < 15.0:
        # Comercial o industrial ligero
        if tipo_zona == 'Urbano':
            load_type = 'comercial'
            load_profile = 'comercial'
        else:
            load_type = 'industrial_ligero'
            load_profile = 'industrial_ligero'
    else:
        # Industrial pesado o grandes consumidores
        load_type = 'industrial_pesado'
        load_profile = 'gran_consumidor'
    
    # Ajuste por zona rural
    if tipo_zona == 'Rural' and load_type == 'industrial_ligero':
        load_type = 'rural_agricola'
        load_profile = 'agricola'
    
    return {
        'tipo_carga': load_type,
        'perfil_carga': load_profile,
        'kva_por_usuario': kva_per_user
    }

def estimate_diversity_factor(row):
    """
    Estimar factor de diversidad basado en número de usuarios y tipo
    """
    n_users = row['Q_Usuarios']
    load_type = row['tipo_carga']
    
    if 'residencial' in load_type:
        if n_users <= 5:
            return DIVERSITY_FACTORS['residencial']['usuarios_1_5']
        elif n_users <= 10:
            return DIVERSITY_FACTORS['residencial']['usuarios_6_10']
        elif n_users <= 20:
            return DIVERSITY_FACTORS['residencial']['usuarios_11_20']
        elif n_users <= 50:
            return DIVERSITY_FACTORS['residencial']['usuarios_21_50']
        else:
            return DIVERSITY_FACTORS['residencial']['usuarios_50+']
    elif 'comercial' in load_type:
        return DIVERSITY_FACTORS['comercial']
    elif 'industrial' in load_type:
        return DIVERSITY_FACTORS['industrial']
    else:
        return DIVERSITY_FACTORS['rural']

def calculate_load_features(row):
    """
    Calcular características de carga estimadas
    """
    # Factor de potencia basado en tipo de carga
    fp = POWER_FACTOR_BY_TYPE.get(row['tipo_carga'], 0.85)
    
    # Factor de diversidad
    fd = estimate_diversity_factor(row)
    
    # Factor de utilización promedio
    load_category = 'industrial' if 'industrial' in row['tipo_carga'] else row['tipo_carga']
    if load_category in ['residencial', 'comercial', 'industrial']:
        fu = UTILIZATION_CURVE[load_category]['promedio']
        fu_pico = UTILIZATION_CURVE[load_category]['pico_tarde']
    else:
        fu = 0.60
        fu_pico = 0.85
    
    # Potencia nominal
    S_kva = row['Potencia']
    
    # Carga diversificada promedio
    S_div = S_kva * fd * fu
    P_est = S_div * fp  # Potencia activa
    Q_est = S_div * np.sqrt(1 - fp**2)  # Potencia reactiva
    
    # Carga pico estimada
    S_pico = S_kva * fd * fu_pico
    P_pico = S_pico * fp
    Q_pico = S_pico * np.sqrt(1 - fp**2)
    
    # Factor de carga (load factor)
    load_factor = fu / fu_pico
    
    # Índice de carga reactiva (mayor = peor para la red)
    reactive_index = Q_est / max(P_est, 1)
    
    # Densidad de carga (kW/usuario)
    load_density = P_est / max(row['Q_Usuarios'], 1)
    
    return {
        'factor_potencia_estimado': fp,
        'factor_diversidad': fd,
        'factor_utilizacion_promedio': fu,
        'factor_utilizacion_pico': fu_pico,
        'carga_activa_P_est_kW': P_est,
        'carga_reactiva_Q_est_kVAR': Q_est,
        'carga_aparente_S_est_kVA': S_div,
        'carga_activa_pico_kW': P_pico,
        'carga_reactiva_pico_kVAR': Q_pico,
        'factor_carga': load_factor,
        'indice_carga_reactiva': reactive_index,
        'densidad_carga_kW_usuario': load_density
    }

def calculate_overload_risk(row):
    """
    Calcular índices de riesgo de sobrecarga
    """
    # Factor de utilización actual (respecto a capacidad nominal)
    utilization = row['carga_aparente_S_est_kVA'] / row['Potencia']
    utilization_pico = (row['carga_activa_pico_kW'] / row['factor_potencia_estimado']) / row['Potencia']
    
    # Margen de reserva
    reserve_margin = 1 - utilization_pico
    
    # Índice de sobrecarga (>1 indica sobrecarga)
    overload_index = utilization_pico
    
    # Clasificar riesgo
    if overload_index > 1.2:
        risk_level = 'Crítico'
        risk_score = 1.0
    elif overload_index > 1.0:
        risk_level = 'Alto'
        risk_score = 0.8
    elif overload_index > 0.85:
        risk_level = 'Medio'
        risk_score = 0.6
    elif overload_index > 0.70:
        risk_level = 'Bajo'
        risk_score = 0.4
    else:
        risk_level = 'Mínimo'
        risk_score = 0.2
    
    # Factor de estrés térmico combinado con impedancia
    thermal_stress = overload_index * (1 + 0.1 * row.get('indice_debilidad_electrica', 0))
    
    return {
        'factor_utilizacion_actual': utilization,
        'factor_utilizacion_pico': utilization_pico,
        'margen_reserva': reserve_margin,
        'indice_sobrecarga': overload_index,
        'nivel_riesgo_sobrecarga': risk_level,
        'score_riesgo_sobrecarga': risk_score,
        'indice_estres_termico': thermal_stress
    }

def visualize_load_analysis(df_results, save_dir):
    """Generar visualizaciones del análisis de carga"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Distribución de tipos de carga
    ax1 = axes[0, 0]
    load_dist = df_results['tipo_carga'].value_counts()
    load_dist.plot(kind='bar', ax=ax1, color='skyblue')
    ax1.set_title('Distribución de Tipos de Carga')
    ax1.set_xlabel('Tipo de Carga')
    ax1.set_ylabel('Número de Transformadores')
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Factor de potencia por tipo
    ax2 = axes[0, 1]
    fp_by_type = df_results.groupby('tipo_carga')['factor_potencia_estimado'].mean().sort_values()
    fp_by_type.plot(kind='barh', ax=ax2, color='lightcoral')
    ax2.set_title('Factor de Potencia Promedio por Tipo')
    ax2.set_xlabel('Factor de Potencia')
    ax2.axvline(x=0.85, color='red', linestyle='--', label='FP objetivo')
    ax2.legend()
    
    # 3. Distribución de utilización
    ax3 = axes[1, 0]
    df_results['factor_utilizacion_pico'].hist(bins=50, ax=ax3, alpha=0.7, color='green')
    ax3.axvline(x=1.0, color='red', linestyle='--', label='Capacidad nominal')
    ax3.set_title('Distribución de Factor de Utilización Pico')
    ax3.set_xlabel('Factor de Utilización')
    ax3.set_ylabel('Frecuencia')
    ax3.legend()
    
    # 4. Mapa de riesgo de sobrecarga
    ax4 = axes[1, 1]
    risk_counts = df_results['nivel_riesgo_sobrecarga'].value_counts()
    risk_order = ['Crítico', 'Alto', 'Medio', 'Bajo', 'Mínimo']
    risk_counts = risk_counts.reindex(risk_order, fill_value=0)
    colors = ['darkred', 'red', 'orange', 'yellow', 'green']
    risk_counts.plot(kind='pie', ax=ax4, colors=colors, autopct='%1.1f%%')
    ax4.set_title('Distribución de Niveles de Riesgo de Sobrecarga')
    ax4.set_ylabel('')
    
    plt.tight_layout()
    plt.savefig(save_dir / 'load_analysis_overview.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Visualización adicional: Correlación FP vs kVA/usuario
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(df_results['kva_por_usuario'], 
                         df_results['factor_potencia_estimado'],
                         c=df_results['score_riesgo_sobrecarga'],
                         cmap='RdYlGn_r', alpha=0.6)
    plt.colorbar(scatter, label='Score Riesgo Sobrecarga')
    plt.xlabel('kVA por Usuario')
    plt.ylabel('Factor de Potencia Estimado')
    plt.title('Relación entre Tipo de Carga y Factor de Potencia')
    plt.xscale('log')
    plt.grid(True, alpha=0.3)
    plt.savefig(save_dir / 'fp_vs_load_type.png', dpi=150, bbox_inches='tight')
    plt.close()

def main():
    """Función principal"""
    print("=" * 80)
    print("ESTIMACIÓN DE CARGAS Y FEATURES DE POTENCIA")
    print("=" * 80)
    
    # Cargar datos
    print("Cargando datos...")
    df = pd.read_csv(INPUT_FILE)
    print(f"✓ {len(df)} transformadores cargados")
    
    # Clasificar tipos de carga
    print("\nClasificando tipos de carga...")
    load_classification = df.apply(classify_load_type, axis=1)
    df_class = pd.DataFrame(list(load_classification))
    df = pd.concat([df, df_class], axis=1)
    
    # Calcular features de carga
    print("Calculando características de carga...")
    load_features = df.apply(calculate_load_features, axis=1)
    df_features = pd.DataFrame(list(load_features))
    df = pd.concat([df, df_features], axis=1)
    
    # Calcular riesgo de sobrecarga
    print("Evaluando riesgo de sobrecarga...")
    overload_risk = df.apply(calculate_overload_risk, axis=1)
    df_risk = pd.DataFrame(list(overload_risk))
    df = pd.concat([df, df_risk], axis=1)
    
    # Guardar resultados
    output_file = OUTPUT_DIR / "transformadores_carga_estimada.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✓ Resultados guardados en: {output_file}")
    
    # Generar visualizaciones
    viz_dir = OUTPUT_DIR / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    visualize_load_analysis(df, viz_dir)
    print(f"✓ Visualizaciones guardadas en: {viz_dir}")
    
    # Generar reporte
    report = {
        'timestamp': datetime.now().isoformat(),
        'parametros_utilizados': {
            'factores_potencia': POWER_FACTOR_BY_TYPE,
            'factores_diversidad': DIVERSITY_FACTORS,
            'curvas_utilizacion': UTILIZATION_CURVE
        },
        'distribucion_tipos_carga': df['tipo_carga'].value_counts().to_dict(),
        'estadisticas_carga': {
            'carga_total_estimada_MW': df['carga_activa_P_est_kW'].sum() / 1000,
            'carga_reactiva_total_MVAR': df['carga_reactiva_Q_est_kVAR'].sum() / 1000,
            'factor_potencia_promedio_red': df['factor_potencia_estimado'].mean(),
            'factor_utilizacion_promedio': df['factor_utilizacion_actual'].mean(),
            'factor_utilizacion_pico_promedio': df['factor_utilizacion_pico'].mean()
        },
        'analisis_sobrecarga': {
            'transformadores_sobrecargados': (df['indice_sobrecarga'] > 1.0).sum(),
            'porcentaje_sobrecargados': ((df['indice_sobrecarga'] > 1.0).sum() / len(df)) * 100,
            'distribucion_riesgo': df['nivel_riesgo_sobrecarga'].value_counts().to_dict(),
            'capacidad_total_MVA': df['Potencia'].sum() / 1000,
            'margen_reserva_promedio': df['margen_reserva'].mean()
        },
        'transformadores_criticos_sobrecarga': df[df['nivel_riesgo_sobrecarga'] == 'Crítico'].nlargest(10, 'indice_sobrecarga')[
            ['Codigo', 'Alimentador', 'Potencia', 'Q_Usuarios', 'tipo_carga',
             'factor_utilizacion_pico', 'indice_sobrecarga', 'indice_estres_termico']
        ].to_dict('records'),
        'alimentadores_bajo_fp': df.groupby('Alimentador').agg({
            'factor_potencia_estimado': 'mean',
            'carga_reactiva_Q_est_kVAR': 'sum'
        }).nsmallest(10, 'factor_potencia_estimado').to_dict('index')
    }
    
    report_file = OUTPUT_DIR / "load_estimation_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✓ Reporte guardado en: {report_file}")
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS")
    print("=" * 80)
    print("\nDistribución de Tipos de Carga:")
    for tipo, count in df['tipo_carga'].value_counts().items():
        print(f"  - {tipo}: {count} ({(count/len(df))*100:.1f}%)")
    
    print(f"\nEstadísticas de Carga:")
    print(f"  - Carga activa total estimada: {df['carga_activa_P_est_kW'].sum()/1000:.1f} MW")
    print(f"  - Carga reactiva total: {df['carga_reactiva_Q_est_kVAR'].sum()/1000:.1f} MVAR")
    print(f"  - Factor de potencia promedio: {df['factor_potencia_estimado'].mean():.3f}")
    print(f"  - Factor de utilización promedio: {df['factor_utilizacion_actual'].mean():.2%}")
    
    print(f"\nAnálisis de Sobrecarga:")
    print(f"  - Transformadores sobrecargados (>100%): {(df['indice_sobrecarga'] > 1.0).sum()} "
          f"({((df['indice_sobrecarga'] > 1.0).sum() / len(df)) * 100:.1f}%)")
    print(f"  - Margen de reserva promedio: {df['margen_reserva'].mean():.2%}")
    
    print("\nDistribución de Riesgo:")
    for nivel in ['Crítico', 'Alto', 'Medio', 'Bajo', 'Mínimo']:
        count = (df['nivel_riesgo_sobrecarga'] == nivel).sum()
        print(f"  - {nivel}: {count} ({(count/len(df))*100:.1f}%)")
    
    # Top transformadores críticos
    print("\nTop 5 Transformadores Críticos por Sobrecarga:")
    top_critical = df[df['nivel_riesgo_sobrecarga'] == 'Crítico'].nlargest(5, 'indice_sobrecarga')
    for _, row in top_critical.iterrows():
        print(f"  - {row['Codigo']} ({row['Alimentador']}): "
              f"Utilización={row['factor_utilizacion_pico']:.1%}, "
              f"Tipo={row['tipo_carga']}, "
              f"Estrés térmico={row['indice_estres_termico']:.2f}")

if __name__ == "__main__":
    main()