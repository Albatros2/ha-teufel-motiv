from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TeufelRuntimeData
from .entity import get_device_info


def _extract_i32(payload: dict[str, Any] | None) -> int | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("value")
    if isinstance(value, dict):
        if value.get("type") == "i32_" and "i32_" in value:
            return int(value["i32_"])
    return None


class TeufelEqNumber(CoordinatorEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_step = 1
    _attr_native_min_value = -6
    _attr_native_max_value = 6

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: TeufelRuntimeData,
        key: str,
        name: str,
    ) -> None:
        super().__init__(runtime.coordinator)
        self._api = runtime.api
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> float | None:
        current = _extract_i32(self.coordinator.data.get(self._key))
        return float(current) if current is not None else None

    async def async_set_native_value(self, value: float) -> None:
        ivalue = int(round(value))
        if self._key == "bass":
            await self._api.async_set_bass(ivalue)
        elif self._key == "treble":
            await self._api.async_set_treble(ivalue)
        await self.coordinator.async_request_refresh()


class TeufelMaxIdleTimeNumber(CoordinatorEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Max Idle Time"
    _attr_native_step = 10
    _attr_native_min_value = 0
    _attr_native_max_value = 7200
    _attr_native_unit_of_measurement = "s"
    _attr_icon = "mdi:timer-cog"

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: TeufelRuntimeData,
    ) -> None:
        super().__init__(runtime.coordinator)
        self._api = runtime.api
        self._attr_unique_id = f"{entry.entry_id}_max_idle_time"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> float | None:
        current = _extract_i32(self.coordinator.data.get("max_idle_time"))
        return float(current) if current is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self._api.async_set_max_idle_time(int(round(value)))
        await self.coordinator.async_request_refresh()


class TeufelMaxBatteryIdleTimeNumber(CoordinatorEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Max Battery Idle Time"
    _attr_native_step = 300
    _attr_native_min_value = 0
    _attr_native_max_value = 3600
    _attr_native_unit_of_measurement = "s"
    _attr_icon = "mdi:battery-clock"

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: TeufelRuntimeData,
    ) -> None:
        super().__init__(runtime.coordinator)
        self._api = runtime.api
        self._attr_unique_id = f"{entry.entry_id}_max_battery_idle_time"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> float | None:
        current = _extract_i32(self.coordinator.data.get("max_battery_idle_time"))
        return float(current) if current is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self._api.async_set_max_battery_idle_time(int(round(value)))
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: TeufelRuntimeData = entry.runtime_data
    async_add_entities(
        [
            TeufelEqNumber(entry, runtime, key="bass", name="Bass"),
            TeufelEqNumber(entry, runtime, key="treble", name="Treble"),
            TeufelMaxIdleTimeNumber(entry, runtime),
            TeufelMaxBatteryIdleTimeNumber(entry, runtime),
        ]
    )
