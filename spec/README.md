# spec

Ratified specification and decision records for the nuclear event detector on
gf180mcu.

- [`target-spec.md`](target-spec.md) — the target table (one row per
  parameter: target, fallback, stretch, verification method) plus the default
  verification corner set and the provenance of every value against the
  DRAFT table it replaces.
- [`decisions/`](decisions/) — one decision record per parameter: options
  considered, the choice, the fallback, evidence with sources and access
  dates, and a `Status:` line.

## Ratification

A record is ratified when the pull request carrying it is reviewed and merged
after two independent reviews (engineering and market) by sessions that
authored neither the PR nor the design. The record's own `Status:` line flips
from `proposed` to `RATIFIED` inside that PR — never in a follow-up commit.
A later change to any ratified value goes through a new decision record,
ratified the same way; values are never relaxed to make a recorded result
pass.

## Records

| Record | Parameter | Status |
|---|---|---|
| [0001](decisions/0001-sensing-element.md) | Sensing element | proposed |
| [0002](decisions/0002-threshold.md) | Detection threshold | proposed |
| [0003](decisions/0003-speed.md) | Response time | proposed |
| [0004](decisions/0004-flag-output.md) | Flag output | proposed |
| [0005](decisions/0005-built-in-test.md) | Built-in test | proposed |
| [0006](decisions/0006-immunity.md) | Immunity | proposed |
| [0007](decisions/0007-supply-domain.md) | Supply domain | proposed |
| [0008](decisions/0008-standby-current.md) | Standby current | proposed |
| [0009](decisions/0009-area.md) | Area | proposed |
| [0010](decisions/0010-claims.md) | Claims | proposed |

The status column of this index and the `Status:` lines in the records are
updated together, inside the ratifying PR.
