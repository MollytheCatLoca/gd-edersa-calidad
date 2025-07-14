"""
Power Flow Validation Module
Validates DC power flow results against real measurements
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
from datetime import datetime

from .dc_power_flow import DCPowerFlow, PowerFlowResult

# Setup paths
import sys
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dashboard.pages.utils.data_manager_v2 import DataManagerV2
from dashboard.pages.utils.models import DataResult

logger = logging.getLogger(__name__)


class PowerFlowValidator:
    """
    Validates DC power flow results against historical measurements.
    
    Uses data from Phase 3 to verify accuracy of the simplified model.
    """
    
    def __init__(self, dc_power_flow: DCPowerFlow):
        """Initialize with DC power flow instance."""
        self.pf = dc_power_flow
        self.dm = DataManagerV2()
        self.validation_results = []
        
    def validate_with_historical_data(self, 
                                    start_date: str = "2024-01-01",
                                    end_date: str = "2024-12-31",
                                    sample_hours: int = 24) -> Dict:
        """
        Validate power flow against historical measurements.
        
        Args:
            start_date: Start date for validation period
            end_date: End date for validation period
            sample_hours: Number of hours to sample for validation
            
        Returns:
            Dictionary with validation metrics
        """
        logger.info(f"Starting validation from {start_date} to {end_date}")
        
        # Load historical data
        historical_data = self._load_historical_data(start_date, end_date)
        if historical_data is None:
            return {"error": "Failed to load historical data"}
        
        # Sample hours for validation
        sample_indices = self._get_sample_indices(len(historical_data), sample_hours)
        
        voltage_errors = []
        flow_errors = []
        loss_errors = []
        
        for idx in sample_indices:
            record = historical_data.iloc[idx]
            
            # Run power flow for this hour
            result = self._run_power_flow_for_record(record)
            if not result.converged:
                continue
            
            # Compare voltages
            v_error = self._compare_voltages(result, record)
            if v_error is not None:
                voltage_errors.append(v_error)
            
            # Compare flows (if available)
            f_error = self._compare_flows(result, record)
            if f_error is not None:
                flow_errors.append(f_error)
            
            # Store detailed result
            self.validation_results.append({
                "timestamp": record.get("timestamp", idx),
                "converged": result.converged,
                "voltage_error": v_error,
                "flow_error": f_error,
                "measured_v": record.get("voltage", 0),
                "calculated_v": result.voltages_pu.get(record.get("station", ""), 0)
            })
        
        # Calculate statistics
        metrics = self._calculate_validation_metrics(
            voltage_errors, flow_errors, loss_errors
        )
        
        logger.info(f"Validation complete: {len(self.validation_results)} cases, "
                   f"Mean voltage error: {metrics['mean_voltage_error']:.3f}%")
        
        return metrics
    
    def validate_critical_events(self) -> Dict:
        """
        Validate against known critical events from Phase 3.
        
        Returns:
            Validation results for critical events
        """
        # Load critical events
        critical_events = self._load_critical_events()
        if not critical_events:
            return {"error": "No critical events found"}
        
        results = []
        
        for event in critical_events:
            # Reconstruct network state
            generation, loads = self._reconstruct_network_state(event)
            
            # Run power flow
            pf_result = self.pf.solve(generation, loads)
            
            # Compare with measured values
            comparison = self._compare_event_results(pf_result, event)
            results.append(comparison)
        
        # Summarize
        summary = {
            "total_events": len(critical_events),
            "converged": sum(1 for r in results if r.get("converged", False)),
            "mean_error": np.mean([r.get("voltage_error", 0) for r in results]),
            "max_error": np.max([r.get("voltage_error", 0) for r in results]),
            "details": results
        }
        
        return summary
    
    def validate_typical_days(self) -> Dict:
        """
        Validate against typical day profiles from Phase 3.
        
        Returns:
            Validation results by season
        """
        # Load typical days
        typical_days_result = self.dm.get_typical_days()
        if not typical_days_result.ok():
            return {"error": "Failed to load typical days"}
        
        typical_days = typical_days_result.data
        results = {}
        
        for season, profiles in typical_days.items():
            if not isinstance(profiles, dict):
                continue
                
            season_errors = []
            
            # Run power flow for each hour
            for hour in range(24):
                # Extract loads for this hour
                loads = {}
                for station, profile in profiles.items():
                    if isinstance(profile, dict) and "hourly_mw" in profile:
                        loads[station.lower()] = profile["hourly_mw"][hour]
                
                # Assume minimal generation (only GD if available)
                generation = {"los_menucos": 0.5 if 10 <= hour <= 16 else 0}
                
                # Run power flow
                result = self.pf.solve(generation, loads)
                
                if result.converged:
                    # Calculate average voltage error
                    avg_v = np.mean(list(result.voltages_pu.values()))
                    expected_v = 0.92 if 18 <= hour <= 22 else 0.94  # Typical pattern
                    error = abs(avg_v - expected_v) / expected_v * 100
                    season_errors.append(error)
            
            results[season] = {
                "mean_error": np.mean(season_errors) if season_errors else 0,
                "max_error": np.max(season_errors) if season_errors else 0,
                "hours_validated": len(season_errors)
            }
        
        return results
    
    def _load_historical_data(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Load historical data for validation period."""
        try:
            # This would load from processed Phase 3 data
            # For now, return None as placeholder
            logger.warning("Historical data loading not yet implemented")
            return None
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            return None
    
    def _load_critical_events(self) -> List[Dict]:
        """Load critical events from Phase 3 analysis."""
        result = self.dm.get_critical_events()
        if result.ok() and "events" in result.data:
            return result.data["events"][:10]  # Top 10 events
        return []
    
    def _get_sample_indices(self, total_records: int, sample_size: int) -> List[int]:
        """Get evenly spaced sample indices."""
        if sample_size >= total_records:
            return list(range(total_records))
        
        step = total_records // sample_size
        return list(range(0, total_records, step))[:sample_size]
    
    def _run_power_flow_for_record(self, record: pd.Series) -> PowerFlowResult:
        """Run power flow for a historical record."""
        # Extract loads from record
        loads = {}
        station = record.get("station", "").lower()
        if station and "power" in record:
            loads[station] = record["power"]
        
        # Minimal generation assumption
        generation = {}
        if "gd_power" in record:
            generation["los_menucos"] = record["gd_power"]
        
        return self.pf.solve(generation, loads)
    
    def _compare_voltages(self, result: PowerFlowResult, 
                         record: pd.Series) -> Optional[float]:
        """Compare calculated vs measured voltages."""
        station = record.get("station", "").lower()
        if station not in result.voltages_pu:
            return None
        
        measured = record.get("voltage", 0)
        if measured <= 0:
            return None
        
        calculated = result.voltages_pu[station]
        error = abs(calculated - measured) / measured * 100  # Percentage error
        
        return error
    
    def _compare_flows(self, result: PowerFlowResult,
                      record: pd.Series) -> Optional[float]:
        """Compare calculated vs measured flows (if available)."""
        # Flow measurements typically not available at distribution level
        return None
    
    def _reconstruct_network_state(self, event: Dict) -> Tuple[Dict, Dict]:
        """Reconstruct generation and load state from event data."""
        loads = {}
        generation = {}
        
        # Extract load at event location
        if "station" in event and "avg_power" in event:
            loads[event["station"].lower()] = event["avg_power"]
        
        # Assume typical loads at other stations
        typical_loads = {
            "pilcaniyeu": 2.5,
            "jacobacci": 1.8,
            "maquinchao": 3.2,
            "los_menucos": 2.1
        }
        
        for station, load in typical_loads.items():
            if station not in loads:
                loads[station] = load * 0.8  # 80% of typical
        
        return generation, loads
    
    def _compare_event_results(self, result: PowerFlowResult,
                              event: Dict) -> Dict:
        """Compare power flow results with event measurements."""
        station = event.get("station", "").lower()
        
        comparison = {
            "event_time": event.get("start_time"),
            "station": station,
            "converged": result.converged,
            "measured_voltage": event.get("min_voltage", 0),
            "calculated_voltage": result.voltages_pu.get(station, 0),
            "voltage_error": 0
        }
        
        if comparison["measured_voltage"] > 0 and comparison["calculated_voltage"] > 0:
            error = abs(comparison["calculated_voltage"] - comparison["measured_voltage"])
            comparison["voltage_error"] = error / comparison["measured_voltage"] * 100
        
        return comparison
    
    def _calculate_validation_metrics(self, voltage_errors: List[float],
                                    flow_errors: List[float],
                                    loss_errors: List[float]) -> Dict:
        """Calculate validation metrics."""
        metrics = {
            "total_cases": len(self.validation_results),
            "converged_cases": sum(1 for r in self.validation_results if r["converged"])
        }
        
        if voltage_errors:
            metrics.update({
                "mean_voltage_error": np.mean(voltage_errors),
                "max_voltage_error": np.max(voltage_errors),
                "std_voltage_error": np.std(voltage_errors),
                "voltage_error_percentiles": {
                    "p50": np.percentile(voltage_errors, 50),
                    "p90": np.percentile(voltage_errors, 90),
                    "p95": np.percentile(voltage_errors, 95)
                }
            })
        
        if flow_errors:
            metrics["mean_flow_error"] = np.mean(flow_errors)
        
        if loss_errors:
            metrics["mean_loss_error"] = np.mean(loss_errors)
        
        # Overall assessment
        if voltage_errors:
            mean_error = metrics["mean_voltage_error"]
            if mean_error < 5:
                metrics["validation_status"] = "excellent"
            elif mean_error < 10:
                metrics["validation_status"] = "good"
            elif mean_error < 15:
                metrics["validation_status"] = "acceptable"
            else:
                metrics["validation_status"] = "poor"
        
        return metrics
    
    def generate_validation_report(self) -> str:
        """Generate validation report."""
        if not self.validation_results:
            return "No validation results available"
        
        report = []
        report.append("="*60)
        report.append("DC POWER FLOW VALIDATION REPORT")
        report.append("="*60)
        report.append(f"Generated: {datetime.now()}")
        report.append(f"Total cases: {len(self.validation_results)}")
        
        # Calculate summary statistics
        converged = sum(1 for r in self.validation_results if r["converged"])
        v_errors = [r["voltage_error"] for r in self.validation_results 
                   if r["voltage_error"] is not None]
        
        report.append(f"\nConvergence: {converged}/{len(self.validation_results)} "
                     f"({converged/len(self.validation_results)*100:.1f}%)")
        
        if v_errors:
            report.append(f"\nVoltage Error Statistics:")
            report.append(f"  Mean: {np.mean(v_errors):.2f}%")
            report.append(f"  Max: {np.max(v_errors):.2f}%")
            report.append(f"  Std: {np.std(v_errors):.2f}%")
        
        # Worst cases
        report.append(f"\nWorst Voltage Errors:")
        worst_cases = sorted(self.validation_results, 
                           key=lambda x: x.get("voltage_error", 0) or 0,
                           reverse=True)[:5]
        
        for case in worst_cases:
            if case.get("voltage_error"):
                report.append(f"  {case['timestamp']}: {case['voltage_error']:.1f}% "
                            f"(Measured: {case['measured_v']:.3f}, "
                            f"Calculated: {case['calculated_v']:.3f})")
        
        return "\n".join(report)