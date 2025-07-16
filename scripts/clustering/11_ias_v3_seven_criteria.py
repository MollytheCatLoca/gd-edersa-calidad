#!/usr/bin/env python3
"""
FASE 2.5 - Script 11: IAS 3.0 con 7 Criterios
=============================================
Implementación del Índice de Aptitud Solar versión 3.0 incorporando:
- C1-C5: Criterios originales de coincidencia solar
- C6: Soporte reactivo nocturno (Q at Night)
- C7: Disponibilidad de terreno

Este script re-prioriza los clusters considerando la capacidad de los
inversores solares de operar como STATCOM durante la noche.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMap
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
CLUSTERING_DIR = REPORTS_DIR / "clustering"
IAS_V3_DIR = CLUSTERING_DIR / "ias_v3"
IAS_V3_DIR.mkdir(exist_ok=True)

class IAS_V3_Calculator:
    """
    Calculador del Índice de Aptitud Solar versión 3.0 con 7 criterios.
    Incorpora análisis de soporte reactivo nocturno y disponibilidad de terreno.
    """
    
    def __init__(self):
        """Inicializa el calculador con pesos AHP actualizados"""
        
        # Pesos de criterios según matriz AHP actualizada
        # Nota: C6 (Q at Night) tiene peso significativo dado prioridad del cliente
        self.weights = {
            'C1': 0.087,  # Criticidad (reducido)
            'C2': 0.201,  # Coincidencia solar-demanda (mantenido alto)
            'C3': 0.031,  # Vulnerabilidad eléctrica (reducido)
            'C4': 0.056,  # Cargabilidad de activos (reducido)
            'C5': 0.120,  # Riesgo RPF (ajustado)
            'C6': 0.301,  # Soporte reactivo nocturno (NUEVO - prioridad alta)
            'C7': 0.204   # Disponibilidad de terreno (NUEVO - importante)
        }
        
        # Verificar que suman 1.0
        assert abs(sum(self.weights.values()) - 1.0) < 0.001, "Los pesos deben sumar 1.0"
        
        logger.info(f"IAS 3.0 inicializado con pesos: {self.weights}")
        
    def calculate_c6_score(self, row):
        """
        Calcula el score C6 - Aptitud para Soporte Reactivo Nocturno.
        
        Lógica inversa a C2: zonas residenciales ahora son valiosas porque
        tienen picos de demanda nocturnos que requieren soporte de tensión.
        """
        
        # C6_Carga: Basado en porcentaje de carga residencial
        # Score alto = alta carga residencial (inverso de C2)
        if row['perfil_dominante'] == 'Residencial':
            c6_carga = 10.0
        elif row['perfil_dominante'] == 'Rural':
            c6_carga = 8.0
        elif row['perfil_dominante'] == 'Mixto':
            c6_carga = 6.0
        elif row['perfil_dominante'] == 'Oficial':
            c6_carga = 4.0
        elif row['perfil_dominante'] == 'Industrial':
            c6_carga = 3.0
        elif row['perfil_dominante'] == 'Comercial':
            c6_carga = 2.0
        else:
            c6_carga = 5.0
            
        # C6_Necesidad: Reutilizar criticidad (C1) como proxy de problemas de tensión
        c1_score = row.get('C1_criticidad', 5.0)
        
        # Score C6 combinado (70% perfil nocturno, 30% criticidad)
        c6_score = (0.7 * c6_carga) + (0.3 * c1_score)
        
        return min(c6_score, 10.0)
    
    def calculate_ias_v3(self, df_clusters):
        """
        Calcula el IAS 3.0 para cada cluster incorporando todos los criterios.
        """
        logger.info("Calculando IAS 3.0 con 7 criterios...")
        
        # Verificar que tenemos todos los datos necesarios
        required_columns = [
            'C1_criticidad', 'C2_coincidencia', 'C3_vulnerabilidad',
            'C4_cargabilidad', 'C5_riesgo_rpf', 'C7_land_availability',
            'perfil_dominante'
        ]
        
        missing_cols = [col for col in required_columns if col not in df_clusters.columns]
        if missing_cols:
            logger.warning(f"Columnas faltantes: {missing_cols}. Se usarán valores default.")
        
        # Calcular C6 para cada cluster
        df_clusters['C6_q_at_night'] = df_clusters.apply(self.calculate_c6_score, axis=1)
        
        # Normalizar todos los scores a escala 0-10 si es necesario
        for criterion in ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']:
            col_name = f'{criterion}_' + {
                'C1': 'criticidad',
                'C2': 'coincidencia', 
                'C3': 'vulnerabilidad',
                'C4': 'cargabilidad',
                'C5': 'riesgo_rpf',
                'C6': 'q_at_night',
                'C7': 'land_availability'
            }[criterion]
            
            if col_name in df_clusters.columns:
                # Asegurar que está en escala 0-10
                if df_clusters[col_name].max() <= 1.0:
                    df_clusters[col_name] = df_clusters[col_name] * 10
            else:
                # Valor default si no existe
                df_clusters[col_name] = 5.0
                
        # Calcular IAS 3.0
        df_clusters['ias_v3'] = 0
        for criterion, weight in self.weights.items():
            col_name = f'{criterion}_' + {
                'C1': 'criticidad',
                'C2': 'coincidencia', 
                'C3': 'vulnerabilidad',
                'C4': 'cargabilidad',
                'C5': 'riesgo_rpf',
                'C6': 'q_at_night',
                'C7': 'land_availability'
            }[criterion]
            
            df_clusters['ias_v3'] += weight * df_clusters[col_name]
            
        # Normalizar IAS a escala 0-1
        df_clusters['ias_v3'] = df_clusters['ias_v3'] / 10.0
        
        # Calcular cambio respecto a IAS original
        if 'ias_promedio' in df_clusters.columns:
            df_clusters['delta_ias'] = df_clusters['ias_v3'] - df_clusters['ias_promedio']
            df_clusters['rank_change'] = (
                df_clusters['ias_promedio'].rank(ascending=False) - 
                df_clusters['ias_v3'].rank(ascending=False)
            ).astype(int)
        
        return df_clusters
    
    def analyze_criterion_impact(self, df_clusters):
        """
        Analiza el impacto de cada criterio en el score final.
        """
        logger.info("Analizando impacto de criterios...")
        
        # Contribución de cada criterio al IAS
        contributions = {}
        
        for criterion, weight in self.weights.items():
            col_name = f'{criterion}_' + {
                'C1': 'criticidad',
                'C2': 'coincidencia', 
                'C3': 'vulnerabilidad',
                'C4': 'cargabilidad',
                'C5': 'riesgo_rpf',
                'C6': 'q_at_night',
                'C7': 'land_availability'
            }[criterion]
            
            if col_name in df_clusters.columns:
                # Contribución promedio
                avg_score = df_clusters[col_name].mean()
                contributions[criterion] = {
                    'weight': weight,
                    'avg_score': avg_score / 10.0,  # Normalizado 0-1
                    'contribution': weight * avg_score / 10.0,
                    'relative_impact': (weight * avg_score / 10.0) / df_clusters['ias_v3'].mean()
                }
        
        return contributions

def create_ias_comparison_visualization(df_original, df_v3):
    """
    Crea visualización comparando IAS original vs IAS 3.0.
    """
    logger.info("Creando visualización comparativa IAS...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Comparación IAS Original vs IAS 3.0 (con Q at Night y Terreno)', fontsize=16)
    
    # 1. Scatter plot IAS original vs IAS 3.0
    ax = axes[0, 0]
    scatter = ax.scatter(df_v3['ias_promedio'], df_v3['ias_v3'], 
                        c=df_v3['delta_ias'], cmap='RdYlGn', 
                        s=df_v3['gd_recomendada_mw']*5, alpha=0.7)
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    ax.set_xlabel('IAS Original')
    ax.set_ylabel('IAS 3.0')
    ax.set_title('Correlación entre Metodologías')
    plt.colorbar(scatter, ax=ax, label='Δ IAS')
    
    # Anotar clusters con mayor cambio
    top_changes = df_v3.nlargest(3, 'delta_ias')
    for _, cluster in top_changes.iterrows():
        ax.annotate(f"C{cluster['cluster_id']}", 
                   (cluster['ias_promedio'], cluster['ias_v3']),
                   xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    # 2. Cambios en ranking
    ax = axes[0, 1]
    df_sorted = df_v3.sort_values('rank_change')
    colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' 
              for x in df_sorted['rank_change']]
    bars = ax.barh(range(len(df_sorted)), df_sorted['rank_change'], color=colors)
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels([f"Cluster {id}" for id in df_sorted['cluster_id']])
    ax.set_xlabel('Cambio en Ranking (positivo = mejora)')
    ax.set_title('Cambios en Posición del Ranking')
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    
    # 3. Contribución de criterios nuevos
    ax = axes[1, 0]
    df_v3_sorted = df_v3.sort_values('ias_v3', ascending=False).head(10)
    x = np.arange(len(df_v3_sorted))
    width = 0.35
    
    # Scores normalizados
    c6_scores = df_v3_sorted['C6_q_at_night'] / 10
    c7_scores = df_v3_sorted['C7_land_availability'] / 10
    
    bars1 = ax.bar(x - width/2, c6_scores, width, label='C6: Q at Night', color='purple')
    bars2 = ax.bar(x + width/2, c7_scores, width, label='C7: Terreno', color='orange')
    
    ax.set_xlabel('Top 10 Clusters por IAS 3.0')
    ax.set_ylabel('Score Normalizado (0-1)')
    ax.set_title('Contribución de Nuevos Criterios')
    ax.set_xticks(x)
    ax.set_xticklabels([f"C{id}" for id in df_v3_sorted['cluster_id']])
    ax.legend()
    
    # 4. Perfil dominante vs IAS 3.0
    ax = axes[1, 1]
    profile_analysis = df_v3.groupby('perfil_dominante').agg({
        'ias_promedio': 'mean',
        'ias_v3': 'mean',
        'cluster_id': 'count'
    }).round(3)
    
    x = np.arange(len(profile_analysis))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, profile_analysis['ias_promedio'], 
                    width, label='IAS Original', color='blue', alpha=0.7)
    bars2 = ax.bar(x + width/2, profile_analysis['ias_v3'], 
                    width, label='IAS 3.0', color='green', alpha=0.7)
    
    ax.set_xlabel('Perfil Dominante')
    ax.set_ylabel('IAS Promedio')
    ax.set_title('Impacto por Tipo de Perfil')
    ax.set_xticks(x)
    ax.set_xticklabels(profile_analysis.index, rotation=45)
    ax.legend()
    
    # Agregar conteo de clusters
    for i, (idx, row) in enumerate(profile_analysis.iterrows()):
        ax.text(i, max(row['ias_promedio'], row['ias_v3']) + 0.01, 
                f"n={row['cluster_id']}", ha='center', fontsize=8)
    
    plt.tight_layout()
    
    # Guardar
    fig_path = IAS_V3_DIR / "ias_comparison_analysis.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Visualización guardada en: {fig_path}")

def create_criterion_impact_chart(contributions):
    """
    Crea gráfico de impacto de cada criterio.
    """
    logger.info("Creando gráfico de impacto de criterios...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Análisis de Impacto de Criterios en IAS 3.0', fontsize=14)
    
    # Preparar datos
    criteria = list(contributions.keys())
    weights = [contributions[c]['weight'] for c in criteria]
    avg_scores = [contributions[c]['avg_score'] for c in criteria]
    contrib = [contributions[c]['contribution'] for c in criteria]
    
    # 1. Pesos vs Scores promedio
    x = np.arange(len(criteria))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, weights, width, label='Peso AHP', color='blue', alpha=0.7)
    bars2 = ax1.bar(x + width/2, avg_scores, width, label='Score Promedio', color='green', alpha=0.7)
    
    ax1.set_xlabel('Criterio')
    ax1.set_ylabel('Valor (0-1)')
    ax1.set_title('Pesos AHP vs Scores Promedio')
    ax1.set_xticks(x)
    ax1.set_xticklabels(criteria)
    ax1.legend()
    ax1.set_ylim(0, 0.4)
    
    # Agregar etiquetas
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                f'{height:.3f}', ha='center', va='bottom', fontsize=8)
    
    # 2. Contribución total al IAS
    colors_map = {
        'C1': '#FF6B6B', 'C2': '#4ECDC4', 'C3': '#45B7D1',
        'C4': '#96CEB4', 'C5': '#FECA57', 'C6': '#9B59B6', 'C7': '#FF8C42'
    }
    colors_list = [colors_map.get(c, '#95A5A6') for c in criteria]
    
    bars = ax2.bar(criteria, contrib, color=colors_list, alpha=0.8)
    ax2.set_xlabel('Criterio')
    ax2.set_ylabel('Contribución al IAS')
    ax2.set_title('Contribución de cada Criterio al Score Final')
    
    # Agregar valores
    for bar, val in zip(bars, contrib):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.001,
                f'{val:.3f}', ha='center', va='bottom', fontsize=9)
    
    # Línea de contribución uniforme
    uniform_contrib = 1.0 / len(criteria) * np.mean(avg_scores)
    ax2.axhline(y=uniform_contrib, color='red', linestyle='--', alpha=0.5,
                label=f'Contribución uniforme ({uniform_contrib:.3f})')
    ax2.legend()
    
    plt.tight_layout()
    
    # Guardar
    fig_path = IAS_V3_DIR / "criterion_impact_analysis.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Gráfico de impacto guardado en: {fig_path}")

def create_priority_map_v3(df_clusters):
    """
    Crea mapa de priorización con IAS 3.0.
    """
    logger.info("Creando mapa de priorización IAS 3.0...")
    
    # Centro del mapa
    center_lat = df_clusters['centroid_lat'].mean()
    center_lon = df_clusters['centroid_lon'].mean()
    
    # Crear mapa
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Escala de colores para IAS 3.0
    def get_color(ias_score):
        if ias_score >= 0.7:
            return '#006400'  # Verde oscuro
        elif ias_score >= 0.6:
            return '#228B22'  # Verde
        elif ias_score >= 0.5:
            return '#FFFF00'  # Amarillo
        elif ias_score >= 0.4:
            return '#FFA500'  # Naranja
        else:
            return '#FF0000'  # Rojo
    
    # Agregar clusters
    for _, cluster in df_clusters.iterrows():
        # Color basado en IAS 3.0
        color = get_color(cluster['ias_v3'])
        
        # Tamaño basado en capacidad GD
        radius = np.sqrt(cluster['gd_recomendada_mw']) * 1000
        
        # Crear popup con información detallada
        popup_text = f"""
        <b>Cluster {cluster['cluster_id']}</b><br>
        <b>IAS 3.0:</b> {cluster['ias_v3']:.3f}<br>
        <b>IAS Original:</b> {cluster.get('ias_promedio', 0):.3f}<br>
        <b>Cambio Ranking:</b> {cluster.get('rank_change', 0):+d}<br>
        <hr>
        <b>Perfil:</b> {cluster['perfil_dominante']}<br>
        <b>GD Recomendada:</b> {cluster['gd_recomendada_mw']:.1f} MW<br>
        <b>Usuarios:</b> {cluster['n_usuarios']:,}<br>
        <hr>
        <b>Scores por Criterio:</b><br>
        C1 (Criticidad): {cluster.get('C1_criticidad', 0):.1f}<br>
        C2 (Coincidencia): {cluster.get('C2_coincidencia', 0):.1f}<br>
        C3 (Vulnerabilidad): {cluster.get('C3_vulnerabilidad', 0):.1f}<br>
        C4 (Cargabilidad): {cluster.get('C4_cargabilidad', 0):.1f}<br>
        C5 (Riesgo RPF): {cluster.get('C5_riesgo_rpf', 0):.1f}<br>
        <b>C6 (Q at Night): {cluster.get('C6_q_at_night', 0):.1f}</b><br>
        <b>C7 (Terreno): {cluster.get('C7_land_availability', 0):.1f}</b>
        """
        
        # Agregar círculo
        folium.Circle(
            location=[cluster['centroid_lat'], cluster['centroid_lon']],
            radius=radius,
            popup=popup_text,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=2
        ).add_to(m)
        
        # Agregar marcador para top 5
        if cluster['ias_v3'] >= df_clusters['ias_v3'].nlargest(5).min():
            folium.Marker(
                location=[cluster['centroid_lat'], cluster['centroid_lon']],
                icon=folium.Icon(color='green', icon='star'),
                popup=popup_text
            ).add_to(m)
    
    # Agregar leyenda
    legend_html = '''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: 180px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px">
    <p style="margin: 10px;"><b>IAS 3.0 Score</b></p>
    <p style="margin: 10px;"><span style="color:#006400;">●</span> ≥0.70 (Excelente)</p>
    <p style="margin: 10px;"><span style="color:#228B22;">●</span> 0.60-0.70 (Muy Bueno)</p>
    <p style="margin: 10px;"><span style="color:#FFFF00;">●</span> 0.50-0.60 (Bueno)</p>
    <p style="margin: 10px;"><span style="color:#FFA500;">●</span> 0.40-0.50 (Regular)</p>
    <p style="margin: 10px;"><span style="color:#FF0000;">●</span> <0.40 (Bajo)</p>
    <p style="margin: 10px;">⭐ = Top 5 Clusters</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Guardar mapa
    map_path = IAS_V3_DIR / "priority_map_ias_v3.html"
    m.save(str(map_path))
    logger.info(f"Mapa guardado en: {map_path}")
    
    return m

def generate_ias_v3_report(df_clusters, contributions):
    """
    Genera reporte completo de IAS 3.0.
    """
    logger.info("Generando reporte IAS 3.0...")
    
    # Estadísticas generales
    report = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'methodology': 'IAS 3.0 - 7 Criterios',
            'total_clusters': len(df_clusters),
            'criteria_weights': {k: float(v['weight']) for k, v in contributions.items()}
        },
        'summary': {
            'avg_ias_v3': float(df_clusters['ias_v3'].mean()),
            'avg_ias_original': float(df_clusters['ias_promedio'].mean()),
            'avg_delta': float(df_clusters['delta_ias'].mean()),
            'clusters_improved': int((df_clusters['delta_ias'] > 0).sum()),
            'clusters_worsened': int((df_clusters['delta_ias'] < 0).sum())
        },
        'top_5_clusters': [],
        'biggest_changes': {
            'gainers': [],
            'losers': []
        },
        'profile_analysis': {},
        'recommendations': []
    }
    
    # Top 5 clusters por IAS 3.0
    top_5 = df_clusters.nlargest(5, 'ias_v3')
    for _, cluster in top_5.iterrows():
        report['top_5_clusters'].append({
            'cluster_id': int(cluster['cluster_id']),
            'ias_v3': float(cluster['ias_v3']),
            'ias_original': float(cluster['ias_promedio']),
            'delta': float(cluster['delta_ias']),
            'rank_change': int(cluster['rank_change']),
            'perfil': cluster['perfil_dominante'],
            'gd_mw': float(cluster['gd_recomendada_mw']),
            'usuarios': int(cluster['n_usuarios']),
            'c6_score': float(cluster['C6_q_at_night']),
            'c7_score': float(cluster['C7_land_availability'])
        })
    
    # Mayores ganadores y perdedores
    if 'rank_change' in df_clusters.columns:
        gainers = df_clusters[df_clusters['rank_change'] > 0].nlargest(3, 'rank_change')
        for _, cluster in gainers.iterrows():
            report['biggest_changes']['gainers'].append({
                'cluster_id': int(cluster['cluster_id']),
                'rank_change': int(cluster['rank_change']),
                'perfil': cluster['perfil_dominante'],
                'reason': 'Alto score en Q at Night' if cluster['C6_q_at_night'] > 7 else 'Buena disponibilidad de terreno'
            })
        
        losers = df_clusters[df_clusters['rank_change'] < 0].nsmallest(3, 'rank_change')
        for _, cluster in losers.iterrows():
            report['biggest_changes']['losers'].append({
                'cluster_id': int(cluster['cluster_id']),
                'rank_change': int(cluster['rank_change']),
                'perfil': cluster['perfil_dominante'],
                'reason': 'Bajo score en terreno' if cluster['C7_land_availability'] < 3 else 'Limitado beneficio nocturno'
            })
    
    # Análisis por perfil
    profile_stats = df_clusters.groupby('perfil_dominante').agg({
        'ias_v3': ['mean', 'std', 'count'],
        'delta_ias': 'mean',
        'C6_q_at_night': 'mean',
        'C7_land_availability': 'mean'
    }).round(3)
    
    for perfil in profile_stats.index:
        report['profile_analysis'][perfil] = {
            'avg_ias_v3': float(profile_stats.loc[perfil, ('ias_v3', 'mean')]),
            'std_ias_v3': float(profile_stats.loc[perfil, ('ias_v3', 'std')]),
            'count': int(profile_stats.loc[perfil, ('ias_v3', 'count')]),
            'avg_delta': float(profile_stats.loc[perfil, ('delta_ias', 'mean')]),
            'avg_c6': float(profile_stats.loc[perfil, ('C6_q_at_night', 'mean')]),
            'avg_c7': float(profile_stats.loc[perfil, ('C7_land_availability', 'mean')])
        }
    
    # Recomendaciones
    report['recommendations'] = [
        "CAMBIO ESTRATÉGICO: Considerar clusters residenciales/mixtos para maximizar beneficio 24h",
        "Clusters con IAS 3.0 > 0.6 son candidatos ideales para implementación inmediata",
        "Evaluar capacidad de inversores con función Q at Night en especificaciones técnicas",
        "Priorizar clusters con alta disponibilidad de terreno (C7 > 7) para reducir riesgos",
        "Desarrollar esquema de remuneración por servicios auxiliares nocturnos con CAMMESA",
        "Implementar sistema DERMS para gestión coordinada de reactiva en 15 clusters"
    ]
    
    # Guardar reporte
    report_path = IAS_V3_DIR / "ias_v3_analysis_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Reporte guardado en: {report_path}")
    
    # Generar resumen markdown
    generate_markdown_summary(report, df_clusters)
    
    return report

def generate_markdown_summary(report, df_clusters):
    """
    Genera resumen ejecutivo en markdown.
    """
    md_content = f"""# Análisis IAS 3.0: Incorporando Q at Night y Disponibilidad de Terreno
## Resumen Ejecutivo

**Fecha**: {datetime.now().strftime('%d de %B de %Y')}  
**Metodología**: IAS 3.0 con 7 criterios  
**Cambio clave**: Incorporación de soporte reactivo nocturno (30.1% peso) y disponibilidad de terreno (20.4% peso)

---

## Impacto de la Nueva Metodología

- **IAS promedio**: {report['summary']['avg_ias_original']:.3f} → {report['summary']['avg_ias_v3']:.3f} (Δ = {report['summary']['avg_delta']:+.3f})
- **Clusters mejorados**: {report['summary']['clusters_improved']} de {report['metadata']['total_clusters']}
- **Clusters empeorados**: {report['summary']['clusters_worsened']} de {report['metadata']['total_clusters']}

## Top 5 Clusters con IAS 3.0

| Ranking | Cluster | Perfil | IAS 3.0 | IAS Original | Cambio Rank | GD (MW) | C6 Score | C7 Score |
|---------|---------|--------|---------|--------------|-------------|---------|----------|----------|
"""
    
    for i, cluster in enumerate(report['top_5_clusters'], 1):
        md_content += f"| #{i} | {cluster['cluster_id']} | {cluster['perfil']} | "
        md_content += f"{cluster['ias_v3']:.3f} | {cluster['ias_original']:.3f} | "
        md_content += f"{cluster['rank_change']:+d} | {cluster['gd_mw']:.1f} | "
        md_content += f"{cluster['c6_score']:.1f} | {cluster['c7_score']:.1f} |\n"
    
    md_content += """
## Hallazgos Clave

### 🌙 Inversión del Paradigma: Zonas Residenciales Ahora Valiosas
Con la incorporación del criterio C6 (Q at Night), los clusters con alta carga residencial 
que antes eran evitados ahora pueden ser valiosos por su capacidad de proporcionar 
soporte de tensión nocturno mediante inversores operando como STATCOM.

### 🏗️ Disponibilidad de Terreno como Factor Limitante
El criterio C7 penaliza clusters en zonas urbanas densas donde conseguir 1 ha/MW 
es extremadamente difícil, favoreciendo zonas periurbanas y rurales con espacio disponible.

### 📊 Análisis por Perfil de Usuario

| Perfil | IAS 3.0 Promedio | Δ vs Original | C6 Promedio | C7 Promedio |
|--------|------------------|---------------|-------------|-------------|
"""
    
    for perfil, stats in report['profile_analysis'].items():
        md_content += f"| {perfil} | {stats['avg_ias_v3']:.3f} | "
        md_content += f"{stats['avg_delta']:+.3f} | "
        md_content += f"{stats['avg_c6']:.1f} | {stats['avg_c7']:.1f} |\n"
    
    md_content += f"""
## Mayores Cambios en Ranking

### 📈 Ganadores (subieron posiciones)
"""
    for g in report['biggest_changes']['gainers']:
        md_content += f"- **Cluster {g['cluster_id']}** ({g['perfil']}): +{g['rank_change']} posiciones - {g['reason']}\n"
    
    md_content += """
### 📉 Perdedores (bajaron posiciones)
"""
    for l in report['biggest_changes']['losers']:
        md_content += f"- **Cluster {l['cluster_id']}** ({l['perfil']}): {l['rank_change']} posiciones - {l['reason']}\n"
    
    md_content += """
## Recomendaciones Estratégicas

1. **Reevaluar Portfolio**: Los clusters residenciales/mixtos merecen una segunda mirada dado su valor para soporte nocturno.

2. **Especificaciones Técnicas**: Asegurar que los inversores seleccionados tengan capacidad "Q at Night" certificada.

3. **Negociación Regulatoria**: Iniciar conversaciones con CAMMESA/ENRE para remunerar servicios auxiliares nocturnos.

4. **Búsqueda de Terrenos**: Priorizar identificación de terrenos en clusters con C7 > 7.0.

5. **Análisis Detallado**: Realizar estudios de flujo de potencia 24h para validar beneficios día/noche.

---

*Análisis generado por sistema GD-EDERSA con metodología IAS 3.0*
"""
    
    # Guardar
    md_path = IAS_V3_DIR / "IAS_V3_RESUMEN_EJECUTIVO.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    logger.info(f"Resumen markdown guardado en: {md_path}")

def main():
    """Función principal"""
    logger.info("=== INICIANDO CÁLCULO IAS 3.0 CON 7 CRITERIOS ===")
    
    # Cargar datos de clusters con IAS original
    cluster_file = CLUSTERING_DIR / "cluster_ranking_ias.csv"
    if not cluster_file.exists():
        logger.error("No se encontró archivo de clusters. Ejecutar scripts previos.")
        return
        
    df_clusters = pd.read_csv(cluster_file)
    logger.info(f"Cargados {len(df_clusters)} clusters")
    
    # Cargar scores de disponibilidad de terreno
    land_file = DATA_DIR / "processed" / "land_availability_scores.parquet"
    if land_file.exists():
        df_land = pd.read_parquet(land_file)
        # Merge con clusters
        df_clusters = pd.merge(
            df_clusters, 
            df_land[['cluster_id', 'C7_land_availability']], 
            on='cluster_id',
            how='left'
        )
        logger.info("Scores de disponibilidad de terreno cargados")
    else:
        logger.warning("No se encontró archivo de land availability. Usando valores default.")
        df_clusters['C7_land_availability'] = 5.0
    
    # Crear calculador y procesar
    calculator = IAS_V3_Calculator()
    df_clusters = calculator.calculate_ias_v3(df_clusters)
    
    # Analizar impacto de criterios
    contributions = calculator.analyze_criterion_impact(df_clusters)
    
    # Estadísticas resumen
    logger.info("\n=== RESUMEN IAS 3.0 ===")
    logger.info(f"IAS 3.0 promedio: {df_clusters['ias_v3'].mean():.3f}")
    logger.info(f"IAS original promedio: {df_clusters['ias_promedio'].mean():.3f}")
    logger.info(f"Delta promedio: {df_clusters['delta_ias'].mean():+.3f}")
    
    # Top 5 nuevos
    logger.info("\nTop 5 clusters por IAS 3.0:")
    top_5 = df_clusters.nlargest(5, 'ias_v3')
    for _, cluster in top_5.iterrows():
        logger.info(f"  Cluster {cluster['cluster_id']}: IAS={cluster['ias_v3']:.3f}, "
                   f"Perfil={cluster['perfil_dominante']}, "
                   f"Cambio ranking={cluster['rank_change']:+d}")
    
    # Crear visualizaciones
    create_ias_comparison_visualization(df_clusters, df_clusters)
    create_criterion_impact_chart(contributions)
    create_priority_map_v3(df_clusters)
    
    # Generar reporte
    report = generate_ias_v3_report(df_clusters, contributions)
    
    # Guardar datos actualizados
    output_path = DATA_DIR / "processed" / "clusters_ias_v3.parquet"
    df_clusters.to_parquet(output_path)
    logger.info(f"\nDatos guardados en: {output_path}")
    
    # También guardar CSV para fácil acceso
    csv_path = IAS_V3_DIR / "cluster_ranking_ias_v3.csv"
    df_clusters.sort_values('ias_v3', ascending=False).to_csv(csv_path, index=False)
    logger.info(f"Ranking CSV guardado en: {csv_path}")
    
    logger.info("\n=== ANÁLISIS IAS 3.0 COMPLETADO ===")

if __name__ == "__main__":
    main()