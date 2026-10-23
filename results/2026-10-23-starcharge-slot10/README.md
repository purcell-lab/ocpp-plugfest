# Starcharge against the Purcell CitrineOS CSMS (23 October 2026, slot 10)

**Status: in progress.** Started about 16:19 AEDT, 23 October 2026. Starcharge V2G charging station
(Plugfest slot 10) against the Purcell CitrineOS CSMS. Times are AEDT.

## Executive summary

To be written when the session closes.

## What works

| Area | Result |
|---|---|
| Connection | OCPP 2.1 over the venue LAN (port 8083, Security Profile 1), open admission, Heartbeat |
| Device model | GetVariables (4 per request) and GetBaseReport FullInventory Accepted, full NotifyReport |
| Availability | ChangeAvailability Operative Accepted; connector Unavailable → Available |
| V2X smart charging | OCPP 2.1 **CentralSetpoint TxDefaultProfile** with charge and discharge setpoints **Accepted**, and reported back under `chargingLimitSource` CSO |

## Needs further investigation

| # | Item | Owner | Detail |
|---|---|---|---|
| 1 | **Empty station ID admitted** | Lab (CitrineOS App) | Plugfest open admission accepted a WebSocket with no station ID in the path. CitrineOS then can't store its messages or address it. The listener should refuse an empty identity (HTTP 400/404) so the station sees a clear failure |
| 3 | **Secrets in the device model report** | Starcharge | The base report returns `ConfigurationCtrlr.Password` (a password hash), `ConfigurationCtrlr.PinPassword` (a plain PIN), the local authorisation list and setup card token, and the SIM's IMSI and ICCID. Credentials should be WriteOnly and not reported. Values are not recorded here |
| 4 | **Station clock** | Starcharge | `ClockCtrlr.DateTime` read 15:36:19**Z** at 05:36 UTC: local time labelled as UTC (time zone `Etc/GMT-10` / `UTC+10`; the venue is on AEDT, UTC+11). `TimeSource` is Heartbeat. The station's own message timestamps are correct UTC (StatusNotification 05:39:10Z at 16:39:10 AEDT), so only the reported `DateTime` value is mislabelled |
| 6 | **Zero setpoint dropped in ReportChargingProfiles** | Starcharge | Period 5 of 9620 was sent with `setpoint: 0`; the report omits `setpoint`. Check whether the station stores 0 or "no setpoint" for that period |
| 7 | **Empty composite schedule period** | Starcharge | GetCompositeSchedule with no transaction returns a period with no `limit`. OCPP 2.1 makes `limit` optional, but the composite schedule is meant to give the effective limit, here the 7.4 kW rating |
| 5 | **No plug-in available** | Starcharge | No EV can be connected, so no transaction, TxProfile or Cactus session is possible today. The station was **Unavailable** until the CSMS sent ChangeAvailability Operative (16:39:08); then connector 1 became Available |
| 2 | **Station ID missing from the connection URL** | Starcharge | The CSMS URL must end with the station ID: `ws://<host>:8083/<station-id>` (OCPP 2.x Security Profile 1) |

## Set-up

| | |
|---|---|
| Station | StarCharge **AD20074EU1923**, firmware **v3.20.5-standard**, serial SN2604180222 (from GetVariables; no BootNotification recorded). Station ID **`STARCHARGE-01`**, **OCPP 2.1**, EVSE 1 / connector 1 |
| CSMS | CitrineOS v2.0.1 in the CitrineOS server App **0.7.7** (Green build only: OCPP 2.1 DC_BPT and V2X charging needs accepted, `allowedEnergyTransfer` in AuthorizeResponse, metering-only SetVariables) |
| Endpoint | Venue LAN, port 8083, Security Profile 1 (`ws://<green>:8083/STARCHARGE-01`) |
| Admission | Plugfest **open admission on** (any station ID, no password) |
| Command station | Carried over from the ChargeSim session: `charger1`. To drive Starcharge from the lab bridge it must become the command station (CitrineOS restart) |
| Bridge | Carried over: automation on, prefix `citrineos_lab_charger1`, **charging-only**. For a V2G station: prefix `citrineos_lab_<station-id>`, charging-only **off** (CentralSetpoint periods), lab hold as needed, export mode for discharge tests |
| Tokens | `C17E0001`, `00054321` (ISO14443), eMAID `AAAAAAAAAAAAAA` (Plug & Charge), all Accepted |
| Lab automatics | Automatic GetBaseReport off |

## Device model (GetBaseReport, 16:36)

| Area | Reported |
|---|---|
| Station | StarCharge AD20074EU1923, firmware v3.20.5-standard, 1 EVSE / 1 connector, **single phase**, 35 A max (charge and discharge), grid power 7.4 kW, grid code AUA, grid type TN, country AU |
| V2X | `V2XChargingCtrlr` enabled; energy transfer **DC, DC_BPT**; operation modes **ChargingOnly, CentralSetpoint, LocalLoadBalancing** |
| Smart charging | Rate unit **W**, ProfileStackLevel 99, PeriodsPerSchedule 1024, SetpointPriority CSMS, no profiles installed |
| Metering | SampledDataCtrlr TxUpdatedInterval 10 s; AlignedDataCtrlr off (60 s interval) |
| Grid (AS/NZS 4777.2) | Active power rise/fall and reconnect rate 16.67 %/min, reconnect wait 60 s, voltage limits 0.89–1.10 pu, frequency 47.5–50.15 Hz, anti-islanding on |
| Local controls | LocalLoadBalancing and PeakShifting enabled; PV and DLC off; external GCP meter (EM112) configured but off |
| Availability | Connector 1 `Available=false`, EVSE and station AvailabilityState **Unavailable** |
| Device data limits | ItemsPerMessage 4 for GetVariables, SetVariables and GetReport (BytesPerMessage 5000) |
| Security | SecurityProfile 0, Basic Auth password unset, 3 certificates installed |
| Clock | Time zone `Etc/GMT-10`, NTP manual, time source Heartbeat |

## Connection

| Time (AEDT) | Event | Cause / fix |
|---|---|---|
| | | |

## Commands from the CSMS

| Time (AEDT) | Command | Starcharge response |
|---|---|---|
| | | |

## Transactions

| Transaction | Started (AEDT) | How it ended |
|---|---|---|
| | | |

## Progress log

Updated as testing continues. Times AEDT.

| Time | Change or result |
|---|---|
| about 16:19 | Test record opened. The Green was still unreachable from outside: `wss://ocpp.purcell.id.au` → Cloudflare 530 (tunnel down) and HA-OCPP 502, since about 16:10 (see the [ChargeSim report](../2026-10-23-chargesim-cactus/README.md)). Starcharge on the venue LAN works only if the Green itself is up |
| 16:26 | HA-OCPP reachable again; CitrineOS running (the lab's simulators online). **Starcharge not connected** (no new station since 16:10); ChargeSim's 11 stations offline. **Cloudflared App in `error` state**: it lost its Cloudflare edge connections at 16:10:2x (QUIC "no recent network activity", a venue network loss) and stopped, so `wss://ocpp.purcell.id.au` returns 530. The venue LAN endpoint `ws://purcell.local:8083` doesn't depend on it |
| 16:22:17 | CitrineOS had restarted after the 16:10 network loss (startup in its log); the lab's simulators reconnected |
| 16:28 | Starcharge trying the venue LAN listener on port 8083 |
| **16:28:37** | **A station connected on OCPP 2.1 with an empty station ID** (`ocppConnectionName` ""), CitrineOS station 110, admitted by open admission. It sends Heartbeats and CitrineOS answers them, but every message fails to persist (`ocpp-message-persist failed`, dead-lettered), so no BootNotification or other message is recorded and no command can target it. The connection URL had no station ID in its path (`ws://<host>:8083/` instead of `ws://<host>:8083/<station-id>`) |
| 16:30:18 | The empty-ID connection closed |
| **16:30:19** | **Starcharge connected as `STARCHARGE-01`**, OCPP 2.1, venue LAN port 8083 (CitrineOS station 112) |
| 16:30:24 | StatusNotification EVSE 1 / connector 1 **Unavailable** → accepted. No BootNotification recorded (vendor, model, serial and firmware unknown) |
| 16:31:21 | TriggerMessage `BootNotification` → **Rejected**. Correct per OCPP 2.x (F06.FR.17): a station whose last BootNotification was Accepted rejects a triggered one, so Starcharge's boot was accepted earlier, most likely on the 16:28:37 empty-ID connection, whose messages CitrineOS couldn't store |
| 16:32:46 | GetVariables with 8 entries → CALLERROR `OccurrenceConstraintViolation`. Correct: the station's `ItemsPerMessage` for GetVariables is 4 (from the base report), so the CSMS request was too large |
| **16:32:58** | GetVariables, ChargingStation VendorName / Model / SerialNumber / FirmwareVersion only → **Accepted ×4**: **StarCharge**, model **AD20074EU1923**, serial SN2604180222, firmware **v3.20.5-standard** |
| **16:36:19** | **GetBaseReport `FullInventory` (requested by the operator) → Accepted**; NotifyReport streamed 4 variables per message (24+ messages by 16:37:13). Highlights below |
| **16:39:08** | **ChangeAvailability `Operative`** (whole station) → **Accepted** |
| 16:39:10 | StatusNotification EVSE 1 / connector 1 **Available** (message timestamp 05:39:10Z, correct UTC) |
| **16:40:11** | **SetChargingProfile 9620, TxDefaultProfile** (EVSE 1, stack 0, Relative, W, 300 s, **CentralSetpoint**: setpoints +7.4 / −7.4 / +3.0 / −2.5 / 0 kW in 60 s steps, limit 7.4 kW, dischargeLimit −7.4 kW) → **Accepted** |
| 16:40:12 | CitrineOS's automatic GetChargingProfiles (`chargingLimitSource` CSO) → **Accepted**; ReportChargingProfiles returns 9620 with all 5 periods, so Starcharge files CSMS profiles under **CSO** (correct). The last period comes back **without its `setpoint: 0`** |
| 16:41:11 | **GetCompositeSchedule** (EVSE 1, 300 s, W) → **Accepted**: one period `{startPeriod: 0}` with **no limit, setpoint or operation mode**, scheduleStart 05:41:11Z. Without a transaction the Relative TxDefaultProfile has no start, so nothing constrains the EVSE; a composite schedule would normally still state the limit in force (the station maximum, 7.4 kW) |

## Plan

1. **TxProfile test** once Starcharge connects: profiles sent through the operator route to its
   station ID (no command-station change, no restart). First the station's details from
   BootNotification, then a remote start or the station's own session, then TxProfiles.
2. **Cactus run** after that: Starcharge becomes the command station (CitrineOS restart, so it
   reconnects once), the bridge goes to `citrineos_lab_<station-id>` with charging-only **off**
   (V2G CentralSetpoint periods), lab hold **off**, and the house load is set for the run.
   Metering SetVariables (0.7.7) if Starcharge doesn't send power by default.

## Open items

- Confirm the Green is back (tunnel, HA-OCPP), then check the CitrineOS App is running and
  ChargeSim's 11 stations have gone.
- Record Starcharge's station ID, OCPP version and endpoint; set it as the command station and the
  bridge to V2G mode if the lab is to drive it.
