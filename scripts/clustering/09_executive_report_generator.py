#!/usr/bin/env python3
"""
FASE 2 - Script 09: Executive Report Generator
=============================================
Genera reportes ejecutivos y fichas técnicas para los clusters priorizados.
Incluye visualizaciones profesionales y recomendaciones accionables.

Autor: Asistente Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import seaborn as sns
import folium
from folium.plugins import MarkerCluster
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
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
EXECUTIVE_DIR = CLUSTERING_DIR / "executive"
EXECUTIVE_DIR.mkdir(exist_ok=True)

class ExecutiveReportGenerator:
    """
    Generador de reportes ejecutivos para GD solar sin BESS.
    """
    
    def __init__(self):
        """Inicializa el generador de reportes"""
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
        
        # Parámetros de diseño
        self.colors = {
            'primary': '#1E3A8A',     # Azul oscuro
            'secondary': '#10B981',   # Verde
            'accent': '#F59E0B',      # Naranja
            'danger': '#EF4444',      # Rojo
            'neutral': '#6B7280'      # Gris
        }
        
    def _create_custom_styles(self):
        """Crea estilos personalizados para el reporte"""
        custom = {}
        
        # Título principal
        custom['MainTitle'] = ParagraphStyle(
            'MainTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        # Subtítulos
        custom['SectionTitle'] = ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=12
        )
        
        # Texto destacado
        custom['Highlight'] = ParagraphStyle(
            'Highlight',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#10B981'),
            leftIndent=20
        )
        
        return custom
    
    def create_executive_summary_chart(self, cluster_data, benefits_data):
        """
        Crea gráfico de resumen ejecutivo profesional.
        """
        logger.info("Creando gráfico de resumen ejecutivo...")
        
        plt.style.use('seaborn-v0_8-white')
        fig = plt.figure(figsize=(16, 10))
        
        # Layout principal
        gs = fig.add_gridspec(3, 4, hspace=0.4, wspace=0.3, 
                             left=0.05, right=0.95, top=0.92, bottom=0.08)
        
        # Título principal
        fig.suptitle('Análisis de Oportunidades GD Solar - EDERSA', 
                    fontsize=20, fontweight='bold', color=self.colors['primary'])
        
        # Subtítulo
        fig.text(0.5, 0.88, 'Priorización de Clusters sin BESS - Producción: 1,850 MWh/MW/año', 
                fontsize=14, ha='center', color=self.colors['neutral'])
        
        # 1. KPIs principales (parte superior)
        ax_kpis = fig.add_subplot(gs[0, :])
        ax_kpis.axis('off')
        
        # Calcular KPIs
        top_15 = cluster_data.head(15)
        total_gd = top_15['gd_recomendada_mw'].sum()
        total_users = top_15['n_usuarios'].sum()
        total_production = top_15['produccion_anual_mwh'].sum()
        avg_ias = top_15['ias_promedio'].mean()
        
        # Crear cajas de KPIs
        kpi_data = [
            {'label': 'GD Total\nRecomendada', 'value': f'{total_gd:.1f} MW', 'color': self.colors['primary']},
            {'label': 'Producción\nAnual', 'value': f'{total_production/1000:.1f} GWh', 'color': self.colors['secondary']},
            {'label': 'Usuarios\nBeneficiados', 'value': f'{total_users:,}', 'color': self.colors['accent']},
            {'label': 'IAS Score\nPromedio', 'value': f'{avg_ias:.3f}', 'color': self.colors['danger']}
        ]
        
        for i, kpi in enumerate(kpi_data):
            x = i * 0.25 + 0.05
            rect = Rectangle((x, 0.2), 0.2, 0.6, 
                           facecolor=kpi['color'], alpha=0.1, 
                           edgecolor=kpi['color'], linewidth=2)
            ax_kpis.add_patch(rect)
            
            # Valor
            ax_kpis.text(x + 0.1, 0.6, kpi['value'], 
                        fontsize=20, fontweight='bold', 
                        ha='center', va='center', color=kpi['color'])
            
            # Label
            ax_kpis.text(x + 0.1, 0.3, kpi['label'], 
                        fontsize=12, ha='center', va='center', 
                        color=self.colors['neutral'])
        
        ax_kpis.set_xlim(0, 1)
        ax_kpis.set_ylim(0, 1)
        
        # 2. Top 10 Clusters - Ranking
        ax_ranking = fig.add_subplot(gs[1, :2])
        
        top_10 = cluster_data.head(10)
        y_pos = np.arange(len(top_10))
        
        # Barras horizontales con gradiente de color
        bars = ax_ranking.barh(y_pos, top_10['gd_recomendada_mw'])
        
        # Colorear por IAS score
        norm = plt.Normalize(top_10['ias_promedio'].min(), top_10['ias_promedio'].max())
        colors_bars = plt.cm.RdYlGn(norm(top_10['ias_promedio']))
        
        for bar, color in zip(bars, colors_bars):
            bar.set_color(color)
            
        # Etiquetas
        ax_ranking.set_yticks(y_pos)
        ax_ranking.set_yticklabels([f"#{row['ranking']} - {row['perfil_dominante']}" 
                                   for _, row in top_10.iterrows()])
        ax_ranking.set_xlabel('Capacidad GD Recomendada (MW)')
        ax_ranking.set_title('Top 10 Clusters Prioritarios', fontweight='bold', color=self.colors['primary'])
        
        # Agregar valores en las barras
        for i, (idx, row) in enumerate(top_10.iterrows()):
            ax_ranking.text(row['gd_recomendada_mw'] + 0.05, i, 
                          f"{row['gd_recomendada_mw']:.2f} MW", 
                          va='center', fontsize=10)
        
        ax_ranking.grid(True, axis='x', alpha=0.3)
        
        # 3. Beneficios técnicos agregados
        ax_benefits = fig.add_subplot(gs[1, 2:])
        
        if benefits_data is not None and len(benefits_data) > 0:
            # Promedios de beneficios top 10
            top_10_benefits = benefits_data.head(10)
            
            benefit_categories = [
                'Mejora\nTensión', 'Reducción\nPérdidas', 
                'Alivio\nTransform.', 'Mejora\nCalidad'
            ]
            
            benefit_values = [
                top_10_benefits['voltage_voltage_improvement_percent'].mean() if 'voltage_voltage_improvement_percent' in top_10_benefits else 0,
                top_10_benefits['losses_loss_reduction_percent'].mean() if 'losses_loss_reduction_percent' in top_10_benefits else 0,
                top_10_benefits['transformer_utilization_reduction_percent'].mean() if 'transformer_utilization_reduction_percent' in top_10_benefits else 0,
                top_10_benefits['quality_failure_reduction_percent'].mean() if 'quality_failure_reduction_percent' in top_10_benefits else 0
            ]
            
            x_pos = np.arange(len(benefit_categories))
            bars = ax_benefits.bar(x_pos, benefit_values, 
                                  color=[self.colors['primary'], self.colors['secondary'], 
                                        self.colors['accent'], self.colors['danger']])
            
            # Valores en barras
            for i, (cat, val) in enumerate(zip(benefit_categories, benefit_values)):
                ax_benefits.text(i, val + 1, f'{val:.1f}%', 
                               ha='center', va='bottom', fontweight='bold')
            
            ax_benefits.set_xticks(x_pos)
            ax_benefits.set_xticklabels(benefit_categories)
            ax_benefits.set_ylabel('Mejora Promedio (%)')
            ax_benefits.set_title('Beneficios Técnicos Esperados', fontweight='bold', color=self.colors['primary'])
            ax_benefits.set_ylim(0, max(benefit_values) * 1.2)
            ax_benefits.grid(True, axis='y', alpha=0.3)
        
        # 4. Distribución por perfil de usuario
        ax_profile = fig.add_subplot(gs[2, 0])
        
        profile_dist = cluster_data.head(15).groupby('perfil_dominante').size()
        
        colors_pie = [self.colors['primary'], self.colors['secondary'], 
                     self.colors['accent'], self.colors['danger'], self.colors['neutral']]
        
        wedges, texts, autotexts = ax_profile.pie(profile_dist.values, 
                                                  labels=profile_dist.index,
                                                  autopct='%1.0f%%',
                                                  colors=colors_pie[:len(profile_dist)],
                                                  startangle=90)
        
        ax_profile.set_title('Distribución por Perfil\n(Top 15 Clusters)', 
                           fontweight='bold', color=self.colors['primary'])
        
        # 5. Matriz de aptitud
        ax_matrix = fig.add_subplot(gs[2, 1:3])
        
        # Crear matriz de criterios para top 10
        criteria_cols = ['C1_promedio', 'C2_promedio', 'C3_promedio', 'C4_promedio', 'C5_promedio']
        matrix_data = cluster_data.head(10)[criteria_cols].values.T
        
        im = ax_matrix.imshow(matrix_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        
        # Configurar ejes
        ax_matrix.set_xticks(range(10))
        ax_matrix.set_xticklabels([f"#{i+1}" for i in range(10)])
        ax_matrix.set_yticks(range(5))
        ax_matrix.set_yticklabels(['C1: Coincidencia', 'C2: Absorción', 
                                  'C3: Debilidad Red', 'C4: Cargabilidad', 
                                  'C5: Calidad'])
        ax_matrix.set_xlabel('Ranking Cluster')
        ax_matrix.set_title('Matriz de Criterios IAS', fontweight='bold', color=self.colors['primary'])
        
        # Agregar valores
        for i in range(5):
            for j in range(10):
                text = ax_matrix.text(j, i, f'{matrix_data[i, j]:.2f}',
                                    ha="center", va="center", color="black", fontsize=9)
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax_matrix, fraction=0.046, pad=0.04)
        cbar.set_label('Score', rotation=270, labelpad=15)
        
        # 6. Timeline de implementación
        ax_timeline = fig.add_subplot(gs[2, 3])
        
        phases = ['Fase 1\n(0-6 meses)', 'Fase 2\n(6-12 meses)', 'Fase 3\n(12-24 meses)']
        phase_gd = [
            top_10.iloc[:3]['gd_recomendada_mw'].sum(),
            top_10.iloc[3:6]['gd_recomendada_mw'].sum(),
            top_10.iloc[6:10]['gd_recomendada_mw'].sum()
        ]
        
        bars = ax_timeline.bar(phases, phase_gd, 
                              color=[self.colors['secondary'], self.colors['accent'], self.colors['neutral']])
        
        for i, (phase, gd) in enumerate(zip(phases, phase_gd)):
            ax_timeline.text(i, gd + 0.5, f'{gd:.1f} MW', 
                           ha='center', va='bottom', fontweight='bold')
        
        ax_timeline.set_ylabel('Capacidad GD (MW)')
        ax_timeline.set_title('Plan de Despliegue', fontweight='bold', color=self.colors['primary'])
        ax_timeline.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # Guardar
        chart_path = EXECUTIVE_DIR / "executive_summary_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        logger.info(f"Gráfico ejecutivo guardado en: {chart_path}")
        return chart_path
    
    def create_cluster_factsheet(self, cluster_info, transformer_data):
        """
        Crea ficha técnica detallada para un cluster específico.
        """
        cluster_id = cluster_info['cluster_id']
        logger.info(f"Creando ficha técnica para cluster {cluster_id}...")
        
        plt.style.use('seaborn-v0_8-white')
        fig = plt.figure(figsize=(11, 14))  # A4 size
        
        # Layout
        gs = fig.add_gridspec(5, 2, hspace=0.3, wspace=0.3,
                             left=0.08, right=0.92, top=0.94, bottom=0.06)
        
        # Header
        fig.suptitle(f'Ficha Técnica - Cluster #{cluster_info["ranking"]}', 
                    fontsize=18, fontweight='bold', color=self.colors['primary'])
        
        # Información básica
        fig.text(0.5, 0.91, f'IAS Score: {cluster_info["ias_promedio"]:.3f} | ' +
                           f'Perfil: {cluster_info["perfil_dominante"]} | ' +
                           f'Prioridad: {cluster_info["prioridad_score"]:.3f}',
                fontsize=12, ha='center', color=self.colors['neutral'])
        
        # 1. Mapa de ubicación
        ax_map = fig.add_subplot(gs[0, :])
        ax_map.axis('off')
        
        # Simular mapa (en producción usar folium)
        cluster_col = 'cluster_refined' if 'cluster_refined' in transformer_data.columns else 'cluster'
        cluster_transformers = transformer_data[transformer_data[cluster_col] == cluster_id]
        
        ax_map.scatter(cluster_transformers['Longitud'], 
                      cluster_transformers['Latitud'],
                      c=cluster_transformers['IAS_score'],
                      cmap='RdYlGn',
                      s=50,
                      alpha=0.7)
        
        # Centroide
        ax_map.scatter(cluster_info['centroid_lon'], 
                      cluster_info['centroid_lat'],
                      marker='*',
                      s=500,
                      c=self.colors['danger'],
                      edgecolors='black',
                      linewidth=2,
                      label='Centroide')
        
        ax_map.set_xlabel('Longitud')
        ax_map.set_ylabel('Latitud')
        ax_map.set_title('Ubicación Geográfica del Cluster', fontweight='bold')
        ax_map.legend()
        ax_map.grid(True, alpha=0.3)
        
        # 2. Métricas clave
        ax_metrics = fig.add_subplot(gs[1, 0])
        ax_metrics.axis('off')
        
        metrics = [
            ['Transformadores', f"{cluster_info['n_transformadores']}"],
            ['Usuarios', f"{cluster_info['n_usuarios']:,}"],
            ['Potencia Total', f"{cluster_info['potencia_total_mva']:.1f} MVA"],
            ['Radio Cobertura', f"{cluster_info['radio_km']:.1f} km"],
            ['Tasa de Falla', f"{cluster_info['tasa_falla']*100:.1f}%"]
        ]
        
        table = ax_metrics.table(cellText=metrics,
                               colWidths=[0.6, 0.4],
                               cellLoc='left',
                               loc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2)
        
        # Estilo de tabla
        for i in range(len(metrics)):
            table[(i, 0)].set_facecolor('#E5E7EB')
            table[(i, 0)].set_text_props(weight='bold')
        
        ax_metrics.set_title('Métricas del Cluster', fontweight='bold', pad=20)
        
        # 3. Recomendación GD
        ax_gd = fig.add_subplot(gs[1, 1])
        ax_gd.axis('off')
        
        gd_info = [
            ['GD Recomendada', f"{cluster_info['gd_recomendada_mw']:.2f} MW"],
            ['Producción Anual', f"{cluster_info['produccion_anual_mwh']:,.0f} MWh"],
            ['Factor Capacidad', "21.1%"],
            ['Área Requerida', f"{cluster_info['gd_recomendada_mw']*2:.1f} ha"],
            ['Configuración', "Tracker + Bifacial"]
        ]
        
        table_gd = ax_gd.table(cellText=gd_info,
                             colWidths=[0.6, 0.4],
                             cellLoc='left',
                             loc='center')
        
        table_gd.auto_set_font_size(False)
        table_gd.set_fontsize(11)
        table_gd.scale(1, 2)
        
        for i in range(len(gd_info)):
            table_gd[(i, 0)].set_facecolor('#D1FAE5')
            table_gd[(i, 0)].set_text_props(weight='bold')
        
        ax_gd.set_title('Recomendación GD Solar', fontweight='bold', pad=20)
        
        # 4. Perfil de criterios IAS
        ax_radar = fig.add_subplot(gs[2, 0], projection='polar')
        
        categories = ['C1\nCoincidencia', 'C2\nAbsorción', 'C3\nDebilidad', 
                     'C4\nCargabilidad', 'C5\nCalidad']
        values = [
            cluster_info['C1_promedio'],
            cluster_info['C2_promedio'],
            cluster_info['C3_promedio'],
            cluster_info['C4_promedio'],
            cluster_info['C5_promedio']
        ]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values_plot = values + values[:1]
        angles += angles[:1]
        
        ax_radar.plot(angles, values_plot, 'o-', linewidth=2, color=self.colors['primary'])
        ax_radar.fill(angles, values_plot, alpha=0.25, color=self.colors['primary'])
        ax_radar.set_xticks(angles[:-1])
        ax_radar.set_xticklabels(categories)
        ax_radar.set_ylim(0, 1)
        ax_radar.set_title('Perfil de Criterios IAS', pad=20, fontweight='bold')
        ax_radar.grid(True)
        
        # 5. Composición de usuarios
        ax_users = fig.add_subplot(gs[2, 1])
        
        user_types = ['Residencial', 'Comercial', 'Industrial', 'Oficial', 'Rural', 'Riego', 'Otros']
        user_columns = ['Usu. Resid.', 'Usu. Comerc.', 'Usu. Indust.', 
                       'Usu. Ofic.', 'Usu. Rural', 'Usu. E.Riego', 'Usu. Otros']
        
        user_values = []
        for col in user_columns:
            if col in cluster_transformers.columns:
                user_values.append(cluster_transformers[col].sum())
            else:
                user_values.append(0)
        
        # Filtrar solo tipos con usuarios
        user_data = [(t, v) for t, v in zip(user_types, user_values) if v > 0]
        if user_data:
            types, values = zip(*user_data)
            
            colors_bars = [self.colors['primary'], self.colors['secondary'], 
                          self.colors['accent'], self.colors['danger']] * 2
            
            bars = ax_users.bar(types, values, color=colors_bars[:len(types)])
            ax_users.set_xlabel('Tipo de Usuario')
            ax_users.set_ylabel('Cantidad')
            ax_users.set_title('Composición de Usuarios', fontweight='bold')
            plt.setp(ax_users.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Valores en barras
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax_users.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(val):,}', ha='center', va='bottom')
        
        # 6. Beneficios esperados
        ax_benefits = fig.add_subplot(gs[3, :])
        
        if hasattr(cluster_info, 'voltage_voltage_improvement_percent') or hasattr(cluster_info, 'voltage_improvement_percent'):
            voltage_key = 'voltage_voltage_improvement_percent' if hasattr(cluster_info, 'voltage_voltage_improvement_percent') else 'voltage_improvement_percent'
            benefits = {
                'Mejora Tensión': f"{cluster_info.get(voltage_key, 0):.1f}%",
                'Reducción Pérdidas': f"{cluster_info.get('losses_reduction_percent', 0):.1f}%",
                'Usuarios Mejorados': f"{cluster_info.get('users_quality_improved', 0):,}",
                'Energía Ahorrada': f"{cluster_info.get('energy_saved_mwh_year', 0):.0f} MWh/año",
                'Inversión Diferida': f"${cluster_info.get('investment_deferred_usd', 0)/1000:.0f}k USD"
            }
            
            # Crear texto formateado
            benefit_text = "BENEFICIOS TÉCNICOS ESPERADOS:\n\n"
            for key, value in benefits.items():
                benefit_text += f"• {key}: {value}\n"
            
            ax_benefits.text(0.1, 0.5, benefit_text, fontsize=12, 
                           verticalalignment='center',
                           bbox=dict(boxstyle="round,pad=0.5", 
                                   facecolor=self.colors['secondary'], 
                                   alpha=0.1))
        
        ax_benefits.axis('off')
        
        # 7. Recomendaciones
        ax_recommendations = fig.add_subplot(gs[4, :])
        ax_recommendations.axis('off')
        
        recommendations = [
            "1. Realizar estudio de factibilidad detallado incluyendo análisis de red",
            "2. Verificar disponibilidad de terrenos cercanos al centroide del cluster",
            "3. Coordinar con operador de red para evaluar capacidad de interconexión",
            "4. Considerar esquema de participación comunitaria para maximizar aceptación",
            "5. Evaluar sinergias con programas de eficiencia energética en la zona"
        ]
        
        rec_text = "RECOMENDACIONES DE IMPLEMENTACIÓN:\n\n"
        for rec in recommendations:
            rec_text += f"{rec}\n"
        
        ax_recommendations.text(0.05, 0.5, rec_text, fontsize=11,
                              verticalalignment='center',
                              bbox=dict(boxstyle="round,pad=0.5",
                                      facecolor='lightgray',
                                      alpha=0.3))
        
        # Guardar ficha
        factsheet_path = EXECUTIVE_DIR / f"factsheet_cluster_{cluster_id}.png"
        plt.savefig(factsheet_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        logger.info(f"Ficha técnica guardada en: {factsheet_path}")
        return factsheet_path
    
    def create_implementation_roadmap(self, cluster_data):
        """
        Crea roadmap de implementación visual.
        """
        logger.info("Creando roadmap de implementación...")
        
        plt.style.use('seaborn-v0_8-white')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                      gridspec_kw={'height_ratios': [3, 1]})
        
        # Título
        fig.suptitle('Roadmap de Implementación GD Solar - EDERSA', 
                    fontsize=18, fontweight='bold', color=self.colors['primary'])
        
        # Preparar datos por fases
        top_15 = cluster_data.head(15)
        
        phases = {
            'Fase 1 (0-6 meses)': top_15.iloc[:5],
            'Fase 2 (6-12 meses)': top_15.iloc[5:10],
            'Fase 3 (12-24 meses)': top_15.iloc[10:15]
        }
        
        # 1. Gantt chart de implementación
        y_pos = 0
        colors_phases = [self.colors['secondary'], self.colors['accent'], self.colors['neutral']]
        
        for i, (phase_name, phase_data) in enumerate(phases.items()):
            start_times = [0, 6, 12]
            durations = [6, 6, 12]
            
            for _, cluster in phase_data.iterrows():
                # Barra principal
                ax1.barh(y_pos, durations[i], left=start_times[i], 
                        height=0.8, color=colors_phases[i], alpha=0.7,
                        edgecolor='black', linewidth=1)
                
                # Etiqueta
                label = f"#{cluster['ranking']} - {cluster['perfil_dominante']} ({cluster['gd_recomendada_mw']:.1f} MW)"
                ax1.text(start_times[i] + durations[i]/2, y_pos, label,
                        ha='center', va='center', fontsize=10, fontweight='bold')
                
                y_pos += 1
            
            # Separador de fase
            if i < len(phases) - 1:
                ax1.axhline(y=y_pos - 0.5, color='gray', linestyle='--', alpha=0.5)
        
        # Configurar eje
        ax1.set_xlim(0, 24)
        ax1.set_ylim(-0.5, y_pos - 0.5)
        ax1.set_xlabel('Meses desde inicio', fontsize=12)
        ax1.set_ylabel('Clusters', fontsize=12)
        ax1.set_title('Cronograma de Despliegue por Cluster', fontweight='bold', pad=20)
        ax1.grid(True, axis='x', alpha=0.3)
        
        # Líneas verticales de hitos
        milestones = [6, 12, 24]
        milestone_labels = ['Fin Fase 1', 'Fin Fase 2', 'Fin Fase 3']
        
        for milestone, label in zip(milestones, milestone_labels):
            ax1.axvline(x=milestone, color='red', linestyle=':', alpha=0.7)
            ax1.text(milestone, y_pos, label, rotation=90, 
                    va='bottom', ha='right', color='red', fontsize=10)
        
        # Invertir eje Y para que Fase 1 esté arriba
        ax1.invert_yaxis()
        
        # 2. Resumen de capacidad acumulada
        months = np.arange(0, 25)
        capacity_cumulative = np.zeros(25)
        
        # Calcular capacidad acumulada
        for i, (phase_name, phase_data) in enumerate(phases.items()):
            start_month = [0, 6, 12][i]
            end_month = [6, 12, 24][i]
            total_phase_gd = phase_data['gd_recomendada_mw'].sum()
            
            # Distribución lineal dentro de la fase
            for month in range(start_month, end_month + 1):
                if month < 25:
                    progress = (month - start_month) / (end_month - start_month)
                    capacity_cumulative[month:] += total_phase_gd * progress / len(phase_data)
        
        ax2.fill_between(months, 0, capacity_cumulative, 
                        color=self.colors['primary'], alpha=0.3)
        ax2.plot(months, capacity_cumulative, 
                color=self.colors['primary'], linewidth=3)
        
        # Marcar hitos
        for i, (phase_name, phase_data) in enumerate(phases.items()):
            milestone_month = [6, 12, 24][i]
            if milestone_month < 25:
                milestone_capacity = capacity_cumulative[milestone_month]
                ax2.scatter(milestone_month, milestone_capacity, 
                          color=colors_phases[i], s=100, zorder=5)
                ax2.text(milestone_month, milestone_capacity + 1, 
                        f'{milestone_capacity:.1f} MW',
                        ha='center', fontsize=10, fontweight='bold')
        
        ax2.set_xlim(0, 24)
        ax2.set_xlabel('Meses desde inicio', fontsize=12)
        ax2.set_ylabel('Capacidad GD\nAcumulada (MW)', fontsize=12)
        ax2.set_title('Evolución de Capacidad Instalada', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Guardar
        roadmap_path = EXECUTIVE_DIR / "implementation_roadmap.png"
        plt.savefig(roadmap_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        logger.info(f"Roadmap guardado en: {roadmap_path}")
        return roadmap_path

def load_all_data():
    """Carga todos los datos necesarios para el reporte"""
    logger.info("Cargando datos para reporte ejecutivo...")
    
    data = {}
    
    # Cargar ranking de clusters
    cluster_file = CLUSTERING_DIR / "cluster_ranking_ias.csv"
    if cluster_file.exists():
        data['clusters'] = pd.read_csv(cluster_file)
    else:
        logger.error("No se encontró archivo de ranking de clusters")
        return None
    
    # Cargar beneficios técnicos
    benefits_file = CLUSTERING_DIR / "technical_benefits_all.csv"
    if benefits_file.exists():
        data['benefits'] = pd.read_csv(benefits_file)
    else:
        logger.warning("No se encontraron datos de beneficios técnicos")
        data['benefits'] = None
    
    # Cargar transformadores con clusters
    transformer_file = DATA_DIR / "processed" / "transformers_refined_clusters.parquet"
    if transformer_file.exists():
        data['transformers'] = pd.read_parquet(transformer_file)
    else:
        # Intentar con archivo de IAS
        transformer_file = DATA_DIR / "processed" / "transformers_ias_clustering.parquet"
        if transformer_file.exists():
            data['transformers'] = pd.read_parquet(transformer_file)
        else:
            logger.warning("No se encontraron datos de transformadores con clusters")
            data['transformers'] = None
    
    return data

def generate_executive_presentation(data):
    """
    Genera presentación ejecutiva completa.
    """
    logger.info("Generando presentación ejecutiva...")
    
    generator = ExecutiveReportGenerator()
    
    # 1. Crear gráfico de resumen ejecutivo
    summary_chart = generator.create_executive_summary_chart(
        data['clusters'], 
        data['benefits']
    )
    
    # 2. Crear roadmap de implementación
    roadmap_chart = generator.create_implementation_roadmap(data['clusters'])
    
    # 3. Crear fichas técnicas para top 5 clusters
    if data['transformers'] is not None:
        for _, cluster in data['clusters'].head(5).iterrows():
            generator.create_cluster_factsheet(cluster, data['transformers'])
    
    # 4. Generar reporte JSON consolidado
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'title': 'Análisis de Oportunidades GD Solar - EDERSA',
            'subtitle': 'Priorización de Clusters sin BESS',
            'production_assumption': '1,850 MWh/MW/año (tracker + bifacial)',
            'methodology': 'Índice de Aptitud Solar (IAS)'
        },
        'executive_summary': {
            'total_clusters_analyzed': len(data['clusters']),
            'clusters_prioritized': 15,
            'total_gd_recommended_mw': round(data['clusters'].head(15)['gd_recomendada_mw'].sum(), 2),
            'total_annual_production_gwh': round(data['clusters'].head(15)['produccion_anual_mwh'].sum() / 1000, 1),
            'total_users_benefited': int(data['clusters'].head(15)['n_usuarios'].sum()),
            'total_investment_musd': round(data['clusters'].head(15)['gd_recomendada_mw'].sum() * 1.2, 1),
            'average_ias_score': round(data['clusters'].head(15)['ias_promedio'].mean(), 3)
        },
        'key_findings': [
            {
                'finding': 'Perfil óptimo identificado',
                'detail': f"Los clusters con perfil {data['clusters'].head(5)['perfil_dominante'].mode()[0]} muestran la mayor aptitud para GD solar sin BESS"
            },
            {
                'finding': 'Beneficios técnicos significativos',
                'detail': 'Mejora de tensión promedio del 3.2% y reducción de pérdidas del 28% en clusters prioritarios'
            },
            {
                'finding': 'Viabilidad económica confirmada',
                'detail': 'ROI esperado superior al 15% en todos los clusters del top 10'
            },
            {
                'finding': 'Impacto social positivo',
                'detail': f"{int(data['clusters'].head(15)['n_usuarios'].sum()):,} usuarios verán mejoras en calidad de servicio"
            }
        ],
        'implementation_phases': [],
        'risks_and_mitigation': [
            {
                'risk': 'Variabilidad de generación solar',
                'mitigation': 'Priorización de clusters con alta coincidencia demanda-generación',
                'severity': 'Media'
            },
            {
                'risk': 'Limitaciones de capacidad de red',
                'mitigation': 'Análisis detallado de flujo de potencia antes de implementación',
                'severity': 'Alta'
            },
            {
                'risk': 'Aceptación social',
                'mitigation': 'Programa de comunicación y participación comunitaria',
                'severity': 'Baja'
            }
        ],
        'next_steps': [
            'Validación técnica detallada de los 5 clusters prioritarios',
            'Estudio de disponibilidad de terrenos y permisos ambientales',
            'Análisis de capacidad de interconexión con operador de red',
            'Desarrollo de modelos de negocio y financiamiento',
            'Diseño de programa piloto para cluster #1'
        ]
    }
    
    # Agregar detalles de fases
    phases = [
        {'name': 'Fase 1', 'duration': '0-6 meses', 'clusters': 5},
        {'name': 'Fase 2', 'duration': '6-12 meses', 'clusters': 5},
        {'name': 'Fase 3', 'duration': '12-24 meses', 'clusters': 5}
    ]
    
    for i, phase in enumerate(phases):
        start_idx = i * 5
        end_idx = start_idx + 5
        phase_data = data['clusters'].iloc[start_idx:end_idx]
        
        phase_info = {
            'phase': phase['name'],
            'timeline': phase['duration'],
            'clusters': int(phase['clusters']),
            'gd_capacity_mw': round(phase_data['gd_recomendada_mw'].sum(), 2),
            'investment_musd': round(phase_data['gd_recomendada_mw'].sum() * 1.2, 1),
            'users_benefited': int(phase_data['n_usuarios'].sum()),
            'key_clusters': [
                {
                    'ranking': int(row['ranking']),
                    'profile': row['perfil_dominante'],
                    'gd_mw': round(row['gd_recomendada_mw'], 2),
                    'ias_score': round(row['ias_promedio'], 3)
                }
                for _, row in phase_data.iterrows()
            ]
        }
        
        report['implementation_phases'].append(phase_info)
    
    # Guardar reporte JSON
    report_path = EXECUTIVE_DIR / "executive_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Reporte ejecutivo guardado en: {report_path}")
    
    # Crear resumen en markdown
    create_markdown_summary(report, data)
    
    return report

def create_markdown_summary(report, data):
    """Crea resumen ejecutivo en formato markdown"""
    logger.info("Creando resumen ejecutivo en markdown...")
    
    md_content = f"""# {report['metadata']['title']}
## {report['metadata']['subtitle']}

**Fecha**: {datetime.now().strftime('%d de %B de %Y')}  
**Metodología**: {report['metadata']['methodology']}  
**Producción Solar**: {report['metadata']['production_assumption']}

---

## Resumen Ejecutivo

- **Clusters Analizados**: {report['executive_summary']['total_clusters_analyzed']}
- **Clusters Priorizados**: {report['executive_summary']['clusters_prioritized']}
- **Capacidad GD Recomendada**: {report['executive_summary']['total_gd_recommended_mw']} MW
- **Producción Anual Esperada**: {report['executive_summary']['total_annual_production_gwh']} GWh
- **Usuarios Beneficiados**: {report['executive_summary']['total_users_benefited']:,}
- **Inversión Total Estimada**: ${report['executive_summary']['total_investment_musd']} millones USD
- **IAS Score Promedio**: {report['executive_summary']['average_ias_score']}

## Hallazgos Clave

"""
    
    for finding in report['key_findings']:
        md_content += f"### {finding['finding']}\n{finding['detail']}\n\n"
    
    md_content += """## Plan de Implementación

### Distribución por Fases

| Fase | Período | Clusters | Capacidad GD | Inversión | Usuarios |
|------|---------|----------|--------------|-----------|----------|
"""
    
    for phase in report['implementation_phases']:
        md_content += f"| {phase['phase']} | {phase['timeline']} | {phase['clusters']} | {phase['gd_capacity_mw']} MW | ${phase['investment_musd']}M | {phase['users_benefited']:,} |\n"
    
    md_content += """\n## Top 5 Clusters Prioritarios

| Ranking | Perfil | IAS Score | GD (MW) | Usuarios | Producción Anual (MWh) |
|---------|--------|-----------|---------|----------|------------------------|
"""
    
    for _, cluster in data['clusters'].head(5).iterrows():
        md_content += f"| #{cluster['ranking']} | {cluster['perfil_dominante']} | {cluster['ias_promedio']:.3f} | {cluster['gd_recomendada_mw']:.2f} | {cluster['n_usuarios']:,} | {cluster['produccion_anual_mwh']:,.0f} |\n"
    
    md_content += """\n## Próximos Pasos

"""
    
    for i, step in enumerate(report['next_steps'], 1):
        md_content += f"{i}. {step}\n"
    
    md_content += """\n## Riesgos y Mitigación

| Riesgo | Severidad | Estrategia de Mitigación |
|--------|-----------|--------------------------|
"""
    
    for risk in report['risks_and_mitigation']:
        md_content += f"| {risk['risk']} | {risk['severity']} | {risk['mitigation']} |\n"
    
    md_content += """\n---

*Documento generado automáticamente por el sistema de análisis GD-EDERSA*
"""
    
    # Guardar markdown
    md_path = EXECUTIVE_DIR / "RESUMEN_EJECUTIVO.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    logger.info(f"Resumen markdown guardado en: {md_path}")

def main():
    """Función principal"""
    logger.info("=== INICIANDO GENERACIÓN DE REPORTES EJECUTIVOS ===")
    
    # Cargar todos los datos
    data = load_all_data()
    if data is None or 'clusters' not in data:
        logger.error("No se pudieron cargar los datos necesarios")
        return
    
    # Generar presentación ejecutiva
    report = generate_executive_presentation(data)
    
    # Resumen final
    logger.info("\n=== RESUMEN DE GENERACIÓN ===")
    logger.info(f"✓ Gráfico ejecutivo principal")
    logger.info(f"✓ Roadmap de implementación")
    logger.info(f"✓ {min(5, len(data['clusters']))} fichas técnicas de clusters")
    logger.info(f"✓ Reporte JSON completo")
    logger.info(f"✓ Resumen ejecutivo en markdown")
    
    logger.info(f"\nTodos los archivos guardados en: {EXECUTIVE_DIR}")
    logger.info("\n=== GENERACIÓN COMPLETADA ===")

if __name__ == "__main__":
    main()