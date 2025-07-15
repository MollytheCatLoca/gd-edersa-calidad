#!/usr/bin/env python3
"""
Fase 0 - Script 4: Reconstrucción de Topología con MST
======================================================

Este script implementa la reconstrucción de la topología de red usando
Minimum Spanning Tree (MST) por alimentador, basado en la metodología
descrita en el documento de teoría eléctrica.

Objetivos:
- Reconstruir la topología radial más probable de cada alimentador
- Identificar la subestación probable
- Calcular características topológicas para cada transformador
- Generar visualizaciones de la topología reconstruida
"""

import pandas as pd
import numpy as np
import networkx as nx
from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuración de rutas
BASE_DIR = Path("/Users/maxkeczeli/Proyects/gd-edersa-calidad")
INPUT_FILE = BASE_DIR / "data/processed/network_analysis/transformadores_con_topologia.csv"
FEEDERS_FILE = BASE_DIR / "data/processed/network_analysis/alimentadores_caracterizados.csv"
OUTPUT_DIR = BASE_DIR / "data/processed/electrical_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de visualización
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def load_data():
    """Cargar datos de transformadores y alimentadores"""
    print("Cargando datos...")
    df_transformers = pd.read_csv(INPUT_FILE)
    df_feeders = pd.read_csv(FEEDERS_FILE)
    
    # Filtrar transformadores con coordenadas válidas
    df_transformers = df_transformers[
        (df_transformers['Coord_X'].notna()) & 
        (df_transformers['Coord_Y'].notna())
    ].copy()
    
    print(f"✓ {len(df_transformers)} transformadores con coordenadas válidas")
    print(f"✓ {df_transformers['Alimentador'].nunique()} alimentadores únicos")
    
    return df_transformers, df_feeders

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcular distancia entre dos puntos usando fórmula de Haversine
    Retorna distancia en kilómetros
    """
    R = 6371  # Radio de la Tierra en km
    
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c

def identify_substation(df_feeder):
    """
    Identificar la ubicación probable de la subestación
    Estrategias:
    1. Centroide de transformadores grandes (>= 315 kVA)
    2. Transformador con mayor capacidad
    3. Centroide general si no hay transformadores grandes
    """
    # Estrategia 1: Centroide de transformadores grandes
    large_trafos = df_feeder[df_feeder['Potencia'] >= 315]
    if len(large_trafos) >= 3:
        substation_x = large_trafos['Coord_X'].mean()
        substation_y = large_trafos['Coord_Y'].mean()
        strategy = "centroide_grandes"
    # Estrategia 2: Transformador más grande
    elif len(df_feeder) > 0:
        idx_max = df_feeder['Potencia'].idxmax()
        substation_x = df_feeder.loc[idx_max, 'Coord_X']
        substation_y = df_feeder.loc[idx_max, 'Coord_Y']
        strategy = "trafo_mayor"
    # Estrategia 3: Centroide general
    else:
        substation_x = df_feeder['Coord_X'].mean()
        substation_y = df_feeder['Coord_Y'].mean()
        strategy = "centroide_general"
    
    return substation_x, substation_y, strategy

def build_mst_topology(df_feeder, substation_coords):
    """
    Construir MST para un alimentador
    """
    # Crear lista de todos los nodos (subestación + transformadores)
    nodes = [('SUBSTATION', substation_coords[0], substation_coords[1], 0, 0)]
    
    for idx, row in df_feeder.iterrows():
        nodes.append((
            row['Codigo'],
            row['Coord_X'],
            row['Coord_Y'],
            row['Potencia'],
            row['Q_Usuarios']
        ))
    
    n_nodes = len(nodes)
    
    # Calcular matriz de distancias
    coords = np.array([(n[2], n[1]) for n in nodes])  # lat, lon
    distances = np.zeros((n_nodes, n_nodes))
    
    for i in range(n_nodes):
        for j in range(i+1, n_nodes):
            dist = haversine_distance(
                coords[i][0], coords[i][1],
                coords[j][0], coords[j][1]
            )
            distances[i, j] = dist
            distances[j, i] = dist
    
    # Crear grafo completo
    G = nx.Graph()
    for i, node in enumerate(nodes):
        G.add_node(node[0], 
                  x=node[1], y=node[2], 
                  potencia=node[3], usuarios=node[4])
    
    # Agregar todas las aristas con pesos (distancias)
    for i in range(n_nodes):
        for j in range(i+1, n_nodes):
            if distances[i, j] > 0:
                G.add_edge(nodes[i][0], nodes[j][0], weight=distances[i, j])
    
    # Calcular MST
    mst = nx.minimum_spanning_tree(G)
    
    # Convertir a grafo dirigido con raíz en subestación
    mst_directed = nx.DiGraph()
    mst_directed.add_nodes_from(mst.nodes(data=True))
    
    # BFS desde subestación para orientar aristas
    visited = set()
    queue = ['SUBSTATION']
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        for neighbor in mst.neighbors(current):
            if neighbor not in visited:
                mst_directed.add_edge(current, neighbor, 
                                    weight=mst[current][neighbor]['weight'])
                queue.append(neighbor)
    
    return mst_directed

def calculate_topology_features(mst, node_id):
    """
    Calcular características topológicas para un nodo
    """
    features = {}
    
    # Número de saltos desde subestación
    try:
        path = nx.shortest_path(mst, 'SUBSTATION', node_id)
        features['numero_saltos'] = len(path) - 1
    except:
        features['numero_saltos'] = -1
    
    # Es nodo hoja
    features['es_nodo_hoja'] = mst.out_degree(node_id) == 0
    
    # Profundidad en el árbol
    features['profundidad_arbol'] = features['numero_saltos']
    
    # kVA aguas abajo (suma de todos los descendientes)
    descendants = nx.descendants(mst, node_id)
    kva_downstream = sum(mst.nodes[d]['potencia'] for d in descendants)
    features['kVA_aguas_abajo'] = kva_downstream + mst.nodes[node_id]['potencia']
    
    # Usuarios aguas abajo
    users_downstream = sum(mst.nodes[d]['usuarios'] for d in descendants)
    features['usuarios_aguas_abajo'] = users_downstream + mst.nodes[node_id]['usuarios']
    
    # Número de descendientes
    features['num_descendientes'] = len(descendants)
    
    # Padre en el MST
    predecessors = list(mst.predecessors(node_id))
    features['padre_mst'] = predecessors[0] if predecessors else None
    
    # Centralidad de intermediación normalizada
    G_undirected = mst.to_undirected()
    betweenness = nx.betweenness_centrality(G_undirected)
    features['centralidad_intermediacion'] = betweenness.get(node_id, 0)
    
    return features

def process_feeder(feeder_name, df_feeder, output_data):
    """
    Procesar un alimentador completo
    """
    print(f"\n  Procesando alimentador: {feeder_name}")
    print(f"    - {len(df_feeder)} transformadores")
    
    # Identificar subestación
    sub_x, sub_y, strategy = identify_substation(df_feeder)
    print(f"    - Subestación identificada ({strategy}): ({sub_x:.6f}, {sub_y:.6f})")
    
    # Construir MST
    mst = build_mst_topology(df_feeder, (sub_x, sub_y))
    print(f"    - MST construido: {mst.number_of_nodes()} nodos, {mst.number_of_edges()} aristas")
    
    # Calcular features para cada transformador
    for idx, row in df_feeder.iterrows():
        codigo = row['Codigo']
        if codigo in mst:
            features = calculate_topology_features(mst, codigo)
            
            # Agregar a datos de salida
            output_data['Codigo'].append(codigo)
            output_data['Alimentador'].append(feeder_name)
            output_data['substation_x'].append(sub_x)
            output_data['substation_y'].append(sub_y)
            output_data['substation_strategy'].append(strategy)
            
            for key, value in features.items():
                output_data[key].append(value)
    
    return mst, (sub_x, sub_y)

def visualize_mst(mst, substation_coords, feeder_name, save_path):
    """
    Visualizar el MST de un alimentador
    """
    plt.figure(figsize=(14, 10))
    
    # Preparar posiciones
    pos = {}
    for node in mst.nodes():
        if node == 'SUBSTATION':
            pos[node] = (substation_coords[0], substation_coords[1])
        else:
            pos[node] = (mst.nodes[node]['x'], mst.nodes[node]['y'])
    
    # Colores por tipo de nodo
    node_colors = []
    node_sizes = []
    for node in mst.nodes():
        if node == 'SUBSTATION':
            node_colors.append('red')
            node_sizes.append(500)
        else:
            potencia = mst.nodes[node]['potencia']
            if potencia >= 315:
                node_colors.append('orange')
                node_sizes.append(300)
            elif potencia >= 100:
                node_colors.append('yellow')
                node_sizes.append(200)
            else:
                node_colors.append('lightblue')
                node_sizes.append(100)
    
    # Dibujar
    nx.draw_networkx_nodes(mst, pos, 
                          node_color=node_colors, 
                          node_size=node_sizes,
                          alpha=0.8)
    nx.draw_networkx_edges(mst, pos, 
                          edge_color='gray', 
                          width=1.5,
                          alpha=0.6,
                          arrows=True,
                          arrowsize=10)
    
    # Resaltar subestación
    nx.draw_networkx_nodes(mst, pos,
                          nodelist=['SUBSTATION'],
                          node_color='red',
                          node_size=600,
                          node_shape='s')
    
    plt.title(f'Topología MST - Alimentador: {feeder_name}', fontsize=14)
    plt.xlabel('Longitud')
    plt.ylabel('Latitud')
    
    # Leyenda
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', label='Subestación'),
        Patch(facecolor='orange', label='Trafo Grande (≥315 kVA)'),
        Patch(facecolor='yellow', label='Trafo Mediano (100-315 kVA)'),
        Patch(facecolor='lightblue', label='Trafo Pequeño (<100 kVA)')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    """Función principal"""
    print("=" * 80)
    print("FASE 0 - RECONSTRUCCIÓN DE TOPOLOGÍA CON MST")
    print("=" * 80)
    
    # Cargar datos
    df_transformers, df_feeders = load_data()
    
    # Inicializar estructura de datos de salida
    output_data = {
        'Codigo': [],
        'Alimentador': [],
        'substation_x': [],
        'substation_y': [],
        'substation_strategy': [],
        'numero_saltos': [],
        'es_nodo_hoja': [],
        'profundidad_arbol': [],
        'kVA_aguas_abajo': [],
        'usuarios_aguas_abajo': [],
        'num_descendientes': [],
        'padre_mst': [],
        'centralidad_intermediacion': []
    }
    
    # Directorio para visualizaciones
    viz_dir = OUTPUT_DIR / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    # Procesar cada alimentador
    topologies = {}
    substations = {}
    
    # Seleccionar alimentadores top para visualización
    top_feeders = df_feeders.nlargest(10, 'usuarios_totales')['Alimentador'].tolist()
    
    for i, feeder in enumerate(df_transformers['Alimentador'].unique()):
        df_feeder = df_transformers[df_transformers['Alimentador'] == feeder].copy()
        
        if len(df_feeder) < 2:
            print(f"\n  ⚠️ Saltando alimentador {feeder} (solo {len(df_feeder)} transformador)")
            continue
        
        mst, substation = process_feeder(feeder, df_feeder, output_data)
        topologies[feeder] = mst
        substations[feeder] = substation
        
        # Visualizar solo los top alimentadores
        if feeder in top_feeders:
            viz_path = viz_dir / f"mst_topology_{feeder.replace('/', '_')}.png"
            visualize_mst(mst, substation, feeder, viz_path)
            print(f"    ✓ Visualización guardada")
    
    # Crear DataFrame de salida
    df_output = pd.DataFrame(output_data)
    
    # Merge con datos originales
    df_final = df_transformers.merge(
        df_output[['Codigo'] + [col for col in df_output.columns if col not in ['Codigo', 'Alimentador']]],
        on='Codigo',
        how='left'
    )
    
    # Guardar resultados
    output_file = OUTPUT_DIR / "transformadores_mst_topology.csv"
    df_final.to_csv(output_file, index=False)
    print(f"\n✓ Resultados guardados en: {output_file}")
    
    # Generar reporte resumen
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_alimentadores_procesados': len(topologies),
        'total_transformadores': len(df_output),
        'estadisticas_topologicas': {
            'promedio_saltos_desde_subestacion': df_output['numero_saltos'].mean(),
            'max_saltos': df_output['numero_saltos'].max(),
            'porcentaje_nodos_hoja': (df_output['es_nodo_hoja'].sum() / len(df_output)) * 100,
            'promedio_kVA_aguas_abajo': df_output['kVA_aguas_abajo'].mean(),
            'max_kVA_aguas_abajo': df_output['kVA_aguas_abajo'].max()
        },
        'estrategias_subestacion': pd.DataFrame(output_data).groupby('substation_strategy').size().to_dict(),
        'top_nodos_criticos': df_output.nlargest(10, 'centralidad_intermediacion')[
            ['Codigo', 'Alimentador', 'centralidad_intermediacion', 'kVA_aguas_abajo']
        ].to_dict('records')
    }
    
    report_file = OUTPUT_DIR / "mst_topology_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Reporte guardado en: {report_file}")
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS")
    print("=" * 80)
    print(f"• Alimentadores procesados: {len(topologies)}")
    print(f"• Transformadores con topología: {len(df_output)}")
    print(f"• Promedio saltos desde subestación: {df_output['numero_saltos'].mean():.2f}")
    print(f"• Máximo saltos: {df_output['numero_saltos'].max()}")
    print(f"• Nodos hoja: {df_output['es_nodo_hoja'].sum()} ({(df_output['es_nodo_hoja'].sum()/len(df_output))*100:.1f}%)")
    print(f"• Visualizaciones generadas: {len(top_feeders)}")
    
    # Top nodos críticos por centralidad
    print("\nTop 5 Nodos Críticos por Centralidad:")
    top_critical = df_output.nlargest(5, 'centralidad_intermediacion')
    for _, row in top_critical.iterrows():
        print(f"  - {row['Codigo']} ({row['Alimentador']}): "
              f"Centralidad={row['centralidad_intermediacion']:.3f}, "
              f"kVA aguas abajo={row['kVA_aguas_abajo']:.0f}")

if __name__ == "__main__":
    main()