"""
BESS Validation Module
======================

Validaciones energéticas automáticas para el Dashboard BESS Lab.
Implementa las validaciones críticas especificadas:

1. Balance energético: E_exportada = E_PSFV - E_pérdidas
2. Límite de pérdidas: ≤ 7% máximo
3. Conservación de energía en BESS
4. Validación de SOC dentro de límites técnicos
5. Verificación de estrategias BESS

Autor: Claude AI Assistant
Fecha: Julio 2025
Versión: 1.0
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationStatus(Enum):
    """Estados de validación"""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Resultado de una validación específica"""
    status: ValidationStatus
    message: str
    value: float
    threshold: float
    suggestion: Optional[str] = None
    

@dataclass
class EnergyBalanceValidation:
    """Resultado completo de validación de balance energético"""
    is_valid: bool
    overall_status: ValidationStatus
    validations: List[ValidationResult]
    energy_flows: Dict[str, float]
    performance_metrics: Dict[str, float]
    warnings: List[str]
    errors: List[str]
    

class BESSEnergyValidator:
    """
    Validador de balance energético para sistemas BESS.
    
    Implementa las validaciones críticas según especificación:
    - Balance energético fundamental
    - Límites de pérdidas
    - Conservación de energía
    - Validación de estrategias
    """
    
    def __init__(self):
        # Límites críticos según especificación
        self.MAX_LOSS_PERCENTAGE = 7.0  # 7% máximo
        self.MIN_EFFICIENCY = 85.0      # 85% mínimo
        self.MAX_BALANCE_ERROR = 0.001  # 1 Wh tolerancia
        self.SOC_MIN = 10.0            # 10% mínimo
        self.SOC_MAX = 95.0            # 95% máximo
        
    def validate_energy_balance(self, 
                               solar_profile: List[float],
                               bess_profile: List[float], 
                               losses: List[float],
                               dt: float = 1.0) -> EnergyBalanceValidation:
        """
        Validación completa del balance energético.
        
        Verifica la ecuación fundamental:
        E_exportada = E_PSFV - E_pérdidas
        
        Args:
            solar_profile: Generación solar por hora [MW]
            bess_profile: Potencia BESS por hora [MW] (neg=carga, pos=descarga)
            losses: Pérdidas por hora [MW] o [MWh]
            dt: Paso de tiempo en horas
            
        Returns:
            EnergyBalanceValidation con resultado completo
        """
        validations = []
        warnings = []
        errors = []
        
        # Calcular flujos energéticos
        solar_energy = sum(solar_profile) * dt
        bess_energy = sum(bess_profile) * dt
        
        # Pérdidas pueden ser array o escalar
        if isinstance(losses, list):
            total_losses = sum(losses) * dt
        else:
            total_losses = losses
        
        # Energía exportada = Solar + BESS neto
        exported_energy = solar_energy + bess_energy
        
        # Energía teórica = Solar - Pérdidas
        theoretical_energy = solar_energy - total_losses
        
        # 1. VALIDACIÓN FUNDAMENTAL: Balance energético
        balance_error = abs(exported_energy - theoretical_energy)
        balance_validation = ValidationResult(
            status=ValidationStatus.VALID if balance_error < self.MAX_BALANCE_ERROR else ValidationStatus.ERROR,
            message=f"Balance energético: error {balance_error:.6f} MWh",
            value=balance_error,
            threshold=self.MAX_BALANCE_ERROR,
            suggestion="Verificar cálculo de pérdidas y flujos BESS" if balance_error >= self.MAX_BALANCE_ERROR else None
        )
        validations.append(balance_validation)
        
        # 2. VALIDACIÓN DE PÉRDIDAS: ≤ 7% objetivo (pero no bloqueante para ML)
        loss_percentage = (total_losses / solar_energy * 100) if solar_energy > 0 else 0
        
        # Clasificación de pérdidas para ML learning
        if loss_percentage <= self.MAX_LOSS_PERCENTAGE:
            loss_status = ValidationStatus.VALID
            loss_message = f"Pérdidas: {loss_percentage:.1f}% ✅ (dentro del objetivo)"
            loss_suggestion = None
        elif loss_percentage <= self.MAX_LOSS_PERCENTAGE * 1.5:  # 10.5%
            loss_status = ValidationStatus.WARNING
            loss_message = f"Pérdidas: {loss_percentage:.1f}% ⚠️ (por encima del objetivo)"
            loss_suggestion = f"🔬 ML Learning: Analizar por qué supera {self.MAX_LOSS_PERCENTAGE}%"
        else:
            loss_status = ValidationStatus.ERROR
            loss_message = f"Pérdidas: {loss_percentage:.1f}% 🔴 (muy altas - datos para ML)"
            loss_suggestion = f"🔬 ML Learning: Caso extremo para análisis de estrategias ineficientes"
        
        loss_validation = ValidationResult(
            status=loss_status,
            message=loss_message,
            value=loss_percentage,
            threshold=self.MAX_LOSS_PERCENTAGE,
            suggestion=loss_suggestion
        )
        validations.append(loss_validation)
        
        # 3. VALIDACIÓN DE EFICIENCIA BESS
        bess_efficiency = self._calculate_bess_efficiency(bess_profile)
        efficiency_validation = ValidationResult(
            status=ValidationStatus.VALID if bess_efficiency >= self.MIN_EFFICIENCY else ValidationStatus.WARNING,
            message=f"Eficiencia BESS: {bess_efficiency:.1f}%",
            value=bess_efficiency,
            threshold=self.MIN_EFFICIENCY,
            suggestion=f"Mejorar eficiencia BESS a ≥{self.MIN_EFFICIENCY}%" if bess_efficiency < self.MIN_EFFICIENCY else None
        )
        validations.append(efficiency_validation)
        
        # 4. VALIDACIÓN DE CONSERVACIÓN DE ENERGÍA
        energy_conservation = self._validate_energy_conservation(solar_profile, bess_profile, losses)
        validations.append(energy_conservation)
        
        # Determinar estado general
        has_errors = any(v.status == ValidationStatus.ERROR for v in validations)
        has_warnings = any(v.status == ValidationStatus.WARNING for v in validations)
        
        if has_errors:
            overall_status = ValidationStatus.ERROR
        elif has_warnings:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.VALID
            
        # Preparar métricas de performance
        performance_metrics = {
            'energy_balance_error_mwh': balance_error,
            'loss_percentage': loss_percentage,
            'bess_efficiency': bess_efficiency,
            'solar_energy_mwh': solar_energy,
            'exported_energy_mwh': exported_energy,
            'total_losses_mwh': total_losses,
            'theoretical_energy_mwh': theoretical_energy,
        }
        
        # Flujos energéticos detallados
        energy_flows = {
            'solar_input': solar_energy,
            'bess_net': bess_energy,
            'losses_total': total_losses,
            'exported_output': exported_energy,
            'theoretical_output': theoretical_energy,
        }
        
        # Compilar warnings y errors
        for validation in validations:
            if validation.status == ValidationStatus.WARNING:
                warnings.append(validation.message)
            elif validation.status == ValidationStatus.ERROR:
                errors.append(validation.message)
        
        return EnergyBalanceValidation(
            is_valid=overall_status == ValidationStatus.VALID,
            overall_status=overall_status,
            validations=validations,
            energy_flows=energy_flows,
            performance_metrics=performance_metrics,
            warnings=warnings,
            errors=errors
        )
    
    def validate_soc_profile(self, soc_profile: List[float]) -> ValidationResult:
        """
        Valida que el SOC esté dentro de límites técnicos.
        
        Args:
            soc_profile: Estado de carga por hora [%]
            
        Returns:
            ValidationResult con resultado de validación SOC
        """
        min_soc = min(soc_profile)
        max_soc = max(soc_profile)
        
        violations = []
        if min_soc < self.SOC_MIN:
            violations.append(f"SOC mínimo {min_soc:.1f}% < {self.SOC_MIN}%")
        if max_soc > self.SOC_MAX:
            violations.append(f"SOC máximo {max_soc:.1f}% > {self.SOC_MAX}%")
        
        if violations:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"SOC fuera de límites: {', '.join(violations)}",
                value=min_soc if min_soc < self.SOC_MIN else max_soc,
                threshold=self.SOC_MIN if min_soc < self.SOC_MIN else self.SOC_MAX,
                suggestion=f"Mantener SOC entre {self.SOC_MIN}% y {self.SOC_MAX}%"
            )
        else:
            return ValidationResult(
                status=ValidationStatus.VALID,
                message=f"SOC dentro de límites: {min_soc:.1f}% - {max_soc:.1f}%",
                value=(min_soc + max_soc) / 2,
                threshold=50.0
            )
    
    def validate_strategy_performance(self, 
                                    strategy: str,
                                    solar_profile: List[float],
                                    bess_profile: List[float],
                                    target_metrics: Dict[str, float]) -> ValidationResult:
        """
        Valida el performance de una estrategia BESS específica.
        
        Args:
            strategy: Nombre de la estrategia
            solar_profile: Generación solar [MW]
            bess_profile: Potencia BESS [MW]
            target_metrics: Métricas objetivo para la estrategia
            
        Returns:
            ValidationResult con validación de estrategia
        """
        # Calcular métricas de la estrategia
        variability_reduction = self._calculate_variability_reduction(solar_profile, bess_profile)
        peak_shaving = self._calculate_peak_shaving(solar_profile, bess_profile)
        energy_shifted = self._calculate_energy_shifted(bess_profile)
        
        # Validar según tipo de estrategia
        if strategy in ['cap_shaving', 'peak_limit']:
            target_peak_reduction = target_metrics.get('peak_reduction', 20.0)
            if peak_shaving >= target_peak_reduction:
                return ValidationResult(
                    status=ValidationStatus.VALID,
                    message=f"Peak shaving: {peak_shaving:.1f}% (objetivo: {target_peak_reduction:.1f}%)",
                    value=peak_shaving,
                    threshold=target_peak_reduction
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.WARNING,
                    message=f"Peak shaving insuficiente: {peak_shaving:.1f}% < {target_peak_reduction:.1f}%",
                    value=peak_shaving,
                    threshold=target_peak_reduction,
                    suggestion="Aumentar potencia BESS o ajustar parámetros"
                )
        
        elif strategy in ['time_shift', 'night_shift']:
            target_energy_shift = target_metrics.get('energy_shift', 1.0)
            if energy_shifted >= target_energy_shift:
                return ValidationResult(
                    status=ValidationStatus.VALID,
                    message=f"Energy shifting: {energy_shifted:.2f} MWh (objetivo: {target_energy_shift:.2f} MWh)",
                    value=energy_shifted,
                    threshold=target_energy_shift
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.WARNING,
                    message=f"Energy shifting insuficiente: {energy_shifted:.2f} MWh < {target_energy_shift:.2f} MWh",
                    value=energy_shifted,
                    threshold=target_energy_shift,
                    suggestion="Aumentar duración BESS o ajustar ventanas temporales"
                )
        
        elif strategy in ['smoothing', 'flat_day']:
            target_variability = target_metrics.get('variability_reduction', 30.0)
            if variability_reduction >= target_variability:
                return ValidationResult(
                    status=ValidationStatus.VALID,
                    message=f"Variability reduction: {variability_reduction:.1f}% (objetivo: {target_variability:.1f}%)",
                    value=variability_reduction,
                    threshold=target_variability
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.WARNING,
                    message=f"Reducción de variabilidad insuficiente: {variability_reduction:.1f}% < {target_variability:.1f}%",
                    value=variability_reduction,
                    threshold=target_variability,
                    suggestion="Optimizar parámetros de smoothing"
                )
        
        else:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message=f"Estrategia '{strategy}' no reconocida para validación",
                value=0.0,
                threshold=0.0,
                suggestion="Verificar nombre de estrategia"
            )
    
    def generate_validation_report(self, validation: EnergyBalanceValidation) -> str:
        """
        Genera reporte textual de validación para console log.
        
        Args:
            validation: Resultado de validación
            
        Returns:
            String con reporte formateado
        """
        lines = []
        lines.append("=" * 50)
        lines.append("REPORTE DE VALIDACIÓN ENERGÉTICA")
        lines.append("=" * 50)
        
        # Estado general
        status_icon = "✅" if validation.is_valid else "❌"
        lines.append(f"Estado General: {status_icon} {validation.overall_status.value.upper()}")
        lines.append("")
        
        # Validaciones individuales
        lines.append("VALIDACIONES INDIVIDUALES:")
        for i, val in enumerate(validation.validations, 1):
            icon = "✅" if val.status == ValidationStatus.VALID else "⚠️" if val.status == ValidationStatus.WARNING else "❌"
            lines.append(f"{i}. {icon} {val.message}")
            if val.suggestion:
                lines.append(f"   → {val.suggestion}")
        lines.append("")
        
        # Métricas de performance
        lines.append("MÉTRICAS DE PERFORMANCE:")
        for key, value in validation.performance_metrics.items():
            lines.append(f"• {key}: {value:.4f}")
        lines.append("")
        
        # Flujos energéticos
        lines.append("FLUJOS ENERGÉTICOS:")
        for key, value in validation.energy_flows.items():
            lines.append(f"• {key}: {value:.4f} MWh")
        lines.append("")
        
        # Warnings y errors
        if validation.warnings:
            lines.append("WARNINGS:")
            for warning in validation.warnings:
                lines.append(f"⚠️ {warning}")
            lines.append("")
        
        if validation.errors:
            lines.append("ERRORS:")
            for error in validation.errors:
                lines.append(f"❌ {error}")
            lines.append("")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def _calculate_bess_efficiency(self, bess_profile: List[float]) -> float:
        """Calcula eficiencia BESS basada en flujos de energía."""
        charge_energy = sum(abs(p) for p in bess_profile if p < 0)
        discharge_energy = sum(p for p in bess_profile if p > 0)
        
        if charge_energy == 0:
            return 100.0  # No hay operación BESS
        
        return (discharge_energy / charge_energy) * 100
    
    def _validate_energy_conservation(self, 
                                    solar_profile: List[float],
                                    bess_profile: List[float],
                                    losses: List[float]) -> ValidationResult:
        """Valida conservación de energía en el sistema."""
        # Energía total input
        total_input = sum(solar_profile)
        
        # Energía total output + pérdidas
        net_output = sum(s + b for s, b in zip(solar_profile, bess_profile))
        total_losses = sum(losses) if isinstance(losses, list) else losses
        total_output_plus_losses = net_output + total_losses
        
        # Error de conservación
        conservation_error = abs(total_input - total_output_plus_losses)
        
        if conservation_error < self.MAX_BALANCE_ERROR:
            return ValidationResult(
                status=ValidationStatus.VALID,
                message=f"Conservación de energía: error {conservation_error:.6f} MWh",
                value=conservation_error,
                threshold=self.MAX_BALANCE_ERROR
            )
        else:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Violación de conservación: error {conservation_error:.6f} MWh",
                value=conservation_error,
                threshold=self.MAX_BALANCE_ERROR,
                suggestion="Verificar cálculo de pérdidas y balances energéticos"
            )
    
    def _calculate_variability_reduction(self, 
                                       solar_profile: List[float],
                                       bess_profile: List[float]) -> float:
        """Calcula reducción de variabilidad."""
        solar_std = np.std(solar_profile)
        net_profile = [s + b for s, b in zip(solar_profile, bess_profile)]
        net_std = np.std(net_profile)
        
        if solar_std == 0:
            return 0.0
        
        return ((solar_std - net_std) / solar_std) * 100
    
    def _calculate_peak_shaving(self, 
                               solar_profile: List[float],
                               bess_profile: List[float]) -> float:
        """Calcula reducción de pico."""
        solar_peak = max(solar_profile)
        net_profile = [s + b for s, b in zip(solar_profile, bess_profile)]
        net_peak = max(net_profile)
        
        if solar_peak == 0:
            return 0.0
        
        return ((solar_peak - net_peak) / solar_peak) * 100
    
    def _calculate_energy_shifted(self, bess_profile: List[float]) -> float:
        """Calcula energía desplazada por BESS."""
        return sum(abs(p) for p in bess_profile if p != 0) / 2  # Ciclo completo = carga + descarga


# Función de conveniencia para validación rápida
def validate_bess_energy_balance(solar_profile: List[float],
                               bess_profile: List[float],
                               losses: List[float],
                               strategy: str = "unknown",
                               target_metrics: Optional[Dict[str, float]] = None) -> EnergyBalanceValidation:
    """
    Validación rápida de balance energético BESS.
    
    Args:
        solar_profile: Generación solar [MW]
        bess_profile: Potencia BESS [MW]
        losses: Pérdidas [MW] o [MWh]
        strategy: Nombre de estrategia (opcional)
        target_metrics: Métricas objetivo (opcional)
        
    Returns:
        EnergyBalanceValidation con resultado completo
    """
    validator = BESSEnergyValidator()
    return validator.validate_energy_balance(solar_profile, bess_profile, losses)


# Configuración de exportación
__all__ = [
    'BESSEnergyValidator',
    'EnergyBalanceValidation',
    'ValidationResult',
    'ValidationStatus',
    'validate_bess_energy_balance'
]