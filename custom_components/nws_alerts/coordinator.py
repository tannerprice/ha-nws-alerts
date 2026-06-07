import logging
from datetime import timedelta
from typing import Any

from aiohttp import ClientError, ClientTimeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from yarl import URL

from .const import (
    ALERT_FILTERS,
    CONF_SCAN_INTERVAL,
    CONF_USER_AGENT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_ALERT,
    EVENT_ALERT_CANCELLED,
    EVENT_ALERT_ISSUED,
    EVENT_ALERT_UPDATED,
    MESSAGE_TYPE_ALERT,
    MESSAGE_TYPE_CANCEL,
    MESSAGE_TYPE_UPDATE,
    NWS_ALERTS_URL,
)

_LOGGER = logging.getLogger(__name__)


class NWSAlertsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.session = async_get_clientsession(hass)

        self._seen_fingerprints: set[str] = set()
        self._startup_complete = False

        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(scan_interval)),
            always_update=False,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        payload = await self._fetch_alerts()
        alerts = self._normalize_alerts(payload)

        self._fire_new_alert_events(alerts)

        self._startup_complete = True

        return {
            "count": len(alerts),
            "alerts": alerts,
            "url": self._build_url(),
        }

    def _build_url(self) -> str:
        params: dict[str, str] = {}
        merged = {**self.entry.data, **self.entry.options}

        for key in ALERT_FILTERS:
            value = merged.get(key)
            if value not in (None, ""):
                nws_key = self._to_nws_param(key)
                params[nws_key] = str(value)

        return str(URL(NWS_ALERTS_URL).with_query(params))

    async def _fetch_alerts(self) -> dict[str, Any]:
        merged = {**self.entry.data, **self.entry.options}

        headers = {
            "Accept": "application/geo+json",
            "User-Agent": merged[CONF_USER_AGENT],
        }

        url = self._build_url()
        timeout = ClientTimeout(total=20)

        try:
            async with self.session.get(
                url, headers=headers, timeout=timeout
            ) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise UpdateFailed(f"NWS API error {response.status}: {text}")

                return await response.json()

        except (ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error fetching NWS alerts: {err}") from err

    def _normalize_alerts(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []

        for feature in payload.get("features", []):
            props = feature.get("properties", {})

            alert_id = props.get("id")
            message_type = props.get("messageType")
            sent = props.get("sent")
            updated = props.get("updated")

            alert = {
                "id": alert_id,
                "area_desc": props.get("areaDesc"),
                "event": props.get("event"),
                "headline": props.get("headline"),
                "description": props.get("description"),
                "instruction": props.get("instruction"),
                "severity": props.get("severity"),
                "certainty": props.get("certainty"),
                "urgency": props.get("urgency"),
                "status": props.get("status"),
                "message_type": message_type,
                "category": props.get("category"),
                "response": props.get("response"),
                "sent": sent,
                "effective": props.get("effective"),
                "onset": props.get("onset"),
                "expires": props.get("expires"),
                "ends": props.get("ends"),
                "updated": updated,
                "sender_name": props.get("senderName"),
                "zones": props.get("geocode", {}).get("UGC", []),
            }

            alert["fingerprint"] = self._fingerprint(alert)

            alerts.append(alert)

        return alerts

    def _fingerprint(self, alert: dict[str, Any]) -> str:
        return "|".join(
            [
                str(alert.get("id")),
                str(alert.get("message_type")),
                str(alert.get("sent")),
                str(alert.get("updated")),
                str(alert.get("expires")),
            ]
        )

    def _fire_new_alert_events(self, alerts: list[dict[str, Any]]) -> None:
        for alert in alerts:
            fingerprint = alert["fingerprint"]

            if fingerprint in self._seen_fingerprints:
                continue

            self._seen_fingerprints.add(fingerprint)

            # Avoid firing every currently-active alert on HA startup/reload.
            if not self._startup_complete:
                continue

            event_type = self._event_type_for_alert(alert)

            event_data = {
                **alert,
                "is_new": alert.get("message_type") == MESSAGE_TYPE_ALERT,
                "is_update": alert.get("message_type") == MESSAGE_TYPE_UPDATE,
                "is_cancel": alert.get("message_type") == MESSAGE_TYPE_CANCEL,
            }

            self.hass.bus.async_fire(EVENT_ALERT, event_data)
            self.hass.bus.async_fire(event_type, event_data)

    def _event_type_for_alert(self, alert: dict[str, Any]) -> str:
        message_type = alert.get("message_type")

        if message_type == MESSAGE_TYPE_ALERT:
            return EVENT_ALERT_ISSUED

        if message_type == MESSAGE_TYPE_UPDATE:
            return EVENT_ALERT_UPDATED

        if message_type == MESSAGE_TYPE_CANCEL:
            return EVENT_ALERT_CANCELLED

        return EVENT_ALERT

    def _to_nws_param(self, key: str) -> str:
        if key == "message_type":
            return "message_type"

        if key == "region_type":
            return "region_type"

        return key
