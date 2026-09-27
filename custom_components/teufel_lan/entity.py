from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def get_device_info(entry: ConfigEntry) -> DeviceInfo:
    host = entry.data.get(CONF_HOST, "unknown")
    name = entry.data.get(CONF_NAME, "Teufel Speaker")
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Teufel",
        model="LAN Speaker",
        name=name,
        configuration_url=f"http://{host}",
    )