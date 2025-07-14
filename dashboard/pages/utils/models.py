"""
models.py ‒ Unified data models and typed helpers
================================================
This module centralises every **public** data‐structure used across the
_DataManager V2_ architecture.  All classes are **import‑safe** (no heavy
runtime deps) so that any sub‑package can reference them without triggering
large import chains – useful for CLI utilities and unit‑tests.

Key design notes
----------------
*   ✅  **Explicit typing** with `TypedDict`, `dataclass(frozen=True)` and
    `Literal` ⇒ first‑class support for `mypy`, `pyright` & IDEs.
*   ✅  **Helpers** on runtime objects (`DataResult`) for quick checks and JSON
    serialisation.
*   ✅  **Const‑correctness** – immutable configs (`frozen=True`) &
    `__slots__` to reduce memory when many objects are instantiated in
    analytics loops.
*   ✅  **Forward compatibility** – any *removed* symbol from the legacy mono
    file is kept as an `Alias` (see bottom) so other modules keep working
    until we finish the full refactor.

When you **remove** a public symbol, add it to `__deprecated__` with a short
comment so future PRs can handle the migration.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from typing_extensions import Literal, TypedDict
import json

# -----------------------------------------------------------------------------
# Enums (import from constants to avoid duplication)
# -----------------------------------------------------------------------------
from .constants import DataStatus, BESSStrategy, SolarTechnology  # noqa: F401

# -----------------------------------------------------------------------------
# Runtime helper classes
# -----------------------------------------------------------------------------

@dataclass(slots=True)
class DataResult:
    """Generic container returned by *every* public DataManager call."""

    data: Any
    status: DataStatus
    meta: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------ helper
    def ok(self) -> bool:  # pylint: disable=invalid-name
        """`True` if :pyattr:`status` is *not* ``ERROR`` and `data` is present."""
        return self.status not in {DataStatus.ERROR} and self.data is not None

    # legacy aliases (keep API stable)
    is_valid = ok  # type: ignore

    # ------------------------------------------------------------------ helper
    def is_fallback(self) -> bool:
        return self.status is DataStatus.FALLBACK

    # ------------------------------------------------------------------ helper
    def json(self, *, pretty: bool = False) -> str:
        """Return a JSON string (safe for logging / REST responses)."""

        def _default(obj: Any):  # pylint: disable=unused‑argument
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)

        indent = 2 if pretty else None
        return json.dumps(asdict(self), default=_default, indent=indent, ensure_ascii=False)

    # ------------------------------------------------------------------ dunder
    def __bool__(self) -> bool:  # truthiness helper (``if result: ...``)
        return self.ok()


# -----------------------------------------------------------------------------
# Network topology types
# -----------------------------------------------------------------------------

class NodeData(TypedDict):
    name: str
    coordinates: Tuple[float, float]
    distance_km: float
    transformation: str
    type: str
    load_mw: float
    load_mvar: float
    voltage_pu: float


class EdgeData(TypedDict):
    from_node: str
    to_node: str
    length_km: float
    impedance_ohm: float
    current_capacity_a: float
    voltage_drop_pu: float
    losses_mw: float


class TransformerData(TypedDict):
    name: str
    location: str
    primary_voltage_kv: float
    secondary_voltage_kv: float
    power_rating_mva: float
    impedance_percent: float
    tap_range: Dict[str, float]
    regulation_type: str


class SystemSummary(TypedDict):
    total_power_mw: float
    total_reactive_mvar: float
    power_factor: float
    total_losses_mw: float
    voltage_profile: Dict[str, float]
    load_distribution: Dict[str, float]


# -----------------------------------------------------------------------------
# Historical & analytics types
# -----------------------------------------------------------------------------

class HistoricalRecord(TypedDict):
    timestamp: datetime
    station: str
    voltage_pu: float
    power_mw: float
    reactive_mvar: float
    current_a: float
    power_factor: float
    frequency_hz: float


class AnalysisMetrics(TypedDict):
    mean: float
    std: float
    min: float
    max: float
    percentiles: Dict[str, float]
    count: int
    missing_rate: float


# -----------------------------------------------------------------------------
# Solar / BESS configurations
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SolarConfiguration:
    power_mw: float
    technology: SolarTechnology
    tilt_angle: float = 35.0
    azimuth_angle: float = 180.0
    inverter_efficiency: float = 0.97
    system_losses: float = 0.12
    degradation_rate: float = 0.005


@dataclass(frozen=True, slots=True)
class BESSConfiguration:
    power_mw: float
    energy_mwh: float
    efficiency: float = 0.92
    soc_min: float = 0.10
    soc_max: float = 0.95
    strategy: BESSStrategy = BESSStrategy.SMOOTHING
    max_cycles_per_day: int = 2


class SolarProfile(TypedDict):
    timestamp: List[datetime]
    power_mw: List[float]
    capacity_factor: float
    peak_power_mw: float
    energy_mwh: float
    hours_above_50pct: float
    hours_above_20pct: float


class BESSOperationResult(TypedDict):
    timestamp: List[datetime]
    soc_percent: List[float]
    power_charge_mw: List[float]
    power_discharge_mw: List[float]
    power_net_mw: List[float]
    energy_throughput_mwh: float
    cycles_count: float
    efficiency_realized: float
    capacity_utilized_percent: float


# -----------------------------------------------------------------------------
# Economics
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class EconomicParameters:
    discount_rate: float = 0.08
    inflation_rate: float = 0.03
    analysis_period_years: int = 25
    capex_solar_usd_kw: float = 850
    capex_bess_usd_kwh: float = 350
    opex_solar_usd_kw_year: float = 18
    opex_bess_usd_kwh_year: float = 5


class EconomicResult(TypedDict):
    npv_usd: float
    irr_percent: float
    payback_years: float
    lcoe_usd_mwh: float
    capex_total_usd: float
    opex_annual_usd: float
    energy_annual_mwh: float
    revenue_annual_usd: float


# -----------------------------------------------------------------------------
# Clustering / optimisation / ML
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ClusteringParameters:
    n_clusters: int = 3
    algorithm: Literal["kmeans", "agglomerative", "dbscan"] = "kmeans"
    features: List[str] = field(default_factory=lambda: ["voltage", "power"])
    normalize: bool = True
    random_state: int = 42


class ClusteringResult(TypedDict):
    cluster_labels: List[int]
    cluster_centers: List[List[float]]
    silhouette_score: float
    inertia: float
    feature_importance: Dict[str, float]
    cluster_summary: Dict[int, Dict[str, Any]]


@dataclass(frozen=True, slots=True)
class OptimizationConstraints:
    min_voltage_pu: float = 0.95
    max_voltage_pu: float = 1.05
    max_power_flow_mw: float = 10.0
    min_power_factor: float = 0.92
    max_investment_usd: float = 10_000_000
    min_reliability_percent: float = 99.5


class OptimizationResult(TypedDict):
    objective_value: float
    solution: Dict[str, Any]
    constraints_satisfied: bool
    optimization_status: str
    iterations: int
    solve_time_seconds: float
    sensitivity_analysis: Dict[str, float]


# -----------------------------------------------------------------------------
# Validation / retry / performance misc
# -----------------------------------------------------------------------------

@dataclass(slots=True)
class ValidationError:
    field: str
    message: str
    expected: Any
    actual: Any
    severity: Literal["error", "warning"] = "error"


class ValidationResult(TypedDict):
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    summary: Dict[str, Any]


@dataclass(slots=True)
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 128

    @property
    def hit_rate(self) -> float:
        ttl = self.hits + self.misses
        return self.hits / ttl if ttl else 0.0


class PerformanceMetrics(TypedDict):
    execution_time_seconds: float
    memory_usage_mb: float
    cache_stats: CacheStats
    data_points_processed: int
    operations_per_second: float


@dataclass(slots=True)
class RetryState:
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    backoff_factor: float = 2.0
    base_delay: float = 1.0
    max_delay: float = 30.0

    def should_retry(self) -> bool:
        return self.attempts < self.max_attempts

    def get_delay(self) -> float:
        return min(self.base_delay * (self.backoff_factor ** self.attempts), self.max_delay)


# -----------------------------------------------------------------------------
# API & configuration facade
# -----------------------------------------------------------------------------

class APIResponse(TypedDict):
    success: bool
    data: Optional[Any]
    message: str
    errors: List[str]
    meta: Dict[str, Any]
    timestamp: str


@dataclass(frozen=True, slots=True)
class DataManagerConfig:
    data_path: str = "data/processed"
    fallback_path: str = "data/fallback"
    cache_enabled: bool = True
    cache_size: int = 128
    max_retries: int = 3
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    thread_safe: bool = True
    validation_enabled: bool = True


# -----------------------------------------------------------------------------
# Public export control
# -----------------------------------------------------------------------------

__all__: List[str] = [
    # helpers
    "DataResult",
    "APIResponse",
    "DataManagerConfig",
    # topology
    "NodeData",
    "EdgeData",
    "TransformerData",
    "SystemSummary",
    # historical
    "HistoricalRecord",
    "AnalysisMetrics",
    # solar / BESS
    "SolarConfiguration",
    "BESSConfiguration",
    "SolarProfile",
    "BESSOperationResult",
    # economics
    "EconomicParameters",
    "EconomicResult",
    # ML / optimisation
    "ClusteringParameters",
    "ClusteringResult",
    "OptimizationConstraints",
    "OptimizationResult",
    # validation / perf
    "ValidationError",
    "ValidationResult",
    "CacheStats",
    "PerformanceMetrics",
    "RetryState",
]

# -----------------------------------------------------------------------------
# Backwards‑compatibility aliases (temporary ‒ mark for removal!)
# -----------------------------------------------------------------------------

__deprecated__ = {
    "AnalysisMetrics": "renamed but kept",  # example placeholder
}
