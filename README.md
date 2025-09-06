# Blocky DNS Home Assistant Integration

A comprehensive Home Assistant integration for [Blocky DNS](https://0xerr0r.github.io/blocky/), providing network-wide ad-blocking, DNS filtering, and performance monitoring.

## 🚀 Features

### **Core Functionality**

- 🛡️ **DNS Blocking Control** - Enable/disable blocking with one click
- ⏰ **Timed Disable** - Temporarily disable blocking (5min, 15min, 1hr, custom)
- 🔄 **List Management** - Refresh blocking lists and clear DNS cache
- 📊 **Real-time Status** - Live monitoring of blocking status and timers

### **Advanced Monitoring** (Optional Prometheus Support)

- 📈 **Performance Metrics** - Query volume, cache hit rates, response times
- 🎯 **Cache Analytics** - DNS cache utilization and efficiency tracking
- 🛡️ **Security Insights** - Blocked vs allowed queries, response analysis
- 📋 **System Health** - Error tracking, failed downloads, list refresh status
- 👥 **Client Analysis** - Per-client query statistics and DNS request types

### **Beautiful Dashboards**

- 📊 **Multiple Layout Options** - From simple controls to comprehensive analytics
- 📱 **Mobile Optimized** - Responsive design for phone and tablet
- 📈 **Interactive Graphs** - Built-in time-series charts and performance gauges
- 🎨 **Visual Status Indicators** - Color-coded protection status and alerts

## 📦 Installation

### Method 1: HACS (Recommended)

1. Open HACS in your Home Assistant instance
1. Go to “Integrations”
1. Click the “+” button and search for “Blocky DNS”
1. Click “Download” and restart Home Assistant
1. Go to Settings → Devices & Services → Add Integration
1. Search for “Blocky DNS” and follow setup wizard

### Method 2: Manual Installation

1. Download the `blocky` folder from the [latest release](https://github.com/yourusername/ha-blocky/releases)
1. Copy the folder to your `config/custom_components/` directory
1. Restart Home Assistant
1. Go to Settings → Devices & Services → Add Integration
1. Search for “Blocky DNS” and configure

## ⚙️ Configuration

### Initial Setup

1. **Add Integration**: Settings → Devices & Services → Add Integration → “Blocky DNS”
1. **Enter Details**:
- **Host**: IP address of your Blocky server (e.g., `192.168.1.100`)
- **API Port**: Port where Blocky API runs (default: `4000`)
- **Enable Prometheus**: Check to enable advanced metrics (optional)
- **Prometheus Port**: Port for metrics endpoint (usually same as API port)

### Advanced Options

Access via Settings → Devices & Services → Blocky → Configure:

- **Update Interval**: How often to check Blocky status (default: 30 seconds)
- **Connection Timeout**: Maximum wait time for Blocky responses (default: 10 seconds)
- **Prometheus Metrics**: Enable/disable detailed performance monitoring

## 🛠️ Blocky Server Setup

Ensure your Blocky server has the API enabled in `config.yml`:

```yaml
# Blocky configuration
api:
  host: 0.0.0.0
  port: 4000

# Optional: Enable Prometheus metrics
prometheus:
  enable: true
  path: /metrics
```

Restart your Blocky server after configuration changes.

## 📊 Entities Created

### **Always Available**

|Entity                            |Description                       |Type  |
|----------------------------------|----------------------------------|------|
|`sensor.blocky_blocking_status`   |Current blocking status (ON/OFF)  |Sensor|
|`sensor.blocky_auto_enable_timer` |Auto-enable countdown in seconds  |Sensor|
|`sensor.blocky_disabled_groups`   |Currently disabled blocking groups|Sensor|
|`switch.blocky_blocking`          |Master blocking toggle            |Switch|
|`button.blocky_refresh_lists`     |Refresh blocking lists            |Button|
|`button.blocky_flush_cache`       |Clear DNS cache                   |Button|
|`button.blocky_disable_5_minutes` |Quick 5-minute disable            |Button|
|`button.blocky_disable_15_minutes`|Quick 15-minute disable           |Button|
|`button.blocky_disable_1_hour`    |Quick 1-hour disable              |Button|

### **Prometheus Metrics** (When Enabled)

|Entity                               |Description                                    |Type  |
|-------------------------------------|-----------------------------------------------|------|
|`sensor.blocky_total_queries`        |Total DNS queries with client/type breakdown   |Sensor|
|`sensor.blocky_total_responses`      |DNS responses by type (blocked/cached/resolved)|Sensor|
|`sensor.blocky_cache_entries`        |Current DNS cache size                         |Sensor|
|`sensor.blocky_cache_hits`           |DNS cache hit counter                          |Sensor|
|`sensor.blocky_cache_misses`         |DNS cache miss counter                         |Sensor|
|`sensor.blocky_total_errors`         |Total DNS resolution errors                    |Sensor|
|`sensor.blocky_last_list_refresh`    |Timestamp of last list update                  |Sensor|
|`sensor.blocky_denylist_cache`       |Blocked domains by group                       |Sensor|
|`sensor.blocky_allowlist_cache`      |Allowed domains by group                       |Sensor|
|`sensor.blocky_total_prefetches`     |DNS prefetch operations                        |Sensor|
|`sensor.blocky_prefetch_hits`        |Successful prefetch hits with efficiency       |Sensor|
|`sensor.blocky_failed_downloads`     |Failed blocklist downloads                     |Sensor|
|`sensor.blocky_prefetch_domain_cache`|Prefetch cache size                            |Sensor|

## 🎨 Dashboard Examples

### Simple Control Panel

```yaml
type: entities
title: "🛡️ DNS Protection"
entities:
  - entity: sensor.blocky_blocking_status
    name: "Status"
  - entity: switch.blocky_blocking
    name: "Toggle Protection"
  - entity: button.blocky_disable_15_minutes
    name: "Pause 15 Minutes"
```

### Performance Dashboard

```yaml
type: vertical-stack
cards:
  - type: glance
    entities:
      - sensor.blocky_total_queries
      - sensor.blocky_cache_hits
      - sensor.blocky_total_errors
    
  - type: history-graph
    title: "DNS Activity (24h)"
    entities:
      - sensor.blocky_total_queries
      - sensor.blocky_cache_hits
    hours_to_show: 24
```



## 🐛 Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.blocky: debug
```

### Development Setup

1. Fork the repository
1. Create a feature branch: `git checkout -b feature-name`
1. Install development dependencies: `pip install -r requirements_dev.txt`
1. Make changes and test thoroughly
1. Submit a pull request



## 📄 License

This project is licensed under the MIT License - see the <LICENSE> file for details.

## 🙏 Acknowledgments

- [Blocky DNS](https://0xerr0r.github.io/blocky/) - Amazing DNS proxy and ad-blocker
- [Home Assistant](https://www.home-assistant.io/) - Open source home automation platform
- Community contributors and testers


## 🏷️ Version History

### v1.0.0

- Initial release with basic API integration
- Blocking control and status monitoring
- Dashboard examples and documentation


-----

**Made with ❤️ for the Home Assistant community**