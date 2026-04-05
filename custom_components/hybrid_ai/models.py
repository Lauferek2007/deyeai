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
class PriceBundle:
    import_prices: list[float] = field(default_factory=list)
    export_prices: list[float] = field(default_factory=list)
    avg_import_price: float = 0.0
    avg_export_price: float = 0.0
    cheapest_import_price: float = 0.0
    highest_export_price: float = 0.0
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


@dataclass(slots=True)
class DiscoveryResult:
    adapter: str
    confidence: float
    matched_by: str
    battery_soc_entity: str | None = None
    load_power_entity: str | None = None
    pv_power_entity: str | None = None
    grid_power_entity: str | None = None
    solar_forecast_entity: str | None = None
    price_import_entity: str | None = None
    price_export_entity: str | None = None
    deye_load_limit_entity: str | None = None
    deye_battery_max_charge_current_entity: str | None = None
    deye_program_1_mode_entity: str | None = None
    notes: list[str] = field(default_factory=list)
