"""Constants for the Blocky integration."""

DOMAIN = "blocky"
DEFAULT_PORT = 4000
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 10

# Configuration
CONF_TIMEOUT = "timeout"
CONF_PROMETHEUS_ENABLED = "prometheus_enabled"
CONF_PROMETHEUS_PORT = "prometheus_port"

# Default Prometheus settings
DEFAULT_PROMETHEUS_PORT = 4000
DEFAULT_PROMETHEUS_ENABLED = False

# Attributes
ATTR_ENABLED = "enabled"
ATTR_AUTO_ENABLE_IN_SEC = "autoEnableInSec"
ATTR_DISABLED_GROUPS = "disabledGroups"

# Services
SERVICE_ENABLE_BLOCKING = "enable_blocking"
SERVICE_DISABLE_BLOCKING = "disable_blocking"
SERVICE_REFRESH_LISTS = "refresh_lists"
SERVICE_FLUSH_CACHE = "flush_cache"
SERVICE_QUERY_DNS = "query_dns"

# Prometheus Metrics Names
PROMETHEUS_METRICS = {
    "denylist_cache_entries": "blocky_denylist_cache_entries",
    "allowlist_cache_entries": "blocky_allowlist_cache_entries", 
    "error_total": "blocky_error_total",
    "query_total": "blocky_query_total",
    "request_duration_seconds": "blocky_blocky_request_duration_seconds",
    "response_total": "blocky_response_total",
    "blocking_enabled": "blocky_blocking_enabled",
    "cache_entries": "blocky_cache_entries",
    "cache_hits_total": "blocky_cache_hits_total",
    "cache_misses_total": "blocky_cache_misses_total",
    "last_list_group_refresh": "blocky_last_list_group_refresh_timestamp_seconds",
    "prefetches_total": "blocky_prefetches_total",
    "prefetch_hits_total": "blocky_prefetch_hits_total",
    "prefetch_domain_cache_entries": "blocky_prefetch_domain_name_cache_entries",
    "failed_downloads_total": "blocky_failed_downloads_total",
}