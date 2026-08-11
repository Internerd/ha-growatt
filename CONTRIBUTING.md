# Contributing

This is a small integration built for two specific inverters
(Growatt SPH-TL3 and MIC). Issues and pull requests are welcome, but
please keep the project's scope in mind - see
[`custom_components/growatt_local/README.md`](custom_components/growatt_local/README.md)
for what's deliberately in and out of scope before proposing something
that expands it significantly (e.g. auto-detection, other inverter
families, VPP/V2.01 protocol support). If in doubt, open an issue to
discuss before writing code - it may be a five-minute conversation that
saves a PR nobody can merge.

## Reporting a bug

Please include:

- Which profile (SPH-TL3 or MIC) and, if known, the exact inverter model.
- The entity/entities affected and their current vs. expected value.
- Relevant Home Assistant logs (`Settings → System → Logs`, filter for
  `growatt_local`).
- Whether the affected register is confirmed against real hardware or
  just carried over from the upstream register map (see
  [`/NOTICE.md`](NOTICE.md)) - if you can confirm a register value
  against your inverter's display or app, say so; that's the kind of
  detail that turns "might be right" into "confirmed."

## Adding or correcting a register

Register maps live in
[`custom_components/growatt_local/profiles/sph_tl3.py`](custom_components/growatt_local/profiles/sph_tl3.py)
and
[`.../profiles/mic.py`](custom_components/growatt_local/profiles/mic.py).
Each entry needs: address, `name`, `scale`, `unit`, and (for 32-bit
values) a `pair` + `combined_scale`/`combined_unit` on the low half - see
the existing entries for the pattern. If you're adding a register from
your own scan/testing rather than porting from the upstream project, say
so in the PR - that provenance matters (see `NOTICE.md`'s attribution
section for why).

After changing a register map, run the block-coverage check locally
before opening a PR (no Home Assistant install required, pure Python):

```bash
python3 -c "
import sys; sys.path.insert(0, 'custom_components/growatt_local')
from profiles import sph_tl3 as s, mic as m
def covered(a, blocks): return any(x <= a < x+c for x, c in blocks)
for label, regs, blocks in [
    ('SPH input', s.SPH_TL3_INPUT_REGISTERS, s.SPH_TL3_INPUT_BLOCKS),
    ('SPH holding', s.SPH_TL3_HOLDING_REGISTERS, s.SPH_TL3_HOLDING_BLOCKS),
    ('MIC input', m.MIC_INPUT_REGISTERS, m.MIC_INPUT_BLOCKS),
    ('MIC holding', m.MIC_HOLDING_REGISTERS, m.MIC_HOLDING_BLOCKS),
]:
    missing = [a for a in regs if not covered(a, blocks)]
    print(label, 'OK' if not missing else f'MISSING {missing}')
"
```

A register present in a profile dict but not covered by any block in that
profile's `*_BLOCKS` list is silently never read - this catches that
before it ships.

## AI-assisted contributions

This project's existing code was written with AI assistance (see
[`NOTICE.md`](NOTICE.md)) - AI-assisted PRs are fine, just apply the same
standard as any other contribution: you're responsible for what you
submit, and register data should be traceable to a real source (protocol
doc, hardware scan, or an existing upstream project with compatible
license), not invented.
