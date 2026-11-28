"""Selftest grid checks read one ``analyze_grid`` per grid (issue #26).

PR #21 (issue #19) made a recorded ``run`` evaluate its finished grid
exactly once, through ``report.analyze_grid``. ``cmd_selftest`` stayed on
the older hand-rolled sequence: it imported ``axis_sensitivity``,
``evaluate_checks`` and ``summarize`` directly, and judged grid
completeness by result *count* alone -- so a grid with one duplicated PVT
point and one missing point of the same length passed, although
``report.reconcile_results`` (the check a recorded run's verdict rests on)
rejects it. These tests pin the selftest to the shared evaluation:

* each grid (normal, sabotaged) goes through ``report.analyze_grid``
  exactly once, and no analysis primitive runs outside that evaluation;
* the verdicts are unchanged: corners that move normally and collapse when
  sabotaged pass, while a process floor that is missed normally, or that
  still holds under sabotage, fails;
* a grid that does not reconcile with its requested points -- whatever its
  length -- is refused before any sensitivity is judged, and a failed point
  or a point missing a measurement is still refused as before.

No simulator and no PDK install are needed: ``run_grid`` is stubbed with
canned ``PointResult`` lists over the real five-corner grid of a throwaway
experiment, and the PDK lookup and toolchain preflight are stubbed too.
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sim.harness import cli, report  # noqa: E402
from sim.harness.corners import CORNERS, PvtPoint  # noqa: E402
from sim.harness.pdk import Pdk  # noqa: E402
from sim.harness.runner import PointResult  # noqa: E402

MODEL_LIB_REL = "libs.tech/ngspice/sm141064.ngspice"

#: ``analyze_grid`` first, then the four primitives it bundles. Each is
#: wrapped in every namespace that may call it (``report``, and ``cli`` for
#: the names it imports), so a count sees every call, whoever makes it.
EVALUATION_CALLS = (
    "analyze_grid", "summarize", "axis_sensitivity", "evaluate_checks", "reconcile_results",
)

EXPERIMENT = "stub-selftest"

#: The two measurements of the throwaway experiment: one per device family
#: whose sections the per-family negative control must prove are switched.
MEASURES = ("mos_i", "dio_i")

#: A measurement's value at each corner when its family follows the process
#: corner: 40% spread across the five, at every (temperature, supply) slice.
MOVING = {"tt": 1.0, "ff": 1.2, "ss": 0.8, "fs": 1.1, "sf": 0.9}
#: ... and when its family is forced to typical: one value, 0% spread.
COLLAPSED = {corner: 1.0 for corner in MOVING}

#: The process-spread floor a real bench declares: 40% meets it, 0% misses.
PROCESS_FLOOR = {"min_spread_pct_by_axis": {"process": 10}}
DEFAULT_CHECKS = {"mos_i": PROCESS_FLOOR, "dio_i": PROCESS_FLOOR}

#: How many PVT points the experiment's grid has: five corners at the
#: default three temperatures and three supplies.
GRID_POINTS = 45


def _both(values: dict) -> dict:
    """Both measurements take ``values`` at each corner."""
    return {name: values for name in MEASURES}


def _stub_pdk(tmp: Path) -> Pdk:
    return Pdk(
        name="gf180",
        path=tmp / "gf180mcuD",
        variant="gf180mcuD",
        source="unit-test stub",
        model_lib_rel=MODEL_LIB_REL,
        design_include_rel="libs.tech/ngspice/design.ngspice",
    )


def _write_experiment(tmp: Path, checks: dict) -> Path:
    """A throwaway experiment (45-point grid, two measurements, ``checks``)
    the real loader accepts; rewritten in place when called again."""
    tb_dir = tmp / EXPERIMENT / "testbench"
    tb_dir.mkdir(parents=True, exist_ok=True)
    (tb_dir / "tb_stub.spice").write_text(
        "* stub fragment\nvdd top 0 {vdd_val}\n", encoding="utf-8"
    )
    manifest = {
        "name": EXPERIMENT,
        "netlist": "tb_stub.spice",
        "nominal_supply_v": 5.0,
        "corners": ["mos"],
        "measure": {"mos_i": "i(vmos)", "dio_i": "i(vdio)"},
        "checks": checks,
    }
    (tb_dir / "tb.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return tb_dir.parent


class SelftestEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _selftest(self, normal: dict, sabotaged: dict, checks: dict = DEFAULT_CHECKS,
                  alter: dict | None = None):
        """Drive ``selftest`` on a stubbed experiment.

        ``normal`` / ``sabotaged`` map each measurement to its value at each
        corner. ``alter`` optionally maps a grid label (``"normal"`` /
        ``"sabotaged"``) to a function that rewrites that grid's finished
        results, as a faulty runner would. Returns (exit code, stdout,
        stderr, evaluation call counters, the ``run_grid`` mock).
        """
        experiment = _write_experiment(self.tmp, checks)
        values = {"normal": normal, "sabotaged": sabotaged}
        alter = alter or {}

        def fake_run_grid(tb, pdk, points, workdir, jobs=1):
            label = Path(workdir).name
            results = [
                PointResult(
                    point=p,
                    status="ok",
                    measurements={
                        name: values[label][name][p.corner.name] for name in tb.measure
                    },
                )
                for p in points
            ]
            change = alter.get(label)
            return change(results) if change else results

        with ExitStack() as stack:
            calls = {}
            for name in EVALUATION_CALLS:
                counter = mock.Mock(wraps=getattr(report, name))
                calls[name] = counter
                for module in (report, cli):
                    if hasattr(module, name):
                        stack.enter_context(mock.patch.object(module, name, counter))
            stack.enter_context(
                mock.patch.object(cli, "_resolve_pdk", return_value=_stub_pdk(self.tmp))
            )
            stack.enter_context(
                mock.patch.object(cli, "_toolchain_preflight", return_value=("ngspice-stub", {}))
            )
            grid = stack.enter_context(
                mock.patch.object(cli, "run_grid", side_effect=fake_run_grid)
            )
            out, err = io.StringIO(), io.StringIO()
            stack.enter_context(redirect_stdout(out))
            stack.enter_context(redirect_stderr(err))
            rc = cli.main(["selftest", str(experiment), "--workdir", str(self.tmp / "scratch")])
        return rc, out.getvalue(), err.getvalue(), calls, grid

    def test_passes_when_corners_move_normally_and_collapse_sabotaged(self) -> None:
        rc, out, err, _, grid = self._selftest(_both(MOVING), _both(COLLAPSED))
        self.assertEqual(rc, 0, err)
        self.assertIn("ok: corner switching demonstrably changes the simulated result", out)
        self.assertNotIn("FAIL:", err)
        self.assertEqual(
            {p.corner.sections for p in grid.call_args_list[1].args[2]},
            {CORNERS["tt"].sections},
            "the second grid must be the all-typical one the COLLAPSED values assume",
        )
        for evidence in ("records", "corners", "netlist-snapshots"):
            self.assertFalse(
                (self.tmp / EXPERIMENT / evidence).exists(),
                f"selftest must not create {evidence}/",
            )

    def test_evaluates_each_grid_once_through_analyze_grid(self) -> None:
        rc, _, err, calls, grid = self._selftest(_both(MOVING), _both(COLLAPSED))
        self.assertEqual(rc, 0, err)
        self.assertEqual(
            [Path(run.args[3]).name for run in grid.call_args_list],
            ["normal", "sabotaged"],
        )
        self.assertEqual(
            calls["analyze_grid"].call_count, 2,
            "each grid (normal, sabotaged) must be evaluated exactly once; "
            f"analyze_grid ran {calls['analyze_grid'].call_count}x",
        )
        for run, evaluation in zip(grid.call_args_list, calls["analyze_grid"].call_args_list):
            self.assertIs(
                evaluation.args[1], run.args[2],
                "a grid must be evaluated against the points that were requested of it",
            )
            self.assertTrue(
                all(r.point is p for r, p in zip(evaluation.args[2], run.args[2])),
                "a grid must be evaluated on the results the runner returned for it",
            )
        for name in EVALUATION_CALLS[1:]:
            self.assertEqual(
                calls[name].call_count, 2,
                f"{name} ran {calls[name].call_count}x, expected exactly once per grid",
            )

    def test_fails_when_a_process_floor_is_missed_normally(self) -> None:
        rc, out, err, _, _ = self._selftest(
            {"mos_i": MOVING, "dio_i": COLLAPSED}, _both(COLLAPSED)
        )
        self.assertEqual(rc, 1)
        self.assertIn(
            "FAIL: normal run misses its own process floor — "
            "dio_i min_spread_pct_by_axis on the process axis=10 (got 0)",
            err,
        )
        self.assertNotIn("ok: corner switching", out)

    def test_fails_when_a_process_floor_holds_under_sabotage(self) -> None:
        """A floor of 0 is met even by the collapsed 0% spread, so sabotage
        can never break it and the negative control cannot vouch for that
        family."""
        rc, out, err, _, _ = self._selftest(
            _both(MOVING),
            _both(COLLAPSED),
            checks={"mos_i": PROCESS_FLOOR, "dio_i": {"min_spread_pct_by_axis": {"process": 0}}},
        )
        self.assertEqual(rc, 1)
        self.assertIn(
            "FAIL: sabotaged run still passes the process floor for dio_i", err
        )
        self.assertNotIn("ok: corner switching", out)

    def test_rejects_results_that_do_not_reconcile_with_the_grid(self) -> None:
        def duplicated_and_missing(results):
            return [results[0]] + results[:-1]

        def unrequested_point(results):
            last = results[-1]
            return results[:-1] + [
                PointResult(
                    point=PvtPoint(last.point.corner, 0.0, last.point.vdd),
                    status="ok",
                    measurements=dict(last.measurements),
                )
            ]

        equal = f"({GRID_POINTS} results for {GRID_POINTS} requested points)"
        cases = {
            "duplicated and missing point, equal length": (
                duplicated_and_missing,
                (f"{equal}: 1 requested point(s) have no result, "
                 "1 requested point(s) have more than one result"),
            ),
            "result for an unrequested point, equal length": (
                unrequested_point,
                (f"{equal}: 1 requested point(s) have no result, "
                 "1 result identity(ies) were never requested"),
            ),
            "missing result": (
                lambda results: results[:-1],
                (f"(44 results for {GRID_POINTS} requested points): "
                 "1 requested point(s) have no result"),
            ),
        }
        for label, (alter, detail) in cases.items():
            with self.subTest(label):
                rc, out, err, _, _ = self._selftest(
                    _both(MOVING), _both(COLLAPSED), alter={"normal": alter}
                )
                self.assertEqual(rc, 1, err)
                self.assertIn(
                    "FAIL: normal grid incomplete or failed — results do not reconcile "
                    f"with the requested grid {detail}",
                    err,
                )
                self.assertNotIn("ok: corner switching", out)

    def test_still_refuses_failed_points_and_missing_measurements(self) -> None:
        def fail_one(results):
            results[7] = PointResult(
                point=results[7].point, status="failed", message="no convergence"
            )
            return results

        def drop_measurement(results):
            last = results[-1]
            results[-1] = PointResult(
                point=last.point, status="ok",
                measurements={"mos_i": last.measurements["mos_i"]},
            )
            return results

        cases = {
            "failed point": (
                fail_one,
                f"1/{GRID_POINTS} points did not succeed (status failed)",
            ),
            "point missing a measurement": (
                drop_measurement,
                "point is missing measurements: dio_i",
            ),
        }
        for label, (alter, problem) in cases.items():
            with self.subTest(label):
                rc, out, err, _, _ = self._selftest(
                    _both(MOVING), _both(COLLAPSED), alter={"normal": alter}
                )
                self.assertEqual(rc, 1, err)
                self.assertIn(
                    f"FAIL: normal grid incomplete or failed — {problem}; diagnostics kept in",
                    err,
                )
                self.assertNotIn("ok: corner switching", out)


if __name__ == "__main__":
    unittest.main()
