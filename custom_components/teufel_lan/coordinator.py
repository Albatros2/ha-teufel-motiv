from __future__ import annotations

import asyncio
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
        self._event_task: asyncio.Task[None] | None = None
        self._event_queue_id: str | None = None
        self._event_path_map: dict[str, str] = {
            "player:volume": "volume",
            "settings:/mediaPlayer/mute": "mute",
            "settings:/dspc/dynamoreEnabled": "dynamore",
            "settings:/dspc/dspcBass": "bass",
            "settings:/dspc/dspcTreble": "treble",
            "settings:/system/maxIdleTime": "max_idle_time",
            "player:player/data/playTime": "play_time",
            "teufel:mediaPlayerData": "media",
            "network:info": "network_info",
        }

    async def async_start_event_listener(self) -> None:
        if self._event_task is None or self._event_task.done():
            self._event_task = asyncio.create_task(self._event_loop())

    async def async_stop_event_listener(self) -> None:
        if self._event_task is not None:
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass
            self._event_task = None

    def _apply_event(self, data: dict[str, Any], event: dict[str, Any]) -> bool:
        path = event.get("path")
        key = self._event_path_map.get(path) if isinstance(path, str) else None
        if key is None:
            return False

        item_value = event.get("itemValue")
        if not isinstance(item_value, dict):
            return False

        target = data.get(key)
        if isinstance(target, dict):
            target["value"] = item_value
        else:
            data[key] = {"value": item_value}
        return True

    async def _event_loop(self) -> None:
        while True:
            try:
                if self._event_queue_id is None:
                    self._event_queue_id = await self.api.async_create_event_queue()
                    if self._event_queue_id is None:
                        await asyncio.sleep(10)
                        continue

                events = await self.api.async_poll_event_queue(self._event_queue_id, timeout=60)
                if not events:
                    continue

                current_data = dict(self.data or {})
                changed = False
                for event in events:
                    changed = self._apply_event(current_data, event) or changed

                if changed:
                    self.async_set_updated_data(current_data)
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                self.logger.debug("Event loop fallback to polling due to error: %s", err)
                self._event_queue_id = None
                await asyncio.sleep(10)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            media = await self.api.async_get_data("teufel:mediaPlayerData", roles="@all", typ="structure")
            volume = await self.api.async_get_data("player:volume", roles="@all", typ="structure")
            mute = await self.api.async_get_data("settings:/mediaPlayer/mute", roles="@all", typ="structure")
            dynamore = await self.api.async_get_data("settings:/dspc/dynamoreEnabled", roles="@all", typ="structure")
            bass = await self.api.async_get_data("settings:/dspc/dspcBass", roles="@all", typ="structure")
            treble = await self.api.async_get_data("settings:/dspc/dspcTreble", roles="@all", typ="structure")
            max_idle_time = await self.api.async_get_data("settings:/system/maxIdleTime", roles="@all", typ="structure")
            network_info = await self.api.async_get_data("network:info", roles="@all", typ="structure")
            play_time = await self.api.async_get_data("player:player/data/playTime", roles="@all", typ="structure")

            return {
                "media": media,
                "volume": volume,
                "mute": mute,
                "dynamore": dynamore,
                "bass": bass,
                "treble": treble,
                "max_idle_time": max_idle_time,
                "network_info": network_info,
                "play_time": play_time,
            }
        except TeufelApiError as err:
            raise UpdateFailed(str(err)) from err
