"""
Modelo de Flujos de Caja Integrados para PSFV Multipropósito
===========================================================
Calcula el flujo total considerando ingresos directos del PSFV
más los beneficios en la red de distribución.

FlujoTotal = FlujoPSFV + FlujosRed - OPEX

Autor: Asistente Claude
Fecha: Julio 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
from pathlib import Path
import sys

# Agregar path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config.config_loader import get_config

logger = logging.getLogger(__name__)


@dataclass
class CashFlowComponent:
    """Componente individual de flujo de caja"""
    name: str
    year: int
    value: float
    category: str  # 'pv_revenue', 'network_benefit', 'opex', 'capex'
    

@dataclass
class IntegratedCashFlow:
    """Flujo de caja integrado anual"""
    year: int
    
    # Flujos PSFV
    self_consumption_savings: float = 0.0
    export_credits: float = 0.0
    demand_charge_reduction: float = 0.0
    
    # Flujos Red
    loss_reduction_value: float = 0.0
    q_night_value: float = 0.0
    capex_deferral_value: float = 0.0
    penalty_avoidance: float = 0.0
    
    # Costos
    opex: float = 0.0
    
    @property
    def pv_flow(self) -> float:
        """Flujo total del PSFV"""
        return (self.self_consumption_savings + 
                self.export_credits + 
                self.demand_charge_reduction)
    
    @property
    def network_flow(self) -> float:
        """Flujo total de beneficios en red"""
        return (self.loss_reduction_value + 
                self.q_night_value + 
                self.capex_deferral_value + 
                self.penalty_avoidance)
    
    @property
    def total_flow(self) -> float:
        """Flujo total integrado"""
        return self.pv_flow + self.network_flow - self.opex
    
    @property
    def net_flow(self) -> float:
        """Flujo neto (alias para compatibilidad)"""
        return self.total_flow


class IntegratedCashFlowCalculator:
    """
    Calculador de flujos de caja integrados para proyectos PSFV multipropósito.
    Considera tanto los ingresos directos como los beneficios en la red.
    """
    
    def __init__(self, params: Optional[Dict] = None):
        """
        Inicializa el calculador con parámetros económicos.
        
        Args:
            params: Diccionario con parámetros económicos (si None, usa ConfigLoader)
        """
        if params is None:
            # Cargar desde configuración centralizada
            config = get_config()
            self.params = config.get_economic_params()
        else:
            self.params = params
        
        # Validar parámetros requeridos
        required = ['discount_rate', 'project_lifetime', 'electricity_price']
        for param in required:
            if param not in self.params:
                raise ValueError(f"Parámetro requerido '{param}' no encontrado")
        
        logger.info("Calculador de flujos integrados inicializado")
    
    def calculate_integrated_flows(self,
                                   cluster_data: Dict,
                                   pv_capacity_mw: float,
                                   bess_capacity_mwh: float,
                                   q_night_mvar: float,
                                   capex: Dict) -> List[IntegratedCashFlow]:
        """
        Calcula flujos de caja integrados para configuración dada.
        
        Args:
            cluster_data: Datos del cluster (demanda, perfiles, etc.)
            pv_capacity_mw: Capacidad solar en MW
            bess_capacity_mwh: Capacidad BESS en MWh
            q_night_mvar: Capacidad reactiva nocturna en MVAr
            capex: Diccionario con CAPEX por componente
            
        Returns:
            Lista de flujos de caja por año
        """
        flows = []
        
        for year in range(1, self.params['project_lifetime'] + 1):
            flow = IntegratedCashFlow(year=year)
            
            # Factor de degradación
            pv_degradation_factor = (1 - self.params['pv_degradation']) ** (year - 1)
            bess_degradation_factor = (1 - self.params['bess_degradation']) ** (year - 1)
            
            # Factor de inflación
            inflation_factor = (1 + self.params['inflation_rate']) ** (year - 1)
            
            # 1. Flujos PSFV
            flow.self_consumption_savings = self._calculate_self_consumption_savings(
                cluster_data, pv_capacity_mw, bess_capacity_mwh,
                pv_degradation_factor, bess_degradation_factor, inflation_factor
            )
            
            flow.export_credits = self._calculate_export_credits(
                cluster_data, pv_capacity_mw, bess_capacity_mwh,
                pv_degradation_factor, bess_degradation_factor, inflation_factor
            )
            
            flow.demand_charge_reduction = self._calculate_demand_reduction(
                cluster_data, pv_capacity_mw, bess_capacity_mwh,
                pv_degradation_factor, bess_degradation_factor, inflation_factor
            )
            
            # 2. Flujos Red
            flow.loss_reduction_value = self._calculate_loss_reduction(
                cluster_data, pv_capacity_mw, pv_degradation_factor, inflation_factor
            )
            
            flow.q_night_value = self._calculate_q_night_value(
                cluster_data, q_night_mvar, inflation_factor
            )
            
            flow.capex_deferral_value = self._calculate_capex_deferral(
                cluster_data, pv_capacity_mw, year
            )
            
            flow.penalty_avoidance = self._calculate_penalty_avoidance(
                cluster_data, pv_capacity_mw, q_night_mvar, inflation_factor
            )
            
            # 3. OPEX
            flow.opex = self._calculate_opex(capex, inflation_factor)
            
            flows.append(flow)
            
        return flows
    
    def _calculate_self_consumption_savings(self, cluster_data: Dict, pv_mw: float,
                                          bess_mwh: float, pv_deg: float,
                                          bess_deg: float, inflation: float) -> float:
        """Calcula ahorros por autoconsumo"""
        # Energía PV anual (considerando factor de planta)
        pv_energy_mwh = pv_mw * 8760 * cluster_data.get('pv_capacity_factor', 0.211) * pv_deg
        
        # Proporción autoconsumida (depende del perfil de carga)
        self_consumption_ratio = self._estimate_self_consumption_ratio(
            cluster_data, pv_mw, bess_mwh
        )
        
        self_consumed_mwh = pv_energy_mwh * self_consumption_ratio
        
        # Valor del autoconsumo
        electricity_price = self.params['electricity_price'] * inflation
        return self_consumed_mwh * electricity_price
    
    def _calculate_export_credits(self, cluster_data: Dict, pv_mw: float,
                                bess_mwh: float, pv_deg: float,
                                bess_deg: float, inflation: float) -> float:
        """Calcula créditos por exportación"""
        # Energía PV anual
        pv_energy_mwh = pv_mw * 8760 * cluster_data.get('pv_capacity_factor', 0.211) * pv_deg
        
        # Proporción exportada
        self_consumption_ratio = self._estimate_self_consumption_ratio(
            cluster_data, pv_mw, bess_mwh
        )
        export_ratio = 1 - self_consumption_ratio
        
        exported_mwh = pv_energy_mwh * export_ratio
        
        # Valor de exportación
        export_price = self.params['export_price'] * inflation
        return exported_mwh * export_price
    
    def _calculate_demand_reduction(self, cluster_data: Dict, pv_mw: float,
                                  bess_mwh: float, pv_deg: float,
                                  bess_deg: float, inflation: float) -> float:
        """Calcula reducción en cargos por demanda"""
        # Reducción de pico estimada
        peak_reduction_mw = min(pv_mw * pv_deg, cluster_data.get('peak_demand_mw', 0) * 0.3)
        
        # Si hay BESS, puede reducir más el pico
        if bess_mwh > 0:
            bess_power_mw = bess_mwh / 4  # Asumiendo C-rate de 0.25
            peak_reduction_mw += bess_power_mw * bess_deg * 0.8  # Factor de coincidencia
        
        # Valor anual
        demand_charge = self.params['demand_charge'] * inflation
        return peak_reduction_mw * demand_charge * 12  # 12 meses
    
    def _calculate_loss_reduction(self, cluster_data: Dict, pv_mw: float,
                                pv_deg: float, inflation: float) -> float:
        """Calcula valor de reducción de pérdidas"""
        # Factor de sensibilidad de pérdidas (MW pérdidas / MW inyección)
        loss_sensitivity = cluster_data.get('loss_sensitivity', 0.05)
        
        # Energía inyectada promedio
        avg_injection_mw = pv_mw * cluster_data.get('pv_capacity_factor', 0.211) * pv_deg
        
        # Reducción de pérdidas
        loss_reduction_mw = avg_injection_mw * loss_sensitivity
        loss_reduction_mwh = loss_reduction_mw * 8760
        
        # Valor económico
        upstream_cost = self.params['upstream_energy_cost'] * inflation
        return loss_reduction_mwh * upstream_cost
    
    def _calculate_q_night_value(self, cluster_data: Dict, q_mvar: float,
                               inflation: float) -> float:
        """Calcula valor de compensación reactiva nocturna"""
        if q_mvar <= 0:
            return 0
        
        # Opción 1: Evitar penalizaciones por bajo factor de potencia
        reactive_penalty = self.params['reactive_penalty'] * inflation
        penalty_avoided = q_mvar * reactive_penalty * 12
        
        # Opción 2: Valor equivalente STATCOM
        statcom_capex_per_mvar = 50000  # USD/MVAr
        statcom_lifetime = 15  # años
        statcom_annual_value = statcom_capex_per_mvar / statcom_lifetime
        statcom_equivalent = q_mvar * statcom_annual_value
        
        # Usar el mayor valor
        return max(penalty_avoided, statcom_equivalent)
    
    def _calculate_capex_deferral(self, cluster_data: Dict, pv_mw: float,
                                year: int) -> float:
        """Calcula valor de diferimiento de inversiones en red"""
        # Capacidad de upgrade evitado o diferido
        upgrade_mva = cluster_data.get('deferred_upgrade_mva', 0)
        if upgrade_mva <= 0:
            return 0
        
        # Años de diferimiento (simplificado)
        deferral_years = min(5, pv_mw / upgrade_mva * 10)
        
        # Valor solo en los primeros años
        if year <= deferral_years:
            upgrade_cost = cluster_data.get('upgrade_cost_usd', 100000)
            discount_factor = (1 + self.params['discount_rate']) ** deferral_years
            return upgrade_cost / discount_factor / deferral_years
        
        return 0
    
    def _calculate_penalty_avoidance(self, cluster_data: Dict, pv_mw: float,
                                   q_mvar: float, inflation: float) -> float:
        """Calcula penalizaciones evitadas por mejora de calidad"""
        # Penalizaciones históricas anuales
        historical_penalties = cluster_data.get('annual_penalties_usd', 0)
        
        # Factor de mejora (simplificado)
        improvement_factor = min(0.8, (pv_mw + q_mvar * 0.5) / 
                               cluster_data.get('peak_demand_mw', 10))
        
        return historical_penalties * improvement_factor * inflation
    
    def _calculate_opex(self, capex: Dict, inflation: float) -> float:
        """Calcula OPEX anual"""
        pv_opex = capex.get('pv', 0) * self.params['pv_opex_rate']
        bess_opex = capex.get('bess', 0) * self.params['bess_opex_rate']
        
        return (pv_opex + bess_opex) * inflation
    
    def _estimate_self_consumption_ratio(self, cluster_data: Dict,
                                       pv_mw: float, bess_mwh: float) -> float:
        """
        Estima ratio de autoconsumo basado en perfiles de carga y generación.
        """
        # Ratio base según tipo de carga predominante
        load_type = cluster_data.get('dominant_load_type', 'mixed')
        base_ratios = {
            'residential': 0.3,  # Bajo: pico nocturno
            'commercial': 0.7,   # Alto: pico diurno
            'industrial': 0.6,   # Medio: carga constante
            'rural': 0.4,        # Bajo-medio
            'mixed': 0.5         # Promedio
        }
        
        base_ratio = base_ratios.get(load_type, 0.5)
        
        # Ajustar por tamaño relativo PV vs demanda
        pv_to_demand = pv_mw / cluster_data.get('peak_demand_mw', pv_mw)
        if pv_to_demand > 1:
            # Penalizar sobredimensionamiento
            base_ratio *= 1 / pv_to_demand
        
        # Bonus por BESS (aumenta autoconsumo)
        if bess_mwh > 0:
            bess_bonus = min(0.2, bess_mwh / (pv_mw * 4))  # Hasta 20% extra
            base_ratio += bess_bonus
        
        return min(0.95, base_ratio)  # Máximo 95% autoconsumo
    
    def calculate_financial_metrics(self, cash_flows: List[IntegratedCashFlow],
                                  initial_capex: float) -> Dict:
        """
        Calcula métricas financieras del proyecto.
        
        Args:
            cash_flows: Lista de flujos de caja
            initial_capex: CAPEX inicial total
            
        Returns:
            Diccionario con NPV, IRR, Payback, B/C ratio
        """
        # Preparar flujos para cálculo
        years = [0] + [cf.year for cf in cash_flows]
        flows = [-initial_capex] + [cf.total_flow for cf in cash_flows]
        
        # NPV
        discount_factors = [(1 + self.params['discount_rate']) ** -t for t in range(len(years))]
        npv = sum(flow * df for flow, df in zip(flows, discount_factors))
        
        # IRR
        irr = self._calculate_irr(flows)
        
        # Payback simple
        cumulative = 0
        payback = None
        for i, flow in enumerate(flows[1:], 1):  # Skip initial investment
            cumulative += flow
            if cumulative >= initial_capex:
                payback = i
                break
        
        # Benefit/Cost ratio
        pv_benefits = sum(cf.total_flow * df for cf, df in 
                         zip(cash_flows, discount_factors[1:]))
        bc_ratio = pv_benefits / initial_capex if initial_capex > 0 else 0
        
        # LCOE (si aplica)
        total_energy_mwh = sum(
            cf.self_consumption_savings / self.params['electricity_price'] / 
            ((1 + self.params['inflation_rate']) ** (cf.year - 1))
            for cf in cash_flows
        )
        lcoe = (initial_capex + sum(cf.opex * df for cf, df in 
                zip(cash_flows, discount_factors[1:]))) / total_energy_mwh if total_energy_mwh > 0 else 0
        
        return {
            'npv_usd': npv,
            'irr_percent': irr * 100 if irr else None,
            'payback_years': payback,
            'bc_ratio': bc_ratio,
            'lcoe_usd_mwh': lcoe
        }
    
    def _calculate_irr(self, cash_flows: List[float], max_iterations: int = 100) -> Optional[float]:
        """Calcula TIR usando método Newton-Raphson"""
        if len(cash_flows) < 2:
            return None
        
        # Estimación inicial
        irr = 0.1
        
        for _ in range(max_iterations):
            # NPV y su derivada
            npv = 0
            dnpv = 0
            
            for t, cf in enumerate(cash_flows):
                npv += cf / (1 + irr) ** t
                if t > 0:
                    dnpv -= t * cf / (1 + irr) ** (t + 1)
            
            # Actualizar estimación
            if abs(dnpv) < 1e-10:
                break
                
            irr_new = irr - npv / dnpv
            
            # Verificar convergencia
            if abs(irr_new - irr) < 1e-6:
                return irr_new if -1 < irr_new < 10 else None
                
            irr = irr_new
        
        return None