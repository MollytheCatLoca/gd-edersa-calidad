"""
Modelo de Beneficios en Red para PSFV Multipropósito
==================================================
Calcula y valoriza los beneficios que el PSFV aporta a la red
de distribución más allá de la generación de energía.

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
class NetworkBenefit:
    """Beneficio individual en la red"""
    type: str  # loss_reduction, voltage_support, deferral, etc.
    value_usd: float
    technical_impact: float  # Magnitud técnica (MW, MVAr, %, etc.)
    affected_users: int
    description: str


class NetworkBenefitsCalculator:
    """
    Calculador de beneficios en red para proyectos de generación distribuida.
    Incluye reducción de pérdidas, soporte de tensión, diferimiento de inversiones
    y mejora de índices de calidad.
    """
    
    def __init__(self, network_params: Optional[Dict] = None):
        """
        Inicializa el calculador con parámetros de red.
        
        Args:
            network_params: Parámetros técnicos de la red (si None, usa ConfigLoader)
        """
        if network_params is None:
            # Cargar desde configuración centralizada
            config = get_config()
            self.params = config.get_network_params()
        else:
            self.params = network_params
            
        logger.info("Calculador de beneficios en red inicializado")
    
    def calculate_all_benefits(self,
                             cluster_data: Dict,
                             pv_mw: float,
                             bess_mwh: float,
                             q_night_mvar: float,
                             simulation_years: int = 20) -> Dict[str, NetworkBenefit]:
        """
        Calcula todos los beneficios en red para una configuración dada.
        
        Args:
            cluster_data: Datos del cluster
            pv_mw: Capacidad PV en MW
            bess_mwh: Capacidad BESS en MWh
            q_night_mvar: Capacidad reactiva nocturna
            simulation_years: Años de análisis
            
        Returns:
            Diccionario con beneficios calculados
        """
        benefits = {}
        
        # 1. Reducción de pérdidas técnicas
        benefits['loss_reduction'] = self.calculate_loss_reduction(
            cluster_data, pv_mw, simulation_years
        )
        
        # 2. Soporte de tensión (día y noche)
        benefits['voltage_support'] = self.calculate_voltage_support(
            cluster_data, pv_mw, q_night_mvar, simulation_years
        )
        
        # 3. Mejora factor de potencia
        benefits['power_factor'] = self.calculate_power_factor_improvement(
            cluster_data, pv_mw, q_night_mvar, simulation_years
        )
        
        # 4. Diferimiento de inversiones
        benefits['investment_deferral'] = self.calculate_investment_deferral(
            cluster_data, pv_mw, bess_mwh
        )
        
        # 5. Reducción de congestión
        benefits['congestion_relief'] = self.calculate_congestion_relief(
            cluster_data, pv_mw, bess_mwh, simulation_years
        )
        
        # 6. Mejora confiabilidad
        benefits['reliability'] = self.calculate_reliability_improvement(
            cluster_data, pv_mw, bess_mwh, simulation_years
        )
        
        return benefits
    
    def calculate_loss_reduction(self, cluster_data: Dict, pv_mw: float,
                               years: int) -> NetworkBenefit:
        """
        Calcula beneficio por reducción de pérdidas técnicas.
        """
        # Impedancia equivalente del cluster
        r_eq = cluster_data.get('equivalent_resistance_pu', 0.05)
        
        # Flujo de potencia base (sin GD)
        base_flow_mw = cluster_data.get('peak_demand_mw', 10)
        
        # Pérdidas base: I²R = (P²+Q²)/V² * R
        base_losses_mw = (base_flow_mw ** 2) * r_eq
        
        # Flujo con GD (reducido)
        net_flow_mw = max(0, base_flow_mw - pv_mw * 0.7)  # Factor de coincidencia
        new_losses_mw = (net_flow_mw ** 2) * r_eq
        
        # Reducción de pérdidas
        loss_reduction_mw = base_losses_mw - new_losses_mw
        annual_energy_saved_mwh = loss_reduction_mw * 8760 * 0.4  # Factor de carga
        
        # Valorización
        energy_cost = self.params['energy_cost_upstream_usd_mwh']
        annual_value = annual_energy_saved_mwh * energy_cost
        total_value = annual_value * years * 0.8  # Factor VP simplificado
        
        return NetworkBenefit(
            type='loss_reduction',
            value_usd=total_value,
            technical_impact=loss_reduction_mw,
            affected_users=cluster_data.get('total_users', 0),
            description=f"Reducción de {loss_reduction_mw:.2f} MW en pérdidas técnicas"
        )
    
    def calculate_voltage_support(self, cluster_data: Dict, pv_mw: float,
                                q_night_mvar: float, years: int) -> NetworkBenefit:
        """
        Calcula beneficio por soporte de tensión (24 horas).
        """
        # Sensibilidad de tensión
        x_eq = cluster_data.get('equivalent_reactance_pu', 0.1)
        v_sensitivity = self.params['voltage_sensitivity_kv_mvar']
        
        # Mejora de tensión diurna (por P)
        delta_v_day = pv_mw * x_eq * 0.3  # pu
        
        # Mejora de tensión nocturna (por Q)
        delta_v_night = q_night_mvar * v_sensitivity / self.params['voltage_nominal_kv']
        
        # Horas con violación evitadas
        current_violations_h = cluster_data.get('voltage_violation_hours', 500)
        
        # Reducción de violaciones
        day_improvement = min(0.7, delta_v_day / 0.05)  # 70% máx
        night_improvement = min(0.9, delta_v_night / 0.05)  # 90% máx
        
        # Promedio ponderado (10h día, 14h noche)
        avg_improvement = (day_improvement * 10 + night_improvement * 14) / 24
        
        violations_avoided_h = current_violations_h * avg_improvement
        
        # Valorización
        violation_cost = self.params['voltage_violation_cost_usd_hour']
        annual_value = violations_avoided_h * violation_cost
        total_value = annual_value * years * 0.8
        
        # Usuarios beneficiados
        affected_users = int(cluster_data.get('critical_users', 0) * avg_improvement)
        
        return NetworkBenefit(
            type='voltage_support',
            value_usd=total_value,
            technical_impact=avg_improvement * 100,  # % mejora
            affected_users=affected_users,
            description=f"Mejora de tensión {avg_improvement*100:.1f}% (24h)"
        )
    
    def calculate_power_factor_improvement(self, cluster_data: Dict, pv_mw: float,
                                         q_night_mvar: float, years: int) -> NetworkBenefit:
        """
        Calcula beneficio por mejora de factor de potencia.
        """
        # Factor de potencia actual
        current_pf = cluster_data.get('power_factor', self.params['base_power_factor'])
        
        # Potencia reactiva actual
        p_demand = cluster_data.get('peak_demand_mw', 10)
        current_q = p_demand * np.tan(np.arccos(current_pf))
        
        # Compensación reactiva disponible
        # Día: inversor PV puede dar algo de Q
        q_day = pv_mw * 0.3  # 30% capacidad para Q
        # Noche: Q dedicado
        q_total_available = (q_day * 10 + q_night_mvar * 14) / 24
        
        # Nueva Q neta
        new_q = max(0, current_q - q_total_available)
        new_pf = np.cos(np.arctan(new_q / p_demand))
        
        # Beneficios
        benefits_list = []
        
        # 1. Evitar penalizaciones por bajo FP
        if current_pf < self.params['target_power_factor']:
            pf_penalty_avoided = p_demand * 1000 * 5 * 12  # USD/año estimado
            benefits_list.append(pf_penalty_avoided)
        
        # 2. Reducción de pérdidas por reactivo
        q_loss_reduction = (current_q - new_q) * self.params['mvar_to_mw_loss_factor']
        q_loss_value = q_loss_reduction * 8760 * 0.5 * self.params['energy_cost_upstream_usd_mwh']
        benefits_list.append(q_loss_value)
        
        # 3. Liberación de capacidad en transformadores
        capacity_freed_mva = p_demand * (1/current_pf - 1/new_pf)
        capacity_value = capacity_freed_mva * self.params['transformer_cost_usd_mva'] * 0.1
        benefits_list.append(capacity_value)
        
        annual_value = sum(benefits_list)
        total_value = annual_value * years * 0.8
        
        return NetworkBenefit(
            type='power_factor',
            value_usd=total_value,
            technical_impact=new_pf - current_pf,
            affected_users=cluster_data.get('total_users', 0),
            description=f"Mejora FP de {current_pf:.3f} a {new_pf:.3f}"
        )
    
    def calculate_investment_deferral(self, cluster_data: Dict, pv_mw: float,
                                    bess_mwh: float) -> NetworkBenefit:
        """
        Calcula beneficio por diferimiento de inversiones en red.
        """
        # Capacidad actual y margen
        transformer_capacity_mva = cluster_data.get('transformer_capacity_mva', 20)
        current_load_mva = cluster_data.get('peak_demand_mw', 10) / 0.85  # Con FP
        margin_mva = transformer_capacity_mva - current_load_mva
        
        # Crecimiento de carga
        growth_rate = cluster_data.get('load_growth_rate', 0.03)  # 3% anual
        
        # Años hasta necesitar upgrade (sin GD)
        if margin_mva > 0 and growth_rate > 0:
            years_to_upgrade_base = np.log(1 + margin_mva/current_load_mva) / np.log(1 + growth_rate)
        else:
            years_to_upgrade_base = 0
        
        # Reducción de carga neta por GD
        load_reduction_mva = pv_mw * 0.7 / 0.85  # Factor coincidencia y FP
        if bess_mwh > 0:
            load_reduction_mva += (bess_mwh / 4) * 0.8 / 0.85  # BESS contribution
        
        # Nuevos años hasta upgrade
        new_margin_mva = margin_mva + load_reduction_mva
        if new_margin_mva > 0 and growth_rate > 0:
            years_to_upgrade_gd = np.log(1 + new_margin_mva/current_load_mva) / np.log(1 + growth_rate)
        else:
            years_to_upgrade_gd = 20  # Máximo horizonte
        
        # Años diferidos
        years_deferred = years_to_upgrade_gd - years_to_upgrade_base
        
        # Valor del diferimiento
        upgrade_cost = cluster_data.get('upgrade_cost_usd', 
                                      transformer_capacity_mva * self.params['transformer_cost_usd_mva'])
        
        # Valor presente del diferimiento
        if years_deferred > 0:
            discount_rate = 0.12
            deferral_value = upgrade_cost * (1 - (1 + discount_rate)**(-years_deferred))
        else:
            deferral_value = 0
        
        return NetworkBenefit(
            type='investment_deferral',
            value_usd=deferral_value,
            technical_impact=years_deferred,
            affected_users=cluster_data.get('total_users', 0),
            description=f"Diferimiento de {years_deferred:.1f} años en upgrade"
        )
    
    def calculate_congestion_relief(self, cluster_data: Dict, pv_mw: float,
                                  bess_mwh: float, years: int) -> NetworkBenefit:
        """
        Calcula beneficio por alivio de congestión en líneas.
        """
        # Nivel de congestión actual
        line_loading = cluster_data.get('max_line_loading_percent', 80)
        
        if line_loading < 90:
            # No hay congestión significativa
            return NetworkBenefit(
                type='congestion_relief',
                value_usd=0,
                technical_impact=0,
                affected_users=0,
                description="Sin congestión significativa"
            )
        
        # Horas de congestión al año
        congestion_hours = cluster_data.get('congestion_hours', 200)
        
        # Reducción de flujo por GD
        flow_reduction_percent = min(30, pv_mw / cluster_data.get('peak_demand_mw', 10) * 100)
        
        # Nueva carga de línea
        new_loading = line_loading * (1 - flow_reduction_percent/100)
        
        # Horas de congestión evitadas
        if new_loading < 90:
            congestion_avoided = congestion_hours
        else:
            congestion_avoided = congestion_hours * (line_loading - new_loading) / (line_loading - 90)
        
        # Costo de congestión (pérdidas extras + riesgo)
        congestion_cost_hour = cluster_data.get('peak_demand_mw', 10) * 50  # USD/h
        
        annual_value = congestion_avoided * congestion_cost_hour
        total_value = annual_value * years * 0.8
        
        return NetworkBenefit(
            type='congestion_relief',
            value_usd=total_value,
            technical_impact=flow_reduction_percent,
            affected_users=cluster_data.get('total_users', 0),
            description=f"Reducción de {flow_reduction_percent:.1f}% en flujo pico"
        )
    
    def calculate_reliability_improvement(self, cluster_data: Dict, pv_mw: float,
                                        bess_mwh: float, years: int) -> NetworkBenefit:
        """
        Calcula beneficio por mejora en confiabilidad (SAIDI/SAIFI).
        """
        # Índices actuales
        saidi_current = cluster_data.get('saidi_minutes', 120)  # min/año
        saifi_current = cluster_data.get('saifi_interruptions', 2)  # int/año
        
        # Mejora por respaldo local (solo si hay BESS)
        if bess_mwh > 0:
            # BESS puede cubrir interrupciones cortas
            bess_backup_hours = bess_mwh / (cluster_data.get('peak_demand_mw', 10) * 0.5)
            
            # Reducción SAIDI (interrupciones < backup time)
            short_interruptions_ratio = 0.6  # 60% son < 2 horas
            saidi_reduction = saidi_current * short_interruptions_ratio * min(1, bess_backup_hours/2)
            
            # SAIFI no cambia mucho (mismo número de eventos)
            saifi_reduction = 0
        else:
            saidi_reduction = saidi_current * 0.1  # 10% mejora por GD
            saifi_reduction = 0
        
        # Valorización
        ens_mwh = saidi_reduction / 60 * cluster_data.get('avg_demand_mw', 5)
        ens_value = ens_mwh * self.params['ens_cost_usd_mwh']
        
        # Costo regulatorio evitado
        regulatory_cost = saidi_reduction * self.params['saidi_cost_usd_minute']
        
        annual_value = ens_value + regulatory_cost
        total_value = annual_value * years * 0.8
        
        users_benefited = int(cluster_data.get('total_users', 0) * saidi_reduction / saidi_current)
        
        return NetworkBenefit(
            type='reliability',
            value_usd=total_value,
            technical_impact=saidi_reduction,
            affected_users=users_benefited,
            description=f"Reducción SAIDI de {saidi_reduction:.1f} min/año"
        )
    
    def aggregate_benefits(self, benefits: Dict[str, NetworkBenefit]) -> Dict:
        """
        Agrega todos los beneficios en métricas resumen.
        """
        total_value = sum(b.value_usd for b in benefits.values())
        total_users = max(b.affected_users for b in benefits.values())
        
        # Desglose por categoría
        categories = {
            'technical': ['loss_reduction', 'congestion_relief'],
            'quality': ['voltage_support', 'power_factor', 'reliability'],
            'economic': ['investment_deferral']
        }
        
        breakdown = {}
        for category, types in categories.items():
            breakdown[category] = sum(
                benefits[t].value_usd for t in types if t in benefits
            )
        
        return {
            'total_value_usd': total_value,
            'value_per_user_usd': total_value / total_users if total_users > 0 else 0,
            'affected_users': total_users,
            'breakdown': breakdown,
            'top_benefit': max(benefits.items(), key=lambda x: x[1].value_usd)[0]
        }