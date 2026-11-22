#!/usr/bin/env bash
#
# sim/smoke.sh -- the ONE command that proves this repo's sim harness works,
# from a clean checkout, with no configuration beyond a ngspice + PDK install
# (see sim/toolchain.json for the pins, sim/pdk.json for the PDK identity).
#
#   1. Corner-bundle unit tests (no simulator, no PDK): every corner's
#      composed deck carries one .lib card per device family -- diode,
#      resistor, MIM capacitor included -- in declaration order.
#   2. Harness selftest (the negative control) per bench: runs the bench's
#      PVT grid normally, then sabotaged (every family forced to typical),
#      and fails unless real corner switching measurably moved the result
#      and the sabotaged run's process sensitivity collapsed -- per
#      measurement floor, so the non-MOS families are covered too, not just
#      MOS. Nothing is written.
#   3. Recorded smoke run per bench: the same neutral bench over the full
#      default matrix, checked against its sanity band + process-sensitivity
#      floor, writing an append-only evidence record under
#      sim/<bench>/records/<record-id>.md with its raw decks and logs beside
#      it in sim/<bench>/corners/<record-id>/.
#
# Benches (BENCHES below):
#   sim/smoke     3.3 V domain -- diode-connected nfet_03v3 operating point.
#   sim/smoke-5v  5 V domain -- nfet_06v0 operating point plus a reverse-
#                biased junction diode leakage and a poly resistor, proving
#                the harness resolves 6 V devices and switches the non-MOS
#                model sections every corner.
#
# Exit 0 only if all hold. Recorded runs (step 3) happen only after every
# selftest passes: a harness that cannot prove its corners are real must not
# write evidence.
#
# CI runs exactly this script (.github/workflows/smoke.yml). Both benches are
# harness checks, not block claims: each testbench is a generic device-level
# circuit with no connection to this repo's design.

set -uo pipefail

SIM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SIM_DIR}/.." && pwd)"
cd "${REPO_ROOT}" || exit 1

JOBS="${SMOKE_JOBS:-2}"
BENCHES=(sim/smoke sim/smoke-5v)

echo "==== 1/3: corner-bundle unit tests (.lib card per family at every corner) ===="
if ! python3 -m unittest discover -s sim/tests; then
  echo "FAIL: corner-bundle unit tests did not pass -- the per-family .lib cards are not proven" >&2
  exit 1
fi

echo
echo "==== 2/3: harness selftest per bench (normal + sabotaged corners, nothing written) ===="
for bench in "${BENCHES[@]}"; do
  echo "-- selftest: ${bench}"
  if ! python3 -m sim.harness.cli selftest "${bench}" --jobs "${JOBS}"; then
    echo "FAIL: harness selftest did not pass for ${bench} -- corner switching is not proven; no evidence written" >&2
    exit 1
  fi
done

echo
echo "==== 3/3: recorded smoke run per bench (append-only evidence record) ===="
for bench in "${BENCHES[@]}"; do
  echo "-- recorded run: ${bench}"
  if ! python3 -m sim.harness.cli run "${bench}" --jobs "${JOBS}"; then
    echo "FAIL: recorded smoke run did not pass its checks for ${bench}" >&2
    exit 1
  fi
done

echo
echo "smoke: PASS (unit tests + ${#BENCHES[@]} selftests + ${#BENCHES[@]} recorded runs)"
