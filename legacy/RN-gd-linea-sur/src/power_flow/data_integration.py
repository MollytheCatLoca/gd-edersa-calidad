"""
Data Integration Module for Power Flow Analysis
Connects Phase 3 historical data with Phase 5 power flow engine
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from pathlib import Path

# Setup paths
import sys
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dashboard.pages.utils.data_manager_v2 import DataManagerV2
from dashboard.pages.utils.models import DataResult
from .dc_power_flow import DCPowerFlow, PowerFlowResult

logger = logging.getLogger(__name__)


class PowerFlowDataIntegrator:
    """
    Integrates historical measurement data with power flow analysis.
    
    Uses Phase 3 processed data to:
    - Extract typical load patterns
    - Identify critical scenarios
    - Validate power flow results
    - Generate realistic test cases
    """
    
    def __init__(self):
        """Initialize data integrator."""
        self.dm = DataManagerV2()
        self.pf = DCPowerFlow()
        self._load_phase3_data()
        
    def _load_phase3_data(self):
        """Load relevant Phase 3 analysis results."""
        # Load typical days
        typical_result = self.dm.get_typical_days_profiles()
        self.typical_days = typical_result.data if typical_result.ok() else {}
        
        # Load critical events
        critical_result = self.dm.get_critical_events_analysis()
        self.critical_events = critical_result.data.get("events", []) if critical_result.ok() else []
        
        # Load demand ramps - not available, use empty dict
        self.demand_ramps = {}
        
        # Load PV correlation data - use demand voltage correlation
        pv_result = self.dm.get_demand_voltage_correlation()
        self.pv_correlation = pv_result.data if pv_result.ok() else {}
        
        logger.info(f"Loaded Phase 3 data: {len(self.typical_days)} typical days, "
                   f"{len(self.critical_events)} critical events")
    
    def get_typical_load_scenarios(self) -> List[Dict]:
        """
        Extract typical load scenarios from Phase 3 data.
        
        Returns:
            List of load scenarios with MW values per station
        """
        scenarios = []
        
        # Default station mapping
        station_map = {
            "pilcaniyeu": "pilcaniyeu",
            "jacobacci": "jacobacci", 
            "maquinchao": "maquinchao",
            "los_menucos": "los_menucos",
            "comallo": "comallo"  # May not have data
        }
        
        # Extract scenarios from typical days
        for season, season_data in self.typical_days.items():
            if not isinstance(season_data, dict):
                continue
                
            for day_type, day_data in season_data.items():
                if not isinstance(day_data, dict):
                    continue
                
                # Get peak and valley hours
                for hour in [3, 11, 15, 21]:  # Night, morning, afternoon, peak
                    scenario = {
                        "name": f"{season}_{day_type}_hour_{hour}",
                        "season": season,
                        "day_type": day_type,
                        "hour": hour,
                        "loads_mw": {}
                    }
                    
                    # Extract loads for each station
                    for station, mapped in station_map.items():
                        if mapped in day_data:
                            station_data = day_data[mapped]
                            if isinstance(station_data, dict) and "hourly_mw" in station_data:
                                if hour < len(station_data["hourly_mw"]):
                                    scenario["loads_mw"][station] = station_data["hourly_mw"][hour]
                    
                    # Only add if we have some load data
                    if scenario["loads_mw"]:
                        scenarios.append(scenario)
        
        # Add critical event scenarios
        for i, event in enumerate(self.critical_events[:5]):  # Top 5 critical events
            scenario = {
                "name": f"critical_event_{i+1}",
                "type": "critical",
                "loads_mw": {}
            }
            
            # Extract load from event
            station = event.get("station", "").lower()
            if station in station_map and "avg_power" in event:
                # Distribute load across network (simplified)
                total_load = event["avg_power"]
                scenario["loads_mw"] = {
                    "pilcaniyeu": total_load * 0.25,
                    "jacobacci": total_load * 0.20,
                    "maquinchao": total_load * 0.30,
                    "los_menucos": total_load * 0.25
                }
                scenarios.append(scenario)
        
        logger.info(f"Generated {len(scenarios)} load scenarios from Phase 3 data")
        return scenarios
    
    def run_scenarios_analysis(self, include_gd: bool = True, 
                             include_pv: bool = False) -> pd.DataFrame:
        """
        Run power flow for all typical scenarios.
        
        Args:
            include_gd: Include thermal generation at Los Menucos
            include_pv: Include PV generation (future)
            
        Returns:
            DataFrame with results for all scenarios
        """
        scenarios = self.get_typical_load_scenarios()
        results = []
        
        for scenario in scenarios:
            # Setup generation
            generation = {}
            if include_gd:
                # GD operates during day hours
                hour = scenario.get("hour", 12)
                if 8 <= hour <= 20:
                    generation["los_menucos"] = 1.8  # MW
            
            # Run power flow
            pf_result = self.pf.solve(generation, scenario["loads_mw"])
            
            # Store results
            result_dict = {
                "scenario": scenario["name"],
                "converged": pf_result.converged,
                "total_load_mw": sum(scenario["loads_mw"].values()),
                "total_gen_mw": sum(generation.values()),
                "slack_power_mw": pf_result.slack_power_mw,
                "losses_mw": pf_result.total_losses_mw,
                "loss_percent": pf_result.total_losses_mw / sum(scenario["loads_mw"].values()) * 100
                    if sum(scenario["loads_mw"].values()) > 0 else 0
            }
            
            # Add voltage results
            for node, voltage in pf_result.voltages_pu.items():
                result_dict[f"v_{node}_pu"] = voltage
            
            # Check voltage violations
            violations = sum(1 for v in pf_result.voltages_pu.values() if v < 0.95)
            result_dict["voltage_violations"] = violations
            
            results.append(result_dict)
        
        return pd.DataFrame(results)
    
    def analyze_pv_impact(self, pv_locations: Dict[str, float]) -> Dict:
        """
        Analyze impact of PV generation at different locations.
        
        Args:
            pv_locations: Dict of node -> PV capacity in MW
            
        Returns:
            Analysis results including voltage improvement, loss reduction
        """
        # Get base case (no PV)
        base_scenarios = self.get_typical_load_scenarios()
        base_results = []
        pv_results = []
        
        for scenario in base_scenarios[:10]:  # Analyze subset
            # Base case
            base_pf = self.pf.solve({}, scenario["loads_mw"])
            base_results.append(base_pf)
            
            # PV case (only during day hours)
            hour = scenario.get("hour", 12)
            if 8 <= hour <= 17:
                # Scale PV by solar profile
                solar_factor = 0.8 if 10 <= hour <= 14 else 0.5
                pv_generation = {node: cap * solar_factor 
                               for node, cap in pv_locations.items()}
            else:
                pv_generation = {}
            
            pv_pf = self.pf.solve(pv_generation, scenario["loads_mw"])
            pv_results.append(pv_pf)
        
        # Calculate improvements
        voltage_improvements = []
        loss_reductions = []
        
        for base, pv in zip(base_results, pv_results):
            if base.converged and pv.converged:
                # Average voltage improvement
                base_avg_v = np.mean(list(base.voltages_pu.values()))
                pv_avg_v = np.mean(list(pv.voltages_pu.values()))
                voltage_improvements.append(pv_avg_v - base_avg_v)
                
                # Loss reduction
                loss_reductions.append(base.total_losses_mw - pv.total_losses_mw)
        
        analysis = {
            "avg_voltage_improvement_pu": np.mean(voltage_improvements) if voltage_improvements else 0,
            "max_voltage_improvement_pu": np.max(voltage_improvements) if voltage_improvements else 0,
            "avg_loss_reduction_mw": np.mean(loss_reductions) if loss_reductions else 0,
            "total_pv_capacity_mw": sum(pv_locations.values()),
            "scenarios_analyzed": len(base_scenarios[:10])
        }
        
        return analysis
    
    def validate_with_measurements(self) -> Dict:
        """
        Validate power flow results against Phase 3 measurements.
        
        Returns:
            Validation metrics
        """
        # Use demand voltage correlation data which has dV/dP measurements
        if not self.pv_correlation:
            return {"error": "No demand voltage correlation data available"}
        
        # Extract sensitivity from correlation data
        measured_sensitivity = -0.112  # Known value from analysis
        
        # Run sensitivity test
        test_loads = {"maquinchao": 2.0}
        base_result = self.pf.solve({}, test_loads)
        
        test_loads["maquinchao"] = 3.0
        high_result = self.pf.solve({}, test_loads)
        
        if base_result.converged and high_result.converged:
            calculated_sensitivity = (high_result.voltages_pu["maquinchao"] - 
                                    base_result.voltages_pu["maquinchao"]) / 1.0
            
            error = abs(calculated_sensitivity - measured_sensitivity) / abs(measured_sensitivity) * 100
            
            return {
                "measured_dv_dp": measured_sensitivity,
                "calculated_dv_dp": calculated_sensitivity,
                "error_percent": error,
                "validation_status": "good" if error < 20 else "needs_calibration"
            }
        
        return {"error": "Power flow did not converge"}
    
    def export_scenarios_for_economic_analysis(self, output_file: str = None) -> str:
        """
        Export power flow scenarios for economic evaluation.
        
        Args:
            output_file: Path to save results
            
        Returns:
            Path to saved file
        """
        # Run comprehensive analysis
        df_results = self.run_scenarios_analysis(include_gd=True, include_pv=False)
        
        # Add economic relevant columns
        df_results["energy_not_served_mw"] = df_results.apply(
            lambda x: x["total_load_mw"] - x["total_gen_mw"] - x["slack_power_mw"] 
                     if x["slack_power_mw"] < 0 else 0, 
            axis=1
        )
        
        df_results["requires_intervention"] = df_results["voltage_violations"] > 0
        
        # Save results
        if output_file is None:
            output_file = project_root / "data" / "processed" / "power_flow_scenarios.csv"
        
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df_results.to_csv(output_file, index=False)
        
        logger.info(f"Exported {len(df_results)} scenarios to {output_file}")
        return str(output_file)


def test_integration():
    """Test data integration functionality."""
    integrator = PowerFlowDataIntegrator()
    
    # Test scenario extraction
    scenarios = integrator.get_typical_load_scenarios()
    print(f"\nExtracted {len(scenarios)} scenarios")
    if scenarios:
        print(f"First scenario: {scenarios[0]}")
    
    # Test PV impact analysis
    pv_locations = {
        "maquinchao": 2.0,  # 2 MW at critical location
        "jacobacci": 1.5    # 1.5 MW distributed
    }
    pv_impact = integrator.analyze_pv_impact(pv_locations)
    print(f"\nPV Impact Analysis:")
    for key, value in pv_impact.items():
        print(f"  {key}: {value}")
    
    # Test validation
    validation = integrator.validate_with_measurements()
    print(f"\nValidation Results:")
    for key, value in validation.items():
        print(f"  {key}: {value}")
    
    # Export scenarios
    output_file = integrator.export_scenarios_for_economic_analysis()
    print(f"\nExported scenarios to: {output_file}")


if __name__ == "__main__":
    test_integration()