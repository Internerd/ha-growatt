# ha-growatt

A minimal, self-contained Home Assistant custom integration for exactly two
Growatt inverters (SPH-TL3 and MIC series) via Modbus TCP - a drop-in
replacement for the HACS `Growatt_ModbusTCP` integration, scoped to just
what this installation uses.

See [`custom_components/growatt_local/README.md`](custom_components/growatt_local/README.md)
for installation, migration steps from the old integration, and scope notes.

## Installing via HACS

This repository is HACS-ready (`hacs.json` at the root). Add it as a
**custom repository** rather than copying files by hand:

1. HACS -> the three-dot menu (top right) -> **Custom repositories**.
2. Repository: `Internerd/ha-growatt`, Category: **Integration**.
3. Find "Growatt Local (SPH-TL3 / MIC)" in HACS and install it.
4. Restart Home Assistant, then follow the migration steps below.