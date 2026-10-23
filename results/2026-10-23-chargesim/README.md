# ChargeSim against the Purcell CitrineOS CSMS (23 October 2026)

**Status: in progress.** Started about 15:14 AEDT, 23 October 2026. ChargeSim (station simulator)
against the Purcell CitrineOS CSMS. Times are AEDT.

## Executive summary

To be written when the session closes.

## What works

| Area | Result |
|---|---|
| | |

## Needs further investigation

| # | Item | Owner | Detail |
|---|---|---|---|
| | | | |

## Set-up

| | |
|---|---|
| Test tool | ChargeSim (vendor, model, firmware, OCPP version and EVSEs to be recorded from its BootNotification) |
| CSMS | CitrineOS v2.0.1 in the CitrineOS server App **0.7.6** (Green build only: DC_BPT and V2X charging needs accepted, `allowedEnergyTransfer` in AuthorizeResponse), on a Home Assistant Green |
| Endpoint | To be confirmed: `wss://ocpp.purcell.id.au/<station-id>` (internet, Cloudflare Tunnel, publicly trusted certificate) or `ws://purcell.local:8083/<station-id>` (venue LAN, Security Profile 1) |
| Admission | Carried over from the OCTT session: Plugfest **open admission on**; provisioned Basic Auth stations `SIM-EV-EVEREST-V2G-03` and `OCTT_OCA_21_1` |
| Command station | `SIM-EV-EVEREST-V2G-03` (the lab's GetTransactionStatus check doesn't target the station under test). Operator UI commands reach any connected station |
| Lab automatics | ODE bridge automation **off**. Automatic GetBaseReport set off (`device_model_reports: false`), applied at the next CitrineOS restart |
| Tokens | `C17E0001` (ISO14443), `00054321` (ISO14443), eMAID `AAAAAAAAAAAAAA` (Plug & Charge), all Accepted |

## Connection

| Time (AEDT) | Event | Cause / fix |
|---|---|---|
| | | |

## Commands from the CSMS

| Time (AEDT) | Command | ChargeSim response |
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
| about 15:14 | Test record opened; lab carried over from the OCTT (OCA) session ([report](../2026-10-23-octt-oca/README.md)) |

## Open items

- Confirm ChargeSim's station ID, OCPP version, endpoint and security profile, and provision a
  password if open admission is to be turned off.
