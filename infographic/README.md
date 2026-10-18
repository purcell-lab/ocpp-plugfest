# One-page infographic

[**`plugfest-infographic.pdf`**](plugfest-infographic.pdf) (A3 portrait, prints on A4 at 71 %) ·
[`plugfest-infographic.png`](plugfest-infographic.png) · [`plugfest-infographic.svg`](plugfest-infographic.svg)

![OCPP Plugfest infographic](plugfest-infographic.png)

## Rebuild

`build.py` writes the infographic SVG and the README graphics in [`../assets/`](../assets/). The
V2G chart uses the recorded CSMS meter samples in
[`../results/2026-10-17-v2g-txprofile/data.json`](../results/2026-10-17-v2g-txprofile/data.json).
`render.js` renders the PNG and PDF with Playwright Chromium.

```bash
python3 infographic/build.py
NODE_PATH=$(npm root -g) node infographic/render.js
```

Brand colours: teal `#0f6e6e`, gold `#d2a55c`, cream `#fff6e5`, ink `#1b1b1b`. Chart polarity uses
green `#2e8540` (charging) and blue `#2a6fc9` (discharging), checked for colour-blind separation.
