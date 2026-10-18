# The proposal (30 July 2026) and what has been built since

[**`purcell_ocpp_plugfest_briefing.pdf`**](purcell_ocpp_plugfest_briefing.pdf): *Open-source CSIP-AUS to
OCPP demonstration*, the scoping note sent to the OCA Plugfest organisers on 30 July 2026.

It proposed a public, reproducible demonstration of all three draft AS 5438 protocols on one
household stack: SEP2 via CSIP-AUS and OCPP 2.1 as the primary paths, SunSpec Modbus as the
secondary path, with Home Assistant as the EEMS.

## Then and now

| | Proposed (July) | Built (October) |
|---|---|---|
| CSIP-AUS client | Open Dynamic Export | Open Dynamic Export, packaged as a Home Assistant App |
| CSIP-AUS server | CSIP-AUS server or Cactus | **Cactus CSIP-AUS v1.2 test harness**, LOA-11 passed 16/16 on AC and on DC V2G |
| EEMS | Home Assistant + ODE | Home Assistant Green; schedule-ahead bridge from ODE limits to charging profiles |
| CSMS | lbbrhzn/ocpp integration (OCPP 2.1 experimental) | **CitrineOS** (open-source CSMS: OCPP 2.1, 2.0.1, 1.6) as a Home Assistant App, with the CitrineOS-HA integration |
| Charging station | Bidirectional OCPP charger | **EVerest** simulators: OCPP 2.1 AC charger and a **DC V2G charger with ISO 15118-20 DC_BPT**, ±25 kW |
| Bidirectional control | OCPP 2.1 V2X profile | OCPP 2.1 TxProfile, `operationMode: CentralSetpoint`, `setpoint`/`limit`/`dischargeLimit` in W. No DER control block |
| Optimiser | HAEO over AEMO spot price | Not in the Plugfest path: the demonstration shows the envelope → profile chain directly |
| SunSpec Modbus | Secondary path | Secondary path, unchanged |
| Plugfest role | Demonstration | Demonstration **and** CSMS under test in six vendor slots |

## Known gaps named in the proposal

- ODE Cactus gaps LOA-05 (subscriptions) and GEN-11 (EventSuperseded): still to be retested.
- Three-protocol coordination not yet measured against the AS 5438 function map: timing evidence
  now exists for the CSIP-AUS → OCPP path (LOA-11 step responses, V2G TxProfile).
- OCPP 2.1 experimental in lbbrhzn/ocpp: resolved by moving the CSMS role to CitrineOS.
