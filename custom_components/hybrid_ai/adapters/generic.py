from __future__ import annotations

from .base import InverterAdapter


class GenericEntityAdapter(InverterAdapter):
    @property
    def name(self) -> str:
        return "generic"
