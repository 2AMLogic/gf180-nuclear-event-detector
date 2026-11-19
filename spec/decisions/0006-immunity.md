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

- **Supply steps** of ± 10 % of VDD (± 0.5 V at the 5.0 V nominal) with edge rates ≤ 10 V/µs — confirmed from the DRAFT row ("supply steps up to 10 % within the supply range"), now with an edge-rate bound; the ± 10 % is the same band the supply row rates the part over, so this grades normal regulation behaviour, not an extreme event.
- **Power-up**: VDD ramped to 4.5 V in 1 ms – 100 ms must not raise the flag during or after the ramp — the part must come up silent.
- **Coupled noise**: ± 0.25 V sinusoid superimposed on VDD, 1 kHz – 10 MHz, must not raise the flag — the frequency span covers board-level coupling from regulation ripple up through the detect path's own regime.

The ± 0.25 V / 10 V/µs figures are chosen inside the hysteresis and bandwidth budgets established by the threshold row ([0002](0002-threshold.md)) and the response row ([0003](0003-speed.md)); if those rows change, this row re-grades against them.

## Fallback

Relax the step edge-rate bound to ≤ 1 V/µs via a new decision record if the grid shows false flags at the faster edge rates — recorded with the measured edge-rate ceiling, never silently.

## Evidence (public primary sources, accessed 2026-11-19)

- In-repo: `sim/harness/corners.py` — the default grid's ± 10 % supply axis (`DEFAULT_SUPPLY_TOLERANCE = 0.10`) is the same band these stimulus amplitudes are set inside, so the immunity runs ride the existing grid machinery.
- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`: the device domain is unchanged by this record (6.0 V MOS families, `sm141064.ngspice` lines 130–132); the immunity cases stress the *design*, not new devices.

## Verification

`tb_immunity` (target-spec row 6): one transient per stimulus case at every grid point — step up/down at the bound edge rate, power-up ramps at both endpoints, the noise sinusoid swept across its frequency span (frequency is an additional sweep axis inside the request). Pass: the flag never asserts during any of these runs.

## Consequences

- Every future pin (TEST, flag) is graded under these cases too; the built-in-test record ([0005](0005-built-in-test.md)) already cross-references this grid.
- A false-flag miss recorded by `tb_immunity` is evidence, and the fallback path is the only sanctioned response to it.
