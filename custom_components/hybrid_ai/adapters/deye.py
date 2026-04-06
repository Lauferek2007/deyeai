from __future__ import annotations

from ..const import (
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
            return self._select_calls(CONF_DEYE_LOAD_LIMIT_ENTITY, action.value)

        if action.action == "deye_set_battery_charge_current":
            entity_id = self._entity(CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY)
            if entity_id:
                return [self._number_call(entity_id, action.value)]

        if action.action == "deye_set_program_1_mode":
            return self._select_calls(CONF_DEYE_PROGRAM_1_MODE_ENTITY, action.value)

        if action.action == "deye_prepare_grid_charge_window":
            return []

        if action.action == "deye_enable_system_export":
            if bool(action.value):
                return self._select_calls(CONF_DEYE_WORK_MODE_ENTITY, "Export First") or \
                    self._switch_calls(CONF_DEYE_EXPORT_SURPLUS_ENTITY, True) or \
                    self._switch_calls(CONF_DEYE_SOLAR_EXPORT_ENTITY, True)
            return self._select_calls(CONF_DEYE_WORK_MODE_ENTITY, "Zero Export To Load", "Zero Export To CT") or \
                self._switch_calls(CONF_DEYE_EXPORT_SURPLUS_ENTITY, False) or \
                self._switch_calls(CONF_DEYE_SOLAR_EXPORT_ENTITY, False)

        if action.action == "deye_enable_use_timer":
            if bool(action.value):
                return self._select_calls(CONF_DEYE_TIME_OF_USE_ENTITY, "Week", "Enabled", "On") or \
                    self._switch_calls(CONF_DEYE_USE_TIMER_ENTITY, True)
            return self._select_calls(CONF_DEYE_TIME_OF_USE_ENTITY, "Disabled") or \
                self._switch_calls(CONF_DEYE_USE_TIMER_ENTITY, False)

        if action.action == "deye_enable_grid_charge":
            return self._switch_calls(CONF_DEYE_BATTERY_GRID_CHARGING_ENTITY, bool(action.value)) or \
                self._switch_calls(CONF_DEYE_GRID_CHARGE_ENABLED_ENTITY, bool(action.value))

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
                4: CONF_DEYE_PROGRAM_4_TIME_ENTITY,
                5: CONF_DEYE_PROGRAM_5_TIME_ENTITY,
                6: CONF_DEYE_PROGRAM_6_TIME_ENTITY,
            }
            charge_keys = {
                1: CONF_DEYE_PROGRAM_1_CHARGE_ENTITY,
                2: CONF_DEYE_PROGRAM_2_CHARGE_ENTITY,
                3: CONF_DEYE_PROGRAM_3_CHARGE_ENTITY,
                4: CONF_DEYE_PROGRAM_4_CHARGE_ENTITY,
                5: CONF_DEYE_PROGRAM_5_CHARGE_ENTITY,
                6: CONF_DEYE_PROGRAM_6_CHARGE_ENTITY,
            }
            power_keys = {
                1: CONF_DEYE_PROGRAM_1_POWER_ENTITY,
                2: CONF_DEYE_PROGRAM_2_POWER_ENTITY,
                3: CONF_DEYE_PROGRAM_3_POWER_ENTITY,
                4: CONF_DEYE_PROGRAM_4_POWER_ENTITY,
                5: CONF_DEYE_PROGRAM_5_POWER_ENTITY,
                6: CONF_DEYE_PROGRAM_6_POWER_ENTITY,
            }
            soc_keys = {
                1: CONF_DEYE_PROGRAM_1_SOC_ENTITY,
                2: CONF_DEYE_PROGRAM_2_SOC_ENTITY,
                3: CONF_DEYE_PROGRAM_3_SOC_ENTITY,
                4: CONF_DEYE_PROGRAM_4_SOC_ENTITY,
                5: CONF_DEYE_PROGRAM_5_SOC_ENTITY,
                6: CONF_DEYE_PROGRAM_6_SOC_ENTITY,
            }
            mode_options = {
                "grid_charge": ("Charge", "Grid charge"),
                "export_battery": ("Discharge", "Selling First"),
                "export_surplus": ("Selling First", "Discharge"),
            }
            charge_options = {
                "grid_charge": ("Grid", "Both", "Generator"),
                "export_battery": ("Disabled",),
                "export_surplus": ("Disabled",),
            }
            power_values = {
                "grid_charge": 10000,
                "export_battery": 10000,
                "export_surplus": 10000,
            }
            soc_values = {
                "grid_charge": 90,
                "export_battery": 20,
                "export_surplus": 15,
            }
            for period in action.value:
                program = int(period["program"])
                mode_key = mode_keys.get(program)
                time_key = time_keys.get(program)
                charge_key = charge_keys.get(program)
                power_key = power_keys.get(program)
                soc_key = soc_keys.get(program)
                mode_entity = self._entity(mode_key) if mode_key else None
                time_entity = self._entity(time_key) if time_key else None
                charge_entity = self._entity(charge_key) if charge_key else None
                power_entity = self._entity(power_key) if power_key else None
                soc_entity = self._entity(soc_key) if soc_key else None
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
                    mode_call = self._select_entity_call(mode_entity, mode_options.get(period["mode"], ("Selling First",)))
                    if mode_call:
                        calls.append(mode_call)
                if charge_entity:
                    charge_call = self._select_entity_call(charge_entity, charge_options.get(period["mode"], ("Disabled",)))
                    if charge_call:
                        calls.append(charge_call)
                if power_entity:
                    calls.append(self._number_call(power_entity, power_values.get(period["mode"], 10000)))
                if soc_entity:
                    calls.append(self._number_call(soc_entity, soc_values.get(period["mode"], 20)))
            return calls

        return []

    def _switch_calls(self, key: str, enabled: bool) -> list[dict]:
        entity_id = self._entity(key)
        if not entity_id:
            return []
        return [
            {
                "domain": "switch",
                "service": "turn_on" if enabled else "turn_off",
                "data": {"entity_id": entity_id},
            }
        ]

    def _select_calls(self, key: str, *options: str) -> list[dict]:
        entity_id = self._entity(key)
        if not entity_id:
            return []
        call = self._select_entity_call(entity_id, options)
        return [call] if call else []

    def _select_entity_call(self, entity_id: str, options: tuple[str, ...] | list[str]) -> dict | None:
        state = self.hass.states.get(entity_id)
        available = state.attributes.get("options", []) if state else []
        normalized_available = {
            self._normalize_option(option): option for option in available if isinstance(option, str)
        }
        for option in options:
            matched = normalized_available.get(self._normalize_option(option))
            if matched:
                return {
                    "domain": "select",
                    "service": "select_option",
                    "data": {"entity_id": entity_id, "option": matched},
                }
        if options:
            return {
                "domain": "select",
                "service": "select_option",
                "data": {"entity_id": entity_id, "option": options[0]},
            }
        return None

    def _number_call(self, entity_id: str, value: float | int) -> dict:
        state = self.hass.states.get(entity_id)
        attrs = state.attributes if state else {}
        try:
            minimum = float(attrs.get("min"))
        except (TypeError, ValueError):
            minimum = None
        try:
            maximum = float(attrs.get("max"))
        except (TypeError, ValueError):
            maximum = None

        numeric_value = float(value)
        if minimum is not None:
            numeric_value = max(numeric_value, minimum)
        if maximum is not None:
            numeric_value = min(numeric_value, maximum)
        if numeric_value.is_integer():
            numeric_value = int(numeric_value)
        return {
            "domain": "number",
            "service": "set_value",
            "data": {"entity_id": entity_id, "value": numeric_value},
        }

    def _normalize_option(self, option: str) -> str:
        return "".join(char for char in option.lower() if char.isalnum())

    def _entity(self, key: str) -> str | None:
        if not key:
            return None
        configured = self._config_value(key)
        if configured:
            return configured
        discovered = discover_inverter_entities(self.hass)
        return getattr(discovered, key, None)
