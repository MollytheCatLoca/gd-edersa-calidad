#!/usr/bin/env python3
"""
FASE 3 - Script 16: Cálculo de Flujos Integrados
==============================================
Calcula los flujos de caja integrados (PSFV + Red) para diferentes
configuraciones de GD en cada cluster, generando superficies de valor
para la optimización posterior.

Entrada:
- Datos preparados de clusters (script 15)
- Parámetros económicos y técnicos

Salida:
- Matriz de flujos por configuración
- Análisis de sensibilidad
- Visualizaciones de superficies de valor

Autor: Asistente Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Agregar el directorio src al path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

# Importar módulos económicos
from src.economics.integrated_cash_flow import IntegratedCashFlowCalculator
from src.economics.network_benefits import NetworkBenefitsCalculator

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OPTIMIZATION_DIR = BASE_DIR / "reports" / "clustering" / "optimization"
RESULTS_DIR = OPTIMIZATION_DIR / "integrated_flows"
RESULTS_DIR.mkdir(exist_ok=True)

# Configuración de visualización
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class IntegratedFlowAnalyzer:
    """
    Analiza flujos de caja integrados para diferentes configuraciones de GD.
    """
    
    def __init__(self):
        """Inicializa el analizador"""
        # Cargar configuración centralizada
        from src.config.config_loader import get_config
        config = get_config()
        
        # Obtener parámetros
        self.economic_params = config.get_economic_params()
        self.technical_params = config.get_network_params()
        
        # Inicializar calculadores (ya usan ConfigLoader internamente)
        self.cash_flow_calc = IntegratedCashFlowCalculator()
        self.network_calc = NetworkBenefitsCalculator()
        
        # Configuración de análisis
        self.pv_ratios = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]  # Ratio sobre demanda pico
        self.bess_hours = [0, 1, 2, 3, 4]  # Horas de almacenamiento
        self.q_night_ratios = [0, 0.1, 0.2, 0.3]  # Ratio sobre capacidad PV
        
        logger.info("Analizador de flujos integrados inicializado con parámetros centralizados")
    
    def load_cluster_data(self) -> pd.DataFrame:
        """Carga datos de clusters preparados"""
        cluster_file = OPTIMIZATION_DIR / 'clusters_optimization_data.parquet'
        return pd.read_parquet(cluster_file)
    
    def analyze_cluster(self, cluster_data: pd.Series) -> pd.DataFrame:
        """
        Analiza flujos para todas las configuraciones de un cluster.
        
        Args:
            cluster_data: Serie con datos del cluster
            
        Returns:
            DataFrame con resultados de todas las configuraciones
        """
        cluster_id = cluster_data['cluster_id']
        logger.info(f"Analizando cluster {cluster_id}...")
        
        results = []
        peak_demand_mw = cluster_data['peak_demand_mw']
        
        # Preparar datos del cluster para los calculadores
        cluster_dict = cluster_data.to_dict()
        
        # Iterar sobre todas las configuraciones
        for pv_ratio in self.pv_ratios:
            pv_mw = peak_demand_mw * pv_ratio
            
            for bess_hours in self.bess_hours:
                bess_mwh = peak_demand_mw * bess_hours
                
                for q_ratio in self.q_night_ratios:
                    q_night_mvar = pv_mw * q_ratio
                    
                    # Calcular CAPEX
                    capex = self._calculate_capex(pv_mw, bess_mwh, q_night_mvar)
                    
                    try:
                        # Calcular flujos integrados
                        cash_flows = self.cash_flow_calc.calculate_integrated_flows(
                            cluster_dict, pv_mw, bess_mwh, q_night_mvar, capex
                        )
                        
                        # Calcular métricas financieras
                        metrics = self.cash_flow_calc.calculate_financial_metrics(
                            cash_flows, capex['total']
                        )
                        
                        # Calcular beneficios en red detallados
                        network_benefits = self.network_calc.calculate_all_benefits(
                            cluster_dict, pv_mw, bess_mwh, q_night_mvar
                        )
                        
                        # Agregar resultado
                        result = {
                            'cluster_id': cluster_id,
                            'pv_mw': pv_mw,
                            'pv_ratio': pv_ratio,
                            'bess_mwh': bess_mwh,
                            'bess_hours': bess_hours,
                            'q_night_mvar': q_night_mvar,
                            'q_ratio': q_ratio,
                            'capex_musd': capex['total'] / 1e6,
                            'npv_musd': metrics['npv_usd'] / 1e6,
                            'irr_percent': metrics['irr_percent'],
                            'payback_years': metrics['payback_years'],
                            'bc_ratio': metrics['bc_ratio'],
                            'lcoe_usd_mwh': metrics['lcoe_usd_mwh'],
                            
                            # Flujos promedio anuales
                            'avg_pv_flow_musd': sum(cf.pv_flow for cf in cash_flows) / len(cash_flows) / 1e6,
                            'avg_network_flow_musd': sum(cf.network_flow for cf in cash_flows) / len(cash_flows) / 1e6,
                            'avg_total_flow_musd': sum(cf.total_flow for cf in cash_flows) / len(cash_flows) / 1e6,
                            
                            # Beneficios de red específicos
                            'loss_reduction_musd': network_benefits['loss_reduction'].value_usd / 1e6,
                            'voltage_support_musd': network_benefits['voltage_support'].value_usd / 1e6,
                            'deferral_musd': network_benefits['investment_deferral'].value_usd / 1e6,
                            
                            # Ratio de beneficios de red
                            'network_benefit_ratio': (
                                sum(cf.network_flow for cf in cash_flows) / 
                                sum(cf.total_flow for cf in cash_flows)
                                if sum(cf.total_flow for cf in cash_flows) > 0 else 0
                            )
                        }
                        
                        results.append(result)
                        
                    except Exception as e:
                        logger.warning(f"Error en configuración PV={pv_mw:.1f}, BESS={bess_mwh:.1f}, Q={q_night_mvar:.1f}: {e}")
        
        df_results = pd.DataFrame(results)
        logger.info(f"Cluster {cluster_id}: {len(df_results)} configuraciones analizadas")
        
        return df_results
    
    def _calculate_capex(self, pv_mw: float, bess_mwh: float, q_night_mvar: float) -> Dict:
        """Calcula CAPEX desglosado"""
        # PV
        pv_capex = pv_mw * self.economic_params['pv_capex_usd_mw']
        
        # BESS (energía + potencia)
        bess_energy_capex = bess_mwh * self.economic_params['bess_capex_usd_mwh']
        bess_power_capex = (bess_mwh / 4) * self.economic_params['bess_capex_usd_mw'] if bess_mwh > 0 else 0
        bess_capex = bess_energy_capex + bess_power_capex
        
        # STATCOM/Q night
        if q_night_mvar <= pv_mw * 0.3:
            q_capex = q_night_mvar * self.economic_params['statcom_capex_usd_mvar'] * 0.3
        else:
            q_capex = q_night_mvar * self.economic_params['statcom_capex_usd_mvar']
        
        # BOS y conexión
        subtotal = pv_capex + bess_capex + q_capex
        bos_capex = subtotal * 0.15
        
        return {
            'pv': pv_capex,
            'bess': bess_capex,
            'q_night': q_capex,
            'bos': bos_capex,
            'total': subtotal + bos_capex
        }
    
    def create_value_surfaces(self, cluster_results: pd.DataFrame, cluster_id: str):
        """
        Crea visualizaciones de superficies de valor para un cluster.
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Superficies de Valor - Cluster {cluster_id}', fontsize=16)
        
        # 1. NPV vs PV y BESS (sin Q)
        ax1 = axes[0, 0]
        data_pivot = cluster_results[cluster_results['q_ratio'] == 0].pivot_table(
            values='npv_musd', index='bess_hours', columns='pv_ratio'
        )
        sns.heatmap(data_pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=0, ax=ax1)
        ax1.set_title('NPV (M USD) - Sin Q nocturno')
        ax1.set_xlabel('Ratio PV/Demanda')
        ax1.set_ylabel('Horas BESS')
        
        # 2. NPV vs PV y Q (sin BESS)
        ax2 = axes[0, 1]
        data_pivot = cluster_results[cluster_results['bess_hours'] == 0].pivot_table(
            values='npv_musd', index='q_ratio', columns='pv_ratio'
        )
        sns.heatmap(data_pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=0, ax=ax2)
        ax2.set_title('NPV (M USD) - Sin BESS')
        ax2.set_xlabel('Ratio PV/Demanda')
        ax2.set_ylabel('Ratio Q/PV')
        
        # 3. Ratio beneficios red vs configuración
        ax3 = axes[1, 0]
        # Mejor configuración para cada combinación PV-BESS
        best_configs = cluster_results.loc[cluster_results.groupby(['pv_ratio', 'bess_hours'])['npv_musd'].idxmax()]
        data_pivot = best_configs.pivot_table(
            values='network_benefit_ratio', index='bess_hours', columns='pv_ratio'
        )
        sns.heatmap(data_pivot, annot=True, fmt='.1%', cmap='YlOrRd', ax=ax3)
        ax3.set_title('Ratio Beneficios Red/Total')
        ax3.set_xlabel('Ratio PV/Demanda')
        ax3.set_ylabel('Horas BESS')
        
        # 4. IRR vs configuración
        ax4 = axes[1, 1]
        data_pivot = best_configs.pivot_table(
            values='irr_percent', index='bess_hours', columns='pv_ratio'
        )
        sns.heatmap(data_pivot, annot=True, fmt='.0f', cmap='viridis', vmin=0, vmax=30, ax=ax4)
        ax4.set_title('TIR (%)')
        ax4.set_xlabel('Ratio PV/Demanda')
        ax4.set_ylabel('Horas BESS')
        
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / f'value_surfaces_cluster_{cluster_id}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_flow_breakdown(self, cluster_results: pd.DataFrame, cluster_id: str):
        """
        Crea visualización del desglose de flujos para las mejores configuraciones.
        """
        # Top 5 configuraciones por NPV
        top_configs = cluster_results.nlargest(5, 'npv_musd')
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Preparar datos para gráfico de barras apiladas
        configs = []
        pv_flows = []
        network_flows = []
        labels = []
        
        for idx, row in top_configs.iterrows():
            config_label = f"PV:{row['pv_mw']:.0f}MW\nBESS:{row['bess_mwh']:.0f}MWh\nQ:{row['q_night_mvar']:.0f}MVAr"
            labels.append(config_label)
            pv_flows.append(row['avg_pv_flow_musd'])
            network_flows.append(row['avg_network_flow_musd'])
        
        x = np.arange(len(labels))
        width = 0.6
        
        # Crear barras apiladas
        p1 = ax.bar(x, pv_flows, width, label='Flujo PV', color='#FFA500')
        p2 = ax.bar(x, network_flows, width, bottom=pv_flows, label='Flujo Red', color='#4169E1')
        
        # Añadir valores
        for i, (pv, net) in enumerate(zip(pv_flows, network_flows)):
            total = pv + net
            ax.text(i, total + 0.1, f'{total:.1f}', ha='center', va='bottom', fontweight='bold')
            ax.text(i, pv/2, f'{pv:.1f}', ha='center', va='center', color='white')
            ax.text(i, pv + net/2, f'{net:.1f}', ha='center', va='center', color='white')
        
        ax.set_ylabel('Flujo Anual Promedio (M USD)')
        ax.set_title(f'Desglose de Flujos - Top 5 Configuraciones - Cluster {cluster_id}')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=0, ha='center')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        # Añadir línea de CAPEX para referencia
        for i, row in enumerate(top_configs.itertuples()):
            capex = row.capex_musd
            ax.hlines(capex/10, i-0.3, i+0.3, colors='red', linestyles='dashed', 
                     label='CAPEX/10' if i == 0 else "")
        
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / f'flow_breakdown_cluster_{cluster_id}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def analyze_all_clusters(self, clusters_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analiza todos los clusters y genera resultados consolidados.
        """
        all_results = []
        
        # Analizar top 5 clusters por tamaño
        top_clusters = clusters_df.nlargest(5, 'peak_demand_mw')
        
        for idx, cluster in top_clusters.iterrows():
            logger.info(f"\nAnalizando cluster {cluster['cluster_id']} ({idx+1}/{len(top_clusters)})")
            
            # Analizar configuraciones
            cluster_results = self.analyze_cluster(cluster)
            all_results.append(cluster_results)
            
            # Crear visualizaciones
            self.create_value_surfaces(cluster_results, cluster['cluster_id'])
            self.create_flow_breakdown(cluster_results, cluster['cluster_id'])
            
            # Guardar resultados del cluster
            cluster_results.to_csv(
                RESULTS_DIR / f'flows_cluster_{cluster["cluster_id"]}.csv',
                index=False
            )
        
        # Consolidar resultados
        df_all = pd.concat(all_results, ignore_index=True)
        
        # Identificar configuraciones óptimas por cluster
        optimal_configs = df_all.loc[df_all.groupby('cluster_id')['npv_musd'].idxmax()]
        
        return df_all, optimal_configs
    
    def generate_summary_report(self, all_results: pd.DataFrame, optimal_configs: pd.DataFrame):
        """
        Genera reporte resumen del análisis de flujos.
        """
        summary = {
            'analysis_date': datetime.now().isoformat(),
            'clusters_analyzed': optimal_configs['cluster_id'].nunique(),
            'total_configurations': len(all_results),
            'optimal_configurations': len(optimal_configs),
            
            # Métricas agregadas de configuraciones óptimas
            'total_optimal_pv_mw': optimal_configs['pv_mw'].sum(),
            'total_optimal_bess_mwh': optimal_configs['bess_mwh'].sum(),
            'total_optimal_q_mvar': optimal_configs['q_night_mvar'].sum(),
            'total_optimal_capex_musd': optimal_configs['capex_musd'].sum(),
            'total_optimal_npv_musd': optimal_configs['npv_musd'].sum(),
            'avg_optimal_irr_percent': optimal_configs['irr_percent'].mean(),
            'avg_optimal_payback_years': optimal_configs['payback_years'].mean(),
            
            # Flujos anuales totales
            'total_annual_pv_flow_musd': optimal_configs['avg_pv_flow_musd'].sum(),
            'total_annual_network_flow_musd': optimal_configs['avg_network_flow_musd'].sum(),
            'total_annual_flow_musd': optimal_configs['avg_total_flow_musd'].sum(),
            'avg_network_benefit_ratio': optimal_configs['network_benefit_ratio'].mean(),
            
            # Estadísticas por tipo de configuración
            'pv_only_count': len(optimal_configs[(optimal_configs['bess_hours'] == 0) & (optimal_configs['q_ratio'] == 0)]),
            'pv_bess_count': len(optimal_configs[(optimal_configs['bess_hours'] > 0) & (optimal_configs['q_ratio'] == 0)]),
            'pv_q_count': len(optimal_configs[(optimal_configs['bess_hours'] == 0) & (optimal_configs['q_ratio'] > 0)]),
            'full_config_count': len(optimal_configs[(optimal_configs['bess_hours'] > 0) & (optimal_configs['q_ratio'] > 0)]),
        }
        
        # Guardar resumen
        with open(RESULTS_DIR / 'analysis_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Mostrar resumen
        logger.info("\n=== RESUMEN DEL ANÁLISIS DE FLUJOS ===")
        logger.info(f"Clusters analizados: {summary['clusters_analyzed']}")
        logger.info(f"Configuraciones evaluadas: {summary['total_configurations']}")
        logger.info(f"\nCapacidad óptima total:")
        logger.info(f"  - PV: {summary['total_optimal_pv_mw']:.1f} MW")
        logger.info(f"  - BESS: {summary['total_optimal_bess_mwh']:.1f} MWh")
        logger.info(f"  - Q nocturno: {summary['total_optimal_q_mvar']:.1f} MVAr")
        logger.info(f"\nMétricas financieras:")
        logger.info(f"  - CAPEX total: ${summary['total_optimal_capex_musd']:.1f}M USD")
        logger.info(f"  - NPV total: ${summary['total_optimal_npv_musd']:.1f}M USD")
        logger.info(f"  - TIR promedio: {summary['avg_optimal_irr_percent']:.1f}%")
        logger.info(f"  - Payback promedio: {summary['avg_optimal_payback_years']:.1f} años")
        logger.info(f"\nFlujos anuales:")
        logger.info(f"  - Flujo PV: ${summary['total_annual_pv_flow_musd']:.1f}M USD/año")
        logger.info(f"  - Flujo Red: ${summary['total_annual_network_flow_musd']:.1f}M USD/año")
        logger.info(f"  - Flujo Total: ${summary['total_annual_flow_musd']:.1f}M USD/año")
        logger.info(f"  - Ratio beneficios red: {summary['avg_network_benefit_ratio']:.1%}")
        
        return summary


def main():
    """Función principal"""
    logger.info("=== FASE 3 - CÁLCULO DE FLUJOS INTEGRADOS ===")
    logger.info(f"Iniciando: {datetime.now()}")
    
    try:
        # Inicializar analizador
        analyzer = IntegratedFlowAnalyzer()
        
        # Cargar datos de clusters
        clusters = analyzer.load_cluster_data()
        logger.info(f"Cargados {len(clusters)} clusters")
        
        # Analizar todos los clusters
        all_results, optimal_configs = analyzer.analyze_all_clusters(clusters)
        
        # Guardar resultados consolidados
        all_results.to_parquet(RESULTS_DIR / 'all_integrated_flows.parquet', index=False)
        optimal_configs.to_csv(RESULTS_DIR / 'optimal_configurations.csv', index=False)
        
        # Generar reporte resumen
        summary = analyzer.generate_summary_report(all_results, optimal_configs)
        
        logger.info("\n✅ Análisis de flujos completado exitosamente")
        logger.info(f"Resultados guardados en: {RESULTS_DIR}")
        
    except Exception as e:
        logger.error(f"❌ Error en análisis: {str(e)}")
        raise
    
    finally:
        logger.info(f"Finalizado: {datetime.now()}")


if __name__ == "__main__":
    main()