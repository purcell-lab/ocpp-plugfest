# ChargeSim against the Purcell CitrineOS CSMS (23 October 2026)

**Status: in progress.** Started about 15:14 AEDT, 23 October 2026. ChargeSim (station simulator)
against the Purcell CitrineOS CSMS. Times are AEDT.

## Executive summary

To be written when the session closes.

## What works

| Area | Result |
|---|---|
| Connection | OCPP 2.0.1, BootNotification Accepted, Heartbeat, StatusNotification |
| Device model | GetBaseReport Accepted, full NotifyReport |
| Remote start | RequestStartTransaction Accepted → TransactionEvent Started / Updated with meter values, idTokenInfo Accepted |
| Smart charging | Stepped W TxProfile with a `salesTariff` (9701) **Accepted** |

## Needs further investigation

| # | Item | Owner | Detail |
|---|---|---|---|
| 1 | **GetChargingProfiles returns NoProfiles after an accepted TxProfile** | ChargeSim | 9701 Accepted at 15:38:25, GetChargingProfiles (CSO) at 15:38:29 → NoProfiles. Expected Accepted plus ReportChargingProfiles. (CitrineOS asks for `chargingLimitSource` CSO; check whether ChargeSim files TxProfiles under a different source) |
| 2 | **Local token `1` Unknown** | Lab | ChargeSim's own Authorize (`Local`, `1`) at 15:33:45 → Unknown. Register it if ChargeSim's local-start tests need it |
| 3 | **Lab automatic GetBaseReport still on** | Lab | Needs a CitrineOS restart for `device_model_reports: false` (drops ChargeSim's connection) |

## Set-up

| | |
|---|---|
| Test tool | ChargeSim: BootNotification vendor `ChargeSim SCDE`, model `150kW Single`, firmware `0.0.0`, serial `charger1`, **OCPP 2.0.1**, station ID **`charger1`** (CitrineOS station 93), 1 EVSE / 1 connector |
| CSMS | CitrineOS v2.0.1 in the CitrineOS server App **0.7.6** (Green build only: DC_BPT and V2X charging needs accepted, `allowedEnergyTransfer` in AuthorizeResponse), on a Home Assistant Green |
| Endpoint | To be confirmed: `wss://ocpp.purcell.id.au/<station-id>` (internet, Cloudflare Tunnel, publicly trusted certificate) or `ws://purcell.local:8083/<station-id>` (venue LAN, Security Profile 1) |
| Admission | Carried over from the OCTT session: Plugfest **open admission on**; provisioned Basic Auth stations `SIM-EV-EVEREST-V2G-03` and `OCTT_OCA_21_1` |
| Command station | `SIM-EV-EVEREST-V2G-03` (the lab's GetTransactionStatus check doesn't target the station under test). Operator UI commands reach any connected station |
| Lab automatics | ODE bridge automation **off**. Automatic GetBaseReport **still on**: `device_model_reports: false` is set but CitrineOS hasn't restarted since 12:30 (the 15:19 outage was network only), so it sent one to `charger1` |
| Tokens | `C17E0001` (ISO14443), `00054321` (ISO14443), eMAID `AAAAAAAAAAAAAA` (Plug & Charge), all Accepted |

## Connection

| Time (AEDT) | Event | Cause / fix |
|---|---|---|
| | | |

## Commands from the CSMS

| Time (AEDT) | Command | ChargeSim response |
|---|---|---|
| 15:33:55 | GetBaseReport `FullInventory` (lab automatic) | Accepted, full NotifyReport |
| 15:37:40 | RequestStartTransaction (EVSE 1, `C17E0001`) | Accepted; transaction started |
| 15:38:25 | SetChargingProfile 9701 (TxProfile, W, stepped 50 → 0 kW, `salesTariff`) | **Accepted** |
| 15:38:29 | GetChargingProfiles (CSO) | NoProfiles |

## Transactions

| Transaction | Started (AEDT) | How it ended |
|---|---|---|
| `7a798266` | 15:37:40 (remote start, `C17E0001`) | Charging at 15:38 |

## Progress log

Updated as testing continues. Times AEDT.

| Time | Change or result |
|---|---|
| about 15:14 | Test record opened; lab carried over from the OCTT (OCA) session ([report](../2026-10-23-octt-oca/README.md)) |
| 15:19 | **Green offline:** `wss://ocpp.purcell.id.au` → Cloudflare 530 / error 1033 (no tunnel connector); Home Assistant Cloud remote access also unreachable |
| 15:23 | **Green back online:** the tunnel reaches the CitrineOS Plugfest listener again (plain HTTPS GET → CitrineOS 404 `Route GET:/ not found`, as expected without a WebSocket upgrade); Home Assistant Cloud remote access answers. CitrineOS itself didn't restart (last start 12:30) |
| **15:33:35** | **ChargeSim connected** as `charger1`, OCPP 2.0.1, open admission: **BootNotification Accepted** (interval 60 s); StatusNotification EVSE 1 / connector 1 **Occupied** |
| 15:33:45 | Authorize `1` (type `Local`) → **Unknown** (token not registered in CitrineOS) |
| 15:33:55 | Lab automatic GetBaseReport `FullInventory` → **Accepted**; NotifyReport streams the device model (SmartChargingCtrlr ProfileStackLevel 1000, AlignedDataCtrlr Interval 900 s, SampledDataCtrlr TxUpdatedInterval 0, SecurityCtrlr OrganizationName ChargeSim) |
| 15:36 | Heartbeats answered |
| **15:37:40** | **RequestStartTransaction** (EVSE 1, `C17E0001` ISO14443, remoteStartId 2310231) → **Accepted**; StatusNotification Occupied |
| 15:37:46–15:37:55 | Transaction **`7a798266`** `Started` (idToken `C17E0001`, meter value Transaction.Begin 0) → idTokenInfo **Accepted**; `Updated` with meter values → Accepted. CitrineOS shows it **Charging** |
| **15:38:25** | **SetChargingProfile 9701** (TxProfile, stack 1, Relative, 300 s, **W**: **50 → 25 → 11 → 5 → 0 kW** at 0 / 60 / 120 / 180 / 240 s, OCPP 2.0.1 `salesTariff` "OpenADR NSW1 0.3163 AUD/kWh", ePriceLevel 4 of 10) to `7a798266` → **Accepted** |
| 15:38:29 | GetChargingProfiles (CSO, sent by CitrineOS after the set) → **NoProfiles**: ChargeSim doesn't report the TxProfile it just accepted |


## Open items

- Confirm ChargeSim's station ID, OCPP version, endpoint and security profile, and provision a
  password if open admission is to be turned off.
