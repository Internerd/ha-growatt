"""Diagnostics dump for a Growatt Local config entry.

What lands in a bug report matters more than what is in the log: the
decoded register values, the profile in use and whether the V2.01 overlay
answered are the three things needed to tell "this register does not exist
on my firmware" apart from "this register was decoded wrong".

The host, port and Modbus unit ID are redacted - they identify the network
the inverter sits on, and none of them is needed to read the register dump.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_SLAVE_ID, DOMAIN
from .coordinator import GrowattLocalCoordinator

TO_REDACT = {"host", "port", CONF_SLAVE_ID}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: GrowattLocalCoordinator = hass.data[DOMAIN][entry.entry_id]

    data = dict(coordinator.data or {})
    # datetime is not JSON-serialisable and adds nothing here.
    last_update = data.pop("last_update", None)

    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinator": {
            "profile": coordinator.profile,
            "protocol_v201": coordinator.protocol_v201,
            "is_online": coordinator.is_online,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "last_successful_update": last_update.isoformat() if last_update else None,
        },
        "decoded_registers": data,
    }
