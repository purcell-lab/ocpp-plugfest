# OCPP 2.1 EMS interoperability checklist (per vendor slot)

**What it's for.** Run these checks in each slot with a station that speaks OCPP 2.1 (some also apply
to 2.0.1). They gather evidence on how chargers support a **local energy management system (EMS)**
alongside the CSMS. That's the deployment model that fits Australian sites: a CPO's CSMS, plus a local
CSIP-AUS client enforcing the site's dynamic operating envelope.

Background: [What's New in OCPP 2.1 (OCA)](https://openchargealliance.org/wp-content/uploads/2024/03/Whats-New-OCPP-2.1.pdf),
the "Smart Charging" modes and "Energy management systems" slides. Lab follow-ups:
[ha-addons#87](https://github.com/purcell-lab/ha-addons/issues/87) (store and show `NotifyChargingLimit`)
[ha-addons#88](https://github.com/purcell-lab/ha-addons/issues/88) (local-EMS prototype on the EVerest simulator)
and [ha-addons#89](https://github.com/purcell-lab/ha-addons/issues/89) (CSIP-AUS `setGradW` as OCPP 2.1 DER control `Gradients`).

**Rules for the slot.**
- **Observe first.** Read-only checks need nothing beyond the slot set-up in the [runbook](RUNBOOK.md).
- **Setting profiles needs a command path.** Checks that send a profile need a command path to the
  vendor station. The Home Assistant command path is limited to `SIM-EV-` simulators, so use the
  Operator UI with commands enabled ([ha-addons#40](https://github.com/purcell-lab/ha-addons/issues/40)),
  or ask the vendor to set the limit from their side.
- **Agree each test with the vendor first.** Record what they say before you run it.
- **Recording results.** Record each result as **Supported**, **Rejected** (with the status or
  CALLERROR), **Not implemented** or **Not tested**, with the message trace.

## A. Device model (read-only)

With citrineos_server 0.7.2 the CSMS requests `GetBaseReport FullInventory` when a station comes online.
Before that, ask the vendor to send it.

- [ ] **`SmartChargingCtrlr`:** record `Enabled`, `Available`, `ExternalControlSignalsEnabled`,
      `NotifyChargingLimitWithSchedules`, `LimitChangeSignificance`, `RateUnit`, `PeriodsPerSchedule`,
      `ProfileStackLevel` and `Entries` (ChargingProfiles).
- [ ] **Power rating:** `EVSE.Power` and `ChargingStation.Power`. Record maxLimit and minLimit (a negative
      minLimit means discharge), and the MaxSet and MinSet attributes. These feed the CitrineOS-HA power
      rating sensors (0.6.2).
- [ ] **OCPP 2.1 V2X and operation-mode variables:** record whatever the station declares, for example
      the supported operation modes, and whether it lists `ExternalLimits`, `ExternalSetpoint` or
      `LocalLoadBalancing`.
- [ ] **`SmartChargingCtrlr.SupportedAdditionalPurposes`:** record the list. `LocalGeneration` and
      `PriorityCharging` are only supported if listed; an absent or empty list means neither. The lab's
      EVerest 2025.10 simulator reports it empty (libocpp lists 2.1 use case K27, "Smart Charging with EMS
      and LocalGeneration", as not implemented).

## B. External (EMS) limits reported by the station

- [ ] **Local EMS input:** does the station have one? Record the interface (Modbus, EEBus, a vendor API,
      a local controller, none). Ask whether it can be driven during the slot.
- [ ] **`NotifyChargingLimit` when a local limit applies:** record `chargingLimitSource` (`EMS`, `SO`, `CSO`,
      `Other`), `isGridCritical`, `isLocalGeneration` (2.1) and whether a `chargingSchedule` is included.
- [ ] **`ClearedChargingLimit`** when the local limit is removed.
- [ ] **The external limit wins:** with a local limit active, send a higher `TxProfile`. The station should
      keep the lower external limit. Record `GetCompositeSchedule` before and after.
- [ ] **The CSMS can't set it:** CitrineOS refuses `ChargingStationExternalConstraints` from the CSMS. Note
      whether the vendor expects a local controller to be able to set it.

## C. OCPP 2.1 profiles and modes sent by the CSMS (with a command path)

- [ ] **`LocalGeneration` profile** on EVSE 0 or the transaction's EVSE, as extra capacity on top of a
      grid limit. Record the `SetChargingProfile` status, `GetCompositeSchedule`, and the power the
      station actually allows.
- [ ] **Operation modes:** a `TxProfile` with `operationMode` `ExternalLimits`, then `ExternalSetpoint`.
      Record the status. If Accepted, record whose limit or setpoint the station follows, and what
      `GetCompositeSchedule` reports.
- [ ] **`LocalLoadBalancing`** (if the station has a site meter): record the status and behaviour. See E
      for the V2H questions.
- [ ] **Dynamic profiles:** a `TxProfile` with `dynUpdateInterval`, then `UpdateDynamicSchedule` with a
      new setpoint and limit. Record the statuses, and whether the station sends
      `PullDynamicScheduleUpdate`.
- [ ] **DER control `Gradients` and `EnterService`** ([ha-addons#89](https://github.com/purcell-lab/ha-addons/issues/89)):
      how the CSIP-AUS ramp rates map to the charger.
      - **First, read back:** `GetDERControl` for `Gradients` and `EnterService` (what the station
        already holds).
      - **Gradients:** send `SetDERControl` `Gradients` with `isDefault: true` and `gradient` and
        `softGradient` set. Record the status.
      - **EnterService:** send `SetDERControl` `EnterService` with `delay` 60 and `rampRate` set.
        Record the status.
      - **If Accepted:** does the station ramp a step change in its limit at that gradient? Does it
        apply the delay and ramp after a disconnect? Does it send `ReportDERControl` or
        `NotifyDERStartStop`?
      - **Units:** record how the vendor reads `gradient`, "ramp rate in seconds": time to 100 % of
        rating, or something else.
- [ ] **Priority charging:** does the station offer it (`PriorityCharging` purpose,
      `UsePriorityCharging`)? Record, but don't test unless the vendor asks.

## D. Comms loss with an EMS (only if B works)

- [ ] **During an outage:** with a local EMS limit active, ask the vendor to block the CSMS connection
      briefly. The station should keep the external limit.
- [ ] **After reconnecting:** does the station send the `NotifyChargingLimit` or `ClearedChargingLimit`
      it couldn't send during the outage? Compare ODE's lost DERControl responses in
      [ha-addons#86](https://github.com/purcell-lab/ha-addons/issues/86).

## E. V2H: supplying the local (house) load

OCPP 2.1 has no message that carries the site's load to the station. V2H works one of three ways,
depending on who knows the house load:

| Who knows the house load | Operation mode | How |
|---|---|---|
| The station, from its own grid-connection meter or CT | `LocalLoadBalancing` | The CSMS or EMS sets the mode and the bounds (`limit`, `dischargeLimit`); the station charges or discharges to balance the local load within them |
| A local EMS | `ExternalSetpoint` (or `ExternalLimits`) | The EMS measures the house load and gives the station the setpoint directly |
| The CSMS, fed by the EMS | `CentralSetpoint` | The lab today: the HA bridge adds the house-load cover to the setpoint it sends through CitrineOS |

`LocalGeneration` is the opposite case (extra capacity from solar), not a load to supply.

- [ ] **Site meter:** does the station have a grid-connection meter or CT input? Record the interface and
      whether it measures import and export at the connection point.
- [ ] **`LocalLoadBalancing`:** supported? If so, what target does it balance to (0 W at the connection
      point, or a configurable value), and does it stay within the profile's `limit` and `dischargeLimit`?
- [ ] **CSIP-AUS export limit:** with a 0 W export limit, does the station discharge only to cover the house
      load and never export? Record how the limit reaches it (`dischargeLimit`, an EMS input, a DER control).
- [ ] **Local EMS setpoint:** can a local EMS give it a discharge setpoint for the house load
      (`ExternalSetpoint`), and does the station report that limit with `NotifyChargingLimit`?
- [ ] **Bidirectional session:** does the EV session have to be ISO 15118-20 DC_BPT (or the AC equivalent)
      for discharge? Record what happens if a discharge is requested in a session that isn't bidirectional:
      the lab's EVerest simulator logs an error and keeps its previous charge limit (ALL-06, 21 October).
- [ ] **Backup / islanding:** record whether the vendor offers off-grid V2H. Out of scope for the slot.

## Results template

| Vendor | OCPP | A: device model | B: `NotifyChargingLimit` | B: external wins | C: `LocalGeneration` | C: `ExternalLimits` / `ExternalSetpoint` | C: dynamic profiles | C: DER `Gradients` / `EnterService` | E: V2H (meter, mode, export) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |
