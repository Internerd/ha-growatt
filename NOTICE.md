# Notice & Attribution

This file documents where content in this repository comes from, as
required by the license of reused material, and discloses the use of AI
assistance in writing it.

## 1. Third-party attribution (required by license)

The Modbus register maps in
[`custom_components/growatt_local/profiles/sph_tl3.py`](custom_components/growatt_local/profiles/sph_tl3.py)
and
[`custom_components/growatt_local/profiles/mic.py`](custom_components/growatt_local/profiles/mic.py)
(register addresses, scale factors, and units) are derived from the public
register documentation of:

> **Growatt_ModbusTCP**
> https://github.com/0xAHA/Growatt_ModbusTCP
> Copyright (c) 2025 0xAHA
> Licensed under the MIT License

That project's MIT license requires this notice to accompany any reuse of
its content. No source code from that project was copied - only the
register address/scale/unit *data*, re-expressed in this repository's own
data structures. All other code (config flow, coordinator, Modbus client,
entity platforms, documentation) is an independent implementation written
for this repository.

Fault/warning code text: Growatt's public Modbus protocol documents
(referenced above) define the existence of these registers but not a
code -> meaning table, so this repository does not claim or invent one
beyond the universally-documented "0 = none". See
[`custom_components/growatt_local/README.md`](custom_components/growatt_local/README.md#fault--warning-codes)
for details.

## 2. AI-assistance disclosure

Most of the code and documentation in this repository was written with the
assistance of an AI coding assistant (**Claude**, by Anthropic, via
Claude Code), directed and reviewed by the repository owner. Concretely:

- Config flow, coordinator, Modbus client, and all entity platforms
  (`sensor.py`, `number.py`, `switch.py`, `time.py`, `binary_sensor.py`)
  were AI-generated based on the register maps cited above and Home
  Assistant's public developer documentation.
- The register map *data* (addresses/scale/units) was extracted from the
  cited third-party source, not invented by the AI.
- This integration has **not** been tested against a live Growatt
  inverter by the AI (no such access exists in that environment); testing
  was/should be done manually by the repository owner before relying on it,
  especially before using any of the writable `number`/`switch`/`time`
  controls.
- Every source file carries a short note pointing back to this file.

### On AI-generated content and copyright (Germany/EU)

This is a factual note, not legal advice. Under German copyright law
(`§ 2 Abs. 2 UrhG`), copyright protection requires a "persönliche geistige
Schöpfung" (personal intellectual creation) - purely machine-generated
output without sufficient human creative input may not itself qualify.
The code in this repository was AI-generated under direction and review by
a human (the repository owner), which is the relevant factor for
copyright purposes, but the exact boundary is not settled law. The MIT
license in `LICENSE` is provided for practical, everyday open-source use
(reuse, forks, HACS distribution) regardless of that theoretical question.
If copyright ownership matters for your use case (e.g. commercial
relicensing, disputes), get advice from a lawyer rather than relying on
this note.

The EU AI Act's transparency principle (Art. 50) is the general reference
point for "AI content should be disclosed" - it targets synthetic media
and AI system interactions rather than source code repositories
specifically, but this repository follows that spirit by disclosing AI
involvement clearly and by file, rather than presenting the code as
entirely human-written.
