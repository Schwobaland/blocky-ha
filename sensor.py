"""Sensor platform for Blocky integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTR_ENABLED, ATTR_AUTO_ENABLE_IN_SEC, ATTR_DISABLED_GROUPS
from . import BlockyDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blocky sensor based on a config entry."""
    coordinator: BlockyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        BlockyStatusSensor(coordinator),
        BlockyAutoEnableTimerSensor(coordinator),
        BlockyDisabledGroupsSensor(coordinator),
    ]
    
    async_add_entities(sensors)


class BlockyStatusSensor(CoordinatorEntity, SensorEntity):
    """Representation of Blocky blocking status sensor."""

    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Blocky Blocking Status"
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_blocking_status"
        self._attr_icon = "mdi:shield"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        if self.coordinator.data and ATTR_ENABLED in self.coordinator.data:
            return "ON" if self.coordinator.data[ATTR_ENABLED] else "OFF"
        return "unknown"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        if self.coordinator.data and ATTR_ENABLED in self.coordinator.data:
            return "mdi:shield-check" if self.coordinator.data[ATTR_ENABLED] else "mdi:shield-off"
        return "mdi:shield-outline"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
        return {
            ATTR_ENABLED: self.coordinator.data.get(ATTR_ENABLED),
            ATTR_AUTO_ENABLE_IN_SEC: self.coordinator.data.get(ATTR_AUTO_ENABLE_IN_SEC),
            ATTR_DISABLED_GROUPS: self.coordinator.data.get(ATTR_DISABLED_GROUPS, []),
        }


class BlockyAutoEnableTimerSensor(CoordinatorEntity, SensorEntity):
    """Representation of Blocky auto-enable timer sensor."""

    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Blocky Auto Enable Timer"
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_auto_enable_timer"
        self._attr_icon = "mdi:timer"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "s"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        if self.coordinator.data and ATTR_AUTO_ENABLE_IN_SEC in self.coordinator.data:
            return self.coordinator.data[ATTR_AUTO_ENABLE_IN_SEC]
        return None


class BlockyDisabledGroupsSensor(CoordinatorEntity, SensorEntity):
    """Representation of Blocky disabled groups sensor."""

    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Blocky Disabled Groups"
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_disabled_groups"
        self._attr_icon = "mdi:account-group-outline"
        self._attr_should_poll = False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success 
            and self.coordinator.data is not None
        )

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        if not self.available:
            return "unavailable"
            
        groups = self.coordinator.data.get(ATTR_DISABLED_GROUPS)
        if groups is None:
            return "None"
        elif isinstance(groups, list):
            return ", ".join(groups) if groups else "None"
        else:
            return str(groups) if groups else "None"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        if not self.available:
            return {}
            
        groups = self.coordinator.data.get(ATTR_DISABLED_GROUPS, [])
        return {
            "groups_list": groups if isinstance(groups, list) else [],
            "count": len(groups) if isinstance(groups, list) else 0,
            "raw_data": groups,
        }
