# How the TxProfile test was run without the bridge overwriting it

This is the procedure behind the [network-constrained V2G result](README.md) (19 October 2026). All
times are AEDT. Use it to repeat a hand-written OCPP 2.1 TxProfile test on the Green while the ODE
schedule bridge is installed.

## Why the bridge would overwrite a test profile

The ODE schedule bridge, `automation.lab_ode_schedule_to_ac_everest_prototype_v2`, runs on every
ODE `limits/csipAus` message (about once a second). While a transaction is active on
`SIM-EV-EVEREST-V2G-03`, it calls `citrine_ha.lab_schedule`:
- **When it sends:** at once when the limit falls or the scheduled steps change, otherwise at least
  every 60 s.
- **What it replaces:** `lab_schedule` always sends the same TxProfile, id 9001 at stack level 1.
  A test profile sent through the same service gets the same id, so the bridge's next send
  replaces it within a minute.

The fix is to pause the bridge for the length of the test, then turn it back on.

## Procedure

| Step | Time (AEDT) | Action | Home Assistant call |
|---|---|---|---|
| 1 | 14:39:34 | **Pause the bridge** | `automation.turn_off` on `automation.lab_ode_schedule_to_ac_everest_prototype_v2` (via the MCP: `ha_config_set_automation` with `enabled: false`) |
| 2 | 14:39:35 | **Plug in the simulated EV** | Fire event `everest_v2g_command` with `{"charge_point_id": "SIM-EV-EVEREST-V2G-03", "command": "plugin"}` |
| 3 | 14:39:46 | **Start the transaction** | Press `button.citrineos_everest_v2g_lab_sim_ev_everest_v2g_03_start_charging` |
| 3a | 14:39:53 | **Only if the start is refused with "Previous outcome unresolved":** clear the stale command state, then start again | Press `button.citrineos_everest_v2g_lab_sim_ev_everest_v2g_03_reconcile_command_state`, then the start button again |
| 4 | to 14:40:45 | **Wait for charging, then read the site** | Wait about 40 s. Read the transaction sensor, measured EV power, `input_number.lab_ode_import_limit` / `lab_ode_export_limit` and `sensor.home_power_production_now` to work out the headroom |
| 5 | 14:40:56 | **Send the test profile** | `citrine_ha.lab_schedule` with `immediate: true`, `duration: 330` and the five periods below |
| 6 | to 14:46:28 | **Let it run** | The profile expires 330 s after it was sent. Nothing else sends to the station while the bridge is off |
| 7 | 14:46:55 | **Stop the transaction** | Press `button.citrineos_everest_v2g_lab_sim_ev_everest_v2g_03_stop_transaction` |
| 8 | 14:47:26 | **Unplug** | Fire `everest_v2g_command` with `"command": "unplug"` |
| 9 | 14:47:27 | **Turn the bridge back on** | `automation.turn_on` (MCP: `enabled: true`) |

The service call in step 5 (entry id of the CitrineOS Green Lab integration):

```yaml
action: citrine_ha.lab_schedule
data:
  entry_id: 01M51W1XF0B0JJP3H2VVTNKPZ1
  immediate: true      # schedule starts now, so the replaced profile leaves no gap
  duration: 330        # seconds; the service allows at most 600
  periods:             # W, OCPP 2.1 CentralSetpoint; + charge, − discharge
    - {startPeriod: 0,   limit: 17420, dischargeLimit: 0, setpoint: 17420, operationMode: CentralSetpoint}
    - {startPeriod: 60,  limit: 17420, dischargeLimit: 0, setpoint: 0,     operationMode: CentralSetpoint}
    - {startPeriod: 120, limit: 17420, dischargeLimit: 0, setpoint: 6000,  operationMode: CentralSetpoint}
    - {startPeriod: 180, limit: 17420, dischargeLimit: 0, setpoint: 0,     operationMode: CentralSetpoint}
    - {startPeriod: 240, limit: 17420, dischargeLimit: 0, setpoint: 0,     operationMode: CentralSetpoint}
```

The requested steps were +20, −20, +6, −5 and 0 kW. They were clamped before sending:
- **Charge steps:** clamped to the charge headroom, 17,420 W: the import limit, plus the least
  solar expected, minus the house load.
- **Discharge steps:** clamped to the discharge headroom, 0 W. Solar already filled the 4.5 kW
  export limit.
- **Bounds:** every period also carries `limit` 17,420 W and `dischargeLimit` 0 W, so even a stale
  setpoint stays inside the site limits.

## What to do differently next time

The result shows two windows with no profile in force: 14:40:18–14:41:03, after the start, and
14:46:28–14:46:58, after the profile expired. In both the charger fell back to its full 25 kW, and
the site imported about 11 kW against the 4.5 kW limit. Both windows came from this procedure, not
from the bridge.
- **At the start:** send the test profile straight after the start is accepted, instead of
  waiting for the charging state. Better, start with the bridge still on and pause it only at
  step 5, so the bridge's profile covers the start.
- **At the end:** set `duration` to cover the steps plus the stop. Or turn the bridge back on before
  the test profile expires; its next send replaces the test profile at once.
- **Keep the bridge off only briefly.** While it is off, nothing follows the CSIP-AUS limits.
  Never leave it off across a Cactus control boundary.

## Notes for the current setup

- **Bridge pricing:** since 19 October the bridge also attaches the OpenADR NSW1 Essential import
  price schedule (`price_entity`). A test call without `price_entity` sends a power-only profile,
  so the price schedule is missing from the station for the test.
- **Price updates still run:** the price-update automation keeps sending CostUpdated every 5
  minutes during the test. It does not touch charging profiles, so it needs no pause.
- **Stale transactions:** CitrineOS 0.7.1 closes stale transactions automatically (purcell-lab/ha-addons#79). The step 3a
  reconcile button clears the integration's own unresolved-command state, which is a separate check.
