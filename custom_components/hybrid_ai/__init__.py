from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, SERVICE_RUN_OPTIMIZATION
from .coordinator import HybridAiCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    coordinator = HybridAiCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    if not hass.services.has_service(DOMAIN, SERVICE_RUN_OPTIMIZATION):

        async def handle_run_optimization(call: ServiceCall) -> None:
            for stored in hass.data.get(DOMAIN, {}).values():
                await stored.async_request_refresh()

        hass.services.async_register(DOMAIN, SERVICE_RUN_OPTIMIZATION, handle_run_optimization)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    if not hass.data.get(DOMAIN) and hass.services.has_service(DOMAIN, SERVICE_RUN_OPTIMIZATION):
        hass.services.async_remove(DOMAIN, SERVICE_RUN_OPTIMIZATION)

    return unload_ok
