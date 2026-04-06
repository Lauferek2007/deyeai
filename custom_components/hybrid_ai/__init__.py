from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    CONF_AUTO_DISCOVERY,
    DATA_COORDINATORS,
    DOMAIN,
    SERVICE_DISCOVER_ENTITIES,
    SERVICE_RUN_OPTIMIZATION,
)
from .coordinator import HybridAiCoordinator
from .discovery import discover_inverter_entities, discovery_as_dict

PLATFORMS = ["sensor"]
FRONTEND_URL = f"/{DOMAIN}-static"
LEGACY_FRONTEND_URL = f"/api/{DOMAIN}/static"
FRONTEND_PATH = Path(__file__).parent / "frontend"


async def async_setup(hass: HomeAssistant, config) -> bool:
    await _async_register_frontend(hass)
    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    domain_data = hass.data.setdefault(
        DOMAIN,
        {DATA_COORDINATORS: {}, "frontend_registered": False},
    )
    if domain_data.get("frontend_registered"):
        return

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(FRONTEND_URL, str(FRONTEND_PATH), False),
            StaticPathConfig(LEGACY_FRONTEND_URL, str(FRONTEND_PATH), False),
        ]
    )
    domain_data["frontend_registered"] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(
        DOMAIN,
        {DATA_COORDINATORS: {}, "frontend_registered": False},
    )
    await _async_register_frontend(hass)
    coordinator = HybridAiCoordinator(hass, entry)
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    if not hass.services.has_service(DOMAIN, SERVICE_RUN_OPTIMIZATION):

        async def handle_run_optimization(call: ServiceCall) -> None:
            for stored in hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {}).values():
                await stored.async_request_refresh()

        hass.services.async_register(DOMAIN, SERVICE_RUN_OPTIMIZATION, handle_run_optimization)

    if not hass.services.has_service(DOMAIN, SERVICE_DISCOVER_ENTITIES):

        async def handle_discover_entities(call: ServiceCall) -> None:
            result = discovery_as_dict(discover_inverter_entities(hass))
            hass.states.async_set(f"{DOMAIN}.last_discovery", result.get("adapter", "generic"), result)
            reload_entries = [
                stored.entry.entry_id
                for stored in list(hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {}).values())
                if stored.config.get(CONF_AUTO_DISCOVERY, True)
            ]
            for entry_id in reload_entries:
                await hass.config_entries.async_reload(entry_id)

        hass.services.async_register(DOMAIN, SERVICE_DISCOVER_ENTITIES, handle_discover_entities)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: HybridAiCoordinator | None = hass.data.get(DOMAIN, {}).get(
        DATA_COORDINATORS, {}
    ).get(entry.entry_id)
    if coordinator is not None:
        await coordinator.async_shutdown()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN][DATA_COORDINATORS].pop(entry.entry_id, None)

    if not hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS):
        if hass.services.has_service(DOMAIN, SERVICE_RUN_OPTIMIZATION):
            hass.services.async_remove(DOMAIN, SERVICE_RUN_OPTIMIZATION)
        if hass.services.has_service(DOMAIN, SERVICE_DISCOVER_ENTITIES):
            hass.services.async_remove(DOMAIN, SERVICE_DISCOVER_ENTITIES)

    return unload_ok
