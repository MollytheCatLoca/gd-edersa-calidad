#!/bin/bash

# Setup script for Estudio GD Línea Sur project

echo "=== Setup del Proyecto Estudio GD Línea Sur ==="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado. Por favor instala Python 3.9 o superior."
    exit 1
fi

echo "Python 3 encontrado: $(python3 --version)"
echo ""

# Create virtual environment
echo "1. Creando entorno virtual..."
if [ -d "venv" ]; then
    echo "   El entorno virtual ya existe. ¿Deseas recrearlo? (s/n)"
    read -r response
    if [[ "$response" =~ ^[Ss]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo "   ✓ Entorno virtual recreado"
    else
        echo "   → Usando entorno virtual existente"
    fi
else
    python3 -m venv venv
    echo "   ✓ Entorno virtual creado"
fi

# Activate virtual environment
echo ""
echo "2. Activando entorno virtual..."
source venv/bin/activate
echo "   ✓ Entorno virtual activado"

# Upgrade pip
echo ""
echo "3. Actualizando pip..."
pip install --upgrade pip
echo "   ✓ pip actualizado"

# Install requirements
echo ""
echo "4. Instalando dependencias..."
echo "   Esto puede tomar varios minutos..."

# Install core requirements first
pip install numpy pandas scipy matplotlib seaborn

# Install visualization tools
pip install plotly folium dash

# Install Jupyter
pip install jupyter jupyterlab ipykernel

# Install network analysis
pip install networkx

# Install power systems (if available)
pip install pandapower || echo "   ⚠ pandapower no se pudo instalar"

# Install other requirements
pip install pyyaml tqdm openpyxl xlrd

echo "   ✓ Dependencias instaladas"

# Create Jupyter kernel
echo ""
echo "5. Creando kernel de Jupyter..."
python -m ipykernel install --user --name=linea_sur --display-name="Python (Línea Sur)"
echo "   ✓ Kernel de Jupyter creado"

# Create necessary directories
echo ""
echo "6. Verificando estructura de directorios..."
mkdir -p data/{raw,processed,interim,external}
mkdir -p notebooks/{01_exploratory,02_topology,03_data_processing,04_clustering,05_ml_models,06_power_flow,07_economic,08_optimization,09_reporting}
mkdir -p reports/{drafts,figures,tables,presentations,final}
mkdir -p models
mkdir -p logs
mkdir -p docs/{methodology,api,examples,topology,equipment,validation}
echo "   ✓ Directorios verificados"

echo ""
echo "=== Setup completado exitosamente! ==="
echo ""
echo "Para activar el entorno virtual en el futuro, ejecuta:"
echo "  source venv/bin/activate"
echo ""
echo "Para ejecutar Jupyter Lab:"
echo "  jupyter lab"
echo ""
echo "Para ejecutar el dashboard:"
echo "  python dashboard/app.py"
echo ""
echo "Para desactivar el entorno virtual:"
echo "  deactivate"
echo ""