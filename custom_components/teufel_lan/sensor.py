from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TeufelRuntimeData
from .entity import get_device_info


def _network_info(data: dict[str, Any]) -> dict[str, Any]:
    return (
        data.get("network_info", {})
        .get("value", {})
        .get("networkInfo", {})
    )


def _ipv4_address(data: dict[str, Any]) -> str | None:
    addresses = _network_info(data).get("wireless", {}).get("addresses", [])
    for addr in addresses:
        if addr.get("protocol") == "ipv4" and isinstance(addr.get("ip"), str):
            return addr["ip"]
    return None


class TeufelWifiSsidSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "WiFi SSID"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:wifi"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_wifi_ssid"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> str | None:
        return _network_info(self.coordinator.data).get("wireless", {}).get("ssid")


class TeufelWifiSignalSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "WiFi Signal"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_wifi_signal"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> float | None:
        value = _network_info(self.coordinator.data).get("wireless", {}).get("signalLevel")
        if isinstance(value, (int, float)):
            return float(value)
        return None


class TeufelIpAddressSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "IP Address"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:ip-network"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_ip_address"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> str | None:
        return _ipv4_address(self.coordinator.data)


class TeufelPlayTimeSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Play Time"
    _attr_icon = "mdi:timer-outline"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_play_time"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> float | None:
        value = (
            self.coordinator.data.get("play_time", {})
            .get("value", {})
            .get("i64_")
        )
        if isinstance(value, (int, float)) and value >= 0:
            return float(value) / 1000.0
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: TeufelRuntimeData = entry.runtime_data
    async_add_entities(
        [
            TeufelWifiSsidSensor(entry, runtime),
            TeufelWifiSignalSensor(entry, runtime),
            TeufelIpAddressSensor(entry, runtime),
            TeufelPlayTimeSensor(entry, runtime),
        ]
    )
