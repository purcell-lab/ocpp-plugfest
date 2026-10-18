# Design note: dynamic electricity prices, OpenADR 3 to OCPP 2.1

**Status, October 2026.**
- OCPP side **built, in review**:
  - [purcell-lab/ha-addons#78](https://github.com/purcell-lab/ha-addons/pull/78): CitrineOS App 0.7.0, EVerest Apps 0.1.5 / 0.1.11.
  - [purcell-lab/CitrineOS-HA-Integration#10](https://github.com/purcell-lab/CitrineOS-HA-Integration/pull/10): integration 0.6.0.
- OpenADR price source: **in service** (purcell-lab VTN and the `openadr3_ven` VEN), with the
  adapter in CitrineOS-HA-Integration#10.

**Scope:** the Home Assistant lab stack, and the CSMS-under-test slots at the OCA Plugfest. The
chain is OpenADR 3.1 VTN → Home Assistant (VEN + EEMS) → CitrineOS → EVerest.

## Summary

The household energy management system (EEMS) takes its **price signal from an OpenADR 3.1 server
(VTN)**, the open standard for price and flexibility signals, and its **network envelope from
CSIP-AUS**. It decides the power and sends it to the charging station as an OCPP 2.1 profile. The
price travels to the station alongside the power, so the station and the driver can see why. Three
open standards make up one chain:

```
OpenADR 3.1 VTN ──PRICE / EXPORT_PRICE events──► Home Assistant (VEN + EEMS) ◄──CSIP-AUS (DOE)── DNSP
                                                      │
                                                      ▼  OCPP 2.1
                                          CitrineOS (CSMS) ──► charging station ──ISO 15118-20──► EV
```

OCPP 2.1 has two ways to carry a price to a charging station:
- **Tariffs** (functional block I, `SetDefaultTariff`), for billing and cost display.
- **Price schedules** on a charging profile (`absolutePriceSchedule`, `priceLevelSchedule`), for the
  station or the EV to plan with.

Neither tells the station what power to use. That stays with the EEMS.

| | Path | OCPP message | What it proves |
|---|---|---|---|
| **A** | Price drives power | `SetChargingProfile` TxProfile, `CentralSetpoint` | The charger, including V2G discharge, follows the OpenADR price through the same OCPP path as the CSIP-AUS envelope |
| **B** | Price travels with the profile | Same profile, plus `chargingSchedule.absolutePriceSchedule` | The forecast reaches the station in standard OCPP 2.1 form, alongside the setpoint it explains |
| **C** | Price shown at the station | `CostUpdated` with the OCA California Pricing extension | The station shows the price now and the next price, live, during the session |
| **D** | Tariff conformance | `SetDefaultTariff` (OCPP 2.1 block I) | Which Plugfest stations accept an OCPP 2.1 tariff built from the OpenADR prices, in AUD |

## Price source: OpenADR 3.1

### Why OpenADR

- **Source-neutral.** The EEMS takes a standard signal, not one retailer's API. Any OpenADR VTN can
  drive the chain: a retailer, an aggregator, a network, or our own lab VTN.
- **Built for prices.** OpenADR 3 events carry `PRICE` and `EXPORT_PRICE` payloads over time
  intervals, with currency and units in the program. "Continuous Pricing VEN" is one of the OpenADR
  3 certification profiles.
- **In production for EV charging.** In the Netherlands, three DSOs and eight CPOs run grid-aware
  charging on the open-source openleadr-rs, and EVerest is reported to be integrating it.
- **One message model for all event types.** The same events can carry short-notice events
  (Minimum System Load and Lack of Reserve price spikes) for the demonstration, using the same
  interval model.

### In service: the purcell-lab Australian VTN and the Home Assistant VEN

Both halves already run:

- **VTN:** an openleadr VTN at `https://openleadr-vtn-au.fly.dev`.
  - Programs and events are per NEM region and network tariff, for example `AU-QLD1-ENERGEX-6900`,
    `AU-NSW1-ESSENTIAL-BLNT3AL` and the raw regional reference price (`AU-QLD1-RRP`).
  - Prices are set through the [nem_pd7day](https://github.com/purcell-lab/nem_pd7day) integration
    (AEMO 7-day pre-dispatch plus the network tariff).
  - Each event carries about 7 days of intervals: 5-minute near now, 30-minute after.
- **VEN:** the `openadr3_ven` Home Assistant integration.
  - It creates `…_price`, `…_export_price` and `…_rrp` sensors per event. The state is the current
    interval. Attributes hold the next value, the daily minimum, maximum and average, and the row count.
  - The full forecast comes from its `openadr3_ven.get_forecast` service, not from attributes, to stay
    under the recorder's 16 KB limit. Each row is `{datetime, value, interval_minutes}`.

An event as served (abridged):

```json
{
  "programID": "6523d6f3-…",
  "eventName": "AU-QLD1-ENERGEX-6900",
  "payloadDescriptors": [
    {"payloadType": "PRICE", "units": "KWH", "currency": "AUD"},
    {"payloadType": "EXPORT_PRICE", "units": "KWH", "currency": "AUD"},
    {"payloadType": "RRP", "units": "KWH", "currency": "AUD"}
  ],
  "intervalPeriod": {"start": "2026-10-18T23:25:45+00:00", "duration": "P0Y0M0DT0H10080M0S"},
  "intervals": [
    {"id": 0, "intervalPeriod": {"start": "2026-10-18T23:25:00+00:00", "duration": "P0Y0M0DT0H5M0S"},
     "payloads": [{"type": "PRICE", "values": [0.209758]}, {"type": "EXPORT_PRICE", "values": [0.095519]},
                  {"type": "RRP", "values": [0.095519]}]},
    {"id": 1, "intervalPeriod": {"start": "2026-10-18T23:30:00+00:00", "duration": "P0Y0M0DT0H30M0S"},
     "payloads": [{"type": "PRICE", "values": [0.383078]}, {"type": "EXPORT_PRICE", "values": [0.239819]},
                  {"type": "RRP", "values": [0.239819]}]}
  ]
}
```

- **Values** are AUD/kWh including GST. `EXPORT_PRICE` is positive when the customer is paid. Negative
  prices are allowed.
- **Each interval has its own period,** so 5- and 30-minute intervals sit in one event.
- **`RRP`** is a private payload type: the wholesale regional reference price, for information.

### From the VEN to OCPP: the adapter (built)

The CitrineOS-HA integration
([purcell-lab/CitrineOS-HA-Integration#10](https://github.com/purcell-lab/CitrineOS-HA-Integration/pull/10))
treats any price sensor with a `payload_type` attribute as an OpenADR VEN sensor:
- It calls `openadr3_ven.get_forecast` for the next 48 hours.
- It converts the rows into the same intervals that the price schedule (B), `CostUpdated` (C) and
  tariff (D) builders already use.
- Messages then name the source: the price text reads "OpenADR 35.5 c/kWh now, 38.3 c/kWh from
  09:30", and the tariff ID is `openadr-YYYYMMDD-HHMM`.
- Amber sensors still work, as a fallback.

For the services:
- `price_entity` is the `…_price` sensor of the chosen event.
- `export_price_entity` is its `…_export_price` sensor (path D).

### Short-notice events

A one-minute-notice Minimum System Load price drop, or a Lack of Reserve export price spike, is a
change to the VTN's prices, made through nem_pd7day. The VEN picks it up on its next poll. The next
Home Assistant price update then carries it to the charger through paths A to D.

## What each component supports

| | CitrineOS 2.0.1 | EVerest 2025.10.0 (libocpp v0.30.3) |
|---|---|---|
| `SetDefaultTariff` | REST endpoint, OCPP 2.1 only | **Not implemented**: answers CALLERROR `NotImplemented` |
| `ChangeTransactionTariff`, `ClearTariffs`, `GetTariffs` | No endpoints | Not implemented |
| `CostUpdated` | REST endpoint; also sent every 60 s from its own tariff table | Applied when the Cost feature is enabled; California Pricing `customData` gives price now and next |
| `absolutePriceSchedule` / `priceLevelSchedule` on a profile | Passed through | Accepted and stored, **not acted on**; not passed to the EV |
| Prices to the EV over ISO 15118-20 | n/a | Not supported: the station runs dynamic mode (the station sets the power), and the ISO 15118-20 stack sends no price schedule |

The gaps are on the station side. That is why path D is a Plugfest test: vendor stations may
implement OCPP 2.1 tariffs that the open-source reference does not yet.

## Upstream status (EVerest, checked 19 October 2026)

- **OCPP 2.1 tariffs are still not implemented on everest-core main** (16 October 2026).
  - `SetDefaultTariff`, `ChangeTransactionTariff`, `GetTariffs` and `ClearTariffs` are in the
    not-implemented list in `lib/everest/ocpp/lib/ocpp/v2/charge_point.cpp`.
  - libocpp was folded into everest-core and its own repository was archived on 27 April 2026.
  - No issue or pull request proposes implementing these messages.
- **ISO 15118-20 sends no real price to the EV.** Main now sends a placeholder `PriceLevelSchedule`
  with zero price levels, because some testers reject a schedule exchange with no price schedule.
  The code comment says "The actual tariff is unknown here".
- **Recent pricing work is all California Pricing and cost display:**
  - tariff-message fallback handling ([#1989](https://github.com/EVerest/everest-core/pull/1989));
  - tariff messages on the consumer APIs ([#1922](https://github.com/EVerest/everest-core/pull/1922));
  - `default_price` publishing ([#2000](https://github.com/EVerest/everest-core/pull/2000));
  - a session-cost consumer API ([#1596](https://github.com/EVerest/everest-core/pull/1596));
  - DisplayCostAndPrice write rules ([#2077](https://github.com/EVerest/everest-core/pull/2077));
  - meter tariff-text limits ([#2542](https://github.com/EVerest/everest-core/pull/2542)).
- **[EVerest #1199](https://github.com/EVerest/everest-core/issues/1199)** asks for OCPP charging
  schedules, with price data, to be handed to ISO 15118 EVs.
  - It is open, in the backlog, and has no pull request.
  - A maintainer confirmed it is "still relevant" (12 November 2025) and sketched new callbacks
    between the OCPP and ISO 15118 libraries.
- **[EVerest #2527](https://github.com/EVerest/everest-core/pull/2527)** lets the station tell the EV
  at runtime that the charge is free (`FreeService`).
  - It is open, approved on 14 October 2026, and labelled `include-in-release`.
- **The older libocpp California Pricing issues** (#373–#378, #706) are closed. None cover OCPP 2.1
  tariffs.
- **Implication:** path C follows where upstream is investing. Path D will keep getting
  `NotImplemented` from EVerest, so it is a real differentiator when tested against vendor stations.
  Upgrading EVerest would not add tariff support.

## Path A: price drives power (exists)

The Home Assistant bridge already turns limits into OCPP 2.1 `CentralSetpoint` periods for the next
600 s (`citrine_ha.lab_schedule`).
- A price rule changes the setpoint: for example, charge when the OpenADR import price is low, and
  discharge when the export price spikes.
- The CSIP-AUS envelope still caps the setpoint.
- This is the only path in which the price changes what the charger does.

## Path B: price schedule on the profile

Each `lab_schedule` call can name a price sensor (`price_entity`, now `sensor.openadr_price`). The
integration converts the import forecast into an `absolutePriceSchedule` on the same OCPP 2.1
profile:

```json
"absolutePriceSchedule": {
  "timeAnchor": "2026-10-23T03:30:00Z",
  "priceScheduleID": 1,
  "currency": "AUD",
  "language": "en",
  "priceAlgorithm": "urn:iso:std:iso:15118:-20:PriceAlgorithm:1-Power",
  "priceRuleStacks": [
    {"duration": 300, "priceRule": [{"energyFee": {"value": 225, "exponent": -3},
                                     "powerRangeStart": {"value": 0, "exponent": 0}}]},
    {"duration": 1800, "priceRule": [{"energyFee": {"value": 202, "exponent": -3},
                                      "powerRangeStart": {"value": 0, "exponent": 0}}]}
  ]
}
```

- One price rule stack per interval, in $/kWh to three decimals (0.1 c/kWh).
- The gateway accepts at most 288 stacks and 48 hours, in AUD only.
- `priceLevelSchedule` (ordinal levels, no currency) is also accepted, for stations that prefer it.
- The EVerest status page shows the schedule as received. EVerest does not act on it.
- A price schedule has no export price. The export price travels in C and D.

## Path C: price at the station (California Pricing)

`citrine_ha.lab_cost_update` sends `CostUpdated` for the active transaction with the OCA
California Pricing extension:

```json
{
  "totalCost": 1.24,
  "transactionId": "…",
  "customData": {
    "vendorId": "org.openchargealliance.costmsg",
    "chargingPrice": {"kWhPrice": 0.225},
    "nextPeriod": {"atTime": "2026-10-23T04:00:00Z", "chargingPrice": {"kWhPrice": 0.202}},
    "priceText": "22.5 c/kWh now, 20.2 c/kWh from 14:00"
  }
}
```

- An automation calls it whenever the current OpenADR interval changes.
- The EVerest Apps:
  - enable the Tariff and Cost features in AUD;
  - turn on California Pricing;
  - show the latest price on the status page.
- CitrineOS's own 60-second `CostUpdated` comes from its zero-price lab tariff. It is switched off
  when price commands are enabled, so it does not overwrite the OpenADR price.
- Limits: one price now and one next, import only, during a transaction.

## Path D: OCPP 2.1 tariff to vendor stations

`citrine_ha.lab_default_tariff` sends `SetDefaultTariff` with the OpenADR forecast as an OCPP 2.1
`TariffType`:

- `currency` is AUD. `energy.prices[]` has one entry per interval, with
  `startTimeOfDay`/`endTimeOfDay` and `validFromDate`/`validToDate` in local time. An interval that
  crosses midnight is split.
- `priceKwh` excludes GST (the OpenADR price ÷ 1.1); `taxRates` is `[{type: "GST", tax: 10}]`.
- Export (discharge) prices come from `EXPORT_PRICE`.
  - They are entries with negative `minPower`/`maxPower` conditions, which is how OCPP 2.1 expresses
    reverse energy flow.
  - `priceKwh` is the negative export price, meaning the station pays the driver.
- At most 96 price entries per tariff.
- The station's reply is recorded verbatim: `Accepted`, `Rejected`, `TooManyElements`,
  `ConditionNotSupported`, or a CALLERROR such as `NotImplemented`.

D may target the command station or any provisioned Plugfest station that is online on OCPP 2.1.
It is information, not control, so it is allowed for vendor stations. Power commands to vendor
stations stay disabled.

## Safety and limits

- Everything is off by default: `price_commands_enabled: false` on the CitrineOS App.
- The gateway validates every price message: AUD only, −5 to 20 $/kWh, bounded sizes, only the
  listed fields. Power validation of setpoint profiles is unchanged.
- C needs the command station's active transaction. D needs a provisioned, online OCPP 2.1 station.
- The CitrineOS-HA integration reads the new `price_commands` policy separately, so older clients
  keep working.
- The OpenADR VEN only reads prices. A lost VTN connection keeps the last forecast until it expires,
  then falls back to Amber, or to no price. The CSIP-AUS envelope and the station's own limits are
  unaffected.

## Evidence

| Path | Evidence |
|---|---|
| Source | VTN event list and VEN reports; the price sensor tracks the VTN intervals |
| A | Meter follows the setpoint (as in the [V2G TxProfile result](../results/2026-10-17-v2g-txprofile/README.md)) |
| B | Profile `Accepted`; status page and `GetChargingProfiles` show the price schedule |
| C | `CostUpdated` frame in the station log; status page shows price now and next |
| D | Station reply per station, recorded in the slot notes |

## Remaining steps

1. **VEN on the Green.** Install `openadr3_ven` on the Green, pointed at the same VTN and events,
   because the CitrineOS-HA integration runs there.
2. **Venue connectivity.** The VTN is internet-hosted, so the Green needs internet at the Plugfest.
   If it has none, the fallback is a recorded forecast replayed into the same price sensors.
3. **Automations.** On each change of the `…_price` sensor:
   - call `lab_cost_update` (C);
   - call `lab_default_tariff` for vendor slots (D);
   - add `price_entity` to the bridge's `lab_schedule` calls (B).
4. **Demonstration.** Script the Friday price changes in nem_pd7day: a normal day, a one-minute-notice
   Minimum System Load price drop, and a Lack of Reserve export price spike.

## Open questions

- **CSIP-AUS pricing.** In Australia, network prices may arrive through CSIP-AUS instead.
  - Ausgrid's Project Edith sends dynamic network prices and envelopes over CSIP-AUS, and moves to an
    on-market tariff from July 2026.
  - The DER Integration API Technical Working Group has an activity to add retailer and network
    pricing to CSIP-AUS.
  - The VEN abstraction should allow a CSIP-AUS price source as well.
- **OpenADR 3.0 and 3.1.** openleadr-rs 0.2 and later implement 3.1 only, which is not
  backward-compatible with 3.0. Confirm which version the VTN serves before connecting third-party VENs.
- **ISO 15118-20 scheduled mode.** Passing price schedules to the EV needs scheduled mode and
  price-schedule support in the station's ISO 15118-20 stack; neither is in EVerest (see Upstream
  status).
- **CitrineOS cost calculation.** CitrineOS saves an accepted `SetDefaultTariff` with a zero flat
  price and does not link it to a connector, so its own cost figures ignore the pushed prices.
- **Tariff updates.** OCPP 2.1 tariffs are rule sets, not rolling forecasts, so each re-forecast is a
  new `tariffId`. `ChangeTransactionTariff`, for running sessions, needs a CitrineOS endpoint.

## References

- **OpenADR**
  - [OpenADR 3 introduction and certification](https://www.openadr.org/openadr-3-0)
  - [openleadr-rs](https://github.com/OpenLEADR/openleadr-rs), OpenADR 3.1 VTN and VEN in Rust
    (LF Energy); `openleadr-wire/src/event.rs` lists the event payload types (`PRICE`,
    `EXPORT_PRICE`, `IMPORT_CAPACITY_LIMIT`, …)
  - [LF Energy OpenLEADR](https://lfenergy.org/projects/openleadr/)
  - [Tweede golf: openleadr-rs for real-world demand response](https://tweedegolf.nl/en/blog/162/rust-meets-the-grid-building-openleadr-rs-for-real-world-demand-response/)
- **OCPP**
  - OCPP 2.1 JSON schemas (`SetDefaultTariffRequest`, `ChargingScheduleType`, `CostUpdatedRequest`)
  - [OCA: What's new in OCPP 2.1](https://openchargealliance.org/wp-content/uploads/2024/03/Whats-New-OCPP-2.1.pdf)
- **EVerest**
  - libocpp v0.30.3 `charge_point.cpp` and `functional_blocks/tariff_and_cost.cpp`
  - everest-core main `lib/everest/ocpp` and `lib/everest/iso15118/src/iso15118/d20/state/schedule_exchange.cpp`
  - [EVerest #1199](https://github.com/EVerest/everest-core/issues/1199) and [#2527](https://github.com/EVerest/everest-core/pull/2527)
  - [libocpp pricing issues (archived)](https://github.com/EVerest/libocpp/issues?q=tariff+OR+price+OR+cost)
- **CitrineOS:** v2.0.1 `set-default-tariff-endpoint.ts` and `cost-calculator.ts`
- **CSIP-AUS pricing:** [Ausgrid submission (Project Edith)](https://www.aemo.com.au/-/media/files/initiatives/der/2024/submissions/ausgrid.pdf?la=en)
  and [CIGRE C6-11978 (2026)](https://www.e-cigre.org/publications/detail/c6-11978-2026-managing-distribution-networks-and-enabling-der-participation-through-dynamic-network-pricing-in-australia-project-edith.html)
