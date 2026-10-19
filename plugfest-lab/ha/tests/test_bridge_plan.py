"""Render the ODE schedule bridge's plan template outside Home Assistant.

Run: python3 -m unittest discover -s plugfest-lab/ha/tests  (needs jinja2 and PyYAML)

A small shim stands in for the Home Assistant template functions and filters
the plan uses (states, is_state, now, as_timestamp, float/round/int with HA's
signatures, is_number). The final check before deploying stays a render with
Home Assistant's own engine (ha_eval_template).
"""
import ast
import datetime as dt
import math
import unittest
from pathlib import Path

import yaml
from jinja2 import Environment

BRIDGE = Path(__file__).resolve().parents[1] / "bridge_automation.yaml"
NOW = 1792390963.0  # 19 Oct 2026 17:22:43 AEDT


def plan_template():
    return yaml.safe_load(BRIDGE.read_text())["actions"][0]["variables"]["plan"]


def _is_number(v):
    if isinstance(v, bool) or v is None:
        return False
    try:
        return math.isfinite(float(v)) and str(v).strip() != ""
    except (TypeError, ValueError):
        return False


def _float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        if default is None:
            raise
        return default


def _round(v, precision=0, method="common"):
    v, m = float(v), 10 ** precision
    if method == "floor":
        return math.floor(v * m) / m
    if method == "ceil":
        return math.ceil(v * m) / m
    return round(v, precision)


class _Now:
    def __init__(self, ts):
        self.ts = ts

    def timestamp(self):
        return self.ts


def render(payload, states, test_steps="", now=NOW):
    env = Environment(extensions=["jinja2.ext.loopcontrols"])
    env.filters.update(float=_float, round=_round, is_number=_is_number,
                       int=lambda v, d=0: int(float(v)) if _is_number(v) else d)
    env.tests.update(is_number=_is_number, mapping=lambda v: isinstance(v, dict),
                     number=lambda v: isinstance(v, (int, float)) and not isinstance(v, bool))
    full = dict(states, **{"input_text.lab_v2g_test_steps": test_steps})
    env.globals.update(states=lambda e: full.get(e, "unknown"), is_state=lambda e, s: full.get(e) == s,
                       now=lambda: _Now(now), state_attr=lambda e, a: None,
                       as_timestamp=lambda v: dt.datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp())
    out = env.from_string(plan_template()).render(trigger={"payload_json": payload}, false=False, true=True)
    return ast.literal_eval(out)


def iso(offset):
    return dt.datetime.fromtimestamp(NOW + offset, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def control(kind, start, end, value, multiplier=0):
    return {"effectiveStartInclusive": iso(start), "effectiveEndExclusive": iso(end),
            "derControlBase": {kind: {"value": value, "multiplier": multiplier}}}


def payload(energised=True):
    """DERC1-like 4.5 kW import and export limits, then a 12 kW import / 1.5 kW export control at +197 s."""
    return {"limit": {"opModImpLimW": 4500, "opModExpLimW": 4500, "opModConnect": True, "opModEnergize": energised},
            "schedules": {"opModImpLimW": [control("opModImpLimW", -3600, 197, 45, 2), control("opModImpLimW", 197, 3000, 120, 2)],
                          "opModExpLimW": [control("opModExpLimW", -3600, 197, 45, 2), control("opModExpLimW", 197, 3000, 15, 2)]}}


def site(solar, house=1000, export_mode=False, target=0):
    return {"input_boolean.lab_v2g_export": "on" if export_mode else "off",
            "input_number.lab_v2g_discharge_target": str(target),
            "input_number.lab_ac_default_limit": "4500", "input_number.lab_v2g_default_export_limit": "4500",
            "input_number.lab_house_load": str(house), "input_number.lab_ode_generation_limit": "-1",
            "sensor.home_power_production_now": str(solar), "input_boolean.lab_ode_energized": "on"}


def rows(plan):
    return [(p["startPeriod"], p["setpoint"], p["limit"], p["dischargeLimit"]) for p in plan["periods"]]


class ImportMode(unittest.TestCase):
    def test_night_charges_at_import_limit_less_house_load(self):
        # 4,500 - 1.05 x 1,000 = 3,450 W, so house + EV stays within the 4.5 kW import limit.
        plan = render(payload(), site(solar=0))
        self.assertEqual(rows(plan)[0], (0, 3450, 3450, 0))
        self.assertEqual(rows(plan)[1], (198, 10950, 10950, 0))

    def test_day_adds_the_least_expected_solar(self):
        # 4,500 + 0.95 x 7,191 - 1,050 = 10,281 -> 10,280 W (rounded down to 10 W).
        self.assertEqual(rows(render(payload(), site(solar=7191)))[0], (0, 10280, 10280, 0))

    def test_never_above_25_kw(self):
        self.assertEqual(rows(render(payload(), site(solar=15000, house=0)))[1][1], 25000)

    def test_deenergised_is_zero_whatever_the_solar(self):
        self.assertEqual(rows(render(payload(energised=False), site(solar=7191)))[0], (0, 0, 0, 0))

    def test_headroom_change_changes_the_signature(self):
        a = render(payload(), site(solar=0))["sig"]
        b = render(payload(), site(solar=0, house=1200))["sig"]
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith("h-10|"))


class ExportMode(unittest.TestCase):
    def test_discharge_at_target_clipped_by_export_ceiling(self):
        plan = render(payload(), site(solar=7191, export_mode=True, target=7000))
        self.assertEqual(rows(plan)[0], (0, -4500, 4500, -4500))
        self.assertEqual(rows(plan)[-1][1:], (-1500, 12000, -1500))
        self.assertTrue(plan["sig"].startswith("x7000|"))


class TxProfileTest(unittest.TestCase):
    STEPS = f"{int(NOW) + 20}|60|20000,-20000,6000,-5000,0"

    def test_steps_clamped_to_site_headroom(self):
        plan = render(payload(), site(solar=7191), self.STEPS)
        self.assertTrue(plan["test"])
        self.assertEqual(rows(plan), [
            (0, 10280, 10280, 0),       # before the test: import-mode headroom
            (21, 10280, 10280, 0),      # +20 kW -> charge headroom
            (81, 0, 10280, 0),          # -20 kW -> no discharge headroom (solar fills the export limit)
            (141, 6000, 10280, 0),
            (198, 6000, 17780, 0),      # the 12 kW control raises the charge headroom mid-step
            (201, 0, 17780, 0),         # -5 kW -> 0
            (261, 0, 17780, 0),
            (321, 17780, 17780, 0),     # test over: import-mode headroom again
        ])

    def test_discharge_allowed_without_solar(self):
        plan = render(payload(), site(solar=0), f"{int(NOW)}|60|-20000,-1000")
        self.assertEqual(rows(plan)[:2], [(0, -4500, 3450, -4500), (61, -1000, 3450, -4500)])

    def test_empty_invalid_or_finished_steps_are_ignored(self):
        normal = render(payload(), site(solar=7191))
        for steps in ("", "unknown", "garbage|x|1", f"{int(NOW) - 1000}|60|1,2", f"{int(NOW)}|0|1"):
            with self.subTest(steps=steps):
                plan = render(payload(), site(solar=7191), steps)
                self.assertFalse(plan["test"])
                self.assertEqual(plan["periods"], normal["periods"])


if __name__ == "__main__":
    unittest.main()
