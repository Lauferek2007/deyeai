from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, SERVICE_DISCOVER_ENTITIES, SERVICE_RUN_OPTIMIZATION
from .coordinator import HybridAiCoordinator
from .discovery import discover_inverter_entities, discovery_as_dict

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    coordinator = HybridAiCoordinator(hass, entry)
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    if not hass.services.has_service(DOMAIN, SERVICE_RUN_OPTIMIZATION):

        async def handle_run_optimization(call: ServiceCall) -> None:
            for stored in hass.data.get(DOMAIN, {}).values():
                await stored.async_request_refresh()

        hass.services.async_register(DOMAIN, SERVICE_RUN_OPTIMIZATION, handle_run_optimization)

    if not hass.services.has_service(DOMAIN, SERVICE_DISCOVER_ENTITIES):

        async def handle_discover_entities(call: ServiceCall) -> None:
            result = discovery_as_dict(discover_inverter_entities(hass))
            hass.states.async_set(f"{DOMAIN}.last_discovery", result.get("adapter", "generic"), result)

        hass.services.async_register(DOMAIN, SERVICE_DISCOVER_ENTITIES, handle_discover_entities)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: HybridAiCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None:
        await coordinator.async_shutdown()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    if not hass.data.get(DOMAIN):
        if hass.services.has_service(DOMAIN, SERVICE_RUN_OPTIMIZATION):
            hass.services.async_remove(DOMAIN, SERVICE_RUN_OPTIMIZATION)
        if hass.services.has_service(DOMAIN, SERVICE_DISCOVER_ENTITIES):
            hass.services.async_remove(DOMAIN, SERVICE_DISCOVER_ENTITIES)

    return unload_ok
