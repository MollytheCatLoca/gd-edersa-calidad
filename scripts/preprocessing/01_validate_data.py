#!/usr/bin/env python3
"""
01_validate_data.py - Validación y separación de datasets

Segundo paso del pipeline de preprocesamiento.
Valida datos y separa en dos datasets:
- Dataset A: Transformadores con medición de calidad (para análisis)
- Dataset B: Inventario completo georeferenciado (para cobertura)

Autor: Claude
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
import json
import logging
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Configurar paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_FILE = PROJECT_ROOT / "config" / "preprocessing_config.yaml"

# Crear directorios si no existen
for dir_path in [DATA_PROCESSED, REPORTS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Configurar logging
log_file = LOGS_DIR / f"01_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Carga la configuración del archivo YAML."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuración cargada desde {CONFIG_FILE}")
        return config
    except Exception as e:
        logger.error(f"Error cargando configuración: {e}")
        raise


def validate_data_types(df: pd.DataFrame, expected_types: Dict[str, type]) -> Dict[str, List[str]]:
    """Valida tipos de datos y convierte cuando es posible."""
    issues = {
        "type_mismatches": [],
        "conversion_failures": [],
        "conversions_made": []
    }
    
    for col, expected_type in expected_types.items():
        if col not in df.columns:
            continue
            
        current_type = df[col].dtype
        
        # Mapeo de tipos esperados a pandas dtypes
        type_map = {
            'str': 'object',
            'float': 'float64',
            'int': 'int64'
        }
        
        expected_dtype = type_map.get(expected_type, expected_type)
        
        # Si ya es del tipo correcto, continuar
        if str(current_type) == expected_dtype:
            continue
            
        # Intentar conversión
        try:
            if expected_type == 'float':
                # Para float, convertir primero a numérico
                df[col] = pd.to_numeric(df[col], errors='coerce')
                issues["conversions_made"].append(f"{col}: {current_type} → float64")
            elif expected_type == 'int':
                # Para int, primero a float, luego a int (maneja NaN)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Solo convertir a int si no hay NaN
                if not df[col].isna().any():
                    df[col] = df[col].astype('int64')
                    issues["conversions_made"].append(f"{col}: {current_type} → int64")
            elif expected_type == 'str':
                df[col] = df[col].astype(str)
                # Reemplazar 'nan' strings con NaN real
                df[col] = df[col].replace('nan', np.nan)
                issues["conversions_made"].append(f"{col}: {current_type} → object")
                
        except Exception as e:
            issues["conversion_failures"].append(f"{col}: {str(e)}")
            
    return issues


def validate_ranges(df: pd.DataFrame, ranges: Dict[str, Dict]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Valida rangos numéricos y marca registros fuera de rango."""
    validation_flags = pd.DataFrame(index=df.index)
    range_details = {}
    
    for col, range_spec in ranges.items():
        if col not in df.columns:
            continue
            
        # Crear columna de validación
        flag_col = f"{col}_valid"
        validation_flags[flag_col] = True
        
        # Validar solo valores no nulos
        mask_not_null = df[col].notna()
        
        violations_detail = {}
        
        if 'min' in range_spec:
            mask_min = df[col] >= range_spec['min']
            validation_flags.loc[mask_not_null, flag_col] &= mask_min[mask_not_null]
            below_min = df[mask_not_null & (df[col] < range_spec['min'])]
            if len(below_min) > 0:
                violations_detail['below_min'] = {
                    'count': len(below_min),
                    'values': below_min[col].value_counts().head(5).to_dict()
                }
            
        if 'max' in range_spec:
            mask_max = df[col] <= range_spec['max']
            validation_flags.loc[mask_not_null, flag_col] &= mask_max[mask_not_null]
            above_max = df[mask_not_null & (df[col] > range_spec['max'])]
            if len(above_max) > 0:
                violations_detail['above_max'] = {
                    'count': len(above_max),
                    'values': above_max[col].value_counts().head(5).to_dict()
                }
            
        # Contar violaciones totales
        violations = (~validation_flags[flag_col] & mask_not_null).sum()
        if violations > 0:
            logger.warning(f"  {col}: {violations} valores fuera de rango [{range_spec.get('min', '-∞')}, {range_spec.get('max', '∞')}]")
            range_details[col] = violations_detail
            
            # Caso especial para Potencia = 0
            if col == 'Potencia' and 'below_min' in violations_detail:
                zeros = (df[col] == 0).sum()
                if zeros > 0:
                    logger.warning(f"    → {zeros} transformadores con potencia 0 kVA (posible error de datos)")
            
    return validation_flags, range_details


def analyze_transformer_circuits(df: pd.DataFrame) -> Dict[str, Any]:
    """Analiza transformadores con múltiples circuitos (no son duplicados)."""
    circuits_info = {}
    
    # Análisis de circuitos por transformador
    circuits_per_transformer = df.groupby('Codigoct')['Nro de circuito'].agg(['count', 'nunique'])
    
    # Transformadores con múltiples circuitos
    multi_circuit = circuits_per_transformer[circuits_per_transformer['nunique'] > 1]
    single_circuit = circuits_per_transformer[circuits_per_transformer['nunique'] == 1]
    
    circuits_info["total_transformers"] = int(circuits_per_transformer.index.nunique())
    circuits_info["single_circuit_transformers"] = int(len(single_circuit))
    circuits_info["multi_circuit_transformers"] = int(len(multi_circuit))
    circuits_info["total_circuits"] = int(df['Nro de circuito'].count())
    
    # Distribución de número de circuitos
    circuit_distribution = circuits_per_transformer['nunique'].value_counts().sort_index().to_dict()
    circuits_info["circuits_distribution"] = {int(k): int(v) for k, v in circuit_distribution.items()}
    
    # Análisis de mediciones temporales
    mediciones_info = {
        "total_mediciones": int(df['Nro de medicion'].nunique()),
        "sin_medicion": int((df['Nro de medicion'] == -1).sum()),
        "con_medicion": int((df['Nro de medicion'] >= 0).sum()),
        "max_mediciones": int(df['Nro de medicion'].max()) if df['Nro de medicion'].max() >= 0 else 0
    }
    circuits_info["mediciones_temporales"] = mediciones_info
    
    # Ejemplos de transformadores con múltiples circuitos
    if len(multi_circuit) > 0:
        examples = []
        for idx in multi_circuit.head(3).index:
            transformer_data = df[df['Codigoct'] == idx]
            examples.append({
                "codigo": idx,
                "num_circuitos": int(multi_circuit.loc[idx, 'nunique']),
                "circuitos": transformer_data['Nro de circuito'].unique().tolist(),
                "tiene_mediciones": bool((transformer_data['Resultado'].notna()).any())
            })
        circuits_info["multi_circuit_examples"] = examples
    
    logger.info(f"  Transformadores únicos: {circuits_info['total_transformers']}")
    logger.info(f"  Con circuito único: {circuits_info['single_circuit_transformers']}")
    logger.info(f"  Con múltiples circuitos: {circuits_info['multi_circuit_transformers']}")
    
    return circuits_info


def separate_datasets(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Separa el dataset en tres grupos:
    - Dataset A: Con medición de calidad
    - Dataset B: Inventario completo georeferenciado  
    - Excluidos: Registros problemáticos
    """
    logger.info("\nSeparando datasets...")
    
    # Valores válidos de resultado para análisis
    valid_quality_results = ['Correcta', 'Penalizada', 'Fallida']
    
    # Dataset A: Transformadores con medición de calidad
    mask_quality = df['Resultado'].isin(valid_quality_results)
    dataset_a = df[mask_quality].copy()
    
    # Dataset B: Todos con georeferenciación válida (incluye los de Dataset A)
    mask_georef = (
        df['Coord_X'].notna() & 
        df['Coord_Y'].notna() & 
        (df['Coord_X'] != 0) & 
        (df['Coord_Y'] != 0)
    )
    dataset_b = df[mask_georef].copy()
    
    # Excluidos: Sin georeferenciación
    excluded = df[~mask_georef].copy()
    
    # Agregar flags identificadores
    dataset_a['dataset'] = 'quality_analysis'
    dataset_b['dataset'] = 'full_inventory'
    dataset_b['has_quality_data'] = dataset_b['Resultado'].isin(valid_quality_results)
    excluded['dataset'] = 'excluded'
    excluded['exclusion_reason'] = 'sin_georeferenciacion'
    
    logger.info(f"  Dataset A (análisis calidad): {len(dataset_a):,} registros")
    logger.info(f"  Dataset B (inventario total): {len(dataset_b):,} registros")
    logger.info(f"  Excluidos: {len(excluded):,} registros")
    
    # Análisis de "No Instalado" y otros
    no_instalado = df[df['Resultado'] == 'No Instalado']
    otros = df[df['Resultado'].isin(['???'])]
    sin_resultado = df[df['Resultado'].isna()]
    
    logger.info(f"\nRegistros especiales:")
    logger.info(f"  No Instalado: {len(no_instalado):,}")
    logger.info(f"  ???: {len(otros):,}")
    logger.info(f"  Sin resultado (no medidos): {len(sin_resultado):,}")
    
    return dataset_a, dataset_b, excluded


def generate_validation_report(
    df_original: pd.DataFrame,
    dataset_a: pd.DataFrame,
    dataset_b: pd.DataFrame,
    excluded: pd.DataFrame,
    validation_results: Dict
) -> Dict:
    """Genera reporte completo de validación."""
    
    # Función helper para convertir tipos numpy a Python nativos
    def convert_to_native(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_records": int(len(df_original)),
            "dataset_a_records": int(len(dataset_a)),
            "dataset_b_records": int(len(dataset_b)),
            "excluded_records": int(len(excluded)),
            "quality_coverage": float(len(dataset_a) / len(df_original) * 100) if len(df_original) > 0 else 0,
            "georef_coverage": float(len(dataset_b) / len(df_original) * 100) if len(df_original) > 0 else 0
        },
        "data_quality": {
            "type_issues": validation_results.get("type_issues", {}),
            "range_violations": validation_results.get("range_violations", {}),
            "range_details": validation_results.get("range_details", {}),
            "circuits_analysis": validation_results.get("circuits_analysis", {}),
            "missing_values": {}
        },
        "dataset_characteristics": {
            "dataset_a": {
                "quality_distribution": dataset_a['Resultado'].value_counts().to_dict() if 'Resultado' in dataset_a else {},
                "sucursales": int(dataset_a['N_Sucursal'].nunique()) if 'N_Sucursal' in dataset_a else 0,
                "alimentadores": int(dataset_a['Alimentador'].nunique()) if 'Alimentador' in dataset_a else 0,
                "potencia_total_mva": float(dataset_a['Potencia'].sum() / 1000) if 'Potencia' in dataset_a else 0,
                "usuarios_totales": int(dataset_a['Q_Usuarios'].sum()) if 'Q_Usuarios' in dataset_a else 0
            },
            "dataset_b": {
                "con_calidad": int(dataset_b['has_quality_data'].sum()) if 'has_quality_data' in dataset_b else 0,
                "sin_calidad": int((~dataset_b['has_quality_data']).sum()) if 'has_quality_data' in dataset_b else 0,
                "localidades": int(dataset_b['N_Localida'].nunique()) if 'N_Localida' in dataset_b else 0,
                "bbox": {
                    "min_x": convert_to_native(dataset_b['Coord_X'].min()) if 'Coord_X' in dataset_b else None,
                    "max_x": convert_to_native(dataset_b['Coord_X'].max()) if 'Coord_X' in dataset_b else None,
                    "min_y": convert_to_native(dataset_b['Coord_Y'].min()) if 'Coord_Y' in dataset_b else None,
                    "max_y": convert_to_native(dataset_b['Coord_Y'].max()) if 'Coord_Y' in dataset_b else None
                }
            }
        },
        "excluded_analysis": {
            "total": int(len(excluded)),
            "reasons": excluded['exclusion_reason'].value_counts().to_dict() if 'exclusion_reason' in excluded else {},
            "affected_sucursales": excluded['N_Sucursal'].value_counts().to_dict() if 'N_Sucursal' in excluded else {}
        }
    }
    
    # Análisis de valores faltantes por columna clave
    key_columns = ['Codigoct', 'N_Sucursal', 'Alimentador', 'Potencia', 'Q_Usuarios', 
                   'N_Localida', 'Coord_X', 'Coord_Y', 'Resultado']
    
    for col in key_columns:
        if col in df_original.columns:
            missing_info = {
                "total_missing": int(df_original[col].isna().sum()),
                "percent_missing": float(df_original[col].isna().sum() / len(df_original) * 100),
                "dataset_a_missing": int(dataset_a[col].isna().sum()) if col in dataset_a else 0,
                "dataset_b_missing": int(dataset_b[col].isna().sum()) if col in dataset_b else 0
            }
            report["data_quality"]["missing_values"][col] = missing_info
    
    return report


def main():
    """Función principal del script."""
    logger.info("=" * 70)
    logger.info("INICIANDO VALIDACIÓN Y SEPARACIÓN DE DATASETS")
    logger.info("=" * 70)
    
    try:
        # Cargar configuración
        config = load_config()
        
        # Cargar datos
        input_file = DATA_INTERIM / "transformers_raw.csv"
        logger.info(f"\nCargando datos desde: {input_file}")
        df = pd.read_csv(input_file)
        logger.info(f"  Registros cargados: {len(df):,}")
        
        # Diccionario para almacenar resultados de validación
        validation_results = {}
        
        # 1. Validar tipos de datos
        logger.info("\n1. VALIDACIÓN DE TIPOS DE DATOS")
        type_issues = validate_data_types(df, config['columns']['dtypes'])
        validation_results["type_issues"] = type_issues
        
        for conversion in type_issues.get("conversions_made", []):
            logger.info(f"  ✓ {conversion}")
        for failure in type_issues.get("conversion_failures", []):
            logger.error(f"  ✗ {failure}")
        
        # 2. Validar rangos
        logger.info("\n2. VALIDACIÓN DE RANGOS")
        range_flags, range_details = validate_ranges(df, config['validation']['ranges'])
        validation_results["range_violations"] = {
            col: int((~range_flags[col]).sum()) 
            for col in range_flags.columns
        }
        validation_results["range_details"] = range_details
        
        # 3. Análisis de circuitos (no son duplicados)
        logger.info("\n3. ANÁLISIS DE CIRCUITOS POR TRANSFORMADOR")
        circuits_analysis = analyze_transformer_circuits(df)
        validation_results["circuits_analysis"] = circuits_analysis
        
        # 4. Separar datasets
        logger.info("\n4. SEPARACIÓN DE DATASETS")
        dataset_a, dataset_b, excluded = separate_datasets(df)
        
        # 5. Validaciones específicas por dataset
        logger.info("\n5. VALIDACIONES ESPECÍFICAS")
        
        # Dataset A - Validaciones estrictas
        logger.info("\nDataset A - Análisis de calidad:")
        required_cols_a = config['columns']['required']
        for col in required_cols_a:
            if col in dataset_a.columns:
                nulls = dataset_a[col].isna().sum()
                if nulls > 0:
                    logger.warning(f"  {col}: {nulls} valores nulos")
                else:
                    logger.info(f"  ✓ {col}: completo")
        
        # Dataset B - Información general
        logger.info("\nDataset B - Inventario completo:")
        logger.info(f"  Con datos de calidad: {dataset_b['has_quality_data'].sum():,}")
        logger.info(f"  Sin datos de calidad: {(~dataset_b['has_quality_data']).sum():,}")
        
        # 6. Generar reporte
        logger.info("\n6. GENERANDO REPORTE DE VALIDACIÓN")
        report = generate_validation_report(df, dataset_a, dataset_b, excluded, validation_results)
        
        # Guardar reporte JSON
        report_file = REPORTS_DIR / "01_validation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"  Reporte guardado en: {report_file}")
        
        # 7. Guardar datasets
        logger.info("\n7. GUARDANDO DATASETS VALIDADOS")
        
        # Dataset A - Para análisis de calidad
        output_a = DATA_PROCESSED / "dataset_a_quality_analysis.csv"
        dataset_a.to_csv(output_a, index=False)
        logger.info(f"  Dataset A guardado: {output_a}")
        
        # Dataset B - Inventario completo
        output_b = DATA_PROCESSED / "dataset_b_full_inventory.csv"
        dataset_b.to_csv(output_b, index=False)
        logger.info(f"  Dataset B guardado: {output_b}")
        
        # Excluidos
        if len(excluded) > 0:
            output_excluded = DATA_PROCESSED / "excluded_records.csv"
            excluded.to_csv(output_excluded, index=False)
            logger.info(f"  Registros excluidos guardados: {output_excluded}")
        
        # 8. Resumen final
        logger.info("\n" + "=" * 70)
        logger.info("VALIDACIÓN COMPLETADA")
        logger.info("=" * 70)
        logger.info(f"Dataset A (calidad): {len(dataset_a):,} registros ({report['summary']['quality_coverage']:.1f}%)")
        logger.info(f"Dataset B (inventario): {len(dataset_b):,} registros ({report['summary']['georef_coverage']:.1f}%)")
        logger.info(f"Excluidos: {len(excluded):,} registros")
        logger.info(f"\nLogs guardados en: {log_file}")
        logger.info("Próximo paso: Ejecutar 02_clean_enrich_data.py")
        
    except Exception as e:
        logger.error(f"\nERROR FATAL: {str(e)}")
        logger.exception("Detalles del error:")
        sys.exit(1)


if __name__ == "__main__":
    main()