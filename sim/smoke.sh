#!/usr/bin/env bash
#
# sim/smoke.sh -- the ONE command that proves this repo's sim harness works,
# from a clean checkout, with no configuration beyond a ngspice + PDK install
# (see sim/toolchain.json for the pins, sim/pdk.json for the PDK identity).
#
#   1. Harness selftest (the negative control): runs the smoke bench's PVT
#      grid normally, then sabotaged (every corner forced to typical), and
#      fails unless real corner switching measurably moved the result and
#      the sabotaged run's process sensitivity collapsed. Nothing is written.
#   2. Recorded smoke run: the same neutral bench over the full default
#      matrix, checked against its sanity band + process-sensitivity floor,
#      writing an append-only evidence record under
#      sim/smoke/records/<record-id>.md with its raw decks and logs beside it
#      in sim/smoke/corners/<record-id>/.
#
# Exit 0 only if both hold. Step 2 runs only after step 1 passes: a harness
# that cannot prove its corners are real must not write evidence.
#
# CI runs exactly this script (.github/workflows/smoke.yml). This bench is a
# harness check, not a block claim: sim/smoke/testbench/tb.json is a generic
# diode-connected NMOS operating point with no connection to this repo's
# design.

set -uo pipefail

SIM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SIM_DIR}/.." && pwd)"
cd "${REPO_ROOT}" || exit 1

JOBS="${SMOKE_JOBS:-2}"

echo "==== 1/2: harness selftest (normal + sabotaged corners, nothing written) ===="
if ! python3 -m sim.harness.cli selftest sim/smoke --jobs "${JOBS}"; then
  echo "FAIL: harness selftest did not pass -- corner switching is not proven; no evidence written" >&2
  exit 1
fi

echo
echo "==== 2/2: recorded smoke run (append-only evidence record) ===="
if ! python3 -m sim.harness.cli run sim/smoke --jobs "${JOBS}"; then
  echo "FAIL: recorded smoke run did not pass its checks" >&2
  exit 1
fi

echo
echo "smoke: PASS (selftest + recorded run)"
