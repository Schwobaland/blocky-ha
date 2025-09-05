"""The Blocky DNS integration."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import timedelta
from typing import Any

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
    CONF_PROMETHEUS_ENABLED,
    CONF_PROMETHEUS_PORT,
    DEFAULT_PROMETHEUS_ENABLED,
    DEFAULT_PROMETHEUS_PORT,
    ATTR_ENABLED,
    ATTR_AUTO_ENABLE_IN_SEC,
    ATTR_DISABLED_GROUPS,
    PROMETHEUS_METRICS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Blocky from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    timeout = entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    
    # Prometheus settings (check both options and data for backwards compatibility)
    prometheus_enabled = entry.options.get(
        CONF_PROMETHEUS_ENABLED,
        entry.data.get(CONF_PROMETHEUS_ENABLED, DEFAULT_PROMETHEUS_ENABLED)
    )
    prometheus_port = entry.options.get(
        CONF_PROMETHEUS_PORT,
        entry.data.get(CONF_PROMETHEUS_PORT, DEFAULT_PROMETHEUS_PORT)
    )

    coordinator = BlockyDataUpdateCoordinator(
        hass, host, port, timedelta(seconds=scan_interval), timeout, 
        prometheus_enabled, prometheus_port
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
        prometheus_enabled: bool = False,
        prometheus_port: int = DEFAULT_PROMETHEUS_PORT,
    ) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.prometheus_enabled = prometheus_enabled
        self.prometheus_port = prometheus_port
        self.session = async_get_clientsession(hass)
        self.base_url = f"http://{host}:{port}/api"
        self.prometheus_url = f"http://{host}:{prometheus_port}/metrics"

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
                # Always fetch basic API data
                data = await self._fetch_status()
                _LOGGER.debug(f"Received API data from Blocky: {data}")
                
                # Ensure disabledGroups is always a list
                if ATTR_DISABLED_GROUPS not in data:
                    data[ATTR_DISABLED_GROUPS] = []
                elif data[ATTR_DISABLED_GROUPS] is None:
                    data[ATTR_DISABLED_GROUPS] = []
                elif not isinstance(data[ATTR_DISABLED_GROUPS], list):
                    data[ATTR_DISABLED_GROUPS] = []
                
                # Fetch Prometheus metrics if enabled
                if self.prometheus_enabled:
                    try:
                        prometheus_data = await self._fetch_prometheus_metrics()
                        data["prometheus"] = prometheus_data
                        _LOGGER.debug(f"Received Prometheus data: {len(prometheus_data)} metrics")
                    except Exception as e:
                        _LOGGER.warning(f"Failed to fetch Prometheus metrics: {e}")
                        data["prometheus"] = {}
                else:
                    data["prometheus"] = {}
                
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

    async def _fetch_prometheus_metrics(self) -> dict[str, Any]:
        """Fetch and parse Prometheus metrics."""
        async with self.session.get(self.prometheus_url) as response:
            if response.status != 200:
                raise UpdateFailed(f"Prometheus metrics returned {response.status}")
            
            metrics_text = await response.text()
            return self._parse_prometheus_metrics(metrics_text)

    def _parse_prometheus_metrics(self, metrics_text: str) -> dict[str, Any]:
        """Parse Prometheus metrics text format."""
        metrics = {}
        
        for line in metrics_text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse metric line: metric_name{labels} value timestamp
            match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)?(\{[^}]*\})?\s+([^\s]+)', line)
            if not match:
                continue
                
            metric_name = match.group(1)
            labels_str = match.group(2) or ""
            value_str = match.group(3)
            
            # Only parse metrics we're interested in
            if metric_name not in PROMETHEUS_METRICS.values():
                continue
            
            try:
                # Try to convert to number
                if '.' in value_str:
                    value = float(value_str)
                else:
                    value = int(value_str)
            except ValueError:
                value = value_str
            
            # Parse labels if present
            labels = {}
            if labels_str:
                # Simple label parsing - remove braces and split by comma
                labels_content = labels_str[1:-1]  # Remove { and }
                for label_pair in labels_content.split(','):
                    if '=' in label_pair:
                        key, val = label_pair.split('=', 1)
                        key = key.strip()
                        val = val.strip().strip('"')
                        labels[key] = val
            
            # Store metric with its labels
            if metric_name not in metrics:
                metrics[metric_name] = []
            
            metrics[metric_name].append({
                'value': value,
                'labels': labels
            })
        
        return metrics

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