"""
Analizador de calidad de servicio EDERSA
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Analiza calidad de servicio por transformador"""
    
    def __init__(self, transformers: List):
        self.transformers = transformers
        self.df = pd.DataFrame([t.__dict__ for t in transformers])
        
    def analyze_by_zone(self, zone_column: str = 'sucursal') -> pd.DataFrame:
        """Analiza calidad por zona (sucursal, alimentador, etc.)"""
        
        quality_by_zone = self.df.groupby(zone_column).agg({
            'codigo': 'count',
            'potencia_kva': 'sum',
            'usuarios': 'sum',
            'penalized': ['sum', 'mean'],
            'quality_score': 'mean'
        })
        
        quality_by_zone.columns = [
            'total_transformers', 
            'total_kva', 
            'total_users',
            'penalized_count',
            'penalized_rate',
            'avg_quality_score'
        ]
        
        # Calcular criticidad
        quality_by_zone['criticality_index'] = (
            quality_by_zone['penalized_rate'] * 0.4 +
            (1 - quality_by_zone['avg_quality_score']) * 0.3 +
            (quality_by_zone['penalized_count'] / quality_by_zone['total_transformers']) * 0.3
        )
        
        return quality_by_zone.sort_values('criticality_index', ascending=False)
        
    def identify_critical_zones(self, top_n: int = 10) -> List[Dict]:
        """Identifica las zonas más críticas"""
        
        # Por sucursal
        by_branch = self.analyze_by_zone('sucursal')
        
        # Por alimentador
        by_feeder = self.analyze_by_zone('alimentador')
        
        critical_zones = []
        
        # Top sucursales críticas
        for branch in by_branch.head(top_n).index:
            zone_data = by_branch.loc[branch]
            critical_zones.append({
                'type': 'branch',
                'name': branch,
                'criticality_index': zone_data['criticality_index'],
                'penalized_transformers': int(zone_data['penalized_count']),
                'affected_users': int(zone_data['total_users']),
                'total_capacity_mva': zone_data['total_kva'] / 1000
            })
            
        return critical_zones
        
    def calculate_impact_metrics(self) -> Dict:
        """Calcula métricas de impacto del problema de calidad"""
        
        total_users = self.df['usuarios'].sum()
        affected_users = self.df[self.df['penalized']]['usuarios'].sum()
        
        total_capacity = self.df['potencia_kva'].sum()
        affected_capacity = self.df[self.df['penalized']]['potencia_kva'].sum()
        
        metrics = {
            'total_users': int(total_users),
            'affected_users': int(affected_users),
            'users_impact_rate': affected_users / total_users if total_users > 0 else 0,
            'total_capacity_mva': total_capacity / 1000,
            'affected_capacity_mva': affected_capacity / 1000,
            'capacity_impact_rate': affected_capacity / total_capacity if total_capacity > 0 else 0,
            'avg_transformer_size_kva': total_capacity / len(self.df) if len(self.df) > 0 else 0,
            'transformers_by_quality': self.df['resultado'].value_counts().to_dict()
        }
        
        return metrics
