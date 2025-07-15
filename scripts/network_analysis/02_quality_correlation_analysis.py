#!/usr/bin/env python3
"""
FASE 0: Análisis de Correlación de Calidad
==========================================
Objetivo: Analizar correlaciones entre problemas de calidad dentro de alimentadores

Este script analiza:
1. Correlación de fallas entre transformadores del mismo alimentador
2. Patrones temporales en las mediciones
3. Relación entre características técnicas y problemas
4. Identificación de problemas sistémicos vs aleatorios
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import warnings
from datetime import datetime
from scipy.stats import chi2_contingency, pearsonr, spearmanr
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations

warnings.filterwarnings('ignore')

# Configuración
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
NETWORK_DIR = PROCESSED_DIR / 'network_analysis'
REPORTS_DIR = BASE_DIR / 'reports'
FIGURES_DIR = REPORTS_DIR / 'figures'

def load_data():
    """Cargar datos enriquecidos"""
    transformers_df = pd.read_csv(NETWORK_DIR / 'transformadores_con_topologia.csv')
    feeders_df = pd.read_csv(NETWORK_DIR / 'alimentadores_caracterizados.csv')
    spatial_patterns = pd.read_csv(NETWORK_DIR / 'patrones_espaciales_alimentadores.csv')
    
    print(f"\n📊 Datos cargados:")
    print(f"   - {len(transformers_df)} transformadores")
    print(f"   - {len(feeders_df)} alimentadores")
    print(f"   - {len(spatial_patterns)} patrones espaciales")
    
    return transformers_df, feeders_df, spatial_patterns

def analyze_failure_independence(transformers_df):
    """Analizar si las fallas son independientes dentro de cada alimentador"""
    
    independence_tests = []
    
    for feeder in transformers_df['Alimentador'].unique():
        if pd.isna(feeder):
            continue
            
        feeder_data = transformers_df[transformers_df['Alimentador'] == feeder].copy()
        
        if len(feeder_data) < 10:  # Necesitamos suficientes datos
            continue
        
        # Test de independencia usando chi-cuadrado
        # H0: Las fallas son independientes
        # H1: Las fallas están correlacionadas
        
        # Crear tabla de contingencia: posición en alimentador vs estado
        feeder_data['posicion_bin'] = pd.qcut(
            feeder_data['posicion_relativa'].fillna(0.5), 
            q=3, 
            labels=['Inicio', 'Medio', 'Final']
        )
        
        contingency_table = pd.crosstab(
            feeder_data['posicion_bin'],
            feeder_data['Resultado']
        )
        
        if contingency_table.shape[0] >= 2 and contingency_table.shape[1] >= 2:
            chi2, p_value, dof, expected = chi2_contingency(contingency_table)
            
            # Calcular tamaño del efecto (Cramér's V)
            n = contingency_table.sum().sum()
            min_dim = min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)
            cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
            
            independence_tests.append({
                'alimentador': feeder,
                'num_transformadores': len(feeder_data),
                'chi2_statistic': chi2,
                'p_value': p_value,
                'cramers_v': cramers_v,
                'fallas_independientes': p_value > 0.05,
                'interpretacion': 'Independientes' if p_value > 0.05 else 
                                'Correlacionadas' if cramers_v > 0.3 else 
                                'Débilmente correlacionadas'
            })
    
    return pd.DataFrame(independence_tests)

def analyze_temporal_patterns(transformers_df):
    """Analizar patrones temporales en las mediciones"""
    
    temporal_analysis = []
    
    # Análisis por alimentador
    for feeder in transformers_df['Alimentador'].unique():
        if pd.isna(feeder):
            continue
            
        feeder_data = transformers_df[transformers_df['Alimentador'] == feeder].copy()
        
        # Análisis de rango de mediciones
        feeder_data['rango_medicion'] = feeder_data['max_medicion'] - feeder_data['min_medicion']
        
        # Estadísticas temporales
        analysis = {
            'alimentador': feeder,
            'num_transformadores': len(feeder_data),
            'mediciones_promedio': feeder_data['num_mediciones'].mean(),
            'rango_temporal_promedio': feeder_data['rango_medicion'].mean(),
            'variabilidad_temporal': feeder_data['rango_medicion'].std(),
        }
        
        # Correlación entre número de mediciones y problemas
        feeder_data['tiene_problema'] = (feeder_data['Resultado'] != 'Correcta').astype(int)
        
        if feeder_data['num_mediciones'].std() > 0:
            corr, p_value = spearmanr(
                feeder_data['num_mediciones'],
                feeder_data['tiene_problema']
            )
            analysis['corr_mediciones_problemas'] = corr
            analysis['p_value_temporal'] = p_value
            analysis['patron_temporal'] = 'Más mediciones = más problemas' if corr > 0.2 else \
                                        'Más mediciones = menos problemas' if corr < -0.2 else \
                                        'Sin patrón claro'
        
        temporal_analysis.append(analysis)
    
    return pd.DataFrame(temporal_analysis)

def analyze_technical_correlations(transformers_df):
    """Analizar correlaciones entre características técnicas y problemas"""
    
    # Preparar datos
    tech_data = transformers_df[transformers_df['Potencia'].notna()].copy()
    tech_data['tiene_problema'] = (tech_data['Resultado'] != 'Correcta').astype(int)
    tech_data['es_fallida'] = (tech_data['Resultado'] == 'Fallida').astype(int)
    
    # Variables técnicas a analizar
    tech_vars = ['Potencia', 'Q_Usuarios', 'usuarios_por_kva', 
                 'factor_utilizacion_estimado', 'num_circuitos']
    
    correlations = {}
    
    for var in tech_vars:
        if var in tech_data.columns and tech_data[var].notna().sum() > 30:
            # Correlación con problemas en general
            corr_prob, p_prob = spearmanr(
                tech_data[var].dropna(),
                tech_data.loc[tech_data[var].notna(), 'tiene_problema']
            )
            
            # Correlación con fallas específicamente
            corr_fail, p_fail = spearmanr(
                tech_data[var].dropna(),
                tech_data.loc[tech_data[var].notna(), 'es_fallida']
            )
            
            correlations[var] = {
                'corr_problemas': corr_prob,
                'p_value_problemas': p_prob,
                'corr_fallas': corr_fail,
                'p_value_fallas': p_fail,
                'significativo': p_prob < 0.05 or p_fail < 0.05
            }
    
    # Análisis por categorías
    categorical_analysis = {}
    
    # Por tamaño
    size_crosstab = pd.crosstab(tech_data['size_category'], tech_data['Resultado'])
    chi2, p_value, _, _ = chi2_contingency(size_crosstab)
    categorical_analysis['size_category'] = {
        'chi2': chi2,
        'p_value': p_value,
        'asociacion': 'Significativa' if p_value < 0.05 else 'No significativa'
    }
    
    # Por tipo de instalación
    if 'Tipoinstalacion' in tech_data.columns:
        tipo_crosstab = pd.crosstab(tech_data['Tipoinstalacion'], tech_data['Resultado'])
        if tipo_crosstab.shape[0] >= 2:
            chi2, p_value, _, _ = chi2_contingency(tipo_crosstab)
            categorical_analysis['tipo_instalacion'] = {
                'chi2': chi2,
                'p_value': p_value,
                'asociacion': 'Significativa' if p_value < 0.05 else 'No significativa'
            }
    
    return correlations, categorical_analysis

def identify_systemic_problems(transformers_df, feeders_df):
    """Identificar problemas sistémicos vs aleatorios"""
    
    systemic_analysis = []
    
    # Umbral para considerar un problema como sistémico
    SYSTEMIC_THRESHOLD = 0.5  # 50% de fallas
    
    for _, feeder in feeders_df.iterrows():
        if feeder['num_transformadores'] < 5:  # Mínimo para análisis
            continue
        
        analysis = {
            'alimentador': feeder['alimentador'],
            'num_transformadores': feeder['num_transformadores'],
            'tasa_problemas': feeder['tasa_problemas'],
            'num_fallidas': feeder['num_fallida'],
            'num_penalizadas': feeder['num_penalizada'],
        }
        
        # Clasificar tipo de problema
        if feeder['tasa_problemas'] > SYSTEMIC_THRESHOLD:
            if feeder['num_fallida'] > feeder['num_penalizada']:
                analysis['tipo_problema'] = 'Sistémico - Fallas generalizadas'
            else:
                analysis['tipo_problema'] = 'Sistémico - Calidad degradada'
        elif feeder['tasa_problemas'] > 0.3:
            analysis['tipo_problema'] = 'Parcial - Problemas localizados'
        else:
            analysis['tipo_problema'] = 'Aleatorio - Casos aislados'
        
        # Buscar patrones en los datos del alimentador
        feeder_trafos = transformers_df[
            transformers_df['Alimentador'] == feeder['alimentador']
        ]
        
        if len(feeder_trafos) >= 10:
            # Analizar si los problemas están agrupados geográficamente
            problem_trafos = feeder_trafos[feeder_trafos['Resultado'] != 'Correcta']
            
            if len(problem_trafos) >= 3 and 'dist_a_centroide_km' in problem_trafos.columns:
                # Comparar distancia promedio de transformadores con problemas vs sin problemas
                dist_problems = problem_trafos['dist_a_centroide_km'].mean()
                dist_ok = feeder_trafos[
                    feeder_trafos['Resultado'] == 'Correcta'
                ]['dist_a_centroide_km'].mean()
                
                if not pd.isna(dist_problems) and not pd.isna(dist_ok):
                    if abs(dist_problems - dist_ok) > 0.5:  # Diferencia significativa
                        analysis['patron_geografico'] = 'Concentrado' if dist_problems < dist_ok else 'Periférico'
                    else:
                        analysis['patron_geografico'] = 'Distribuido'
        
        systemic_analysis.append(analysis)
    
    return pd.DataFrame(systemic_analysis)

def generate_correlation_visualizations(
    transformers_df, independence_tests, technical_corrs, systemic_problems
):
    """Generar visualizaciones de correlaciones"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Distribución de independencia de fallas
    ax = axes[0, 0]
    if not independence_tests.empty:
        interpretations = independence_tests['interpretacion'].value_counts()
        colors = {'Independientes': 'green', 
                 'Débilmente correlacionadas': 'yellow',
                 'Correlacionadas': 'red'}
        
        bars = ax.bar(interpretations.index, interpretations.values,
                      color=[colors.get(x, 'gray') for x in interpretations.index])
        
        for bar, value in zip(bars, interpretations.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   str(value), ha='center', va='bottom')
        
        ax.set_xlabel('Tipo de Correlación')
        ax.set_ylabel('Número de Alimentadores')
        ax.set_title('Independencia de Fallas por Alimentador')
    else:
        ax.text(0.5, 0.5, 'Sin datos suficientes', 
               ha='center', va='center', transform=ax.transAxes)
    
    # 2. Correlaciones técnicas
    ax = axes[0, 1]
    if technical_corrs:
        tech_df = pd.DataFrame(technical_corrs).T
        
        # Crear matriz de correlación para visualizar
        corr_matrix = tech_df[['corr_problemas', 'corr_fallas']].astype(float)
        
        sns.heatmap(corr_matrix, annot=True, fmt='.3f', 
                   cmap='RdBu_r', center=0, 
                   cbar_kws={'label': 'Correlación'},
                   ax=ax)
        ax.set_title('Correlaciones: Variables Técnicas vs Problemas')
        ax.set_xlabel('Tipo de Problema')
    
    # 3. Tipos de problemas sistémicos
    ax = axes[1, 0]
    if not systemic_problems.empty:
        problem_types = systemic_problems['tipo_problema'].value_counts()
        
        # Gráfico de torta
        colors_prob = {'Sistémico - Fallas generalizadas': 'darkred',
                      'Sistémico - Calidad degradada': 'orange',
                      'Parcial - Problemas localizados': 'yellow',
                      'Aleatorio - Casos aislados': 'lightgreen'}
        
        wedges, texts, autotexts = ax.pie(
            problem_types.values, 
            labels=problem_types.index,
            autopct='%1.1f%%',
            colors=[colors_prob.get(x, 'gray') for x in problem_types.index],
            startangle=90
        )
        
        ax.set_title('Clasificación de Problemas en Alimentadores')
    
    # 4. Relación tamaño vs tasa de problemas
    ax = axes[1, 1]
    ax.scatter(transformers_df.groupby('Alimentador').size(),
              transformers_df.groupby('Alimentador').apply(
                  lambda x: (x['Resultado'] != 'Correcta').mean() * 100
              ),
              alpha=0.6, s=50)
    
    ax.set_xlabel('Número de Transformadores')
    ax.set_ylabel('Tasa de Problemas (%)')
    ax.set_title('Tamaño del Alimentador vs Tasa de Problemas')
    ax.grid(True, alpha=0.3)
    
    # Agregar línea de tendencia
    x = transformers_df.groupby('Alimentador').size().values
    y = transformers_df.groupby('Alimentador').apply(
        lambda x: (x['Resultado'] != 'Correcta').mean() * 100
    ).values
    
    if len(x) > 10:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        ax.plot(sorted(x), p(sorted(x)), "r--", alpha=0.8, label=f'Tendencia: y={z[0]:.2f}x+{z[1]:.1f}')
        ax.legend()
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'quality_correlations.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Visualizaciones guardadas en: {FIGURES_DIR / 'quality_correlations.png'}")

def save_results(
    independence_tests, temporal_patterns, technical_corrs, 
    categorical_analysis, systemic_problems
):
    """Guardar resultados del análisis"""
    
    # Guardar tests de independencia
    if not independence_tests.empty:
        independence_tests.to_csv(
            NETWORK_DIR / 'tests_independencia_fallas.csv', 
            index=False
        )
        print(f"✅ Tests de independencia guardados")
    
    # Guardar patrones temporales
    if not temporal_patterns.empty:
        temporal_patterns.to_csv(
            NETWORK_DIR / 'patrones_temporales.csv', 
            index=False
        )
        print(f"✅ Patrones temporales guardados")
    
    # Guardar problemas sistémicos
    if not systemic_problems.empty:
        systemic_problems.to_csv(
            NETWORK_DIR / 'problemas_sistemicos.csv', 
            index=False
        )
        print(f"✅ Análisis de problemas sistémicos guardado")
    
    # Generar reporte resumen
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Estadísticas de independencia
    indep_stats = {}
    if not independence_tests.empty:
        indep_stats = independence_tests['interpretacion'].value_counts().to_dict()
    
    # Estadísticas de problemas sistémicos
    systemic_stats = {}
    if not systemic_problems.empty:
        systemic_stats = systemic_problems['tipo_problema'].value_counts().to_dict()
    
    # Variables técnicas significativas
    sig_tech_vars = []
    if technical_corrs:
        for var, stats in technical_corrs.items():
            if stats['significativo']:
                sig_tech_vars.append({
                    'variable': var,
                    'corr_problemas': stats['corr_problemas'],
                    'corr_fallas': stats['corr_fallas']
                })
    
    report = {
        'timestamp': timestamp,
        'resumen_ejecutivo': {
            'alimentadores_analizados_independencia': len(independence_tests),
            'alimentadores_con_fallas_correlacionadas': 
                len(independence_tests[independence_tests['fallas_independientes'] == False])
                if not independence_tests.empty else 0,
            'variables_tecnicas_significativas': len(sig_tech_vars),
            'alimentadores_problema_sistemico': 
                len(systemic_problems[systemic_problems['tipo_problema'].str.contains('Sistémico')])
                if not systemic_problems.empty else 0,
        },
        'hallazgos_principales': {
            'independencia_fallas': indep_stats,
            'tipos_problemas': systemic_stats,
            'variables_tecnicas_criticas': sig_tech_vars,
            'asociaciones_categoricas': categorical_analysis,
        },
        'recomendaciones_analisis': {
            'alimentadores_prioritarios': 
                systemic_problems[
                    systemic_problems['tipo_problema'].str.contains('Sistémico')
                ].nlargest(5, 'tasa_problemas')[
                    ['alimentador', 'tipo_problema', 'tasa_problemas']
                ].to_dict('records') if not systemic_problems.empty else [],
            'patrones_identificados': {
                'geograficos': len(systemic_problems[
                    systemic_problems['patron_geografico'].notna()
                ]) if 'patron_geografico' in systemic_problems.columns else 0,
                'temporales': len(temporal_patterns[
                    temporal_patterns['patron_temporal'] != 'Sin patrón claro'
                ]) if not temporal_patterns.empty else 0,
            }
        }
    }
    
    with open(REPORTS_DIR / '02_quality_correlation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"✅ Reporte guardado: {REPORTS_DIR / '02_quality_correlation_report.json'}")

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("FASE 0: ANÁLISIS DE CORRELACIÓN DE CALIDAD")
    print("="*60)
    
    # Cargar datos
    transformers_df, feeders_df, spatial_patterns = load_data()
    
    # Test de independencia de fallas
    print("\n🔍 Analizando independencia de fallas...")
    independence_tests = analyze_failure_independence(transformers_df)
    print(f"✅ {len(independence_tests)} alimentadores analizados")
    
    # Análisis de patrones temporales
    print("\n⏱️ Analizando patrones temporales...")
    temporal_patterns = analyze_temporal_patterns(transformers_df)
    print(f"✅ {len(temporal_patterns)} patrones temporales identificados")
    
    # Análisis de correlaciones técnicas
    print("\n🔧 Analizando correlaciones técnicas...")
    technical_corrs, categorical_analysis = analyze_technical_correlations(transformers_df)
    sig_vars = sum(1 for v in technical_corrs.values() if v['significativo'])
    print(f"✅ {sig_vars} variables técnicas con correlación significativa")
    
    # Identificar problemas sistémicos
    print("\n🎯 Identificando problemas sistémicos...")
    systemic_problems = identify_systemic_problems(transformers_df, feeders_df)
    systemic_count = len(
        systemic_problems[systemic_problems['tipo_problema'].str.contains('Sistémico')]
    ) if not systemic_problems.empty else 0
    print(f"✅ {systemic_count} alimentadores con problemas sistémicos")
    
    # Generar visualizaciones
    print("\n📈 Generando visualizaciones...")
    generate_correlation_visualizations(
        transformers_df, independence_tests, 
        technical_corrs, systemic_problems
    )
    
    # Guardar resultados
    print("\n💾 Guardando resultados...")
    save_results(
        independence_tests, temporal_patterns, technical_corrs,
        categorical_analysis, systemic_problems
    )
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DEL ANÁLISIS DE CALIDAD")
    print("="*60)
    
    if not independence_tests.empty:
        print(f"\n📊 Independencia de fallas:")
        for tipo, count in independence_tests['interpretacion'].value_counts().items():
            print(f"   - {tipo}: {count} alimentadores")
    
    if technical_corrs:
        print(f"\n📊 Variables técnicas correlacionadas con problemas:")
        for var, stats in technical_corrs.items():
            if stats['significativo']:
                print(f"   - {var}: r={stats['corr_problemas']:.3f} (p<0.05)")
    
    if not systemic_problems.empty:
        print(f"\n📊 Clasificación de problemas:")
        for tipo, count in systemic_problems['tipo_problema'].value_counts().items():
            print(f"   - {tipo}: {count} alimentadores")
    
    print("\n✅ Análisis de correlación de calidad completado exitosamente!")

if __name__ == "__main__":
    main()