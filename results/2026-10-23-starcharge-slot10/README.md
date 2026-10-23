# Starcharge against the Purcell CitrineOS CSMS (23 October 2026, slot 10)

**Status: in progress.** Started about 16:19 AEDT, 23 October 2026. Starcharge V2G charging station
(Plugfest slot 10) against the Purcell CitrineOS CSMS. Times are AEDT.

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
| Station | Starcharge V2G charging station (station ID, model, firmware, OCPP version and EVSEs to be recorded from its BootNotification) |
| CSMS | CitrineOS v2.0.1 in the CitrineOS server App **0.7.7** (Green build only: OCPP 2.1 DC_BPT and V2X charging needs accepted, `allowedEnergyTransfer` in AuthorizeResponse, metering-only SetVariables) |
| Endpoint | `ws://purcell.local:8083/<station-id>` on the venue LAN (Security Profile 1), or `wss://ocpp.purcell.id.au/<station-id>` over the internet |
| Admission | Plugfest **open admission on** (any station ID, no password) |
| Command station | Carried over from the ChargeSim session: `charger1`. To drive Starcharge from the lab bridge it must become the command station (CitrineOS restart) |
| Bridge | Carried over: automation on, prefix `citrineos_lab_charger1`, **charging-only**. For a V2G station: prefix `citrineos_lab_<station-id>`, charging-only **off** (CentralSetpoint periods), lab hold as needed, export mode for discharge tests |
| Tokens | `C17E0001`, `00054321` (ISO14443), eMAID `AAAAAAAAAAAAAA` (Plug & Charge), all Accepted |
| Lab automatics | Automatic GetBaseReport off |

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

## Open items

- Confirm the Green is back (tunnel, HA-OCPP), then check the CitrineOS App is running and
  ChargeSim's 11 stations have gone.
- Record Starcharge's station ID, OCPP version and endpoint; set it as the command station and the
  bridge to V2G mode if the lab is to drive it.
