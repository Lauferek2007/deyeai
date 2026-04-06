from __future__ import annotations

from dataclasses import asdict

from homeassistant.core import HomeAssistant, State

from .models import DiscoveryResult

ADAPTER_KEYWORDS = {
    "deye": ["deye", "sunsynk", "solarman"],
    "huawei": ["huawei", "sun2000", "huawei_solar"],
    "goodwe": ["goodwe", "et_", "eh_", "gw"],
    "solarman": ["solarman", "deye", "sunsynk"],
}

ENTITY_PATTERNS = {
    "battery_soc_entity": ["battery_soc", "state_of_capacity", "soc", "battery_level", "battery"],
    "load_power_entity": ["load_power", "house_load", "home_load", "consumption", "active_power_load"],
    "pv_power_entity": ["pv_power", "solar_power", "photovoltaic", "generation_power", "inverter_power"],
    "grid_power_entity": ["grid_power", "meter_power", "active_power_grid", "import_export", "grid_exchange"],
    "solar_forecast_entity": ["solar_forecast", "pv_forecast", "forecast_solar", "forecast_energy"],
    "price_import_entity": ["nordpool", "import_price", "buy_price", "energy_price", "spot_price"],
    "price_export_entity": ["export_price", "sell_price", "feed_in_tariff", "spot_sell", "nordpool_export"],
    "deye_work_mode_entity": ["work_mode"],
    "deye_time_of_use_entity": ["time_of_use"],
    "deye_export_surplus_entity": ["export_surplus"],
    "deye_battery_grid_charging_entity": ["battery_grid_charging"],
    "deye_grid_charge_enabled_entity": ["grid_charge_enabled"],
    "deye_load_limit_entity": ["load_limit"],
    "deye_solar_export_entity": ["solar_export"],
    "deye_use_timer_entity": ["use_timer"],
    "deye_battery_max_charge_current_entity": ["battery_max_charge_current", "max_charge_current"],
    "deye_program_1_mode_entity": ["prog1_mode", "program_1_mode"],
    "deye_program_1_time_entity": ["prog1_time", "program_1_time"],
    "deye_program_1_charge_entity": ["prog1_charge", "program_1_charge"],
    "deye_program_1_power_entity": ["prog1_power", "program_1_power"],
    "deye_program_1_soc_entity": ["prog1_soc", "program_1_soc"],
    "deye_program_2_mode_entity": ["prog2_mode", "program_2_mode"],
    "deye_program_2_time_entity": ["prog2_time", "program_2_time"],
    "deye_program_2_charge_entity": ["prog2_charge", "program_2_charge"],
    "deye_program_2_power_entity": ["prog2_power", "program_2_power"],
    "deye_program_2_soc_entity": ["prog2_soc", "program_2_soc"],
    "deye_program_3_mode_entity": ["prog3_mode", "program_3_mode"],
    "deye_program_3_time_entity": ["prog3_time", "program_3_time"],
    "deye_program_3_charge_entity": ["prog3_charge", "program_3_charge"],
    "deye_program_3_power_entity": ["prog3_power", "program_3_power"],
    "deye_program_3_soc_entity": ["prog3_soc", "program_3_soc"],
    "deye_program_4_time_entity": ["prog4_time", "program_4_time"],
    "deye_program_4_charge_entity": ["prog4_charge", "program_4_charge"],
    "deye_program_4_power_entity": ["prog4_power", "program_4_power"],
    "deye_program_4_soc_entity": ["prog4_soc", "program_4_soc"],
    "deye_program_5_time_entity": ["prog5_time", "program_5_time"],
    "deye_program_5_charge_entity": ["prog5_charge", "program_5_charge"],
    "deye_program_5_power_entity": ["prog5_power", "program_5_power"],
    "deye_program_5_soc_entity": ["prog5_soc", "program_5_soc"],
    "deye_program_6_time_entity": ["prog6_time", "program_6_time"],
    "deye_program_6_charge_entity": ["prog6_charge", "program_6_charge"],
    "deye_program_6_power_entity": ["prog6_power", "program_6_power"],
    "deye_program_6_soc_entity": ["prog6_soc", "program_6_soc"],
}

EXCLUDE_KEYWORDS = ["daily", "monthly", "yearly", "total", "lifetime", "status", "temperature", "alarm"]


def discover_inverter_entities(hass: HomeAssistant) -> DiscoveryResult:
    states = list(hass.states.async_all())
    adapter, adapter_confidence, matched_by = _detect_adapter(states)
    candidates = {
        field: _pick_best_entity(states, patterns, adapter)
        for field, patterns in ENTITY_PATTERNS.items()
    }
    candidates["weather_entity"] = _pick_best_weather_entity(states)

    confidence = adapter_confidence
    filled = sum(1 for value in candidates.values() if value)
    confidence = max(confidence, min(0.35 + filled * 0.12, 0.92))

    notes = []
    if filled < 4:
        notes.append("Autodiscovery found only a partial entity set; manual confirmation is recommended.")
    if adapter == "generic":
        notes.append("No popular inverter family matched strongly; using generic entity adapter.")
    if adapter == "deye":
        notes.append("Deye/Sunsynk style entities detected; load limit and charge-current controls will be preferred.")

    return DiscoveryResult(
        adapter=adapter,
        confidence=round(confidence, 2),
        matched_by=matched_by,
        battery_soc_entity=candidates["battery_soc_entity"],
        load_power_entity=candidates["load_power_entity"],
        pv_power_entity=candidates["pv_power_entity"],
        grid_power_entity=candidates["grid_power_entity"],
        solar_forecast_entity=candidates["solar_forecast_entity"],
        weather_entity=candidates["weather_entity"],
        price_import_entity=candidates["price_import_entity"],
        price_export_entity=candidates["price_export_entity"],
        deye_work_mode_entity=candidates["deye_work_mode_entity"],
        deye_time_of_use_entity=candidates["deye_time_of_use_entity"],
        deye_export_surplus_entity=candidates["deye_export_surplus_entity"],
        deye_battery_grid_charging_entity=candidates["deye_battery_grid_charging_entity"],
        deye_grid_charge_enabled_entity=candidates["deye_grid_charge_enabled_entity"],
        deye_load_limit_entity=candidates["deye_load_limit_entity"],
        deye_solar_export_entity=candidates["deye_solar_export_entity"],
        deye_use_timer_entity=candidates["deye_use_timer_entity"],
        deye_battery_max_charge_current_entity=candidates["deye_battery_max_charge_current_entity"],
        deye_program_1_mode_entity=candidates["deye_program_1_mode_entity"],
        deye_program_1_time_entity=candidates["deye_program_1_time_entity"],
        deye_program_1_charge_entity=candidates["deye_program_1_charge_entity"],
        deye_program_1_power_entity=candidates["deye_program_1_power_entity"],
        deye_program_1_soc_entity=candidates["deye_program_1_soc_entity"],
        deye_program_2_mode_entity=candidates["deye_program_2_mode_entity"],
        deye_program_2_time_entity=candidates["deye_program_2_time_entity"],
        deye_program_2_charge_entity=candidates["deye_program_2_charge_entity"],
        deye_program_2_power_entity=candidates["deye_program_2_power_entity"],
        deye_program_2_soc_entity=candidates["deye_program_2_soc_entity"],
        deye_program_3_mode_entity=candidates["deye_program_3_mode_entity"],
        deye_program_3_time_entity=candidates["deye_program_3_time_entity"],
        deye_program_3_charge_entity=candidates["deye_program_3_charge_entity"],
        deye_program_3_power_entity=candidates["deye_program_3_power_entity"],
        deye_program_3_soc_entity=candidates["deye_program_3_soc_entity"],
        deye_program_4_time_entity=candidates["deye_program_4_time_entity"],
        deye_program_4_charge_entity=candidates["deye_program_4_charge_entity"],
        deye_program_4_power_entity=candidates["deye_program_4_power_entity"],
        deye_program_4_soc_entity=candidates["deye_program_4_soc_entity"],
        deye_program_5_time_entity=candidates["deye_program_5_time_entity"],
        deye_program_5_charge_entity=candidates["deye_program_5_charge_entity"],
        deye_program_5_power_entity=candidates["deye_program_5_power_entity"],
        deye_program_5_soc_entity=candidates["deye_program_5_soc_entity"],
        deye_program_6_time_entity=candidates["deye_program_6_time_entity"],
        deye_program_6_charge_entity=candidates["deye_program_6_charge_entity"],
        deye_program_6_power_entity=candidates["deye_program_6_power_entity"],
        deye_program_6_soc_entity=candidates["deye_program_6_soc_entity"],
        notes=notes,
    )


def discovery_as_dict(result: DiscoveryResult) -> dict:
    return asdict(result)


def _detect_adapter(states: list[State]) -> tuple[str, float, str]:
    scores = {name: 0 for name in ADAPTER_KEYWORDS}
    for state in states:
        haystack = _state_haystack(state)
        for adapter, keywords in ADAPTER_KEYWORDS.items():
            for keyword in keywords:
                if keyword in haystack:
                    scores[adapter] += 1

    best_adapter = max(scores, key=scores.get, default="generic")
    best_score = scores.get(best_adapter, 0)
    if best_score <= 0:
        return "generic", 0.25, "fallback"

    confidence = min(0.35 + best_score * 0.08, 0.9)
    return best_adapter, confidence, "entity_keywords"


def _pick_best_entity(states: list[State], patterns: list[str], adapter: str) -> str | None:
    ranked: list[tuple[int, str]] = []
    for state in states:
        entity_id = state.entity_id
        haystack = _state_haystack(state)
        if any(excluded in haystack for excluded in EXCLUDE_KEYWORDS):
            continue

        score = 0
        for pattern in patterns:
            if pattern in haystack:
                score += 10
            elif pattern.replace("_", "") in haystack.replace("_", ""):
                score += 6

        if adapter != "generic" and adapter in haystack:
            score += 4

        unit = str(state.attributes.get("unit_of_measurement", "")).lower()
        device_class = str(state.attributes.get("device_class", "")).lower()
        state_class = str(state.attributes.get("state_class", "")).lower()

        if "soc" in patterns[0] and "%" in unit:
            score += 5
        if "power" in patterns[0] and unit in {"w", "kw"}:
            score += 5
        if "forecast" in patterns[0] and unit in {"kwh", "wh"}:
            score += 5
        if device_class in {"power", "energy", "battery"}:
            score += 2
        if state_class in {"measurement", "total", "total_increasing"}:
            score += 1
        if entity_id.startswith("sensor."):
            score += 1

        if score > 0:
            ranked.append((score, entity_id))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1] if ranked else None


def _state_haystack(state: State) -> str:
    friendly = str(state.attributes.get("friendly_name", ""))
    return f"{state.entity_id} {friendly}".lower()


def _pick_best_weather_entity(states: list[State]) -> str | None:
    weather_entities = [
        state.entity_id
        for state in states
        if state.entity_id.startswith("weather.")
    ]
    if not weather_entities:
        return None

    preferred = [
        entity_id
        for entity_id in weather_entities
        if "forecast" in entity_id or "dom" in entity_id or "home" in entity_id
    ]
    return preferred[0] if preferred else weather_entities[0]
