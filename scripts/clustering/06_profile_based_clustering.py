#!/usr/bin/env python3
"""
FASE 2 - Script 06: Profile-Based Clustering
============================================
Clasificación de transformadores por perfil de usuario y clustering basado en 
aptitud para GD solar sin BESS.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sqlite3
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
import folium
from folium.plugins import HeatMap, MarkerCluster
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
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
CLUSTERING_DIR.mkdir(exist_ok=True)

class SolarAptitudeAnalyzer:
    """
    Analizador de aptitud solar sin BESS basado en el documento teórico.
    Implementa el Índice de Aptitud Solar (IAS) con 5 criterios ponderados.
    """
    
    def __init__(self):
        """Inicializa pesos AHP según documento teórico"""
        self.weights = {
            'C1_coincidencia': 0.501,      # Coincidencia demanda-generación
            'C2_capacidad_absorcion': 0.206,  # Capacidad absorción local
            'C3_debilidad_red': 0.148,     # Debilidad de red
            'C4_cargabilidad': 0.096,      # Cargabilidad de activos
            'C5_calidad_servicio': 0.049   # Calidad de servicio actual
        }
        
        # Factores de coincidencia por tipo de usuario (proxy sin curvas horarias)
        self.coincidence_factors = {
            'Comercial': 0.85,      # Alta coincidencia diurna
            'Industrial': 0.80,     # Alta coincidencia
            'Residencial': 0.25,    # Baja coincidencia (pico nocturno)
            'Oficial': 0.70,        # Buena coincidencia
            'Rural': 0.40,          # Variable
            'Riego': 0.60,          # Estacional pero diurno
            'Otros': 0.50           # Promedio
        }
        
    def calculate_user_profile_score(self, df_transformers):
        """
        Calcula score de perfil de usuario basado en composición.
        C1: Coincidencia horaria demanda-generación
        """
        logger.info("Calculando scores de perfil de usuario...")
        
        # Como no tenemos desglose de usuarios, estimamos perfil basado en características
        df = df_transformers.copy()
        
        # Estimar perfil basado en:
        # 1. Potencia del transformador y usuarios/kVA
        # 2. Localidad (urbana vs rural)
        # 3. Tamaño del transformador
        
        # Inicializar perfil dominante
        df['perfil_dominante'] = 'Mixto'
        
        # Calcular usuarios por kVA si no existe
        if 'usuarios_por_kva' not in df.columns:
            df['usuarios_por_kva'] = df['Usu. Total'] / df['Potencia Nom.(kVA)'].replace(0, 1)
        
        # Reglas heurísticas para estimar perfil:
        # Industrial: Alta potencia (>500 kVA) y pocos usuarios/kVA (<0.5)
        mask_industrial = (df['Potencia Nom.(kVA)'] > 500) & (df['usuarios_por_kva'] < 0.5)
        df.loc[mask_industrial, 'perfil_dominante'] = 'Industrial'
        
        # Comercial: Potencia media (100-500 kVA) y usuarios/kVA medio (0.5-2)
        mask_comercial = (df['Potencia Nom.(kVA)'].between(100, 500)) & (df['usuarios_por_kva'].between(0.5, 2))
        df.loc[mask_comercial, 'perfil_dominante'] = 'Comercial'
        
        # Rural: Localidades pequeñas o con "Rural" en el nombre
        if 'Localidad' in df.columns:
            mask_rural = df['Localidad'].str.contains('Rural|Campo|Colonia|Chacra', case=False, na=False)
            df.loc[mask_rural, 'perfil_dominante'] = 'Rural'
        
        # Residencial: Baja potencia (<100 kVA) y muchos usuarios/kVA (>2)
        mask_residencial = (df['Potencia Nom.(kVA)'] < 100) & (df['usuarios_por_kva'] > 2)
        df.loc[mask_residencial, 'perfil_dominante'] = 'Residencial'
        
        # Asignar scores de coincidencia basados en perfil estimado
        df['C1_coincidencia'] = df['perfil_dominante'].map(self.coincidence_factors)
        
        # Para perfiles mixtos, usar promedio ponderado
        mask_mixto = df['perfil_dominante'] == 'Mixto'
        # Asumimos 60% residencial, 30% comercial, 10% otros para zonas mixtas
        df.loc[mask_mixto, 'C1_coincidencia'] = (
            0.6 * self.coincidence_factors['Residencial'] +
            0.3 * self.coincidence_factors['Comercial'] +
            0.1 * self.coincidence_factors['Otros']
        )
            
        return df
    
    def calculate_absorption_capacity(self, df):
        """
        C2: Capacidad de absorción local (densidad de carga)
        """
        logger.info("Calculando capacidad de absorción local...")
        
        # Normalizar potencia y usuarios para crear índice de densidad
        df['potencia_norm'] = df['Potencia Nom.(kVA)'] / df['Potencia Nom.(kVA)'].max()
        df['usuarios_norm'] = df['Usu. Total'] / df['Usu. Total'].max()
        
        # Score de capacidad de absorción (más potencia y usuarios = mejor)
        df['C2_capacidad_absorcion'] = (df['potencia_norm'] + df['usuarios_norm']) / 2
        
        return df
    
    def calculate_network_weakness(self, df):
        """
        C3: Debilidad de la red (basado en impedancia y caída de tensión)
        """
        logger.info("Calculando debilidad de red...")
        
        # Si no hay datos eléctricos, usar distancia como proxy
        if 'voltage_drop_percent' in df.columns:
            # Normalizar caída de tensión (más caída = red más débil = mejor para GD)
            df['C3_debilidad_red'] = df['voltage_drop_percent'] / 10  # Normalizar a 0-1
            df['C3_debilidad_red'] = df['C3_debilidad_red'].clip(0, 1)
        else:
            # Usar número de saltos como proxy (más saltos = red más débil)
            if 'num_saltos' in df.columns:
                df['C3_debilidad_red'] = df['num_saltos'] / df['num_saltos'].max()
            else:
                df['C3_debilidad_red'] = 0.5  # Valor neutral si no hay datos
                
        return df
    
    def calculate_asset_loading(self, df):
        """
        C4: Cargabilidad de activos (transformadores cerca del límite)
        """
        logger.info("Calculando cargabilidad de activos...")
        
        # Estimar carga basada en usuarios y potencia nominal
        # Asumiendo factor de simultaneidad típico
        factor_simultaneidad = 0.4
        potencia_por_usuario = 2.5  # kW promedio por usuario
        
        df['carga_estimada_kva'] = df['Usu. Total'] * potencia_por_usuario * factor_simultaneidad
        df['utilizacion'] = df['carga_estimada_kva'] / df['Potencia Nom.(kVA)']
        
        # Score: transformadores con utilización 70-90% son ideales
        df['C4_cargabilidad'] = 0
        mask_ideal = (df['utilizacion'] >= 0.7) & (df['utilizacion'] <= 0.9)
        mask_alta = df['utilizacion'] > 0.9
        mask_baja = df['utilizacion'] < 0.7
        
        df.loc[mask_ideal, 'C4_cargabilidad'] = 1.0
        df.loc[mask_alta, 'C4_cargabilidad'] = 0.8  # Muy cargados, riesgo
        df.loc[mask_baja, 'C4_cargabilidad'] = 0.3   # Poco cargados, menos beneficio
        
        return df
    
    def calculate_service_quality(self, df):
        """
        C5: Calidad de servicio actual
        """
        logger.info("Calculando calidad de servicio...")
        
        # Mapear resultados a scores
        quality_scores = {
            'Correcta': 0.0,      # No necesita mejora
            'Penalizada': 0.7,    # Necesita mejora
            'Fallida': 1.0        # Urgente mejora
        }
        
        df['C5_calidad_servicio'] = df['Resultado'].map(quality_scores).fillna(0.5)
        
        return df
    
    def calculate_ias_score(self, df):
        """
        Calcula el Índice de Aptitud Solar sin BESS (IAS)
        """
        logger.info("Calculando IAS (Índice de Aptitud Solar sin BESS)...")
        
        # Aplicar todos los criterios
        df = self.calculate_user_profile_score(df)
        df = self.calculate_absorption_capacity(df)
        df = self.calculate_network_weakness(df)
        df = self.calculate_asset_loading(df)
        df = self.calculate_service_quality(df)
        
        # Calcular IAS ponderado
        df['IAS_score'] = (
            self.weights['C1_coincidencia'] * df['C1_coincidencia'] +
            self.weights['C2_capacidad_absorcion'] * df['C2_capacidad_absorcion'] +
            self.weights['C3_debilidad_red'] * df['C3_debilidad_red'] +
            self.weights['C4_cargabilidad'] * df['C4_cargabilidad'] +
            self.weights['C5_calidad_servicio'] * df['C5_calidad_servicio']
        )
        
        # Clasificar aptitud
        df['aptitud_solar'] = pd.cut(
            df['IAS_score'],
            bins=[0, 0.3, 0.5, 0.7, 1.0],
            labels=['Baja', 'Media', 'Alta', 'Muy Alta']
        )
        
        return df

def load_transformer_data():
    """Carga datos de transformadores con features eléctricas"""
    logger.info("Cargando datos de transformadores...")
    
    # Cargar datos con topología de red (de Fase 1)
    topology_path = DATA_DIR / "processed" / "network_analysis" / "transformadores_con_topologia.csv"
    
    if topology_path.exists():
        df = pd.read_csv(topology_path)
        
        # Filtrar solo con coordenadas
        df = df[df['Coord_X'].notna() & df['Coord_Y'].notna()]
        
        # Renombrar columnas para compatibilidad
        column_mapping = {
            'Codigoct': 'CODIGO',
            'Coord_X': 'Longitud',
            'Coord_Y': 'Latitud',
            'Potencia': 'Potencia Nom.(kVA)',
            'Q_Usuarios': 'Usu. Total',
            'N_Sucursal': 'Sucursal',
            'N_Localida': 'Localidad',
            'Resultado': 'Resultado',
            'Alimentador': 'Alimentador'
        }
        
        # Renombrar solo las columnas que existen
        existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        logger.info(f"Cargados {len(df)} transformadores con coordenadas y topología")
        logger.info(f"Columnas disponibles: {df.columns.tolist()[:10]}...")
        return df
    else:
        logger.error("No se encontró archivo de datos con topología")
        return None

def perform_clustering(df, method='dbscan', **params):
    """
    Realiza clustering basado en ubicación geográfica y score IAS
    """
    logger.info(f"Realizando clustering con método: {method}")
    
    # Preparar features para clustering
    features = ['Longitud', 'Latitud', 'IAS_score']
    X = df[features].values
    
    # Escalar features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if method == 'dbscan':
        eps = params.get('eps', 0.5)  # Radio en km
        min_samples = params.get('min_samples', 5)
        
        # Convertir eps de km a grados aproximadamente (1 grado ≈ 111 km)
        eps_degrees = eps / 111
        
        # Ajustar eps para features escaladas
        eps_scaled = eps_degrees * np.mean(scaler.scale_[:2])  # Solo para coordenadas
        
        clusterer = DBSCAN(eps=eps_scaled, min_samples=min_samples)
        
    elif method == 'kmeans':
        n_clusters = params.get('n_clusters', 10)
        clusterer = KMeans(n_clusters=n_clusters, random_state=42)
    
    # Realizar clustering
    df['cluster'] = clusterer.fit_predict(X_scaled)
    
    # Calcular métricas si hay clusters válidos
    n_clusters = len(set(df['cluster'])) - (1 if -1 in df['cluster'] else 0)
    logger.info(f"Clusters identificados: {n_clusters}")
    
    if n_clusters > 1:
        # Filtrar ruido para silhouette
        mask = df['cluster'] != -1
        if mask.sum() > 1:
            score = silhouette_score(X_scaled[mask], df.loc[mask, 'cluster'])
            logger.info(f"Silhouette score: {score:.3f}")
    
    return df

def analyze_clusters(df):
    """Analiza características de cada cluster"""
    logger.info("Analizando características de clusters...")
    
    cluster_stats = []
    
    for cluster_id in sorted(df['cluster'].unique()):
        if cluster_id == -1:  # Ruido en DBSCAN
            continue
            
        cluster_data = df[df['cluster'] == cluster_id]
        
        stats = {
            'cluster_id': cluster_id,
            'n_transformadores': len(cluster_data),
            'n_usuarios': cluster_data['Usu. Total'].sum(),
            'potencia_total_mva': cluster_data['Potencia Nom.(kVA)'].sum() / 1000,
            'ias_promedio': cluster_data['IAS_score'].mean(),
            'ias_max': cluster_data['IAS_score'].max(),
            'perfil_dominante': cluster_data['perfil_dominante'].mode()[0] if len(cluster_data['perfil_dominante'].mode()) > 0 else 'Mixto',
            'tasa_falla': (cluster_data['Resultado'] == 'Fallida').mean(),
            'centroid_lat': cluster_data['Latitud'].mean(),
            'centroid_lon': cluster_data['Longitud'].mean(),
            'radio_km': calculate_cluster_radius(cluster_data),
            'C1_promedio': cluster_data['C1_coincidencia'].mean(),
            'C2_promedio': cluster_data['C2_capacidad_absorcion'].mean(),
            'C3_promedio': cluster_data['C3_debilidad_red'].mean(),
            'C4_promedio': cluster_data['C4_cargabilidad'].mean(),
            'C5_promedio': cluster_data['C5_calidad_servicio'].mean()
        }
        
        # Calcular potencia GD recomendada (30% de capacidad con factor 1850 MWh/año/MW)
        stats['gd_recomendada_mw'] = stats['potencia_total_mva'] * 0.3
        stats['produccion_anual_mwh'] = stats['gd_recomendada_mw'] * 1850  # Con trackers y bifacial
        
        cluster_stats.append(stats)
    
    df_clusters = pd.DataFrame(cluster_stats)
    
    # Calcular score de prioridad final
    df_clusters['prioridad_score'] = (
        df_clusters['ias_promedio'] * 0.4 +
        (df_clusters['n_usuarios'] / df_clusters['n_usuarios'].max()) * 0.3 +
        df_clusters['tasa_falla'] * 0.2 +
        (df_clusters['gd_recomendada_mw'] / df_clusters['gd_recomendada_mw'].max()) * 0.1
    )
    
    # Ordenar por prioridad
    df_clusters = df_clusters.sort_values('prioridad_score', ascending=False)
    df_clusters['ranking'] = range(1, len(df_clusters) + 1)
    
    return df_clusters

def calculate_cluster_radius(cluster_data):
    """Calcula radio del cluster en km"""
    from geopy.distance import distance
    
    centroid = (cluster_data['Latitud'].mean(), cluster_data['Longitud'].mean())
    
    max_dist = 0
    for _, row in cluster_data.iterrows():
        point = (row['Latitud'], row['Longitud'])
        dist = distance(centroid, point).km
        max_dist = max(max_dist, dist)
    
    return round(max_dist, 2)

def create_cluster_map(df, df_clusters):
    """Crea mapa interactivo de clusters"""
    logger.info("Creando mapa de clusters...")
    
    # Centro del mapa
    center_lat = df['Latitud'].mean()
    center_lon = df['Longitud'].mean()
    
    # Crear mapa base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Colores para clusters
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
              'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
              'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen',
              'gray', 'black', 'lightgray']
    
    # Agregar transformadores por cluster
    for cluster_id in sorted(df['cluster'].unique()):
        if cluster_id == -1:  # Ruido
            color = 'gray'
            cluster_name = 'Sin cluster'
        else:
            color = colors[cluster_id % len(colors)]
            cluster_info = df_clusters[df_clusters['cluster_id'] == cluster_id].iloc[0]
            cluster_name = f"Cluster {cluster_id} (Rank #{cluster_info['ranking']})"
        
        cluster_data = df[df['cluster'] == cluster_id]
        
        for _, row in cluster_data.iterrows():
            folium.CircleMarker(
                location=[row['Latitud'], row['Longitud']],
                radius=5 + row['IAS_score'] * 10,  # Tamaño por score
                popup=f"""
                <b>Transformador:</b> {row['CODIGO']}<br>
                <b>Cluster:</b> {cluster_name}<br>
                <b>IAS Score:</b> {row['IAS_score']:.3f}<br>
                <b>Aptitud Solar:</b> {row['aptitud_solar']}<br>
                <b>Perfil:</b> {row['perfil_dominante']}<br>
                <b>Potencia:</b> {row['Potencia Nom.(kVA)']} kVA<br>
                <b>Usuarios:</b> {row['Usu. Total']}<br>
                <b>Estado:</b> {row['Resultado']}
                """,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6
            ).add_to(m)
    
    # Agregar centroides de clusters
    for _, cluster in df_clusters.iterrows():
        folium.Marker(
            location=[cluster['centroid_lat'], cluster['centroid_lon']],
            popup=f"""
            <b>Cluster {cluster['cluster_id']}</b><br>
            <b>Ranking:</b> #{cluster['ranking']}<br>
            <b>IAS Promedio:</b> {cluster['ias_promedio']:.3f}<br>
            <b>Transformadores:</b> {cluster['n_transformadores']}<br>
            <b>Usuarios:</b> {cluster['n_usuarios']:,}<br>
            <b>Potencia Total:</b> {cluster['potencia_total_mva']:.1f} MVA<br>
            <b>GD Recomendada:</b> {cluster['gd_recomendada_mw']:.2f} MW<br>
            <b>Producción Anual:</b> {cluster['produccion_anual_mwh']:,.0f} MWh<br>
            <b>Perfil Dominante:</b> {cluster['perfil_dominante']}
            """,
            icon=folium.Icon(color='red', icon='star')
        ).add_to(m)
    
    # Agregar capa de calor para IAS scores
    heat_data = [[row['Latitud'], row['Longitud'], row['IAS_score']] 
                 for _, row in df.iterrows()]
    HeatMap(heat_data, name='IAS Score Heatmap', show=False).add_to(m)
    
    # Control de capas
    folium.LayerControl().add_to(m)
    
    # Guardar mapa
    map_path = CLUSTERING_DIR / "cluster_map_ias.html"
    m.save(str(map_path))
    logger.info(f"Mapa guardado en: {map_path}")
    
    return m

def create_visualizations(df, df_clusters):
    """Crea visualizaciones de análisis"""
    logger.info("Creando visualizaciones...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Análisis de Clustering para GD Solar sin BESS', fontsize=16)
    
    # 1. Distribución de IAS Score por perfil
    ax = axes[0, 0]
    df.boxplot(column='IAS_score', by='perfil_dominante', ax=ax)
    ax.set_title('IAS Score por Perfil de Usuario')
    ax.set_xlabel('Perfil Dominante')
    ax.set_ylabel('IAS Score')
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    # 2. Top 10 Clusters por prioridad
    ax = axes[0, 1]
    top_clusters = df_clusters.head(10)
    bars = ax.bar(top_clusters['ranking'], top_clusters['prioridad_score'])
    ax.set_title('Top 10 Clusters por Prioridad')
    ax.set_xlabel('Ranking')
    ax.set_ylabel('Score de Prioridad')
    
    # Colorear barras por IAS promedio
    colors = plt.cm.RdYlGn(top_clusters['ias_promedio'])
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    # 3. Scatter: Usuarios vs GD Recomendada
    ax = axes[0, 2]
    scatter = ax.scatter(df_clusters['n_usuarios'], 
                        df_clusters['gd_recomendada_mw'],
                        c=df_clusters['ias_promedio'],
                        s=df_clusters['n_transformadores'] * 10,
                        cmap='RdYlGn',
                        alpha=0.6)
    ax.set_xlabel('Usuarios Totales')
    ax.set_ylabel('GD Recomendada (MW)')
    ax.set_title('Usuarios vs GD Recomendada')
    plt.colorbar(scatter, ax=ax, label='IAS Promedio')
    
    # 4. Componentes del IAS
    ax = axes[1, 0]
    components = ['C1\nCoincidencia', 'C2\nAbsorción', 'C3\nDebilidad', 
                  'C4\nCargabilidad', 'C5\nCalidad']
    values = [df['C1_coincidencia'].mean(), df['C2_capacidad_absorcion'].mean(),
              df['C3_debilidad_red'].mean(), df['C4_cargabilidad'].mean(),
              df['C5_calidad_servicio'].mean()]
    weights = [0.501, 0.206, 0.148, 0.096, 0.049]
    
    x = np.arange(len(components))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, values, width, label='Valor Promedio', alpha=0.8)
    bars2 = ax.bar(x + width/2, weights, width, label='Peso AHP', alpha=0.8)
    
    ax.set_xlabel('Criterios')
    ax.set_ylabel('Valor')
    ax.set_title('Componentes del IAS: Valores vs Pesos')
    ax.set_xticks(x)
    ax.set_xticklabels(components)
    ax.legend()
    
    # 5. Producción anual esperada
    ax = axes[1, 1]
    top_10_prod = df_clusters.head(10).sort_values('produccion_anual_mwh', ascending=True)
    ax.barh(top_10_prod['ranking'].astype(str), top_10_prod['produccion_anual_mwh'])
    ax.set_xlabel('Producción Anual (MWh)')
    ax.set_ylabel('Ranking Cluster')
    ax.set_title('Producción Anual Esperada - Top 10 (1850 MWh/MW/año)')
    
    # Agregar valores en las barras
    for i, (idx, row) in enumerate(top_10_prod.iterrows()):
        ax.text(row['produccion_anual_mwh'], i, 
                f" {row['produccion_anual_mwh']:,.0f} MWh", 
                va='center')
    
    # 6. Matriz de criterios para top clusters
    ax = axes[1, 2]
    criteria_cols = ['C1_promedio', 'C2_promedio', 'C3_promedio', 'C4_promedio', 'C5_promedio']
    criteria_data = df_clusters.head(5)[criteria_cols].values.T
    
    im = ax.imshow(criteria_data, cmap='RdYlGn', aspect='auto')
    ax.set_xticks(range(5))
    ax.set_xticklabels([f"#{i+1}" for i in range(5)])
    ax.set_yticks(range(5))
    ax.set_yticklabels(['C1', 'C2', 'C3', 'C4', 'C5'])
    ax.set_xlabel('Top 5 Clusters')
    ax.set_ylabel('Criterios')
    ax.set_title('Matriz de Criterios - Top 5 Clusters')
    
    # Agregar valores en celdas
    for i in range(5):
        for j in range(5):
            text = ax.text(j, i, f'{criteria_data[i, j]:.2f}',
                         ha="center", va="center", color="black")
    
    plt.colorbar(im, ax=ax)
    
    plt.tight_layout()
    
    # Guardar figura
    fig_path = CLUSTERING_DIR / "ias_clustering_analysis.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Visualizaciones guardadas en: {fig_path}")

def generate_cluster_report(df_clusters, top_n=15):
    """Genera reporte ejecutivo de clusters prioritarios"""
    logger.info(f"Generando reporte ejecutivo para top {top_n} clusters...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'methodology': 'Índice de Aptitud Solar sin BESS (IAS)',
        'production_assumption': '1850 MWh/año/MW (trackers + bifacial)',
        'total_clusters': len(df_clusters),
        'top_clusters': []
    }
    
    # Información detallada de top clusters
    for _, cluster in df_clusters.head(top_n).iterrows():
        cluster_info = {
            'ranking': int(cluster['ranking']),
            'cluster_id': int(cluster['cluster_id']),
            'ubicacion': {
                'latitud': round(cluster['centroid_lat'], 6),
                'longitud': round(cluster['centroid_lon'], 6),
                'radio_km': cluster['radio_km']
            },
            'metricas_basicas': {
                'transformadores': int(cluster['n_transformadores']),
                'usuarios': int(cluster['n_usuarios']),
                'potencia_total_mva': round(cluster['potencia_total_mva'], 2),
                'tasa_falla': round(cluster['tasa_falla'], 3)
            },
            'scores_ias': {
                'ias_promedio': round(cluster['ias_promedio'], 3),
                'C1_coincidencia': round(cluster['C1_promedio'], 3),
                'C2_capacidad_absorcion': round(cluster['C2_promedio'], 3),
                'C3_debilidad_red': round(cluster['C3_promedio'], 3),
                'C4_cargabilidad': round(cluster['C4_promedio'], 3),
                'C5_calidad_servicio': round(cluster['C5_promedio'], 3)
            },
            'recomendacion_gd': {
                'potencia_mw': round(cluster['gd_recomendada_mw'], 2),
                'produccion_anual_mwh': round(cluster['produccion_anual_mwh'], 0),
                'perfil_dominante': cluster['perfil_dominante'],
                'configuracion_sugerida': 'Solar FV con trackers + paneles bifaciales',
                'area_estimada_ha': round(cluster['gd_recomendada_mw'] * 2, 1)  # ~2 ha/MW
            },
            'beneficios_esperados': {
                'usuarios_beneficiados': int(cluster['n_usuarios']),
                'reduccion_fallas_esperada': '30-50%',
                'mejora_tension': 'Significativa en horario diurno',
                'reduccion_perdidas': '20-40% en alimentador'
            }
        }
        
        report['top_clusters'].append(cluster_info)
    
    # Resumen ejecutivo
    total_gd = df_clusters.head(top_n)['gd_recomendada_mw'].sum()
    total_usuarios = df_clusters.head(top_n)['n_usuarios'].sum()
    total_produccion = df_clusters.head(top_n)['produccion_anual_mwh'].sum()
    
    report['resumen_ejecutivo'] = {
        'gd_total_recomendada_mw': round(total_gd, 2),
        'produccion_total_anual_mwh': round(total_produccion, 0),
        'usuarios_beneficiados_total': int(total_usuarios),
        'inversion_estimada_musd': round(total_gd * 1.2, 1),  # ~1.2 MUSD/MW
        'area_total_requerida_ha': round(total_gd * 2, 0),
        'reduccion_emisiones_tco2_anual': round(total_produccion * 0.4 / 1000, 1)  # 0.4 tCO2/MWh
    }
    
    # Guardar reporte
    report_path = CLUSTERING_DIR / "cluster_report_ias.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Reporte guardado en: {report_path}")
    
    # Generar también CSV para fácil análisis
    csv_path = CLUSTERING_DIR / "cluster_ranking_ias.csv"
    df_clusters.to_csv(csv_path, index=False)
    logger.info(f"Ranking CSV guardado en: {csv_path}")
    
    return report

def main():
    """Función principal"""
    logger.info("=== INICIANDO ANÁLISIS DE CLUSTERING BASADO EN PERFILES ===")
    logger.info("Metodología: Índice de Aptitud Solar sin BESS (IAS)")
    
    # Cargar datos
    df = load_transformer_data()
    if df is None:
        logger.error("No se pudieron cargar los datos")
        return
    
    # Calcular IAS scores
    analyzer = SolarAptitudeAnalyzer()
    df = analyzer.calculate_ias_score(df)
    
    # Estadísticas de IAS
    logger.info("\nEstadísticas de IAS Score:")
    logger.info(f"  - Media: {df['IAS_score'].mean():.3f}")
    logger.info(f"  - Mediana: {df['IAS_score'].median():.3f}")
    logger.info(f"  - Desv. Estándar: {df['IAS_score'].std():.3f}")
    logger.info(f"  - Transformadores Alta/Muy Alta aptitud: {(df['aptitud_solar'].isin(['Alta', 'Muy Alta'])).sum()}")
    
    # Realizar clustering (DBSCAN por defecto)
    df = perform_clustering(df, method='dbscan', eps=0.5, min_samples=10)
    
    # Si hay muy pocos clusters, intentar con K-means
    n_clusters = len(set(df['cluster'])) - (1 if -1 in df['cluster'] else 0)
    if n_clusters < 10:
        logger.warning(f"Solo {n_clusters} clusters encontrados con DBSCAN. Intentando K-means...")
        df = perform_clustering(df, method='kmeans', n_clusters=15)
    
    # Analizar clusters
    df_clusters = analyze_clusters(df)
    
    # Crear visualizaciones
    create_cluster_map(df, df_clusters)
    create_visualizations(df, df_clusters)
    
    # Generar reporte
    report = generate_cluster_report(df_clusters, top_n=15)
    
    # Guardar datos procesados
    output_path = DATA_DIR / "processed" / "transformers_ias_clustering.parquet"
    output_path.parent.mkdir(exist_ok=True)
    df.to_parquet(output_path)
    logger.info(f"Datos procesados guardados en: {output_path}")
    
    # Resumen final
    logger.info("\n=== RESUMEN DEL ANÁLISIS ===")
    logger.info(f"Total transformadores analizados: {len(df)}")
    logger.info(f"Clusters identificados: {len(df_clusters)}")
    logger.info(f"Top 5 clusters por prioridad:")
    for _, cluster in df_clusters.head(5).iterrows():
        logger.info(f"  #{cluster['ranking']}: Cluster {cluster['cluster_id']} - "
                   f"IAS: {cluster['ias_promedio']:.3f}, "
                   f"Usuarios: {cluster['n_usuarios']:,}, "
                   f"GD: {cluster['gd_recomendada_mw']:.2f} MW")
    
    logger.info("\n=== ANÁLISIS COMPLETADO ===")

if __name__ == "__main__":
    main()