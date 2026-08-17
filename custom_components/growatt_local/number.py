"""Number platform for Growatt Local - RW percentage/SOC-style holding registers.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    CONF_DEVICE_NAME,
    CONF_PROFILE,
    CONF_PROTOCOL_V201,
    DOMAIN,
    display_name,
    entity_suffix,
)
from .coordinator import GrowattLocalCoordinator, register_map_for

ICONS = {
    "export_limit_power": "mdi:speedometer",
    "vpp_export_limit_power_rate": "mdi:transmission-tower-export",
    "max_output_power_rate": "mdi:speedometer",
    "load_first_battery_minimum_soc": "mdi:battery-sync",
    "discharge_power_rate": "mdi:battery-minus",
    "discharge_stopped_soc": "mdi:battery-arrow-down",
    "charge_power_rate": "mdi:battery-plus",
    "charge_stopped_soc": "mdi:battery-arrow-up",
    "dry_contact_on_rate": "mdi:electric-switch",
    "dry_contact_off_rate": "mdi:electric-switch",
    "reactive_power_rate": "mdi:sine-wave",
    "power_factor": "mdi:angle-acute",
    "export_limit_failed_power_rate": "mdi:transmission-tower-export",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GrowattLocalCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_slug = slugify(config_entry.data[CONF_DEVICE_NAME])
    maps = register_map_for(
        config_entry.data[CONF_PROFILE],
        config_entry.data.get(CONF_PROTOCOL_V201, False),
    )

    entities = [
        GrowattNumber(coordinator, config_entry, device_slug, register_key, meta)
        for register_key, meta in maps["holding_registers"].items()
        if meta.get("control_type") == "number"
    ]
    async_add_entities(entities)


class GrowattNumber(CoordinatorEntity, NumberEntity):
    """A writable numeric (percentage/SOC/rate) holding register."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GrowattLocalCoordinator,
        config_entry: ConfigEntry,
        device_slug: str,
        register_key: str,
        meta: dict,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._register_key = meta["name"]

        suffix = entity_suffix(meta["name"])
        self.entity_id = f"number.{device_slug}_{suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{suffix}"
        self._attr_name = display_name(meta["name"])
        self._attr_native_min_value = meta.get("min", 0)
        self._attr_native_max_value = meta.get("max", 100)
        self._attr_native_step = meta.get("scale", 1)
        self._attr_native_unit_of_measurement = meta.get("unit") or None
        if self._attr_native_unit_of_measurement == "%":
            self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = ICONS.get(meta["name"], "mdi:tune")
        self._attr_entity_registry_enabled_default = meta.get("enabled_default", True)

    @property
    def device_info(self):
        return self.coordinator.get_device_info()

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._register_key)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.is_online

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_scaled(self._register_key, value)
