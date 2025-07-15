"""
BESS Strategies V2 – Estrategias “agresivas”
Forzamos el uso real de la batería para evidenciar pérdidas (≈5-7 %)
y ciclado; todas las potencias en MW, energías en MWh.
"""

from __future__ import annotations

import numpy as np
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class BESSStrategiesV2:
    """
    Estrategias que fuerzan el uso de la batería.
    Patrón común:

        for t in range(len(solar)):
            soc[t] = bess_model.soc               # 1) registrar SOC
            …  decidir acción …
            grid[t]      = solar[t] + battery[t]  # 2) siempre balancear
            losses[t]    = result['energy_loss']  #    (o 0)
            curtailed[t] = …                      #    si aplica
    """

    # ------------------------------------------------------------------
    # 1. Solar smoothing
    # ------------------------------------------------------------------
    @staticmethod
    def apply_solar_smoothing(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        smoothing_factor: float = 0.8,
        force_cycles: bool = True,
        **_: Any,
    ) -> None:
        """
        Suaviza la curva: un porcentaje de la generación diurna
        pasa obligatoriamente por la batería.

        Args:
            smoothing_factor : fracción de la energía solar que
                               se encola en el BESS (0–1).
            force_cycles     : si True, provoca ciclos completos
                               alternando carga/descarga.
        """
        bess_model.reset()

        sunny_hours = {h for h in range(24) if 6 <= h <= 17}

        for i, p_solar in enumerate(solar):
            soc[i] = bess_model.soc
            hour   = i % 24

            if p_solar > 0.01 and (force_cycles or hour in sunny_hours):
                p_to_bess   = p_solar * smoothing_factor
                p_direct    = p_solar - p_to_bess

                # Prioridad: carga; si SOC alto, simultanear descarga
                if bess_model.soc < 0.8:
                    res = bess_model.step(-min(p_to_bess, bess_model.get_charge_limit()))
                else:  # Cycling
                    res = bess_model.step(
                        min(p_to_bess * 0.7, bess_model.get_discharge_limit())
                    )

                battery[i]  = res["actual_power"]
                losses[i]   = res["energy_loss"]
                grid[i]     = p_direct + p_solar + battery[i] - p_solar  # balance
                curtailed[i] = 0.0  # No curtailment in solar smoothing strategy
            else:
                # Horas sin sol o sin forzado → posible descarga nocturna
                if hour in (19, 20, 21) and bess_model.soc > 0.2:
                    p_dch = min(bess_model.power_mw * 0.5, bess_model.get_discharge_limit())
                    res   = bess_model.step(p_dch) if p_dch > 0.01 else {"actual_power": 0, "energy_loss": 0}
                    battery[i] = res["actual_power"]
                    losses[i]  = res["energy_loss"]
                    grid[i]    = p_solar + battery[i]
                    curtailed[i] = 0.0  # No curtailment in solar smoothing strategy
                else:
                    grid[i] = p_solar
                    battery[i] = losses[i] = curtailed[i] = 0.0

    # ------------------------------------------------------------------
    # 2. Time-shift agresivo
    # ------------------------------------------------------------------
    @staticmethod
    def apply_time_shift_aggressive(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        charge_hours: Optional[List[int]] = None,
        discharge_hours: Optional[List[int]] = None,
        **_: Any,
    ) -> None:
        """Trasvasa toda la producción del mediodía al pico nocturno."""
        charge_hours    = charge_hours or list(range(10, 15))   # 10-14 h
        discharge_hours = discharge_hours or list(range(18, 22))  # 18-21 h
        bess_model.reset()

        for i, p_solar in enumerate(solar):
            soc[i] = bess_model.soc
            hour   = i % 24

            if hour in charge_hours and p_solar > 0.01:
                res = bess_model.step(-min(p_solar, bess_model.get_charge_limit()))
                battery[i] = res["actual_power"]
                losses[i]  = res["energy_loss"]
                grid[i]    = max(0.0, p_solar + battery[i])  # excedente
                curtailed[i] = 0.0  # No curtailment in time shift strategy
            elif hour in discharge_hours:
                p_dch = bess_model.get_discharge_limit()
                res   = bess_model.step(p_dch) if p_dch > 0.01 else {"actual_power": 0, "energy_loss": 0}
                battery[i] = res["actual_power"]
                losses[i]  = res["energy_loss"]
                grid[i]    = p_solar + battery[i]
                curtailed[i] = 0.0  # No curtailment in time shift strategy
            else:
                grid[i] = p_solar
                battery[i] = losses[i] = curtailed[i] = 0.0

    # ------------------------------------------------------------------
    # 3. Cycling demo
    # ------------------------------------------------------------------
    @staticmethod
    def apply_cycling_demo(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        cycle_depth: float = 0.8,
        min_cycles_per_day: int = 2,
        **_: Any,
    ) -> None:
        """Fuerza ≥ `min_cycles_per_day` ciclos completos por día."""
        bess_model.reset(initial_soc=0.5)
        state = "charging"

        for i, p_solar in enumerate(solar):
            soc[i] = bess_model.soc
            hour   = i % 24

            # Toggle estado
            if state == "charging" and bess_model.soc >= cycle_depth:
                state = "discharging"
            elif state == "discharging" and bess_model.soc <= 0.2:
                state = "charging"

            if state == "charging" and p_solar > 0.01:
                p_chg   = min(p_solar, bess_model.get_charge_limit())
                res     = bess_model.step(-p_chg)
            elif state == "discharging":
                p_dch   = min(bess_model.power_mw * 0.6, bess_model.get_discharge_limit())
                res     = bess_model.step(p_dch) if p_dch > 0.01 else {"actual_power": 0, "energy_loss": 0}
            else:
                res = {"actual_power": 0, "energy_loss": 0}

            battery[i] = res["actual_power"]
            losses[i]  = res["energy_loss"]
            grid[i]    = p_solar + battery[i]
            curtailed[i] = 0.0  # No curtailment in cycling demo strategy

            # Fin de día → asegurarse de completar ciclos mínimos
            if hour == 23 and bess_model.cycles < min_cycles_per_day:
                state = "discharging" if bess_model.soc > 0.5 else "charging"

    # ------------------------------------------------------------------
    # 4. Frequency regulation
    # ------------------------------------------------------------------
    @staticmethod
    def apply_frequency_regulation(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        regulation_band: float = 0.1,
        response_speed: float = 0.8,
        **_: Any,
    ) -> None:
        """Micro-ciclos continuos simulando un servicio de regulación."""
        bess_model.reset(initial_soc=0.5)
        rng = np.random.default_rng(42)
        reg_signal = rng.normal(0, regulation_band, len(solar))

        for i, p_solar in enumerate(solar):
            soc[i] = bess_model.soc
            reg_p  = reg_signal[i] * bess_model.power_mw * response_speed

            if reg_p < 0:   # absorción
                p_chg = min(-reg_p, bess_model.get_charge_limit())
                res   = bess_model.step(-p_chg) if p_chg > 0.01 else {"actual_power": 0, "energy_loss": 0}
            else:           # inyección
                p_dch = min(reg_p, bess_model.get_discharge_limit())
                res   = bess_model.step(p_dch) if p_dch > 0.01 else {"actual_power": 0, "energy_loss": 0}

            battery[i] = res["actual_power"]
            losses[i]  = res["energy_loss"]
            grid[i]    = p_solar + battery[i]
            curtailed[i] = 0.0  # No curtailment in frequency regulation strategy

            # Re-centrar SOC si se aleja demasiado del 50 %
            if bess_model.soc < 0.3 and p_solar > 0.1:
                p_extra = min(p_solar * 0.3, bess_model.get_charge_limit())
                res2    = bess_model.step(-p_extra) if p_extra > 0.01 else {"actual_power": 0, "energy_loss": 0}
                battery[i] += res2["actual_power"]
                losses[i]  += res2["energy_loss"]
                grid[i]     = p_solar + battery[i]
            elif bess_model.soc > 0.7 and p_solar < 0.5:
                p_extra = min(bess_model.power_mw * 0.3, bess_model.get_discharge_limit())
                res2    = bess_model.step(p_extra) if p_extra > 0.01 else {"actual_power": 0, "energy_loss": 0}
                battery[i] += res2["actual_power"]
                losses[i]  += res2["energy_loss"]
                grid[i]     = p_solar + battery[i]

    # ------------------------------------------------------------------
    # 5. Arbitrage agresivo
    # ------------------------------------------------------------------
    @staticmethod
    def apply_arbitrage_aggressive(
        bess_model,
        solar: np.ndarray,
        grid: np.ndarray,
        battery: np.ndarray,
        soc: np.ndarray,
        curtailed: np.ndarray,
        losses: np.ndarray,
        *,
        price_threshold: float = 1.5,
        **_: Any,
    ) -> None:
        """Compra barato (carga) y vende caro (descarga); fuerza múltiples ciclos."""
        bess_model.reset()
        hourly_prices = np.array(
            [0.5, 0.5, 0.5, 0.5, 0.6, 0.8,  # 0-5
             1.0, 1.2, 1.3, 1.2, 1.0, 0.9,  # 6-11
             0.8, 0.7, 0.8, 0.9, 1.1, 1.3,  # 12-17
             1.5, 1.8, 2.0, 1.8, 1.5, 1.2]  # 18-23
        )

        for i, p_solar in enumerate(solar):
            soc[i]       = bess_model.soc
            hour         = i % 24
            price        = hourly_prices[hour]
            battery[i]   = losses[i] = 0.0  # reset por defecto
            action_power = 0.0

            if price < 0.8:  # cargar
                p_chg = p_solar if p_solar > 0.01 else bess_model.power_mw * 0.7
                action_power = min(p_chg, bess_model.get_charge_limit())
                if action_power > 0.01:
                    res = bess_model.step(-action_power)
                    battery[i] = res["actual_power"]
                    losses[i]  = res["energy_loss"]

            elif price > price_threshold:  # descargar
                action_power = bess_model.get_discharge_limit()
                if action_power > 0.01:
                    res = bess_model.step(action_power)
                    battery[i] = res["actual_power"]
                    losses[i]  = res["energy_loss"]

            else:  # precio medio
                if p_solar > 1.0 and bess_model.soc < 0.7:
                    action_power = min(p_solar - 1.0, bess_model.get_charge_limit())
                    if action_power > 0.01:
                        res = bess_model.step(-action_power)
                        battery[i] = res["actual_power"]
                        losses[i]  = res["energy_loss"]

            grid[i] = p_solar + battery[i]  # puede ser <0 si se “compra” red
            curtailed[i] = 0.0  # No curtailment in arbitrage strategy
