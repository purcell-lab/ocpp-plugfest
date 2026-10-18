# Demonstration script: CSIP-AUS envelope to OCPP 2.1 bidirectional charging

**Slot:** Friday 23 October 2026, after lunch, under one hour. No long-running soak tests.
**Goal:** show a home energy management system coordinating CSIP-AUS dynamic operating envelopes
and turning them into OCPP 2.1 bidirectional charging profiles that a charging station validates,
and show how fast the end-to-end OCPP chain responds to network and price events.

```
Cactus CSIP-AUS server ──SEP2/CSIP-AUS──► Open Dynamic Export ──MQTT──► Home Assistant (EEMS)
   ──REST──► CitrineOS (CSMS) ──OCPP 2.1 SetChargingProfile──► EVerest ──ISO 15118-20 DC_BPT──► EV
```

## What is on screen

| Panel | Source |
|---|---|
| CSIP-AUS controls (envelope and schedule) | Cactus run page, ODE `limits/csipAus` |
| Bridge decisions (profile sent, reason) | Home Assistant automation trace, `input_number.lab_v2g_discharge_sent` |
| OCPP 2.1 profile as received and accepted | EVerest V2G simulator status page, *Last received charging profile* |
| Power at the socket | EVerest live readings; CitrineOS MeterValues (5 s) |

## Running order (about 45 minutes)

| # | Min | Scenario | What the audience sees | Status |
|---|---:|---|---|---|
| 0 | 5 | **Stack tour** | Infographic; each hop named with its protocol; open source throughout | Ready |
| 1 | 5 | **Plug in and start** | RequestStartTransaction from the CSMS; ISO 15118-20 DC_BPT session; transaction appears in CitrineOS | Proven 17 Oct |
| 2 | 5 | **Bidirectional setpoints** | One OCPP 2.1 CentralSetpoint TxProfile: +20, −20, +6, −5, 0 kW; meter follows each step | Proven 17 Oct ([result](../results/2026-10-17-v2g-txprofile/README.md)) |
| 3 | 8 | **Import limit (network constraint)** | CSIP-AUS `opModImpLimW` steps (for example 30 → 12 → 7.5 → 0 kW); each arrives as profile periods ahead of time and takes effect at its start | Proven: Cactus LOA-11 16/16 on AC and DC V2G ([report](../cactus/LOA-11/README.md)) |
| 4 | 8 | **Export limit with V2G discharge** | Export mode on; discharge target clipped by the CSIP-AUS export limit (`opModExpLimW`/`opModGenLimW`) and released | Built; Cactus ALL-22 attempted 17 Oct, rerun pending |
| 5 | 6 | **Short-notice events (1 minute)** | A control with 60 s notice, modelling Minimum System Load (raise charging / soak) and Lack of Reserve (stop charging, discharge): the next profile carries it before it starts | Rehearse: schedule-ahead path proven in LOA-11 |
| 6 | 4 | **Local congestion** | Site load rises; the charger's limit falls so site import stays inside the envelope | Gap: the bridge does not yet subtract other site load (Cactus ALT-LOA-13) |
| 7 | 4 | **Price signal** | AEMO spot price moves the household plan; the plan reaches the charger through the same OCPP path | Rehearse |
| 8 | 5 | **Questions** | Evidence pages, timing against draft AS 5438 (≤5 s, ≤30 s, ≤15 s) | Ready |

## Fall-backs

- **No CSIP-AUS server on the day:** replay the recorded LOA-11 controls (`cactus/LOA-11/data/`) or
  drive the same limits from Home Assistant helpers, and say so.
- **Green unreachable on the venue network:** run on the laptop hotspot; or present the recorded
  evidence (charts, screenshots, raw JSON).
- **Station stops replying after a reconnect:** restart the V2G simulator App (until citrineos_server 0.6.3 is
  installed, see purcell-lab/ha-addons#67).
- **EV gave up waiting for authorisation:** unplug and plug in, then start within 60 s
  (until V2G simulator 0.1.10, see purcell-lab/ha-addons#33).

## Points to make

- Standard OCPP 2.1 smart charging carries the bidirectional setpoint (TxProfile, CentralSetpoint,
  `setpoint`/`limit`/`dischargeLimit` in W). **No dependency on the OCPP 2.1 DER control block.**
- The charging station validates and accepts every profile; the CSMS records the station's meter.
- Schedule-ahead: the next 600 s of CSIP-AUS controls go to the station as profile periods, so a
  network or market event takes effect on time even if the link drops.
- Everything shown is open source and reproducible from this repository and
  [purcell-lab/ha-addons](https://github.com/purcell-lab/ha-addons).
