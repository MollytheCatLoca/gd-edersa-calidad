"""
Low Voltage Analyzer for Phase 5
Specialized analysis for networks operating below 0.95 pu
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Setup paths for imports
import sys
from pathlib import Path
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dashboard.pages.utils.data_manager_v2 import DataManagerV2
from dashboard.pages.utils.models import DataResult, DataStatus

logger = logging.getLogger(__name__)


@dataclass
class VoltageViolation:
    """Details of a voltage violation"""
    node_id: str
    voltage_pu: float
    voltage_kv: float
    severity: str  # "critical", "severe", "moderate"
    duration_hours: float
    energy_at_risk_mwh: float
    estimated_cost_usd: float
    timestamp: Optional[datetime] = None


@dataclass
class VoltageImprovementOption:
    """Option for improving voltage at a node"""
    node_id: str
    method: str  # "capacitor", "gd", "pv", "line_upgrade"
    delta_v_pu: float  # Expected improvement
    cost_usd: float
    cost_per_pu: float  # $/pu improvement
    implementation_days: int
    description: str


@dataclass
class LowVoltageAnalysisResult:
    """Comprehensive analysis of low voltage conditions"""
    total_nodes: int
    nodes_below_095: int
    nodes_below_090: int
    critical_nodes: List[str]  # V < 0.90 pu
    total_energy_at_risk_mwh: float
    total_cost_violations_usd: float
    worst_node: str
    worst_voltage_pu: float
    violations: List[VoltageViolation]
    improvement_options: List[VoltageImprovementOption]
    summary_stats: Dict[str, float]


class LowVoltageAnalyzer:
    """
    Specialized analyzer for networks with V < 0.95 pu.
    
    Key focus areas:
    - Quantify energy at risk
    - Calculate economic impact
    - Identify critical nodes
    - Propose improvement options
    - Track voltage improvement costs
    """
    
    def __init__(self):
        """Initialize analyzer with economic parameters."""
        self.dm = DataManagerV2()
        
        # Load economic parameters
        econ_result = self.dm.get_economic_params()
        if econ_result.ok():
            self.voltage_penalties = econ_result.data.get("voltage_penalty", {})
            self.ens_cost = econ_result.data.get("energy_not_served_cost", 150)
        else:
            # Defaults
            self.voltage_penalties = {
                "below_0.90": 50,
                "below_0.95": 20,
                "above_1.05": 10
            }
            self.ens_cost = 150  # USD/MWh
        
        # Load validation limits
        limits_result = self.dm.get_validation_limits()
        if limits_result.ok():
            self.v_min_normal = limits_result.data.get("voltage_min_pu", 0.95)
            self.v_min_emergency = limits_result.data.get("voltage_emergency_min_pu", 0.90)
        else:
            self.v_min_normal = 0.95
            self.v_min_emergency = 0.90
        
        # Load alternative costs
        alt_costs_result = self.dm.get_alternative_costs()
        if alt_costs_result.ok():
            self.alternative_costs = alt_costs_result.data
        else:
            self.alternative_costs = {}
        
        # Voltage sensitivity (from Phase 3 data)
        self.dv_dp = -0.112  # pu/MW for Maquinchao (worst case)
        
        logger.info("LowVoltageAnalyzer initialized")
    
    def analyze_voltage_violations(self, network_state: Dict[str, Any]) -> LowVoltageAnalysisResult:
        """
        Analyze voltage violations in the network.
        
        Args:
            network_state: Dictionary containing:
                - node_voltages: Dict[node_id, voltage_pu]
                - node_loads: Dict[node_id, load_mw]
                - duration_hours: Analysis period (default 1)
                
        Returns:
            Comprehensive analysis results
        """
        node_voltages = network_state.get("node_voltages", {})
        node_loads = network_state.get("node_loads", {})
        duration_hours = network_state.get("duration_hours", 1.0)
        
        violations = []
        critical_nodes = []
        total_energy_at_risk = 0.0
        total_cost = 0.0
        
        # Analyze each node
        for node_id, v_pu in node_voltages.items():
            if v_pu < self.v_min_normal:
                # Determine severity
                if v_pu < 0.85:
                    severity = "critical"
                elif v_pu < self.v_min_emergency:
                    severity = "severe"
                else:
                    severity = "moderate"
                
                # Get load at node
                load_mw = node_loads.get(node_id, 0)
                
                # Calculate energy at risk
                if v_pu < self.v_min_emergency:
                    # Below emergency limit - high risk of outage
                    energy_at_risk = load_mw * duration_hours * 0.5  # 50% risk
                else:
                    # Below normal but above emergency
                    energy_at_risk = load_mw * duration_hours * 0.1  # 10% risk
                
                # Calculate cost
                if v_pu < self.v_min_emergency:
                    penalty = self.voltage_penalties.get("below_0.90", 50)
                else:
                    penalty = self.voltage_penalties.get("below_0.95", 20)
                
                cost = (load_mw * duration_hours * penalty) + (energy_at_risk * self.ens_cost)
                
                # Create violation record
                violation = VoltageViolation(
                    node_id=node_id,
                    voltage_pu=v_pu,
                    voltage_kv=v_pu * 33.0,  # Assuming 33kV base
                    severity=severity,
                    duration_hours=duration_hours,
                    energy_at_risk_mwh=energy_at_risk,
                    estimated_cost_usd=cost
                )
                
                violations.append(violation)
                total_energy_at_risk += energy_at_risk
                total_cost += cost
                
                if v_pu < self.v_min_emergency:
                    critical_nodes.append(node_id)
        
        # Find worst node
        worst_node = ""
        worst_voltage = 1.0
        for node_id, v_pu in node_voltages.items():
            if v_pu < worst_voltage:
                worst_voltage = v_pu
                worst_node = node_id
        
        # Calculate summary statistics
        voltages = list(node_voltages.values())
        summary_stats = {
            "mean_voltage_pu": np.mean(voltages),
            "std_voltage_pu": np.std(voltages),
            "min_voltage_pu": np.min(voltages),
            "max_voltage_pu": np.max(voltages),
            "percent_below_095": (sum(1 for v in voltages if v < 0.95) / len(voltages)) * 100
        }
        
        # Generate improvement options
        improvement_options = self._generate_improvement_options(violations, network_state)
        
        result = LowVoltageAnalysisResult(
            total_nodes=len(node_voltages),
            nodes_below_095=sum(1 for v in voltages if v < 0.95),
            nodes_below_090=sum(1 for v in voltages if v < 0.90),
            critical_nodes=critical_nodes,
            total_energy_at_risk_mwh=total_energy_at_risk,
            total_cost_violations_usd=total_cost,
            worst_node=worst_node,
            worst_voltage_pu=worst_voltage,
            violations=violations,
            improvement_options=improvement_options,
            summary_stats=summary_stats
        )
        
        # Log summary
        logger.info(f"Low voltage analysis: {result.nodes_below_095}/{result.total_nodes} nodes "
                   f"below 0.95 pu, cost: ${result.total_cost_violations_usd:,.0f}")
        
        return result
    
    def calculate_voltage_improvement_cost(self, node_id: str, current_v_pu: float,
                                         target_v_pu: float = 0.95) -> Dict[str, VoltageImprovementOption]:
        """
        Calculate cost of different options to improve voltage.
        
        Args:
            node_id: Node to improve
            current_v_pu: Current voltage
            target_v_pu: Target voltage (default 0.95)
            
        Returns:
            Dictionary of improvement options by method
        """
        delta_v_required = target_v_pu - current_v_pu
        options = {}
        
        # Option 1: Capacitor bank
        if delta_v_required > 0:
            # Estimate MVAr needed (simplified)
            mvar_needed = delta_v_required * 10  # Rough estimate
            cap_cost = self.alternative_costs.get("traditional", {}).get("capacitor_bank", 50000)
            
            options["capacitor"] = VoltageImprovementOption(
                node_id=node_id,
                method="capacitor",
                delta_v_pu=delta_v_required,
                cost_usd=cap_cost * mvar_needed,
                cost_per_pu=(cap_cost * mvar_needed) / delta_v_required,
                implementation_days=60,
                description=f"Install {mvar_needed:.1f} MVAr capacitor bank"
            )
        
        # Option 2: Distributed Generation (thermal)
        # Using sensitivity dV/dP
        mw_needed = abs(delta_v_required / self.dv_dp)
        gd_cost_per_mwh = self.alternative_costs.get("gd_thermal", {}).get("opex_mwh", 122.7)
        annual_hours = 4 * 365  # 4h/day operation
        annual_cost = mw_needed * annual_hours * gd_cost_per_mwh
        
        options["gd_thermal"] = VoltageImprovementOption(
            node_id=node_id,
            method="gd_thermal",
            delta_v_pu=delta_v_required,
            cost_usd=annual_cost * 10,  # 10-year equivalent
            cost_per_pu=(annual_cost * 10) / delta_v_required,
            implementation_days=180,
            description=f"Add {mw_needed:.1f} MW thermal generation"
        )
        
        # Option 3: Solar PV
        pv_capex = self.alternative_costs.get("pv_distributed", {}).get("capex_usd_per_kw", 850)
        pv_cost = mw_needed * 1000 * pv_capex
        
        options["pv_distributed"] = VoltageImprovementOption(
            node_id=node_id,
            method="pv_distributed",
            delta_v_pu=delta_v_required,
            cost_usd=pv_cost,
            cost_per_pu=pv_cost / delta_v_required,
            implementation_days=120,
            description=f"Install {mw_needed:.1f} MW solar PV"
        )
        
        return options
    
    def _generate_improvement_options(self, violations: List[VoltageViolation],
                                    network_state: Dict[str, Any]) -> List[VoltageImprovementOption]:
        """Generate improvement options for worst violations."""
        options = []
        
        # Sort violations by severity
        sorted_violations = sorted(violations, key=lambda v: v.voltage_pu)
        
        # Generate options for worst 5 nodes
        for violation in sorted_violations[:5]:
            node_options = self.calculate_voltage_improvement_cost(
                violation.node_id,
                violation.voltage_pu
            )
            
            # Add best option for each node
            if node_options:
                best_option = min(node_options.values(), key=lambda x: x.cost_per_pu)
                options.append(best_option)
        
        return options
    
    def analyze_temporal_patterns(self, hourly_states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze voltage patterns over 24 hours.
        
        Identifies:
        - Hours with worst violations
        - Total energy at risk
        - Peak violation periods
        """
        hourly_results = []
        
        for hour, state in enumerate(hourly_states):
            result = self.analyze_voltage_violations(state)
            hourly_results.append({
                "hour": hour,
                "nodes_below_095": result.nodes_below_095,
                "worst_voltage": result.worst_voltage_pu,
                "cost_usd": result.total_cost_violations_usd,
                "energy_at_risk_mwh": result.total_energy_at_risk_mwh
            })
        
        # Aggregate results
        df = pd.DataFrame(hourly_results)
        
        analysis = {
            "worst_hour": int(df.loc[df['worst_voltage'].idxmin(), 'hour']),
            "worst_voltage_day": float(df['worst_voltage'].min()),
            "total_cost_day_usd": float(df['cost_usd'].sum()),
            "total_energy_at_risk_day_mwh": float(df['energy_at_risk_mwh'].sum()),
            "peak_violation_hours": df[df['nodes_below_095'] == df['nodes_below_095'].max()]['hour'].tolist(),
            "hourly_pattern": df.to_dict('records')
        }
        
        return analysis
    
    def compare_alternatives(self, base_state: Dict[str, Any],
                           alternative_states: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """
        Compare voltage improvement from different alternatives.
        
        Args:
            base_state: Current network state
            alternative_states: Dict of alternative_name -> network_state
            
        Returns:
            DataFrame comparing alternatives
        """
        results = []
        
        # Analyze base case
        base_result = self.analyze_voltage_violations(base_state)
        
        # Analyze each alternative
        for alt_name, alt_state in alternative_states.items():
            alt_result = self.analyze_voltage_violations(alt_state)
            
            # Calculate improvements
            improvement = {
                "alternative": alt_name,
                "nodes_improved": base_result.nodes_below_095 - alt_result.nodes_below_095,
                "worst_voltage_improvement_pu": alt_result.worst_voltage_pu - base_result.worst_voltage_pu,
                "cost_reduction_usd": base_result.total_cost_violations_usd - alt_result.total_cost_violations_usd,
                "energy_risk_reduction_mwh": base_result.total_energy_at_risk_mwh - alt_result.total_energy_at_risk_mwh,
                "remaining_violations": alt_result.nodes_below_095
            }
            
            results.append(improvement)
        
        return pd.DataFrame(results).sort_values('cost_reduction_usd', ascending=False)


# Convenience function for quick analysis
def analyze_current_network_voltage() -> LowVoltageAnalysisResult:
    """Quick analysis of current network voltage state."""
    analyzer = LowVoltageAnalyzer()
    dm = DataManagerV2()
    
    # Get latest voltage data
    # This would need to be implemented based on actual data source
    # For now, return a placeholder
    
    logger.warning("analyze_current_network_voltage needs real-time data implementation")
    
    # Placeholder network state
    network_state = {
        "node_voltages": {
            "pilcaniyeu": 0.95,
            "jacobacci": 0.92,
            "maquinchao": 0.89,  # Critical
            "los_menucos": 0.91
        },
        "node_loads": {
            "pilcaniyeu": 2.5,
            "jacobacci": 1.8,
            "maquinchao": 3.2,
            "los_menucos": 2.1
        },
        "duration_hours": 1.0
    }
    
    return analyzer.analyze_voltage_violations(network_state)