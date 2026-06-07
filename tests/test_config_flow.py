from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from custom_components.nws_alerts.const import (
    CONF_SCAN_INTERVAL,
    CONF_USER_AGENT,
    DEFAULT_NAME,
    DOMAIN,
)


async def test_config_flow_user(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_USER_AGENT: "HomeAssistant-NWSAlerts/0.1 test@example.com",
            CONF_SCAN_INTERVAL: 300,
            "area": "TX",
            "event": "Tornado Warning",
        },
    )

    assert result["type"] == "create_entry"
    assert result["title"] == DEFAULT_NAME
    assert result["data"]["area"] == "TX"
