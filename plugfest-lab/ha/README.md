# Home Assistant lab automations on the Green

These are the Home Assistant pieces that turn CSIP-AUS limits into OCPP 2.1 charging profiles on the
Green. They are UI-managed on the Green; this folder is their source of truth, so changes are reviewed
here first.

| File | On the Green |
|---|---|
| [`bridge_automation.yaml`](bridge_automation.yaml) | `automation.lab_ode_schedule_to_ac_everest_prototype_v2`, the ODE schedule bridge |
| [`txprofile_test_script.yaml`](txprofile_test_script.yaml) | `script.lab_v2g_txprofile_test`, a stepped TxProfile test run through the bridge |
| [`synthetic_site_automation.yaml`](synthetic_site_automation.yaml) | `automation.lab_open_meteo_solar_forecast_to_ode_inverters_1`, the synthetic 10 kW solar inverter (`inverters/1`) and site meter (`site`) |
| [`v2g_readings_automation.yaml`](v2g_readings_automation.yaml) | `automation.lab_v2g_readings_to_ode_lab_site_inverters_4`: `site` + V2G EV + Cactus test load → `lab/site` (ODE's meter), and the charger as ODE's `inverters/4` |
| [`ode_limits_helpers_automation.yaml`](ode_limits_helpers_automation.yaml) | `automation.lab_ode_limits_to_lab_helpers`: ODE's live `limits/csipAus` → the `lab_ode_*` helpers the synthetic site curtails to |
| [`helpers.yaml`](helpers.yaml) | Every lab helper these automations use, with its settings |
| [`tests/test_bridge_plan.py`](tests/test_bridge_plan.py) | Renders the bridge's plan template with sample ODE limits and site readings |

## The bridge

The bridge runs on each ODE `limits/csipAus` message (about once a second). While a transaction is
active on `SIM-EV-EVEREST-V2G-03`, it sends one OCPP 2.1 TxProfile (id 9001) through
`citrine_ha.lab_schedule`. The profile has:
- **Power:** CentralSetpoint periods for the current limit and ODE's scheduled controls over the
  next 600 s.
- **Price:** the OpenADR NSW1 Essential import price schedule.

**Import mode** (the default) charges at the site headroom, not at the bare import limit:

```
limit = setpoint = import limit + 0.95 × solar forecast − 1.05 × house load   (0 to 25 kW, rounded down to 10 W)
```

- **Inputs:** solar is `sensor.home_power_production_now`, capped at the 15 kW nameplate and
  `opModGenLimW`, and 0 while de-energised. House load is `input_number.lab_house_load`. The ±5 %
  margins cover the synthetic site's random variation.
- **Night:** this keeps site import (house + EV − solar) within the import limit. With a 4.5 kW
  limit and 1 kW of house load, the EV gets 3,450 W instead of 4,500 W.
- **Day:** the EV also soaks up the solar.
- **Off:** while ODE reports disconnected or de-energised, the bridge sends 0 W.
- **Sending:** a headroom change of 100 W or more is sent at once.

**Export mode** (`input_boolean.lab_v2g_export` on, for Cactus ALL-22) is unchanged. The EV
discharges at `input_number.lab_v2g_discharge_target`, capped at the export ceiling.

**TxProfile test.** While `input_text.lab_v2g_test_steps` holds `start_ts|step_s|W,W,...`, the
requested steps (+ charge, − discharge) are added to the same schedule as extra boundaries. Each
step is clamped to the headroom of its period:
- **Charging:** the charge headroom above.
- **Discharging:** export limit − 1.05 × solar + 0.95 × house load. Solar has priority on export,
  and house load the solar doesn't cover absorbs discharge too: at night the EV may discharge the
  export limit plus the house load.

The profile id and the price schedule stay the same, so nothing has to be paused. Start a test with:

```yaml
action: script.lab_v2g_txprofile_test
data:
  setpoints: "20000,-20000,6000,-5000,0"   # W per step
  step_s: 60
  lead_s: 10
```

## The synthetic site

Away from the home broker, the Green has no real solar or site meter. This automation stands in for
them on the local Mosquitto, every 10 s and on every change.
- **Solar:** the Open-Meteo Solar Forecast for a 10 kW system at the Green's home location: 3.6 kWp
  east and 6.4 kWp west, with a 10 kW inverter (`sensor.home_power_production_now`). It is published
  as ODE's `inverters/1`, with a 10 kW / 10 kVA nameplate.
- **Site meter:** house load (`input_number.lab_house_load`) minus solar, published on `site`.
  "Lab: V2G readings to ODE" then adds the V2G EV and the Cactus test load and publishes it as
  `lab/site`.
- **Curtailment:** solar is curtailed like an inverter obeying ODE. It never goes above
  `opModGenLimW`, it keeps site export within `opModExpLimW` (aiming at limit / 1.05), and it is 0
  while de-energised.
- **Variation:** readings vary randomly like a live meter: ±5 % on power, phases and voltage, and
  ±0.1 % on frequency.
- **Reactive power:** the house load runs at PF 0.95 lagging. The inverter follows the
  AS/NZS 4777.2 Australia A volt-var curve on its 10 kVA rating, plus a 0.995 absorbing
  power-factor offset.

The Open-Meteo integration itself is configured in the UI: azimuth 90° and 270°, declination 10°,
efficiency 0.84 and inverter limit 10,000 W. Array sizes can only be changed by removing the entry
and adding it again, which keeps the entity IDs.

## How the pieces fit

```
Open-Meteo forecast ──► synthetic site ──► site, inverters/1 ──► V2G readings ──► lab/site, inverters/4 ──► ODE
        ▲                     ▲                                       ▲                                      │
  lab_house_load        lab_ode_* helpers ◄── ODE limits to helpers ◄─┼──────────── limits/csipAus ◄─────────┤
                                                                      │                                      ▼
                                              V2G EV power (CitrineOS meter values) ◄── charger ◄── bridge (TxProfile)
```

- **Meter:** ODE reads `lab/site` and inverters 1 and 4, and publishes `limits/csipAus` about once
  a second.
- **Charger:** the bridge turns the limits into the charger's TxProfile.
- **Curtailment:** "ODE limits to lab helpers" copies the same limits into helpers, so the
  synthetic site curtails solar like an inverter obeying ODE.

## Changing and deploying

1. Edit the YAML here and run the tests:
   `python3 -m unittest discover -s plugfest-lab/ha/tests` (needs `jinja2` and `PyYAML`).
2. Render the new plan once with Home Assistant's own engine (Developer tools > Template, or the MCP
   `ha_eval_template`), with a sample `limits/csipAus` payload.
3. On the Green, open the automation or script, choose **Edit in YAML**, replace it with the file
   (keep the `id`) and save. Deploy between Cactus control windows, and say so in the run notes.
