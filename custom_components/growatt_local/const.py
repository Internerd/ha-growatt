"""Constants for the Growatt Local integration."""
from homeassistant.const import Platform

DOMAIN = "growatt_local"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.TIME,
]

# Display names for holding-register-backed controls (number/switch/
# diagnostic-sensor). Keyed by the register's "name" field from the
# profile's HOLDING_REGISTERS dict. Entries not listed here fall back to a
# title-cased version of the register key.
CONTROL_NAMES = {
    "on_off": "On/Off",
    "export_limit_power": "VPP Export Limit Power Rate",  # kept from the original integration for entity_id parity
    "max_output_power_rate": "Max Output Power Rate",  # kept from the original integration for entity_id parity
    "load_first_battery_minimum_soc": "Load First Battery Minimum SOC",
    "discharge_power_rate": "Discharge Power Rate",
    "discharge_stopped_soc": "Discharge Stopped SOC",
    "charge_power_rate": "Charge Power Rate",
    "charge_stopped_soc": "Charge Stopped SOC",
    "ac_charge_enable": "AC Charge Enable",
    "time_period_1_enable": "Time Period 1 Enable",
    "time_period_2_enable": "Time Period 2 Enable",
    "time_period_3_enable": "Time Period 3 Enable",
    "batt_first_time_period_4_enable": "Battery First Slot 4 Enable",
    "batt_first_time_period_5_enable": "Battery First Slot 5 Enable",
    "batt_first_time_period_6_enable": "Battery First Slot 6 Enable",
    "grid_first_time_period_4_enable": "Grid First Slot 4 Enable",
    "grid_first_time_period_5_enable": "Grid First Slot 5 Enable",
    "grid_first_time_period_6_enable": "Grid First Slot 6 Enable",
    "grid_first_time_period_7_enable": "Grid First Slot 7 Enable",
    "grid_first_time_period_8_enable": "Grid First Slot 8 Enable",
    "grid_first_time_period_9_enable": "Grid First Slot 9 Enable",
    "dry_contact_enable": "Dry Contact Enable",
    "dry_contact_on_rate": "Dry Contact On Rate",
    "dry_contact_off_rate": "Dry Contact Off Rate",
    "dry_contact_state": "Dry Contact State",
    "pf_cmd_memory": "PF Command Memory",
    "reactive_power_rate": "Reactive Power Rate",
    "power_factor": "Power Factor",
    "export_limit_failed_power_rate": "Export Limit Failed Power Rate",
    "ntognd_detect": "NToGND Detection",
    "nonstd_vac_enable": "Non-Standard VAC Enable",
    "enable_spec_set": "Regional Spec Bitmask",
    "fast_mppt_enable": "Fast MPPT Enable",
}

# Entity-id suffixes that must NOT equal the register key, to stay
# byte-identical with entity_ids the previous integration already created.
SUFFIX_OVERRIDES = {
    "export_limit_power": "vpp_export_limit_power_rate",
}

# Growatt "fault code" / "warning code" registers report a single numeric
# maincode. Growatt does not publish the full code->meaning table in the
# public Modbus protocol documents (only the register's existence, not its
# value table) - so beyond the universally-documented "0 = none", codes are
# shown as-is. Extend this if you have the printed manual / display firmware
# for your model.
FAULT_CODE_TEXT = {0: "No fault"}
WARNING_CODE_TEXT = {0: "No warning"}


def display_name(register_key: str) -> str:
    """Human-readable name for a register key, with curated overrides."""
    return CONTROL_NAMES.get(register_key, register_key.replace("_", " ").title())


def entity_suffix(register_key: str) -> str:
    """Entity-id suffix for a register key, with parity overrides."""
    return SUFFIX_OVERRIDES.get(register_key, register_key)

CONF_DEVICE_NAME = "device_name"
CONF_PROFILE = "profile"
CONF_SLAVE_ID = "slave_id"

PROFILE_SPH_TL3 = "sph_tl3"
PROFILE_MIC = "mic"

PROFILE_LABELS = {
    PROFILE_SPH_TL3: "SPH-TL3 (3-10kW, three-phase hybrid)",
    PROFILE_MIC: "MIC (0.6-3.3kW, single-phase)",
}

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_SCAN_INTERVAL = 10
DEFAULT_TIMEOUT = 10

MANUFACTURER = "Growatt"
