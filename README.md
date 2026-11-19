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

## Target specification (DRAFT — engineering to ratify, see issue #1)

| Parameter | Target | Stretch |
|---|---|---|
| Supply voltage | 5 V ± 10 % |  |
| Detection threshold | photocurrent threshold set by one external resistor, 10 µA to 1 mA |  |
| Response time | ≤ 200 ns from a threshold crossing to the flag | ≤ 50 ns |
| Flag output | active-low, open-drain; pulse stretched to a width set by one external capacitor |  |
| Built-in test | a test input injects a current pulse and must raise the flag |  |
| Standby current | ≤ 500 µA | ≤ 100 µA |
| False triggers | none for supply steps up to 10 % within the supply range |  |
| AREA | ≤ 0.10 mm² core | ≤ 0.05 mm² |

## Repo layout

```
design/        schematics (xschem)
layout/        GDS + DRC/LVS reports (klayout-tools driven)
measurements/  silicon characterization (empty until tape-out)
sim/           analog testbenches + PVT corner results
spec/          ratified spec + decision records
WORK_LOG.md    record of merged PRs and closed issues (maintained by Guide)
WORK_PLAN.md   backlog snapshot from label state (maintained by Guide)
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).
