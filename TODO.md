# Plugfest to-do

OCA Plugfest & Conference Australia, **21–23 October 2026, Canberra**.
Two roles: **CSMS under test** (vendor slots, see [`plugfest-lab/RUNBOOK.md`](plugfest-lab/RUNBOOK.md))
and the **CSIP-AUS → OCPP 2.1 demonstration** (see [`demo/DEMO.md`](demo/DEMO.md)).

Status at **21 October 2026, 20:48 AEDT**, checked on the Green.

## Station endpoint (decided 21 October)

Every vendor uses one endpoint, **`ws://purcell.local:8083/<station-id>`** (or the Green's venue LAN
address, port 8083), OCPP 2.1 / 2.0.1 / 1.6, Security Profile 1. The station ID tells stations apart.
`plugfest_enabled` stays on and 8083 stays published for the event. Listeners 8100–8105
(citrineos_server 0.7.2) are spares. **Open admission** (`plugfest_open_admission: true`) for the
vendor slots: any station ID connects without a password. Ask each vendor for a unique station ID.

## 1. Before the slots

- [x] Green online; all Apps started.
- [x] CitrineOS **0.7.2** on the Green ([ha-addons#90](https://github.com/purcell-lab/ha-addons/pull/90):
      Plugfest listeners, reconnect and stale-transaction fixes). Supersedes 0.6.3.
- [x] CitrineOS-HA integration **0.6.1** on the Green (supersedes 0.5.0).
- [x] Physical-charger path rehearsed: charging-only (OCPP 1.6) and V2G (OCPP 2.1), and a station on
      port 8105 driven by the bridge
      ([record](results/2026-10-21-physical-path-rehearsal/README.md)).
- [x] Full backup before the event: `9e83a612`, 21 October 20:15 AEDT (config and Apps, no database).
- [x] Operator UI enabled with commands (`operator_ui_enabled`, `operator_commands_enabled`).
- [x] **Station ratings**: citrineos_server **0.7.3** and everest_v2g_simulator **0.1.13**
      ([ha-addons#91](https://github.com/purcell-lab/ha-addons/pull/91)) and CitrineOS-HA **0.6.2**
      ([CitrineOS-HA-Integration#12](https://github.com/purcell-lab/CitrineOS-HA-Integration/pull/12))
      on the Green, 20:41 AEDT. The V2G simulator reports 25 kW charge and discharge from its device
      model (`source: evse_rating`); the bridge followed again at 20:46 (-950 W). A vendor station that
      reports no rating falls back to 25 kW: set `input_number.lab_bridge_rating` for it.
- [ ] **OCPP 2.1 EMS checks in each vendor slot**: follow
      [`plugfest-lab/OCPP21-EMS-CHECKLIST.md`](plugfest-lab/OCPP21-EMS-CHECKLIST.md) and fill in its
      results table. Lab follow-ups: [ha-addons#87](https://github.com/purcell-lab/ha-addons/issues/87),
      [ha-addons#88](https://github.com/purcell-lab/ha-addons/issues/88).
- Secret rotation: not planned. The Green is a throw-away lab configuration; treat its secrets as
  public ([ha-addons#71](https://github.com/purcell-lab/ha-addons/issues/71), closed).

## 2. Per slot

- [ ] Note the station ID, OCPP version and, on 1.6, `ChargingScheduleAllowedChargingRateUnit`
      (W only; an amps-only station rejects the bridge's TxProfiles).
- [ ] To control a vendor charger through the bridge (with the vendor's agreement):
      `command_station_id` = the station ID, `command_real_stations_enabled: true`, restart CitrineOS,
      reload the integration once CitrineOS is ready, then set `input_text.lab_bridge_station_prefix`,
      `input_boolean.lab_bridge_charge_only` (on for a charging-only station) and
      `input_number.lab_bridge_rating`. See the [runbook](plugfest-lab/RUNBOOK.md).
- [ ] End a station's transaction (unplug) before moving it to another port or restarting it.
- [ ] Reset after the slot: command station back to `SIM-EV-EVEREST-V2G-03`, prefix empty,
      charge-only off, rating 0.

## 3. Decisions still open

- [ ] **Slot 1 (OCTT / DNV)**: confirm the security profile its test cases need. Security Profile 1
      tests need a provisioned password in `plugfest_stations` and open admission off for that slot.
- [ ] **Slot 7 (AS Jade, online)**: cannot reach a LAN-only CSMS. Ask the organisers to reschedule;
      never expose 8083 to the internet.
- [ ] **MeterValues interval** per vendor station: vendors set it, or use the Operator UI.
- [x] **Commands to vendor stations** ([ha-addons#40](https://github.com/purcell-lab/ha-addons/issues/40)):
      Operator UI with commands; the bridge retargets one command station per slot.
- [x] **Connector status "Unknown" on 8083**: not reproduced on 21 October
      ([ha-addons#37](https://github.com/purcell-lab/ha-addons/issues/37), closed).

## 4. Demonstration (Friday afternoon, under an hour, with Riccardo)

- [x] ODE `log_level: info`.
- [ ] Send the reply to Riccardo with the V2G screenshot attached.
- [ ] Book a Cactus CSIP-AUS session for Friday, or stop ODE and replay recorded controls.
- [ ] Rehearse [`demo/DEMO.md`](demo/DEMO.md) end to end; time each scenario.
- [ ] Print the [infographic](infographic/plugfest-infographic.pdf); load the evidence pages offline.

## 5. Venue logistics

- [ ] Ethernet cable, power, DHCP reservation if possible; note the Green's venue IP.
- [ ] Check `purcell.local` resolves on the venue network; otherwise give vendors the IP.
- [ ] Assume no internet: every App image already pulled on the Green.
- [ ] No updates during the event: Home Assistant Core stays on 2026.10.2, Mosquitto 7.1.2 waits.
- [ ] Backup after the event.
- [ ] After the event: `plugfest_enabled: false`, unpublish 8083 and 8100–8105, export the evidence,
      reset the CitrineOS database, treat every password used as public.

## 6. After the event

- CitrineOS heap use in long slots ([ha-addons#80](https://github.com/purcell-lab/ha-addons/issues/80)):
  restart the App if it runs out.
- ODE upstream patches: [#83](https://github.com/purcell-lab/ha-addons/issues/83),
  [#85](https://github.com/purcell-lab/ha-addons/issues/85),
  [#86](https://github.com/purcell-lab/ha-addons/issues/86).
- OCPP 2.1 EMS and DER control: [#87](https://github.com/purcell-lab/ha-addons/issues/87),
  [#88](https://github.com/purcell-lab/ha-addons/issues/88),
  [#89](https://github.com/purcell-lab/ha-addons/issues/89).
- Simulator and integration follow-ups: [#26](https://github.com/purcell-lab/ha-addons/issues/26),
  [#28](https://github.com/purcell-lab/ha-addons/issues/28),
  [#31](https://github.com/purcell-lab/ha-addons/issues/31),
  [#32](https://github.com/purcell-lab/ha-addons/issues/32),
  [#42](https://github.com/purcell-lab/ha-addons/issues/42),
  [#70](https://github.com/purcell-lab/ha-addons/issues/70).
- Restart-free command retarget ([#40](https://github.com/purcell-lab/ha-addons/issues/40)).
- Prune the stale feature branches in ha-addons.
