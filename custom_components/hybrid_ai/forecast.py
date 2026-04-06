from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CONDITION_FACTORS = {
    "sunny": 1.0,
    "clear": 0.96,
    "clear-night": 0.06,
    "partlycloudy": 0.74,
    "cloudy": 0.48,
    "windy": 0.68,
    "fog": 0.5,
    "rainy": 0.26,
    "pouring": 0.16,
    "lightning": 0.14,
    "lightning-rainy": 0.12,
    "snowy": 0.2,
    "snowy-rainy": 0.16,
    "hail": 0.1,
}


class SolarForecastProvider:
    def __init__(
        self,
        hass: HomeAssistant,
        entity_id: str | None,
        weather_entity_id: str | None = None,
        manual_max_daily_kwh: float = 0.0,
    ) -> None:
        self._hass = hass
        self._entity_id = entity_id
        self._weather_entity_id = weather_entity_id
        self._manual_max_daily_kwh = max(float(manual_max_daily_kwh), 0.0)

    async def get_next_24h_kwh(self) -> tuple[float, dict[str, str | float | bool]]:
        direct_value, direct_meta = self._read_numeric_forecast()
        if direct_value is not None:
            value = max(direct_value, 0.0)
            if self._manual_max_daily_kwh > 0:
                direct_meta["manual_max_daily_kwh"] = round(self._manual_max_daily_kwh, 2)
                if value > self._manual_max_daily_kwh:
                    value = self._manual_max_daily_kwh
                    direct_meta["capped_by_manual_max"] = True
            return round(value, 3), direct_meta

        if self._manual_max_daily_kwh > 0:
            estimate, estimate_meta = await self._estimate_from_weather()
            return round(max(estimate, 0.0), 3), estimate_meta

        return 0.0, {"source": "none", "status": "missing"}

    def _read_numeric_forecast(self) -> tuple[float | None, dict[str, str | float | bool]]:
        if not self._entity_id:
            return None, {"source": "none", "status": "not_configured"}

        state = self._hass.states.get(self._entity_id)
        if state is None:
            return None, {"source": self._entity_id, "status": "missing"}

        try:
            value = float(state.state)
        except ValueError:
            return None, {"source": self._entity_id, "status": "invalid"}

        return value, {"source": self._entity_id, "status": "ok", "method": "entity"}

    async def _estimate_from_weather(self) -> tuple[float, dict[str, str | float | bool]]:
        forecast_factor, details = await self._read_weather_factor()
        estimated = self._manual_max_daily_kwh * forecast_factor
        return estimated, {
            "source": self._weather_entity_id or "manual_max_daily_pv_kwh",
            "status": details.get("status", "estimated"),
            "method": details.get("method", "manual_fallback"),
            "condition": details.get("condition", "unknown"),
            "factor": round(forecast_factor, 3),
            "manual_max_daily_kwh": round(self._manual_max_daily_kwh, 2),
        }

    async def _read_weather_factor(self) -> tuple[float, dict[str, str | float]]:
        if not self._weather_entity_id:
            return 0.65, {
                "status": "weather_not_configured",
                "method": "manual_fallback",
                "condition": "unknown",
            }

        service_response = await self._call_weather_service("hourly")
        hourly_forecast = self._extract_forecast(service_response)
        if hourly_forecast:
            factor = self._factor_from_hourly(hourly_forecast)
            return factor, {
                "status": "ok",
                "method": "weather_hourly_service",
                "condition": str(hourly_forecast[0].get("condition", "unknown")),
            }

        service_response = await self._call_weather_service("daily")
        daily_forecast = self._extract_forecast(service_response)
        if daily_forecast:
            first = daily_forecast[0]
            factor = self._factor_for_condition(str(first.get("condition", "unknown")))
            return factor, {
                "status": "ok",
                "method": "weather_daily_service",
                "condition": str(first.get("condition", "unknown")),
            }

        state = self._hass.states.get(self._weather_entity_id)
        if state is None:
            return 0.65, {
                "status": "weather_missing",
                "method": "manual_fallback",
                "condition": "unknown",
            }

        condition = str(state.state)
        factor = self._factor_for_condition(condition)
        cloud_coverage = state.attributes.get("cloud_coverage")
        if cloud_coverage is not None:
            try:
                factor *= max(0.18, 1 - (float(cloud_coverage) / 110))
            except (TypeError, ValueError):
                pass
        return factor, {
            "status": "ok",
            "method": "weather_state",
            "condition": condition,
        }

    async def _call_weather_service(self, forecast_type: str):
        try:
            return await self._hass.services.async_call(
                "weather",
                "get_forecasts",
                {"type": forecast_type},
                target={"entity_id": [self._weather_entity_id]},
                blocking=True,
                return_response=True,
            )
        except Exception as exc:  # pragma: no cover - HA service compatibility
            _LOGGER.debug("Weather forecast service failed for %s: %s", forecast_type, exc)
            return None

    def _extract_forecast(self, response) -> list[dict]:
        if not isinstance(response, dict):
            return []
        entity_data = response.get(self._weather_entity_id)
        if not isinstance(entity_data, dict):
            return []
        forecast = entity_data.get("forecast")
        if not isinstance(forecast, Sequence):
            return []
        return [item for item in forecast if isinstance(item, dict)]

    def _factor_from_hourly(self, forecast: list[dict]) -> float:
        daylight_items = forecast[:24]
        weighted_total = 0.0
        weight_sum = 0.0
        for hour_index, item in enumerate(daylight_items):
            condition = str(item.get("condition", "unknown"))
            hour = self._hour_from_item(item, hour_index)
            if 9 <= hour <= 16:
                weight = 1.0
            elif 7 <= hour < 9 or 16 < hour <= 18:
                weight = 0.6
            else:
                weight = 0.18
            factor = self._factor_for_condition(condition)
            cloud_coverage = item.get("cloud_coverage")
            try:
                if cloud_coverage is not None:
                    factor *= max(0.12, 1 - (float(cloud_coverage) / 120))
            except (TypeError, ValueError):
                pass
            weighted_total += factor * weight
            weight_sum += weight
        if weight_sum <= 0:
            return 0.65
        return max(min(weighted_total / weight_sum, 1.0), 0.08)

    def _factor_for_condition(self, condition: str) -> float:
        normalized = condition.lower()
        return CONDITION_FACTORS.get(normalized, 0.62)

    def _hour_from_item(self, item: dict, fallback_hour: int) -> int:
        raw_value = item.get("datetime")
        if not raw_value:
            return fallback_hour % 24
        try:
            return datetime.fromisoformat(str(raw_value)).hour
        except ValueError:
            return fallback_hour % 24
