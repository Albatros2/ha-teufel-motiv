from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .api import TeufelApiClient
from .const import CONF_PORT, DEFAULT_PORT
from .coordinator import TeufelDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.NUMBER]


@dataclass
class TeufelRuntimeData:
    api: TeufelApiClient
    coordinator: TeufelDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    api = TeufelApiClient(hass, host=host, port=port)
    coordinator = TeufelDataUpdateCoordinator(hass, api=api, entry=entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = TeufelRuntimeData(api=api, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        entry.runtime_data = None
    return unloaded
