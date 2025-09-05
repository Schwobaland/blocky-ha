"""Button platform for Blocky integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from . import BlockyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blocky button based on a config entry."""
    coordinator: BlockyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    buttons = [
        BlockyRefreshListsButton(coordinator),
        BlockyFlushCacheButton(coordinator),
        BlockyDisable5MinButton(coordinator),
        BlockyDisable15MinButton(coordinator),
        BlockyDisable1HourButton(coordinator),
    ]
    
    async_add_entities(buttons)


class BlockyRefreshListsButton(CoordinatorEntity, ButtonEntity):
    """Representation of Blocky refresh lists button."""

    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Blocky Refresh Lists"
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_refresh_lists"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.refresh_lists()
        if success:
            _LOGGER.info("Successfully refreshed Blocky lists")
        else:
            _LOGGER.error("Failed to refresh Blocky lists")


class BlockyFlushCacheButton(CoordinatorEntity, ButtonEntity):
    """Representation of Blocky flush cache button."""

    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Blocky Flush Cache"
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_flush_cache"
        self._attr_icon = "mdi:delete-sweep"

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.flush_cache()
        if success:
            _LOGGER.info("Successfully flushed Blocky cache")
        else:
            _LOGGER.error("Failed to flush Blocky cache")


class BlockyDisable5MinButton(CoordinatorEntity, ButtonEntity):
    """Representation of Blocky disable 5 minutes button."""

    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Blocky Disable 5 Minutes"
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_disable_5min"
        self._attr_icon = "mdi:timer-5"

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.disable_blocking("5m")
        if success:
            _LOGGER.info("Successfully disabled Blocky for 5 minutes")
        else:
            _LOGGER.error("Failed to disable Blocky")


class BlockyDisable15MinButton(CoordinatorEntity, ButtonEntity):
    """Representation of Blocky disable 15 minutes button."""

    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Blocky Disable 15 Minutes"
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_disable_15min"
        self._attr_icon = "mdi:timer-15"

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.disable_blocking("15m")
        if success:
            _LOGGER.info("Successfully disabled Blocky for 15 minutes")
        else:
            _LOGGER.error("Failed to disable Blocky")


class BlockyDisable1HourButton(CoordinatorEntity, ButtonEntity):
    """Representation of Blocky disable 1 hour button."""

    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Blocky Disable 1 Hour"
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_disable_1hour"
        self._attr_icon = "mdi:timer-1"

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.disable_blocking("1h")
        if success:
            _LOGGER.info("Successfully disabled Blocky for 1 hour")
        else:
            _LOGGER.error("Failed to disable Blocky")
