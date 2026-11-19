# 0003 — Response time

- **Date:** 2026-11-19
- **Status:** proposed (flips to `RATIFIED` in the carrying PR, after the two independent reviews — see [target-spec.md](../target-spec.md))
- **Decides:** the response-time budget from photocurrent threshold crossing to flag assertion.
- **Grades:** target-spec.md row 3 (Response time).

## Context

The system around the part acts on the flag, so the flag must arrive quickly and predictably — at every corner point, not just typical. The path is sensing-node settling, the comparison against the programmed threshold, the decision logic, and the start of the pulse stretch.

## Options considered

1. **≤ 200 ns at every grid point** (the DRAFT value) with a ≤ 50 ns stretch goal.
2. **A looser ≤ 500 ns budget** as the primary value — easier at the slow corners.
3. **A best-effort statement with no bound** — rejected: not verifiable, and this repository ships no claim without a testbench.

## Choice

Option 1, confirmed from the DRAFT table: **≤ 200 ns from the photocurrent crossing the programmed threshold (row 2's setting) to flag assertion, at every point of the default grid; stretch goal ≤ 50 ns.**

- The measurement is per grid point and per pulse shape from the sensing row's pulse model (rise time constant ≤ 1 ns), so the bound covers the slowest sanctioned stimulus, not just an idealised step.
- The pulse model's fastest decay (5 ns time constant) empties the photocurrent well inside the 200 ns budget, so the bound is defined on a *latched* crossing: assertion means the flag asserted on the threshold-crossing event, held by the stretcher (the flag row's width definition) after the stimulus is gone — never a response graded on a sustained photocurrent level, which the fastest pulse shape does not provide.
- A 180 nm current comparator plus a few logic stages is comfortably sub-100 ns at the slow corners; the 200 ns budget leaves roughly an order of magnitude of design margin, and the 50 ns stretch keeps the value honest rather than trivially loose.

## Fallback

**≤ 500 ns at every grid point**, activated by a new decision record if the grid shows the 200 ns bound missed at the slow corners after design iteration — recorded, not silently relaxed.

## Evidence (public primary sources, accessed 2026-11-19)

- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`: the 6.0 V MOS model families (`nfet_06v0`, `pfet_06v0`, `sm141064.ngspice` lines 130–132) are the transistors on the decision path; their `tt/ff/ss/fs/sf` sections are the corners the bound is graded over.
- In-repo: the default grid in `sim/harness/corners.py` (five MOS corners × −40/27/125 °C × 4.5/5.0/5.5 V) is the grid the bound is measured on.

## Verification

`tb_response` (target-spec row 3): transient runs measuring the threshold-crossing to flag-assertion delay at every grid point; the bound is met only if all points meet it.

## Consequences

- The built-in-test row (record [0005](0005-built-in-test.md)) reuses this bound as its pass criterion, keeping the test path graded by the same clock.
- The flag-pulse-width row ([0004](0004-flag-output.md)) starts its width at the assertion instant this row defines.
