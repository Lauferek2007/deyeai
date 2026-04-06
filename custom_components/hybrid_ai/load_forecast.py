from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import timedelta
import math

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "hybrid_ai_load_profile"
SLOTS_PER_DAY = 24
PROFILE_DAYS = 7
EWMA_ALPHA = 0.18


def _empty_profile() -> dict[str, list[float]]:
    return {str(day): [0.0] * SLOTS_PER_DAY for day in range(PROFILE_DAYS)}


def _empty_counts() -> dict[str, list[int]]:
    return {str(day): [0] * SLOTS_PER_DAY for day in range(PROFILE_DAYS)}


class LoadForecaster:
    """Automatic load learner with weekday/hour profiles."""

    def __init__(self, hass: HomeAssistant, load_entity_id: str | None, entry_id: str) -> None:
        self._hass = hass
        self._load_entity_id = load_entity_id
        self._entry_id = entry_id
        self._samples: deque[float] = deque(maxlen=96 * 14)
        self._weekday_profile = _empty_profile()
        self._weekday_counts = _empty_counts()
        self._sample_counter = 0
        self._last_saved_counter = 0
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{entry_id}")

    async def async_initialize(self) -> None:
        stored = await self._store.async_load()
        if not stored:
            return
        self._weekday_profile = stored.get("weekday_profile", _empty_profile())
        self._weekday_counts = stored.get("weekday_counts", _empty_counts())

    async def async_persist(self, force: bool = False) -> None:
        if not force and self._sample_counter - self._last_saved_counter < 8:
            return
        await self._store.async_save(
            {
                "weekday_profile": self._weekday_profile,
                "weekday_counts": self._weekday_counts,
            }
        )
        self._last_saved_counter = self._sample_counter

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
        self._update_profile(value)
        return value

    def forecast_next_24h_kwh(self, current_load_w: float) -> tuple[float, float, float]:
        if not self._samples:
            return current_load_w * 24 / 1000, current_load_w * 8 / 1000, 0.2

        now = dt_util.now()
        daily_kwh = 0.0
        overnight_kwh = 0.0
        confidence_components: list[float] = []

        recent_w = sum(list(self._samples)[-8:]) / min(len(self._samples), 8)
        global_avg_w = sum(self._samples) / len(self._samples)

        for hour_offset in range(24):
            target = now + timedelta(hours=hour_offset)
            slot_w, slot_confidence = self._predict_slot(target, recent_w, global_avg_w, current_load_w)
            daily_kwh += slot_w / 1000
            if target.hour < 6:
                overnight_kwh += slot_w / 1000
            confidence_components.append(slot_confidence)

        confidence = sum(confidence_components) / len(confidence_components)
        return daily_kwh, overnight_kwh, min(max(confidence, 0.2), 0.93)

    def get_profile_summary(self) -> dict:
        total_samples = sum(sum(day_counts) for day_counts in self._weekday_counts.values())
        coverage = {
            day: sum(1 for count in counts if count > 0)
            for day, counts in self._weekday_counts.items()
        }
        return {
            "total_samples": total_samples,
            "slots_with_history": coverage,
            "has_full_week_profile": all(value >= 12 for value in coverage.values()),
            "current_weekday_profile": deepcopy(
                self._weekday_profile[str(dt_util.now().weekday())]
            ),
        }

    def _predict_slot(
        self,
        target,
        recent_w: float,
        global_avg_w: float,
        fallback_w: float,
    ) -> tuple[float, float]:
        day_key = str(target.weekday())
        slot = target.hour
        weekday_value = self._weekday_profile[day_key][slot]
        weekday_count = self._weekday_counts[day_key][slot]

        previous_day_slot = self._weekday_profile[str((target.weekday() - 1) % 7)][slot]
        next_day_slot = self._weekday_profile[str((target.weekday() + 1) % 7)][slot]
        neighborhood = [value for value in (previous_day_slot, weekday_value, next_day_slot) if value > 0]
        neighborhood_avg = sum(neighborhood) / len(neighborhood) if neighborhood else 0.0

        if weekday_count > 0:
            predicted = (weekday_value * 0.55) + (recent_w * 0.2) + (global_avg_w * 0.15) + (neighborhood_avg * 0.1)
            confidence = min(0.45 + math.log10(weekday_count + 1) * 0.18, 0.92)
        elif neighborhood_avg > 0:
            predicted = (neighborhood_avg * 0.55) + (recent_w * 0.25) + (global_avg_w * 0.2)
            confidence = 0.5
        else:
            predicted = (fallback_w * 0.4) + (recent_w * 0.3) + (global_avg_w * 0.3)
            confidence = 0.3

        return max(predicted, 0.0), confidence

    def _update_profile(self, value: float) -> None:
        now = dt_util.now()
        day_key = str(now.weekday())
        slot = now.hour
        previous = self._weekday_profile[day_key][slot]
        count = self._weekday_counts[day_key][slot]

        if count == 0 or previous <= 0:
            updated = value
        else:
            updated = (previous * (1 - EWMA_ALPHA)) + (value * EWMA_ALPHA)

        self._weekday_profile[day_key][slot] = round(updated, 3)
        self._weekday_counts[day_key][slot] = count + 1
        self._sample_counter += 1
