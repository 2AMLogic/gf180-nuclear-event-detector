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

runs the harness's own acceptance proof and exits 0 only if both halves hold:

1. **selftest** (`python3 -m sim.harness.cli selftest sim/smoke`) — the
   negative control: the smoke bench runs normally, then sabotaged (every
   corner forced to typical), and must show real process movement normally
   and a collapsed spread sabotaged. Nothing is written.
2. **recorded smoke run** (`python3 -m sim.harness.cli run sim/smoke`) — the
   neutral bench over the full default PVT matrix (5 corners × 3
   temperatures × 3 supplies), checked against its manifest `checks`, writing
   an append-only evidence record under `smoke/records/<record-id>.md` with
   raw decks and logs beside it in `smoke/corners/<record-id>/`.

CI runs exactly this script on every PR and every push to `main`
(`.github/workflows/smoke.yml`). Under the hood the CLI is the generic
harness: `python3 -m sim.harness.cli list|run|selftest` (see
`harness/README.md`).

## Experiments

- `smoke/` — the neutral harness smoke bench: a diode-connected 3.3 V NMOS
  (`nfet_03v3`) operating point, device-level and generic **on purpose**. It
  is a harness check, not a block claim: a green run proves PDK resolution,
  corner switching, PVT sweeping and evidence recording work; it makes no
  statement about this repository's block. Design testbenches will be added
  alongside it once design work starts; each follows the same
  `<slug>/testbench/tb.json` + fragment convention.

## Records are append-only evidence

A record is never edited or deleted; a correction is a later record whose
`supersedes` names the one it replaces and says why. The committed
`smoke/records/` + `smoke/corners/` entries are the standing proof that this
harness ran green at that commit; later runs mint new record ids.
