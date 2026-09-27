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


def _extract_i32(payload: dict[str, Any] | None) -> int | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("value")
    if isinstance(value, dict):
        i32_value = value.get("i32_")
        if isinstance(i32_value, int):
            return i32_value
    return None


def _extract_string(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("value")
    if isinstance(value, dict):
        string_value = value.get("string_")
        if isinstance(string_value, str):
            return string_value
    return None


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


class TeufelDeviceNameSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Device Name"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:speaker"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_device_name"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> str | None:
        return _extract_string(self.coordinator.data.get("device_name"))


class TeufelBatterySocSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Battery State of Charge"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = "%"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_battery_soc"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> float | None:
        value = _extract_i32(self.coordinator.data.get("battery_soc"))
        return float(value) if value is not None else None


class TeufelBatteryCycleCountSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Battery Cycle Count"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:battery-sync"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_battery_cycle_count"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> float | None:
        value = _extract_i32(self.coordinator.data.get("battery_cycle_count"))
        return float(value) if value is not None else None


class TeufelBatteryStatusSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Battery Status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:battery-heart-variant"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_battery_status"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> str | None:
        return _extract_string(self.coordinator.data.get("battery_stat"))


class TeufelPowerTargetSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Power Target"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:power-settings"

    def __init__(self, entry: ConfigEntry, runtime: TeufelRuntimeData) -> None:
        super().__init__(runtime.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_power_target"
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> str | None:
        power_target = (
            self.coordinator.data.get("power_target", {})
            .get("value", {})
            .get("powerTarget", {})
            .get("target")
        )
        return power_target if isinstance(power_target, str) else None


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
            TeufelDeviceNameSensor(entry, runtime),
            TeufelBatterySocSensor(entry, runtime),
            TeufelBatteryCycleCountSensor(entry, runtime),
            TeufelBatteryStatusSensor(entry, runtime),
            TeufelPowerTargetSensor(entry, runtime),
        ]
    )
