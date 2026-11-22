# sim

Testbenches and PVT corner results (ngspice). `harness/` carries the generic
sim-harness-core scaffold (see `harness/README.md`); what is generic and what
is specific to this block is tabulated there (§ "Generic core vs specific to
this block").

## One command

From the repo root:

```
./sim/smoke.sh
```

runs the harness's own acceptance proof and exits 0 only if all steps hold:

1. **corner-bundle unit tests** (`python3 -m unittest discover -s
   sim/tests`) — every corner's composed deck carries one `.lib` card per
   device family (MOS, resistor, BJT, diode, MOS cap, MIM cap); no
   simulator or PDK needed.
2. **selftest per bench** (`python3 -m sim.harness.cli selftest sim/smoke`
   and `sim/smoke-5v`) — the negative control: each bench runs normally,
   then sabotaged (every family forced to typical), and must show real
   process movement normally and a collapsed spread sabotaged — per
   measurement floor, so the non-MOS families are covered too. Nothing is
   written.
3. **recorded smoke run per bench** (`python3 -m sim.harness.cli run …`) —
   the neutral bench over the full default PVT matrix (5 corners × 3
   temperatures × 3 supplies), checked against its manifest `checks`,
   writing an append-only evidence record under
   `<bench>/records/<record-id>.md` with raw decks and logs beside it in
   `<bench>/corners/<record-id>/`.

CI runs exactly this script on every PR and every push to `main`
(`.github/workflows/smoke.yml`). Under the hood the CLI is the generic
harness: `python3 -m sim.harness.cli list|run|selftest` (see
`harness/README.md`).

## Experiments

- `smoke/` — the neutral 3.3 V harness smoke bench: a diode-connected 3.3 V
  NMOS (`nfet_03v3`) operating point, device-level and generic **on
  purpose**. It is a harness check, not a block claim: a green run proves
  PDK resolution, corner switching, PVT sweeping and evidence recording
  work; it makes no statement about this repository's block.
- `smoke-5v/` — the neutral 5 V harness smoke bench: a diode-connected 6 V
  NMOS (`nfet_06v0`) operating point plus a reverse-biased 6 V
  junction-diode leakage measurement and an n-poly resistor, over the same
  five corners. It proves the harness resolves 6 V-domain devices and
  switches the non-MOS model sections (diode, resistor) at every corner —
  each corner is a bundle of one `.lib` section per device family, so
  `ss`/`ff` genuinely skew those families too. Same harness-check rules:
  its diode/resistor process floors are what the selftest's sabotaged run
  (all families forced typical) must break.

Design testbenches will be added alongside these once design work starts;
each follows the same `<slug>/testbench/tb.json` + fragment convention.

## Records are append-only evidence

A record is never edited or deleted; a correction is a later record whose
`supersedes` names the one it replaces and says why. The committed
`smoke/records/` + `smoke/corners/` and `smoke-5v/records/` +
`smoke-5v/corners/` entries are the standing proof that this
harness ran green at that commit; later runs mint new record ids.
