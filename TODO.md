# Plugfest to-do

OCA Plugfest & Conference Australia, **21–23 October 2026, Canberra**.
Two roles: **CSMS under test** (vendor slots, see [`plugfest-lab/RUNBOOK.md`](plugfest-lab/RUNBOOK.md))
and the **CSIP-AUS → OCPP 2.1 demonstration** (see [`demo/DEMO.md`](demo/DEMO.md)).

Status at 18 October 2026. The Green test box is offline; nothing below has been checked on it since.

## 1. Blockers before leaving

- [ ] **Green back online.** All Apps started; CitrineOS `/lab/status` answers.
- [ ] **Release citrineos_server 0.6.3** ([ha-addons#74](https://github.com/purcell-lab/ha-addons/pull/74)):
      publish the image, merge, update on the Green. Fixes lost station replies after a reconnect
      ([ha-addons#67](https://github.com/purcell-lab/ha-addons/issues/67)). Highest risk for vendor slots.
- [ ] **Release CitrineOS-HA integration 0.5.0**
      ([CitrineOS-HA-Integration#9](https://github.com/purcell-lab/CitrineOS-HA-Integration/pull/9)):
      no more lock-outs that need a reload ([ha-addons#69](https://github.com/purcell-lab/ha-addons/issues/69)).
- [ ] **Rotate every lab secret** ([ha-addons#71](https://github.com/purcell-lab/ha-addons/issues/71)):
      database, broker, Hasura, API, command and operator tokens, Plugfest station passwords.
- [ ] **Close open admission for the event**: `plugfest_open_admission: false`,
      `open_admission_enabled: false`; one `plugfest_stations` entry per vendor station, each with
      its own password.
- [ ] **Port 8083 closed between slots** (`8083/tcp: null`); open it only for a slot.
- [ ] **Rehearsal on the home network** after the releases: V2G TxProfile steps, a forced station
      reconnect (replies must continue), a test station on 8083 with Basic Auth, the HA bridge.

- [ ] **OCPP 2.1 EMS checks in each vendor slot**: follow
      [`plugfest-lab/OCPP21-EMS-CHECKLIST.md`](plugfest-lab/OCPP21-EMS-CHECKLIST.md) and fill in its
      results table. Lab follow-ups: [ha-addons#87](https://github.com/purcell-lab/ha-addons/issues/87),
      [ha-addons#88](https://github.com/purcell-lab/ha-addons/issues/88).

## 2. Decisions

- [ ] **Commands to vendor stations** ([ha-addons#40](https://github.com/purcell-lab/ha-addons/issues/40)):
      retarget the single command station per slot (server restart + integration reload), or enable
      the Operator UI with commands.
- [ ] **Connector status "Unknown" on 8083** ([ha-addons#37](https://github.com/purcell-lab/ha-addons/issues/37)):
      fix, or record it in each slot.
- [ ] **MeterValues interval** per vendor station: agree vendors set it, or use the Operator UI.
- [ ] **Slot 1 (OCTT / DNV)**: confirm the security profile its test cases need (we offer SP1 only).
- [ ] **Slot 7 (AS Jade, online)**: cannot reach a LAN-only CSMS. Ask the organisers to reschedule;
      never expose 8083 to the internet.
- [ ] **Release V2G simulator 0.1.10** ([ha-addons#75](https://github.com/purcell-lab/ha-addons/pull/75))
      for the demo (late-start recovery). ODE 0.1.3 (#72), AC test (#73) and MicroOCPP diagnostics (#76)
      can wait.

## 3. Demonstration (Friday afternoon, under an hour, with Riccardo)

- [ ] Send the reply to Riccardo with the V2G screenshot attached.
- [ ] Book a Cactus CSIP-AUS session for Friday, or stop ODE and replay recorded controls.
- [ ] ODE `log_level: info` (debug prints device identifiers every cycle).
- [ ] Rehearse [`demo/DEMO.md`](demo/DEMO.md) end to end; time each scenario.
- [ ] Print the [infographic](infographic/plugfest-infographic.pdf); load the evidence pages offline.

## 4. Venue logistics

- [ ] Ethernet cable, power, DHCP reservation if possible; note the Green's venue IP.
- [ ] Assume no internet: every App image already pulled on the Green.
- [ ] No updates in the week before (Home Assistant Core 2026.10.2 waits).
- [ ] Full backup before the event and after.
- [ ] After the event: `plugfest_enabled: false`, export the evidence, reset the CitrineOS
      database, treat every password used as public.

## 5. Tidy-up

- [ ] Stop the V2G session left charging after the 17 October test
      ([ha-addons#26](https://github.com/purcell-lab/ha-addons/issues/26)).
- [ ] Stop the MicroOCPP simulators until #76's diagnostics are captured
      ([ha-addons#31](https://github.com/purcell-lab/ha-addons/issues/31)).
- [ ] Close [ha-addons#27](https://github.com/purcell-lab/ha-addons/issues/27): the 0 W step held 0 W
      on 17 October (fixed in 0.1.8).
