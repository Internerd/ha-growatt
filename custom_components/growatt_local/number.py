"""Number platform for Growatt Local - the two power-limiting controls."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_DEVICE_NAME, CONF_PROFILE, DOMAIN, PROFILE_MIC, PROFILE_SPH_TL3
from .coordinator import GrowattLocalCoordinator

# (register_key, entity_id_suffix, name, min, max, step, icon)
NUMBER_DEFINITIONS = {
    PROFILE_MIC: [
        ("max_output_power_rate", "max_output_power_rate", "Max Output Power Rate", 0, 100, 1, "mdi:speedometer"),
    ],
    PROFILE_SPH_TL3: [
        ("export_limit_power", "vpp_export_limit_power_rate", "VPP Export Limit Power Rate", 0, 100, 0.1, "mdi:transmission-tower-export"),
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GrowattLocalCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_slug = slugify(config_entry.data[CONF_DEVICE_NAME])
    definitions = NUMBER_DEFINITIONS.get(config_entry.data[CONF_PROFILE], [])

    entities = [
        GrowattPowerRateNumber(coordinator, config_entry, device_slug, *definition)
        for definition in definitions
    ]
    async_add_entities(entities)


class GrowattPowerRateNumber(CoordinatorEntity, NumberEntity):
    """A writable percentage-based power-limiting control."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: GrowattLocalCoordinator,
        config_entry: ConfigEntry,
        device_slug: str,
        register_key: str,
        suffix: str,
        name: str,
        min_value: float,
        max_value: float,
        step: float,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._register_key = register_key

        self.entity_id = f"number.{device_slug}_{suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{suffix}"
        self._attr_name = name
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_icon = icon

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
        await self.coordinator.async_write_percent(self._register_key, value)
