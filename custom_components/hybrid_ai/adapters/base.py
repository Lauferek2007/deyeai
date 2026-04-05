from __future__ import annotations

from abc import ABC, abstractmethod

from homeassistant.core import HomeAssistant

from ..models import ControlAction


class InverterAdapter(ABC):
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def supports_write(self) -> bool:
        return False

    async def async_execute(self, actions: list[ControlAction], dry_run: bool) -> list[dict]:
        return [
            {
                "adapter": self.name,
                "action": action.action,
                "value": action.value,
                "reason": action.reason,
                "executed": False,
                "dry_run": dry_run or not self.supports_write,
            }
            for action in actions
        ]
