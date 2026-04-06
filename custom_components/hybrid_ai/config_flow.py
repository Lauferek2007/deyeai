from __future__ import annotations

import json

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
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
    CONF_DEYE_TIME_OF_USE_ENTITY,
    CONF_DEYE_USE_TIMER_ENTITY,
    CONF_DEYE_WORK_MODE_ENTITY,
    CONF_ENABLE_WRITE_MODE,
    CONF_EXPORT_ALLOWED,
    CONF_GRID_CHARGE_ALLOWED,
    CONF_GRID_POWER_ENTITY,
    CONF_LOAD_POWER_ENTITY,
    CONF_MANUAL_MAX_DAILY_PV_KWH,
    CONF_MAX_SOC,
    CONF_MIN_SOC,
    CONF_PV_POWER_ENTITY,
    CONF_PRICE_EXPORT_ENTITY,
    CONF_PRICE_IMPORT_ENTITY,
    CONF_SOLAR_FORECAST_ENTITY,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_WEATHER_ENTITY,
    CONF_WEEKLY_LOAD_OFFSETS,
    DEFAULT_ADAPTER,
    DEFAULT_BATTERY_CYCLE_COST,
    DEFAULT_MANUAL_MAX_DAILY_PV_KWH,
    DEFAULT_MAX_SOC,
    DEFAULT_MIN_SOC,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DEFAULT_WEEKLY_LOAD_OFFSETS,
    DOMAIN,
)

ADAPTER_OPTIONS = ["auto", "deye", "generic", "solarman", "goodwe", "huawei"]


def _parse_weekly_offsets(value):
    if value in ("", None):
        return DEFAULT_WEEKLY_LOAD_OFFSETS
    if isinstance(value, list):
        items = value
    else:
        try:
            items = json.loads(value)
        except json.JSONDecodeError as exc:
            raise vol.Invalid("weekly_load_offsets must be a valid JSON array") from exc

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            raise vol.Invalid("Each weekly offset must be an object")
        try:
            day = int(item["day"])
            start_hour = int(item["start_hour"])
            duration_hours = int(item["duration_hours"])
            power_w = float(item["power_w"])
        except (KeyError, TypeError, ValueError) as exc:
            raise vol.Invalid(
                "Weekly offset requires day, start_hour, duration_hours and power_w"
            ) from exc
        if day < 0 or day > 6:
            raise vol.Invalid("day must be between 0 and 6")
        if start_hour < 0 or start_hour > 23:
            raise vol.Invalid("start_hour must be between 0 and 23")
        if duration_hours < 1 or duration_hours > 24:
            raise vol.Invalid("duration_hours must be between 1 and 24")
        if power_w < 0:
            raise vol.Invalid("power_w must be non-negative")
        normalized.append(
            {
                "day": day,
                "start_hour": start_hour,
                "duration_hours": duration_hours,
                "power_w": power_w,
                "label": str(item.get("label", "")),
            }
        )
    return normalized


def _serialize_weekly_offsets(value) -> str:
    if not value:
        return "[]"
    return json.dumps(value, ensure_ascii=False)


def _merged_entry_config(entry) -> dict:
    return {**entry.data, **entry.options}


def _normalize_user_input(user_input: dict) -> dict:
    normalized = dict(user_input)
    normalized[CONF_WEEKLY_LOAD_OFFSETS] = _parse_weekly_offsets(
        normalized.get(CONF_WEEKLY_LOAD_OFFSETS)
    )
    return normalized


def _build_schema(values: dict) -> vol.Schema:
    weekly_offsets = _serialize_weekly_offsets(
        values.get(CONF_WEEKLY_LOAD_OFFSETS, DEFAULT_WEEKLY_LOAD_OFFSETS)
    )
    return vol.Schema(
        {
            vol.Required(CONF_ADAPTER, default=values.get(CONF_ADAPTER, DEFAULT_ADAPTER)): vol.In(ADAPTER_OPTIONS),
            vol.Required(CONF_AUTO_DISCOVERY, default=values.get(CONF_AUTO_DISCOVERY, True)): bool,
            vol.Optional(CONF_BATTERY_SOC_ENTITY, default=values.get(CONF_BATTERY_SOC_ENTITY, "")): str,
            vol.Required(CONF_BATTERY_CAPACITY_KWH, default=values.get(CONF_BATTERY_CAPACITY_KWH, 10.0)): vol.Coerce(float),
            vol.Optional(CONF_LOAD_POWER_ENTITY, default=values.get(CONF_LOAD_POWER_ENTITY, "")): str,
            vol.Optional(CONF_PV_POWER_ENTITY, default=values.get(CONF_PV_POWER_ENTITY, "")): str,
            vol.Optional(CONF_GRID_POWER_ENTITY, default=values.get(CONF_GRID_POWER_ENTITY, "")): str,
            vol.Optional(CONF_SOLAR_FORECAST_ENTITY, default=values.get(CONF_SOLAR_FORECAST_ENTITY, "")): str,
            vol.Optional(CONF_WEATHER_ENTITY, default=values.get(CONF_WEATHER_ENTITY, "")): str,
            vol.Required(
                CONF_MANUAL_MAX_DAILY_PV_KWH,
                default=values.get(CONF_MANUAL_MAX_DAILY_PV_KWH, DEFAULT_MANUAL_MAX_DAILY_PV_KWH),
            ): vol.Coerce(float),
            vol.Optional(CONF_PRICE_IMPORT_ENTITY, default=values.get(CONF_PRICE_IMPORT_ENTITY, "")): str,
            vol.Optional(CONF_PRICE_EXPORT_ENTITY, default=values.get(CONF_PRICE_EXPORT_ENTITY, "")): str,
            vol.Optional(CONF_WEEKLY_LOAD_OFFSETS, default=weekly_offsets): str,
            vol.Optional(CONF_DEYE_WORK_MODE_ENTITY, default=values.get(CONF_DEYE_WORK_MODE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_TIME_OF_USE_ENTITY, default=values.get(CONF_DEYE_TIME_OF_USE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_EXPORT_SURPLUS_ENTITY, default=values.get(CONF_DEYE_EXPORT_SURPLUS_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_BATTERY_GRID_CHARGING_ENTITY, default=values.get(CONF_DEYE_BATTERY_GRID_CHARGING_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_GRID_CHARGE_ENABLED_ENTITY, default=values.get(CONF_DEYE_GRID_CHARGE_ENABLED_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_LOAD_LIMIT_ENTITY, default=values.get(CONF_DEYE_LOAD_LIMIT_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_SOLAR_EXPORT_ENTITY, default=values.get(CONF_DEYE_SOLAR_EXPORT_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_USE_TIMER_ENTITY, default=values.get(CONF_DEYE_USE_TIMER_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY, default=values.get(CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_1_MODE_ENTITY, default=values.get(CONF_DEYE_PROGRAM_1_MODE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_1_TIME_ENTITY, default=values.get(CONF_DEYE_PROGRAM_1_TIME_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_1_CHARGE_ENTITY, default=values.get(CONF_DEYE_PROGRAM_1_CHARGE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_1_POWER_ENTITY, default=values.get(CONF_DEYE_PROGRAM_1_POWER_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_1_SOC_ENTITY, default=values.get(CONF_DEYE_PROGRAM_1_SOC_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_2_MODE_ENTITY, default=values.get(CONF_DEYE_PROGRAM_2_MODE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_2_TIME_ENTITY, default=values.get(CONF_DEYE_PROGRAM_2_TIME_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_2_CHARGE_ENTITY, default=values.get(CONF_DEYE_PROGRAM_2_CHARGE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_2_POWER_ENTITY, default=values.get(CONF_DEYE_PROGRAM_2_POWER_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_2_SOC_ENTITY, default=values.get(CONF_DEYE_PROGRAM_2_SOC_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_3_MODE_ENTITY, default=values.get(CONF_DEYE_PROGRAM_3_MODE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_3_TIME_ENTITY, default=values.get(CONF_DEYE_PROGRAM_3_TIME_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_3_CHARGE_ENTITY, default=values.get(CONF_DEYE_PROGRAM_3_CHARGE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_3_POWER_ENTITY, default=values.get(CONF_DEYE_PROGRAM_3_POWER_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_3_SOC_ENTITY, default=values.get(CONF_DEYE_PROGRAM_3_SOC_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_4_TIME_ENTITY, default=values.get(CONF_DEYE_PROGRAM_4_TIME_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_4_CHARGE_ENTITY, default=values.get(CONF_DEYE_PROGRAM_4_CHARGE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_4_POWER_ENTITY, default=values.get(CONF_DEYE_PROGRAM_4_POWER_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_4_SOC_ENTITY, default=values.get(CONF_DEYE_PROGRAM_4_SOC_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_5_TIME_ENTITY, default=values.get(CONF_DEYE_PROGRAM_5_TIME_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_5_CHARGE_ENTITY, default=values.get(CONF_DEYE_PROGRAM_5_CHARGE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_5_POWER_ENTITY, default=values.get(CONF_DEYE_PROGRAM_5_POWER_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_5_SOC_ENTITY, default=values.get(CONF_DEYE_PROGRAM_5_SOC_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_6_TIME_ENTITY, default=values.get(CONF_DEYE_PROGRAM_6_TIME_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_6_CHARGE_ENTITY, default=values.get(CONF_DEYE_PROGRAM_6_CHARGE_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_6_POWER_ENTITY, default=values.get(CONF_DEYE_PROGRAM_6_POWER_ENTITY, "")): str,
            vol.Optional(CONF_DEYE_PROGRAM_6_SOC_ENTITY, default=values.get(CONF_DEYE_PROGRAM_6_SOC_ENTITY, "")): str,
            vol.Required(CONF_MIN_SOC, default=values.get(CONF_MIN_SOC, DEFAULT_MIN_SOC)): vol.Coerce(float),
            vol.Required(CONF_MAX_SOC, default=values.get(CONF_MAX_SOC, DEFAULT_MAX_SOC)): vol.Coerce(float),
            vol.Required(CONF_EXPORT_ALLOWED, default=values.get(CONF_EXPORT_ALLOWED, False)): bool,
            vol.Required(CONF_GRID_CHARGE_ALLOWED, default=values.get(CONF_GRID_CHARGE_ALLOWED, False)): bool,
            vol.Required(CONF_BATTERY_CYCLE_COST, default=values.get(CONF_BATTERY_CYCLE_COST, DEFAULT_BATTERY_CYCLE_COST)): vol.Coerce(float),
            vol.Required(CONF_ENABLE_WRITE_MODE, default=values.get(CONF_ENABLE_WRITE_MODE, False)): bool,
            vol.Required(CONF_UPDATE_INTERVAL_MINUTES, default=values.get(CONF_UPDATE_INTERVAL_MINUTES, DEFAULT_UPDATE_INTERVAL_MINUTES)): vol.Coerce(int),
        }
    )


class HybridAiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return HybridAiOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                normalized = _normalize_user_input(user_input)
            except vol.Invalid:
                errors[CONF_WEEKLY_LOAD_OFFSETS] = "invalid_weekly_load_offsets"
            else:
                return self.async_create_entry(title=DEFAULT_NAME, data=normalized)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema({}),
            errors=errors,
        )


class HybridAiOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                normalized = _normalize_user_input(user_input)
            except vol.Invalid:
                errors[CONF_WEEKLY_LOAD_OFFSETS] = "invalid_weekly_load_offsets"
            else:
                return self.async_create_entry(title="", data=normalized)

        values = _merged_entry_config(self.config_entry)
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(values),
            errors=errors,
        )
