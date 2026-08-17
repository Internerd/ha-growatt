"""Time platform for Growatt Local - time-of-use scheduling windows.

Only the SPH-TL3 profile has these; the MIC profile has an empty
time_windows list, so no entities are created for it.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_DEVICE_NAME, DOMAIN
from .coordinator import GrowattLocalCoordinator, unpack_time


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GrowattLocalCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_slug = slugify(config_entry.data[CONF_DEVICE_NAME])

    entities: list[GrowattTimeEntity] = []
    for label, suffix, start_reg, end_reg, _enable_reg, enabled_default in coordinator.time_windows:
        entities.append(
            GrowattTimeEntity(coordinator, config_entry, device_slug, suffix, "start", f"{label} Start", start_reg, enabled_default)
        )
        entities.append(
            GrowattTimeEntity(coordinator, config_entry, device_slug, suffix, "end", f"{label} End", end_reg, enabled_default)
        )
    # The enable flag that goes with each window lives on the select
    # platform (see SPH_TL3_HOLDING_REGISTERS); a window with both times set
    # but its flag off is inert.
    async_add_entities(entities)


class GrowattTimeEntity(CoordinatorEntity, TimeEntity):
    """One half (start or end) of a time-of-use scheduling window."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-time-four-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GrowattLocalCoordinator,
        config_entry: ConfigEntry,
        device_slug: str,
        suffix: str,
        edge: str,
        name: str,
        register_address: int,
        enabled_default: bool,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._data_key = f"{suffix}_{edge}_raw"
        self._register_address = register_address

        entity_suffix = f"{suffix}_{edge}"
        self.entity_id = f"time.{device_slug}_{entity_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{entity_suffix}"
        self._attr_name = name
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def device_info(self):
        return self.coordinator.get_device_info()

    @property
    def native_value(self) -> dt_time | None:
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(self._data_key)
        if raw is None:
            return None
        hour, minute = unpack_time(int(raw))
        if hour > 23 or minute > 59:
            return None
        return dt_time(hour=hour, minute=minute)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.is_online

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_write_time_register(self._register_address, value.hour, value.minute)
