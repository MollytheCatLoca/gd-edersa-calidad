#!/usr/bin/env python3
"""
Script para probar la página fixed directamente
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

print("Iniciando dashboard...")
print("Navega a: http://127.0.0.1:8050/optimization-fixed")
print("Presiona Ctrl+C para detener")

# Import and run the app
from dashboard.app_multipagina import app

if __name__ == "__main__":
    app.run(debug=True, port=8050)