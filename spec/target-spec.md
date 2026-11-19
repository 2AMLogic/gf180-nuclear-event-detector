# Target specification — nuclear event detector (gf180mcu)

- **Date:** 2026-11-19
- **Status:** proposed — flips to `RATIFIED` in the pull request that carries
  this file, after two independent reviews (engineering and market) by
  sessions that authored neither that PR nor the design. Never flipped in a
  follow-up commit. Each parameter additionally has a decision record under
  [`decisions/`](decisions/) with the same lifecycle.
- **Terms of expression:** every value below is electrical — photocurrent,
  time, voltage, current, area. This specification states no ionizing-exposure
  figure of any kind; see decision record
  [0010-claims](decisions/0010-claims.md).

## PDK and device domain

The design targets the [gf180mcu](https://github.com/google/gf180mcu-pdk) PDK,
5 V supply domain: 6.0 V-rated MOS model families (`nfet_06v0`, `pfet_06v0`)
and the 6.0 V diode families, with the PDK's 5 V standard-cell libraries
(`gf180mcu_fd_sc_mcu7t5v0`, `gf180mcu_fd_sc_mcu9t5v0`) as the digital working
set. Evidence cites below were taken from the `gf180mcuD` variant's model
library (`libs.tech/ngspice/sm141064.ngspice`), local install accessed
2026-11-19; line numbers are as accessed and may shift across variants — the
symbol names cited are the stable reference.

## Default verification corner set

Unless a row says otherwise, every verification below runs over one full
factorial grid, expressible as a single `klt sim` request (`corners` plus
temperature and supply axes):

- MOS process corners: `tt`, `ff`, `ss`, `fs`, `sf` (the five `.lib` sections
  the model library ships; diode model sections follow their `typical`/`ss`/
  `ff` blocks, paired with the matching MOS corner).
- Temperature: −40 °C, +27 °C, +125 °C.
- Supply: VDD ∈ {4.5 V, 5.0 V, 5.5 V} — the operating band of the supply row.

These axes match the harness defaults (`sim/harness/corners.py`:
`DEFAULT_TEMPERATURES_C = (-40.0, 27.0, 125.0)`,
`DEFAULT_SUPPLY_TOLERANCE = 0.10`, five-corner `CORNER_SETS["mos"]`). Where a
row says *statistical*, the run adds a Monte-Carlo request with the PDK's
documented variation switches (`sw_stat_global=1`, `sw_stat_mismatch=1`, per
`libs.tech/ngspice/design.ngspice`).

A bound is met when every point of the row's grid meets it. A bound is missed
when any point misses it; misses are recorded, never argued away by narrowing
the grid.

## Target table

| # | Parameter | Target | Fallback | Stretch | Verification (testbench + grid) |
|---|---|---|---|---|---|
| 1 | Sensing element | One reverse-biased Nwell/P-substrate junction of the 6.0 V diode family, junction area ≥ 1,000 µm²; cathode (N-well) at VDD, anode (P-substrate) at ground | N+/P-substrate junction of the 6.0 V diode family, same polarity and bias | Junction area ≥ 10,000 µm² | `tb_sense_bias`: DC operating point of the biased junction plus a transient with the modelled photocurrent pulse (exponential current source in parallel with the junction, rise time constant ≤ 1 ns, decay time constant swept 5 ns – 1 µs); full default grid |
| 2 | Detection threshold | 10 µA – 1 mA photocurrent, set by one external resistor; accuracy ± 25 % of the programmed threshold over the default grid; hysteresis ≥ 30 % of the programmed threshold | 50 µA – 250 µA program range, accuracy ± 35 %, hysteresis ≥ 15 % | Accuracy ± 15 % | `tb_threshold`: DC sweep of the photocurrent source amplitude around the programmed threshold, plus *statistical* runs (global + mismatch); full default grid |
| 3 | Response time | ≤ 200 ns from photocurrent crossing the programmed threshold to flag assertion | ≤ 500 ns | ≤ 50 ns | `tb_response`: transient, threshold-crossing to flag-assertion delay measured per point; full default grid |
| 4 | Flag output | Active-low, open-drain (external pull-up); pulse width 10 µs – 10 ms set by one external capacitor, width accuracy ± 30 % over the default grid | 100 µs – 1 ms width range | Width accuracy ± 15 % | `tb_flag`: transient, width measured at both capacitor endpoints (10 pF, 100 nF); full default grid |
| 5 | Built-in test | A TEST input injects a fixed internal current (≥ 1.2 × the minimum programmable threshold) and must raise the flag within the response-time bound, holding the stretched width within ± 30 % | Externally injected test current on the sensing node instead of an internal path | TEST current programmable in two steps | `tb_bit`: assert TEST, measure flag timing and width; full default grid |
| 6 | Immunity | None of the following raises the flag: supply steps of ± 10 % of VDD with edge rates ≤ 10 V/µs; power-up ramp to 4.5 V in 1 – 100 ms; ± 0.25 V sinusoid superimposed on VDD, 1 kHz – 10 MHz | Step edge-rate bound relaxed to ≤ 1 V/µs via a new decision record | Survives ± 15 % supply steps without a false flag | `tb_immunity`: one transient per stimulus case; full default grid |
| 7 | Standby current | ≤ 500 µA total VDD current in the inactive state, measured at the 10 µA threshold setting, at the worst grid point (5.5 V, 125 °C, ss), including the sensing junction's dark leakage | ≤ 1 mA, via a new decision record | ≤ 100 µA | `tb_standby`: DC operating point, inactive state; the bound is checked at the worst point of the full default grid |
| 8 | Supply voltage | 5 V nominal, 4.5 V – 5.5 V operating | None — the device domain is fixed by the sensing-element record | Functional 4.0 V – 5.5 V | The supply axis of every other row's grid; `tb_standby` additionally demonstrates the inactive state at both rail extremes |
| 9 | AREA | ≤ 0.10 mm² core (silicon area inside the core ring, excluding the pad ring and all external components) | ≤ 0.20 mm² core, via a new decision record | ≤ 0.05 mm² core | Not a simulation: post-layout area of the DRC-clean GDS, measured with klayout-tools and recorded under `measurements/` |
| 10 | Claims | Electrical terms only; no ionizing-exposure figure anywhere in this repository; export-classification ruling pending, repository stays private until ruled | — | — | Review gate: automated text check plus human read, re-run on every later change to this file |

## Provenance of the values

Each value is either confirmed from the DRAFT table this specification
replaces (README.md as of `0a0cc75`), or added, with the decision record that
justifies it:

| Row | DRAFT value | Disposition | Record |
|---|---|---|---|
| 1 Sensing element | *(no row in the DRAFT table)* | added — the DRAFT table never named the sensing element | [0001](decisions/0001-sensing-element.md) |
| 2 Detection threshold | one external resistor, 10 µA – 1 mA | confirmed range; accuracy and hysteresis added as new sub-values | [0002](decisions/0002-threshold.md) |
| 3 Response time | ≤ 200 ns, stretch ≤ 50 ns | confirmed unchanged | [0003](decisions/0003-speed.md) |
| 4 Flag output | active-low, open-drain, width set by one external capacitor | confirmed; width range 10 µs – 10 ms added as a new sub-value | [0004](decisions/0004-flag-output.md) |
| 5 Built-in test | a test input injects a current pulse and must raise the flag | confirmed; injection amplitude and pass criterion added | [0005](decisions/0005-built-in-test.md) |
| 6 Immunity | DRAFT "False triggers": supply steps up to 10 % within the supply range | confirmed; power-up and coupled-noise cases added | [0006](decisions/0006-immunity.md) |
| 7 Standby current | ≤ 500 µA, stretch ≤ 100 µA | confirmed; measurement condition (minimum threshold setting, worst grid point) added | [0008](decisions/0008-standby-current.md) |
| 8 Supply voltage | 5 V ± 10 % | confirmed against the PDK device domain | [0007](decisions/0007-supply-domain.md) |
| 9 AREA | ≤ 0.10 mm² core, stretch ≤ 0.05 mm² | confirmed; core-area definition made explicit | [0009](decisions/0009-area.md) |
| 10 Claims | *(no row in the DRAFT table)* | added — records the classification ruling and the terms-of-expression rule | [0010](decisions/0010-claims.md) |

## Change discipline

These values are binding once `RATIFIED`. A later change — including a
fallback activation — goes through a new decision record under
[`decisions/`](decisions/), ratified the same way. Ratified values are never
relaxed to make a recorded result pass; a recorded result is superseded only
by a later record that says why.
