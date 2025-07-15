#!/usr/bin/env python3
"""
05_create_database.py - Creación de base de datos SQLite para dashboard

Sexto y último paso del pipeline de preprocesamiento.
- Crea base de datos SQLite optimizada
- Carga todos los datasets procesados
- Crea índices para consultas rápidas
- Genera estadísticas finales

Autor: Claude
Fecha: Julio 2025
"""

import sqlite3
import pandas as pd
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Configurar paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DB_DIR = PROJECT_ROOT / "data" / "database"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorios necesarios
LOGS_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# Configurar logging
log_file = LOGS_DIR / f"05_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def create_tables(conn: sqlite3.Connection):
    """
    Crea las tablas necesarias en la base de datos.
    """
    logger.info("  Creando tablas...")
    
    cursor = conn.cursor()
    
    # Tabla principal de transformadores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transformadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigoct TEXT UNIQUE NOT NULL,
        n_sucursal TEXT,
        alimentador TEXT,
        n_localida TEXT,
        potencia REAL,
        q_usuarios INTEGER,
        coord_x REAL,
        coord_y REAL,
        tipoinstalacion TEXT,
        resultado TEXT,
        quality_score REAL,
        size_category TEXT,
        usuarios_por_kva REAL,
        factor_utilizacion_estimado REAL,
        zona_geografica TEXT,
        tipo_zona TEXT,
        densidad_local INTEGER,
        cluster_geografico_id INTEGER,
        criticidad_tecnica REAL,
        criticidad_usuarios REAL,
        criticidad_geografica REAL,
        criticidad_compuesta REAL,
        nivel_criticidad TEXT,
        prioridad_gd REAL,
        num_circuitos INTEGER,
        potencia_imputada BOOLEAN,
        gd_opportunity_score REAL,
        gd_priority TEXT,
        gd_capacity_recommended_kw REAL,
        gd_type_recommended TEXT
    );
    """)
    
    # Tabla de circuitos (inventario completo)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS circuitos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigoct TEXT NOT NULL,
        nro_circuito INTEGER,
        n_sucursal TEXT,
        alimentador TEXT,
        n_localida TEXT,
        potencia REAL,
        q_usuarios INTEGER,
        coord_x REAL,
        coord_y REAL,
        resultado TEXT,
        nro_medicion INTEGER,
        FOREIGN KEY (codigoct) REFERENCES transformadores(codigoct)
    );
    """)
    
    # Tabla de agregaciones por sucursal
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sucursales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        n_sucursal TEXT UNIQUE NOT NULL,
        num_transformadores INTEGER,
        potencia_total_kva REAL,
        potencia_promedio_kva REAL,
        potencia_mediana_kva REAL,
        usuarios_totales INTEGER,
        usuarios_promedio REAL,
        quality_score_promedio REAL,
        quality_score_desviacion REAL,
        criticidad_promedio REAL,
        criticidad_maxima REAL,
        prioridad_gd_promedio REAL,
        prioridad_gd_maxima REAL,
        circuitos_totales INTEGER,
        transformadores_imputados INTEGER,
        usuarios_por_kva_mean REAL,
        factor_utilizacion_estimado_mean REAL,
        indice_calidad REAL,
        categoria_tamano TEXT,
        pct_correcta REAL,
        pct_penalizada REAL,
        pct_fallida REAL,
        num_correcta INTEGER,
        num_penalizada INTEGER,
        num_fallida INTEGER
    );
    """)
    
    # Tabla de agregaciones por localidad
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS localidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        n_localida TEXT UNIQUE NOT NULL,
        num_transformadores INTEGER,
        potencia_total_kva REAL,
        usuarios_totales INTEGER,
        quality_score_promedio REAL,
        criticidad_promedio REAL,
        zona_geografica TEXT,
        indice_calidad REAL,
        pct_correcta REAL,
        pct_penalizada REAL,
        pct_fallida REAL
    );
    """)
    
    # Tabla de zonas críticas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS zonas_criticas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo_zona TEXT NOT NULL,
        categoria TEXT NOT NULL,
        nombre TEXT NOT NULL,
        criticidad_promedio REAL,
        num_transformadores INTEGER,
        usuarios_totales INTEGER,
        potencia_total_kva REAL,
        impacto_usuarios REAL
    );
    """)
    
    # Tabla de recomendaciones GD
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recomendaciones_gd (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigoct TEXT NOT NULL,
        score REAL,
        prioridad TEXT,
        capacidad_actual_kva REAL,
        usuarios INTEGER,
        criticidad REAL,
        calidad_actual TEXT,
        tipo_gd_recomendado TEXT,
        capacidad_gd_kw REAL,
        beneficios_esperados TEXT,
        FOREIGN KEY (codigoct) REFERENCES transformadores(codigoct)
    );
    """)
    
    # Tabla de métricas resumen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metricas_resumen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_actualizacion TIMESTAMP,
        total_transformadores INTEGER,
        total_circuitos INTEGER,
        total_usuarios INTEGER,
        capacidad_total_mva REAL,
        transformadores_correctos INTEGER,
        transformadores_penalizados INTEGER,
        transformadores_fallidos INTEGER,
        transformadores_criticos INTEGER,
        oportunidades_gd_alta_prioridad INTEGER,
        capacidad_gd_potencial_mw REAL,
        inversion_estimada_musd REAL,
        usuarios_beneficiados_gd INTEGER
    );
    """)
    
    conn.commit()
    logger.info("  Tablas creadas exitosamente")


def create_indexes(conn: sqlite3.Connection):
    """
    Crea índices para optimizar consultas.
    """
    logger.info("  Creando índices...")
    
    cursor = conn.cursor()
    
    # Índices para transformadores
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transformadores_sucursal ON transformadores(n_sucursal);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transformadores_localidad ON transformadores(n_localida);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transformadores_criticidad ON transformadores(criticidad_compuesta);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transformadores_gd_score ON transformadores(gd_opportunity_score);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transformadores_resultado ON transformadores(resultado);")
    
    # Índices para circuitos
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_circuitos_codigoct ON circuitos(codigoct);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_circuitos_sucursal ON circuitos(n_sucursal);")
    
    # Índices para agregaciones
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sucursales_criticidad ON sucursales(criticidad_promedio);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_localidades_criticidad ON localidades(criticidad_promedio);")
    
    conn.commit()
    logger.info("  Índices creados exitosamente")


def load_transformers_data(conn: sqlite3.Connection):
    """
    Carga datos de transformadores con análisis GD.
    """
    logger.info("  Cargando datos de transformadores...")
    
    # Cargar dataset con análisis GD
    df_path = DATA_PROCESSED / "transformers_gd_analysis.parquet"
    if not df_path.exists():
        # Si no existe, usar el análisis básico
        df_path = DATA_PROCESSED / "transformers_analysis.parquet"
    
    df = pd.read_parquet(df_path)
    
    # Seleccionar columnas relevantes
    columns = [
        'Codigoct', 'N_Sucursal', 'Alimentador', 'N_Localida', 'Potencia',
        'Q_Usuarios', 'Coord_X', 'Coord_Y', 'Tipoinstalacion', 'Resultado',
        'quality_score', 'size_category', 'usuarios_por_kva', 
        'factor_utilizacion_estimado', 'zona_geografica', 'tipo_zona',
        'densidad_local', 'cluster_geografico_id', 'criticidad_tecnica',
        'criticidad_usuarios', 'criticidad_geografica', 'criticidad_compuesta',
        'nivel_criticidad', 'prioridad_gd', 'num_circuitos', 'potencia_imputada'
    ]
    
    # Agregar columnas GD si existen
    gd_columns = ['gd_opportunity_score', 'gd_priority', 
                  'gd_capacity_recommended_kw', 'gd_type_recommended']
    
    for col in gd_columns:
        if col in df.columns:
            columns.append(col)
    
    # Filtrar columnas disponibles
    available_columns = [col for col in columns if col in df.columns]
    df_to_load = df[available_columns].copy()
    
    # Renombrar columnas para coincidir con la tabla
    df_to_load.columns = [col.lower() for col in df_to_load.columns]
    
    # Cargar a la base de datos
    df_to_load.to_sql('transformadores', conn, if_exists='append', index=False)
    logger.info(f"    {len(df_to_load)} transformadores cargados")
    
    return len(df_to_load)


def load_circuits_data(conn: sqlite3.Connection):
    """
    Carga datos del inventario completo de circuitos.
    """
    logger.info("  Cargando datos de circuitos...")
    
    # Cargar dataset de inventario
    df_path = DATA_PROCESSED / "circuits_inventory.parquet"
    if not df_path.exists():
        df_path = DATA_PROCESSED / "dataset_b_full_inventory.csv"
        df = pd.read_csv(df_path)
    else:
        df = pd.read_parquet(df_path)
    
    # Seleccionar columnas relevantes
    columns = [
        'Codigoct', 'Nro de circuito', 'N_Sucursal', 'Alimentador',
        'N_Localida', 'Potencia', 'Q_Usuarios', 'Coord_X', 'Coord_Y',
        'Resultado', 'Nro de medicion'
    ]
    
    # Filtrar columnas disponibles
    available_columns = [col for col in columns if col in df.columns]
    df_to_load = df[available_columns].copy()
    
    # Renombrar columnas
    rename_map = {
        'Codigoct': 'codigoct',
        'Nro de circuito': 'nro_circuito',
        'N_Sucursal': 'n_sucursal',
        'Alimentador': 'alimentador',
        'N_Localida': 'n_localida',
        'Potencia': 'potencia',
        'Q_Usuarios': 'q_usuarios',
        'Coord_X': 'coord_x',
        'Coord_Y': 'coord_y',
        'Resultado': 'resultado',
        'Nro de medicion': 'nro_medicion'
    }
    df_to_load.rename(columns=rename_map, inplace=True)
    
    # Cargar a la base de datos
    df_to_load.to_sql('circuitos', conn, if_exists='append', index=False)
    logger.info(f"    {len(df_to_load)} circuitos cargados")
    
    return len(df_to_load)


def load_aggregations(conn: sqlite3.Connection):
    """
    Carga datos agregados por sucursal y localidad.
    """
    logger.info("  Cargando agregaciones...")
    
    cursor = conn.cursor()
    
    # Cargar agregación por sucursal
    df_sucursal_path = DATA_PROCESSED / "aggregations" / "by_sucursal.parquet"
    if df_sucursal_path.exists():
        df_sucursal = pd.read_parquet(df_sucursal_path)
        
        # Renombrar columnas
        df_sucursal.columns = [col.lower() for col in df_sucursal.columns]
        
        # Obtener columnas de la tabla
        cursor.execute("PRAGMA table_info(sucursales)")
        table_columns = [row[1] for row in cursor.fetchall() if row[1] != 'id']
        
        # Filtrar solo columnas que existen en ambos
        available_columns = [col for col in table_columns if col in df_sucursal.columns]
        
        # Eliminar duplicados si existen (tomar el primer registro por sucursal)
        df_to_load = df_sucursal[available_columns].drop_duplicates(subset=['n_sucursal'], keep='first').copy()
        
        # Cargar a la base de datos
        df_to_load.to_sql('sucursales', conn, if_exists='append', index=False)
        logger.info(f"    {len(df_to_load)} sucursales cargadas")
    
    # Cargar agregación por localidad
    df_localidad_path = DATA_PROCESSED / "aggregations" / "by_localidad.parquet"
    if df_localidad_path.exists():
        df_localidad = pd.read_parquet(df_localidad_path)
        
        # Renombrar columnas
        df_localidad.columns = [col.lower() for col in df_localidad.columns]
        
        # Obtener columnas de la tabla
        cursor.execute("PRAGMA table_info(localidades)")
        table_columns = [row[1] for row in cursor.fetchall() if row[1] != 'id']
        
        # Filtrar solo columnas que existen en ambos
        available_columns = [col for col in table_columns if col in df_localidad.columns]
        
        # Eliminar duplicados si existen (tomar el primer registro por localidad)
        df_to_load = df_localidad[available_columns].drop_duplicates(subset=['n_localida'], keep='first').copy()
        
        # Cargar a la base de datos
        df_to_load.to_sql('localidades', conn, if_exists='append', index=False)
        logger.info(f"    {len(df_to_load)} localidades cargadas")


def load_critical_zones(conn: sqlite3.Connection):
    """
    Carga información de zonas críticas.
    """
    logger.info("  Cargando zonas críticas...")
    
    critical_zones_path = DATA_PROCESSED / "aggregations" / "critical_zones.json"
    if not critical_zones_path.exists():
        logger.warning("    No se encontró archivo de zonas críticas")
        return
    
    with open(critical_zones_path, 'r', encoding='utf-8') as f:
        critical_zones = json.load(f)
    
    cursor = conn.cursor()
    
    # Cargar sucursales críticas
    if 'sucursales' in critical_zones:
        for categoria, items in critical_zones['sucursales'].items():
            if isinstance(items, list):
                for item in items:
                    cursor.execute("""
                    INSERT INTO zonas_criticas 
                    (tipo_zona, categoria, nombre, criticidad_promedio, 
                     num_transformadores, usuarios_totales, potencia_total_kva, impacto_usuarios)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'sucursal', categoria, 
                        item.get('N_Sucursal', ''),
                        item.get('criticidad_promedio', 0),
                        item.get('num_transformadores', 0),
                        item.get('usuarios_totales', 0),
                        item.get('potencia_total_kva', 0),
                        item.get('impacto_usuarios', 0)
                    ))
    
    # Cargar localidades críticas
    if 'localidades' in critical_zones:
        for categoria, items in critical_zones['localidades'].items():
            if isinstance(items, list):
                for item in items:
                    cursor.execute("""
                    INSERT INTO zonas_criticas 
                    (tipo_zona, categoria, nombre, criticidad_promedio, 
                     num_transformadores, usuarios_totales, potencia_total_kva, impacto_usuarios)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'localidad', categoria,
                        item.get('N_Localida', ''),
                        item.get('criticidad_promedio', 0),
                        item.get('num_transformadores', 0),
                        item.get('usuarios_totales', 0),
                        0,  # No hay potencia en localidades
                        item.get('impacto_usuarios', 0)
                    ))
    
    conn.commit()
    logger.info("    Zonas críticas cargadas")


def load_gd_recommendations(conn: sqlite3.Connection):
    """
    Carga recomendaciones de GD.
    """
    logger.info("  Cargando recomendaciones GD...")
    
    recommendations_path = DATA_PROCESSED / "gd_recommendations.json"
    if not recommendations_path.exists():
        logger.warning("    No se encontró archivo de recomendaciones")
        return
    
    with open(recommendations_path, 'r', encoding='utf-8') as f:
        recommendations = json.load(f)
    
    cursor = conn.cursor()
    
    for rec in recommendations:
        # Convertir lista de beneficios a string
        beneficios = json.dumps(rec.get('beneficios_esperados', []), ensure_ascii=False)
        
        cursor.execute("""
        INSERT INTO recomendaciones_gd 
        (codigoct, score, prioridad, capacidad_actual_kva, usuarios,
         criticidad, calidad_actual, tipo_gd_recomendado, capacidad_gd_kw,
         beneficios_esperados)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec['codigo'],
            rec['score'],
            rec['prioridad'],
            rec['capacidad_actual_kva'],
            rec['usuarios'],
            rec['criticidad'],
            rec['calidad_actual'],
            rec['tipo_gd_recomendado'],
            rec['capacidad_gd_kw'],
            beneficios
        ))
    
    conn.commit()
    logger.info(f"    {len(recommendations)} recomendaciones cargadas")


def calculate_summary_metrics(conn: sqlite3.Connection):
    """
    Calcula y guarda métricas resumen.
    """
    logger.info("  Calculando métricas resumen...")
    
    cursor = conn.cursor()
    
    # Obtener métricas básicas
    metrics = {
        'fecha_actualizacion': datetime.now().isoformat()
    }
    
    # Total transformadores
    cursor.execute("SELECT COUNT(*) FROM transformadores")
    metrics['total_transformadores'] = cursor.fetchone()[0]
    
    # Total circuitos
    cursor.execute("SELECT COUNT(*) FROM circuitos")
    metrics['total_circuitos'] = cursor.fetchone()[0]
    
    # Total usuarios
    cursor.execute("SELECT SUM(q_usuarios) FROM transformadores")
    metrics['total_usuarios'] = cursor.fetchone()[0] or 0
    
    # Capacidad total
    cursor.execute("SELECT SUM(potencia) FROM transformadores")
    metrics['capacidad_total_mva'] = (cursor.fetchone()[0] or 0) / 1000
    
    # Distribución por resultado
    cursor.execute("""
    SELECT resultado, COUNT(*) 
    FROM transformadores 
    WHERE resultado IS NOT NULL 
    GROUP BY resultado
    """)
    resultados = dict(cursor.fetchall())
    metrics['transformadores_correctos'] = resultados.get('Correcta', 0)
    metrics['transformadores_penalizados'] = resultados.get('Penalizada', 0)
    metrics['transformadores_fallidos'] = resultados.get('Fallida', 0)
    
    # Transformadores críticos
    cursor.execute("""
    SELECT COUNT(*) 
    FROM transformadores 
    WHERE criticidad_compuesta > 0.5
    """)
    metrics['transformadores_criticos'] = cursor.fetchone()[0]
    
    # Oportunidades GD
    cursor.execute("""
    SELECT COUNT(*) 
    FROM transformadores 
    WHERE gd_priority IN ('Alta', 'Muy Alta')
    """)
    metrics['oportunidades_gd_alta_prioridad'] = cursor.fetchone()[0]
    
    # Capacidad GD potencial
    cursor.execute("""
    SELECT SUM(gd_capacity_recommended_kw) 
    FROM transformadores 
    WHERE gd_opportunity_score > 0.6
    """)
    metrics['capacidad_gd_potencial_mw'] = (cursor.fetchone()[0] or 0) / 1000
    
    # Obtener métricas de inversión del reporte
    report_path = REPORTS_DIR / "04_criticality_report.json"
    if report_path.exists():
        with open(report_path, 'r') as f:
            report = json.load(f)
            if 'expected_impact' in report:
                metrics['inversion_estimada_musd'] = report['expected_impact']['inversion_estimada']['total_millones_usd']
                metrics['usuarios_beneficiados_gd'] = report['expected_impact']['usuarios_beneficiados']
    
    # Insertar métricas
    cursor.execute("""
    INSERT INTO metricas_resumen 
    (fecha_actualizacion, total_transformadores, total_circuitos, total_usuarios,
     capacidad_total_mva, transformadores_correctos, transformadores_penalizados,
     transformadores_fallidos, transformadores_criticos, oportunidades_gd_alta_prioridad,
     capacidad_gd_potencial_mw, inversion_estimada_musd, usuarios_beneficiados_gd)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metrics['fecha_actualizacion'],
        metrics['total_transformadores'],
        metrics['total_circuitos'],
        metrics['total_usuarios'],
        metrics['capacidad_total_mva'],
        metrics['transformadores_correctos'],
        metrics['transformadores_penalizados'],
        metrics['transformadores_fallidos'],
        metrics['transformadores_criticos'],
        metrics['oportunidades_gd_alta_prioridad'],
        metrics['capacidad_gd_potencial_mw'],
        metrics.get('inversion_estimada_musd', 0),
        metrics.get('usuarios_beneficiados_gd', 0)
    ))
    
    conn.commit()
    logger.info("    Métricas resumen calculadas")
    
    return metrics


def generate_database_report(metrics: Dict) -> Dict:
    """
    Genera reporte de la base de datos creada.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "database_info": {
            "path": str(DB_DIR / "edersa_quality.db"),
            "size_mb": round((DB_DIR / "edersa_quality.db").stat().st_size / 1024 / 1024, 2),
            "tables": [
                "transformadores",
                "circuitos",
                "sucursales",
                "localidades",
                "zonas_criticas",
                "recomendaciones_gd",
                "metricas_resumen"
            ]
        },
        "data_summary": metrics,
        "ready_for_dashboard": True,
        "next_steps": [
            "Ejecutar el dashboard con: python dashboard/app_edersa.py",
            "La base de datos está lista para consultas y visualización",
            "Todos los índices han sido creados para optimizar el rendimiento"
        ]
    }


def main():
    """Función principal del script."""
    logger.info("=" * 70)
    logger.info("INICIANDO CREACIÓN DE BASE DE DATOS")
    logger.info("=" * 70)
    
    try:
        # Crear conexión a base de datos
        db_path = DB_DIR / "edersa_quality.db"
        logger.info(f"\nCreando base de datos: {db_path}")
        
        # Eliminar base de datos existente si existe
        if db_path.exists():
            db_path.unlink()
            logger.info("  Base de datos anterior eliminada")
        
        conn = sqlite3.connect(db_path)
        
        # 1. Crear estructura de tablas
        logger.info("\n1. CREANDO ESTRUCTURA DE TABLAS")
        create_tables(conn)
        
        # 2. Cargar datos de transformadores
        logger.info("\n2. CARGANDO DATOS DE TRANSFORMADORES")
        n_transformers = load_transformers_data(conn)
        
        # 3. Cargar datos de circuitos
        logger.info("\n3. CARGANDO DATOS DE CIRCUITOS")
        n_circuits = load_circuits_data(conn)
        
        # 4. Cargar agregaciones
        logger.info("\n4. CARGANDO AGREGACIONES")
        load_aggregations(conn)
        
        # 5. Cargar zonas críticas
        logger.info("\n5. CARGANDO ZONAS CRÍTICAS")
        load_critical_zones(conn)
        
        # 6. Cargar recomendaciones GD
        logger.info("\n6. CARGANDO RECOMENDACIONES GD")
        load_gd_recommendations(conn)
        
        # 7. Calcular métricas resumen
        logger.info("\n7. CALCULANDO MÉTRICAS RESUMEN")
        metrics = calculate_summary_metrics(conn)
        
        # 8. Crear índices
        logger.info("\n8. CREANDO ÍNDICES")
        create_indexes(conn)
        
        # 9. Optimizar base de datos
        logger.info("\n9. OPTIMIZANDO BASE DE DATOS")
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        logger.info("  Base de datos optimizada")
        
        # Cerrar conexión
        conn.close()
        
        # 10. Generar reporte
        logger.info("\n10. GENERANDO REPORTE DE BASE DE DATOS")
        report = generate_database_report(metrics)
        
        report_file = REPORTS_DIR / "05_database_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"  Reporte guardado: {report_file}")
        
        # 11. Resumen final
        logger.info("\n" + "=" * 70)
        logger.info("BASE DE DATOS CREADA EXITOSAMENTE")
        logger.info("=" * 70)
        logger.info(f"Ubicación: {db_path}")
        logger.info(f"Tamaño: {report['database_info']['size_mb']} MB")
        logger.info(f"Transformadores: {metrics['total_transformadores']:,}")
        logger.info(f"Circuitos: {metrics['total_circuitos']:,}")
        logger.info(f"Usuarios totales: {int(metrics['total_usuarios']):,}")
        logger.info(f"\nLogs guardados en: {log_file}")
        logger.info("\nPRÓXIMOS PASOS:")
        for step in report['next_steps']:
            logger.info(f"  - {step}")
        
    except Exception as e:
        logger.error(f"\nERROR FATAL: {str(e)}")
        logger.exception("Detalles del error:")
        sys.exit(1)


if __name__ == "__main__":
    main()