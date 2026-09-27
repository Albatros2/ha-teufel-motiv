from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
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


class TeufelBatteryAcPlugBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Battery AC Plug"
    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_battery_ac_plug"
        self._attr_device_info = get_device_info(entry)

    @property
    def is_on(self) -> bool | None:
        return _extract_bool(self.coordinator.data.get("battery_ac_plug"))


class TeufelBatteryDefectiveBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Battery Defective"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_battery_defective"
        self._attr_device_info = get_device_info(entry)

    @property
    def is_on(self) -> bool | None:
        return _extract_bool(self.coordinator.data.get("battery_defective"))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: TeufelRuntimeData = entry.runtime_data
    async_add_entities(
        [
            TeufelBatteryAcPlugBinarySensor(entry, runtime),
            TeufelBatteryDefectiveBinarySensor(entry, runtime),
        ]
    )
