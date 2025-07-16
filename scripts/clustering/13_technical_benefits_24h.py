#!/usr/bin/env python3
"""
FASE 2.5 - Script 13: Cálculo de Beneficios Técnicos 24 Horas
============================================================
Calcula beneficios técnicos considerando operación diurna (generación solar)
y nocturna (STATCOM para soporte reactivo). Incluye análisis de pérdidas,
mejora de tensión, alivio de activos y estabilidad de red.

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
BENEFITS_24H_DIR = CLUSTERING_DIR / "benefits_24h"
BENEFITS_24H_DIR.mkdir(exist_ok=True)

class TechnicalBenefits24H:
    """
    Calculador de beneficios técnicos considerando operación 24 horas.
    Incluye generación solar diurna y compensación reactiva nocturna.
    """
    
    def __init__(self):
        """Inicializa el calculador con parámetros técnicos"""
        
        # Parámetros de red
        self.voltage_nominal = 13.2  # kV típico MT
        self.power_factor_base = 0.85  # Factor de potencia base
        self.power_factor_target = 0.95  # Objetivo ENRE
        
        # Parámetros solares
        self.solar_capacity_factor = 0.211  # 1850 MWh/MW/año
        self.solar_hours = 10  # Horas efectivas de generación solar
        
        # Parámetros STATCOM nocturno
        self.statcom_efficiency = 0.98  # Eficiencia del inversor como STATCOM
        self.reactive_capacity_night = 0.3  # 30% de capacidad nominal para Q nocturno
        self.night_hours = 14  # Horas nocturnas (24 - solar_hours)
        
        # Perfiles horarios típicos
        self.load_profiles = self._create_load_profiles()
        self.solar_profile = self._create_solar_profile()
        
    def _create_load_profiles(self):
        """Crea perfiles de carga horarios por tipo de usuario"""
        hours = np.arange(24)
        
        profiles = {
            'Residencial': self._residential_profile(hours),
            'Comercial': self._commercial_profile(hours),
            'Industrial': self._industrial_profile(hours),
            'Rural': self._rural_profile(hours),
            'Mixto': self._mixed_profile(hours)
        }
        
        return profiles
    
    def _residential_profile(self, hours):
        """Perfil residencial con picos mañana y noche"""
        profile = np.ones(24) * 0.4
        # Pico matutino (6-9)
        profile[6:9] = [0.6, 0.7, 0.6]
        # Valle diurno (10-17)
        profile[10:17] = 0.3
        # Pico nocturno (18-23)
        profile[18:23] = [0.8, 0.95, 1.0, 0.9, 0.7]
        return profile
    
    def _commercial_profile(self, hours):
        """Perfil comercial con pico diurno"""
        profile = np.ones(24) * 0.2
        # Horario comercial (8-20)
        profile[8:20] = [0.5, 0.7, 0.85, 0.95, 1.0, 0.95, 0.9, 0.85, 0.8, 0.7, 0.6, 0.4]
        return profile
    
    def _industrial_profile(self, hours):
        """Perfil industrial relativamente constante"""
        profile = np.ones(24) * 0.7
        # Turnos diurnos más cargados
        profile[6:18] = 0.9
        # Pico producción
        profile[9:15] = 1.0
        return profile
    
    def _rural_profile(self, hours):
        """Perfil rural con actividad temprana"""
        profile = np.ones(24) * 0.3
        # Actividad temprana (5-8)
        profile[5:8] = [0.5, 0.7, 0.8]
        # Actividad tarde (17-21)
        profile[17:21] = [0.6, 0.8, 0.9, 0.7]
        return profile
    
    def _mixed_profile(self, hours):
        """Perfil mixto (promedio ponderado)"""
        return 0.4 * self._residential_profile(hours) + \
               0.3 * self._commercial_profile(hours) + \
               0.3 * self._industrial_profile(hours)
    
    def _create_solar_profile(self):
        """Crea perfil de generación solar típico"""
        hours = np.arange(24)
        profile = np.zeros(24)
        
        # Generación solar (6-18 horas)
        solar_hours = np.arange(6, 18)
        # Campana gaussiana centrada en mediodía
        for h in solar_hours:
            profile[h] = np.exp(-0.5 * ((h - 12) / 3) ** 2)
        
        # Normalizar para que el máximo sea 1
        profile = profile / profile.max()
        
        return profile
    
    def calculate_24h_benefits(self, cluster_data):
        """
        Calcula beneficios técnicos para operación 24 horas.
        
        Args:
            cluster_data: DataFrame con información del cluster
            
        Returns:
            dict: Beneficios calculados por período y total
        """
        logger.info(f"Calculando beneficios 24h para cluster {cluster_data['cluster_id']}")
        
        # Capacidad GD solar
        gd_mw = cluster_data['gd_recomendada_mw']
        
        # Determinar perfil de carga dominante
        perfil = cluster_data.get('perfil_dominante', 'Mixto')
        load_profile = self.load_profiles.get(perfil, self.load_profiles['Mixto'])
        
        # Potencia base del cluster
        potencia_mva = cluster_data.get('potencia_mva', cluster_data.get('gd_recomendada_mw', 0) * 3)
        
        # Calcular beneficios diurnos (generación solar)
        day_benefits = self._calculate_day_benefits(
            gd_mw, potencia_mva, load_profile, perfil
        )
        
        # Calcular beneficios nocturnos (STATCOM)
        night_benefits = self._calculate_night_benefits(
            gd_mw, potencia_mva, load_profile, perfil
        )
        
        # Beneficios agregados 24h
        total_benefits = self._aggregate_24h_benefits(day_benefits, night_benefits)
        
        return {
            'day_benefits': day_benefits,
            'night_benefits': night_benefits,
            'total_24h': total_benefits,
            'perfil_carga': perfil,
            'gd_mw': gd_mw
        }
    
    def _calculate_day_benefits(self, gd_mw, potencia_mva, load_profile, perfil):
        """Calcula beneficios durante operación solar diurna"""
        
        # Horas solares efectivas
        solar_hours = np.where(self.solar_profile > 0.1)[0]
        
        # Generación solar promedio durante el día
        solar_generation = gd_mw * self.solar_profile[solar_hours].mean()
        
        # Carga promedio durante horas solares
        day_load = potencia_mva * load_profile[solar_hours].mean()
        
        # Penetración solar
        if day_load > 0:
            solar_penetration = min(solar_generation / day_load, 1.0)
        else:
            solar_penetration = 0
        
        # Mejora de tensión diurna
        # ΔV = (P*R + Q*X) / V²
        # Asumiendo R = 0.3 Ω/km, longitud promedio 10 km
        r_total = 0.3 * 10  # Ω
        delta_v_pu = (r_total * solar_generation * 1000) / (self.voltage_nominal ** 2)
        voltage_improvement_day = min(delta_v_pu * 100, 5.0)  # Cap at 5%
        
        # Reducción de pérdidas diurnas
        # Pérdidas ∝ I² ∝ (P² + Q²)
        # Con GD local, se reduce la corriente desde la subestación
        loss_reduction_factor = solar_penetration ** 2
        base_losses_pct = 0.08  # 8% pérdidas base
        loss_reduction_day = base_losses_pct * loss_reduction_factor * 100
        
        # Alivio de transformadores
        transformer_relief_day = solar_penetration * 100
        
        # Factor de coincidencia solar-demanda
        if perfil == 'Comercial':
            coincidence_factor = 0.85
        elif perfil == 'Industrial':
            coincidence_factor = 0.80
        elif perfil == 'Residencial':
            coincidence_factor = 0.25
        else:
            coincidence_factor = 0.50
        
        # Energía desplazada diurna
        energy_displaced_mwh = solar_generation * self.solar_hours * 365 * coincidence_factor
        
        return {
            'voltage_improvement_pct': voltage_improvement_day,
            'loss_reduction_pct': loss_reduction_day,
            'transformer_relief_pct': transformer_relief_day,
            'solar_penetration': solar_penetration,
            'coincidence_factor': coincidence_factor,
            'energy_displaced_mwh_year': energy_displaced_mwh,
            'average_power_mw': solar_generation
        }
    
    def _calculate_night_benefits(self, gd_mw, potencia_mva, load_profile, perfil):
        """Calcula beneficios durante operación STATCOM nocturna"""
        
        # Horas nocturnas (sin sol)
        night_hours = np.where(self.solar_profile < 0.1)[0]
        
        # Capacidad reactiva disponible de noche
        q_capacity_mvar = gd_mw * self.reactive_capacity_night
        
        # Carga promedio nocturna
        night_load = potencia_mva * load_profile[night_hours].mean()
        
        # Demanda reactiva nocturna (basada en factor de potencia)
        # Q = P * tan(acos(pf))
        q_demand = night_load * np.tan(np.arccos(self.power_factor_base))
        
        # Compensación reactiva efectiva
        q_compensation = min(q_capacity_mvar, q_demand * 0.5)  # Compensar hasta 50%
        
        # Mejora del factor de potencia
        new_q_demand = q_demand - q_compensation
        new_pf = np.cos(np.arctan(new_q_demand / night_load))
        pf_improvement = new_pf - self.power_factor_base
        
        # Mejora de tensión nocturna
        # Mayor impacto en zonas residenciales con caída de tensión nocturna
        if perfil == 'Residencial':
            voltage_boost_factor = 1.5
        elif perfil == 'Rural':
            voltage_boost_factor = 1.3
        else:
            voltage_boost_factor = 1.0
            
        x_total = 0.4 * 10  # Reactancia, Ω
        delta_v_pu = (x_total * q_compensation * 1000) / (self.voltage_nominal ** 2)
        voltage_improvement_night = min(delta_v_pu * 100 * voltage_boost_factor, 4.0)
        
        # Reducción de pérdidas nocturnas
        # Pérdidas reactivas I²X
        q_loss_reduction = (q_compensation / q_demand) ** 2 if q_demand > 0 else 0
        base_losses_pct = 0.08  # 8% pérdidas base
        loss_reduction_night = base_losses_pct * 0.3 * q_loss_reduction * 100  # 30% de pérdidas son reactivas
        
        # Liberación de capacidad en transformadores
        # S² = P² + Q², reducir Q libera capacidad
        s_original = np.sqrt(night_load**2 + q_demand**2)
        s_new = np.sqrt(night_load**2 + new_q_demand**2)
        capacity_released = (1 - s_new/s_original) * 100 if s_original > 0 else 0
        
        # Energía reactiva compensada anual
        q_energy_mvarh = q_compensation * self.night_hours * 365
        
        # Consumo del inversor como STATCOM
        inverter_consumption_mwh = q_compensation * (1 - self.statcom_efficiency) * self.night_hours * 365
        
        return {
            'voltage_improvement_pct': voltage_improvement_night,
            'loss_reduction_pct': loss_reduction_night,
            'pf_improvement': pf_improvement,
            'new_power_factor': new_pf,
            'capacity_released_pct': capacity_released,
            'reactive_power_mvar': q_compensation,
            'reactive_energy_mvarh_year': q_energy_mvarh,
            'inverter_consumption_mwh_year': inverter_consumption_mwh
        }
    
    def _aggregate_24h_benefits(self, day_benefits, night_benefits):
        """Agrega beneficios diurnos y nocturnos ponderados por horas"""
        
        # Ponderación por horas
        day_weight = self.solar_hours / 24
        night_weight = self.night_hours / 24
        
        # Mejora de tensión promedio ponderada
        voltage_improvement_avg = (
            day_benefits['voltage_improvement_pct'] * day_weight +
            night_benefits['voltage_improvement_pct'] * night_weight
        )
        
        # Reducción de pérdidas total
        loss_reduction_total = (
            day_benefits['loss_reduction_pct'] * day_weight +
            night_benefits['loss_reduction_pct'] * night_weight
        )
        
        # Alivio de activos máximo
        asset_relief_max = max(
            day_benefits['transformer_relief_pct'],
            night_benefits['capacity_released_pct']
        )
        
        # Energía total gestionada (activa + reactiva equivalente)
        # Factor 0.3 para convertir MVArh a "MWh equivalentes" en valor
        total_energy_value = (
            day_benefits['energy_displaced_mwh_year'] +
            night_benefits['reactive_energy_mvarh_year'] * 0.3 -
            night_benefits['inverter_consumption_mwh_year']
        )
        
        # Score de beneficio 24h compuesto
        benefit_score_24h = (
            0.35 * voltage_improvement_avg / 5.0 +  # Normalizado a máx 5%
            0.35 * loss_reduction_total / 10.0 +    # Normalizado a máx 10%
            0.20 * asset_relief_max / 50.0 +        # Normalizado a máx 50%
            0.10 * (night_benefits['new_power_factor'] - 0.85) / 0.15  # Mejora FP
        )
        
        return {
            'voltage_improvement_24h_pct': voltage_improvement_avg,
            'loss_reduction_24h_pct': loss_reduction_total,
            'asset_relief_max_pct': asset_relief_max,
            'total_energy_value_mwh_year': total_energy_value,
            'power_factor_final': night_benefits['new_power_factor'],
            'benefit_score_24h': min(benefit_score_24h, 1.0),
            'operation_mode': self._determine_operation_mode(day_benefits, night_benefits)
        }
    
    def _determine_operation_mode(self, day_benefits, night_benefits):
        """Determina el modo de operación óptimo basado en beneficios"""
        
        day_score = (
            day_benefits['voltage_improvement_pct'] * 0.5 +
            day_benefits['loss_reduction_pct'] * 0.5
        )
        
        night_score = (
            night_benefits['voltage_improvement_pct'] * 0.5 +
            night_benefits['loss_reduction_pct'] * 0.3 +
            night_benefits['pf_improvement'] * 100 * 0.2
        )
        
        if day_score > night_score * 1.5:
            return "Solar-Optimized"
        elif night_score > day_score * 1.5:
            return "STATCOM-Optimized"
        else:
            return "Balanced 24h"

def analyze_all_clusters_24h(df_clusters):
    """
    Analiza beneficios 24h para todos los clusters.
    """
    logger.info("Analizando beneficios 24h para todos los clusters...")
    
    calculator = TechnicalBenefits24H()
    results = []
    
    for _, cluster in df_clusters.iterrows():
        benefits = calculator.calculate_24h_benefits(cluster)
        
        # Combinar datos del cluster con beneficios
        result = {
            'cluster_id': cluster['cluster_id'],
            'perfil_dominante': cluster.get('perfil_dominante', 'Mixto'),
            'gd_mw': benefits['gd_mw'],
            'n_usuarios': cluster.get('n_usuarios', cluster.get('usuarios_total', 0)),
            **benefits['day_benefits'],
            **{f'night_{k}': v for k, v in benefits['night_benefits'].items()},
            **benefits['total_24h']
        }
        
        results.append(result)
    
    df_benefits = pd.DataFrame(results)
    return df_benefits

def create_24h_benefits_visualization(df_benefits):
    """
    Crea visualizaciones de beneficios 24 horas.
    """
    logger.info("Creando visualizaciones de beneficios 24h...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Análisis de Beneficios Técnicos 24 Horas - GD Solar con Q at Night', fontsize=16)
    
    # 1. Comparación día vs noche por cluster
    ax = axes[0, 0]
    top_10 = df_benefits.nlargest(10, 'benefit_score_24h')
    
    x = np.arange(len(top_10))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, top_10['voltage_improvement_pct'], 
                    width, label='Día (Solar)', color='gold', alpha=0.7)
    bars2 = ax.bar(x + width/2, top_10['night_voltage_improvement_pct'], 
                    width, label='Noche (STATCOM)', color='navy', alpha=0.7)
    
    ax.set_xlabel('Cluster ID')
    ax.set_ylabel('Mejora de Tensión (%)')
    ax.set_title('Mejora de Tensión: Día vs Noche')
    ax.set_xticks(x)
    ax.set_xticklabels([f"C{int(id)}" for id in top_10['cluster_id']])
    ax.legend()
    
    # 2. Reducción de pérdidas 24h
    ax = axes[0, 1]
    df_benefits_sorted = df_benefits.sort_values('loss_reduction_24h_pct', ascending=True).tail(15)
    
    bars = ax.barh(range(len(df_benefits_sorted)), df_benefits_sorted['loss_reduction_24h_pct'])
    
    # Color por modo de operación
    colors = {'Solar-Optimized': 'gold', 'STATCOM-Optimized': 'purple', 'Balanced 24h': 'green'}
    for i, (_, row) in enumerate(df_benefits_sorted.iterrows()):
        bars[i].set_color(colors.get(row['operation_mode'], 'gray'))
    
    ax.set_yticks(range(len(df_benefits_sorted)))
    ax.set_yticklabels([f"C{int(id)}" for id in df_benefits_sorted['cluster_id']])
    ax.set_xlabel('Reducción de Pérdidas 24h (%)')
    ax.set_title('Top 15: Reducción de Pérdidas Técnicas')
    
    # 3. Factor de potencia mejorado
    ax = axes[0, 2]
    
    # Scatter plot: FP inicial vs final
    base_pf = 0.85
    ax.scatter(np.ones(len(df_benefits)) * base_pf, df_benefits['power_factor_final'],
               c=df_benefits['night_reactive_power_mvar'], cmap='viridis',
               s=df_benefits['gd_mw']*20, alpha=0.7)
    
    ax.plot([0.85, 0.95], [0.85, 0.95], 'k--', alpha=0.5)
    ax.axhline(y=0.95, color='red', linestyle='--', alpha=0.5, label='Objetivo ENRE')
    ax.set_xlabel('Factor de Potencia Base')
    ax.set_ylabel('Factor de Potencia con STATCOM')
    ax.set_title('Mejora de Factor de Potencia Nocturno')
    ax.set_xlim(0.84, 0.86)
    ax.set_ylim(0.84, 0.98)
    ax.legend()
    
    # 4. Beneficio por perfil de usuario
    ax = axes[1, 0]
    
    profile_benefits = df_benefits.groupby('perfil_dominante').agg({
        'voltage_improvement_24h_pct': 'mean',
        'loss_reduction_24h_pct': 'mean',
        'asset_relief_max_pct': 'mean',
        'benefit_score_24h': 'mean'
    })
    
    profile_benefits.plot(kind='bar', ax=ax, width=0.8)
    ax.set_xlabel('Perfil Dominante')
    ax.set_ylabel('Beneficio Promedio (%)')
    ax.set_title('Beneficios Promedio por Tipo de Perfil')
    ax.legend(['Mejora Tensión', 'Reducción Pérdidas', 'Alivio Activos', 'Score Total'], 
              bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    # 5. Energía gestionada anual
    ax = axes[1, 1]
    
    top_15_energy = df_benefits.nlargest(15, 'total_energy_value_mwh_year')
    
    # Stacked bar: energía activa vs reactiva
    active_energy = top_15_energy['energy_displaced_mwh_year']
    reactive_value = top_15_energy['night_reactive_energy_mvarh_year'] * 0.3
    
    x = np.arange(len(top_15_energy))
    bars1 = ax.bar(x, active_energy, label='Energía Activa (MWh)', color='gold')
    bars2 = ax.bar(x, reactive_value, bottom=active_energy, 
                   label='Valor Reactiva (MWh eq)', color='purple')
    
    ax.set_xlabel('Cluster ID')
    ax.set_ylabel('Energía Anual (MWh)')
    ax.set_title('Top 15: Energía Total Gestionada')
    ax.set_xticks(x)
    ax.set_xticklabels([f"C{int(id)}" for id in top_15_energy['cluster_id']], rotation=45)
    ax.legend()
    
    # 6. Score de beneficio 24h
    ax = axes[1, 2]
    
    # Heatmap de componentes del score
    score_components = df_benefits.nlargest(20, 'benefit_score_24h')[
        ['cluster_id', 'voltage_improvement_24h_pct', 'loss_reduction_24h_pct', 
         'asset_relief_max_pct', 'power_factor_final']
    ].set_index('cluster_id')
    
    # Normalizar componentes
    score_norm = score_components.copy()
    score_norm['voltage_improvement_24h_pct'] /= 5.0
    score_norm['loss_reduction_24h_pct'] /= 10.0
    score_norm['asset_relief_max_pct'] /= 50.0
    score_norm['power_factor_final'] = (score_norm['power_factor_final'] - 0.85) / 0.15
    
    sns.heatmap(score_norm.T, annot=True, fmt='.2f', cmap='RdYlGn',
                xticklabels=[f"C{int(id)}" for id in score_norm.index],
                yticklabels=['Tensión', 'Pérdidas', 'Activos', 'FP'],
                ax=ax, cbar_kws={'label': 'Score Normalizado'})
    ax.set_title('Componentes del Beneficio 24h (Top 20)')
    
    plt.tight_layout()
    
    # Guardar
    fig_path = BENEFITS_24H_DIR / "technical_benefits_24h_analysis.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Visualizaciones guardadas en: {fig_path}")

def create_operation_profile_charts(df_benefits, calculator):
    """
    Crea gráficos de perfiles de operación 24h.
    """
    logger.info("Creando gráficos de perfiles de operación...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Perfiles de Operación 24 Horas por Tipo de Usuario', fontsize=14)
    
    hours = np.arange(24)
    
    # Seleccionar clusters representativos por perfil
    profiles_to_plot = ['Comercial', 'Residencial', 'Industrial', 'Mixto']
    
    for idx, perfil in enumerate(profiles_to_plot):
        ax = axes[idx // 2, idx % 2]
        
        # Obtener perfil de carga
        load_profile = calculator.load_profiles[perfil]
        solar_profile = calculator.solar_profile
        
        # Graficar perfiles
        ax.plot(hours, load_profile, 'b-', linewidth=2, label='Demanda')
        ax.plot(hours, solar_profile, 'gold', linewidth=2, label='Generación Solar')
        
        # Área de operación STATCOM (nocturna)
        night_mask = solar_profile < 0.1
        ax.fill_between(hours, 0, 1, where=night_mask, alpha=0.2, color='purple',
                       label='Operación STATCOM')
        
        # Configuración
        ax.set_xlabel('Hora del Día')
        ax.set_ylabel('Por Unidad (p.u.)')
        ax.set_title(f'Perfil {perfil}')
        ax.set_xlim(0, 23)
        ax.set_ylim(0, 1.1)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Agregar anotaciones
        if perfil == 'Comercial':
            ax.annotate('Alta coincidencia\nsolar-demanda', xy=(12, 0.95), 
                       xytext=(14, 0.7), arrowprops=dict(arrowstyle='->', color='green'))
        elif perfil == 'Residencial':
            ax.annotate('Pico nocturno\n→ STATCOM valioso', xy=(20, 0.95), 
                       xytext=(15, 0.6), arrowprops=dict(arrowstyle='->', color='purple'))
    
    plt.tight_layout()
    
    # Guardar
    fig_path = BENEFITS_24H_DIR / "operation_profiles_24h.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Perfiles de operación guardados en: {fig_path}")

def generate_24h_benefits_report(df_benefits, df_clusters):
    """
    Genera reporte completo de beneficios 24h.
    """
    logger.info("Generando reporte de beneficios 24h...")
    
    report = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'methodology': 'Technical Benefits 24h with Q at Night',
            'total_clusters': len(df_benefits),
            'total_gd_mw': float(df_benefits['gd_mw'].sum()),
            'total_users': int(df_benefits['n_usuarios'].sum())
        },
        'summary': {
            'avg_voltage_improvement_24h': float(df_benefits['voltage_improvement_24h_pct'].mean()),
            'avg_loss_reduction_24h': float(df_benefits['loss_reduction_24h_pct'].mean()),
            'avg_power_factor_improvement': float(
                df_benefits['power_factor_final'].mean() - 0.85
            ),
            'total_energy_value_gwh_year': float(
                df_benefits['total_energy_value_mwh_year'].sum() / 1000
            )
        },
        'by_operation_mode': {},
        'top_10_clusters': [],
        'profile_analysis': {},
        'economic_benefits': {},
        'recommendations': []
    }
    
    # Análisis por modo de operación
    mode_stats = df_benefits.groupby('operation_mode').agg({
        'cluster_id': 'count',
        'gd_mw': 'sum',
        'benefit_score_24h': 'mean',
        'voltage_improvement_24h_pct': 'mean',
        'loss_reduction_24h_pct': 'mean'
    }).round(3)
    
    for mode in mode_stats.index:
        report['by_operation_mode'][mode] = {
            'n_clusters': int(mode_stats.loc[mode, 'cluster_id']),
            'total_gd_mw': float(mode_stats.loc[mode, 'gd_mw']),
            'avg_benefit_score': float(mode_stats.loc[mode, 'benefit_score_24h']),
            'avg_voltage_improvement': float(mode_stats.loc[mode, 'voltage_improvement_24h_pct']),
            'avg_loss_reduction': float(mode_stats.loc[mode, 'loss_reduction_24h_pct'])
        }
    
    # Top 10 clusters
    top_10 = df_benefits.nlargest(10, 'benefit_score_24h')
    for _, cluster in top_10.iterrows():
        report['top_10_clusters'].append({
            'cluster_id': int(cluster['cluster_id']),
            'benefit_score_24h': float(cluster['benefit_score_24h']),
            'operation_mode': cluster['operation_mode'],
            'perfil': cluster['perfil_dominante'],
            'gd_mw': float(cluster['gd_mw']),
            'usuarios': int(cluster['n_usuarios']),
            'voltage_improvement_24h': float(cluster['voltage_improvement_24h_pct']),
            'loss_reduction_24h': float(cluster['loss_reduction_24h_pct']),
            'power_factor_final': float(cluster['power_factor_final']),
            'energy_value_mwh_year': float(cluster['total_energy_value_mwh_year'])
        })
    
    # Análisis por perfil
    profile_stats = df_benefits.groupby('perfil_dominante').agg({
        'benefit_score_24h': ['mean', 'std'],
        'voltage_improvement_pct': 'mean',  # Día
        'night_voltage_improvement_pct': 'mean',  # Noche
        'operation_mode': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown'
    }).round(3)
    
    for perfil in profile_stats.index:
        report['profile_analysis'][perfil] = {
            'avg_benefit_score': float(profile_stats.loc[perfil, ('benefit_score_24h', 'mean')]),
            'std_benefit_score': float(profile_stats.loc[perfil, ('benefit_score_24h', 'std')]),
            'day_voltage_benefit': float(profile_stats.loc[perfil, ('voltage_improvement_pct', 'mean')]),
            'night_voltage_benefit': float(profile_stats.loc[perfil, ('night_voltage_improvement_pct', 'mean')]),
            'typical_operation_mode': profile_stats.loc[perfil, ('operation_mode', '<lambda>')]
        }
    
    # Beneficios económicos estimados
    # Precio energía: $60 USD/MWh
    # Valor servicios auxiliares: $20 USD/MWh equivalente
    energy_value_usd = df_benefits['energy_displaced_mwh_year'].sum() * 60
    reactive_value_usd = (df_benefits['night_reactive_energy_mvarh_year'].sum() * 0.3) * 20
    loss_savings_usd = df_benefits['loss_reduction_24h_pct'].mean() * 0.01 * energy_value_usd
    
    report['economic_benefits'] = {
        'energy_displacement_value_musd': round(energy_value_usd / 1e6, 2),
        'reactive_support_value_musd': round(reactive_value_usd / 1e6, 2),
        'loss_reduction_savings_musd': round(loss_savings_usd / 1e6, 2),
        'total_annual_benefits_musd': round((energy_value_usd + reactive_value_usd + loss_savings_usd) / 1e6, 2)
    }
    
    # Recomendaciones
    report['recommendations'] = [
        "Especificar inversores con capacidad 'Q at Night' certificada para todos los proyectos",
        f"Priorizar {len(df_benefits[df_benefits['operation_mode'] == 'Balanced 24h'])} clusters con modo balanceado para máximo beneficio",
        "Implementar sistema DERMS para coordinar despacho de reactiva nocturna en tiempo real",
        "Negociar tarifa de servicios auxiliares con CAMMESA para compensación Q nocturna",
        f"Potencial de mejora de FP promedio de {0.85:.2f} a {df_benefits['power_factor_final'].mean():.2f}",
        "Monitorear calidad de onda (THD) durante operación STATCOM nocturna",
        "Desarrollar contratos de O&M específicos considerando operación 24/7 de inversores"
    ]
    
    # Guardar reporte
    report_path = BENEFITS_24H_DIR / "technical_benefits_24h_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Reporte guardado en: {report_path}")
    
    return report

def main():
    """Función principal"""
    logger.info("=== INICIANDO ANÁLISIS DE BENEFICIOS TÉCNICOS 24 HORAS ===")
    
    # Cargar datos de clusters con IAS v3
    ias_v3_file = CLUSTERING_DIR / "ias_v3" / "cluster_ranking_ias_v3.csv"
    if ias_v3_file.exists():
        df_clusters = pd.read_csv(ias_v3_file)
        logger.info(f"Usando clusters IAS v3: {len(df_clusters)} clusters")
    else:
        # Fallback a clusters originales
        cluster_file = CLUSTERING_DIR / "cluster_ranking_ias.csv"
        if not cluster_file.exists():
            logger.error("No se encontraron archivos de clusters. Ejecutar scripts previos.")
            return
        df_clusters = pd.read_csv(cluster_file)
        logger.info(f"Usando clusters originales: {len(df_clusters)} clusters")
    
    # Verificar columnas necesarias
    if 'gd_recomendada_mw' not in df_clusters.columns:
        if 'gd_estimada_mw' in df_clusters.columns:
            df_clusters['gd_recomendada_mw'] = df_clusters['gd_estimada_mw']
        else:
            logger.error("No se encontró información de capacidad GD")
            return
    
    # Crear calculador
    calculator = TechnicalBenefits24H()
    
    # Analizar todos los clusters
    df_benefits = analyze_all_clusters_24h(df_clusters)
    
    # Estadísticas resumen
    logger.info("\n=== RESUMEN DE BENEFICIOS 24H ===")
    logger.info(f"Mejora de tensión 24h promedio: {df_benefits['voltage_improvement_24h_pct'].mean():.2f}%")
    logger.info(f"Reducción de pérdidas 24h promedio: {df_benefits['loss_reduction_24h_pct'].mean():.2f}%")
    logger.info(f"Factor de potencia mejorado promedio: {df_benefits['power_factor_final'].mean():.3f}")
    logger.info(f"Energía total gestionada: {df_benefits['total_energy_value_mwh_year'].sum()/1000:.1f} GWh/año")
    
    # Distribución por modo de operación
    mode_dist = df_benefits['operation_mode'].value_counts()
    logger.info("\nDistribución por modo de operación:")
    for mode, count in mode_dist.items():
        logger.info(f"  {mode}: {count} clusters")
    
    # Top 5 clusters por beneficio 24h
    logger.info("\nTop 5 clusters por beneficio 24h:")
    top_5 = df_benefits.nlargest(5, 'benefit_score_24h')
    for _, cluster in top_5.iterrows():
        logger.info(f"  Cluster {int(cluster['cluster_id'])}: "
                   f"Score={cluster['benefit_score_24h']:.3f}, "
                   f"Modo={cluster['operation_mode']}, "
                   f"Perfil={cluster['perfil_dominante']}")
    
    # Crear visualizaciones
    create_24h_benefits_visualization(df_benefits)
    create_operation_profile_charts(df_benefits, calculator)
    
    # Generar reporte
    report = generate_24h_benefits_report(df_benefits, df_clusters)
    
    # Guardar resultados
    output_path = BENEFITS_24H_DIR / "technical_benefits_24h.csv"
    df_benefits.to_csv(output_path, index=False)
    logger.info(f"\nBeneficios guardados en: {output_path}")
    
    # También guardar en formato parquet para siguiente script
    parquet_path = DATA_DIR / "processed" / "technical_benefits_24h.parquet"
    df_benefits.to_parquet(parquet_path)
    logger.info(f"Beneficios en parquet: {parquet_path}")
    
    logger.info("\n=== ANÁLISIS DE BENEFICIOS 24H COMPLETADO ===")

if __name__ == "__main__":
    main()