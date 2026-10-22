# Handover: a public `wss://` endpoint for a cloud-hosted test tool (Cloudflare Tunnel)

**What it's for.** A Plugfest test tool that runs in the vendor's cloud, such as DNV's OCTT, can't reach
the Green's plain `ws://` listener on the venue LAN. A Cloudflare Tunnel gives it a public, TLS-terminated
endpoint, `wss://ocpp.<your-domain>/<station-id>`, with no inbound port or public IP at the venue.
Background: [ha-addons#93](https://github.com/purcell-lab/ha-addons/issues/93) (DNV connection) and
[ha-addons#92](https://github.com/purcell-lab/ha-addons/issues/92) (native TLS listeners).

**Status.** Used for the DNV session on 22 October 2026. The steps below include the corrections found
during that setup. The as-built record is in
[ha-addons#93](https://github.com/purcell-lab/ha-addons/issues/93#issuecomment-6331306260).

```
OCTT (cloud) --wss:443--> Cloudflare edge --tunnel (outbound from the Green)--> cloudflared App
            --http/ws--> 31ac84d3-citrineos-server:8083 (Plugfest listener)
```

**What it gives and what it doesn't**

| | |
|---|---|
| Security Profile 2 (TLS + Basic Auth) | **Yes.** Cloudflare terminates TLS with a publicly trusted certificate (Universal SSL serves ECDSA, with RSA for clients that offer only RSA). The `Authorization` and `Sec-WebSocket-Protocol` headers pass through to CitrineOS. |
| Security Profile 3 (mutual TLS) | **No.** The station's client certificate stops at Cloudflare and never reaches CitrineOS. SP3 needs the native listeners in #92. |
| Security Profile 1 (plain `ws://`) over the internet | Don't. Basic Auth credentials would cross the internet in clear text. |

## 1. Cloudflare (dashboard, done by the account owner)

The domain is already on Cloudflare.

1. **Create the tunnel:** Zero Trust → Networks → Tunnels → *Create a tunnel* → type **Cloudflared**,
   for example the name `plugfest-green`. Copy the **tunnel token** (the long `eyJ…` string). Treat it as a
   secret: anyone holding it can run the tunnel. Don't paste it into issues, commits or chat.
   - The same setup can be done through the Cloudflare API with a scoped token (Account: Cloudflare
     Tunnel Edit; Zone: DNS Edit, Zone Settings Edit, Zone WAF Edit). Create the tunnel with
     `config_src: cloudflare`, put the ingress (this hostname, then a catch-all `http_status:404`) in its
     configuration, and add a proxied `CNAME` from `ocpp` to `<tunnel-id>.cfargotunnel.com`. Revoke the
     API token after teardown.
2. **Public hostname** on the tunnel:
   - Subdomain `ocpp` (or similar), on your domain.
   - Service type **HTTP**, URL **`31ac84d3-citrineos-server:8083`**. If that name doesn't resolve from
     the App, use `192.168.88.252:8083`, the Green's venue LAN address.
   - Add no other hostnames. In particular, don't publish Home Assistant (8123), the gateway (8080),
     Hasura or the Operator UI.
3. **Zone settings that affect a non-browser websocket client:**
   - **Network → WebSockets: On** (the default).
   - **SSL/TLS → Edge Certificates → Minimum TLS version: 1.2.** OCPP requires TLS 1.2 or later.
   - **Security:** a bot or WAF challenge would block OCTT, which can't answer a JavaScript challenge.
     - **Bot Fight Mode** (free plan) can't be bypassed by a WAF Skip rule. It must be **off for the
       whole zone** (Security → Settings).
     - For everything else, add a WAF custom rule with action **Skip** for
       `http.host eq "ocpp.<your-domain>"`. Skip the remaining custom rules, the managed rules and rate
       limiting phases, and the Browser Integrity Check, Security Level and User Agent Blocking products.
       Browser Integrity Check is on by default and can refuse non-browser clients.
   - **Cloudflare Access:** don't put an Access application on this hostname. OCTT can't complete a login.
4. **Optional:** restrict the hostname to DNV's egress IPs with a WAF rule, if DNV can supply them.

## 2. Home Assistant Green (the lab)

1. **Install the Cloudflared App** from the community repository
   `https://github.com/brenner-tobias/ha-addons` (Settings → Apps → App store → ⋮ → Repositories).
   `.../addon-cloudflared` is not an App repository and fails to add. On the Green the App slug is
   `9074a9fa_cloudflared` (version 7.0.18 on 22 October).
   This is a new App during the event-week freeze, so install it only with the lab owner's go-ahead.
2. **App options:**
   - `tunnel_token`: the token from step 1.1. With a token, the App runs a dashboard-managed tunnel, so
     routes come only from the public hostname set in Cloudflare.
   - Don't set `external_hostname` or `additional_hosts`. Leave HA itself unpublished.
   - Set **Start on boot** to manual, so the tunnel doesn't come back by itself after a reboot.
3. **Start the App.** Its log should show the tunnel registering four connections to Cloudflare. The
   dashboard should show the tunnel as **Healthy**. If the venue blocks part of the QUIC traffic
   (UDP 7844), the precheck reports "degraded transport" and the tunnel uses HTTP/2. That is fine.

## 3. CitrineOS server App (before the tunnel goes live)

1. **`plugfest_open_admission: false`.** With open admission on, anyone on the internet could register
   any station ID. This is required.
2. **`plugfest_stations`:** add one entry for the test tool's station ID. The ID must match
   `^[A-Za-z0-9._~*+-]{1,48}$`, so no `/`. Give it its own password, 16 to 40 printable characters
   (`python3 -c "import secrets;print(secrets.token_urlsafe(24))"`). Keep the existing entries.
   - Any vendor station still being tested on the LAN, such as an EVX `TEST5`, also needs an entry,
     because open admission is off. The vendor must then enter that password on the charger.
   - Open admission covers all Plugfest listeners (8083 and 8100 to 8105) together, not only the
     tunnelled one.
   - **Lab simulators without a Basic Auth option are refused** once open admission is off. The AC
     simulator (`SIM-EV-EVEREST-G1`) is one: CitrineOS logs `Has no password`. Stop it for the session
     and set it to manual boot. Moving it to the internal open listener (8082) trips its safety guard
     ("test destination changed"), which needs an archive and rebind of its data first. The V2G
     simulator has a password option and stays connected.
3. **Restart the CitrineOS server App,** then follow "After any CitrineOS restart" in the [runbook](RUNBOOK.md):
   - wait for the stations to reconnect;
   - reload the CitrineOS-HA integration;
   - run `citrine_ha.lab_reconcile` if the command dispatch status is `outcome_unknown`.

## 4. Give the test tool

| | |
|---|---|
| CSMS URL | `wss://ocpp.<your-domain>/` with the station ID appended (`wss://ocpp.<your-domain>/<station-id>`), port 443 |
| Security Profile | 2 (TLS with Basic Auth) |
| Basic Auth | user = the station ID, password = the one set in step 3.2. Send the password over a private channel, not in an issue or email thread with others. |
| OCPP | 2.1, 2.0.1 or 1.6J (`Sec-WebSocket-Protocol` `ocpp2.1`, `ocpp2.0.1` or `ocpp1.6`) |
| Server certificate | Publicly trusted (Cloudflare). No CA needs to be installed in OCTT. |

## 5. Verify from outside the venue

1. **TLS and the tunnel:** `curl.exe -I https://ocpp.<your-domain>/`. Expect an HTTP response from
   CitrineOS, a `404 Route … not found`, not a Cloudflare error page (`502`/`1033` means the tunnel or
   service URL is wrong).
2. **Handshake** (Windows: `curl.exe` on one line, not PowerShell's `curl`):
   ```
   curl.exe -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" -H "Sec-WebSocket-Protocol: ocpp2.0.1" -u "<station-id>:<password>" https://ocpp.<your-domain>/<station-id>
   ```
   - `101 Switching Protocols`: the tunnel and the auth both work. Press Ctrl-C at once.
   - **`502` (not `401`) without `-u` or with a wrong password:** the auth is enforced. CitrineOS closes
     the socket on a refused upgrade, and `cloudflared` reports that as a bad gateway. Confirm in the
     CitrineOS log (step 3) that it was an auth refusal and not a tunnel fault.
   - `404` or `502` for a station ID that isn't provisioned: refused by `UnknownStationFilter`.
   - To test refusals without touching the real identity, use a wrong password on the real ID or any
     unprovisioned ID. A refused upgrade doesn't hold the identity.
   - **Don't run this under the tool's real station ID while the tool is connecting.** A test socket holds
     the identity, and CitrineOS refuses the real station ("already connected identifier").
3. **On the Green:** the CitrineOS log shows `NetworkProfileFilter` for each accepted upgrade. Refused
   upgrades show as `BasicAuthenticationFilter Filter failed` (wrong or missing password),
   `UnknownStationFilter Filter failed` (unprovisioned ID) or `ConnectedStationFilter Filter failed`
   (identity already connected). The `ChargingStations` table shows the station
   online, with vendor and model filled in after its BootNotification.

## 6. Tear down after the session

1. Stop the Cloudflared App (or uninstall it). The hostname then returns a Cloudflare error.
2. Delete the tunnel, the `ocpp` DNS record and the WAF Skip rule. Rotate the tunnel token if it was
   shared, and revoke any API token used for the setup.
3. Set `plugfest_open_admission` back to what the remaining LAN slots need, remove the test tool's
   `plugfest_stations` entry if it's no longer needed, and restart CitrineOS (then the runbook steps).
4. Restart any simulator stopped in step 3, and set its boot back to automatic if wanted.

## Known limits

- **Cloudflare free plan:** websockets are supported. A connection may be dropped when Cloudflare
  restarts edge servers; OCPP stations reconnect, so this is harmless for a test.
- **CitrineOS doesn't log client IPs**, so with the tunnel every connection comes from `cloudflared`
  anyway. Use the Cloudflare dashboard's analytics or logs to see the tool's source address.
- **SP3 and certificate-management test cases** (`InstallCertificate`, `SignCertificate`, mTLS) can't run
  through the tunnel. See #92.
