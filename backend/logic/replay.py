"""Independent replay validator for the GridWise preliminary.

This module is the scoring oracle. It reimplements the audit the judge performs:
given a request and a returned response, it replays the 24-hour schedule hour by
hour against the GridWise rules in ``problem.md`` and reports precise violations.

It deliberately imports nothing from the rest of ``backend`` and accepts plain
dicts. Three reasons:

* It is an *independent* check, derived from the specification rather than from
  the optimizer's assumptions. A validator sharing code with the thing it
  validates inherits its misreadings.
* It therefore has no build-order dependency on any other workstream.
* The in-request final check and the offline harness call the same function, so
  the harness tests exactly what ships.

Two modes, and the distinction is the point:

* ``directives=None`` -- Mode A, self-consistent. Replays against the
  interpretation the service itself returned.
* ``directives=[...]`` -- Mode B, ground truth. Replays against the organizer's
  directives. This is what the judge does, and the only mode that separates
  "interpreted correctly but applied wrong" from "interpreted wrong".
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

TOL = 0.01  # absolute tolerance, kWh / BDT -- problem.md section 7

DIRECTIVE_TYPES = (
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
)

BATTERY_ACTIONS = ("charge", "discharge", "idle")

_ADJUSTMENT_KEYS = {
    "solar_reduction": ("hours", "factor"),
    "minimum_battery_reserve": ("hours", "minimum_energy_kwh"),
    "no_charge_window": ("hours",),
    "no_discharge_window": ("hours",),
    "max_grid_window": ("hours", "max_grid_kwh"),
}

_TOP_LEVEL_FIELDS = (
    "scenario_id",
    "directive_interpretation",
    "hourly_plan",
    "total_grid_kwh",
    "total_cost_bdt",
    "peak_grid_kwh",
    "plan_summary",
)

_PLAN_FIELDS = (
    "hour",
    "grid_kwh",
    "solar_used_kwh",
    "battery_action",
    "battery_kwh",
    "battery_energy_after_kwh",
)

_INTERPRETATION_FIELDS = (
    "note_index",
    "applies",
    "directive_type",
    "structured_adjustment",
    "explanation",
)

_BATTERY_FIELDS = (
    "capacity_kwh",
    "initial_energy_kwh",
    "minimum_energy_kwh",
    "max_charge_kwh_per_hour",
    "max_discharge_kwh_per_hour",
)


@dataclass
class ReplayResult:
    """Contract C-6."""

    ok: bool
    violations: list[str] = field(default_factory=list)

    @property
    def root(self) -> str | None:
        """The first violation. Later ones are often downstream of it."""
        return self.violations[0] if self.violations else None

    def report(self, limit: int = 12) -> str:
        if self.ok:
            return "PASS"
        head = "\n".join("  - " + v for v in self.violations[:limit])
        extra = len(self.violations) - limit
        if extra > 0:
            head += "\n  ... and {} more".format(extra)
        return "FAIL ({} violations)\n{}".format(len(self.violations), head)


def _is_num(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _hours_problem(hours: object, label: str) -> str | None:
    """Validate an hours array: unique integers 0-23 in ascending order."""
    if not isinstance(hours, list) or not hours:
        return label + ": hours must be a non-empty list"
    for h in hours:
        if isinstance(h, bool) or not isinstance(h, int):
            return "{}: hours contains non-integer {!r}".format(label, h)
        if not 0 <= h <= 23:
            return "{}: hour {} outside 0-23".format(label, h)
    if len(set(hours)) != len(hours):
        return "{}: hours contains duplicates {}".format(label, hours)
    if hours != sorted(hours):
        return "{}: hours not in ascending order {}".format(label, hours)
    return None


def validate_request(request: dict) -> list[str]:
    """Contract C-1. Used by the harness; the API enforces this with Pydantic."""
    v: list[str] = []
    notes = request.get("operator_notes")
    if not isinstance(notes, list) or not 1 <= len(notes) <= 3:
        v.append("request: operator_notes must be a list of 1-3 entries")
    elif any(not isinstance(n, str) or not n.strip() for n in notes):
        v.append("request: operator_notes entries must be non-empty strings")

    hours = request.get("hours")
    if not isinstance(hours, list) or len(hours) != 24:
        v.append("request: hours must contain exactly 24 entries")
    else:
        got = sorted(h.get("hour") for h in hours)
        if got != list(range(24)):
            v.append("request: hour values must be exactly 0-23, unique")

    battery = request.get("battery")
    if not isinstance(battery, dict):
        v.append("request: battery object missing")
    else:
        for k in _BATTERY_FIELDS:
            if not _is_num(battery.get(k)) or battery[k] < 0:
                v.append("request: battery." + k + " must be finite and non-negative")
    return v


def validate_directives(directives: object, note_count: int, capacity: float) -> list[str]:
    """Interpretation schema and guardrails -- problem.md sections 10 and 11."""
    v: list[str] = []
    if not isinstance(directives, list):
        return ["directive_interpretation: not a list"]
    if len(directives) != note_count:
        v.append(
            "directive_interpretation: {} entries for {} notes".format(
                len(directives), note_count
            )
        )

    seen: list[int] = []
    for pos, e in enumerate(directives):
        if not isinstance(e, dict):
            v.append("directive_interpretation[{}]: not an object".format(pos))
            continue
        label = "note {}".format(e.get("note_index", "@" + str(pos)))
        for name in _INTERPRETATION_FIELDS:
            if name not in e:
                v.append("{}: missing field '{}'".format(label, name))

        idx = e.get("note_index")
        if isinstance(idx, bool) or not isinstance(idx, int):
            v.append(label + ": note_index must be an integer")
        else:
            seen.append(idx)

        dtype = e.get("directive_type")
        applies = e.get("applies")
        adj = e.get("structured_adjustment")

        if dtype not in DIRECTIVE_TYPES:
            v.append("{}: unsupported directive_type {!r}".format(label, dtype))
            continue

        # The C-2 invariant, enforced rather than assumed.
        if dtype == "no_op":
            if applies is not False:
                v.append(
                    "{}: no_op requires applies=false, got {!r}".format(label, applies)
                )
            if adj is not None:
                v.append(label + ": no_op requires structured_adjustment=null")
            continue
        if applies is not True:
            v.append(
                "{}: {} requires applies=true, got {!r}".format(label, dtype, applies)
            )
        if not isinstance(adj, dict):
            v.append("{}: {} requires a structured_adjustment object".format(label, dtype))
            continue

        for k in _ADJUSTMENT_KEYS[dtype]:
            if k not in adj:
                v.append("{}: {} missing '{}'".format(label, dtype, k))
        problem = _hours_problem(adj.get("hours"), label)
        if problem:
            v.append(problem)

        if dtype == "solar_reduction":
            factor = adj.get("factor")
            if not _is_num(factor) or not 0.0 <= factor <= 1.0:
                v.append(
                    "{}: factor {!r} must be a number in [0,1]".format(label, factor)
                )
        elif dtype == "minimum_battery_reserve":
            m = adj.get("minimum_energy_kwh")
            if not _is_num(m) or m < 0:
                v.append(
                    "{}: minimum_energy_kwh {!r} must be finite and >= 0".format(label, m)
                )
            elif m > capacity + TOL:
                v.append(
                    "{}: minimum_energy_kwh {} exceeds capacity {}".format(
                        label, m, capacity
                    )
                )
        elif dtype == "max_grid_window":
            g = adj.get("max_grid_kwh")
            if not _is_num(g) or g < 0:
                v.append("{}: max_grid_kwh {!r} must be finite and >= 0".format(label, g))

    if seen:
        expected = list(range(note_count))
        if sorted(seen) != expected:
            v.append(
                "directive_interpretation: note_index coverage {} != required {}".format(
                    sorted(seen), expected
                )
            )
        elif seen != sorted(seen):
            v.append("directive_interpretation: note_index not ascending " + str(seen))
    return v


def compile_constraints(request: dict, directives: list) -> dict:
    """Directives to per-hour numeric bounds. Contract C-3, independently derived.

    Merge rules resolve overlaps in the direction that satisfies every individual
    directive at once: reserves take the maximum, grid caps the minimum, and two
    solar reductions on one hour take the *minimum factor* rather than multiplying.
    Multiplying two independent 0.5s to 0.25 over-reduces and could tighten the
    ceiling below what the judge computes; the minimum satisfies every individual
    directive's ceiling under any reading.
    """
    hours = sorted(request["hours"], key=lambda x: x["hour"])
    battery = request["battery"]
    eff = [float(h["solar_kwh"]) for h in hours]
    charge_ub = [float(battery["max_charge_kwh_per_hour"])] * 24
    discharge_ub = [float(battery["max_discharge_kwh_per_hour"])] * 24
    grid_ub = [math.inf] * 24
    energy_lb = [float(battery["minimum_energy_kwh"])] * 24

    for e in directives:
        if not isinstance(e, dict):
            continue
        dtype = e.get("directive_type")
        adj = e.get("structured_adjustment")
        if dtype in (None, "no_op") or not isinstance(adj, dict):
            continue
        hrs = [h for h in adj.get("hours", []) if isinstance(h, int) and 0 <= h <= 23]
        if dtype == "solar_reduction" and _is_num(adj.get("factor")):
            for h in hrs:
                eff[h] = min(eff[h], float(hours[h]["solar_kwh"]) * float(adj["factor"]))
        elif dtype == "minimum_battery_reserve" and _is_num(adj.get("minimum_energy_kwh")):
            for h in hrs:
                energy_lb[h] = max(energy_lb[h], float(adj["minimum_energy_kwh"]))
        elif dtype == "no_charge_window":
            for h in hrs:
                charge_ub[h] = 0.0
        elif dtype == "no_discharge_window":
            for h in hrs:
                discharge_ub[h] = 0.0
        elif dtype == "max_grid_window" and _is_num(adj.get("max_grid_kwh")):
            for h in hrs:
                grid_ub[h] = min(grid_ub[h], float(adj["max_grid_kwh"]))

    return {
        "eff_solar": eff,
        "charge_ub": charge_ub,
        "discharge_ub": discharge_ub,
        "grid_ub": grid_ub,
        "energy_lb": energy_lb,
    }


def _window_hours(directives: list, dtype: str) -> set:
    out = set()
    for e in directives:
        if isinstance(e, dict) and e.get("directive_type") == dtype:
            adj = e.get("structured_adjustment")
            if isinstance(adj, dict):
                out.update(h for h in adj.get("hours", []) if isinstance(h, int))
    return out


def replay(request: dict, response: dict, directives: list | None = None) -> ReplayResult:
    """Replay a returned schedule against the GridWise rules.

    ``directives=None`` uses the response's own interpretation (Mode A).
    Passing ``directives`` replays against ground truth (Mode B).
    """
    v: list[str] = []

    for name in _TOP_LEVEL_FIELDS:
        if name not in response:
            v.append("response: missing top-level field '" + name + "'")
    if v:
        return ReplayResult(False, v)

    if response["scenario_id"] != request.get("scenario_id"):
        v.append(
            "scenario_id: response {!r} does not echo request {!r}".format(
                response["scenario_id"], request.get("scenario_id")
            )
        )

    notes = request.get("operator_notes") or []
    battery = request["battery"]
    capacity = float(battery["capacity_kwh"])
    initial = float(battery["initial_energy_kwh"])

    v.extend(validate_directives(response["directive_interpretation"], len(notes), capacity))

    applied = response["directive_interpretation"] if directives is None else directives
    if directives is not None:
        v.extend(validate_directives(directives, len(notes), capacity))
    if not isinstance(applied, list):
        return ReplayResult(False, v)

    plan = response["hourly_plan"]
    if not isinstance(plan, list) or len(plan) != 24:
        count = len(plan) if isinstance(plan, list) else "n/a"
        v.append("hourly_plan: must contain exactly 24 entries, got {}".format(count))
        return ReplayResult(False, v)
    plan = sorted(plan, key=lambda p: p.get("hour", -1))
    if [p.get("hour") for p in plan] != list(range(24)):
        v.append("hourly_plan: hour values must be exactly 0-23, unique")
        return ReplayResult(False, v)

    bounds = compile_constraints(request, applied)
    no_charge = _window_hours(applied, "no_charge_window")
    no_discharge = _window_hours(applied, "no_discharge_window")
    hours = {h["hour"]: h for h in request["hours"]}

    energy = initial
    desynced = False
    total_grid = 0.0
    total_cost = 0.0
    peak_grid = 0.0

    for h in range(24):
        p = plan[h]
        for name in _PLAN_FIELDS:
            if name not in p:
                v.append("h{}: missing plan field '{}'".format(h, name))
        action = p.get("battery_action")
        amount = p.get("battery_kwh")
        grid = p.get("grid_kwh")
        solar = p.get("solar_used_kwh")
        reported_e = p.get("battery_energy_after_kwh")

        numeric_ok = True
        for name, val in (
            ("grid_kwh", grid),
            ("solar_used_kwh", solar),
            ("battery_kwh", amount),
            ("battery_energy_after_kwh", reported_e),
        ):
            if not _is_num(val):
                v.append("h{}: {} must be a finite number, got {!r}".format(h, name, val))
                numeric_ok = False
        if not numeric_ok:
            continue

        for name, val in (
            ("grid_kwh", grid),
            ("solar_used_kwh", solar),
            ("battery_kwh", amount),
        ):
            if val < -TOL:
                v.append("h{}: {} is negative ({})".format(h, name, val))

        if action not in BATTERY_ACTIONS:
            v.append("h{}: battery_action {!r} not one of {}".format(h, action, BATTERY_ACTIONS))
            charge = 0.0
            discharge = 0.0
        else:
            if action == "idle" and abs(amount) > TOL:
                v.append("h{}: battery_action is idle but battery_kwh is {}".format(h, amount))
            charge = amount if action == "charge" else 0.0
            discharge = amount if action == "discharge" else 0.0

        demand = float(hours[h]["demand_kwh"])
        tariff = float(hours[h]["tariff_bdt_per_kwh"])

        if solar > bounds["eff_solar"][h] + TOL:
            v.append(
                "h{}: solar_used_kwh {} exceeds effective solar {}".format(
                    h, solar, bounds["eff_solar"][h]
                )
            )

        balance = (grid + solar + discharge) - (demand + charge)
        if abs(balance) > TOL:
            v.append("h{}: ENERGY BALANCE violated by {:+.4f}".format(h, balance))

        if charge > bounds["charge_ub"][h] + TOL:
            if h in no_charge:
                v.append("h{}: charge {} in no_charge_window hour".format(h, charge))
            else:
                v.append(
                    "h{}: charge {} exceeds charge limit {}".format(
                        h, charge, bounds["charge_ub"][h]
                    )
                )
        if discharge > bounds["discharge_ub"][h] + TOL:
            if h in no_discharge:
                v.append("h{}: discharge {} in no_discharge_window hour".format(h, discharge))
            else:
                v.append(
                    "h{}: discharge {} exceeds discharge limit {}".format(
                        h, discharge, bounds["discharge_ub"][h]
                    )
                )
        if grid > bounds["grid_ub"][h] + TOL:
            v.append(
                "h{}: grid_kwh {} exceeds grid cap {}".format(h, grid, bounds["grid_ub"][h])
            )

        energy = energy + charge - discharge
        if abs(energy - reported_e) > TOL:
            if not desynced:
                v.append(
                    "h{}: battery_energy_after_kwh {} does not match the trajectory "
                    "({:.4f} from the reported actions)".format(h, reported_e, energy)
                )
                desynced = True
            # Re-sync to the reported trajectory so one arithmetic slip does not
            # cascade into twenty downstream violations and bury the root cause.
            energy = float(reported_e)

        if energy < bounds["energy_lb"][h] - TOL:
            v.append(
                "h{}: battery energy {} below active minimum {}".format(
                    h, energy, bounds["energy_lb"][h]
                )
            )
        if energy > capacity + TOL:
            v.append("h{}: battery energy {} above capacity {}".format(h, energy, capacity))

        total_grid += grid
        total_cost += grid * tariff
        peak_grid = max(peak_grid, grid)

    final_e = plan[23].get("battery_energy_after_kwh")
    if _is_num(final_e) and abs(final_e - initial) > TOL:
        v.append(
            "NEUTRALITY: final battery_energy_after_kwh {} != initial_energy_kwh {}".format(
                final_e, initial
            )
        )

    for name, computed in (
        ("total_grid_kwh", total_grid),
        ("total_cost_bdt", total_cost),
        ("peak_grid_kwh", peak_grid),
    ):
        reported = response.get(name)
        if not _is_num(reported):
            v.append("{}: must be a finite number, got {!r}".format(name, reported))
        elif abs(reported - computed) > TOL:
            v.append(
                "{}: reported {} != {:.4f} recomputed from hourly_plan".format(
                    name, reported, computed
                )
            )

    return ReplayResult(not v, v)


def recomputed_cost(request: dict, response: dict) -> float:
    """Grid cost recomputed from hourly_plan -- the judge's cost, not ours."""
    tariff = {h["hour"]: float(h["tariff_bdt_per_kwh"]) for h in request["hours"]}
    return sum(float(p["grid_kwh"]) * tariff[p["hour"]] for p in response["hourly_plan"])
