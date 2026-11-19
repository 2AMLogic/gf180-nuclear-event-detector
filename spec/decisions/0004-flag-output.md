# 0004 — Flag output

- **Date:** 2026-11-19
- **Status:** proposed (flips to `RATIFIED` in the carrying PR, after the two independent reviews — see [target-spec.md](../target-spec.md))
- **Decides:** the flag output's polarity and drive type, and how its pulse width is programmed.
- **Grades:** target-spec.md row 4 (Flag output).

## Context

The flag is the part's entire output contract: polarity and drive type decide how the system around it wires the alarm line, and the pulse width decides how long the system has to react to a single event — long enough to be seen by slow supervision logic, short enough to allow re-arming.

## Options considered

1. **Active-low, open-drain** — the part pulls the line low for the event pulse; the system provides the pull-up.
2. **Push-pull CMOS output, active-high** — stronger drive, no external pull-up, but fixed polarity and a hard rail-to-rail contract at the pin.
3. **Active-low open-drain with an internal current-source pull-up** — fewer external parts, but the pull-up then sits inside the standby budget and the wired-line use below is lost.

## Choice

Option 1, confirmed from the DRAFT table: **active-low, open-drain output (external pull-up), pulse width set by one external capacitor**.

- Active-low open-drain lets several detectors share one wired alarm line — any detector can pull it low — and leaves polarity inversion to the system.
- **Width range 10 µs – 10 ms**, set by the external capacitor over 10 pF – 100 nF with a nominal 1 µA internal stretch current (width ≈ C_ext × 1 V / 1 µA nominal): slow enough at the long end for supervision polling, fast enough at the short end to re-arm within the response row's regime.
- **Width accuracy ± 30 %** over the default grid: the stretch current's corner spread dominates; the bound is graded by measurement at both capacitor endpoints, not interpolated.

## Fallback

Narrow the width range to **100 µs – 1 ms** if the ± 30 % width bound cannot hold at both endpoints across the grid. Activating the fallback is a new decision record.

## Evidence (public primary sources, accessed 2026-11-19)

- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`: the 6.0 V MOS families (`nfet_06v0`/`pfet_06v0`, `sm141064.ngspice` lines 130–132) provide the open-drain device at the 5 V rail; the pad/IO library (`libs.ref/gf180mcu_fd_io`) provides the pin structure.
- Any internal stretch capacitor required by the stretch topology uses the PDK's MIM capacitor models (`libs.tech/ngspice/sm141064_mim.ngspice`, `cap_mim_*` subcircuits); the width-setting capacitor itself is external, exactly like the threshold row's resistor.
- The 1 µA nominal stretch current is chosen on the same order as the standby budget (record [0008](0008-standby-current.md)) so the stretch branch stays inside the inactive-state budget while not asserting.

## Verification

`tb_flag` (target-spec row 4): transient runs measuring pulse width at C_ext = 10 pF and 100 nF at every grid point, graded against 10 µs – 10 ms and ± 30 %.

## Consequences

- The built-in-test row ([0005](0005-built-in-test.md)) and the immunity row ([0006](0006-immunity.md)) both grade "a flag was raised" by this row's width definition — one definition of *raised*, everywhere.
- The external pull-up and pull-down-less pin behaviour must respect the immunity row's coupled-noise case; the pin is part of that grid.
