# Plugfest retrospective: the Purcell CitrineOS lab (17–23 October 2026)

What the test reports from the Plugfest week show when read together: what went well, the problems
that kept coming back, and what to change before the next event. Times are AEDT.

## Reports covered

| Date | Report | Station or client | OCPP | Outcome in one line |
|---|---|---|---|---|
| 17–19 Oct | [V2G TxProfile](../2026-10-17-v2g-txprofile/README.md), [network-constrained](../2026-10-19-v2g-network-constrained/README.md), [night house load](../2026-10-19-v2g-night-house-load/README.md) | EVerest DC V2G simulator | 2.1 | Bidirectional TxProfiles followed, CSIP-AUS limits met |
| 20–22 Oct | Cactus [GEN-10](../2026-10-20-cactus-gen10/README.md), [GEN-11](../2026-10-20-cactus-gen11/README.md), [ALL-28](../2026-10-20-cactus-all28/README.md), [ALL-23](../2026-10-20-cactus-all23/README.md), [LOA-10](../2026-10-21-cactus-loa10/README.md), [ALT-ALL-29](../2026-10-21-cactus-alt-all29/README.md), [ALL-06](../2026-10-21-cactus-all06/README.md), [ALL-21](../2026-10-22-cactus-all21/README.md), [ALT-LOA-13](../2026-10-21-cactus-alt-loa13/README.md) | ODE + EVerest DC V2G | 2.1 | All passed in Cactus; ALL-06 and ALT-LOA-13 needed bridge fixes |
| 22 Oct | [ALT-ALL-29 with EVSE](../2026-10-22-cactus-alt-all29-evse/README.md) | EVSE Ocular IOCAH39-7S | 2.0.1 | First Cactus pass with a vendor charger |
| 22 Oct | [EVX slot 2](../2026-10-22-evx-slot2/README.md) | EVX CC613_ELPR | 2.0.1, 1.6J | Booted on both; no smart charging on 2.0.1; no EV |
| 23 Oct | [Trialog slot 6](../2026-10-23-trialog-slot6/README.md) | Trialog ComboCS4M-SW | 2.1 | DC_BPT fixed live (0.7.4); 11 CentralSetpoint TxProfiles accepted; sessions dropped |
| 23 Oct | [OCTT (OCA)](../2026-10-23-octt-oca/README.md) | OCA OCPP Compliance Test Tool | 2.1 | Connection, auth, Plug & Charge work; two CSMS gaps fixed (0.7.5, 0.7.6); V2X profiles not proven |
| 23 Oct | [ChargeSim](../2026-10-23-chargesim/README.md), [Cactus and 11 stations](../2026-10-23-chargesim-cactus/README.md) | ChargeSim SCDE simulator | 2.0.1 | 11 stations, all profiles accepted; metering fixed live (0.7.7); ALT-ALL-29 not valid |
| 23 Oct | [StarCharge slot 10](../2026-10-23-starcharge-slot10/README.md) | StarCharge AD20074EU1923 | 2.1 | 14/14 commands answered; V2X TxDefaultProfile accepted; no EV |

## What went well

1. **Every station connected and was accepted.** EVX (2.0.1 and 1.6J), Trialog (2.1), OCTT (2.1 over the
   internet), 11 ChargeSim stations at once (2.0.1) and StarCharge (2.1) all booted. Plugfest open
   admission and the Cloudflare tunnel let vendors join on the venue LAN or remotely without
   per-station provisioning.
2. **Charging profiles were widely accepted.** Trialog accepted all 11 bidirectional CentralSetpoint
   TxProfiles. ChargeSim accepted every profile on all 11 stations and visibly followed a 0 W step.
   StarCharge accepted a bidirectional TxDefaultProfile and a ChargingStationMaxProfile, and reported
   them back under `chargingLimitSource` CSO. EVSE's Ocular followed Cactus limits end to end.
3. **CSMS gaps were fixed during the event.** Four CitrineOS server App releases went out on the
   day, each with tests and an exact-build guard, and each unblocked a vendor:

   | Release | Fix | Unblocked |
   |---|---|---|
   | 0.7.4 | Accept OCPP 2.1 DC charging needs (`DC_BPT`, `DC_ACDP`, `DC_ACDP_BPT`) | Trialog |
   | 0.7.5 | `allowedEnergyTransfer` in Accepted OCPP 2.1 AuthorizeResponses | OCTT |
   | 0.7.6 | Accept V2X charging needs with only `v2xChargingParameters` (AC_BPT) | OCTT |
   | 0.7.7 | Operator SetVariables for metering variables only | ChargeSim |

4. **The Cactus → ODE → CitrineOS → charger chain passes CSIP-AUS tests.** Nine Cactus test
   definitions passed, including ALT-ALL-29 with a vendor charger.
5. **Reports were same-day and evidence-based.** Each slot has a report with message-level logs,
   charts and spec references, sent to the vendor within the slot, so findings are actionable.

## Recurring problems

| # | Theme | Where it showed up | Effect |
|---|---|---|---|
| 1 | **No EV or test load** | EVX, StarCharge; OCTT only simulates; Trialog sessions dropped seconds after `Charging` | Profiles accepted but their effect rarely seen. **Discharge was never measured on a vendor station** |
| 2 | **Missing or coarse metering** | EVX (energy only), Trialog (energy every 300 s), OCTT (none), ChargeSim (power only when asked over OCPP) | Neither the lab nor Cactus could check that a station followed a limit |
| 3 | **CSMS OCPP 2.1 gaps** (CitrineOS v2.0.1) | DC_BPT and AC V2X needs, `allowedEnergyTransfer`, no `LocalGeneration` purpose, no SetVariables route, NotifyEVChargingSchedule handling | Each bidirectional slot hit at least one; fixed by build-time patches, not upstream yet |
| 4 | **Lab automation interfering with tests** | GetTransactionStatus check closed live transactions (OCTT, likely Trialog); automatic GetBaseReport; 10 kW synthetic house load took 5.8 kW off every Cactus limit; bridge drives one station only | Unrequested messages to stations under test; misleading limits; multi-station Cactus not possible |
| 5 | **Lab stability** | Network losses 15:19 and 16:10 on 23 Oct; CitrineOS restarts at 16:22 and a crash at about 16:46; Cloudflared stopped and stayed down (watchdog off); every config change needs a CitrineOS restart, dropping all stations (OCTT doesn't reconnect) | Lost test time and ended two sessions early |
| 6 | **Onboarding friction** | OCTT station ID and password mismatch; StarCharge connected with an empty station ID (and the lab accepted it); `purcell.local` resolution; Trialog token format (`54321` vs `00054321`) | 10–30 minutes lost per slot |
| 7 | **Inconsistent profile reporting** | ChargeSim reports CSMS profiles as `Other`; OCTT answered NoProfiles after Accepted; StarCharge's EVSE composite ignores the station maximum; Trialog's NotifyEVChargingSchedule all schema-invalid | Accepting profiles works; reading them back doesn't yet |
| 8 | **Security hygiene** | StarCharge's device model exposes a plain-text PIN, password hash and local authorisation list; the lab ran open admission on the internet with Security Profile 1 | Credentials leak through standard reports; an open endpoint |

## What to do differently

### Before the event

- **Pre-slot checklist, agreed with each vendor in advance:** station ID, OCPP version, endpoint as
  an IP address (not `purcell.local`), security profile, token type and value, whether an EV or load
  bank is available, which measurands the station can send.
- **Ask vendors to bring an EV emulator or load bank.** It's the single biggest gap in what could be
  tested.
- **Agree a V2X test case with the OCA** (Q-section, DC_BPT or discharge-capable AC_BPT,
  DynamicControl) so the bidirectional TxProfile can be exercised.

### Lab behaviour

- **A standard "on connect" step:** refuse empty station IDs; send metering SetVariables (power and
  energy every 10 s); check availability; GetBaseReport only on request.
- **A vendor-slot profile for the lab:** GetTransactionStatus check off, automatic reports off,
  house load 0, and the bridge settings recorded in each run's report.
- **Never close a transaction on a single `ongoingIndicator: false`** while the station still sends
  TransactionEvents for it.

### Lab robustness

- Change Plugfest stations and the command station without restarting CitrineOS.
- Turn on Cloudflared's watchdog; investigate the 16:46 CitrineOS crash; check the Green's memory
  headroom or move CitrineOS to a larger host for multi-station tests.
- Multi-station bridge: a group limit across stations and summed site power in ODE's readings.
- Close the internet endpoint (or require Basic Auth / Security Profile 2) outside test slots.

### Upstream and vendor follow-up

- Offer the 0.7.4–0.7.7 patches to CitrineOS upstream.
- Vendor findings to follow up: ChargeSim (`chargingLimitSource`, power by default), StarCharge
  (credentials in reports, composite schedules), Trialog (NotifyEVChargingSchedule, session drops,
  reboots), OCA (`ongoingIndicator`, scripted TxProfile acceptance), EVX (no Smart Charging on 2.0.1).

### Process

- **One session drives the lab at a time.** On 23 October two Claude sessions overlapped during the
  ChargeSim slot.
- **Log runs to the report automatically** (connection, commands, replies, meter values) instead of
  polling by hand, so reports keep up during busy slots.
- **Real time only** while Cactus or the bridge is involved: CitrineOS has no simulated clock.
