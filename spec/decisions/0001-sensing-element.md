# 0001 — Sensing element

- **Date:** 2026-11-19
- **Status:** proposed (flips to `RATIFIED` in the carrying PR, after the two independent reviews — see [target-spec.md](../target-spec.md))
- **Decides:** which PDK junction senses the photocurrent, its polarity, bias and minimum area, and how the photocurrent pulse is modelled in simulation.
- **Grades:** target-spec.md row 1 (Sensing element).

## Context

The part watches a reverse-biased junction: a fast transient photocurrent through that junction is the event signal, and the spec is written in photocurrent terms. The sensing element must therefore collect as much of the transient as possible per unit layout area, hold a stable reverse bias at the 5 V rail, and be a plain PDK device the layout flow already knows.

## Options considered

1. **Nwell/P-substrate junction, 6.0 V diode family (`diode_nw2ps_06v0`)** — the well/substrate junction, reverse-biased with the N-well at VDD and the P-substrate at ground.
2. **N+/P-substrate junction, 6.0 V diode family (`diode_nd2ps_06v0`)** — a shallow surface junction on the substrate.
3. **P+/Nwell junction (`diode_pd2nw_06v0`)** — a surface junction inside a well.
4. **Well-internal junctions (`diode_pw2dw`, `diode_dw2ps`) or the Schottky (`sc_diode`)** — structures meant for isolation, double-well design or fast-recovery switching, not junction collection.

## Choice

Option 1, the **Nwell/P-substrate junction (`diode_nw2ps_06v0`)**, junction area ≥ 1,000 µm², cathode (N-well) tied to VDD, anode (P-substrate) at ground.

- Of the surface-referenced candidates it encloses the largest depletion volume per unit layout area — the well/substrate junction is the deep one — so it collects the most transient photocurrent for a given layout area.
- Reverse bias spans the full supply band, 5.5 V worst case, against a modelled breakdown of 14 V for this family (`bv=14` on the `diode_nw2ps_06v0` card) — more than twice the worst-case bias.
- Both terminals land on existing rails: no extra isolation structures, no extra bias domain.

**Photocurrent pulse model:** a current source in parallel with the junction instance, a single exponential pulse — rise time constant ≤ 1 ns, decay time constant swept 5 ns – 1 µs (prompt collection through diffusion-tail collection), peak amplitude the swept variable over the threshold row's range. This is expressible as a `klt sim` transient request parameterised the same way at every corner point, so every row's grid uses one pulse definition.

## Fallback

Option 2, the N+/P-substrate junction (`diode_nd2ps_06v0`), same polarity and bias. It is the shallower junction — less collection volume per layout area — but still a plain substrate-referenced diode with a modelled breakdown of 11 V, comfortably above the 5.5 V worst-case rail. Activating the fallback is a new decision record.

## Evidence (public primary sources, accessed 2026-11-19)

- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`, model library `libs.tech/ngspice/sm141064.ngspice`:
  - lines 45–53: the diode model inventory, including `diode_nw2ps_06v0` ("6.0V Nwell/Psub diode") and `diode_nd2ps_06v0` ("6.0V N+/Psub diode");
  - line 38461: the `diode_nw2ps_06v0` model card — `bv=14`, `is='1.6119e-006*jsa'`, level-3 diode with area scaling (`jsa`, `cja`, `cjswa`);
  - line 38379: the `diode_nd2ps_06v0` model card — `bv=11`;
  - lines 367/380/393: the diode corner sections `diode_typical` / `diode_ss` / `diode_ff`, which pair with the MOS corners in the verification grid.
- The 6.0 V MOS families (`nfet_06v0`, `pfet_06v0`, model-library `.lib` sections at lines 130–132) are the matching transistor domain for the 5 V rail — see record [0007](0007-supply-domain.md).

## Verification

`tb_sense_bias` (target-spec row 1): DC operating point of the biased junction, plus transients with the modelled pulse; full default grid. The junction instance's area parameter is graded against the layout by LVS at the layout stage.

## Consequences

- The sensing junction's dark leakage lands in the standby row's budget and is measured, not assumed (record [0008](0008-standby-current.md)).
- Junction area appears twice — as a collection target here and inside the AREA row's budget ([0009](0009-area.md)); the stretch goal (≥ 10,000 µm²) still fits the 0.10 mm² core budget with an order of margin.
- The pulse model defined here is the reference stimulus for every other row's verification; changing it means changing this record first.
