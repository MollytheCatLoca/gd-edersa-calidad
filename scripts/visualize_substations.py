#!/usr/bin/env python3
"""
Visualización detallada de subestaciones del Sistema Línea Sur
Muestra transformadores, barras, alimentadores y equipamiento
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Arrow
import json
from pathlib import Path

# Project root
project_root = Path(__file__).parent.parent

def draw_transformer(ax, x, y, size=0.3, label="", power=""):
    """Draw transformer symbol."""
    # Two circles
    circle1 = Circle((x-size/2, y), size/2, fill=False, linewidth=2)
    circle2 = Circle((x+size/2, y), size/2, fill=False, linewidth=2)
    ax.add_patch(circle1)
    ax.add_patch(circle2)
    
    # Connection lines
    ax.plot([x-size/2, x-size/2], [y+size/2, y+size/2+0.2], 'k-', linewidth=2)
    ax.plot([x+size/2, x+size/2], [y-size/2, y-size/2-0.2], 'k-', linewidth=2)
    
    # Label
    if label:
        ax.text(x, y+size+0.1, label, ha='center', va='bottom', fontsize=10, fontweight='bold')
    if power:
        ax.text(x, y-size-0.1, power, ha='center', va='top', fontsize=9)

def draw_busbar(ax, x, y, width, label="", voltage=""):
    """Draw busbar."""
    rect = Rectangle((x-width/2, y-0.05), width, 0.1, facecolor='black')
    ax.add_patch(rect)
    if label:
        ax.text(x, y+0.15, label, ha='center', va='bottom', fontsize=9)
    if voltage:
        ax.text(x, y-0.15, voltage, ha='center', va='top', fontsize=8, style='italic')

def draw_breaker(ax, x, y, closed=True):
    """Draw circuit breaker."""
    size = 0.15
    rect = Rectangle((x-size/2, y-size/2), size, size, fill=False, linewidth=1.5)
    ax.add_patch(rect)
    if closed:
        ax.plot([x-size/2, x+size/2], [y, y], 'k-', linewidth=2)
    else:
        ax.plot([x-size/2, x], [y, y], 'k-', linewidth=2)

def draw_load(ax, x, y, label="", power=""):
    """Draw load arrow."""
    arrow = mpatches.FancyArrowPatch((x, y), (x, y-0.3),
                                     mutation_scale=20, 
                                     color='red',
                                     arrowstyle='->')
    ax.add_patch(arrow)
    if label:
        ax.text(x+0.1, y-0.15, label, ha='left', va='center', fontsize=8)
    if power:
        ax.text(x+0.1, y-0.25, power, ha='left', va='center', fontsize=7, color='red')

def draw_generator(ax, x, y, label="GEN", power=""):
    """Draw generator symbol."""
    circle = Circle((x, y), 0.2, fill=False, linewidth=2)
    ax.add_patch(circle)
    ax.text(x, y, 'G', ha='center', va='center', fontsize=12, fontweight='bold')
    if label:
        ax.text(x, y+0.3, label, ha='center', va='bottom', fontsize=9)
    if power:
        ax.text(x, y-0.3, power, ha='center', va='top', fontsize=8, color='green')

def draw_regulator(ax, x, y, label="REG"):
    """Draw voltage regulator."""
    rect = FancyBboxPatch((x-0.2, y-0.1), 0.4, 0.2, 
                          boxstyle="round,pad=0.02",
                          facecolor='lightblue',
                          edgecolor='blue',
                          linewidth=2)
    ax.add_patch(rect)
    ax.text(x, y, 'REG', ha='center', va='center', fontsize=8, fontweight='bold')
    if label:
        ax.text(x, y-0.2, label, ha='center', va='top', fontsize=7)

def create_pilcaniyeu_diagram():
    """Create Pilcaniyeu substation diagram."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Title
    ax.text(0.5, 0.95, 'ET PILCANIYEU - DIAGRAMA UNIFILAR', 
            ha='center', va='top', fontsize=14, fontweight='bold',
            transform=ax.transAxes)
    
    # 132 kV busbar
    draw_busbar(ax, 5, 8, 3, "Barra 132 kV", "Desde ALIPIBA")
    
    # Transformer
    draw_transformer(ax, 5, 6.5, size=0.5, label="T1", power="25 MVA\nYd")
    ax.plot([5, 5], [7.5, 7], 'k-', linewidth=2)
    ax.plot([5, 5], [6, 5.5], 'k-', linewidth=2)
    
    # OLTC
    draw_regulator(ax, 6, 6.5, "RBC ±10%")
    
    # 33 kV busbar
    draw_busbar(ax, 5, 5, 3, "Barra 33 kV", "")
    
    # Outgoing feeder
    draw_breaker(ax, 5, 4.5)
    ax.plot([5, 5], [4.35, 4], 'k-', linewidth=2)
    ax.text(5, 3.8, 'A Comallo\n120 Al/Al - 70 km', ha='center', va='top', fontsize=9)
    
    ax.set_xlim(2, 8)
    ax.set_ylim(3, 9)
    ax.axis('off')
    
    return fig

def create_jacobacci_diagram():
    """Create Jacobacci substation diagram."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Title
    ax.text(0.5, 0.95, 'ET JACOBACCI - DIAGRAMA UNIFILAR', 
            ha='center', va='top', fontsize=14, fontweight='bold',
            transform=ax.transAxes)
    
    # Incoming 33 kV
    ax.text(5, 8.5, 'Desde Onelli\n120 Al/Al', ha='center', va='center', fontsize=9)
    ax.plot([5, 5], [8.2, 7.8], 'k-', linewidth=2)
    
    # Series regulator
    draw_regulator(ax, 5, 7.5, "REG 33/33 kV\n±10%")
    ax.plot([5, 5], [7.3, 7], 'k-', linewidth=2)
    
    # 33 kV busbar
    draw_busbar(ax, 5, 6.5, 4, "Barra 33 kV", "")
    
    # Transformer
    draw_transformer(ax, 5, 5, size=0.5, label="T1", power="5 MVA\nDy11")
    ax.plot([5, 5], [6, 5.5], 'k-', linewidth=2)
    ax.plot([5, 5], [4.5, 4], 'k-', linewidth=2)
    
    # 13.2 kV busbar
    draw_busbar(ax, 5, 3.5, 5, "Barra 13.2 kV", "")
    
    # Feeders
    # Norte
    ax.plot([4, 4], [3.5, 3], 'k-', linewidth=2)
    draw_breaker(ax, 4, 2.8)
    draw_load(ax, 4, 2.5, "Alim. NORTE", "0.7 MW")
    
    # Sur
    ax.plot([6, 6], [3.5, 3], 'k-', linewidth=2)
    draw_breaker(ax, 6, 2.8)
    draw_load(ax, 6, 2.5, "Alim. SUR", "0.75 MW")
    
    # Outgoing 33 kV
    ax.plot([7, 7], [6.5, 6], 'k-', linewidth=2)
    draw_breaker(ax, 7, 5.8)
    ax.plot([7, 7], [5.65, 5.3], 'k-', linewidth=2)
    ax.text(7, 5.1, 'A Maquinchao\n70 Al/Al', ha='center', va='top', fontsize=9)
    
    # Total load
    ax.text(2, 2, 'Carga Total:\n1.45 MW\n0.60 MVAr', 
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"),
            fontsize=9)
    
    ax.set_xlim(1, 9)
    ax.set_ylim(1.5, 9)
    ax.axis('off')
    
    return fig

def create_menucos_diagram():
    """Create Los Menucos substation diagram with DG."""
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Title
    ax.text(0.5, 0.95, 'ET LOS MENUCOS - DIAGRAMA UNIFILAR CON GD', 
            ha='center', va='top', fontsize=14, fontweight='bold',
            transform=ax.transAxes)
    
    # Incoming 33 kV
    ax.text(7, 9, 'Desde Aguada Guerra\n70 Al/Al', ha='center', va='center', fontsize=9)
    ax.plot([7, 7], [8.7, 8.3], 'k-', linewidth=2)
    
    # 33 kV busbar
    draw_busbar(ax, 7, 8, 4, "Barra 33 kV", "")
    
    # Distribution transformers
    draw_transformer(ax, 7, 6.5, size=0.5, label="T1-Tn", power="~6 MVA total\nDy11")
    ax.plot([7, 7], [7.5, 7], 'k-', linewidth=2)
    ax.plot([7, 7], [6, 5.5], 'k-', linewidth=2)
    
    # 13.2 kV busbar
    draw_busbar(ax, 7, 5, 8, "Barra 13.2 kV", "")
    
    # Series regulator
    draw_regulator(ax, 7, 4.3, "REG 13.2/13.2 kV\n±10%")
    ax.plot([7, 7], [5, 4.5], 'k-', linewidth=2)
    ax.plot([7, 7], [4.1, 3.8], 'k-', linewidth=2)
    
    # Distribution feeders
    for i, x in enumerate([5, 6, 8, 9]):
        ax.plot([x, x], [3.8, 3.3], 'k-', linewidth=2)
        draw_breaker(ax, x, 3.1)
        draw_load(ax, x, 2.8, f"Alim. {i+1}", "0.35 MW")
    
    # Generation section
    ax.text(2, 6, 'GENERACIÓN DISTRIBUIDA', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"))
    
    # Generator 1
    draw_generator(ax, 2, 4, "GEN 1", "1.5 MW")
    ax.plot([2, 2], [4.2, 4.5], 'k-', linewidth=2)
    draw_transformer(ax, 2, 5, size=0.3, label="TG1", power="2 MVA\n0.4/13.2")
    ax.plot([2, 2], [5.3, 5.5], 'k-', linewidth=2)
    draw_breaker(ax, 2, 5.7)
    ax.plot([2, 2.5], [5.8, 5.8], 'k-', linewidth=2)
    ax.plot([2.5, 2.5], [5.8, 5], 'k-', linewidth=2)
    ax.plot([2.5, 3], [5, 5], 'k-', linewidth=2)
    
    # Generator 2
    draw_generator(ax, 4, 4, "GEN 2", "1.5 MW")
    ax.plot([4, 4], [4.2, 4.5], 'k-', linewidth=2)
    draw_transformer(ax, 4, 5, size=0.3, label="TG2", power="2 MVA\n0.4/13.2")
    ax.plot([4, 4], [5.3, 5.5], 'k-', linewidth=2)
    draw_breaker(ax, 4, 5.7)
    ax.plot([4, 3.5], [5.8, 5.8], 'k-', linewidth=2)
    ax.plot([3.5, 3.5], [5.8, 5], 'k-', linewidth=2)
    ax.plot([3.5, 3], [5, 5], 'k-', linewidth=2)
    
    # Gas supply
    ax.text(3, 3, 'Gas Natural', ha='center', fontsize=9, 
            bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow"))
    
    # Total load
    ax.text(10.5, 3, 'Carga Total:\n1.40 MW\n0.20 MVAr\n\nGeneración:\n3.0 MW (gas)', 
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"),
            fontsize=9)
    
    ax.set_xlim(0, 12)
    ax.set_ylim(2, 9.5)
    ax.axis('off')
    
    return fig

def create_summary_diagram():
    """Create summary diagram of all substations."""
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Title
    ax.text(0.5, 0.95, 'SISTEMA LÍNEA SUR - RESUMEN DE TRANSFORMADORES', 
            ha='center', va='top', fontsize=16, fontweight='bold',
            transform=ax.transAxes)
    
    # Station data
    stations = [
        {"name": "PILCANIYEU", "x": 2, "mva": "25 MVA", "kv": "132/33", "reg": "RBC"},
        {"name": "COMALLO", "x": 4, "mva": "1.5 MVA", "kv": "33/13.2", "reg": "Taps"},
        {"name": "ONELLI", "x": 6, "mva": "40 kVA", "kv": "33/13.2", "reg": "Taps"},
        {"name": "JACOBACCI", "x": 8, "mva": "5 MVA", "kv": "33/13.2", "reg": "Serie 33kV"},
        {"name": "MAQUINCHAO", "x": 10, "mva": "0.5 MVA", "kv": "33/13.2", "reg": "Taps"},
        {"name": "LOS MENUCOS", "x": 13, "mva": "6 MVA + 3MW GD", "kv": "33/13.2", "reg": "Serie 13.2kV"}
    ]
    
    # Draw 33 kV line
    ax.plot([1.5, 14], [6, 6], 'k-', linewidth=3)
    ax.text(7.5, 6.3, 'Línea 33 kV - 270 km', ha='center', fontsize=12, fontweight='bold')
    
    # Draw stations
    for i, st in enumerate(stations):
        # Vertical line
        ax.plot([st['x'], st['x']], [6, 5], 'k-', linewidth=2)
        
        # Transformer
        draw_transformer(ax, st['x'], 4, size=0.4)
        
        # Station name
        ax.text(st['x'], 3.3, st['name'], ha='center', fontsize=10, fontweight='bold')
        
        # Technical data
        ax.text(st['x'], 2.9, st['mva'], ha='center', fontsize=8)
        ax.text(st['x'], 2.6, st['kv'], ha='center', fontsize=8)
        ax.text(st['x'], 2.3, st['reg'], ha='center', fontsize=7, style='italic')
        
        # Distance
        if i > 0:
            km = [0, 70, 120, 150, 210, 270][i]
            ax.text(st['x'], 1.8, f"{km} km", ha='center', fontsize=8, color='blue')
    
    # Legend
    ax.text(1, 8, 'Leyenda:', fontsize=10, fontweight='bold')
    ax.text(1, 7.6, '• RBC: Regulador Bajo Carga', fontsize=9)
    ax.text(1, 7.3, '• Serie: Regulador Serie', fontsize=9)
    ax.text(1, 7, '• GD: Generación Distribuida', fontsize=9)
    ax.text(1, 6.7, '• Taps: Regulación por taps fijos', fontsize=9)
    
    # Capacity summary
    ax.text(12, 8, 'Capacidad Total:', fontsize=10, fontweight='bold')
    ax.text(12, 7.6, '• Transformación 132/33: 25 MVA', fontsize=9)
    ax.text(12, 7.3, '• Transformación 33/13.2: 13.54 MVA', fontsize=9)
    ax.text(12, 7, '• Generación: 3 MW', fontsize=9)
    ax.text(12, 6.7, '• Carga total: 3.8 MW', fontsize=9)
    
    ax.set_xlim(0, 15)
    ax.set_ylim(1, 9)
    ax.axis('off')
    
    return fig

def main():
    """Generate all substation diagrams."""
    output_dir = project_root / "reports" / "figures" / "substations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create diagrams
    diagrams = [
        ("pilcaniyeu_diagram.png", create_pilcaniyeu_diagram()),
        ("jacobacci_diagram.png", create_jacobacci_diagram()),
        ("menucos_diagram.png", create_menucos_diagram()),
        ("summary_transformers.png", create_summary_diagram())
    ]
    
    # Save all diagrams
    for filename, fig in diagrams:
        filepath = output_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"Saved: {filepath}")
    
    print(f"\nAll diagrams saved to: {output_dir}")
    
    # Also save a combined PDF
    from matplotlib.backends.backend_pdf import PdfPages
    
    pdf_path = output_dir / "substations_diagrams.pdf"
    with PdfPages(pdf_path) as pdf:
        for filename, fig in diagrams:
            fig = eval(f"create_{filename.split('_')[0]}_diagram()")
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
    
    print(f"Combined PDF saved: {pdf_path}")

if __name__ == "__main__":
    main()