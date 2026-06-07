from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    ALERT_FILTERS,
    CONF_SCAN_INTERVAL,
    CONF_USER_AGENT,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def _schema(defaults: dict | None = None):
    defaults = defaults or {}

    schema: dict[Any, Any] = {
        vol.Required(
            CONF_NAME,
            default=defaults.get(CONF_NAME, DEFAULT_NAME),
        ): str,
        vol.Required(
            CONF_USER_AGENT,
            default=defaults.get(
                CONF_USER_AGENT,
                "HomeAssistant-NWS-Alerts/0.1",
            ),
        ): str,
        vol.Required(
            CONF_SCAN_INTERVAL,
            default=defaults.get(
                CONF_SCAN_INTERVAL,
                DEFAULT_SCAN_INTERVAL,
            ),
        ): int,
    }

    for key in ALERT_FILTERS:
        schema[
            vol.Optional(
                key,
                default=defaults.get(key, ""),
            )
        ] = str

    return vol.Schema(schema)


class NWSAlertsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            title = user_input.get(CONF_NAME, DEFAULT_NAME)

            await self.async_set_unique_id(title.lower().replace(" ", "_"))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return NWSAlertsOptionsFlow(config_entry)


class NWSAlertsOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(defaults),
        )
