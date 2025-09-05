"""Sensor platform for Blocky integration."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity, 
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN, 
    ATTR_ENABLED, 
    ATTR_AUTO_ENABLE_IN_SEC, 
    ATTR_DISABLED_GROUPS,
    PROMETHEUS_METRICS,
)
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
    
    # Add Prometheus sensors if enabled
    if coordinator.prometheus_enabled:
        sensors.extend([
            BlockyCacheEntriesSensor(coordinator),
            BlockyCacheHitsSensor(coordinator),
            BlockyCacheMissesSensor(coordinator),
            BlockyErrorTotalSensor(coordinator),
            BlockyQueryTotalSensor(coordinator),
            BlockyResponseTotalSensor(coordinator),
            BlockyPrefetchesTotalSensor(coordinator),
            BlockyPrefetchHitsSensor(coordinator),
            BlockyFailedDownloadsSensor(coordinator),
            BlockyLastListRefreshSensor(coordinator),
            BlockyDenylistCacheSensor(coordinator),
            BlockyAllowlistCacheSensor(coordinator),
            BlockyPrefetchDomainCacheSensor(coordinator),
        ])
    
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
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_state_class = SensorStateClass.MEASUREMENT

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


# Prometheus-based sensors
class BlockyPrometheusBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Prometheus-based sensors."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator, metric_name: str, display_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.metric_name = metric_name
        self._attr_name = display_name
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_{metric_name}"
        self._attr_should_poll = False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.prometheus_enabled
            and self.coordinator.last_update_success 
            and self.coordinator.data is not None
            and "prometheus" in self.coordinator.data
        )

    def get_metric_value(self, labels_filter: dict = None) -> Any:
        """Get metric value with optional label filtering."""
        if not self.available:
            return None
            
        prometheus_data = self.coordinator.data.get("prometheus", {})
        metric_data = prometheus_data.get(self.metric_name, [])
        
        if not metric_data:
            return None
        
        # If no label filter, return first value or sum if multiple
        if not labels_filter:
            if len(metric_data) == 1:
                return metric_data[0]["value"]
            else:
                # Sum all values for aggregate metrics
                return sum(item["value"] for item in metric_data if isinstance(item["value"], (int, float)))
        
        # Filter by labels
        for item in metric_data:
            if all(item["labels"].get(k) == v for k, v in labels_filter.items()):
                return item["value"]
        
        return None


class BlockyCacheEntriesSensor(BlockyPrometheusBaseSensor):
    """Cache entries sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["cache_entries"], "Blocky Cache Entries")
        self._attr_icon = "mdi:database"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()


class BlockyCacheHitsSensor(BlockyPrometheusBaseSensor):
    """Cache hits sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["cache_hits_total"], "Blocky Cache Hits")
        self._attr_icon = "mdi:database-check"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()


class BlockyCacheMissesSensor(BlockyPrometheusBaseSensor):
    """Cache misses sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["cache_miss_count"], "Blocky Cache Misses")
        self._attr_icon = "mdi:database-remove"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()


class BlockyErrorTotalSensor(BlockyPrometheusBaseSensor):
    """Total errors sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["error_total"], "Blocky Total Errors")
        self._attr_icon = "mdi:alert-circle"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()


class BlockyQueryTotalSensor(BlockyPrometheusBaseSensor):
    """Total queries sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["query_total"], "Blocky Total Queries")
        self._attr_icon = "mdi:dns"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes with breakdown by client and type."""
        if not self.available:
            return {}
            
        prometheus_data = self.coordinator.data.get("prometheus", {})
        metric_data = prometheus_data.get(self.metric_name, [])
        
        attributes = {
            "by_client": {},
            "by_type": {},
        }
        
        for item in metric_data:
            labels = item.get("labels", {})
            value = item["value"]
            
            # Group by client
            client = labels.get("client", "unknown")
            if client not in attributes["by_client"]:
                attributes["by_client"][client] = 0
            attributes["by_client"][client] += value
            
            # Group by DNS type
            dns_type = labels.get("type", "unknown")
            if dns_type not in attributes["by_type"]:
                attributes["by_type"][dns_type] = 0
            attributes["by_type"][dns_type] += value
        
        return attributes


class BlockyResponseTotalSensor(BlockyPrometheusBaseSensor):
    """Total responses sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["response_total"], "Blocky Total Responses")
        self._attr_icon = "mdi:reply"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes with breakdown by response type."""
        if not self.available:
            return {}
            
        prometheus_data = self.coordinator.data.get("prometheus", {})
        metric_data = prometheus_data.get(self.metric_name, [])
        
        attributes = {
            "by_response_type": {},
            "by_reason": {},
            "blocked": 0,
            "cached": 0,
        }
        
        for item in metric_data:
            labels = item.get("labels", {})
            value = item["value"]
            
            # Group by response type
            response_type = labels.get("response_type", "unknown")
            if response_type not in attributes["by_response_type"]:
                attributes["by_response_type"][response_type] = 0
            attributes["by_response_type"][response_type] += value
            
            # Group by reason
            reason = labels.get("reason", "unknown")
            if reason not in attributes["by_reason"]:
                attributes["by_reason"][reason] = 0
            attributes["by_reason"][reason] += value
            
            # Special counters for blocked and cached
            if response_type.lower() == "blocked":
                attributes["blocked"] += value
            elif response_type.lower() == "cached":
                attributes["cached"] += value
        
        return attributes


class BlockyPrefetchesTotalSensor(BlockyPrometheusBaseSensor):
    """Total prefetches sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["prefetches_total"], "Blocky Total Prefetches")
        self._attr_icon = "mdi:download"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()


class BlockyPrefetchHitsSensor(BlockyPrometheusBaseSensor):
    """Prefetch hits sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["prefetch_hits_total"], "Blocky Prefetch Hits")
        self._attr_icon = "mdi:download-circle"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()


class BlockyFailedDownloadsSensor(BlockyPrometheusBaseSensor):
    """Failed downloads sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["failed_downloads_total"], "Blocky Failed Downloads")
        self._attr_icon = "mdi:download-off"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()


class BlockyLastListRefreshSensor(BlockyPrometheusBaseSensor):
    """Last list refresh timestamp sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["last_list_group_refresh"], "Blocky Last List Refresh")
        self._attr_icon = "mdi:refresh"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        """Return the native value of the sensor."""
        timestamp = self.get_metric_value()
        if timestamp and isinstance(timestamp, (int, float)) and timestamp > 0:
            return dt_util.utc_from_timestamp(timestamp)
        return None


class BlockyDenylistCacheSensor(BlockyPrometheusBaseSensor):
    """Denylist cache entries sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["denylist_cache_entries"], "Blocky Denylist Cache")
        self._attr_icon = "mdi:shield-off"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes with breakdown by group."""
        if not self.available:
            return {}
            
        prometheus_data = self.coordinator.data.get("prometheus", {})
        metric_data = prometheus_data.get(self.metric_name, [])
        
        attributes = {"by_group": {}}
        
        for item in metric_data:
            labels = item.get("labels", {})
            value = item["value"]
            group = labels.get("group", "default")
            attributes["by_group"][group] = value
        
        return attributes


class BlockyAllowlistCacheSensor(BlockyPrometheusBaseSensor):
    """Allowlist cache entries sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["allowlist_cache_entries"], "Blocky Allowlist Cache")
        self._attr_icon = "mdi:shield-check"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes with breakdown by group."""
        if not self.available:
            return {}
            
        prometheus_data = self.coordinator.data.get("prometheus", {})
        metric_data = prometheus_data.get(self.metric_name, [])
        
        attributes = {"by_group": {}}
        
        for item in metric_data:
            labels = item.get("labels", {})
            value = item["value"]
            group = labels.get("group", "default")
            attributes["by_group"][group] = value
        
        return attributes


class BlockyPrefetchDomainCacheSensor(BlockyPrometheusBaseSensor):
    """Prefetch domain cache entries sensor."""
    
    def __init__(self, coordinator: BlockyDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, PROMETHEUS_METRICS["prefetch_domain_cache_entries"], "Blocky Prefetch Domain Cache")
        self._attr_icon = "mdi:cached"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.get_metric_value()