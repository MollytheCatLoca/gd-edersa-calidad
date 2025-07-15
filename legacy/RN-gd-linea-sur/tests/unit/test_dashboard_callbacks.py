#!/usr/bin/env python3
"""
Test para verificar que no hay callbacks duplicados en el dashboard
"""

import re
from pathlib import Path

def test_duplicate_callbacks():
    """Test para verificar que no hay callbacks duplicados en fase4_bess_lab_v2.py"""
    
    dashboard_file = Path("dashboard/pages/fase4_bess_lab_v2.py")
    
    if not dashboard_file.exists():
        print("❌ Archivo no encontrado")
        return False
    
    # Leer el archivo
    with open(dashboard_file, 'r') as f:
        content = f.read()
    
    # Buscar todos los outputs
    output_pattern = r'Output\([\'"]([^\'\"]+)[\'"],\s*[\'"]([^\'\"]+)[\'"]'
    outputs = re.findall(output_pattern, content)
    
    print("🔍 Verificando callbacks duplicados...")
    print("=" * 50)
    
    # Crear diccionario para contar outputs
    output_counts = {}
    for element_id, prop in outputs:
        key = f"{element_id}.{prop}"
        output_counts[key] = output_counts.get(key, 0) + 1
    
    # Verificar duplicados
    print("📋 Outputs encontrados:")
    duplicates = []
    for output, count in output_counts.items():
        if count > 1:
            print(f"❌ {output}: {count} veces (DUPLICADO)")
            duplicates.append(output)
        else:
            print(f"✅ {output}: {count} vez")
    
    print("\n📊 Resultados:")
    print("-" * 50)
    
    if duplicates:
        print(f"❌ ENCONTRADOS {len(duplicates)} OUTPUTS DUPLICADOS:")
        for dup in duplicates:
            print(f"   - {dup}")
        print("❌ Dashboard tendrá errores de callbacks duplicados")
        return False
    else:
        print("✅ NO HAY OUTPUTS DUPLICADOS")
        print("✅ Dashboard debería cargar sin errores de callbacks")
        return True

def test_callback_structure():
    """Test para verificar la estructura de callbacks"""
    
    dashboard_file = Path("dashboard/pages/fase4_bess_lab_v2.py")
    
    with open(dashboard_file, 'r') as f:
        content = f.read()
    
    # Contar callbacks
    callback_pattern = r'@callback'
    callbacks = re.findall(callback_pattern, content)
    
    print(f"\n🔧 Estructura de callbacks:")
    print(f"   - Total callbacks: {len(callbacks)}")
    
    # Verificar que cada callback tiene función
    callback_functions = re.findall(r'@callback.*?def (\w+)\(', content, re.DOTALL)
    print(f"   - Funciones callback: {len(callback_functions)}")
    
    for func in callback_functions:
        print(f"     • {func}()")
    
    return len(callbacks) == len(callback_functions)

if __name__ == "__main__":
    print("🧪 Testing Dashboard Callbacks")
    print("=" * 60)
    
    # Test de outputs duplicados
    no_duplicates = test_duplicate_callbacks()
    
    # Test de estructura
    structure_ok = test_callback_structure()
    
    print("\n🎯 Resultado Final:")
    print("=" * 60)
    
    if no_duplicates and structure_ok:
        print("✅ TODOS LOS TESTS PASARON")
        print("✅ Dashboard debería cargar sin errores de callbacks")
        print("✅ Problema de 'Duplicate callback outputs' resuelto")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("❌ Dashboard puede tener errores de callbacks")
        
    print("\n🚀 Próximo paso: Probar dashboard")
    print("   python3 dashboard/app_multipagina.py")