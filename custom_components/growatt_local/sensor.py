"""Sensor platform for Growatt Local.

Entity IDs are pinned explicitly (rather than left to Home Assistant's
automatic slug-from-name behaviour) so that, given the same device name the
"Growatt_ModbusTCP" integration entries used, this integration reproduces the
exact same entity_ids - keeping existing helpers, automations and dashboards
working without any changes.

The suffixes below are not guesses. Upstream builds each entity_id from the
sensor's *display* name, not its register key, and the two differ for a
handful of sensors - "AC Current Phase R" rather than "ac_current_r",
"Battery Charge Today" rather than "charge_energy_today", "Battery State of
Health" rather than "bms_soh". Each suffix here was checked against a live
Growatt_ModbusTCP install.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

from typing import Any, NamedTuple

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    CONF_DEVICE_NAME,
    CONF_PROFILE,
    CONF_PROTOCOL_V201,
    DERATING_CODES,
    DOMAIN,
    FAULT_CODE_TEXT,
    PRIORITY_MODES,
    PROFILE_MIC,
    PROFILE_SPH_TL3,
    PROFILE_STATUS_CODES,
    WARNING_CODE_TEXT,
    display_name,
    entity_suffix,
)
from .coordinator import GrowattLocalCoordinator, register_map_for

POWER = SensorDeviceClass.POWER
ENERGY = SensorDeviceClass.ENERGY
VOLTAGE = SensorDeviceClass.VOLTAGE
CURRENT = SensorDeviceClass.CURRENT
TEMPERATURE = SensorDeviceClass.TEMPERATURE
MEASUREMENT = SensorStateClass.MEASUREMENT
TOTAL_INCREASING = SensorStateClass.TOTAL_INCREASING
WATT = UnitOfPower.WATT
KWH = UnitOfEnergy.KILO_WATT_HOUR
VOLT = UnitOfElectricPotential.VOLT
AMPERE = UnitOfElectricCurrent.AMPERE
CELSIUS = UnitOfTemperature.CELSIUS


class SensorDef(NamedTuple):
    """One register (or derived value) exposed as a sensor entity."""

    key: str
    suffix: str
    name: str
    device_class: Any = None
    state_class: Any = None
    unit: Any = None
    icon: str = "mdi:information-outline"
    enabled_default: bool = True
    diagnostic: bool = False


# Sensors shared by every profile.
_COMMON_SENSORS = [
    SensorDef("inverter_status", "status", "Status", icon="mdi:information-outline", diagnostic=True),
    SensorDef("last_update", "last_update", "Last Update", SensorDeviceClass.TIMESTAMP,
              icon="mdi:clock-check-outline", diagnostic=True),
    SensorDef("derating_mode", "derating_mode", "Derating Mode", icon="mdi:speedometer-slow", diagnostic=True),
    SensorDef("fault_code", "fault_code", "Fault Code", icon="mdi:alert-circle-outline", diagnostic=True),
    SensorDef("warning_code", "warning_code", "Warning Code", icon="mdi:alert-outline", diagnostic=True),
]

SPH_TL3_SENSORS: list[SensorDef] = [
    *_COMMON_SENSORS,

    # --- Solar ---
    SensorDef("pv_total_power", "solar_total_power", "Solar Total Power", POWER, MEASUREMENT, WATT, "mdi:solar-power"),
    SensorDef("pv1_voltage", "pv1_voltage", "PV1 Voltage", VOLTAGE, MEASUREMENT, VOLT, "mdi:lightning-bolt"),
    SensorDef("pv1_current", "pv1_current", "PV1 Current", CURRENT, MEASUREMENT, AMPERE, "mdi:current-dc"),
    SensorDef("pv1_power", "pv1_power", "PV1 Power", POWER, MEASUREMENT, WATT, "mdi:solar-panel"),
    SensorDef("pv2_voltage", "pv2_voltage", "PV2 Voltage", VOLTAGE, MEASUREMENT, VOLT, "mdi:lightning-bolt"),
    SensorDef("pv2_current", "pv2_current", "PV2 Current", CURRENT, MEASUREMENT, AMPERE, "mdi:current-dc"),
    SensorDef("pv2_power", "pv2_power", "PV2 Power", POWER, MEASUREMENT, WATT, "mdi:solar-panel"),
    # PV3 exists only on 3-MPPT variants. Off by default so 2-string
    # hardware does not gain three entities that read a permanent zero.
    SensorDef("pv3_voltage", "pv3_voltage", "PV3 Voltage", VOLTAGE, MEASUREMENT, VOLT, "mdi:lightning-bolt", enabled_default=False),
    SensorDef("pv3_current", "pv3_current", "PV3 Current", CURRENT, MEASUREMENT, AMPERE, "mdi:current-dc", enabled_default=False),
    SensorDef("pv3_power", "pv3_power", "PV3 Power", POWER, MEASUREMENT, WATT, "mdi:solar-panel", enabled_default=False),

    # --- AC output, three phase ---
    SensorDef("ac_frequency", "ac_frequency", "AC Frequency", SensorDeviceClass.FREQUENCY, MEASUREMENT, UnitOfFrequency.HERTZ, "mdi:sine-wave"),
    SensorDef("ac_voltage_r", "ac_voltage_r", "AC Voltage R", VOLTAGE, MEASUREMENT, VOLT, "mdi:lightning-bolt"),
    SensorDef("ac_voltage_s", "ac_voltage_s", "AC Voltage S", VOLTAGE, MEASUREMENT, VOLT, "mdi:lightning-bolt"),
    SensorDef("ac_voltage_t", "ac_voltage_t", "AC Voltage T", VOLTAGE, MEASUREMENT, VOLT, "mdi:lightning-bolt"),
    SensorDef("ac_current_r", "ac_current_phase_r", "AC Current Phase R", CURRENT, MEASUREMENT, AMPERE, "mdi:current-ac"),
    SensorDef("ac_current_s", "ac_current_phase_s", "AC Current Phase S", CURRENT, MEASUREMENT, AMPERE, "mdi:current-ac"),
    SensorDef("ac_current_t", "ac_current_phase_t", "AC Current Phase T", CURRENT, MEASUREMENT, AMPERE, "mdi:current-ac"),
    SensorDef("ac_power_r", "ac_power_phase_r", "AC Power Phase R", POWER, MEASUREMENT, WATT, "mdi:power-plug"),
    SensorDef("ac_power_s", "ac_power_phase_s", "AC Power Phase S", POWER, MEASUREMENT, WATT, "mdi:power-plug"),
    SensorDef("ac_power_t", "ac_power_phase_t", "AC Power Phase T", POWER, MEASUREMENT, WATT, "mdi:power-plug"),

    # --- Production energy ---
    SensorDef("energy_today", "energy_today", "Energy Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:calendar-today"),
    SensorDef("energy_total", "energy_total", "Energy Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:counter"),
    SensorDef("pv_energy_total", "pv_energy_total", "PV Energy Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:solar-panel"),
    SensorDef("pv1_energy_today", "pv1_energy_today", "PV1 Energy Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:solar-panel", enabled_default=False),
    SensorDef("pv1_energy_total", "pv1_energy_total", "PV1 Energy Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:solar-panel", enabled_default=False),
    SensorDef("pv2_energy_today", "pv2_energy_today", "PV2 Energy Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:solar-panel", enabled_default=False),
    SensorDef("pv2_energy_total", "pv2_energy_total", "PV2 Energy Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:solar-panel", enabled_default=False),
    SensorDef("pv3_energy_today", "pv3_energy_today", "PV3 Energy Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:solar-panel", enabled_default=False),

    # --- Grid ---
    SensorDef("grid_power", "grid_power", "Grid Power", POWER, MEASUREMENT, WATT, "mdi:transmission-tower"),
    SensorDef("grid_export_power", "grid_export_power", "Grid Export Power", POWER, MEASUREMENT, WATT, "mdi:transmission-tower-export"),
    SensorDef("grid_import_power", "grid_import_power", "Grid Import Power", POWER, MEASUREMENT, WATT, "mdi:transmission-tower-import"),
    SensorDef("power_to_grid", "power_to_grid", "Power to Grid", POWER, MEASUREMENT, WATT, "mdi:transmission-tower-export"),
    SensorDef("power_to_user", "power_to_user", "Power to User", POWER, MEASUREMENT, WATT, "mdi:transmission-tower-import"),
    SensorDef("power_to_load", "power_to_load", "Power to Load", POWER, MEASUREMENT, WATT, "mdi:home-lightning-bolt"),
    SensorDef("energy_to_grid_today", "energy_to_grid_today", "Energy to Grid Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:transmission-tower-export"),
    SensorDef("energy_to_grid_total", "energy_to_grid_total", "Energy to Grid Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:transmission-tower-export"),
    SensorDef("energy_to_user_today", "grid_import_energy_today", "Grid Import Energy Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:transmission-tower-import"),
    SensorDef("energy_to_user_total", "grid_import_energy_total", "Grid Import Energy Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:transmission-tower-import"),
    # Net grid energy (export - import). Deliberately carries no energy
    # device class: the value is signed and falls as the house imports, and
    # an `energy` sensor that decreases is rejected by the statistics engine
    # and unusable on the Energy Dashboard. The directional counters above
    # are the ones to feed into it.
    SensorDef("grid_energy_today", "grid_energy_today", "Grid Energy Today", None, MEASUREMENT, KWH, "mdi:transmission-tower"),
    SensorDef("grid_energy_total", "grid_energy_total", "Grid Energy Total", None, MEASUREMENT, KWH, "mdi:transmission-tower"),

    # --- Consumption ---
    SensorDef("house_consumption", "house_consumption", "House Consumption", POWER, MEASUREMENT, WATT, "mdi:home-lightning-bolt"),
    SensorDef("self_consumption", "self_consumption", "Self Consumption", POWER, MEASUREMENT, WATT, "mdi:home-battery"),
    SensorDef("self_consumption_percentage", "self_consumption_percentage", "Self Consumption Percentage", None, MEASUREMENT, PERCENTAGE, "mdi:percent"),
    SensorDef("load_energy_today", "load_energy_today", "Load Energy Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:home-lightning-bolt"),
    SensorDef("load_energy_total", "load_energy_total", "Load Energy Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:home-lightning-bolt"),

    # --- Battery ---
    SensorDef("battery_power", "battery_power", "Battery Power", POWER, MEASUREMENT, WATT, "mdi:battery-charging"),
    SensorDef("battery_charge_power", "battery_charge_power", "Battery Charge Power", POWER, MEASUREMENT, WATT, "mdi:battery-plus"),
    SensorDef("battery_discharge_power", "battery_discharge_power", "Battery Discharge Power", POWER, MEASUREMENT, WATT, "mdi:battery-minus"),
    SensorDef("battery_voltage", "battery_voltage", "Battery Voltage", VOLTAGE, MEASUREMENT, VOLT, "mdi:battery"),
    # Only the V2.01 register range carries a battery current.
    SensorDef("battery_current", "battery_current", "Battery Current", CURRENT, MEASUREMENT, AMPERE, "mdi:current-dc"),
    SensorDef("battery_soc", "battery_soc", "Battery SOC", SensorDeviceClass.BATTERY, MEASUREMENT, PERCENTAGE, "mdi:battery-high"),
    SensorDef("battery_temp", "battery_temperature", "Battery Temperature", TEMPERATURE, MEASUREMENT, CELSIUS, "mdi:thermometer"),
    SensorDef("charge_energy_today", "battery_charge_today", "Battery Charge Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:battery-plus"),
    SensorDef("charge_energy_total", "battery_charge_total", "Battery Charge Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:battery-plus"),
    SensorDef("discharge_energy_today", "battery_discharge_today", "Battery Discharge Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:battery-minus"),
    SensorDef("discharge_energy_total", "battery_discharge_total", "Battery Discharge Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:battery-minus"),
    SensorDef("bms_soh", "battery_state_of_health", "Battery State of Health", None, MEASUREMENT, PERCENTAGE, "mdi:battery-heart"),
    SensorDef("ac_charge_energy_total", "ac_charge_energy_total", "AC Charge Energy Total", ENERGY, TOTAL_INCREASING,
              KWH, "mdi:transmission-tower-import", enabled_default=False),
    SensorDef("bms_status", "bms_status", "BMS Status", icon="mdi:battery-heart-variant", diagnostic=True),
    SensorDef("bms_error", "bms_error", "BMS Error", icon="mdi:battery-alert-variant-outline", diagnostic=True),
    SensorDef("bms_cycle_count", "bms_cycle_count", "BMS Cycle Count", None, TOTAL_INCREASING, None, "mdi:battery-sync", diagnostic=True),

    # --- Misc diagnostics ---
    SensorDef("dry_contact_state", "dry_contact_state", "Dry Contact State", icon="mdi:electric-switch",
              enabled_default=False, diagnostic=True),
    SensorDef("inverter_temp", "inverter_temperature", "Inverter Temperature", TEMPERATURE, MEASUREMENT, CELSIUS, "mdi:thermometer"),
    SensorDef("ipm_temp", "ipm_temperature", "IPM Temperature", TEMPERATURE, MEASUREMENT, CELSIUS, "mdi:thermometer"),
    SensorDef("boost_temp", "boost_temperature", "Boost Temperature", TEMPERATURE, MEASUREMENT, CELSIUS, "mdi:thermometer"),
]

MIC_SENSORS: list[SensorDef] = [
    *_COMMON_SENSORS,

    SensorDef("pv_total_power", "solar_total_power", "Solar Total Power", POWER, MEASUREMENT, WATT, "mdi:solar-power"),
    SensorDef("pv1_voltage", "pv1_voltage", "PV1 Voltage", VOLTAGE, MEASUREMENT, VOLT, "mdi:lightning-bolt"),
    SensorDef("pv1_current", "pv1_current", "PV1 Current", CURRENT, MEASUREMENT, AMPERE, "mdi:current-dc"),
    SensorDef("pv1_power", "pv1_power", "PV1 Power", POWER, MEASUREMENT, WATT, "mdi:solar-panel"),

    SensorDef("ac_power", "ac_power", "AC Power", POWER, MEASUREMENT, WATT, "mdi:power-plug"),
    SensorDef("ac_frequency", "ac_frequency", "AC Frequency", SensorDeviceClass.FREQUENCY, MEASUREMENT, UnitOfFrequency.HERTZ, "mdi:sine-wave"),
    SensorDef("ac_voltage", "ac_voltage", "AC Voltage", VOLTAGE, MEASUREMENT, VOLT, "mdi:lightning-bolt"),
    SensorDef("ac_current", "ac_current", "AC Current", CURRENT, MEASUREMENT, AMPERE, "mdi:current-ac"),
    SensorDef("ac_apparent_power", "ac_apparent_power", "AC Apparent Power", SensorDeviceClass.APPARENT_POWER,
              MEASUREMENT, UnitOfApparentPower.VOLT_AMPERE, "mdi:power-plug"),

    SensorDef("energy_today", "energy_today", "Energy Today", ENERGY, TOTAL_INCREASING, KWH, "mdi:calendar-today"),
    SensorDef("energy_total", "energy_total", "Energy Total", ENERGY, TOTAL_INCREASING, KWH, "mdi:counter"),
    # Lifetime grid-connected hours (registers 30/31, half-hour units).
    SensorDef("time_total", "total_operating_time", "Total Operating Time", SensorDeviceClass.DURATION,
              TOTAL_INCREASING, UnitOfTime.HOURS, "mdi:timer-outline", enabled_default=False, diagnostic=True),

    SensorDef("inverter_temp", "inverter_temperature", "Inverter Temperature", TEMPERATURE, MEASUREMENT, CELSIUS, "mdi:thermometer"),
    SensorDef("ipm_temp", "ipm_temperature", "IPM Temperature", TEMPERATURE, MEASUREMENT, CELSIUS, "mdi:thermometer"),
]

SENSOR_DEFINITIONS = {
    PROFILE_SPH_TL3: SPH_TL3_SENSORS,
    PROFILE_MIC: MIC_SENSORS,
}

# Values rendered as text rather than the raw register number.
VALUE_MAPS = {
    "dry_contact_state": {0: "Off", 1: "On"},
    "derating_mode": DERATING_CODES,
    "priority_mode": PRIORITY_MODES,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GrowattLocalCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_slug = slugify(config_entry.data[CONF_DEVICE_NAME])
    profile = config_entry.data[CONF_PROFILE]

    entities = [
        GrowattSensor(coordinator, config_entry, device_slug, definition)
        for definition in SENSOR_DEFINITIONS[profile]
    ]

    # Read-only holding registers are pure passthroughs of the register map,
    # so they are generated rather than listed.
    maps = register_map_for(profile, config_entry.data.get(CONF_PROTOCOL_V201, False))
    for meta in maps["holding_registers"].values():
        if meta.get("control_type") != "diagnostic":
            continue
        key = meta["name"]
        entities.append(
            GrowattSensor(
                coordinator,
                config_entry,
                device_slug,
                SensorDef(
                    key,
                    entity_suffix(key),
                    display_name(key),
                    icon="mdi:cog-outline",
                    enabled_default=meta.get("enabled_default", True),
                    diagnostic=True,
                ),
            )
        )

    async_add_entities(entities)


class GrowattSensor(CoordinatorEntity, SensorEntity):
    """A single register-backed (or derived) sensor with a pinned entity_id."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GrowattLocalCoordinator,
        config_entry: ConfigEntry,
        device_slug: str,
        definition: SensorDef,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._definition = definition
        self._register_key = definition.key
        self._value_map = VALUE_MAPS.get(definition.key)
        self._status_codes = PROFILE_STATUS_CODES[config_entry.data[CONF_PROFILE]]

        self.entity_id = f"sensor.{device_slug}_{definition.suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{definition.suffix}"
        self._attr_name = definition.name
        self._attr_device_class = definition.device_class
        self._attr_state_class = definition.state_class
        self._attr_native_unit_of_measurement = definition.unit
        self._attr_icon = definition.icon
        self._attr_entity_registry_enabled_default = definition.enabled_default
        if definition.diagnostic:
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

        if self._register_key == "inverter_status":
            if not self.coordinator.is_online:
                return "Offline"
            return self._status_codes.get(int(raw), f"Unknown ({raw})")

        if self._value_map is not None:
            return self._value_map.get(int(raw), f"Unknown ({raw})")
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
        # Two entities stay available once the inverter has answered even
        # once, because they are what you look at while it is not
        # answering: "Last Update" says when it was last reachable, and
        # "Status" reports "Offline". Every other sensor goes unavailable
        # rather than holding a stale reading - a power sensor frozen at
        # its last value is worse than a gap.
        if self._register_key in ("last_update", "inverter_status"):
            return self.coordinator.last_successful_update is not None
        return super().available and self.coordinator.is_online
