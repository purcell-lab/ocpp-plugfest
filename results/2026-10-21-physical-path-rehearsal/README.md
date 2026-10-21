# Physical-charger path rehearsal (Green, 21 Oct 2026, AEDT)

Rehearsal of the Plugfest chain ODE -> HA bridge -> CitrineOS -> charger with
`command_real_stations_enabled: true`, using lab simulators in place of vendor
chargers. No Cactus run was active: ODE's import and export limits were 0 W
(house load 1 kW, solar about 0.1 kW).

## Charging-only station (OCPP 1.6, MicroOCPP `SIM-16-MICROOCPP-01`)

Setup: the simulator was rebound to the Plugfest listener `ws://172.30.32.1:8083`
(open admission); server `command_real_stations_enabled: true`,
`command_station_id: SIM-16-MICROOCPP-01`; integration reloaded. The device
appears as "CitrineOS lab SIM-16-MICROOCPP-01" (prefix
`citrineos_lab_sim_16_microocpp_01`, observed protocol `ocpp1.6`). Helpers:
prefix set, `lab_bridge_charge_only` on, `lab_bridge_rating` 7400 W.

| Time | Event |
|---|---|
| 19:13:09 | Start charging (RemoteStart); connector Preparing until the EV was plugged in through the simulator API |
| 19:13:38 | Transaction 1 open, Charging |
| 19:13:39 | Bridge TxProfile: id 9001, `chargingRateUnit: W`, charging-only `[{startPeriod: 0, limit: 0}]`, 600 s; power 0 W |
| ~19:14:57 | Manual `lab_schedule` 4200 W then 7000 W; measured 4192 W at the station and in HA |
| 19:15:00 | Bridge resend (60 s refresh) replaced profile 9001 with ODE's 0 W; power back to 0 W |
| 19:15:40 | Unplugged; transaction closed; test profile cleared |

Readings: `inverters/4` stayed at 0 W with rating 0 (charging-only station is a
load, not a DER); the EV's 4.2 kW import appeared in `lab/site` (net 5.1 kW).

## V2G station (OCPP 2.1, EVerest DC V2G `SIM-EV-EVEREST-V2G-03`)

Setup: `command_station_id: SIM-EV-EVEREST-V2G-03` with
`command_real_stations_enabled` still true (as for a StarCharge slot); prefix
`citrineos_everest_v2g_lab_sim_ev_everest_v2g_03`, `lab_bridge_charge_only`
off, `lab_bridge_rating` 0, `lab_v2g_export` on (target 25 kW).

| Time | Event |
|---|---|
| 19:18:17 | Transaction open (ISO 15118-20 DC_BPT) |
| 19:18:19 | Bridge export-mode CentralSetpoint profile; discharge 950 W (export ceiling 0 W + 95 % house load - 105 % solar) |
| 19:18:25 | Measured -950 W; `inverters/4` realPower 950 W, maxW 25000; `lab/site` net 16 W |
| 19:20:47 | After the reset restart of CitrineOS the simulator reconnected on 8083 with the session intact; 19:20:50 profile Accepted |

## Findings

- The integration must be reloaded after CitrineOS is ready; a reload during
  startup leaves the station's entities unavailable (502 on /health/ready) until
  a second reload.
- Changing a MicroOCPP App's backend needs `archive_and_rebind` (state is
  archived under `/data/archive-<UTC>`, not deleted).
- A charging-only station connected to Preparing waits for the EV: on a vendor
  charger the vendor plugs in; RemoteStart alone does not open the transaction.

## Reset

Server `command_real_stations_enabled: false`, station `SIM-EV-EVEREST-V2G-03`;
MicroOCPP rebound to `ws://172.30.32.1:19002` (HA native OCPP); prefix empty,
`lab_bridge_charge_only` off, `lab_bridge_rating` 0.
