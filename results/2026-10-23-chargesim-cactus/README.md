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

## Open items

- When the stations connect: SetVariables on each (TxStarted/TxUpdated measurands
  `Energy.Active.Import.Register,Power.Active.Import`, TxUpdatedInterval 10 s), then start
  `charger1`'s session and rerun ALT-ALL-29.
- Decide the house load for the rerun (10 kW takes 5.8 kW off each limit).
