"""Corner-bundle unit tests: every corner's deck really carries the
non-MOS families (issue #16).

The five built-in corners are per-family section bundles, and the whole
point of the bundles is that a generated deck includes a ``.lib`` card for
the diode, resistor and MIM-capacitor families at every corner -- the
condition the gf180mcu model library imposes, since its MOS sections alone
include no diode/resistor/capacitor models at all. These tests pin that
property without a simulator: they compose the deck for each corner (with a
stub PDK, so no install is needed) and assert the cards are present, one
per family, in declaration order. The end-to-end proof (the sections also
*do* something) lives in the selftest's per-family negative control and the
recorded smoke-5v bench, which need ngspice and the PDK.
"""

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sim.harness.corners import CORNERS, FAMILIES, PvtPoint, resolve_corners  # noqa: E402
from sim.harness.pdk import Pdk  # noqa: E402
from sim.harness.runner import compose_deck  # noqa: E402
from sim.harness.testbench import Testbench  # noqa: E402

MODEL_LIB_REL = "libs.tech/ngspice/sm141064.ngspice"


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
    fragment = tmp / "tb_stub.spice"
    fragment.write_text("* stub fragment\nvdd top 0 {vdd_val}\n", encoding="utf-8")
    return Testbench(
        directory=tmp,
        name="stub",
        netlist=fragment,
        nominal_supply_v=5.0,
        measure={"m": "i(vdd)"},
    )


class CornerBundleTests(unittest.TestCase):
    def test_five_corners_exist_with_one_section_per_family(self) -> None:
        for name in ("tt", "ff", "ss", "fs", "sf"):
            self.assertIn(name, CORNERS)
            sections = CORNERS[name].sections
            self.assertEqual(
                len(sections),
                len(FAMILIES),
                f"corner {name}: {sections!r} is not one section per family {FAMILIES!r}",
            )

    def test_ff_ss_skew_every_family(self) -> None:
        for skew in ("ff", "ss"):
            sections = CORNERS[skew].sections
            for family in ("res", "bjt", "diode", "moscap", "mimcap"):
                self.assertIn(f"{family}_{skew}", sections, f"{skew} must skew {family}")

    def test_fs_sf_skew_mos_only(self) -> None:
        for name in ("fs", "sf"):
            sections = CORNERS[name].sections
            self.assertIn(name, sections)
            for family in ("res", "bjt", "diode", "moscap", "mimcap"):
                self.assertIn(f"{family}_typical", sections)

    def test_deck_has_lib_card_per_family_at_every_corner(self) -> None:
        with tempfile.TemporaryDirectory() as tmpname:
            tmp = Path(tmpname)
            pdk = _stub_pdk(tmp)
            tb = _stub_testbench(tmp)
            model_lib = str((pdk.path / MODEL_LIB_REL))
            for corner in resolve_corners(["mos"]):
                deck = compose_deck(tb, pdk, PvtPoint(corner, 27.0, 5.0))
                cards = [
                    line for line in deck.splitlines()
                    if line.startswith(".lib") and model_lib in line
                ]
                self.assertEqual(
                    [line.rsplit(" ", 1)[1] for line in cards],
                    list(corner.sections),
                    f"corner {corner.name}: deck must emit one .lib card per "
                    f"family section, in declaration order",
                )
                for family_section in corner.sections:
                    self.assertIn(
                        f'.lib "{model_lib}" {family_section}',
                        deck,
                        f"corner {corner.name}: missing .lib card for {family_section}",
                    )

    def test_deck_names_the_pinned_sections_per_corner(self) -> None:
        expected = {
            "tt": ["typical", "res_typical", "bjt_typical", "diode_typical", "moscap_typical", "mimcap_typical"],
            "ss": ["ss", "res_ss", "bjt_ss", "diode_ss", "moscap_ss", "mimcap_ss"],
            "ff": ["ff", "res_ff", "bjt_ff", "diode_ff", "moscap_ff", "mimcap_ff"],
            "fs": ["fs", "res_typical", "bjt_typical", "diode_typical", "moscap_typical", "mimcap_typical"],
            "sf": ["sf", "res_typical", "bjt_typical", "diode_typical", "moscap_typical", "mimcap_typical"],
        }
        for name, sections in expected.items():
            self.assertEqual(list(CORNERS[name].sections), sections)

    def test_as_bundle_is_klt_sim_shape(self) -> None:
        bundle = CORNERS["ss"].as_bundle()
        self.assertEqual(bundle, {"name": "ss", "sections": list(CORNERS["ss"].sections)})
        self.assertEqual(bundle["sections"][0], "ss")
        self.assertIn("diode_ss", bundle["sections"])


if __name__ == "__main__":
    unittest.main()
