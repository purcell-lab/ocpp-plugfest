# Plugfest slot 2: EVX Australia CC613_ELPR against the Purcell CitrineOS CSMS

**22 October 2026, about 11:15–11:40 AEDT.** EVX Australia's AC charger connected to the Purcell
CitrineOS CSMS on the venue LAN, first on OCPP 2.0.1 and then on OCPP 1.6J. **Both connections booted
and were accepted.**

- **OCPP 2.0.1:** the charger implements no Smart Charging functional block. `SetChargingProfile` is answered with a CALLERROR.
- **OCPP 1.6J:** the same firmware advertises the `SmartCharging` profile, in amps only.
- **No EV:** no EV or test load was available, so no transaction or charging-profile test could run under load.

| Check | OCPP 2.0.1 (`TEST4`) | OCPP 1.6J (`TEST5`) |
|---|---|---|
| Connect (Security Profile 1, plain `ws://`, port 8083) | Connected | Connected |
| `BootNotification` | Accepted | Accepted (interval 60 s) |
| Status | EVSE 1 / connector 1 `Available` | Connectors 0 and 1 `Available`, `NoError` |
| Device model / configuration | `GetBaseReport FullInventory` Accepted, 127 values | `GetConfiguration` answered, no unknown keys |
| Smart charging advertised | **No**: no `SmartChargingCtrlr` component | **Yes**: `SmartCharging` in `SupportedFeatureProfiles`, `Current` (A) only |
| `SetChargingProfile` | **CALLERROR `GenericError`**, "Unknown OCPP action: SetChargingProfile" | Not sent (see [Limits of this test](#limits-of-this-test)) |
| Remote start | Not tested | `RemoteStartTransaction` Accepted → `Authorize` Accepted → `Preparing`, back to `Available` after 60 s with no EV |
| Transactions and meter values | Not tested (no EV) | Not tested (no EV) |

## Set-up

| | |
|---|---|
| Charger | EVX Australia CC613_ELPR, firmware 6.2.2-245. The controller identifies its organisation as Bender. 1 EVSE, 1 socketed Type 2 connector (`sType2`), Ethernet. |
| CSMS | CitrineOS 0.7.3 (CitrineOS v2.0.1) on a Home Assistant Green, Plugfest listener `ws://192.168.88.252:8083/<station-id>` |
| Security | Security Profile 1 listener with open admission (no Basic Auth password needed), venue LAN |
| Station IDs | `TEST4` for the OCPP 2.0.1 run, `TEST5` for the OCPP 1.6J run |

## OCPP 2.0.1 (`TEST4`)

The charger booted at about 11:17 AEDT. CitrineOS requested a `GetBaseReport FullInventory`, which was
Accepted, and the station sent 127 variable values.

### Device model highlights

| Component | What it reports |
|---|---|
| `SmartChargingCtrlr` | **Absent.** `GetVariables` for `Enabled`, `Available`, `RateUnit`, `PeriodsPerSchedule`, `ProfileStackLevel`, `Entries` (ChargingProfiles), `ExternalControlSignalsEnabled`, `LimitChangeSignificance` and `NotifyChargingLimitWithSchedules` all returned `UnknownComponent` ("variable not implemented") |
| `EVSE` | `Power` Actual `0.0`. The `MaxSet` attribute is `NotSupportedAttributeType`. `SupplyPhases` 0 (the connector reports 3). |
| `DlmCtrlr` (vendor) | Bender dynamic load management: present, available and enabled, but `DlmMode` `Disabled`. Phase limit 16 / 16 / 16 A, minimum 6 A. External meter at the grid connection point (off). Solar mode "Grid Charging". |
| `ExternalMeter` (vendor) | Present and enabled; no second meter configured |
| `TxCtrlr` | `TxStartPoint` and `TxStopPoint` `PowerPathClosed`; stops on EV disconnect and on an invalid ID; `EVConnectionTimeOut` 45 s |
| `AuthCtrlr` | `AuthorizeRemoteStart` true, `LocalPreAuthorize` true, `LocalAuthorizeOffline` false |
| `SampledDataCtrlr` | `Energy.Active.Import.Register` only (started, updated every 60 s, ended); **signed readings** (`SignReadings`, `SignStartedReadings`) |
| `AlignedDataCtrlr` | Disabled (900 s interval if enabled) |
| `SecurityCtrlr` | `SecurityProfile` 1, no certificates installed, downgrade not allowed |
| `ISO15118Ctrlr` | Disabled; Plug & Charge off |
| `MonitoringCtrlr` | Not available |
| `OCPPCommCtrlr` | `WebSocketPingInterval` 60 s, `MessageTimeout` 30 s, `TransactionEvent` 5 attempts every 60 s |

### `SetChargingProfile`

Sent at 11:22:51 AEDT: a `ChargingStationMaxProfile` on EVSE 0, Absolute, 10 A on 3 phases for 600 s
(profile 9301, stack level 0). No transaction is needed for this profile. The charger answered 57 ms later:

```
[4, "bc5b5e50-322a-44c3-84af-715a4305ed06", "GenericError", "Generic error: Unknown OCPP action: SetChargingProfile", {}]
```

**Note for EVX.** For an action that isn't implemented, OCPP-J specifies the CALLERROR code
`NotImplemented` ("Requested Action is not known by receiver"), not `GenericError`. This is a small
conformance fix.

## OCPP 1.6J (`TEST5`)

The charger rebooted onto OCPP 1.6J and booted at 11:30:56 AEDT (`BootNotification` Accepted, interval
60 s). Its boot message reports an Eastron SDM120 Modbus meter. The SDM120 is a single-phase meter, but
the 2.0.1 device model reports a 3-phase connector, so this is worth confirming with EVX.

### Configuration (`GetConfiguration`, read at about 11:35 AEDT)

| Key | Value |
|---|---|
| `SupportedFeatureProfiles` | Core, FirmwareManagement, LocalAuthListManagement, Reservation, **SmartCharging**, RemoteTrigger |
| `ChargingScheduleAllowedChargingRateUnit` | `Current` (A only) |
| `ChargingScheduleMaxPeriods` | 255 |
| `ChargeProfileMaxStackLevel` | 255 |
| `MaxChargingProfilesInstalled` | 255 |
| `NumberOfConnectors` | 1 |
| `GetConfigurationMaxKeys` | 329 |
| `MeterValuesSampledData` (writable) | Energy.Active.Import.Register, Power.Active.Import, Current.Import, Frequency, SoC, Temperature |

On 1.6 the charger advertises smart charging in amps and samples power and current. On 2.0.1 it does
neither.

### Remote start without an EV

| Time (AEDT) | Message | Result |
|---|---|---|
| 11:38:12.848 | CSMS → `RemoteStartTransaction` (connector 1, idTag `C17E0001`) | Accepted |
| 11:38:13.031 | Charger → `Authorize` | Accepted by the CSMS |
| 11:38:13.416 | Charger → `StatusNotification` connector 1 | `Preparing` |
| 11:39:13.429 | Charger → `StatusNotification` connector 1 | `Available` (no EV within 60 s) |

As expected, no `StartTransaction` was sent without an EV.

## Limits of this test

- **No EV or test load:** no transaction, `MeterValues` or `TxProfile` test was possible on either version.
- **1.6 `SetChargingProfile` not sent.** The lab CSMS's scoped 1.6 command path only allows a W `TxProfile` tied to an active transaction. A station-level `ChargePointMaxProfile` or `TxDefaultProfile` in amps, which is what this charger supports without an EV, is not allowed yet. Adding it is lab follow-up work.
- **TLS not tested:** Security Profile 2 and 3 were not available on the CSMS (tracked in [ha-addons#92](https://github.com/purcell-lab/ha-addons/issues/92)).

## Suggested follow-ups

1. **EVX:** answer unimplemented actions with CALLERROR `NotImplemented`.
2. **EVX:** whether OCPP 2.0.1 smart charging (`SmartCharging` functional block, K01 `SetChargingProfile`) is planned for this firmware, as it is already on 1.6.
3. **EVX:** with a load, test a 1.6 `ChargePointMaxProfile` and `TxDefaultProfile` in A, and a `TxProfile` during a transaction, then `GetCompositeSchedule`.
4. **EVX:** whether a limit from the Bender DLM, external meter or operator phase limit is reported to the CSMS (`NotifyChargingLimit` on 2.0.1; there is no equivalent on 1.6).
5. **Lab:** allow station-level amp profiles and 1.6 `GetCompositeSchedule` and `ClearChargingProfile` for a real 1.6 command station.
