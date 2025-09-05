"""Config flow for Blocky integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import HomeAssistantError

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
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_PROMETHEUS_ENABLED, default=DEFAULT_PROMETHEUS_ENABLED): bool,
        vol.Optional(CONF_PROMETHEUS_PORT, default=DEFAULT_PROMETHEUS_PORT): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    
    session = async_get_clientsession(hass)
    url = f"http://{host}:{port}/api/blocking/status"
    
    try:
        async with async_timeout.timeout(10):
            async with session.get(url) as response:
                if response.status != 200:
                    raise CannotConnect("API returned non-200 status")
                result = await response.json()
                if "enabled" not in result:
                    raise InvalidResponse("Invalid response format")
    except aiohttp.ClientError as err:
        raise CannotConnect(f"Cannot connect to Blocky: {err}")
    except Exception as err:
        raise CannotConnect(f"Unexpected error: {err}")

    # Validate Prometheus endpoint if enabled
    if data.get(CONF_PROMETHEUS_ENABLED, False):
        prometheus_port = data.get(CONF_PROMETHEUS_PORT, port)
        prometheus_url = f"http://{host}:{prometheus_port}/metrics"
        
        try:
            async with async_timeout.timeout(10):
                async with session.get(prometheus_url) as response:
                    if response.status != 200:
                        raise CannotConnect("Prometheus metrics endpoint not accessible")
        except aiohttp.ClientError:
            raise CannotConnect("Cannot connect to Prometheus metrics endpoint")

    return {"title": f"Blocky ({host}:{port})"}


class BlockyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blocky."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> BlockyOptionsFlowHandler:
        """Create the options flow."""
        return BlockyOptionsFlowHandler(config_entry)


class BlockyOptionsFlowHandler(config_entries.OptionsFlow):
    """Blocky config flow options handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): int,
                    vol.Optional(
                        CONF_TIMEOUT,
                        default=self.config_entry.options.get(
                            CONF_TIMEOUT, DEFAULT_TIMEOUT
                        ),
                    ): int,
                    vol.Optional(
                        CONF_PROMETHEUS_ENABLED,
                        default=self.config_entry.options.get(
                            CONF_PROMETHEUS_ENABLED, 
                            self.config_entry.data.get(CONF_PROMETHEUS_ENABLED, DEFAULT_PROMETHEUS_ENABLED)
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_PROMETHEUS_PORT,
                        default=self.config_entry.options.get(
                            CONF_PROMETHEUS_PORT,
                            self.config_entry.data.get(CONF_PROMETHEUS_PORT, DEFAULT_PROMETHEUS_PORT)
                        ),
                    ): int,
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidResponse(HomeAssistantError):
    """Error to indicate invalid response."""