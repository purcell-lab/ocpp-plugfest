# Imatra cloud ISO 15118-2 server in the lab

Status: evidence stage. Simulated station and EV only. Nothing is installed on
the HA Green, and no Cloudflare or charger configuration has changed.

## What Imatra is

[Imatra](https://github.com/Chargetronic/imatra.iso15118_server) (Chargetronic,
Finland, v0.1.0 released 18 November 2026, Apache 2.0) runs the ISO 15118-2 AC
SECC in the cloud. The device at the charger keeps the control pilot, SLAC,
TLS and metering, and tunnels V2G messages to the server over MQTT with mTLS.
The device answers the repeating Charging Loop from a cache that the server
pushes, so the server is not on the 2 s timing path.

An operator gets the EV's energy need, departure time and state of charge, and
can set per-device current limits and staged fleet activations through `/v1`
(OpenAPI 3.1) and an event feed read by cursor.

| In scope | Out of scope (this edition) |
|---|---|
| ISO 15118-2 AC with EIM, DIN 70121 SoC read-out, IEC 61851 PWM | ISO 15118-20, DC, bidirectional (V2G), Plug & Charge |
| Per-device limits (6 A minimum, with a duration), fleet activations | Per-device charging schedules (on its roadmap) |
| `/v1` API, event feed, keys with rights, audit | OCPP, OpenADR or HA adapters (left to separate projects) |

## How it fits the lab

| | EVerest + CitrineOS (existing) | Imatra |
|---|---|---|
| Where the SECC runs | At the charger | In the cloud |
| Grid interface | OCPP 1.6 / 2.0.1 / 2.1 | Its own `/v1` API |
| ISO 15118-20 and V2G | Yes | No |
| Departure time and energy need | Through OCPP 2.0.1 `NotifyEVChargingNeeds` | Directly from `/v1` events (`ev.parameters`) |

Imatra complements the lab rather than replacing anything. Its value is
smart AC charging for ISO 15118-2 EVs behind low-cost hardware. The useful
comparison is the EV data and control it exposes against the same data
reaching Home Assistant through OCPP and CitrineOS.

## Evidence

Workflow: [`.github/workflows/imatra-iso15118.yml`](../.github/workflows/imatra-iso15118.yml).
It fetches the test harness at `e1e9dfc` and Imatra at the harness's pin
`d07ba26` (the 0.1.0 release commit) at run time.

Imatra's own CI had not run when this was checked: GitHub refused to start
its jobs because of a billing problem on the Chargetronic account. These runs
are the first passing end-to-end evidence we have.

| Check | x86_64 | arm64 (HA Green's architecture) |
|---|---|---|
| Build every image, start Imatra and the harness | Pass | Pass |
| One ISO 15118-2 session with TLS, 0 contract problems | Pass | Pass |
| T2: limit confirmed via the Charging Loop cache | Pass, 52 ms | Pass, 50 ms |
| T2: limits below 6 A, above the station limit or without a duration refused (422) | Pass | Pass |
| T2: fleet activation confirmed, idempotent, ended | Pass | Pass |
| T6: session over plain TCP, then TLS again | Pass | Pass |
| T7: mTLS, ACL, block, 401/403, key revocation, rate limits, no internal ports published | Pass | Pass |

Run: <https://github.com/purcell-lab/ocpp-plugfest/actions/runs/44383271044>

Limits of this evidence:

- The station and EV are simulated over a virtual IPv6 link. There is no SLAC,
  PLC, control pilot or meter.
- Energy is a stub derived from the current limit (one session reported
  2.29 Wh on x86_64, 0 Wh on arm64). It is not a power-tracking measurement.
- The "confirmed" limit is the station acknowledging a new cache pair. It does
  not show that a real EV followed the limit.

## Licence and patent boundaries

- Imatra server: Apache 2.0. We can run it, change it and publish changes.
- Test harness: PolyForm Internal Use 1.0.0. We can use and change it inside
  purcell.id.au, but must not distribute it. This repository and
  `ha-addons` are public, so the harness is fetched at run time and never
  copied, forked publicly or packaged as an HA App.
- Patents: Chargetronic holds FI 20246111 A1 and EP 4711188 A1. Running the
  server is free. Charging devices or adapters built on the architecture need
  a licence from Chargetronic. A hardware trial needs a Chargetronic device.

## Proposed next stages

1. **Done:** reproducible end-to-end evidence on x86_64 and arm64.
2. **Lab host.** Run Imatra and the harness on a separate Linux host or VM,
   not on the HA Green. It needs Docker Compose (not available on HA OS),
   about ten containers including Postgres and Valkey, and port 8883, which
   can clash with the Mosquitto App. The Green already hosts CitrineOS and
   the V2G simulator.
3. **Home Assistant adapter (read-only first).** A small custom integration
   reading `/v1/devices`, `/v1/sessions` and the event feed with a `read` key:
   plug state, energy need, departure time, SoC, power, active limit.
4. **Control.** Add a `control` key and a service that maps a CSIP-AUS or HAEO
   site limit to `POST /v1/devices/{id}/limit`, with the 6 A floor and a
   duration, and record what the simulated station confirms.
5. **Hardware (optional).** Only with a Chargetronic device and a real
   ISO 15118-2 AC EV, with metered evidence that the EV followed the limit.
