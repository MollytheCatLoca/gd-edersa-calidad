#!/usr/bin/env python3
"""
00_excel_to_csv.py - Conversión de Excel a CSV

Primer paso del pipeline de preprocesamiento.
Convierte el archivo Excel de EDERSA a CSV para procesamiento posterior.

Autor: Claude
Fecha: Julio 2025
"""

import pandas as pd
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import warnings

# Suprimir warnings de openpyxl
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Configurar paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorios si no existen
for dir_path in [DATA_INTERIM, REPORTS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Configurar logging
log_file = LOGS_DIR / f"00_excel_conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def inspect_excel(file_path: Path) -> dict:
    """
    Inspecciona el archivo Excel y retorna información sobre su estructura.
    """
    logger.info(f"Inspeccionando archivo: {file_path}")
    
    try:
        # Leer información básica del Excel
        xl_file = pd.ExcelFile(file_path)
        
        inspection = {
            "file_info": {
                "path": str(file_path),
                "size_mb": file_path.stat().st_size / (1024 * 1024),
                "sheets": xl_file.sheet_names,
                "sheet_count": len(xl_file.sheet_names)
            },
            "sheets_info": {}
        }
        
        # Inspeccionar cada hoja
        for sheet_name in xl_file.sheet_names:
            logger.info(f"  Analizando hoja: {sheet_name}")
            
            # Leer primeras filas para análisis
            df_sample = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10)
            df_shape = pd.read_excel(file_path, sheet_name=sheet_name, nrows=0)
            
            # Contar filas sin cargar todo en memoria
            total_rows = len(pd.read_excel(file_path, sheet_name=sheet_name, usecols=[0]))
            
            sheet_info = {
                "rows": total_rows,
                "columns": len(df_shape.columns),
                "column_names": list(df_shape.columns),
                "column_types": df_sample.dtypes.astype(str).to_dict(),
                "sample_data": df_sample.head(5).to_dict('records')
            }
            
            inspection["sheets_info"][sheet_name] = sheet_info
            
            logger.info(f"    - Filas: {total_rows:,}")
            logger.info(f"    - Columnas: {len(df_shape.columns)}")
        
        return inspection
        
    except Exception as e:
        logger.error(f"Error inspeccionando Excel: {str(e)}")
        raise


def excel_to_csv(input_path: Path, output_path: Path, sheet_name: str = "Hoja 1") -> dict:
    """
    Convierte el archivo Excel a CSV.
    """
    logger.info(f"Convirtiendo Excel a CSV...")
    logger.info(f"  Input: {input_path}")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Hoja: {sheet_name}")
    
    conversion_stats = {
        "start_time": datetime.now().isoformat(),
        "input_file": str(input_path),
        "output_file": str(output_path),
        "sheet_name": sheet_name
    }
    
    try:
        # Leer Excel
        logger.info("Leyendo archivo Excel...")
        df = pd.read_excel(input_path, sheet_name=sheet_name)
        
        # Estadísticas básicas
        conversion_stats["rows_read"] = len(df)
        conversion_stats["columns_read"] = len(df.columns)
        conversion_stats["memory_usage_mb"] = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        logger.info(f"  - Filas leídas: {len(df):,}")
        logger.info(f"  - Columnas: {len(df.columns)}")
        logger.info(f"  - Memoria utilizada: {conversion_stats['memory_usage_mb']:.2f} MB")
        
        # Información sobre tipos de datos
        dtype_counts = df.dtypes.value_counts()
        conversion_stats["data_types"] = {
            str(k): int(v) for k, v in dtype_counts.items()
        }
        
        # Verificar valores nulos
        null_counts = df.isnull().sum()
        columns_with_nulls = null_counts[null_counts > 0]
        conversion_stats["columns_with_nulls"] = len(columns_with_nulls)
        conversion_stats["null_summary"] = {
            col: int(count) for col, count in columns_with_nulls.items()
        }
        
        logger.info(f"  - Columnas con valores nulos: {len(columns_with_nulls)}")
        
        # Guardar como CSV
        logger.info("Guardando archivo CSV...")
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Verificar que se guardó correctamente
        if output_path.exists():
            conversion_stats["output_size_mb"] = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"  - Archivo CSV creado: {conversion_stats['output_size_mb']:.2f} MB")
        else:
            raise Exception("El archivo CSV no se creó correctamente")
        
        conversion_stats["end_time"] = datetime.now().isoformat()
        conversion_stats["status"] = "success"
        
        # Análisis adicional de columnas clave
        key_columns = ['Codigoct', 'N_Sucursal', 'Alimentador', 'Potencia', 'Q_Usuarios', 
                      'N_Localida', 'Coord_X', 'Coord_Y', 'Resultado']
        
        column_analysis = {}
        for col in key_columns:
            if col in df.columns:
                col_stats = {
                    "exists": True,
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "null_percentage": float(df[col].isnull().sum() / len(df) * 100),
                    "unique_values": int(df[col].nunique())
                }
                
                # Para columnas numéricas, agregar estadísticas
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_stats.update({
                        "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                        "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                        "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                        "std": float(df[col].std()) if not pd.isna(df[col].std()) else None
                    })
                
                # Para la columna Resultado, contar valores
                if col == 'Resultado':
                    col_stats["value_counts"] = df[col].value_counts().to_dict()
                
                column_analysis[col] = col_stats
            else:
                column_analysis[col] = {"exists": False}
                logger.warning(f"  - Columna esperada no encontrada: {col}")
        
        conversion_stats["column_analysis"] = column_analysis
        
        return conversion_stats
        
    except Exception as e:
        logger.error(f"Error en conversión: {str(e)}")
        conversion_stats["status"] = "error"
        conversion_stats["error"] = str(e)
        conversion_stats["end_time"] = datetime.now().isoformat()
        raise


def main():
    """
    Función principal del script.
    """
    logger.info("=" * 70)
    logger.info("INICIANDO CONVERSIÓN EXCEL A CSV")
    logger.info("=" * 70)
    
    # Archivos de entrada y salida
    input_file = DATA_RAW / "Mediciones Originales EDERSA.xlsx"
    output_file = DATA_INTERIM / "transformers_raw.csv"
    
    # Verificar que existe el archivo de entrada
    if not input_file.exists():
        logger.error(f"Archivo de entrada no encontrado: {input_file}")
        sys.exit(1)
    
    try:
        # 1. Inspeccionar Excel
        logger.info("\n1. INSPECCIÓN DEL ARCHIVO EXCEL")
        inspection_result = inspect_excel(input_file)
        
        # Guardar reporte de inspección
        inspection_report = REPORTS_DIR / "00_excel_inspection.json"
        with open(inspection_report, 'w', encoding='utf-8') as f:
            json.dump(inspection_result, f, indent=2, ensure_ascii=False)
        logger.info(f"  - Reporte de inspección guardado en: {inspection_report}")
        
        # 2. Convertir a CSV
        logger.info("\n2. CONVERSIÓN A CSV")
        conversion_result = excel_to_csv(input_file, output_file)
        
        # Guardar reporte de conversión
        conversion_report = REPORTS_DIR / "00_conversion_stats.json"
        with open(conversion_report, 'w', encoding='utf-8') as f:
            json.dump(conversion_result, f, indent=2, ensure_ascii=False)
        logger.info(f"  - Reporte de conversión guardado en: {conversion_report}")
        
        # 3. Resumen final
        logger.info("\n" + "=" * 70)
        logger.info("CONVERSIÓN COMPLETADA EXITOSAMENTE")
        logger.info("=" * 70)
        logger.info(f"Archivo CSV creado: {output_file}")
        logger.info(f"Registros procesados: {conversion_result['rows_read']:,}")
        logger.info(f"Columnas: {conversion_result['columns_read']}")
        logger.info(f"Tamaño archivo: {conversion_result['output_size_mb']:.2f} MB")
        
        # Mostrar resumen de calidad de datos
        if conversion_result['column_analysis'].get('Resultado', {}).get('exists'):
            resultado_values = conversion_result['column_analysis']['Resultado'].get('value_counts', {})
            logger.info("\nDistribución de calidad:")
            for estado, count in resultado_values.items():
                percentage = (count / conversion_result['rows_read']) * 100
                logger.info(f"  - {estado}: {count:,} ({percentage:.1f}%)")
        
        logger.info(f"\nLogs guardados en: {log_file}")
        logger.info("Próximo paso: Ejecutar 01_validate_data.py")
        
    except Exception as e:
        logger.error(f"\nERROR FATAL: {str(e)}")
        logger.error("La conversión falló. Revisar logs para más detalles.")
        sys.exit(1)


if __name__ == "__main__":
    main()