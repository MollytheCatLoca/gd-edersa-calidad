"""
Cargador Centralizado de Configuración
====================================
Carga y gestiona todos los parámetros desde el archivo YAML centralizado.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Cargador centralizado de configuración desde archivo YAML.
    Proporciona acceso a todos los parámetros del sistema.
    """
    
    def __init__(self, config_file: str = "parameters.yaml"):
        """
        Inicializa el cargador de configuración.
        
        Args:
            config_file: Nombre del archivo de configuración
        """
        # Buscar archivo de configuración
        self.config_path = self._find_config_file(config_file)
        
        # Cargar configuración
        self.config = self._load_yaml()
        
        # Validar configuración
        self._validate_config()
        
        logger.info(f"Configuración cargada desde: {self.config_path}")
    
    def _find_config_file(self, config_file: str) -> Path:
        """Busca el archivo de configuración en varias ubicaciones"""
        # Intentar varias rutas posibles
        possible_paths = [
            Path(__file__).parent.parent.parent / "config" / config_file,
            Path.cwd() / "config" / config_file,
            Path.home() / ".gd_edersa" / config_file,
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        raise FileNotFoundError(
            f"No se encontró archivo de configuración '{config_file}' en: "
            f"{[str(p) for p in possible_paths]}"
        )
    
    def _load_yaml(self) -> Dict[str, Any]:
        """Carga el archivo YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            raise
    
    def _validate_config(self):
        """Valida que la configuración tenga las secciones requeridas"""
        required_sections = [
            'energy_prices',
            'capex',
            'opex',
            'financial',
            'network_technical',
            'operation_factors'
        ]
        
        missing = [s for s in required_sections if s not in self.config]
        if missing:
            raise ValueError(f"Secciones faltantes en configuración: {missing}")
    
    def get_all_params(self) -> Dict[str, Any]:
        """Retorna toda la configuración"""
        return self.config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Retorna una sección específica de la configuración.
        
        Args:
            section: Nombre de la sección
            
        Returns:
            Diccionario con los parámetros de la sección
        """
        if section not in self.config:
            raise KeyError(f"Sección '{section}' no encontrada en configuración")
        return self.config[section].copy()
    
    def get_economic_params(self) -> Dict[str, Any]:
        """
        Retorna parámetros económicos para IntegratedCashFlowCalculator.
        Mapea desde la estructura YAML a la esperada por el calculador.
        """
        return {
            # Precios de energía
            'electricity_price': self.config['energy_prices']['electricity_price'],
            'peak_electricity_price': (
                self.config['energy_prices']['electricity_price'] * 
                self.config['energy_prices']['peak_tariff_multiplier']
            ),
            'export_price': self.config['energy_prices']['export_price'],
            'upstream_energy_cost': self.config['energy_prices']['upstream_energy_cost'],
            
            # Cargos
            'demand_charge': self.config['charges_penalties']['demand_charge_usd_kw_month'],
            'reactive_penalty': self.config['charges_penalties']['reactive_penalty_usd_kvar_month'],
            'voltage_penalty': self.config['charges_penalties']['voltage_violation_cost_usd_hour'],
            
            # Financieros
            'discount_rate': self.config['financial']['discount_rate'],
            'inflation_rate': self.config['financial']['inflation_rate'],
            'project_lifetime': self.config['financial']['project_lifetime'],
            
            # CAPEX
            'pv_capex_usd_mw': self.config['capex']['pv_capex_usd_mw'],
            'bess_capex_usd_mwh': self.config['capex']['bess_capex_usd_mwh'],
            'bess_capex_usd_mw': self.config['capex']['bess_capex_usd_mw'],
            'statcom_capex_usd_mvar': self.config['capex']['statcom_capex_usd_mvar'],
            
            # OPEX
            'pv_opex_rate': self.config['opex']['pv_opex_rate'],
            'bess_opex_rate': self.config['opex']['bess_opex_rate'],
            
            # Degradación
            'pv_degradation': self.config['degradation_efficiency']['pv_degradation_annual'],
            'bess_degradation': self.config['degradation_efficiency']['bess_degradation_annual'],
        }
    
    def get_network_params(self) -> Dict[str, Any]:
        """
        Retorna parámetros de red para NetworkBenefitsCalculator.
        """
        return {
            # Parámetros eléctricos
            'voltage_nominal_kv': self.config['network_technical']['voltage_nominal_kv'],
            'base_power_factor': self.config['network_technical']['base_power_factor'],
            'target_power_factor': self.config['network_technical']['target_power_factor'],
            'min_voltage_pu': self.config['network_technical']['min_voltage_pu'],
            'max_voltage_pu': self.config['network_technical']['max_voltage_pu'],
            
            # Costos técnicos
            'technical_loss_rate': self.config['network_technical']['technical_loss_rate'],
            'energy_cost_upstream_usd_mwh': self.config['energy_prices']['upstream_energy_cost'],
            'transformer_cost_usd_mva': self.config['capex']['transformer_cost_usd_mva'],
            'line_cost_usd_km': self.config['capex']['line_cost_usd_km'],
            
            # Penalizaciones
            'voltage_violation_cost_usd_hour': self.config['charges_penalties']['voltage_violation_cost_usd_hour'],
            'saidi_cost_usd_minute': self.config['charges_penalties']['saidi_cost_usd_minute'],
            'ens_cost_usd_mwh': self.config['energy_prices']['energy_not_served_cost'],
            
            # Factores técnicos
            'mvar_to_mw_loss_factor': self.config['technical_sensitivities']['mvar_to_mw_loss_factor'],
            'voltage_sensitivity_kv_mvar': self.config['technical_sensitivities']['voltage_sensitivity_kv_mvar'],
        }
    
    def get_optimization_constraints(self) -> Dict[str, Any]:
        """
        Retorna restricciones para el optimizador.
        """
        return self.config['optimization_constraints'].copy()
    
    def get_demand_factors(self) -> Dict[str, Any]:
        """
        Retorna factores de demanda y consumo.
        """
        return self.config['demand_factors'].copy()
    
    def get_operation_factors(self) -> Dict[str, Any]:
        """
        Retorna factores de operación y planta.
        """
        return self.config['operation_factors'].copy()
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Obtiene un valor específico usando notación de punto.
        
        Args:
            path: Ruta al valor (ej: 'energy_prices.electricity_price')
            default: Valor por defecto si no existe
            
        Returns:
            Valor encontrado o default
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def update_value(self, path: str, value: Any):
        """
        Actualiza un valor en la configuración (solo en memoria).
        
        Args:
            path: Ruta al valor
            value: Nuevo valor
        """
        keys = path.split('.')
        config_ref = self.config
        
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        config_ref[keys[-1]] = value
        logger.info(f"Actualizado {path} = {value}")
    
    def save_config(self, output_path: Optional[Path] = None):
        """
        Guarda la configuración actual a archivo.
        
        Args:
            output_path: Ruta de salida (None usa la original)
        """
        save_path = output_path or self.config_path
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuración guardada en: {save_path}")


# Instancia singleton para uso global
_config_instance = None

def get_config() -> ConfigLoader:
    """
    Obtiene la instancia global del cargador de configuración.
    
    Returns:
        Instancia de ConfigLoader
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigLoader()
    
    return _config_instance