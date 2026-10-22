# Plugfest slot 6: Trialog ComboCS4M-SW against the Purcell CitrineOS CSMS

**23 October 2026, about 09:30–10:56 AEDT.** Trialog's DC charging station (with its EV simulator)
connected to the Purcell CitrineOS CSMS on the venue LAN over **OCPP 2.1**. It was the first vendor
station at the Plugfest to ask for **bidirectional DC (ISO 15118-20 `DC_BPT`)**.

- **Bidirectional charging needs:** CitrineOS v2.0.1 rejected every `DC_BPT` NotifyEVChargingNeeds, and
  the station then ended the session with `ReqEnergyTransferRejected`. We fixed the CSMS during the
  slot: [citrineos_server 0.7.4](https://github.com/purcell-lab/ha-addons/pull/96), deployed at about
  10:48. On the next session the needs were **Accepted**, and the station went to `Charging` in
  `CentralSetpoint` mode.
- **TxProfile steps:** every CentralSetpoint TxProfile the lab sent was **Accepted**, including the
  stepped charge/discharge test.
- **Power not tested:** no delivered or discharged power could be measured. The station reports only
  `Energy.Active.Import.Register`, every 300 s.
- **Issues for Trialog:** repeated reboots, an invalid NotifyEVChargingSchedule, a transaction that
  stopped without an `Ended` event, and the meter settings above (see
  [Issues for Trialog](#issues-for-trialog)).

| Check | Result |
|---|---|
| Connect (Security Profile 1, plain `ws://`, port 8083, open admission) | Connected, OCPP 2.1 (`ocpp2.1`) |
| `BootNotification` | Accepted (interval 60 s); the station rebooted (`PowerUp`) at least 7 times during the slot |
| Device model | `GetBaseReport FullInventory` Accepted |
| `ChargingStationMaxProfile` in W (EVSE 0) | Accepted (profile 9503, stack level 1, 7,000 then 3,500 W) |
| OCPP 2.1 `LocalGeneration` profile | Not sent: CitrineOS v2.0.1's 2.1 schema has no `LocalGeneration` purpose (lab gap, [ha-addons#95](https://github.com/purcell-lab/ha-addons/issues/95)) |
| Local authorisation (station `Authorize`) | Token `54321` (ISO14443): **CALLERROR** from CSMS; token `00054321`: **Unknown** (not provisioned) |
| Remote start (`RequestStartTransaction`, idToken `C17E0001`) | Accepted every time; starts at once when the EV is already connected |
| NotifyEVChargingNeeds `DC_BPT` | **Rejected** on CitrineOS 0.7.3 → **Accepted** on 0.7.4 |
| TxProfile, OCPP 2.1 `CentralSetpoint` (+ charge / − discharge, with `dischargeLimit`) | Accepted (8 sends); station reports `operationMode` `CentralSetpoint` |
| Stepped TxProfile test (+15 / −15 / +6 / −5 / 0 kW, 60 s each, clamped to the site headroom) | Profile Accepted and installed (confirmed by `ReportChargingProfiles`); **effect not measurable** |
| Delivered power, discharge | Not measurable (no power or export measurand) |

## Set-up

| | |
|---|---|
| Station | Trialog ComboCS4M-SW, firmware 3.4.1, OCPP 2.1, 1 EVSE / 1 connector, DC. Trialog's EV simulator on the cable. |
| CSMS | CitrineOS v2.0.1 in the CitrineOS server App 0.7.3, then **0.7.4** from about 10:48 AEDT, on a Home Assistant Green. Listener `ws://purcell.local:8083/TRIALOG-201`. |
| Security | Security Profile 1 (`SecurityProfile` 1 on the station), open admission, venue LAN |
| Lab control | The HA bridge sends one TxProfile (id 9001, stack 1, W, 600 s schedule ahead) for the command station `TRIALOG-201`, rating set to 15 kW. Lab hold on for the TxProfile test (ODE ignored), export mode on. |

## Device model highlights

| Variable | Value | Note |
|---|---|---|
| `V2XChargingCtrlr[1].Enabled` | `true` | Set locally by Trialog during the slot; the lab CSMS can't send SetVariables yet ([ha-addons#95](https://github.com/purcell-lab/ha-addons/issues/95)) |
| `ElectricalFeed.Power` | 15,000 W | Set locally by Trialog |
| `EVSE.SupplyPhases` | 0 | DC |
| `AuthCtrlr.AuthorizeRemoteStart` | `false` | A remote start is not re-authorised by the station |
| `TxCtrlr.TxStartPoint` / `TxStopPoint` | `Authorized,EVConnected` | |
| `TxCtrlr.EVConnectionTimeOut` | 60 s | A remote start sent before plug-in times out after 60 s (`EVConnectTimeout`) |
| `TxCtrlr.StopTxOnEVSideDisconnect` | `true` | |
| `SampledDataCtrlr.TxUpdatedMeasurands` | `Energy.Active.Import.Register` | No power, current or export register |
| `SampledDataCtrlr.TxUpdatedInterval` | 300 s | |
| `LocalAuthListCtrlr.Enabled` | `true` | |

## Timeline (AEDT)

Times are when CitrineOS stored each message.

### First sessions (CitrineOS 0.7.3)

| Time | Event |
|---|---|
| 10:08:06 | `RequestStartTransaction` Accepted; transaction `30c6c3fd` starts (Idle, no EV) |
| 10:08:23 | TxProfile 9001 (CentralSetpoint −4,770 W) Accepted; `OperationModeChanged` → CentralSetpoint |
| 10:09:07 | Transaction ended: `EVConnectTimeout` (EV plugged in 61 s after the start) |
| 10:09:08 | EV plugged in; new transaction `5450c339` (`CablePluggedIn`, EVConnected) |
| 10:12:24, 10:12:54 | **Station reboots** (`PowerUp`); `5450c339` disappears without an `Ended` event |
| 10:15:34 | Connector `Faulted`; transaction `22884f36` ends with `EVCommunicationLost` / `EmergencyStop` |
| 10:16:29 | `Authorize` `54321` (ISO14443) → **CALLERROR** `PropertyConstraintViolation` |
| 10:19:00 | EV plugged in; transaction `b69b397e`; the EV asks for **`DC_BPT`** (±50 kW `v2xChargingParameters`) |
| 10:19:01 | NotifyEVChargingNeeds → **Rejected** by CitrineOS |
| 10:19:12 | **Station reboot**; a TxProfile sent during the reboot gets CALLERROR `SecurityError` "BootNotification is rejected!" |
| 10:19:54 | `RequestStartTransaction` Accepted and attached to `b69b397e` |
| 10:19:57 | `chargingState` → **Charging**, `operationMode` → ChargingOnly |
| 10:20:27 | A TxProfile **9504** (stack 2, not from the lab bridge) Rejected by the station: `startPeriod` was a Unix timestamp ("StartPeriod of first period not equal to 0"); TxProfile 9001 with the test steps Accepted |
| 10:20:24 (station clock) | Transaction ended: `AbnormalCondition`, stopped reason **`ReqEnergyTransferRejected`**, 11 Wh |

### Fix and retest (CitrineOS 0.7.4)

| Time | Event |
|---|---|
| about 10:48 | CitrineOS server App 0.7.4 deployed and restarted |
| 10:49:45, 10:50:53, 10:51:54, 10:52:45 | **Station reboots** (`PowerUp`) |
| 10:49:54, 10:50:56, 10:51:57 | `Authorize` `54321` → CALLERROR, each time |
| 10:53:12 | `Authorize` `00054321` → **Unknown** (a valid reply; the token isn't provisioned) |
| 10:53:37 | `RequestStartTransaction` (`C17E0001`) Accepted; transaction `6e19e5ec` `Started` (RemoteStart) |
| 10:53:38 | NotifyEVChargingNeeds `DC_BPT` → **Accepted** |
| 10:53:42 | `chargingState` **Charging**, `operationMode` **CentralSetpoint** |
| 10:53:43 | NotifyEVChargingSchedule, 4 times → **CALLERROR `FormatViolation`** each time (see below) |
| 10:53:51 | TxProfile 9001 with the test steps installed: −15,000 W, then +9,450 / −15,000 / +6,000 / −5,000 / 0 W, 60 s each, then −15,000 W (`ReportChargingProfiles`) |
| 10:54:02 | `GetTransactionStatus` → `ongoingIndicator: false`. The station no longer runs the transaction, but sent no `Ended` event |
| 10:55:00 | `MeterValues` (Sample.Clock, not linked to the transaction): import register **0 Wh** (it was 1,000 Wh at the start) |
| to 10:56 | Heartbeats only; station online |

The +15 kW step was clamped to the site import headroom (lab hold import 25 kW + 95 % of solar − 105 %
of the 10 kW house load, about 9.1–9.5 kW).

## Issues for Trialog

1. **Invalid NotifyEVChargingSchedule.** After the charging needs were accepted, the station sent
   NotifyEVChargingSchedule four times with:
   - `timeBase: ""` and `chargingSchedule.startSchedule: ""` (both must be date-times);
   - `chargingRateUnit: "Undefined"` (must be `W` or `A`);
   - an empty `chargingSchedulePeriod` (at least one period is required).

   CitrineOS answered each with CALLERROR `FormatViolation`. If the EV has no schedule to report, the
   station shouldn't send the message.
2. **Transactions end without an `Ended` event.** Transaction `5450c339` (after the 10:12 reboots) and
   transaction `6e19e5ec` (at about 10:54, `GetTransactionStatus` `ongoingIndicator: false`) stopped
   without a `TransactionEvent` `Ended`. The CSMS can't tell why the session stopped, or how much energy
   was transferred.
3. **Repeated reboots.** At least 7 `PowerUp` boots during the slot. Several came soon after a refused
   message (Authorize CALLERROR, NotifyEVChargingNeeds Rejected), so it's worth checking whether the
   station restarts on an error reply.
4. **Meter values too sparse to verify a profile.** Only `Energy.Active.Import.Register`, every 300 s.
   To show that a CentralSetpoint is followed, and discharge in particular, please set:
   - `SampledDataCtrlr.TxUpdatedMeasurands` = `Energy.Active.Import.Register,Energy.Active.Export.Register,Power.Active.Import,Power.Active.Export`;
   - `SampledDataCtrlr.TxUpdatedInterval` = 5 (s).
5. **Energy register reset.** The import register read 1,000 Wh at the transaction start and 0 Wh at
   10:55. A register should only increase.
6. **Local test token.** `54321` with type `ISO14443` is not a valid ISO14443 UID (8 or 14 hex
   characters). `00054321` is valid, or use `Central` or `Local` for a free-form test token.
7. **`EVConnectTimeout` of 60 s:** a remote start sent before plug-in expires after 60 s. That's
   per spec. For lab sessions, either plug in first or raise `TxCtrlr.EVConnectionTimeOut`.

## Issues for the CSMS (lab)

| Issue | Status |
|---|---|
| CitrineOS v2.0.1 rejects OCPP 2.1 charging needs (`DC_BPT`, `DC_ACDP`, `DC_ACDP_BPT`): it matches DC needs only when `requestedEnergyTransfer` is exactly `DC` | **Fixed** in [citrineos_server 0.7.4](https://github.com/purcell-lab/ha-addons/pull/96): needs stored, Accepted, no automatic profile (the lab's TxProfile keeps control). Verified at 10:53:38 |
| Authorize with a malformed ISO14443 token gets a CALLERROR `PropertyConstraintViolation`, not `idTokenInfo` `Invalid` | Open (upstream CitrineOS behaviour). A CALLERROR leaves the station without an authorisation result; `Invalid` would be friendlier |
| No scoped SetVariables, so `V2XChargingCtrlr.Enabled`, `EVConnectionTimeOut` and the sampled-data settings had to be set by Trialog locally | Open, [ha-addons#95](https://github.com/purcell-lab/ha-addons/issues/95) |
| OCPP 2.1 `LocalGeneration` (and `PriorityCharging`) profile purposes missing from CitrineOS's 2.1 schema | Open, [ha-addons#95](https://github.com/purcell-lab/ha-addons/issues/95) |
| A station-reported `validTo` of 2036 on a profile blocks a new profile with the same purpose and stack level (profile 9502 at stack 0 was refused; 9503 at stack 1 worked) | Open, to add to [ha-addons#95](https://github.com/purcell-lab/ha-addons/issues/95) |
| Without a power measurand, the Home Assistant EV power sensor shows 0 W while the station is charging | Expected with this station's settings (issue 4 above) |

## Next steps

1. **Trialog:** fix issues 1, 2 and 4 above.
2. **Rerun the stepped TxProfile test:** plug in first, then a lab remote start. The test passes if
   power follows +9 / −15 / +6 / −5 / 0 kW within a few seconds of each step and the export register
   increases during the discharge steps.
3. **Then a Cactus run with TRIALOG-201** as the command station (lab hold off, ODE restarted after the
   run starts).
