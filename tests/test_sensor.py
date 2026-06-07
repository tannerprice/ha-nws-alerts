from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nws_alerts.const import (
    CONF_SCAN_INTERVAL,
    CONF_USER_AGENT,
    DOMAIN,
)
from custom_components.nws_alerts.coordinator import NWSAlertsCoordinator
from custom_components.nws_alerts.sensor import NWSAlertsSensor


def _make_entry(hass) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USER_AGENT: "HomeAssistant-NWSAlerts/0.1 test@example.com",
            CONF_SCAN_INTERVAL: 300,
            "area": "TX",
        },
        options={},
    )
    entry.add_to_hass(hass)
    return entry


async def test_sensor_syncs_from_coordinator(hass) -> None:
    entry = _make_entry(hass)
    coordinator = NWSAlertsCoordinator(hass, entry)

    coordinator.data = {
        "count": 2,
        "alerts": [
            {"event": "Tornado Warning"},
            {"event": "Severe Thunderstorm Warning"},
        ],
        "url": "https://api.weather.gov/alerts/active?area=TX",
    }

    sensor = NWSAlertsSensor(coordinator, entry)

    assert sensor.native_value == 2

    attrs = sensor.extra_state_attributes

    assert attrs is not None
    assert attrs["url"].startswith("https://api.weather.gov")
    assert len(attrs["alerts"]) == 2
