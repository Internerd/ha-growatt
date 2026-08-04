# Growatt Local (SPH-TL3 / MIC)

A minimal, self-contained Home Assistant integration for exactly two
inverters: a **Growatt SPH-TL3** (three-phase hybrid, 3-10 kW) and a
**Growatt MIC** (single-phase, 0.6-3.3 kW), talking Modbus TCP directly.

It exists as a drop-in replacement for the HACS `Growatt_ModbusTCP`
integration, scoped down to just what this installation actually uses:

- Sensors (power, voltage, current, energy, temperature, battery, fault codes)
- Two writable power-limiting controls (`number` entities)
- One "Inverter Online" diagnostic `binary_sensor` per device
- **No** `select` entities (priority mode, charge config, control authority) -
  explicitly out of scope for this installation
- **No** auto-detection, no support for any other Growatt model, no
  time-of-use scheduling, no VPP/V2.01 protocol registers

Entity IDs are pinned in code to match the ones the old integration
generated, so existing helpers, automations and dashboards keep working
without edits - **provided you enter the same device name during setup**
(see Migration below).

## Register source / attribution

Register addresses, scale factors and units come from the MIT-licensed
[`0xAHA/Growatt_ModbusTCP`](https://github.com/0xAHA/Growatt_ModbusTCP)
project's public register documentation. See `NOTICE.md` for the full
attribution and license text. All code here (config flow, coordinator,
Modbus client, entity platforms) is a fresh, independent implementation.

## What's intentionally different from the original integration

- **No "calculated" sensors.** `grid_export_power`, `grid_import_power`
  (split from the signed grid register), `self_consumption`,
  `self_consumption_percentage` (as a computed value), and
  `house_consumption` are not implemented - none of your existing helpers
  depend on them, and they're straightforward to rebuild as HA template
  helpers if you want them back. Note the raw `power_to_grid` /
  `power_to_user` / `power_to_load` registers *are* included.
- **One power control per physical register, not two.** On the MIC profile,
  the original integration exposed the same holding register (3,
  "max output power %") under two different entities
  (`Active Power Rate` *and* `Max Output Power Rate`); one of them was
  permanently `unavailable` on this installation. This integration exposes
  it once, as `number.<device>_max_output_power_rate`, matching the entity
  that was actually working.
- **Legacy register range only.** Both profiles use the plain
  0-124 / 1000-1124 register ranges, not the VPP Protocol V2.01 (30000+/31000+)
  registers - matching how this installation was already running on v0.5.0
  of the original integration.

## Installation

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

### Known pre-existing issue worth fixing while you're in there

`sensor.gesamterzeugung_mic1500` (an `integration`/Riemann-sum helper) points
at `sensor.growatt_solar_total_power`, which hasn't existed since well before
this migration - it's been frozen since **31 Jul**. Its dependent
`sensor.tageszaehler_mic1500` utility meter is frozen too. A working
replacement (`sensor.gesamterzeugung_mic1.5` → `sensor.growatt_mic1500_pv1_power`)
already exists; the old helper and utility meter can be deleted.
