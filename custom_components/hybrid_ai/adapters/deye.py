from __future__ import annotations

from ..const import (
    CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY,
    CONF_DEYE_LOAD_LIMIT_ENTITY,
    CONF_DEYE_PROGRAM_1_MODE_ENTITY,
)
from ..discovery import discover_inverter_entities
from ..models import ControlAction
from .base import InverterAdapter


class DeyeAdapter(InverterAdapter):
    @property
    def name(self) -> str:
        return "deye"

    @property
    def supports_write(self) -> bool:
        return True

    async def async_execute(self, actions: list[ControlAction], dry_run: bool) -> list[dict]:
        rendered: list[dict] = []
        for action in actions:
            service_call = self._map_action_to_service(action)
            record = {
                "adapter": self.name,
                "action": action.action,
                "value": action.value,
                "reason": action.reason,
                "dry_run": dry_run,
                "executed": False,
                "service_call": service_call,
            }
            if not dry_run and service_call:
                await self.hass.services.async_call(
                    service_call["domain"],
                    service_call["service"],
                    service_call["data"],
                    blocking=True,
                )
                record["executed"] = True
            rendered.append(record)
        return rendered

    def _map_action_to_service(self, action: ControlAction) -> dict | None:
        if action.action == "deye_set_load_limit_mode":
            entity_id = self._entity(CONF_DEYE_LOAD_LIMIT_ENTITY)
            if entity_id:
                return {
                    "domain": "select",
                    "service": "select_option",
                    "data": {"entity_id": entity_id, "option": action.value},
                }

        if action.action == "deye_set_battery_charge_current":
            entity_id = self._entity(CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY)
            if entity_id:
                return {
                    "domain": "number",
                    "service": "set_value",
                    "data": {"entity_id": entity_id, "value": action.value},
                }

        if action.action == "deye_set_program_1_mode":
            entity_id = self._entity(CONF_DEYE_PROGRAM_1_MODE_ENTITY)
            if entity_id:
                return {
                    "domain": "select",
                    "service": "select_option",
                    "data": {"entity_id": entity_id, "option": action.value},
                }

        return None

    def _entity(self, key: str) -> str | None:
        entry = self.hass.config_entries.async_get_entry(self.entry_id)
        if entry is None:
            return None
        configured = entry.data.get(key)
        if configured:
            return configured
        discovered = discover_inverter_entities(self.hass)
        return getattr(discovered, key, None)
