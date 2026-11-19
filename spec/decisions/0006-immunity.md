# 0006 — Immunity

- **Date:** 2026-11-19
- **Status:** proposed (flips to `RATIFIED` in the carrying PR, after the two independent reviews — see [target-spec.md](../target-spec.md))
- **Decides:** the supply-domain disturbances that must not raise the flag, and their bounds.
- **Grades:** target-spec.md row 6 (Immunity).

## Context

A part whose entire purpose is asserting one line under one stimulus must be graded just as hard on *not* asserting it under legitimate supply-domain disturbances — otherwise every supply transient on the board is a false alarm. The DRAFT table's "False triggers" row stated the supply-step case; this record turns the immunity requirement into individually bounded, individually testable cases.

## Options considered

1. **Per-case bounded immunity** — a named list of stimulus cases, each with an amplitude/edge/frequency bound and its own transient check.
2. **A blanket "no false flag" statement** — simple to write, impossible to verify: any missed case is an argument, not a result.
3. **Blanket statement plus the bounded list as examples** — the blanket remains unverifiable, so nothing is gained over option 1.

## Choice

Option 1. None of the following raises the flag, at any point of the default grid:

- **Supply steps** of ± 0.5 V (the DRAFT row's ± 10 % at the 5.0 V nominal), stated as an absolute step, with edge rates ≤ 10 V/µs — confirmed from the DRAFT row ("supply steps up to 10 % within the supply range"), now with an edge-rate bound. The step is absolute, not a percentage of the grid point: at the 5.5 V point a + 10 % step would reach 6.05 V — outside the supply row's band and above the 6.0 V device rating the supply record leans on — so the case would be undefined at the top of its own grid. A ± 0.5 V step at the 5.5 V point is not inside the band either (it reaches 6.0 V, exactly the cited device rating); what bounds it is the stimulus envelope below, which states the rail explicitly rather than leaving a testbench author to invent one.
- **Power-up**: VDD ramped to the grid point's own supply (4.5 / 5.0 / 5.5 V) in 1 ms – 100 ms must not raise the flag during or after the ramp — the part must come up silent at every supply the part is rated over.
- **Coupled noise**: ± 0.25 V sinusoid superimposed on VDD, 1 kHz – 10 MHz, must not raise the flag — the amplitude puts the 5.5 V point's positive peak at 5.75 V and the 4.5 V point's trough at 4.25 V, exactly the stimulus envelope's edges, so the case is graded without clamping at every grid point; the frequency span covers board-level coupling from regulation ripple up through the detect path's own regime.

**Stimulus envelope:** the step and coupled-noise cases run in both directions at every grid point, with the instantaneous rail held inside **4.25 V – 5.75 V** — the operating band widened by the coupled-noise amplitude, whose ceiling stays below the 6.0 V device rating the supply record leans on. A stimulus whose nominal amplitude would leave the envelope is clamped at the envelope edge and graded at the clamped amplitude: the + 0.5 V step clamps to 5.75 V at the 5.5 V point and the − 0.5 V step to 4.25 V at the 4.5 V point, while the sinusoid fits the envelope everywhere and is never distorted. This keeps every case bidirectional — in particular the up-step is graded at the top of the supply range and the ± 0.75 V stretch below at both directions of the 5.0 V point — where clamping to the operating band itself would void one step direction at each band extreme and leave the up-step ungraded exactly where a false flag is likeliest.

The ± 0.25 V and 10 V/µs figures are chosen engineering bounds, not derived values: no supply-referred-to-photocurrent mapping is asserted here, because the detect path's rejection of supply-referred disturbance is a design property to be *measured*, and `tb_immunity` grades these bounds directly. They are sized to be plausible against the hysteresis and bandwidth budgets established by the threshold row ([0002](0002-threshold.md)) and the response row ([0003](0003-speed.md)); if those rows change, this row re-grades against them. **Stretch:** surviving ± 0.75 V supply steps without a false flag (same stimulus envelope) — a chosen bound in the same class as the figures above, graded directly by `tb_immunity` when pursued. It is stated in absolute volts for the same reason the target step is: + 15 % of the 5.5 V grid point (6.325 V) would leave the envelope and the 6.0 V device rating.

## Fallback

Relax the step edge-rate bound to ≤ 1 V/µs via a new decision record if the grid shows false flags at the faster edge rates — recorded with the measured edge-rate ceiling, never silently.

## Evidence (public primary sources, accessed 2026-11-19)

- In-repo: `sim/harness/corners.py` — the default grid's ± 10 % supply axis (`DEFAULT_SUPPLY_TOLERANCE = 0.10`, i.e. the 4.5 – 5.5 V band) is the band these stimulus amplitudes are defined inside, so the immunity runs ride the existing grid machinery.
- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`: the device domain is unchanged by this record (6.0 V MOS families, `sm141064.ngspice` lines 130–132); the immunity cases stress the *design*, not new devices.

## Verification

`tb_immunity` (target-spec row 6): one transient per stimulus case at every grid point — step up/down at the bound edge rate, power-up ramps at both endpoints, the noise sinusoid swept across its frequency span (frequency is an additional sweep axis inside the request). Pass: the flag never asserts during any of these runs.

## Consequences

- Every future pin (TEST, flag) is graded under these cases too; the built-in-test record ([0005](0005-built-in-test.md)) already cross-references this grid.
- A false-flag miss recorded by `tb_immunity` is evidence, and the fallback path is the only sanctioned response to it.
