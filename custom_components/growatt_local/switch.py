"""Switch platform for Growatt Local - boolean holding-register controls.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_DEVICE_NAME, CONF_PROFILE, DOMAIN, display_name, entity_suffix
from .coordinator import GrowattLocalCoordinator, PROFILE_REGISTER_MAPS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GrowattLocalCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_slug = slugify(config_entry.data[CONF_DEVICE_NAME])
    holding_registers = PROFILE_REGISTER_MAPS[config_entry.data[CONF_PROFILE]]["holding_registers"]

    entities = [
        GrowattSwitch(coordinator, config_entry, device_slug, register_key, meta)
        for register_key, meta in holding_registers.items()
        if meta.get("control_type") == "switch"
    ]
    async_add_entities(entities)


class GrowattSwitch(CoordinatorEntity, SwitchEntity):
    """A writable on/off holding register."""

    _attr_has_entity_name = True

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
        self.entity_id = f"switch.{device_slug}_{suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{suffix}"
        self._attr_name = display_name(meta["name"])
        self._attr_entity_registry_enabled_default = meta.get("enabled_default", True)

    @property
    def device_info(self):
        return self.coordinator.get_device_info()

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self._register_key)
        if value is None:
            return None
        return bool(value)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.is_online

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_switch(self._register_key, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_switch(self._register_key, False)
