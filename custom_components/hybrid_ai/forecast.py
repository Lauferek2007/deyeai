from __future__ import annotations

from homeassistant.core import HomeAssistant


class SolarForecastProvider:
    def __init__(self, hass: HomeAssistant, entity_id: str | None) -> None:
        self._hass = hass
        self._entity_id = entity_id

    def get_next_24h_kwh(self) -> tuple[float, dict[str, str]]:
        if not self._entity_id:
            return 0.0, {"source": "none"}

        state = self._hass.states.get(self._entity_id)
        if state is None:
            return 0.0, {"source": self._entity_id, "status": "missing"}

        try:
            return float(state.state), {"source": self._entity_id, "status": "ok"}
        except ValueError:
            return 0.0, {"source": self._entity_id, "status": "invalid"}
