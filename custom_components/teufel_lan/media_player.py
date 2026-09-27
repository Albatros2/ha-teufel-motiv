from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TeufelRuntimeData


def _extract_i32(payload: dict[str, Any] | None) -> int | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("value")
    if isinstance(value, dict):
        if value.get("type") == "i32_" and "i32_" in value:
            return int(value["i32_"])
    return None


def _extract_bool(payload: dict[str, Any] | None) -> bool | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("value")
    if isinstance(value, dict):
        bool_value = value.get("bool_")
        if isinstance(bool_value, bool):
            return bool_value
    return None


class TeufelMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._entry = entry
        self._api = runtime.api
        self._attr_unique_id = f"{entry.entry_id}_player"
        self._attr_supported_features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.PLAY_MEDIA
        )
        self._source_map: dict[str, str] = {}

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def name(self) -> str:
        return self._entry.data.get(CONF_NAME, "Teufel Speaker")

    @property
    def state(self) -> MediaPlayerState | None:
        media = self.coordinator.data.get("media", {})
        state = media.get("value", {}).get("playLogicData", {}).get("state")
        if state == "playing":
            return MediaPlayerState.PLAYING
        if state == "stopped":
            return MediaPlayerState.IDLE
        if state == "transitioning":
            return MediaPlayerState.BUFFERING
        return MediaPlayerState.IDLE

    @property
    def volume_level(self) -> float | None:
        vol = _extract_i32(self.coordinator.data.get("volume"))
        if vol is None:
            return None
        return max(0.0, min(1.0, vol / 100.0))

    @property
    def media_title(self) -> str | None:
        media = self.coordinator.data.get("media", {})
        return (
            media.get("value", {})
            .get("playLogicData", {})
            .get("trackRoles", {})
            .get("title")
            or media.get("value", {})
            .get("playLogicData", {})
            .get("mediaRoles", {})
            .get("title")
        )

    @property
    def is_volume_muted(self) -> bool | None:
        return _extract_bool(self.coordinator.data.get("mute"))

    @property
    def source_list(self) -> list[str] | None:
        return list(self._source_map.keys()) if self._source_map else None

    @property
    def source(self) -> str | None:
        return self.media_title

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._async_refresh_sources()

    async def _async_refresh_sources(self) -> None:
        rows = await self._api.async_get_rows("playhistory:", 0, 9)
        sources: dict[str, str] = {}
        for row in rows.get("rows", []):
            title = row.get("title")
            guide = row.get("id")
            if isinstance(title, str) and isinstance(guide, str):
                sources[title] = guide
        self._source_map = sources

    async def async_set_volume_level(self, volume: float) -> None:
        target = int(round(max(0.0, min(1.0, volume)) * 100))
        await self._api.async_set_volume(target)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self._api.async_set_mute(mute)
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        await self._api.async_stop()
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        guide_id = self._source_map.get(source)
        if guide_id:
            await self._api.async_tunein_by_guide_id(guide_id)
            await self.coordinator.async_request_refresh()

    async def async_play_media(
        self,
        media_type: str,
        media_id: str,
        **kwargs: Any,
    ) -> None:
        if media_type in ("music", "channel", "radio"):
            await self._api.async_tunein_by_guide_id(media_id)
            await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: TeufelRuntimeData = entry.runtime_data
    async_add_entities([TeufelMediaPlayer(entry, runtime)])
