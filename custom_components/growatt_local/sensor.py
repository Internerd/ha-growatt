"""Sensor platform for Growatt Local.

Entity IDs are pinned explicitly (rather than left to Home Assistant's
automatic slug-from-name behaviour) so that, given the same device name the
old "Growatt_ModbusTCP" integration entries used, this integration reproduces
the exact same entity_ids - keeping existing helpers, automations and
dashboards working without any changes.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfApparentPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    CONF_DEVICE_NAME,
    CONF_PROFILE,
    DOMAIN,
    FAULT_CODE_TEXT,
    PROFILE_MIC,
    PROFILE_SPH_TL3,
    WARNING_CODE_TEXT,
    display_name,
    entity_suffix,
)
from .coordinator import GrowattLocalCoordinator, PROFILE_REGISTER_MAPS

VALUE_MAPS = {
    "dry_contact_state": {0: "Off", 1: "On"},
}

# Each entry: (register_key, entity_id_suffix, name, device_class, state_class, unit, icon)
SPH_TL3_SENSORS: list[tuple[str, str, str, Any, Any, Any, str]] = [
    ("inverter_status", "status", "Status", None, None, None, "mdi:information-outline"),
    ("pv_total_power", "solar_total_power", "Solar Total Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:solar-power"),
    ("pv1_voltage", "pv1_voltage", "PV1 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:solar-panel"),
    ("pv1_current", "pv1_current", "PV1 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:solar-panel"),
    ("pv1_power", "pv1_power", "PV1 Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:solar-panel"),
    ("pv2_voltage", "pv2_voltage", "PV2 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:solar-panel"),
    ("pv2_current", "pv2_current", "PV2 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:solar-panel"),
    ("pv2_power", "pv2_power", "PV2 Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:solar-panel"),
    ("pv3_voltage", "pv3_voltage", "PV3 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:solar-panel"),
    ("pv3_current", "pv3_current", "PV3 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:solar-panel"),
    ("pv3_power", "pv3_power", "PV3 Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:solar-panel"),
    ("ac_frequency", "ac_frequency", "AC Frequency", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, UnitOfFrequency.HERTZ, "mdi:sine-wave"),
    ("ac_voltage_r", "ac_voltage_r", "AC Voltage R", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:lightning-bolt"),
    ("ac_current_r", "ac_current_r", "AC Current R", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:current-ac"),
    ("ac_power_r", "ac_power_r", "AC Power R", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:power-plug"),
    ("ac_voltage_s", "ac_voltage_s", "AC Voltage S", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:lightning-bolt"),
    ("ac_current_s", "ac_current_s", "AC Current S", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:current-ac"),
    ("ac_power_s", "ac_power_s", "AC Power S", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:power-plug"),
    ("ac_voltage_t", "ac_voltage_t", "AC Voltage T", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:lightning-bolt"),
    ("ac_current_t", "ac_current_t", "AC Current T", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:current-ac"),
    ("ac_power_t", "ac_power_t", "AC Power T", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:power-plug"),
    ("energy_today", "energy_today", "Energy Today", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:calendar-today"),
    ("energy_total", "energy_total", "Energy Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:counter"),
    ("pv1_energy_today", "pv1_energy_today", "PV1 Energy Today", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:solar-panel"),
    ("pv1_energy_total", "pv1_energy_total", "PV1 Energy Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:solar-panel"),
    ("pv2_energy_today", "pv2_energy_today", "PV2 Energy Today", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:solar-panel"),
    ("pv2_energy_total", "pv2_energy_total", "PV2 Energy Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:solar-panel"),
    ("pv_energy_total", "pv_energy_total", "PV Energy Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:solar-panel"),
    ("inverter_temp", "inverter_temperature", "Inverter Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:thermometer"),
    ("fault_code", "fault_code", "Fault Code", None, None, None, "mdi:alert-circle-outline"),
    ("warning_code", "warning_code", "Warning Code", None, None, None, "mdi:alert-outline"),
    ("battery_discharge_power", "battery_discharge_power", "Battery Discharge Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:battery-minus"),
    ("battery_charge_power", "battery_charge_power", "Battery Charge Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:battery-plus"),
    ("battery_voltage", "battery_voltage", "Battery Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:battery"),
    ("battery_soc", "battery_soc", "Battery SOC", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, PERCENTAGE, "mdi:battery-high"),
    ("battery_temp", "battery_temperature", "Battery Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:thermometer"),
    ("power_to_user", "power_to_user", "Power to User", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:home-import-outline"),
    ("power_to_grid", "power_to_grid", "Power to Grid", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:transmission-tower-export"),
    ("power_to_load", "power_to_load", "Power to Load", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:home-lightning-bolt"),
    ("self_consumption_percentage", "self_consumption_percentage", "Self Consumption Percentage", None, SensorStateClass.MEASUREMENT, PERCENTAGE, "mdi:percent"),
    ("energy_to_user_today", "energy_to_user_today", "Energy to User Today", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:home-import-outline"),
    ("energy_to_user_total", "energy_to_user_total", "Energy to User Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:home-import-outline"),
    ("energy_to_grid_today", "energy_to_grid_today", "Energy to Grid Today", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:transmission-tower-export"),
    ("energy_to_grid_total", "energy_to_grid_total", "Energy to Grid Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:transmission-tower-export"),
    ("discharge_energy_today", "discharge_energy_today", "Discharge Energy Today", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:battery-minus"),
    ("discharge_energy_total", "discharge_energy_total", "Discharge Energy Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:battery-minus"),
    ("charge_energy_today", "charge_energy_today", "Charge Energy Today", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:battery-plus"),
    ("charge_energy_total", "charge_energy_total", "Charge Energy Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:battery-plus"),
    ("load_energy_today", "load_energy_today", "Load Energy Today", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:home-lightning-bolt"),
    ("load_energy_total", "load_energy_total", "Load Energy Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:home-lightning-bolt"),
    ("dry_contact_state", "dry_contact_state", "Dry Contact State", None, None, None, "mdi:electric-switch"),
]

SPH_TL3_DIAGNOSTIC_DEFAULT_ENABLED = {"dry_contact_state": False}

MIC_SENSORS: list[tuple[str, str, str, Any, Any, Any, str]] = [
    ("inverter_status", "status", "Status", None, None, None, "mdi:information-outline"),
    ("pv1_voltage", "pv1_voltage", "PV1 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:solar-panel"),
    ("pv1_current", "pv1_current", "PV1 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:solar-panel"),
    ("pv1_power", "pv1_power", "PV1 Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:solar-panel"),
    ("ac_power", "ac_power", "AC Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:power-plug"),
    ("ac_frequency", "ac_frequency", "AC Frequency", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, UnitOfFrequency.HERTZ, "mdi:sine-wave"),
    ("ac_voltage", "ac_voltage", "AC Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:lightning-bolt"),
    ("ac_current", "ac_current", "AC Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:current-ac"),
    ("ac_apparent_power", "ac_apparent_power", "AC Apparent Power", SensorDeviceClass.APPARENT_POWER, SensorStateClass.MEASUREMENT, UnitOfApparentPower.VOLT_AMPERE, "mdi:power-plug"),
    ("energy_today", "energy_today", "Energy Today", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:calendar-today"),
    ("energy_total", "energy_total", "Energy Total", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:counter"),
    ("inverter_temp", "inverter_temperature", "Inverter Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:thermometer"),
    ("ipm_temp", "ipm_temperature", "IPM Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:thermometer"),
    ("fault_code", "fault_code", "Fault Code", None, None, None, "mdi:alert-circle-outline"),
    ("warning_code", "warning_code", "Warning Code", None, None, None, "mdi:alert-outline"),
]

SENSOR_DEFINITIONS = {
    PROFILE_SPH_TL3: SPH_TL3_SENSORS,
    PROFILE_MIC: MIC_SENSORS,
}

DIAGNOSTIC_SUFFIXES = {"status", "fault_code", "warning_code", "dry_contact_state"}

# (register_key, suffix, name, device_class, state_class, unit, icon) tuples
# for the fixed sensor list, or None below - the diagnostic holding
# registers (control_type == "diagnostic") are added dynamically per
# profile since they're pure passthroughs of the register map.


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GrowattLocalCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_slug = slugify(config_entry.data[CONF_DEVICE_NAME])
    profile = config_entry.data[CONF_PROFILE]
    definitions = SENSOR_DEFINITIONS[profile]
    enabled_overrides = {PROFILE_SPH_TL3: SPH_TL3_DIAGNOSTIC_DEFAULT_ENABLED}.get(profile, {})

    entities = [
        GrowattSensor(
            coordinator, config_entry, device_slug, *definition,
            enabled_default=enabled_overrides.get(definition[0], True),
        )
        for definition in definitions
    ]

    holding_registers = PROFILE_REGISTER_MAPS[profile]["holding_registers"]
    for register_key, meta in holding_registers.items():
        if meta.get("control_type") != "diagnostic":
            continue
        suffix = entity_suffix(meta["name"])
        entities.append(
            GrowattSensor(
                coordinator, config_entry, device_slug,
                meta["name"], suffix, display_name(meta["name"]),
                None, None, None, "mdi:cog-outline",
                enabled_default=meta.get("enabled_default", True),
                is_diagnostic=True,
            )
        )

    async_add_entities(entities)


class GrowattSensor(CoordinatorEntity, SensorEntity):
    """A single register-backed sensor with a pinned entity_id."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GrowattLocalCoordinator,
        config_entry: ConfigEntry,
        device_slug: str,
        register_key: str,
        suffix: str,
        name: str,
        device_class: Any,
        state_class: Any,
        unit: Any,
        icon: str,
        enabled_default: bool = True,
        is_diagnostic: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._register_key = register_key
        self._value_map = VALUE_MAPS.get(register_key)

        self.entity_id = f"sensor.{device_slug}_{suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{suffix}"
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_entity_registry_enabled_default = enabled_default
        if is_diagnostic or suffix in DIAGNOSTIC_SUFFIXES:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_info(self):
        return self.coordinator.get_device_info()

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(self._register_key)
        if raw is None:
            return None
        if self._value_map is not None:
            return self._value_map.get(raw, raw)
        return raw

    @property
    def extra_state_attributes(self):
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(self._register_key)
        if raw is None:
            return None
        if self._register_key == "fault_code":
            return {"description": FAULT_CODE_TEXT.get(raw, f"Code {raw} - see inverter display/manual")}
        if self._register_key == "warning_code":
            return {"description": WARNING_CODE_TEXT.get(raw, f"Code {raw} - see inverter display/manual")}
        return None

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.is_online
