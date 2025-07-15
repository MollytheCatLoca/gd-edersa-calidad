#!/bin/bash
# Script para ejecutar el dashboard EDERSA

echo "Iniciando Dashboard EDERSA..."
echo "================================"

# Activar entorno virtual
source venv/bin/activate

# Ejecutar dashboard
python3 dashboard/app_edersa.py