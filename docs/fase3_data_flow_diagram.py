"""
Generador de Diagrama de Flujo de Datos - Fase 3
Crea visualización del pipeline de procesamiento de datos
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

def create_data_flow_diagram():
    """Crea diagrama de flujo de datos del sistema."""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Colores
    color_source = '#3498db'      # Azul
    color_process = '#e74c3c'     # Rojo
    color_storage = '#2ecc71'     # Verde
    color_consume = '#f39c12'     # Naranja
    color_ml = '#9b59b6'          # Púrpura
    
    # 1. Fuentes de Datos (arriba)
    ax.add_patch(FancyBboxPatch((1, 8), 3, 1.2, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color_source, 
                                edgecolor='black',
                                alpha=0.8))
    ax.text(2.5, 8.6, 'SCADA/EPRE\nSistema', ha='center', va='center', 
            fontsize=10, fontweight='bold', color='white')
    
    # 2. Raw Data
    ax.add_patch(FancyBboxPatch((1, 6.5), 3, 0.8, 
                                boxstyle="round,pad=0.1", 
                                facecolor='lightgray', 
                                edgecolor='black'))
    ax.text(2.5, 6.9, 'Raw Data (CSV)\n210,156 registros', ha='center', va='center', fontsize=9)
    
    # 3. Processing Pipeline (centro)
    ax.add_patch(FancyBboxPatch((0.5, 4), 4, 2, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color_process, 
                                edgecolor='black',
                                alpha=0.8))
    ax.text(2.5, 5.5, 'Data Processing Pipeline', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='white')
    
    # Sub-procesos
    processes = [
        'Validación y Limpieza',
        'Cálculo de Métricas',
        'Feature Engineering',
        'Agregaciones Temporales'
    ]
    for i, proc in enumerate(processes):
        ax.text(2.5, 5.2 - i*0.3, f'• {proc}', ha='center', va='center', 
                fontsize=8, color='white')
    
    # 4. Almacenamiento (dos ramas)
    # JSON Branch
    ax.add_patch(FancyBboxPatch((5.5, 4.5), 3.5, 1.5, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color_storage, 
                                edgecolor='black',
                                alpha=0.8))
    ax.text(7.25, 5.5, 'JSON Files (10)', ha='center', va='center', 
            fontsize=10, fontweight='bold', color='white')
    ax.text(7.25, 5.1, 'Análisis Descriptivo\n~147KB total', ha='center', va='center', 
            fontsize=8, color='white')
    
    # Parquet Branch
    ax.add_patch(FancyBboxPatch((9.5, 4.5), 3.5, 1.5, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color_ml, 
                                edgecolor='black',
                                alpha=0.8))
    ax.text(11.25, 5.5, 'Parquet Files (4)', ha='center', va='center', 
            fontsize=10, fontweight='bold', color='white')
    ax.text(11.25, 5.1, 'ML Features\n~40MB total', ha='center', va='center', 
            fontsize=8, color='white')
    
    # 5. Consumidores
    # Dashboard
    ax.add_patch(FancyBboxPatch((5.5, 2), 3.5, 1.2, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color_consume, 
                                edgecolor='black',
                                alpha=0.8))
    ax.text(7.25, 2.6, 'Dashboard Dash\nFase 3: 12 Tabs', ha='center', va='center', 
            fontsize=10, fontweight='bold', color='white')
    
    # ML Models
    ax.add_patch(FancyBboxPatch((9.5, 2), 3.5, 1.2, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color_ml, 
                                edgecolor='black',
                                alpha=0.8))
    ax.text(11.25, 2.6, 'ML Models\n(Future)', ha='center', va='center', 
            fontsize=10, fontweight='bold', color='white')
    
    # 6. Detalles de archivos
    # JSON files list
    json_files = [
        'summary.json (4.9K)',
        'quality_metrics.json (5.5K)',
        'temporal_patterns.json (26K)',
        'correlations.json (2.8K)',
        'hourly_analysis.json (32K)',
        'pv_correlation.json (1.8K)',
        'critical_events.json (6.4K)',
        'demand_ramps.json (26K)',
        'duration_curves.json (8.2K)',
        'typical_days.json (35K)'
    ]
    
    for i, file in enumerate(json_files[:5]):
        ax.text(5.7, 4.2 - i*0.15, file, ha='left', va='center', fontsize=7, style='italic')
    for i, file in enumerate(json_files[5:]):
        ax.text(7.5, 4.2 - i*0.15, file, ha='left', va='center', fontsize=7, style='italic')
    
    # Parquet files list
    parquet_files = [
        'pilcaniyeu_features.parquet (10M)',
        'jacobacci_features.parquet (16M)',
        'maquinchao_features.parquet (5.3M)',
        'los_menucos_features.parquet (9.3M)'
    ]
    
    for i, file in enumerate(parquet_files):
        ax.text(9.7, 4.2 - i*0.15, file, ha='left', va='center', fontsize=7, style='italic')
    
    # 7. Flechas de flujo
    # Source to Raw
    ax.add_patch(FancyArrowPatch((2.5, 8), (2.5, 7.3),
                                 connectionstyle="arc3", 
                                 arrowstyle='->', 
                                 mutation_scale=20, 
                                 lw=2,
                                 color='black'))
    
    # Raw to Processing
    ax.add_patch(FancyArrowPatch((2.5, 6.5), (2.5, 6),
                                 connectionstyle="arc3", 
                                 arrowstyle='->', 
                                 mutation_scale=20, 
                                 lw=2,
                                 color='black'))
    
    # Processing to JSON
    ax.add_patch(FancyArrowPatch((4.5, 5), (5.5, 5.25),
                                 connectionstyle="arc3,rad=.2", 
                                 arrowstyle='->', 
                                 mutation_scale=20, 
                                 lw=2,
                                 color='black'))
    
    # Processing to Parquet
    ax.add_patch(FancyArrowPatch((4.5, 5), (9.5, 5.25),
                                 connectionstyle="arc3,rad=-.3", 
                                 arrowstyle='->', 
                                 mutation_scale=20, 
                                 lw=2,
                                 color='black'))
    
    # JSON to Dashboard
    ax.add_patch(FancyArrowPatch((7.25, 4.5), (7.25, 3.2),
                                 connectionstyle="arc3", 
                                 arrowstyle='->', 
                                 mutation_scale=20, 
                                 lw=2,
                                 color='black'))
    
    # Parquet to ML
    ax.add_patch(FancyArrowPatch((11.25, 4.5), (11.25, 3.2),
                                 connectionstyle="arc3", 
                                 arrowstyle='->', 
                                 mutation_scale=20, 
                                 lw=2,
                                 color='black'))
    
    # 8. Métricas clave
    metrics_text = """
    Métricas del Sistema:
    • 4 estaciones monitoreadas
    • Resolución: 15 minutos
    • Período: Ene 2024 - Abr 2025
    • 100% datos fuera de límites
    • 547 eventos críticos
    """
    ax.text(0.5, 1.5, metrics_text, ha='left', va='top', fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow'))
    
    # 9. Título y subtítulo
    ax.text(7, 9.5, 'Flujo de Datos - Fase 3: Procesamiento y Análisis', 
            ha='center', va='center', fontsize=16, fontweight='bold')
    ax.text(7, 9, 'Pipeline de transformación desde SCADA hasta ML', 
            ha='center', va='center', fontsize=11, style='italic')
    
    # 10. Leyenda
    legend_elements = [
        mlines.Line2D([0], [0], marker='s', color='w', label='Fuente de Datos',
                      markerfacecolor=color_source, markersize=10),
        mlines.Line2D([0], [0], marker='s', color='w', label='Procesamiento',
                      markerfacecolor=color_process, markersize=10),
        mlines.Line2D([0], [0], marker='s', color='w', label='Almacenamiento',
                      markerfacecolor=color_storage, markersize=10),
        mlines.Line2D([0], [0], marker='s', color='w', label='Consumo/Visualización',
                      markerfacecolor=color_consume, markersize=10),
        mlines.Line2D([0], [0], marker='s', color='w', label='Machine Learning',
                      markerfacecolor=color_ml, markersize=10)
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9)
    
    plt.tight_layout()
    
    # Guardar en múltiples formatos
    output_dir = '/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/docs/images/'
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    plt.savefig(f'{output_dir}fase3_data_flow_diagram.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_dir}fase3_data_flow_diagram.pdf', bbox_inches='tight')
    
    print(f"Diagrama guardado en: {output_dir}")
    
    return fig

if __name__ == "__main__":
    # Crear y mostrar diagrama
    fig = create_data_flow_diagram()
    plt.show()