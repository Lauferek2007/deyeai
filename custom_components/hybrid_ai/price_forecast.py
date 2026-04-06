from __future__ import annotations

from homeassistant.core import HomeAssistant

from .models import PriceBundle


class PriceForecastProvider:
    def __init__(self, hass: HomeAssistant, import_entity_id: str | None, export_entity_id: str | None) -> None:
        self._hass = hass
        self._import_entity_id = import_entity_id
        self._export_entity_id = export_entity_id

    def get_next_24h_prices(self) -> PriceBundle:
        import_prices, import_meta = self._read_prices(self._import_entity_id)
        export_prices, export_meta = self._read_prices(self._export_entity_id)

        avg_import = sum(import_prices) / len(import_prices) if import_prices else 0.0
        avg_export = sum(export_prices) / len(export_prices) if export_prices else 0.0

        return PriceBundle(
            import_prices=import_prices,
            export_prices=export_prices,
            avg_import_price=avg_import,
            avg_export_price=avg_export,
            cheapest_import_price=min(import_prices) if import_prices else 0.0,
            highest_export_price=max(export_prices) if export_prices else 0.0,
            source_details={"import": import_meta, "export": export_meta},
        )

    def _read_prices(self, entity_id: str | None) -> tuple[list[float], dict[str, str]]:
        if not entity_id:
            return [], {"source": "none", "status": "missing"}

        state = self._hass.states.get(entity_id)
        if state is None:
            return [], {"source": entity_id, "status": "missing"}

        attrs = state.attributes
        raw_today = attrs.get("raw_today") or attrs.get("today") or attrs.get("prices") or attrs.get("rates") or []
        raw_tomorrow = attrs.get("raw_tomorrow") or attrs.get("tomorrow") or []
        extracted = self._extract_values(raw_today) + self._extract_values(raw_tomorrow)
        if extracted:
            return extracted[:24], {"source": entity_id, "status": "hourly"}

        unit = str(attrs.get("unit_of_measurement", "")).lower()
        device_class = str(attrs.get("device_class", "")).lower()
        if device_class == "monetary" and "/kwh" not in unit and "/mwh" not in unit:
            return [], {"source": entity_id, "status": "invalid_unit"}

        try:
            return [float(state.state)], {"source": entity_id, "status": "single_value"}
        except ValueError:
            return [], {"source": entity_id, "status": "invalid"}

    def _extract_values(self, items) -> list[float]:
        values: list[float] = []
        for item in items:
            if isinstance(item, dict):
                value = item.get("value")
            else:
                value = item
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue
        return values
