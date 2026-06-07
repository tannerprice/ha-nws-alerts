from typing import Any
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nws_alerts.const import (
    CONF_SCAN_INTERVAL,
    CONF_USER_AGENT,
    DOMAIN,
    EVENT_ALERT,
    EVENT_ALERT_CANCELLED,
    EVENT_ALERT_ISSUED,
    EVENT_ALERT_UPDATED,
)
from custom_components.nws_alerts.coordinator import NWSAlertsCoordinator


def _make_entry(hass, data: dict[str, Any] | None = None) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USER_AGENT: "HomeAssistant-NWSAlerts/0.1 test@example.com",
            CONF_SCAN_INTERVAL: 300,
            "area": "TX",
            **(data or {}),
        },
        options={},
    )
    entry.add_to_hass(hass)
    return entry


def _payload(
    *,
    alert_id: str = "abc123",
    event: str = "Tornado Warning",
    message_type: str = "Alert",
    updated: str = "2026-06-07T12:00:00-05:00",
) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": alert_id,
                    "areaDesc": "Dallas County",
                    "event": event,
                    "headline": f"{event} {message_type}",
                    "description": "Take shelter.",
                    "instruction": "Move indoors.",
                    "severity": "Extreme",
                    "certainty": "Observed",
                    "urgency": "Immediate",
                    "status": "Actual",
                    "messageType": message_type,
                    "category": "Met",
                    "response": "Shelter",
                    "sent": "2026-06-07T12:00:00-05:00",
                    "effective": "2026-06-07T12:00:00-05:00",
                    "onset": "2026-06-07T12:00:00-05:00",
                    "expires": "2026-06-07T12:45:00-05:00",
                    "ends": None,
                    "updated": updated,
                    "senderName": "NWS Fort Worth TX",
                    "geocode": {"UGC": ["TXC113"]},
                },
            }
        ],
    }


class MockResponse:
    status = 200

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args: Any) -> None:
        return None

    async def json(self) -> dict[str, Any]:
        return self._payload

    async def text(self) -> str:
        return ""


async def test_coordinator_fetches_alerts(hass) -> None:
    entry = _make_entry(hass)

    with patch(
        "custom_components.nws_alerts.coordinator.async_get_clientsession"
    ) as mock_get_session:
        session = mock_get_session.return_value
        session.get.return_value = MockResponse(_payload())

        coordinator = NWSAlertsCoordinator(hass, entry)
        data = await coordinator._async_update_data()

    assert data["count"] == 1
    assert data["alerts"][0]["id"] == "abc123"
    assert data["alerts"][0]["event"] == "Tornado Warning"
    assert data["alerts"][0]["message_type"] == "Alert"
    assert data["alerts"][0]["severity"] == "Extreme"
    assert data["alerts"][0]["zones"] == ["TXC113"]
    assert data["url"].startswith("https://api.weather.gov/alerts/active")


async def test_coordinator_builds_url_with_filters(hass) -> None:
    entry = _make_entry(
        hass,
        {
            "event": "Tornado Warning",
            "severity": "Extreme",
            "certainty": "Observed",
        },
    )

    with patch(
        "custom_components.nws_alerts.coordinator.async_get_clientsession"
    ) as mock_get_session:
        session = mock_get_session.return_value
        session.get.return_value = MockResponse(_payload())

        coordinator = NWSAlertsCoordinator(hass, entry)
        data = await coordinator._async_update_data()

    assert "area=TX" in data["url"]
    assert "event=Tornado+Warning" in data["url"]
    assert "severity=Extreme" in data["url"]
    assert "certainty=Observed" in data["url"]


async def test_startup_alerts_seed_fingerprints_without_firing_events(hass) -> None:
    entry = _make_entry(hass)
    fired_events = []

    hass.bus.async_listen(EVENT_ALERT, lambda event: fired_events.append(event))
    hass.bus.async_listen(EVENT_ALERT_ISSUED, lambda event: fired_events.append(event))

    with patch(
        "custom_components.nws_alerts.coordinator.async_get_clientsession"
    ) as mock_get_session:
        session = mock_get_session.return_value
        session.get.return_value = MockResponse(_payload())

        coordinator = NWSAlertsCoordinator(hass, entry)
        await coordinator._async_update_data()
        await hass.async_block_till_done()

    assert fired_events == []


async def test_same_alert_revision_does_not_fire_twice(hass) -> None:
    entry = _make_entry(hass)
    fired_events = []

    hass.bus.async_listen(EVENT_ALERT, lambda event: fired_events.append(event))
    hass.bus.async_listen(EVENT_ALERT_ISSUED, lambda event: fired_events.append(event))

    with patch(
        "custom_components.nws_alerts.coordinator.async_get_clientsession"
    ) as mock_get_session:
        session = mock_get_session.return_value
        session.get.return_value = MockResponse(_payload())

        coordinator = NWSAlertsCoordinator(hass, entry)

        await coordinator._async_update_data()
        await coordinator._async_update_data()
        await hass.async_block_till_done()

    assert fired_events == []


async def test_updated_alert_revision_fires_update_event_once(hass) -> None:
    entry = _make_entry(hass)

    generic_events = []
    updated_events = []

    hass.bus.async_listen(EVENT_ALERT, lambda event: generic_events.append(event))
    hass.bus.async_listen(
        EVENT_ALERT_UPDATED, lambda event: updated_events.append(event)
    )

    with patch(
        "custom_components.nws_alerts.coordinator.async_get_clientsession"
    ) as mock_get_session:
        session = mock_get_session.return_value

        coordinator = NWSAlertsCoordinator(hass, entry)

        session.get.return_value = MockResponse(_payload())
        await coordinator._async_update_data()

        session.get.return_value = MockResponse(
            _payload(
                message_type="Update",
                updated="2026-06-07T12:10:00-05:00",
            )
        )
        await coordinator._async_update_data()
        await coordinator._async_update_data()

        await hass.async_block_till_done()

    assert len(generic_events) == 1
    assert len(updated_events) == 1

    event_data = updated_events[0].data

    assert event_data["event"] == "Tornado Warning"
    assert event_data["message_type"] == "Update"
    assert event_data["is_update"] is True
    assert event_data["is_new"] is False
    assert event_data["is_cancel"] is False


async def test_cancelled_alert_revision_fires_cancel_event_once(hass) -> None:
    entry = _make_entry(hass)

    generic_events = []
    cancelled_events = []

    hass.bus.async_listen(EVENT_ALERT, lambda event: generic_events.append(event))
    hass.bus.async_listen(
        EVENT_ALERT_CANCELLED,
        lambda event: cancelled_events.append(event),
    )

    with patch(
        "custom_components.nws_alerts.coordinator.async_get_clientsession"
    ) as mock_get_session:
        session = mock_get_session.return_value

        coordinator = NWSAlertsCoordinator(hass, entry)

        session.get.return_value = MockResponse(_payload())
        await coordinator._async_update_data()

        session.get.return_value = MockResponse(
            _payload(
                message_type="Cancel",
                updated="2026-06-07T12:15:00-05:00",
            )
        )
        await coordinator._async_update_data()
        await coordinator._async_update_data()

        await hass.async_block_till_done()

    assert len(generic_events) == 1
    assert len(cancelled_events) == 1

    event_data = cancelled_events[0].data

    assert event_data["event"] == "Tornado Warning"
    assert event_data["message_type"] == "Cancel"
    assert event_data["is_cancel"] is True
    assert event_data["is_update"] is False
    assert event_data["is_new"] is False


async def test_new_alert_after_startup_fires_issued_event_once(hass) -> None:
    entry = _make_entry(hass)

    generic_events = []
    issued_events = []

    hass.bus.async_listen(EVENT_ALERT, lambda event: generic_events.append(event))
    hass.bus.async_listen(EVENT_ALERT_ISSUED, lambda event: issued_events.append(event))

    with patch(
        "custom_components.nws_alerts.coordinator.async_get_clientsession"
    ) as mock_get_session:
        session = mock_get_session.return_value

        coordinator = NWSAlertsCoordinator(hass, entry)

        session.get.return_value = MockResponse(_payload(alert_id="abc123"))
        await coordinator._async_update_data()

        session.get.return_value = MockResponse(_payload(alert_id="def456"))
        await coordinator._async_update_data()
        await coordinator._async_update_data()

        await hass.async_block_till_done()

    assert len(generic_events) == 1
    assert len(issued_events) == 1

    event_data = issued_events[0].data

    assert event_data["id"] == "def456"
    assert event_data["message_type"] == "Alert"
    assert event_data["is_new"] is True
    assert event_data["is_update"] is False
    assert event_data["is_cancel"] is False
