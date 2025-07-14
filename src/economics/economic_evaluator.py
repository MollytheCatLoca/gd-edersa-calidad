"""
Economic Evaluator for Power System Alternatives
Evaluates NPV of different solutions to voltage problems
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Setup paths
import sys
from pathlib import Path
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dashboard.pages.utils.constants import ECONOMIC_PARAMS, ALTERNATIVE_COSTS
from src.power_flow.dc_power_flow import DCPowerFlow, PowerFlowResult

logger = logging.getLogger(__name__)


@dataclass
class CashFlow:
    """Represents cash flows over project lifetime."""
    year: int
    capex: float  # Capital expenditure
    opex: float   # Operating expenditure
    revenue: float  # Revenue or savings
    net_flow: float  # Net cash flow
    discounted_flow: float  # Present value


@dataclass
class EconomicResult:
    """Economic evaluation results."""
    alternative: str
    npv: float  # Net Present Value
    irr: float  # Internal Rate of Return
    payback_years: float
    lcoe: float  # Levelized Cost of Energy
    benefit_cost_ratio: float
    cash_flows: List[CashFlow]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "alternative": self.alternative,
            "npv_usd": self.npv,
            "irr_percent": self.irr * 100,
            "payback_years": self.payback_years,
            "lcoe_usd_mwh": self.lcoe,
            "benefit_cost_ratio": self.benefit_cost_ratio
        }


class EconomicEvaluator:
    """
    Evaluates economic viability of power system alternatives.
    
    Alternatives:
    1. Traditional grid reinforcement
    2. Distributed Generation (thermal)
    3. Distributed PV + BESS
    """
    
    def __init__(self, discount_rate: float = None, project_lifetime: int = None):
        """
        Initialize economic evaluator.
        
        Args:
            discount_rate: Annual discount rate (default from constants)
            project_lifetime: Project lifetime in years (default from constants)
        """
        self.discount_rate = discount_rate or ECONOMIC_PARAMS["discount_rate"]
        self.project_lifetime = project_lifetime or ECONOMIC_PARAMS.get("analysis_period", 25)
        # Energy prices - create default structure if not available
        self.energy_prices = {
            "spot": 62.5,  # Average tariff
            "peak": 80.0,  # Peak hours
            "gd": 122.7    # GD cost from Phase 3
        }
        self.ens_cost = ECONOMIC_PARAMS.get("energy_not_served_cost", 150)
        
        # Load alternative costs
        self.alt_costs = ALTERNATIVE_COSTS
        
        # Initialize power flow for technical analysis
        self.pf = DCPowerFlow()
        
        logger.info(f"Economic evaluator initialized: {self.discount_rate:.1%} discount rate, "
                   f"{self.project_lifetime} year lifetime")
    
    def evaluate_all_alternatives(self, load_scenario: Dict[str, float],
                                baseline_voltage_pu: float = 0.90) -> List[EconomicResult]:
        """
        Evaluate all alternatives for given load scenario.
        
        Args:
            load_scenario: Load in MW per node
            baseline_voltage_pu: Current average voltage
            
        Returns:
            List of economic results for each alternative
        """
        results = []
        
        # 1. Traditional grid reinforcement
        traditional_result = self._evaluate_traditional(load_scenario, baseline_voltage_pu)
        results.append(traditional_result)
        
        # 2. Distributed Generation expansion
        dg_result = self._evaluate_dg_expansion(load_scenario, baseline_voltage_pu)
        results.append(dg_result)
        
        # 3. PV + BESS solution
        pv_result = self._evaluate_pv_bess(load_scenario, baseline_voltage_pu)
        results.append(pv_result)
        
        return results
    
    def _evaluate_traditional(self, load_scenario: Dict[str, float],
                            baseline_voltage_pu: float) -> EconomicResult:
        """Evaluate traditional grid reinforcement."""
        alt_name = "traditional"
        costs = self.alt_costs[alt_name]
        
        # Calculate required capacity
        total_load = sum(load_scenario.values())
        required_capacity = total_load * 1.5  # 50% margin
        
        # Capital costs - assume new line construction for voltage support
        line_length = 100  # km of line reinforcement needed
        capex = costs["new_line_33kv"] * line_length + costs["voltage_regulator"] * 2
        
        # Annual costs
        annual_opex = capex * costs["opex_percent"]
        
        # Benefits: reduced losses and improved reliability
        # Assume 5% loss reduction and 99% reliability improvement
        annual_energy = total_load * 8760 * 0.3  # 30% capacity factor
        loss_savings = annual_energy * 0.05 * self.energy_prices["spot"]
        reliability_savings = annual_energy * 0.01 * self.ens_cost
        
        annual_benefits = loss_savings + reliability_savings
        
        # Generate cash flows
        cash_flows = self._generate_cash_flows(
            capex, annual_opex, annual_benefits, alt_name
        )
        
        # Calculate metrics
        npv = self._calculate_npv(cash_flows)
        irr = self._calculate_irr(cash_flows)
        payback = self._calculate_payback(cash_flows)
        lcoe = self._calculate_lcoe(capex, annual_opex, annual_energy)
        bcr = sum(cf.revenue for cf in cash_flows) / (capex + sum(cf.opex for cf in cash_flows))
        
        return EconomicResult(
            alternative=alt_name,
            npv=npv,
            irr=irr,
            payback_years=payback,
            lcoe=lcoe,
            benefit_cost_ratio=bcr,
            cash_flows=cash_flows
        )
    
    def _evaluate_dg_expansion(self, load_scenario: Dict[str, float],
                             baseline_voltage_pu: float) -> EconomicResult:
        """Evaluate distributed generation expansion."""
        alt_name = "gd_thermal"
        costs = self.alt_costs[alt_name]
        
        # Size DG to meet 30% of peak load
        total_load = sum(load_scenario.values())
        dg_capacity = total_load * 0.3
        
        # Capital and operating costs (rental model)
        capex = costs["capex_expansion"]  # Zero for rental
        hours_per_year = costs["availability_hours"] * 365
        annual_generation = dg_capacity * hours_per_year * costs["capacity_factor"]
        annual_opex = annual_generation * costs["opex_mwh"] + costs["startup_cost"] * 365
        
        # Benefits: avoided grid energy and improved local voltage
        avoided_grid_cost = annual_generation * self.energy_prices["spot"]  # Avoid spot price
        voltage_benefit = annual_generation * 0.1 * self.ens_cost  # 10% reliability improvement
        
        annual_benefits = avoided_grid_cost + voltage_benefit
        
        # Generate cash flows
        cash_flows = self._generate_cash_flows(
            capex, annual_opex, annual_benefits, alt_name
        )
        
        # Calculate metrics
        npv = self._calculate_npv(cash_flows)
        irr = self._calculate_irr(cash_flows)
        payback = self._calculate_payback(cash_flows)
        lcoe = self._calculate_lcoe(capex, annual_opex, annual_generation)
        bcr = sum(cf.revenue for cf in cash_flows) / (capex + sum(cf.opex for cf in cash_flows))
        
        return EconomicResult(
            alternative=alt_name,
            npv=npv,
            irr=irr,
            payback_years=payback,
            lcoe=lcoe,
            benefit_cost_ratio=bcr,
            cash_flows=cash_flows
        )
    
    def _evaluate_pv_bess(self, load_scenario: Dict[str, float],
                         baseline_voltage_pu: float) -> EconomicResult:
        """Evaluate PV + BESS solution."""
        alt_name = "pv_distributed"
        pv_costs = self.alt_costs[alt_name]
        bess_costs = self.alt_costs["bess"]
        
        # Size PV for 50% of peak load, BESS for 4 hours
        total_load = sum(load_scenario.values())
        pv_capacity = total_load * 0.5
        bess_power = pv_capacity * 0.5
        bess_energy = bess_power * 4  # 4-hour storage
        
        # Capital costs
        pv_capex = pv_costs["capex_usd_per_kw"] * pv_capacity * 1000  # Convert MW to kW
        bess_capex = (bess_costs["capex_power_usd_per_kw"] * bess_power * 1000 + 
                     bess_costs["capex_energy_usd_per_kwh"] * bess_energy * 1000)
        capex = pv_capex + bess_capex
        
        # Operating costs
        pv_opex = pv_costs["opex_usd_per_kw_year"] * pv_capacity * 1000
        bess_opex = bess_capex * bess_costs["opex_percent"]
        annual_opex = pv_opex + bess_opex
        
        # Benefits
        # PV generation: 20% capacity factor in Patagonia
        annual_pv_generation = pv_capacity * 8760 * 0.20
        
        # Energy arbitrage with BESS
        bess_cycles = min(bess_costs["cycles_per_year"], 250)
        annual_bess_throughput = bess_energy * bess_cycles * bess_costs["efficiency"]
        
        # Total benefits
        energy_value = annual_pv_generation * self.energy_prices["spot"]
        arbitrage_value = annual_bess_throughput * (self.energy_prices["peak"] - self.energy_prices["spot"])
        voltage_support = (annual_pv_generation + annual_bess_throughput) * 0.15 * self.ens_cost
        
        annual_benefits = energy_value + arbitrage_value + voltage_support
        
        # Generate cash flows
        cash_flows = self._generate_cash_flows(
            capex, annual_opex, annual_benefits, alt_name
        )
        
        # Calculate metrics
        npv = self._calculate_npv(cash_flows)
        irr = self._calculate_irr(cash_flows)
        payback = self._calculate_payback(cash_flows)
        lcoe = self._calculate_lcoe(capex, annual_opex, annual_pv_generation + annual_bess_throughput)
        bcr = sum(cf.revenue for cf in cash_flows) / (capex + sum(cf.opex for cf in cash_flows))
        
        return EconomicResult(
            alternative=alt_name,
            npv=npv,
            irr=irr,
            payback_years=payback,
            lcoe=lcoe,
            benefit_cost_ratio=bcr,
            cash_flows=cash_flows
        )
    
    def _generate_cash_flows(self, capex: float, annual_opex: float,
                           annual_revenue: float, alternative: str) -> List[CashFlow]:
        """Generate cash flows over project lifetime."""
        cash_flows = []
        
        for year in range(self.project_lifetime + 1):
            if year == 0:
                # Initial investment
                cf = CashFlow(
                    year=year,
                    capex=capex,
                    opex=0,
                    revenue=0,
                    net_flow=-capex,
                    discounted_flow=-capex
                )
            else:
                # Operating years
                # Degradation factor for PV/BESS
                if "pv" in alternative:
                    degradation = 0.995 ** year  # 0.5% annual degradation
                else:
                    degradation = 1.0
                
                revenue = annual_revenue * degradation
                net_flow = revenue - annual_opex
                discount_factor = 1 / (1 + self.discount_rate) ** year
                
                cf = CashFlow(
                    year=year,
                    capex=0,
                    opex=annual_opex,
                    revenue=revenue,
                    net_flow=net_flow,
                    discounted_flow=net_flow * discount_factor
                )
            
            cash_flows.append(cf)
        
        return cash_flows
    
    def _calculate_npv(self, cash_flows: List[CashFlow]) -> float:
        """Calculate Net Present Value."""
        return sum(cf.discounted_flow for cf in cash_flows)
    
    def _calculate_irr(self, cash_flows: List[CashFlow]) -> float:
        """Calculate Internal Rate of Return."""
        # Create array of net cash flows
        flows = [cf.net_flow for cf in cash_flows]
        
        try:
            # Use numpy's irr function (deprecated, using npf.irr)
            irr = np.real(np.irr(flows))  # Take real part only
            if not np.isnan(irr) and -0.99 < irr < 10:  # Reasonable bounds
                return float(irr)
            else:
                # Fallback to simple calculation
                total_return = sum(flows[1:])  # Exclude initial investment
                initial_investment = -flows[0] if flows[0] < 0 else 1.0
                if initial_investment > 0 and total_return > 0:
                    simple_return = (total_return / initial_investment) ** (1/self.project_lifetime) - 1
                    return max(-0.99, min(simple_return, 1.0))  # Cap at reasonable values
                return -0.99 if total_return < 0 else 0.0
        except:
            return 0.0
    
    def _calculate_payback(self, cash_flows: List[CashFlow]) -> float:
        """Calculate simple payback period."""
        cumulative = 0
        initial_investment = -cash_flows[0].net_flow
        
        for cf in cash_flows[1:]:
            cumulative += cf.net_flow
            if cumulative >= initial_investment:
                # Interpolate to get fractional year
                prev_cumulative = cumulative - cf.net_flow
                fraction = (initial_investment - prev_cumulative) / cf.net_flow
                return cf.year - 1 + fraction
        
        return float('inf')  # Never pays back
    
    def _calculate_lcoe(self, capex: float, annual_opex: float, 
                       annual_energy: float) -> float:
        """Calculate Levelized Cost of Energy."""
        if annual_energy <= 0:
            return float('inf')
        
        # Total discounted costs
        total_cost = capex
        for year in range(1, self.project_lifetime + 1):
            discount_factor = 1 / (1 + self.discount_rate) ** year
            total_cost += annual_opex * discount_factor
        
        # Total discounted energy
        total_energy = 0
        for year in range(1, self.project_lifetime + 1):
            discount_factor = 1 / (1 + self.discount_rate) ** year
            total_energy += annual_energy * discount_factor
        
        return total_cost / total_energy if total_energy > 0 else float('inf')
    
    def sensitivity_analysis(self, load_scenario: Dict[str, float],
                           parameter: str, variation_range: List[float]) -> pd.DataFrame:
        """
        Perform sensitivity analysis on key parameters.
        
        Args:
            load_scenario: Load scenario to analyze
            parameter: Parameter to vary (e.g., 'discount_rate', 'energy_price')
            variation_range: Range of values to test
            
        Returns:
            DataFrame with sensitivity results
        """
        results = []
        original_value = getattr(self, parameter, None)
        
        for value in variation_range:
            # Update parameter
            if parameter == 'discount_rate':
                self.discount_rate = value
            elif parameter == 'energy_price':
                self.energy_prices["spot"] = value
            
            # Evaluate all alternatives
            alt_results = self.evaluate_all_alternatives(load_scenario)
            
            # Store results
            for alt in alt_results:
                results.append({
                    parameter: value,
                    'alternative': alt.alternative,
                    'npv': alt.npv,
                    'irr': alt.irr,
                    'lcoe': alt.lcoe
                })
        
        # Restore original value
        if original_value is not None:
            setattr(self, parameter, original_value)
        
        return pd.DataFrame(results)


def test_economic_evaluator():
    """Test economic evaluation functionality."""
    evaluator = EconomicEvaluator()
    
    # Test scenario: peak load conditions
    load_scenario = {
        "pilcaniyeu": 3.5,
        "jacobacci": 2.5,
        "maquinchao": 4.5,
        "los_menucos": 3.0
    }
    
    print("Economic Evaluation Results")
    print("="*60)
    print(f"Load scenario: {sum(load_scenario.values()):.1f} MW total")
    
    # Evaluate all alternatives
    results = evaluator.evaluate_all_alternatives(load_scenario)
    
    # Display results
    for result in results:
        print(f"\n{result.alternative.upper()}:")
        print(f"  NPV: ${result.npv:,.0f}")
        print(f"  IRR: {result.irr:.1%}")
        print(f"  Payback: {result.payback_years:.1f} years")
        print(f"  LCOE: ${result.lcoe:.2f}/MWh")
        print(f"  B/C Ratio: {result.benefit_cost_ratio:.2f}")
    
    # Sensitivity analysis
    print("\nSensitivity Analysis - Discount Rate")
    print("-"*40)
    sensitivity_df = evaluator.sensitivity_analysis(
        load_scenario, 
        'discount_rate',
        [0.06, 0.08, 0.10, 0.12]
    )
    print(sensitivity_df.pivot(index='discount_rate', columns='alternative', values='npv'))


if __name__ == "__main__":
    test_economic_evaluator()