"""Register map for the Growatt MIC 600-3300TL-X series (single-phase micro inverter).

Register addresses, scale factors and units below are taken from the public,
MIT-licensed register map published in:
    https://github.com/0xAHA/Growatt_ModbusTCP
    Copyright (c) 2025 0xAHA, MIT License.

Only the legacy V3.05 register range (0-179) is included, since that is the
range this installation's inverter actually responds on.
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
]

# See SPH_TL3_HOLDING_REGISTERS in sph_tl3.py for what "control_type" and
# "enabled_default" mean. Note: holding register 30 ("com_address" - the
# Modbus slave/unit ID itself) is deliberately NOT exposed here - writing
# it from Home Assistant risks the inverter switching to an address this
# integration is no longer configured for, silently losing the connection.
MIC_HOLDING_REGISTERS = {
    0: {"name": "on_off", "scale": 1, "unit": "", "access": "RW", "control_type": "switch"},
    2: {"name": "pf_cmd_memory", "scale": 1, "unit": "", "access": "RW", "control_type": "switch"},

    # Max output active power percentage (0-100%). This is the single
    # physical control on this inverter family - the upstream integration
    # exposes it twice under two different entity names ("Active Power
    # Rate" and "Max Output Power Rate") which both write the same
    # register; this integration exposes it once, as "Max Output Power
    # Rate", matching the entity that was actually functioning.
    3: {"name": "max_output_power_rate", "scale": 1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100},

    4: {"name": "reactive_power_rate", "scale": 1, "unit": "%", "access": "RW", "control_type": "number", "min": -100, "max": 100, "enabled_default": False},
    5: {"name": "power_factor", "scale": 1, "unit": "", "access": "RW", "control_type": "number", "min": 0, "max": 20000, "enabled_default": False},

    3000: {"name": "export_limit_failed_power_rate", "scale": 0.1, "unit": "%", "access": "RW", "control_type": "number", "min": 0, "max": 100, "enabled_default": False},

    # Safety/compliance diagnostic registers (read-only)
    235: {"name": "ntognd_detect", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic"},
    236: {"name": "nonstd_vac_enable", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic"},
    237: {"name": "enable_spec_set", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic"},
    238: {"name": "fast_mppt_enable", "scale": 1, "unit": "", "access": "R", "control_type": "diagnostic"},
}

MIC_HOLDING_BLOCKS = [
    (0, 6),        # 0-5: on_off, pf_cmd_memory, max_output_power_rate, reactive_power_rate, power_factor
    (235, 4),      # 235-238: safety/compliance diagnostics
    (3000, 1),     # export_limit_failed_power_rate
]
