# 0002 — Detection threshold

- **Date:** 2026-11-19
- **Status:** proposed (flips to `RATIFIED` in the carrying PR, after the two independent reviews — see [target-spec.md](../target-spec.md))
- **Decides:** the photocurrent threshold range, how it is programmed, its accuracy over corners, and the hysteresis bound.
- **Grades:** target-spec.md row 2 (Detection threshold).

## Context

The threshold is the photocurrent amplitude above which the flag is raised. It must be settable from outside the part (no calibration, no trim, one external component), hold its accuracy across the PVT grid, and not chatter when the photocurrent hovers near the setting.

## Options considered

1. **One external resistor into an internal mirror** — the resistor programs a reference current; a ratio-matched MOS mirror compares it against the sensing-junction current.
2. **Internal fixed reference** (bandgap-style) — fixed threshold, no external setting.
3. **DAC-programmed internal threshold** — register domain plus a reference and a converter.

## Choice

Option 1: **10 µA – 1 mA photocurrent threshold, programmed by one external resistor** (5 kΩ – 500 kΩ at ≈ 5 V across it).

- The whole range maps onto ordinary resistor values, and the setting transfer needs no reference circuitry beyond a mirror.
- **Accuracy ± 25 %** of the programmed threshold over the default grid: the mirror's corner and ratio spread dominates; the bound is set from that, and statistical runs (global + mismatch, the PDK's `sw_stat_global=1` / `sw_stat_mismatch=1` switches documented in `libs.tech/ngspice/design.ngspice`) grade it, not just corner points.
- **Hysteresis ≥ 30 %** of the programmed threshold: a photocurrent hovering near the setting cannot re-cross into repeated flag events, and supply-noise band re-crossings stay inside the immunity row's budget.

**Consequence on the standby row:** the reference branch carries the programmed threshold current continuously, so quiescent current grows with the setting; the standby bound (record [0008](0008-standby-current.md)) is therefore defined at the minimum setting.

## Fallback

Narrow the program range to **50 µA – 250 µA** (accuracy ± 35 %, hysteresis ≥ 15 %) if the accuracy bound cannot hold at the range extremes across the grid. Activating the fallback is a new decision record.

## Evidence (public primary sources, accessed 2026-11-19)

- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`, `libs.tech/ngspice/sm141064.ngspice`:
  - lines 130–132: the `nfet_06v0` / `pfet_06v0` model families and their `t/f/s/fs/sf` corner sections — the mirror devices whose corner spread sets the accuracy bound;
  - `libs.tech/ngspice/design.ngspice`: the documented statistical switches `sw_stat_global` / `sw_stat_mismatch` used by the threshold row's Monte-Carlo runs.
- The setting resistor is external; the PDK's on-poly resistor families (`ppolyf_u_1k/2k/3k`, `sm141064.ngspice`) are available for any internal ratio-setting resistors, where their corner behaviour is graded inside the same grid.
- In-repo: `sim/harness/corners.py` defines the ± 10 % supply axis and the five MOS corners the accuracy bound is graded over.

## Verification

`tb_threshold` (target-spec row 2): DC sweep of the photocurrent source amplitude around the programmed threshold at every grid point, plus statistical runs; flag-assertion amplitude graded against ± 25 % and hysteresis against ≥ 30 %.

## Consequences

- Threshold range, accuracy and hysteresis are graded with one testbench, so a fallback activation moves all three together.
- The response-time row (record [0003](0003-speed.md)) measures from the threshold crossing *as defined by this row's setting*, so the two rows stay coupled.
