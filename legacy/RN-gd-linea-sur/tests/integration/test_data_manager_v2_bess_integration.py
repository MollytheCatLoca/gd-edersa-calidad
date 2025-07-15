"""
Comprehensive Integration Test Suite: DataManagerV2 ↔ BESSModel
=============================================================

Test suite completo para validar la integración entre DataManagerV2 y BESSModel.
Cubre todas las funcionalidades integradas de BESS en el sistema.

Autor: Claude AI Assistant  
Fecha: Julio 2025
Versión: 1.0
"""

import logging
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from typing import Dict, List, Any

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests

# Add project root to path for imports
import sys
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dashboard.pages.utils.data_manager_v2 import DataManagerV2, get_data_manager, reset_data_manager
from dashboard.pages.utils.models import DataResult, DataStatus
from dashboard.pages.utils.constants import BESS_TECHNOLOGIES, BESS_TOPOLOGIES, BESSStrategy


class TestDataManagerV2BESSIntegration:
    """Test suite principal para integración DataManagerV2 ↔ BESSModel"""
    
    def setup_method(self):
        """Setup antes de cada test"""
        reset_data_manager()
        self.dm = get_data_manager()
        
        # Solar profile típico para tests (24 horas, resolución horaria)
        self.test_solar_profile = np.concatenate([
            np.zeros(6),  # 00:00-05:00: Noche
            np.array([0.1, 0.3, 0.6, 0.8, 1.0, 1.2]),  # 06:00-11:00: Rampa matutina
            np.array([1.5, 1.8, 2.0, 1.8, 1.5, 1.2]),  # 12:00-17:00: Pico solar
            np.array([0.8, 0.4, 0.2, 0.0, 0.0, 0.0])   # 18:00-23:00: Rampa vespertina
        ])
        
        # Configuraciones BESS para tests
        self.bess_configs = [
            {"power_mw": 1.0, "duration_hours": 2.0, "technology": "standard"},
            {"power_mw": 2.0, "duration_hours": 4.0, "technology": "modern_lfp"},
            {"power_mw": 0.5, "duration_hours": 6.0, "technology": "premium"}
        ]
    
    def teardown_method(self):
        """Cleanup después de cada test"""
        reset_data_manager()

    # =====================================================================
    # 1. TESTS DE CONFIGURACIÓN Y ACCESO A CONSTANTES BESS
    # =====================================================================
    
    def test_get_bess_constants(self):
        """Test acceso a constantes BESS centralizadas"""
        result = self.dm.get_bess_constants()
        
        assert result.status == DataStatus.REAL
        assert isinstance(result.data, dict)
        assert "CYCLE_ENERGY_THRESHOLD_MWH" in result.data
        assert result.meta["source"] == "constants.py"
    
    def test_get_bess_technologies(self):
        """Test acceso a tecnologías BESS disponibles"""
        result = self.dm.get_bess_technologies()
        
        assert result.status == DataStatus.REAL
        assert isinstance(result.data, dict)
        
        # Verificar tecnologías esperadas
        expected_techs = ["standard", "modern_lfp", "premium"]
        for tech in expected_techs:
            assert tech in result.data
            assert "η_charge" in result.data[tech]
            assert "η_discharge" in result.data[tech]
            assert "η_roundtrip" in result.data[tech]
            assert "soc_min" in result.data[tech]
            assert "soc_max" in result.data[tech]
        
        assert "available_technologies" in result.meta
    
    def test_get_bess_topologies(self):
        """Test acceso a topologías BESS disponibles"""
        result = self.dm.get_bess_topologies()
        
        assert result.status == DataStatus.REAL
        assert isinstance(result.data, dict)
        
        # Verificar topologías esperadas  
        expected_topos = ["parallel_ac", "series_dc", "hybrid"]
        for topo in expected_topos:
            assert topo in result.data
            assert "efficiency_penalty" in result.data[topo]
            assert "flexibility" in result.data[topo]
            assert "description" in result.data[topo]
        
        assert "available_topologies" in result.meta
    
    def test_get_bess_technology_params_valid(self):
        """Test obtención de parámetros de tecnología válida"""
        result = self.dm.get_bess_technology_params("modern_lfp")
        
        assert result.status == DataStatus.REAL
        assert isinstance(result.data, dict)
        assert result.data["η_roundtrip"] == 0.93  # Eficiencia esperada para modern_lfp
        assert result.meta["technology"] == "modern_lfp"
    
    def test_get_bess_technology_params_invalid(self):
        """Test obtención de parámetros de tecnología inválida"""
        result = self.dm.get_bess_technology_params("invalid_tech")
        
        assert result.status == DataStatus.ERROR
        assert result.data is None
        assert "not found" in result.meta["error"]
        assert "available" in result.meta
    
    def test_get_bess_topology_params_valid(self):
        """Test obtención de parámetros de topología válida"""
        result = self.dm.get_bess_topology_params("series_dc")
        
        assert result.status == DataStatus.REAL
        assert isinstance(result.data, dict)
        assert result.data["efficiency_penalty"] == 0.02  # 2% penalty para series_dc
        assert result.meta["topology"] == "series_dc"
    
    def test_get_bess_topology_params_invalid(self):
        """Test obtención de parámetros de topología inválida"""
        result = self.dm.get_bess_topology_params("invalid_topology")
        
        assert result.status == DataStatus.ERROR
        assert result.data is None
        assert "not found" in result.meta["error"]

    # =====================================================================
    # 2. TESTS DE CREACIÓN DE BESSModel
    # =====================================================================
    
    def test_create_bess_model_default(self):
        """Test creación de BESSModel con parámetros default"""
        result = self.dm.create_bess_model(power_mw=2.0, duration_hours=4.0)
        
        assert result.status == DataStatus.REAL
        assert result.data is not None
        
        # Verificar configuración del modelo
        bess_model = result.data
        assert bess_model.power_mw == 2.0
        assert bess_model.duration_hours == 4.0
        assert bess_model.capacity_mwh == 8.0
        assert bess_model.technology == "modern_lfp"
        assert bess_model.topology == "parallel_ac"
        
        # Verificar metadata
        assert result.meta["power_mw"] == 2.0
        assert result.meta["duration_hours"] == 4.0
        assert result.meta["technology"] == "modern_lfp"
        assert result.meta["topology"] == "parallel_ac"
    
    def test_create_bess_model_custom_config(self):
        """Test creación de BESSModel con configuración custom"""
        result = self.dm.create_bess_model(
            power_mw=1.5,
            duration_hours=6.0,
            technology="premium",
            topology="series_dc",
            track_history=False,
            verbose=False
        )
        
        assert result.status == DataStatus.REAL
        bess_model = result.data
        
        assert bess_model.power_mw == 1.5
        assert bess_model.duration_hours == 6.0
        assert bess_model.technology == "premium"
        assert bess_model.topology == "series_dc"
        
        # Verificar que topología series_dc aplica penalty
        assert bess_model.power_mw_eff < bess_model.power_mw
    
    def test_create_bess_model_invalid_technology(self):
        """Test creación con tecnología inválida"""
        result = self.dm.create_bess_model(
            power_mw=2.0,
            duration_hours=4.0,
            technology="invalid_tech"
        )
        
        assert result.status == DataStatus.ERROR
        assert result.data is None
        assert "not found" in result.meta["error"]
    
    def test_create_bess_model_invalid_topology(self):
        """Test creación con topología inválida"""
        result = self.dm.create_bess_model(
            power_mw=2.0,
            duration_hours=4.0,
            topology="invalid_topology"
        )
        
        assert result.status == DataStatus.ERROR
        assert result.data is None
        assert "not found" in result.meta["error"]

    # =====================================================================
    # 3. TESTS DE SIMULACIÓN BESS CON ESTRATEGIAS
    # =====================================================================
    
    def test_simulate_bess_strategy_time_shift(self):
        """Test simulación BESS con estrategia time_shift_aggressive"""
        result = self.dm.simulate_bess_strategy(
            solar_profile=self.test_solar_profile,
            strategy="time_shift_aggressive",
            power_mw=2.0,
            duration_hours=4.0
        )
        
        assert result.status == DataStatus.REAL
        assert isinstance(result.data, dict)
        
        # Verificar estructura de resultados
        expected_keys = [
            'grid_power', 'battery_power', 'soc', 'solar_curtailed',
            'energy_losses', 'solar_delivered', 'total_cycles',
            'bess_config', 'metrics', 'validation'
        ]
        for key in expected_keys:
            assert key in result.data
        
        # Verificar arrays tienen el tamaño correcto
        assert len(result.data['grid_power']) == len(self.test_solar_profile)
        assert len(result.data['battery_power']) == len(self.test_solar_profile)
        assert len(result.data['soc']) == len(self.test_solar_profile)
        
        # Verificar métricas
        metrics = result.data['metrics']
        assert metrics['total_solar_mwh'] > 0
        assert metrics['energy_efficiency'] > 0
        assert metrics['strategy_used'] == "time_shift_aggressive"
    
    def test_simulate_bess_strategy_solar_smoothing(self):
        """Test simulación BESS con estrategia solar_smoothing"""
        result = self.dm.simulate_bess_strategy(
            solar_profile=self.test_solar_profile,
            strategy="solar_smoothing",
            power_mw=1.0,
            duration_hours=2.0,
            technology="modern_lfp"
        )
        
        assert result.status == DataStatus.REAL
        
        # Verificar que smoothing reduce variabilidad
        grid_power = result.data['grid_power']
        solar_power = self.test_solar_profile
        
        # Calcular variabilidad (desviación estándar)
        solar_std = np.std(solar_power)
        grid_std = np.std(grid_power)
        
        # El smoothing debería reducir la variabilidad
        assert grid_std <= solar_std * 1.1  # Permitir pequeño margen
    
    def test_simulate_bess_strategy_invalid_strategy(self):
        """Test simulación con estrategia inválida (debería hacer pass-through)"""
        result = self.dm.simulate_bess_strategy(
            solar_profile=self.test_solar_profile,
            strategy="invalid_strategy",
            power_mw=1.0,
            duration_hours=2.0
        )
        
        assert result.status == DataStatus.REAL
        
        # Debería hacer pass-through (grid_power = solar_profile)
        np.testing.assert_array_almost_equal(
            result.data['grid_power'], 
            self.test_solar_profile, 
            decimal=6
        )
        
        # No debería usar el BESS
        np.testing.assert_array_almost_equal(
            result.data['battery_power'], 
            np.zeros_like(self.test_solar_profile), 
            decimal=6
        )
    
    def test_simulate_bess_strategy_empty_solar_profile(self):
        """Test simulación con perfil solar vacío"""
        result = self.dm.simulate_bess_strategy(
            solar_profile=[],
            strategy="time_shift_aggressive",
            power_mw=1.0,
            duration_hours=2.0
        )
        
        assert result.status == DataStatus.ERROR
        assert "Empty solar profile" in result.meta["error"]
    
    def test_simulate_bess_strategy_negative_solar(self):
        """Test simulación con valores negativos en perfil solar"""
        bad_profile = self.test_solar_profile.copy()
        bad_profile[10] = -1.0  # Introducir valor negativo
        
        result = self.dm.simulate_bess_strategy(
            solar_profile=bad_profile,
            strategy="time_shift_aggressive",
            power_mw=1.0,
            duration_hours=2.0
        )
        
        assert result.status == DataStatus.ERROR
        assert "Negative values" in result.meta["error"]
    
    def test_simulate_bess_strategy_multiple_technologies(self):
        """Test simulación con diferentes tecnologías BESS"""
        technologies = ["standard", "modern_lfp", "premium"]
        results = {}
        
        for tech in technologies:
            result = self.dm.simulate_bess_strategy(
                solar_profile=self.test_solar_profile,
                strategy="time_shift_aggressive",
                power_mw=2.0,
                duration_hours=4.0,
                technology=tech
            )
            
            assert result.status == DataStatus.REAL
            results[tech] = result.data
        
        # Verificar que tecnologías premium tienen mayor eficiencia
        std_eff = results["standard"]["metrics"]["energy_efficiency"]
        lfp_eff = results["modern_lfp"]["metrics"]["energy_efficiency"]
        premium_eff = results["premium"]["metrics"]["energy_efficiency"]
        
        assert premium_eff >= lfp_eff >= std_eff

    # =====================================================================
    # 4. TESTS DE CONTROL DINÁMICO BESS
    # =====================================================================
    
    def test_simulate_bess_dynamic_control_basic(self):
        """Test control dinámico BESS básico"""
        # Perfil de potencia: cargar por 4 horas, luego descargar por 4 horas
        power_requests = np.concatenate([
            np.full(4, -1.0),  # Cargar a 1 MW por 4 horas
            np.full(4, 1.5)    # Descargar a 1.5 MW por 4 horas
        ])
        
        result = self.dm.simulate_bess_dynamic_control(
            initial_soc=0.2,
            power_requests=power_requests,
            power_mw=2.0,
            duration_hours=4.0,
            dt=1.0  # 1 hora por paso
        )
        
        assert result.status == DataStatus.REAL
        assert isinstance(result.data, dict)
        
        # Verificar estructura de resultados
        expected_keys = [
            'soc_trajectory', 'actual_power', 'requested_power',
            'losses', 'power_curtailment', 'bess_config', 'metrics'
        ]
        for key in expected_keys:
            assert key in result.data
        
        # Verificar trayectoria SOC
        soc_traj = result.data['soc_trajectory']
        assert len(soc_traj) == len(power_requests) + 1  # +1 para estado inicial
        assert soc_traj[0] == 0.2  # SOC inicial
        
        # SOC debería subir durante carga y bajar durante descarga
        assert soc_traj[4] > soc_traj[0]  # Después de cargar
        assert soc_traj[-1] < soc_traj[4]  # Después de descargar
        
        # Verificar métricas
        metrics = result.data['metrics']
        assert metrics['total_energy_in_mwh'] > 0
        assert metrics['total_energy_out_mwh'] > 0
        assert 0 < metrics['realized_roundtrip_efficiency'] < 1
    
    def test_simulate_bess_dynamic_control_power_limits(self):
        """Test control dinámico con límites de potencia"""
        # Solicitar más potencia de la que el BESS puede entregar
        excessive_power = np.array([5.0, -5.0, 3.0, -3.0])  # BESS solo tiene 2 MW
        
        result = self.dm.simulate_bess_dynamic_control(
            initial_soc=0.5,
            power_requests=excessive_power,
            power_mw=2.0,
            duration_hours=4.0
        )
        
        assert result.status == DataStatus.REAL
        
        actual_power = result.data['actual_power']
        curtailment = result.data['power_curtailment']
        
        # Verificar que la potencia actual está limitada
        assert np.all(np.abs(actual_power) <= 2.0)
        
        # Verificar que hay curtailment cuando se exceden los límites
        assert np.any(np.abs(curtailment) > 0)
    
    def test_simulate_bess_dynamic_control_soc_limits(self):
        """Test control dinámico con límites de SOC"""
        # Intentar descargar completamente desde SOC bajo
        discharge_requests = np.full(10, 2.0)  # Descargar a máxima potencia
        
        result = self.dm.simulate_bess_dynamic_control(
            initial_soc=0.15,  # Cerca del SOC mínimo
            power_requests=discharge_requests,
            power_mw=2.0,
            duration_hours=4.0,
            technology="modern_lfp"  # SOC mín = 0.10
        )
        
        assert result.status == DataStatus.REAL
        
        soc_traj = result.data['soc_trajectory']
        
        # SOC nunca debería ir por debajo del mínimo
        assert np.all(soc_traj >= 0.10 - 1e-6)  # Pequeña tolerancia numérica

    # =====================================================================
    # 5. TESTS DE OPTIMIZACIÓN BESS
    # =====================================================================
    
    def test_optimize_bess_for_solar_energy_efficiency(self):
        """Test optimización BESS para maximizar eficiencia energética"""
        result = self.dm.optimize_bess_for_solar(
            solar_profile=self.test_solar_profile,
            power_range=(0.5, 3.0),
            duration_range=(2.0, 6.0),
            strategy="time_shift_aggressive",
            optimization_metric="energy_efficiency"
        )
        
        assert result.status == DataStatus.REAL
        assert isinstance(result.data, dict)
        
        # Verificar estructura de resultados
        assert "best_configuration" in result.data
        assert "all_configurations" in result.data
        assert "optimization_settings" in result.data
        assert "summary" in result.data
        
        best_config = result.data["best_configuration"]
        assert best_config is not None
        assert "power_mw" in best_config
        assert "duration_hours" in best_config
        assert "metrics" in best_config
        
        # Verificar que se probaron múltiples configuraciones
        all_configs = result.data["all_configurations"]
        assert len(all_configs) > 1
        
        # Verificar rangos de búsqueda
        powers = [cfg["power_mw"] for cfg in all_configs]
        durations = [cfg["duration_hours"] for cfg in all_configs]
        assert min(powers) >= 0.5
        assert max(powers) <= 3.0
        assert min(durations) >= 2.0
        assert max(durations) <= 6.0
    
    def test_optimize_bess_for_solar_curtailment_ratio(self):
        """Test optimización BESS para minimizar curtailment"""
        result = self.dm.optimize_bess_for_solar(
            solar_profile=self.test_solar_profile,
            power_range=(1.0, 2.0),
            duration_range=(3.0, 5.0),
            strategy="solar_smoothing",
            optimization_metric="curtailment_ratio"
        )
        
        assert result.status == DataStatus.REAL
        
        settings = result.data["optimization_settings"]
        assert settings["metric"] == "curtailment_ratio"
        assert settings["strategy"] == "solar_smoothing"
        
        # Para minimizar curtailment, configuraciones más grandes deberían ser mejores
        best_config = result.data["best_configuration"]
        assert best_config["objective_value"] >= 0  # Curtailment ratio es no-negativo
    
    def test_optimize_bess_for_solar_no_valid_configs(self):
        """Test optimización cuando no hay configuraciones válidas"""
        # Usar perfil solar muy pequeño que no justifica BESS
        tiny_profile = np.full(24, 0.01)  # 0.01 MW constante
        
        result = self.dm.optimize_bess_for_solar(
            solar_profile=tiny_profile,
            power_range=(10.0, 20.0),  # BESS muy grande para perfil pequeño
            duration_range=(8.0, 12.0),
            optimization_metric="energy_efficiency"
        )
        
        # Debería encontrar configuraciones pero posiblemente con eficiencia baja
        assert result.status == DataStatus.REAL
        assert result.data["best_configuration"] is not None

    # =====================================================================
    # 6. TESTS DE VALIDACIÓN CONFIGURACIÓN BESS
    # =====================================================================
    
    def test_validate_bess_configuration_valid(self):
        """Test validación de configuración BESS válida"""
        result = self.dm.validate_bess_configuration(
            power_mw=2.0,
            duration_hours=4.0,
            technology="modern_lfp",
            topology="parallel_ac"
        )
        
        assert result.status == DataStatus.REAL
        assert isinstance(result.data, dict)
        
        validation = result.data
        assert validation["configuration_valid"] is True
        assert "warnings" in validation
        assert "recommendations" in validation
        assert "technical_parameters" in validation
        assert "performance_estimates" in validation
        
        # Verificar parámetros técnicos
        tech_params = validation["technical_parameters"]
        assert tech_params["power_mw"] == 2.0
        assert tech_params["duration_h"] == 4.0
        assert tech_params["capacity_mwh"] == 8.0
        assert tech_params["technology"] == "modern_lfp"
    
    def test_validate_bess_configuration_high_c_rate_warning(self):
        """Test validación con C-rate alto (debería generar warning)"""
        result = self.dm.validate_bess_configuration(
            power_mw=5.0,
            duration_hours=1.0,  # C-rate = 5.0 (muy alto)
            technology="standard"
        )
        
        assert result.status == DataStatus.REAL
        
        validation = result.data
        warnings = validation["warnings"]
        
        # Debería haber warning sobre C-rate alto
        c_rate_warning = any("High C-rate" in warning for warning in warnings)
        assert c_rate_warning
    
    def test_validate_bess_configuration_low_c_rate_warning(self):
        """Test validación con C-rate bajo (debería generar warning)"""
        result = self.dm.validate_bess_configuration(
            power_mw=0.5,
            duration_hours=10.0,  # C-rate = 0.05 (muy bajo)
            technology="premium"
        )
        
        assert result.status == DataStatus.REAL
        
        validation = result.data
        warnings = validation["warnings"]
        
        # Debería haber warning sobre C-rate bajo
        c_rate_warning = any("Low C-rate" in warning for warning in warnings)
        assert c_rate_warning
    
    def test_validate_bess_configuration_short_duration_warning(self):
        """Test validación con duración corta"""
        result = self.dm.validate_bess_configuration(
            power_mw=2.0,
            duration_hours=0.5,  # Muy corto
            technology="modern_lfp"
        )
        
        assert result.status == DataStatus.REAL
        
        validation = result.data
        warnings = validation["warnings"]
        
        # Debería haber warning sobre duración corta
        duration_warning = any("Short duration" in warning for warning in warnings)
        assert duration_warning
    
    def test_validate_bess_configuration_long_duration_warning(self):
        """Test validación con duración larga"""
        result = self.dm.validate_bess_configuration(
            power_mw=1.0,
            duration_hours=10.0,  # Muy largo
            technology="modern_lfp"
        )
        
        assert result.status == DataStatus.REAL
        
        validation = result.data
        warnings = validation["warnings"]
        
        # Debería haber warning sobre duración larga
        duration_warning = any("Long duration" in warning for warning in warnings)
        assert duration_warning

    # =====================================================================
    # 7. TESTS DE CONSERVACIÓN DE ENERGÍA Y FÍSICA
    # =====================================================================
    
    def test_energy_conservation_in_simulation(self):
        """Test conservación de energía en simulación BESS completa"""
        result = self.dm.simulate_bess_strategy(
            solar_profile=self.test_solar_profile,
            strategy="time_shift_aggressive",
            power_mw=2.0,
            duration_hours=4.0
        )
        
        assert result.status == DataStatus.REAL
        
        # Calcular balance de energía
        solar_energy = np.sum(self.test_solar_profile)
        grid_energy = np.sum(result.data['grid_power'])
        losses = np.sum(result.data['energy_losses'])
        curtailed = np.sum(result.data['solar_curtailed'])
        
        # Energía entregada + pérdidas + curtailment = energía solar
        total_accounted = grid_energy + losses + curtailed
        
        # Permitir pequeña tolerancia por precisión numérica
        energy_balance_error = abs(total_accounted - solar_energy) / solar_energy
        assert energy_balance_error < 0.01, f"Energy balance error: {energy_balance_error:.4f}"
    
    def test_soc_bounds_respected(self):
        """Test que los límites de SOC son respetados en simulación"""
        for config in self.bess_configs:
            result = self.dm.simulate_bess_strategy(
                solar_profile=self.test_solar_profile,
                strategy="cycling_demo",  # Estrategia que cicla agresivamente
                **config
            )
            
            assert result.status == DataStatus.REAL
            
            soc_profile = result.data['soc']
            
            # Obtener límites de SOC para la tecnología
            tech_result = self.dm.get_bess_technology_params(config["technology"])
            assert tech_result.status == DataStatus.REAL
            
            soc_min = tech_result.data["soc_min"]
            soc_max = tech_result.data["soc_max"]
            
            # Verificar que SOC se mantiene dentro de límites
            assert np.all(soc_profile >= soc_min - 1e-6), f"SOC below minimum for {config['technology']}"
            assert np.all(soc_profile <= soc_max + 1e-6), f"SOC above maximum for {config['technology']}"
    
    def test_roundtrip_efficiency_consistency(self):
        """Test consistencia de eficiencia round-trip"""
        for tech in ["standard", "modern_lfp", "premium"]:
            # Obtener eficiencia teórica
            tech_result = self.dm.get_bess_technology_params(tech)
            theoretical_efficiency = tech_result.data["η_roundtrip"]
            
            # Simular ciclo simple: cargar completamente, luego descargar
            simple_cycle_solar = np.concatenate([
                np.full(8, 2.0),   # Cargar por 8 horas
                np.zeros(16)       # Descargar automáticamente por estrategia
            ])
            
            result = self.dm.simulate_bess_strategy(
                solar_profile=simple_cycle_solar,
                strategy="time_shift_aggressive",
                power_mw=2.0,
                duration_hours=4.0,
                technology=tech
            )
            
            assert result.status == DataStatus.REAL
            
            # Calcular eficiencia realizada
            metrics = result.data['metrics']
            realized_efficiency = metrics['energy_efficiency']
            
            # La eficiencia realizada debería estar cerca de la teórica
            # (puede ser menor debido a operación parcial y otras pérdidas)
            assert realized_efficiency <= theoretical_efficiency + 0.05
            assert realized_efficiency >= theoretical_efficiency * 0.8

    # =====================================================================
    # 8. TESTS DE PERFORMANCE Y ROBUSTEZ
    # =====================================================================
    
    def test_performance_large_solar_profile(self):
        """Test performance con perfil solar grande (8760 horas)"""
        # Crear perfil anual sintético
        annual_profile = np.random.uniform(0, 3.0, 8760)  # Año completo
        
        import time
        start_time = time.time()
        
        result = self.dm.simulate_bess_strategy(
            solar_profile=annual_profile,
            strategy="time_shift_aggressive",
            power_mw=2.0,
            duration_hours=4.0,
            technology="modern_lfp"
        )
        
        execution_time = time.time() - start_time
        
        assert result.status == DataStatus.REAL
        assert execution_time < 10.0  # Debería completar en menos de 10 segundos
        
        # Verificar que los resultados son consistentes
        assert len(result.data['grid_power']) == 8760
        assert result.data['metrics']['simulation_hours'] == 8760
    
    def test_robustness_extreme_solar_values(self):
        """Test robustez con valores extremos en perfil solar"""
        # Perfil con picos muy altos y valores muy bajos
        extreme_profile = np.array([0.0, 0.001, 0.01, 0.1, 1.0, 10.0, 50.0, 100.0])
        
        result = self.dm.simulate_bess_strategy(
            solar_profile=extreme_profile,
            strategy="solar_smoothing",
            power_mw=5.0,
            duration_hours=2.0
        )
        
        assert result.status == DataStatus.REAL
        
        # Verificar que no hay valores NaN o infinitos
        for key in ['grid_power', 'battery_power', 'soc']:
            assert np.all(np.isfinite(result.data[key]))
    
    def test_robustness_zero_capacity_bess(self):
        """Test robustez con BESS de capacidad mínima"""
        result = self.dm.simulate_bess_strategy(
            solar_profile=self.test_solar_profile,
            strategy="time_shift_aggressive",
            power_mw=0.001,  # Capacidad mínima
            duration_hours=0.001
        )
        
        assert result.status == DataStatus.REAL
        
        # Con capacidad mínima, debería comportarse como pass-through
        np.testing.assert_array_almost_equal(
            result.data['grid_power'],
            self.test_solar_profile,
            decimal=3
        )

    # =====================================================================
    # 9. TESTS DE CASOS EDGE Y MANEJO DE ERRORES
    # =====================================================================
    
    def test_pandas_series_input(self):
        """Test que acepta pandas Series como input"""
        solar_series = pd.Series(self.test_solar_profile, 
                                index=pd.date_range('2024-01-01', periods=24, freq='H'))
        
        result = self.dm.simulate_bess_strategy(
            solar_profile=solar_series,
            strategy="time_shift_aggressive",
            power_mw=2.0,
            duration_hours=4.0
        )
        
        assert result.status == DataStatus.REAL
        assert len(result.data['grid_power']) == len(solar_series)
    
    def test_list_input(self):
        """Test que acepta lista Python como input"""
        solar_list = self.test_solar_profile.tolist()
        
        result = self.dm.simulate_bess_strategy(
            solar_profile=solar_list,
            strategy="time_shift_aggressive",
            power_mw=2.0,
            duration_hours=4.0
        )
        
        assert result.status == DataStatus.REAL
        assert len(result.data['grid_power']) == len(solar_list)
    
    def test_thread_safety(self):
        """Test thread safety del DataManagerV2 singleton"""
        import threading
        import concurrent.futures
        
        results = []
        
        def worker():
            dm = get_data_manager()
            result = dm.simulate_bess_strategy(
                solar_profile=self.test_solar_profile,
                strategy="time_shift_aggressive",
                power_mw=1.0,
                duration_hours=2.0
            )
            results.append(result.status == DataStatus.REAL)
        
        # Ejecutar múltiples workers en paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker) for _ in range(10)]
            concurrent.futures.wait(futures)
        
        # Todos los workers deberían haber tenido éxito
        assert all(results)
        assert len(results) == 10


# =====================================================================
# TESTS DE INTEGRACIÓN DE ALTO NIVEL
# =====================================================================

class TestFullPipelineIntegration:
    """Tests de integración completa del pipeline PSFV+BESS"""
    
    def setup_method(self):
        reset_data_manager()
        self.dm = get_data_manager()
    
    def teardown_method(self):
        reset_data_manager()
    
    def test_solar_to_bess_full_pipeline(self):
        """Test pipeline completo: Solar → BESS → Validación"""
        # Paso 1: Simular solar puro
        solar_result = self.dm.simulate_psfv_only(
            station="MAQUINCHAO",
            power_mw=3.0,
            month=6
        )
        
        if solar_result.status != DataStatus.REAL:
            pytest.skip("Solar simulation not available")
        
        solar_profile = solar_result.data.get('hourly_generation', np.random.uniform(0, 3, 24))
        
        # Paso 2: Optimizar BESS para este perfil solar
        optimization_result = self.dm.optimize_bess_for_solar(
            solar_profile=solar_profile,
            power_range=(1.0, 2.0),
            duration_range=(2.0, 4.0),
            optimization_metric="energy_efficiency"
        )
        
        assert optimization_result.status == DataStatus.REAL
        best_config = optimization_result.data["best_configuration"]
        
        # Paso 3: Simular con configuración óptima
        simulation_result = self.dm.simulate_bess_strategy(
            solar_profile=solar_profile,
            strategy="time_shift_aggressive",
            power_mw=best_config["power_mw"],
            duration_hours=best_config["duration_hours"]
        )
        
        assert simulation_result.status == DataStatus.REAL
        
        # Paso 4: Validar configuración
        validation_result = self.dm.validate_bess_configuration(
            power_mw=best_config["power_mw"],
            duration_hours=best_config["duration_hours"]
        )
        
        assert validation_result.status == DataStatus.REAL
        assert validation_result.data["configuration_valid"] is True
    
    def test_multiple_scenarios_comparison(self):
        """Test comparación de múltiples escenarios BESS"""
        # Perfil solar típico
        solar_profile = np.concatenate([
            np.zeros(6),
            np.linspace(0, 2, 6),
            np.full(6, 2.0),
            np.linspace(2, 0, 6)
        ])
        
        scenarios = [
            {"name": "No BESS", "strategy": "no_bess", "power": 0.1, "duration": 0.1},
            {"name": "Small BESS", "strategy": "time_shift_aggressive", "power": 1.0, "duration": 2.0},
            {"name": "Large BESS", "strategy": "time_shift_aggressive", "power": 2.0, "duration": 4.0},
        ]
        
        results = {}
        
        for scenario in scenarios:
            result = self.dm.simulate_bess_strategy(
                solar_profile=solar_profile,
                strategy=scenario["strategy"],
                power_mw=scenario["power"],
                duration_hours=scenario["duration"]
            )
            
            assert result.status == DataStatus.REAL
            results[scenario["name"]] = result.data["metrics"]
        
        # Verificar que BESS más grande tiene mejor eficiencia energética
        no_bess_eff = results["No BESS"]["energy_efficiency"]
        small_bess_eff = results["Small BESS"]["energy_efficiency"]
        large_bess_eff = results["Large BESS"]["energy_efficiency"]
        
        # Con BESS debería poder entregar más energía (efficiency ≥ 1.0 posible con time shift)
        assert small_bess_eff >= no_bess_eff * 0.95  # Al menos similar
        assert large_bess_eff >= small_bess_eff * 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])