# Signal bot POC: signal-cli-rest-api as a linked device

This runs [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) with **signal-cli 0.14.9** and links it to an existing Signal account as a _secondary (linked) device_, the same way Signal Desktop is linked.

You don't need a phone number or SMS. The primary device (your Android phone, already logged in) approves the link by scanning a QR code. Your Signal recovery key is **not** needed for linking. Keep it safe and never put it into this container.

## 1. Start

```bash
docker compose up -d
```

Image: `bbernhard/signal-cli-rest-api:1792271041-ci`. The `latest` tag (0.101) still ships signal-cli 0.14.8. This CI build from master ships 0.14.9. Once a release tag with 0.14.9 is out, you can switch to it.

## 2. Check health and version

```bash
curl -i http://127.0.0.1:8080/v1/health            # HTTP 204 = healthy
curl -s http://127.0.0.1:8080/v1/about             # API info (version shows "unset" on CI builds)
docker compose exec signal-api signal-cli --version   # -> signal-cli 0.14.9
docker compose ps                                  # STATUS should show (healthy)
```

## 3. Link the device (QR code)

1. On Android, open **Signal → Settings → Linked devices → Link new device (+)**.
2. On the computer, run:
   ```bash
   ./link.sh            # optional: ./link.sh my-device-name
   ```
   This saves `qr.png` and opens it.
3. Scan the QR code **right away**. It expires after about a minute. If it expires, run `./link.sh` again.
4. Approve on the phone. You can choose whether to transfer message history.

Each run starts a new link session, so always scan the newest QR code.

**Phoneless accounts: "The device you are trying to link needs an update".** Signal Android 8.30+ requires the `nopni2` capability for accounts without a phone number. signal-cli 0.14.9 only advertises `nopni` ([signal-cli#2140](https://github.com/AsamK/signal-cli/issues/2140); it's fixed on master but not released yet). `link.sh` therefore gets the raw URI from `/v1/qrcodelink/raw`, rewrites it to `capabilities=nopni,nopni2`, and renders the QR code locally with `qrencode` (`brew install qrencode`). The API's own `/v1/qrcodelink` PNG does **not** work for phoneless accounts.

**Why `qrcode_version=15`** (only needed if you use the API's PNG): signal-cli 0.14.x link URIs are longer than before (`sgnl://linkdevice?uuid=…&pub_key=…&capabilities=…`). They don't fit the API's default QR size (version 10), so the plain `/v1/qrcodelink` call fails with `content too large for fixed size QR Code version 10`.

Manual alternatives:

```bash
# Open in a browser (the PNG is shown directly):
open "http://127.0.0.1:8080/v1/qrcodelink?device_name=signal-bot&qrcode_version=15"

# Raw link URI (render it with any QR tool, e.g. `brew install qrencode`):
curl -s "http://127.0.0.1:8080/v1/qrcodelink/raw?device_name=signal-bot"
qrencode -t ansiutf8 'sgnl://linkdevice?...'
```

## 4. Check login status

```bash
curl -s http://127.0.0.1:8080/v1/accounts
```

- `[]` means not linked yet.
- `["+15551234567"]` means it's linked, with that number as the account ID.
- `[""]` means a **phoneless** account is linked. It has no number, so use its account UUID wherever the API asks for a number. Get the UUID with:
  ```bash
  python3 -c "import json;print(json.load(open('signal-cli-data/data/accounts.json'))['accounts'][0]['uuid'])"
  ```

More checks once linked (replace the number or UUID):

```bash
NUM='+15551234567'   # or the account UUID for a phoneless account
curl -s "http://127.0.0.1:8080/v1/devices/$NUM"                 # list linked devices
curl -s "http://127.0.0.1:8080/v1/receive/$NUM"                 # pull new messages (also syncs)
curl -s -X POST http://127.0.0.1:8080/v2/send -H 'Content-Type: application/json' \
  -d "{\"message\":\"hello from the bot\",\"number\":\"$NUM\",\"recipients\":[\"$NUM\"]}"   # Note to Self
```

On the phone, the device also shows up under **Settings → Linked devices**.

## API documentation (Swagger)

The container serves its own Swagger (OpenAPI) docs, so they always match the running version.

| What                                                  | URL                                      |
| ----------------------------------------------------- | ---------------------------------------- |
| Swagger UI (interactive, try requests in the browser) | http://127.0.0.1:8080/swagger/index.html |
| OpenAPI spec, JSON                                    | http://127.0.0.1:8080/swagger/doc.json   |

How to open:

```bash
open http://127.0.0.1:8080/swagger/index.html      # macOS, opens the browser
curl -s http://127.0.0.1:8080/swagger/doc.json | python3 -m json.tool | less   # raw spec in the terminal
```

Notes:

- The service serves the spec only as JSON. `doc.yaml`, `doc.yml` and `swagger.yaml` return 404. If you need YAML, convert the JSON locally (for example, with `yq -P` or a Python YAML library).
- Docs are only available while the container is running. Start it with `docker compose up -d`.
- The Swagger UI only runs on localhost, the same as the API.

## Notes

- Account keys are stored in `./signal-cli-data/`. Back it up and keep it private: anyone with it can read and send as you. Delete it, and unlink the device on the phone, to log out.
- A linked device that stays offline for a long time (about 30 days) is unlinked by Signal. Call `receive` regularly.
- The API listens only on `127.0.0.1:8080`, so it isn't reachable from the network.
- For a real bot, set `SIGNAL_API_MODE=json-rpc` in `.env`. That mode receives messages over the websocket `ws://127.0.0.1:8080/v1/receive/<number>`. Restart the container after changing the mode.
