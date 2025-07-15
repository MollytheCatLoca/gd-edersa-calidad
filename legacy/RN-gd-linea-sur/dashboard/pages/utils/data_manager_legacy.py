"""
Centralized Data Manager for Dashboard
Handles all data loading, validation, and status tracking to ensure consistency
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from enum import Enum
import numpy as np
from datetime import datetime

# Import centralized constants
from .constants import (
    BESS_CONSTANTS, BESS_TECHNOLOGIES, BESS_TOPOLOGIES,
    BESSTechnology, BESSTopology, BESSStrategy
)

# Configure logging safely - only if not already configured
# FIXED: January 2025 - Prevent overwriting existing log config
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)

class DataStatus(Enum):
    """Enum for data status levels"""
    REAL = "real"           # Real data from files
    PARTIAL = "partial"     # Some real data, some missing
    FALLBACK = "fallback"   # Using fallback data
    ERROR = "error"         # Error loading data

class DataManager:
    """Centralized data management for the dashboard"""
    
    def __init__(self):
        self.project_root = self._resolve_project_root()
        self.data_path = self.project_root / "data" / "processed"
        self.fallback_path = self.project_root / "data" / "fallback"
        
        # Data storage
        self._system_data = None
        self._transformer_details = None
        self._historical_data = None
        
        # Status tracking
        self.data_status = {
            "system": DataStatus.ERROR,
            "transformers": DataStatus.ERROR,
            "historical": DataStatus.ERROR,
            "overall": DataStatus.ERROR
        }
        
        # Load tracking
        self.load_attempts = {
            "system": 0,
            "transformers": 0,
            "historical": 0
        }
        
        # Timestamps
        self.last_load = {
            "system": None,
            "transformers": None,
            "historical": None
        }
        
        # Initialize by loading all data
        self._load_all_data()
    
    def _load_all_data(self):
        """Load all data sources on initialization"""
        self._load_system_data()
        self._load_transformer_details()
        self._load_historical_data()
        self._update_overall_status()
    
    def _load_system_data(self) -> None:
        """Load main system data (nodes, edges, transformers)"""
        self.load_attempts["system"] += 1
        
        try:
            # Try to load real data
            file_path = self.data_path / "sistema_linea_sur.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                self._system_data = json.load(f)
            
            # Validate data structure
            if self._validate_system_data(self._system_data):
                self.data_status["system"] = DataStatus.REAL
                self.last_load["system"] = datetime.now()
                logger.info(f"Successfully loaded system data from {file_path}")
            else:
                raise ValueError("System data validation failed")
                
        except Exception as e:
            logger.warning(f"Failed to load system data: {e}")
            # Try fallback
            self._system_data = self._get_fallback_system_data()
            self.data_status["system"] = DataStatus.FALLBACK
            self.last_load["system"] = datetime.now()
    
    def _load_transformer_details(self) -> None:
        """Load transformer details data"""
        self.load_attempts["transformers"] += 1
        
        try:
            file_path = self.data_path / "transformadores_detalle.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                self._transformer_details = json.load(f)
            
            self.data_status["transformers"] = DataStatus.REAL
            self.last_load["transformers"] = datetime.now()
            logger.info(f"Successfully loaded transformer details from {file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load transformer details: {e}")
            # Use data from system file if available
            if self._system_data and "transformers" in self._system_data:
                self._transformer_details = {"transformadores": self._system_data["transformers"]}
                self.data_status["transformers"] = DataStatus.PARTIAL
            else:
                self._transformer_details = self._get_fallback_transformer_data()
                self.data_status["transformers"] = DataStatus.FALLBACK
            self.last_load["transformers"] = datetime.now()
    
    def _load_historical_data(self) -> None:
        """Load historical measurement data"""
        self.load_attempts["historical"] += 1
        
        # For now, we don't have historical data files
        # This is a placeholder for future implementation
        self._historical_data = {}
        self.data_status["historical"] = DataStatus.ERROR
        logger.info("Historical data loading not yet implemented")
    
    def _validate_system_data(self, data: Dict[str, Any]) -> bool:
        """Validate system data structure"""
        required_keys = ["nodes", "edges", "transformers"]
        return all(key in data for key in required_keys)
    
    def _update_overall_status(self) -> None:
        """Update overall data status based on individual statuses"""
        statuses = [self.data_status[key] for key in ["system", "transformers"]]
        
        if all(s == DataStatus.REAL for s in statuses):
            self.data_status["overall"] = DataStatus.REAL
        elif any(s == DataStatus.ERROR for s in statuses):
            self.data_status["overall"] = DataStatus.ERROR
        elif any(s == DataStatus.FALLBACK for s in statuses):
            self.data_status["overall"] = DataStatus.FALLBACK
        else:
            self.data_status["overall"] = DataStatus.PARTIAL
    
    def _get_fallback_system_data(self) -> Dict[str, Any]:
        """Return minimal fallback system data"""
        return {
            "metadata": {
                "name": "Sistema Eléctrico Línea Sur (FALLBACK)",
                "operator": "EdERSA",
                "base_values": {
                    "power_mva": 100,
                    "voltage_hv_kv": 132,
                    "voltage_mv_kv": 33,
                    "voltage_lv_kv": 13.2,
                    "frequency_hz": 50
                },
                "total_length_km": 270,
                "configuration": "radial",
                "last_updated": "FALLBACK DATA"
            },
            "nodes": {
                "pilcaniyeu": {
                    "name": "ET Pilcaniyeu",
                    "type": "substation",
                    "coordinates": {"lat": -41.12, "lon": -70.90},
                    "load_mw": 0,
                    "load_mvar": 0,
                    "distance_from_origin_km": 0
                },
                "jacobacci": {
                    "name": "ET Ingeniero Jacobacci",
                    "type": "substation",
                    "coordinates": {"lat": -41.329, "lon": -69.550},
                    "load_mw": 1.45,
                    "load_mvar": 0.60,
                    "distance_from_origin_km": 150,
                    "criticality": "high"
                },
                "los_menucos": {
                    "name": "ET Los Menucos",
                    "type": "substation",
                    "coordinates": {"lat": -40.843, "lon": -68.086},
                    "load_mw": 1.40,
                    "load_mvar": 0.20,
                    "distance_from_origin_km": 270,
                    "criticality": "high",
                    "has_generation": True
                }
            },
            "edges": {},
            "transformers": {},
            "system_summary": {
                "total_load": {
                    "active_power_mw": 3.80,
                    "reactive_power_mvar": 1.05,
                    "power_factor": 0.964
                }
            }
        }
    
    def _get_fallback_transformer_data(self) -> Dict[str, Any]:
        """Return minimal fallback transformer data"""
        return {
            "transformadores": {
                "pilcaniyeu_132_33": {
                    "location": "Pilcaniyeu",
                    "power_mva": 25,
                    "voltage": "132/33 kV",
                    "connection": "Yd"
                }
            }
        }
    
    # Public methods for data access
    def get_system_data(self) -> Tuple[Dict[str, Any], DataStatus]:
        """Get system data and its status"""
        return self._system_data, self.data_status["system"]
    
    def get_transformer_details(self) -> Tuple[Dict[str, Any], DataStatus]:
        """Get transformer details and status"""
        return self._transformer_details, self.data_status["transformers"]
    
    def get_nodes(self) -> Dict[str, Any]:
        """Get nodes data"""
        return self._system_data.get("nodes", {}) if self._system_data else {}
    
    def get_edges(self) -> Dict[str, Any]:
        """Get edges data"""
        return self._system_data.get("edges", {}) if self._system_data else {}
    
    def get_transformers(self) -> Dict[str, Any]:
        """Get transformers data"""
        return self._system_data.get("transformers", {}) if self._system_data else {}
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get system summary data"""
        return self._system_data.get("system_summary", {}) if self._system_data else {}
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get system metadata"""
        return self._system_data.get("metadata", {}) if self._system_data else {}
    
    def get_gd_costs(self) -> Dict[str, Any]:
        """Get distributed generation cost data with source metadata"""
        return {
            # System parameters
            "potencia_mw": 1.8,  # Actualizado a valor real
            "potencia_expansion_mw": 3.0,  # Expansión planificada
            "factor_capacidad": 0.8,
            "horas_dia_base": 4,
            "dias_ano": 365,
            
            # Validated costs (USD) - Basados en 1.8 MW
            "alquiler_mensual": 15_000,  # $8.33/kW-mes × 1800 kW
            "alquiler_anual": 180_000,   # $15,000 × 12
            "opex_por_mw_anual": 30_918,
            "opex_total_anual": 55_652,  # 1.8 MW × 30,918
            "opex_mensual": 4_638,        # 55,652 / 12
            "costo_oym_anual": 9_000,     # Proporcional a 1.8 MW
            "costo_oym_mensual": 750,     # 9,000 / 12
            
            # Fuel costs
            "consumo_gas": 0.282,  # m³/kWh
            "precio_gas": 0.11137,  # USD/m³
            "costo_combustible_anual": 46_652,  # Para 1.8 MW
            "costo_combustible_mensual": 3_888,  # 46,652 / 12
            
            # Totals - Actualizados para 1.8 MW
            "costo_total_mensual": 24_276,  # 15,000 + 4,638 + 3,888 + 750
            "costo_total_anual": 291_304,   # 24,276 × 12
            
            # Generation - Para 1.8 MW
            "generacion_anual_mwh": 2_102,  # 1.8 × 1000 × 0.8 × 4 × 365 / 1000
            "generacion_mensual_mwh": 175,   # 2,102 / 12
            
            # Unit costs - Recalculados
            "costo_por_mwh": 138.6,  # 291,304 / 2,102
            "costo_por_kw_mes": 13.49,  # 24,276 / 1,800
            
            # Reference data
            "alquiler_referencia": {
                "costo_mensual": 15_000,
                "potencia_kw": 1_800,
                "costo_unitario": 8.33  # USD/kW-mes
            },
            
            # Alternative fuel for comparison
            "combustible_gasoil": {
                "consumo": 0.249,  # L/kWh
                "precio": 1.0      # USD/L
            },
            
            # EdERSA purchase price
            "precio_compra_edersa": 60,  # USD/MWh
            
            # Data source metadata
            "data_sources": {
                "potencia_mw": {"tipo": "DATO", "fuente": "Facturas EDERSA 2024"},
                "alquiler": {"tipo": "DATO", "fuente": "Facturas alquiler equipos"},
                "consumo_gas": {"tipo": "DATO", "fuente": "Especificaciones técnicas"},
                "precio_gas": {"tipo": "DATO", "fuente": "Tarifas gas 2024"},
                "opex": {"tipo": "REFERENCIA", "fuente": "Valores típicos industria"},
                "generacion": {"tipo": "CALCULADO", "fuente": "MW × FC × horas × días"}
            }
        }
    
    def get_theoretical_voltages(self) -> Dict[str, Any]:
        """Get theoretical voltage values calculated with typical drop"""
        return {
            "voltages": {
                "PILCANIYEU": {"value": 1.000, "type": "REFERENCIA", "distance_km": 0, "note": "Punto de referencia 132/33 kV"},
                "COMALLO": {"value": 0.895, "type": "TEORICO", "distance_km": 70, "note": "Caída teórica 0.15%/km"},
                "ONELLI": {"value": 0.820, "type": "TEORICO", "distance_km": 120, "note": "Caída teórica 0.15%/km"},
                "JACOBACCI": {"value": 0.775, "type": "TEORICO", "distance_km": 150, "note": "Caída teórica 0.15%/km"},
                "MAQUINCHAO": {"value": 0.685, "type": "TEORICO", "distance_km": 210, "note": "Caída teórica 0.15%/km"},
                "AGUADA DE GUERRA": {"value": 0.640, "type": "TEORICO", "distance_km": 240, "note": "Caída teórica 0.15%/km"},
                "LOS MENUCOS": {"value": 0.595, "type": "TEORICO", "distance_km": 270, "note": "Caída teórica 0.15%/km"}
            },
            "drop_rate_per_km": 0.0015,  # 0.15%/km
            "calculation_method": "Linear approximation",
            "note": "Valores teóricos para comparación con mediciones reales"
        }
    
    def get_theoretical_losses(self) -> Dict[str, Any]:
        """Get theoretical power losses by line segment"""
        return {
            "segments": [
                {
                    "name": "Pilcaniyeu-Comallo",
                    "from": "PILCANIYEU",
                    "to": "COMALLO",
                    "length_km": 70,
                    "loss_mw": 0.08,
                    "loss_percentage": 20,
                    "type": "TEORICO",
                    "note": "Calculado con I²R teórico"
                },
                {
                    "name": "Comallo-Jacobacci",
                    "from": "COMALLO", 
                    "to": "JACOBACCI",
                    "length_km": 80,
                    "loss_mw": 0.12,
                    "loss_percentage": 30,
                    "type": "TEORICO",
                    "note": "Mayor pérdida por mayor carga"
                },
                {
                    "name": "Jacobacci-Maquinchao",
                    "from": "JACOBACCI",
                    "to": "MAQUINCHAO", 
                    "length_km": 60,
                    "loss_mw": 0.10,
                    "loss_percentage": 25,
                    "type": "TEORICO",
                    "note": "Calculado con I²R teórico"
                },
                {
                    "name": "Maquinchao-Los Menucos",
                    "from": "MAQUINCHAO",
                    "to": "LOS MENUCOS",
                    "length_km": 60,
                    "loss_mw": 0.10,
                    "loss_percentage": 25,
                    "type": "TEORICO",
                    "note": "Incluye tramo a Aguada de Guerra"
                }
            ],
            "total": {
                "loss_mw": 0.40,
                "loss_percentage": 10.0,
                "type": "TEORICO",
                "note": "Pérdidas totales estimadas típicas para líneas rurales"
            },
            "calculation_basis": "I²R con flujos estimados",
            "for_comparison": "Comparar con pérdidas reales cuando estén disponibles"
        }
    
    def get_impedances(self) -> Dict[str, Any]:
        """Get line impedances (accumulated and by segment)"""
        return {
            "accumulated": {
                "COMALLO": {"R_ohm": 17.15, "X_ohm": 28.70, "Z_ohm": 33.43, "type": "REFERENCIA"},
                "JACOBACCI": {"R_ohm": 36.75, "X_ohm": 61.50, "Z_ohm": 71.64, "type": "REFERENCIA"},
                "MAQUINCHAO": {"R_ohm": 52.05, "X_ohm": 87.10, "Z_ohm": 101.47, "type": "REFERENCIA"},
                "LOS MENUCOS": {"R_ohm": 87.15, "X_ohm": 112.50, "Z_ohm": 142.35, "type": "REFERENCIA"}
            },
            "conductor_data": {
                "type": "ACSR",
                "note": "Valores típicos de catálogo para conductor ACSR en 33 kV"
            }
        }
    
    def get_real_measurements(self) -> Dict[str, Any]:
        """Get real measurements when available (from Phase 3 analysis)"""
        # This will be populated with real data from Phase 3
        return {
            "voltages": {
                # To be filled with real EPRE data
                "available": False,
                "note": "Datos reales disponibles en análisis Fase 3"
            },
            "losses": {
                "available": False,
                "note": "Pérdidas reales a calcular con mediciones"
            }
        }
    
    def get_processed_data_summary(self) -> Dict[str, Any]:
        """Get summary of processed measurement data"""
        try:
            # Load quality metrics
            quality_file = self.data_path / "quality_metrics.json"
            if quality_file.exists():
                with open(quality_file, 'r', encoding='utf-8') as f:
                    quality_data = json.load(f)
            else:
                quality_data = {}
            
            # Load temporal analysis
            temporal_file = self.data_path / "temporal_analysis.json"
            if temporal_file.exists():
                with open(temporal_file, 'r', encoding='utf-8') as f:
                    temporal_data = json.load(f)
            else:
                temporal_data = {}
            
            # Calculate summary statistics
            total_records = sum(s.get('total_clean_records', 0) for s in quality_data.values())
            stations_processed = list(quality_data.keys())
            
            # Extract date ranges
            date_ranges = {}
            for station, data in quality_data.items():
                if 'date_range' in data:
                    date_ranges[station] = data['date_range']
            
            return {
                "available": bool(quality_data),
                "total_records": total_records,
                "stations_processed": stations_processed,
                "date_ranges": date_ranges,
                "temporal_data": temporal_data.get('overall', {}),
                "quality_metrics": quality_data,
                "data_status": "REAL" if quality_data else "NO_DATA"
            }
        except Exception as e:
            logger.error(f"Error loading processed data summary: {e}")
            return {
                "available": False,
                "error": str(e),
                "data_status": "ERROR"
            }
    
    def get_station_measurements(self, station_name: str) -> Dict[str, Any]:
        """Get measurement data for a specific station"""
        try:
            # Load quality metrics
            quality_file = self.data_path / "quality_metrics.json"
            quality_data = {}
            if quality_file.exists():
                with open(quality_file, 'r', encoding='utf-8') as f:
                    all_quality = json.load(f)
                    quality_data = all_quality.get(station_name, {})
            
            # Load temporal analysis
            temporal_file = self.data_path / "temporal_analysis.json"
            temporal_data = {}
            if temporal_file.exists():
                with open(temporal_file, 'r', encoding='utf-8') as f:
                    all_temporal = json.load(f)
                    temporal_data = all_temporal.get('by_station', {}).get(station_name, {})
            
            return {
                "available": bool(quality_data),
                "station": station_name,
                "quality_metrics": quality_data,
                "temporal_patterns": temporal_data,
                "data_status": "REAL" if quality_data else "NO_DATA"
            }
        except Exception as e:
            logger.error(f"Error loading station measurements for {station_name}: {e}")
            return {
                "available": False,
                "station": station_name,
                "error": str(e),
                "data_status": "ERROR"
            }
    
    def get_correlation_matrices(self) -> Dict[str, Any]:
        """Get correlation matrices between stations"""
        try:
            clustering_path = self.data_path / "clustering"
            correlations = {}
            
            # Load different correlation files
            correlation_files = {
                "power_pearson": "correlation_power_pearson.csv",
                "power_spearman": "correlation_power_spearman.csv",
                "voltage_pearson": "correlation_voltage_pearson.csv",
                "voltage_spearman": "correlation_voltage_spearman.csv",
                "reactive_pearson": "correlation_reactive_pearson.csv",
                "cross_power_voltage": "correlation_cross_power_voltage.csv"
            }
            
            for key, filename in correlation_files.items():
                file_path = clustering_path / filename
                if file_path.exists():
                    import pandas as pd
                    df = pd.read_csv(file_path, index_col=0)
                    correlations[key] = {
                        "matrix": df.to_dict(),
                        "stations": df.index.tolist()
                    }
            
            # Load lag correlation summary
            lag_file = clustering_path / "lag_correlation_summary.json"
            if lag_file.exists():
                with open(lag_file, 'r', encoding='utf-8') as f:
                    correlations['lag_analysis'] = json.load(f)
            
            return {
                "available": bool(correlations),
                "correlations": correlations,
                "data_status": "REAL" if correlations else "NO_DATA"
            }
        except Exception as e:
            logger.error(f"Error loading correlation matrices: {e}")
            return {
                "available": False,
                "error": str(e),
                "data_status": "ERROR"
            }
    
    def get_temporal_patterns(self) -> Dict[str, Any]:
        """Get temporal patterns analysis"""
        try:
            temporal_file = self.data_path / "temporal_analysis.json"
            if temporal_file.exists():
                with open(temporal_file, 'r', encoding='utf-8') as f:
                    temporal_data = json.load(f)
                
                return {
                    "available": True,
                    "overall": temporal_data.get('overall', {}),
                    "by_station": temporal_data.get('by_station', {}),
                    "data_status": "REAL"
                }
            else:
                return {
                    "available": False,
                    "data_status": "NO_DATA"
                }
        except Exception as e:
            logger.error(f"Error loading temporal patterns: {e}")
            return {
                "available": False,
                "error": str(e),
                "data_status": "ERROR"
            }
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality metrics for all stations"""
        try:
            quality_file = self.data_path / "quality_metrics.json"
            if quality_file.exists():
                with open(quality_file, 'r', encoding='utf-8') as f:
                    quality_data = json.load(f)
                
                # Calculate aggregate metrics
                total_raw = sum(s.get('total_raw_records', 0) for s in quality_data.values())
                total_clean = sum(s.get('total_clean_records', 0) for s in quality_data.values())
                total_removed = sum(s.get('records_removed', 0) for s in quality_data.values())
                
                # Voltage quality summary
                stations_below_limit = sum(1 for s in quality_data.values() 
                                         if s.get('voltage_quality', {}).get('within_limits_pct', 0) == 0)
                
                return {
                    "available": True,
                    "by_station": quality_data,
                    "aggregate": {
                        "total_raw_records": total_raw,
                        "total_clean_records": total_clean,
                        "total_removed": total_removed,
                        "removal_rate": (total_removed / total_raw * 100) if total_raw > 0 else 0,
                        "stations_below_voltage_limit": stations_below_limit,
                        "total_stations": len(quality_data)
                    },
                    "data_status": "REAL"
                }
            else:
                return {
                    "available": False,
                    "data_status": "NO_DATA"
                }
        except Exception as e:
            logger.error(f"Error loading data quality metrics: {e}")
            return {
                "available": False,
                "error": str(e),
                "data_status": "ERROR"
            }
    
    def get_clustering_results(self) -> Dict[str, Any]:
        """Get clustering analysis results"""
        try:
            clustering_path = self.data_path / "clustering"
            results = {}
            
            # Load criticality metrics
            criticality_file = clustering_path / "criticality_metrics.json"
            if criticality_file.exists():
                with open(criticality_file, 'r', encoding='utf-8') as f:
                    results['criticality'] = json.load(f)
            
            # Load DG priority report
            dg_priority_file = clustering_path / "dg_priority_report.json"
            if dg_priority_file.exists():
                with open(dg_priority_file, 'r', encoding='utf-8') as f:
                    results['dg_priority'] = json.load(f)
            
            # Load clustering summary
            clustering_file = clustering_path / "clustering_summary.json"
            if clustering_file.exists():
                with open(clustering_file, 'r', encoding='utf-8') as f:
                    results['clustering'] = json.load(f)
            
            return {
                "available": bool(results),
                "results": results,
                "data_status": "REAL" if results else "NO_DATA"
            }
        except Exception as e:
            logger.error(f"Error loading clustering results: {e}")
            return {
                "available": False,
                "error": str(e),
                "data_status": "ERROR"
            }
    
    # ============================================================================
    # FASE 3: Métodos de análisis profundo agregados en Enero 2025
    # Estos métodos son críticos para fases 4-8
    # NO MODIFICAR sin actualizar documentación en CLAUDE.md
    # Ver docs/dev/fase3_quick_reference.md para uso
    # ============================================================================
    
    def get_hourly_voltage_analysis(self) -> Dict[str, Any]:
        """Get detailed hourly voltage analysis for each station
        
        FASE 3 - Análisis estadístico por hora para identificar patrones
        críticos y horarios de mayor stress del sistema.
        
        Returns:
            Dict con estadísticas horarias por estación incluyendo
            percentiles, violaciones y valores extremos
        """
        try:
            # Check if consolidated data exists
            csv_file = self.data_path / "consolidated_data.csv"
            parquet_file = self.data_path / "consolidated_data.parquet"
            
            if csv_file.exists():
                # Load only necessary columns to save memory
                import pandas as pd
                chunks = []
                for chunk in pd.read_csv(csv_file, chunksize=10000, 
                                        usecols=['station', 'hour', 'v_pu', 'p_total', 'timestamp']):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            elif parquet_file.exists():
                import pandas as pd
                df = pd.read_parquet(parquet_file, 
                                   columns=['station', 'hour', 'v_pu', 'p_total', 'timestamp'])
            else:
                return {"available": False, "data_status": "NO_DATA"}
            
            # Analyze by station and hour
            hourly_stats = {}
            stations = df['station'].unique()
            
            for station in stations:
                station_df = df[df['station'] == station]
                hourly_stats[station] = {}
                
                for hour in range(24):
                    hour_data = station_df[station_df['hour'] == hour]['v_pu']
                    if len(hour_data) > 0:
                        hourly_stats[station][hour] = {
                            'mean': float(hour_data.mean()),
                            'min': float(hour_data.min()),
                            'max': float(hour_data.max()),
                            'p5': float(hour_data.quantile(0.05)),
                            'p25': float(hour_data.quantile(0.25)),
                            'p50': float(hour_data.quantile(0.50)),
                            'p75': float(hour_data.quantile(0.75)),
                            'p95': float(hour_data.quantile(0.95)),
                            'violations': int((hour_data < 0.95).sum()),
                            'severe_violations': int((hour_data < 0.5).sum()),
                            'critical_violations': int((hour_data < 0.3).sum()),
                            'samples': len(hour_data)
                        }
            
            return {
                "available": True,
                "hourly_stats": hourly_stats,
                "total_records": len(df),
                "data_status": "REAL"
            }
        except Exception as e:
            logger.error(f"Error in hourly voltage analysis: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def get_demand_voltage_correlation(self) -> Dict[str, Any]:
        """Get correlation between demand and voltage for each station
        
        FASE 3 - Calcula sensibilidad dV/dP crítica para dimensionamiento
        de GD. Valores más negativos = mayor impacto de GD.
        
        Returns:
            Dict con correlaciones y sensibilidad dV/dP en pu/MW
        """
        try:
            # Load data
            csv_file = self.data_path / "consolidated_data.csv"
            if csv_file.exists():
                import pandas as pd
                # Load in chunks for memory efficiency
                correlations = {}
                
                # Read only required columns
                df = pd.read_csv(csv_file, usecols=['station', 'v_pu', 'p_total', 'hour'])
                
                for station in df['station'].unique():
                    station_df = df[df['station'] == station]
                    
                    # Overall correlation
                    corr = station_df['p_total'].corr(station_df['v_pu'])
                    
                    # Correlation by time period
                    morning = station_df[(station_df['hour'] >= 6) & (station_df['hour'] < 12)]
                    afternoon = station_df[(station_df['hour'] >= 12) & (station_df['hour'] < 18)]
                    evening = station_df[(station_df['hour'] >= 18) & (station_df['hour'] < 22)]
                    night = station_df[(station_df['hour'] >= 22) | (station_df['hour'] < 6)]
                    
                    correlations[station] = {
                        'overall': float(corr),
                        'morning': float(morning['p_total'].corr(morning['v_pu'])),
                        'afternoon': float(afternoon['p_total'].corr(afternoon['v_pu'])),
                        'evening': float(evening['p_total'].corr(evening['v_pu'])),
                        'night': float(night['p_total'].corr(night['v_pu'])),
                        'sensitivity_dv_dp': self._calculate_sensitivity(station_df),
                        'demand_at_low_v': {
                            'v_below_0.5': float(station_df[station_df['v_pu'] < 0.5]['p_total'].mean()),
                            'v_below_0.6': float(station_df[station_df['v_pu'] < 0.6]['p_total'].mean()),
                            'v_above_0.6': float(station_df[station_df['v_pu'] >= 0.6]['p_total'].mean())
                        }
                    }
                
                return {
                    "available": True,
                    "correlations": correlations,
                    "data_status": "REAL"
                }
            else:
                return {"available": False, "data_status": "NO_DATA"}
                
        except Exception as e:
            logger.error(f"Error in demand-voltage correlation: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def _calculate_sensitivity(self, df):
        """Calculate dV/dP sensitivity using linear regression"""
        try:
            from sklearn.linear_model import LinearRegression
            X = df['p_total'].values.reshape(-1, 1)
            y = df['v_pu'].values
            
            # Remove outliers
            mask = (df['v_pu'] > 0.1) & (df['p_total'] > 0)
            X_clean = X[mask]
            y_clean = y[mask]
            
            if len(X_clean) > 10:
                model = LinearRegression()
                model.fit(X_clean, y_clean)
                return float(model.coef_[0])  # dV/dP in pu/MW
            else:
                return 0.0
        except:
            return 0.0
    
    def get_critical_events_analysis(self) -> Dict[str, Any]:
        """Analyze critical voltage events (duration, timing, severity)
        
        FASE 3 - Identifica 547 eventos críticos que son restricción
        dura para optimización. Objetivo: eliminar 100%.
        
        Returns:
            Dict con eventos V < 0.5pu por más de 15 minutos
        """
        try:
            csv_file = self.data_path / "consolidated_data.csv"
            if not csv_file.exists():
                return {"available": False, "data_status": "NO_DATA"}
            
            import pandas as pd
            # Read with timestamp parsing
            df = pd.read_csv(csv_file, 
                           usecols=['station', 'timestamp', 'v_pu', 'p_total'],
                           parse_dates=['timestamp'])
            
            critical_events = {}
            
            for station in df['station'].unique():
                station_df = df[df['station'] == station].sort_values('timestamp')
                
                # Find continuous events below threshold
                events_05 = self._find_continuous_events(station_df, 0.5)
                events_03 = self._find_continuous_events(station_df, 0.3)
                
                # Analyze worst events
                worst_events = station_df.nsmallest(100, 'v_pu')
                
                critical_events[station] = {
                    'events_below_0.5pu': {
                        'count': len(events_05),
                        'total_duration_hours': sum(e['duration_minutes'] for e in events_05) / 60,
                        'max_duration_hours': max([e['duration_minutes'] for e in events_05], default=0) / 60,
                        'events': events_05[:10]  # Top 10 longest
                    },
                    'events_below_0.3pu': {
                        'count': len(events_03),
                        'total_duration_hours': sum(e['duration_minutes'] for e in events_03) / 60,
                        'events': events_03[:10]
                    },
                    'worst_100_events': {
                        'min_voltage': float(worst_events['v_pu'].min()),
                        'avg_voltage': float(worst_events['v_pu'].mean()),
                        'avg_demand': float(worst_events['p_total'].mean()),
                        'hour_distribution': worst_events['timestamp'].dt.hour.value_counts().to_dict()
                    }
                }
            
            return {
                "available": True,
                "critical_events": critical_events,
                "data_status": "REAL"
            }
            
        except Exception as e:
            logger.error(f"Error in critical events analysis: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def _find_continuous_events(self, df, threshold):
        """Find continuous events below voltage threshold"""
        events = []
        below_threshold = df['v_pu'] < threshold
        
        # Find starts and ends of events
        starts = (~below_threshold).shift(1) & below_threshold
        ends = below_threshold.shift(1) & (~below_threshold)
        
        start_times = df[starts]['timestamp'].tolist()
        end_times = df[ends]['timestamp'].tolist()
        
        # Match starts with ends
        for i, start in enumerate(start_times):
            if i < len(end_times) and end_times[i] > start:
                duration = (end_times[i] - start).total_seconds() / 60  # minutes
                if duration > 15:  # Only events longer than 15 minutes
                    event_df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end_times[i])]
                    events.append({
                        'start': start.isoformat(),
                        'end': end_times[i].isoformat(),
                        'duration_minutes': duration,
                        'min_voltage': float(event_df['v_pu'].min()),
                        'avg_voltage': float(event_df['v_pu'].mean()),
                        'avg_demand': float(event_df['p_total'].mean()),
                        'start_hour': start.hour
                    })
        
        # Sort by duration
        return sorted(events, key=lambda x: x['duration_minutes'], reverse=True)
    
    def get_demand_ramps_analysis(self) -> Dict[str, Any]:
        """Analyze demand ramps (MW/hour) by station and time
        
        FASE 3 - Rampas máximas ±0.85 MW/h determinan requisitos
        de respuesta dinámica para BESS (< 5 minutos).
        
        Returns:
            Dict con análisis de rampas por hora y período crítico
        """
        try:
            csv_file = self.data_path / "consolidated_data.csv"
            if not csv_file.exists():
                return {"available": False, "data_status": "NO_DATA"}
            
            import pandas as pd
            df = pd.read_csv(csv_file,
                           usecols=['station', 'timestamp', 'p_total', 'hour'],
                           parse_dates=['timestamp'])
            
            ramp_analysis = {}
            
            for station in df['station'].unique():
                station_df = df[df['station'] == station].sort_values('timestamp')
                
                # Calculate ramps (MW per 15 min interval)
                station_df['ramp_mw_15min'] = station_df['p_total'].diff()
                # Convert to MW/hour
                station_df['ramp_mw_hour'] = station_df['ramp_mw_15min'] * 4
                
                # Analyze by hour
                hourly_ramps = {}
                for hour in range(24):
                    hour_data = station_df[station_df['hour'] == hour]['ramp_mw_hour'].dropna()
                    if len(hour_data) > 0:
                        hourly_ramps[hour] = {
                            'max_up': float(hour_data.max()),
                            'max_down': float(hour_data.min()),
                            'avg_up': float(hour_data[hour_data > 0].mean()) if len(hour_data[hour_data > 0]) > 0 else 0,
                            'avg_down': float(hour_data[hour_data < 0].mean()) if len(hour_data[hour_data < 0]) > 0 else 0,
                            'p95_up': float(hour_data[hour_data > 0].quantile(0.95)) if len(hour_data[hour_data > 0]) > 0 else 0,
                            'p95_down': float(hour_data[hour_data < 0].quantile(0.05)) if len(hour_data[hour_data < 0]) > 0 else 0
                        }
                
                # Critical ramp periods
                morning_ramp = station_df[(station_df['hour'] >= 6) & (station_df['hour'] <= 9)]
                evening_ramp = station_df[(station_df['hour'] >= 18) & (station_df['hour'] <= 21)]
                
                ramp_analysis[station] = {
                    'hourly_ramps': hourly_ramps,
                    'critical_periods': {
                        'morning_6_9h': {
                            'max_ramp_up': float(morning_ramp['ramp_mw_hour'].max()),
                            'avg_ramp': float(morning_ramp['ramp_mw_hour'].mean())
                        },
                        'evening_18_21h': {
                            'max_ramp_up': float(evening_ramp['ramp_mw_hour'].max()),
                            'avg_ramp': float(evening_ramp['ramp_mw_hour'].mean())
                        }
                    }
                }
            
            return {
                "available": True,
                "ramp_analysis": ramp_analysis,
                "data_status": "REAL"
            }
            
        except Exception as e:
            logger.error(f"Error in demand ramps analysis: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def get_load_duration_curves(self) -> Dict[str, Any]:
        """Get load duration curves data for each station
        
        FASE 3 - Curvas de duración para dimensionamiento:
        P90: 1.5 MW (base), P50: 2.8 MW (media), P10: 4.5 MW (pico)
        
        Returns:
            Dict con curvas de duración y estadísticas de excedencia
        """
        try:
            csv_file = self.data_path / "consolidated_data.csv"
            if not csv_file.exists():
                return {"available": False, "data_status": "NO_DATA"}
            
            import pandas as pd
            import numpy as np
            
            df = pd.read_csv(csv_file, usecols=['station', 'p_total', 'v_pu'])
            
            duration_curves = {}
            
            for station in df['station'].unique():
                station_df = df[df['station'] == station]
                
                # Sort values for duration curves
                p_sorted = np.sort(station_df['p_total'].values)[::-1]  # Descending
                v_sorted = np.sort(station_df['v_pu'].values)  # Ascending
                
                # Calculate percentages
                n = len(p_sorted)
                percentages = np.linspace(0, 100, n)
                
                # Sample points for visualization (every 1%)
                indices = [int(i * n / 100) for i in range(101)]
                
                duration_curves[station] = {
                    'demand_curve': {
                        'percentages': [percentages[i] for i in indices if i < n],
                        'values': [float(p_sorted[i]) for i in indices if i < n]
                    },
                    'voltage_curve': {
                        'percentages': [percentages[i] for i in indices if i < n],
                        'values': [float(v_sorted[i]) for i in indices if i < n]
                    },
                    'statistics': {
                        'hours_above_80pct_peak': float((station_df['p_total'] > 0.8 * station_df['p_total'].max()).sum() * 0.25),
                        'hours_below_0.5pu': float((station_df['v_pu'] < 0.5).sum() * 0.25),
                        'hours_below_0.6pu': float((station_df['v_pu'] < 0.6).sum() * 0.25),
                        'energy_below_limit_mwh': float((station_df[station_df['v_pu'] < 0.95]['p_total'].sum() * 0.25))
                    }
                }
            
            return {
                "available": True,
                "duration_curves": duration_curves,
                "data_status": "REAL"
            }
            
        except Exception as e:
            logger.error(f"Error in load duration curves: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def get_typical_days_profiles(self) -> Dict[str, Any]:
        """Get profiles for typical days (max, min, average, critical)
        
        FASE 3 - Perfiles de días típicos para TODAS las estaciones.
        Crítico para escenarios de simulación en Fase 6.
        
        Returns:
            Dict con perfiles horarios para días extremos y promedio
        """
        try:
            csv_file = self.data_path / "consolidated_data.csv"
            if not csv_file.exists():
                return {"available": False, "data_status": "NO_DATA"}
            
            import pandas as pd
            df = pd.read_csv(csv_file,
                           usecols=['station', 'timestamp', 'p_total', 'v_pu', 'hour'],
                           parse_dates=['timestamp'])
            
            # Add date column
            df['date'] = df['timestamp'].dt.date
            
            typical_days = {}
            
            for station in df['station'].unique():
                station_df = df[df['station'] == station]
                
                # Find special days
                daily_stats = station_df.groupby('date').agg({
                    'p_total': ['mean', 'max'],
                    'v_pu': 'mean'
                })
                
                # Flatten column names
                daily_stats.columns = ['_'.join(col).strip() for col in daily_stats.columns]
                
                # Find specific days
                max_demand_date = daily_stats['p_total_max'].idxmax()
                min_demand_date = daily_stats['p_total_max'].idxmin()
                worst_voltage_date = daily_stats['v_pu_mean'].idxmin()
                
                # Get hourly profiles for these days
                typical_days[station] = {
                    'max_demand_day': self._get_day_profile(station_df, max_demand_date),
                    'min_demand_day': self._get_day_profile(station_df, min_demand_date),
                    'worst_voltage_day': self._get_day_profile(station_df, worst_voltage_date),
                    'average_day': self._get_average_day_profile(station_df)
                }
            
            return {
                "available": True,
                "typical_days": typical_days,
                "data_status": "REAL"
            }
            
        except Exception as e:
            logger.error(f"Error in typical days analysis: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def _get_day_profile(self, df, date):
        """Get hourly profile for a specific day"""
        day_df = df[df['date'] == date]
        profile = day_df.groupby('hour').agg({
            'p_total': 'mean',
            'v_pu': 'mean'
        }).to_dict()
        
        return {
            'date': str(date),
            'hourly_demand': {int(h): float(v) for h, v in profile['p_total'].items()},
            'hourly_voltage': {int(h): float(v) for h, v in profile['v_pu'].items()}
        }
    
    def _get_average_day_profile(self, df):
        """Get average hourly profile across all days"""
        profile = df.groupby('hour').agg({
            'p_total': ['mean', 'std'],
            'v_pu': ['mean', 'std']
        })
        
        return {
            'hourly_demand_mean': {int(h): float(v) for h, v in profile['p_total']['mean'].items()},
            'hourly_demand_std': {int(h): float(v) for h, v in profile['p_total']['std'].items()},
            'hourly_voltage_mean': {int(h): float(v) for h, v in profile['v_pu']['mean'].items()},
            'hourly_voltage_std': {int(h): float(v) for h, v in profile['v_pu']['std'].items()}
        }
    
    # =============================================
    # FASE 4: ANÁLISIS SOLAR - Enero 2025
    # =============================================
    
    def get_solar_generation_profile(self, station: str, capacity_mw: float = 1.0, 
                                   technology: str = 'SAT Bifacial') -> Dict[str, Any]:
        """
        Get hourly solar generation profile for a station.
        
        Args:
            station: Station name (Pilcaniyeu, Jacobacci, Maquinchao, Los Menucos)
            capacity_mw: Installed capacity in MW (default 1.0 MW)
            technology: Solar technology type (Fixed Monofacial, Fixed Bifacial, 
                       SAT Monofacial, SAT Bifacial)
        
        Returns:
            Dictionary with hourly and monthly generation profiles
        """
        try:
            # Pre-calculated monthly generation for 1 MW SAT Bifacial (base case)
            # Based on 1,872 MWh/MW/year with flattened seasonal curve
            monthly_generation_base = {
                1: 257.5,   # January
                2: 197.7,   # February 
                3: 174.5,   # March
                4: 116.2,   # April
                5: 67.8,    # May
                6: 45.7,    # June
                7: 58.0,    # July
                8: 93.9,    # August
                9: 140.3,   # September
                10: 216.1,  # October
                11: 237.8,  # November
                12: 266.4   # December
            }
            
            # Technology scaling factors relative to SAT Bifacial
            tech_factors = {
                'Fixed Monofacial': 0.727,    # 1360/1872
                'Fixed Bifacial': 0.790,      # 1479/1872
                'SAT Monofacial': 0.868,      # 1624/1872
                'SAT Bifacial': 1.000         # Base case
            }
            
            # Station-specific adjustments (based on solar resource)
            station_factors = {
                'Pilcaniyeu': 0.95,    # Slightly lower (more clouds)
                'Jacobacci': 1.00,     # Reference
                'Maquinchao': 1.02,    # Slightly higher (clearer skies)
                'Los Menucos': 1.01    # Slightly higher
            }
            
            # Get factors
            tech_factor = tech_factors.get(technology, 1.0)
            station_factor = station_factors.get(station, 1.0)
            
            # Calculate monthly generation for this configuration
            monthly_generation = {}
            annual_total = 0
            
            for month, base_gen in monthly_generation_base.items():
                gen_mwh = base_gen * tech_factor * station_factor * capacity_mw
                monthly_generation[month] = gen_mwh
                annual_total += gen_mwh
            
            # Create hourly profiles (typical day per month)
            hourly_profiles = {}
            
            for month in range(1, 13):
                # Days in month
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]
                daily_energy = monthly_generation[month] / days_in_month
                
                # Create bell curve for solar generation
                hourly_profile = []
                for hour in range(24):
                    if 6 <= hour <= 20:  # Daylight hours
                        # Bell curve centered at solar noon (13:00)
                        x = (hour - 13) / 4
                        normalized = np.exp(-0.5 * x**2)
                        
                        # Adjust for seasonal day length
                        if month in [12, 1, 2]:  # Summer - longer days
                            if hour < 8 or hour > 18:
                                normalized *= 0.5
                        elif month in [6, 7, 8]:  # Winter - shorter days
                            if hour < 9 or hour > 17:
                                normalized *= 0.3
                        
                        # Convert to MW
                        power_mw = normalized * daily_energy * 2.5  # Scaling factor
                    else:
                        power_mw = 0.0
                    
                    hourly_profile.append(power_mw)
                
                # Normalize to match daily total
                total_generated = sum(hourly_profile)
                if total_generated > 0:
                    factor = daily_energy / total_generated
                    hourly_profile = [p * factor for p in hourly_profile]
                
                hourly_profiles[month] = hourly_profile
            
            # Calculate capacity factor
            capacity_factor = annual_total / (capacity_mw * 8760)
            
            return {
                "available": True,
                "station": station,
                "technology": technology,
                "capacity_mw": capacity_mw,
                "annual_generation_mwh": round(annual_total, 1),
                "capacity_factor": round(capacity_factor, 3),
                "monthly_generation_mwh": {k: round(v, 1) for k, v in monthly_generation.items()},
                "hourly_profiles": hourly_profiles,
                "peak_power_mw": round(capacity_mw * 0.95, 2),  # Typical peak
                "data_status": "MODEL"
            }
            
        except Exception as e:
            logger.error(f"Error calculating solar generation: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def get_solar_impact_analysis(self, solar_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the impact of solar generation on system performance.
        
        Args:
            solar_config: Dictionary with solar plant configurations
                         {station: {'capacity_mw': float, 'technology': str}}
        
        Returns:
            Dictionary with voltage improvement and loss reduction analysis
        """
        try:
            # Get current system state
            voltage_data = self.get_hourly_voltage_analysis()
            if not voltage_data.get('available'):
                return {"available": False, "error": "No voltage data available"}
            
            # Sensitivities (dV/dP) from Phase 3 analysis
            sensitivities = {
                'Pilcaniyeu': 0.047,    # pu/MW
                'Jacobacci': 0.089,     # pu/MW
                'Maquinchao': 0.112,    # pu/MW
                'Los Menucos': 0.095    # pu/MW
            }
            
            results = {}
            total_solar_mw = 0
            
            for station, config in solar_config.items():
                if station not in sensitivities:
                    continue
                
                capacity_mw = config.get('capacity_mw', 0)
                technology = config.get('technology', 'SAT Bifacial')
                
                if capacity_mw <= 0:
                    continue
                
                total_solar_mw += capacity_mw
                
                # Get solar generation profile
                solar_profile = self.get_solar_generation_profile(
                    station, capacity_mw, technology
                )
                
                # Calculate voltage improvement
                sensitivity = sensitivities[station]
                
                # Estimate average injection during peak hours
                monthly_gen = solar_profile.get('monthly_generation_mwh', {})
                avg_monthly = sum(monthly_gen.values()) / 12
                avg_daily = avg_monthly / 30
                avg_peak_injection = avg_daily / 10  # Assume 10 peak hours
                
                voltage_improvement = sensitivity * avg_peak_injection
                
                results[station] = {
                    'capacity_mw': capacity_mw,
                    'technology': technology,
                    'annual_generation_mwh': solar_profile.get('annual_generation_mwh', 0),
                    'avg_voltage_improvement_pu': round(voltage_improvement, 3),
                    'peak_voltage_improvement_pu': round(sensitivity * capacity_mw * 0.8, 3),
                    'critical_hours_reduced': int(voltage_improvement * 1000)  # Rough estimate
                }
            
            # System-wide impact
            system_impact = {
                'total_solar_capacity_mw': round(total_solar_mw, 1),
                'total_annual_generation_mwh': sum(
                    r['annual_generation_mwh'] for r in results.values()
                ),
                'avg_voltage_improvement_pu': round(
                    sum(r['avg_voltage_improvement_pu'] for r in results.values()), 3
                ),
                'estimated_loss_reduction_pct': round(total_solar_mw * 2.5, 1),  # Rough estimate
                'critical_events_reduction_pct': round(total_solar_mw * 15, 0)   # Rough estimate
            }
            
            return {
                "available": True,
                "station_results": results,
                "system_impact": system_impact,
                "data_status": "MODEL"
            }
            
        except Exception as e:
            logger.error(f"Error in solar impact analysis: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def get_solar_bess_profile(self, station: str, solar_mw: float, 
                              bess_power_mw: float, bess_duration_h: float,
                              strategy: str = 'smoothing',
                              technology: str = 'SAT Bifacial', **kwargs) -> Dict[str, Any]:
        """
        Get combined solar+BESS operation profile.
        
        Args:
            station: Station name
            solar_mw: Solar plant capacity in MW
            bess_power_mw: BESS power rating in MW
            bess_duration_h: BESS duration in hours
            strategy: BESS operation strategy
            technology: Solar technology type
            
        Returns:
            Dictionary with combined operation profiles and metrics
        """
        try:
            # Import BESS model
            from src.battery import BESSModel, calculate_metrics
            
            # Get solar profile
            solar_data = self.get_solar_generation_profile(
                station, solar_mw, technology
            )
            
            if not solar_data['available']:
                return {"available": False, "error": "Could not generate solar profile"}
            
            # Create annual profile from monthly profiles
            annual_profile = []
            for month in range(1, 13):
                hourly = solar_data['hourly_profiles'][month]
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]
                for day in range(days_in_month):
                    annual_profile.extend(hourly)
            
            annual_profile = np.array(annual_profile[:8760])  # Ensure exactly 8760 hours
            
            # Create BESS model
            bess = BESSModel(bess_power_mw, bess_duration_h)
            
            # Prepare kwargs for strategies
            sim_kwargs = {}
            if strategy == 'firm_delivery_window':
                # Use kwargs passed from dashboard
                sim_kwargs.update(kwargs)
            
            # Simulate BESS operation
            bess_results = bess.simulate_strategy(annual_profile, strategy, **sim_kwargs)
            
            # Calculate metrics from BESS results
            total_solar = np.sum(annual_profile)
            total_delivered = np.sum(bess_results['grid_power'])
            total_losses = np.sum(bess_results['energy_losses'])
            total_curtailed = np.sum(bess_results['solar_curtailed'])
            
            # Get cycles from BESS model
            annual_cycles = bess.cycles
            
            # Calculate utilization (throughput / max possible throughput)
            total_throughput = bess.total_energy_charged + bess.total_energy_discharged
            max_throughput = bess.capacity_mwh * 2 * 365  # Max possible cycles in a year
            utilization = total_throughput / max_throughput if max_throughput > 0 else 0
            
            metrics = {
                'solar_energy_mwh': total_solar,
                'delivered_energy_mwh': total_delivered,
                'losses_mwh': total_losses,
                'curtailed_mwh': total_curtailed,
                'bess_cycles_annual': annual_cycles,
                'bess_utilization': utilization,
                'system_efficiency': total_delivered / total_solar if total_solar > 0 else 0,
                'validation': bess_results.get('validation', {})
            }
            
            # Add firm window specific metrics if using that strategy
            if strategy == 'firm_delivery_window' and 'window_start' in sim_kwargs:
                # Calculate firm window performance
                window_start = sim_kwargs['window_start']
                window_end = sim_kwargs['window_end'] 
                firm_power = sim_kwargs['firm_power']
                
                # TODO: Implement firm window metrics calculation
                pass
            
            # Calculate monthly summaries
            monthly_grid = []
            monthly_solar = []
            monthly_battery = []
            
            hour_idx = 0
            for month in range(1, 13):
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]
                month_hours = days_in_month * 24
                
                month_grid = np.sum(bess_results['grid_power'][hour_idx:hour_idx+month_hours])
                month_solar = np.sum(annual_profile[hour_idx:hour_idx+month_hours])
                month_battery = np.sum(np.abs(bess_results['battery_power'][hour_idx:hour_idx+month_hours]))
                
                monthly_grid.append(month_grid)
                monthly_solar.append(month_solar)
                monthly_battery.append(month_battery / 2)  # Divide by 2 for throughput
                
                hour_idx += month_hours
            
            return {
                "available": True,
                "station": station,
                "solar_capacity_mw": solar_mw,
                "bess_power_mw": bess_power_mw,
                "bess_capacity_mwh": bess_power_mw * bess_duration_h,
                "bess_duration_h": bess_duration_h,
                "strategy": strategy,
                "annual_metrics": metrics,
                "monthly_grid_mwh": monthly_grid,
                "monthly_solar_mwh": monthly_solar,
                "monthly_battery_throughput_mwh": monthly_battery,
                "typical_day_profiles": self._extract_typical_days(bess_results, annual_profile),
                "data_status": "MODEL"
            }
            
        except Exception as e:
            logger.error(f"Error in solar+BESS simulation: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    # ============================================================================
    # REMOVED DUPLICATE METHOD: optimize_bess_for_solar (v1) 
    # 
    # This method was duplicated at line ~1968 causing CRITICAL SHADOWING BUG
    # Only the second definition was active, this one was ignored by Python
    # 
    # FIXED: January 2025 - DataManager Refactoring Phase 1
    # The active implementation is preserved below (was previously line ~1968)
    # ============================================================================
    
    # ============================================================================
    # REMOVED DUPLICATE METHOD: _extract_typical_days (v1)
    # 
    # This method was duplicated causing SHADOWING BUG (line ~2025 overwrites this)
    # FIXED: January 2025 - DataManager Refactoring Phase 1
    # 
    # Available implementations:
    # - _extract_typical_days_v2() at line ~1713 (preserved)
    # - _extract_typical_days() at line ~2025 (active/preserved)
    # ============================================================================
    
    def simulate_psfv_only(self, station: str, capacity_mw: float = 1.0,
                          technology: str = 'SAT Bifacial', 
                          day_type: str = 'typical') -> Dict[str, Any]:
        """
        NUEVO MÉTODO: Simular PSFV sin BESS para comparación en dashboard
        
        Genera perfil solar puro de 24h para mostrar diferencias con PSFV+BESS
        
        Args:
            station: Estación (Pilcaniyeu, Jacobacci, Maquinchao, Los Menucos)
            capacity_mw: Capacidad instalada en MW
            technology: Tecnología solar (Fixed/SAT × Monofacial/Bifacial)
            day_type: Tipo de día ('typical', 'summer', 'winter')
            
        Returns:
            Dictionary con perfil solar 24h y métricas básicas
        """
        try:
            # Get solar profile data
            solar_data = self.get_solar_generation_profile(
                station=station,
                capacity_mw=capacity_mw,
                technology=technology
            )
            
            if not solar_data['available']:
                return {"available": False, "error": "Could not generate solar profile"}
            
            # Select appropriate monthly profile based on day_type
            if day_type == 'summer':
                month = 1  # January (summer in southern hemisphere)
            elif day_type == 'winter':
                month = 6  # June (winter)
            else:  # typical
                month = 3  # March (shoulder season)
            
            # Get 24h profile for selected month
            hourly_profile = solar_data['hourly_profiles'][month]
            solar_profile = np.array(hourly_profile)
            
            # For PSFV only: grid_profile = solar_profile (no BESS)
            grid_profile = solar_profile.copy()
            
            # Calculate metrics
            daily_energy_mwh = float(np.sum(solar_profile))
            peak_mw = float(np.max(solar_profile))
            
            # Capacity factor (daily)
            theoretical_max = capacity_mw * 24  # MW × 24h
            capacity_factor = daily_energy_mwh / theoretical_max if theoretical_max > 0 else 0
            
            # Variability index (coefficient of variation)
            non_zero_values = solar_profile[solar_profile > 0.01]  # Only daylight hours
            if len(non_zero_values) > 1:
                variability_index = float(np.std(non_zero_values) / np.mean(non_zero_values))
            else:
                variability_index = 0.0
            
            # Count productive hours (> 5% of peak)
            productive_hours = int(np.sum(solar_profile > peak_mw * 0.05))
            
            return {
                "available": True,
                "station": station,
                "capacity_mw": capacity_mw,
                "technology": technology,
                "day_type": day_type,
                "solar_profile": solar_profile.tolist(),
                "grid_profile": grid_profile.tolist(),  # Same as solar (no BESS)
                "daily_energy_mwh": daily_energy_mwh,
                "peak_mw": peak_mw,
                "capacity_factor": capacity_factor,
                "variability_index": variability_index,
                "productive_hours": productive_hours,
                "curtailment_mwh": 0.0,  # No BESS = no curtailment
                "losses_mwh": 0.0,       # No BESS = no losses
                "efficiency_percent": 100.0,  # Perfect efficiency without BESS
                "data_status": "MODEL"
            }
            
        except Exception as e:
            logger.error(f"Error in PSFV-only simulation: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def get_daily_solar_profile(self, station: str, capacity_mw: float = 1.0,
                               technology: str = 'SAT Bifacial',
                               season: str = 'summer') -> Dict[str, Any]:
        """
        NUEVO MÉTODO: Generar perfil solar diario típico (24h) para dashboard
        
        Basado en get_solar_generation_profile pero formato 24h específico
        
        Args:
            station: Estación objetivo
            capacity_mw: Capacidad instalada
            technology: Tecnología solar
            season: Estación del año ('summer', 'winter', 'shoulder')
            
        Returns:
            Dictionary con perfil 24h y métricas
        """
        try:
            # Map seasons to representative months
            season_months = {
                'summer': 1,    # January
                'winter': 6,    # June  
                'shoulder': 3,  # March
                'autumn': 4,    # April
                'spring': 10    # October
            }
            
            month = season_months.get(season, 1)
            
            # Get solar data
            solar_data = self.get_solar_generation_profile(
                station=station,
                capacity_mw=capacity_mw,
                technology=technology
            )
            
            if not solar_data['available']:
                return {"available": False, "error": "Could not generate solar profile"}
            
            # Extract hourly profile for selected month
            hourly_profile = np.array(solar_data['hourly_profiles'][month])
            
            # Calculate additional metrics
            daily_energy = float(np.sum(hourly_profile))
            peak_power = float(np.max(hourly_profile))
            
            # Peak hours (> 80% of peak)
            peak_hours = int(np.sum(hourly_profile > peak_power * 0.8))
            
            # Average power during daylight (> 1% of peak)
            daylight_mask = hourly_profile > peak_power * 0.01
            avg_daylight_power = float(np.mean(hourly_profile[daylight_mask])) if np.any(daylight_mask) else 0.0
            
            return {
                "available": True,
                "station": station,
                "capacity_mw": capacity_mw,
                "technology": technology,
                "season": season,
                "month": month,
                "hourly_profile": hourly_profile.tolist(),
                "daily_energy_mwh": daily_energy,
                "peak_mw": peak_power,
                "peak_hours": peak_hours,
                "avg_daylight_power": avg_daylight_power,
                "capacity_factor": daily_energy / (capacity_mw * 24),
                "data_status": "MODEL"
            }
            
        except Exception as e:
            logger.error(f"Error generating daily solar profile: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def calculate_gd_cost_per_mwh(self, hours_per_day: float, fc: float = None, gas_price: float = None) -> Dict[str, Any]:
        """
        Calculate GD cost per MWh based on operational parameters
        
        Args:
            hours_per_day: Daily operation hours (2-24)
            fc: Factor de capacidad (optional, defaults to 0.8)
            gas_price: Gas price USD/m³ (optional, defaults to 0.11137)
            
        Returns:
            Dict with:
                - cost_per_mwh: USD/MWh
                - annual_generation_mwh: MWh/year
                - annual_cost_usd: USD/year
                - cost_breakdown: Dict with component costs
        """
        # Get base costs
        gd_costs = self.get_gd_costs()
        
        # Use defaults if not provided
        if fc is None:
            fc = gd_costs["factor_capacidad"]
        if gas_price is None:
            gas_price = gd_costs["precio_gas"]
            
        # System parameters
        potencia_mw = gd_costs["potencia_mw"]
        dias_ano = gd_costs["dias_ano"]
        horas_base = gd_costs["horas_dia_base"]
        
        # Calculate annual generation
        gen_anual_kwh = potencia_mw * 1000 * fc * hours_per_day * dias_ano
        gen_anual_mwh = gen_anual_kwh / 1000
        
        # Fixed costs (don't change with hours)
        alquiler_anual = gd_costs["alquiler_anual"]
        
        # Variable costs - OPEX and O&M scale with hours above base
        if hours_per_day <= horas_base:
            opex_anual = gd_costs["opex_total_anual"]
            oym_anual = gd_costs["costo_oym_anual"]
        else:
            # Linear scaling above base hours
            factor_incremento = hours_per_day / horas_base
            opex_anual = gd_costs["opex_total_anual"] * factor_incremento
            oym_anual = gd_costs["costo_oym_anual"] * factor_incremento
        
        # Fuel cost (always proportional to generation)
        consumo_gas_anual = gen_anual_kwh * gd_costs["consumo_gas"]
        costo_combustible_anual = consumo_gas_anual * gas_price
        
        # Total annual cost
        total_anual = alquiler_anual + opex_anual + costo_combustible_anual + oym_anual
        
        # Cost per MWh
        cost_per_mwh = total_anual / gen_anual_mwh if gen_anual_mwh > 0 else float('inf')
        
        return {
            "cost_per_mwh": round(cost_per_mwh, 2),
            "annual_generation_mwh": round(gen_anual_mwh, 0),
            "annual_cost_usd": round(total_anual, 0),
            "monthly_cost_usd": round(total_anual / 12, 0),
            "cost_breakdown": {
                "alquiler": round(alquiler_anual, 0),
                "opex": round(opex_anual, 0),
                "combustible": round(costo_combustible_anual, 0),
                "oym": round(oym_anual, 0)
            },
            "cost_breakdown_percent": {
                "alquiler": round((alquiler_anual / total_anual) * 100, 1),
                "opex": round((opex_anual / total_anual) * 100, 1),
                "combustible": round((costo_combustible_anual / total_anual) * 100, 1),
                "oym": round((oym_anual / total_anual) * 100, 1)
            },
            "parameters_used": {
                "hours_per_day": hours_per_day,
                "factor_capacidad": fc,
                "gas_price_usd_m3": gas_price,
                "potencia_mw": potencia_mw
            }
        }
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary"""
        return {
            "status": self.data_status,
            "load_attempts": self.load_attempts,
            "last_load": {k: v.isoformat() if v else None for k, v in self.last_load.items()},
            "overall_status": self.data_status["overall"].value,
            "is_using_fallback": any(s == DataStatus.FALLBACK for s in self.data_status.values())
        }
    
    def reload_data(self) -> None:
        """Force reload all data"""
        logger.info("Reloading all data...")
        self._load_all_data()
    
    def get_status_color(self) -> str:
        """Get color for status indicator based on overall status"""
        status_colors = {
            DataStatus.REAL: "success",      # Green
            DataStatus.PARTIAL: "warning",   # Yellow
            DataStatus.FALLBACK: "danger",   # Red
            DataStatus.ERROR: "dark"         # Dark/Black
        }
        return status_colors.get(self.data_status["overall"], "secondary")
    
    def get_status_text(self) -> str:
        """Get human-readable status text"""
        status_texts = {
            DataStatus.REAL: "Datos Reales",
            DataStatus.PARTIAL: "Datos Parciales",
            DataStatus.FALLBACK: "Datos de Respaldo",
            DataStatus.ERROR: "Error de Datos"
        }
        return status_texts.get(self.data_status["overall"], "Desconocido")
    
    def get_solar_bess_profile_v2(self, station: str, solar_mw: float, 
                                  bess_power_mw: float, bess_duration_h: float,
                                  strategy: str = 'cap_shaving',
                                  bess_technology: str = 'modern_lfp',
                                  solar_technology: str = 'SAT Bifacial', 
                                  **kwargs) -> Dict[str, Any]:
        """
        Get solar+BESS profile using enhanced BESS model v2 with validation.
        
        Args:
            station: Station name
            solar_mw: Solar plant capacity in MW
            bess_power_mw: BESS power rating in MW
            bess_duration_h: BESS duration in hours
            strategy: BESS operation strategy
            bess_technology: BESS technology (standard/modern_lfp/premium)
            solar_technology: Solar technology type
            **kwargs: Strategy-specific parameters
            
        Returns:
            Dictionary with operation profiles, metrics, and validation
        """
        try:
            # Import BESS model
            from src.battery.bess_model import BESSModel
            
            # Get solar profile
            solar_data = self.get_solar_generation_profile(
                station, solar_mw, solar_technology
            )
            
            if not solar_data['available']:
                return {"available": False, "error": "Could not generate solar profile"}
            
            # Create annual profile from monthly profiles
            annual_profile = []
            for month in range(1, 13):
                hourly = solar_data['hourly_profiles'][month]
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]
                for day in range(days_in_month):
                    annual_profile.extend(hourly)
            
            annual_profile = np.array(annual_profile[:8760])  # Ensure exactly 8760 hours
            
            # Create BESS model v2
            bess = BESSModel(bess_power_mw, bess_duration_h, bess_technology, 'parallel_ac')
            
            # Simulate with strategy
            results = bess.simulate_strategy(annual_profile, strategy, **kwargs)
            
            # Extract validation
            validation = results['validation']
            
            # Calculate monthly summaries
            monthly_grid = []
            monthly_solar = []
            monthly_losses = []
            
            hour_idx = 0
            for month in range(1, 13):
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]
                month_hours = days_in_month * 24
                
                month_grid = np.sum(results['grid_power'][hour_idx:hour_idx+month_hours])
                month_solar = np.sum(annual_profile[hour_idx:hour_idx+month_hours])
                month_loss = np.sum(results['energy_losses'][hour_idx:hour_idx+month_hours])
                
                monthly_grid.append(month_grid)
                monthly_solar.append(month_solar)
                monthly_losses.append(month_loss)
                
                hour_idx += month_hours
            
            # Extract typical days
            typical_days = self._extract_typical_days_v2(results, annual_profile)
            
            return {
                "available": True,
                "station": station,
                "solar_capacity_mw": solar_mw,
                "bess_config": bess.get_configuration_summary(),
                "strategy": strategy,
                "validation": validation,
                "annual_metrics": validation['metrics'],
                "monthly_grid_mwh": monthly_grid,
                "monthly_solar_mwh": monthly_solar,
                "monthly_losses_mwh": monthly_losses,
                "typical_day_profiles": typical_days,
                "ml_features": validation.get('ml_features', {}),
                "data_status": "MODEL"
            }
            
        except Exception as e:
            logger.error(f"Error in solar+BESS v2 simulation: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def _extract_typical_days_v2(self, bess_results: Dict, solar_profile: np.ndarray) -> Dict:
        """Extract typical day profiles from annual simulation for v2."""
        # Find days with different characteristics
        daily_solar = solar_profile.reshape(-1, 24).sum(axis=1)
        
        # High solar day
        high_solar_day = np.argmax(daily_solar)
        # Low solar day (but not zero)
        non_zero_days = daily_solar > 1
        low_solar_day = np.argmin(daily_solar[non_zero_days])
        # Average day
        avg_solar = np.mean(daily_solar)
        avg_day = np.argmin(np.abs(daily_solar - avg_solar))
        
        typical_days = {}
        
        for name, day_idx in [('high_solar', high_solar_day), 
                              ('low_solar', low_solar_day),
                              ('average', avg_day)]:
            start_hour = day_idx * 24
            end_hour = start_hour + 24
            
            typical_days[name] = {
                'hour': list(range(24)),
                'solar_mw': solar_profile[start_hour:end_hour].tolist(),
                'grid_mw': bess_results['grid_power'][start_hour:end_hour].tolist(),
                'battery_mw': bess_results['battery_power'][start_hour:end_hour].tolist(),
                'soc_percent': (bess_results['soc'][start_hour:end_hour] * 100).tolist(),
                'losses_mw': bess_results['energy_losses'][start_hour:end_hour].tolist()
            }
        
        return typical_days
    
    def simulate_solar_with_bess(self, 
                                station: str,
                                solar_mw: float,
                                bess_power_mw: float,
                                bess_duration_h: float,
                                strategy: str,
                                solar_technology: str = 'SAT Bifacial',
                                bess_technology: str = 'modern_lfp',
                                use_aggressive_strategies: bool = False,
                                **kwargs) -> Dict[str, Any]:
        """
        Simulate solar generation with BESS integration.
        
        MODIFICADO: January 2025 - Added support for BESSStrategies V2
        
        Args:
            station: Station name
            solar_mw: Solar capacity in MW
            bess_power_mw: BESS power in MW
            bess_duration_h: BESS duration in hours
            strategy: BESS operation strategy
            solar_technology: Solar technology type
            bess_technology: BESS technology ('standard', 'modern_lfp', 'premium')
            use_aggressive_strategies: Use BESSStrategies V2 for demonstration
            **kwargs: Additional strategy parameters
            
        Returns:
            Dictionary with simulation results and metrics
        """
        try:
            # Import BESS model
            from src.battery.bess_model import BESSModel
            
            # Step 1: Get solar generation profile
            solar_data = self.get_solar_generation_profile(
                station=station,
                capacity_mw=solar_mw,
                technology=solar_technology
            )
            
            if not solar_data['available']:
                return {"available": False, "error": "Could not generate solar profile"}
            
            # Step 2: Create annual profile from monthly data
            annual_profile = []
            monthly_solar = []
            
            for month in range(1, 13):
                hourly = solar_data['hourly_profiles'][month]
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]
                
                month_profile = []
                for day in range(days_in_month):
                    month_profile.extend(hourly)
                
                annual_profile.extend(month_profile)
                monthly_solar.append(sum(month_profile))
            
            # Ensure we have exactly 8760 hours
            annual_profile = np.array(annual_profile[:8760])
            
            # Step 3: Create and configure BESS model
            if bess_power_mw > 0 and bess_duration_h > 0:
                bess = BESSModel(
                    power_mw=bess_power_mw,
                    duration_hours=bess_duration_h,
                    technology=bess_technology,
                    verbose=False
                )
                
                # Step 4: Run simulation with strategy selection
                if use_aggressive_strategies:
                    # Use BESSStrategies V2 for demonstration of real losses
                    # For now, we simulate with enhanced parameters to show differences
                    logger.info(f"Using aggressive strategy mode for {strategy}")
                    
                    # Modify kwargs to make strategies more aggressive
                    enhanced_kwargs = kwargs.copy()
                    
                    # Enhance parameters based on strategy
                    if strategy == 'cap_shaving':
                        enhanced_kwargs['cap_mw'] = enhanced_kwargs.get('cap_mw', solar_mw * 0.6)  # Lower cap
                    elif strategy == 'flat_day':
                        enhanced_kwargs['target_power'] = enhanced_kwargs.get('target_power', solar_mw * 0.7)
                    elif strategy == 'night_shift':
                        enhanced_kwargs['shift_factor'] = enhanced_kwargs.get('shift_factor', 0.8)
                    elif strategy == 'ramp_limit':
                        enhanced_kwargs['max_ramp_mw_h'] = enhanced_kwargs.get('max_ramp_mw_h', solar_mw * 0.3)
                    
                    # Use standard simulation but with aggressive parameters
                    bess_results = bess.simulate_strategy(
                        solar_profile=annual_profile,
                        strategy=strategy,
                        **enhanced_kwargs
                    )
                    
                    # Mark as aggressive in results
                    bess_results['strategy_used'] = f"{strategy}_aggressive"
                    bess_results['aggressive_mode'] = True
                    
                else:
                    # Use standard BESSModel simulation
                    bess_results = bess.simulate_strategy(
                        solar_profile=annual_profile,
                        strategy=strategy,
                        **kwargs
                    )
                    bess_results['aggressive_mode'] = False
                
                # Extract validation from results
                validation = bess_results.get('validation', {})
                
            else:
                # No BESS - pass through solar
                bess_results = {
                    'grid_power': annual_profile.copy(),
                    'battery_power': np.zeros_like(annual_profile),
                    'soc': np.zeros_like(annual_profile),
                    'solar_curtailed': np.zeros_like(annual_profile),
                    'energy_losses': np.zeros_like(annual_profile),
                    'validation': {
                        'valid': True,
                        'efficiency': 1.0,
                        'metrics': {'solar_energy_mwh': np.sum(annual_profile)},
                        'technology': 'none',
                        'strategy_metrics': {}
                    }
                }
                validation = bess_results['validation']
            
            # Step 5: Calculate monthly metrics
            monthly_grid = []
            monthly_battery = []
            hour_idx = 0
            
            for month in range(1, 13):
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]
                month_hours = days_in_month * 24
                
                month_grid = np.sum(bess_results['grid_power'][hour_idx:hour_idx+month_hours])
                month_battery = np.sum(np.abs(bess_results['battery_power'][hour_idx:hour_idx+month_hours]))
                
                monthly_grid.append(month_grid)
                monthly_battery.append(month_battery / 2)  # Divide by 2 for throughput
                
                hour_idx += month_hours
            
            # Step 6: Calculate annual metrics
            annual_metrics = {
                'solar_energy_mwh': np.sum(annual_profile),
                'delivered_energy_mwh': np.sum(bess_results['grid_power']),
                'losses_mwh': np.sum(bess_results['energy_losses']),
                'curtailed_mwh': np.sum(bess_results['solar_curtailed']),
                'validation': validation
            }
            
            # Step 7: Extract typical days
            typical_days = self._extract_typical_days(bess_results, annual_profile)
            
            return {
                "available": True,
                "station": station,
                "solar_capacity_mw": solar_mw,
                "bess_power_mw": bess_power_mw,
                "bess_duration_h": bess_duration_h,
                "bess_capacity_mwh": bess_power_mw * bess_duration_h,
                "strategy": strategy,
                "annual_metrics": annual_metrics,
                "monthly_grid_mwh": monthly_grid,
                "monthly_solar_mwh": monthly_solar,
                "monthly_battery_throughput_mwh": monthly_battery,
                "typical_day_profiles": typical_days,
                "data_status": "MODEL"
            }
            
        except Exception as e:
            logger.error(f"Error in solar+BESS simulation: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def optimize_bess_for_solar(self,
                               station: str,
                               solar_mw: float,
                               objective: str = 'minimize_variability',
                               strategy: str = 'smoothing',
                               technology: str = 'SAT Bifacial') -> Dict[str, Any]:
        """
        Find optimal BESS sizing for given solar plant and objective.
        
        Args:
            station: Station name
            solar_mw: Solar plant capacity
            objective: Optimization objective
            strategy: BESS operation strategy
            technology: Solar technology
            
        Returns:
            Dictionary with optimization results
        """
        try:
            # Import BESS model
            from src.battery.bess_model import BESSModel
            import pandas as pd
            
            # Get solar profile
            solar_data = self.get_solar_generation_profile(
                station=station,
                capacity_mw=solar_mw,
                technology=technology
            )
            
            if not solar_data['available']:
                return {"available": False, "error": "Could not generate solar profile"}
            
            # Create annual profile
            annual_profile = []
            for month in range(1, 13):
                hourly = solar_data['hourly_profiles'][month]
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]
                for day in range(days_in_month):
                    annual_profile.extend(hourly)
            
            annual_profile = np.array(annual_profile[:8760])
            
            # Define search ranges
            power_range = np.arange(0.1 * solar_mw, 0.8 * solar_mw, 0.1 * solar_mw)
            duration_range = [1, 2, 3, 4, 5, 6]
            
            # Results storage
            results = []
            
            # Try each configuration
            for power in power_range:
                for duration in duration_range:
                    # Create BESS
                    bess = BESSModel(
                        power_mw=power,
                        duration_hours=duration,
                        technology='modern_lfp'
                    )
                    
                    # Map strategy names
                    bess_strategy = 'cap_shaving' if strategy == 'smoothing' else strategy
                    
                    # Simulate
                    bess_results = bess.simulate_strategy(
                        solar_profile=annual_profile,
                        strategy=bess_strategy
                    )
                    
                    # Calculate metrics
                    validation = bess_results.get('validation', {})
                    strategy_metrics = validation.get('strategy_metrics', {})
                    
                    # Calculate variability reduction
                    solar_std = np.std(annual_profile)
                    grid_std = np.std(bess_results['grid_power'])
                    variability_reduction = (1 - grid_std/solar_std) * 100 if solar_std > 0 else 0
                    
                    results.append({
                        'power_mw': power,
                        'duration_h': duration,
                        'capacity_mwh': power * duration,
                        'variability_reduction_percent': variability_reduction,
                        'battery_utilization_percent': strategy_metrics.get('bess_utilization', 0),
                        'efficiency_percent': validation.get('efficiency', 0) * 100,
                        'cycles': validation.get('strategy_metrics', {}).get('daily_cycles', 0) * 365
                    })
            
            # Convert to DataFrame for easy sorting
            results_df = pd.DataFrame(results)
            
            # Sort by objective
            if objective == 'minimize_variability':
                results_df = results_df.sort_values('variability_reduction_percent', ascending=False)
            elif objective == 'maximize_utilization':
                results_df = results_df.sort_values('battery_utilization_percent', ascending=False)
            else:
                results_df = results_df.sort_values('efficiency_percent', ascending=False)
            
            # Get top configurations
            top_configs = results_df.head(5).to_dict('records')
            
            # Find sweet spot (best trade-off)
            results_df['score'] = (
                results_df['variability_reduction_percent'] / 100 * 0.4 +
                results_df['battery_utilization_percent'] / 100 * 0.3 +
                results_df['efficiency_percent'] / 100 * 0.3
            )
            
            best_idx = results_df['score'].idxmax()
            recommended = results_df.loc[best_idx].to_dict()
            
            return {
                "available": True,
                "station": station,
                "solar_capacity_mw": solar_mw,
                "objective": objective,
                "strategy": strategy,
                "recommended_config": {
                    "power_mw": recommended['power_mw'],
                    "duration_h": recommended['duration_h'],
                    "capacity_mwh": recommended['capacity_mwh'],
                    "metrics": {
                        "variability_reduction": recommended['variability_reduction_percent'],
                        "utilization": recommended['battery_utilization_percent'],
                        "efficiency": recommended['efficiency_percent'],
                        "annual_cycles": recommended['cycles']
                    }
                },
                "top_configurations": top_configs,
                "all_results": results_df.to_dict('records'),
                "data_status": "MODEL"
            }
            
        except Exception as e:
            logger.error(f"Error in BESS optimization: {e}")
            return {"available": False, "error": str(e), "data_status": "ERROR"}
    
    def _extract_typical_days(self, bess_results: Dict, solar_profile: np.ndarray) -> Dict:
        """Extract typical day profiles from annual simulation"""
        # Find days with different characteristics
        daily_solar = solar_profile.reshape(-1, 24).sum(axis=1)
        
        # High solar day
        high_solar_day = np.argmax(daily_solar)
        # Low solar day (but not zero)
        non_zero_days = daily_solar > 1
        if np.any(non_zero_days):
            low_solar_indices = np.where(non_zero_days)[0]
            low_solar_day = low_solar_indices[np.argmin(daily_solar[non_zero_days])]
        else:
            low_solar_day = 0
        # Average day
        avg_solar = np.mean(daily_solar)
        avg_day = np.argmin(np.abs(daily_solar - avg_solar))
        
        typical_days = {}
        
        for name, day_idx in [('high_solar', high_solar_day), 
                              ('low_solar', low_solar_day),
                              ('average', avg_day)]:
            start_hour = day_idx * 24
            end_hour = start_hour + 24
            
            typical_days[name] = {
                'hour': list(range(24)),
                'solar_mw': solar_profile[start_hour:end_hour].tolist(),
                'grid_mw': bess_results['grid_power'][start_hour:end_hour].tolist(),
                'battery_mw': bess_results['battery_power'][start_hour:end_hour].tolist(),
                'soc_percent': (bess_results['soc'][start_hour:end_hour] * 100).tolist()
            }
        
        return typical_days
    
    def _resolve_project_root(self) -> Path:
        """
        Robust project root resolution with fallback mechanisms
        FIXED: January 2025 - Handle deployment scenarios properly
        """
        import os
        
        # Try environment variable first (for deployments)
        if data_root := os.getenv('ESTUDIO_DATA_ROOT'):
            root = Path(data_root)
            if root.exists() and (root / "data").exists():
                logger.info(f"Using project root from ESTUDIO_DATA_ROOT: {root}")
                return root
            else:
                logger.warning(f"ESTUDIO_DATA_ROOT set but invalid: {root}")
        
        # Try relative path from this file
        root = Path(__file__).parent.parent.parent.parent
        if root.exists() and (root / "data").exists():
            logger.info(f"Using relative project root: {root}")
            return root
        
        # Try current working directory
        cwd = Path.cwd()
        if (cwd / "data").exists():
            logger.info(f"Using CWD as project root: {cwd}")
            return cwd
        
        # Try parent directories up to 3 levels
        for i in range(1, 4):
            parent = cwd.parents[i-1]
            if (parent / "data").exists():
                logger.info(f"Using parent directory as project root: {parent}")
                return parent
        
        # Last resort: create minimal structure
        logger.error("Cannot resolve project root. Creating minimal structure in current directory.")
        minimal_root = cwd / "estudio_data"
        minimal_root.mkdir(exist_ok=True)
        (minimal_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (minimal_root / "data" / "fallback").mkdir(parents=True, exist_ok=True)
        return minimal_root

    # ============================================================================
    # BESS CONSTANTS AND CONFIGURATIONS - CENTRALIZED ACCESS
    # ============================================================================
    
    def get_bess_constants(self) -> Dict[str, Any]:
        """
        Get centralized BESS constants
        
        Returns:
            Dictionary with BESS constants
        """
        return dict(BESS_CONSTANTS)
    
    def get_bess_technologies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available BESS technologies with their parameters
        
        Returns:
            Dictionary with technology configurations
        """
        return dict(BESS_TECHNOLOGIES)
    
    def get_bess_topologies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available BESS topologies with their parameters
        
        Returns:
            Dictionary with topology configurations
        """
        return dict(BESS_TOPOLOGIES)
    
    def get_bess_strategy_enum(self) -> type:
        """
        Get BESSStrategy enum class
        
        Returns:
            BESSStrategy enum class
        """
        return BESSStrategy
    
    def get_bess_technology_enum(self) -> type:
        """
        Get BESSTechnology enum class
        
        Returns:
            BESSTechnology enum class
        """
        return BESSTechnology
    
    def get_bess_topology_enum(self) -> type:
        """
        Get BESSTopology enum class
        
        Returns:
            BESSTopology enum class
        """
        return BESSTopology
    
    def get_bess_technology_params(self, technology: str) -> Dict[str, Any]:
        """
        Get parameters for a specific BESS technology
        
        Args:
            technology: Technology name (e.g., 'modern_lfp', 'standard', 'premium')
            
        Returns:
            Dictionary with technology parameters
            
        Raises:
            ValueError: If technology is not found
        """
        if technology not in BESS_TECHNOLOGIES:
            available = list(BESS_TECHNOLOGIES.keys())
            raise ValueError(f"Technology '{technology}' not found. Available: {available}")
        
        return dict(BESS_TECHNOLOGIES[technology])
    
    def get_bess_topology_params(self, topology: str) -> Dict[str, Any]:
        """
        Get parameters for a specific BESS topology
        
        Args:
            topology: Topology name (e.g., 'parallel_ac', 'series_dc', 'hybrid')
            
        Returns:
            Dictionary with topology parameters
            
        Raises:
            ValueError: If topology is not found
        """
        if topology not in BESS_TOPOLOGIES:
            available = list(BESS_TOPOLOGIES.keys())
            raise ValueError(f"Topology '{topology}' not found. Available: {available}")
        
        return dict(BESS_TOPOLOGIES[topology])
    
    def create_bess_model(self, power_mw: float, duration_hours: float,
                         technology: str = "modern_lfp", topology: str = "parallel_ac",
                         **kwargs) -> Any:
        """
        Create a BESSModel instance using centralized constants
        
        Args:
            power_mw: Power rating in MW
            duration_hours: Duration in hours
            technology: Technology type (default: 'modern_lfp')
            topology: Topology type (default: 'parallel_ac')
            **kwargs: Additional parameters for BESSModel
            
        Returns:
            BESSModel instance
            
        Raises:
            ImportError: If BESSModel is not available
        """
        try:
            from ....src.battery.bess_model import BESSModel
            
            return BESSModel(
                power_mw=power_mw,
                duration_hours=duration_hours,
                technology=technology,
                topology=topology,
                **kwargs
            )
        except ImportError as e:
            raise ImportError(f"BESSModel not available: {e}")

# Create singleton instance
_data_manager_instance = None

def get_data_manager() -> DataManager:
    """Get or create the singleton DataManager instance"""
    global _data_manager_instance
    if _data_manager_instance is None:
        _data_manager_instance = DataManager()
    return _data_manager_instance