"""
Módulo de Cálculo de Beneficios de Red (Versión Modular)
========================================================

Funciones independientes y reutilizables para calcular beneficios económicos
de la integración de GD en la red eléctrica. Diseñado para calibración,
testing y uso en ML.

Autor: Asistente Claude
Fecha: Julio 2025
"""

from typing import Dict, Tuple, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


def calculate_loss_reduction(pv_mw: float,
                           base_losses_mw: float,
                           loss_sensitivity: float = 0.05,
                           electricity_price: float = 75,
                           loss_price_multiplier: float = 1.0) -> Tuple[float, float]:
    """
    Calcula la reducción de pérdidas técnicas por inyección de GD.
    
    Args:
        pv_mw: Capacidad de generación distribuida en MW
        base_losses_mw: Pérdidas base del sistema en MW
        loss_sensitivity: Sensibilidad de pérdidas (ΔLoss/ΔGen)
        electricity_price: Precio base de electricidad (USD/MWh)
        loss_price_multiplier: Multiplicador para valorizar pérdidas
    
    Returns:
        Tuple[float, float]: (reducción_mw, valor_anual_usd)
    
    Example:
        >>> loss_mw, value = calculate_loss_reduction(10, 2, 0.03, 75, 1.2)
        >>> print(f"Reducción: {loss_mw:.2f} MW, valor ${value/1e3:.0f}k/año")
    """
    # Reducción de pérdidas con factor de sensibilidad
    loss_reduction_mw = pv_mw * loss_sensitivity
    
    # Limitar a máximo 50% de pérdidas base
    loss_reduction_mw = min(loss_reduction_mw, base_losses_mw * 0.5)
    
    # Valor económico: MWh ahorrados × precio × multiplicador × horas
    hours_per_year = 8760
    loss_price = electricity_price * loss_price_multiplier
    value_annual = loss_reduction_mw * hours_per_year * loss_price
    
    logger.debug(f"Loss reduction: {loss_reduction_mw:.3f} MW × {hours_per_year}h × ${loss_price:.0f}/MWh = ${value_annual/1e3:.0f}k/año")
    
    return loss_reduction_mw, value_annual


def calculate_reactive_support_value(q_mvar: float,
                                   pf_penalty_usd_kvar_month: float = 4.0,
                                   months_per_year: int = 12) -> float:
    """
    Calcula el valor económico del soporte reactivo (Q at Night).
    
    Args:
        q_mvar: Capacidad de compensación reactiva en MVAr
        pf_penalty_usd_kvar_month: Penalización por kVAr-mes
        months_per_year: Meses por año
    
    Returns:
        float: Valor anual del soporte reactivo en USD/año
    
    Example:
        >>> value = calculate_reactive_support_value(30, 4.0)
        >>> print(f"Q support: ${value/1e6:.2f}M/año")
    """
    # Convertir MVAr a kVAr
    q_kvar = q_mvar * 1000
    
    # Valor = kVAr × penalty × meses
    value_annual = q_kvar * pf_penalty_usd_kvar_month * months_per_year
    
    logger.debug(f"Reactive support: {q_mvar} MVAr = ${value_annual/1e3:.0f}k/año")
    
    return value_annual


def calculate_voltage_support_value(pv_mw: float,
                                  q_mvar: float,
                                  voltage_improvement_pu: float = 0.02,
                                  violation_hours_year: float = 500,
                                  violation_cost_hour: float = 500) -> float:
    """
    Calcula el valor de mejora de tensión y reducción de violaciones.
    
    Args:
        pv_mw: Capacidad activa en MW
        q_mvar: Capacidad reactiva en MVAr
        voltage_improvement_pu: Mejora esperada de tensión (pu)
        violation_hours_year: Horas de violación actuales
        violation_cost_hour: Costo por hora de violación
    
    Returns:
        float: Valor anual por soporte de tensión
    """
    # Factor de mejora combinado P+Q
    improvement_factor = (pv_mw + 0.7 * q_mvar) / (pv_mw + q_mvar + 1e-6)
    
    # Reducción de horas de violación
    hours_reduced = violation_hours_year * voltage_improvement_pu * 50 * improvement_factor
    hours_reduced = min(hours_reduced, violation_hours_year * 0.8)  # Max 80% reducción
    
    value_annual = hours_reduced * violation_cost_hour
    
    logger.debug(f"Voltage support: {hours_reduced:.0f} horas × ${violation_cost_hour} = ${value_annual/1e3:.0f}k/año")
    
    return value_annual


def calculate_reliability_improvement(pv_mw: float,
                                    bess_mwh: float,
                                    users_affected: int,
                                    saidi_minutes: float = 120,
                                    saidi_cost_minute: float = 50) -> float:
    """
    Calcula el valor de mejora en confiabilidad (reducción SAIDI).
    
    Args:
        pv_mw: Capacidad PV en MW
        bess_mwh: Capacidad BESS en MWh
        users_affected: Usuarios en la zona
        saidi_minutes: SAIDI actual (minutos/año)
        saidi_cost_minute: Costo por minuto SAIDI
    
    Returns:
        float: Valor anual por mejora de confiabilidad
    """
    # Factor de mejora por generación local
    has_bess = bess_mwh > 0
    improvement_factor = 0.15 if has_bess else 0.08  # 15% con BESS, 8% sin BESS
    
    # Reducción SAIDI
    saidi_reduction = saidi_minutes * improvement_factor
    
    # Valor económico
    value_annual = saidi_reduction * saidi_cost_minute * (users_affected / 1000)  # Por cada 1000 usuarios
    
    logger.debug(f"Reliability: {saidi_reduction:.1f} min × ${saidi_cost_minute} × {users_affected/1000:.1f}k users = ${value_annual/1e3:.0f}k/año")
    
    return value_annual


def calculate_demand_charge_reduction(pv_mw: float,
                                    coincidence_factor: float = 0.7,
                                    demand_charge_usd_kw_month: float = 12.0,
                                    months_per_year: int = 12) -> float:
    """
    Calcula la reducción en cargos por demanda máxima.
    
    Args:
        pv_mw: Capacidad PV en MW
        coincidence_factor: Factor de coincidencia con pico (0-1)
        demand_charge_usd_kw_month: Cargo por kW-mes
        months_per_year: Meses por año
    
    Returns:
        float: Valor anual por reducción de demanda
    """
    # Reducción efectiva de demanda
    demand_reduction_kw = pv_mw * 1000 * coincidence_factor
    
    # Valor anual
    value_annual = demand_reduction_kw * demand_charge_usd_kw_month * months_per_year
    
    logger.debug(f"Demand reduction: {demand_reduction_kw:.0f} kW × ${demand_charge_usd_kw_month} × {months_per_year} = ${value_annual/1e3:.0f}k/año")
    
    return value_annual


def calculate_transmission_deferral(pv_mw: float,
                                  upgrade_cost_usd_mw: float = 100000,
                                  deferral_years: float = 5,
                                  discount_rate: float = 0.10) -> float:
    """
    Calcula el valor de diferimiento de inversiones en transmisión.
    
    Args:
        pv_mw: Capacidad que difiere la inversión
        upgrade_cost_usd_mw: Costo de ampliación por MW
        deferral_years: Años de diferimiento
        discount_rate: Tasa de descuento
    
    Returns:
        float: Valor anual equivalente del diferimiento
    """
    # Inversión diferida
    deferred_investment = pv_mw * upgrade_cost_usd_mw
    
    # Valor presente del diferimiento
    pv_deferral = deferred_investment * (1 - 1/(1 + discount_rate)**deferral_years)
    
    # Anualizar el beneficio
    annuity_factor = discount_rate / (1 - (1 + discount_rate)**(-20))  # 20 años
    value_annual = pv_deferral * annuity_factor
    
    logger.debug(f"Transmission deferral: ${deferred_investment/1e6:.1f}M diferido {deferral_years} años = ${value_annual/1e3:.0f}k/año")
    
    return value_annual


def calculate_total_network_benefits(pv_mw: float,
                                   bess_mwh: float,
                                   q_mvar: float,
                                   network_params: Dict,
                                   network_need_factor: Optional[float] = None) -> Dict[str, float]:
    """
    Calcula todos los beneficios de red de forma integrada.
    
    Args:
        pv_mw: Capacidad PV en MW
        bess_mwh: Capacidad BESS en MWh
        q_mvar: Capacidad reactiva en MVAr
        network_params: Diccionario con parámetros de red
        network_need_factor: Factor de necesidad de red (0-1). Si None, no se aplica ajuste.
    
    Returns:
        Dict con desglose de beneficios por categoría
    
    Example:
        >>> params = {
        ...     'base_losses_mw': 2.0,
        ...     'users_affected': 5000,
        ...     'saidi_minutes': 120
        ... }
        >>> benefits = calculate_total_network_benefits(10, 5, 3, params, network_need_factor=0.5)
        >>> print(f"Total red (50% necesidad): ${benefits['total']/1e6:.2f}M/año")
    """
    benefits = {}
    
    # 1. Reducción de pérdidas
    loss_mw, loss_value = calculate_loss_reduction(
        pv_mw, 
        network_params.get('base_losses_mw', pv_mw * 0.08),
        network_params.get('loss_sensitivity', 0.05)
    )
    benefits['loss_reduction'] = loss_value
    
    # 2. Soporte reactivo
    benefits['reactive_support'] = calculate_reactive_support_value(
        q_mvar,
        network_params.get('pf_penalty_usd_kvar_month', 4.0)
    )
    
    # 3. Soporte de tensión
    benefits['voltage_support'] = calculate_voltage_support_value(
        pv_mw, q_mvar,
        network_params.get('voltage_improvement_pu', 0.02),
        network_params.get('violation_hours_year', 500),
        network_params.get('violation_cost_hour', 500)
    )
    
    # 4. Mejora de confiabilidad
    benefits['reliability'] = calculate_reliability_improvement(
        pv_mw, bess_mwh,
        network_params.get('users_affected', 1000),
        network_params.get('saidi_minutes', 120),
        network_params.get('saidi_cost_minute', 50)
    )
    
    # 5. Reducción cargo por demanda
    benefits['demand_reduction'] = calculate_demand_charge_reduction(
        pv_mw,
        network_params.get('coincidence_factor', 0.7),
        network_params.get('demand_charge_usd_kw_month', 12.0)
    )
    
    # 6. Diferimiento de inversiones
    if network_params.get('include_deferral', True):
        benefits['transmission_deferral'] = calculate_transmission_deferral(
            pv_mw,
            network_params.get('upgrade_cost_usd_mw', 100000),
            network_params.get('deferral_years', 5),
            network_params.get('discount_rate', 0.10)
        )
    else:
        benefits['transmission_deferral'] = 0
    
    # Total
    benefits['total'] = sum(benefits.values())
    
    # Aplicar factor de necesidad de red si se especifica
    if network_need_factor is not None:
        benefits = apply_network_need_factor(benefits, network_need_factor)
        logger.info(f"Network Benefits (ajustados por necesidad {network_need_factor:.0%}): ${benefits['total']/1e6:.2f}M/año")
    else:
        logger.info(f"Network Benefits: ${benefits['total']/1e6:.2f}M/año")
    
    logger.info(f"  - Pérdidas: ${benefits['loss_reduction']/1e6:.2f}M")
    logger.info(f"  - Reactivo: ${benefits['reactive_support']/1e6:.2f}M")
    logger.info(f"  - Tensión: ${benefits['voltage_support']/1e6:.2f}M")
    logger.info(f"  - Confiabilidad: ${benefits['reliability']/1e6:.2f}M")
    logger.info(f"  - Demanda: ${benefits['demand_reduction']/1e6:.2f}M")
    logger.info(f"  - Diferimiento: ${benefits['transmission_deferral']/1e6:.2f}M")
    
    return benefits


def estimate_network_parameters(cluster_data: Dict) -> Dict:
    """
    Estima parámetros de red basado en datos del cluster.
    
    Args:
        cluster_data: Datos del cluster (transformadores, usuarios, etc)
    
    Returns:
        Dict con parámetros estimados para cálculos
    """
    # Extraer datos básicos
    total_trafos = cluster_data.get('total_trafos', 100)
    total_users = cluster_data.get('affected_users', 5000)
    total_kva = cluster_data.get('total_kva', 10000)
    penalized_rate = cluster_data.get('penalized_rate', 0.3)
    
    # Estimar pérdidas base (8% de carga)
    load_factor = 0.6
    base_losses_mw = (total_kva / 1000) * load_factor * 0.08
    
    # Estimar parámetros de calidad
    violation_hours = 8760 * penalized_rate * 0.1  # 10% del tiempo penalizado
    saidi_minutes = 120 * (1 + penalized_rate)  # Peor SAIDI si más penalizados
    
    params = {
        'base_losses_mw': base_losses_mw,
        'users_affected': total_users,
        'loss_sensitivity': 0.05,
        'pf_penalty_usd_kvar_month': 4.0,
        'voltage_improvement_pu': 0.02,
        'violation_hours_year': violation_hours,
        'violation_cost_hour': 500,
        'saidi_minutes': saidi_minutes,
        'saidi_cost_minute': 50,
        'coincidence_factor': 0.7,
        'demand_charge_usd_kw_month': 12.0,
        'include_deferral': True,
        'upgrade_cost_usd_mw': 100000,
        'deferral_years': 5,
        'discount_rate': 0.10
    }
    
    logger.debug(f"Estimated network params for {total_trafos} trafos, {total_users} users")
    
    return params


# Funciones de validación
def validate_network_benefits(benefits: Dict[str, float]) -> bool:
    """Valida que los beneficios de red sean razonables."""
    total = benefits.get('total', 0)
    
    # Verificar que no sea negativo
    if total < 0:
        logger.warning("Beneficios de red negativos!")
        return False
    
    # Verificar que no sea excesivo (más de 50% del valor PV)
    # Esto requeriría conocer el valor PV, por ahora solo verificamos magnitud
    if total > 100e6:  # Más de $100M/año es sospechoso
        logger.warning(f"Beneficios de red muy altos: ${total/1e6:.1f}M/año")
        return False
    
    return True


def get_benefit_weights() -> Dict[str, float]:
    """
    Retorna pesos relativos de cada beneficio para análisis de sensibilidad.
    """
    return {
        'loss_reduction': 0.25,
        'reactive_support': 0.20,
        'voltage_support': 0.15,
        'reliability': 0.20,
        'demand_reduction': 0.15,
        'transmission_deferral': 0.05
    }


def apply_network_need_factor(benefits: Dict[str, float], 
                            network_need_factor: float) -> Dict[str, float]:
    """
    Aplica factor de necesidad de red a los beneficios.
    
    El factor refleja qué tan necesario es el proyecto para la red:
    - 1.0 (100%): Red con problemas críticos, necesita urgente el proyecto
    - 0.5 (50%): Red con problemas moderados
    - 0.0 (0%): Red sin problemas, no necesita el proyecto
    
    Args:
        benefits: Dict con beneficios calculados
        network_need_factor: Factor 0-1 (0=no necesita, 1=necesita mucho)
        
    Returns:
        Dict con beneficios ajustados por necesidad
        
    Example:
        >>> benefits = {'loss_reduction': 100000, 'total': 200000}
        >>> adjusted = apply_network_need_factor(benefits, 0.5)
        >>> print(f"Beneficios al 50%: ${adjusted['total']/1e3:.0f}k")
    """
    if not 0 <= network_need_factor <= 1:
        logger.warning(f"Network need factor {network_need_factor} fuera de rango [0,1], usando 1.0")
        network_need_factor = max(0, min(1, network_need_factor))
    
    adjusted_benefits = {}
    
    # Aplicar factor a cada beneficio individual
    for key, value in benefits.items():
        if key != 'total' and isinstance(value, (int, float)):
            adjusted_benefits[key] = value * network_need_factor
    
    # Recalcular total
    adjusted_benefits['total'] = sum(
        v for k, v in adjusted_benefits.items() 
        if k != 'total' and isinstance(v, (int, float))
    )
    
    logger.info(f"Network need factor {network_need_factor:.0%}: "
                f"Beneficios ajustados de ${benefits.get('total', 0)/1e6:.2f}M "
                f"a ${adjusted_benefits['total']/1e6:.2f}M/año")
    
    return adjusted_benefits