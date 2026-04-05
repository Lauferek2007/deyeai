from __future__ import annotations

from collections import deque

from homeassistant.core import HomeAssistant


class LoadForecaster:
    """Lightweight forecast based on recent and historical observations."""

    def __init__(self, hass: HomeAssistant, load_entity_id: str | None) -> None:
        self._hass = hass
        self._load_entity_id = load_entity_id
        self._samples: deque[float] = deque(maxlen=96 * 14)

    def ingest_current_sample(self) -> float:
        if not self._load_entity_id:
            return 0.0

        state = self._hass.states.get(self._load_entity_id)
        if state is None:
            return 0.0

        try:
            value = max(float(state.state), 0.0)
        except ValueError:
            value = 0.0

        self._samples.append(value)
        return value

    def forecast_next_24h_kwh(self, current_load_w: float) -> tuple[float, float, float]:
        if not self._samples:
            return current_load_w * 24 / 1000, current_load_w * 8 / 1000, 0.2

        average_w = sum(self._samples) / len(self._samples)
        recent_w = sum(list(self._samples)[-8:]) / min(len(self._samples), 8)
        blended_w = (average_w * 0.7) + (recent_w * 0.3)
        return blended_w * 24 / 1000, blended_w * 8 / 1000, min(0.3 + len(self._samples) / 500, 0.85)
