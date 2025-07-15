"""data_analytics.py
Data Analytics Module for DataManager V2
=================================================
Core responsibilities
---------------------
* Estadística descriptiva y temporal de mediciones
* Cálculo de correlaciones y rampas de demanda
* Detección de eventos críticos de tensión

Principios de diseño
--------------------
1. **Only analytics — no I/O.**  Cualquier carga/validación de datos vive en
   *data_loaders.py*.  Esta clase espera *DataFrames* ya formados.
2. **Funciones puras cuando sea posible.**  Facilita test unitarios.
3. **Decorador de cronometraje** incluido para profiling liviano – se puede
   desactivar vía `DataAnalytics.ENABLE_PROFILING`.
4. **Caching LRU** opcional (ver `CACHE_CONFIG`).  Mantengo helpers legacy en
   variables _LEGACY_* para migración — **TODO‑remove‑v3**.

Notas de compatibilidad
-----------------------
* Se mantiene el nombre **DataAnalytics** y la signatura pública de métodos
  para no romper imports existentes.
* Ex‑constants renombrados se re‑exportan acá con alias
  (**TODO‑remove‑v3**).  Ej.: `MIN_SAMPLES = ANALYSIS_CONSTANTS["MIN_SAMPLES_CORRELATION"]`.
* He añadido la importación explícita de `DataStatus` (faltaba).
"""

from __future__ import annotations

import logging
import warnings
from datetime import datetime
from functools import lru_cache, wraps
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from .constants import (
    ANALYSIS_CONSTANTS,
    CACHE_CONFIG,
    TIME_CONSTANTS,
    DataStatus,  # <- importado, faltaba en v1
)
from .models import CacheStats, DataResult, PerformanceMetrics

# ---------------------------------------------------------------------------
# Compat / legacy aliases (TODO‑remove‑v3)
# ---------------------------------------------------------------------------
MIN_SAMPLES = ANALYSIS_CONSTANTS["MIN_SAMPLES_CORRELATION"]  # TODO‑remove‑v3
CRITICAL_VOLTAGE = ANALYSIS_CONSTANTS["CRITICAL_VOLTAGE_PU"]  # TODO‑remove‑v3

__all__ = [
    "DataAnalytics",
]

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=FutureWarning)


class DataAnalytics:
    """All *in‑memory* analytics for the Línea Sur dashboard.

    Parameters
    ----------
    enable_profiling : bool, default ``True``
        If *False*, the timing decorator becomes a no‑op.
    """

    ENABLE_PROFILING: bool = True

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def __init__(self, enable_profiling: bool | None = None):
        self.ENABLE_PROFILING = self.ENABLE_PROFILING if enable_profiling is None else enable_profiling
        self.cache_stats = CacheStats(max_size=CACHE_CONFIG["CACHE_SIZE"])
        self._perf: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Internal: timing decorator
    # ------------------------------------------------------------------
    def _time_operation(self, name: str):
        """Return decorator that times *func* and logs slow calls."""

        def decorator(func):
            if not self.ENABLE_PROFILING:
                return func

            @wraps(func)
            def wrapper(*args, **kwargs):
                start = datetime.now()
                mem_before = self._get_mem()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = (datetime.now() - start).total_seconds()
                    mem_after = self._get_mem()
                    self._perf.append(
                        {
                            "operation": name,
                            "execution_time": elapsed,
                            "memory_delta": mem_after - mem_before,
                            "timestamp": start,
                        }
                    )
                    if elapsed > 1.0:
                        logger.warning("Slow operation %s: %.2fs", name, elapsed)

            return wrapper

        return decorator

    # ------------------------------------------------------------------
    # Mem util
    # ------------------------------------------------------------------
    @staticmethod
    def _get_mem() -> float:
        """Return RSS in MB (0 if *psutil* not present)."""
        try:
            import psutil  # type: ignore

            return psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    # ------------------------------------------------------------------
    # Caching helper (placeholder)
    # ------------------------------------------------------------------
    @lru_cache(maxsize=128)  # Default cache size
    def _cached_groupby_analysis(self, data_hash: str, group_by: str, value_col: str) -> dict[str, Any]:
        """Cached analysis helper - placeholder for future implementation."""
        # TODO: Implement actual caching logic when needed
        # For now, return empty dict as cache mechanism is not fully utilized
        return {
            "data_hash": data_hash,
            "group_by": group_by,
            "value_col": value_col,
            "cached": True
        }

    # ==================================================================
    # PUBLIC API METHODS
    # ==================================================================

    def get_hourly_voltage_analysis(self, df: pd.DataFrame) -> DataResult:
        """Create per‑hour voltage stats per station."""
        if df is None or df.empty:
            return DataResult(data=None, status=DataStatus.ERROR, meta={"error": "No data provided"})

        df = df.copy()
        if "hour" not in df.columns:
            df["hour"] = df["timestamp"].dt.hour

        result: Dict[str, Dict[int, Dict[str, float | int]]] = {}
        for station, grp in df.groupby("station"):
            stats_for_station: Dict[int, Dict[str, float | int]] = {}
            for hr in range(TIME_CONSTANTS["HOURS_PER_DAY"]):
                vals = grp.loc[grp["hour"] == hr, "voltage"].to_numpy()
                if vals.size:
                    stats_for_station[hr] = {
                        "mean": float(vals.mean()),
                        "std": float(vals.std()),
                        "min": float(vals.min()),
                        "max": float(vals.max()),
                        "count": int(vals.size),
                        "below_limit": int((vals < CRITICAL_VOLTAGE).sum()),
                    }
                else:
                    stats_for_station[hr] = {
                        "mean": 0.0,
                        "std": 0.0,
                        "min": 0.0,
                        "max": 0.0,
                        "count": 0,
                        "below_limit": 0,
                    }
            result[station] = stats_for_station

        return DataResult(data=result, status=DataStatus.REAL, meta={"analysis_type": "hourly_voltage"})

    
    def get_demand_voltage_correlation(self, df: pd.DataFrame) -> DataResult:
        """Correlation + dV/dP sensitivity per station (with R²)."""
        if df is None or df.empty:
            return DataResult(data=None, status=DataStatus.ERROR, meta={"error": "No data provided"})

        out: Dict[str, Dict[str, Any]] = {}
        for station, grp in df.groupby("station"):
            n = len(grp)
            if n < MIN_SAMPLES:
                out[station] = {
                    "quality": "insufficient_samples",
                    "sample_size": n,
                    "correlation": 0.0,
                    "sensitivity_pu_per_mw": 0.0,
                    "r_squared": 0.0,
                    "intercept": 0.0,
                }
                continue

            corr = grp["power"].corr(grp["voltage"])
            X = grp[["power"]].to_numpy()
            y = grp["voltage"].to_numpy()
            mask = np.isfinite(X).flatten() & np.isfinite(y)
            if mask.sum() < 2:
                out[station] = {
                    "quality": "poor",
                    "sample_size": int(mask.sum()),
                    "correlation": float(corr),
                    "sensitivity_pu_per_mw": 0.0,
                    "r_squared": 0.0,
                    "intercept": 0.0,
                }
                continue

            model = LinearRegression().fit(X[mask], y[mask])
            r2 = r2_score(y[mask], model.predict(X[mask]))
            out[station] = {
                "correlation": float(corr),
                "sensitivity_pu_per_mw": float(model.coef_[0]),
                "r_squared": float(r2),
                "intercept": float(model.intercept_),
                "sample_size": int(mask.sum()),
                "quality": "good" if r2 > 0.7 else "moderate" if r2 > 0.3 else "poor",
            }

        return DataResult(data=out, status=DataStatus.REAL, meta={"analysis_type": "demand_voltage_correlation"})

    
    def get_critical_events_analysis(self, df: pd.DataFrame) -> DataResult:
        """Detect V < threshold events >= min duration."""
        if df is None or df.empty:
            return DataResult(data=None, status=DataStatus.ERROR, meta={"error": "No data provided"})

        events: List[Dict[str, Any]] = []
        for station, grp in df.groupby("station"):
            grp = grp.sort_values("timestamp")
            events.extend(self._find_continuous_events(grp, station, CRITICAL_VOLTAGE))

        durations = [e["duration_minutes"] for e in events]
        meta_summary = {
            "total_events": len(events),
            "total_duration_hours": sum(durations) / 60 if durations else 0,
            "max_duration_min": max(durations) if durations else 0,
        }
        return DataResult(data={"events": events}, status=DataStatus.REAL, meta=meta_summary)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _find_continuous_events(self, df: pd.DataFrame, station: str, threshold: float) -> List[Dict[str, Any]]:
        """Vectorised event detection (handles open‑ended events)."""
        v = df["voltage"].to_numpy()
        t = df["timestamp"].to_numpy()
        below = v < threshold
        if not below.any():
            return []

        trans = np.diff(below.astype(int))
        starts = np.where(trans == 1)[0] + 1
        ends = np.where(trans == -1)[0] + 1
        if below[0]:
            starts = np.insert(starts, 0, 0)
        if below[-1]:
            ends = np.append(ends, below.size)

        evts: List[Dict[str, Any]] = []
        for s, e in zip(starts, ends):
            dur = (t[e - 1] - t[s]).astype("timedelta64[m]").astype(int)
            if dur >= ANALYSIS_CONSTANTS["CRITICAL_EVENT_MIN_DURATION"]:
                evts.append(
                    {
                        "station": station,
                        "start_time": t[s],
                        "end_time": t[e - 1],
                        "duration_minutes": dur,
                        "min_voltage": float(v[s:e].min()),
                        "avg_voltage": float(v[s:e].mean()),
                    }
                )
        return evts

    
    def get_demand_ramps_analysis(self, df: pd.DataFrame) -> DataResult:
        """Compute MW/h ramps per station."""
        if df is None or df.empty:
            return DataResult(data=None, status=DataStatus.ERROR, meta={"error": "No data provided"})

        ramps_out: Dict[str, Dict[str, Any]] = {}
        for station, grp in df.groupby("station"):
            grp = grp.sort_values("timestamp")
            if len(grp) < 2:
                continue

            # Compute deltas
            p = grp["power"].to_numpy()
            t = grp["timestamp"].astype("datetime64[h]").to_numpy()
            dp = np.diff(p)
            dt = np.diff(t).astype(float)  # hours
            valid = dt > 0
            if not valid.any():
                continue

            ramp = dp[valid] / dt[valid]
            if ramp.size == 0:
                continue

            thresh = 0.1  # MW/h significance
            sig = np.abs(ramp) > thresh
            ramps_out[station] = {
                "max_up_ramp_mw_per_h": float(ramp.max()),
                "max_down_ramp_mw_per_h": float(ramp.min()),
                "avg_abs_ramp_mw_per_h": float(np.abs(ramp).mean()),
                "std_ramp": float(ramp.std()),
                "ramp_events_count": int(sig.sum()),
                "total_samples": int(ramp.size),
            }

        return DataResult(data=ramps_out, status=DataStatus.REAL, meta={"analysis_type": "demand_ramps"})

    
    def get_load_duration_curves(self, df: pd.DataFrame) -> DataResult:
        """Generate load duration curves per station."""
        if df is None or df.empty:
            return DataResult(data=None, status=DataStatus.ERROR, meta={"error": "No data provided"})

        curves: Dict[str, Dict[str, Any]] = {}
        percentiles = np.array([1, 5, 10, 25, 50, 75, 90, 95, 99])
        for station, grp in df.groupby("station"):
            power = grp["power"].to_numpy()
            if power.size == 0:
                continue
            sorted_power = np.sort(power)[::-1]
            pct_vals = np.percentile(sorted_power, percentiles)
            curves[station] = {
                "percentiles": {f"p{p}": float(v) for p, v in zip(percentiles, pct_vals)},
                "max_power_mw": float(sorted_power[0]),
                "avg_power_mw": float(sorted_power.mean()),
                "capacity_factor": float(sorted_power.mean() / sorted_power[0]) if sorted_power[0] else 0.0,
                "hours": int(sorted_power.size),
            }

        return DataResult(data=curves, status=DataStatus.REAL, meta={"analysis_type": "load_duration_curves"})

    # ------------------------------------------------------------------
    # Performance helpers
    # ------------------------------------------------------------------
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Return aggregated performance metrics."""
        if not self._perf:
            return PerformanceMetrics(
                execution_time_seconds=0.0,
                memory_usage_mb=0.0,
                cache_stats=self.cache_stats,
                data_points_processed=0,
                operations_per_second=0.0,
            )

        total_time = sum(p["execution_time"] for p in self._perf)
        total_mem = sum(p["memory_delta"] for p in self._perf)
        ops = len(self._perf)
        return PerformanceMetrics(
            execution_time_seconds=total_time,
            memory_usage_mb=total_mem,
            cache_stats=self.cache_stats,
            data_points_processed=ops,
            operations_per_second=ops / total_time if total_time else 0.0,
        )

    def clear_performance_metrics(self) -> None:
        """Reset stored performance metrics."""
        self._perf.clear()
        logger.info("Performance metrics cleared")
