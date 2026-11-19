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

Option 1, confirmed from the DRAFT table, now with a measurable pass criterion: **a TEST input injects an internal current of at least 2 × the programmed threshold (row 2) at row 2's target accuracy, 2.1 × under its fallback accuracy — both clearing the formula floor (1 + a)/(1 − s) ×; driving TEST active must raise the flag within the response row's budget (row 3) and hold the stretched width within ± 30 % (row 4).**

- The floor is a formula, not a literal, so it survives row 2's fallback accuracy: the delivered test current must exceed the worst realized trip point at whatever setting is graded, i.e. (1 − s) · k > 1 + a, or **k > (1 + a)/(1 − s)** — where a is row 2's accuracy at that setting (target ± 25 %, fallback ± 35 %) and s the injection branch's own corner spread, budgeted at the same tolerance (it is built from the same 6.0 V device families and graded on the same grid). The injection scales with the programmed threshold — it is derived from the same reference branch that programs the comparison — so one multiplier covers row 2's whole 10 µA – 1 mA range; a fixed injection sized only for the minimum setting would provably fail to trip the comparison at every higher setting. At the target accuracy the formula gives k > 1.667 (fallback: k > 2.077), so the required 2 × / 2.1 × carry margin; a floor below the accuracy bound (e.g. 1.2 ×) would be arithmetically false at exactly the corner this test exists to cover.
- **Stretch:** the TEST injection ratio is field-selectable between two values — the required floor ratio and a higher margin ratio — so the detect path can be exercised with margin above the floor, not only at it (row 5's stretch cell); a chosen engineering enhancement, graded by the same `tb_bit` runs at both selectable ratios.
- Pass = flag raises within the response bound at every grid point, with the width bound of the flag row. Failing either is a failed test; there is no partial pass.
- TEST must be inert when inactive: an inactive TEST pin behaves like any other input under the immunity row's stimuli.

## Fallback

Option 2: the board forces a calibrated test current on the sensing node externally, and the same pass criterion applies. Chosen only if the internal injection cannot be made inert enough under the immunity grid. Activating the fallback is a new decision record.

## Evidence (public primary sources, accessed 2026-11-19)

- The injected current is defined against row 2's *programmed* threshold, scaled from the same reference branch that programs the comparison — see record [0002](0002-threshold.md); both branches are graded by the same grid.
- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`: 6.0 V MOS families (`sm141064.ngspice` lines 130–132) for the injection branch; no new device family is introduced by this record.

## Verification

`tb_bit` (target-spec row 5): assert TEST at both endpoints of row 2's then-current programming range (the stretch's selectable ratios, when pursued, are graded the same way) — at every grid point; measure flag assertion delay against the response bound and the width against the flag row's bound; verify TEST's inert state under the immunity row's stimuli (shared run with `tb_immunity`).

## Consequences

- The part's tested-ness is a ratified, measurable claim: "the detect path raises the flag on demand" — not an assumption carried between stages.
- The TEST pin joins the pin budget that the AREA row's pad-ring exclusion ([0009](0009-area.md)) and the immunity row's coupled-noise grid ([0006](0006-immunity.md)) both account for.
