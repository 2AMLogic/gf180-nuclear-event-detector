# 0010 — Claims

- **Date:** 2026-11-19
- **Status:** proposed (flips to `RATIFIED` in the carrying PR, after the two independent reviews — see [target-spec.md](../target-spec.md))
- **Decides:** what this specification may and may not state, and where the export-classification ruling is recorded.
- **Grades:** target-spec.md row 10 (Claims).

## Context

This specification was written and is verified by agents. Its claims are only as good as the discipline behind them: a part described in a measurable physical domain, with every number traceable to a testbench and every result append-only. Two boundaries follow from the repository's own rules and the operator's standing instructions: the terms of expression, and the export-classification status.

## Options considered

1. **Electrical terms only, the operator's ruling recorded** — every value in photocurrent, time, voltage, current, area; the classification status recorded as ruled (general-purpose science instrument, repository public).
2. **Electrical terms plus informal physical characterisation in prose** — looser to write, but prose claims escape the verification discipline and invite exactly the figures this rule exists to prevent.
3. **State the classification status as this record's own assertion** — no: the classification ruling is the operator's; the record cites it, it does not issue it.

## Choice

Option 1:

- **This specification states no ionizing-exposure figure of any kind.** Every value is electrical — photocurrent, response time, voltage, current, area. The part is defined by what its junctions do under a photocurrent pulse, and nothing else. Any future claim outside that domain requires a new decision record ratified by the operator, not a relaxation of this one.
- **No military specification.** Nothing in this specification is designed to a military specification, and none is cited: the part is a general-purpose science instrument, and its bounds are electrical, verified by this repository's own testbench discipline.
- **Recorded results are append-only evidence.** A recorded result is never deleted or superseded by omission; it is superseded only by a later record that says why. No claim without a testbench; no pass without a recorded grid.
- **Spec values are never relaxed to make a result pass.** A missed bound is recorded evidence and goes through the fallback path of its row's record.
- **Export-classification ruling: made (2026-11-19).** The operator ruled on issue #1 that this block is a general-purpose science instrument and the repository is public; the earlier stay-private-pending line is superseded and is not carried into this specification. The ruling's text belongs to the operator, not to this repository's agents; a future change to the classification status is recorded by a new ratified record, not by editing this one.

## Fallback

Not applicable — this record bounds the specification's language and evidence rules; there is no degraded mode.

## Evidence (public primary sources, accessed 2026-11-19)

- In-repo: the repository's own instructions (`CLAUDE.md` / `AGENTS.md`) establish the electrical-terms rule, the append-only evidence rule, and the rule that no military specification is cited or designed to; this record restates them as ratified specification, so they grade the spec instead of merely describing the process.
- The operator's ruling on issue #1 (2026-11-19): this block is a general-purpose science instrument and the repository is public — the earlier stay-private-pending premise is superseded, and the standing rules (electrical terms, no hardness/dose/dose-rate claim, no military specification) are unchanged.
- The sibling records carry the technical evidence; nothing in this record introduces a device or value claim.

## Verification

Review gate, re-run on every later change to `spec/target-spec.md` or the records:

- automated text check over `spec/`, `README.md` and the carrying PR's text: no ionizing-exposure figure of any kind appears, and no military specification is cited or designed to;
- human read: every row's value traces to its record, and every record's evidence cites a source with an access date.

## Consequences

- This record is the one that never falls back — the terms-of-expression rule outlives every other row's revisions.
- A later record that violates the terms-of-expression rule is void by construction; ratification cannot repair it, only the operator can.
