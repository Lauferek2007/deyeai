from __future__ import annotations

from dataclasses import asdict

from homeassistant.core import HomeAssistant, State

from .models import DiscoveryResult

ADAPTER_KEYWORDS = {
    "huawei": ["huawei", "sun2000", "huawei_solar"],
    "goodwe": ["goodwe", "et_", "eh_", "gw"],
    "solarman": ["solarman", "deye", "sunsynk"],
}

ENTITY_PATTERNS = {
    "battery_soc_entity": ["battery_soc", "state_of_capacity", "soc", "battery_level"],
    "load_power_entity": ["load_power", "house_load", "home_load", "consumption", "active_power_load"],
    "pv_power_entity": ["pv_power", "solar_power", "photovoltaic", "generation_power", "inverter_power"],
    "grid_power_entity": ["grid_power", "meter_power", "active_power_grid", "import_export", "grid_exchange"],
    "solar_forecast_entity": ["solar_forecast", "pv_forecast", "forecast_solar", "forecast_energy"],
}

EXCLUDE_KEYWORDS = ["daily", "monthly", "yearly", "total", "lifetime", "status", "temperature", "alarm"]


def discover_inverter_entities(hass: HomeAssistant) -> DiscoveryResult:
    states = list(hass.states.async_all())
    adapter, adapter_confidence, matched_by = _detect_adapter(states)
    candidates = {
        field: _pick_best_entity(states, patterns, adapter)
        for field, patterns in ENTITY_PATTERNS.items()
    }

    confidence = adapter_confidence
    filled = sum(1 for value in candidates.values() if value)
    confidence = max(confidence, min(0.35 + filled * 0.12, 0.92))

    notes = []
    if filled < 4:
        notes.append("Autodiscovery found only a partial entity set; manual confirmation is recommended.")
    if adapter == "generic":
        notes.append("No popular inverter family matched strongly; using generic entity adapter.")

    return DiscoveryResult(
        adapter=adapter,
        confidence=round(confidence, 2),
        matched_by=matched_by,
        battery_soc_entity=candidates["battery_soc_entity"],
        load_power_entity=candidates["load_power_entity"],
        pv_power_entity=candidates["pv_power_entity"],
        grid_power_entity=candidates["grid_power_entity"],
        solar_forecast_entity=candidates["solar_forecast_entity"],
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
