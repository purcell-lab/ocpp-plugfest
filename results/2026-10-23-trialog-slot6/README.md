# Plugfest slot 6: Trialog ComboCS4M-SW against the Purcell CitrineOS CSMS

**23 October 2026, about 09:30–11:05 AEDT.** Trialog's DC charging station (with its EV simulator)
connected to the Purcell CitrineOS CSMS on the venue LAN over **OCPP 2.1**. It was the first vendor
station at the Plugfest to ask for **bidirectional DC (ISO 15118-20 `DC_BPT`)**.

## Summary

- **Bidirectional charging needs: fixed on the CSMS during the slot.** CitrineOS v2.0.1 rejected
  every `DC_BPT` NotifyEVChargingNeeds, and the station then ended the session with
  `ReqEnergyTransferRejected`. The fix,
  [citrineos_server 0.7.4](https://github.com/purcell-lab/ha-addons/pull/96), was deployed at about
  10:48 AEDT. In both later sessions the needs were **Accepted**, and the station went to `Charging`
  in `CentralSetpoint` mode.
- **TxProfiles: accepted.** Every OCPP 2.1 CentralSetpoint TxProfile the lab bridge sent was
  **Accepted** (11 sends), including the stepped charge/discharge test. ReportChargingProfiles
  confirmed the profile was installed.
- **Authorisation: works after two changes.** The lab registered Trialog's corrected test token, and
  remote start works when the EV is already connected.
- **The stepped test could not be evaluated. The main open issues:**
  1. **Sessions stopped seconds after `Charging`.** Twice the station sent an invalid
     **NotifyEVChargingSchedule**, CitrineOS refused it, and the station then reported the
     transaction as not ongoing (`GetTransactionStatus` → `ongoingIndicator: false`), with no
     `Ended` event.
  2. **No power data.** The station reports only `Energy.Active.Import.Register`, every 300 s, so
     neither delivered nor discharged power could be measured.
  3. **At least 9 station reboots** during the slot, several straight after an error reply from the CSMS.

| Check | Result |
|---|---|
| Connect (Security Profile 1, plain `ws://`, port 8083, open admission) | ✅ Connected, OCPP 2.1 (`ocpp2.1`) |
| `BootNotification` | ✅ Accepted (interval 60 s). ⚠️ At least 9 `PowerUp` boots during the slot |
| Device model | ✅ `GetBaseReport FullInventory` Accepted |
| `ChargingStationMaxProfile` in W (EVSE 0) | ✅ Accepted (profile 9503, stack level 1, 7,000 then 3,500 W) |
| OCPP 2.1 `LocalGeneration` profile | ⛔ Not sent: CitrineOS v2.0.1's 2.1 schema has no `LocalGeneration` purpose |
| Local authorisation | ⚠️ `54321` (ISO14443) → CALLERROR · `00054321` → Unknown, then ✅ **Accepted** once registered (11:02) |
| Remote start (`RequestStartTransaction`, idToken `C17E0001`) | ✅ Accepted every time. A remote start before plug-in times out after 60 s |
| NotifyEVChargingNeeds `DC_BPT` | ⛔ Rejected on CitrineOS 0.7.3 → ✅ **Accepted** on 0.7.4 (twice) |
| TxProfile, OCPP 2.1 `CentralSetpoint` (+ charge / − discharge, `dischargeLimit`) | ✅ Accepted (11 sends); station reports `operationMode` `CentralSetpoint` |
| NotifyEVChargingSchedule | ⛔ 11 messages, all schema-invalid (CALLERROR `FormatViolation`) |
| Session stays open while charging | ⛔ Ended about 5–20 s after `Charging` (`ongoingIndicator: false`, no `Ended` event) |
| Stepped TxProfile test (+15 / −15 / +6 / −5 / 0 kW, 60 s each) | ⚠️ Profile installed, effect not measurable |
| Delivered power, discharge | ⛔ Not measurable (no power or export measurand) |

## Set-up

| | |
|---|---|
| Station | Trialog ComboCS4M-SW, firmware 3.4.1, OCPP 2.1, 1 EVSE / 1 connector, DC. Trialog's EV simulator on the cable (DC_BPT, up to ±50 kW). |
| CSMS | CitrineOS v2.0.1 in the CitrineOS server App 0.7.3, then **0.7.4** from about 10:48 AEDT, on a Home Assistant Green. Listener `ws://purcell.local:8083/TRIALOG-201`. |
| Security | Security Profile 1 (`SecurityProfile` 1 on the station), open admission, venue LAN |
| Lab control | The HA bridge sends one TxProfile (id 9001, stack 1, W, 600 s schedule ahead, with the OpenADR import price schedule) for the command station `TRIALOG-201`, rating set to 15 kW. For the TxProfile test: lab hold on (Open Dynamic Export ignored), hold import 25 kW, hold export 25 kW, export mode on. |
| Tokens | `C17E0001` (lab remote start). `00054321` registered by the lab at about 11:00 AEDT. |

## Device model highlights

| Variable | Value | Note |
|---|---|---|
| `V2XChargingCtrlr[1].Enabled` | `true` | Set locally by Trialog during the slot; the lab CSMS can't send SetVariables yet |
| `ElectricalFeed.Power` | 15,000 W | Set locally by Trialog |
| `EVSE.SupplyPhases` | 0 | DC |
| `AuthCtrlr.AuthorizeRemoteStart` | `false` | A remote start is not re-authorised by the station |
| `TxCtrlr.TxStartPoint` / `TxStopPoint` | `Authorized,EVConnected` | |
| `TxCtrlr.EVConnectionTimeOut` | 60 s | |
| `TxCtrlr.StopTxOnEVSideDisconnect` | `true` | |
| `SampledDataCtrlr.TxUpdatedMeasurands` | `Energy.Active.Import.Register` | No power, current or export register |
| `SampledDataCtrlr.TxUpdatedInterval` | 300 s | |
| `LocalAuthListCtrlr.Enabled` | `true` | |

## Timeline (AEDT)

Times are when CitrineOS stored each message.

### Sessions on CitrineOS 0.7.3

| Time | Event |
|---|---|
| 10:08:06 | `RequestStartTransaction` Accepted; transaction `30c6c3fd` starts (Idle, no EV) |
| 10:08:23 | TxProfile 9001 (CentralSetpoint −4,770 W) Accepted; `OperationModeChanged` → CentralSetpoint |
| 10:09:07 | Transaction ended: `EVConnectTimeout` (the EV was plugged in 61 s after the start) |
| 10:09:08 | EV plugged in; new transaction `5450c339` (`CablePluggedIn`, EVConnected) |
| 10:12:24, 10:12:54 | **Station reboots**; `5450c339` disappears without an `Ended` event |
| 10:15:34 | Connector `Faulted`; transaction `22884f36` ends with `EVCommunicationLost` / `EmergencyStop` |
| 10:16:29 | `Authorize` `54321` (ISO14443) → **CALLERROR** `PropertyConstraintViolation` |
| 10:19:00 | EV plugged in; transaction `b69b397e`; the EV asks for **`DC_BPT`** (±50 kW `v2xChargingParameters`) |
| 10:19:01 | NotifyEVChargingNeeds → **Rejected** by CitrineOS |
| 10:19:12 | **Station reboot**; a TxProfile sent during the reboot gets CALLERROR `SecurityError` "BootNotification is rejected!" |
| 10:19:54 | `RequestStartTransaction` Accepted and attached to `b69b397e` |
| 10:19:57 | `chargingState` → **Charging**, `operationMode` → ChargingOnly |
| 10:20:27 | A TxProfile **9504** (stack 2, not from the lab bridge) Rejected by the station: `startPeriod` was a Unix timestamp ("StartPeriod of first period not equal to 0"). TxProfile 9001 with the test steps Accepted |
| 10:20:24 (station clock) | Transaction ended: `AbnormalCondition`, stopped reason **`ReqEnergyTransferRejected`**, 11 Wh |

### First session on CitrineOS 0.7.4 (transaction `6e19e5ec`)

| Time | Event |
|---|---|
| about 10:48 | CitrineOS server App 0.7.4 deployed and restarted |
| 10:49:45, 10:50:53, 10:51:54, 10:52:45 | **Station reboots** |
| 10:49:54, 10:50:56, 10:51:57 | `Authorize` `54321` → CALLERROR, each time |
| 10:53:12 | `Authorize` `00054321` → **Unknown** (a valid reply; the token wasn't registered yet) |
| 10:53:37 | `RequestStartTransaction` (`C17E0001`) Accepted; transaction `6e19e5ec` `Started` (RemoteStart) |
| 10:53:38 | NotifyEVChargingNeeds `DC_BPT` → **Accepted** |
| 10:53:42 | `chargingState` **Charging**, `operationMode` **CentralSetpoint** |
| 10:53:43 | NotifyEVChargingSchedule ×4 → **CALLERROR `FormatViolation`** each time |
| 10:53:51 | TxProfile 9001 with the test steps installed (`ReportChargingProfiles`): −15,000 W, then +9,450 / −15,000 / +6,000 / −5,000 / 0 W, 60 s each, then −15,000 W |
| 10:54:02 | `GetTransactionStatus` → **`ongoingIndicator: false`**, no `Ended` event |
| 10:55:00 | `MeterValues` (Sample.Clock, not linked to the transaction): import register **0 Wh** (it was 1,000 Wh at the start) |

The +15 kW step was clamped to the site import headroom: hold import 25 kW + 95 % of solar − 105 % of
the 10 kW house load, about 9.1–9.5 kW.

### Second session on CitrineOS 0.7.4 (transaction `c6436d1b`)

| Time | Event |
|---|---|
| 10:58:06, 10:58:58 | `Authorize` `00054321` → Unknown; **station reboot** at 10:58:44; offline at 10:59:03 |
| about 11:00 | Lab registers `00054321` (ISO14443, Accepted) in CitrineOS |
| 11:01:23 | **Station reboot** (the 9th); connector Occupied |
| 11:01:52 | `RequestStartTransaction` Accepted, but the station attaches it to the **old** transaction ID `6e19e5ec` |
| 11:02:24–25 | Connector Available → Occupied (re-plug) |
| 11:02:26 | Transaction **`c6436d1b`** `Started` (`CablePluggedIn`) |
| 11:02:27 | `Authorize` `00054321` → **Accepted**; TransactionEvent `Authorized`; NotifyEVChargingNeeds `DC_BPT` → **Accepted** |
| 11:02:28 | TxProfile 9001 **Accepted**; `operationMode` **CentralSetpoint** |
| 11:02:30 | `chargingState` **Charging** |
| 11:02:30–31 | NotifyEVChargingSchedule ×6 → **CALLERROR `FormatViolation`** each time |
| 11:02:32 | `GetTransactionStatus c6436d1b` → **`ongoingIndicator: false`**, no `Ended` event. CitrineOS marks the transaction inactive, and the lab bridge stops sending profiles |
| to 11:05 | Heartbeats only; station online, connector Occupied, no transaction |

> **Note (added 23 October, after the OCTT session):** the `GetTransactionStatus` calls at 10:54:02
> and 11:02:32 were sent by the lab gateway's automatic transaction check, not by an operator.
> CitrineOS closed the transactions because of the `ongoingIndicator: false` replies. See
> [the OCTT report](../2026-10-23-octt-dnv/README.md#issue-the-labs-gettransactionstatus-check-interferes-with-the-station-under-test).

## Issues for Trialog

1. **Invalid NotifyEVChargingSchedule (11 messages).** Each one sent after the charging needs were
   accepted had:

   | Field | Sent | Required by the OCPP 2.1 schema |
   |---|---|---|
   | `timeBase` | `""` | date-time |
   | `chargingSchedule.startSchedule` | `""` | date-time |
   | `chargingSchedule.chargingRateUnit` | `"Undefined"` | `W` or `A` |
   | `chargingSchedule.chargingSchedulePeriod` | `[]` | at least 1 period |

   CitrineOS answered each with CALLERROR `FormatViolation`. If the EV has no schedule to report yet,
   the message shouldn't be sent.
2. **The transaction stops after the refused schedule, and no `Ended` event is sent.** In both
   sessions on 0.7.4 the station answered `GetTransactionStatus` with `ongoingIndicator: false`
   about 1–20 s after `Charging`, straight after the NotifyEVChargingSchedule CALLERRORs. The same
   happened to `5450c339` after a reboot. The CSMS can't tell why the session stopped or how much
   energy was transferred.
3. **Repeated reboots.** At least 9 `PowerUp` boots in about 50 minutes: 10:12:24, 10:12:54, 10:19:12,
   10:49:45, 10:50:53, 10:51:54, 10:52:45, 10:58:44 and 11:01:23. Several came within seconds of a
   refused message (Authorize CALLERROR or Unknown, NotifyEVChargingNeeds Rejected).
4. **Meter values too sparse to verify a profile.** Only `Energy.Active.Import.Register`, every
   300 s.
5. **Energy register reset.** The import register read 1,000 Wh at a transaction start and 0 Wh
   later. A register should only increase.
6. **A remote start was attached to a transaction that had already stopped.** At 11:01:52
   `RequestStartTransaction` returned `transactionId` `6e19e5ec`, which the station had reported as
   not ongoing at 10:54.
7. **Local test token.** `54321` with type `ISO14443` is not a valid ISO14443 UID (8 or 14 hex
   characters). `00054321` is now registered in the lab CSMS.

## Issues for the CSMS (lab)

| Issue | Status |
|---|---|
| CitrineOS v2.0.1 rejects OCPP 2.1 charging needs (`DC_BPT`, `DC_ACDP`, `DC_ACDP_BPT`): it matches DC needs only when `requestedEnergyTransfer` is exactly `DC` | **Fixed** in [citrineos_server 0.7.4](https://github.com/purcell-lab/ha-addons/pull/96): needs stored, Accepted, no automatic profile (the lab's TxProfile keeps control). Verified at 10:53:38 and 11:02:27 |
| Authorize with a malformed ISO14443 token gets CALLERROR `PropertyConstraintViolation`, not `idTokenInfo` `Invalid` | Open (upstream CitrineOS behaviour) |
| No scoped SetVariables, so `V2XChargingCtrlr.Enabled`, `EVConnectionTimeOut` and the sampled-data settings had to be set by Trialog locally | Open, [ha-addons#95](https://github.com/purcell-lab/ha-addons/issues/95) |
| OCPP 2.1 `LocalGeneration` (and `PriorityCharging`) profile purposes missing from CitrineOS's 2.1 schema | Open, [ha-addons#95](https://github.com/purcell-lab/ha-addons/issues/95) |
| A station-reported `validTo` of 2036 on a profile blocks a new profile with the same purpose and stack level (9502 at stack 0 refused; 9503 at stack 1 worked) | Open |
| A TxProfile 9504 with a Unix timestamp in `startPeriod` reached the station; the lab can't tell who sent it | Open: check the Operator UI and CitrineOS API logs |
| Without a power measurand, the Home Assistant EV power sensor shows 0 W while the station is charging | Expected with this station's settings (Trialog issue 4) |

## Areas for exploration

### Trialog

1. **NotifyEVChargingSchedule.** Send it only once the EV has a schedule, with real date-times, a
   `W` or `A` rate unit and at least one period (K15/K17 in OCPP 2.1). If the EV offers no schedule,
   omit the message rather than send an empty one.
2. **What ends the transaction?** Check the station and EV logs around 10:54:02 and 11:02:32:
   - Does a CALLERROR on NotifyEVChargingSchedule abort the ISO 15118-20 session?
   - Should it? A CALLERROR on a notify message shouldn't need to stop charging.
   - When a transaction does stop, the station should send `TransactionEvent` `Ended` with a
     `stoppedReason`.
3. **Reboots.** Which conditions restart the station: an Authorize CALLERROR or Unknown, a
   NotifyEVChargingNeeds Rejected, a `SecurityError`? A refused authorisation should stop the
   session, not restart the station.
4. **Meter values for V2X.** Set:
   - `SampledDataCtrlr.TxUpdatedMeasurands` = `Energy.Active.Import.Register,Energy.Active.Export.Register,Power.Active.Import,Power.Active.Export`;
   - `SampledDataCtrlr.TxUpdatedInterval` = 5 s.

   With those, a CSMS can confirm that each CentralSetpoint step is followed, discharge included.
5. **Transaction IDs after a reboot.** Don't return a stopped transaction's ID from
   `RequestStartTransaction`, and keep the energy register monotonic across reboots.
6. **CentralSetpoint behaviour.** Once sessions stay up, confirm how the station applies `setpoint`
   versus `limit` and `dischargeLimit`. Report the operation mode actually used for each period, and
   whether the EV's ±50 kW limits or `ElectricalFeed.Power` (15 kW) bound it.

### CitrineOS (upstream and the lab)

1. **OCPP 2.1 smart-charging handlers.** The 0.7.4 patch only accepts the 2.1 DC modes. An upstream
   fix should also:
   - store `v2xChargingParameters` (there is no column for them today);
   - calculate a 2.1 profile with CentralSetpoint or the V2X operation modes, as an option;
   - answer `NoChargingProfile` or `Processing` when the CSMS won't send a schedule.

   Raise it with CitrineOS upstream, with the Trialog message as a test case.
2. **Authorize error handling.** Answer a malformed token with `idTokenInfo.status` `Invalid`, not a
   CALLERROR. Some stations treat a CALLERROR as a fault.
3. **Tolerance of 2.1 notify messages.** CitrineOS answers a schema-invalid NotifyEVChargingSchedule
   with `FormatViolation`, which is correct. A lab option to log it and answer an empty CALLRESULT
   would keep vendor sessions alive while they fix it.
4. **Transaction state from `GetTransactionStatus`.** CitrineOS marks a transaction inactive when the
   station says `ongoingIndicator: false`, but no `Ended` event is ever recorded. Record a synthetic
   end (reason "station reported not ongoing"), so energy and duration are reported.
5. **Scoped SetVariables** for lab commands (`SampledDataCtrlr`, `TxCtrlr.EVConnectionTimeOut`,
   `V2XChargingCtrlr`), and the 2.1 `LocalGeneration` / `PriorityCharging` purposes
   ([ha-addons#95](https://github.com/purcell-lab/ha-addons/issues/95)).
6. **Profile validity.** A profile's `validTo` far in the future shouldn't block a replacement at the
   same stack level, or the CSMS should clear the old profile first.

## Next steps

1. **Trialog:** fix the NotifyEVChargingSchedule message (or don't send it), and configure the power
   and export measurands.
2. **Rerun the stepped TxProfile test:** plug in, then authorise locally with `00054321` or use a lab
   remote start. The test passes if power follows +9 / −15 / +6 / −5 / 0 kW within a few seconds of
   each step, and the export register increases during the discharge steps.
3. **Then a Cactus run with TRIALOG-201** as the command station (lab hold off, ODE restarted after the
   run starts).
