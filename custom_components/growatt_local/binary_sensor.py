"""Binary sensor platform for Growatt Local.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_DEVICE_NAME, DOMAIN
from .coordinator import GrowattLocalCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GrowattLocalCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_slug = slugify(config_entry.data[CONF_DEVICE_NAME])
    async_add_entities([GrowattInverterOnlineSensor(coordinator, config_entry, device_slug)])


class GrowattInverterOnlineSensor(CoordinatorEntity, BinarySensorEntity):
    """Whether the inverter is currently responding on Modbus."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:solar-power-variant"

    def __init__(
        self,
        coordinator: GrowattLocalCoordinator,
        config_entry: ConfigEntry,
        device_slug: str,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self.entity_id = f"binary_sensor.{device_slug}_inverter_online"
        self._attr_unique_id = f"{config_entry.entry_id}_inverter_online"
        self._attr_name = "Inverter Online"

    @property
    def device_info(self):
        return self.coordinator.get_device_info()

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_online

    @property
    def extra_state_attributes(self):
        if self.coordinator.last_successful_update is None:
            return None
        return {"last_successful_update": self.coordinator.last_successful_update.isoformat()}
