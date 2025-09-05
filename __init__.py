"""The Blocky DNS integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_TIMEOUT,
    ATTR_DISABLED_GROUPS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Blocky from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    timeout = entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

    coordinator = BlockyDataUpdateCoordinator(
        hass, host, port, timedelta(seconds=scan_interval), timeout
    )

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady(f"Unable to connect to Blocky at {host}:{port}")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class BlockyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Blocky data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        update_interval: timedelta,
        timeout: int,
    ) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.session = async_get_clientsession(hass)
        self.base_url = f"http://{host}:{port}/api"

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        try:
            async with async_timeout.timeout(self.timeout):
                data = await self._fetch_status()
                _LOGGER.debug(f"Received data from Blocky API: {data}")
                
                # Ensure disabledGroups is always a list
                if ATTR_DISABLED_GROUPS not in data:
                    data[ATTR_DISABLED_GROUPS] = []
                elif data[ATTR_DISABLED_GROUPS] is None:
                    data[ATTR_DISABLED_GROUPS] = []
                elif not isinstance(data[ATTR_DISABLED_GROUPS], list):
                    data[ATTR_DISABLED_GROUPS] = []
                
                return data
        except asyncio.TimeoutError as exception:
            raise UpdateFailed(f"Timeout communicating with API: {exception}")
        except aiohttp.ClientError as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}")
        except Exception as exception:
            _LOGGER.exception("Unexpected error fetching data")
            raise UpdateFailed(f"Unexpected error: {exception}")

    async def _fetch_status(self) -> dict:
        """Fetch status from Blocky API."""
        url = f"{self.base_url}/blocking/status"
        async with self.session.get(url) as response:
            if response.status != 200:
                raise UpdateFailed(f"API returned {response.status}")
            return await response.json()

    async def enable_blocking(self) -> bool:
        """Enable blocking."""
        url = f"{self.base_url}/blocking/enable"
        try:
            async with async_timeout.timeout(self.timeout):
                async with self.session.get(url) as response:
                    success = response.status == 200
                    if success:
                        # Wait a moment before refreshing to allow Blocky to update
                        await asyncio.sleep(0.5)
                        await self.async_request_refresh()
                    return success
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return False

    async def disable_blocking(self, duration: str = None, groups: str = None) -> bool:
        """Disable blocking."""
        url = f"{self.base_url}/blocking/disable"
        params = {}
        if duration:
            params["duration"] = duration
        if groups:
            params["groups"] = groups

        try:
            async with async_timeout.timeout(self.timeout):
                async with self.session.get(url, params=params) as response:
                    success = response.status == 200
                    if success:
                        # Wait a moment before refreshing to allow Blocky to update
                        await asyncio.sleep(0.5)
                        await self.async_request_refresh()
                    return success
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return False

    async def refresh_lists(self) -> bool:
        """Refresh blocking lists."""
        url = f"{self.base_url}/lists/refresh"
        try:
            async with async_timeout.timeout(self.timeout * 3):  # Lists refresh can take longer
                async with self.session.post(url) as response:
                    return response.status == 200
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return False

    async def flush_cache(self) -> bool:
        """Flush DNS cache."""
        url = f"{self.base_url}/cache/flush"
        try:
            async with async_timeout.timeout(self.timeout):
                async with self.session.post(url) as response:
                    return response.status == 200
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return False

    async def query_dns(self, query: str, query_type: str) -> dict:
        """Perform DNS query."""
        url = f"{self.base_url}/query"
        data = {"query": query, "type": query_type}
        try:
            async with async_timeout.timeout(self.timeout):
                async with self.session.post(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return None