# ChargeSim: Cactus ALT-ALL-29 and multi-station session (23 October 2026)

**Status: closed.** 23 October 2026, about 15:46–16:14 AEDT. ChargeSim (ChargeSim SCDE) as the
lab command station for a Cactus (CSIP-AUS) **ALT-ALL-29** run, then a multi-station session with
stations `charger1` to `charger11`, all OCPP 2.0.1. Follows the
[ChargeSim functional session](../2026-10-23-chargesim/README.md). Times are AEDT.

## Executive summary

ChargeSim's simulated 150 kW stations were driven by the Purcell CitrineOS CSMS in two parts: a
Cactus (CSIP-AUS) **ALT-ALL-29** run with `charger1` as the lab command station, then a
**multi-station session with 11 stations** (`charger1` … `charger11`), all OCPP 2.0.1, in real
time. The earlier single-station functional session has its own
[report](../2026-10-23-chargesim/README.md).

**Results**

- **Smart charging works at scale.** All 11 stations booted, accepted the metering configuration
  and remote starts, and every TxProfile that reached a station was **Accepted**: the bridge's
  Cactus profiles on `charger1` (which then paused at 0 W as required) and stepped 50 → 0 kW
  profiles on `charger2` … `charger10`.
- **Power metering needed a lab change.** ChargeSim reports power only when the CSMS asks for it
  over OCPP (SetVariables). The lab gateway allowed no SetVariables, so the first ALT-ALL-29 run
  couldn't measure ChargeSim and Cactus saw the site without it. CitrineOS App **0.7.7** (Green
  build) allows SetVariables for metering variables only; after it, all 11 stations sent
  `Power.Active.Import` (kW) and energy every 10 s.
- **ALT-ALL-29 wasn't completed as a valid run.** ODE had the correct import limits (12.5 / 10 /
  7.5 / 0 kW) and the bridge delivered them, but reduced by 5.8 kW for the lab's synthetic 10 kW
  house load, and without ChargeSim's power in the site reading. A rerun with metering on and the
  house load set deliberately is needed.
- **The Green lab went offline twice** (15:19–15:23, network; from about 16:10, cause not yet
  known, with 11 stations reporting every 10 s), ending the session before the random TxProfile
  test completed.

**Findings for ChargeSim**

1. Profiles set by the CSMS are reported with `chargingLimitSource: "Other"` instead of `CSO`, so
   CitrineOS's automatic check after every SetChargingProfile returns NoProfiles.
2. Power is reported in kW (`unitOfMeasure` kW), and periodic meter values are off by default
   (TxUpdatedInterval 0, energy only).
3. `charger11` accepted RequestStartTransaction (16:07:24) but started no transaction.
4. Each station's own local token (`Local`, `1` … `11`) is Unknown in the lab CSMS.

**Findings for the lab**

1. Metering SetVariables were missing from the operator route (fixed in 0.7.7, verified on all 11
   stations).
2. The bridge controls and measures only one command station; a multi-station Cactus test needs a
   group limit and the sum of all stations' power in the site reading.
3. The synthetic house load (10 kW) silently reduces every Cactus limit sent to the charger; it
   should be set per run and shown in the run record.
4. Green stability under multi-station load (second outage at about 16:10) needs investigating.
5. CitrineOS has no simulated clock: runs must be in real time while Cactus or the bridge is used.

## What works

| Area | Result |
|---|---|
| Admission | 11 stations admitted together through Plugfest open admission (`wss://ocpp.purcell.id.au`) |
| Boot | BootNotification **Accepted** for all 11 (16:03:54–16:04:09), StatusNotification accepted |
| Metering configuration | SetVariables (SampledDataCtrlr TxStarted/TxUpdated measurands, TxUpdatedInterval 10 s) **Accepted ×3 on all 11** (App 0.7.7) |
| Power readings | `Power.Active.Import` and `Energy.Active.Import.Register` every 10 s (`MeterValuePeriodic`) on every charging station |
| Remote start | RequestStartTransaction **Accepted by all 11**; 10 transactions Started and Charging (16:07:01–16:07:35) |
| Bridge (Cactus) profiles | Absolute W TxProfiles following ODE's import limit and schedule, **Accepted** on `charger1`; GetCompositeSchedule matched; 0 W step → `SuspendedEVSE` |
| Operator profiles | Stepped TxProfiles 9802–9810 **Accepted by all 9** stations they were sent to |
| Transaction status | GetTransactionStatus answered with a correct `ongoingIndicator` (`true` while charging, `false` after a reboot, so a stale transaction was closed correctly) |
| Stale profile | A profile for a closed transaction was **Rejected** (correct) |

## Needs further investigation

| # | Item | Owner | Detail |
|---|---|---|---|
| 1 | `chargingLimitSource` of CSMS profiles | ChargeSim | Reported as `Other`; expected `CSO` for a CSMS-set TxProfile |
| 2 | `charger11` remote start | ChargeSim | Accepted at 16:07:24 but no TransactionEvent; retried at 16:10, outcome unknown (Green offline) |
| 3 | Power unit | ChargeSim + lab | Power is sent in kW. Check the lab's CitrineOS integration converts kW to W while charging (only 0 W was observed on `charger1`) |
| 4 | Local tokens | Lab | Register `Local` tokens `1` … `11` if ChargeSim's local-start tests need them |
| 5 | ALT-ALL-29 rerun | Lab + ChargeSim | Rerun with metering on, house load chosen for the run (0 kW suggested), `charger1` as command station |
| 6 | Multi-station Cactus | Lab | Group limit across stations and summed site power; not supported by the bridge today |
| 7 | Green outage at about 16:10 | Lab | Check uptime, memory and the CitrineOS App log; see whether load from 11 stations plus the simulators caused it |
| 8 | Random TxProfiles | Lab | 9901–9905 outcome unknown (HA-OCPP 502), 9906–9911 not sent; profiles saved for a rerun |

## Set-up

| | |
|---|---|
| Stations | `charger1` … `charger11`, ChargeSim SCDE, OCPP 2.0.1, Plugfest open admission |
| CSMS | CitrineOS v2.0.1 in the CitrineOS server App **0.7.6**, then **0.7.7** from 15:55 (Green build only: operator SetVariables for metering variables) |
| Command station | **`charger1`** from 15:47 (CitrineOS restart). Only the command station gets the Cactus limits from the ODE bridge, is counted in ODE's site meter, and gets the lab's GetTransactionStatus check |
| Bridge | Station prefix `citrineos_lab_charger1`, **charging-only** (W limit periods), lab hold **off**, export mode off, rating cap 15 kW, lab house load 10 kW, test load 0 |
| ODE | Restarted 15:47:58 for the Cactus run |
| Lab automatics | Automatic GetBaseReport off (applied by the 15:47 restart) |

## Cactus ALT-ALL-29

ALT-ALL-29 sets the site import limit (DERC1 200 %, then 50 / 40 / 30 / 0 % of the 25 kW rating,
2 minutes each). The bridge turns the import limit into a TxProfile for the command station at the
**site headroom**: import limit + 95 % solar − 105 % (house load + test load).

| Cactus import limit | Sent to `charger1` (house load 10 kW, solar 4.96 kW) |
|---|---|
| 12.5 kW | 6.71 kW |
| 10 kW | 4.21 kW |
| 7.5 kW | 1.71 kW |
| 0 W | 0 W |

**Finding: ChargeSim's power wasn't visible to Cactus.** ChargeSim sends no power measurand and no
periodic transaction meter values by default (`SampledDataCtrlr.TxUpdatedInterval` 0, energy
only), so the lab's EV power for `charger1` stayed unknown and ODE's site reading counted it as
0 W. ChargeSim says it sends power only when asked over OCPP; the lab gateway refused every
SetVariables, so CitrineOS App **0.7.7** allows SetVariables for metering variables only
(`SampledDataCtrlr`, `AlignedDataCtrlr` measurands and intervals).

## Progress log

| Time | Change or result |
|---|---|
| 15:46 | Command station set to `charger1`; CitrineOS restarted. ChargeSim reconnected 15:47:55; no GetBaseReport sent |
| 15:47:58 | ODE restarted for Cactus. Until the run starts, Cactus answers ODE's DER updates with 403 (EndDevice not registered) |
| about 15:48 | CitrineOS integration reloaded (entities for `charger1`, rating 157.9 kW); bridge set to `citrineos_lab_charger1`, charging-only, hold off, export off; bridge automation **on** |
| 15:49:34 | RequestStartTransaction (`C17E0001`) → Accepted; transaction **`7cf741b1`** Started 15:49:48 (4.878 kWh), **Charging** 15:49:54 |
| 15:49:54 | First bridge TxProfile 9001 (Absolute, W, 600 s: 6.83 / 6.71 / 4.21 / 0 / 1.71 / 0 kW) → **Accepted**; resent on each change, all Accepted. CitrineOS's CSO-filtered GetChargingProfiles → NoProfiles each time (ChargeSim reports source `Other`) |
| 15:50:14 | Lab GetTransactionStatus → `ongoingIndicator: true`, `messagesInQueue: false` (correct) |
| about 15:51 | **ALT-ALL-29 running.** User reports the limits don't look right: the charger limits are the import limit less 5.8 kW (synthetic 10 kW house load), and ChargeSim's power isn't in the site reading |
| about 15:52 | Operator SetVariables (TxUpdatedMeasurands, TxUpdatedInterval) → refused by the gateway (403, "Operator route denied") |
| 15:53:06 | TriggerMessage MeterValues → Accepted; MeterValues energy only, 5.875 kWh (stamped 15:45:00) |
| 15:53:16 | GetCompositeSchedule → 4.21 kW, 0 W (2 s), 1.71 kW, 0 W: the bridge's profile is installed |
| 15:55 | **CitrineOS App 0.7.7 deployed** (metering SetVariables); the restart disconnected `charger1` at 15:55:08. Transaction `7cf741b1` still listed as active |
| 16:00 | `charger1` hadn't reconnected; ChargeSim to reconnect |
| about 16:02 | ChargeSim to connect **11 stations, `charger1` to `charger11`**, all OCPP 2.0.1. Only `charger1` (command station) follows the Cactus limits and counts in the site reading; the others are for a multi-station session |
| **16:03:54–16:04:09** | **All 11 stations connected** (`charger1` … `charger11`, ChargeSim SCDE "150kW Single", OCPP 2.0.1): BootNotification **Accepted** for each, StatusNotification accepted |
| 16:04:02 | Lab GetTransactionStatus for `charger1`'s old transaction `7cf741b1` → `ongoingIndicator: false` (ChargeSim had rebooted), so CitrineOS closed it: correct |
| 16:04:10 | The bridge's TxProfile for the closed `7cf741b1` → **Rejected** by `charger1` (correct: no such transaction) |
| 16:04:10–16:04:22 | Each station sends Authorize with its own local token (`Local`, `1` … `11`) → **Unknown** (not registered in CitrineOS) |
| **16:04:52–16:05** | **Metering SetVariables (App 0.7.7) to all 11:** SampledDataCtrlr TxStartedMeasurands and TxUpdatedMeasurands `Energy.Active.Import.Register,Power.Active.Import`, TxUpdatedInterval 10 s → **Accepted ×3 on every station** |
| **16:06:51–16:07:24** | **RequestStartTransaction to all 11** (`C17E0001`, remoteStartId 2310301 … 2310311) → **Accepted by all 11** |
| 16:07:01–16:07:35 | Transactions Started and **Charging** on `charger1` … `charger10`; `charger11` accepted the start but had no TransactionEvent by 16:08 |
| 16:07:18 | Bridge TxProfile 9001 for `charger1`'s new transaction `dbc58468` (0 W: ODE's current import limit) → **Accepted**; `charger1` → **SuspendedEVSE** at 16:07:46, power 0, as the profile requires |
| from 16:07:10 | **Periodic meter values with power every 10 s** (`MeterValuePeriodic`): `Power.Active.Import` in **kW** (unitOfMeasure `kW`), e.g. 112.5 kW and 150 kW on the unlimited stations, energy rising accordingly. The lab's `charger1` power sensor now updates (0 W while suspended) |
| 16:08:30–16:09:41 | **Stepped TxProfiles 9802–9810** (Relative, W, 600 s: 50 / 25 / 11 / 5 / 0 kW, 2 min each) to `charger2` … `charger10` → **Accepted by all 9**. `charger1` keeps the bridge's profile; `charger11` had no transaction |
| 16:10 | RequestStartTransaction retried on `charger11` (remoteStartId 2310312); the first start at 16:07:24 was Accepted but no transaction followed |
| 16:10:4x | **Random TxProfiles 9901–9911** (seeded, Relative, W, 600 s, 3–6 steps of 0–150 kW; `charger1` at stack level 2 over the bridge's profile): the sends to `charger1` … `charger5` failed with **502 from the HA-OCPP connection**, outcome unknown; `charger6` … `charger11` not sent |
| **16:12:00** | **Green unreachable again:** `wss://ocpp.purcell.id.au` → Cloudflare 530 (tunnel down), Home Assistant Cloud remote access times out, HA-OCPP 502. All 11 ChargeSim stations will have lost the CSMS |
| 15:57–15:58 | CitrineOS restarted twice during the 0.7.7 update (15:57:12, ready about 15:58). The lab's simulators reconnected; no ChargeSim station did |
| 16:03 | **No ChargeSim station connected:** `charger1` offline since 15:55:08; `charger2` … `charger11` never seen by CitrineOS; no refused connection attempts in the CitrineOS log, so nothing from ChargeSim was reaching the lab. Endpoint check: `wss://ocpp.purcell.id.au` answers (HTTP 404 without a WebSocket upgrade, as expected). ChargeSim asked to confirm the URL: `wss://ocpp.purcell.id.au/chargerN` (internet) or `ws://purcell.local:8083/chargerN` (venue LAN) |

## Lab state at 16:03 (before the outage)

| | |
|---|---|
| CitrineOS | App 0.7.7, ready; open admission on; command station `charger1` (offline); transaction `7cf741b1` still listed as active from before the 15:55 restart |
| Bridge | Automation **on**, prefix `citrineos_lab_charger1`, charging-only, hold off, house load 10 kW, rating cap 15 kW. It sends nothing while `charger1` is offline |
| ODE | Running since 15:47:58 |
| Other session | The "HA-OCPP connector check" Claude session stood down at 15:46 and sends nothing to the lab |

## Open items

- Find why the Green went offline at about 16:10 (second time today, after 15:19), with 11 stations sending meter values every 10 s and the lab's simulators connected.
- CitrineOS has no simulated clock; ChargeSim ran in real time. A fast-forward run would only suit Relative profiles without Cactus or the bridge.

- When the stations connect: SetVariables on each (TxStarted/TxUpdated measurands
  `Energy.Active.Import.Register,Power.Active.Import`, TxUpdatedInterval 10 s), then start
  `charger1`'s session and rerun ALT-ALL-29.
- Decide the house load for the rerun (10 kW takes 5.8 kW off each limit).
