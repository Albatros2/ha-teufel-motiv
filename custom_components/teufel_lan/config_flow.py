from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from zeroconf import ServiceStateChange
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo

from homeassistant.components import zeroconf
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers import selector

from .api import TeufelApiClient, TeufelApiError
from .const import (
    CONF_DISCOVERED_DEVICE,
    CONF_MAC,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_PORT,
    CONF_SERIAL,
    CONF_UUID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)


def _decode_properties(properties: Any) -> dict[str, str]:
    if not isinstance(properties, dict):
        return {}

    decoded: dict[str, str] = {}
    for raw_key, raw_value in properties.items():
        if isinstance(raw_key, bytes):
            key = raw_key.decode("utf-8", errors="ignore")
        else:
            key = str(raw_key)

        if isinstance(raw_value, bytes):
            value = raw_value.decode("utf-8", errors="ignore")
        else:
            value = str(raw_value)

        if key:
            decoded[key] = value
    return decoded


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        discovered_devices = await self._async_discover_motiv_devices()
        discovered_by_id = {device["id"]: device for device in discovered_devices}

        if user_input is not None:
            selected_device_id = user_input.get(CONF_DISCOVERED_DEVICE)
            selected_device = discovered_by_id.get(selected_device_id) if selected_device_id else None

            host = (
                selected_device["host"]
                if selected_device
                else str(user_input.get(CONF_HOST, "")).strip()
            )
            port = user_input[CONF_PORT]
            name = str(user_input.get(CONF_NAME, "")).strip()

            if not host:
                errors["base"] = "no_device_selected"
            elif not name:
                errors["base"] = "name_required"
            else:
                api = TeufelApiClient(self.hass, host=host, port=port)
                try:
                    await api.async_get_data("teufel:mediaPlayerData", roles="@all", typ="structure")
                except TeufelApiError:
                    errors["base"] = "cannot_connect"
                else:
                    unique_id = host
                    serial = None
                    uuid = None
                    mac = None
                    model = None
                    manufacturer = None

                    if selected_device is not None:
                        unique_id = selected_device.get("unique_id", host)
                        serial = selected_device.get("serial")
                        uuid = selected_device.get("uuid")
                        mac = selected_device.get("mac")
                        model = selected_device.get("model")
                        manufacturer = selected_device.get("manufacturer")

                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_HOST: host,
                            CONF_PORT: port,
                            CONF_NAME: name,
                            CONF_SERIAL: serial,
                            CONF_UUID: uuid,
                            CONF_MAC: mac,
                            CONF_MODEL: model,
                            CONF_MANUFACTURER: manufacturer,
                        },
                    )

        schema = self._build_user_schema(discovered_devices, user_input)
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    def _build_user_schema(
        self,
        discovered_devices: list[dict[str, str | None]],
        user_input: dict[str, Any] | None,
    ) -> vol.Schema:
        discovered_options = [
            selector.SelectOptionDict(
                value=device["id"],
                label=f"{device['name']} ({device['host']})",
            )
            for device in discovered_devices
        ]

        default_name = DEFAULT_NAME
        if discovered_devices:
            default_name = str(discovered_devices[0].get("name") or DEFAULT_NAME)
        if user_input and user_input.get(CONF_NAME):
            default_name = str(user_input[CONF_NAME])

        fields: dict[Any, Any] = {}

        if discovered_options:
            fields[vol.Optional(CONF_DISCOVERED_DEVICE)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=discovered_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    sort=True,
                )
            )

        default_host = ""
        if user_input and user_input.get(CONF_HOST):
            default_host = str(user_input[CONF_HOST])

        fields[vol.Optional(CONF_HOST, default=default_host)] = str
        fields[vol.Optional(CONF_PORT, default=DEFAULT_PORT)] = int
        fields[vol.Optional(CONF_NAME, default=default_name)] = str
        return vol.Schema(fields)

    async def _async_discover_motiv_devices(self) -> list[dict[str, str | None]]:
        service_types = [
            "_teufelstreaming._tcp.local.",
            "_sues800device._tcp.local.",
        ]
        devices: dict[str, dict[str, str | None]] = {}

        try:
            async_zc = await zeroconf.async_get_async_instance(self.hass)
        except Exception:
            return []

        pending_tasks: set[asyncio.Task] = set()

        async def _resolve(service_type: str, service_name: str) -> None:
            info = AsyncServiceInfo(service_type, service_name)
            if not await info.async_request(async_zc.zeroconf, 2000):
                return

            addresses = info.parsed_scoped_addresses()
            if not addresses:
                return

            host = addresses[0].split("%", 1)[0]
            props = _decode_properties(info.properties)
            device_name = props.get("name") or service_name.rstrip(".") or DEFAULT_NAME
            serial = props.get("serial")
            uuid = props.get("uuid")
            mac = props.get("macAddress")
            model = props.get("modelName") or props.get("productName") or props.get("modelId")
            manufacturer = props.get("manufacturer") or props.get("vendor") or "Teufel"
            unique_id = uuid or serial or mac or host

            devices[unique_id] = {
                "id": unique_id,
                "unique_id": unique_id,
                "host": host,
                "name": device_name,
                "serial": serial,
                "uuid": uuid,
                "mac": mac,
                "model": model,
                "manufacturer": manufacturer,
            }

        def _service_handler(_zc, service_type: str, service_name: str, state_change: ServiceStateChange):
            if state_change not in (ServiceStateChange.Added, ServiceStateChange.Updated):
                return

            task = self.hass.async_create_task(_resolve(service_type, service_name))
            pending_tasks.add(task)
            task.add_done_callback(lambda done_task: pending_tasks.discard(done_task))

        browsers = [
            AsyncServiceBrowser(async_zc.zeroconf, service_type, handlers=[_service_handler])
            for service_type in service_types
        ]

        await asyncio.sleep(1.5)

        for browser in browsers:
            await browser.async_cancel()

        if pending_tasks:
            await asyncio.gather(*pending_tasks, return_exceptions=True)

        return sorted(
            devices.values(),
            key=lambda item: f"{item.get('name') or ''}|{item.get('host') or ''}".lower(),
        )

    async def async_step_zeroconf(self, discovery_info: Any):
        # Zeroconf payload shape varies between HA versions.
        host = getattr(discovery_info, "host", None)
        name = getattr(discovery_info, "name", None)
        properties = getattr(discovery_info, "properties", None)
        if host is None and isinstance(discovery_info, dict):
            host = discovery_info.get("host")
            name = discovery_info.get("name")
            properties = discovery_info.get("properties")
        if not host:
            return self.async_abort(reason="cannot_connect")

        props = _decode_properties(properties)
        discovered_name = props.get("name") or (name or "").rstrip(".") or DEFAULT_NAME
        discovered_serial = props.get("serial")
        discovered_uuid = props.get("uuid")
        discovered_mac = props.get("macAddress")
        discovered_model = props.get("modelName") or props.get("productName") or props.get("modelId")
        discovered_manufacturer = props.get("manufacturer") or props.get("vendor") or "Teufel"

        unique_id = discovered_uuid or discovered_serial or discovered_mac or host

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self.context["title_placeholders"] = {
            "name": discovered_name
        }
        self._discovered_host = host
        self._discovered_name = discovered_name
        self._discovered_serial = discovered_serial
        self._discovered_uuid = discovered_uuid
        self._discovered_mac = discovered_mac
        self._discovered_model = discovered_model
        self._discovered_manufacturer = discovered_manufacturer

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            name = user_input.get(CONF_NAME, self._discovered_name)

            api = TeufelApiClient(self.hass, host=self._discovered_host, port=port)
            try:
                await api.async_get_data("teufel:mediaPlayerData", roles="@all", typ="structure")
            except TeufelApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: self._discovered_host,
                        CONF_PORT: port,
                        CONF_NAME: name,
                        CONF_SERIAL: self._discovered_serial,
                        CONF_UUID: self._discovered_uuid,
                        CONF_MAC: self._discovered_mac,
                        CONF_MODEL: self._discovered_model,
                        CONF_MANUFACTURER: self._discovered_manufacturer,
                    },
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_NAME, default=self._discovered_name): str,
            }
        )
        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"host": self._discovered_host},
        )
