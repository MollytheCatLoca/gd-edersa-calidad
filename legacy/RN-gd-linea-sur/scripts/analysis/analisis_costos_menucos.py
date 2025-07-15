import sys
import os
sys.path = [p for p in sys.path if 'numpy' not in p]

import pandas as pd
import numpy as np
from pathlib import Path

# Rutas a los archivos
data_path = Path("/Users/maxkeczeli/Proyects/estudio-gd-linea-sur/data")
archivo1 = data_path / "Costo Los Menucos.xlsx"
archivo2 = data_path / "Costo ganeración Los Menucos Nov24Ene25.xlsx"
archivo3 = data_path / "LOS MENUCOS.xlsx"

print("=" * 80)
print("ANÁLISIS DE ARCHIVOS DE COSTOS - LOS MENUCOS")
print("=" * 80)

# Función para explorar archivo Excel
def explorar_excel(filepath, nombre):
    print(f"\n{'='*60}")
    print(f"ARCHIVO: {nombre}")
    print(f"{'='*60}")
    
    try:
        # Leer todas las hojas disponibles
        xl_file = pd.ExcelFile(filepath)
        hojas = xl_file.sheet_names
        print(f"\nHojas disponibles: {hojas}")
        
        # Analizar cada hoja
        for hoja in hojas:
            print(f"\n{'-'*40}")
            print(f"HOJA: {hoja}")
            print(f"{'-'*40}")
            
            df = pd.read_excel(filepath, sheet_name=hoja)
            print(f"Dimensiones: {df.shape}")
            print(f"\nColumnas: {list(df.columns)}")
            
            # Mostrar primeras filas
            print(f"\nPrimeras 5 filas:")
            print(df.head())
            
            # Información adicional si hay datos numéricos
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                print(f"\nEstadísticas de columnas numéricas:")
                print(df[numeric_cols].describe())
            
            # Buscar palabras clave relevantes
            keywords = ['costo', 'consumo', 'combustible', 'potencia', 'mw', 'kw', 
                       'gas', 'generac', 'motor', 'capex', 'opex', '$', 'litros', 'm3']
            
            # Buscar en nombres de columnas
            cols_relevantes = [col for col in df.columns if any(kw in str(col).lower() for kw in keywords)]
            if cols_relevantes:
                print(f"\nColumnas con información relevante: {cols_relevantes}")
            
            # Buscar valores únicos en columnas de texto que puedan ser categorías
            text_cols = df.select_dtypes(include=['object']).columns
            for col in text_cols[:5]:  # Limitar a primeras 5 columnas de texto
                valores_unicos = df[col].dropna().unique()
                if len(valores_unicos) < 20 and len(valores_unicos) > 0:
                    print(f"\nValores únicos en '{col}': {valores_unicos[:10]}")
            
    except Exception as e:
        print(f"Error al leer archivo: {e}")

# Analizar cada archivo
archivos = [
    (archivo1, "Costo Los Menucos.xlsx"),
    (archivo2, "Costo ganeración Los Menucos Nov24Ene25.xlsx"),
    (archivo3, "LOS MENUCOS.xlsx")
]

for archivo, nombre in archivos:
    if archivo.exists():
        explorar_excel(archivo, nombre)
    else:
        print(f"\nARCHIVO NO ENCONTRADO: {nombre}")