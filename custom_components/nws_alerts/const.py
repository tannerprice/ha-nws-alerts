DOMAIN = "nws_alerts"

PLATFORMS = ["sensor"]

DEFAULT_NAME = "NWS Alerts"
DEFAULT_SCAN_INTERVAL = 300

CONF_USER_AGENT = "user_agent"
CONF_SCAN_INTERVAL = "scan_interval"

NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"

EVENT_ALERT = f"{DOMAIN}_alert"
EVENT_ALERT_ISSUED = f"{DOMAIN}_alert_issued"
EVENT_ALERT_UPDATED = f"{DOMAIN}_alert_updated"
EVENT_ALERT_CANCELLED = f"{DOMAIN}_alert_cancelled"

MESSAGE_TYPE_ALERT = "Alert"
MESSAGE_TYPE_UPDATE = "Update"
MESSAGE_TYPE_CANCEL = "Cancel"

ALERT_FILTERS = [
    "status",
    "message_type",
    "event",
    "code",
    "area",
    "point",
    "region",
    "region_type",
    "zone",
    "urgency",
    "severity",
    "certainty",
    "limit",
]
