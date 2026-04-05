from __future__ import annotations

from .base import InverterAdapter


class GoodWeAdapter(InverterAdapter):
    @property
    def name(self) -> str:
        return "goodwe"
