from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo

from .const import CONF_MAC, CONF_MANUFACTURER, CONF_MODEL, CONF_SERIAL, CONF_UUID, DOMAIN


def get_device_info(entry: ConfigEntry) -> DeviceInfo:
    host = entry.data.get(CONF_HOST, "unknown")
    name = entry.data.get(CONF_NAME, "Teufel Speaker")
    serial = entry.data.get(CONF_SERIAL)
    uuid = entry.data.get(CONF_UUID)
    mac = entry.data.get(CONF_MAC)
    manufacturer = entry.data.get(CONF_MANUFACTURER, "Teufel")
    model = entry.data.get(CONF_MODEL, "MOTIV HOME")

    identifiers: set[tuple[str, str]] = {(DOMAIN, entry.entry_id)}
    if isinstance(serial, str) and serial:
        identifiers.add((DOMAIN, f"serial:{serial}"))
    if isinstance(uuid, str) and uuid:
        identifiers.add((DOMAIN, f"uuid:{uuid}"))

    connections = set()
    if isinstance(mac, str) and mac:
        connections.add((CONNECTION_NETWORK_MAC, mac.upper()))

    return DeviceInfo(
        identifiers=identifiers,
        connections=connections,
        manufacturer=manufacturer,
        model=model,
        name=name,
        configuration_url=f"http://{host}",
    )