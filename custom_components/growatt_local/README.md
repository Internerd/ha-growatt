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
  power-flow, fault/warning codes, plus read-only safety/compliance
  diagnostic registers.
- **Number controls**: every writable percentage/SOC/rate register -
  export/output power limiting, battery charge/discharge power rate and
  stop-SOC, load-first minimum SOC, dry contact thresholds, MIC reactive
  power rate/power factor.
- **Switch controls**: inverter on/off, AC charge enable, dry contact
  enable, PF command memory, and an enable switch for every
  time-of-use scheduling window.
- **Time controls**: start/end time for every time-of-use scheduling
  window (Time Period 1-3, plus the Battery-First/Grid-First slots 4-9
  on SPH-TL3).
- **Binary sensor**: "Inverter Online" (Modbus reachability) per device.
- **No** `select` entities (priority mode, charge config, control
  authority, system enable) - explicitly out of scope per your request.
- **No** auto-detection, no support for any other Growatt model, no
  VPP/V2.01 protocol registers - only the plain legacy register ranges
  these two inverters actually respond on.

Advanced/rarely-used controls (Battery-First/Grid-First scheduling slots
4-9, dry contact, MIC reactive power rate/power factor) are created
**disabled by default** - enable them individually under
*Settings → Devices & Services → Entities* if you use them.

Entity IDs are pinned in code to match the ones the old integration
generated, so existing helpers, automations and dashboards keep working
without edits - **provided you enter the same device name during setup**
(see Migration below).

## Status / Known limitations

This integration has not been validated against real hardware by an
independent third party - it was built from the register maps and
protocol documents cited below, without live access to a Growatt
inverter. Test carefully, one control at a time, before relying on the
writable `number`/`switch`/`time` entities, the same caution you'd apply
to any Modbus integration touching an inverter you depend on.

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

## Register source / attribution

Register addresses, scale factors and units come from the MIT-licensed
[`0xAHA/Growatt_ModbusTCP`](https://github.com/0xAHA/Growatt_ModbusTCP)
project's public register documentation. See `NOTICE.md` for the full
attribution and license text. All code here (config flow, coordinator,
Modbus client, entity platforms) is a fresh, independent implementation.

## What's intentionally different from the original integration

- **No "calculated" sensors.** `grid_export_power`, `grid_import_power`
  (split from the signed grid register), `self_consumption` and
  `house_consumption` are not implemented - none of your existing helpers
  depend on them, and they're straightforward to rebuild as HA template
  helpers if you want them back. The raw `power_to_grid` / `power_to_user`
  / `power_to_load` registers *are* included, and `self_consumption_percentage`
  is included since it comes directly from a register (not calculated).
- **One power control per physical register, not two.** On the MIC profile,
  the original integration exposed the same holding register (3,
  "max output power %") under two different entities
  (`Active Power Rate` *and* `Max Output Power Rate`); one of them was
  permanently `unavailable` on this installation. This integration exposes
  it once, as `number.<device>_max_output_power_rate`, matching the entity
  that was actually working.
- **No Modbus address (`com_address`) control.** Writable in the protocol,
  deliberately not exposed here - changing it from Home Assistant risks the
  inverter switching to an address this integration no longer polls,
  silently losing the connection with no way to fix it except local access
  to the inverter.
- **Legacy register range only.** Both profiles use the plain
  0-124 / 1000-1124 register ranges, not the VPP Protocol V2.01
  (30000+/31000+) registers - matching how this installation was already
  running on v0.5.0 of the original integration.

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
     host/port/slave ID.
   - Device name: `Growatt-MIC1500`, model `MIC`, plus its host/port/slave ID.
3. Check **Settings → Devices & Services → Entities**, filter by `growatt`,
   and confirm the entity_ids match what your helpers expect (they should be
   identical to before).
4. Once you've confirmed data is flowing correctly, remove the
   `Growatt_ModbusTCP` HACS repository entirely (HACS → Integrations → ⋮ →
   Remove) to avoid two integrations polling the same inverters.

**Before flipping any of the new switches** (especially `On/Off` and
`AC Charge Enable`) or writing to the new number/time controls: these write
directly to the inverter over Modbus, same as the original integration's
controls did. Toggling `On/Off` off will stop the inverter feeding in until
switched back on. Test one control at a time on a system you can physically
access, the same caution you'd apply to the original integration's controls.

### Known pre-existing issue worth fixing while you're in there

`sensor.gesamterzeugung_mic1500` (an `integration`/Riemann-sum helper) points
at `sensor.growatt_solar_total_power`, which hasn't existed since well before
this migration - it's been frozen since **31 Jul**. Its dependent
`sensor.tageszaehler_mic1500` utility meter is frozen too. A working
replacement (`sensor.gesamterzeugung_mic1.5` → `sensor.growatt_mic1500_pv1_power`)
already exists; the old helper and utility meter can be deleted.
