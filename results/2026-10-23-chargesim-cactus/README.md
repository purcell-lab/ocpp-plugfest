# ChargeSim: Cactus ALT-ALL-29 and multi-station session (23 October 2026)

**Status: in progress.** From about 15:46 AEDT, 23 October 2026. ChargeSim (ChargeSim SCDE) as the
lab command station for a Cactus (CSIP-AUS) **ALT-ALL-29** run, then a multi-station session with
stations `charger1` to `charger11`, all OCPP 2.0.1. Follows the
[ChargeSim functional session](../2026-10-23-chargesim/README.md). Times are AEDT.

## Executive summary

To be written when the session closes.

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

## Lab state at 16:03

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
