# ha-growatt

A self-contained Home Assistant custom integration for exactly two
Growatt inverters (SPH-TL3 and MIC series) via Modbus TCP - a drop-in
replacement for the HACS `Growatt_ModbusTCP` integration, scoped to just
what this installation uses, but exposing everything its register map has
to offer for those two models (sensors, number/switch/time controls).

**License:** [MIT](LICENSE). **Attribution & AI-assistance disclosure:**
[NOTICE.md](NOTICE.md) - read this before reusing, forking, or judging where
the code came from. Short version: register-map data is credited to
[0xAHA/Growatt_ModbusTCP](https://github.com/0xAHA/Growatt_ModbusTCP) (MIT),
and the code itself was written with AI assistance (Claude/Anthropic, via
Claude Code) under human direction and review - every source file says so.

See [`custom_components/growatt_local/README.md`](custom_components/growatt_local/README.md)
for the full feature list, installation, migration steps from the old
integration, and scope notes.

## Installing via HACS

This repository is HACS-ready (`hacs.json` at the root). Add it as a
**custom repository** rather than copying files by hand:

1. HACS -> the three-dot menu (top right) -> **Custom repositories**.
2. Repository: `https://github.com/Internerd/ha-growatt`, Category: **Integration**.
3. Find "Growatt Local (SPH-TL3 / MIC)" in HACS and install it.
4. Restart Home Assistant, then follow the
   [migration steps](custom_components/growatt_local/README.md#migration-from-growatt_modbustcp)
   in the component README if you're replacing the original
   `Growatt_ModbusTCP` integration.

## Contributing

Issues and pull requests are welcome - see [CONTRIBUTING.md](CONTRIBUTING.md)
for scope/register-map guidelines, [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
for how discussion here is expected to go, and [SECURITY.md](SECURITY.md)
for reporting an actual vulnerability (as opposed to "Modbus has no
built-in auth," which is the protocol, not a bug here).

## Status / disclaimer

This integration writes directly to inverter Modbus registers (on/off,
power limits, battery charge/discharge settings, time-of-use scheduling).
It has not been validated against real hardware by an independent third
party - test carefully, one control at a time, on hardware you can
physically access. See [NOTICE.md](NOTICE.md) for how this project was
built and [`custom_components/growatt_local/README.md`](custom_components/growatt_local/README.md#status--known-limitations)
for known limitations (e.g. fault/warning codes are shown numerically,
not translated to text - see why in that section).
