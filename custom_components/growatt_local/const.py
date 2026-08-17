"""Constants for the Growatt Local integration.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from homeassistant.const import Platform

DOMAIN = "growatt_local"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TIME,
]

# Display names for holding-register-backed controls (number/select/
# diagnostic-sensor). Keyed by the register's "name" field from the
# profile's HOLDING_REGISTERS dict. Entries not listed here fall back to a
# title-cased version of the register key - which is exactly what the
# upstream Growatt_ModbusTCP integration does, so the fallback already
# produces matching entity_ids for most controls.
CONTROL_NAMES = {
    "on_off": "On Off",
    "system_enable": "System Enable",
    "export_limit_mode": "Export Limit Mode",
    "export_limit_power": "Export Limit Power",
    "max_output_power_rate": "Max Output Power Rate",
    "load_first_battery_minimum_soc": "Load First Battery Minimum SOC",
    "discharge_power_rate": "Discharge Power Rate",
    "discharge_stopped_soc": "Discharge Stopped SOC",
    "charge_power_rate": "Charge Power Rate",
    "charge_stopped_soc": "Charge Stopped SOC",
    "ac_charge_enable": "AC Charge Enable",
    "time_period_1_enable": "Time Period 1 Enable",
    "time_period_2_enable": "Time Period 2 Enable",
    "time_period_3_enable": "Time Period 3 Enable",
    "batt_first_time_period_4_enable": "Batt First Time Period 4 Enable",
    "batt_first_time_period_5_enable": "Batt First Time Period 5 Enable",
    "batt_first_time_period_6_enable": "Batt First Time Period 6 Enable",
    "grid_first_time_period_4_enable": "Grid First Time Period 4 Enable",
    "grid_first_time_period_5_enable": "Grid First Time Period 5 Enable",
    "grid_first_time_period_6_enable": "Grid First Time Period 6 Enable",
    "grid_first_time_period_7_enable": "Grid First Time Period 7 Enable",
    "grid_first_time_period_8_enable": "Grid First Time Period 8 Enable",
    "grid_first_time_period_9_enable": "Grid First Time Period 9 Enable",
    "dry_contact_enable": "Dry Contact Enable",
    "dry_contact_on_rate": "Dry Contact On Rate",
    "dry_contact_off_rate": "Dry Contact Off Rate",
    "dry_contact_state": "Dry Contact State",
    "priority_mode": "Priority Mode",
    "pf_cmd_memory": "PF CMD Memory",
    "reactive_power_rate": "Reactive Power Rate",
    "power_factor": "Power Factor",
    # Upstream number.py renames this one on display ("Fallback" reads better
    # than "Failed"); the entity_id follows the display name, so both are
    # pinned through SUFFIX_OVERRIDES below.
    "export_limit_failed_power_rate": "Export Limit Fallback Power Rate",
    "control_authority": "Control Authority",
    "vpp_export_limit_enable": "Vpp Export Limit Enable",
    "vpp_export_limit_power_rate": "VPP Export Limit Power Rate",
    "protocol_version": "Protocol Version",
    "ntognd_detect": "NToGND Detect",
    "nonstd_vac_enable": "Non-Standard VAC Enable",
    "enable_spec_set": "Appointed Spec Setting",
    "fast_mppt_enable": "Fast MPPT Enable",
}

# Entity-id suffixes that must NOT equal the register key, because the
# upstream integration derives the entity_id from the *display* name rather
# than the register key and the two differ for these controls.
SUFFIX_OVERRIDES = {
    "export_limit_failed_power_rate": "export_limit_fallback_power_rate",
    "ntognd_detect": "ntognd_detect",
}

# Inverter status register (input register 0).
#
# Two tables exist because Growatt reuses the same register with different
# meanings. Grid-tied string inverters (MIC) use the small V3.05 table;
# hybrids with battery storage (SPH/SPH-TL3) report the V1.39 / VPP V2.01
# "system work mode" range, where 5 means "PV on-grid" rather than
# "standby". Picking the wrong table is not cosmetic: an SPH-TL3 exporting
# 900 W reports 5, which the grid-tied table renders as "Standby".
STATUS_CODES_GRID_TIED = {
    0: "Waiting",
    1: "Normal",
    3: "Fault",
    5: "Standby",
}

STATUS_CODES_HYBRID = {
    0: "Waiting",
    1: "Self-Test",
    2: "Reserved",
    3: "Fault",
    4: "Updating",
    5: "PV On-Grid",
    6: "Bat On-Grid",
    7: "PV+Bat Off-Grid",
    8: "Bat Off-Grid",
    9: "Bypass",
}

# Derating mode (input register 104) - why the inverter is currently
# limiting its own output.
DERATING_CODES = {
    0: "No derating",
    1: "Bus voltage high derating",
    2: "Aging fixed power derating",
    3: "Grid voltage high derating",
    4: "Over-frequency reduce derating",
    5: "Single DC source mode derating",
    6: "Inverter module over-temperature derating",
    7: "User activated setting to limit output derating",
    8: "Load speed process derating",
    9: "Over back by time derating",
    10: "Internal environment over-temperature derating",
    11: "External environment over-temperature derating",
    12: "Wire impedance derating",
    13: "Parallel inverter export limit derating",
    14: "Single inverter export limit derating",
    15: "Load first mode derating",
    16: "CT installation issue derating",
    17: "Zero current mode derating",
    18: "Boost module over-temperature derating",
    19: "Zero power mode derating",
    20: "Under-frequency increase derating",
    21: "Bus bar current limit derating",
}

# Battery priority mode (holding register 1044). Read-only per the V1.39
# spec - the inverter accepts the write but ignores it, so this is exposed
# as a diagnostic sensor rather than a select.
PRIORITY_MODES = {
    0: "Load First",
    1: "Battery First",
    2: "Grid First",
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

# Which status table each profile's register 0 speaks.
PROFILE_STATUS_CODES = {
    PROFILE_SPH_TL3: STATUS_CODES_HYBRID,
    PROFILE_MIC: STATUS_CODES_GRID_TIED,
}

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_SCAN_INTERVAL = 10
DEFAULT_TIMEOUT = 10
DEFAULT_OFFLINE_SCAN_INTERVAL = 300

CONF_OFFLINE_SCAN_INTERVAL = "offline_scan_interval"
CONF_INVERT_GRID_POWER = "invert_grid_power"
CONF_INVERT_BATTERY_POWER = "invert_battery_power"
CONF_PROTOCOL_V201 = "protocol_v201"
CONF_BLOCK_SIZE = "block_size"

# Maximum registers per Modbus request. Some RS485->TCP gateways and
# dataloggers silently reject reads above a certain span; capping the block
# size trades round trips for compatibility. 0 = use each block as defined.
BLOCK_SIZE_OPTIONS = {
    "auto": 0,
    "50": 50,
    "25": 25,
    "10": 10,
    "5": 5,
    "1": 1,
}
DEFAULT_BLOCK_SIZE = "auto"

MANUFACTURER = "Growatt"
