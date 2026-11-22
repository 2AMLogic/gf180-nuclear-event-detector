"""Process / voltage / temperature corner definitions and PVT grid mechanics.

GENERIC CORE:

- The classic five-corner process sweep (``tt``, ``ff``, ``ss``, ``fs``,
  ``sf``) registered below as the default ``CORNER_SETS["mos"]``. A corner is
  a *bundle*: exactly one ``.lib`` section per entry in :data:`FAMILIES`,
  because this PDK's model library has no all-device corner section -- each
  device family ships its own (see the EXTENSION POINT table below).
  ``CORNER_SETS["tt"]`` is the reduced, single-corner smoke-test set (not a
  valid evidence matrix on its own).
- :class:`Corner`, :class:`PvtPoint`, :func:`build_grid`, :func:`supply_points`,
  :func:`resolve_corners` -- the PVT-grid arithmetic itself (a corner ×
  temperature × supply full factorial, in a stable order).
- :func:`select_corner_names` -- which selection a run uses: an explicit
  ``--corners`` override, else the testbench manifest's ``corners``, else
  :data:`DEFAULT_CORNER_SET`. Empty or unknown selections are a
  :class:`CornerSelectionError`, never a silent fallback.
- :func:`sabotage` -- the harness's negative control: forces every corner's
  every-family sections to the all-typical bundle so a corner-runner
  self-test can prove that switching corners actually changes what gets
  simulated, rather than silently simulating typical everywhere no matter
  what was asked for -- per family, not just for MOS.

EXTENSION POINT -- corner sections don't generalize across PDKs (a PDK's
``.lib`` section names for "fast", "slow", or a device family other than MOS
are PDK-specific), and *which* additional corners matter is block-specific
(a SAR ADC cares about CDAC capacitor corners; a bandgap cares about
resistor and BJT corners; plenty of blocks need only the five classic
corners as-is). Two ways to extend:

1. Edit the ``sections`` tuples on the built-in :data:`CORNERS` entries if
   this PDK's model library uses different section names than the ones
   registered below (that is the one edit new to this PDK; the gf180mcu
   spellings and the revision they were checked against are recorded in the
   :data:`CORNERS` comment).
2. Call :func:`register_corner` (and optionally :func:`register_corner_set`)
   to add block-specific corners on top -- see
   ``gf180-sar-adc/sim/harness/corners.py`` for a worked example that adds
   MiM/MOS-cap-dominated corners for a CDAC-heavy block.

gf180mcu family sections, checked against the pinned install's
``libs.tech/ngspice/sm141064.ngspice`` (open_pdks
``f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7``, the revision
``sim/toolchain.json`` pins), 2026-11-22 -- ported by pattern from
``2AMLogic/gf180-comparator``'s ``sim/harness/corners.py``:

    MOS       typical | ff | ss | fs | sf
    resistor  res_typical | res_ss | res_ff
    BJT       bjt_typical | bjt_ss | bjt_ff
    diode     diode_typical | diode_ss | diode_ff
    MOS cap   moscap_typical | moscap_ss | moscap_ff
    MIM cap   mimcap_typical | mimcap_ss | mimcap_ff

Only the MOS family ships ``fs``/``sf`` sections, so those two corners skew
MOS only and leave every other family at ``*_typical``. Bundles carry their
sections in :data:`FAMILIES` order, and :meth:`Corner.as_bundle` serialises
them as ``klt sim`` ``corners.process`` bundle objects (``{"name": ...,
"sections": [...]}``), so the same corner map drives both this harness and
a fleet ``klt sim`` request without a second translation layer.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

# Default PVT axes. A block's own CLAUDE.md / spec should state its PVT
# requirement explicitly; these are reasonable open-PDK defaults to start
# from, not a substitute for that statement.
DEFAULT_TEMPERATURES_C: tuple[float, ...] = (-40.0, 27.0, 125.0)
DEFAULT_SUPPLY_TOLERANCE: float = 0.10  # +/-10 %
DEFAULT_NOMINAL_SUPPLY_V: float = 1.8   # FILL: this block's nominal supply

#: Device families in the order their ``.lib`` sections are included in the
#: generated deck (see runner.compose_deck). Each corner bundles exactly one
#: section per family; a block that needs a family the core does not sweep
#: adds it here first, then gives every corner a section for it.
FAMILIES: tuple[str, ...] = ("mos", "res", "bjt", "diode", "moscap", "mimcap")


def _bundle(mos: str, res: str, bjt: str, diode: str, moscap: str, mimcap: str) -> tuple[str, ...]:
    """One section per :data:`FAMILIES` entry, in :data:`FAMILIES` order."""
    return (mos, res, bjt, diode, moscap, mimcap)


#: The all-typical bundle (what ``tt`` -- and the :func:`sabotage` negative
#: control -- simulate).
_TYPICAL = _bundle(
    mos="typical",
    res="res_typical",
    bjt="bjt_typical",
    diode="diode_typical",
    moscap="moscap_typical",
    mimcap="mimcap_typical",
)


@dataclass(frozen=True)
class Corner:
    """A named process corner: an ordered list of model ``.lib`` sections,
    one per entry in :data:`FAMILIES`."""

    name: str
    sections: tuple[str, ...]
    description: str = ""

    def as_bundle(self) -> dict:
        """This corner as a ``klt sim`` ``corners.process`` bundle object.

        Emits ``{"name": <name>, "sections": [...]}`` -- the request shape
        klayout-tools' corner runner expands into one ``.lib`` card per
        section, in declaration order (klayout-tools ``docs/cli/sim.md`` ->
        "Corner axes"). Serialising every :data:`CORNERS` entry this way
        yields a ``corners.process`` axis that simulates the identical
        section bundles this harness does, with no second corner map to
        keep in step.
        """
        return {"name": self.name, "sections": list(self.sections)}


def _all(skew: str, description: str) -> Corner:
    """Global corner: every device family skewed the same direction."""
    if skew not in ("ff", "ss"):  # pragma: no cover - programming error
        raise ValueError(f"no global {skew!r} bundle exists in this PDK")
    return Corner(
        name=skew,
        sections=_bundle(
            mos=skew,
            res=f"res_{skew}",
            bjt=f"bjt_{skew}",
            diode=f"diode_{skew}",
            moscap=f"moscap_{skew}",
            mimcap=f"mimcap_{skew}",
        ),
        description=description,
    )


def _mos_only(name: str, mos_section: str, description: str) -> Corner:
    """MOS skewed, every other family at typical (this PDK ships no
    ``fs``/``sf`` sections for the non-MOS families)."""
    return Corner(name=name, sections=(mos_section,) + _TYPICAL[1:], description=description)


#: The classic five corners as per-family section bundles. gf180mcu edit
#: (the one PDK-specific edit this package's docstring names): the model
#: library ``libs.tech/ngspice/sm141064.ngspice`` names its MOS typical
#: section ``typical`` (not ``tt``) and ships each non-MOS family as its own
#: ``<family>_typical``/``<family>_ss``/``<family>_ff`` sections with no
#: ``fs``/``sf`` variant -- the full table is in this module's docstring.
#: Verified against the open_pdks ``f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7``
#: install (the revision ``sim/toolchain.json`` pins), 2026-11-22.
CORNERS: dict[str, Corner] = {
    "tt": Corner("tt", _TYPICAL, "every device family typical"),
    "ff": _all("ff", "every device family fast"),
    "ss": _all("ss", "every device family slow"),
    "fs": _mos_only("fs", "fs", "fast NMOS / slow PMOS; other families typical"),
    "sf": _mos_only("sf", "sf", "slow NMOS / fast PMOS; other families typical"),
}

CORNER_SETS: dict[str, tuple[str, ...]] = {
    # Minimum bar for a quick smoke run. Not a valid evidence matrix on its own.
    "tt": ("tt",),
    # The five classic MOS corners -- the default.
    "mos": ("tt", "ff", "ss", "fs", "sf"),
}
DEFAULT_CORNER_SET = "mos"


def register_corner(
    name: str, sections: tuple[str, ...], description: str = "", *, sets: tuple[str, ...] = ()
) -> None:
    """Extension point: add a block-specific corner (and optionally the
    corner set(s) it belongs to) on top of the generic core.

    ``sections`` must have one entry per :data:`FAMILIES` in order -- add to
    ``FAMILIES`` first if this corner needs a device family the core does not
    already sweep (e.g. a capacitor or resistor family).
    """
    if len(sections) != len(FAMILIES):
        raise ValueError(
            f"corner {name!r}: {len(sections)} section(s) given, "
            f"expected one per family {FAMILIES!r}"
        )
    CORNERS[name] = Corner(name=name, sections=sections, description=description)
    for set_name in sets:
        CORNER_SETS[set_name] = CORNER_SETS.get(set_name, ()) + (name,)


def register_corner_set(name: str, corner_names: tuple[str, ...]) -> None:
    """Extension point: name a group of (already-registered) corners."""
    unknown = [c for c in corner_names if c not in CORNERS]
    if unknown:
        raise KeyError(f"corner set {name!r} references unknown corner(s): {unknown}")
    CORNER_SETS[name] = tuple(corner_names)


class CornerSelectionError(KeyError, ValueError):
    """A corner selection that cannot be resolved: empty, blank, or naming a
    corner / corner set that is not registered.

    Subclasses ``KeyError`` (what :func:`resolve_corners` raised for unknown
    names before) and ``ValueError`` (what manifest validation raises), so
    existing ``except`` clauses keep working. ``str()`` is the plain message,
    not ``KeyError``'s quoted repr, so a CLI can print it as-is.
    """

    def __str__(self) -> str:
        return str(self.args[0]) if self.args else ""


def parse_corner_list(text: str) -> list[str]:
    """Split a comma-separated ``--corners`` value into names.

    Surrounding whitespace is ignored; an empty value or an empty element
    (``""``, ``"mos,"``, ``" , "``) is a :class:`CornerSelectionError` rather
    than silently meaning "the default".
    """
    names = [part.strip() for part in text.split(",")]
    if not any(names):
        raise CornerSelectionError("empty corner selection; name at least one corner or corner set")
    if not all(names):
        raise CornerSelectionError(f"corner selection {text!r} contains an empty name")
    return names


def select_corner_names(
    cli_names: list[str] | tuple[str, ...] | None,
    manifest_names: list[str] | tuple[str, ...] | None,
) -> list[str]:
    """Which corner / corner-set names a run should use.

    Precedence: an explicit CLI selection (``cli_names`` not ``None``) wins;
    otherwise the testbench manifest's ``corners`` selection; otherwise the
    generic :data:`DEFAULT_CORNER_SET`. A selection that is present but
    empty is an error, never a fallback to the next source.
    """
    for source, names in (("--corners", cli_names), ("manifest 'corners'", manifest_names)):
        if names is None:
            continue
        names = list(names)
        if not names:
            raise CornerSelectionError(f"{source}: empty corner selection")
        return names
    return [DEFAULT_CORNER_SET]


def resolve_corners(names: list[str] | tuple[str, ...] | None) -> list[Corner]:
    """Turn a list of corner *or* corner-set names into Corner objects.

    ``None`` means the generic :data:`DEFAULT_CORNER_SET`. An empty list, a
    blank name, or a name that is neither a registered corner nor a
    registered corner set raises :class:`CornerSelectionError`.
    """
    if names is None:
        names = [DEFAULT_CORNER_SET]
    names = list(names)
    if not names:
        raise CornerSelectionError("empty corner selection; name at least one corner or corner set")
    resolved: list[Corner] = []
    seen: set[str] = set()
    for name in names:
        if not isinstance(name, str) or not name.strip():
            raise CornerSelectionError(f"invalid corner name {name!r}")
        expanded = CORNER_SETS.get(name, (name,))
        for corner_name in expanded:
            if corner_name in seen:
                continue
            if corner_name not in CORNERS:
                raise CornerSelectionError(
                    f"unknown corner {corner_name!r}; "
                    f"known corners: {', '.join(sorted(CORNERS))}; "
                    f"known sets: {', '.join(sorted(CORNER_SETS))}"
                )
            seen.add(corner_name)
            resolved.append(CORNERS[corner_name])
    return resolved


def sabotage(corner_list: list[Corner]) -> list[Corner]:
    """Return the same corner *names* with every family's section forced to
    the all-typical bundle.

    This is the harness's negative control, not a feature: it reproduces the
    exact silent failure mode a corner sweep is most exposed to -- a runner
    that appears to sweep process corners but actually simulates typical
    everywhere (wrong model include, ignored parameter, wrong section name).
    A self-test should run once normally and once sabotaged; the sabotaged
    run's per-axis sensitivity checks (see report.axis_sensitivity) MUST
    fail. If they pass, corner switching is not taking effect and every
    downstream evidence record is worthless. Force ``--no-write`` whenever
    this is used -- a sabotaged run must never enter the evidence tree.
    """
    typical = CORNERS["tt"].sections
    return [
        Corner(name=corner.name, sections=typical, description=f"SABOTAGED ({corner.description})")
        for corner in corner_list
    ]


def supply_points(
    nominal_v: float = DEFAULT_NOMINAL_SUPPLY_V,
    tolerance: float = DEFAULT_SUPPLY_TOLERANCE,
) -> list[float]:
    """Nominal supply and its +/- tolerance rails, low to high."""
    if tolerance <= 0:
        return [round(nominal_v, 6)]
    return [
        round(nominal_v * (1.0 - tolerance), 6),
        round(nominal_v, 6),
        round(nominal_v * (1.0 + tolerance), 6),
    ]


def _format_supply(vdd: float) -> str:
    """Shortest fixed-point text of ``vdd`` with >= 2 and <= 6 decimals."""
    text = f"{vdd:.6f}".rstrip("0")
    whole, _, frac = text.partition(".")
    return f"{whole}.{frac.ljust(2, '0')}"


class DuplicateArtifactError(ValueError):
    """Two grid points map to the same per-point artifact id."""


def check_unique_artifact_ids(points: "list[PvtPoint]") -> None:
    """Raise :class:`DuplicateArtifactError` if any two points share a
    ``corner_id`` (and so would overwrite each other's deck and log)."""
    seen: dict[str, PvtPoint] = {}
    dupes: list[str] = []
    for point in points:
        cid = point.corner_id
        if cid in seen:
            dupes.append(cid)
        seen[cid] = point
    if dupes:
        raise DuplicateArtifactError(
            "duplicate PVT artifact id(s) in grid: "
            + ", ".join(sorted(set(dupes)))
            + "; remove duplicate corners/temperatures/supplies"
        )


@dataclass(frozen=True)
class PvtPoint:
    """One point in the PVT grid -- exactly one ngspice invocation."""

    corner: Corner
    temp_c: float
    vdd: float
    index: int = field(default=0, compare=False)

    @property
    def corner_id(self) -> str:
        """``<process>_<temp>c_<supply>v`` -- the per-corner log/evidence id.

        The supply keeps at least two decimals (``1.80``) and grows to as many
        as needed (up to 6, matching :func:`supply_points` rounding) so close
        supplies such as 1.801 and 1.804 get distinct ids. Grids whose
        supplies are exact to two decimals (the defaults) keep their
        historical ids.
        """
        return f"{self.corner.name}_{self.temp_c:g}c_{_format_supply(self.vdd)}v"

    def as_dict(self) -> dict:
        return {
            "corner": self.corner.name,
            "corner_sections": list(self.corner.sections),
            "temp_c": self.temp_c,
            "vdd": self.vdd,
            "corner_id": self.corner_id,
        }


def build_grid(
    corners: list[Corner],
    temperatures: list[float] | tuple[float, ...],
    supplies: list[float],
) -> list[PvtPoint]:
    """Full factorial P x V x T grid, in a stable, reproducible order."""
    return [
        PvtPoint(corner=corner, temp_c=float(temp), vdd=float(vdd), index=i)
        for i, (corner, temp, vdd) in enumerate(
            itertools.product(corners, temperatures, supplies)
        )
    ]
