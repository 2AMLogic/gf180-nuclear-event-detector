# 0005 — Built-in test

- **Date:** 2026-11-19
- **Status:** proposed (flips to `RATIFIED` in the carrying PR, after the two independent reviews — see [target-spec.md](../target-spec.md))
- **Decides:** how the part tests its own detect path, and what passing means.
- **Grades:** target-spec.md row 5 (Built-in test).

## Context

The detect path — sensing junction node, comparison against the programmed threshold, decision logic, flag stretcher — sits idle until an event. A system that cares about this part needs to prove the path works on demand, without a source of real photocurrent on the board.

## Options considered

1. **TEST input forcing an internal current into the detect path** — one pin, exercised entirely inside the part.
2. **External forced current on the sensing node** — the board injects a calibrated current through the sense pin.
3. **Digital-only self-test** (exercise logic, bypass the analog path) — cheap, but never exercises the junction node or the comparison.

## Choice

Option 1, confirmed from the DRAFT table, now with a measurable pass criterion: **a TEST input injects a fixed internal current of at least 1.2 × the minimum programmable threshold (row 2) into the detect path; driving TEST active must raise the flag within the response row's budget (row 3) and hold the stretched width within ± 30 % (row 4).**

- ≥ 1.2 × minimum threshold guarantees the test current trips the comparison even at the worst accuracy corner of the lowest setting — the test proves the *whole* path, at the setting where accuracy is least favourable.
- Pass = flag raises within the response bound at every grid point, with the width bound of the flag row. Failing either is a failed test; there is no partial pass.
- TEST must be inert when inactive: an inactive TEST pin behaves like any other input under the immunity row's stimuli.

## Fallback

Option 2: the board forces a calibrated test current on the sensing node externally, and the same pass criterion applies. Chosen only if the internal injection cannot be made inert enough under the immunity grid. Activating the fallback is a new decision record.

## Evidence (public primary sources, accessed 2026-11-19)

- The injected current is defined against row 2's minimum programmable threshold (10 µA) — see record [0002](0002-threshold.md); the reference branch that mirrors it is graded by the same grid.
- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`: 6.0 V MOS families (`sm141064.ngspice` lines 130–132) for the injection branch; no new device family is introduced by this record.

## Verification

`tb_bit` (target-spec row 5): assert TEST at every grid point, measure flag assertion delay against the response bound and the width against the flag row's bound; verify TEST's inert state under the immunity row's stimuli (shared run with `tb_immunity`).

## Consequences

- The part's tested-ness is a ratified, measurable claim: "the detect path raises the flag on demand" — not a assumption carried between stages.
- The TEST pin joins the pin budget that the AREA row's pad-ring exclusion ([0009](0009-area.md)) and the immunity row's coupled-noise grid ([0006](0006-immunity.md)) both account for.
