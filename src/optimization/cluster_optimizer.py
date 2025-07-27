"""
Optimizador de Dimensionamiento para Clusters GD
==============================================
Encuentra la configuración óptima de PV, BESS y Q_night
para maximizar el flujo económico total de cada cluster.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from scipy.optimize import minimize, differential_evolution
import logging

# Importar módulos económicos y config
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from economics.integrated_cash_flow import IntegratedCashFlowCalculator
from economics.network_benefits import NetworkBenefitsCalculator
from config.config_loader import get_config

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Resultado de optimización para un cluster"""
    cluster_id: str
    pv_mw_optimal: float
    bess_mwh_optimal: float
    q_night_mvar_optimal: float
    npv_usd: float
    irr_percent: float
    payback_years: float
    bc_ratio: float
    total_capex_usd: float
    annual_flow_usd: float
    pv_flow_usd: float
    network_flow_usd: float
    optimization_status: str
    iterations: int
    

class ClusterOptimizer:
    """
    Optimizador para encontrar el dimensionamiento óptimo de GD
    que maximiza el valor económico total (PV + Red).
    """
    
    def __init__(self, 
                 economic_params: Optional[Dict] = None,
                 technical_constraints: Optional[Dict] = None,
                 optimization_params: Optional[Dict] = None):
        """
        Inicializa el optimizador.
        
        Args:
            economic_params: Parámetros económicos (si None, usa ConfigLoader)
            technical_constraints: Restricciones técnicas (si None, usa ConfigLoader)
            optimization_params: Parámetros del algoritmo (si None, usa ConfigLoader)
        """
        # Cargar configuración centralizada
        config = get_config()
        
        # Usar parámetros proporcionados o cargar desde config
        if economic_params is None:
            self.economic_params = config.get_economic_params()
        else:
            self.economic_params = economic_params
            
        if technical_constraints is None:
            self.constraints = config.get_optimization_constraints()
        else:
            self.constraints = technical_constraints
            
        if optimization_params is None:
            self.opt_params = config.get_section('optimization_algorithm')
        else:
            self.opt_params = optimization_params
        
        # Inicializar calculadores (ya usan ConfigLoader internamente)
        self.cash_flow_calc = IntegratedCashFlowCalculator(self.economic_params)
        self.network_calc = NetworkBenefitsCalculator()
        
        # Contadores para tracking
        self.iteration_count = 0
        self.best_value = -np.inf
        
        logger.info("Optimizador de clusters inicializado con parámetros centralizados")
    
    def optimize_cluster(self, cluster_data: Dict) -> OptimizationResult:
        """
        Optimiza dimensionamiento para un cluster específico.
        
        Args:
            cluster_data: Datos del cluster incluyendo demanda, usuarios, etc.
            
        Returns:
            Resultado de optimización con configuración óptima
        """
        logger.info(f"Optimizando cluster {cluster_data.get('cluster_id', 'unknown')}")
        
        # Reset contadores
        self.iteration_count = 0
        self.best_value = -np.inf
        self.current_cluster = cluster_data
        
        # Definir límites de variables
        bounds = self._get_optimization_bounds(cluster_data)
        
        # Función objetivo
        def objective(x):
            return -self._evaluate_configuration(x, cluster_data)
        
        # Restricciones
        constraints = self._get_optimization_constraints(cluster_data)
        
        # Optimizar según método
        if self.opt_params['method'] == 'differential_evolution':
            result = differential_evolution(
                objective,
                bounds,
                maxiter=self.opt_params['maxiter'],
                popsize=self.opt_params['popsize'],
                tol=self.opt_params['tol'],
                seed=self.opt_params['seed'],
                workers=self.opt_params['workers'],
                disp=self.opt_params['disp'],
                constraints=constraints,
                callback=self._optimization_callback
            )
        else:
            # Punto inicial
            x0 = self._get_initial_guess(cluster_data)
            
            result = minimize(
                objective,
                x0,
                method=self.opt_params['method'],
                bounds=bounds,
                constraints=constraints,
                options={
                    'maxiter': self.opt_params['maxiter'],
                    'disp': self.opt_params['disp']
                },
                callback=self._optimization_callback
            )
        
        # Extraer solución óptima
        if result.success:
            pv_mw, bess_mwh, q_night_mvar = result.x
            metrics = self._calculate_final_metrics(result.x, cluster_data)
            status = 'optimal'
        else:
            # Usar mejor punto encontrado
            pv_mw, bess_mwh, q_night_mvar = self._get_feasible_point(cluster_data)
            metrics = self._calculate_final_metrics([pv_mw, bess_mwh, q_night_mvar], cluster_data)
            status = f'suboptimal: {result.message}'
        
        return OptimizationResult(
            cluster_id=cluster_data.get('cluster_id', 'unknown'),
            pv_mw_optimal=pv_mw,
            bess_mwh_optimal=bess_mwh,
            q_night_mvar_optimal=q_night_mvar,
            npv_usd=metrics['npv_usd'],
            irr_percent=metrics['irr_percent'],
            payback_years=metrics['payback_years'],
            bc_ratio=metrics['bc_ratio'],
            total_capex_usd=metrics['total_capex_usd'],
            annual_flow_usd=metrics['annual_flow_usd'],
            pv_flow_usd=metrics['pv_flow_usd'],
            network_flow_usd=metrics['network_flow_usd'],
            optimization_status=status,
            iterations=self.iteration_count
        )
    
    def _get_optimization_bounds(self, cluster_data: Dict) -> List[Tuple[float, float]]:
        """Define límites para variables de decisión"""
        peak_demand_mw = cluster_data.get('peak_demand_mw', 10)
        
        # PV bounds
        pv_min = self.constraints['pv_min_mw']
        pv_max = peak_demand_mw * self.constraints['pv_max_ratio']
        
        # BESS bounds (en MWh)
        bess_min = 0  # Puede ser 0
        bess_max = peak_demand_mw * self.constraints['bess_max_hours']
        
        # Q night bounds (en MVAr)
        q_min = 0
        q_max = pv_max * self.constraints['q_night_max_ratio']
        
        return [(pv_min, pv_max), (bess_min, bess_max), (q_min, q_max)]
    
    def _get_optimization_constraints(self, cluster_data: Dict) -> List[Dict]:
        """Define restricciones de optimización"""
        constraints = []
        
        # Restricción de inyección máxima
        trafo_capacity = cluster_data.get('transformer_capacity_mva', 20)
        max_injection = trafo_capacity * self.constraints['max_injection_ratio']
        
        def injection_constraint(x):
            pv_mw = x[0]
            return max_injection - pv_mw
        
        constraints.append({
            'type': 'ineq',
            'fun': injection_constraint
        })
        
        # Restricción de IRR mínima (implementada en evaluación)
        # Se maneja penalizando en función objetivo
        
        return constraints
    
    def _evaluate_configuration(self, x: np.ndarray, cluster_data: Dict) -> float:
        """
        Evalúa una configuración específica.
        
        Args:
            x: [pv_mw, bess_mwh, q_night_mvar]
            cluster_data: Datos del cluster
            
        Returns:
            Valor de función objetivo (a maximizar)
        """
        pv_mw, bess_mwh, q_night_mvar = x
        
        # Calcular CAPEX
        capex = self._calculate_capex(pv_mw, bess_mwh, q_night_mvar)
        
        # Calcular flujos de caja
        try:
            cash_flows = self.cash_flow_calc.calculate_integrated_flows(
                cluster_data, pv_mw, bess_mwh, q_night_mvar, capex
            )
            
            # Métricas financieras
            metrics = self.cash_flow_calc.calculate_financial_metrics(
                cash_flows, capex['total']
            )
            
            # Verificar restricciones
            if metrics['irr_percent'] and metrics['irr_percent'] < self.constraints['min_irr'] * 100:
                penalty = -1e6 * (self.constraints['min_irr'] * 100 - metrics['irr_percent'])
            else:
                penalty = 0
            
            if metrics['payback_years'] and metrics['payback_years'] > self.constraints['max_payback']:
                penalty -= 1e5 * (metrics['payback_years'] - self.constraints['max_payback'])
            
            # Función objetivo ponderada
            npv_norm = metrics['npv_usd'] / 1e6  # Normalizar a millones
            irr_norm = (metrics['irr_percent'] or 0) / 100
            
            # Calcular proporción de beneficios de red
            network_ratio = sum(cf.network_flow for cf in cash_flows) / sum(cf.total_flow for cf in cash_flows)
            
            objective = (
                self.opt_params['npv_weight'] * npv_norm +
                self.opt_params['irr_weight'] * irr_norm * 10 +  # Escalar IRR
                self.opt_params['network_benefit_weight'] * network_ratio * 100
            ) + penalty
            
            # Actualizar mejor valor
            if objective > self.best_value:
                self.best_value = objective
                self.best_config = x.copy()
            
            self.iteration_count += 1
            
            return objective
            
        except Exception as e:
            logger.warning(f"Error evaluando configuración {x}: {e}")
            return -1e9  # Penalización severa
    
    def _calculate_capex(self, pv_mw: float, bess_mwh: float, q_night_mvar: float) -> Dict:
        """Calcula CAPEX desglosado"""
        # PV
        pv_capex = pv_mw * self.economic_params['pv_capex_usd_mw']
        
        # BESS (energía + potencia)
        bess_energy_capex = bess_mwh * self.economic_params['bess_capex_usd_mwh']
        bess_power_capex = (bess_mwh / 4) * self.economic_params['bess_capex_usd_mw']  # C-rate 0.25
        bess_capex = bess_energy_capex + bess_power_capex
        
        # STATCOM/Q night
        # Si Q_night <= 0.3 * PV, se incluye en inversor (costo marginal)
        if q_night_mvar <= pv_mw * 0.3:
            q_capex = q_night_mvar * self.economic_params['statcom_capex_usd_mvar'] * 0.3  # 30% costo
        else:
            # Necesita STATCOM dedicado
            q_capex = q_night_mvar * self.economic_params['statcom_capex_usd_mvar']
        
        # BOS y conexión (15% del total)
        subtotal = pv_capex + bess_capex + q_capex
        bos_capex = subtotal * 0.15
        
        return {
            'pv': pv_capex,
            'bess': bess_capex,
            'q_night': q_capex,
            'bos': bos_capex,
            'total': subtotal + bos_capex
        }
    
    def _calculate_final_metrics(self, x: np.ndarray, cluster_data: Dict) -> Dict:
        """Calcula métricas finales para configuración óptima"""
        pv_mw, bess_mwh, q_night_mvar = x
        
        # CAPEX
        capex = self._calculate_capex(pv_mw, bess_mwh, q_night_mvar)
        
        # Flujos
        cash_flows = self.cash_flow_calc.calculate_integrated_flows(
            cluster_data, pv_mw, bess_mwh, q_night_mvar, capex
        )
        
        # Métricas financieras
        financial_metrics = self.cash_flow_calc.calculate_financial_metrics(
            cash_flows, capex['total']
        )
        
        # Flujos promedio
        avg_annual_flow = sum(cf.total_flow for cf in cash_flows) / len(cash_flows)
        avg_pv_flow = sum(cf.pv_flow for cf in cash_flows) / len(cash_flows)
        avg_network_flow = sum(cf.network_flow for cf in cash_flows) / len(cash_flows)
        
        return {
            **financial_metrics,
            'total_capex_usd': capex['total'],
            'annual_flow_usd': avg_annual_flow,
            'pv_flow_usd': avg_pv_flow,
            'network_flow_usd': avg_network_flow
        }
    
    def _get_initial_guess(self, cluster_data: Dict) -> np.ndarray:
        """Genera punto inicial para optimización"""
        peak_demand = cluster_data.get('peak_demand_mw', 10)
        
        # Heurística simple
        pv_mw = peak_demand * 0.8  # 80% de demanda pico
        bess_mwh = peak_demand * 1.0  # 1 hora de almacenamiento
        q_night_mvar = pv_mw * 0.2  # 20% para Q nocturno
        
        return np.array([pv_mw, bess_mwh, q_night_mvar])
    
    def _get_feasible_point(self, cluster_data: Dict) -> np.ndarray:
        """Retorna un punto factible si optimización falla"""
        if hasattr(self, 'best_config'):
            return self.best_config
        else:
            return self._get_initial_guess(cluster_data)
    
    def _optimization_callback(self, xk, convergence=None):
        """Callback para monitorear progreso"""
        if self.iteration_count % 10 == 0:
            logger.info(f"Iteración {self.iteration_count}: mejor valor = {self.best_value:.2f}")
    
    def optimize_multiple_clusters(self, clusters_data: List[Dict],
                                 parallel: bool = True) -> pd.DataFrame:
        """
        Optimiza múltiples clusters.
        
        Args:
            clusters_data: Lista de datos de clusters
            parallel: Si ejecutar en paralelo
            
        Returns:
            DataFrame con resultados de optimización
        """
        results = []
        
        if parallel and self.opt_params['workers'] > 1:
            # TODO: Implementar paralelización con multiprocessing
            pass
        
        # Ejecución secuencial
        for cluster in clusters_data:
            logger.info(f"Optimizando cluster {cluster.get('cluster_id')}...")
            result = self.optimize_cluster(cluster)
            results.append(result)
        
        # Convertir a DataFrame
        df_results = pd.DataFrame([
            {
                'cluster_id': r.cluster_id,
                'pv_mw_optimal': r.pv_mw_optimal,
                'bess_mwh_optimal': r.bess_mwh_optimal,
                'q_night_mvar_optimal': r.q_night_mvar_optimal,
                'npv_musd': r.npv_usd / 1e6,
                'irr_percent': r.irr_percent,
                'payback_years': r.payback_years,
                'bc_ratio': r.bc_ratio,
                'capex_musd': r.total_capex_usd / 1e6,
                'annual_flow_musd': r.annual_flow_usd / 1e6,
                'pv_flow_musd': r.pv_flow_usd / 1e6,
                'network_flow_musd': r.network_flow_usd / 1e6,
                'network_benefit_ratio': r.network_flow_usd / r.annual_flow_usd if r.annual_flow_usd > 0 else 0,
                'status': r.optimization_status,
                'iterations': r.iterations
            }
            for r in results
        ])
        
        # Ordenar por NPV
        df_results = df_results.sort_values('npv_musd', ascending=False)
        
        return df_results