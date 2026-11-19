# 0008 — Standby current

- **Date:** 2026-11-19
- **Status:** proposed (flips to `RATIFIED` in the carrying PR, after the two independent reviews — see [target-spec.md](../target-spec.md))
- **Decides:** the inactive-state supply-current budget, its measurement condition, and why the condition is defined at the minimum threshold setting.
- **Grades:** target-spec.md row 7 (Standby current).

## Context

The part sits in its inactive state almost all its life; the standby budget governs the system-level cost of that. The quiescent current has three parts: the threshold reference branch (which, per the threshold record, carries the *programmed threshold current* continuously), the flag stretch branch's idle bias, and the sensing junction's dark leakage at full reverse bias.

## Options considered

1. **≤ 500 µA, measured at the minimum threshold setting (10 µA), worst grid point** — the DRAFT bound, with the measurement condition made explicit.
2. **≤ 500 µA at any threshold setting** — contradicts the threshold record: at a 1 mA setting the reference branch alone carries 1 mA continuously.
3. **Switched/pulsed reference branch** — average current falls, but the comparison then must re-settle on every reference pulse, coupling the response-time row to a duty cycle.

## Choice

Option 1, confirmed from the DRAFT table with an explicit condition: **total VDD current ≤ 500 µA in the inactive state, measured at the 10 µA threshold setting, at the worst point of the default grid (5.5 V, 125 °C, ss), including the sensing junction's dark leakage.**

- Defining the condition at the minimum setting keeps the bound verifiable and consistent with the threshold record's consequence (quiescent current grows with the programmed setting — by design, and documented there).
- The worst grid point is where leakage and branch currents are both maximal, so a single-point check bounds the whole grid: every other point is lower.
- Dark leakage is *measured* at that point, not assumed from the diode model card — the model's area-scaling convention for its saturation parameters makes a first-principles number unreliable at sensing-grade junction areas, and the testbench is authoritative by this repository's own rule.

## Fallback

**≤ 1 mA** via a new decision record if the measured worst-point current exceeds the bound after design iteration — recorded with the measured value that forced the change.

## Evidence (public primary sources, accessed 2026-11-19)

- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`, `libs.tech/ngspice/sm141064.ngspice` line 38461: the `diode_nw2ps_06v0` card's saturation parameters (`is='1.6119e-006*jsa'`, level-3 model with `jsa`/`rsa` area scaling) — the parameters whose absolute value at sensing-grade areas the standby testbench measures.
- `libs.tech/ngspice/design.ngspice`: temperature-dependent model behaviour (`tref=25` °C reference on the diode cards, temperature coefficients on the junction parameters) — the reason the check point is 125 °C, the grid's hot end.
- In-repo: the threshold record ([0002](0002-threshold.md)) defines the reference branch whose programmed current dominates the setting dependence; the default grid in `sim/harness/corners.py` supplies the worst-point definition.

## Verification

`tb_standby` (target-spec row 7): DC operating point in the inactive state (no photocurrent, TEST inactive, flag deasserted), VDD current measured at every grid point for the report, the bound checked at the worst point; the report states both.

## Consequences

- The standby bound and the threshold range are coupled by the reference branch: changing either re-grades the other.
- The dark-leakage measurement feeds back into the sensing-element record: if leakage at the minimum area breaches the budget, that record's area choice is the knob, changed by a new decision record.
