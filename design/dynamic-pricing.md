# Design note: dynamic electricity prices over OCPP 2.1

**Status:** built, in review, October 2026: [purcell-lab/ha-addons#78](https://github.com/purcell-lab/ha-addons/pull/78) (CitrineOS App 0.7.0, EVerest Apps 0.1.5 / 0.1.11) and [purcell-lab/CitrineOS-HA-Integration#10](https://github.com/purcell-lab/CitrineOS-HA-Integration/pull/10) (0.6.0). **Scope:** the Home Assistant lab stack (Amber Electric →
Home Assistant → CitrineOS → EVerest) and the CSMS-under-test slots at the OCA Plugfest.

## Summary

OCPP 2.1 has two ways to carry a price to a charging station: **tariffs** (functional block I,
`SetDefaultTariff`) for billing and cost display, and **price schedules** on a charging profile
(`absolutePriceSchedule`, `priceLevelSchedule`) for the station or EV to plan with. Neither tells the
station what power to use. In this stack the **household EEMS decides the power** from the price
and the network envelope, and sends it as an OCPP 2.1 `CentralSetpoint` profile; the price travels
alongside it so the station and the driver can see why.

We build four paths:

| | Path | OCPP message | What it proves |
|---|---|---|---|
| **A** | Price drives power | `SetChargingProfile` TxProfile, `CentralSetpoint` | The charger (and V2G discharge) follows the Amber price, through the same OCPP path as the CSIP-AUS envelope |
| **B** | Price travels with the profile | Same profile, plus `chargingSchedule.absolutePriceSchedule` | The forecast reaches the station in standard OCPP 2.1 form, alongside the setpoint it explains |
| **C** | Price shown at the station | `CostUpdated` with the OCA California Pricing extension | The station shows the price now and the next price, live, during the session |
| **D** | Tariff conformance | `SetDefaultTariff` (OCPP 2.1 block I) | Which Plugfest stations accept an OCPP 2.1 tariff with Amber prices in AUD |

## Source: Amber Electric in Home Assistant

Two Amber integrations on the household (main) Home Assistant expose the same data. The Green, which
runs CitrineOS and the CitrineOS-HA integration, needs the same sensors: either the Amber Electric
integration installed on the Green (its own API token) or the main system's sensors mirrored to it.
Sensors seen on the main system, 19 October 2026:

- `sensor.amber_general_price` / `sensor.amber_feed_in_price`: the current import and feed-in price
  in $/kWh including GST.
- `sensor.amber_general_forecast` / `sensor.amber_feed_in_forecast` (`forecasts` attribute), or the
  Amber Express sensors (`detailedForecast` attribute): **48 intervals, about 20 hours ahead**, the
  first hour in 5-minute intervals and then 30-minute intervals. Each interval has `per_kwh`,
  `start_time`, `end_time`, `spot_per_kwh`, `descriptor` and `spike_status`. Feed-in values are
  positive (paid to the customer). Prices can be negative.

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

## Path A: price drives power (exists)

The Home Assistant bridge already turns limits into OCPP 2.1 `CentralSetpoint` periods for the next
600 s (`citrine_ha.lab_schedule`). A price rule (for example, charge when import is cheap, discharge
when the feed-in price spikes) changes the setpoint; the CSIP-AUS envelope still caps it. This is the
only path in which the price changes what the charger does.

## Path B: price schedule on the profile

Each `lab_schedule` call can name a price sensor (`price_entity`). The integration converts the
Amber import forecast into an `absolutePriceSchedule` on the same OCPP 2.1 profile:

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

- One price rule stack per Amber interval, in $/kWh with three decimals (0.1 c/kWh).
- The gateway accepts at most 288 stacks and 48 hours, in AUD only.
- `priceLevelSchedule` (ordinal levels, no currency) is also accepted for stations that prefer it.
- The EVerest status page shows the schedule as received. EVerest does not act on it.
- There is no export price in a price schedule; the export price travels in C and D.

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
    "priceText": "Amber 22.5 c/kWh now, 20.2 c/kWh from 14:00"
  }
}
```

- An automation calls it whenever the Amber price changes.
- The EVerest Apps enable the Tariff and Cost features (currency AUD) and California Pricing, and
  show the latest price on the status page.
- CitrineOS's own 60-second `CostUpdated` (from its zero-price lab tariff) is switched off when
  price commands are enabled, so it does not overwrite the Amber price.
- Limits: one price now and one next, import only, during a transaction.

## Path D: OCPP 2.1 tariff to vendor stations

`citrine_ha.lab_default_tariff` sends `SetDefaultTariff` with the Amber forecast as an OCPP 2.1
`TariffType`:

- `currency` AUD; `energy.prices[]`, one entry per interval, with `startTimeOfDay`/`endTimeOfDay`
  and `validFromDate`/`validToDate` in local time (an interval that crosses midnight is split).
- `priceKwh` excludes GST (Amber price ÷ 1.1); `taxRates` `[{type: "GST", tax: 10}]`.
- Export (discharge) prices are entries with negative `minPower`/`maxPower` conditions, which OCPP 2.1
  uses for reverse energy flow; `priceKwh` is the negative feed-in price (the station pays the driver).
- At most 96 price entries per tariff.
- The station's reply is recorded verbatim: `Accepted`, `Rejected`, `TooManyElements`,
  `ConditionNotSupported`, or a CALLERROR such as `NotImplemented`.

D may target the command station or any provisioned Plugfest station that is online on OCPP 2.1.
It is information, not control, so it is allowed for vendor stations; power commands to vendor
stations stay disabled.

## Safety and limits

- Everything is off by default: `price_commands_enabled: false` on the CitrineOS App.
- The gateway validates every price message: AUD only, −5 to 20 $/kWh, bounded sizes, only the
  listed fields. Power validation of setpoint profiles is unchanged.
- C needs the command station's active transaction; D needs a provisioned, online OCPP 2.1 station.
- The CitrineOS-HA integration reads the new `price_commands` policy separately, so older clients
  keep working.

## Evidence

| Path | Evidence |
|---|---|
| A | Meter follows the setpoint (as in the [V2G TxProfile result](../results/2026-10-17-v2g-txprofile/README.md)) |
| B | Profile `Accepted`; status page and `GetChargingProfiles` show the price schedule |
| C | `CostUpdated` frame in the station log; status page shows price now and next |
| D | Station reply per station, recorded in the slot notes |

## Open questions

- **ISO 15118-20 scheduled mode.** Passing price schedules to the EV needs scheduled mode and
  price-schedule support in the station's ISO 15118-20 stack; neither is in EVerest 2025.10.0.
- **CitrineOS cost calculation.** CitrineOS saves an accepted `SetDefaultTariff` with a zero flat
  price and does not link it to a connector, so its own cost figures ignore the pushed prices.
- **Tariff updates.** OCPP 2.1 tariffs are rule sets, not rolling forecasts; each re-forecast is a
  new `tariffId`. `ChangeTransactionTariff` (for running sessions) needs a CitrineOS endpoint.

## References

- OCPP 2.1 JSON schemas (`SetDefaultTariffRequest`, `ChargingScheduleType`, `CostUpdatedRequest`)
- OCA *What's new in OCPP 2.1*
- libocpp v0.30.3 `charge_point.cpp`, `functional_blocks/tariff_and_cost.cpp`
- CitrineOS v2.0.1 `set-default-tariff-endpoint.ts`, `cost-calculator.ts`
