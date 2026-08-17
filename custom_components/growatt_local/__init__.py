"""Growatt Local - a minimal, self-contained Modbus TCP integration for a
fixed pair of Growatt inverters (SPH-TL3 and MIC series only).

This intentionally does not attempt to auto-detect inverter models or
support the full Growatt lineup; it exists to serve exactly the two
inverters it was configured for, with entity IDs matching the previous
HACS "Growatt_ModbusTCP" integration so existing helpers/automations/
dashboards keep working unchanged.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    BLOCK_SIZE_OPTIONS,
    CONF_BLOCK_SIZE,
    CONF_DEVICE_NAME,
    CONF_INVERT_BATTERY_POWER,
    CONF_INVERT_GRID_POWER,
    CONF_OFFLINE_SCAN_INTERVAL,
    CONF_PROFILE,
    CONF_PROTOCOL_V201,
    CONF_SLAVE_ID,
    DEFAULT_BLOCK_SIZE,
    DEFAULT_OFFLINE_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import GrowattLocalCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one inverter from a config entry."""
    options = entry.options or {}

    def _get(key, default):
        return options.get(key, entry.data.get(key, default))

    coordinator = GrowattLocalCoordinator(
        hass,
        device_name=entry.data[CONF_DEVICE_NAME],
        profile=entry.data[CONF_PROFILE],
        host=entry.data["host"],
        port=entry.data["port"],
        slave_id=entry.data[CONF_SLAVE_ID],
        scan_interval=_get("scan_interval", DEFAULT_SCAN_INTERVAL),
        offline_scan_interval=_get(CONF_OFFLINE_SCAN_INTERVAL, DEFAULT_OFFLINE_SCAN_INTERVAL),
        timeout=_get("timeout", DEFAULT_TIMEOUT),
        invert_grid_power=_get(CONF_INVERT_GRID_POWER, False),
        invert_battery_power=_get(CONF_INVERT_BATTERY_POWER, False),
        # Which entities exist depends on this one, so it comes from
        # entry.data (set in the config/reconfigure flow) rather than
        # options - changing it recreates the entity set.
        protocol_v201=entry.data.get(CONF_PROTOCOL_V201, False),
        block_size=BLOCK_SIZE_OPTIONS.get(_get(CONF_BLOCK_SIZE, DEFAULT_BLOCK_SIZE), 0),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: GrowattLocalCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown_client()
    return unload_ok
