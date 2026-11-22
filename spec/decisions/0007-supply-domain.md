# 0007 — Supply domain

- **Date:** 2026-11-19
- **Status:** proposed (flips to `RATIFIED` in the carrying PR, after the two independent reviews — see [target-spec.md](../target-spec.md))
- **Decides:** the part's supply domain — nominal voltage, operating band, and the PDK device families it implies.
- **Grades:** target-spec.md row 8 (Supply voltage).

## Context

Every other row is graded on a supply grid; the supply record is what makes that grid meaningful. The DRAFT table said 5 V ± 10 %; this record confirms that value against what the PDK's device families are rated for, so the rest of the spec stands on the device domain rather than on convention.

## Options considered

1. **5 V nominal (4.5 V – 5.5 V) on the 6.0 V-rated device families** — the DRAFT value.
2. **3.3 V nominal on the 3.3 V-rated families** (`nfet_03v3`/`pfet_03v3`, `diode_*_03v3`).
3. **Dual-rail** (3.3 V logic, 5 V analog) — two pins, two domains.

## Choice

Option 1, confirmed from the DRAFT table: **5 V nominal, 4.5 V – 5.5 V operating; stretch: functional 4.0 V – 5.5 V.**

- The PDK ships complete 5 V working sets: 6.0 V-rated MOS families (`nfet_06v0`, `pfet_06v0`), the 6.0 V diode families the sensing record ([0001](0001-sensing-element.md)) chooses from, and two 5 V standard-cell libraries (`gf180mcu_fd_sc_mcu7t5v0`, `gf180mcu_fd_sc_mcu9t5v0`) for the decision logic.
- The sense junction's modelled breakdown (14 V for `diode_nw2ps_06v0`) holds more than twice the worst-case 5.5 V reverse bias — margin that the 3.3 V domain would trade away for no benefit here.
- A higher reverse bias across the sensing junction means a wider depletion region — more collection volume for the same layout area — which favours the sensing row's collection goal.
- No second rail: one supply pin keeps the pin budget and the immunity grid ([0006](0006-immunity.md)) minimal.

**Fallback: none.** The device domain is fixed by the sensing-element record — changing it re-opens that record, and every row's grid with it.

## Evidence (public primary sources, accessed 2026-11-19)

- gf180mcu PDK (https://github.com/google/gf180mcu-pdk), variant `gf180mcuD`:
  - `libs.tech/ngspice/sm141064.ngspice` lines 130–132: the `nfet_06v0` / `pfet_06v0` / `nfet_06v0_nvt` model sections — the 6.0 V-rated transistor families;
  - lines 45–53: the `diode_*_06v0` diode families; line 38461: `diode_nw2ps_06v0` with `bv=14`;
  - `libs.ref/gf180mcu_fd_sc_mcu7t5v0/` and `libs.ref/gf180mcu_fd_sc_mcu9t5v0/`: the 5 V standard-cell libraries (the `5v0` family suffix).
- In-repo: `sim/harness/corners.py` expects the block's spec to state its supply requirement explicitly (`DEFAULT_NOMINAL_SUPPLY_V` carries a `FILL` marker "this block's nominal supply" and `DEFAULT_SUPPLY_TOLERANCE = 0.10`) — this record is that statement.

## Verification

The supply band is not measured on its own testbench: it is the supply axis of every other row's grid, and `tb_standby` (record [0008](0008-standby-current.md)) additionally demonstrates the inactive state at both rail extremes. The 4.0 V – 5.5 V stretch, if pursued, adds 4.0 V to that axis via a new decision record.

## Consequences

- Every row's grid inherits the {4.5, 5.0, 5.5} V axis from this record; changing it moves every row.
- The 6.0 V-rated families are the only sanctioned transistor/diode domain; using a 3.3 V-family device anywhere means a new decision record.
