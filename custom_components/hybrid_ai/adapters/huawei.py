from __future__ import annotations

from .base import InverterAdapter


class HuaweiSolarAdapter(InverterAdapter):
    @property
    def name(self) -> str:
        return "huawei"

    @property
    def supports_write(self) -> bool:
        return True
