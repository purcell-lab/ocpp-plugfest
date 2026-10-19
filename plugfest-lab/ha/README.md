# Home Assistant lab automations on the Green

These are the Home Assistant pieces that turn CSIP-AUS limits into OCPP 2.1 charging profiles on the
Green. They are UI-managed on the Green; this folder is their source of truth, so changes are reviewed
here first.

| File | On the Green |
|---|---|
| [`bridge_automation.yaml`](bridge_automation.yaml) | `automation.lab_ode_schedule_to_ac_everest_prototype_v2`, the ODE schedule bridge |
| [`txprofile_test_script.yaml`](txprofile_test_script.yaml) | `script.lab_v2g_txprofile_test`, a stepped TxProfile test run through the bridge |
| [`helpers.yaml`](helpers.yaml) | `input_text.lab_v2g_test_steps`, the test steps the script hands to the bridge |
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
- **Discharging:** export limit − 1.05 × solar + 0.95 × house load, because solar has priority on
  export.

The profile id and the price schedule stay the same, so nothing has to be paused. Start a test with:

```yaml
action: script.lab_v2g_txprofile_test
data:
  setpoints: "20000,-20000,6000,-5000,0"   # W per step
  step_s: 60
  lead_s: 10
```

## Changing and deploying

1. Edit the YAML here and run the tests:
   `python3 -m unittest discover -s plugfest-lab/ha/tests` (needs `jinja2` and `PyYAML`).
2. Render the new plan once with Home Assistant's own engine (Developer tools > Template, or the MCP
   `ha_eval_template`), with a sample `limits/csipAus` payload.
3. On the Green, open the automation or script, choose **Edit in YAML**, replace it with the file
   (keep the `id`) and save. Deploy between Cactus control windows, and say so in the run notes.
