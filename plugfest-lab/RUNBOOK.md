# Plugfest runbook: CitrineOS on the Home Assistant Green

OCPP 2.0.1 & 2.1 Plugfest, October 2026. Purcell is a **CSMS** under test.
The CSMS is the CitrineOS Isolated Lab App on the Home Assistant Green,
plugged into the venue LAN. Stations connect with Security Profile 1
(Basic Auth over `ws://`) to the opt-in Plugfest listener (port 8083).

## Slots (Purcell row)

| Slot | Charging station | Notes |
|---|---|---|
| 1 | OCTT (DNV) | Conformance tool acting as a station; ask which security profile its test cases need |
| 2 | EVX Australia | Venue LAN |
| 5 | EVSE | Venue LAN |
| 6 | Trialog | Venue LAN |
| 7 | AS Jade - CS (online) | **Online**: cannot reach a LAN-only CSMS; needs a separately agreed TLS path, or reschedule. Do not port-forward 8083 |
| 10 | Starcharge | Venue LAN |

## Before the event

1. Install the CitrineOS stack on the Green (database, broker, Hasura,
   server; aarch64 support from the aarch64 PR). Fresh generated secrets.
2. Ask each vendor for its **station identity** (OCPP `chargingStation`
   id) and OCPP version. Generate one password per station, 16 to 40
   printable characters, for example
   `python3 -c "import secrets;print(secrets.token_urlsafe(24))"`.
3. Server options: `mode: isolated`, the dependency hosts and secrets,
   `plugfest_enabled: true`, and `plugfest_stations` with one
   `{id, password}` entry per vendor station. Keep
   `command_control_enabled: false` unless a simulator command test is
   planned.
4. Rehearse on a home network: set a host port for `8083/tcp` (for example
   `8083`), connect a test station with Basic Auth to
   `ws://<green-ip>:8083/<id>`, check its BootNotification is Accepted, then
   remove the host port again.

## At the venue

1. Connect the Green by Ethernet. Note its venue IP (Settings → System →
   Network) and, if possible, ask for a DHCP reservation.
2. Start database, broker, Hasura, then the server; check `/lab/status`
   lists the expected `plugfest_stations`.
3. Keep the `8083/tcp` host port empty between slots.

## Each slot

1. Set the `8083/tcp` host port; restart the server App.
2. Give the vendor: URL `ws://<green-ip>:8083/` (the station appends its
   identity), its identity and its password. Nothing else is shared.
3. Run the agreed test cases. Record supported and unsupported features,
   message traces and the transaction evidence (TransactionEvents and
   MeterValues through the read-only discovery endpoint).
   If the station runs OCPP 2.1, also send the dynamic tariff
   (`citrine_ha.lab_default_tariff` with `station_id` set to the vendor's
   identity; needs `price_commands_enabled: true`) and record the reply:
   `Accepted`, `Rejected`, `TooManyElements`, `ConditionNotSupported` or a
   CALLERROR. See [dynamic pricing](../design/dynamic-pricing.md#path-d-ocpp-21-tariff-to-vendor-stations).
   Then work through the [OCPP 2.1 EMS checklist](OCPP21-EMS-CHECKLIST.md). Do the read-only
   device model and `NotifyChargingLimit` checks every slot. Do the profile and operation-mode
   checks only with a command path and the vendor's agreement.
4. After the slot: clear the `8083/tcp` host port and restart the server
   App. Remove the vendor's entry from `plugfest_stations` if it will not
   return; on restart its password is revoked in the database.

## ODE controlling a vendor's charger (with the vendor's agreement)

The demonstration chain is **Cactus → ODE → bridge → CitrineOS → the vendor's charger**. Cactus sets
CSIP-AUS controls (this needs venue internet); Open Dynamic Export turns them into limits; the bridge
turns those into TxProfiles that CitrineOS sends to the charger.

- **V2G stations** (for example StarCharge): OCPP 2.1 `CentralSetpoint` periods, charging in import
  mode and discharging in export mode, as with the V2G simulator.
- **Charging-only stations:** charging-only `limit` periods (W) on the station's OCPP version (1.6,
  2.0.1 or 2.1).

The server bounds every profile: one command station, an active transaction, 600 s, 10 periods, 25 kW.

1. **Agree with the vendor first.** Their charger, their EV, and limits we'll vary (import, and export
   for a V2G station). Ask:
   - **Rate unit:** does the station accept charging profiles in **W**? (2.x: `SmartChargingCtrlr.RateUnit`;
     1.6: `ChargingScheduleAllowedChargingRateUnit`.) The lab command path only sends W; an A-only
     station will reject the profile.
   - **Rating:** the charger's rating in W, and whether it's V2G (bidirectional) or charging only.
2. **Server options** (citrineos_server):
   - `command_control_enabled: true`, with its `command_token`;
   - `command_real_stations_enabled: true`;
   - `command_station_id: <vendor station id>`.

   Restart the server App, then reload the CitrineOS-HA integration.
3. **Home Assistant helpers:**
   - `input_text.lab_bridge_station_prefix` = `citrineos_lab_<station id, lower case, with every
     character other than a-z and 0-9 replaced by _>`. Check that
     `sensor.<prefix>_current_transaction` exists.
   - `input_boolean.lab_bridge_charge_only`: **on** for a charging-only station (charging-only periods,
     no export, `inverters/4` at 0 W; its power still counts in `lab/site`). **Off** for a V2G station,
     which is then ODE's `inverters/4` DER, rated at `lab_bridge_rating`.
   - `input_number.lab_bridge_rating` = the charger's rating in W. It bounds charge and discharge, and is
     the V2G station's nameplate (ODE's `setMaxW`, Cactus's `maxExportW`). Set it unless CitrineOS
     reports a rating.
   - V2G stations only: `input_boolean.lab_v2g_export` **on** for export tests (ALL-22, GEN-10, GEN-11,
     ALL-28, ALL-23), with `input_number.lab_v2g_discharge_target`; **off** for import tests (LOA-11).
     It's ignored for a charging-only station.
4. **Start a transaction:** the vendor starts it with its own ID token, or press
   `button.<prefix>_start_charging`. The bridge acts only while the transaction is open.
5. **Change the limit.**
   - **With internet:** run a Cactus test: an import test such as LOA-11 for any station, export tests
     (ALL-22, GEN-10, GEN-11, ALL-28, ALL-23) for a V2G station. As in the lab, restart ODE once Cactus
     has started the run if it still shows the previous run's controls.
   - **Without internet:** ODE gets no CSIP-AUS controls. Change `setpoints.csipAus.fixedDefaults.importLimitWatts`
     in ODE's config and restart ODE. Rehearse this first: it assumes ODE publishes the fixed default on
     `limits/csipAus` when it can't reach the server. The `lab_ode_*` helpers can't be used as a knob,
     because they are written from ODE's output.

   Record the TxProfile status and the charger's measured power against the limit.
6. **After the slot:**
   - `input_boolean.lab_bridge_charge_only` **off**, `input_number.lab_bridge_rating` 0 and
     `input_text.lab_bridge_station_prefix` empty, so the
     bridge targets the V2G simulator again;
   - `command_station_id` back to `SIM-EV-EVEREST-V2G-03` and `command_real_stations_enabled: false`;
     restart the server and reload the integration.

**After any CitrineOS restart** (22 October):
- **Wait for each station to reconnect** before sending commands. CitrineOS can hold a station's old
  websocket for about a minute and refuse its reconnect ("New connection attempted for already connected
  identifier"). A profile sent then fails as `dispatch_not_confirmed`, and the integration blocks every
  command until it's reconciled.
- **Reload the integration once CitrineOS is ready**, then check the command station's
  `command_dispatch_status`. If it reads `outcome_unknown` or `dispatch_not_confirmed`, run
  `citrine_ha.lab_reconcile` (it's allowed 90 s after the last send; the error message gives the wait).
- **Don't stop a transaction HA hasn't shown yet.** Right after a start, the `current_transaction` sensor can
  lag; check the station's own status first. A new transaction mistaken for a stale one was stopped on
  the AC simulator.
- **Ask the station what it applied:** `GetCompositeSchedule` and `GetChargingProfiles` through the
  Operator UI (see the EMS checklist, section A).

## After the event

1. Set `plugfest_enabled: false`, clear `plugfest_stations` and the host
   port, and restart the server.
2. Export the evidence, then reset or archive the dedicated database.
   Passwords of stations no longer listed are revoked at each restart; the
   station records and their message history stay until the reset.
3. Treat every Plugfest password as public; none is reused.

## Not covered

- Security Profile 2/3 (TLS, client certificates). OCTT test cases may need
  them; agree the scope with DNV beforehand.
- Internet-facing access for the online slot.
- Control of more than one real station at a time: the command path has one command station,
  chosen in the server options (see "ODE controlling a vendor's charger").
