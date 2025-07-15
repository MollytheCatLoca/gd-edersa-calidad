# BESSModel V2 – Documentation and Usage Guide

This document is a reference for developers and data‑science workflows that integrate the `BESSModel` class (file: `bess_model.py`).  It is meant to be consumed by humans **and** by code‑assist AIs (e.g. Vibe Coding), so key signatures and semantics are spelled out explicitly.

---

## 1  Quick description

`BESSModel` emulates the power‑energy dynamics of a Battery Energy Storage System (BESS) coupled to a PV plant or a generic grid node.

* **Technologies**: standard lead‑acid / early Li‑ion, modern LFP, premium LTO/advanced Li‑ion.
* **Topologies**: parallel AC (retro‑fit), series DC (bus‑DC/hybrid), hybrid (mix AC/DC).
* **Core features**
  – Time‑step simulation (`step`)
  – Strategy runner (`simulate_strategy`)
  – Vectorised, stateless transition (`next_state`) for RL or batched Monte‑Carlo
  – Built‑in cycle counting, energy/loss tracking, curtailment calc.
  – Validation hook (`BESSValidator`).

---

## 2  Public constructor

```python
BESSModel(
    power_mw: float,           # Rated PCS power (per direction)
    duration_hours: float,     # Storage hours at rated power (=> energy in MWh)
    technology: str = "modern_lfp",  # 'standard' | 'modern_lfp' | 'premium'
    topology: str   = "parallel_ac", # 'parallel_ac' | 'series_dc' | 'hybrid'
    track_history: bool = True,        # Store per‑timestep log (can be heavy)
    verbose: bool = True              # Info logging (set False for ML)
)
```

Throws `ValueError` if `power_mw<=0` or `duration_hours<=0`.

### Penalty handling

* `series_dc` adds **2 %** conversion loss and derates `power_mw` by the same 2 %.
* `hybrid` adds **1 %**.

---

## 3  Key attributes (post‑init)

| Attribute             | Type                 | Meaning                                    |
| --------------------- | -------------------- | ------------------------------------------ |
| `capacity_mwh`        | `float`              | Nominal energy (`power_mw*duration_hours`) |
| `power_mw_eff`        | `float`              | Rated power after topology derating        |
| `soc`                 | `float`              | State of charge (0–1)                      |
| `energy_stored`       | `float`              | Actual stored energy \[MWh]                |
| `cycles`              | `float`              | Cumulative cycles (Full‑Equivalent)        |
| `total_energy_losses` |  `float`             | MWh lost to efficiency so far              |
| `operation_history`   | `list[dict] \| None` | Per‑step log if `track_history`            |

---

## 4  Low‑level timestep API

### `step(power_request: float, dt=1.0) -> dict`

Performs one physical step (mutable).

* `power_request` < 0 → **charge**; > 0 → **discharge** (MW)
* Saturates to SOC, C‑rate, `power_mw_eff`.
* Returns keys: `actual_power`, `energy_loss`, `soc`, `limited_by`.

### `next_state(soc, p_req, dt=0.25, dtype=np.float64) -> (soc_new, p_act, loss)`

Pure, **stateless** and vectorisable. Shapes preserved (scalar‑in → scalar‑out, array‑in → array‑out). Use in RL or JIT'd loops.

---

## 5  High‑level runner

### `simulate_strategy(solar_profile, strategy, **kwargs)`

Runs one of the strategies implemented in `bess_strategies.py` (V1: gentle) or `bess_strategies_v2.py` (V2: aggressive demos).

* `solar_profile`: `np.ndarray` or `pd.Series` (MW) – **resolution must match** the internal `dt` expected by the strategy.
* `strategy`: name string. Unknown names fallback to "no‑BESS pass‑through".
* Returns a dict with arrays `grid_power`, `battery_power`, `soc`, etc. plus `validation` dict.

> **Note** V2 strategies are intended to stress the BESS (cycling, smoothing) for tutorial/demo purposes.

---

## 6  Typical usage patterns

```python
from bess_model import BESSModel
import numpy as np

dt = 0.25  # 15‑min steps
pv_curve = np.load("tmy_1mw.npy")      # shape (96,)

bess = BESSModel(power_mw=0.5, duration_hours=2,
                 technology="modern_lfp", topology="parallel_ac")
results = bess.simulate_strategy(pv_curve, "cap_shaving", cap=0.6)
print(results["validation"])
```

**Batch RL:**

```python
soc = np.zeros((batch,)) + 0.5
p_req = agent_policy(obs)
new_soc, p_act, loss = bess.next_state(soc, p_req, dt=0.25, dtype=np.float32)
```

---

## 7  Extending / plugging new strategies

1. Create your function in `bess_strategies_v2.py`:

   ```python
   def apply_my_strategy(model, pv, grid, batt, soc, curtail, losses, *, paramX=…):
       # loop over timesteps, call model.step(...)
   ```
2. Add an `elif strategy == 'my_strategy':` block in `simulate_strategy`.

---

## 8  Validator contract

`BESSValidator.validate_strategy_result(pv, result, name, meta)` must return a dict like:

```json
{"valid": true, "reason": "", "energy_balance_error": 0.004}
```

The caller **raises** if `valid==False`.

---

## 9  Assumptions & limits

* Single contiguous battery bank (no per‑rack balancing).
* No calendar degradation; cycles are counted but do not affect capacity.
* Thermal / HVAC consumption not modelled (can be added as fixed parasitic loss).
* Time‑step (`dt`) uniform inside each run; changing `dt` mid‑simulation is unsupported.

---

## 10  Changelog

| Version | Date (yy‑mm) | Highlights                                                                                                                                                                                          |
| ------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **2.2** | 25‑07        | *Added* topology‑based power derating (`power_mw_eff`).<br>*Added* strategy set **V2** (smoothing, aggressive cycling, freq‑reg, arbitrage\_demo).<br>*Documentation* converted to canmore textdoc. |
| **2.1** | 25‑05        | Loss formula for discharge fixed (`P·dt·(1/η−1)`).<br>Cycle counting now uses *usable* capacity.<br>`next_state` gained `dtype` param and array‑preserving semantics.                               |
| **2.0** | 25‑03        | Vectorised stateless API, logger control, tech/topology tables externalised.                                                                                                                        |
| **1.x** | 24‑10        | First public release; basic cap‑shave / flat‑day strategies.                                                                                                                                        |

---

## 11  Licensing

`BESSModel` is released under the **MIT License**.  Feel free to fork, modify, and redistribute, provided you keep attribution and license notice.

---

## 12  Road‑map / TODO

* **Calendar degradation** model (capacity fade vs cycles + C‑rate).
* Parameter‑isable **auxiliary HVAC** losses.
* Add **multi‑cluster** dispatch (N inverters sharing one central battery).
* Seamless export to **ONNX** for deployment inside power‑flow engines.

---

## 13  References & further reading

1. NREL, *Battery Storage for Grid Services* (2024).
2. IEEE Std 2030.2‑2022, *Guide for Interoperation of Energy Storage Systems*.
3. Chen et al., *Battery Dispatch Optimisation for Solar Smoothing*, IEEE TSG (2023).
4. Sandia, *PV + Storage Modelling Best Practices* (2025).