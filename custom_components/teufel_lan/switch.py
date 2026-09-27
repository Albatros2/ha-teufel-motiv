from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TeufelRuntimeData
from .entity import get_device_info


def _extract_bool(payload: dict[str, Any] | None) -> bool | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("value")
    if isinstance(value, dict):
        bool_value = value.get("bool_")
        if isinstance(bool_value, bool):
            return bool_value
    return None


class TeufelMuteSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Mute"
    _attr_icon = "mdi:volume-mute"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._api = runtime.api
        self._attr_unique_id = f"{entry.entry_id}_mute"
        self._attr_device_info = get_device_info(entry)

    @property
    def is_on(self) -> bool | None:
        return _extract_bool(self.coordinator.data.get("mute"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._api.async_set_mute(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._api.async_set_mute(False)
        await self.coordinator.async_request_refresh()


class TeufelDynamoreSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Dynamore"
    _attr_icon = "mdi:speaker-wireless"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._api = runtime.api
        self._attr_unique_id = f"{entry.entry_id}_dynamore"
        self._attr_device_info = get_device_info(entry)

    @property
    def is_on(self) -> bool | None:
        return _extract_bool(self.coordinator.data.get("dynamore"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._api.async_set_dynamore(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._api.async_set_dynamore(False)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: TeufelRuntimeData = entry.runtime_data
    async_add_entities(
        [
            TeufelMuteSwitch(entry, runtime),
            TeufelDynamoreSwitch(entry, runtime),
        ]
    )
