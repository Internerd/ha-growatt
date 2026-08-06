"""Config flow for Growatt Local.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DEVICE_NAME,
    CONF_PROFILE,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PROFILE_LABELS,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_NAME): str,
        vol.Required(CONF_PROFILE): vol.In(PROFILE_LABELS),
        vol.Required("host"): str,
        vol.Required("port", default=DEFAULT_PORT): int,
        vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
        vol.Required("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
        vol.Required("timeout", default=DEFAULT_TIMEOUT): int,
    }
)


class GrowattLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for one Growatt inverter."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = f"{user_input['host']}_{user_input['port']}_{user_input[CONF_SLAVE_ID]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_DEVICE_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={
                "sph_label": PROFILE_LABELS["sph_tl3"],
                "mic_label": PROFILE_LABELS["mic"],
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "GrowattLocalOptionsFlow":
        return GrowattLocalOptionsFlow(config_entry)


class GrowattLocalOptionsFlow(config_entries.OptionsFlow):
    """Allow adjusting scan interval / timeout after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options or self._config_entry.data
        schema = vol.Schema(
            {
                vol.Required(
                    "scan_interval",
                    default=current.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                ): int,
                vol.Required(
                    "timeout",
                    default=current.get("timeout", DEFAULT_TIMEOUT),
                ): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
