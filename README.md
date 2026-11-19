# gf180-nuclear-event-detector

A Nuclear event detector on the [gf180mcu](https://github.com/google/gf180mcu-pdk) open PDK,
designed by AI agents driving
[klayout-tools](https://github.com/2AMLogic/klayout-tools) and the open-source
flow — xschem + ngspice, with layout, DRC, and LVS through klayout-tools.

It watches the photocurrent of a reverse-biased diode and raises a flag within a fraction of a microsecond when a radiation pulse arrives, so the system around it can protect itself.

**Where the idea came from.** It is the most-discussed part the idea list turned up, and the circuit itself is a fast current comparator with a pulse stretcher: a good test of the open analog flow. The prompt was a post on r/nicechips, a forum where engineers share parts they admire: [a nuclear event detector](https://www.reddit.com/r/nicechips/comments/1xuv0ca/nuclear_event_detector/). This repo is an original design of the same kind of part, not a copy of the one in the post.

## Status

```
Area (measured, post-layout): not yet measured
Design stage: spec
```

<!-- The two fields above are correct as they stand for a repo where nothing is
     built yet, so there is nothing to fill in here — only to keep current. They
     are a fixed-location summary a chip-level integrator reads without parsing
     the prose below, so the keys, their spelling, and their order do not change.

     Area (measured, post-layout): the as-built area of a DRC-clean,
     LVS-matched layout, as a number with units (e.g. 1.059 mm²), taken from
     this repo's own committed measurement. Never a target, a plan, or an
     estimate — the ratified bound is the AREA row of the target-specification
     table below. Until a layout exists, the literal "not yet measured".

     Design stage: exactly one token, from this ladder, in order —
     spec | schematic-sim | layout-DRC-LVS-clean | extracted-verified | silicon
     — describing what this repo has produced and recorded evidence for, never
     what it is aiming at. One token; not a range, not a hedge, not prose. -->

**Just opened, specification phase.** Nothing is designed yet, nothing has been
taped out, and nothing has been measured.

Not being built here: a radiation-hardened part. This is an unhardened detector circuit, verified in simulation only; no radiation test is planned and no hardness or dose-rate figure is claimed. No schematic, layout or silicon exists yet.

## Built agent-native

Every specification, decision record, testbench, and line of documentation in
this repo is produced by AI agents working from a ratified spec and an
append-only evidence trail — not human-authored work that agents merely
assisted with. Verification is the product: every claim traces to a recorded
result. Where the agents hit friction with the open-source tooling — most often
[klayout-tools](https://github.com/2AMLogic/klayout-tools) — that friction gets
filed as a public issue against the tool itself, so the fix benefits everyone
using gf180mcu, not just this repo.

## Target specification

Ratified in [`spec/target-spec.md`](spec/target-spec.md), one decision record
per row under [`spec/decisions/`](spec/decisions/). The verification method
per row (testbench + corner grid, expressible as a `klt sim` request) lives in
the spec and is not repeated here.

| Parameter | Target | Fallback | Stretch |
|---|---|---|---|
| Sensing element | One reverse-biased Nwell/P-substrate junction of the 6.0 V diode family, junction area ≥ 1,000 µm²; cathode (N-well) at VDD, anode (P-substrate) at ground | N+/P-substrate junction of the 6.0 V diode family, same polarity and bias | Junction area ≥ 10,000 µm² |
| Detection threshold | 10 µA – 1 mA photocurrent, set by one external resistor; accuracy ± 25 % of the programmed threshold over the default grid; hysteresis ≥ 30 % of the programmed threshold | 50 µA – 250 µA program range, accuracy ± 35 %, hysteresis ≥ 15 % | Accuracy ± 15 % |
| Response time | ≤ 200 ns from photocurrent crossing the programmed threshold to flag assertion | ≤ 500 ns | ≤ 50 ns |
| Flag output | Active-low, open-drain (external pull-up); pulse width 10 µs – 10 ms set by one external capacitor, width accuracy ± 30 % over the default grid | 100 µs – 1 ms width range | Width accuracy ± 15 % |
| Built-in test | A TEST input injects a fixed internal current (≥ 1.2 × the minimum programmable threshold) and must raise the flag within the response-time bound, holding the stretched width within ± 30 % | Externally injected test current on the sensing node instead of an internal path | TEST current programmable in two steps |
| Immunity | None of the following raises the flag: supply steps of ± 10 % of VDD with edge rates ≤ 10 V/µs; power-up ramp to 4.5 V in 1 – 100 ms; ± 0.25 V sinusoid superimposed on VDD, 1 kHz – 10 MHz | Step edge-rate bound relaxed to ≤ 1 V/µs via a new decision record | Survives ± 15 % supply steps without a false flag |
| Standby current | ≤ 500 µA total VDD current in the inactive state, measured at the 10 µA threshold setting, at the worst grid point (5.5 V, 125 °C, ss), including the sensing junction's dark leakage | ≤ 1 mA, via a new decision record | ≤ 100 µA |
| Supply voltage | 5 V nominal, 4.5 V – 5.5 V operating | None — the device domain is fixed by the sensing-element record | Functional 4.0 V – 5.5 V |
| AREA | ≤ 0.10 mm² core (silicon area inside the core ring, excluding the pad ring and all external components) | ≤ 0.20 mm² core, via a new decision record | ≤ 0.05 mm² core |
| Claims | Electrical terms only; no ionizing-exposure figure anywhere in this repository; export-classification ruling pending, repository stays private until ruled | — | — |

## Repo layout

```
design/        schematics (xschem)
layout/        GDS + DRC/LVS reports (klayout-tools driven)
measurements/  silicon characterization (empty until tape-out)
sim/           analog testbenches + PVT corner results
spec/          ratified spec + decision records
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).
