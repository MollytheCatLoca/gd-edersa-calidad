"""
ML Data Collector
=================

Módulo para capturar datos de simulaciones BESS para machine learning.
Recopila tanto casos exitosos como fallidos para entrenamiento de modelos.

Funcionalidades:
- Captura datos de simulaciones con pérdidas >7% (casos de aprendizaje)
- Almacena features y targets para ML
- Exporta datasets para entrenamiento
- Análisis de patrones en estrategias ineficientes

Autor: Claude AI Assistant
Fecha: Julio 2025
Versión: 1.0
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class MLDataPoint:
    """Punto de datos para ML con features y targets"""
    # Metadata
    timestamp: str
    simulation_id: str
    
    # Features de configuración
    station: str
    month: int
    psfv_power_mw: float
    bess_power_mw: float
    bess_duration_h: float
    bess_technology: str
    strategy: str
    is_aggressive: bool
    
    # Features de perfil solar
    solar_peak_mw: float
    solar_total_mwh: float
    solar_variability: float
    solar_capacity_factor: float
    
    # Features de operación BESS
    bess_cycles: float
    bess_efficiency: float
    bess_utilization: float
    energy_shifted_mwh: float
    
    # Targets (resultados)
    loss_percentage: float
    net_energy_mwh: float
    variability_reduction: float
    peak_shaving: float
    
    # Labels de calidad
    is_efficient: bool  # < 7% pérdidas
    is_viable: bool     # < 10.5% pérdidas
    quality_score: float  # 0-100
    
    # Metadata adicional
    balance_error: float
    simulation_time_ms: float
    cache_hit: bool


class MLDataCollector:
    """
    Colector de datos para machine learning de sistemas BESS.
    
    Captura todos los datos de simulación, especialmente casos con pérdidas
    elevadas que son útiles para aprender qué configuraciones evitar.
    """
    
    def __init__(self, data_dir: str = "data/ml_training"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos de datos
        self.efficient_data_file = self.data_dir / "efficient_cases.jsonl"
        self.inefficient_data_file = self.data_dir / "inefficient_cases.jsonl"
        self.all_data_file = self.data_dir / "all_simulations.jsonl"
        
        # Contadores
        self.total_simulations = 0
        self.efficient_cases = 0
        self.inefficient_cases = 0
        
    def collect_simulation_data(self, 
                              config: Dict[str, Any],
                              solar_profile: List[float],
                              bess_profile: List[float],
                              losses: List[float],
                              validation_result: Dict[str, Any],
                              simulation_metadata: Dict[str, Any]) -> MLDataPoint:
        """
        Recopila datos de una simulación para ML.
        
        Args:
            config: Configuración de la simulación
            solar_profile: Perfil solar [MW]
            bess_profile: Perfil BESS [MW]
            losses: Pérdidas [MW]
            validation_result: Resultado de validación
            simulation_metadata: Metadata de la simulación
            
        Returns:
            MLDataPoint con datos estructurados
        """
        # Calcular features
        solar_features = self._calculate_solar_features(solar_profile)
        bess_features = self._calculate_bess_features(bess_profile)
        targets = self._calculate_targets(solar_profile, bess_profile, losses)
        
        # Crear punto de datos
        data_point = MLDataPoint(
            # Metadata
            timestamp=datetime.now().isoformat(),
            simulation_id=simulation_metadata.get('simulation_id', ''),
            
            # Features de configuración
            station=config.get('station', ''),
            month=config.get('month', 6),
            psfv_power_mw=config.get('psfv_power_mw', 0),
            bess_power_mw=config.get('bess_power_mw', 0),
            bess_duration_h=config.get('bess_duration_h', 0),
            bess_technology=config.get('bess_technology', 'modern_lfp'),
            strategy=config.get('strategy', ''),
            is_aggressive=config.get('is_aggressive', False),
            
            # Features de perfil solar
            **solar_features,
            
            # Features de operación BESS
            **bess_features,
            
            # Targets
            **targets,
            
            # Labels de calidad
            is_efficient=targets['loss_percentage'] <= 7.0,
            is_viable=targets['loss_percentage'] <= 10.5,
            quality_score=self._calculate_quality_score(targets),
            
            # Metadata adicional
            balance_error=validation_result.get('balance_error', 0),
            simulation_time_ms=simulation_metadata.get('simulation_time_ms', 0),
            cache_hit=simulation_metadata.get('cache_hit', False)
        )
        
        # Almacenar punto de datos
        self._store_data_point(data_point)
        
        return data_point
    
    def _calculate_solar_features(self, solar_profile: List[float]) -> Dict[str, float]:
        """Calcula features del perfil solar."""
        solar_array = np.array(solar_profile)
        
        return {
            'solar_peak_mw': float(solar_array.max()),
            'solar_total_mwh': float(solar_array.sum()),
            'solar_variability': float(solar_array.std()),
            'solar_capacity_factor': float(solar_array.mean() / solar_array.max()) if solar_array.max() > 0 else 0.0
        }
    
    def _calculate_bess_features(self, bess_profile: List[float]) -> Dict[str, float]:
        """Calcula features de la operación BESS."""
        bess_array = np.array(bess_profile)
        
        # Energía cargada y descargada
        charge_energy = sum(abs(p) for p in bess_profile if p < 0)
        discharge_energy = sum(p for p in bess_profile if p > 0)
        
        # Ciclos aproximados
        cycles = (charge_energy + discharge_energy) / 2 if charge_energy > 0 else 0
        
        # Eficiencia
        efficiency = (discharge_energy / charge_energy) * 100 if charge_energy > 0 else 100
        
        # Utilización
        utilization = (sum(abs(p) for p in bess_profile) / len(bess_profile)) if bess_profile else 0
        
        return {
            'bess_cycles': float(cycles),
            'bess_efficiency': float(efficiency),
            'bess_utilization': float(utilization),
            'energy_shifted_mwh': float(charge_energy)
        }
    
    def _calculate_targets(self, 
                         solar_profile: List[float],
                         bess_profile: List[float],
                         losses: List[float]) -> Dict[str, float]:
        """Calcula targets para ML."""
        solar_array = np.array(solar_profile)
        bess_array = np.array(bess_profile)
        net_profile = solar_array + bess_array
        
        # Pérdidas
        total_losses = sum(losses) if isinstance(losses, list) else losses
        loss_percentage = (total_losses / solar_array.sum() * 100) if solar_array.sum() > 0 else 0
        
        # Variabilidad
        variability_reduction = ((solar_array.std() - net_profile.std()) / solar_array.std() * 100) if solar_array.std() > 0 else 0
        
        # Peak shaving
        peak_shaving = ((solar_array.max() - net_profile.max()) / solar_array.max() * 100) if solar_array.max() > 0 else 0
        
        return {
            'loss_percentage': float(loss_percentage),
            'net_energy_mwh': float(net_profile.sum()),
            'variability_reduction': float(variability_reduction),
            'peak_shaving': float(peak_shaving)
        }
    
    def _calculate_quality_score(self, targets: Dict[str, float]) -> float:
        """Calcula score de calidad 0-100."""
        # Penalizar pérdidas altas
        loss_penalty = max(0, targets['loss_percentage'] - 7.0) * 10
        
        # Bonus por reducción de variabilidad
        variability_bonus = max(0, targets['variability_reduction']) * 0.5
        
        # Bonus por peak shaving
        peak_bonus = max(0, targets['peak_shaving']) * 0.3
        
        # Score base
        base_score = 100
        
        # Score final
        final_score = base_score - loss_penalty + variability_bonus + peak_bonus
        
        return float(max(0, min(100, final_score)))
    
    def _store_data_point(self, data_point: MLDataPoint):
        """Almacena punto de datos en archivos apropriados."""
        # Convertir a dict
        data_dict = asdict(data_point)
        data_json = json.dumps(data_dict)
        
        # Almacenar en archivo general
        with open(self.all_data_file, 'a') as f:
            f.write(data_json + '\n')
        
        # Almacenar en archivo específico según eficiencia
        if data_point.is_efficient:
            with open(self.efficient_data_file, 'a') as f:
                f.write(data_json + '\n')
            self.efficient_cases += 1
        else:
            with open(self.inefficient_data_file, 'a') as f:
                f.write(data_json + '\n')
            self.inefficient_cases += 1
        
        self.total_simulations += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de recolección de datos."""
        return {
            'total_simulations': self.total_simulations,
            'efficient_cases': self.efficient_cases,
            'inefficient_cases': self.inefficient_cases,
            'efficiency_rate': (self.efficient_cases / self.total_simulations * 100) if self.total_simulations > 0 else 0,
            'data_files': {
                'all_data': str(self.all_data_file),
                'efficient_data': str(self.efficient_data_file),
                'inefficient_data': str(self.inefficient_data_file)
            }
        }
    
    def load_dataset(self, file_type: str = 'all') -> pd.DataFrame:
        """
        Carga dataset para análisis.
        
        Args:
            file_type: 'all', 'efficient', 'inefficient'
            
        Returns:
            DataFrame con datos de simulación
        """
        file_map = {
            'all': self.all_data_file,
            'efficient': self.efficient_data_file,
            'inefficient': self.inefficient_data_file
        }
        
        file_path = file_map.get(file_type, self.all_data_file)
        
        if not file_path.exists():
            return pd.DataFrame()
        
        # Leer archivo JSONL
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                data.append(json.loads(line.strip()))
        
        return pd.DataFrame(data)
    
    def export_for_ml(self, output_path: str = None) -> str:
        """
        Exporta dataset procesado para ML.
        
        Args:
            output_path: Ruta de salida (opcional)
            
        Returns:
            Ruta del archivo exportado
        """
        if output_path is None:
            output_path = self.data_dir / "ml_dataset.csv"
        
        # Cargar todos los datos
        df = self.load_dataset('all')
        
        if df.empty:
            return ""
        
        # Seleccionar features importantes para ML
        feature_columns = [
            'psfv_power_mw', 'bess_power_mw', 'bess_duration_h',
            'solar_peak_mw', 'solar_total_mwh', 'solar_variability',
            'solar_capacity_factor', 'bess_cycles', 'bess_efficiency',
            'bess_utilization', 'energy_shifted_mwh'
        ]
        
        target_columns = [
            'loss_percentage', 'net_energy_mwh', 'variability_reduction',
            'peak_shaving', 'is_efficient', 'is_viable', 'quality_score'
        ]
        
        # Filtrar columnas existentes
        available_features = [col for col in feature_columns if col in df.columns]
        available_targets = [col for col in target_columns if col in df.columns]
        
        # Crear dataset para ML
        ml_df = df[available_features + available_targets].copy()
        
        # Exportar
        ml_df.to_csv(output_path, index=False)
        
        return str(output_path)
    
    def analyze_inefficient_patterns(self) -> Dict[str, Any]:
        """
        Analiza patrones en casos ineficientes para insights.
        
        Returns:
            Dict con análisis de patrones
        """
        df = self.load_dataset('inefficient')
        
        if df.empty:
            return {"message": "No hay datos de casos ineficientes"}
        
        analysis = {
            'total_inefficient_cases': len(df),
            'worst_strategies': df.groupby('strategy')['loss_percentage'].mean().sort_values(ascending=False).head(5).to_dict(),
            'problematic_configurations': {
                'high_power_ratio': len(df[df['bess_power_mw'] / df['psfv_power_mw'] > 0.8]),
                'short_duration': len(df[df['bess_duration_h'] < 2]),
                'aggressive_mode': len(df[df['is_aggressive'] == True])
            },
            'loss_distribution': {
                'mean': df['loss_percentage'].mean(),
                'std': df['loss_percentage'].std(),
                'max': df['loss_percentage'].max(),
                'min': df['loss_percentage'].min()
            }
        }
        
        return analysis


# Instancia global para recolección de datos
ml_collector = MLDataCollector()


def collect_ml_data(config: Dict[str, Any],
                   solar_profile: List[float],
                   bess_profile: List[float],
                   losses: List[float],
                   validation_result: Dict[str, Any],
                   simulation_metadata: Dict[str, Any]) -> MLDataPoint:
    """
    Función de conveniencia para recolección de datos ML.
    
    Args:
        config: Configuración de simulación
        solar_profile: Perfil solar [MW]
        bess_profile: Perfil BESS [MW]
        losses: Pérdidas [MW]
        validation_result: Resultado de validación
        simulation_metadata: Metadata de simulación
        
    Returns:
        MLDataPoint con datos recolectados
    """
    return ml_collector.collect_simulation_data(
        config, solar_profile, bess_profile, losses,
        validation_result, simulation_metadata
    )


# Exportar funciones principales
__all__ = [
    'MLDataCollector',
    'MLDataPoint',
    'ml_collector',
    'collect_ml_data'
]