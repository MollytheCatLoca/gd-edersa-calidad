#!/usr/bin/env python3
"""
Complete test suite for Phase 5.1
Tests all validators, data manager integration, and economic calculations
"""

import sys
import unittest
from pathlib import Path
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.validation.power_balance import PowerBalanceValidator, validate_typical_day
from src.validation.kirchhoff_laws import KirchhoffValidator, check_node_current_balance
from src.validation.low_voltage_analyzer import LowVoltageAnalyzer
from dashboard.pages.utils.data_manager_v2 import DataManagerV2
from dashboard.pages.utils.constants import (
    ELECTRICAL_PARAMS, VALIDATION_LIMITS, ECONOMIC_PARAMS, 
    ALTERNATIVE_COSTS, PHASE5_CACHE_CONFIG
)


class TestPhase5Parameters(unittest.TestCase):
    """Test Phase 5 parameters loaded correctly."""
    
    def setUp(self):
        self.dm = DataManagerV2()
    
    def test_electrical_params_loaded(self):
        """Test electrical parameters are accessible."""
        result = self.dm.get_electrical_params()
        self.assertTrue(result.ok())
        self.assertIn("conductor_types", result.data)
        self.assertIn("power_flow_config", result.data)
        self.assertEqual(result.data["power_flow_config"]["max_iterations"], 10)
    
    def test_validation_limits_loaded(self):
        """Test validation limits are accessible."""
        result = self.dm.get_validation_limits()
        self.assertTrue(result.ok())
        self.assertIn("voltage_min_pu", result.data)
        self.assertEqual(result.data["voltage_min_pu"], 0.95)
        self.assertEqual(result.data["power_balance_tolerance"], 0.001)
    
    def test_economic_params_loaded(self):
        """Test economic parameters are accessible."""
        result = self.dm.get_economic_params()
        self.assertTrue(result.ok())
        self.assertIn("discount_rate", result.data)
        self.assertEqual(result.data["discount_rate"], 0.08)
        self.assertEqual(result.data["energy_not_served_cost"], 150)
    
    def test_alternative_costs_loaded(self):
        """Test alternative costs are accessible."""
        result = self.dm.get_alternative_costs()
        self.assertTrue(result.ok())
        self.assertIn("gd_thermal", result.data)
        self.assertIn("pv_distributed", result.data)
        self.assertEqual(result.data["gd_thermal"]["opex_mwh"], 122.7)
    
    def test_cache_config_loaded(self):
        """Test cache configuration is accessible."""
        result = self.dm.get_cache_config()
        self.assertTrue(result.ok())
        self.assertIn("redis", result.data)
        self.assertIn("lru", result.data)
        self.assertEqual(result.data["redis"]["port"], 6379)


class TestPowerBalanceValidator(unittest.TestCase):
    """Test power balance validation functionality."""
    
    def setUp(self):
        self.validator = PowerBalanceValidator()
    
    def test_balanced_network(self):
        """Test validation of balanced network."""
        # Calculate balanced network
        gen = {"pilcaniyeu": 5.0, "gd_los_menucos": 1.8}
        loads = {
            "pilcaniyeu": 2.5,
            "jacobacci": 1.8,
            "maquinchao": 1.2,
            "los_menucos": 1.0
        }
        line_losses = {
            "pilca_jacob": 0.1,
            "jacob_maqui": 0.08,
            "maqui_menu": 0.05
        }
        transformer_losses = {
            "xfmr_pilca": 0.02,
            "xfmr_jacob": 0.015,
            "xfmr_maqui": 0.01,
            "xfmr_menu": 0.015
        }
        
        # Ensure balance: add system import to match load + losses
        total_load = sum(loads.values())
        total_losses = sum(line_losses.values()) + sum(transformer_losses.values())
        total_gen_needed = total_load + total_losses
        current_gen = sum(gen.values())
        gen["system_import"] = total_gen_needed - current_gen
        
        network_state = {
            "generation": gen,
            "loads": loads,
            "line_losses": line_losses,
            "transformer_losses": transformer_losses
        }
        
        result = self.validator.validate(network_state)
        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.imbalance, 0.0, places=3)
    
    def test_imbalanced_network(self):
        """Test detection of imbalanced network."""
        network_state = {
            "generation": {"pilcaniyeu": 5.0},
            "loads": {"pilcaniyeu": 7.0},  # More load than generation
            "line_losses": {},
            "transformer_losses": {}
        }
        
        result = self.validator.validate(network_state)
        self.assertFalse(result.is_valid)
        self.assertLess(result.imbalance, 0)  # Negative imbalance
        self.assertEqual(len(result.violations), 1)
    
    def test_high_losses_detection(self):
        """Test detection of high losses."""
        network_state = {
            "generation": {"pilcaniyeu": 10.0},
            "loads": {"pilcaniyeu": 8.0},
            "line_losses": {"pilca_jacob": 1.5},  # 15% losses
            "transformer_losses": {"xfmr_pilca": 0.5}
        }
        
        result = self.validator.validate(network_state)
        violations_types = [v["type"] for v in result.violations]
        self.assertIn("high_losses", violations_types)
    
    def test_gd_contribution(self):
        """Test validation with GD contribution."""
        network_state = {
            "generation": {"pilcaniyeu": 5.0},
            "loads": {"total": 6.5},
            "line_losses": {"total": 0.3},
            "transformer_losses": {"total": 0.05}
        }
        
        # Without GD - should be imbalanced
        result1 = self.validator.validate(network_state)
        self.assertFalse(result1.is_valid)
        
        # With GD - should be balanced
        result2 = self.validator.validate_with_gd(network_state, gd_output=1.85)
        self.assertTrue(result2.is_valid)
        self.assertIn("gd_contribution", result2.details)


class TestKirchhoffValidator(unittest.TestCase):
    """Test Kirchhoff laws validation functionality."""
    
    def setUp(self):
        self.validator = KirchhoffValidator()
    
    def test_current_balance_at_node(self):
        """Test current balance validation at single node."""
        # Node with 2 MW load at 0.92 pu
        line_flows = {
            "line_in": 45.0,  # A
            "line_out": 0.0
        }
        
        violation = self.validator.validate_current_law(
            node_id="test_node",
            line_flows=line_flows,
            load_current=45.0,
            generation_current=0.0
        )
        
        self.assertIsNone(violation)  # Balanced
    
    def test_current_imbalance_detection(self):
        """Test detection of current imbalance."""
        line_flows = {
            "line_in": 50.0,
            "line_out": -10.0  # Negative for outgoing
        }
        
        violation = self.validator.validate_current_law(
            node_id="test_node",
            line_flows=line_flows,
            load_current=35.0,  # Should be 40.0
            generation_current=0.0
        )
        
        self.assertIsNotNone(violation)
        self.assertEqual(violation.law_type, "current")
        self.assertAlmostEqual(violation.imbalance, 5.0, places=1)
    
    def test_network_validation(self):
        """Test network-wide Kirchhoff validation."""
        network_state = {
            "node_currents": {
                "pilcaniyeu": {
                    "load_current": 30.0,
                    "generation_current": 100.0,
                    "line_flows": {
                        "to_comallo": -40.0,
                        "to_jacobacci": -30.0
                    }
                },
                "jacobacci": {
                    "load_current": 30.0,
                    "generation_current": 0.0,
                    "line_flows": {
                        "from_pilcaniyeu": 30.0
                    }
                }
            },
            "node_voltages": {
                "pilcaniyeu": 33.0,
                "jacobacci": 31.35
            },
            "line_voltage_drops": {}
        }
        
        result = self.validator.validate_network(network_state)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.nodes_checked, 2)
    
    def test_quick_current_balance_check(self):
        """Test quick current balance helper function."""
        # 2 MW at 0.9 PF, 30.5 kV
        # Q = P * tan(acos(PF)) = 2.0 * tan(acos(0.9)) = 2.0 * 0.484 = 0.968 MVAr
        # S = P / PF = 2.0 / 0.9 = 2.222 MVA
        # I = S / (sqrt(3) * V) = 2222 / (1.732 * 30.5) = 42.05 A
        
        # Create a balanced scenario with correct tolerance
        p_mw = 2.0
        pf = 0.9
        v_kv = 30.5
        s_mva = p_mw / pf
        i_calc = (s_mva * 1000) / (np.sqrt(3) * v_kv)
        
        is_balanced = check_node_current_balance(
            node_id="test",
            p_mw=p_mw,
            q_mvar=p_mw * np.tan(np.arccos(pf)),
            v_kv=v_kv,
            line_currents={"line1": i_calc}  # Use exact calculated current
        )
        
        self.assertTrue(is_balanced)


class TestLowVoltageAnalyzer(unittest.TestCase):
    """Test low voltage analysis functionality."""
    
    def setUp(self):
        self.analyzer = LowVoltageAnalyzer()
    
    def test_voltage_violation_detection(self):
        """Test detection of voltage violations."""
        network_state = {
            "node_voltages": {
                "node1": 0.96,  # OK
                "node2": 0.94,  # Below normal
                "node3": 0.89,  # Below emergency
                "node4": 0.85   # Critical
            },
            "node_loads": {
                "node1": 1.0,
                "node2": 2.0,
                "node3": 3.0,
                "node4": 1.5
            },
            "duration_hours": 1.0
        }
        
        result = self.analyzer.analyze_voltage_violations(network_state)
        
        self.assertEqual(result.total_nodes, 4)
        self.assertEqual(result.nodes_below_095, 3)
        self.assertEqual(result.nodes_below_090, 2)
        self.assertEqual(len(result.critical_nodes), 2)
        self.assertEqual(result.worst_node, "node4")
        self.assertAlmostEqual(result.worst_voltage_pu, 0.85)
    
    def test_energy_at_risk_calculation(self):
        """Test calculation of energy at risk."""
        network_state = {
            "node_voltages": {
                "critical": 0.88,  # High risk
                "moderate": 0.93   # Low risk
            },
            "node_loads": {
                "critical": 2.0,
                "moderate": 3.0
            },
            "duration_hours": 2.0
        }
        
        result = self.analyzer.analyze_voltage_violations(network_state)
        
        # Critical: 2 MW * 2h * 0.5 = 2 MWh at risk
        # Moderate: 3 MW * 2h * 0.1 = 0.6 MWh at risk
        self.assertAlmostEqual(result.total_energy_at_risk_mwh, 2.6, places=1)
    
    def test_improvement_cost_calculation(self):
        """Test voltage improvement cost calculations."""
        options = self.analyzer.calculate_voltage_improvement_cost(
            node_id="test_node",
            current_v_pu=0.90,
            target_v_pu=0.95
        )
        
        self.assertIn("capacitor", options)
        self.assertIn("gd_thermal", options)
        self.assertIn("pv_distributed", options)
        
        # Check all options have required fields
        for method, option in options.items():
            self.assertAlmostEqual(option.delta_v_pu, 0.05, places=2)
            self.assertGreater(option.cost_usd, 0)
            self.assertGreater(option.cost_per_pu, 0)
    
    def test_temporal_pattern_analysis(self):
        """Test 24-hour temporal pattern analysis."""
        # Create varying voltage conditions
        hourly_states = []
        for hour in range(24):
            if 18 <= hour <= 22:  # Peak hours
                v_factor = 0.95
            else:
                v_factor = 1.0
            
            hourly_states.append({
                "node_voltages": {
                    "node1": 0.92 * v_factor,
                    "node2": 0.89 * v_factor
                },
                "node_loads": {
                    "node1": 2.0,
                    "node2": 1.5
                },
                "duration_hours": 1.0
            })
        
        temporal = self.analyzer.analyze_temporal_patterns(hourly_states)
        
        self.assertIn("worst_hour", temporal)
        self.assertIn("total_cost_day_usd", temporal)
        self.assertIn("peak_violation_hours", temporal)
        self.assertTrue(18 <= temporal["worst_hour"] <= 22)
    
    def test_alternatives_comparison(self):
        """Test comparison of improvement alternatives."""
        base_state = {
            "node_voltages": {"node1": 0.90, "node2": 0.92},
            "node_loads": {"node1": 2.0, "node2": 1.5},
            "duration_hours": 1.0
        }
        
        alternatives = {
            "capacitor": {
                "node_voltages": {"node1": 0.94, "node2": 0.95},
                "node_loads": {"node1": 2.0, "node2": 1.5},
                "duration_hours": 1.0
            },
            "pv": {
                "node_voltages": {"node1": 0.95, "node2": 0.96},
                "node_loads": {"node1": 2.0, "node2": 1.5},
                "duration_hours": 1.0
            }
        }
        
        comparison = self.analyzer.compare_alternatives(base_state, alternatives)
        
        self.assertEqual(len(comparison), 2)
        self.assertIn("alternative", comparison.columns)
        self.assertIn("nodes_improved", comparison.columns)
        self.assertIn("cost_reduction_usd", comparison.columns)


class TestIntegration(unittest.TestCase):
    """Integration tests for Phase 5.1 components."""
    
    def setUp(self):
        self.dm = DataManagerV2()
        self.pv = PowerBalanceValidator()
        self.kv = KirchhoffValidator()
        self.lva = LowVoltageAnalyzer()
    
    def test_complete_network_validation(self):
        """Test complete validation workflow."""
        # Create realistic network state with proper balance
        loads = {
            "pilcaniyeu": 2.5,
            "jacobacci": 1.8,
            "maquinchao": 3.2,
            "los_menucos": 2.1
        }
        line_losses = {
            "pilca_jacob": 0.15,
            "jacob_maqui": 0.12,
            "maqui_menu": 0.08
        }
        transformer_losses = {
            "xfmr_pilca": 0.02,
            "xfmr_jacob": 0.015,
            "xfmr_maqui": 0.025,
            "xfmr_menu": 0.018
        }
        
        # Calculate required generation
        total_load = sum(loads.values())
        total_losses = sum(line_losses.values()) + sum(transformer_losses.values())
        total_gen_needed = total_load + total_losses
        
        network_state = {
            "generation": {
                "system_import": total_gen_needed - 1.8,
                "gd_los_menucos": 1.8
            },
            "loads": loads,
            "line_losses": line_losses,
            "transformer_losses": transformer_losses,
            "node_voltages": {
                "pilcaniyeu": 0.95,
                "jacobacci": 0.92,
                "maquinchao": 0.89,
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
        
        # Validate power balance
        pb_result = self.pv.validate(network_state)
        self.assertTrue(pb_result.is_valid)
        
        # Validate low voltage
        lv_result = self.lva.analyze_voltage_violations(network_state)
        self.assertEqual(lv_result.nodes_below_095, 3)
        self.assertGreater(lv_result.total_cost_violations_usd, 0)
        
        # Check economic parameters are used
        econ_params = self.dm.get_economic_params()
        self.assertTrue(econ_params.ok())
        self.assertEqual(
            self.lva.ens_cost, 
            econ_params.data["energy_not_served_cost"]
        )
    
    def test_typical_day_validation(self):
        """Test validation of a typical day."""
        # Create 24-hour data
        day_data = {}
        for hour in range(24):
            # Peak load at hour 20
            load_factor = 1.2 if 18 <= hour <= 22 else 0.8
            
            # Calculate balanced generation
            gd_gen = 0.5 if 10 <= hour <= 16 else 0.0
            load = 9.5 * load_factor
            line_loss = 0.4 * load_factor
            xfmr_loss = 0.1 * load_factor
            system_gen = load + line_loss + xfmr_loss - gd_gen
            
            day_data[f"hour_{hour}"] = {
                "generation": {
                    "system": system_gen,
                    "gd": gd_gen
                },
                "loads": {
                    "total": load
                },
                "line_losses": {
                    "total": line_loss
                },
                "transformer_losses": {
                    "total": xfmr_loss
                }
            }
        
        results = validate_typical_day(day_data)
        
        self.assertEqual(len(results), 24)
        # All hours should be balanced
        for i, result in enumerate(results):
            self.assertTrue(result.is_valid, f"Hour {i} not balanced")


class TestEconomicCalculations(unittest.TestCase):
    """Test economic calculations and NPV analysis."""
    
    def setUp(self):
        self.analyzer = LowVoltageAnalyzer()
        self.dm = DataManagerV2()
    
    def test_npv_calculation(self):
        """Test NPV calculation with correct parameters."""
        econ_params = self.dm.get_economic_params()
        self.assertTrue(econ_params.ok())
        
        discount_rate = econ_params.data["discount_rate"]
        years = econ_params.data["analysis_period"]
        
        # Annual benefit of $100,000
        annual_benefit = 100000
        
        # Calculate NPV manually
        npv = 0
        for year in range(1, years + 1):
            npv += annual_benefit / ((1 + discount_rate) ** year)
        
        # NPV should be positive and reasonable
        self.assertGreater(npv, 0)
        self.assertLess(npv, annual_benefit * years)  # Less than simple sum
        
        # Check NPV formula
        # For 8% discount rate, 25 years: factor ≈ 10.675
        pv_factor = ((1 + discount_rate) ** years - 1) / (discount_rate * (1 + discount_rate) ** years)
        calculated_npv = annual_benefit * pv_factor
        
        self.assertAlmostEqual(npv, calculated_npv, places=0)
    
    def test_cost_effectiveness_ranking(self):
        """Test ranking of alternatives by cost-effectiveness."""
        alternatives = [
            {"name": "capacitor", "cost": 50000, "benefit": 10000},
            {"name": "gd", "cost": 200000, "benefit": 30000},
            {"name": "pv", "cost": 150000, "benefit": 35000}
        ]
        
        # Calculate benefit/cost ratio
        for alt in alternatives:
            alt["bc_ratio"] = alt["benefit"] / alt["cost"]
        
        # Sort by B/C ratio
        ranked = sorted(alternatives, key=lambda x: x["bc_ratio"], reverse=True)
        
        # PV should be first (35k/150k = 0.233)
        self.assertEqual(ranked[0]["name"], "pv")
        # Capacitor second (10k/50k = 0.2)
        self.assertEqual(ranked[1]["name"], "capacitor")
        # GD last (30k/200k = 0.15)
        self.assertEqual(ranked[2]["name"], "gd")


def run_all_tests():
    """Run all Phase 5.1 tests."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test cases
    test_cases = [
        TestPhase5Parameters,
        TestPowerBalanceValidator,
        TestKirchhoffValidator,
        TestLowVoltageAnalyzer,
        TestIntegration,
        TestEconomicCalculations
    ]
    
    for test_case in test_cases:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_case)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("PHASE 5.1 TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All Phase 5.1 tests passed!")
    else:
        print("\n❌ Some tests failed. See details above.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)