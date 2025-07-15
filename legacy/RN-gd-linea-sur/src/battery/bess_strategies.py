"""
bess_strategies.py
------------------
BESS Strategies – versión optimizada y *dt-safe*.

• Potencias en MW, energías en MWh.
• `dt` (h) se propaga a los límites y a `BESSModel.step`.
"""

from __future__ import annotations
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BESSStrategies:
    """
    Estrategias para operar un `BESSModel`.

    Cada método modifica *in-place* los arrays:
        grid, battery, soc, curtailed, losses
    """

    # ───── 1. Cap Shaving ────────────────────────────────────────────────────
    @staticmethod
    def apply_cap_shaving(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        cap_mw: Optional[float] = None,
        soft_discharge: bool = True,
        dt: float = 1.0,
        **_,
    ) -> None:
        cap_mw = cap_mw or float(np.nanmax(solar) * 0.7)
        thr_rel = 0.02  # 2 % de tolerancia

        for i, p_solar in enumerate(solar):
            soc[i] = bess_model.soc
            curtailed[i] = 0.0  # init

            if p_solar > cap_mw:                       # exceso
                excess = p_solar - cap_mw
                res = bess_model.step(-excess, dt=dt)
                battery[i] = res["actual_power"]
                losses[i] = res["energy_loss"]

                grid[i] = p_solar + battery[i]         # batería negativa
                if grid[i] > cap_mw * (1 + thr_rel):
                    curtailed[i] = grid[i] - cap_mw
                    grid[i] = cap_mw

            elif (
                soft_discharge
                and p_solar < cap_mw * 0.5
                and bess_model.soc > 0.30
                and bess_model.get_discharge_limit(dt) > 0
            ):
                deficit = cap_mw * 0.5 - p_solar
                discharge = min(deficit, bess_model.get_discharge_limit(dt) * 0.3)
                res = bess_model.step(discharge, dt=dt)
                battery[i] = res["actual_power"]
                losses[i] = res["energy_loss"]
                grid[i] = p_solar + battery[i]
            else:
                grid[i] = p_solar
                battery[i] = losses[i] = 0.0

    # ───── 1b. Cap Shaving Balanced ──────────────────────────────────────────
    @staticmethod
    def apply_cap_shaving_balanced(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        cap_mw: Optional[float] = None,
        use_percentile: bool = True,
        percentile: float = 70.0,
        discharge_start_hour: int = 16,
        dt: float = 1.0,
        **_,
    ) -> None:
        """
        Cap Shaving con balance diario garantizado.
        
        Args:
            cap_mw: Límite de potencia en MW. Si None, se calcula automáticamente.
            use_percentile: Si True, usa percentil de generación real. Si False, usa cap_mw directo.
            percentile: Percentil a usar si use_percentile=True (default: 70).
            discharge_start_hour: Hora para comenzar descarga forzada (default: 16).
            dt: Intervalo de tiempo en horas.
        """
        # Calcular cap basado en percentil o valor fijo
        if cap_mw is None:
            if use_percentile:
                # Usar percentil de la generación real del día (excluyendo ceros)
                solar_positive = solar[solar > 0.001]
                if len(solar_positive) > 0:
                    cap_mw = float(np.percentile(solar_positive, percentile))
                else:
                    cap_mw = float(np.nanmax(solar) * 0.7)
            else:
                cap_mw = float(np.nanmax(solar) * 0.7)
        
        thr_rel = 0.02  # 2% de tolerancia
        hours_in_day = int(24 / dt)
        
        for i, p_solar in enumerate(solar):
            soc[i] = bess_model.soc
            curtailed[i] = 0.0  # init
            hour = i % hours_in_day
            
            # Fase 1: Carga cuando solar > cap
            if p_solar > cap_mw:
                excess = p_solar - cap_mw
                res = bess_model.step(-excess, dt=dt)
                battery[i] = res["actual_power"]
                losses[i] = res["energy_loss"]
                
                grid[i] = p_solar + battery[i]  # batería negativa
                if grid[i] > cap_mw * (1 + thr_rel):
                    curtailed[i] = grid[i] - cap_mw
                    grid[i] = cap_mw
            
            # Fase 2: Descarga balanceada
            elif hour >= discharge_start_hour and bess_model.soc > bess_model.tech_params['soc_min']:
                # Calcular energía restante que necesitamos descargar
                energy_remaining = (bess_model.soc - bess_model.tech_params['soc_min']) * bess_model.capacity_mwh
                hours_remaining = max(1, hours_in_day - hour)
                
                # Tasa de descarga necesaria para llegar a SOC mínimo al final del día
                required_discharge_rate = energy_remaining / (hours_remaining * dt)
                
                # Limitar por capacidad del BESS
                discharge_power = min(required_discharge_rate, bess_model.get_discharge_limit(dt))
                
                if discharge_power > 0.001:
                    res = bess_model.step(discharge_power, dt=dt)
                    battery[i] = res["actual_power"]
                    losses[i] = res["energy_loss"]
                    grid[i] = p_solar + battery[i]
                else:
                    grid[i] = p_solar
                    battery[i] = losses[i] = 0.0
            else:
                grid[i] = p_solar
                battery[i] = losses[i] = 0.0

    # ───── 2. Flat Day ───────────────────────────────────────────────────────
    @staticmethod
    def apply_flat_day(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        flat_mw: Optional[float] = None,
        start_hour: int = 8,
        end_hour: int = 18,
        dt: float = 1.0,
        **_,
    ) -> None:
        hours_per_day = int(round(24 / dt))
        day_count = int(np.ceil(len(solar) / hours_per_day))
        window_mask = np.zeros(hours_per_day, dtype=bool)
        window_mask[int(start_hour / dt) : int(end_hour / dt)] = True

        for day in range(day_count):
            sl = slice(day * hours_per_day, (day + 1) * hours_per_day)
            s_day = solar[sl]
            if s_day.size == 0:
                continue

            w_day = window_mask[: s_day.size]
            solar_in = np.sum(s_day[w_day]) * dt

            if flat_mw is None:
                flat_mw_day = 0.95 * np.sum(s_day) * dt / w_day.sum()
            else:
                flat_mw_day = flat_mw

            need = flat_mw_day * w_day.sum()
            deficit = max(0.0, need - solar_in)

            for k, p_solar in enumerate(s_day, start=sl.start):
                soc[k] = bess_model.soc
                curtailed[k] = 0.0
                in_window = window_mask[k - sl.start]

                if in_window:
                    target = flat_mw_day
                    if p_solar >= target:                 # sobra
                        excess = p_solar - target
                        charge = min(excess, bess_model.get_charge_limit(dt))
                        res = bess_model.step(-charge, dt=dt) if charge > 0 else None
                        battery[k] = res["actual_power"] if res else 0
                        losses[k] = res["energy_loss"] if res else 0
                        grid[k] = target
                        curtailed[k] = max(0.0, excess - charge)
                    else:                                  # falta
                        deficit_p = target - p_solar
                        discharge = min(deficit_p, bess_model.get_discharge_limit(dt))
                        res = bess_model.step(discharge, dt=dt) if discharge > 0 else None
                        battery[k] = res["actual_power"] if res else 0
                        losses[k] = res["energy_loss"] if res else 0
                        grid[k] = p_solar + battery[k]
                else:                                      # fuera ventana
                    if (
                        deficit > 0.0
                        and p_solar > 0.0
                        and bess_model.soc < 0.8
                    ):
                        charge = min(
                            p_solar,
                            bess_model.get_charge_limit(dt),
                            deficit / dt,
                        )
                        res = bess_model.step(-charge, dt=dt) if charge > 0 else None
                        battery[k] = res["actual_power"] if res else 0
                        losses[k] = res["energy_loss"] if res else 0
                        grid[k] = p_solar + battery[k]
                        deficit -= -battery[k] * dt
                    else:
                        grid[k] = p_solar
                        battery[k] = losses[k] = 0.0

    # ───── 3. Night Shift ────────────────────────────────────────────────────
    @staticmethod
    def apply_night_shift(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        charge_hours: Optional[list[int]] = None,
        discharge_hours: Optional[list[int]] = None,
        dt: float = 1.0,
        **_,
    ) -> None:
        charge_hours = charge_hours or list(range(10, 15))
        discharge_hours = discharge_hours or list(range(19, 22))

        max_night_e = min(
            bess_model.power_mw * len(discharge_hours) * dt,
            bess_model.capacity_mwh * 0.85,
        )
        charged = 0.0

        for i, p_solar in enumerate(solar):
            hour = (i * dt) % 24
            soc[i] = bess_model.soc
            curtailed[i] = 0.0  # nunca hay curtailment en esta estrategia

            if hour in charge_hours and p_solar > 0.5:
                if charged < max_night_e and bess_model.soc < 0.9:
                    need = max_night_e - charged
                    charge = min(p_solar * 0.8, bess_model.get_charge_limit(dt), need / dt)
                    res = bess_model.step(-charge, dt=dt) if charge > 0 else None
                    battery[i] = res["actual_power"] if res else 0
                    losses[i] = res["energy_loss"] if res else 0
                    grid[i] = p_solar + battery[i]
                    charged += -battery[i] * dt
                else:
                    grid[i] = p_solar
                    battery[i] = losses[i] = 0.0

            elif hour in discharge_hours:
                discharge = min(bess_model.power_mw * 0.6, bess_model.get_discharge_limit(dt))
                res = bess_model.step(discharge, dt=dt) if discharge > 0 else None
                battery[i] = res["actual_power"] if res else 0
                losses[i] = res["energy_loss"] if res else 0
                grid[i] = p_solar + battery[i]
            else:
                grid[i] = p_solar
                battery[i] = losses[i] = 0.0

    # ───── 4. Ramp Limit ─────────────────────────────────────────────────────
    @staticmethod
    def apply_ramp_limit(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        ramp_limit_mw_per_hour: Optional[float] = None,
        dt: float = 1.0,
        **_,
    ) -> None:
        if ramp_limit_mw_per_hour is None:
            ramp_limit_mw_per_hour = np.nanmax(solar) * 0.15

        ramp_step = ramp_limit_mw_per_hour * dt
        prev_grid = solar[0]
        grid[0] = prev_grid
        soc[0] = bess_model.soc
        curtailed[0] = battery[0] = losses[0] = 0.0

        for i in range(1, len(solar)):
            p_solar = solar[i]
            soc[i] = bess_model.soc
            curtailed[i] = 0.0

            ramp = p_solar - prev_grid
            if abs(ramp) <= ramp_step:
                grid[i] = p_solar
                battery[i] = losses[i] = 0.0
            else:
                if ramp > 0:                               # subida
                    target = prev_grid + ramp_step
                    excess = p_solar - target
                    charge = min(excess, bess_model.get_charge_limit(dt))
                    if charge > 0:
                        res = bess_model.step(-charge, dt=dt)
                        battery[i] = res["actual_power"]
                        losses[i] = res["energy_loss"]
                        grid[i] = p_solar + battery[i]
                    else:
                        curtailed[i] = excess
                        grid[i] = target
                        battery[i] = losses[i] = 0.0
                else:                                      # bajada
                    target = prev_grid - ramp_step
                    deficit = target - p_solar
                    discharge = min(deficit, bess_model.get_discharge_limit(dt))
                    if discharge > 0:
                        res = bess_model.step(discharge, dt=dt)
                        battery[i] = res["actual_power"]
                        losses[i] = res["energy_loss"]
                        grid[i] = p_solar + battery[i]
                    else:
                        grid[i] = p_solar
                        battery[i] = losses[i] = 0.0

            prev_grid = grid[i]

    # ───── 5. Peak Shaving ───────────────────────────────────────────────────
    @staticmethod
    def apply_peak_shaving(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        peak_threshold: Optional[float] = None,
        dt: float = 1.0,
        **_,
    ) -> None:
        positive = solar[solar > 0]
        peak_threshold = (
            peak_threshold
            if peak_threshold is not None
            else (np.percentile(positive, 80) if positive.size else 0.0)
        )

        for i, p_solar in enumerate(solar):
            soc[i] = bess_model.soc
            curtailed[i] = 0.0

            if p_solar > peak_threshold:                  # pico
                excess = p_solar - peak_threshold
                charge = min(excess, bess_model.get_charge_limit(dt))
                res = bess_model.step(-charge, dt=dt) if charge > 0 else None
                battery[i] = res["actual_power"] if res else 0.0
                losses[i] = res["energy_loss"] if res else 0.0
                grid[i] = p_solar + battery[i]
                curtailed[i] = max(0.0, excess - charge)

            elif (
                p_solar < peak_threshold * 0.3
                and bess_model.soc > 0.20
                and bess_model.get_discharge_limit(dt) > 0
            ):
                discharge = min(
                    peak_threshold * 0.3 - p_solar,
                    bess_model.get_discharge_limit(dt) * 0.5,
                )
                res = bess_model.step(discharge, dt=dt)
                battery[i] = res["actual_power"]
                losses[i] = res["energy_loss"]
                grid[i] = p_solar + battery[i]
            else:
                grid[i] = p_solar
                battery[i] = losses[i] = 0.0

    # ───── 5. Soft Cap Shaving (sin curtailment real) ───────────────────────
    @staticmethod
    def apply_soft_cap_shaving(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        cap_mw: Optional[float] = None,
        soft_discharge: bool = True,
        dt: float = 1.0,
        **_,
    ) -> None:
        """
        Como cap_shaving pero SIN curtailment real.
        Registra lo que SERÍA curtailed pero lo entrega a la red.
        Útil cuando la red puede manejar picos temporales.
        """
        cap_mw = cap_mw or float(np.nanmax(solar) * 0.7)
        thr_rel = 0.02  # 2% tolerancia
        
        for i, p_solar in enumerate(solar):
            soc[i] = bess_model.soc
            curtailed[i] = 0.0  # init
            
            if p_solar > cap_mw:  # exceso
                excess = p_solar - cap_mw
                res = bess_model.step(-excess, dt=dt)
                battery[i] = res["actual_power"]
                losses[i] = res["energy_loss"]
                
                grid[i] = p_solar + battery[i]  # batería negativa
                
                # DIFERENCIA CLAVE: Registrar pero NO aplicar curtailment
                if grid[i] > cap_mw * (1 + thr_rel):
                    # Registrar lo que SERÍA curtailed (para análisis/métricas)
                    potential_curtailment = grid[i] - cap_mw
                    curtailed[i] = potential_curtailment
                    
                    # PERO NO limitamos grid - dejamos pasar todo
                    # grid[i] = cap_mw  # <-- NO HACER ESTO
                    
                    # Log para tracking
                    logger.debug(
                        f"Hour {i}: Would curtail {potential_curtailment:.3f} MW "
                        f"but allowing full export of {grid[i]:.3f} MW"
                    )
            
            elif (
                soft_discharge
                and p_solar < cap_mw * 0.5
                and bess_model.soc > 0.30
                and bess_model.get_discharge_limit(dt) > 0
            ):
                # Descarga suave - igual que cap_shaving
                deficit = cap_mw * 0.5 - p_solar
                discharge = min(deficit, bess_model.get_discharge_limit(dt) * 0.3)
                res = bess_model.step(discharge, dt=dt)
                battery[i] = res["actual_power"]
                losses[i] = res["energy_loss"]
                grid[i] = p_solar + battery[i]
            else:
                grid[i] = p_solar
                battery[i] = losses[i] = 0.0
            
            # VALIDACIÓN DE BALANCE en cada timestep
            # Para soft_cap_shaving el curtailment registrado NO se resta
            charge_to_bess = -battery[i] if battery[i] < 0 else 0
            discharge_from_bess = battery[i] if battery[i] > 0 else 0
            
            # Balance: Solar = Grid + Carga_BESS - Descarga_BESS
            balance = grid[i] + charge_to_bess - discharge_from_bess
            error = abs(p_solar - balance)
            
            if error > 1e-6:
                logger.warning(
                    f"Balance error at hour {i}: Solar={p_solar:.3f}, "
                    f"Grid={grid[i]:.3f}, BESS_flow={battery[i]:.3f}, "
                    f"Error={error:.6f} MW"
                )


__all__ = ["BESSStrategies"]
