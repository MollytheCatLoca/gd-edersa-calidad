"""
constants.py
Centralized Constants and Enumerations for the DataManager ecosystem (V2)

This module replaces the previous scattered constant definitions
and enforces **immutability**, **typed access**, and **back‑compatibility**.

────────────────────────────────────────────────────────────────────────
⚠️  IMPORTANT FOR THE TRANSITION
────────────────────────────────────────────────────────────────────────
* All PUBLIC names from the original `constants.py` are still exported.
* Names that are DEPRECATED remain as aliases and are marked with
  `# TODO‑remove‑v3` so you can grep the code‑base later.
* If you delete or rename a constant **add the old name here** pointing
  to the new one and mark it.

Example:
```python
# legacy usage in code
from constants import SOLAR_CONSTANTS
```
continues to work, but new code should import `SOLAR`.

────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Sequence, Tuple, TypedDict, Literal

# ────────────────────────────────────────────────────────────────────
#  ENUMERATIONS
# ────────────────────────────────────────────────────────────────────


class DataStatus(str, Enum):
    """Lifecycle status for each dataset."""

    REAL = "real"
    PARTIAL = "partial"
    FALLBACK = "fallback"
    ERROR = "error"


class BESSStrategy(str, Enum):
    """Enumerates accepted battery‑control strategies."""

    SMOOTHING = "smoothing"
    PEAK_LIMIT = "peak_limit"  # was `cap_shaving`
    TIME_SHIFT = "time_shift"  # was `night_shift`
    FIRM_CAPACITY = "firm_capacity"  # was `firm_delivery_window`
    
    # V1 Strategy aliases (minimize BESS usage)
    CAP_SHAVING = "cap_shaving"
    FLAT_DAY = "flat_day"
    NIGHT_SHIFT = "night_shift"
    RAMP_LIMIT = "ramp_limit"
    
    # V2 Strategy aliases (force BESS usage for demonstration)
    SOLAR_SMOOTHING = "solar_smoothing"
    TIME_SHIFT_AGGRESSIVE = "time_shift_aggressive"
    CYCLING_DEMO = "cycling_demo"
    FREQUENCY_REGULATION = "frequency_regulation"
    ARBITRAGE_AGGRESSIVE = "arbitrage_aggressive"


class BESSTopology(str, Enum):
    """Enumerates BESS system topology configurations."""
    
    PARALLEL_AC = "parallel_ac"
    SERIES_DC = "series_dc"
    HYBRID = "hybrid"


class BESSTechnology(str, Enum):
    """Enumerates BESS technology types."""
    
    STANDARD = "standard"
    MODERN_LFP = "modern_lfp"
    PREMIUM = "premium"


LEGACY_TO_BESS_STRATEGY: Mapping[str, BESSStrategy] = MappingProxyType(
    {
        "cap_shaving": BESSStrategy.PEAK_LIMIT,
        "night_shift": BESSStrategy.TIME_SHIFT,
        "flat_day": BESSStrategy.SMOOTHING,
        "firm_delivery_window": BESSStrategy.FIRM_CAPACITY,
    }
)


class SolarTechnology(str, Enum):
    """Reference list of solar configurations in *snake_case*."""

    FIXED_MONOFACIAL = "fixed_monofacial"
    FIXED_BIFACIAL = "fixed_bifacial"
    SAT_MONOFACIAL = "sat_monofacial"
    SAT_BIFACIAL = "sat_bifacial"

    # Legacy alias kept for one release cycle
    SAT_BI = "sat_bifacial"  # TODO-remove-v3


def normalize_solar_tech(name: str) -> SolarTechnology:
    """Map user‑provided names (any case / spaces) to :class:`SolarTechnology`."""
    key = name.strip().lower().replace(" ", "_")
    mapping = {
        "fixed_monofacial": SolarTechnology.FIXED_MONOFACIAL,
        "fixed_bifacial": SolarTechnology.FIXED_BIFACIAL,
        "sat_monofacial": SolarTechnology.SAT_MONOFACIAL,
        "sat_bifacial": SolarTechnology.SAT_BIFACIAL,
    }
    try:
        return mapping[key]
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f"Unknown solar technology: {name}") from exc


# ────────────────────────────────────────────────────────────────────
#  IMMUTABLE CONSTANT BLOCKS
# ────────────────────────────────────────────────────────────────────

def _freeze(d: dict) -> Mapping:
    """Utility: return an immutable view of *d*."""
    return MappingProxyType(d)


SYSTEM = _freeze(
    {
        "VOLTAGE_NOMINAL_KV": 33.0,
        "VOLTAGE_MIN_PU": 0.95,
        "VOLTAGE_MAX_PU": 1.05,
        "POWER_FACTOR_MIN": 0.92,
        "FREQUENCY_HZ": 50.0,
        "BASE_MVA": 100.0,
    }
)

NETWORK = _freeze(
    {
        "TOTAL_LENGTH_KM": 270.0,
        "VOLTAGE_DROP_PU_PER_KM": 0.0015,
        "LOSSES_MW_PER_KM": 0.0037,  # at nominal load
        "IMPEDANCE_OHM_PER_KM": 0.5,
    }
)

SOLAR = _freeze(
    {
        "PANEL_EFFICIENCY": 0.235,
        "INVERTER_EFFICIENCY": 0.97,
        "SYSTEM_LOSSES": 0.12,
        "DEGRADATION_RATE": 0.005,
        "TILT_ANGLE_DEG": 35.0,
        "AZIMUTH_ANGLE_DEG": 180.0,
    }
)

BESS = _freeze(
    {
        "ROUND_TRIP_EFFICIENCY": 0.92,
        "SOC_MIN": 0.10,
        "SOC_MAX": 0.95,
        "DISCHARGE_EFFICIENCY": 0.96,
        "CHARGE_EFFICIENCY": 0.96,
        "CYCLING_EFFICIENCY": 0.99,
        "CALENDAR_LIFE_Y": 15,
        "CYCLE_LIFE": 6000,
        "CYCLE_ENERGY_THRESHOLD_MWH": 0.01,  # 10 kWh threshold for cycle counting
    }
)

# BESS Technology configurations
BESS_TECHNOLOGIES = _freeze(
    {
        "standard": _freeze({
            "η_charge": 0.949,      # sqrt(0.90)
            "η_discharge": 0.949,
            "η_roundtrip": 0.90,
            "soc_min": 0.20,        # 20% minimum (lead-acid friendly)
            "soc_max": 0.90,        # 90% maximum
            "c_rate_max": 0.5,      # Conservative C-rate
            "description": "Standard technology (Lead-acid or old Li-ion)"
        }),
        "modern_lfp": _freeze({
            "η_charge": 0.964,      # sqrt(0.93)
            "η_discharge": 0.964,
            "η_roundtrip": 0.93,
            "soc_min": 0.10,        # 10% minimum
            "soc_max": 0.95,        # 95% maximum
            "c_rate_max": 1.0,      # 1C typical for LFP
            "description": "Modern LiFePO4 technology"
        }),
        "premium": _freeze({
            "η_charge": 0.975,      # sqrt(0.95)
            "η_discharge": 0.975,
            "η_roundtrip": 0.95,
            "soc_min": 0.05,        # 5% minimum
            "soc_max": 0.95,        # 95% maximum
            "c_rate_max": 2.0,      # 2C for premium systems
            "description": "Premium technology (LTO or advanced Li-ion)"
        })
    }
)

# BESS Topology configurations
BESS_TOPOLOGIES = _freeze(
    {
        "parallel_ac": _freeze({
            "efficiency_penalty": 0.00,  # No additional penalty
            "flexibility": "high",
            "description": "AC-coupled parallel configuration"
        }),
        "series_dc": _freeze({
            "efficiency_penalty": 0.02,  # 2% penalty for DC-DC conversion
            "flexibility": "medium",
            "description": "DC-coupled series configuration"
        }),
        "hybrid": _freeze({
            "efficiency_penalty": 0.01,  # 1% penalty
            "flexibility": "high",
            "description": "Hybrid AC/DC configuration"
        })
    }
)

ECONOMICS = _freeze(
    {
        "DISCOUNT_RATE": 0.08,
        "INFLATION_RATE": 0.03,
        "CAPEX_SOLAR_USD_KW": 850,
        "CAPEX_BESS_USD_KWH": 350,
        "OPEX_SOLAR_USD_KW_YEAR": 18,
        "OPEX_BESS_USD_KWH_YEAR": 5,
    }
)

TIME = _freeze(
    {
        "HOURS_PER_DAY": 24,
        "MONTHS_PER_YEAR": 12,
        "MONTH_NAMES": (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
    }
)


def days_in_month(year: int, month: int) -> int:  # noqa: D401
    """Return the number of days in *month* for *year* (supports leap years)."""
    import calendar

    return calendar.monthrange(year, month)[1]


ANALYSIS = _freeze(
    {
        "MIN_SAMPLES_CORRELATION": 10,
        "CRITICAL_VOLTAGE_PU": 0.5,
        "CRITICAL_EVENT_MIN_MINUTES": 15,
        "MAX_RAMP_RATE_MW_H": 1.0,
        "CONFIDENCE_INTERVAL": 0.95,
    }
)

FILEPATH = _freeze(
    {
        "SYSTEM_DATA": "sistema_linea_sur.json",
        "TRANSFORMER_DATA": "transformadores_detalle.json",  # canonical
        "HISTORICAL_DATA": "consolidated_data.csv",
        "FALLBACK_DATA": "fallback_data.json",
    }
)

# ────────────────────────────────────────────────────────────────────
#  STRUCTURED DATA
# ────────────────────────────────────────────────────────────────────


class StationInfo(TypedDict):
    coordinates: Tuple[float, float]
    distance_km: float
    transformation: str
    type: Literal["source", "load"]


STATIONS: Mapping[str, StationInfo] = _freeze(
    {
        "PILCANIYEU": {
            "coordinates": (-41.12, -70.90),
            "distance_km": 0,
            "transformation": "132/33 kV",
            "type": "source",
        },
        "COMALLO": {
            "coordinates": (-41.06, -70.27),
            "distance_km": 70,
            "transformation": "33/13.2 kV",
            "type": "load",
        },
        "ONELLI": {
            "coordinates": (-41.14, -69.89),
            "distance_km": 120,
            "transformation": "33/13.2 kV",
            "type": "load",
        },
        "JACOBACCI": {
            "coordinates": (-41.329, -69.550),
            "distance_km": 150,
            "transformation": "33/13.2 kV",
            "type": "load",
        },
        "MAQUINCHAO": {
            "coordinates": (-41.25, -68.73),
            "distance_km": 210,
            "transformation": "33/13.2 kV",
            "type": "load",
        },
        "AGUADA_DE_GUERRA": {
            "coordinates": (-41.00, -68.40),
            "distance_km": 240,
            "transformation": "33 kV",
            "type": "load",
        },
        "LOS_MENUCOS": {
            "coordinates": (-40.843, -68.086),
            "distance_km": 270,
            "transformation": "33/13.2 kV",
            "type": "load",
        },
    }
)

# TODO‑move‑out‑of‑constants (operational data) ────────────────────
GD_CONFIG = _freeze(
    {
        "LOS_MENUCOS": {
            "installed_power_mw": 3.0,
            "available_power_mw": 1.8,
            "fuel_type": "natural_gas",
            "efficiency": 0.35,
            "operating_hours_per_day": 4.0,
            "cost_usd_per_mwh": 138.6,
            "utilization_factor": 0.133,
        }
    }
)

MONTHLY_SOLAR_GENERATION_MWH_PER_MW: Mapping[int, float] = _freeze(
    {
        1: 196.8,   # enero - verano
        2: 160.9,   # febrero
        3: 170.4,   # marzo
        4: 137.7,   # abril
        5: 120.9,   # mayo
        6: 103.4,   # junio - invierno
        7: 116.0,   # julio
        8: 135.4,   # agosto
        9: 155.4,   # septiembre
        10: 183.3,  # octubre
        11: 185.8,  # noviembre
        12: 204.1,  # diciembre - verano
    }
)

# Promedio mensual para simulaciones flat (1870 MWh/año ÷ 12 meses)
AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW: float = 155.8

# ────────────────────────────────────────────────────────────────────
#  CACHE SETTINGS
# ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CacheConfig:
    enable: bool = True
    size: int = 128
    ttl_s: int = 300
    persist: bool = False


CACHE = CacheConfig()

# Backwards‑compat mapping                       # TODO-remove-v3
CACHE_CONFIG = {
    "ENABLE_CACHE": CACHE.enable,
    "CACHE_SIZE": CACHE.size,
    "CACHE_TTL": CACHE.ttl_s,
    "CACHE_PERSIST": CACHE.persist,
}

# ────────────────────────────────────────────────────────────────────
#  EXPORT CONTROL
# ────────────────────────────────────────────────────────────────────

__all__: Sequence[str] = (
    # enums
    "DataStatus",
    "BESSStrategy",
    "BESSTopology",
    "BESSTechnology",
    "SolarTechnology",
    # helpers
    "normalize_solar_tech",
    "LEGACY_TO_BESS_STRATEGY",
    "days_in_month",
    # constants
    "SYSTEM",
    "NETWORK",
    "SOLAR",
    "BESS",
    "BESS_TECHNOLOGIES",
    "BESS_TOPOLOGIES",
    "ECONOMICS",
    "TIME",
    "ANALYSIS",
    "FILEPATH",
    "STATIONS",
    "GD_CONFIG",  # TODO-move-out-of-constants
    "MONTHLY_SOLAR_GENERATION_MWH_PER_MW",
    "AVERAGE_MONTHLY_SOLAR_GENERATION_MWH_PER_MW",
    "CACHE",
    # legacy exports
    "SYSTEM_CONSTANTS",  # TODO-remove-v3
    "NETWORK_CONSTANTS",
    "SOLAR_CONSTANTS",
    "BESS_CONSTANTS",
    "ECONOMIC_CONSTANTS",
    "TIME_CONSTANTS",
    "ANALYSIS_CONSTANTS",
    "FILE_PATHS",
    "CACHE_CONFIG",
    "GD_CONSTANTS",
    "UI_COLORS",
)


# ────────────────────────────────────────────────────────────────────
#  DISTRIBUTED GENERATION CONSTANTS
# ────────────────────────────────────────────────────────────────────

GD_CONSTANTS: Mapping[str, float | int | str] = MappingProxyType({
    # Capacidad y operación
    "potencia_mw": 1.8,  # MW disponibles (de 3 MW instalados)
    "potencia_total_mw": 3.0,  # MW instalados totales
    "factor_capacidad": 0.95,  # Factor de capacidad durante operación
    "horas_dia_base": 4,  # Horas de operación diaria
    "dias_ano": 365,
    "dias_mes": 30,
    
    # Costos mensuales (datos reales proporcionados)
    "alquiler_mensual": 16000,  # USD/mes total
    "opex_por_mw_mensual": 1600,  # USD/MW/mes
    "combustible_mensual_base": 6000,  # USD/mes @ 4h/día
    
    # Costos unitarios derivados
    "alquiler_unitario": 8.89,  # USD/kW-mes (16000/1800)
    "opex_por_mw_anual": 19200,  # USD/MW/año (1600*12)
    
    # Parámetros técnicos
    "consumo_gas": 0.278,  # m³/kWh
    "precio_gas": 0.11137,  # USD/m³
    "precio_compra_edersa": 85.0,  # USD/MWh
    
    # Factores O&M
    "factor_oym": 0.1,  # 10% del OPEX
    
    # Metadatos
    "ubicacion": "Los Menucos",
    "tecnologia": "Motogeneradores a gas",
    "conexion_kv": 13.2,
})


# ────────────────────────────────────────────────────────────────────
#  UI COLOR PALETTE
# ────────────────────────────────────────────────────────────────────

UI_COLORS: Mapping[str, str] = MappingProxyType({
    # General UI colors
    "background": "#f8f9fa",
    "text": "#212529",
    "primary": "#0d6efd",
    "success": "#198754",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#0dcaf0",
    
    # Network specific colors
    "conductor_primary": "#0066cc",      # 120mm² conductors
    "conductor_secondary": "#003d7a",    # Other conductors
    "node_default": "#dc3545",           # Default node color
    "node_low_load": "#198754",          # Low load nodes
    "node_medium_load": "#ffc107",       # Medium load nodes
    "node_critical": "#dc3545",          # Critical/high load nodes
    "gd_marker": "#6f42c1",              # Distributed generation
    
    # Chart colors
    "voltage_theoretical": "#ffa500",     # Orange for theoretical
    "voltage_measured": "#008000",        # Green for measured
    "voltage_limit": "#ff0000",           # Red for limits
    "voltage_nominal": "#00ff00",         # Light green for nominal
})


# Legacy aliases (immutable views)  ───────────── TODO-remove-v3
SYSTEM_CONSTANTS = SYSTEM
NETWORK_CONSTANTS = NETWORK
SOLAR_CONSTANTS = SOLAR
BESS_CONSTANTS = BESS


# ────────────────────────────────────────────────────────────────────
#  PHASE 5 - ELECTRICAL PARAMETERS (SIMULATED)
# ────────────────────────────────────────────────────────────────────

ELECTRICAL_PARAMS: Mapping[str, any] = MappingProxyType({
    "conductor_types": {
        "ACSR_95": {
            "r_ohm_per_km": 0.341,  # at 20°C
            "x_ohm_per_km": 0.428,
            "b_microsiemens_per_km": 2.65,
            "temp_coeff": 0.00403,  # 1/°C
            "ampacity": 240  # A
        },
        "ACSR_50": {
            "r_ohm_per_km": 0.642,
            "x_ohm_per_km": 0.451,
            "b_microsiemens_per_km": 2.51,
            "temp_coeff": 0.00403,
            "ampacity": 170
        },
        "ACSR_120": {
            "r_ohm_per_km": 0.273,
            "x_ohm_per_km": 0.412,
            "b_microsiemens_per_km": 2.74,
            "temp_coeff": 0.00403,
            "ampacity": 290
        }
    },
    "load_models": {
        "residential": {"z": 0.2, "i": 0.3, "p": 0.5},  # ZIP coefficients
        "commercial": {"z": 0.1, "i": 0.2, "p": 0.7},
        "industrial": {"z": 0.0, "i": 0.1, "p": 0.9},
        "rural": {"z": 0.3, "i": 0.3, "p": 0.4}
    },
    "power_flow_config": {
        "max_iterations": 10,
        "tolerance": 1e-6,
        "acceleration_factor": 1.6,
        "flat_start": True,
        "enforce_q_limits": True
    }
})


# ────────────────────────────────────────────────────────────────────
#  PHASE 5 - VALIDATION LIMITS
# ────────────────────────────────────────────────────────────────────

VALIDATION_LIMITS: Mapping[str, float] = MappingProxyType({
    "power_balance_tolerance": 0.001,  # 0.1%
    "voltage_min_pu": 0.95,
    "voltage_max_pu": 1.05,
    "voltage_emergency_min_pu": 0.90,  # Emergency operation
    "line_loading_max": 0.9,  # 90%
    "transformer_loading_max": 1.0,  # 100%
    "transformer_emergency_max": 1.2,  # 120% for short time
    "frequency_min": 49.8,
    "frequency_max": 50.2,
    "power_factor_min": 0.92
})


# ────────────────────────────────────────────────────────────────────
#  PHASE 5 - ECONOMIC PARAMETERS
# ────────────────────────────────────────────────────────────────────

ECONOMIC_PARAMS: Mapping[str, any] = MappingProxyType({
    "discount_rate": 0.08,  # 8% annual
    "analysis_period": 25,  # years
    "inflation_rate": 0.03,  # 3% annual
    "energy_not_served_cost": 150,  # USD/MWh
    "loss_cost": 62.5,  # USD/MWh (average tariff)
    "voltage_penalty": {  # USD/MWh by voltage range
        "below_0.90": 50,  # Severe penalty
        "below_0.95": 20,  # Regulatory violation
        "above_1.05": 10   # Overvoltage penalty
    },
    "reliability_costs": {
        "outage_cost_residential": 5.0,  # USD/kWh
        "outage_cost_commercial": 15.0,  # USD/kWh
        "outage_cost_industrial": 25.0,  # USD/kWh
    }
})


# ────────────────────────────────────────────────────────────────────
#  PHASE 5 - ALTERNATIVE INVESTMENT COSTS
# ────────────────────────────────────────────────────────────────────

ALTERNATIVE_COSTS: Mapping[str, any] = MappingProxyType({
    "traditional": {
        "new_line_33kv": 80000,  # USD/km
        "reconductoring_33kv": 50000,  # USD/km
        "capacitor_bank": 50000,  # USD/MVAr
        "svc": 80000,  # USD/MVAr (Static Var Compensator)
        "tap_changer": 100000,  # USD/unit
        "voltage_regulator": 150000,  # USD/unit
        "opex_percent": 0.02  # 2% of CAPEX annually
    },
    "gd_thermal": {
        "capex_expansion": 0,  # Rental model
        "opex_mwh": 122.7,  # From existing GD data
        "availability_hours": 4,  # hours/day
        "capacity_factor": 0.133,
        "startup_cost": 50  # USD per start
    },
    "pv_distributed": {
        "capex_usd_per_kw": 850,  # Current Patagonia costs
        "opex_usd_per_kw_year": 18,
        "degradation_rate": 0.005,  # 0.5% annual
        "inverter_replacement_year": 12,
        "inverter_cost_percent": 0.15  # 15% of initial CAPEX
    },
    "bess": {
        "capex_power_usd_per_kw": 400,
        "capex_energy_usd_per_kwh": 350,
        "opex_percent": 0.015,  # 1.5% of CAPEX
        "efficiency": 0.92,
        "cycles_per_year": 350,
        "lifetime_cycles": 5000
    }
})


# ────────────────────────────────────────────────────────────────────
#  PHASE 5 - CACHE CONFIGURATION
# ────────────────────────────────────────────────────────────────────

PHASE5_CACHE_CONFIG: Mapping[str, any] = MappingProxyType({
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": None,  # Set in environment if needed
        "socket_timeout": 5,
        "connection_pool_kwargs": {
            "max_connections": 50,
            "retry_on_timeout": True
        }
    },
    "lru": {
        "maxsize": 1000,
        "typed": True  # Different types cached separately
    },
    "ttl": {
        "power_flow": 300,  # 5 minutes
        "network_topology": 3600,  # 1 hour
        "load_profile": 900,  # 15 minutes
        "economic_analysis": 1800  # 30 minutes
    },
    "compression": {
        "enabled": True,
        "algorithm": "gzip",
        "level": 6
    }
})
ECONOMIC_CONSTANTS = ECONOMICS
TIME_CONSTANTS = TIME
ANALYSIS_CONSTANTS = ANALYSIS
FILE_PATHS = FILEPATH
