# ChargeSim against the Purcell CitrineOS CSMS (23 October 2026)

**Status: closed.** 23 October 2026, about 15:14–15:44 AEDT. ChargeSim (ChargeSim SCDE
station simulator, "150kW Single") against the Purcell CitrineOS CSMS, on **OCPP 2.0.1**, as station
`charger1`. Times are AEDT.

## Executive summary

ChargeSim connected at 15:33:34 and was admitted through Plugfest open admission. It completed
BootNotification, StatusNotification, Heartbeat and a full device model report (GetBaseReport →
NotifyReport). It accepted a remote start (RequestStartTransaction with RFID `C17E0001`) and
reported the transaction Started and then Charging. It accepted an OCPP 2.0.1 **TxProfile with
power and price** (5 power steps from 50 kW to 0 W, plus an ISO 15118-2 `salesTariff` built from the
OpenADR NSW1 price). The station applies the profile: its composite schedule follows the power steps,
counted from the transaction start, and falls back to its 157.9 kW maximum when the profile ends.
The meter readings agree: charging suspended (`SuspendedEVSE`) for exactly the 0 W step and resumed
when the profile ended. A remote stop ended the transaction at 15:44:04 with 4.815 kWh delivered.

**Findings for ChargeSim**

1. A profile the CSMS sets is accepted and applied, but reported with `chargingLimitSource: "Other"`, not `CSO`, so a
   GetChargingProfiles filtered on `CSO` returns `NoProfiles` (item 1).
2. The `salesTariff` sent in the TxProfile isn't returned in ReportChargingProfiles (item 2).

## What works

| Area | Result |
|---|---|
| Transport | WebSocket upgrade with `ocpp2.0.1`, admitted through Plugfest open admission |
| Boot | BootNotification **Accepted** (interval 60 s): vendor **ChargeSim SCDE**, model **150kW Single**, serial `charger1`, firmware `0.0.0`. One EVSE |
| Status and heartbeat | StatusNotification accepted; Heartbeat answered throughout |
| Device model | GetBaseReport `FullInventory` (sent automatically by the lab, see Set-up) **Accepted**, followed by a full NotifyReport (SmartChargingCtrlr ProfileStackLevel 1000, AlignedDataCtrlr Interval 900 s, SampledDataCtrlr TxUpdatedInterval 0, SecurityCtrlr OrganizationName ChargeSim, SimulationCtrlr CSChargerType "150kW Single") |
| Remote start | RequestStartTransaction (EVSE 1, `C17E0001` ISO14443, remoteStartId 2310231) → **Accepted**. TransactionEvent Started (`RemoteStart`, EVConnected) then Updated (`ChargingStateChanged` → Charging, 3 phases), all `idTokenInfo` Accepted |
| TxProfile with power and price | SetChargingProfile 9701 (Relative TxProfile, W, 300 s, 50 / 25 / 11 / 5 / 0 kW in 60 s steps, `salesTariff` with 10 price levels) → **Accepted** |
| Profile reporting | GetChargingProfiles by ID → Accepted; ReportChargingProfiles returns profile 9701 with all 5 periods (`numberPhases: 3`, `minChargingRate: 0` added) |
| Profile effect | TransactionEvent meter values follow the profile: `SuspendedEVSE` at 15:41:39, the start of the 0 W step (15:41:40), with energy flat at 2.250 → 2.253 kWh; back to `Charging` at 15:42:41, when the profile ended (15:42:40); then 2.253 → 4.815 kWh in 82 s, about 113 kW average without a profile |
| Remote stop | RequestStopTransaction → **Accepted**; TransactionEvent Ended (`RemoteStop`, stoppedReason `Remote`, Transaction.End 4.815 kWh); CitrineOS answered `totalCost: 0` |
| Composite schedule | GetCompositeSchedule (300 s, W) → Accepted, with the profile's steps counted from the transaction start and the station maximum (157 894.7 W) after the profile ends |

## Needs further investigation

| # | Item | Owner | Detail |
|---|---|---|---|
| 1 | `chargingLimitSource` of CSMS profiles | ChargeSim | Profile 9701 came from the CSMS but is reported with `chargingLimitSource: "Other"`. CitrineOS's automatic GetChargingProfiles after SetChargingProfile filters on `CSO` and got `NoProfiles` (15:38:29), so CitrineOS can't see the installed profile that way. A CSMS-set profile is expected to report `CSO` |
| 2 | `salesTariff` not reported | ChargeSim | ReportChargingProfiles for 9701 omits the `salesTariff` that was sent and accepted. It isn't clear whether ChargeSim keeps the tariff and doesn't echo it, or drops it. An ISO 15118-2 EV session would show whether the tariff reaches the EV |
| 3 | Energy only, no power readings | ChargeSim | ChargeSim sent energy (`Energy.Active.Import.Register`) only on TransactionEvents, at state changes; no periodic MeterValues and no power measurand (SampledDataCtrlr TxUpdatedInterval is 0). The 0 W step is proven by the suspend; the 50 / 25 / 11 / 5 kW steps can't be checked without power readings. Set TxUpdatedInterval and add `Power.Active.Import` to TxUpdatedMeasurands for a rerun |
| 4 | Local token `1` Unknown | Lab | ChargeSim's own Authorize (`1`, type `Local`) at 15:33:45 → Unknown, as the token isn't registered in CitrineOS. Register it if ChargeSim's local-start tests need it |
| 5 | Price in OCPP 2.0.1 | Lab | The lab can only attach an absolute AUD price schedule (`absolutePriceSchedule`) on OCPP 2.1. On 2.0.1 the price went as a `salesTariff` (price level and relative cost). CostUpdated with the AUD price only reaches the lab's command station, not `charger1`. Rerun on OCPP 2.1 for a priced TxProfile in AUD |

## Set-up

| | |
|---|---|
| Test tool | ChargeSim SCDE, model "150kW Single", firmware `0.0.0`, OCPP 2.0.1, station ID `charger1`, 1 EVSE / 1 connector (CitrineOS station row 93) |
| CSMS | CitrineOS v2.0.1 in the CitrineOS server App **0.7.6** (Green build only: DC_BPT and V2X charging needs accepted, `allowedEnergyTransfer` in AuthorizeResponse), on a Home Assistant Green |
| Endpoint | Plugfest listener, open admission (no Basic Auth) |
| Admission | Plugfest **open admission on**; provisioned Basic Auth stations `SIM-EV-EVEREST-V2G-03` and `OCTT_OCA_21_1` |
| Command station | `SIM-EV-EVEREST-V2G-03` (unchanged; the lab's GetTransactionStatus check and CitrineOS-HA services don't target `charger1`). Commands to `charger1` went through the gateway's operator route (the same fixed command set as the Operator UI), each logged by CitrineOS as `Operator command …` |
| Lab automatics | ODE bridge automation **off**. **Automatic GetBaseReport still on:** `device_model_reports: false` is set but CitrineOS hasn't restarted since 12:30 (the 15:19 outage was the tunnel and Home Assistant Cloud, not a reboot), so the lab sent GetBaseReport to `charger1` at 15:33 |
| Tokens | `C17E0001` (ISO14443), `00054321` (ISO14443), eMAID `AAAAAAAAAAAAAA` (Plug & Charge), all Accepted |
| Price source | OpenADR VTN (openleadr-vtn-au), NSW1 Essential import price: **0.3163 AUD/kWh** at 15:35 (day range 0.2465–0.4448, average 0.3503) |

## Connection

| Time (AEDT) | Event | Cause / fix |
|---|---|---|
| 15:33:34 | `charger1` connects on `ocpp2.0.1`, BootNotification Accepted, interval 60 s (ChargeSim SCDE, 150kW Single) | Open admission |
| 15:33:40, 15:33:49 | StatusNotification EVSE 1 / connector 1 | CitrineOS warns "Missing component or variable for status notification" until the device model is known (harmless) |
| 15:33:45 | Authorize `1` (type `Local`) → **Unknown** | Token not registered in CitrineOS (item 4) |

## Commands from the CSMS

| Time (AEDT) | Command | ChargeSim response |
|---|---|---|
| 15:33:55 | GetBaseReport `FullInventory` (lab automatic, see Set-up) | **Accepted**, NotifyReport follows (last part seen 15:36:19) |
| 15:37:40 | RequestStartTransaction, EVSE 1, `C17E0001` ISO14443, remoteStartId 2310231 | **Accepted**; StatusNotification Occupied; TransactionEvent Started |
| 15:38:25 | **SetChargingProfile 9701**, TxProfile with power and price (below) | **Accepted** |
| 15:38:29 | GetChargingProfiles `chargingLimitSource: [CSO]` (CitrineOS automatic follow-up) | **NoProfiles** (item 1) |
| 15:38:44 | GetCompositeSchedule, EVSE 1, 300 s, W | **Accepted**: 25 kW (0 s), 11 kW (56 s), 5 kW (116 s), 0 W (176 s), 157 894.7 W (237 s), schedule start 15:38:44 |
| 15:38:49 | GetChargingProfiles, profile ID 9701 | **Accepted**; ReportChargingProfiles at 15:38:50 with all 5 periods, `chargingLimitSource: "Other"`, no `salesTariff` (items 1, 2) |
| 15:44:04 | RequestStopTransaction `7a798266…` | **Accepted**; TransactionEvent Ended, 4.815 kWh |

### TxProfile 9701 (power and price)

```json
{
  "evseId": 1,
  "chargingProfile": {
    "id": 9701,
    "stackLevel": 1,
    "chargingProfilePurpose": "TxProfile",
    "chargingProfileKind": "Relative",
    "transactionId": "7a798266e4ea48beb4ccf389932a6a47",
    "chargingSchedule": [{
      "id": 9701,
      "duration": 300,
      "chargingRateUnit": "W",
      "chargingSchedulePeriod": [
        {"startPeriod": 0,   "limit": 50000},
        {"startPeriod": 60,  "limit": 25000},
        {"startPeriod": 120, "limit": 11000},
        {"startPeriod": 180, "limit": 5000},
        {"startPeriod": 240, "limit": 0}
      ],
      "salesTariff": {
        "id": 1,
        "salesTariffDescription": "OpenADR NSW1 0.3163 AUD/kWh",
        "numEPriceLevels": 10,
        "salesTariffEntry": [{
          "relativeTimeInterval": {"start": 0, "duration": 300},
          "ePriceLevel": 4,
          "consumptionCost": [{"startValue": 0,
            "cost": [{"costKind": "RelativePricePercentage", "amount": 90}]}]
        }]
      }
    }]
  }
}
```

The price is expressed the only way OCPP 2.0.1 allows inside a charging schedule. Price level 4 of
10 places 0.3163 AUD/kWh within the day's range (0.2465–0.4448). The relative price is 90 % of the
day's average (0.3503 AUD/kWh).

The profile is Relative, so it counts from the transaction start (15:37:40), not from when it was
sent (15:38:25). The 50 kW first step had passed by the time it arrived. The composite schedule
confirms this: at 15:38:44 (64 s into the transaction) the limit is 25 kW, and each later step
falls on the minute after 15:37:40. The 0 W step runs 15:41:40–15:42:40, then the station returns
to its own maximum.

## Transactions

| Transaction | Started (AEDT) | How it ended |
|---|---|---|
| `7a798266e4ea48beb4ccf389932a6a47` (EVSE 1) | 15:37:40, RemoteStart, `C17E0001`; Charging from 15:37:41, 3 phases | 15:44:04, RequestStopTransaction → Ended, stoppedReason `Remote`, **4.815 kWh** |

## Progress log

Updated as testing continues. Times AEDT.

| Time | Change or result |
|---|---|
| about 15:14 | Test record opened; lab carried over from the OCTT (OCA) session ([report](../2026-10-23-octt-oca/README.md)) |
| 15:19 | **Green unreachable from outside:** `wss://ocpp.purcell.id.au` → Cloudflare 530 / error 1033 (no tunnel connector); Home Assistant Cloud remote access also unreachable |
| 15:23 | **Green reachable again:** the tunnel reaches the CitrineOS Plugfest listener (plain HTTPS GET → CitrineOS 404 `Route GET:/ not found`, as expected without a WebSocket upgrade); Home Assistant Cloud remote access answers |
| 15:30 | Correction: CitrineOS **did not restart** during the outage (its log runs unbroken from the 12:30 start), so `device_model_reports: false` is **not yet in effect** |
| 15:33:34 | **ChargeSim connects** as `charger1` (OCPP 2.0.1); BootNotification Accepted, StatusNotification |
| 15:33:45 | Authorize `1` (`Local`) → Unknown |
| 15:33:55 | Lab automatic GetBaseReport `FullInventory` → Accepted; NotifyReport streams the device model |
| 15:37:40 | RequestStartTransaction Accepted; transaction `7a798266…` Started, then Charging |
| 15:38:25 | **TxProfile 9701 with power and price Accepted** |
| 15:38:29–15:38:50 | Profile checks: CSO-filtered GetChargingProfiles → NoProfiles; GetCompositeSchedule matches the profile; GetChargingProfiles by ID → profile reported with source `Other` and no `salesTariff` |
| 15:41:39 | TransactionEvent Updated: `SuspendedEVSE` (0 W step), 2.250 kWh |
| 15:42:41 | TransactionEvent Updated: back to `Charging` when the profile ends, 2.253 kWh |
| **15:44:04** | **Session stopped:** RequestStopTransaction → Accepted; TransactionEvent Ended (`Remote`), **4.815 kWh**. ChargeSim stays connected |

## Open items

- Rerun with power readings to check each power step (item 3).
- Ask the ChargeSim team about items 1 and 2.
- Rerun the priced TxProfile on OCPP 2.1 for an AUD `absolutePriceSchedule` (item 5).
- Register local token `1` if ChargeSim's local-start tests need it (item 4).
- Restart CitrineOS between test runs so the automatic GetBaseReport switch-off takes effect.
