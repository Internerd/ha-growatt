"""Select platform for Growatt Local - holding registers with fixed options.

Growatt's "boolean" registers are modelled as selects rather than switches,
matching the Growatt_ModbusTCP integration. That is not cosmetic: several of
them are not boolean at all (export limit mode has four values, AC charge
enable has three on some firmwares), and the entity_ids and states that
existing automations use are `select.<device>_<control>` with values
"Enabled"/"Disabled".

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
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
    "on_off": "mdi:power",
    "system_enable": "mdi:power",
    "ac_charge_enable": "mdi:transmission-tower-import",
    "export_limit_mode": "mdi:transmission-tower-export",
    "vpp_export_limit_enable": "mdi:transmission-tower-export",
    "control_authority": "mdi:shield-key-outline",
    "dry_contact_enable": "mdi:electric-switch",
    "pf_cmd_memory": "mdi:memory",
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

    async_add_entities(
        GrowattSelect(coordinator, config_entry, device_slug, meta)
        for meta in maps["holding_registers"].values()
        if meta.get("control_type") == "select"
    )


class GrowattSelect(CoordinatorEntity, SelectEntity):
    """A writable holding register with a fixed set of values."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GrowattLocalCoordinator,
        config_entry: ConfigEntry,
        device_slug: str,
        meta: dict,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._register_key = meta["name"]
        self._value_to_option: dict[int, str] = dict(meta["options"])
        self._option_to_value = {label: value for value, label in self._value_to_option.items()}

        suffix = entity_suffix(meta["name"])
        self.entity_id = f"select.{device_slug}_{suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{suffix}"
        self._attr_name = display_name(meta["name"])
        self._attr_options = list(self._value_to_option.values())
        self._attr_icon = ICONS.get(meta["name"], "mdi:form-dropdown")
        self._attr_entity_registry_enabled_default = meta.get("enabled_default", True)

    @property
    def device_info(self):
        return self.coordinator.get_device_info()

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(self._register_key)
        if raw is None:
            return None
        # An undocumented value must not be reported as a valid option -
        # Home Assistant logs and drops states outside the option list.
        return self._value_to_option.get(int(raw))

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.is_online

    async def async_select_option(self, option: str) -> None:
        value = self._option_to_value.get(option)
        if value is None:
            return
        await self.coordinator.async_write_raw(self._register_key, value)
