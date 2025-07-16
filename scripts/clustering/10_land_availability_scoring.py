#!/usr/bin/env python3
"""
FASE 2.5 - Script 10: Land Availability Scoring
===============================================
Evaluación de disponibilidad de terreno para instalación de parques solares.
Implementa el criterio C7 para el IAS 3.0.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import seaborn as sns
import logging

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

class LandAvailabilityAnalyzer:
    """
    Analizador de disponibilidad de terreno para parques solares.
    Considera densidad poblacional, tipo de zona y requerimientos de área.
    """
    
    def __init__(self, hectares_per_mw=1.0):
        """
        Inicializa el analizador.
        
        Args:
            hectares_per_mw: Hectáreas requeridas por MW (default: 1.0 para tracker+bifacial)
        """
        self.hectares_per_mw = hectares_per_mw
        
        # Clasificación de localidades por tipo de zona
        # Basado en conocimiento general de ciudades de Río Negro
        self.zone_classification = self._classify_localities()
        
        # Parámetros de scoring por tipo de zona y tamaño
        self.scoring_matrix = self._create_scoring_matrix()
        
    def _classify_localities(self):
        """
        Clasifica las localidades por tipo de zona urbana.
        Esta es una clasificación aproximada basada en nombres y conocimiento general.
        """
        classification = {
            # Zonas urbanas densas (ciudades principales)
            'urbana_densa': [
                'CIPOLLETTI', 'GENERAL ROCA', 'VILLA REGINA', 
                'CINCO SALTOS', 'ALLEN', 'NEUQUEN'
            ],
            
            # Zonas urbanas medias
            'urbana_media': [
                'CATRIEL', 'INGENIERO HUERGO', 'MAINQUE', 
                'CERVANTES', 'GENERAL ENRIQUE GODOY', 'CHICHINALES',
                'GENERAL FERNANDEZ ORO', 'CAMPO GRANDE'
            ],
            
            # Zonas periurbanas
            'periurbana': [
                'BARDA DEL MEDIO', 'CONTRALMIRANTE CORDERO',
                'SARGENTO VIDAL', 'PASO CORDOVA', 'PENINSULA RUCA CO',
                'VILLA MANZANO', 'COLONIA JULIA Y ECHARREN'
            ],
            
            # Zonas rurales
            'rural': [
                'RURAL', 'CHACRA', 'COLONIA', 'CAMPO', 'COSTA',
                'ESTABLECIMIENTO', 'PUESTO', 'PARAJE'
            ]
        }
        
        return classification
    
    def _create_scoring_matrix(self):
        """
        Crea matriz de scoring basada en tipo de zona y hectáreas requeridas.
        """
        # Score = f(tipo_zona, hectareas_requeridas)
        # Valores entre 0 (imposible) y 1 (totalmente viable)
        
        scoring = {
            'rural': {
                'ranges': [(0, 10, 1.0), (10, 50, 0.95), (50, 100, 0.85), (100, float('inf'), 0.75)],
                'base_score': 0.9
            },
            'periurbana': {
                'ranges': [(0, 2, 0.9), (2, 5, 0.75), (5, 20, 0.5), (20, 50, 0.25), (50, float('inf'), 0.1)],
                'base_score': 0.6
            },
            'urbana_media': {
                'ranges': [(0, 1, 0.8), (1, 3, 0.6), (3, 10, 0.35), (10, 20, 0.15), (20, float('inf'), 0.05)],
                'base_score': 0.4
            },
            'urbana_densa': {
                'ranges': [(0, 0.5, 0.7), (0.5, 2, 0.4), (2, 5, 0.2), (5, 10, 0.1), (10, float('inf'), 0.02)],
                'base_score': 0.2
            }
        }
        
        return scoring
    
    def classify_zone_type(self, localidad):
        """
        Clasifica una localidad en tipo de zona.
        """
        if pd.isna(localidad):
            return 'rural'
            
        localidad_upper = str(localidad).upper().strip()
        
        # Buscar coincidencia exacta primero
        for zone_type, localities in self.zone_classification.items():
            if localidad_upper in localities:
                return zone_type
        
        # Buscar coincidencia parcial para zonas rurales
        rural_keywords = self.zone_classification['rural']
        for keyword in rural_keywords:
            if keyword in localidad_upper:
                return 'rural'
        
        # Default: periurbana si no se encuentra
        return 'periurbana'
    
    def calculate_land_score(self, hectares_required, zone_type):
        """
        Calcula el score de disponibilidad de terreno.
        
        Args:
            hectares_required: Hectáreas necesarias
            zone_type: Tipo de zona (urbana_densa, urbana_media, periurbana, rural)
        
        Returns:
            Score entre 0 y 1
        """
        if zone_type not in self.scoring_matrix:
            zone_type = 'periurbana'  # Default
            
        scoring_params = self.scoring_matrix[zone_type]
        
        # Buscar el rango correspondiente
        for min_ha, max_ha, score in scoring_params['ranges']:
            if min_ha <= hectares_required < max_ha:
                # Interpolar dentro del rango
                if max_ha == float('inf'):
                    return score
                else:
                    # Degradación lineal dentro del rango
                    range_width = max_ha - min_ha
                    position = (hectares_required - min_ha) / range_width
                    
                    # Obtener score del siguiente rango para interpolar
                    next_score = score
                    for i, (min_h, max_h, s) in enumerate(scoring_params['ranges']):
                        if min_h == max_ha:
                            next_score = s
                            break
                    
                    return score - position * (score - next_score)
        
        # Si no se encuentra en ningún rango, retornar el mínimo
        return 0.02
    
    def analyze_clusters(self, df_clusters):
        """
        Analiza la disponibilidad de terreno para cada cluster.
        """
        logger.info("Analizando disponibilidad de terreno para clusters...")
        
        results = []
        
        for _, cluster in df_clusters.iterrows():
            # Calcular hectáreas requeridas
            mw_required = cluster['gd_recomendada_mw']
            hectares_required = mw_required * self.hectares_per_mw
            
            # Determinar tipo de zona predominante
            # Como no tenemos localidad por cluster, usar el perfil como proxy
            if 'perfil_dominante' in cluster:
                perfil = cluster['perfil_dominante']
                
                # Mapeo aproximado perfil -> tipo de zona
                if perfil == 'Residencial':
                    zone_type = 'urbana_densa'
                elif perfil == 'Comercial':
                    zone_type = 'urbana_media'
                elif perfil == 'Industrial':
                    zone_type = 'periurbana'
                elif perfil == 'Rural':
                    zone_type = 'rural'
                else:  # Mixto
                    zone_type = 'periurbana'
            else:
                zone_type = 'periurbana'
            
            # Calcular score
            land_score = self.calculate_land_score(hectares_required, zone_type)
            
            # Factores adicionales de ajuste
            adjustment_factors = self._calculate_adjustment_factors(cluster)
            final_score = land_score * adjustment_factors['total']
            
            result = {
                'cluster_id': cluster['cluster_id'],
                'mw_required': mw_required,
                'hectares_required': hectares_required,
                'zone_type': zone_type,
                'base_land_score': land_score,
                'adjustment_factors': adjustment_factors,
                'C7_land_availability': min(final_score, 1.0),  # Cap at 1.0
                'feasibility_category': self._categorize_feasibility(final_score),
                'alternative_solutions': self._suggest_alternatives(hectares_required, zone_type)
            }
            
            results.append(result)
        
        return pd.DataFrame(results)
    
    def _calculate_adjustment_factors(self, cluster):
        """
        Calcula factores de ajuste adicionales para el score de terreno.
        """
        factors = {}
        
        # Factor de fragmentación: clusters muy grandes pueden necesitar múltiples sitios
        mw = cluster['gd_recomendada_mw']
        if mw > 50:
            factors['fragmentation'] = 0.8  # Penalización por necesitar múltiples sitios
        elif mw > 20:
            factors['fragmentation'] = 0.9
        else:
            factors['fragmentation'] = 1.0
        
        # Factor de concentración: mejor si transformadores están agrupados
        if 'radio_km' in cluster:
            radio = cluster['radio_km']
            if radio < 5:
                factors['concentration'] = 1.0  # Muy concentrado
            elif radio < 10:
                factors['concentration'] = 0.9
            else:
                factors['concentration'] = 0.8  # Muy disperso
        else:
            factors['concentration'] = 0.9
        
        # Factor total
        factors['total'] = factors['fragmentation'] * factors['concentration']
        
        return factors
    
    def _categorize_feasibility(self, score):
        """
        Categoriza la factibilidad basada en el score.
        """
        if score >= 0.8:
            return 'Alta'
        elif score >= 0.5:
            return 'Media'
        elif score >= 0.2:
            return 'Baja'
        else:
            return 'Muy Baja'
    
    def _suggest_alternatives(self, hectares_required, zone_type):
        """
        Sugiere soluciones alternativas según las restricciones.
        """
        alternatives = []
        
        if zone_type in ['urbana_densa', 'urbana_media'] and hectares_required > 5:
            alternatives.append('Considerar múltiples sitios menores')
            alternatives.append('Solar distribuido en techos industriales/comerciales')
            alternatives.append('Buscar terrenos en zonas periurbanas cercanas')
        
        if hectares_required > 20:
            alternatives.append('Dividir en 2-3 parques menores')
            alternatives.append('Asociación público-privada para terrenos')
        
        if zone_type == 'rural' and hectares_required < 10:
            alternatives.append('Ideal para implementación directa')
            alternatives.append('Posible arrendamiento de terrenos agrícolas')
        
        return alternatives

def analyze_transformer_zones(df_transformers):
    """
    Analiza las zonas de los transformadores individuales.
    """
    logger.info("Analizando zonas de transformadores...")
    
    analyzer = LandAvailabilityAnalyzer()
    
    # Clasificar cada transformador por zona
    df_transformers['zone_type'] = df_transformers['Localidad'].apply(
        analyzer.classify_zone_type
    )
    
    # Estadísticas por zona
    zone_stats = df_transformers.groupby('zone_type').agg({
        'CODIGO': 'count',
        'Usu. Total': 'sum',
        'Potencia Nom.(kVA)': 'sum'
    }).rename(columns={
        'CODIGO': 'n_transformadores',
        'Usu. Total': 'usuarios_totales',
        'Potencia Nom.(kVA)': 'potencia_total_kva'
    })
    
    zone_stats['potencia_total_mva'] = zone_stats['potencia_total_kva'] / 1000
    
    return df_transformers, zone_stats

def create_land_feasibility_map(df_clusters, df_land_analysis):
    """
    Crea mapa de factibilidad de terreno.
    """
    logger.info("Creando mapa de factibilidad de terreno...")
    
    # Merge datos
    df_map = pd.merge(df_clusters, df_land_analysis, on='cluster_id')
    
    # Centro del mapa
    center_lat = df_map['centroid_lat'].mean()
    center_lon = df_map['centroid_lon'].mean()
    
    # Crear mapa
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Colores por categoría de factibilidad
    colors = {
        'Alta': 'green',
        'Media': 'yellow',
        'Baja': 'orange',
        'Muy Baja': 'red'
    }
    
    # Agregar clusters
    for _, row in df_map.iterrows():
        color = colors[row['feasibility_category']]
        
        # Círculo proporcional a hectáreas requeridas
        folium.Circle(
            location=[row['centroid_lat'], row['centroid_lon']],
            radius=row['hectares_required'] * 100,  # Escalar para visualización
            popup=f"""
            <b>Cluster {row['cluster_id']}</b><br>
            <b>Capacidad:</b> {row['mw_required']:.1f} MW<br>
            <b>Hectáreas:</b> {row['hectares_required']:.1f} ha<br>
            <b>Zona:</b> {row['zone_type']}<br>
            <b>Score C7:</b> {row['C7_land_availability']:.3f}<br>
            <b>Factibilidad:</b> {row['feasibility_category']}<br>
            <b>Alternativas:</b> {'; '.join(row['alternative_solutions'][:2])}
            """,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.5
        ).add_to(m)
    
    # Leyenda
    legend_html = '''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: 120px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px">
    <p style="margin: 10px;"><b>Factibilidad de Terreno</b></p>
    <p style="margin: 10px;"><span style="color:green;">●</span> Alta (>0.8)</p>
    <p style="margin: 10px;"><span style="color:yellow;">●</span> Media (0.5-0.8)</p>
    <p style="margin: 10px;"><span style="color:orange;">●</span> Baja (0.2-0.5)</p>
    <p style="margin: 10px;"><span style="color:red;">●</span> Muy Baja (<0.2)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Guardar mapa
    map_path = CLUSTERING_DIR / "land_feasibility_map.html"
    m.save(str(map_path))
    logger.info(f"Mapa guardado en: {map_path}")
    
    return m

def create_visualizations(df_land_analysis, df_clusters):
    """
    Crea visualizaciones del análisis de terreno.
    """
    logger.info("Creando visualizaciones de análisis de terreno...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Análisis de Disponibilidad de Terreno para GD Solar', fontsize=16)
    
    # 1. Distribución de scores C7
    ax = axes[0, 0]
    df_land_analysis['C7_land_availability'].hist(bins=20, ax=ax, color='green', alpha=0.7)
    ax.axvline(x=0.5, color='red', linestyle='--', label='Umbral factibilidad')
    ax.set_xlabel('Score C7 (Disponibilidad de Terreno)')
    ax.set_ylabel('Número de Clusters')
    ax.set_title('Distribución de Scores de Disponibilidad')
    ax.legend()
    
    # 2. Hectáreas vs Score
    ax = axes[0, 1]
    scatter = ax.scatter(df_land_analysis['hectares_required'], 
                        df_land_analysis['C7_land_availability'],
                        c=df_land_analysis['zone_type'].map({
                            'rural': 0, 'periurbana': 1, 
                            'urbana_media': 2, 'urbana_densa': 3
                        }),
                        cmap='RdYlGn_r',
                        s=100,
                        alpha=0.7)
    ax.set_xlabel('Hectáreas Requeridas')
    ax.set_ylabel('Score C7')
    ax.set_title('Relación Área Requerida vs Disponibilidad')
    ax.set_xscale('log')
    plt.colorbar(scatter, ax=ax, label='Tipo de Zona')
    
    # 3. Factibilidad por categoría
    ax = axes[1, 0]
    feasibility_counts = df_land_analysis['feasibility_category'].value_counts()
    colors_cat = {'Alta': 'green', 'Media': 'yellow', 'Baja': 'orange', 'Muy Baja': 'red'}
    bars = ax.bar(feasibility_counts.index, feasibility_counts.values)
    for bar, cat in zip(bars, feasibility_counts.index):
        bar.set_color(colors_cat.get(cat, 'gray'))
    ax.set_xlabel('Categoría de Factibilidad')
    ax.set_ylabel('Número de Clusters')
    ax.set_title('Clusters por Categoría de Factibilidad')
    
    # 4. Top 10 clusters por score combinado (IAS actual × C7)
    ax = axes[1, 1]
    # Merge con datos de IAS
    df_combined = pd.merge(
        df_land_analysis[['cluster_id', 'C7_land_availability', 'hectares_required']], 
        df_clusters[['cluster_id', 'ias_promedio', 'n_usuarios']], 
        on='cluster_id'
    )
    df_combined['combined_score'] = df_combined['ias_promedio'] * df_combined['C7_land_availability']
    df_combined = df_combined.sort_values('combined_score', ascending=False).head(10)
    
    y_pos = np.arange(len(df_combined))
    ax.barh(y_pos, df_combined['combined_score'])
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"Cluster {id}" for id in df_combined['cluster_id']])
    ax.set_xlabel('Score Combinado (IAS × C7)')
    ax.set_title('Top 10 Clusters: Score Técnico × Disponibilidad Terreno')
    
    # Agregar etiquetas con hectáreas
    for i, (idx, row) in enumerate(df_combined.iterrows()):
        ax.text(row['combined_score'] + 0.01, i, 
                f"{row['hectares_required']:.1f} ha", 
                va='center', fontsize=9)
    
    plt.tight_layout()
    
    # Guardar
    fig_path = CLUSTERING_DIR / "land_availability_analysis.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Visualizaciones guardadas en: {fig_path}")

def generate_land_report(df_land_analysis, zone_stats):
    """
    Genera reporte de análisis de disponibilidad de terreno.
    """
    logger.info("Generando reporte de disponibilidad de terreno...")
    
    report = {
        'metadata': {
            'analysis_date': pd.Timestamp.now().isoformat(),
            'hectares_per_mw': 1.0,
            'total_clusters_analyzed': len(df_land_analysis)
        },
        'summary': {
            'total_hectares_required': round(df_land_analysis['hectares_required'].sum(), 1),
            'average_c7_score': round(df_land_analysis['C7_land_availability'].mean(), 3),
            'clusters_high_feasibility': len(df_land_analysis[df_land_analysis['feasibility_category'] == 'Alta']),
            'clusters_low_feasibility': len(df_land_analysis[df_land_analysis['feasibility_category'].isin(['Baja', 'Muy Baja'])])
        },
        'by_zone_type': {},
        'critical_clusters': [],
        'recommendations': []
    }
    
    # Análisis por tipo de zona
    zone_analysis = df_land_analysis.groupby('zone_type').agg({
        'hectares_required': ['sum', 'mean'],
        'C7_land_availability': 'mean',
        'cluster_id': 'count'
    }).round(2)
    
    for zone in zone_analysis.index:
        report['by_zone_type'][zone] = {
            'n_clusters': int(zone_analysis.loc[zone, ('cluster_id', 'count')]),
            'total_hectares': float(zone_analysis.loc[zone, ('hectares_required', 'sum')]),
            'avg_hectares': float(zone_analysis.loc[zone, ('hectares_required', 'mean')]),
            'avg_c7_score': float(zone_analysis.loc[zone, ('C7_land_availability', 'mean')])
        }
    
    # Clusters críticos (baja factibilidad pero alta prioridad técnica)
    critical = df_land_analysis[
        (df_land_analysis['feasibility_category'].isin(['Baja', 'Muy Baja'])) &
        (df_land_analysis['mw_required'] > 10)
    ].sort_values('mw_required', ascending=False)
    
    for _, cluster in critical.head(5).iterrows():
        report['critical_clusters'].append({
            'cluster_id': int(cluster['cluster_id']),
            'mw_required': round(cluster['mw_required'], 2),
            'hectares_required': round(cluster['hectares_required'], 1),
            'zone_type': cluster['zone_type'],
            'c7_score': round(cluster['C7_land_availability'], 3),
            'alternatives': cluster['alternative_solutions']
        })
    
    # Recomendaciones generales
    report['recommendations'] = [
        "Priorizar clusters en zonas rurales y periurbanas para implementación rápida",
        "Para clusters urbanos grandes (>10 MW), evaluar división en múltiples sitios",
        "Considerar solar distribuido en techos para zonas urbanas densas",
        "Desarrollar asociaciones con propietarios rurales para arrendamiento de terrenos",
        "Evaluar brownfields y terrenos industriales abandonados en zonas urbanas"
    ]
    
    # Guardar reporte
    report_path = CLUSTERING_DIR / "land_availability_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Reporte guardado en: {report_path}")
    
    # También guardar análisis detallado
    csv_path = CLUSTERING_DIR / "land_availability_detailed.csv"
    df_land_analysis.to_csv(csv_path, index=False)
    logger.info(f"Análisis detallado guardado en: {csv_path}")
    
    return report

def main():
    """Función principal"""
    logger.info("=== INICIANDO ANÁLISIS DE DISPONIBILIDAD DE TERRENO ===")
    
    # Cargar datos de clusters
    cluster_file = CLUSTERING_DIR / "cluster_ranking_ias.csv"
    if not cluster_file.exists():
        logger.error("No se encontró archivo de clusters. Ejecutar scripts previos primero.")
        return
    
    df_clusters = pd.read_csv(cluster_file)
    logger.info(f"Cargados {len(df_clusters)} clusters")
    
    # Cargar datos de transformadores para análisis de zonas
    transformer_file = DATA_DIR / "processed" / "transformers_ias_clustering.parquet"
    if transformer_file.exists():
        df_transformers = pd.read_parquet(transformer_file)
        df_transformers, zone_stats = analyze_transformer_zones(df_transformers)
        logger.info("\nEstadísticas por tipo de zona:")
        print(zone_stats)
    else:
        zone_stats = None
    
    # Crear analizador y procesar clusters
    analyzer = LandAvailabilityAnalyzer(hectares_per_mw=1.0)
    df_land_analysis = analyzer.analyze_clusters(df_clusters)
    
    # Estadísticas resumen
    logger.info("\n=== RESUMEN DE DISPONIBILIDAD DE TERRENO ===")
    logger.info(f"Total hectáreas requeridas: {df_land_analysis['hectares_required'].sum():.1f} ha")
    logger.info(f"Score C7 promedio: {df_land_analysis['C7_land_availability'].mean():.3f}")
    
    # Distribución por factibilidad
    feasibility_dist = df_land_analysis['feasibility_category'].value_counts()
    logger.info("\nDistribución de factibilidad:")
    for cat, count in feasibility_dist.items():
        logger.info(f"  {cat}: {count} clusters")
    
    # Top 5 clusters con mejor disponibilidad
    logger.info("\nTop 5 clusters con mejor disponibilidad de terreno:")
    top_5 = df_land_analysis.nlargest(5, 'C7_land_availability')
    for _, cluster in top_5.iterrows():
        logger.info(f"  Cluster {cluster['cluster_id']}: {cluster['hectares_required']:.1f} ha, "
                   f"Score C7: {cluster['C7_land_availability']:.3f}, "
                   f"Zona: {cluster['zone_type']}")
    
    # Clusters problemáticos
    logger.info("\nClusters con restricciones severas de terreno:")
    problematic = df_land_analysis[df_land_analysis['C7_land_availability'] < 0.3]
    for _, cluster in problematic.iterrows():
        logger.info(f"  Cluster {cluster['cluster_id']}: {cluster['hectares_required']:.1f} ha, "
                   f"Score C7: {cluster['C7_land_availability']:.3f}, "
                   f"Zona: {cluster['zone_type']}")
    
    # Crear visualizaciones
    create_visualizations(df_land_analysis, df_clusters)
    create_land_feasibility_map(df_clusters, df_land_analysis)
    
    # Generar reporte
    report = generate_land_report(df_land_analysis, zone_stats)
    
    # Guardar resultados para siguiente script
    output_path = DATA_DIR / "processed" / "land_availability_scores.parquet"
    df_land_analysis.to_parquet(output_path)
    logger.info(f"\nResultados guardados en: {output_path}")
    
    logger.info("\n=== ANÁLISIS DE DISPONIBILIDAD DE TERRENO COMPLETADO ===")

if __name__ == "__main__":
    main()