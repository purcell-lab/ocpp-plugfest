# CSIP-AUS Cactus test records

Test reports from the [Cactus](https://cactus.cecs.anu.edu.au/) CSIP-AUS test
harness for the lab chain: Open Dynamic Export (CSIP-AUS client), a Home
Assistant bridge, CitrineOS and the EVerest test chargers. Design notes are in
purcell-lab/ha-addons#55.

| Procedure | Date | Result | Report |
|---|---|---|---|
| LOA-11 | 17 Oct 2026 | Run 74853: 15/16 (finalised before DERC5 ended). Run 74858: 16/16. Run 74865 (DC V2G charger): 16/16. | [LOA-11](LOA-11/README.md) |
| GEN-10 (primacy, generators) | 20 Oct 2026 | Run 75349 stopped after step 1: ODE took an empty default (fixed in ODE App 0.1.4). Run 75351: **46/46**, one warning (DER readings above setMaxW, fixed) | [GEN-10 run 75351](../results/2026-10-20-cactus-gen10/README.md) |
| GEN-11 (variable export limit) | 20 Oct 2026 | Run 75354: **16/16 checks, no warnings** | [GEN-11 run 75354](../results/2026-10-20-cactus-gen11/README.md) |
| ALL-28 (response to changing ramp rates) | 20 Oct 2026 | Run 75360: **15/15 steps, no warnings** | [ALL-28 run 75360](../results/2026-10-20-cactus-all28/README.md) |
| ALL-23 (communication loss) | 20 Oct 2026 | Run 75362 failed (ODE polled 300 s after errors); fixed in ODE App 0.1.5; run 75381: **5/5 steps, no warnings** | [ALL-23 runs 75362 and 75381](../results/2026-10-20-cactus-all23/README.md) |
| ALL-22 (export limits, V2G) | this week | Run 74893 started with the V2G export mapping, aborted before completion; rerun pending | — |
| ALT-ALL-29 (V2G export, readings) | this week | Run 74896 not passed: DER readings incomplete because ODE skipped two DER reading posts; under investigation | — |
| ALT-LOA-13 (load limit) | this week | Run 74902: site import exceeded the load limit because the bridge does not yet subtract other site load; fix pending | — |

Reports for the runs above are written up once the fixes are in and the reruns pass.
