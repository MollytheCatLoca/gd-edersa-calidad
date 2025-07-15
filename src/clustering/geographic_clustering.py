"""
Clustering geográfico para identificar zonas óptimas de GD
"""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from typing import List, Dict, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class GeographicClusterer:
    """Agrupa transformadores geográficamente para identificar ubicaciones óptimas de GD"""
    
    def __init__(self, transformers: List):
        self.transformers = transformers
        # Filtrar solo transformadores con coordenadas
        self.geo_transformers = [t for t in transformers if t.has_coordinates]
        logger.info(f"Transformadores con coordenadas: {len(self.geo_transformers)}")
        
    def cluster_by_density(self, eps: float = 0.01, min_samples: int = 5) -> Dict[int, List]:
        """Clustering por densidad usando DBSCAN"""
        
        # Preparar coordenadas
        coords = np.array([[t.coord_x, t.coord_y] for t in self.geo_transformers])
        
        # Aplicar DBSCAN
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
        
        # Agrupar transformadores por cluster
        clusters = defaultdict(list)
        for idx, label in enumerate(clustering.labels_):
            clusters[label].append(self.geo_transformers[idx])
            
        logger.info(f"Clusters encontrados: {len(clusters) - 1} (excluyendo ruido)")
        return dict(clusters)
        
    def find_optimal_gd_locations(self, n_locations: int = 10) -> List[Dict]:
        """Encuentra ubicaciones óptimas para GD basado en criticidad y densidad"""
        
        # Filtrar transformadores problemáticos con coordenadas
        critical_transformers = [
            t for t in self.geo_transformers 
            if t.penalized
        ]
        
        if len(critical_transformers) < n_locations:
            logger.warning(f"Solo {len(critical_transformers)} transformadores críticos con coordenadas")
            n_locations = len(critical_transformers)
            
        if n_locations == 0:
            return []
            
        # Preparar datos para clustering
        coords = np.array([[t.coord_x, t.coord_y] for t in critical_transformers])
        weights = np.array([t.usuarios * t.potencia_kva for t in critical_transformers])
        
        # K-means ponderado
        kmeans = KMeans(n_clusters=n_locations, random_state=42)
        kmeans.fit(coords, sample_weight=weights)
        
        # Analizar cada cluster
        locations = []
        for i in range(n_locations):
            cluster_mask = kmeans.labels_ == i
            cluster_transformers = [t for t, m in zip(critical_transformers, cluster_mask) if m]
            
            if not cluster_transformers:
                continue
                
            # Centro del cluster
            center = kmeans.cluster_centers_[i]
            
            # Calcular métricas del cluster
            total_users = sum(t.usuarios for t in cluster_transformers)
            total_kva = sum(t.potencia_kva for t in cluster_transformers)
            
            locations.append({
                'location_id': i,
                'latitude': center[1],
                'longitude': center[0],
                'transformers_count': len(cluster_transformers),
                'affected_users': total_users,
                'total_capacity_kva': total_kva,
                'priority_score': total_users * 0.6 + total_kva * 0.4,
                'nearest_branch': self._find_nearest_branch(center[0], center[1])
            })
            
        # Ordenar por prioridad
        locations.sort(key=lambda x: x['priority_score'], reverse=True)
        return locations
        
    def _find_nearest_branch(self, lon: float, lat: float) -> str:
        """Encuentra la sucursal más cercana a una coordenada"""
        min_dist = float('inf')
        nearest = None
        
        for t in self.geo_transformers:
            if t.sucursal != 'SIN_SUCURSAL':
                dist = np.sqrt((t.coord_x - lon)**2 + (t.coord_y - lat)**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest = t.sucursal
                    
        return nearest or 'DESCONOCIDA'
