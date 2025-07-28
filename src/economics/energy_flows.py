"""
Módulo de Cálculo de Flujos de Energía Solar
============================================

Funciones independientes y reutilizables para calcular flujos económicos
de sistemas fotovoltaicos. Diseñado para calibración, testing y uso en ML.

Autor: Asistente Claude
Fecha: Julio 2025
"""

from typing import Dict, Tuple
import logging
from .capex_scale import calculate_pv_capex_per_mw, calculate_pv_total_capex

logger = logging.getLogger(__name__)


def calculate_pv_generation(pv_mw: float, 
                          capacity_factor: float = 0.22,
                          hours_per_year: int = 8760) -> Tuple[float, float]:
    """
    Calcula la generación anual de un sistema PV.
    
    Args:
        pv_mw: Capacidad instalada en MW
        capacity_factor: Factor de planta (default: 0.22 para Argentina)
        hours_per_year: Horas por año (default: 8760)
    
    Returns:
        Tuple[float, float]: (generación_mwh, generación_gwh)
    
    Example:
        >>> mwh, gwh = calculate_pv_generation(100, 0.22)
        >>> print(f"Generación: {mwh:,.0f} MWh/año ({gwh:.2f} GWh/año)")
    """
    generation_mwh = pv_mw * hours_per_year * capacity_factor
    generation_gwh = generation_mwh / 1000
    
    logger.debug(f"PV Generation: {pv_mw} MW × {hours_per_year} h × {capacity_factor} = {generation_mwh:,.0f} MWh/año")
    
    return generation_mwh, generation_gwh


def calculate_pv_self_consumption(generation_mwh: float,
                                self_consumption_ratio: float,
                                electricity_price: float) -> float:
    """
    Calcula el valor económico del autoconsumo solar.
    
    Args:
        generation_mwh: Generación anual en MWh
        self_consumption_ratio: Fracción autoconsumida (0-1)
        electricity_price: Precio de la electricidad (USD/MWh)
    
    Returns:
        float: Valor del autoconsumo en USD/año
    
    Example:
        >>> value = calculate_pv_self_consumption(100000, 0.7, 75)
        >>> print(f"Autoconsumo: ${value/1e6:.2f}M/año")
    """
    self_consumption_mwh = generation_mwh * self_consumption_ratio
    value = self_consumption_mwh * electricity_price
    
    logger.debug(f"Self consumption: {self_consumption_mwh:,.0f} MWh × ${electricity_price}/MWh = ${value:,.0f}/año")
    
    return value


def calculate_pv_exports(generation_mwh: float,
                        export_ratio: float,
                        export_price: float) -> float:
    """
    Calcula el valor económico de las exportaciones a la red.
    
    Args:
        generation_mwh: Generación anual en MWh
        export_ratio: Fracción exportada (0-1)
        export_price: Precio de exportación (USD/MWh)
    
    Returns:
        float: Valor de las exportaciones en USD/año
    
    Example:
        >>> value = calculate_pv_exports(100000, 0.3, 70)
        >>> print(f"Exportación: ${value/1e6:.2f}M/año")
    """
    export_mwh = generation_mwh * export_ratio
    value = export_mwh * export_price
    
    logger.debug(f"Exports: {export_mwh:,.0f} MWh × ${export_price}/MWh = ${value:,.0f}/año")
    
    return value


def calculate_pv_total_flows(generation_mwh: float,
                           self_consumption_ratio: float,
                           electricity_price: float,
                           export_price: float) -> Dict[str, float]:
    """
    Calcula todos los flujos económicos del sistema PV.
    
    Args:
        generation_mwh: Generación anual en MWh
        self_consumption_ratio: Fracción autoconsumida (0-1)
        electricity_price: Precio de la electricidad (USD/MWh)
        export_price: Precio de exportación (USD/MWh)
    
    Returns:
        Dict con keys: 'self_consumption', 'exports', 'total'
    
    Example:
        >>> flows = calculate_pv_total_flows(100000, 0.7, 75, 70)
        >>> print(f"Total PV: ${flows['total']/1e6:.2f}M/año")
    """
    export_ratio = 1 - self_consumption_ratio
    
    self_consumption_value = calculate_pv_self_consumption(
        generation_mwh, self_consumption_ratio, electricity_price
    )
    
    export_value = calculate_pv_exports(
        generation_mwh, export_ratio, export_price
    )
    
    total_value = self_consumption_value + export_value
    
    flows = {
        'self_consumption': self_consumption_value,
        'exports': export_value,
        'total': total_value
    }
    
    logger.info(f"PV Flows: Autoconsumo ${self_consumption_value/1e6:.2f}M + "
                f"Exportación ${export_value/1e6:.2f}M = ${total_value/1e6:.2f}M/año")
    
    return flows


def calculate_pv_capacity_from_demand(peak_demand_mw: float,
                                    pv_ratio: float) -> float:
    """
    Calcula la capacidad PV basada en la demanda pico.
    
    Args:
        peak_demand_mw: Demanda pico en MW
        pv_ratio: Ratio PV/Demanda (ej: 1.2 = 120% de la demanda)
    
    Returns:
        float: Capacidad PV en MW
    """
    pv_mw = peak_demand_mw * pv_ratio
    logger.debug(f"PV Capacity: {peak_demand_mw} MW × {pv_ratio} = {pv_mw} MW")
    return pv_mw


def calculate_bess_capacity(pv_mw: float,
                          bess_hours: float) -> float:
    """
    Calcula la capacidad BESS basada en PV y horas de almacenamiento.
    
    Args:
        pv_mw: Capacidad PV en MW
        bess_hours: Horas de almacenamiento a potencia nominal
    
    Returns:
        float: Capacidad BESS en MWh
    """
    bess_mwh = pv_mw * bess_hours
    logger.debug(f"BESS Capacity: {pv_mw} MW × {bess_hours} h = {bess_mwh} MWh")
    return bess_mwh


def calculate_reactive_capacity(pv_mw: float,
                              q_ratio: float) -> float:
    """
    Calcula la capacidad de compensación reactiva.
    
    Args:
        pv_mw: Capacidad PV en MW
        q_ratio: Ratio Q/PV (ej: 0.3 = 30% de la capacidad PV)
    
    Returns:
        float: Capacidad reactiva en MVAr
    """
    q_mvar = pv_mw * q_ratio
    logger.debug(f"Reactive Capacity: {pv_mw} MW × {q_ratio} = {q_mvar} MVAr")
    return q_mvar


# Funciones de validación
def validate_capacity_factor(cf: float) -> bool:
    """Valida que el factor de capacidad esté en rango razonable."""
    return 0.15 <= cf <= 0.30


def validate_self_consumption_ratio(ratio: float) -> bool:
    """Valida que el ratio de autoconsumo esté entre 0 y 1."""
    return 0.0 <= ratio <= 1.0


def validate_prices(electricity_price: float, export_price: float) -> bool:
    """Valida que los precios sean razonables."""
    return (electricity_price > 0 and 
            export_price > 0 and 
            export_price <= electricity_price * 1.2)  # Export no más de 20% sobre retail


def calculate_pv_capex(pv_mw: float, 
                      bos_factor: float = 0.15,
                      use_scale: bool = True) -> Dict[str, float]:
    """
    Calcula el CAPEX total del proyecto PV con economías de escala.
    
    Args:
        pv_mw: Capacidad del proyecto en MW
        bos_factor: Factor de Balance of System (default: 0.15)
        use_scale: Si usar economías de escala (default: True)
        
    Returns:
        Dict con desglose de CAPEX
        
    Example:
        >>> capex = calculate_pv_capex(50)
        >>> print(f"50 MW: ${capex['total']/1e6:.2f}M (${capex['per_mw']:,.0f}/MW)")
    """
    if use_scale:
        capex_per_mw = calculate_pv_capex_per_mw(pv_mw)
        equipment, bos, total = calculate_pv_total_capex(pv_mw, bos_factor)
    else:
        # Sin economías de escala - usar valor fijo
        capex_per_mw = 850_000  # Máximo para 1 MW
        equipment = pv_mw * capex_per_mw
        bos = equipment * bos_factor
        total = equipment + bos
    
    return {
        'per_mw': capex_per_mw,
        'equipment': equipment,
        'bos': bos,
        'total': total,
        'size_mw': pv_mw
    }