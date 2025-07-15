"""
Pydantic Validation Schemas for DataManager V2
Provides robust validation for all data structures with clear error reporting
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

from .constants import DataStatus, BESSStrategy, SolarTechnology


# Base validation models
class BaseValidatedModel(BaseModel):
    """Base model with common configuration"""
    
    class Config:
        extra = "forbid"  # Prevent unexpected fields
        validate_assignment = True
        use_enum_values = True


# System topology schemas
class NodeSchema(BaseValidatedModel):
    """Validation schema for network nodes"""
    name: str = Field(..., min_length=1, description="Node name")
    coordinates: tuple[float, float] = Field(..., description="Lat/Lon coordinates")
    distance_km: float = Field(..., ge=0, description="Distance from origin in km")
    transformation: str = Field(..., description="Voltage transformation")
    type: str = Field(..., description="Node type (source/load)")
    load_mw: float = Field(..., ge=0, description="Active power load in MW")
    load_mvar: float = Field(..., ge=0, description="Reactive power load in MVAr")
    voltage_pu: float = Field(..., gt=0, le=2.0, description="Voltage in per unit")

    @validator('coordinates')
    def validate_coordinates(cls, v):
        lat, lon = v
        if not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Invalid longitude: {lon}")
        return v


class EdgeSchema(BaseValidatedModel):
    """Validation schema for network edges/lines"""
    from_node: str = Field(..., min_length=1)
    to_node: str = Field(..., min_length=1)
    length_km: float = Field(..., gt=0, description="Line length in km")
    impedance_ohm: float = Field(..., gt=0, description="Line impedance in ohms")
    current_capacity_a: float = Field(..., gt=0, description="Current capacity in amperes")
    voltage_drop_pu: float = Field(..., ge=0, description="Voltage drop in per unit")
    losses_mw: float = Field(..., ge=0, description="Power losses in MW")

    @validator('to_node')
    def validate_different_nodes(cls, v, values):
        if 'from_node' in values and v == values['from_node']:
            raise ValueError("from_node and to_node must be different")
        return v


class TransformerSchema(BaseValidatedModel):
    """Validation schema for transformers"""
    name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    primary_voltage_kv: float = Field(..., gt=0, description="Primary voltage in kV")
    secondary_voltage_kv: float = Field(..., gt=0, description="Secondary voltage in kV")
    power_rating_mva: float = Field(..., gt=0, description="Power rating in MVA")
    impedance_percent: float = Field(..., gt=0, le=100, description="Impedance in percent")
    tap_range: Dict[str, float] = Field(..., description="Tap range settings")
    regulation_type: str = Field(..., description="Type of regulation")

    @validator('tap_range')
    def validate_tap_range(cls, v):
        required_keys = {'min', 'max'}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"tap_range must contain keys: {required_keys}")
        if v['min'] >= v['max']:
            raise ValueError("tap_range min must be less than max")
        return v


class SystemSummarySchema(BaseValidatedModel):
    """Validation schema for system summary"""
    total_power_mw: float = Field(..., ge=0, description="Total active power in MW")
    total_reactive_mvar: float = Field(..., ge=0, description="Total reactive power in MVAr")
    power_factor: float = Field(..., ge=0, le=1, description="System power factor")
    total_losses_mw: float = Field(..., ge=0, description="Total losses in MW")
    voltage_profile: Dict[str, float] = Field(..., description="Voltage profile by station")
    load_distribution: Dict[str, float] = Field(..., description="Load distribution by station")

    @validator('voltage_profile', 'load_distribution')
    def validate_dictionaries(cls, v):
        if not v:
            raise ValueError("Dictionary cannot be empty")
        for key, value in v.items():
            if not isinstance(key, str) or len(key) == 0:
                raise ValueError("Dictionary keys must be non-empty strings")
            if not isinstance(value, (int, float)) or value < 0:
                raise ValueError("Dictionary values must be non-negative numbers")
        return v


# Complete system schema
class SystemDataSchema(BaseValidatedModel):
    """Complete system data validation schema"""
    nodes: List[NodeSchema] = Field(..., min_items=1, description="Network nodes")
    edges: List[EdgeSchema] = Field(..., description="Network edges")
    transformers: List[TransformerSchema] = Field(..., description="Transformers")
    system_summary: SystemSummarySchema = Field(..., description="System summary")
    gd_config: Optional[Dict[str, Any]] = Field(None, description="Generation configuration")
    source: str = Field(..., description="Data source identifier")
    generated_at: datetime = Field(..., description="Generation timestamp")

    @root_validator(skip_on_failure=True)
    def validate_system_consistency(cls, values):
        """Validate system-wide consistency"""
        nodes = values.get('nodes', [])
        edges = values.get('edges', [])
        
        # Check that all edge nodes exist
        node_names = {node.name for node in nodes}
        for edge in edges:
            if edge.from_node not in node_names:
                raise ValueError(f"Edge references unknown from_node: {edge.from_node}")
            if edge.to_node not in node_names:
                raise ValueError(f"Edge references unknown to_node: {edge.to_node}")
        
        return values


# Historical data schemas
class HistoricalRecordSchema(BaseValidatedModel):
    """Validation schema for historical measurement records"""
    timestamp: datetime = Field(..., description="Measurement timestamp")
    station: str = Field(..., min_length=1, description="Station name")
    voltage_pu: float = Field(..., gt=0, le=2.0, description="Voltage in per unit")
    power_mw: float = Field(..., ge=0, description="Active power in MW")
    reactive_mvar: float = Field(..., description="Reactive power in MVAr")
    current_a: float = Field(..., ge=0, description="Current in amperes")
    power_factor: float = Field(..., ge=0, le=1, description="Power factor")
    frequency_hz: float = Field(..., gt=45, lt=55, description="Frequency in Hz")


# Solar and BESS schemas
class SolarConfigurationSchema(BaseValidatedModel):
    """Validation schema for solar PV configuration"""
    power_mw: float = Field(..., gt=0, description="Installed power in MW")
    technology: SolarTechnology = Field(..., description="Solar panel technology")
    tilt_angle: float = Field(35.0, ge=0, le=90, description="Panel tilt angle in degrees")
    azimuth_angle: float = Field(180.0, ge=0, lt=360, description="Panel azimuth angle in degrees")
    inverter_efficiency: float = Field(0.97, gt=0, le=1, description="Inverter efficiency")
    system_losses: float = Field(0.12, ge=0, lt=1, description="System losses fraction")
    degradation_rate: float = Field(0.005, ge=0, lt=0.1, description="Annual degradation rate")


class BESSConfigurationSchema(BaseValidatedModel):
    """Validation schema for BESS configuration"""
    power_mw: float = Field(..., gt=0, description="Power rating in MW")
    energy_mwh: float = Field(..., gt=0, description="Energy capacity in MWh")
    efficiency: float = Field(0.92, gt=0, le=1, description="Round-trip efficiency")
    soc_min: float = Field(0.10, ge=0, lt=1, description="Minimum state of charge")
    soc_max: float = Field(0.95, gt=0, le=1, description="Maximum state of charge")
    strategy: BESSStrategy = Field(BESSStrategy.SMOOTHING, description="Control strategy")
    max_cycles_per_day: int = Field(2, ge=1, le=10, description="Maximum cycles per day")

    @validator('soc_max')
    def validate_soc_range(cls, v, values):
        if 'soc_min' in values and v <= values['soc_min']:
            raise ValueError("soc_max must be greater than soc_min")
        return v

    @validator('energy_mwh')
    def validate_energy_power_ratio(cls, v, values):
        if 'power_mw' in values:
            duration = v / values['power_mw']
            if duration > 12:  # More than 12 hours seems unrealistic
                raise ValueError(f"Duration ({duration:.1f}h) seems too high for practical BESS")
            if duration < 0.25:  # Less than 15 minutes seems too low
                raise ValueError(f"Duration ({duration:.1f}h) seems too low for practical BESS")
        return v


# Economic schemas
class EconomicParametersSchema(BaseValidatedModel):
    """Validation schema for economic parameters"""
    discount_rate: float = Field(0.08, gt=0, lt=1, description="Discount rate")
    inflation_rate: float = Field(0.03, ge=0, lt=1, description="Inflation rate")
    analysis_period_years: int = Field(25, ge=1, le=50, description="Analysis period in years")
    capex_solar_usd_kw: float = Field(850, gt=0, description="Solar CAPEX in USD/kW")
    capex_bess_usd_kwh: float = Field(350, gt=0, description="BESS CAPEX in USD/kWh")
    opex_solar_usd_kw_year: float = Field(18, ge=0, description="Solar OPEX in USD/kW/year")
    opex_bess_usd_kwh_year: float = Field(5, ge=0, description="BESS OPEX in USD/kWh/year")


# Validation result wrapper
class ValidationResultWrapper(BaseValidatedModel):
    """Wrapper for validation results"""
    is_valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    data: Optional[Any] = Field(None, description="Validated data if successful")
    schema_used: str = Field(..., description="Schema type used for validation")


# Validation functions
def validate_system_data(data: Dict[str, Any]) -> ValidationResultWrapper:
    """Validate system data against schema"""
    try:
        validated_data = SystemDataSchema(**data)
        return ValidationResultWrapper(
            is_valid=True,
            data=validated_data.dict(),
            schema_used="SystemDataSchema"
        )
    except Exception as e:
        return ValidationResultWrapper(
            is_valid=False,
            errors=[str(e)],
            schema_used="SystemDataSchema"
        )


def validate_historical_records(records: List[Dict[str, Any]]) -> ValidationResultWrapper:
    """Validate historical records"""
    errors = []
    validated_records = []
    
    for i, record in enumerate(records):
        try:
            validated_record = HistoricalRecordSchema(**record)
            validated_records.append(validated_record.dict())
        except Exception as e:
            errors.append(f"Record {i}: {str(e)}")
    
    if errors:
        return ValidationResultWrapper(
            is_valid=False,
            errors=errors,
            schema_used="HistoricalRecordSchema"
        )
    
    return ValidationResultWrapper(
        is_valid=True,
        data=validated_records,
        schema_used="HistoricalRecordSchema"
    )


def validate_solar_configuration(config: Dict[str, Any]) -> ValidationResultWrapper:
    """Validate solar configuration"""
    try:
        validated_config = SolarConfigurationSchema(**config)
        return ValidationResultWrapper(
            is_valid=True,
            data=validated_config.dict(),
            schema_used="SolarConfigurationSchema"
        )
    except Exception as e:
        return ValidationResultWrapper(
            is_valid=False,
            errors=[str(e)],
            schema_used="SolarConfigurationSchema"
        )


def validate_bess_configuration(config: Dict[str, Any]) -> ValidationResultWrapper:
    """Validate BESS configuration"""
    try:
        validated_config = BESSConfigurationSchema(**config)
        return ValidationResultWrapper(
            is_valid=True,
            data=validated_config.dict(),
            schema_used="BESSConfigurationSchema"
        )
    except Exception as e:
        return ValidationResultWrapper(
            is_valid=False,
            errors=[str(e)],
            schema_used="BESSConfigurationSchema"
        )


def validate_economic_parameters(params: Dict[str, Any]) -> ValidationResultWrapper:
    """Validate economic parameters"""
    try:
        validated_params = EconomicParametersSchema(**params)
        return ValidationResultWrapper(
            is_valid=True,
            data=validated_params.dict(),
            schema_used="EconomicParametersSchema"
        )
    except Exception as e:
        return ValidationResultWrapper(
            is_valid=False,
            errors=[str(e)],
            schema_used="EconomicParametersSchema"
        )


# Export all validation functions
__all__ = [
    "BaseValidatedModel",
    "NodeSchema",
    "EdgeSchema", 
    "TransformerSchema",
    "SystemSummarySchema",
    "SystemDataSchema",
    "HistoricalRecordSchema",
    "SolarConfigurationSchema",
    "BESSConfigurationSchema",
    "EconomicParametersSchema",
    "ValidationResultWrapper",
    "validate_system_data",
    "validate_historical_records",
    "validate_solar_configuration",
    "validate_bess_configuration",
    "validate_economic_parameters",
]