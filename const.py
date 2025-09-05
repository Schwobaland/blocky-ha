"""Constants for the Blocky integration."""

DOMAIN = "blocky"
DEFAULT_PORT = 4000
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 10

# Configuration
CONF_TIMEOUT = "timeout"

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