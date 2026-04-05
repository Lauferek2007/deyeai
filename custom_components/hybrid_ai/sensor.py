from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DISCOVERY,
    ATTR_EXPECTED_SURPLUS_KWH,
    ATTR_FORECAST_LOAD_KWH,
    ATTR_FORECAST_SOLAR_KWH,
    ATTR_PLAN_SUMMARY,
    ATTR_TARGET_MORNING_SOC,
    DOMAIN,
)
from .coordinator import HybridAiCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HybridAiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            HybridAiDiagnosticSensor(coordinator, entry, "plan_summary", ATTR_PLAN_SUMMARY, None),
            HybridAiDiagnosticSensor(coordinator, entry, "forecast_solar_24h", ATTR_FORECAST_SOLAR_KWH, UnitOfEnergy.KILO_WATT_HOUR),
            HybridAiDiagnosticSensor(coordinator, entry, "forecast_load_24h", ATTR_FORECAST_LOAD_KWH, UnitOfEnergy.KILO_WATT_HOUR),
            HybridAiDiagnosticSensor(coordinator, entry, "expected_surplus_24h", ATTR_EXPECTED_SURPLUS_KWH, UnitOfEnergy.KILO_WATT_HOUR),
            HybridAiDiagnosticSensor(coordinator, entry, "target_morning_soc", ATTR_TARGET_MORNING_SOC, PERCENTAGE),
        ]
    )


class HybridAiDiagnosticSensor(CoordinatorEntity[HybridAiCoordinator], SensorEntity):
    def __init__(
        self,
        coordinator: HybridAiCoordinator,
        entry: ConfigEntry,
        key: str,
        data_key: str,
        unit: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = f"{entry.title} {key.replace('_', ' ')}"
        self._data_key = data_key
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key)

    @property
    def extra_state_attributes(self):
        return {
            "adapter": self.coordinator.data.get("adapter"),
            "dry_run": self.coordinator.data.get("dry_run"),
            "forecast_confidence": self.coordinator.data.get("forecast_confidence"),
            "adapter_actions": self.coordinator.data.get("adapter_actions"),
            "discovery": self.coordinator.data.get(ATTR_DISCOVERY),
        }
