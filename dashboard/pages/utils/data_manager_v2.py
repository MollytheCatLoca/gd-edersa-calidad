"""
DataManager V2 — Thread-Safe, Modular Coordinator
=================================================

• Centraliza la coordinación de **DataLoader**, **DataAnalytics** y
  **SolarBESSimulator**.
• Implementa _singleton_ con `threading.Lock` para uso seguro en
  aplicaciones multi-hilo / ASGI workers.
• Exposición de una API homogénea basada en `DataResult` y
  `APIResponse`.
• Métricas de desempeño y estado de cache integradas.

⚠️ **Cambios/renombres importantes**
-----------------------------------
1. Clase **SolarBESSSimulator ⇒ SolarBESSimulator** (se elimina la S
   duplicada). Se exporta también un *alias* retro-compatible para no
   romper otros módulos; eliminar el alias cuando el resto del código
   se actualice.
2. Método `DataResult.is_valid()` no existía; aquí se sustituye por la
   comprobación `result.status == DataStatus.REAL and result.data is
   not None`. Actualizar tests si dependen de dicho método.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

import numpy as np  # usado en `optimize_bess_for_solar`
import pandas as pd

# ─────────────────────────────────────────────────────────────
# Módulos especializados (local package)
# ─────────────────────────────────────────────────────────────
from .constants import (
    BESS_CONSTANTS,
    BESS_TECHNOLOGIES,
    BESS_TOPOLOGIES,
    BESSTechnology,
    BESSTopology,
    BESSStrategy,
    CACHE_CONFIG,
    DataStatus,
    GD_CONSTANTS,
    NETWORK_CONSTANTS,
    STATIONS,
)
from .data_analytics import DataAnalytics
from .data_loaders import DataLoader
from .models import APIResponse, DataManagerConfig, DataResult
from .solar_bess_simulator import SolarBESSSimulator as _SolarBESSimulator  # nuevo nombre
from .data_manager_legacy_compatibility import DataManagerLegacyCompatibility

# Alias retro-compatible (deprecado)
SolarBESSSimulator = _SolarBESSimulator  # TODO: eliminar cuando se actualicen los imports externos

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Configuración por defecto
# ─────────────────────────────────────────────────────────────


def _default_config() -> DataManagerConfig:  # type: ignore[name-defined]
    """Devuelve la configuración por defecto para el *manager*."""
    return DataManagerConfig(
        data_path="data/processed",
        fallback_path="data/fallback",
        cache_enabled=True,
        cache_size=CACHE_CONFIG["CACHE_SIZE"],
        max_retries=3,  # Default retry count
        log_level="INFO",
        thread_safe=True,
        validation_enabled=True,
    )


# ─────────────────────────────────────────────────────────────
# DataManagerV2
# ─────────────────────────────────────────────────────────────


class DataManagerV2(DataManagerLegacyCompatibility):
    """Coordinador principal – **singleton**.

    Usa *lazy-loading* y *locks* finos para minimizar contención.
    Hereda de DataManagerLegacyCompatibility para compatibilidad con dashboards existentes.
    """

    _instance: Optional["DataManagerV2"] = None
    _instance_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Creación thread-safe del singleton
    # ------------------------------------------------------------------

    def __new__(cls, config: Optional[DataManagerConfig] = None):  # type: ignore[name-defined]  # noqa: ARG003
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------

    def __init__(self, config: Optional[DataManagerConfig] = None):  # type: ignore[name-defined]
        # Evitar múltiples inicializaciones en el singleton
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.config = config or _default_config()

        # Resolver raíz del proyecto
        self.project_root: Path = self._resolve_project_root()

        # Componentes especializados
        self.data_loader = DataLoader(self.project_root)
        self.data_analytics = DataAnalytics()
        self.solar_bess_simulator = _SolarBESSimulator()

        # Bloqueos por recurso
        self._data_locks: Dict[str, threading.Lock] = {
            "system": threading.Lock(),
            "transformers": threading.Lock(),
            "historical": threading.Lock(),
        }

        # Almacenes de datos
        self._system_data: Optional[dict] = None
        self._transformer_details: Optional[dict] = None
        self._historical_data: Optional[pd.DataFrame] = None

        # Estado de cada familia de datos
        self.data_status: Dict[str, DataStatus] = {
            "system": DataStatus.ERROR,
            "transformers": DataStatus.ERROR,
            "historical": DataStatus.ERROR,
            "overall": DataStatus.ERROR,
        }

        # Métricas de rendimiento a nivel *manager*
        self._perf: List[Dict[str, Any]] = []

        # Cargar datos iniciales
        self._load_all_data()
        logger.info("DataManagerV2 inicializado — estado global: %s", self.data_status["overall"].value)

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_project_root() -> Path:
        """Intenta localizar la raíz del proyecto subiendo directorios."""
        here = Path(__file__).resolve()
        for parent in here.parents:
            # Check for multiple indicators of project root
            if ((parent / "pyproject.toml").exists() or 
                (parent / ".git").exists() or 
                (parent / "requirements.txt").exists() or
                (parent / "dashboard").exists() and (parent / "data").exists()):
                return parent
        # Fallback: go up 3 levels from utils
        # __file__ is in dashboard/pages/utils/
        return here.parent.parent.parent

    def _log_perf(self, op: str, start: float, ok: bool, err: str | None = None) -> None:
        self._perf.append(
            {
                "operation": op,
                "execution_time": time.time() - start,
                "success": ok,
                "error": err,
                "ts": datetime.now().isoformat(),
            }
        )

    def _timeit(self, op: str):
        """Decorador simple para medir operaciones públicas."""

        def decorator(func):
            def wrapper(self_inner, *args, **kwargs):
                t0 = time.time()
                try:
                    res = func(self_inner, *args, **kwargs)
                    self_inner._log_perf(op, t0, True)
                    return res
                except Exception as exc:  # pragma: no cover
                    self_inner._log_perf(op, t0, False, str(exc))
                    raise

            return wrapper

        return decorator

    def _update_overall_status(self) -> None:
        """Re-calcula el estado global en función de los componentes."""
        s = list(self.data_status.values())[:-1]  # exclude overall
        if all(v == DataStatus.REAL for v in s):
            self.data_status["overall"] = DataStatus.REAL
        elif any(v == DataStatus.ERROR for v in s):
            self.data_status["overall"] = DataStatus.ERROR
        elif any(v == DataStatus.FALLBACK for v in s):
            self.data_status["overall"] = DataStatus.FALLBACK
        else:
            self.data_status["overall"] = DataStatus.PARTIAL

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def _load_all_data(self) -> None:
        """Carga (o recarga) las tres familias de datos."""
        # System
        sys_res = self.data_loader.load_system_data()
        with self._data_locks["system"]:
            self._system_data = sys_res.data
            self.data_status["system"] = sys_res.status

        # Transformers
        tr_res = self.data_loader.load_transformer_details()
        logger.info(f"Transformer load result: status={tr_res.status}, has_data={tr_res.data is not None}")
        if tr_res.data:
            logger.info(f"Transformer data keys: {list(tr_res.data.keys())[:3] if isinstance(tr_res.data, dict) else 'not a dict'}")
        with self._data_locks["transformers"]:
            self._transformer_details = tr_res.data
            self.data_status["transformers"] = tr_res.status

        # Historical
        hist_res = self.data_loader.load_historical_data()
        with self._data_locks["historical"]:
            self._historical_data = hist_res.data
            self.data_status["historical"] = hist_res.status

        # Estado global
        self._update_overall_status()

    # ------------------------------------------------------------------
    # API pública — consultas de datos primarios
    # ------------------------------------------------------------------

    def get_nodes(self) -> DataResult:  # type: ignore[name-defined]
        """
        Get network nodes data with thread-safe access.
        
        Returns:
            DataResult: Contains nodes data with status (REAL/FALLBACK) and metadata
        """
        with self._data_locks["system"]:
            if self._system_data and "nodes" in self._system_data:
                return DataResult(data=self._system_data["nodes"], status=self.data_status["system"], meta={})
            # NO FALLBACK - User wants REAL DATA ONLY
            logger.error("No real nodes data available - NO FALLBACK AS REQUESTED")
            return DataResult(data={}, status=DataStatus.ERROR, meta={"error": "No real data available"})

    def get_edges(self) -> DataResult:  # type: ignore[name-defined]
        """
        Get network edges/lines data with thread-safe access.
        
        Returns:
            DataResult: Contains edges data with status and metadata. 
                       Falls back to generated edges from station constants if real data unavailable.
        """
        with self._data_locks["system"]:
            if self._system_data and "edges" in self._system_data:
                return DataResult(data=self._system_data["edges"], status=self.data_status["system"], meta={})

        # Generar aristas fallback
        edges: List[Dict[str, Any]] = []
        stations = list(STATIONS.keys())
        for i in range(len(stations) - 1):
            a, b = stations[i], stations[i + 1]
            dist = STATIONS[b]["distance_km"] - STATIONS[a]["distance_km"]
            edges.append(
                {
                    "from_node": a,
                    "to_node": b,
                    "length_km": dist,
                    "impedance_ohm": dist * 0.5,
                    "voltage_drop_pu": dist * NETWORK_CONSTANTS["VOLTAGE_DROP_PER_KM"],
                    "losses_mw": dist * NETWORK_CONSTANTS["LOSSES_PER_KM"],
                }
            )
        return DataResult(data=edges, status=DataStatus.FALLBACK, meta={"source": "constants"})

    def get_transformers(self) -> DataResult:  # type: ignore[name-defined]
        with self._data_locks["transformers"]:
            if self._transformer_details is not None:
                # Handle different data structures
                transformers_data = None
                source = "unknown"
                
                if isinstance(self._transformer_details, dict):
                    # Case 1: Real JSON data with "transformadores" key
                    if "transformadores" in self._transformer_details:
                        transformers_data = self._transformer_details["transformadores"]
                        source = "transformadores_detalle.json"
                        logger.info(f"Extracted real transformers data with {len(transformers_data)} locations")
                    
                    # Case 2: Fallback data with "transformers" key and wrapper
                    elif "transformers" in self._transformer_details and "source" in self._transformer_details:
                        transformers_data = self._transformer_details["transformers"]
                        source = self._transformer_details.get("source", "FALLBACK")
                        logger.warning(f"Using {source} transformer data with {len(transformers_data)} locations")
                    
                    # Case 3: Direct transformer data (old format)
                    else:
                        transformers_data = self._transformer_details
                        source = "direct"
                        logger.info("Using direct transformer data format")
                
                if transformers_data is not None:
                    return DataResult(
                        data=transformers_data, 
                        status=self.data_status["transformers"], 
                        meta={"source": source, "format": "unwrapped"}
                    )

        # If we get here, no data was loaded - this shouldn't happen if _load_initial_data worked
        logger.error("No transformer data available - this indicates a loading problem")
        return DataResult(
            data={}, 
            status=DataStatus.ERROR, 
            meta={"error": "No transformer data loaded", "source": "none"}
        )

    # ------------------------------------------------------------------
    # Operaciones analíticas — delegadas a DataAnalytics
    # ------------------------------------------------------------------

    def get_hourly_voltage_analysis(self) -> DataResult:  # type: ignore[name-defined]
        with self._data_locks["historical"]:
            if self._historical_data is None:
                return DataResult(data=None, status=DataStatus.ERROR, meta={"error": "No historical data"})
            return self.data_analytics.get_hourly_voltage_analysis(self._historical_data)

    def get_demand_voltage_correlation(self) -> DataResult:  # type: ignore[name-defined]
        with self._data_locks["historical"]:
            if self._historical_data is None:
                return DataResult(data=None, status=DataStatus.ERROR, meta={"error": "No historical data"})
            return self.data_analytics.get_demand_voltage_correlation(self._historical_data)

    def get_critical_events_analysis(self) -> DataResult:  # type: ignore[name-defined]
        with self._data_locks["historical"]:
            if self._historical_data is None:
                return DataResult(data=None, status=DataStatus.ERROR, meta={"error": "No historical data"})
            return self.data_analytics.get_critical_events_analysis(self._historical_data)

    def get_gd_costs(self) -> Dict[str, Any]:
        """
        Obtiene datos de costos de generación distribuida para Los Menucos.
        
        Método de compatibilidad para fase2_topologia.py y tab6_distributed_generation.py
        que devuelve información completa sobre la generación distribuida existente.
        
        Returns:
            Dict con datos de GD: potencia, expansión, operación, costos
        """
        # Obtener todas las constantes desde GD_CONSTANTS
        potencia_mw = GD_CONSTANTS["potencia_mw"]
        factor_capacidad = GD_CONSTANTS["factor_capacidad"]
        horas_dia_base = GD_CONSTANTS["horas_dia_base"]
        dias_ano = GD_CONSTANTS["dias_ano"]
        dias_mes = GD_CONSTANTS["dias_mes"]
        
        # Costos mensuales desde constantes
        alquiler_mensual = GD_CONSTANTS["alquiler_mensual"]
        opex_por_mw_mensual = GD_CONSTANTS["opex_por_mw_mensual"]
        combustible_mensual = GD_CONSTANTS["combustible_mensual_base"]
        
        # Cálculos anuales
        alquiler_anual = alquiler_mensual * 12
        opex_mensual_total = opex_por_mw_mensual * potencia_mw
        opex_total_anual = opex_mensual_total * 12
        combustible_anual = combustible_mensual * 12
        
        # O&M basado en OPEX
        factor_oym = GD_CONSTANTS["factor_oym"]
        costo_oym_mensual = opex_mensual_total * factor_oym
        costo_oym_anual = costo_oym_mensual * 12
        
        # Parámetros técnicos desde constantes
        consumo_gas = GD_CONSTANTS["consumo_gas"]
        precio_gas = GD_CONSTANTS["precio_gas"]
        
        # Generación mensual y anual
        energia_mensual_mwh = potencia_mw * horas_dia_base * dias_mes * factor_capacidad
        energia_anual_mwh = energia_mensual_mwh * 12
        energia_anual_kwh = energia_anual_mwh * 1000
        
        # Factor de utilización anual (para mostrar)
        factor_utilizacion_anual = (horas_dia_base * factor_capacidad) / 24
        
        # Costos totales mensuales y anuales
        costo_total_mensual = alquiler_mensual + opex_mensual_total + combustible_mensual + costo_oym_mensual
        costo_total_anual = costo_total_mensual * 12
        
        # Costo por MWh
        costo_por_mwh = costo_total_mensual / energia_mensual_mwh if energia_mensual_mwh > 0 else 0
        
        return {
            # Datos actuales de Los Menucos
            'potencia_mw': potencia_mw,
            'potencia_expansion_mw': 1.2,  # MW de expansión planificada
            'horas_dia_base': horas_dia_base,
            'factor_capacidad': factor_capacidad,
            'costo_por_mwh': costo_por_mwh,
            'dias_ano': dias_ano,
            
            # Datos económicos requeridos por tab6
            'alquiler_mensual': alquiler_mensual,
            'alquiler_anual': alquiler_anual,
            'opex_por_mw_anual': opex_total_anual,
            'opex_total_anual': opex_total_anual,
            'opex_mensual': opex_mensual_total,
            'costo_oym_anual': costo_oym_anual,
            'costo_oym_mensual': costo_oym_mensual,
            
            # Costos de combustible
            'consumo_gas': consumo_gas,
            'precio_gas': precio_gas,
            'costo_combustible_anual': combustible_anual,
            'costo_combustible_mensual': combustible_mensual,
            
            # Costos totales
            'costo_total_anual': costo_total_anual,
            'costo_total_mensual': costo_total_mensual,
            
            # Datos de generación
            'energia_anual_mwh': energia_anual_mwh,
            'energia_mensual_mwh': energia_mensual_mwh,
            'energia_diaria_mwh': energia_mensual_mwh / dias_mes,
            'generacion_anual_mwh': energia_anual_mwh,
            'generacion_mensual_mwh': energia_mensual_mwh,
            
            # Metadatos de fuentes
            'data_sources': {
                'potencia_mw': {
                    'tipo': 'DATO',
                    'fuente': 'Documentación oficial',
                    'note': '2 × 1.5 MW motogeneradores - 0.3 MW fuera de servicio'
                },
                'potencia_expansion_mw': {
                    'tipo': 'ESTIMADO',
                    'fuente': 'Análisis técnico FASE 1',
                    'note': 'Expansión recomendada para optimizar operación'
                },
                'horas_dia_base': {
                    'tipo': 'DATO',
                    'fuente': 'Patrón operación actual',
                    'note': 'Operación típica horario pico'
                },
                'factor_capacidad': {
                    'tipo': 'DATO',
                    'fuente': 'Especificación técnica',
                    'note': 'Factor de capacidad DURANTE OPERACIÓN (0.95 = 95% cuando funciona)'
                },
                'costo_por_mwh': {
                    'tipo': 'CALCULADO',
                    'fuente': 'Análisis económico FASE 1',
                    'note': 'Costo actual de operación'
                }
            },
            
            # Datos adicionales para análisis
            'ubicacion': GD_CONSTANTS["ubicacion"],
            'tecnologia': GD_CONSTANTS["tecnologia"],
            'status': 'Operativo',
            'fecha_analisis': '2025-07-01',
            'capacidad_total_mw': GD_CONSTANTS["potencia_total_mw"],
            'capacidad_disponible_mw': potencia_mw,
            'factor_utilizacion': factor_utilizacion_anual,  # Factor anual real
            'factor_capacidad_operacion': factor_capacidad,  # FC durante operación
            
            # Métricas económicas (estos pueden mantenerse como estimados)
            'capex_usd_kw': 1200,  # Estimado para motogeneradores
            'opex_usd_kw_año': opex_total_anual / (potencia_mw * 1000),  # Calculado desde datos reales
            'costo_combustible_usd_mwh': (combustible_mensual * 12) / energia_anual_mwh if energia_anual_mwh > 0 else 0,
            'vida_util_años': 15,
            
            # Análisis de sensibilidad simplificado (removido por complejidad)
            
            # Campos adicionales requeridos por tab6
            'alquiler_referencia': {
                'costo_unitario': GD_CONSTANTS["alquiler_unitario"],  # USD/kW-mes
                'moneda': 'USD',
                'descripcion': 'Costo unitario de alquiler de equipos'
            },
            'precio_compra_edersa': GD_CONSTANTS["precio_compra_edersa"]  # USD/MWh
        }


    def get_theoretical_voltages(self) -> Dict[str, Any]:
        """
        Obtiene voltajes teóricos del sistema para análisis de topología.
        
        Método de compatibilidad para fase2_topologia.py que devuelve
        voltajes teóricos calculados con caída de tensión 0.15%/km.
        
        Returns:
            Dict con voltajes teóricos por nodo en formato esperado
        """
        return {
            'voltages': {
                'PILCANIYEU': {
                    'value': 1.000,
                    'type': 'REFERENCIA',
                    'note': 'Punto de referencia del sistema'
                },
                'COMALLO': {
                    'value': 0.895,
                    'type': 'TEORICO',
                    'note': 'Caída teórica: 70km × 0.15%/km'
                },
                'ONELLI': {
                    'value': 0.820,
                    'type': 'TEORICO',
                    'note': 'Caída teórica: 120km × 0.15%/km'
                },
                'JACOBACCI': {
                    'value': 0.775,
                    'type': 'TEORICO',
                    'note': 'Caída teórica: 150km × 0.15%/km'
                },
                'MAQUINCHAO': {
                    'value': 0.685,
                    'type': 'TEORICO',
                    'note': 'Caída teórica: 210km × 0.15%/km'
                },
                'AGUADA_DE_GUERRA': {
                    'value': 0.640,
                    'type': 'TEORICO',
                    'note': 'Caída teórica: 240km × 0.15%/km'
                },
                'LOS_MENUCOS': {
                    'value': 0.595,
                    'type': 'TEORICO',
                    'note': 'Caída teórica: 270km × 0.15%/km'
                }
            },
            'drop_rate_per_km': 0.0015,  # 0.15%/km
            'base_voltage': 1.0,
            'method': 'Linear drop calculation'
        }

    def get_real_measurements(self) -> Dict[str, Any]:
        """
        Obtiene mediciones reales del sistema cuando están disponibles.
        
        Método de compatibilidad para fase2_topologia.py que devuelve
        mediciones reales de voltaje del sistema.
        
        Returns:
            Dict con mediciones reales por nodo en formato esperado
        """
        return {
            'voltages': {
                'available': True,
                'PILCANIYEU': {
                    'value': 0.607,
                    'type': 'DATO',
                    'note': 'Medición real promedio',
                    'data_points': 21015,
                    'quality': 'BUENA'
                },
                'JACOBACCI': {
                    'value': 0.236,
                    'type': 'DATO',
                    'note': 'Medición real promedio',
                    'data_points': 21015,
                    'quality': 'CRÍTICA'
                },
                'MAQUINCHAO': {
                    'value': 0.241,
                    'type': 'DATO',
                    'note': 'Medición real promedio',
                    'data_points': 21015,
                    'quality': 'CRÍTICA'
                },
                'LOS_MENUCOS': {
                    'value': 0.237,
                    'type': 'DATO',
                    'note': 'Medición real promedio',
                    'data_points': 21015,
                    'quality': 'CRÍTICA'
                }
            },
            'total_data_points': 84060,
            'period': 'Enero-Octubre 2024',
            'quality_summary': {
                'BUENA': 1,
                'CRÍTICA': 3,
                'NO_DISPONIBLE': 3
            }
        }

    def get_theoretical_losses(self) -> Dict[str, Any]:
        """
        Obtiene pérdidas teóricas del sistema para análisis de topología.
        
        Método de compatibilidad para fase2_topologia.py que devuelve
        pérdidas teóricas calculadas para cada tramo de línea.
        
        Returns:
            Dict con pérdidas teóricas por tramo en formato esperado
        """
        return {
            'segments': [
                {
                    'name': 'Pilcaniyeu-Comallo',
                    'loss_mw': 0.08,
                    'loss_percentage': 12.7,
                    'distance_km': 70,
                    'type': 'TEORICO'
                },
                {
                    'name': 'Comallo-Onelli',
                    'loss_mw': 0.12,
                    'loss_percentage': 19.0,
                    'distance_km': 50,
                    'type': 'TEORICO'
                },
                {
                    'name': 'Onelli-Jacobacci',
                    'loss_mw': 0.10,
                    'loss_percentage': 15.9,
                    'distance_km': 30,
                    'type': 'TEORICO'
                },
                {
                    'name': 'Jacobacci-Maquinchao',
                    'loss_mw': 0.15,
                    'loss_percentage': 23.8,
                    'distance_km': 60,
                    'type': 'TEORICO'
                },
                {
                    'name': 'Maquinchao-Aguada',
                    'loss_mw': 0.08,
                    'loss_percentage': 12.7,
                    'distance_km': 30,
                    'type': 'TEORICO'
                },
                {
                    'name': 'Aguada-Los Menucos',
                    'loss_mw': 0.10,
                    'loss_percentage': 15.9,
                    'distance_km': 30,
                    'type': 'TEORICO'
                }
            ],
            'total': {
                'loss_mw': 0.63,
                'loss_percentage': 100.0,
                'type': 'TEORICO'
            },
            'total_distance_km': 270,
            'average_loss_per_km': 0.00233,  # MW/km
            'method': 'I²R theoretical calculation'
        }

    def get_impedances(self) -> Dict[str, Any]:
        """
        Obtiene impedancias de línea calculadas según catálogo de conductores.
        
        Returns:
            Dict con impedancias por segmento y acumuladas
        """
        # Impedancias típicas por km según conductor
        # Fuente: Catálogo de conductores ACSR
        impedances_per_km = {
            'ACSR 120mm²': {'r': 0.236, 'x': 0.395},  # Ohm/km
            'ACSR 95mm²': {'r': 0.298, 'x': 0.405},   # Ohm/km
            'ACSR 70mm²': {'r': 0.405, 'x': 0.415},   # Ohm/km
            'ACSR 50mm²': {'r': 0.567, 'x': 0.428}    # Ohm/km
        }
        
        # Segmentos de línea con conductores
        segments = [
            {'from': 'PILCANIYEU', 'to': 'COMALLO', 'distance_km': 70, 'conductor': 'ACSR 120mm²'},
            {'from': 'COMALLO', 'to': 'ONELLI', 'distance_km': 50, 'conductor': 'ACSR 95mm²'},
            {'from': 'ONELLI', 'to': 'JACOBACCI', 'distance_km': 30, 'conductor': 'ACSR 95mm²'},
            {'from': 'JACOBACCI', 'to': 'MAQUINCHAO', 'distance_km': 60, 'conductor': 'ACSR 70mm²'},
            {'from': 'MAQUINCHAO', 'to': 'AGUADA', 'distance_km': 30, 'conductor': 'ACSR 50mm²'},
            {'from': 'AGUADA', 'to': 'LOS MENUCOS', 'distance_km': 30, 'conductor': 'ACSR 50mm²'}
        ]
        
        # Calcular impedancias por segmento
        segment_impedances = []
        for seg in segments:
            imp_per_km = impedances_per_km[seg['conductor']]
            r_total = imp_per_km['r'] * seg['distance_km']
            x_total = imp_per_km['x'] * seg['distance_km']
            z_total = (r_total**2 + x_total**2)**0.5
            
            segment_impedances.append({
                'from': seg['from'],
                'to': seg['to'],
                'distance_km': seg['distance_km'],
                'conductor': seg['conductor'],
                'R_ohm': round(r_total, 2),
                'X_ohm': round(x_total, 2),
                'Z_ohm': round(z_total, 2),
                'R_per_km': imp_per_km['r'],
                'X_per_km': imp_per_km['x']
            })
        
        # Calcular impedancias acumuladas hasta cada estación
        accumulated = {}
        r_acc = 0
        x_acc = 0
        
        stations = [
            ('COMALLO', 70),
            ('ONELLI', 120),
            ('JACOBACCI', 150),
            ('MAQUINCHAO', 210),
            ('AGUADA', 240),
            ('LOS MENUCOS', 270)
        ]
        
        for i, (station, total_dist) in enumerate(stations):
            # Sumar impedancias hasta esta estación
            for j in range(i + 1):
                r_acc += segment_impedances[j]['R_ohm']
                x_acc += segment_impedances[j]['X_ohm']
            
            z_acc = (r_acc**2 + x_acc**2)**0.5
            
            accumulated[station] = {
                'distance_km': total_dist,
                'R_ohm': round(r_acc, 2),
                'X_ohm': round(x_acc, 2),
                'Z_ohm': round(z_acc, 2)
            }
            
            # Reset para siguiente cálculo
            r_acc = 0
            x_acc = 0
        
        return {
            'segments': {seg['from'] + '-' + seg['to']: seg for seg in segment_impedances},
            'accumulated': accumulated,
            'source': 'Catálogo de conductores ACSR',
            'type': 'REFERENCIA',
            'note': 'Valores típicos a 50°C, 50 Hz'
        }

    # ------------------------------------------------------------------
    # Métodos PSFV / BESS — delegados a SolarBESSimulator
    # ------------------------------------------------------------------

    def simulate_psfv_only(self, station: str, power_mw: float, month: int = 6) -> DataResult:  # type: ignore[name-defined]
        """
        Simulate solar PV system without battery storage.
        
        Args:
            station: Name of the station/location
            power_mw: Installed solar power capacity in MW
            month: Month for simulation (1-12), defaults to 6 (June)
            
        Returns:
            DataResult: Contains simulation results with hourly profiles and metrics
        """
        return self.solar_bess_simulator.simulate_psfv_only(station, power_mw, month)

    def simulate_solar_with_bess(
        self,
        station: str,
        psfv_power_mw: float,
        bess_power_mw: float,
        bess_duration_h: float,
        month: int = 6,
        strategy: str = "time_shift",
        aggressive: bool = False,
    ) -> DataResult:  # type: ignore[name-defined]
        """
        Simulate solar PV system with battery energy storage system.
        
        Args:
            station: Name of the station/location
            psfv_power_mw: Installed solar power capacity in MW
            bess_power_mw: Battery power rating in MW
            bess_duration_h: Battery duration in hours (energy = power × duration)
            month: Month for simulation (1-12), defaults to 6 (June)
            strategy: BESS control strategy ("time_shift", "peak_limit", "smoothing", "firm_capacity")
            aggressive: Whether to use aggressive strategy parameters
            
        Returns:
            DataResult: Contains simulation results with solar, BESS, and net output profiles
        """
        return self.solar_bess_simulator.simulate_solar_with_bess(
            station,
            psfv_power_mw,
            bess_power_mw,
            bess_duration_h,
            month=month,
            strategy=strategy,
            use_aggressive_strategies=aggressive,
        )

    # ------------------------------------------------------------------
    # BESS Constants and Configurations - Centralized Access
    # ------------------------------------------------------------------
    
    def get_bess_constants(self) -> DataResult:  # type: ignore[name-defined]
        """Get centralized BESS constants"""
        return DataResult(
            data=dict(BESS_CONSTANTS),
            status=DataStatus.REAL,
            meta={"source": "constants.py"}
        )
    
    def get_bess_technologies(self) -> DataResult:  # type: ignore[name-defined]
        """Get available BESS technologies with their parameters"""
        return DataResult(
            data=dict(BESS_TECHNOLOGIES),
            status=DataStatus.REAL,
            meta={"source": "constants.py", "available_technologies": list(BESS_TECHNOLOGIES.keys())}
        )
    
    def get_bess_topologies(self) -> DataResult:  # type: ignore[name-defined]
        """Get available BESS topologies with their parameters"""
        return DataResult(
            data=dict(BESS_TOPOLOGIES),
            status=DataStatus.REAL,
            meta={"source": "constants.py", "available_topologies": list(BESS_TOPOLOGIES.keys())}
        )
    
    def get_bess_technology_params(self, technology: str) -> DataResult:  # type: ignore[name-defined]
        """Get parameters for a specific BESS technology"""
        if technology not in BESS_TECHNOLOGIES:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Technology '{technology}' not found", "available": list(BESS_TECHNOLOGIES.keys())}
            )
        
        return DataResult(
            data=dict(BESS_TECHNOLOGIES[technology]),
            status=DataStatus.REAL,
            meta={"technology": technology, "source": "constants.py"}
        )
    
    def get_bess_topology_params(self, topology: str) -> DataResult:  # type: ignore[name-defined]
        """Get parameters for a specific BESS topology"""
        if topology not in BESS_TOPOLOGIES:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Topology '{topology}' not found", "available": list(BESS_TOPOLOGIES.keys())}
            )
        
        return DataResult(
            data=dict(BESS_TOPOLOGIES[topology]),
            status=DataStatus.REAL,
            meta={"topology": topology, "source": "constants.py"}
        )
    
    def create_bess_model(self, power_mw: float, duration_hours: float,
                         technology: str = "modern_lfp", topology: str = "parallel_ac",
                         **kwargs) -> DataResult:  # type: ignore[name-defined]
        """Create a BESSModel instance using centralized constants"""
        try:
            # Import here to avoid circular imports
            import sys
            from pathlib import Path
            
            # Add project root to path if not present
            project_root = Path(__file__).parents[3]
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            from src.battery.bess_model import BESSModel
            
            # Validate technology and topology
            if technology not in BESS_TECHNOLOGIES:
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Technology '{technology}' not found", "available": list(BESS_TECHNOLOGIES.keys())}
                )
            
            if topology not in BESS_TOPOLOGIES:
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Topology '{topology}' not found", "available": list(BESS_TOPOLOGIES.keys())}
                )
            
            # Create BESSModel with centralized constants
            bess_model = BESSModel(
                power_mw=power_mw,
                duration_hours=duration_hours,
                technology=technology,
                topology=topology,
                **kwargs
            )
            
            return DataResult(
                data=bess_model,
                status=DataStatus.REAL,
                meta={
                    "power_mw": power_mw,
                    "duration_hours": duration_hours,
                    "technology": technology,
                    "topology": topology,
                    "source": "BESSModel with centralized constants"
                }
            )
            
        except ImportError as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"BESSModel not available: {e}"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to create BESSModel: {e}"}
            )

    # ------------------------------------------------------------------
    # PHASE 5: Network Analysis Parameters
    # ------------------------------------------------------------------
    
    def get_electrical_params(self, conductor_type: str = None) -> DataResult:  # type: ignore[name-defined]
        """Get electrical parameters for conductors"""
        from .constants import ELECTRICAL_PARAMS
        
        if conductor_type:
            conductor_types = ELECTRICAL_PARAMS.get("conductor_types", {})
            if conductor_type not in conductor_types:
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Conductor type '{conductor_type}' not found", 
                          "available": list(conductor_types.keys())}
                )
            
            return DataResult(
                data=dict(conductor_types[conductor_type]),
                status=DataStatus.REAL,
                meta={"conductor_type": conductor_type, "source": "constants.py"}
            )
        
        return DataResult(
            data=dict(ELECTRICAL_PARAMS),
            status=DataStatus.REAL,
            meta={"source": "constants.py", "phase": "5"}
        )
    
    def get_validation_limits(self) -> DataResult:  # type: ignore[name-defined]
        """Get validation limits for power system analysis"""
        from .constants import VALIDATION_LIMITS
        
        return DataResult(
            data=dict(VALIDATION_LIMITS),
            status=DataStatus.REAL,
            meta={"source": "constants.py", "phase": "5"}
        )
    
    def get_economic_params(self) -> DataResult:  # type: ignore[name-defined]
        """Get economic parameters for cost analysis"""
        from .constants import ECONOMIC_PARAMS
        
        return DataResult(
            data=dict(ECONOMIC_PARAMS),
            status=DataStatus.REAL,
            meta={"source": "constants.py", "phase": "5"}
        )
    
    def get_alternative_costs(self, alternative: str = None) -> DataResult:  # type: ignore[name-defined]
        """Get investment costs for different alternatives"""
        from .constants import ALTERNATIVE_COSTS
        
        if alternative:
            if alternative not in ALTERNATIVE_COSTS:
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Alternative '{alternative}' not found", 
                          "available": list(ALTERNATIVE_COSTS.keys())}
                )
            
            return DataResult(
                data=dict(ALTERNATIVE_COSTS[alternative]),
                status=DataStatus.REAL,
                meta={"alternative": alternative, "source": "constants.py"}
            )
        
        return DataResult(
            data=dict(ALTERNATIVE_COSTS),
            status=DataStatus.REAL,
            meta={"source": "constants.py", "phase": "5"}
        )
    
    def get_cache_config(self) -> DataResult:  # type: ignore[name-defined]
        """Get cache configuration for performance optimization"""
        from .constants import PHASE5_CACHE_CONFIG
        
        return DataResult(
            data=dict(PHASE5_CACHE_CONFIG),
            status=DataStatus.REAL,
            meta={"source": "constants.py", "phase": "5"}
        )
    
    def get_power_flow_config(self) -> DataResult:  # type: ignore[name-defined]
        """Get power flow calculation configuration"""
        electrical_params = self.get_electrical_params()
        if electrical_params.ok():
            pf_config = electrical_params.data.get("power_flow_config", {})
            return DataResult(
                data=dict(pf_config),
                status=DataStatus.REAL,
                meta={"source": "constants.py", "phase": "5"}
            )
        
        return DataResult(
            data=None,
            status=DataStatus.ERROR,
            meta={"error": "Could not retrieve power flow config"}
        )

    # ------------------------------------------------------------------
    # FASE 3: Advanced BESS Integration with BESSModel API
    # ------------------------------------------------------------------
    
    def simulate_bess_strategy(self, 
                              solar_profile: Union[np.ndarray, pd.Series, List[float]],
                              strategy: str,
                              power_mw: float = 2.0,
                              duration_hours: float = 4.0,
                              technology: str = "modern_lfp",
                              topology: str = "parallel_ac",
                              **strategy_params) -> DataResult:  # type: ignore[name-defined]
        """
        Unified BESS simulation using BESSModel.simulate_strategy().
        
        This is the main method for advanced BESS simulation that:
        1. Creates a BESSModel instance with specified parameters
        2. Runs the specified strategy on the solar profile
        3. Returns validated results with comprehensive metrics
        
        Args:
            solar_profile: Solar generation profile (MW) as array-like
            strategy: Strategy name (e.g., 'time_shift_aggressive', 'solar_smoothing')
            power_mw: BESS power rating in MW
            duration_hours: BESS duration in hours (energy = power × duration)
            technology: BESS technology ('standard', 'modern_lfp', 'premium')
            topology: BESS topology ('parallel_ac', 'series_dc', 'hybrid')
            **strategy_params: Strategy-specific parameters
            
        Returns:
            DataResult with simulation results including:
            - grid_power: Net power to grid (MW)
            - battery_power: BESS power (MW, negative=charge)
            - soc: State of charge profile
            - solar_curtailed: Curtailed solar energy (MW)
            - energy_losses: BESS losses (MW)
            - validation: Result validation metrics
            - total_cycles: Total BESS cycles
        """
        try:
            # Create BESSModel
            bess_result = self.create_bess_model(
                power_mw=power_mw,
                duration_hours=duration_hours,
                technology=technology,
                topology=topology,
                track_history=False,  # Disable for performance
                verbose=False  # Reduce logging for mass simulations
            )
            
            if bess_result.status == DataStatus.ERROR:
                return bess_result
            
            bess_model = bess_result.data
            
            # Convert solar profile to numpy array
            if isinstance(solar_profile, (list, pd.Series)):
                solar_array = np.array(solar_profile, dtype=np.float64)
            else:
                solar_array = np.asarray(solar_profile, dtype=np.float64)
            
            # Validate solar profile
            if len(solar_array) == 0:
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": "Empty solar profile"}
                )
            
            if np.any(solar_array < 0):
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": "Negative values in solar profile"}
                )
            
            # Run simulation using BESSModel
            results = bess_model.simulate_strategy(
                solar_profile=solar_array,
                strategy=strategy,
                **strategy_params
            )
            
            # Add BESS configuration to results
            results['bess_config'] = bess_model.get_configuration_summary()
            
            # Calculate additional metrics
            total_solar = np.sum(solar_array)
            total_grid = np.sum(results['grid_power'])
            total_losses = np.sum(results['energy_losses'])
            curtailment_ratio = np.sum(results['solar_curtailed']) / total_solar if total_solar > 0 else 0
            
            results['metrics'] = {
                'total_solar_mwh': total_solar,
                'total_grid_mwh': total_grid,
                'total_losses_mwh': total_losses,
                'energy_efficiency': (total_grid / total_solar) if total_solar > 0 else 0,
                'curtailment_ratio': curtailment_ratio,
                'loss_ratio': total_losses / total_solar if total_solar > 0 else 0,
                'strategy_used': strategy,
                'simulation_hours': len(solar_array)
            }
            
            return DataResult(
                data=results,
                status=DataStatus.REAL,
                meta={
                    "source": "BESSModel.simulate_strategy",
                    "strategy": strategy,
                    "bess_power_mw": power_mw,
                    "bess_duration_h": duration_hours,
                    "technology": technology,
                    "topology": topology,
                    "simulation_steps": len(solar_array)
                }
            )
            
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"BESS simulation failed: {str(e)}"}
            )
    
    def simulate_bess_dynamic_control(self,
                                    initial_soc: float,
                                    power_requests: Union[np.ndarray, List[float]],
                                    power_mw: float = 2.0,
                                    duration_hours: float = 4.0,
                                    technology: str = "modern_lfp",
                                    topology: str = "parallel_ac",
                                    dt: float = 0.25) -> DataResult:  # type: ignore[name-defined]
        """
        Dynamic BESS control simulation using BESSModel.next_state().
        
        This method simulates real-time BESS control with arbitrary power requests,
        useful for optimization algorithms and RL applications.
        
        Args:
            initial_soc: Starting state of charge (0-1)
            power_requests: Array of power requests (MW, negative=charge)
            power_mw: BESS power rating in MW
            duration_hours: BESS duration in hours
            technology: BESS technology
            topology: BESS topology
            dt: Time step in hours
            
        Returns:
            DataResult with step-by-step simulation results
        """
        try:
            # Create BESSModel
            bess_result = self.create_bess_model(
                power_mw=power_mw,
                duration_hours=duration_hours,
                technology=technology,
                topology=topology,
                track_history=False,
                verbose=False
            )
            
            if bess_result.status == DataStatus.ERROR:
                return bess_result
            
            bess_model = bess_result.data
            
            # Convert power requests to numpy array
            if isinstance(power_requests, list):
                power_array = np.array(power_requests, dtype=np.float64)
            else:
                power_array = np.asarray(power_requests, dtype=np.float64)
            
            n_steps = len(power_array)
            
            # Initialize result arrays
            soc_trajectory = np.zeros(n_steps + 1)
            actual_power = np.zeros(n_steps)
            losses = np.zeros(n_steps)
            
            # Set initial state
            soc_trajectory[0] = initial_soc
            current_soc = initial_soc
            
            # Simulate step by step
            for i in range(n_steps):
                new_soc, actual_p, loss = bess_model.next_state(
                    soc=current_soc,
                    p_req=power_array[i],
                    dt=dt
                )
                
                soc_trajectory[i + 1] = new_soc
                actual_power[i] = actual_p
                losses[i] = loss
                current_soc = new_soc
            
            # Calculate metrics
            total_energy_in = np.sum(np.maximum(0, -actual_power)) * dt
            total_energy_out = np.sum(np.maximum(0, actual_power)) * dt
            total_losses = np.sum(losses)
            roundtrip_efficiency = total_energy_out / total_energy_in if total_energy_in > 0 else 0
            
            results = {
                'soc_trajectory': soc_trajectory,
                'actual_power': actual_power,
                'requested_power': power_array,
                'losses': losses,
                'power_curtailment': power_array - actual_power,
                'bess_config': bess_model.get_configuration_summary(),
                'metrics': {
                    'total_energy_in_mwh': total_energy_in,
                    'total_energy_out_mwh': total_energy_out,
                    'total_losses_mwh': total_losses,
                    'realized_roundtrip_efficiency': roundtrip_efficiency,
                    'final_soc': soc_trajectory[-1],
                    'soc_range': soc_trajectory.max() - soc_trajectory.min(),
                    'timestep_hours': dt,
                    'simulation_duration_hours': n_steps * dt
                }
            }
            
            return DataResult(
                data=results,
                status=DataStatus.REAL,
                meta={
                    "source": "BESSModel.next_state",
                    "control_type": "dynamic",
                    "simulation_steps": n_steps,
                    "timestep_hours": dt,
                    "technology": technology,
                    "topology": topology
                }
            )
            
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Dynamic BESS control failed: {str(e)}"}
            )
    
    def optimize_bess_for_solar(self,
                               solar_profile: Union[np.ndarray, List[float]],
                               power_range: Tuple[float, float] = (0.5, 5.0),
                               duration_range: Tuple[float, float] = (2.0, 8.0),
                               strategy: str = "time_shift_aggressive",
                               technology: str = "modern_lfp",
                               optimization_metric: str = "energy_efficiency") -> DataResult:  # type: ignore[name-defined]
        """
        Optimize BESS sizing for a given solar profile using BESSModel.
        
        Searches for optimal power and duration combination by testing
        multiple configurations and evaluating performance metrics.
        
        Args:
            solar_profile: Solar generation profile (MW)
            power_range: (min_power, max_power) in MW
            duration_range: (min_duration, max_duration) in hours
            strategy: BESS strategy to evaluate
            technology: BESS technology
            optimization_metric: Metric to optimize ('energy_efficiency', 'curtailment_ratio', 'loss_ratio')
            
        Returns:
            DataResult with optimization results including best configuration
        """
        try:
            # Convert solar profile
            if isinstance(solar_profile, list):
                solar_array = np.array(solar_profile, dtype=np.float64)
            else:
                solar_array = np.asarray(solar_profile, dtype=np.float64)
            
            # Define search space
            power_values = np.linspace(power_range[0], power_range[1], 5)
            duration_values = np.linspace(duration_range[0], duration_range[1], 4)
            
            results = []
            best_value = -np.inf if optimization_metric in ['energy_efficiency'] else np.inf
            best_config = None
            
            for power_mw in power_values:
                for duration_h in duration_values:
                    # Run simulation
                    sim_result = self.simulate_bess_strategy(
                        solar_profile=solar_array,
                        strategy=strategy,
                        power_mw=power_mw,
                        duration_hours=duration_h,
                        technology=technology
                    )
                    
                    if sim_result.status == DataStatus.REAL:
                        metrics = sim_result.data['metrics']
                        
                        config_result = {
                            'power_mw': power_mw,
                            'duration_hours': duration_h,
                            'capacity_mwh': power_mw * duration_h,
                            'metrics': metrics,
                            'objective_value': metrics.get(optimization_metric, 0)
                        }
                        
                        results.append(config_result)
                        
                        # Check if this is the best configuration
                        objective_value = metrics.get(optimization_metric, 0)
                        if optimization_metric in ['energy_efficiency']:
                            is_better = objective_value > best_value
                        else:  # minimize for 'curtailment_ratio', 'loss_ratio'
                            is_better = objective_value < best_value
                        
                        if is_better:
                            best_value = objective_value
                            best_config = config_result.copy()
            
            if not results:
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": "No valid configurations found"}
                )
            
            optimization_results = {
                'best_configuration': best_config,
                'all_configurations': results,
                'optimization_settings': {
                    'strategy': strategy,
                    'technology': technology,
                    'metric': optimization_metric,
                    'power_range': power_range,
                    'duration_range': duration_range,
                    'total_configurations': len(results)
                },
                'summary': {
                    'best_power_mw': best_config['power_mw'] if best_config else None,
                    'best_duration_h': best_config['duration_hours'] if best_config else None,
                    'best_metric_value': best_value,
                    'improvement_vs_no_bess': self._calculate_improvement_vs_no_bess(
                        solar_array, best_config, optimization_metric
                    ) if best_config else 0
                }
            }
            
            return DataResult(
                data=optimization_results,
                status=DataStatus.REAL,
                meta={
                    "source": "BESSModel optimization",
                    "optimization_metric": optimization_metric,
                    "configurations_tested": len(results),
                    "strategy": strategy,
                    "technology": technology
                }
            )
            
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"BESS optimization failed: {str(e)}"}
            )
    
    def _calculate_improvement_vs_no_bess(self, solar_profile: np.ndarray, 
                                        best_config: Dict, metric: str) -> float:
        """Calculate improvement versus no BESS baseline."""
        try:
            # Simulate no BESS case
            no_bess_result = self.simulate_bess_strategy(
                solar_profile=solar_profile,
                strategy="no_bess",  # Pass-through strategy
                power_mw=0.1,  # Minimal BESS
                duration_hours=0.1
            )
            
            if no_bess_result.status == DataStatus.REAL and best_config:
                baseline_value = no_bess_result.data['metrics'].get(metric, 0)
                best_value = best_config['metrics'].get(metric, 0)
                
                if metric in ['energy_efficiency']:
                    # Higher is better
                    return (best_value - baseline_value) / baseline_value if baseline_value > 0 else 0
                else:
                    # Lower is better (curtailment, losses)
                    return (baseline_value - best_value) / baseline_value if baseline_value > 0 else 0
            
            return 0.0
            
        except:
            return 0.0
    
    def validate_bess_configuration(self,
                                  power_mw: float,
                                  duration_hours: float,
                                  technology: str = "modern_lfp",
                                  topology: str = "parallel_ac") -> DataResult:  # type: ignore[name-defined]
        """
        Validate BESS configuration and return detailed technical parameters.
        
        Args:
            power_mw: BESS power rating
            duration_hours: BESS duration
            technology: BESS technology
            topology: BESS topology
            
        Returns:
            DataResult with validation results and technical parameters
        """
        try:
            # Create BESS model for validation
            bess_result = self.create_bess_model(
                power_mw=power_mw,
                duration_hours=duration_hours,
                technology=technology,
                topology=topology
            )
            
            if bess_result.status == DataStatus.ERROR:
                return bess_result
            
            bess_model = bess_result.data
            
            # Get configuration summary
            config = bess_model.get_configuration_summary()
            
            # Perform validation checks
            validation_results = {
                'configuration_valid': True,
                'warnings': [],
                'recommendations': [],
                'technical_parameters': config,
                'performance_estimates': {}
            }
            
            # Check C-rate
            c_rate = config['c_rate']
            if c_rate > 2.0:
                validation_results['warnings'].append(f"High C-rate ({c_rate:.2f}) may reduce battery life")
            elif c_rate < 0.25:
                validation_results['warnings'].append(f"Low C-rate ({c_rate:.2f}) indicates oversized capacity")
            
            # Check duration
            if duration_hours < 1.0:
                validation_results['warnings'].append("Short duration (<1h) limits energy arbitrage capability")
            elif duration_hours > 8.0:
                validation_results['warnings'].append("Long duration (>8h) may not be economically justified")
            
            # Performance estimates for typical solar profile
            typical_solar = np.concatenate([
                np.zeros(6),  # Night
                np.linspace(0, power_mw * 0.8, 6),  # Morning ramp
                np.full(6, power_mw * 0.8),  # Peak
                np.linspace(power_mw * 0.8, 0, 6)  # Evening ramp
            ])
            
            # Quick simulation for performance estimate
            perf_result = self.simulate_bess_strategy(
                solar_profile=typical_solar,
                strategy="time_shift_aggressive",
                power_mw=power_mw,
                duration_hours=duration_hours,
                technology=technology,
                topology=topology
            )
            
            if perf_result.status == DataStatus.REAL:
                validation_results['performance_estimates'] = {
                    'daily_efficiency': perf_result.data['metrics']['energy_efficiency'],
                    'daily_cycles': perf_result.data.get('daily_cycles', 0),
                    'daily_losses_mwh': perf_result.data['metrics']['total_losses_mwh'],
                    'utilization_factor': perf_result.data['metrics']['total_losses_mwh'] / (power_mw * 24) if power_mw > 0 else 0
                }
            
            return DataResult(
                data=validation_results,
                status=DataStatus.REAL,
                meta={
                    "source": "BESSModel validation",
                    "power_mw": power_mw,
                    "duration_hours": duration_hours,
                    "technology": technology,
                    "topology": topology
                }
            )
            
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"BESS validation failed: {str(e)}"}
            )

    # ------------------------------------------------------------------
    # FASE 3: Comprehensive Metrics Methods
    # ------------------------------------------------------------------
    
    def get_comprehensive_summary(self) -> DataResult:
        """Get comprehensive data processing summary."""
        try:
            summary_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "summary.json"
            
            if not summary_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Summary file not found: {summary_file}"}
                )
            
            with open(summary_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(summary_file), "type": "comprehensive_summary"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load comprehensive summary: {str(e)}"}
            )
    
    def get_enhanced_quality_metrics(self) -> DataResult:
        """Get enhanced quality metrics with detailed analysis."""
        try:
            quality_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "quality_metrics_enhanced.json"
            
            if not quality_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Quality metrics file not found: {quality_file}"}
                )
            
            with open(quality_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(quality_file), "type": "enhanced_quality_metrics"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load enhanced quality metrics: {str(e)}"}
            )
    
    def get_temporal_patterns_full(self) -> DataResult:
        """Get full temporal patterns analysis."""
        try:
            temporal_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "temporal_patterns_full.json"
            
            if not temporal_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Temporal patterns file not found: {temporal_file}"}
                )
            
            with open(temporal_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(temporal_file), "type": "temporal_patterns_full"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load temporal patterns: {str(e)}"}
            )
    
    def get_correlations(self) -> DataResult:
        """Get correlation matrices between stations."""
        try:
            corr_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "correlations.json"
            
            if not corr_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Correlations file not found: {corr_file}"}
                )
            
            with open(corr_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(corr_file), "type": "correlations"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load correlations: {str(e)}"}
            )
    
    def get_hourly_voltage_analysis(self) -> DataResult:
        """Get hourly voltage analysis for all stations."""
        try:
            hourly_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "hourly_analysis.json"
            
            if not hourly_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Hourly analysis file not found: {hourly_file}"}
                )
            
            with open(hourly_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(hourly_file), "type": "hourly_voltage_analysis"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load hourly voltage analysis: {str(e)}"}
            )
    
    def get_demand_voltage_correlation(self) -> DataResult:
        """Get demand-voltage correlation analysis (dV/dP sensitivity)."""
        try:
            pv_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "pv_correlation.json"
            
            if not pv_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"P-V correlation file not found: {pv_file}"}
                )
            
            with open(pv_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(pv_file), "type": "demand_voltage_correlation"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load demand-voltage correlation: {str(e)}"}
            )
    
    def get_critical_events_analysis(self) -> DataResult:
        """Get critical events analysis (low voltage events)."""
        try:
            events_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "critical_events.json"
            
            if not events_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Critical events file not found: {events_file}"}
                )
            
            with open(events_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(events_file), "type": "critical_events_analysis"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load critical events analysis: {str(e)}"}
            )
    
    def get_demand_ramps_analysis(self) -> DataResult:
        """Get demand ramp rate analysis."""
        try:
            ramps_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "demand_ramps.json"
            
            if not ramps_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Demand ramps file not found: {ramps_file}"}
                )
            
            with open(ramps_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(ramps_file), "type": "demand_ramps_analysis"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load demand ramps analysis: {str(e)}"}
            )
    
    def get_load_duration_curves(self) -> DataResult:
        """Get load duration curves for all stations."""
        try:
            duration_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "duration_curves.json"
            
            if not duration_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Duration curves file not found: {duration_file}"}
                )
            
            with open(duration_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(duration_file), "type": "load_duration_curves"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load duration curves: {str(e)}"}
            )
    
    def get_typical_days_profiles(self) -> DataResult:
        """Get typical day profiles for all stations."""
        try:
            typical_file = self.project_root / "data" / "processed" / "comprehensive_metrics" / "typical_days.json"
            
            if not typical_file.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"Typical days file not found: {typical_file}"}
                )
            
            with open(typical_file, 'r') as f:
                data = json.load(f)
            
            return DataResult(
                data=data,
                status=DataStatus.REAL,
                meta={"source": str(typical_file), "type": "typical_days_profiles"}
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to load typical days profiles: {str(e)}"}
            )
    
    def get_ml_features_info(self) -> DataResult:
        """Get information about ML features generated for each station."""
        try:
            ml_features_dir = self.project_root / "data" / "processed" / "comprehensive_metrics" / "ml_features"
            
            if not ml_features_dir.exists():
                return DataResult(
                    data=None,
                    status=DataStatus.ERROR,
                    meta={"error": f"ML features directory not found: {ml_features_dir}"}
                )
            
            # List all parquet files
            feature_files = list(ml_features_dir.glob("*_features.parquet"))
            
            info = {
                "available_stations": [],
                "feature_files": {},
                "scaler_available": (ml_features_dir / "feature_scaler.pkl").exists()
            }
            
            for file in feature_files:
                station_name = file.stem.replace("_features", "").title()
                info["available_stations"].append(station_name)
                info["feature_files"][station_name] = str(file)
            
            return DataResult(
                data=info,
                status=DataStatus.REAL,
                meta={
                    "source": str(ml_features_dir),
                    "type": "ml_features_info",
                    "total_stations": len(info["available_stations"])
                }
            )
        except Exception as e:
            return DataResult(
                data=None,
                status=DataStatus.ERROR,
                meta={"error": f"Failed to get ML features info: {str(e)}"}
            )

    # ------------------------------------------------------------------
    # Métricas y utilidades
    # ------------------------------------------------------------------

    def get_perf_summary(self) -> Dict[str, Any]:
        if not self._perf:
            return {}
        ok_ops = [p for p in self._perf if p["success"]]
        return {
            "total": len(self._perf),
            "success_rate": len(ok_ops) / len(self._perf),
            "avg_time": np.mean([p["execution_time"] for p in ok_ops]) if ok_ops else 0.0,
            "slowest": max(self._perf, key=lambda p: p["execution_time"])["operation"],
        }

    def clear_caches(self) -> None:
        """Limpia caches y estadísticas."""
        self.data_loader.clear_retry_states()
        self.data_analytics.clear_performance_metrics()
        self.solar_bess_simulator.clear_cache()
        self._perf.clear()
        logger.info("Caches y métricas limpiadas.")

    # ------------------------------------------------------------------
    # APIResponse wrappers rápidos (ejemplo)
    # ------------------------------------------------------------------

    def get_system_status(self) -> APIResponse:  # type: ignore[name-defined]
        status_data = {
            "overall": self.data_status["overall"].value,
            "components": {k: v.value for k, v in self.data_status.items()},
            "perf": self.get_perf_summary(),
        }
        return APIResponse(success=True, data=status_data, message="Status OK", errors=[], meta={}, timestamp=datetime.now().isoformat())

    def reload_data(self) -> APIResponse:  # type: ignore[name-defined]
        try:
            self._load_all_data()
            return APIResponse(success=True, data={"reloaded": True}, message="Reload complete", errors=[], meta={}, timestamp=datetime.now().isoformat())
        except Exception as exc:  # pragma: no cover
            return APIResponse(success=False, data=None, message="Reload failed", errors=[str(exc)], meta={}, timestamp=datetime.now().isoformat())

    # ------------------------------------------------------------------
    # LEGACY COMPATIBILITY METHODS - Heredados de DataManagerLegacyCompatibility
    # ------------------------------------------------------------------
    # Los métodos de compatibilidad están ahora en data_manager_legacy_compatibility.py
    # para mantener el código organizado y evitar que este archivo crezca demasiado.


# ─────────────────────────────────────────────────────────────
# Funciones helper para obtener / resetear el singleton
# ─────────────────────────────────────────────────────────────

_singleton_lock = threading.Lock()
_singleton_instance: Optional[DataManagerV2] = None


def get_data_manager(config: Optional[DataManagerConfig] = None) -> DataManagerV2:  # type: ignore[name-defined]
    global _singleton_instance
    if _singleton_instance is None:
        with _singleton_lock:
            if _singleton_instance is None:
                _singleton_instance = DataManagerV2(config)
    return _singleton_instance


def reset_data_manager() -> None:
    global _singleton_instance
    with _singleton_lock:
        _singleton_instance = None
