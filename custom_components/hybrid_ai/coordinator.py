from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .adapters.registry import ADAPTERS
from .const import (
    ATTR_ADAPTER_ACTIONS,
    ATTR_DISCOVERY,
    ATTR_EXPECTED_SURPLUS_KWH,
    ATTR_FORECAST_LOAD_KWH,
    ATTR_FORECAST_SOLAR_KWH,
    ATTR_HOURLY_SCHEDULE,
    ATTR_LOAD_PROFILE,
    ATTR_PLAN_SUMMARY,
    ATTR_PRICE_CONTEXT,
    ATTR_TOU_PLAN,
    ATTR_TARGET_MORNING_SOC,
    CONF_ADAPTER,
    CONF_AUTO_DISCOVERY,
    CONF_BATTERY_CAPACITY_KWH,
    CONF_BATTERY_CYCLE_COST,
    CONF_BATTERY_SOC_ENTITY,
    CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY,
    CONF_DEYE_BATTERY_GRID_CHARGING_ENTITY,
    CONF_DEYE_EXPORT_SURPLUS_ENTITY,
    CONF_DEYE_GRID_CHARGE_ENABLED_ENTITY,
    CONF_DEYE_LOAD_LIMIT_ENTITY,
    CONF_DEYE_PROGRAM_1_CHARGE_ENTITY,
    CONF_DEYE_PROGRAM_1_MODE_ENTITY,
    CONF_DEYE_PROGRAM_1_POWER_ENTITY,
    CONF_DEYE_PROGRAM_1_SOC_ENTITY,
    CONF_DEYE_PROGRAM_1_TIME_ENTITY,
    CONF_DEYE_PROGRAM_2_CHARGE_ENTITY,
    CONF_DEYE_PROGRAM_2_MODE_ENTITY,
    CONF_DEYE_PROGRAM_2_POWER_ENTITY,
    CONF_DEYE_PROGRAM_2_SOC_ENTITY,
    CONF_DEYE_PROGRAM_2_TIME_ENTITY,
    CONF_DEYE_PROGRAM_3_CHARGE_ENTITY,
    CONF_DEYE_PROGRAM_3_MODE_ENTITY,
    CONF_DEYE_PROGRAM_3_POWER_ENTITY,
    CONF_DEYE_PROGRAM_3_SOC_ENTITY,
    CONF_DEYE_PROGRAM_3_TIME_ENTITY,
    CONF_DEYE_PROGRAM_4_CHARGE_ENTITY,
    CONF_DEYE_PROGRAM_4_POWER_ENTITY,
    CONF_DEYE_PROGRAM_4_SOC_ENTITY,
    CONF_DEYE_PROGRAM_4_TIME_ENTITY,
    CONF_DEYE_PROGRAM_5_CHARGE_ENTITY,
    CONF_DEYE_PROGRAM_5_POWER_ENTITY,
    CONF_DEYE_PROGRAM_5_SOC_ENTITY,
    CONF_DEYE_PROGRAM_5_TIME_ENTITY,
    CONF_DEYE_PROGRAM_6_CHARGE_ENTITY,
    CONF_DEYE_PROGRAM_6_POWER_ENTITY,
    CONF_DEYE_PROGRAM_6_SOC_ENTITY,
    CONF_DEYE_PROGRAM_6_TIME_ENTITY,
    CONF_DEYE_SOLAR_EXPORT_ENTITY,
    CONF_DEYE_USE_TIMER_ENTITY,
    CONF_DEYE_WORK_MODE_ENTITY,
    CONF_DEYE_TIME_OF_USE_ENTITY,
    CONF_ENABLE_WRITE_MODE,
    CONF_EXPORT_ALLOWED,
    CONF_GRID_CHARGE_ALLOWED,
    CONF_GRID_POWER_ENTITY,
    CONF_LOAD_POWER_ENTITY,
    CONF_MAX_SOC,
    CONF_MIN_SOC,
    CONF_PV_POWER_ENTITY,
    CONF_PRICE_EXPORT_ENTITY,
    CONF_PRICE_IMPORT_ENTITY,
    CONF_SOLAR_FORECAST_ENTITY,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_WEEKLY_LOAD_OFFSETS,
)
from .deye_strategy import DeyeStrategyPlanner
from .discovery import discover_inverter_entities, discovery_as_dict
from .forecast import SolarForecastProvider
from .load_forecast import LoadForecaster
from .models import EnergySnapshot, ForecastBundle, WeeklyLoadOffset
from .optimizer import BatteryOptimizer
from .price_forecast import PriceForecastProvider

_LOGGER = logging.getLogger(__name__)


class HybridAiCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.optimizer = BatteryOptimizer()
        self.deye_strategy = DeyeStrategyPlanner()
        self.discovery = self._resolve_discovery()
        self.load_forecaster = LoadForecaster(
            hass,
            self._resolved_value(CONF_LOAD_POWER_ENTITY),
            entry.entry_id,
            [WeeklyLoadOffset(**item) for item in entry.data.get(CONF_WEEKLY_LOAD_OFFSETS, [])],
        )
        self.solar_forecaster = SolarForecastProvider(
            hass,
            self._resolved_value(CONF_SOLAR_FORECAST_ENTITY),
        )
        self.price_forecaster = PriceForecastProvider(
            hass,
            self._resolved_value(CONF_PRICE_IMPORT_ENTITY),
            self._resolved_value(CONF_PRICE_EXPORT_ENTITY),
        )

        adapter_cls = ADAPTERS.get(self._resolved_adapter(), ADAPTERS["generic"])
        self.adapter = adapter_cls(hass, entry.entry_id)

        super().__init__(
            hass,
            _LOGGER,
            name=f"Hybrid AI {entry.title}",
            update_interval=timedelta(
                minutes=entry.data.get(CONF_UPDATE_INTERVAL_MINUTES, 15)
            ),
        )

    async def _async_update_data(self) -> dict:
        snapshot = self._read_snapshot()
        current_load_w = self.load_forecaster.ingest_current_sample()
        await self.load_forecaster.async_persist()
        hourly_load = self.load_forecaster.forecast_hourly_load(current_load_w)
        solar_kwh, solar_meta = self.solar_forecaster.get_next_24h_kwh()
        load_kwh, overnight_kwh, forecast_confidence = self.load_forecaster.forecast_next_24h_kwh(
            current_load_w
        )

        forecast = ForecastBundle(
            solar_kwh_next_24h=solar_kwh,
            load_kwh_next_24h=load_kwh,
            load_kwh_overnight=overnight_kwh,
            confidence=forecast_confidence,
            source_details={"solar": solar_meta},
        )
        prices = self.price_forecaster.get_next_24h_prices()

        if self.adapter.name == "deye":
            result = self.deye_strategy.plan(
                snapshot,
                forecast,
                prices,
                hourly_load,
                min_soc=float(self.entry.data[CONF_MIN_SOC]),
                max_soc=float(self.entry.data[CONF_MAX_SOC]),
                export_allowed=bool(self.entry.data[CONF_EXPORT_ALLOWED]),
                grid_charge_allowed=bool(self.entry.data[CONF_GRID_CHARGE_ALLOWED]),
                battery_cycle_cost=float(self.entry.data[CONF_BATTERY_CYCLE_COST]),
            )
        else:
            result = self.optimizer.optimize(
                snapshot,
                forecast,
                min_soc=float(self.entry.data[CONF_MIN_SOC]),
                max_soc=float(self.entry.data[CONF_MAX_SOC]),
                export_allowed=bool(self.entry.data[CONF_EXPORT_ALLOWED]),
            )

        adapter_actions = await self.adapter.async_execute(
            result.actions,
            dry_run=not bool(self.entry.data[CONF_ENABLE_WRITE_MODE]),
        )

        return {
            ATTR_PLAN_SUMMARY: result.summary,
            ATTR_FORECAST_SOLAR_KWH: round(forecast.solar_kwh_next_24h, 2),
            ATTR_FORECAST_LOAD_KWH: round(forecast.load_kwh_next_24h, 2),
            ATTR_EXPECTED_SURPLUS_KWH: round(result.expected_surplus_kwh, 2),
            ATTR_TARGET_MORNING_SOC: round(result.target_morning_soc, 1),
            ATTR_ADAPTER_ACTIONS: adapter_actions,
            "adapter": self.adapter.name,
            "dry_run": not bool(self.entry.data[CONF_ENABLE_WRITE_MODE]),
            "forecast_confidence": round(forecast.confidence, 2),
            ATTR_PRICE_CONTEXT: {
                "avg_import_price": round(prices.avg_import_price, 4),
                "avg_export_price": round(prices.avg_export_price, 4),
                "cheapest_import_price": round(prices.cheapest_import_price, 4),
                "highest_export_price": round(prices.highest_export_price, 4),
                "sources": prices.source_details,
            },
            ATTR_LOAD_PROFILE: self.load_forecaster.get_profile_summary(),
            "hourly_load": [
                {
                    "start": slot["start"].isoformat(),
                    "load_w": round(slot["load_w"], 2),
                    "confidence": round(slot["confidence"], 3),
                }
                for slot in hourly_load
            ],
            ATTR_HOURLY_SCHEDULE: [
                {
                    "start": slot.start.isoformat(),
                    "mode": slot.mode,
                    "expected_load_kwh": slot.expected_load_kwh,
                    "expected_pv_kwh": slot.expected_pv_kwh,
                    "import_price": slot.import_price,
                    "export_price": slot.export_price,
                    "notes": slot.notes,
                }
                for slot in result.hourly_schedule
            ],
            ATTR_TOU_PLAN: [
                {
                    "program": slot.program,
                    "start_hour": slot.start_hour,
                    "end_hour": slot.end_hour,
                    "mode": slot.mode,
                    "label": slot.label,
                }
                for slot in result.tou_periods
            ],
            "snapshot": asdict(snapshot),
            ATTR_DISCOVERY: discovery_as_dict(self.discovery),
        }

    async def async_initialize(self) -> None:
        await self.load_forecaster.async_initialize()

    async def async_shutdown(self) -> None:
        await self.load_forecaster.async_persist(force=True)

    def _resolve_discovery(self):
        if not self.entry.data.get(CONF_AUTO_DISCOVERY, True):
            from .models import DiscoveryResult

            return DiscoveryResult(
                adapter=self.entry.data.get(CONF_ADAPTER, "generic"),
                confidence=1.0,
                matched_by="manual",
                battery_soc_entity=self.entry.data.get(CONF_BATTERY_SOC_ENTITY) or None,
                load_power_entity=self.entry.data.get(CONF_LOAD_POWER_ENTITY) or None,
                pv_power_entity=self.entry.data.get(CONF_PV_POWER_ENTITY) or None,
                grid_power_entity=self.entry.data.get(CONF_GRID_POWER_ENTITY) or None,
                solar_forecast_entity=self.entry.data.get(CONF_SOLAR_FORECAST_ENTITY) or None,
                price_import_entity=self.entry.data.get(CONF_PRICE_IMPORT_ENTITY) or None,
                price_export_entity=self.entry.data.get(CONF_PRICE_EXPORT_ENTITY) or None,
                deye_work_mode_entity=self.entry.data.get(CONF_DEYE_WORK_MODE_ENTITY) or None,
                deye_time_of_use_entity=self.entry.data.get(CONF_DEYE_TIME_OF_USE_ENTITY) or None,
                deye_export_surplus_entity=self.entry.data.get(CONF_DEYE_EXPORT_SURPLUS_ENTITY) or None,
                deye_battery_grid_charging_entity=self.entry.data.get(CONF_DEYE_BATTERY_GRID_CHARGING_ENTITY) or None,
                deye_grid_charge_enabled_entity=self.entry.data.get(CONF_DEYE_GRID_CHARGE_ENABLED_ENTITY) or None,
                deye_load_limit_entity=self.entry.data.get(CONF_DEYE_LOAD_LIMIT_ENTITY) or None,
                deye_solar_export_entity=self.entry.data.get(CONF_DEYE_SOLAR_EXPORT_ENTITY) or None,
                deye_use_timer_entity=self.entry.data.get(CONF_DEYE_USE_TIMER_ENTITY) or None,
                deye_battery_max_charge_current_entity=self.entry.data.get(CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY) or None,
                deye_program_1_mode_entity=self.entry.data.get(CONF_DEYE_PROGRAM_1_MODE_ENTITY) or None,
                deye_program_1_time_entity=self.entry.data.get(CONF_DEYE_PROGRAM_1_TIME_ENTITY) or None,
                deye_program_1_charge_entity=self.entry.data.get(CONF_DEYE_PROGRAM_1_CHARGE_ENTITY) or None,
                deye_program_1_power_entity=self.entry.data.get(CONF_DEYE_PROGRAM_1_POWER_ENTITY) or None,
                deye_program_1_soc_entity=self.entry.data.get(CONF_DEYE_PROGRAM_1_SOC_ENTITY) or None,
                deye_program_2_mode_entity=self.entry.data.get(CONF_DEYE_PROGRAM_2_MODE_ENTITY) or None,
                deye_program_2_time_entity=self.entry.data.get(CONF_DEYE_PROGRAM_2_TIME_ENTITY) or None,
                deye_program_2_charge_entity=self.entry.data.get(CONF_DEYE_PROGRAM_2_CHARGE_ENTITY) or None,
                deye_program_2_power_entity=self.entry.data.get(CONF_DEYE_PROGRAM_2_POWER_ENTITY) or None,
                deye_program_2_soc_entity=self.entry.data.get(CONF_DEYE_PROGRAM_2_SOC_ENTITY) or None,
                deye_program_3_mode_entity=self.entry.data.get(CONF_DEYE_PROGRAM_3_MODE_ENTITY) or None,
                deye_program_3_time_entity=self.entry.data.get(CONF_DEYE_PROGRAM_3_TIME_ENTITY) or None,
                deye_program_3_charge_entity=self.entry.data.get(CONF_DEYE_PROGRAM_3_CHARGE_ENTITY) or None,
                deye_program_3_power_entity=self.entry.data.get(CONF_DEYE_PROGRAM_3_POWER_ENTITY) or None,
                deye_program_3_soc_entity=self.entry.data.get(CONF_DEYE_PROGRAM_3_SOC_ENTITY) or None,
                deye_program_4_time_entity=self.entry.data.get(CONF_DEYE_PROGRAM_4_TIME_ENTITY) or None,
                deye_program_4_charge_entity=self.entry.data.get(CONF_DEYE_PROGRAM_4_CHARGE_ENTITY) or None,
                deye_program_4_power_entity=self.entry.data.get(CONF_DEYE_PROGRAM_4_POWER_ENTITY) or None,
                deye_program_4_soc_entity=self.entry.data.get(CONF_DEYE_PROGRAM_4_SOC_ENTITY) or None,
                deye_program_5_time_entity=self.entry.data.get(CONF_DEYE_PROGRAM_5_TIME_ENTITY) or None,
                deye_program_5_charge_entity=self.entry.data.get(CONF_DEYE_PROGRAM_5_CHARGE_ENTITY) or None,
                deye_program_5_power_entity=self.entry.data.get(CONF_DEYE_PROGRAM_5_POWER_ENTITY) or None,
                deye_program_5_soc_entity=self.entry.data.get(CONF_DEYE_PROGRAM_5_SOC_ENTITY) or None,
                deye_program_6_time_entity=self.entry.data.get(CONF_DEYE_PROGRAM_6_TIME_ENTITY) or None,
                deye_program_6_charge_entity=self.entry.data.get(CONF_DEYE_PROGRAM_6_CHARGE_ENTITY) or None,
                deye_program_6_power_entity=self.entry.data.get(CONF_DEYE_PROGRAM_6_POWER_ENTITY) or None,
                deye_program_6_soc_entity=self.entry.data.get(CONF_DEYE_PROGRAM_6_SOC_ENTITY) or None,
            )

        result = discover_inverter_entities(self.hass)
        return result

    def _resolved_adapter(self) -> str:
        configured = self.entry.data.get(CONF_ADAPTER, "auto")
        if configured == "auto" or not configured:
            return self.discovery.adapter
        return configured

    def _resolved_value(self, key: str) -> str | None:
        manual_value = self.entry.data.get(key)
        if manual_value:
            return manual_value
        return getattr(self.discovery, key, None)

    def _read_float_state(self, entity_id: str) -> float:
        state = self.hass.states.get(entity_id)
        if state is None:
            return 0.0
        try:
            return float(state.state)
        except ValueError:
            return 0.0

    def _read_snapshot(self) -> EnergySnapshot:
        return EnergySnapshot(
            battery_soc=self._read_float_state(self._resolved_value(CONF_BATTERY_SOC_ENTITY) or ""),
            battery_capacity_kwh=float(self.entry.data[CONF_BATTERY_CAPACITY_KWH]),
            load_power_w=self._read_float_state(self._resolved_value(CONF_LOAD_POWER_ENTITY) or ""),
            pv_power_w=self._read_float_state(self._resolved_value(CONF_PV_POWER_ENTITY) or ""),
            grid_power_w=self._read_float_state(self._resolved_value(CONF_GRID_POWER_ENTITY) or ""),
        )
