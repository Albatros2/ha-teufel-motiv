from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import TeufelApiClient, TeufelApiError
from .const import CONF_PORT, DEFAULT_NAME, DEFAULT_PORT, DOMAIN


class TeufelLanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            name = user_input[CONF_NAME]

            api = TeufelApiClient(self.hass, host=host, port=port)
            try:
                await api.async_get_data("teufel:mediaPlayerData", roles="@all", typ="structure")
            except TeufelApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_NAME: name,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        host = discovery_info.host
        if not host:
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self.context["title_placeholders"] = {
            "name": discovery_info.name.rstrip(".") or host
        }
        self._discovered_host = host
        self._discovered_name = discovery_info.name.rstrip(".") or DEFAULT_NAME

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
