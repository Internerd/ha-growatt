# Growatt Local (SPH-TL3 / MIC)

A self-contained Home Assistant integration for exactly two inverters: a
**Growatt SPH-TL3** (three-phase hybrid, 3-10 kW) and a **Growatt MIC**
(single-phase, 0.6-3.3 kW), talking Modbus TCP directly.

It exists as a drop-in replacement for the HACS `Growatt_ModbusTCP`
integration, scoped to just what this installation's two inverters
actually support - but exposes everything the register map has to offer
for them, not just what was previously wired up.

> **Attribution & AI-assistance disclosure:** register-map data is credited
> to [0xAHA/Growatt_ModbusTCP](https://github.com/0xAHA/Growatt_ModbusTCP)
> (MIT License); the code itself was written with AI assistance
> (Claude/Anthropic, via Claude Code) under human direction and review. See
> [`/NOTICE.md`](../../NOTICE.md) at the repository root for the full
> details - every source file links back to it too.

## What's included

- **Sensors**: power, voltage, current, energy, temperature, battery,
  power-flow, status/derating/fault/warning codes, plus read-only
  safety/compliance diagnostic registers.
- **Calculated sensors** (SPH-TL3): `grid_power` (signed),
  `grid_export_power`, `grid_import_power`, `grid_energy_today/total`
  (net), `self_consumption`, `self_consumption_percentage` and
  `house_consumption` - derived exactly the way the upstream integration
  derives them, so the values match.
- **Number controls**: every writable percentage/SOC/rate register -
  export/output power limiting, battery charge/discharge power rate and
  stop-SOC, load-first minimum SOC, dry contact thresholds, MIC reactive
  power rate/power factor.
- **Select controls**: system enable, AC charge enable, export limit mode,
  dry contact enable, an enable select for every time-of-use scheduling
  window, plus (with the V2.01 option) VPP control authority and export
  limit enable.
- **Time controls**: start/end time for every time-of-use scheduling
  window (Time Period 1-3, plus the Battery-First/Grid-First slots 4-9
  on SPH-TL3).
- **Binary sensor**: "Inverter Online" (Modbus reachability) per device.
- **Diagnostics**: *Download diagnostics* on the config entry dumps every
  decoded register plus the profile in use, with host/port/unit ID
  redacted - the one attachment worth putting on a bug report.
- **No** auto-detection and no support for any other Growatt model - the
  model is chosen explicitly at setup.

Advanced/rarely-used entities (PV3, per-string energy counters,
Battery-First/Grid-First scheduling slots 4-9, dry contact, MIC reactive
power rate/power factor, the raw `On Off` register) are created **disabled
by default** - enable them individually under *Settings → Devices &
Services → Entities* if you use them.

Entity IDs are pinned in code to match the ones `Growatt_ModbusTCP`
generates, so existing helpers, automations and dashboards keep working
without edits - **provided you enter the same device name during setup**
(see Migration below). They are pinned rather than derived because upstream
builds each entity_id from a sensor's *display name*, not its register key,
and the two differ for about a dozen entities: `ac_current_r` becomes
`ac_current_phase_r`, `charge_energy_today` becomes `battery_charge_today`,
`bms_soh` becomes `battery_state_of_health`. Every suffix in `sensor.py`
was checked against a live `Growatt_ModbusTCP` install rather than guessed.

## Configuration options

Set at first setup, and editable afterwards via **Settings → Devices &
Services → Growatt Local → the device → Configure**:

- **Scan interval** - normal polling cadence, in seconds.
- **Offline scan interval** - polling cadence used while the inverter is
  unreachable (avoids hammering a device that's off overnight or
  disconnected); switches back to the normal scan interval as soon as it
  responds again.
- **Timeout** - Modbus TCP read/connect timeout, in seconds.
- **Max registers per request** - caps how many registers a single Modbus
  read may span. Some RS485-to-TCP gateways silently reject long reads; the
  symptom is every sensor going unavailable while the inverter itself is
  perfectly reachable. `auto` uses the block layout from the register map;
  drop to 25/10/5/1 if you hit that. Lower values cost more round trips per
  poll, so raise the scan interval to match.
- **Invert grid power** / **Invert battery power** - manual override for
  inverters/firmware that report grid or battery power flow with the
  opposite sign convention than expected (see the note below).

**Protocol V2.01 (VPP) registers**, host, port and slave ID are set at
first setup and - if your Home Assistant is new enough for the
**Reconfigure** action (2024.11+, look for it on the integration's entry
under Devices & Services) - editable in place afterwards too. On older Home
Assistant versions without that action, remove and re-add the entry instead
to change them. This is the only part of the integration with a version
floor above what `hacs.json` requires (2023.6.0, set by the `time` platform
used for the time-of-use scheduling entities) - Reconfigure not being
available on your version doesn't block installing or using everything else.

### Protocol V2.01 (VPP)

Off by default. When enabled, the integration additionally polls the
30000+/31000+ VPP range and gains:

| Entity | Register | Why it needs V2.01 |
|---|---|---|
| `sensor.<device>_battery_current` | 31215/31216 | the legacy range has no battery current register at all |
| `sensor.<device>_battery_power` | 31200/31201 | read as a signed value instead of being derived from the charge/discharge pair |
| `sensor.<device>_battery_state_of_health` | 31218 | the legacy BMS SOH register (1096) reads 0 on several firmwares |
| `select.<device>_control_authority` | 30100 | the master enable for remote control |
| `select.<device>_vpp_export_limit_enable` | 30200 | — |
| `number.<device>_vpp_export_limit_power_rate` | 30201 | — |
| `sensor.<device>_protocol_version` | 30099 | confirms the inverter really speaks V2.01 |

Battery voltage, SOC and temperature are also re-read from the VPP range
and take over the same entities when it answers.

If your inverter does not answer on that range, the extra reads simply fail
and are skipped - nothing else breaks, the new entities just stay
unavailable. Check *Settings → Devices & Services → Growatt Local →
Devices & Services* for the model string the original integration reported:
if it ends in `(V2.01)`, turn this on.

> **On the invert options:** the original integration's `Invert Grid
> Power` existed as a workaround for a real bug in that project (grid
> import/export were swapped in some versions). This integration reads
> the signed grid-power register directly and shouldn't need it, but the
> toggle is kept for parity and as an escape hatch. It applies to the
> signed `grid_power` and net `grid_energy_*` sensors only - the
> always-positive import/export pair is derived from the directional
> registers, whose meaning does not depend on the sign convention.
> `Invert Battery Power` swaps the charge/discharge power readings.

## Keeping in sync with upstream

This integration doesn't auto-update from `0xAHA/Growatt_ModbusTCP` - it's
a one-time fork of the register *data*, not a dependency. New upstream
releases get checked manually and merged in if they add something
relevant to the SPH-TL3/MIC profiles.

| Upstream version checked | What was relevant | Added here |
|---|---|---|
| v0.5.0 (installed at the time) | baseline this integration was built from | everything |
| v1.5.5 | SPH-TL3 gains IPM/Boost temperature (registers 94/95, upstream v1.5.3) and BMS status/error/cycle count/SOH (registers 1083/1085/1095/1096, upstream v1.4.x). | `ipm_temp`, `boost_temp`, `bms_status`, `bms_error`, `bms_cycle_count`, `bms_soh` sensors |
| v1.6.2 | Full audit against a live `Growatt_ModbusTCP` install. Entity-ID and platform corrections (see below), the calculated grid/consumption sensors, status/derating code tables, per-MPPT `energy_today`, the block-size option (v1.5.5, upstream #360/#367), the write-path reconnect retry (v1.6.2, upstream #375), read-only registers withheld as controls (v1.6.1, upstream #374), and the V2.01 overlay. | the bulk of the current release |

## What's intentionally different from the original integration

- **One power control per physical register, not two.** On the MIC profile,
  the original integration exposed the same holding register (3,
  "max output power %") under two different entities
  (`Active Power Rate` *and* `Max Output Power Rate`); one of them was
  permanently `unavailable` on this installation. This integration exposes
  it once, as `number.<device>_max_output_power_rate` - which is also what
  upstream's own writable-register table binds register 3 to.
- **`select.<device>_charge_config` on the MIC is named for what it is.**
  Upstream matches MIC holding register 2 against its off-grid SPF
  "charge config" control and offers solar/utility charging options on a
  micro inverter with no battery. Register 2 on this hardware is the
  power-factor command memory flag, so it is exposed as
  `select.<device>_pf_cmd_memory` (disabled by default).
- **`priority_mode` is a sensor, not a select.** The V1.39 spec documents
  holding register 1044 as read-only: the inverter ACKs the write and keeps
  its previous mode. Upstream v1.6.1 stopped creating controls for
  read-only registers for exactly this reason, so this is
  `sensor.<device>_priority_mode` rather than `select.…`.
- **No phantom entities.** Upstream builds each profile's entity set from
  sensor groups shared with larger models, so a MIC gains PV2 and
  boost-temperature entities and an SPH-TL3 gains a battery-current
  entity even where no register exists to populate them - all reporting a
  permanent 0. Those are omitted here (see the migration table below), a
  policy upstream's own profile comments now argue for.
- **No Modbus address (`com_address`) control.** Writable in the protocol,
  deliberately not exposed - changing it from Home Assistant risks the
  inverter switching to an address this integration no longer polls,
  silently losing the connection with no way to fix it except local access
  to the inverter.

## Status / Known limitations

This integration has not been validated against real hardware by an
independent third party - it was built from the register maps and
protocol documents cited below, and cross-checked against a live
`Growatt_ModbusTCP` install's entity registry, but without direct Modbus
access to a Growatt inverter. Test carefully, one control at a time, before
relying on the writable `number`/`select`/`time` entities, the same caution
you'd apply to any Modbus integration touching an inverter you depend on.

### Fault / warning codes

`fault_code` and `warning_code` are exposed as plain numeric sensors, same
as the original integration. I looked for an authoritative code->meaning
table in Growatt's public Modbus protocol documents to translate them to
plain text and couldn't find one there (the protocol docs define the
*registers*, not the fault code appendix) - so only `0 = No fault` /
`0 = No warning` is filled in (`const.py`, `FAULT_CODE_TEXT` /
`WARNING_CODE_TEXT`), visible as a `description` attribute on those
sensors. If you have the printed inverter manual or display firmware
listing what each code means, send it over and I'll wire in the full
table.

Status and derating codes *are* documented and are translated:
`sensor.<device>_status` renders the V1.39 hybrid work-mode table on
SPH-TL3 and the V3.05 grid-tied table on MIC, and
`sensor.<device>_derating_mode` renders all 22 documented derating reasons.

### The calculated grid/consumption sensors need working power-flow registers

`grid_power`, `grid_export_power`, `grid_import_power`, `self_consumption`,
`self_consumption_percentage` and `house_consumption` are not registers -
upstream calculates all six from `power_to_grid` (1029/1030),
`power_to_user` (1015/1016 or 1021/1022) and `power_to_load` (1037/1038),
falling back to an energy balance over PV and battery power when those read
zero.

**On the SPH-TL3 this was checked against, all three read 0/10/20 W and
never anything else** - 24 hours of recorder history, right through a day
with 900 W of PV and a discharging battery. If yours behaves the same way,
every one of those six sensors rests on the fallback, which cannot tell
house load apart from export without at least one of them: it attributes
`PV + battery discharge` to the grid and will report ~1.8 kW of *export*
while the house is actually consuming it.

Symptoms to look for: `grid_export_power` tracking your PV output on a day
you know you imported, or `house_consumption` flipping between ~10 W and
your full load between polls. **Do not wire these into the Energy Dashboard
before checking them against your meter for a day.** The registers that are
real - `power_to_grid`, `power_to_user`, `power_to_load`,
`energy_to_grid_*`, `grid_import_energy_*`, `load_energy_*`, and the
battery pair - are the ones to trust, and the daily/lifetime energy
counters are unaffected by any of this.

The one thing this integration does beyond upstream here is read *both*
documented grid-import registers (1015/1016 as well as 1021/1022) and
prefer whichever is non-zero, since firmware differs on which one it fills.

### `ac_charge_energy_total` on SPH-TL3

Created disabled by default. Upstream documents input register 115 on the
*single-phase* SPH profiles only, and only "with newer firmware"; it is
also a single 16-bit register, so it wraps at 6553.5 kWh. Enable it and
compare against the Growatt portal before trusting it on TL3 hardware.

## Register source / attribution

Register addresses, scale factors and units come from the MIT-licensed
[`0xAHA/Growatt_ModbusTCP`](https://github.com/0xAHA/Growatt_ModbusTCP)
project's public register documentation. See `NOTICE.md` for the full
attribution and license text. All code here (config flow, coordinator,
Modbus client, entity platforms) is a fresh, independent implementation.

## Installation

### Via HACS (recommended)

See the root [`README.md`](../../README.md) - add this repository as a
HACS custom repository, install, restart.

### Manually

1. Copy the `growatt_local` folder into your Home Assistant `custom_components/`
   directory (so you end up with
   `config/custom_components/growatt_local/...`).
2. Restart Home Assistant so it picks up the new custom integration.

## Migration from `Growatt_ModbusTCP`

Entity IDs are global per domain in Home Assistant - two integrations can't
both own `sensor.growatt_sph_10k_solar_total_power`. Remove the old entries
*before* adding the new ones, so the entity_ids are free to reuse:

1. **Settings → Devices & Services → Growatt Modbus** - delete both config
   entries (`Growatt-SPH-10K` and `Growatt-MIC1500`). This removes their
   entities from the registry.
2. **Settings → Devices & Services → Add Integration → "Growatt Local"**.
   Add it twice, once per inverter:
   - Device name: `Growatt-SPH-10K` (exactly, including the hyphen/case -
     this is what the entity_id is built from), model `SPH-TL3`, plus its
     host/port/slave ID. Tick **Protocol V2.01 (VPP)** if the old
     integration reported the model as `SPH-TL3 Series 3-10kW (V2.01)`.
   - Device name: `Growatt-MIC1500`, model `MIC`, plus its host/port/slave ID.
3. Check **Settings → Devices & Services → Entities**, filter by `growatt`,
   and confirm the entity_ids match what your helpers expect.
4. Once you've confirmed data is flowing correctly, remove the
   `Growatt_ModbusTCP` HACS repository entirely (HACS → Integrations → ⋮ →
   Remove) to avoid two integrations polling the same inverters.

### Entities that do not come back unchanged

Everything else keeps its exact entity_id. These do not:

| Old entity | Now | Why |
|---|---|---|
| `select.<sph>_priority_mode` | `sensor.<sph>_priority_mode` | register 1044 is read-only; the select never took effect |
| `select.<mic>_charge_config` | `select.<mic>_pf_cmd_memory` (disabled) | wrong register identity upstream - see above |
| `number.<mic>_active_power_rate` | — (use `number.<mic>_max_output_power_rate`) | duplicate of the same register; was permanently `unavailable` |
| `sensor.<mic>_pv2_voltage` / `_current` / `_power` | — | no PV2 register on a single-string MIC; read a permanent 0 |
| `sensor.<mic>_boost_temperature` | — | no boost-converter register on MIC; read a permanent 0 |
| `sensor.<sph>_battery_voltage_bms` | — | WIT-only register; read a permanent 0 |
| `sensor.<sph>_ac_discharge_energy_total` | — | no such register in the SPH-TL3 map |
| `sensor.<sph>_battery_current` | same, but needs **Protocol V2.01** | only the VPP range has the register |
| `sensor.<sph>_ac_charge_energy_total` | same, but **disabled by default** | firmware-dependent, see above |

Two entities keep their ID but change what they report:

- **`sensor.<sph>_status`** now uses the hybrid work-mode table, so the
  common value 5 reads **`PV On-Grid`** instead of `Standby`. The old label
  was simply wrong - an SPH-TL3 exporting 900 W is not in standby. Any
  automation comparing this to `"Standby"` needs updating.
- **`sensor.<sph>_energy_today`** is now the sum of the per-string DC
  counters instead of AC output register 53/54. That register counts
  everything the inverter puts onto AC including battery discharge, so it
  climbed overnight and the Energy Dashboard counted stored energy a second
  time as fresh production. Expect a lower, correct daily figure.

**Before changing any of the new selects** (especially `System Enable`,
`On Off` and `AC Charge Enable`) or writing to the number/time controls:
these write directly to the inverter over Modbus, same as the original
integration's controls did. Setting `System Enable` or `On Off` to off will
stop the inverter feeding in until set back on. Test one control at a time
on a system you can physically access.

### Known pre-existing issue worth fixing while you're in there

`sensor.gesamterzeugung_mic1500` (an `integration`/Riemann-sum helper) points
at `sensor.growatt_solar_total_power`, which hasn't existed since well before
this migration - it's been frozen since **31 Jul**. Its dependent
`sensor.tageszaehler_mic1500` utility meter is frozen too. A working
replacement (`sensor.gesamterzeugung_mic1.5` → `sensor.growatt_mic1500_pv1_power`)
already exists; the old helper and utility meter can be deleted.
