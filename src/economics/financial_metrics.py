"""
Módulo de Cálculo de Métricas Financieras
=========================================

Funciones independientes y reutilizables para calcular métricas financieras
de proyectos de generación distribuida. Incluye NPV, IRR, payback, LCOE y
otras métricas estándar.

Autor: Asistente Claude
Fecha: Julio 2025
"""

from typing import Dict, List, Tuple, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


def calculate_capex_total(pv_mw: float,
                         bess_mwh: float,
                         q_mvar: float,
                         pv_capex_usd_mw: float,
                         bess_capex_usd_mwh: float,
                         statcom_capex_usd_mvar: float,
                         bos_factor: float = 0.15) -> float:
    """
    Calcula el CAPEX total del proyecto.
    
    Args:
        pv_mw: Capacidad PV en MW
        bess_mwh: Capacidad BESS en MWh
        q_mvar: Capacidad reactiva en MVAr
        pv_capex_usd_mw: Costo unitario PV (USD/MW)
        bess_capex_usd_mwh: Costo unitario BESS (USD/MWh)
        statcom_capex_usd_mvar: Costo unitario STATCOM (USD/MVAr)
        bos_factor: Factor de Balance of System (0.15 = 15%)
    
    Returns:
        float: CAPEX total en USD
    
    Example:
        >>> capex = calculate_capex_total(10, 5, 3, 800000, 200000, 40000)
        >>> print(f"CAPEX: ${capex/1e6:.2f}M")
    """
    capex_subtotal = (
        pv_mw * pv_capex_usd_mw +
        bess_mwh * bess_capex_usd_mwh +
        q_mvar * statcom_capex_usd_mvar
    )
    
    capex_total = capex_subtotal * (1 + bos_factor)
    
    logger.debug(f"CAPEX: PV ${pv_mw * pv_capex_usd_mw/1e6:.1f}M + "
                f"BESS ${bess_mwh * bess_capex_usd_mwh/1e6:.1f}M + "
                f"Q ${q_mvar * statcom_capex_usd_mvar/1e6:.1f}M + "
                f"BOS {bos_factor*100:.0f}% = ${capex_total/1e6:.1f}M")
    
    return capex_total


def calculate_annual_opex(capex_total: float,
                         pv_mw: float,
                         bess_mwh: float,
                         q_mvar: float,
                         opex_rate_pv: float = 0.01,
                         opex_rate_bess: float = 0.015,
                         opex_rate_statcom: float = 0.02) -> float:
    """
    Calcula el OPEX anual del proyecto.
    
    Args:
        capex_total: CAPEX total del proyecto
        pv_mw: Capacidad PV para ponderación
        bess_mwh: Capacidad BESS para ponderación
        q_mvar: Capacidad Q para ponderación
        opex_rate_pv: Tasa OPEX para PV (% del CAPEX)
        opex_rate_bess: Tasa OPEX para BESS
        opex_rate_statcom: Tasa OPEX para STATCOM
    
    Returns:
        float: OPEX anual en USD
    """
    # Ponderación de tasas OPEX por componente
    total_capacity = pv_mw + bess_mwh + q_mvar
    if total_capacity > 0:
        weighted_opex_rate = (
            (pv_mw * opex_rate_pv + 
             bess_mwh * opex_rate_bess + 
             q_mvar * opex_rate_statcom) / total_capacity
        )
    else:
        weighted_opex_rate = opex_rate_pv  # Default
    
    annual_opex = capex_total * weighted_opex_rate
    
    logger.debug(f"OPEX: ${capex_total/1e6:.1f}M × {weighted_opex_rate*100:.1f}% = ${annual_opex/1e3:.0f}k/año")
    
    return annual_opex


def calculate_cash_flows(capex: float,
                        annual_revenue: float,
                        annual_opex: float,
                        project_lifetime: int,
                        inflation_rate: float = 0.04) -> List[Dict[str, float]]:
    """
    Genera flujo de caja para todo el proyecto.
    
    Args:
        capex: Inversión inicial
        annual_revenue: Ingresos anuales año 1
        annual_opex: OPEX año 1
        project_lifetime: Años de vida útil
        inflation_rate: Tasa de inflación anual
    
    Returns:
        List[Dict]: Lista de flujos por año con 'year' y 'cash_flow'
    """
    cash_flows = []
    
    # Año 0: Inversión
    cash_flows.append({
        'year': 0,
        'revenue': 0,
        'opex': 0,
        'cash_flow': -capex
    })
    
    # Años 1 a N: Operación
    for year in range(1, project_lifetime + 1):
        # Aplicar inflación
        revenue_year = annual_revenue * (1 + inflation_rate) ** (year - 1)
        opex_year = annual_opex * (1 + inflation_rate) ** (year - 1)
        
        cash_flow_year = revenue_year - opex_year
        
        cash_flows.append({
            'year': year,
            'revenue': revenue_year,
            'opex': opex_year,
            'cash_flow': cash_flow_year
        })
    
    return cash_flows


def calculate_npv(cash_flows: List[Dict[str, float]],
                 discount_rate: float = 0.10) -> float:
    """
    Calcula el Valor Presente Neto (NPV).
    
    Args:
        cash_flows: Lista de flujos de caja
        discount_rate: Tasa de descuento
    
    Returns:
        float: NPV en USD
    """
    npv = 0
    
    for flow in cash_flows:
        year = flow['year']
        cash_flow = flow['cash_flow']
        npv += cash_flow / (1 + discount_rate) ** year
    
    logger.debug(f"NPV @ {discount_rate*100:.0f}%: ${npv/1e6:.2f}M")
    
    return npv


def calculate_irr(cash_flows: List[Dict[str, float]]) -> float:
    """
    Calcula la Tasa Interna de Retorno (TIR).
    
    Args:
        cash_flows: Lista de flujos de caja
    
    Returns:
        float: TIR como decimal (0.15 = 15%)
    """
    # Extraer solo los valores de flujo
    flows = [f['cash_flow'] for f in cash_flows]
    
    try:
        irr = np.irr(flows)
        if np.isnan(irr) or irr < -0.99 or irr > 1.0:
            # Fallback: estimación basada en payback
            positive_flows = [f for f in flows[1:] if f > 0]
            if positive_flows:
                avg_positive = sum(positive_flows) / len(positive_flows)
                simple_payback = abs(flows[0]) / avg_positive if avg_positive > 0 else 20
                irr = 0.25 / (1 + simple_payback/4) if simple_payback < 20 else 0.05
            else:
                irr = 0.0
    except:
        irr = 0.0
    
    logger.debug(f"IRR: {irr*100:.1f}%")
    
    return irr


def calculate_payback(cash_flows: List[Dict[str, float]]) -> float:
    """
    Calcula el período de payback simple.
    
    Args:
        cash_flows: Lista de flujos de caja
    
    Returns:
        float: Años de payback
    """
    cumulative = 0
    
    for flow in cash_flows:
        cumulative += flow['cash_flow']
        if cumulative >= 0:
            # Interpolación para payback fraccionario
            if flow['year'] == 0:
                return 0
            
            prev_cumulative = cumulative - flow['cash_flow']
            fraction = -prev_cumulative / flow['cash_flow']
            payback = flow['year'] - 1 + fraction
            
            logger.debug(f"Payback: {payback:.1f} años")
            return payback
    
    # Si no hay payback en el período
    logger.debug("Payback: > vida útil del proyecto")
    return float(cash_flows[-1]['year'])


def calculate_lcoe(capex: float,
                  annual_generation_mwh: float,
                  annual_opex: float,
                  project_lifetime: int,
                  discount_rate: float = 0.10,
                  degradation_rate: float = 0.005) -> float:
    """
    Calcula el Costo Nivelado de Energía (LCOE).
    
    Args:
        capex: Inversión inicial
        annual_generation_mwh: Generación año 1
        annual_opex: OPEX año 1
        project_lifetime: Años de vida útil
        discount_rate: Tasa de descuento
        degradation_rate: Degradación anual (0.005 = 0.5%)
    
    Returns:
        float: LCOE en USD/MWh
    """
    # VP de costos
    pv_costs = capex
    
    # VP de generación
    pv_generation = 0
    
    for year in range(1, project_lifetime + 1):
        # Generación con degradación
        generation_year = annual_generation_mwh * (1 - degradation_rate) ** (year - 1)
        
        # OPEX con inflación (asumiendo 3%)
        opex_year = annual_opex * (1.03) ** (year - 1)
        
        # Descontar
        pv_costs += opex_year / (1 + discount_rate) ** year
        pv_generation += generation_year / (1 + discount_rate) ** year
    
    lcoe = pv_costs / pv_generation if pv_generation > 0 else 0
    
    logger.debug(f"LCOE: ${lcoe:.1f}/MWh")
    
    return lcoe


def calculate_benefit_cost_ratio(total_benefits_npv: float,
                                total_costs_npv: float) -> float:
    """
    Calcula la relación Beneficio/Costo.
    
    Args:
        total_benefits_npv: VP de todos los beneficios
        total_costs_npv: VP de todos los costos
    
    Returns:
        float: Ratio B/C
    """
    if total_costs_npv > 0:
        bc_ratio = total_benefits_npv / total_costs_npv
    else:
        bc_ratio = 0
    
    logger.debug(f"B/C Ratio: {bc_ratio:.2f}")
    
    return bc_ratio


def calculate_all_financial_metrics(capex: float,
                                  annual_revenue: float,
                                  annual_opex: float,
                                  annual_generation_mwh: float,
                                  project_lifetime: int = 20,
                                  discount_rate: float = 0.10,
                                  inflation_rate: float = 0.04) -> Dict[str, float]:
    """
    Calcula todas las métricas financieras principales.
    
    Args:
        capex: Inversión inicial
        annual_revenue: Ingresos anuales
        annual_opex: OPEX anual
        annual_generation_mwh: Generación anual
        project_lifetime: Años de vida útil
        discount_rate: Tasa de descuento
        inflation_rate: Tasa de inflación
    
    Returns:
        Dict con todas las métricas
    """
    # Generar flujos de caja
    cash_flows = calculate_cash_flows(
        capex, annual_revenue, annual_opex, 
        project_lifetime, inflation_rate
    )
    
    # Calcular métricas
    metrics = {
        'capex': capex,
        'npv': calculate_npv(cash_flows, discount_rate),
        'irr': calculate_irr(cash_flows),
        'payback': calculate_payback(cash_flows),
        'lcoe': calculate_lcoe(
            capex, annual_generation_mwh, annual_opex,
            project_lifetime, discount_rate
        ),
        'bc_ratio': 0  # Se calcula externamente con beneficios totales
    }
    
    # Calcular B/C si NPV es positivo
    if metrics['npv'] > 0:
        # Aproximación: beneficios totales = capex + npv
        total_benefits_pv = capex + metrics['npv']
        metrics['bc_ratio'] = total_benefits_pv / capex
    else:
        metrics['bc_ratio'] = metrics['npv'] / capex if capex > 0 else 0
    
    logger.info(f"Financial Metrics: NPV ${metrics['npv']/1e6:.1f}M, "
                f"IRR {metrics['irr']*100:.1f}%, "
                f"Payback {metrics['payback']:.1f} años")
    
    return metrics


# Funciones de validación
def validate_financial_metrics(metrics: Dict[str, float]) -> List[str]:
    """
    Valida que las métricas financieras sean razonables.
    
    Returns:
        List[str]: Lista de advertencias
    """
    warnings = []
    
    # NPV no debe ser extremadamente alto
    if metrics['npv'] > metrics['capex'] * 10:
        warnings.append(f"NPV muy alto: {metrics['npv']/metrics['capex']:.1f}x CAPEX")
    
    # IRR razonable
    if metrics['irr'] > 0.50:  # >50%
        warnings.append(f"IRR muy alta: {metrics['irr']*100:.0f}%")
    elif metrics['irr'] < 0:
        warnings.append(f"IRR negativa: {metrics['irr']*100:.0f}%")
    
    # Payback razonable
    if metrics['payback'] < 2:
        warnings.append(f"Payback muy corto: {metrics['payback']:.1f} años")
    elif metrics['payback'] > 15:
        warnings.append(f"Payback muy largo: {metrics['payback']:.1f} años")
    
    # LCOE razonable
    if metrics['lcoe'] < 20:  # <$20/MWh
        warnings.append(f"LCOE muy bajo: ${metrics['lcoe']:.0f}/MWh")
    elif metrics['lcoe'] > 200:  # >$200/MWh
        warnings.append(f"LCOE muy alto: ${metrics['lcoe']:.0f}/MWh")
    
    # B/C ratio
    if metrics['bc_ratio'] > 5:
        warnings.append(f"B/C muy alto: {metrics['bc_ratio']:.1f}")
    
    return warnings


def format_financial_summary(metrics: Dict[str, float]) -> str:
    """
    Formatea un resumen de métricas financieras.
    """
    return f"""
    Métricas Financieras:
    - CAPEX: ${metrics['capex']/1e6:.1f}M
    - NPV: ${metrics['npv']/1e6:.1f}M
    - IRR: {metrics['irr']*100:.1f}%
    - Payback: {metrics['payback']:.1f} años
    - LCOE: ${metrics['lcoe']:.0f}/MWh
    - B/C: {metrics['bc_ratio']:.2f}
    """