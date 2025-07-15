#!/usr/bin/env python3
"""
FASE 0: Reporte de Caracterización de Red
=========================================
Objetivo: Generar reporte integral de la caracterización de la red EDERSA

Este script:
1. Consolida todos los análisis realizados
2. Identifica los hallazgos principales
3. Genera visualizaciones integradas
4. Produce un reporte ejecutivo
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import warnings
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches

warnings.filterwarnings('ignore')

# Configuración
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
NETWORK_DIR = PROCESSED_DIR / 'network_analysis'
REPORTS_DIR = BASE_DIR / 'reports'
FIGURES_DIR = REPORTS_DIR / 'figures'

def load_all_results():
    """Cargar todos los resultados de análisis previos"""
    
    print("\n📊 Cargando resultados de análisis...")
    
    # Datos principales
    transformers_df = pd.read_csv(NETWORK_DIR / 'transformadores_con_topologia.csv')
    feeders_df = pd.read_csv(NETWORK_DIR / 'alimentadores_caracterizados.csv')
    
    # Resultados de análisis espacial
    spatial_patterns = pd.read_csv(NETWORK_DIR / 'patrones_espaciales_alimentadores.csv')
    
    # Correlaciones
    try:
        distance_corr = pd.read_csv(NETWORK_DIR / 'correlacion_distancia_calidad.csv')
    except:
        distance_corr = pd.DataFrame()
    
    try:
        spatial_clusters = pd.read_csv(NETWORK_DIR / 'clusters_espaciales_problemas.csv')
    except:
        spatial_clusters = pd.DataFrame()
    
    # Análisis de calidad
    try:
        independence_tests = pd.read_csv(NETWORK_DIR / 'tests_independencia_fallas.csv')
    except:
        independence_tests = pd.DataFrame()
    
    try:
        temporal_patterns = pd.read_csv(NETWORK_DIR / 'patrones_temporales.csv')
    except:
        temporal_patterns = pd.DataFrame()
    
    try:
        systemic_problems = pd.read_csv(NETWORK_DIR / 'problemas_sistemicos.csv')
    except:
        systemic_problems = pd.DataFrame()
    
    # Reportes JSON
    reports = {}
    for report_name in ['00_network_topology_report', '01_spatial_correlation_report', 
                       '02_quality_correlation_report']:
        try:
            with open(REPORTS_DIR / f'{report_name}.json', 'r') as f:
                reports[report_name] = json.load(f)
        except:
            reports[report_name] = {}
    
    print("✅ Todos los resultados cargados")
    
    return {
        'transformers': transformers_df,
        'feeders': feeders_df,
        'spatial_patterns': spatial_patterns,
        'distance_corr': distance_corr,
        'spatial_clusters': spatial_clusters,
        'independence_tests': independence_tests,
        'temporal_patterns': temporal_patterns,
        'systemic_problems': systemic_problems,
        'reports': reports
    }

def identify_key_findings(data):
    """Identificar hallazgos clave del análisis"""
    
    findings = {
        'topologia_red': {},
        'patrones_espaciales': {},
        'correlaciones_calidad': {},
        'alimentadores_criticos': []
    }
    
    # 1. Hallazgos de topología
    feeders = data['feeders']
    findings['topologia_red'] = {
        'total_alimentadores': len(feeders),
        'alimentadores_grandes': len(feeders[feeders['num_transformadores'] >= 50]),
        'extension_promedio_km': feeders['diametro_km'].replace([np.inf, -np.inf], np.nan).mean(),
        'densidad_promedio': feeders['densidad_trafos_km2'].replace([np.inf, -np.inf], np.nan).mean(),
        'alimentadores_multi_sucursal': len(feeders[feeders['num_sucursales'] > 1]),
    }
    
    # 2. Hallazgos espaciales
    if not data['spatial_patterns'].empty:
        sp = data['spatial_patterns']
        findings['patrones_espaciales'] = {
            'alimentadores_lineales': len(sp[sp['es_lineal'] == True]),
            'patron_mas_comun': sp['patron_distribucion'].mode().iloc[0] if len(sp) > 0 else 'N/A',
            'autocorrelacion_positiva': len(sp[sp['autocorrelacion_espacial'] == 'positiva']),
            'clustering_promedio': sp['clustering_coefficient'].mean() if 'clustering_coefficient' in sp else 0,
        }
    
    # 3. Hallazgos de calidad
    if not data['systemic_problems'].empty:
        sys_prob = data['systemic_problems']
        findings['correlaciones_calidad'] = {
            'alimentadores_problema_sistemico': len(
                sys_prob[sys_prob['tipo_problema'].str.contains('Sistémico')]
            ),
            'tasa_promedio_problemas': sys_prob['tasa_problemas'].mean(),
            'alimentadores_criticos': len(sys_prob[sys_prob['tasa_problemas'] > 0.5]),
        }
    
    # 4. Identificar top alimentadores críticos
    # Combinar criterios: tasa de problemas, tamaño, patrón sistémico
    critical_feeders = feeders.merge(
        data['systemic_problems'][['alimentador', 'tipo_problema', 'patron_geografico']], 
        on='alimentador', 
        how='left'
    )
    
    # Score de criticidad compuesto
    critical_feeders['score_criticidad'] = (
        critical_feeders['tasa_problemas'] * 0.4 +
        (critical_feeders['num_transformadores'] / critical_feeders['num_transformadores'].max()) * 0.3 +
        (critical_feeders['usuarios_totales'] / critical_feeders['usuarios_totales'].max()) * 0.3
    )
    
    top_critical = critical_feeders.nlargest(10, 'score_criticidad')
    
    for _, feeder in top_critical.iterrows():
        findings['alimentadores_criticos'].append({
            'alimentador': feeder['alimentador'],
            'score': feeder['score_criticidad'],
            'transformadores': feeder['num_transformadores'],
            'usuarios': feeder['usuarios_totales'],
            'tasa_problemas': feeder['tasa_problemas'],
            'tipo_problema': feeder.get('tipo_problema', 'No clasificado'),
            'sucursales': feeder.get('sucursales', [])
        })
    
    return findings

def generate_integrated_visualizations(data, findings):
    """Generar visualizaciones integradas del análisis"""
    
    # Crear PDF con múltiples páginas
    pdf_filename = REPORTS_DIR / 'caracterizacion_red_edersa.pdf'
    
    with PdfPages(pdf_filename) as pdf:
        # Página 1: Resumen general
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle('Caracterización de Red EDERSA - Resumen Ejecutivo', fontsize=16, y=0.98)
        
        # Dividir en 4 cuadrantes
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 1.1 Estadísticas generales
        ax1 = fig.add_subplot(gs[0, 0])
        stats_text = f"""Red EDERSA - Estadísticas Generales

• Total Alimentadores: {findings['topologia_red']['total_alimentadores']}
• Total Transformadores: {len(data['transformers'])}
• Total Usuarios: {data['transformers']['Q_Usuarios'].sum():,.0f}
• Capacidad Total: {data['transformers']['Potencia'].sum()/1000:.1f} MVA

• Alimentadores Grandes (>50 tr): {findings['topologia_red']['alimentadores_grandes']}
• Extensión Promedio: {findings['topologia_red']['extension_promedio_km']:.1f} km
• Tasa Global de Problemas: {(data['transformers']['Resultado'] != 'Correcta').mean():.1%}
"""
        ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes, 
                fontsize=10, verticalalignment='top', family='monospace')
        ax1.axis('off')
        
        # 1.2 Distribución de problemas
        ax2 = fig.add_subplot(gs[0, 1])
        problem_dist = data['transformers']['Resultado'].value_counts()
        colors = {'Correcta': 'green', 'Penalizada': 'yellow', 'Fallida': 'red'}
        
        wedges, texts, autotexts = ax2.pie(
            problem_dist.values, 
            labels=problem_dist.index,
            colors=[colors.get(x, 'gray') for x in problem_dist.index],
            autopct='%1.1f%%',
            startangle=90
        )
        ax2.set_title('Distribución de Estados de Calidad')
        
        # 1.3 Top 10 alimentadores críticos
        ax3 = fig.add_subplot(gs[1, :])
        top_feeders = findings['alimentadores_criticos'][:10]
        
        feeders_names = [f['alimentador'][:20] for f in top_feeders]
        feeders_scores = [f['score'] for f in top_feeders]
        feeders_users = [f['usuarios'] for f in top_feeders]
        
        x = np.arange(len(feeders_names))
        width = 0.35
        
        ax3.bar(x - width/2, feeders_scores, width, label='Score Criticidad', color='red', alpha=0.7)
        ax3_twin = ax3.twinx()
        ax3_twin.bar(x + width/2, feeders_users, width, label='Usuarios', color='blue', alpha=0.7)
        
        ax3.set_xlabel('Alimentador')
        ax3.set_ylabel('Score de Criticidad', color='red')
        ax3_twin.set_ylabel('Usuarios', color='blue')
        ax3.set_title('Top 10 Alimentadores Críticos')
        ax3.set_xticks(x)
        ax3.set_xticklabels(feeders_names, rotation=45, ha='right')
        
        # Leyendas
        ax3.legend(loc='upper left')
        ax3_twin.legend(loc='upper right')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Página 2: Análisis espacial
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle('Análisis Espacial de la Red', fontsize=16, y=0.98)
        
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 2.1 Patrones de distribución
        ax1 = fig.add_subplot(gs[0, 0])
        if not data['spatial_patterns'].empty:
            pattern_counts = data['spatial_patterns']['patron_distribucion'].value_counts()
            ax1.bar(pattern_counts.index, pattern_counts.values)
            ax1.set_xlabel('Patrón de Distribución')
            ax1.set_ylabel('Número de Alimentadores')
            ax1.set_title('Patrones Espaciales Identificados')
            for i, v in enumerate(pattern_counts.values):
                ax1.text(i, v + 0.5, str(v), ha='center', va='bottom')
        
        # 2.2 Autocorrelación espacial
        ax2 = fig.add_subplot(gs[0, 1])
        if 'autocorrelacion_espacial' in data['spatial_patterns'].columns:
            autocorr_counts = data['spatial_patterns']['autocorrelacion_espacial'].value_counts()
            colors_auto = {'positiva': 'red', 'ninguna': 'gray', 'negativa': 'blue'}
            bars = ax2.bar(autocorr_counts.index, autocorr_counts.values,
                          color=[colors_auto.get(x, 'gray') for x in autocorr_counts.index])
            ax2.set_xlabel('Tipo de Autocorrelación')
            ax2.set_ylabel('Número de Alimentadores')
            ax2.set_title('Autocorrelación Espacial de Fallas')
            for bar, v in zip(bars, autocorr_counts.values):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        str(v), ha='center', va='bottom')
        
        # 2.3 Mapa de densidad de problemas (simplificado)
        ax3 = fig.add_subplot(gs[1, :])
        
        # Crear hexbin de problemas
        problem_trafos = data['transformers'][
            (data['transformers']['Resultado'] != 'Correcta') &
            (data['transformers']['Coord_X'].notna())
        ]
        
        if len(problem_trafos) > 0:
            hb = ax3.hexbin(problem_trafos['Coord_X'], problem_trafos['Coord_Y'],
                           gridsize=20, cmap='YlOrRd', mincnt=1)
            cb = plt.colorbar(hb, ax=ax3)
            cb.set_label('Número de Transformadores con Problemas')
            ax3.set_xlabel('Longitud')
            ax3.set_ylabel('Latitud')
            ax3.set_title('Densidad Espacial de Problemas')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Página 3: Análisis de correlaciones
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle('Análisis de Correlaciones y Patrones', fontsize=16, y=0.98)
        
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 3.1 Tipos de problemas
        ax1 = fig.add_subplot(gs[0, 0])
        if not data['systemic_problems'].empty:
            problem_types = data['systemic_problems']['tipo_problema'].value_counts()
            ax1.pie(problem_types.values, labels=problem_types.index,
                   autopct='%1.1f%%', startangle=90)
            ax1.set_title('Clasificación de Problemas')
        
        # 3.2 Correlación tamaño vs problemas
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.scatter(data['feeders']['num_transformadores'],
                   data['feeders']['tasa_problemas'] * 100,
                   alpha=0.6, s=50)
        ax2.set_xlabel('Número de Transformadores')
        ax2.set_ylabel('Tasa de Problemas (%)')
        ax2.set_title('Relación Tamaño vs Problemas')
        ax2.grid(True, alpha=0.3)
        
        # 3.3 Resumen de hallazgos
        ax3 = fig.add_subplot(gs[1, :])
        
        hallazgos_text = f"""Hallazgos Principales:

• Patrones Espaciales:
  - {findings['patrones_espaciales'].get('alimentadores_lineales', 0)} alimentadores con distribución lineal
  - {findings['patrones_espaciales'].get('autocorrelacion_positiva', 0)} alimentadores con autocorrelación positiva de fallas
  - Patrón predominante: {findings['patrones_espaciales'].get('patron_mas_comun', 'N/A')}

• Correlaciones de Calidad:
  - {findings['correlaciones_calidad'].get('alimentadores_problema_sistemico', 0)} alimentadores con problemas sistémicos
  - {findings['correlaciones_calidad'].get('alimentadores_criticos', 0)} alimentadores con >50% de problemas
  - Tasa promedio de problemas: {findings['correlaciones_calidad'].get('tasa_promedio_problemas', 0):.1%}

• Recomendaciones:
  - Priorizar intervención en alimentadores con problemas sistémicos
  - Considerar soluciones diferenciadas según patrón espacial
  - Focalizar en alimentadores con alta concentración de usuarios afectados
"""
        ax3.text(0.05, 0.95, hallazgos_text, transform=ax3.transAxes,
                fontsize=10, verticalalignment='top', family='monospace')
        ax3.axis('off')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Agregar metadatos al PDF
        d = pdf.infodict()
        d['Title'] = 'Caracterización de Red EDERSA - Fase 0'
        d['Author'] = 'Sistema de Análisis EDERSA'
        d['Subject'] = 'Análisis de topología y calidad de red eléctrica'
        d['Keywords'] = 'EDERSA, Red Eléctrica, Calidad, Topología'
        d['CreationDate'] = datetime.now()
    
    print(f"✅ Reporte PDF generado: {pdf_filename}")
    
    return str(pdf_filename)

def generate_executive_summary(data, findings):
    """Generar resumen ejecutivo en formato JSON y Markdown"""
    
    # Preparar datos para el resumen
    total_transformers = len(data['transformers'])
    total_users = data['transformers']['Q_Usuarios'].sum()
    total_power_mva = data['transformers']['Potencia'].sum() / 1000
    
    problem_rate = (data['transformers']['Resultado'] != 'Correcta').mean()
    failure_rate = (data['transformers']['Resultado'] == 'Fallida').mean()
    
    # Crear resumen ejecutivo
    executive_summary = {
        'metadata': {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'version': '1.0',
            'fase': 'Fase 0 - Caracterización de Red'
        },
        'resumen_red': {
            'total_alimentadores': findings['topologia_red']['total_alimentadores'],
            'total_transformadores': total_transformers,
            'total_usuarios': int(total_users),
            'capacidad_total_mva': round(total_power_mva, 2),
            'tasa_problemas_global': round(problem_rate, 3),
            'tasa_fallas_global': round(failure_rate, 3)
        },
        'hallazgos_principales': {
            'topologia': {
                'alimentadores_grandes': findings['topologia_red']['alimentadores_grandes'],
                'extension_promedio_km': round(
                    findings['topologia_red']['extension_promedio_km'], 1
                ) if not np.isnan(findings['topologia_red']['extension_promedio_km']) else 'N/A',
                'alimentadores_multi_sucursal': findings['topologia_red']['alimentadores_multi_sucursal']
            },
            'patrones_espaciales': findings['patrones_espaciales'],
            'problemas_calidad': findings['correlaciones_calidad']
        },
        'alimentadores_criticos_top10': findings['alimentadores_criticos'],
        'recomendaciones': {
            'inmediatas': [
                'Priorizar intervención en alimentadores con problemas sistémicos identificados',
                'Implementar monitoreo intensivo en los 10 alimentadores más críticos',
                'Considerar refuerzo de red en zonas con alta densidad de problemas'
            ],
            'planificacion': [
                'Desarrollar estrategias diferenciadas según patrón espacial de cada alimentador',
                'Evaluar viabilidad de GD en alimentadores con problemas sistémicos',
                'Planificar mantenimiento preventivo basado en correlaciones técnicas identificadas'
            ]
        },
        'proximos_pasos': [
            'Fase 1: Análisis detallado de los 10 alimentadores críticos',
            'Fase 2: Clustering para identificación de zonas óptimas para GD',
            'Fase 3: Dimensionamiento preliminar de soluciones'
        ]
    }
    
    # Guardar JSON
    json_path = REPORTS_DIR / 'resumen_ejecutivo_fase0.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(executive_summary, f, indent=2, ensure_ascii=False)
    print(f"✅ Resumen ejecutivo JSON guardado: {json_path}")
    
    # Generar Markdown
    md_content = f"""# Caracterización de Red EDERSA - Resumen Ejecutivo

**Fecha**: {datetime.now().strftime("%d de %B de %Y")}  
**Fase**: 0 - Comprensión de la Topología de Red

## 1. Resumen de la Red

- **Total Alimentadores**: {findings['topologia_red']['total_alimentadores']}
- **Total Transformadores**: {total_transformers:,}
- **Total Usuarios**: {int(total_users):,}
- **Capacidad Total**: {total_power_mva:.1f} MVA
- **Tasa Global de Problemas**: {problem_rate:.1%}
- **Tasa de Fallas**: {failure_rate:.1%}

## 2. Hallazgos Principales

### 2.1 Topología de Red
- {findings['topologia_red']['alimentadores_grandes']} alimentadores grandes (>50 transformadores)
- Extensión promedio de alimentadores: {findings['topologia_red']['extension_promedio_km']:.1f} km
- {findings['topologia_red']['alimentadores_multi_sucursal']} alimentadores atienden múltiples sucursales

### 2.2 Patrones Espaciales
- {findings['patrones_espaciales'].get('alimentadores_lineales', 0)} alimentadores con distribución lineal
- {findings['patrones_espaciales'].get('autocorrelacion_positiva', 0)} alimentadores muestran autocorrelación positiva de fallas
- Patrón predominante: {findings['patrones_espaciales'].get('patron_mas_comun', 'aleatorio')}

### 2.3 Problemas de Calidad
- {findings['correlaciones_calidad'].get('alimentadores_problema_sistemico', 0)} alimentadores con problemas sistémicos
- {findings['correlaciones_calidad'].get('alimentadores_criticos', 0)} alimentadores con tasa de problemas >50%
- Variables técnicas correlacionadas con problemas: Potencia, Usuarios, Factor de utilización

## 3. Top 10 Alimentadores Críticos

| Alimentador | Transformadores | Usuarios | Tasa Problemas | Tipo |
|------------|-----------------|----------|----------------|------|
"""
    
    for i, feeder in enumerate(findings['alimentadores_criticos'][:10], 1):
        md_content += f"| {feeder['alimentador']} | {feeder['transformadores']} | {feeder['usuarios']:,} | {feeder['tasa_problemas']:.1%} | {feeder['tipo_problema']} |\n"
    
    md_content += """
## 4. Recomendaciones

### Acciones Inmediatas
1. Priorizar intervención en alimentadores con problemas sistémicos
2. Implementar monitoreo intensivo en los 10 alimentadores críticos
3. Reforzar la red en zonas con alta densidad de problemas

### Planificación Estratégica
1. Desarrollar estrategias diferenciadas según patrón espacial
2. Evaluar viabilidad de Generación Distribuida en zonas críticas
3. Planificar mantenimiento preventivo basado en correlaciones identificadas

## 5. Próximos Pasos

- **Fase 1**: Análisis detallado de alimentadores críticos
- **Fase 2**: Clustering para optimización de ubicaciones GD
- **Fase 3**: Dimensionamiento preliminar de soluciones

---
*Documento generado automáticamente por el Sistema de Análisis EDERSA*
"""
    
    md_path = REPORTS_DIR / 'resumen_ejecutivo_fase0.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"✅ Resumen ejecutivo Markdown guardado: {md_path}")
    
    return executive_summary

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("FASE 0: REPORTE DE CARACTERIZACIÓN DE RED")
    print("="*60)
    
    # Cargar todos los resultados
    data = load_all_results()
    
    # Identificar hallazgos clave
    print("\n🔍 Identificando hallazgos clave...")
    findings = identify_key_findings(data)
    print(f"✅ {len(findings['alimentadores_criticos'])} alimentadores críticos identificados")
    
    # Generar visualizaciones integradas
    print("\n📈 Generando visualizaciones integradas...")
    pdf_path = generate_integrated_visualizations(data, findings)
    
    # Generar resumen ejecutivo
    print("\n📝 Generando resumen ejecutivo...")
    executive_summary = generate_executive_summary(data, findings)
    
    # Guardar reporte final de caracterización
    final_report = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'fase': 'Fase 0 - Caracterización de Red Completada',
        'archivos_generados': {
            'datos_procesados': [
                'alimentadores_caracterizados.csv',
                'transformadores_con_topologia.csv',
                'patrones_espaciales_alimentadores.csv',
                'correlacion_distancia_calidad.csv',
                'clusters_espaciales_problemas.csv',
                'tests_independencia_fallas.csv',
                'patrones_temporales.csv',
                'problemas_sistemicos.csv'
            ],
            'reportes': [
                '00_network_topology_report.json',
                '01_spatial_correlation_report.json',
                '02_quality_correlation_report.json',
                'resumen_ejecutivo_fase0.json',
                'resumen_ejecutivo_fase0.md'
            ],
            'visualizaciones': [
                'network_topology_analysis.png',
                'spatial_patterns_feeders.png',
                'spatial_patterns_summary.png',
                'quality_correlations.png',
                'caracterizacion_red_edersa.pdf'
            ]
        },
        'resumen_hallazgos': findings,
        'siguiente_fase': 'Fase 1 - Análisis detallado de alimentadores críticos'
    }
    
    report_path = REPORTS_DIR / 'fase0_caracterizacion_completa.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False, default=str)
    print(f"✅ Reporte final guardado: {report_path}")
    
    # Resumen final en consola
    print("\n" + "="*60)
    print("CARACTERIZACIÓN DE RED COMPLETADA")
    print("="*60)
    
    print(f"\n📊 Resumen de la Red EDERSA:")
    print(f"   - Alimentadores: {findings['topologia_red']['total_alimentadores']}")
    print(f"   - Transformadores: {len(data['transformers']):,}")
    print(f"   - Usuarios: {data['transformers']['Q_Usuarios'].sum():,.0f}")
    print(f"   - Capacidad: {data['transformers']['Potencia'].sum()/1000:.1f} MVA")
    
    print(f"\n🎯 Alimentadores Críticos Identificados: {len(findings['alimentadores_criticos'])}")
    for i, feeder in enumerate(findings['alimentadores_criticos'][:5], 1):
        print(f"   {i}. {feeder['alimentador']} - {feeder['usuarios']:,} usuarios - {feeder['tasa_problemas']:.1%} problemas")
    
    print(f"\n📈 Documentos generados:")
    print(f"   - Reporte PDF: caracterizacion_red_edersa.pdf")
    print(f"   - Resumen ejecutivo: resumen_ejecutivo_fase0.md")
    print(f"   - Datos procesados: {len(final_report['archivos_generados']['datos_procesados'])} archivos")
    
    print("\n✅ Fase 0 completada exitosamente!")
    print("🚀 Listo para proceder con Fase 1: Análisis de alimentadores críticos")

if __name__ == "__main__":
    main()