from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TeufelApiClient, TeufelApiError
from .const import DOMAIN, UPDATE_INTERVAL


class TeufelDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: TeufelApiClient, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            media = await self.api.async_get_data("teufel:mediaPlayerData", roles="@all", typ="structure")
            volume = await self.api.async_get_data("player:volume", roles="@all", typ="structure")
            mute = await self.api.async_get_data("settings:/mediaPlayer/mute", roles="@all", typ="structure")
            bass = await self.api.async_get_data("settings:/dspc/dspcBass", roles="@all", typ="structure")
            treble = await self.api.async_get_data("settings:/dspc/dspcTreble", roles="@all", typ="structure")
            play_time = await self.api.async_get_data("player:player/data/playTime", roles="@all", typ="structure")

            return {
                "media": media,
                "volume": volume,
                "mute": mute,
                "bass": bass,
                "treble": treble,
                "play_time": play_time,
            }
        except TeufelApiError as err:
            raise UpdateFailed(str(err)) from err
