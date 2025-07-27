#!/usr/bin/env python3
"""
Script de búsqueda en la Knowledge Base de Generación Distribuida
Permite buscar conceptos clave en todos los documentos KB
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
from collections import defaultdict

# Colores para output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def search_in_file(file_path: Path, query: str, context_lines: int = 2) -> List[Dict]:
    """Busca en un archivo y retorna matches con contexto"""
    results = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        query_lower = query.lower()
        
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                # Extraer contexto
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                
                context = ''.join(lines[start:end])
                
                results.append({
                    'file': file_path.name,
                    'line_num': i + 1,
                    'line': line.strip(),
                    'context': context,
                    'section': get_section_name(file_path)
                })
    
    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")
    
    return results

def get_section_name(file_path: Path) -> str:
    """Obtiene el nombre de la sección basado en el archivo"""
    mapping = {
        'KB_1': '1. Marco Teórico',
        'KB_2': '2. Sistema de Análisis',
        'KB_3': '3. Cálculo de Pérdidas',
        'KB_4': '4. Q at Night',
        'KB_5': '5. Beneficios Multipropósito',
        'KB_6': '6. Análisis Económico',
        'KB_7': '7. Casos de Estudio',
        'KB_8': '8. Guía de Implementación',
        'KB_9': '9. Guías Operativas'
    }
    
    for prefix, name in mapping.items():
        if prefix in file_path.name:
            return name
    
    return file_path.parent.name

def search_knowledge_base(query: str, kb_path: Path, context_lines: int = 2) -> Dict[str, List[Dict]]:
    """Busca en toda la Knowledge Base"""
    results_by_file = defaultdict(list)
    
    # Buscar en todos los archivos .md
    for md_file in kb_path.rglob('*.md'):
        if md_file.name == 'README.md' or md_file.name == 'INDICE_KB_EDERSA.md':
            continue  # Saltar índices
            
        matches = search_in_file(md_file, query, context_lines)
        if matches:
            results_by_file[str(md_file)] = matches
    
    return dict(results_by_file)

def display_results(results: Dict[str, List[Dict]], query: str):
    """Muestra los resultados de forma legible"""
    
    if not results:
        print(f"\n{Colors.YELLOW}No se encontraron resultados para '{query}'{Colors.ENDC}")
        return
    
    total_matches = sum(len(matches) for matches in results.values())
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}Encontrados {total_matches} resultados para '{query}'{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*80}{Colors.ENDC}")
    
    for file_path, matches in results.items():
        file_name = Path(file_path).name
        section = matches[0]['section']
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}📄 {section} - {file_name}{Colors.ENDC}")
        print(f"{Colors.CYAN}   {len(matches)} coincidencias{Colors.ENDC}")
        
        for match in matches[:3]:  # Mostrar máximo 3 por archivo
            print(f"\n   {Colors.YELLOW}Línea {match['line_num']}:{Colors.ENDC}")
            
            # Resaltar la query en el contexto
            highlighted_context = match['context'].replace(
                query, 
                f"{Colors.RED}{Colors.BOLD}{query}{Colors.ENDC}"
            ).replace(
                query.lower(), 
                f"{Colors.RED}{Colors.BOLD}{query.lower()}{Colors.ENDC}"
            ).replace(
                query.upper(), 
                f"{Colors.RED}{Colors.BOLD}{query.upper()}{Colors.ENDC}"
            )
            
            # Indentar el contexto
            for line in highlighted_context.split('\n'):
                if line.strip():
                    print(f"   {line}")
        
        if len(matches) > 3:
            print(f"\n   {Colors.CYAN}... y {len(matches) - 3} coincidencias más{Colors.ENDC}")

def suggest_related_topics(query: str):
    """Sugiere temas relacionados basados en la query"""
    suggestions = {
        'q at night': ['reactiva', 'STATCOM', 'nocturno', '24 horas'],
        'perdidas': ['I²R', 'técnicas', 'reducción', 'flujo'],
        'economico': ['TIR', 'VPN', 'LCOE', 'payback'],
        'implementacion': ['guía', 'paso a paso', 'checklist'],
        'casos': ['benchmarks', 'ratios', 'éxito', 'ejemplos'],
        'beneficios': ['multipropósito', 'sistémicos', 'valor']
    }
    
    query_lower = query.lower()
    related = []
    
    for key, values in suggestions.items():
        if key in query_lower:
            related.extend(values)
    
    if related:
        print(f"\n{Colors.CYAN}💡 Temas relacionados:{Colors.ENDC}")
        for topic in related[:5]:
            print(f"   - {topic}")

def main():
    parser = argparse.ArgumentParser(
        description='Buscar en la Knowledge Base de Generación Distribuida',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python kb_search.py "Q at Night"          # Buscar concepto específico
  python kb_search.py perdidas -c 5         # Buscar con más contexto
  python kb_search.py TIR                   # Buscar términos económicos
  python kb_search.py "casos de éxito"      # Buscar frases
        """
    )
    
    parser.add_argument(
        'query',
        help='Término o frase a buscar en la Knowledge Base'
    )
    
    parser.add_argument(
        '-c', '--context',
        type=int,
        default=2,
        help='Líneas de contexto a mostrar (default: 2)'
    )
    
    args = parser.parse_args()
    
    # Determinar path de la KB
    script_dir = Path(__file__).parent
    kb_path = script_dir.parent / 'docs' / 'knowledge_base'
    
    if not kb_path.exists():
        print(f"{Colors.RED}Error: No se encuentra la Knowledge Base en {kb_path}{Colors.ENDC}")
        sys.exit(1)
    
    # Realizar búsqueda
    results = search_knowledge_base(args.query, kb_path, args.context)
    
    # Mostrar resultados
    display_results(results, args.query)
    
    # Sugerir temas relacionados
    suggest_related_topics(args.query)
    
    print(f"\n{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.GREEN}Tip: Para ver el documento completo, navega a:{Colors.ENDC}")
    print(f"     docs/knowledge_base/INDICE_KB_EDERSA.md")

if __name__ == '__main__':
    main()