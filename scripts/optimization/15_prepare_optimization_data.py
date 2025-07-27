#!/usr/bin/env python3
"""
FASE 3 - Script 15: Preparación de Datos para Optimización
========================================================
Consolida los datos de clusters de IAS 3.0 y prepara la información
necesaria para el proceso de optimización de flujos integrados.

Entrada:
- Resultados de clustering IAS 3.0
- Datos de transformadores e inventario
- Parámetros económicos y técnicos

Salida:
- Dataset consolidado para optimización
- Parámetros de red por cluster
- Perfiles de carga estimados

Autor: Asistente Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime
import sqlite3
import sys

# Agregar path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config.config_loader import get_config

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CLUSTERING_DIR = BASE_DIR / "reports" / "clustering"
OPTIMIZATION_DIR = CLUSTERING_DIR / "optimization"
OPTIMIZATION_DIR.mkdir(exist_ok=True)

# Ruta de base de datos
DB_PATH = PROCESSED_DIR / "edersa_gd_analysis.db"


class OptimizationDataPreparator:
    """
    Prepara los datos necesarios para el proceso de optimización de flujos.
    """
    
    def __init__(self):
        """Inicializa el preparador de datos"""
        self.conn = sqlite3.connect(DB_PATH)
        
        # Cargar configuración centralizada
        config = get_config()
        
        # Obtener parámetros desde config
        self.economic_params = self._prepare_economic_params(config)
        self.technical_params = self._prepare_technical_params(config)
        
    def _prepare_economic_params(self, config) -> dict:
        """Prepara parámetros económicos desde configuración centralizada"""
        energy_prices = config.get_section('energy_prices')
        financial = config.get_section('financial')
        capex = config.get_section('capex')
        opex = config.get_section('opex')
        charges = config.get_section('charges_penalties')
        degradation = config.get_section('degradation_efficiency')
        
        return {
            # Tarifas energía
            'tariff_residential': energy_prices['tariff_residential'],
            'tariff_commercial': energy_prices['tariff_commercial'],
            'tariff_industrial': energy_prices['tariff_industrial'],
            'tariff_rural': energy_prices['tariff_rural'],
            'tariff_average': energy_prices['electricity_price'],
            
            # Precios especiales
            'peak_tariff_multiplier': energy_prices['peak_tariff_multiplier'],
            'export_price': energy_prices['export_price'],
            'upstream_cost': energy_prices['upstream_energy_cost'],
            
            # Cargos y penalizaciones
            'demand_charge_usd_kw_month': charges['demand_charge_usd_kw_month'],
            'reactive_penalty_usd_kvar_month': charges['reactive_penalty_usd_kvar_month'],
            'voltage_penalty_usd_hour': charges['voltage_violation_cost_usd_hour'],
            
            # Parámetros financieros
            'discount_rate': financial['discount_rate'],
            'inflation_rate': financial['inflation_rate'],
            'project_lifetime': financial['project_lifetime'],
            
            # CAPEX unitarios
            'pv_capex_usd_mw': capex['pv_capex_usd_mw'],
            'bess_capex_usd_mwh': capex['bess_capex_usd_mwh'],
            'bess_capex_usd_mw': capex['bess_capex_usd_mw'],
            'statcom_capex_usd_mvar': capex['statcom_capex_usd_mvar'],
            
            # OPEX
            'pv_opex_rate': opex['pv_opex_rate'],
            'bess_opex_rate': opex['bess_opex_rate'],
            
            # Degradación
            'pv_degradation': degradation['pv_degradation_annual'],
            'bess_degradation': degradation['bess_degradation_annual'],
        }
    
    def _prepare_technical_params(self, config) -> dict:
        """Prepara parámetros técnicos desde configuración centralizada"""
        network = config.get_section('network_technical')
        operation = config.get_section('operation_factors')
        
        return {
            # Parámetros de red
            'voltage_nominal_kv': network['voltage_nominal_kv'],
            'base_power_factor': network['base_power_factor'],
            'technical_loss_rate': network['technical_loss_rate'],
            
            # Factores de capacidad y perfiles
            'pv_capacity_factor': operation['pv_capacity_factor'],
            'load_factor_residential': operation['load_factor_residential'],
            'load_factor_commercial': operation['load_factor_commercial'],
            'load_factor_industrial': operation['load_factor_industrial'],
            'load_factor_rural': operation['load_factor_rural'],
            
            # Factores de diversidad
            'diversity_factor': operation['diversity_factor'],
            'coincidence_factor': operation['coincidence_factor'],
            
            # Límites técnicos
            'max_injection_ratio': network['max_transformer_loading'],
            'min_voltage_pu': network['min_voltage_pu'],
            'max_voltage_pu': network['max_voltage_pu'],
        }
    
    def load_cluster_data(self) -> pd.DataFrame:
        """Carga datos de clusters desde IAS 3.0"""
        logger.info("Cargando datos de clusters IAS 3.0...")
        
        # Cargar resultado de clustering refinado
        cluster_file = PROCESSED_DIR / "clusters_ias_v3.parquet"
        if not cluster_file.exists():
            # Intentar ruta alternativa
            cluster_file = PROCESSED_DIR / "transformers_refined_ias_v3.parquet"
            if not cluster_file.exists():
                raise FileNotFoundError(f"No se encontró archivo de clusters: {cluster_file}")
        
        clusters = pd.read_parquet(cluster_file)
        
        # Los datos ya están consolidados en clusters_ias_v3
        # Renombrar columnas para compatibilidad
        clusters_full = clusters.rename(columns={
            'n_transformadores': 'num_transformers',
            'n_usuarios': 'total_users',
            'potencia_total_mva': 'total_mva'
        })
        
        # Convertir MVA a kVA para compatibilidad
        clusters_full['total_kva'] = clusters_full['total_mva'] * 1000
        
        # Estimar valores faltantes usando los criterios IAS
        clusters_full['avg_impedance_pu'] = 0.05 + 0.1 * clusters_full['C3_vulnerabilidad']
        clusters_full['avg_distance_km'] = clusters_full['radio_km'] * 2  # Aproximación
        
        # Estimar usuarios penalizados/fallidos basado en tasa de falla
        clusters_full['penalized_users'] = clusters_full['total_users'] * clusters_full['tasa_falla'] * 0.6
        clusters_full['failed_users'] = clusters_full['total_users'] * clusters_full['tasa_falla'] * 0.4
        
        # Agregar perfiles de carga basados en perfil dominante
        profile_map = {
            'residencial': 'residential',
            'comercial': 'commercial', 
            'industrial': 'industrial',
            'rural': 'rural'
        }
        
        # Calcular ratios de tipo de carga
        for perfil in ['residencial', 'comercial', 'industrial', 'rural']:
            col_name = f'{profile_map.get(perfil, perfil)}_ratio'
            clusters_full[col_name] = (clusters_full['perfil_dominante'] == perfil).astype(float)
        
        # Para clusters sin perfil claro, asumir mixto
        no_profile = ~clusters_full['perfil_dominante'].isin(profile_map.keys())
        for col in ['residential_ratio', 'commercial_ratio', 'industrial_ratio', 'rural_ratio']:
            clusters_full.loc[no_profile, col] = 0.25
        
        logger.info(f"Cargados {len(clusters_full)} clusters para optimización")
        return clusters_full
    
    def calculate_demand_parameters(self, clusters_df: pd.DataFrame) -> pd.DataFrame:
        """Calcula parámetros de demanda para cada cluster"""
        logger.info("Calculando parámetros de demanda...")
        
        # Estimar demanda pico por cluster
        clusters_df['peak_demand_mw'] = clusters_df.apply(
            lambda row: self._estimate_peak_demand(row), axis=1
        )
        
        # Estimar energía anual
        clusters_df['annual_energy_mwh'] = clusters_df.apply(
            lambda row: self._estimate_annual_energy(row), axis=1
        )
        
        # Factor de carga promedio
        clusters_df['load_factor'] = (
            clusters_df['annual_energy_mwh'] / 
            (clusters_df['peak_demand_mw'] * 8760)
        ).clip(0.2, 0.8)
        
        # Tipo de carga dominante
        clusters_df['dominant_load_type'] = clusters_df.apply(
            lambda row: self._determine_load_type(row), axis=1
        )
        
        return clusters_df
    
    def _estimate_peak_demand(self, row) -> float:
        """Estima demanda pico del cluster en MW"""
        # Cargar factores de demanda desde config
        config = get_config()
        demand_config = config.get_section('demand_factors')
        
        demand_factors = {
            'residential': demand_config['residential_kw_per_user'],
            'commercial': demand_config['commercial_kw_per_kva'],
            'industrial': demand_config['industrial_factor'],
            'rural': demand_config['rural_kw_per_user'],
            'mixed': demand_config['mixed_kw_per_user']
        }
        
        # Determinar tipo predominante por perfil
        if row['industrial_ratio'] > 0.5:
            load_type = 'industrial'
            peak_mw = row['total_kva'] * demand_factors['industrial'] / 1000
        elif row['commercial_ratio'] > 0.4:
            load_type = 'commercial'
            peak_mw = row['total_kva'] * demand_factors['commercial'] / 1000000
        elif row['residential_ratio'] > 0.6:
            load_type = 'residential'
            peak_mw = row['total_users'] * demand_factors['residential'] / 1000
        elif row['rural_ratio'] > 0.5:
            load_type = 'rural'
            peak_mw = row['total_users'] * demand_factors['rural'] / 1000
        else:
            load_type = 'mixed'
            peak_mw = row['total_users'] * demand_factors['mixed'] / 1000
        
        # Aplicar factor de diversidad
        peak_mw *= self.technical_params['diversity_factor']
        
        # Validar contra capacidad instalada
        max_possible = row['total_kva'] * 0.8 / 1000  # 80% de kVA instalado
        return min(peak_mw, max_possible)
    
    def _estimate_annual_energy(self, row) -> float:
        """Estima energía anual del cluster en MWh"""
        # Cargar factores de consumo desde config
        config = get_config()
        demand_config = config.get_section('demand_factors')
        
        consumption_factors = {
            'residential': demand_config['residential_kwh_year'],
            'commercial': demand_config['commercial_kwh_year'],
            'industrial': demand_config['industrial_kwh_year'],
            'rural': demand_config['rural_kwh_year'],
            'mixed': demand_config['mixed_kwh_year']
        }
        
        # Estimar por tipo de carga
        energy_mwh = 0
        
        if row['residential_ratio'] > 0:
            res_users = row['total_users'] * row['residential_ratio']
            energy_mwh += res_users * consumption_factors['residential'] / 1000
        
        if row['commercial_ratio'] > 0:
            com_trafos = row['num_transformers'] * row['commercial_ratio']
            energy_mwh += com_trafos * consumption_factors['commercial'] / 1000
        
        if row['industrial_ratio'] > 0:
            ind_kva = row['total_kva'] * row['industrial_ratio']
            energy_mwh += ind_kva * 0.65 * 8760 * 0.7 / 1000  # Factor carga industrial
        
        if row['rural_ratio'] > 0:
            rural_users = row['total_users'] * row['rural_ratio']
            energy_mwh += rural_users * consumption_factors['rural'] / 1000
        
        # Si no hay datos claros, usar promedio
        if energy_mwh == 0:
            energy_mwh = row['total_users'] * consumption_factors['mixed'] / 1000
        
        return energy_mwh
    
    def _determine_load_type(self, row) -> str:
        """Determina tipo de carga dominante"""
        types = {
            'residential': row['residential_ratio'],
            'commercial': row['commercial_ratio'],
            'industrial': row['industrial_ratio'],
            'rural': row['rural_ratio']
        }
        
        dominant = max(types.items(), key=lambda x: x[1])
        
        if dominant[1] < 0.4:  # No hay tipo claramente dominante
            return 'mixed'
        else:
            return dominant[0]
    
    def calculate_network_parameters(self, clusters_df: pd.DataFrame) -> pd.DataFrame:
        """Calcula parámetros de red para cada cluster"""
        logger.info("Calculando parámetros de red...")
        
        # Capacidad de transformación disponible (debe ir primero)
        clusters_df['transformer_capacity_mva'] = (
            clusters_df['total_kva'] / 1000  # kVA a MVA
        )
        
        # Impedancia equivalente (basado en distancia y topología)
        clusters_df['equivalent_resistance_pu'] = (
            clusters_df['avg_impedance_pu'] * 0.8  # R ~ 80% de Z
        )
        clusters_df['equivalent_reactance_pu'] = (
            clusters_df['avg_impedance_pu'] * 0.6  # X ~ 60% de Z
        )
        
        # Sensibilidad de pérdidas
        clusters_df['loss_sensitivity'] = clusters_df.apply(
            lambda row: self._calculate_loss_sensitivity(row), axis=1
        )
        
        # Margen de capacidad
        clusters_df['capacity_margin_mva'] = (
            clusters_df['transformer_capacity_mva'] - 
            clusters_df['peak_demand_mw'] / self.technical_params['base_power_factor']
        ).clip(lower=0)
        
        # Costo estimado de upgrade
        clusters_df['upgrade_cost_usd'] = clusters_df.apply(
            lambda row: self._estimate_upgrade_cost(row), axis=1
        )
        
        # Penalizaciones históricas (estimadas)
        clusters_df['annual_penalties_usd'] = clusters_df.apply(
            lambda row: self._estimate_penalties(row), axis=1
        )
        
        return clusters_df
    
    def _calculate_loss_sensitivity(self, row) -> float:
        """Calcula sensibilidad de pérdidas (MW pérdidas/MW inyección)"""
        # Basado en distancia y carga
        base_sensitivity = 0.05  # 5% base
        
        # Ajustar por distancia
        distance_factor = min(2.0, row['avg_distance_km'] / 20)  # Normalizar a 20km
        
        # Ajustar por nivel de carga
        loading_factor = min(1.5, row['peak_demand_mw'] / (row['transformer_capacity_mva'] * 0.8))
        
        return base_sensitivity * distance_factor * loading_factor
    
    def _estimate_upgrade_cost(self, row) -> float:
        """Estima costo de upgrade de infraestructura"""
        # Costo base por MVA adicional
        cost_per_mva = 50000  # USD/MVA
        
        # Capacidad adicional necesaria (proyección 10 años)
        growth_rate = 0.03
        future_demand = row['peak_demand_mw'] * (1 + growth_rate) ** 10
        additional_mva = max(0, future_demand / 0.85 - row['transformer_capacity_mva'])
        
        # Costo base
        base_cost = additional_mva * cost_per_mva
        
        # Factor por distancia (más caro en zonas alejadas)
        distance_factor = 1 + (row['avg_distance_km'] / 50)
        
        return base_cost * distance_factor
    
    def _estimate_penalties(self, row) -> float:
        """Estima penalizaciones anuales por calidad"""
        # Penalización base por usuario afectado
        penalty_per_user = 50  # USD/usuario/año
        
        # Usuarios con problemas
        problem_users = row['penalized_users'] + row['failed_users']
        
        # Penalización base
        base_penalty = problem_users * penalty_per_user
        
        # Factor por criticidad
        criticality_factor = 1.0
        if row['failed_users'] > row['penalized_users']:
            criticality_factor = 1.5  # Más crítico si hay más fallidas
        
        return base_penalty * criticality_factor
    
    def generate_load_profiles(self, clusters_df: pd.DataFrame) -> dict:
        """Genera perfiles de carga típicos por tipo"""
        logger.info("Generando perfiles de carga...")
        
        profiles = {}
        hours = np.arange(24)
        
        # Perfil residencial
        profiles['residential'] = self._residential_profile(hours)
        
        # Perfil comercial
        profiles['commercial'] = self._commercial_profile(hours)
        
        # Perfil industrial
        profiles['industrial'] = self._industrial_profile(hours)
        
        # Perfil rural
        profiles['rural'] = self._rural_profile(hours)
        
        # Perfil mixto
        profiles['mixed'] = self._mixed_profile(profiles)
        
        # Guardar perfiles
        profiles_df = pd.DataFrame(profiles)
        profiles_df['hour'] = hours
        profiles_df.to_csv(OPTIMIZATION_DIR / 'load_profiles.csv', index=False)
        
        return profiles
    
    def _residential_profile(self, hours):
        """Perfil residencial con picos mañana y noche"""
        profile = np.ones(24) * 0.4
        profile[6:9] = [0.6, 0.7, 0.6]  # Pico matutino
        profile[10:17] = 0.3  # Valle diurno
        profile[18:23] = [0.8, 0.95, 1.0, 0.9, 0.7]  # Pico nocturno
        return profile
    
    def _commercial_profile(self, hours):
        """Perfil comercial con pico diurno"""
        profile = np.ones(24) * 0.2
        profile[8:20] = [0.5, 0.7, 0.85, 0.95, 1.0, 0.95, 
                        0.9, 0.85, 0.8, 0.7, 0.6, 0.4]
        return profile
    
    def _industrial_profile(self, hours):
        """Perfil industrial relativamente constante"""
        profile = np.ones(24) * 0.7
        profile[6:18] = 0.9  # Turnos diurnos
        profile[9:15] = 1.0  # Pico producción
        return profile
    
    def _rural_profile(self, hours):
        """Perfil rural con actividad temprana"""
        profile = np.ones(24) * 0.3
        profile[5:8] = [0.5, 0.7, 0.8]  # Actividad temprana
        profile[17:21] = [0.6, 0.8, 0.9, 0.7]  # Actividad tarde
        return profile
    
    def _mixed_profile(self, profiles):
        """Perfil mixto ponderado"""
        return (0.4 * profiles['residential'] + 
                0.3 * profiles['commercial'] + 
                0.2 * profiles['industrial'] + 
                0.1 * profiles['rural'])
    
    def save_optimization_data(self, clusters_df: pd.DataFrame, profiles: dict):
        """Guarda datos preparados para optimización"""
        logger.info("Guardando datos de optimización...")
        
        # Guardar datos de clusters
        output_file = OPTIMIZATION_DIR / 'clusters_optimization_data.parquet'
        clusters_df.to_parquet(output_file, index=False)
        logger.info(f"Datos guardados en: {output_file}")
        
        # Guardar parámetros económicos
        with open(OPTIMIZATION_DIR / 'economic_parameters.json', 'w') as f:
            json.dump(self.economic_params, f, indent=2)
        
        # Guardar parámetros técnicos
        with open(OPTIMIZATION_DIR / 'technical_parameters.json', 'w') as f:
            json.dump(self.technical_params, f, indent=2)
        
        # Generar resumen
        summary = {
            'total_clusters': len(clusters_df),
            'total_peak_demand_mw': clusters_df['peak_demand_mw'].sum(),
            'total_annual_energy_gwh': clusters_df['annual_energy_mwh'].sum() / 1000,
            'total_users': clusters_df['total_users'].sum(),
            'avg_load_factor': clusters_df['load_factor'].mean(),
            'total_penalties_musd': clusters_df['annual_penalties_usd'].sum() / 1e6,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(OPTIMIZATION_DIR / 'preparation_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Mostrar resumen
        logger.info("\n=== RESUMEN DE PREPARACIÓN ===")
        logger.info(f"Clusters procesados: {summary['total_clusters']}")
        logger.info(f"Demanda pico total: {summary['total_peak_demand_mw']:.1f} MW")
        logger.info(f"Energía anual: {summary['total_annual_energy_gwh']:.1f} GWh")
        logger.info(f"Usuarios totales: {summary['total_users']:,}")
        logger.info(f"Penalizaciones estimadas: ${summary['total_penalties_musd']:.2f}M USD/año")
        
        return summary


def main():
    """Función principal"""
    logger.info("=== FASE 3 - PREPARACIÓN DE DATOS PARA OPTIMIZACIÓN ===")
    logger.info(f"Iniciando: {datetime.now()}")
    
    try:
        # Inicializar preparador
        preparator = OptimizationDataPreparator()
        
        # Cargar datos de clusters
        clusters = preparator.load_cluster_data()
        
        # Calcular parámetros de demanda
        clusters = preparator.calculate_demand_parameters(clusters)
        
        # Calcular parámetros de red
        clusters = preparator.calculate_network_parameters(clusters)
        
        # Generar perfiles de carga
        profiles = preparator.generate_load_profiles(clusters)
        
        # Guardar datos
        summary = preparator.save_optimization_data(clusters, profiles)
        
        logger.info("\n✅ Preparación completada exitosamente")
        logger.info(f"Datos listos en: {OPTIMIZATION_DIR}")
        
    except Exception as e:
        logger.error(f"❌ Error en preparación: {str(e)}")
        raise
    
    finally:
        logger.info(f"Finalizado: {datetime.now()}")


if __name__ == "__main__":
    main()