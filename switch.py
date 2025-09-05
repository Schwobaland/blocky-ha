"""Switch platform for Blocky integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTR_ENABLED
from . import BlockyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blocky switch based on a config entry."""
    coordinator: BlockyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    switches = [BlockyBlockingSwitch(coordinator)]
    async_add_entities(switches)


class BlockyBlockingSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of Blocky blocking switch."""

    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "Blocky Blocking"
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_blocking_switch"
        self._attr_icon = "mdi:shield"

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self.coordinator.data and ATTR_ENABLED in self.coordinator.data:
            return self.coordinator.data[ATTR_ENABLED]
        return None

    @property
    def icon(self) -> str:
        """Return the icon of the switch."""
        if self.is_on:
            return "mdi:shield-check"
        return "mdi:shield-off"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        success = await self.coordinator.enable_blocking()
        if not success:
            _LOGGER.error("Failed to enable blocking")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        success = await self.coordinator.disable_blocking()
        if not success:
            _LOGGER.error("Failed to disable blocking")
