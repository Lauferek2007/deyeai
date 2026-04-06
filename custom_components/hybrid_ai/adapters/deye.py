from __future__ import annotations

from ..const import (
    CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY,
    CONF_DEYE_LOAD_LIMIT_ENTITY,
    CONF_DEYE_PROGRAM_1_MODE_ENTITY,
    CONF_DEYE_PROGRAM_1_TIME_ENTITY,
    CONF_DEYE_PROGRAM_2_MODE_ENTITY,
    CONF_DEYE_PROGRAM_2_TIME_ENTITY,
    CONF_DEYE_PROGRAM_3_MODE_ENTITY,
    CONF_DEYE_PROGRAM_3_TIME_ENTITY,
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
            service_calls = self._map_action_to_services(action)
            record = {
                "adapter": self.name,
                "action": action.action,
                "value": action.value,
                "reason": action.reason,
                "dry_run": dry_run,
                "executed": False,
                "service_call": service_calls,
            }
            if not dry_run and service_calls:
                for service_call in service_calls:
                    await self.hass.services.async_call(
                        service_call["domain"],
                        service_call["service"],
                        service_call["data"],
                        blocking=True,
                    )
                record["executed"] = True
            rendered.append(record)
        return rendered

    def _map_action_to_services(self, action: ControlAction) -> list[dict]:
        if action.action == "deye_set_load_limit_mode":
            entity_id = self._entity(CONF_DEYE_LOAD_LIMIT_ENTITY)
            if entity_id:
                return [
                    {
                        "domain": "select",
                        "service": "select_option",
                        "data": {"entity_id": entity_id, "option": action.value},
                    }
                ]

        if action.action == "deye_set_battery_charge_current":
            entity_id = self._entity(CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY)
            if entity_id:
                return [
                    {
                        "domain": "number",
                        "service": "set_value",
                        "data": {"entity_id": entity_id, "value": action.value},
                    }
                ]

        if action.action == "deye_set_program_1_mode":
            entity_id = self._entity(CONF_DEYE_PROGRAM_1_MODE_ENTITY)
            if entity_id:
                return [
                    {
                        "domain": "select",
                        "service": "select_option",
                        "data": {"entity_id": entity_id, "option": action.value},
                    }
                ]

        if action.action == "deye_apply_tou_schedule":
            calls: list[dict] = []
            mode_keys = {
                1: CONF_DEYE_PROGRAM_1_MODE_ENTITY,
                2: CONF_DEYE_PROGRAM_2_MODE_ENTITY,
                3: CONF_DEYE_PROGRAM_3_MODE_ENTITY,
            }
            time_keys = {
                1: CONF_DEYE_PROGRAM_1_TIME_ENTITY,
                2: CONF_DEYE_PROGRAM_2_TIME_ENTITY,
                3: CONF_DEYE_PROGRAM_3_TIME_ENTITY,
            }
            mode_options = {
                "grid_charge": "Charge",
                "export_battery": "Discharge",
                "export_surplus": "Selling First",
            }
            for period in action.value:
                program = int(period["program"])
                mode_entity = self._entity(mode_keys[program])
                time_entity = self._entity(time_keys[program])
                if time_entity:
                    calls.append(
                        {
                            "domain": "time",
                            "service": "set_value",
                            "data": {
                                "entity_id": time_entity,
                                "time": f"{int(period['start_hour']):02d}:00",
                            },
                        }
                    )
                if mode_entity:
                    calls.append(
                        {
                            "domain": "select",
                            "service": "select_option",
                            "data": {
                                "entity_id": mode_entity,
                                "option": mode_options.get(period["mode"], "Selling First"),
                            },
                        }
                    )
            return calls

        return []

    def _entity(self, key: str) -> str | None:
        entry = self.hass.config_entries.async_get_entry(self.entry_id)
        if entry is None:
            return None
        configured = entry.data.get(key)
        if configured:
            return configured
        discovered = discover_inverter_entities(self.hass)
        return getattr(discovered, key, None)
