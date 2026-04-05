from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EnergySnapshot:
    battery_soc: float
    battery_capacity_kwh: float
    load_power_w: float
    pv_power_w: float
    grid_power_w: float


@dataclass(slots=True)
class ForecastBundle:
    solar_kwh_next_24h: float
    load_kwh_next_24h: float
    load_kwh_overnight: float
    confidence: float
    source_details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ControlAction:
    action: str
    value: Any
    reason: str


@dataclass(slots=True)
class OptimizationResult:
    target_morning_soc: float
    expected_surplus_kwh: float
    should_discharge_overnight: bool
    should_export_overnight: bool
    summary: str
    actions: list[ControlAction] = field(default_factory=list)
