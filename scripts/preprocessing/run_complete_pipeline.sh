#!/bin/bash
# Script para ejecutar el pipeline completo de preprocesamiento

echo "=========================================="
echo "EJECUTANDO PIPELINE COMPLETO DE DATOS"
echo "=========================================="

# Activar entorno virtual
source venv/bin/activate

# Ejecutar scripts en orden
echo -e "\n1. Conversión Excel a CSV..."
python scripts/preprocessing/00_excel_to_csv.py

echo -e "\n2. Validación de datos..."
python scripts/preprocessing/01_validate_data.py

echo -e "\n3. Limpieza y enriquecimiento..."
python scripts/preprocessing/02_clean_enrich_data.py

echo -e "\n4. Creación de agregaciones..."
python scripts/preprocessing/03_create_aggregations.py

echo -e "\n5. Análisis de criticidad..."
python scripts/preprocessing/04_analyze_criticality.py

echo -e "\n6. Creación de base de datos..."
python scripts/preprocessing/05_create_database.py

echo -e "\n=========================================="
echo "PIPELINE COMPLETADO"
echo "=========================================="

# Verificar usuarios totales
echo -e "\nVerificando usuarios totales:"
sqlite3 data/database/edersa_quality.db "SELECT 'Usuarios en BD:', SUM(q_usuarios) FROM transformadores;"

echo -e "\nDatos oficiales EDERSA: 245,940 clientes"