"""Register map for the Growatt SPH-TL3 series (three-phase hybrid, 3-10 kW).

Register addresses, scale factors and units below are taken from the public,
MIT-licensed register map published in:
    https://github.com/0xAHA/Growatt_ModbusTCP
    Copyright (c) 2025 0xAHA, MIT License.
See /NOTICE.md at the repository root for the full attribution.

Two register ranges are described here:

* the "legacy" V1.39 range (0-124, 1000-1124, 3000-3124), always polled;
* the VPP Protocol V2.01 range (30000+/31000+), polled only when the
  "Protocol V2.01 (VPP)" option is enabled on the config entry. Upstream
  ships this as a separate profile (SPH_TL3_3000_10000_V201); here it is an
  additive overlay so one profile covers both firmwares.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""

SPH_TL3_INPUT_REGISTERS = {
    # System status
    0: {"name": "inverter_status", "scale": 1, "unit": ""},

    # PV total (32-bit, registers 1/2)
    1: {"name": "pv_total_power_high", "pair": 2},
    2: {"name": "pv_total_power_low", "pair": 1, "combined_scale": 0.1, "combined_unit": "W"},

    # PV string 1
    3: {"name": "pv1_voltage", "scale": 0.1, "unit": "V"},
    4: {"name": "pv1_current", "scale": 0.1, "unit": "A"},
    5: {"name": "pv1_power_high", "pair": 6},
    6: {"name": "pv1_power_low", "pair": 5, "combined_scale": 0.1, "combined_unit": "W"},

    # PV string 2
    7: {"name": "pv2_voltage", "scale": 0.1, "unit": "V"},
    8: {"name": "pv2_current", "scale": 0.1, "unit": "A"},
    9: {"name": "pv2_power_high", "pair": 10},
    10: {"name": "pv2_power_low", "pair": 9, "combined_scale": 0.1, "combined_unit": "W"},

    # PV string 3 (present on 3-MPPT models)
    11: {"name": "pv3_voltage", "scale": 0.1, "unit": "V"},
    12: {"name": "pv3_current", "scale": 0.1, "unit": "A"},
    13: {"name": "pv3_power_high", "pair": 14},
    14: {"name": "pv3_power_low", "pair": 13, "combined_scale": 0.1, "combined_unit": "W"},

    # AC grid
    37: {"name": "ac_frequency", "scale": 0.01, "unit": "Hz"},
    38: {"name": "ac_voltage_r", "scale": 0.1, "unit": "V"},
    39: {"name": "ac_current_r", "scale": 0.1, "unit": "A"},
    40: {"name": "ac_power_r_high", "pair": 41},
    41: {"name": "ac_power_r_low", "pair": 40, "combined_scale": 0.1, "combined_unit": "W"},
    42: {"name": "ac_voltage_s", "scale": 0.1, "unit": "V"},
    43: {"name": "ac_current_s", "scale": 0.1, "unit": "A"},
    44: {"name": "ac_power_s_high", "pair": 45},
    45: {"name": "ac_power_s_low", "pair": 44, "combined_scale": 0.1, "combined_unit": "W"},
    46: {"name": "ac_voltage_t", "scale": 0.1, "unit": "V"},
    47: {"name": "ac_current_t", "scale": 0.1, "unit": "A"},
    48: {"name": "ac_power_t_high", "pair": 49},
    49: {"name": "ac_power_t_low", "pair": 48, "combined_scale": 0.1, "combined_unit": "W"},

    # AC output energy (includes battery discharge, not PV-only - see
    # USE_MPPT_ENERGY_TODAY below for why the "Energy Today" sensor does not
    # use this register directly).
    53: {"name": "energy_today_high", "pair": 54},
    54: {"name": "energy_today_low", "pair": 53, "combined_scale": 0.1, "combined_unit": "kWh"},
    55: {"name": "energy_total_high", "pair": 56},
    56: {"name": "energy_total_low", "pair": 55, "combined_scale": 0.1, "combined_unit": "kWh"},

    # Per-string DC (true solar) energy
    59: {"name": "pv1_energy_today_high", "pair": 60},
    60: {"name": "pv1_energy_today_low", "pair": 59, "combined_scale": 0.1, "combined_unit": "kWh"},
    61: {"name": "pv1_energy_total_high", "pair": 62},
    62: {"name": "pv1_energy_total_low", "pair": 61, "combined_scale": 0.1, "combined_unit": "kWh"},
    63: {"name": "pv2_energy_today_high", "pair": 64},
    64: {"name": "pv2_energy_today_low", "pair": 63, "combined_scale": 0.1, "combined_unit": "kWh"},
    65: {"name": "pv2_energy_total_high", "pair": 66},
    66: {"name": "pv2_energy_total_low", "pair": 65, "combined_scale": 0.1, "combined_unit": "kWh"},
    # PV3 daily energy (Epv3_today, V1.24 reg 67) - only 3-MPPT models
    # populate it; on 2-string hardware it stays 0 and the PV3 sensors are
    # disabled by default.
    67: {"name": "pv3_energy_today_high", "pair": 68},
    68: {"name": "pv3_energy_today_low", "pair": 67, "combined_scale": 0.1, "combined_unit": "kWh"},
    91: {"name": "pv_energy_total_high", "pair": 92},
    92: {"name": "pv_energy_total_low", "pair": 91, "combined_scale": 0.1, "combined_unit": "kWh"},

    # Temperature
    93: {"name": "inverter_temp", "scale": 0.1, "unit": "°C", "signed": True},
    # ipm_temp/boost_temp: added in upstream v1.5.3 (were mapped in the
    # sensor list but the registers themselves were missing, so both read
    # a permanent 0.0 - confirmed against real hardware in upstream #360).
    94: {"name": "ipm_temp", "scale": 0.1, "unit": "°C", "signed": True},
    95: {"name": "boost_temp", "scale": 0.1, "unit": "°C", "signed": True},

    # Status codes. 104 (derating mode) sits in the same block as the
    # fault/warning codes; it is what the inverter reports when it limits
    # its own output, and it is the register behind the upstream
    # "Derating Mode" sensor.
    104: {"name": "derating_mode", "scale": 1, "unit": ""},
    105: {"name": "fault_code", "scale": 1, "unit": ""},
    112: {"name": "warning_code", "scale": 1, "unit": ""},

    # Lifetime energy charged into the battery from AC. Documented by
    # upstream on the single-phase SPH profiles only, and only "with newer
    # firmware" - it is a single 16-bit register, so it also wraps at
    # 6553.5 kWh. Read here but its sensor is off by default: enable it and
    # compare against the portal before trusting it on TL3 hardware.
    115: {"name": "ac_charge_energy_total", "scale": 0.1, "unit": "kWh"},

    # Battery / power flow (storage range 1000-1124)
    1009: {"name": "battery_discharge_power_high", "pair": 1010},
    1010: {"name": "battery_discharge_power_low", "pair": 1009, "combined_scale": 0.1, "combined_unit": "W"},
    1011: {"name": "battery_charge_power_high", "pair": 1012},
    1012: {"name": "battery_charge_power_low", "pair": 1011, "combined_scale": 0.1, "combined_unit": "W"},
    1013: {"name": "battery_voltage", "scale": 0.1, "unit": "V"},
    1014: {"name": "battery_soc", "scale": 1, "unit": "%"},
    1040: {"name": "battery_temp", "scale": 0.1, "unit": "°C", "signed": True},

    # BMS block: added in upstream v1.4.x (V1.39 "BMS information" range,
    # 1082-1124). These are INPUT registers; the HOLDING registers at the
    # same numeric addresses 1083/1085 are this profile's Grid First time
    # period 8 start/enable (see SPH_TL3_HOLDING_REGISTERS) - different
    # Modbus function code, unrelated meaning, not a conflict.
    1083: {"name": "bms_status", "scale": 1, "unit": ""},
    1085: {"name": "bms_error", "scale": 1, "unit": ""},
    1095: {"name": "bms_cycle_count", "scale": 1, "unit": ""},
    1096: {"name": "bms_soh", "scale": 1, "unit": "%"},

    # Grid import. Growatt documents two registers for this: 1015/1016
    # ("Pactouser") and 1021/1022 ("PactouserTotal"). Which one a given
    # firmware populates varies - upstream maps both under the same name
    # and lets dict order pick a winner. Both are read here and the
    # coordinator prefers whichever is non-zero, because on at least one
    # SPH-TL3 the "Total" pair never leaves 0-20 W.
    1015: {"name": "power_to_user_legacy_high", "pair": 1016},
    1016: {"name": "power_to_user_legacy_low", "pair": 1015, "combined_scale": 0.1, "combined_unit": "W"},
    1021: {"name": "power_to_user_high", "pair": 1022},
    1022: {"name": "power_to_user_low", "pair": 1021, "combined_scale": 0.1, "combined_unit": "W"},
    1029: {"name": "power_to_grid_high", "pair": 1030},
    1030: {"name": "power_to_grid_low", "pair": 1029, "combined_scale": 0.1, "combined_unit": "W", "signed": True},
    1037: {"name": "power_to_load_high", "pair": 1038},
    1038: {"name": "power_to_load_low", "pair": 1037, "combined_scale": 0.1, "combined_unit": "W"},
    1039: {"name": "self_consumption_percentage_raw", "scale": 1, "unit": "%"},

    1044: {"name": "energy_to_user_today_high", "pair": 1045},
    1045: {"name": "energy_to_user_today_low", "pair": 1044, "combined_scale": 0.1, "combined_unit": "kWh"},
    1046: {"name": "energy_to_user_total_high", "pair": 1047},
    1047: {"name": "energy_to_user_total_low", "pair": 1046, "combined_scale": 0.1, "combined_unit": "kWh"},
    1048: {"name": "energy_to_grid_today_high", "pair": 1049},
    1049: {"name": "energy_to_grid_today_low", "pair": 1048, "combined_scale": 0.1, "combined_unit": "kWh"},
    1050: {"name": "energy_to_grid_total_high", "pair": 1051},
    1051: {"name": "energy_to_grid_total_low", "pair": 1050, "combined_scale": 0.1, "combined_unit": "kWh"},
    1052: {"name": "discharge_energy_today_high", "pair": 1053},
    1053: {"name": "discharge_energy_today_low", "pair": 1052, "combined_scale": 0.1, "combined_unit": "kWh"},
    1054: {"name": "discharge_energy_total_high", "pair": 1055},
    1055: {"name": "discharge_energy_total_low", "pair": 1054, "combined_scale": 0.1, "combined_unit": "kWh"},
    1056: {"name": "charge_energy_today_high", "pair": 1057},
    1057: {"name": "charge_energy_today_low", "pair": 1056, "combined_scale": 0.1, "combined_unit": "kWh"},
    1058: {"name": "charge_energy_total_high", "pair": 1059},
    1059: {"name": "charge_energy_total_low", "pair": 1058, "combined_scale": 0.1, "combined_unit": "kWh"},
    1060: {"name": "load_energy_today_high", "pair": 1061},
    1061: {"name": "load_energy_today_low", "pair": 1060, "combined_scale": 0.1, "combined_unit": "kWh"},
    1062: {"name": "load_energy_total_high", "pair": 1063},
    1063: {"name": "load_energy_total_low", "pair": 1062, "combined_scale": 0.1, "combined_unit": "kWh"},

    # Dry contact relay current state (0=Off, 1=On)
    3119: {"name": "dry_contact_state", "scale": 1, "unit": ""},
}

# Register blocks to poll: (start_address, count) - kept tight to minimise
# round trips. count spans from the lowest to the highest register needed
# in each block (inclusive), reading a few unused registers along the way.
SPH_TL3_INPUT_BLOCKS = [
    (0, 15),      # 0-14: status, PV total, PV1-3
    (37, 13),     # 37-49: AC grid + 3-phase
    (53, 16),     # 53-68: energy today/total, per-string energy incl. PV3
    (91, 5),      # 91-95: PV energy total, inverter/IPM/boost temp
    (104, 9),     # 104-112: derating mode, fault/warning codes
    (115, 1),     # 115: AC charge energy total (firmware-dependent)
    (1009, 6),    # 1009-1014: battery power/voltage/soc
    (1083, 14),   # 1083-1096: BMS status/error/cycle count/SOH
    (1015, 8),    # 1015-1022: power to user (both documented registers)
    (1029, 2),    # 1029-1030: power to grid
    (1037, 3),    # 1037-1039: power to load, self-consumption %
    (1040, 1),    # 1040: battery temp
    (1044, 20),   # 1044-1063: energy breakdown
    (3119, 1),    # 3119: dry contact relay state
]

# On this hardware the AC energy counters at 53-56 include battery
# discharge, so they rise overnight while the house runs off the battery.
# Upstream sets `use_mppt_energy_today` on the same profiles and sums the
# per-MPPT DC counters instead; the coordinator does the same.
SPH_TL3_USE_MPPT_ENERGY_TODAY = True

# Each entry additionally carries a "control_type" used to decide which HA
# platform picks it up:
#   "select"     - writable, fixed set of values (carries "options")
#   "number"     - writable numeric value, min/max in display units
#   "diagnostic" - read-only, shown as a plain diagnostic sensor
# Entries with "enabled_default": False are advanced/rarely-used controls,
# created but hidden until the user opts in (Settings -> Entities -> enable).
#
# Note there is no "switch" control type: Growatt's boolean registers are
# tri-state or mode-valued often enough that the upstream integration
# models every one of them as a select, and matching that keeps entity_ids
# and states identical.
_ENABLE_OPTIONS = {0: "Disabled", 1: "Enabled"}

SPH_TL3_HOLDING_REGISTERS = {
    # Register 0 is the raw inverter on/off flag. Upstream deliberately does
    # not expose it (there is no way back on from Home Assistant if the
    # inverter stops answering), so it is off by default here too - but it
    # is a documented RW register, so it is offered as an opt-in control.
    0: {"name": "on_off", "scale": 1, "unit": "", "access": "RW", "control_type": "select",
        "options": {0: "Off", 1: "On"}, "enabled_default": False},

    # System enable is the control upstream exposes for this purpose.
    1008: {"name": "system_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select",
           "options": _ENABLE_OPTIONS},

    # Export limitation: mode selects the metering source, power sets the cap.
    122: {"name": "export_limit_mode", "scale": 1, "unit": "", "access": "RW", "control_type": "select",
          "options": {0: "Disabled", 1: "RS485 External Meter", 2: "RS232 External Meter", 3: "CT Clamp Limit"}},
    123: {"name": "export_limit_power", "scale": 0.1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100},

    # Minimum battery SOC in Load First mode
    608: {"name": "load_first_battery_minimum_soc", "scale": 1, "unit": "%", "access": "RW", "control_type": "number", "min": 10, "max": 100},

    # Battery priority. Documented read-only in the V1.39 spec: the inverter
    # ACKs the write and keeps its previous mode, so exposing it as a
    # control would be a button that silently does nothing (upstream v1.6.1
    # withholds controls for read-only registers for exactly this reason).
    1044: {"name": "priority_mode", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic",
           "values": {0: "Load First", 1: "Battery First", 2: "Grid First"}},

    # Battery discharge/charge control
    1070: {"name": "discharge_power_rate", "scale": 1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100},
    1071: {"name": "discharge_stopped_soc", "scale": 1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100},
    1090: {"name": "charge_power_rate", "scale": 1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100},
    1091: {"name": "charge_stopped_soc", "scale": 1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100},
    1092: {"name": "ac_charge_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS},

    # Time-of-use scheduling window enable flags (paired with the start/end
    # time entities defined in SPH_TL3_TIME_WINDOWS below).
    1102: {"name": "time_period_1_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS},
    1105: {"name": "time_period_2_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS},
    1108: {"name": "time_period_3_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS},
    1019: {"name": "batt_first_time_period_4_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},
    1022: {"name": "batt_first_time_period_5_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},
    1025: {"name": "batt_first_time_period_6_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},
    1028: {"name": "grid_first_time_period_4_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},
    1031: {"name": "grid_first_time_period_5_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},
    1034: {"name": "grid_first_time_period_6_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},
    1082: {"name": "grid_first_time_period_7_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},
    1085: {"name": "grid_first_time_period_8_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},
    1088: {"name": "grid_first_time_period_9_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},

    # Dry contact control (needs the hardware relay wired up)
    3016: {"name": "dry_contact_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select", "options": _ENABLE_OPTIONS, "enabled_default": False},
    3017: {"name": "dry_contact_on_rate", "scale": 0.1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100, "enabled_default": False},
    3019: {"name": "dry_contact_off_rate", "scale": 0.1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100, "enabled_default": False},

    # Safety/compliance diagnostic registers (read-only)
    235: {"name": "ntognd_detect", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic", "enabled_default": False},
    236: {"name": "nonstd_vac_enable", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic", "enabled_default": False},
    237: {"name": "enable_spec_set", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic", "enabled_default": False},
    238: {"name": "fast_mppt_enable", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic", "enabled_default": False},
}

# Holding registers read as contiguous blocks (same idea as SPH_TL3_INPUT_BLOCKS).
SPH_TL3_HOLDING_BLOCKS = [
    (0, 1),        # on_off
    (122, 2),      # 122-123: export_limit_mode, export_limit_power
    (235, 4),      # 235-238: safety/compliance diagnostics
    (608, 1),      # load_first_battery_minimum_soc
    (1008, 1),     # system_enable
    (1017, 18),    # 1017-1034: Battery First 4-6 + Grid First 4-6 windows
    (1044, 1),     # priority_mode
    (1070, 2),     # discharge_power_rate, discharge_stopped_soc
    (1080, 9),     # 1080-1088: Grid First 7-9 windows
    (1090, 3),     # charge_power_rate, charge_stopped_soc, ac_charge_enable
    (1100, 9),     # 1100-1108: Time Period 1-3 windows
    (3016, 4),     # 3016-3019: dry contact control
]

# ---------------------------------------------------------------------------
# VPP Protocol V2.01 overlay (only polled when the option is enabled)
#
# Every register here reports a value the legacy range either does not have
# at all (battery cluster SOH, signed battery power, the VPP export-limit
# pair) or reports less precisely. Registers carrying "maps_to" overwrite
# the legacy value of that name once decoded.
# ---------------------------------------------------------------------------

SPH_TL3_V201_INPUT_REGISTERS = {
    # Battery cluster 1 (31200-31222). 31200/31201 is signed battery power,
    # positive = charging - the value the upstream "Battery Power" sensor
    # derives from charge/discharge power when V2.01 is unavailable.
    31200: {"name": "battery_power_vpp_high", "pair": 31201},
    31201: {"name": "battery_power_vpp_low", "pair": 31200, "combined_scale": 0.1, "combined_unit": "W", "signed": True},
    31214: {"name": "battery_voltage_vpp", "scale": 0.1, "unit": "V", "signed": True, "maps_to": "battery_voltage"},
    # Battery current. Upstream maps this pair for battery clusters 2-4
    # (31315/31316, 31415/31416, ...) and documents the block as "Battery
    # Information N refer to 31200-31299, same layout, offset +100 per
    # channel" - so cluster 1 sits at 31215/31216. The legacy range has no
    # battery current register at all.
    31215: {"name": "battery_current_high", "pair": 31216},
    31216: {"name": "battery_current_low", "pair": 31215, "combined_scale": 0.1, "combined_unit": "A", "signed": True},
    31217: {"name": "battery_soc_vpp", "scale": 1, "unit": "%", "maps_to": "battery_soc"},
    # The legacy BMS SOH register (1096) reads 0 on several firmwares; the
    # VPP copy is the one that carries a value, so it takes over the same
    # data key and therefore the same "Battery State of Health" entity.
    31218: {"name": "battery_soh_vpp", "scale": 1, "unit": "%", "maps_to": "bms_soh"},
    31222: {"name": "battery_temp_vpp", "scale": 0.1, "unit": "°C", "signed": True, "maps_to": "battery_temp"},
}

SPH_TL3_V201_INPUT_BLOCKS = [
    (31200, 2),    # signed battery power
    (31214, 9),    # 31214-31222: voltage, SOC, SOH, temperature
]

SPH_TL3_V201_HOLDING_REGISTERS = {
    30099: {"name": "protocol_version", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic",
            "enabled_default": False},
    30100: {"name": "control_authority", "scale": 1, "unit": "", "access": "RW", "control_type": "select",
            "options": _ENABLE_OPTIONS},
    # Export limitation over the VPP range. Both halves are needed: the
    # power rate is ignored while the enable flag is 0.
    30200: {"name": "vpp_export_limit_enable", "scale": 1, "unit": "", "access": "RW", "control_type": "select",
            "options": _ENABLE_OPTIONS},
    30201: {"name": "vpp_export_limit_power_rate", "scale": 0.1, "unit": "%", "access": "RW",
            "control_type": "number", "min": 0, "max": 100},
}

SPH_TL3_V201_HOLDING_BLOCKS = [
    (30099, 2),    # protocol_version, control_authority
    (30200, 2),    # export limit enable + power rate
]

# Time-of-use scheduling windows: (label, suffix, start_reg, end_reg, enable_reg, enabled_default)
# Registers are hex-packed: raw = hour * 256 + minute.
SPH_TL3_TIME_WINDOWS = [
    ("Time Period 1", "time_period_1", 1100, 1101, 1102, True),
    ("Time Period 2", "time_period_2", 1103, 1104, 1105, True),
    ("Time Period 3", "time_period_3", 1106, 1107, 1108, True),
    ("Batt First Time Period 4", "batt_first_time_period_4", 1017, 1018, 1019, False),
    ("Batt First Time Period 5", "batt_first_time_period_5", 1020, 1021, 1022, False),
    ("Batt First Time Period 6", "batt_first_time_period_6", 1023, 1024, 1025, False),
    ("Grid First Time Period 4", "grid_first_time_period_4", 1026, 1027, 1028, False),
    ("Grid First Time Period 5", "grid_first_time_period_5", 1029, 1030, 1031, False),
    ("Grid First Time Period 6", "grid_first_time_period_6", 1032, 1033, 1034, False),
    ("Grid First Time Period 7", "grid_first_time_period_7", 1080, 1081, 1082, False),
    ("Grid First Time Period 8", "grid_first_time_period_8", 1083, 1084, 1085, False),
    ("Grid First Time Period 9", "grid_first_time_period_9", 1086, 1087, 1088, False),
]
