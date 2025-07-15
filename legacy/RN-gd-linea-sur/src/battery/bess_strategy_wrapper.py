"""
BESS Strategy Wrapper
--------------------
Wrapper para todas las estrategias BESS que:
1. Valida balance energético en cada timestep
2. Registra métricas para ML
3. Detecta y reporta anomalías
4. Provee interfaz unificada
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .bess_model import BESSModel
from .bess_strategies import BESSStrategies

logger = logging.getLogger(__name__)


class BESSStrategyWrapper:
    """
    Wrapper unificado para ejecutar estrategias BESS con validación y logging ML.
    """
    
    def __init__(self, 
                 log_level: str = 'WARNING',
                 ml_logging: bool = True,
                 validate_balance: bool = True,
                 tolerance: float = 1e-6):
        """
        Inicializa el wrapper.
        
        Args:
            log_level: Nivel de logging ('DEBUG', 'INFO', 'WARNING', 'ERROR')
            ml_logging: Si registrar métricas para ML
            validate_balance: Si validar balance energético
            tolerance: Tolerancia para errores de balance (MW)
        """
        self.ml_logging = ml_logging
        self.validate_balance = validate_balance
        self.tolerance = tolerance
        
        # Configurar logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Almacenamiento de métricas
        self.reset_metrics()
    
    def reset_metrics(self):
        """Reinicia las métricas acumuladas."""
        self.ml_metrics = []
        self.balance_errors = []
        self.execution_metadata = {}
    
    def execute_strategy(self, 
                        bess_model: BESSModel,
                        solar: np.ndarray,
                        strategy_name: str,
                        dt: float = 1.0,
                        **strategy_params) -> Dict[str, Any]:
        """
        Ejecuta una estrategia con validación completa.
        
        Args:
            bess_model: Modelo BESS a usar
            solar: Perfil de generación solar (MW)
            strategy_name: Nombre de la estrategia
            dt: Timestep en horas
            **strategy_params: Parámetros específicos de la estrategia
            
        Returns:
            Dict con resultados y métricas
        """
        # Reset métricas
        self.reset_metrics()
        
        # Guardar metadata
        self.execution_metadata = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_name,
            'bess_config': bess_model.get_configuration_summary(),
            'solar_total_mwh': float(solar.sum() * dt),
            'solar_peak_mw': float(solar.max()),
            'timesteps': len(solar),
            'dt_hours': dt,
            'strategy_params': strategy_params
        }
        
        # Arrays para resultados
        n_steps = len(solar)
        grid = np.zeros(n_steps)
        battery = np.zeros(n_steps)
        soc = np.zeros(n_steps)
        curtailed = np.zeros(n_steps)
        losses = np.zeros(n_steps)
        
        # Resetear BESS
        bess_model.reset()
        
        # Ejecutar estrategia
        start_time = datetime.now()
        
        try:
            # Mapeo de estrategias
            if strategy_name == 'cap_shaving':
                BESSStrategies.apply_cap_shaving(
                    bess_model, solar, grid, battery, soc, curtailed, losses,
                    dt=dt, **strategy_params
                )
            elif strategy_name == 'cap_shaving_balanced':
                BESSStrategies.apply_cap_shaving_balanced(
                    bess_model, solar, grid, battery, soc, curtailed, losses,
                    dt=dt, **strategy_params
                )
            elif strategy_name == 'soft_cap_shaving':
                BESSStrategies.apply_soft_cap_shaving(
                    bess_model, solar, grid, battery, soc, curtailed, losses,
                    dt=dt, **strategy_params
                )
            elif strategy_name == 'flat_day':
                BESSStrategies.apply_flat_day(
                    bess_model, solar, grid, battery, soc, curtailed, losses,
                    dt=dt, **strategy_params
                )
            elif strategy_name == 'night_shift':
                BESSStrategies.apply_night_shift(
                    bess_model, solar, grid, battery, soc, curtailed, losses,
                    dt=dt, **strategy_params
                )
            elif strategy_name == 'ramp_limit':
                BESSStrategies.apply_ramp_limit(
                    bess_model, solar, grid, battery, soc, curtailed, losses,
                    dt=dt, **strategy_params
                )
            else:
                raise ValueError(f"Unknown strategy: {strategy_name}")
                
        except Exception as e:
            self.logger.error(f"Error executing strategy {strategy_name}: {e}")
            raise
        
        execution_time = (datetime.now() - start_time).total_seconds()
        self.execution_metadata['execution_time_seconds'] = execution_time
        
        # Validar balance y registrar métricas
        if self.validate_balance or self.ml_logging:
            for i in range(n_steps):
                # Validar balance
                if self.validate_balance:
                    balance_error = self._validate_timestep(
                        i, solar[i], grid[i], battery[i], curtailed[i], 
                        strategy_name, dt
                    )
                else:
                    balance_error = 0.0
                
                # Registrar métricas ML
                if self.ml_logging:
                    self._log_ml_metrics(
                        i, solar[i], grid[i], battery[i], soc[i], 
                        curtailed[i], losses[i], balance_error, 
                        strategy_name, bess_model, strategy_params, dt
                    )
        
        # Calcular métricas agregadas
        aggregated_metrics = self._calculate_aggregated_metrics(
            solar, grid, battery, soc, curtailed, losses, dt
        )
        
        # Preparar resultados
        results = {
            # Arrays originales
            'grid_power': grid,
            'battery_power': battery,
            'soc': soc,
            'solar_curtailed': curtailed,
            'energy_losses': losses,
            'solar_delivered': solar - curtailed,
            
            # Métricas ML
            'ml_metrics': self.ml_metrics.copy() if self.ml_logging else None,
            'ml_dataframe': pd.DataFrame(self.ml_metrics) if self.ml_logging and self.ml_metrics else None,
            
            # Errores de balance
            'balance_errors': self.balance_errors.copy(),
            'max_balance_error': max([e['error'] for e in self.balance_errors]) if self.balance_errors else 0.0,
            'balance_errors_count': len(self.balance_errors),
            
            # Métricas agregadas
            'metrics': aggregated_metrics,
            
            # Metadata
            'metadata': self.execution_metadata.copy(),
            
            # Validación
            'validation': {
                'valid': len(self.balance_errors) == 0 or self.max_balance_error < self.tolerance,
                'balance_errors': len(self.balance_errors),
                'max_error_mw': self.max_balance_error if hasattr(self, 'max_balance_error') else 0.0
            }
        }
        
        return results
    
    def _validate_timestep(self, i: int, solar: float, grid: float, battery: float, 
                          curtailed: float, strategy: str, dt: float) -> float:
        """
        Valida balance energético en un timestep.
        
        Returns:
            Error absoluto en MW
        """
        # Componentes del balance
        charge_to_bess = -battery if battery < 0 else 0
        discharge_from_bess = battery if battery > 0 else 0
        
        # Balance según estrategia
        if strategy == 'soft_cap_shaving':
            # En soft_cap_shaving, curtailment es informativo
            expected = grid + charge_to_bess - discharge_from_bess
        else:
            # Estrategias normales incluyen curtailment real
            expected = grid + curtailed + charge_to_bess - discharge_from_bess
        
        error = abs(solar - expected)
        
        if error > self.tolerance:
            error_data = {
                'timestep': i,
                'hour': i * dt,
                'solar': float(solar),
                'expected': float(expected),
                'error': float(error),
                'error_pct': float(error / solar * 100) if solar > 0 else 0.0,
                'strategy': strategy,
                'components': {
                    'grid': float(grid),
                    'curtailed': float(curtailed),
                    'charge': float(charge_to_bess),
                    'discharge': float(discharge_from_bess)
                }
            }
            self.balance_errors.append(error_data)
            
            if error > 0.001:  # Error significativo
                self.logger.warning(
                    f"Balance error at timestep {i}: {error:.6f} MW "
                    f"({error_data['error_pct']:.2f}% of solar)"
                )
        
        return error
    
    def _log_ml_metrics(self, i: int, solar: float, grid: float, battery: float,
                       soc: float, curtailed: float, losses: float, balance_error: float,
                       strategy: str, bess_model: BESSModel, strategy_params: dict, dt: float):
        """Registra métricas útiles para ML."""
        
        # Extraer configuración BESS
        bess_config = bess_model.get_configuration_summary()
        
        metrics = {
            # Identificadores
            'timestep': i,
            'hour': i * dt,
            'strategy': strategy,
            
            # Inputs
            'solar_mw': float(solar),
            'bess_power_mw': float(bess_config['power_mw']),
            'bess_capacity_mwh': float(bess_config['capacity_mwh']),
            'bess_c_rate': float(bess_config['c_rate']),
            
            # Outputs principales
            'grid_mw': float(grid),
            'battery_mw': float(battery),
            'soc_pct': float(soc * 100),
            'curtailed_mw': float(curtailed),
            'losses_mwh': float(losses),
            
            # Features derivados - Estado
            'is_charging': battery < 0,
            'is_discharging': battery > 0,
            'is_idle': abs(battery) < 0.001,
            'charge_rate': abs(battery) / bess_config['capacity_mwh'] if battery < 0 else 0.0,
            'discharge_rate': battery / bess_config['capacity_mwh'] if battery > 0 else 0.0,
            
            # Features derivados - SOC
            'soc_headroom': float(bess_model.tech_params['soc_max'] - soc),
            'soc_available': float(soc - bess_model.tech_params['soc_min']),
            'is_saturated': soc >= bess_model.tech_params['soc_max'] - 0.01,
            'is_depleted': soc <= bess_model.tech_params['soc_min'] + 0.01,
            
            # Features derivados - Grid
            'grid_exceeds_solar': grid > solar,
            'grid_below_solar': grid < solar,
            'grid_solar_ratio': float(grid / solar) if solar > 0 else 0.0,
            
            # Features derivados - Curtailment
            'is_curtailing': curtailed > 0,
            'curtailment_ratio': float(curtailed / solar) if solar > 0 else 0.0,
            
            # Balance
            'balance_error_mw': float(balance_error),
            'balance_error_pct': float(balance_error / solar * 100) if solar > 0 else 0.0,
            
            # Eficiencia instantánea
            'instant_efficiency': float(
                1 - (losses / abs(battery)) if abs(battery) > 0 else 1.0
            ),
        }
        
        # Agregar parámetros específicos de estrategia
        if strategy == 'cap_shaving' or strategy == 'soft_cap_shaving':
            cap_mw = strategy_params.get('cap_mw', 0)
            metrics['cap_mw'] = float(cap_mw)
            metrics['solar_exceeds_cap'] = solar > cap_mw
            metrics['excess_over_cap'] = float(max(0, solar - cap_mw))
            metrics['cap_utilization'] = float(grid / cap_mw) if cap_mw > 0 else 0.0
            
        elif strategy == 'flat_day':
            start_hour = strategy_params.get('start_hour', 8)
            end_hour = strategy_params.get('end_hour', 18)
            flat_mw = strategy_params.get('flat_mw')
            
            in_window = start_hour <= (i * dt) < end_hour
            metrics['in_flat_window'] = in_window
            metrics['flat_start_hour'] = start_hour
            metrics['flat_end_hour'] = end_hour
            
            if flat_mw is not None:
                metrics['flat_target_mw'] = float(flat_mw)
                metrics['deviation_from_flat'] = float(abs(grid - flat_mw)) if in_window else 0.0
                metrics['flat_achievement'] = float(grid / flat_mw) if flat_mw > 0 and in_window else 0.0
        
        elif strategy == 'ramp_limit':
            ramp_limit = strategy_params.get('ramp_limit_mw_per_hour', 0)
            metrics['ramp_limit_mw_per_hour'] = float(ramp_limit)
            # El ramp real se calcula en post-processing porque necesita t-1
        
        self.ml_metrics.append(metrics)
    
    def _calculate_aggregated_metrics(self, solar, grid, battery, soc, curtailed, 
                                    losses, dt) -> Dict[str, float]:
        """Calcula métricas agregadas del día completo."""
        
        # Totales de energía
        total_solar = float(solar.sum() * dt)
        total_grid = float(grid.sum() * dt)
        total_curtailed = float(curtailed.sum() * dt)
        total_losses = float(losses.sum() * dt)
        
        # Flujos BESS
        charge_energy = float(-battery[battery < 0].sum() * dt)
        discharge_energy = float(battery[battery > 0].sum() * dt)
        
        # Eficiencia realizada
        roundtrip_efficiency = discharge_energy / charge_energy if charge_energy > 0 else 0.0
        
        # Ciclos equivalentes
        cycles = (charge_energy + discharge_energy) / 2 / (soc.max() - soc.min()) if soc.max() > soc.min() else 0.0
        
        # Utilización
        soc_range = float(soc.max() - soc.min())
        capacity_utilization = soc_range * 100
        
        # Variabilidad
        grid_std = float(np.std(grid))
        solar_std = float(np.std(solar))
        variability_reduction = (solar_std - grid_std) / solar_std * 100 if solar_std > 0 else 0.0
        
        # Rampas
        grid_ramps = np.diff(grid)
        solar_ramps = np.diff(solar)
        max_ramp_reduction = (np.abs(solar_ramps).max() - np.abs(grid_ramps).max()) if len(grid_ramps) > 0 else 0.0
        
        return {
            # Energías
            'total_solar_mwh': total_solar,
            'total_grid_mwh': total_grid,
            'total_curtailed_mwh': total_curtailed,
            'total_losses_mwh': total_losses,
            'charge_energy_mwh': charge_energy,
            'discharge_energy_mwh': discharge_energy,
            
            # Eficiencias
            'roundtrip_efficiency': roundtrip_efficiency,
            'solar_utilization': total_grid / total_solar if total_solar > 0 else 0.0,
            'curtailment_ratio': total_curtailed / total_solar if total_solar > 0 else 0.0,
            'loss_ratio': total_losses / total_solar if total_solar > 0 else 0.0,
            
            # Operación BESS
            'cycles_equivalent': cycles,
            'capacity_utilization_pct': capacity_utilization,
            'max_soc_pct': float(soc.max() * 100),
            'min_soc_pct': float(soc.min() * 100),
            'final_soc_pct': float(soc[-1] * 100),
            
            # Calidad de servicio
            'variability_reduction_pct': variability_reduction,
            'max_ramp_reduction_mw': max_ramp_reduction,
            'peak_shaving_mw': float(solar.max() - grid.max()),
            'peak_shaving_pct': (solar.max() - grid.max()) / solar.max() * 100 if solar.max() > 0 else 0.0,
            
            # Tiempos de operación
            'hours_charging': float(np.sum(battery < -0.001) * dt),
            'hours_discharging': float(np.sum(battery > 0.001) * dt),
            'hours_idle': float(np.sum(np.abs(battery) <= 0.001) * dt),
            'hours_saturated': float(np.sum(soc >= 0.94) * dt),
            'hours_depleted': float(np.sum(soc <= 0.11) * dt),
        }
    
    def get_ml_dataframe(self) -> Optional[pd.DataFrame]:
        """
        Retorna DataFrame con métricas ML incluyendo features adicionales.
        """
        if not self.ml_metrics:
            return None
        
        df = pd.DataFrame(self.ml_metrics)
        
        # Agregar features temporales
        if 'hour' in df.columns:
            df['hour_of_day'] = (df['hour'] % 24).astype(int)
            df['is_daytime'] = df['hour_of_day'].between(6, 18)
            df['is_peak_hour'] = df['hour_of_day'].between(17, 21)
            df['is_morning'] = df['hour_of_day'].between(6, 12)
            df['is_afternoon'] = df['hour_of_day'].between(12, 18)
        
        # Calcular rampas (necesita shift)
        if 'grid_mw' in df.columns:
            df['grid_ramp_mw'] = df['grid_mw'].diff()
            df['solar_ramp_mw'] = df['solar_mw'].diff()
            df['soc_delta_pct'] = df['soc_pct'].diff()
            
            # Rolling stats
            for window in [3, 6, 12]:
                df[f'grid_rolling_mean_{window}h'] = df['grid_mw'].rolling(window, center=True).mean()
                df[f'grid_rolling_std_{window}h'] = df['grid_mw'].rolling(window, center=True).std()
                df[f'solar_rolling_mean_{window}h'] = df['solar_mw'].rolling(window, center=True).mean()
        
        # Lags para series temporales
        for lag in [1, 4, 24]:
            if len(df) > lag:
                df[f'solar_lag_{lag}h'] = df['solar_mw'].shift(lag)
                df[f'soc_lag_{lag}h'] = df['soc_pct'].shift(lag)
        
        return df
    
    def generate_ml_report(self) -> Dict[str, Any]:
        """Genera reporte completo para análisis ML."""
        
        df = self.get_ml_dataframe()
        if df is None:
            return {'error': 'No ML metrics available'}
        
        report = {
            'execution_metadata': self.execution_metadata,
            'balance_validation': {
                'errors_count': len(self.balance_errors),
                'max_error_mw': max([e['error'] for e in self.balance_errors]) if self.balance_errors else 0.0,
                'mean_error_mw': np.mean([e['error'] for e in self.balance_errors]) if self.balance_errors else 0.0,
                'error_timesteps': [e['timestep'] for e in self.balance_errors]
            },
            'feature_statistics': df.describe().to_dict(),
            'feature_correlations': df.select_dtypes(include=[np.number]).corr().to_dict(),
            'strategy_specific': {}
        }
        
        # Análisis específico por estrategia
        strategy = self.execution_metadata.get('strategy')
        
        if strategy in ['cap_shaving', 'soft_cap_shaving']:
            if 'cap_mw' in df.columns:
                report['strategy_specific'] = {
                    'cap_mw': df['cap_mw'].iloc[0],
                    'hours_above_cap': df['solar_exceeds_cap'].sum(),
                    'total_excess_mwh': df['excess_over_cap'].sum() * self.execution_metadata['dt_hours'],
                    'cap_utilization_mean': df['cap_utilization'].mean(),
                    'cap_utilization_max': df['cap_utilization'].max()
                }
        
        elif strategy == 'flat_day':
            if 'in_flat_window' in df.columns:
                window_df = df[df['in_flat_window']]
                if len(window_df) > 0 and 'deviation_from_flat' in window_df.columns:
                    report['strategy_specific'] = {
                        'flat_window_hours': window_df['in_flat_window'].sum(),
                        'mean_deviation_mw': window_df['deviation_from_flat'].mean(),
                        'max_deviation_mw': window_df['deviation_from_flat'].max(),
                        'flat_achievement_mean': window_df['flat_achievement'].mean() if 'flat_achievement' in window_df else None
                    }
        
        return report


# Funciones auxiliares para preparación de datos ML
def prepare_ml_features(wrapper_results: Dict[str, Any], 
                       include_lags: bool = True,
                       include_rolling: bool = True) -> pd.DataFrame:
    """
    Prepara features para entrenamiento ML desde resultados del wrapper.
    
    Args:
        wrapper_results: Resultados de BESSStrategyWrapper.execute_strategy()
        include_lags: Si incluir features con lag temporal
        include_rolling: Si incluir estadísticas rolling
        
    Returns:
        DataFrame listo para ML
    """
    df = wrapper_results.get('ml_dataframe')
    if df is None:
        raise ValueError("No ML dataframe in results")
    
    # Copia para no modificar original
    df = df.copy()
    
    # One-hot encoding para estrategia
    if 'strategy' in df.columns:
        strategy_dummies = pd.get_dummies(df['strategy'], prefix='strategy')
        df = pd.concat([df, strategy_dummies], axis=1)
    
    # Interacciones útiles
    if 'solar_mw' in df.columns and 'bess_power_mw' in df.columns:
        df['solar_to_bess_ratio'] = df['solar_mw'] / df['bess_power_mw']
        df['solar_to_capacity_ratio'] = df['solar_mw'] / df['bess_capacity_mwh']
    
    # Features cíclicos para hora del día
    if 'hour_of_day' in df.columns:
        df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
    
    # Eliminar features no numéricos o redundantes
    exclude_cols = ['timestep', 'hour', 'strategy']
    numeric_df = df.select_dtypes(include=[np.number])
    feature_cols = [col for col in numeric_df.columns if col not in exclude_cols]
    
    return df[feature_cols]


def create_ml_targets(wrapper_results: Dict[str, Any]) -> pd.DataFrame:
    """
    Crea variables target para diferentes tareas de ML.
    
    Returns:
        DataFrame con múltiples targets
    """
    df = wrapper_results.get('ml_dataframe')
    if df is None:
        raise ValueError("No ML dataframe in results")
    
    targets = pd.DataFrame(index=df.index)
    
    # Targets de regresión
    targets['target_grid_mw'] = df['grid_mw']
    targets['target_soc_next'] = df['soc_pct'].shift(-1)  # Predecir SOC siguiente
    targets['target_losses_mwh'] = df['losses_mwh']
    
    # Targets de clasificación
    targets['target_will_curtail'] = df['curtailed_mw'].shift(-1) > 0  # Predecir si habrá curtailment
    targets['target_will_charge'] = df['battery_mw'].shift(-1) < 0
    targets['target_will_discharge'] = df['battery_mw'].shift(-1) > 0
    targets['target_will_saturate'] = df['soc_pct'].shift(-1) >= 94  # Predecir saturación
    
    # Target multi-clase para acción BESS
    conditions = [
        df['battery_mw'].shift(-1) < -0.01,  # Cargando
        df['battery_mw'].shift(-1) > 0.01,   # Descargando
    ]
    choices = ['charge', 'discharge']
    targets['target_bess_action'] = np.select(conditions, choices, default='idle')
    
    return targets