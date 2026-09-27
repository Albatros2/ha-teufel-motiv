from __future__ import annotations

from typing import Awaitable, Callable

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TeufelRuntimeData
from .entity import get_device_info


ActionCallable = Callable[[], Awaitable[None]]


class TeufelActionButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: TeufelRuntimeData,
        key: str,
        name: str,
        icon: str,
        action: ActionCallable,
    ) -> None:
        super().__init__(runtime.coordinator)
        self._action = action
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = get_device_info(entry)

    async def async_press(self) -> None:
        await self._action()
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: TeufelRuntimeData = entry.runtime_data

    async def press_stop() -> None:
        await runtime.api.async_stop()

    async def press_preset_1() -> None:
        await runtime.api.async_activate_preset(0)

    async def press_preset_2() -> None:
        await runtime.api.async_activate_preset(1)

    async def press_preset_3() -> None:
        await runtime.api.async_activate_preset(2)

    async_add_entities(
        [
            TeufelActionButton(entry, runtime, "stop", "Stop", "mdi:stop", press_stop),
            TeufelActionButton(entry, runtime, "preset_1", "Preset 1", "mdi:numeric-1-circle", press_preset_1),
            TeufelActionButton(entry, runtime, "preset_2", "Preset 2", "mdi:numeric-2-circle", press_preset_2),
            TeufelActionButton(entry, runtime, "preset_3", "Preset 3", "mdi:numeric-3-circle", press_preset_3),
        ]
    )
