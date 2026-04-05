from __future__ import annotations

from .base import InverterAdapter


class SolarmanAdapter(InverterAdapter):
    @property
    def name(self) -> str:
        return "solarman"
