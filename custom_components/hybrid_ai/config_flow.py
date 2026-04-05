from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ADAPTER,
    CONF_AUTO_DISCOVERY,
    CONF_BATTERY_CAPACITY_KWH,
    CONF_BATTERY_SOC_ENTITY,
    CONF_ENABLE_WRITE_MODE,
    CONF_EXPORT_ALLOWED,
    CONF_GRID_POWER_ENTITY,
    CONF_LOAD_POWER_ENTITY,
    CONF_MAX_SOC,
    CONF_MIN_SOC,
    CONF_PV_POWER_ENTITY,
    CONF_SOLAR_FORECAST_ENTITY,
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_ADAPTER,
    DEFAULT_MAX_SOC,
    DEFAULT_MIN_SOC,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)


class HybridAiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_ADAPTER, default=DEFAULT_ADAPTER): vol.In(["auto", "generic", "solarman", "goodwe", "huawei"]),
                vol.Required(CONF_AUTO_DISCOVERY, default=True): bool,
                vol.Optional(CONF_BATTERY_SOC_ENTITY, default=""): str,
                vol.Required(CONF_BATTERY_CAPACITY_KWH, default=10.0): vol.Coerce(float),
                vol.Optional(CONF_LOAD_POWER_ENTITY, default=""): str,
                vol.Optional(CONF_PV_POWER_ENTITY, default=""): str,
                vol.Optional(CONF_GRID_POWER_ENTITY, default=""): str,
                vol.Optional(CONF_SOLAR_FORECAST_ENTITY, default=""): str,
                vol.Required(CONF_MIN_SOC, default=DEFAULT_MIN_SOC): vol.Coerce(float),
                vol.Required(CONF_MAX_SOC, default=DEFAULT_MAX_SOC): vol.Coerce(float),
                vol.Required(CONF_EXPORT_ALLOWED, default=False): bool,
                vol.Required(CONF_ENABLE_WRITE_MODE, default=False): bool,
                vol.Required(CONF_UPDATE_INTERVAL_MINUTES, default=DEFAULT_UPDATE_INTERVAL_MINUTES): vol.Coerce(int),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
