"""Register map for the Growatt MIC 600-3300TL-X series (single-phase micro inverter).

Register addresses, scale factors and units below are taken from the public,
MIT-licensed register map published in:
    https://github.com/0xAHA/Growatt_ModbusTCP
    Copyright (c) 2025 0xAHA, MIT License.
See /NOTICE.md at the repository root for the full attribution.

The legacy V3.05 register range (0-179) is always polled. The VPP Protocol
V2.01 overlay (30000+) is polled only when the "Protocol V2.01 (VPP)"
option is enabled on the config entry.

Deliberately absent, because this model has no register for them: PV string
2, boost-converter temperature, and any battery/grid-flow value. The
upstream integration creates those entities anyway (they come from a sensor
group shared with larger models) and they report a permanent 0 - the exact
failure mode upstream's own profile notes warn against.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""

MIC_INPUT_REGISTERS = {
    0: {"name": "inverter_status", "scale": 1, "unit": ""},

    1: {"name": "pv_total_power_high", "pair": 2},
    2: {"name": "pv_total_power_low", "pair": 1, "combined_scale": 0.1, "combined_unit": "W"},

    3: {"name": "pv1_voltage", "scale": 0.1, "unit": "V"},
    4: {"name": "pv1_current", "scale": 0.1, "unit": "A"},
    5: {"name": "pv1_power_high", "pair": 6},
    6: {"name": "pv1_power_low", "pair": 5, "combined_scale": 0.1, "combined_unit": "W"},

    11: {"name": "ac_power_high", "pair": 12},
    12: {"name": "ac_power_low", "pair": 11, "combined_scale": 0.1, "combined_unit": "W"},

    13: {"name": "ac_frequency", "scale": 0.01, "unit": "Hz"},
    14: {"name": "ac_voltage", "scale": 0.1, "unit": "V"},
    15: {"name": "ac_current", "scale": 0.1, "unit": "A"},
    16: {"name": "ac_apparent_power_high", "pair": 17},
    17: {"name": "ac_apparent_power_low", "pair": 16, "combined_scale": 0.1, "combined_unit": "VA"},

    26: {"name": "energy_today_high", "pair": 27},
    27: {"name": "energy_today_low", "pair": 26, "combined_scale": 0.1, "combined_unit": "kWh"},
    28: {"name": "energy_total_high", "pair": 29},
    29: {"name": "energy_total_low", "pair": 28, "combined_scale": 0.1, "combined_unit": "kWh"},
    30: {"name": "time_total_high", "pair": 31},
    31: {"name": "time_total_low", "pair": 30, "combined_scale": 0.5, "combined_unit": "h"},

    32: {"name": "inverter_temp", "scale": 0.1, "unit": "°C", "signed": True},
    41: {"name": "ipm_temp", "scale": 0.1, "unit": "°C", "signed": True},

    40: {"name": "fault_code", "scale": 1, "unit": ""},
    64: {"name": "warning_code", "scale": 1, "unit": ""},

    # Derating mode - why the inverter is currently limiting its output.
    104: {"name": "derating_mode", "scale": 1, "unit": ""},
}

# Register blocks to poll: (start_address, count)
MIC_INPUT_BLOCKS = [
    (0, 7),      # 0-6: status, PV total, PV1
    (11, 7),     # 11-17: AC power/voltage/current/frequency/apparent power
    (26, 6),     # 26-31: energy today/total, running time
    (32, 1),     # 32: inverter temp
    (40, 1),     # 40: fault code
    (41, 1),     # 41: IPM temp
    (64, 1),     # 64: warning code
    (104, 1),    # 104: derating mode
]

# The MIC has no battery, so its AC energy counters really are solar-only
# and are read straight from registers 26-29.
MIC_USE_MPPT_ENERGY_TODAY = False

_ENABLE_OPTIONS = {0: "Disabled", 1: "Enabled"}

# See SPH_TL3_HOLDING_REGISTERS in sph_tl3.py for what "control_type" and
# "enabled_default" mean. Note: holding register 30 ("com_address" - the
# Modbus slave/unit ID itself) is deliberately NOT exposed here - writing
# it from Home Assistant risks the inverter switching to an address this
# integration is no longer configured for, silently losing the connection.
MIC_HOLDING_REGISTERS = {
    # Not exposed upstream; opt-in here for the same reason as on SPH-TL3.
    0: {"name": "on_off", "scale": 1, "unit": "", "access": "RW", "control_type": "select",
        "options": {0: "Off", 1: "On"}, "enabled_default": False},

    # Register 2 is the power-factor command memory flag. The upstream
    # integration matches register 2 against its SPF "charge_config" control
    # and creates a "Charge Config" select with solar/utility options on
    # this hardware, which is a different register's meaning on a model with
    # no battery at all. Named for what it actually is here.
    2: {"name": "pf_cmd_memory", "scale": 1, "unit": "", "access": "RW", "control_type": "select",
        "options": _ENABLE_OPTIONS, "enabled_default": False},

    # Max output active power percentage (0-100%). This is the single
    # physical control on this inverter family. The upstream register map
    # calls register 3 "active_power_rate" but its writable-control table
    # binds the name "Max Output Power Rate" to it, and binds
    # "Active Power Rate" to register 201 - which this model does not have.
    # Older releases created both entities anyway; only this one ever wrote
    # to a real register.
    3: {"name": "max_output_power_rate", "scale": 1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100},

    4: {"name": "reactive_power_rate", "scale": 1, "unit": "%", "access": "RW", "control_type": "number", "min": -100, "max": 100, "enabled_default": False},
    5: {"name": "power_factor", "scale": 1, "unit": "", "access": "RW", "control_type": "number", "min": 0, "max": 20000, "enabled_default": False},

    3000: {"name": "export_limit_failed_power_rate", "scale": 0.1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100, "enabled_default": False},

    # Safety/compliance diagnostic registers (read-only)
    235: {"name": "ntognd_detect", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic", "enabled_default": False},
    236: {"name": "nonstd_vac_enable", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic", "enabled_default": False},
    237: {"name": "enable_spec_set", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic", "enabled_default": False},
    238: {"name": "fast_mppt_enable", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic", "enabled_default": False},
}

MIC_HOLDING_BLOCKS = [
    (0, 6),        # 0-5: on_off, pf_cmd_memory, max_output_power_rate, reactive_power_rate, power_factor
    (235, 4),      # 235-238: safety/compliance diagnostics
    (3000, 1),     # export_limit_failed_power_rate
]

# ---------------------------------------------------------------------------
# VPP Protocol V2.01 overlay (only polled when the option is enabled).
# The MIC V2.01 map carries the control-authority gate but no export-limit
# pair - that block is hybrid-only.
# ---------------------------------------------------------------------------

MIC_V201_INPUT_REGISTERS: dict[int, dict] = {}
MIC_V201_INPUT_BLOCKS: list[tuple[int, int]] = []

MIC_V201_HOLDING_REGISTERS = {
    30099: {"name": "protocol_version", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic",
            "enabled_default": False},
    30100: {"name": "control_authority", "scale": 1, "unit": "", "access": "RW", "control_type": "select",
            "options": _ENABLE_OPTIONS},
}

MIC_V201_HOLDING_BLOCKS = [
    (30099, 2),
]
