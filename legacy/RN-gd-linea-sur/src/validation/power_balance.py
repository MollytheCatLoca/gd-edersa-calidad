"""
Power Balance Validator for Phase 5
Validates P_gen = P_load + P_losses within tolerance
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
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
class PowerBalanceResult:
    """Results from power balance validation"""
    is_valid: bool
    total_generation: float  # MW
    total_load: float  # MW
    total_losses: float  # MW
    imbalance: float  # MW
    imbalance_percent: float  # %
    details: Dict[str, Any]
    violations: List[Dict[str, Any]]


class PowerBalanceValidator:
    """
    Validates power balance in the network.
    
    Key equation: P_gen = P_load + P_losses
    
    For networks with V < 0.95 pu, special attention to:
    - Higher losses due to low voltage
    - Potential measurement errors
    - GD contribution accounting
    """
    
    def __init__(self, tolerance: float = None):
        """
        Initialize validator.
        
        Args:
            tolerance: Maximum allowed imbalance (default from constants)
        """
        self.dm = DataManagerV2()
        
        # Get validation limits
        limits_result = self.dm.get_validation_limits()
        if limits_result.ok():
            self.tolerance = tolerance or limits_result.data.get("power_balance_tolerance", 0.001)
        else:
            self.tolerance = tolerance or 0.001  # 0.1% default
            
        logger.info(f"PowerBalanceValidator initialized with tolerance: {self.tolerance*100:.2f}%")
    
    def validate(self, network_state: Dict[str, Any]) -> PowerBalanceResult:
        """
        Validate power balance for given network state.
        
        Args:
            network_state: Dictionary containing:
                - generation: Dict[node_id, float] - MW per generator
                - loads: Dict[node_id, float] - MW per load  
                - line_losses: Dict[line_id, float] - MW losses per line
                - transformer_losses: Dict[xfmr_id, float] - MW losses per transformer
                
        Returns:
            PowerBalanceResult with validation details
        """
        # Extract data
        generation = network_state.get("generation", {})
        loads = network_state.get("loads", {})
        line_losses = network_state.get("line_losses", {})
        transformer_losses = network_state.get("transformer_losses", {})
        
        # Calculate totals
        total_gen = sum(generation.values())
        total_load = sum(loads.values())
        total_line_losses = sum(line_losses.values())
        total_xfmr_losses = sum(transformer_losses.values())
        total_losses = total_line_losses + total_xfmr_losses
        
        # Calculate imbalance
        imbalance = total_gen - (total_load + total_losses)
        
        # Calculate percentage (avoid division by zero)
        if total_gen > 0:
            imbalance_percent = abs(imbalance) / total_gen
        else:
            imbalance_percent = float('inf') if imbalance != 0 else 0
        
        # Check if valid
        is_valid = imbalance_percent <= self.tolerance
        
        # Identify violations
        violations = []
        if not is_valid:
            violations.append({
                "type": "power_balance",
                "severity": "high" if imbalance_percent > 0.05 else "medium",
                "value": imbalance,
                "percent": imbalance_percent * 100,
                "message": f"Power imbalance of {imbalance:.3f} MW ({imbalance_percent*100:.2f}%)"
            })
        
        # Check for high losses (typical for V < 0.95 pu)
        if total_gen > 0:
            loss_percent = total_losses / total_gen
            if loss_percent > 0.05:  # >5% losses
                violations.append({
                    "type": "high_losses",
                    "severity": "warning",
                    "value": total_losses,
                    "percent": loss_percent * 100,
                    "message": f"High losses: {total_losses:.3f} MW ({loss_percent*100:.2f}%)"
                })
        
        # Build detailed results
        details = {
            "generation_by_node": generation,
            "load_by_node": loads,
            "losses_by_line": line_losses,
            "losses_by_transformer": transformer_losses,
            "loss_breakdown": {
                "line_losses": total_line_losses,
                "transformer_losses": total_xfmr_losses,
                "total_losses": total_losses
            }
        }
        
        result = PowerBalanceResult(
            is_valid=is_valid,
            total_generation=total_gen,
            total_load=total_load,
            total_losses=total_losses,
            imbalance=imbalance,
            imbalance_percent=imbalance_percent,
            details=details,
            violations=violations
        )
        
        # Log results
        if is_valid:
            logger.debug(f"Power balance OK: Gen={total_gen:.2f} MW, "
                        f"Load={total_load:.2f} MW, Losses={total_losses:.2f} MW")
        else:
            logger.warning(f"Power balance VIOLATION: Imbalance={imbalance:.3f} MW "
                          f"({imbalance_percent*100:.2f}%)")
        
        return result
    
    def validate_with_gd(self, network_state: Dict[str, Any], 
                        gd_output: float = 0.0) -> PowerBalanceResult:
        """
        Validate power balance including distributed generation.
        
        Args:
            network_state: Network state dictionary
            gd_output: GD output in MW (typically 1.8 MW for Los Menucos)
            
        Returns:
            PowerBalanceResult with GD accounted
        """
        # Add GD to generation
        generation = network_state.get("generation", {}).copy()
        generation["gd_los_menucos"] = gd_output
        
        # Update network state
        updated_state = network_state.copy()
        updated_state["generation"] = generation
        
        # Validate with GD included
        result = self.validate(updated_state)
        
        # Add GD info to details
        result.details["gd_contribution"] = gd_output
        
        return result
    
    def analyze_imbalance_sources(self, network_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze potential sources of power imbalance.
        
        Useful for debugging when validation fails.
        """
        result = self.validate(network_state)
        
        analysis = {
            "imbalance_mw": result.imbalance,
            "imbalance_percent": result.imbalance_percent * 100,
            "potential_causes": []
        }
        
        # Check for missing generation
        if result.imbalance < 0:
            analysis["potential_causes"].append({
                "cause": "missing_generation",
                "description": "Generation might be underreported or missing",
                "suggestion": "Check if all generators are accounted for"
            })
        
        # Check for missing loads
        if result.imbalance > 0:
            analysis["potential_causes"].append({
                "cause": "missing_loads", 
                "description": "Some loads might not be included",
                "suggestion": "Verify all load points are captured"
            })
        
        # Check for loss calculation issues
        if result.total_losses < result.total_load * 0.01:  # Less than 1%
            analysis["potential_causes"].append({
                "cause": "low_losses",
                "description": "Losses seem unusually low for V < 0.95 pu network",
                "suggestion": "Verify loss calculations, especially with low voltage"
            })
        
        # Check for measurement synchronization
        analysis["potential_causes"].append({
            "cause": "measurement_sync",
            "description": "Generation and load measurements might not be synchronized",
            "suggestion": "Ensure all measurements are from the same timestamp"
        })
        
        return analysis


def validate_typical_day(day_data: Dict[str, Any]) -> List[PowerBalanceResult]:
    """
    Validate power balance for a typical day (24 hours).
    
    Args:
        day_data: Dictionary with hourly network states
        
    Returns:
        List of PowerBalanceResult for each hour
    """
    validator = PowerBalanceValidator()
    results = []
    
    for hour in range(24):
        hour_state = day_data.get(f"hour_{hour}", {})
        if hour_state:
            result = validator.validate(hour_state)
            results.append(result)
            
            if not result.is_valid:
                logger.warning(f"Hour {hour}: Power balance violation - "
                              f"{result.imbalance:.3f} MW imbalance")
    
    return results