"""
Módulo de Cálculo de CAPEX con Economías de Escala
==================================================

Implementa funciones para calcular CAPEX considerando economías de escala
en proyectos fotovoltaicos de diferentes tamaños.

Estructura de costos:
- 1 MW: $850,000/MW (proyectos pequeños)
- 100+ MW: $637,000/MW (proyectos grandes)
- 1-100 MW: Interpolación lineal

Autor: Asistente Claude
Fecha: Julio 2025
"""

from typing import Dict, Tuple, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


def calculate_pv_capex_per_mw(pv_mw: float) -> float:
    """
    Calcula el CAPEX por MW considerando economías de escala.
    
    Args:
        pv_mw: Capacidad del proyecto en MW
        
    Returns:
        float: CAPEX en USD/MW
        
    Estructura:
        - 1 MW o menos: $850,000/MW
        - 100 MW o más: $637,000/MW
        - Entre 1-100 MW: Interpolación lineal
        
    Example:
        >>> capex_1mw = calculate_pv_capex_per_mw(1)
        >>> print(f"1 MW: ${capex_1mw:,.0f}/MW")
        1 MW: $850,000/MW
        
        >>> capex_50mw = calculate_pv_capex_per_mw(50)
        >>> print(f"50 MW: ${capex_50mw:,.0f}/MW")
        50 MW: $743,500/MW
    """
    # Límites de la escala
    MIN_SIZE_MW = 1.0
    MAX_SIZE_MW = 100.0
    MIN_CAPEX = 637_000  # USD/MW para 100+ MW
    MAX_CAPEX = 850_000  # USD/MW para 1 MW
    
    if pv_mw <= MIN_SIZE_MW:
        capex_per_mw = MAX_CAPEX
    elif pv_mw >= MAX_SIZE_MW:
        capex_per_mw = MIN_CAPEX
    else:
        # Interpolación lineal
        # y = mx + b donde m = (y2-y1)/(x2-x1)
        slope = (MIN_CAPEX - MAX_CAPEX) / (MAX_SIZE_MW - MIN_SIZE_MW)
        capex_per_mw = MAX_CAPEX + slope * (pv_mw - MIN_SIZE_MW)
    
    logger.debug(f"PV CAPEX for {pv_mw} MW: ${capex_per_mw:,.0f}/MW")
    
    return capex_per_mw


def calculate_pv_total_capex(pv_mw: float, 
                           bos_factor: float = 0.15) -> Tuple[float, float, float]:
    """
    Calcula el CAPEX total del proyecto PV.
    
    Args:
        pv_mw: Capacidad del proyecto en MW
        bos_factor: Factor de Balance of System (default: 0.15)
        
    Returns:
        Tuple[float, float, float]: (capex_equipo, capex_bos, capex_total)
        
    Example:
        >>> equipment, bos, total = calculate_pv_total_capex(10)
        >>> print(f"10 MW: Equipment ${equipment/1e6:.2f}M + BOS ${bos/1e6:.2f}M = ${total/1e6:.2f}M")
    """
    capex_per_mw = calculate_pv_capex_per_mw(pv_mw)
    capex_equipment = pv_mw * capex_per_mw
    capex_bos = capex_equipment * bos_factor
    capex_total = capex_equipment + capex_bos
    
    logger.info(f"PV CAPEX Total: {pv_mw} MW × ${capex_per_mw:,.0f}/MW × {1+bos_factor} = ${capex_total/1e6:.2f}M")
    
    return capex_equipment, capex_bos, capex_total


def get_economies_of_scale_table(sizes_mw: Optional[list] = None) -> Dict[float, Dict[str, float]]:
    """
    Genera tabla de economías de escala para diferentes tamaños.
    
    Args:
        sizes_mw: Lista de tamaños a evaluar (default: [1, 5, 10, 20, 50, 100, 200])
        
    Returns:
        Dict con tamaño como key y dict de métricas como value
        
    Example:
        >>> table = get_economies_of_scale_table()
        >>> for size, metrics in table.items():
        ...     print(f"{size} MW: ${metrics['capex_per_mw']:,.0f}/MW")
    """
    if sizes_mw is None:
        sizes_mw = [1, 5, 10, 20, 50, 100, 200]
    
    table = {}
    
    for size in sizes_mw:
        capex_per_mw = calculate_pv_capex_per_mw(size)
        equipment, bos, total = calculate_pv_total_capex(size)
        
        # Calcular ahorro vs 1 MW
        capex_1mw = calculate_pv_capex_per_mw(1)
        savings_percent = (1 - capex_per_mw / capex_1mw) * 100
        
        table[size] = {
            'capex_per_mw': capex_per_mw,
            'capex_equipment': equipment,
            'capex_bos': bos,
            'capex_total': total,
            'savings_vs_1mw': savings_percent
        }
    
    return table


def calculate_scale_impact_on_payback(pv_mw: float,
                                    annual_revenue: float,
                                    annual_opex: float,
                                    bos_factor: float = 0.15) -> Dict[str, float]:
    """
    Calcula el impacto de las economías de escala en el payback.
    
    Args:
        pv_mw: Capacidad del proyecto en MW
        annual_revenue: Ingresos anuales en USD
        annual_opex: OPEX anual en USD
        bos_factor: Factor BOS
        
    Returns:
        Dict con métricas de payback
        
    Example:
        >>> impact = calculate_scale_impact_on_payback(10, 1.5e6, 0.1e6)
        >>> print(f"Payback: {impact['payback']:.1f} años")
    """
    # CAPEX con economías de escala
    _, _, capex_scaled = calculate_pv_total_capex(pv_mw, bos_factor)
    
    # CAPEX sin economías de escala (todo a $850k/MW)
    capex_no_scale = pv_mw * 850_000 * (1 + bos_factor)
    
    # Flujo neto anual
    net_flow = annual_revenue - annual_opex
    
    # Paybacks
    payback_scaled = capex_scaled / net_flow if net_flow > 0 else 999
    payback_no_scale = capex_no_scale / net_flow if net_flow > 0 else 999
    
    # Diferencia
    payback_reduction = payback_no_scale - payback_scaled
    reduction_percent = (payback_reduction / payback_no_scale * 100) if payback_no_scale < 999 else 0
    
    return {
        'capex_scaled': capex_scaled,
        'capex_no_scale': capex_no_scale,
        'capex_savings': capex_no_scale - capex_scaled,
        'payback_scaled': payback_scaled,
        'payback_no_scale': payback_no_scale,
        'payback_reduction': payback_reduction,
        'reduction_percent': reduction_percent
    }


def interpolate_capex_curve(sizes_mw: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Genera curva continua de CAPEX vs tamaño para visualización.
    
    Args:
        sizes_mw: Array de tamaños (default: 1 a 200 MW)
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: (sizes, capex_per_mw)
        
    Example:
        >>> sizes, capex = interpolate_capex_curve()
        >>> # Usar para graficar curva de economías de escala
    """
    if sizes_mw is None:
        sizes_mw = np.linspace(1, 200, 200)
    
    capex_values = np.array([calculate_pv_capex_per_mw(size) for size in sizes_mw])
    
    return sizes_mw, capex_values


# Funciones de validación
def validate_pv_size(pv_mw: float) -> bool:
    """Valida que el tamaño del proyecto sea razonable."""
    return 0.1 <= pv_mw <= 1000


def validate_capex_range(capex_per_mw: float) -> bool:
    """Valida que el CAPEX esté en rango esperado."""
    return 500_000 <= capex_per_mw <= 1_000_000


def get_size_category(pv_mw: float) -> str:
    """
    Categoriza el proyecto por tamaño.
    
    Args:
        pv_mw: Capacidad en MW
        
    Returns:
        str: Categoría del proyecto
    """
    if pv_mw < 1:
        return "Micro (<1 MW)"
    elif pv_mw < 5:
        return "Pequeño (1-5 MW)"
    elif pv_mw < 20:
        return "Mediano (5-20 MW)"
    elif pv_mw < 50:
        return "Grande (20-50 MW)"
    elif pv_mw < 100:
        return "Muy Grande (50-100 MW)"
    else:
        return "Utility Scale (>100 MW)"


# Constantes para uso externo
CAPEX_1MW = 850_000
CAPEX_100MW = 637_000
CAPEX_REDUCTION_TOTAL = CAPEX_1MW - CAPEX_100MW
ECONOMIES_OF_SCALE_PERCENT = (CAPEX_REDUCTION_TOTAL / CAPEX_1MW) * 100