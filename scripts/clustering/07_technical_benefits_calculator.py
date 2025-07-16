#!/usr/bin/env python3
"""
FASE 2 - Script 07: Technical Benefits Calculator
================================================
Cálculo de beneficios técnicos de GD solar sin BESS para cada cluster.
Incluye mejora de tensión, reducción de pérdidas y alivio de transformadores.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sqlite3
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
CLUSTERING_DIR = REPORTS_DIR / "clustering"

class TechnicalBenefitsCalculator:
    """
    Calculador de beneficios técnicos de GD solar sin BESS.
    Basado en el marco teórico de sistemas de distribución.
    """
    
    def __init__(self, production_mwh_per_mw=1850):
        """
        Inicializa calculador con parámetros de producción solar.
        
        Args:
            production_mwh_per_mw: Producción anual por MW instalado (tracker+bifacial)
        """
        self.production_annual = production_mwh_per_mw  # MWh/año/MW
        self.hours_year = 8760
        self.capacity_factor = production_mwh_per_mw / self.hours_year  # ~0.211
        
        # Perfiles típicos de generación solar (% de capacidad por hora)
        self.solar_profile = self._create_solar_profile()
        
        # Perfiles típicos de demanda por tipo de usuario
        self.demand_profiles = self._create_demand_profiles()
        
        # Parámetros técnicos
        self.voltage_nominal = 13.2  # kV (MT típica en Argentina)
        self.voltage_limits = {'min': 0.95, 'max': 1.05}  # pu
        self.loss_factor = 0.08  # Pérdidas típicas 8%
        
    def _create_solar_profile(self):
        """Crea perfil horario típico de generación solar con tracker"""
        hours = np.arange(24)
        
        # Perfil simplificado con tracker (más plano que fijo)
        profile = np.zeros(24)
        
        # Generación entre 6 AM y 7 PM con tracker
        sunrise, sunset = 6, 19
        solar_hours = sunset - sunrise
        
        for h in range(sunrise, sunset):
            # Perfil más plano con tracker
            angle = (h - sunrise) * np.pi / solar_hours
            profile[h] = 0.85 * np.sin(angle) + 0.15
        
        # Normalizar para que el promedio diario sea el capacity factor
        daily_average = profile.mean()
        if daily_average > 0:
            profile = profile * self.capacity_factor / daily_average
            
        return profile
    
    def _create_demand_profiles(self):
        """Crea perfiles de demanda típicos por tipo de usuario"""
        profiles = {}
        
        # Residencial: pico nocturno
        profiles['Residencial'] = np.array([
            0.6, 0.5, 0.4, 0.4, 0.4, 0.5,  # 0-5
            0.7, 0.8, 0.7, 0.6, 0.5, 0.5,  # 6-11
            0.5, 0.5, 0.6, 0.7, 0.8, 0.9,  # 12-17
            1.0, 1.0, 0.9, 0.8, 0.7, 0.6   # 18-23
        ])
        
        # Comercial: pico diurno
        profiles['Comercial'] = np.array([
            0.3, 0.3, 0.3, 0.3, 0.3, 0.3,  # 0-5
            0.4, 0.6, 0.8, 0.9, 1.0, 1.0,  # 6-11
            0.9, 0.9, 1.0, 1.0, 0.9, 0.8,  # 12-17
            0.7, 0.5, 0.4, 0.3, 0.3, 0.3   # 18-23
        ])
        
        # Industrial: relativamente plano en horario laboral
        profiles['Industrial'] = np.array([
            0.4, 0.4, 0.4, 0.4, 0.4, 0.5,  # 0-5
            0.7, 0.9, 1.0, 1.0, 1.0, 1.0,  # 6-11
            1.0, 1.0, 1.0, 1.0, 0.9, 0.7,  # 12-17
            0.5, 0.4, 0.4, 0.4, 0.4, 0.4   # 18-23
        ])
        
        # Otros perfiles
        profiles['Oficial'] = profiles['Comercial'] * 0.9  # Similar a comercial
        profiles['Rural'] = profiles['Residencial'] * 0.8 + profiles['Industrial'] * 0.2
        profiles['Riego'] = np.array([
            0.2, 0.2, 0.2, 0.2, 0.2, 0.3,  # 0-5
            0.5, 0.8, 1.0, 1.0, 1.0, 1.0,  # 6-11
            1.0, 1.0, 0.8, 0.6, 0.4, 0.3,  # 12-17
            0.2, 0.2, 0.2, 0.2, 0.2, 0.2   # 18-23
        ])
        profiles['Otros'] = (profiles['Residencial'] + profiles['Comercial']) / 2
        profiles['Mixto'] = (profiles['Residencial'] + profiles['Comercial'] + profiles['Industrial']) / 3
        
        return profiles
    
    def calculate_voltage_improvement(self, cluster_data):
        """
        Calcula mejora de tensión esperada con GD solar.
        Basado en ΔV ≈ (R*P_GD + X*Q_GD) / V_nom
        """
        # Potencia GD recomendada
        p_gd_mw = cluster_data['gd_recomendada_mw']
        
        # Impedancia promedio del cluster (estimada si no está disponible)
        if 'impedance_total' in cluster_data:
            z_total = cluster_data['impedance_total']
        else:
            # Estimar basado en distancia y número de transformadores
            km_avg = cluster_data.get('radio_km', 5)
            z_per_km = 0.5  # Ohm/km típico para MT
            z_total = km_avg * z_per_km
        
        # Factor R/X típico para redes de distribución
        r_x_ratio = 2.0  # Redes de distribución son más resistivas
        r_total = z_total * r_x_ratio / np.sqrt(1 + r_x_ratio**2)
        
        # Mejora de tensión en pu durante generación solar
        # Asumiendo factor de potencia unitario (Q_GD = 0)
        delta_v_pu = (r_total * p_gd_mw * 1000) / (self.voltage_nominal**2)
        
        # Convertir a porcentaje
        voltage_improvement_percent = delta_v_pu * 100
        
        # Limitar mejora razonable
        voltage_improvement_percent = min(voltage_improvement_percent, 5.0)
        
        return {
            'voltage_improvement_percent': round(voltage_improvement_percent, 2),
            'transformers_benefited': cluster_data['n_transformadores'],
            'critical_hours_improved': 'Horario solar (7 AM - 6 PM)',
            'risk_overvoltage': 'Bajo' if cluster_data['perfil_dominante'] in ['Comercial', 'Industrial'] else 'Medio'
        }
    
    def calculate_loss_reduction(self, cluster_data):
        """
        Calcula reducción de pérdidas técnicas con GD.
        Las pérdidas son proporcionales a I²R.
        """
        # Potencia del cluster
        p_cluster_mva = cluster_data['potencia_total_mva']
        p_gd_mw = cluster_data['gd_recomendada_mw']
        
        # Perfil dominante para estimar coincidencia
        perfil = cluster_data['perfil_dominante']
        demand_profile = self.demand_profiles.get(perfil, self.demand_profiles['Mixto'])
        
        # Calcular coincidencia horaria promedio
        coincidence_factor = np.sum(self.solar_profile * demand_profile) / np.sum(self.solar_profile)
        
        # Reducción de corriente en alimentador principal
        current_reduction_factor = (p_gd_mw / p_cluster_mva) * coincidence_factor
        
        # Reducción de pérdidas (proporcional a I²)
        # Si la corriente se reduce en factor f, las pérdidas se reducen en f²
        loss_reduction_factor = current_reduction_factor ** 2
        
        # Pérdidas base estimadas
        base_losses_mw = p_cluster_mva * self.loss_factor
        losses_reduced_mw = base_losses_mw * loss_reduction_factor
        
        # Energía anual ahorrada
        energy_saved_mwh = losses_reduced_mw * self.hours_year * coincidence_factor
        
        return {
            'loss_reduction_percent': round(loss_reduction_factor * 100, 1),
            'losses_reduced_mw': round(losses_reduced_mw, 3),
            'energy_saved_mwh_year': round(energy_saved_mwh, 0),
            'coincidence_factor': round(coincidence_factor, 2),
            'economic_value_usd_year': round(energy_saved_mwh * 50, 0)  # ~50 USD/MWh
        }
    
    def calculate_transformer_relief(self, cluster_data):
        """
        Calcula alivio de carga en transformadores durante picos.
        """
        # Utilización estimada del cluster
        utilization = cluster_data.get('C4_promedio', 0.7)  # Usar cargabilidad como proxy
        
        # Potencia GD vs capacidad del cluster
        relief_factor = cluster_data['gd_recomendada_mw'] / cluster_data['potencia_total_mva']
        
        # Perfil para determinar coincidencia con picos
        perfil = cluster_data['perfil_dominante']
        
        # Factor de alivio durante picos (depende del perfil)
        if perfil in ['Comercial', 'Industrial', 'Oficial']:
            peak_relief_factor = relief_factor * 0.8  # Alta coincidencia
        elif perfil == 'Riego':
            peak_relief_factor = relief_factor * 0.6  # Media coincidencia
        else:
            peak_relief_factor = relief_factor * 0.3  # Baja coincidencia
        
        # Nueva utilización durante picos solares
        new_utilization = utilization * (1 - peak_relief_factor)
        
        # Extensión de vida útil (regla empírica: -10°C = +100% vida)
        # Reducción de temperatura proporcional a reducción de carga²
        temp_reduction_factor = peak_relief_factor ** 2
        life_extension_factor = 1 + temp_reduction_factor
        
        # Transformadores que pasan de crítico a normal
        transformers_relieved = 0
        if utilization > 0.9 and new_utilization < 0.9:
            transformers_relieved = int(cluster_data['n_transformadores'] * 0.3)
        elif utilization > 0.8 and new_utilization < 0.8:
            transformers_relieved = int(cluster_data['n_transformadores'] * 0.2)
        
        return {
            'utilization_reduction_percent': round(peak_relief_factor * 100, 1),
            'new_utilization_peak': round(new_utilization, 2),
            'life_extension_factor': round(life_extension_factor, 1),
            'transformers_relieved': transformers_relieved,
            'investment_deferred_years': round(5 * life_extension_factor - 5, 1),
            'temperature_reduction_c': round(temp_reduction_factor * 20, 1)  # ~20°C típico
        }
    
    def calculate_power_quality_improvement(self, cluster_data):
        """
        Estima mejora en calidad de servicio (reducción de interrupciones).
        """
        # Tasa de falla actual
        failure_rate = cluster_data['tasa_falla']
        
        # Factor de mejora basado en beneficios técnicos
        voltage_factor = 0.3  # 30% de fallas por baja tensión
        thermal_factor = 0.2  # 20% de fallas por sobrecarga
        
        # Mejora esperada
        if cluster_data['perfil_dominante'] in ['Comercial', 'Industrial']:
            improvement_factor = voltage_factor * 0.8 + thermal_factor * 0.7
        else:
            improvement_factor = voltage_factor * 0.5 + thermal_factor * 0.4
        
        # Nueva tasa de falla
        new_failure_rate = failure_rate * (1 - improvement_factor)
        
        # Usuarios beneficiados
        users_improved = int(cluster_data['n_usuarios'] * improvement_factor)
        
        # Reducción de ENS (Energía No Suministrada)
        # Asumiendo 4 horas promedio por falla
        ens_reduced_mwh = (failure_rate - new_failure_rate) * cluster_data['potencia_total_mva'] * 4
        
        return {
            'failure_reduction_percent': round(improvement_factor * 100, 1),
            'new_failure_rate': round(new_failure_rate, 3),
            'users_quality_improved': users_improved,
            'ens_reduced_mwh_year': round(ens_reduced_mwh * 12, 0),  # Mensual a anual
            'saifi_improvement': round(improvement_factor * 0.5, 2),  # ~50% de impacto en SAIFI
            'saidi_improvement_hours': round(improvement_factor * 4, 1)  # Horas anuales
        }
    
    def calculate_grid_investment_deferral(self, cluster_data):
        """
        Calcula el diferimiento de inversiones en red.
        """
        # Crecimiento de demanda típico
        demand_growth_rate = 0.03  # 3% anual
        
        # Capacidad liberada por GD
        capacity_freed_mva = cluster_data['gd_recomendada_mw'] * 0.8  # Factor de coincidencia
        
        # Años de diferimiento
        years_deferred = np.log(1 + capacity_freed_mva / cluster_data['potencia_total_mva']) / np.log(1 + demand_growth_rate)
        
        # Costo de expansión evitado (USD/MVA)
        expansion_cost_per_mva = 150000  # Típico para MT
        
        # Valor presente del diferimiento
        discount_rate = 0.08
        npv_deferral = expansion_cost_per_mva * capacity_freed_mva / ((1 + discount_rate) ** years_deferred)
        
        return {
            'capacity_freed_mva': round(capacity_freed_mva, 2),
            'years_deferred': round(years_deferred, 1),
            'investment_deferred_usd': round(expansion_cost_per_mva * capacity_freed_mva, 0),
            'npv_deferral_usd': round(npv_deferral, 0),
            'irr_improvement_percent': round(years_deferred * 2, 1)  # Aproximación
        }

def load_cluster_data():
    """Carga datos de clusters desde el análisis previo"""
    logger.info("Cargando datos de clusters...")
    
    cluster_file = CLUSTERING_DIR / "cluster_ranking_ias.csv"
    
    if cluster_file.exists():
        df = pd.read_csv(cluster_file)
        logger.info(f"Cargados {len(df)} clusters")
        return df
    else:
        logger.error("No se encontró archivo de clusters. Ejecutar script 06 primero.")
        return None

def analyze_technical_benefits(df_clusters):
    """Analiza beneficios técnicos para todos los clusters"""
    logger.info("Calculando beneficios técnicos para todos los clusters...")
    
    calculator = TechnicalBenefitsCalculator(production_mwh_per_mw=1850)
    
    # Lista para almacenar resultados
    benefits_list = []
    
    for idx, cluster in df_clusters.iterrows():
        logger.info(f"Analizando cluster {cluster['cluster_id']} (Ranking #{cluster['ranking']})")
        
        # Calcular todos los beneficios
        voltage = calculator.calculate_voltage_improvement(cluster)
        losses = calculator.calculate_loss_reduction(cluster)
        transformer = calculator.calculate_transformer_relief(cluster)
        quality = calculator.calculate_power_quality_improvement(cluster)
        deferral = calculator.calculate_grid_investment_deferral(cluster)
        
        # Compilar resultados
        benefits = {
            'cluster_id': cluster['cluster_id'],
            'ranking': cluster['ranking'],
            **{f'voltage_{k}': v for k, v in voltage.items()},
            **{f'losses_{k}': v for k, v in losses.items()},
            **{f'transformer_{k}': v for k, v in transformer.items()},
            **{f'quality_{k}': v for k, v in quality.items()},
            **{f'deferral_{k}': v for k, v in deferral.items()},
            # Beneficio total anual estimado
            'total_benefit_usd_year': (
                losses['economic_value_usd_year'] +
                quality['ens_reduced_mwh_year'] * 100 +  # 100 USD/MWh ENS
                deferral['npv_deferral_usd'] / 10  # Anualizado a 10 años
            )
        }
        
        benefits_list.append(benefits)
    
    # Crear DataFrame con resultados
    df_benefits = pd.DataFrame(benefits_list)
    
    # Agregar score de beneficio técnico total
    df_benefits['technical_benefit_score'] = (
        df_benefits['voltage_voltage_improvement_percent'] / 5 * 0.3 +
        df_benefits['losses_loss_reduction_percent'] / 50 * 0.3 +
        df_benefits['quality_failure_reduction_percent'] / 50 * 0.2 +
        df_benefits['transformer_utilization_reduction_percent'] / 30 * 0.2
    ).clip(0, 1)
    
    return df_benefits

def create_benefits_visualizations(df_benefits, df_clusters):
    """Crea visualizaciones de beneficios técnicos"""
    logger.info("Creando visualizaciones de beneficios técnicos...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Figura principal con subplots
    fig = plt.figure(figsize=(20, 16))
    
    # Layout personalizado
    gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
    
    # 1. Beneficios por categoría - Top 10 clusters
    ax1 = fig.add_subplot(gs[0, :2])
    top_10 = df_benefits.head(10)
    
    categories = ['Tensión', 'Pérdidas', 'Transformadores', 'Calidad']
    values = [
        top_10['voltage_voltage_improvement_percent'].values,
        top_10['losses_loss_reduction_percent'].values,
        top_10['transformer_utilization_reduction_percent'].values,
        top_10['quality_failure_reduction_percent'].values
    ]
    
    x = np.arange(len(top_10))
    width = 0.2
    
    for i, (cat, val) in enumerate(zip(categories, values)):
        ax1.bar(x + i*width, val, width, label=cat)
    
    ax1.set_xlabel('Ranking Cluster')
    ax1.set_ylabel('Mejora (%)')
    ax1.set_title('Beneficios Técnicos por Categoría - Top 10 Clusters')
    ax1.set_xticks(x + width*1.5)
    ax1.set_xticklabels([f"#{r}" for r in top_10['ranking']])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Correlación IAS vs Beneficio Técnico
    ax2 = fig.add_subplot(gs[0, 2])
    
    # Merge con datos de IAS
    merged = pd.merge(df_benefits, df_clusters[['cluster_id', 'ias_promedio', 'perfil_dominante']], on='cluster_id')
    
    scatter = ax2.scatter(merged['ias_promedio'], 
                         merged['technical_benefit_score'],
                         c=merged['ranking'],
                         s=100,
                         cmap='RdYlGn_r',
                         alpha=0.7)
    
    ax2.set_xlabel('IAS Score Promedio')
    ax2.set_ylabel('Score Beneficio Técnico')
    ax2.set_title('Correlación IAS vs Beneficio Técnico')
    plt.colorbar(scatter, ax=ax2, label='Ranking')
    
    # Línea de tendencia
    z = np.polyfit(merged['ias_promedio'], merged['technical_benefit_score'], 1)
    p = np.poly1d(z)
    ax2.plot(merged['ias_promedio'], p(merged['ias_promedio']), "r--", alpha=0.8)
    
    # 3. Reducción de pérdidas por perfil
    ax3 = fig.add_subplot(gs[1, 0])
    
    loss_by_profile = merged.groupby('perfil_dominante')['losses_loss_reduction_percent'].agg(['mean', 'std'])
    
    ax3.bar(loss_by_profile.index, loss_by_profile['mean'], 
            yerr=loss_by_profile['std'], capsize=5)
    ax3.set_xlabel('Perfil Dominante')
    ax3.set_ylabel('Reducción de Pérdidas (%)')
    ax3.set_title('Reducción de Pérdidas por Perfil de Usuario')
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # 4. Mejora de tensión - mapa de calor
    ax4 = fig.add_subplot(gs[1, 1])
    
    # Matriz de mejora de tensión para top 15
    voltage_data = df_benefits.head(15)[['ranking', 'voltage_voltage_improvement_percent']].set_index('ranking')
    
    # Crear matriz para heatmap (simulando horas del día)
    hours = range(6, 19)  # Horas solares
    voltage_matrix = np.zeros((len(voltage_data), len(hours)))
    
    # Simular perfil de mejora durante el día
    solar_factor = calculator.solar_profile[6:19] / calculator.solar_profile[6:19].max()
    for i, improvement in enumerate(voltage_data['voltage_voltage_improvement_percent']):
        voltage_matrix[i, :] = improvement * solar_factor
    
    im = ax4.imshow(voltage_matrix, cmap='RdYlGn', aspect='auto')
    ax4.set_xticks(range(len(hours)))
    ax4.set_xticklabels(hours)
    ax4.set_yticks(range(len(voltage_data)))
    ax4.set_yticklabels([f"#{r}" for r in voltage_data.index])
    ax4.set_xlabel('Hora del Día')
    ax4.set_ylabel('Ranking Cluster')
    ax4.set_title('Mejora de Tensión Durante el Día (%)')
    plt.colorbar(im, ax=ax4)
    
    # 5. Vida útil extendida de transformadores
    ax5 = fig.add_subplot(gs[1, 2])
    
    top_15 = df_benefits.head(15)
    ax5.barh(range(len(top_15)), top_15['transformer_life_extension_factor'])
    ax5.set_yticks(range(len(top_15)))
    ax5.set_yticklabels([f"#{r}" for r in top_15['ranking']])
    ax5.set_xlabel('Factor de Extensión de Vida Útil')
    ax5.set_ylabel('Ranking Cluster')
    ax5.set_title('Extensión de Vida Útil de Transformadores')
    ax5.grid(True, axis='x', alpha=0.3)
    
    # Agregar línea de referencia
    ax5.axvline(x=1.0, color='red', linestyle='--', alpha=0.5, label='Sin mejora')
    ax5.legend()
    
    # 6. Beneficio económico total
    ax6 = fig.add_subplot(gs[2, :])
    
    # Componentes del beneficio económico
    top_10_eco = df_benefits.head(10)
    
    components = {
        'Ahorro Pérdidas': top_10_eco['losses_economic_value_usd_year'] / 1000,
        'Valor ENS': top_10_eco['quality_ens_reduced_mwh_year'] * 0.1,  # 100 USD/MWh -> k USD
        'Diferimiento': top_10_eco['deferral_npv_deferral_usd'] / 10000  # 10k USD
    }
    
    bottom = np.zeros(len(top_10_eco))
    for label, values in components.items():
        ax6.bar(range(len(top_10_eco)), values, bottom=bottom, label=label)
        bottom += values
    
    ax6.set_xlabel('Ranking Cluster')
    ax6.set_ylabel('Beneficio Económico (k USD/año)')
    ax6.set_title('Composición del Beneficio Económico Anual - Top 10')
    ax6.set_xticks(range(len(top_10_eco)))
    ax6.set_xticklabels([f"#{r}" for r in top_10_eco['ranking']])
    ax6.legend()
    ax6.grid(True, axis='y', alpha=0.3)
    
    # 7. Radar chart para cluster #1
    ax7 = fig.add_subplot(gs[3, 0], projection='polar')
    
    cluster1 = df_benefits.iloc[0]
    
    # Normalizar métricas a 0-1
    metrics = {
        'Mejora\nTensión': cluster1['voltage_voltage_improvement_percent'] / 5,
        'Reducción\nPérdidas': cluster1['losses_loss_reduction_percent'] / 50,
        'Alivio\nTransf.': cluster1['transformer_utilization_reduction_percent'] / 30,
        'Mejora\nCalidad': cluster1['quality_failure_reduction_percent'] / 50,
        'Vida Útil\nExtendida': (cluster1['transformer_life_extension_factor'] - 1),
        'Beneficio\nEconómico': cluster1['total_benefit_usd_year'] / df_benefits['total_benefit_usd_year'].max()
    }
    
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    values = list(metrics.values())
    values += values[:1]  # Cerrar el polígono
    angles += angles[:1]
    
    ax7.plot(angles, values, 'o-', linewidth=2, color='green')
    ax7.fill(angles, values, alpha=0.25, color='green')
    ax7.set_xticks(angles[:-1])
    ax7.set_xticklabels(metrics.keys())
    ax7.set_ylim(0, 1)
    ax7.set_title(f'Perfil de Beneficios - Cluster Rank #1', pad=20)
    ax7.grid(True)
    
    # 8. Comparación perfiles
    ax8 = fig.add_subplot(gs[3, 1:])
    
    # Comparar top 5 clusters
    comparison_data = []
    for i in range(min(5, len(df_benefits))):
        cluster = df_benefits.iloc[i]
        comparison_data.append({
            'Ranking': f"#{cluster['ranking']}",
            'Mejora Tensión (%)': cluster['voltage_voltage_improvement_percent'],
            'Reducción Pérdidas (%)': cluster['losses_loss_reduction_percent'],
            'Reducción Fallas (%)': cluster['quality_failure_reduction_percent'],
            'Beneficio Total (kUSD/año)': cluster['total_benefit_usd_year'] / 1000
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    df_comparison.set_index('Ranking').T.plot(kind='bar', ax=ax8)
    ax8.set_title('Comparación de Beneficios - Top 5 Clusters')
    ax8.set_xlabel('Métricas')
    ax8.set_ylabel('Valor')
    ax8.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.setp(ax8.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Guardar figura
    fig_path = CLUSTERING_DIR / "technical_benefits_analysis.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Visualizaciones guardadas en: {fig_path}")

def generate_technical_report(df_benefits, df_clusters):
    """Genera reporte técnico detallado"""
    logger.info("Generando reporte técnico detallado...")
    
    # Merge datos
    df_full = pd.merge(df_benefits, df_clusters, on='cluster_id')
    
    report = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'production_assumption': '1850 MWh/año/MW (trackers + bifacial)',
            'methodology': 'Análisis de beneficios técnicos sin BESS'
        },
        'summary': {
            'total_clusters_analyzed': len(df_benefits),
            'average_voltage_improvement': round(df_benefits['voltage_voltage_improvement_percent'].mean(), 2),
            'average_loss_reduction': round(df_benefits['losses_loss_reduction_percent'].mean(), 1),
            'total_energy_saved_gwh': round(df_benefits['losses_energy_saved_mwh_year'].sum() / 1000, 1),
            'total_users_benefited': int(df_benefits['quality_users_quality_improved'].sum()),
            'total_investment_deferred_musd': round(df_benefits['deferral_investment_deferred_usd'].sum() / 1e6, 1)
        },
        'top_clusters_technical': []
    }
    
    # Detalles de top 10 clusters
    for _, row in df_full.head(10).iterrows():
        cluster_detail = {
            'ranking': int(row['ranking_x']) if 'ranking_x' in row else int(row['ranking']),
            'cluster_id': int(row['cluster_id']),
            'basic_info': {
                'transformers': int(row['n_transformadores']),
                'users': int(row['n_usuarios']),
                'installed_capacity_mva': round(row['potencia_total_mva'], 2),
                'recommended_gd_mw': round(row['gd_recomendada_mw'], 2),
                'dominant_profile': row['perfil_dominante']
            },
            'voltage_benefits': {
                'improvement_percent': row['voltage_voltage_improvement_percent'],
                'transformers_benefited': int(row['voltage_transformers_benefited']),
                'critical_hours': row['voltage_critical_hours_improved'],
                'overvoltage_risk': row['voltage_risk_overvoltage']
            },
            'loss_reduction': {
                'reduction_percent': row['losses_loss_reduction_percent'],
                'power_reduced_mw': row['losses_losses_reduced_mw'],
                'energy_saved_mwh_year': row['losses_energy_saved_mwh_year'],
                'economic_value_usd': row['losses_economic_value_usd_year'],
                'coincidence_factor': row['losses_coincidence_factor']
            },
            'transformer_benefits': {
                'utilization_reduction': row['transformer_utilization_reduction_percent'],
                'new_peak_utilization': row['transformer_new_utilization_peak'],
                'life_extension_factor': row['transformer_life_extension_factor'],
                'temperature_reduction_c': row['transformer_temperature_reduction_c'],
                'transformers_relieved': int(row['transformer_transformers_relieved'])
            },
            'quality_improvement': {
                'failure_reduction_percent': row['quality_failure_reduction_percent'],
                'new_failure_rate': row['quality_new_failure_rate'],
                'users_improved': int(row['quality_users_quality_improved']),
                'ens_reduced_mwh': row['quality_ens_reduced_mwh_year'],
                'saifi_improvement': row['quality_saifi_improvement'],
                'saidi_reduction_hours': row['quality_saidi_improvement_hours']
            },
            'investment_deferral': {
                'capacity_freed_mva': row['deferral_capacity_freed_mva'],
                'years_deferred': row['deferral_years_deferred'],
                'investment_deferred_usd': row['deferral_investment_deferred_usd'],
                'npv_benefit_usd': row['deferral_npv_deferral_usd']
            },
            'total_annual_benefit_usd': round(row['total_benefit_usd_year'], 0)
        }
        
        report['top_clusters_technical'].append(cluster_detail)
    
    # Análisis por perfil de usuario
    profile_analysis = df_full.groupby('perfil_dominante').agg({
        'voltage_voltage_improvement_percent': 'mean',
        'losses_loss_reduction_percent': 'mean',
        'quality_failure_reduction_percent': 'mean',
        'total_benefit_usd_year': 'sum'
    }).round(2)
    
    report['analysis_by_profile'] = profile_analysis.to_dict('index')
    
    # Guardar reporte
    report_path = CLUSTERING_DIR / "technical_benefits_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Reporte técnico guardado en: {report_path}")
    
    # También guardar CSV con todos los beneficios
    csv_path = CLUSTERING_DIR / "technical_benefits_all.csv"
    df_full.to_csv(csv_path, index=False)
    logger.info(f"Datos completos guardados en: {csv_path}")
    
    return report

# Variable global para reutilizar en visualizaciones
calculator = TechnicalBenefitsCalculator(production_mwh_per_mw=1850)

def main():
    """Función principal"""
    logger.info("=== INICIANDO CÁLCULO DE BENEFICIOS TÉCNICOS ===")
    
    # Cargar datos de clusters
    df_clusters = load_cluster_data()
    if df_clusters is None:
        return
    
    # Calcular beneficios técnicos
    df_benefits = analyze_technical_benefits(df_clusters)
    
    # Crear visualizaciones
    create_benefits_visualizations(df_benefits, df_clusters)
    
    # Generar reporte
    report = generate_technical_report(df_benefits, df_clusters)
    
    # Resumen ejecutivo
    logger.info("\n=== RESUMEN EJECUTIVO ===")
    logger.info(f"Clusters analizados: {len(df_benefits)}")
    logger.info(f"Mejora de tensión promedio: {report['summary']['average_voltage_improvement']}%")
    logger.info(f"Reducción de pérdidas promedio: {report['summary']['average_loss_reduction']}%")
    logger.info(f"Energía ahorrada total: {report['summary']['total_energy_saved_gwh']} GWh/año")
    logger.info(f"Usuarios beneficiados: {report['summary']['total_users_benefited']:,}")
    logger.info(f"Inversión diferida: ${report['summary']['total_investment_deferred_musd']:.1f}M USD")
    
    logger.info("\n=== ANÁLISIS COMPLETADO ===")

if __name__ == "__main__":
    main()