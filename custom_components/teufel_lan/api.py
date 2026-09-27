from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import urlencode

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class TeufelApiError(HomeAssistantError):
    """Raised when Teufel LAN API communication fails."""


class TeufelApiClient:
    def __init__(self, hass: HomeAssistant, host: str, port: int = 80) -> None:
        self._hass = hass
        self._host = host
        self._port = port
        self._base_url = f"http://{host}:{port}"
        self._session = async_get_clientsession(hass)

    async def _post(self, endpoint: str, payload: dict[str, Any]) -> Any:
        url = f"{self._base_url}{endpoint}"
        try:
            async with asyncio.timeout(10):
                resp = await self._session.post(url, json=payload)
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except Exception as err:
            raise TeufelApiError(f"POST {endpoint} failed: {err}") from err

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{self._base_url}{endpoint}{query}"
        try:
            async with asyncio.timeout(65):
                resp = await self._session.get(url)
                resp.raise_for_status()
                text = await resp.text()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        except Exception as err:
            raise TeufelApiError(f"GET {endpoint} failed: {err}") from err

    async def async_create_event_queue(self) -> str | None:
        # Firmware variants differ in queue creation endpoint behavior.
        candidates: list[tuple[str, str, dict[str, Any] | None]] = [
            ("GET", "/api/event/createQueue", None),
            ("POST", "/api/event/createQueue", {}),
        ]
        for method, endpoint, payload in candidates:
            try:
                if method == "GET":
                    result = await self._get(endpoint)
                else:
                    result = await self._post(endpoint, payload or {})
            except TeufelApiError:
                continue

            if isinstance(result, dict):
                queue_id = result.get("queueId") or result.get("id")
                if isinstance(queue_id, str) and queue_id:
                    return queue_id
            if isinstance(result, str) and result:
                return result
        return None

    async def async_poll_event_queue(self, queue_id: str, timeout: int = 60) -> list[dict[str, Any]]:
        params = {"queueId": queue_id, "timeout": timeout}
        try:
            result = await self._get("/api/event/pollQueue", params=params)
        except TeufelApiError:
            # Some firmware uses lowercase path.
            result = await self._get("/api/event/pollqueue", params=params)

        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        return []

    async def async_get_data(self, path: str, roles: str = "@all", typ: str = "structure") -> Any:
        return await self._post(
            "/api/getData",
            {
                "path": path,
                "roles": roles,
                "type": typ,
            },
        )

    async def async_get_rows(self, path: str, start: int, end: int) -> Any:
        return await self._post(
            "/api/getRows",
            {
                "path": path,
                "roles": "@all",
                "type": "structure",
                "from": start,
                "to": end,
            },
        )

    async def async_set_data(self, path: str, roles: str, value: dict[str, Any]) -> Any:
        return await self._post(
            "/api/setData",
            {
                "path": path,
                "roles": roles,
                "value": value,
            },
        )

    async def async_set_volume(self, volume: int) -> bool:
        result = await self.async_set_data(
            path="player:volume",
            roles="value",
            value={"type": "i32_", "i32_": int(volume)},
        )
        return bool(result is True or str(result).lower() == "true")

    async def async_set_bass(self, value: int) -> Any:
        return await self.async_set_data(
            path="settings:/dspc/dspcBass",
            roles="value",
            value={"type": "i32_", "i32_": int(value)},
        )

    async def async_set_treble(self, value: int) -> Any:
        return await self.async_set_data(
            path="settings:/dspc/dspcTreble",
            roles="value",
            value={"type": "i32_", "i32_": int(value)},
        )

    async def async_set_mute(self, muted: bool) -> Any:
        return await self.async_set_data(
            path="settings:/mediaPlayer/mute",
            roles="value",
            value={"type": "bool_", "bool_": bool(muted)},
        )

    async def async_set_dynamore(self, enabled: bool) -> Any:
        return await self.async_set_data(
            path="settings:/dspc/dynamoreEnabled",
            roles="value",
            value={"type": "bool_", "bool_": bool(enabled)},
        )

    async def async_set_max_idle_time(self, seconds: int) -> Any:
        return await self.async_set_data(
            path="settings:/system/maxIdleTime",
            roles="value",
            value={"type": "i32_", "i32_": int(seconds)},
        )

    async def async_stop(self) -> None:
        await self.async_set_data(
            path="player:player/control",
            roles="activate",
            value={"control": "stop"},
        )

    async def async_activate_preset(self, index: int) -> Any:
        return await self.async_set_data(
            path=f"presets:play/{index}",
            roles="activate",
            value={},
        )

    async def async_tunein_by_guide_id(self, guide_id: str) -> Any:
        return await self.async_set_data(
            path="tunein:tuneInRequestByGuideId",
            roles="activate",
            value={"type": "string_", "string_": guide_id},
        )
