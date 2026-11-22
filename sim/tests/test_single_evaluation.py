"""Single grid evaluation per recorded run (issue #19).

A recorded `run` used to evaluate the finished grid twice: once in the CLI
to print its diagnostics, once inside ``report.build_record`` to assign the
saved verdict -- two copies of the same analysis sequence that had to be
kept in sync by hand. These tests pin the deduplicated contract:

* every analysis function (``summarize``, ``axis_sensitivity``,
  ``evaluate_checks``, ``reconcile_results``) runs exactly once per run,
  recorded and ``--no-write`` alike;
* the printed diagnostics and the saved record come from that one
  calculation, so they cannot disagree -- checked on a passing grid, a
  failed check, and a missing point (reconciliation independent of the
  measurement limits);
* the disposable run path stays free of evidence writes;
* ``build_record`` stays self-contained when called directly (no shared
  analysis handed in), and refuses one whose check failures were evaluated
  under different ``allow_unswept_axes`` rules than the verdict would use.

No simulator and no PDK install are needed: ``run_grid`` is stubbed with
canned ``PointResult`` lists over a small real PVT grid, and the record is
written into a throwaway experiment directory.
"""

import argparse
import datetime as _dt
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sim.harness import cli, report  # noqa: E402
from sim.harness.corners import CORNERS, build_grid, supply_points  # noqa: E402
from sim.harness.pdk import Pdk  # noqa: E402
from sim.harness.runner import PointResult  # noqa: E402
from sim.harness.testbench import Testbench  # noqa: E402

MODEL_LIB_REL = "libs.tech/ngspice/sm141064.ngspice"

#: Analysis calls the CLI's diagnostics and build_record's verdict share.
ANALYSIS_CALLS = ("summarize", "axis_sensitivity", "evaluate_checks", "reconcile_results")

RECORD_ID = "20990101-000000-unittest"


def _stub_pdk(tmp: Path) -> Pdk:
    return Pdk(
        name="gf180",
        path=tmp / "gf180mcuD",
        variant="gf180mcuD",
        source="unit-test stub",
        model_lib_rel=MODEL_LIB_REL,
        design_include_rel="libs.tech/ngspice/design.ngspice",
    )


def _stub_testbench(tmp: Path) -> Testbench:
    tb_dir = tmp / "tb"
    tb_dir.mkdir(parents=True, exist_ok=True)
    fragment = tb_dir / "tb_stub.spice"
    fragment.write_text("* stub fragment\nvdd top 0 {vdd_val}\n", encoding="utf-8")
    # A hand-built Testbench hashes the manifest bytes for its provenance
    # block; give it a real file so record construction needs no loader.
    (tb_dir / "tb.json").write_text('{"name": "stub"}\n', encoding="utf-8")
    return Testbench(
        directory=tb_dir,
        name="stub",
        netlist=fragment,
        nominal_supply_v=5.0,
        measure={"m": "i(vdd)"},
        checks={"m": {"min": 0.4, "max": 0.6}},
    )


class _AnalysisCounters:
    """Wrap the four analysis functions in both namespaces that call them.

    Pre-deduplication the CLI called them through its own imports while
    ``build_record`` called them through ``report``'s, so a counter must
    aggregate across both module dicts to see every call.
    """

    def __init__(self, case: unittest.TestCase) -> None:
        self.counters = {name: mock.Mock(wraps=getattr(report, name))
                         for name in ANALYSIS_CALLS}
        patchers = []
        for name, counter in self.counters.items():
            patchers.append(mock.patch.object(report, name, counter))
            if hasattr(cli, name):
                patchers.append(mock.patch.object(cli, name, counter))
        for patcher in patchers:
            patcher.start()
            case.addCleanup(patcher.stop)

    def counts(self) -> dict[str, int]:
        return {name: counter.call_count for name, counter in self.counters.items()}

    def assert_each_called_once(self, case: unittest.TestCase, where: str) -> None:
        counts = self.counts()
        for name, count in counts.items():
            case.assertEqual(count, 1,
                             f"{where}: {name} ran {count}x, expected exactly once")


class SingleEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.tb = _stub_testbench(self.tmp)
        self.pdk = _stub_pdk(self.tmp)
        self.points = build_grid(
            [CORNERS["tt"], CORNERS["ss"]], (-40.0, 125.0), supply_points(5.0)
        )
        self.args = argparse.Namespace(
            jobs=1, num_threads=1, claim="", supersedes="", subset_reason=""
        )
        self.git = {"commit": "test", "short": "test", "branch": "test", "dirty": False}

    def _results(self, value: float) -> list[PointResult]:
        return [PointResult(point=p, status="ok", measurements={"m": value})
                for p in self.points]

    def _run(self, results: list[PointResult], record_id: str | None):
        """Drive ``_simulate_and_record`` with a stubbed grid.

        Returns (exit code, stdout, stderr, captured record dict or None,
        analysis counters).
        """
        counters = _AnalysisCounters(self)
        written = mock.Mock(wraps=cli.write_record)
        with mock.patch.object(cli, "write_record", written), \
                mock.patch.object(cli, "run_grid", return_value=results) as grid:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli._simulate_and_record(
                    self.args, self.tb, self.pdk, self.points,
                    self.tmp / "scratch", None,
                    _dt.datetime(2099, 1, 1, tzinfo=_dt.timezone.utc),
                    self.git, "ngspice-stub", {}, record_id,
                )
        self.assertEqual(grid.call_count, 1)
        record = written.call_args[0][0] if written.call_count else None
        return rc, out.getvalue(), err.getvalue(), record, counters

    def test_recorded_passing_grid_evaluates_once_and_agrees(self) -> None:
        rc, out, err, record, counters = self._run(self._results(0.5), RECORD_ID)
        counters.assert_each_called_once(self, "recorded run, passing grid")
        self.assertEqual(rc, 0)
        self.assertEqual(record["status"], "pass")
        self.assertEqual(record["checks"]["failures"], [])
        self.assertTrue(record["reconciliation"]["complete"])
        self.assertIn(f"{len(self.points)}/{len(self.points)} points ok", out)
        self.assertNotIn("FAIL:", err)
        self.assertNotIn("reconcile", err)
        self.assertTrue((self.tb.experiment_dir / "records" / f"{RECORD_ID}.md").exists())

    def test_recorded_failed_check_prints_and_records_same_failures(self) -> None:
        rc, out, err, record, counters = self._run(self._results(9.9), RECORD_ID)
        counters.assert_each_called_once(self, "recorded run, failed check")
        self.assertEqual(rc, 1)
        self.assertEqual(record["status"], "fail")
        printed = [line for line in err.splitlines() if line.startswith("FAIL: ")]
        self.assertEqual(printed,
                         [f"FAIL: {report.describe_failure(f)}"
                          for f in record["checks"]["failures"]])
        self.assertTrue(printed, "a failed check must print its FAIL lines")

    def test_recorded_missing_point_prints_and_records_same_reconciliation(self) -> None:
        rc, out, err, record, counters = self._run(self._results(0.5)[:-1], RECORD_ID)
        counters.assert_each_called_once(self, "recorded run, missing point")
        self.assertEqual(rc, 1)
        self.assertEqual(record["status"], "error")
        self.assertFalse(record["reconciliation"]["complete"])
        self.assertIn("results do not reconcile with the requested grid", err)
        self.assertEqual(record["reconciliation"]["missing"], 1)

    def test_no_write_evaluates_once_and_writes_no_evidence(self) -> None:
        for results, expected_rc in ((self._results(0.5), 0), (self._results(9.9), 1)):
            with self.subTest(rc=expected_rc):
                rc, out, err, record, counters = self._run(results, None)
                counters.assert_each_called_once(self, "--no-write run")
                self.assertEqual(rc, expected_rc)
                self.assertIsNone(record)
                self.assertIn("nothing recorded", out)
                for evidence in ("records", "corners", "netlist-snapshots"):
                    self.assertFalse(
                        (self.tb.experiment_dir / evidence).exists(),
                        f"--no-write must not create {evidence}/",
                    )

    def test_build_record_self_contained_without_analysis(self) -> None:
        record = report.build_record(
            self.tb, self.pdk, self.points, self._results(0.5), "ngspice-stub",
            self.tmp, RECORD_ID, "2099-01-01T00:00:00+00:00", 1.0, git=self.git,
        )
        self.assertEqual(record["status"], "pass")
        self.assertEqual(record["grid"]["points_ok"], len(self.points))

    def test_build_record_refuses_analysis_under_other_unswept_rules(self) -> None:
        analysis = report.analyze_grid(self.tb, self.points, self._results(0.5))
        with self.assertRaises(ValueError):
            report.build_record(
                self.tb, self.pdk, self.points, self._results(0.5), "ngspice-stub",
                self.tmp, RECORD_ID, "2099-01-01T00:00:00+00:00", 1.0,
                git=self.git, allow_unswept_axes=True, analysis=analysis,
            )


if __name__ == "__main__":
    unittest.main()
