# Working with signal-cli-rest-api

How megabot talks to Signal: linking the bot, finding out who it is, joining groups, receiving
and storing messages, and sending replies.

Checked against the running `signal-api` container (`bbernhard/signal-cli-rest-api:1792271041-ci`,
signal-cli **0.14.9**) and the upstream source on `master`. Anything not checked against a live
account is marked _(unverified)_.

- [1. What it is](#1-what-it-is)
- [2. Mental model: the bot is a linked device](#2-mental-model-the-bot-is-a-linked-device)
- [3. Modes: native vs json-rpc](#3-modes-native-vs-json-rpc)
- [4. Link a device](#4-link-a-device)
- [5. Account and device status](#5-account-and-device-status)
- [6. Groups: list, inspect, invitations, join](#6-groups-list-inspect-invitations-join)
- [7. Receiving messages](#7-receiving-messages)
- [8. Message structure](#8-message-structure)
- [9. Processing and storing messages](#9-processing-and-storing-messages)
- [10. Sending messages](#10-sending-messages)
- [11. Endpoint reference](#11-endpoint-reference)
- [12. Gotchas](#12-gotchas)

---

## 1. What it is

[signal-cli](https://github.com/AsamK/signal-cli) is an unofficial command-line Signal client
written in Java. [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) wraps it
in a small Go HTTP server, so you can drive Signal with plain HTTP and JSON instead of shelling
out to a CLI.

In this repo it runs as the `signal-api` Compose service ([docker-compose.yml](../docker-compose.yml)):

| Setting        | Value                                                              |
| -------------- | ------------------------------------------------------------------ |
| Base URL       | `http://127.0.0.1:8080` from the host, `http://signal-api:8080` from `app` |
| Auth           | **None.** It's bound to loopback, so never publish it.             |
| State          | `signal-cli-data` volume → `/home/.local/share/signal-cli`         |
| Mode           | `SIGNAL_API_MODE` (default `native`), passed through as `MODE`     |
| Interactive docs | <http://127.0.0.1:8080/swagger/index.html>                        |

```bash
curl -i  http://127.0.0.1:8080/v1/health   # 204 = healthy
curl -s  http://127.0.0.1:8080/v1/about    # {"versions":["v1","v2"],"mode":"native",...}
docker compose exec signal-api signal-cli --version   # signal-cli 0.14.9
```

## 2. Mental model: the bot is a linked device

The bot does **not** have its own Signal identity. It's linked to an existing account as a
secondary device, the same way Signal Desktop is. So:

- Messages the bot sends show up as sent **by that account**, on every device, the phone included.
- Messages sent from the phone reach the bot as **sync messages** (`syncMessage.sentMessage`),
  not as normal incoming messages.
- Whatever the account can see, the bot can see: every 1:1 chat and every group.
- The phone (primary device) stays in charge. It can unlink the bot at any time, and Signal
  unlinks a device that stays offline for about 30 days.

**Account identifier.** Every `{number}` path parameter and every `"number"` body field takes the
account's **E.164 phone number or ACI UUID**. Our account is **phoneless**, so always use its
UUID (see [§5](#5-account-and-device-status)).

## 3. Modes: native vs json-rpc

The `MODE` variable decides how the REST layer drives signal-cli.

| Mode              | How it runs signal-cli                      | Receiving                                | Speed / memory               |
| ----------------- | ------------------------------------------- | ---------------------------------------- | ---------------------------- |
| `normal`          | New JVM process per request                 | `GET /v1/receive/{n}` (poll)             | Slow (JVM start) / low       |
| `native` (ours)   | New GraalVM native binary process per request | `GET /v1/receive/{n}` (poll)           | Fast start / low             |
| `json-rpc`        | One long-running JVM daemon                 | **WebSocket** `/v1/receive/{n}` or webhook | Fastest / higher memory    |
| `json-rpc-native` | One long-running native daemon              | Same as `json-rpc`                       | Fast / low                   |

In practice:

- **native** is simplest for scripting and a POC. Each request is a separate process, so there's
  nothing to keep connected. The downside: messages only arrive when *you* call `receive`.
- **json-rpc** suits a real bot. signal-cli keeps a live connection to Signal and pushes each
  message to you as it arrives. `GET /v1/receive` stops being a plain GET (it returns 400) and
  becomes a WebSocket endpoint.
- Both modes use the same send, groups, and devices endpoints with the same payloads. Only
  receiving differs.

To switch, set `SIGNAL_API_MODE=json-rpc` in `.env` and run `docker compose up -d signal-api`.

Extra container variables that matter in json-rpc mode (not wired into our Compose file yet):

| Variable                    | Meaning                                                                                 |
| --------------------------- | --------------------------------------------------------------------------------------- |
| `JSON_RPC_RECEIVE_MODE`     | `on-start` (default): signal-cli pulls messages all the time, and **drops** any that arrive while no WebSocket client is connected. `manual`: pulls only while a client is connected, otherwise messages wait on Signal's servers. **Use `manual` for a bot that can restart.** |
| `RECEIVE_WEBHOOK_URL`       | POST every incoming message to this URL (json-rpc mode only). No retries: anything other than a 200/201 response is logged and lost. |
| `JSON_RPC_IGNORE_ATTACHMENTS` / `_STORIES` / `_AVATARS` / `_STICKERS` | Skip the automatic downloads. |
| `JSON_RPC_TRUST_NEW_IDENTITIES` | `on-first-use` (default), `always`, or `never`.                                      |
| `AUTO_RECEIVE_SCHEDULE`     | **normal/native only.** A cron expression that runs `receive` periodically so the device stays alive. It consumes messages, so don't combine it with your own polling. |

## 4. Link a device

Linking makes the container a secondary device of an existing account. No phone number or SMS
is needed, and **never** put the recovery key into the container.

### The normal flow

```bash
./signal-api-link-device.sh            # or: ./signal-api-link-device.sh my-device-name
```

1. On the phone, open **Signal → Settings → Linked devices → Link new device (+)**.
2. Run the script. It saves `signal-api-qrcode.png` and opens it.
3. Scan the QR code **within about a minute**. Each run starts a new link session, so always scan
   the newest code.
4. Approve on the phone. Message history transfer is optional.
5. Confirm: `curl -s http://127.0.0.1:8080/v1/accounts` should now return something other than `[]`.

What happens underneath:

```bash
# 1. Start a link session and get the provisioning URI (blocks until scanned or expired)
curl -s "http://127.0.0.1:8080/v1/qrcodelink/raw?device_name=signal-bot-poc"
# {"device_link_uri":"sgnl://linkdevice?uuid=...&pub_key=...&capabilities=nopni"}

# 2. Render it as a QR code
qrencode -o qr.png -s 10 -m 4 'sgnl://linkdevice?...'
```

There's also `GET /v1/qrcodelink?device_name=…&qrcode_version=15`, which returns a PNG directly.
signal-cli 0.14.x URIs are too long for the default QR version 10 (`content too large for fixed
size QR Code version 10`), so you need `qrcode_version=15`. This endpoint doesn't work for
phoneless accounts either (see the next section).

### The `nopni2` issue (phoneless accounts)

**Symptom:** the phone says _"The device you are trying to link needs an update"_.

**Cause:** Signal Android 8.30+ only links a device to an account **without a phone number** if
the link URI advertises the `nopni2` capability. signal-cli 0.14.9 only advertises `nopni`
([signal-cli#2140](https://github.com/AsamK/signal-cli/issues/2140)). This is fixed on signal-cli
master (`32f652e`) but not in a release yet.

**Workaround** (what `signal-api-link-device.sh` does): take the raw URI from
`/v1/qrcodelink/raw`, rewrite it to `capabilities=nopni,nopni2`, and render the QR code locally
with `qrencode` (`brew install qrencode`). Remove the patch once the image ships a signal-cli
release that includes the fix.

### Unlinking

Unlink from the phone (**Settings → Linked devices**), then wipe the local keys:

```bash
docker compose down && docker volume rm megabot_signal-cli-data
```

`DELETE /v1/devices/{number}/local-data` also deletes local account data through the API.
Don't confuse it with `POST /v1/devices/{number}`, which links *another* device **to** this
account (the opposite direction) and isn't needed here.

## 5. Account and device status

### Is a device linked?

```bash
curl -s http://127.0.0.1:8080/v1/accounts
```

| Response            | Meaning                                                     |
| ------------------- | ----------------------------------------------------------- |
| `[]`                | Nothing linked yet                                          |
| `["+15551234567"]`  | Linked. The phone number is the account ID                  |
| `[""]`              | Linked, **phoneless** account. Use the ACI UUID instead     |

### Get the account UUID, number, and other IDs

The API doesn't expose the ACI of a phoneless account, but signal-cli's account index does:

```bash
docker compose exec signal-api cat /home/.local/share/signal-cli/data/accounts.json
# {"accounts":[{"path":"684078","environment":"LIVE","number":null,
#               "uuid":"f0c7fc1e-0000-4000-8000-000000000000"}],"version":2}

ACCOUNT=$(docker compose exec -T signal-api cat /home/.local/share/signal-cli/data/accounts.json \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["accounts"][0]["uuid"])')
```

| Field         | What it is                                                                     |
| ------------- | ------------------------------------------------------------------------------ |
| `uuid`        | **ACI**: the account's stable Signal identity. Use it as `{number}` everywhere |
| `number`      | E.164 phone number, or `null` for a phoneless account                          |
| `path`        | signal-cli's internal data directory under `data/`. Ignore it                  |
| `environment` | `LIVE` (production Signal) or `STAGING`                                        |

Store `ACCOUNT` in settings (for example `APP_SIGNAL_ACCOUNT`), not in code.

### Is the link still alive? Which devices exist?

```bash
curl -s "http://127.0.0.1:8080/v1/devices/$ACCOUNT"
```

```json
[
  { "id": 1, "name": "",               "creation_timestamp": 1792312253795, "last_seen_timestamp": 1792800000000 },
  { "id": 3, "name": "signal-bot-poc", "creation_timestamp": 1792855225145, "last_seen_timestamp": 1792886400000 }
]
```

- `id: 1` is always the primary device (the phone). The entry with your `device_name` is the bot.
- Timestamps are Unix milliseconds. Signal rounds `last_seen` to the day.
- A **successful** response means the device is still linked. Once the phone unlinks it, calls
  that hit Signal's servers (devices, send, receive) fail with an authorization error, even
  though `/v1/accounts` still lists the account locally _(unverified: the exact error text)_.

Other useful identity calls:

```bash
curl -s "http://127.0.0.1:8080/v1/about"                              # API version, mode, capabilities
curl -s "http://127.0.0.1:8080/v1/configuration/$ACCOUNT/settings"    # {"trust_mode":"on-first-use"}
curl -s "http://127.0.0.1:8080/v1/contacts/$ACCOUNT"                  # contacts: uuid, number, profile_name, username
curl -s "http://127.0.0.1:8080/v1/identities/$ACCOUNT"                # safety numbers / trust state
```

## 6. Groups: list, inspect, invitations, join

### Two group ID formats

This trips everyone up. A group has **two** IDs:

| Name                  | Example                                   | Where you see it                                   |
| --------------------- | ----------------------------------------- | -------------------------------------------------- |
| `internal_id`         | `X5Oxu7cq4G7s…GalSI=`                     | signal-cli's ID. Received messages carry this as `groupInfo.groupId` |
| `id` (REST group ID)  | `group.WDVPeHU3Y3E0…YWxTST0=`             | Every REST endpoint: `/v1/groups/{n}/{groupid}`, send `recipients` |

The conversion is mechanical: **`id = "group." + base64(internal_id)`**. The internal ID is
already base64, so it gets base64-encoded a second time:

```python
import base64


def to_rest_group_id(internal_id: str) -> str:
    return "group." + base64.b64encode(internal_id.encode()).decode()


def to_internal_group_id(rest_id: str) -> str:
    return base64.b64decode(rest_id.removeprefix("group.")).decode()
```

### List the groups the account is in

```bash
curl -s "http://127.0.0.1:8080/v1/groups/$ACCOUNT"
```

```json
[
  {
    "name": "Megabot",
    "description": "",
    "id": "group.WDVPeHU3Y3E0RzdzT2NpYlVMWi9XQTF0TVRLS2lxdkxhRXBzWE9HYWxTST0=",
    "internal_id": "X5Oxu7cq4G7sOcibULZ/WA1tMTKKiqvLaEpsXOGalSI=",
    "members": ["74f5673c-…", "f0c7fc1e-…"],
    "admins": ["f0c7fc1e-…"],
    "pending_invites": [],
    "pending_requests": [],
    "member": true,
    "blocked": false,
    "invite_link": "",
    "permissions": { "add_members": "every-member", "edit_group": "every-member", "send_messages": "every-member" }
  }
]
```

| Field              | Meaning                                                                       |
| ------------------ | ----------------------------------------------------------------------------- |
| `member`           | `true` if the account is a full member. `false` for invited or left groups    |
| `members`, `admins` | Phone number if known, otherwise the ACI UUID                                |
| `pending_invites`  | Invited but not yet accepted                                                  |
| `pending_requests` | Asked to join through a link; waiting for admin approval                      |
| `invite_link`      | `https://signal.group/#…` when the group link is enabled                      |

Single group: `GET /v1/groups/{number}/{groupid}`. Avatar: `GET …/{groupid}/avatar`.

### How the bot gets into a group

Because the bot *is* the account (§2), "inviting the bot" means adding **the account** to a group.

| Situation                                        | What happens                                                     | What to do |
| ------------------------------------------------ | ---------------------------------------------------------------- | ---------- |
| The account is already in the group (on the phone) | Group state syncs to the linked device                          | Nothing. It appears in `GET /v1/groups` |
| Someone who has the account as a contact adds it | Added as a full member right away                                | Nothing |
| Someone who isn't a contact adds it              | Signal creates an **invitation** (message request)               | Accept on the phone, **or** `POST …/join` (below) |
| You have a `https://signal.group/#…` invite link | Join request (approval may be needed)                            | Open the link on the phone. The REST API has no "join by link" endpoint |
| The bot should own a new group                   | Create it through the API                                        | `POST /v1/groups/{number}` |

### Check for pending invitations

There's no dedicated "invitations" endpoint. An invitation is a group where the account isn't a
member yet but is listed in `pending_invites` _(unverified against a real invite)_:

```bash
curl -s "http://127.0.0.1:8080/v1/groups/$ACCOUNT" | python3 -c '
import sys, json
me = sys.argv[1]
for g in json.load(sys.stdin):
    if not g["member"] and me in g["pending_invites"]:
        print(g["id"], g["name"])' "$ACCOUNT"
```

When the invite arrives, the receive stream also carries an envelope with
`dataMessage.groupInfo.type == "UPDATE"`, which you can use as a trigger to re-check the list.

### Accept an invitation

```bash
curl -s -X POST "http://127.0.0.1:8080/v1/groups/$ACCOUNT/group.WDVP…ST0=/join"   # 204 on success
```

Underneath this runs signal-cli `updateGroup -g <id>`, which accepts a pending invitation. To
decline or leave, use `POST …/{groupid}/quit`. To stop receiving a group's messages, use
`POST …/{groupid}/block`.

**Joining by invite link without the phone** is only possible with signal-cli directly, in
native mode (in json-rpc mode the daemon holds the account lock):

```bash
docker compose exec -u signal-api signal-api \
  signal-cli --config /home/.local/share/signal-cli -a "$ACCOUNT" joinGroup --uri 'https://signal.group/#…'
```

### Create and manage groups

```bash
# Create a group. Response: {"id":"group.…"}
curl -s -X POST "http://127.0.0.1:8080/v1/groups/$ACCOUNT" -H 'Content-Type: application/json' -d '{
  "name": "Megabot test",
  "members": ["74f5673c-1c12-4543-a441-b1429093642d"],
  "group_link": "enabled-with-approval",
  "permissions": {"add_members": "only-admins", "edit_group": "only-admins", "send_messages": "every-member"}
}'

# Add or remove members / admins
curl -s -X POST   "http://127.0.0.1:8080/v1/groups/$ACCOUNT/$GROUP/members" -d '{"members":["<uuid>"]}'
curl -s -X DELETE "http://127.0.0.1:8080/v1/groups/$ACCOUNT/$GROUP/members" -d '{"members":["<uuid>"]}'
curl -s -X POST   "http://127.0.0.1:8080/v1/groups/$ACCOUNT/$GROUP/admins"  -d '{"admins":["<uuid>"]}'

# Rename / describe / avatar / link
curl -s -X PUT "http://127.0.0.1:8080/v1/groups/$ACCOUNT/$GROUP" -d '{"name":"New name","description":"…"}'
```

## 7. Receiving messages

Signal holds incoming messages in a per-account queue on its servers. **Receiving takes them out
of that queue**, so there must be exactly one consumer per account. If you poll and also run
`AUTO_RECEIVE_SCHEDULE` or a second script, messages get split between them and some are lost.

Receiving also keeps the linked device alive and syncs contacts and groups, so a bot that's
idle should still receive regularly.

### Native mode: poll over HTTP

```bash
curl -s "http://127.0.0.1:8080/v1/receive/$ACCOUNT?timeout=5"
```

| Query param          | Default   | Meaning                                                 |
| -------------------- | --------- | ------------------------------------------------------- |
| `timeout`            | `1`       | Seconds to wait for new messages                        |
| `max_messages`       | unlimited | Cap per call                                            |
| `ignore_attachments` | `false`   | Don't download attachment files                         |
| `ignore_stories`     | `false`   | Skip stories                                            |
| `ignore_avatars`, `ignore_stickers` | `false` | Skip those downloads                        |
| `send_read_receipts` | `false`   | Automatically mark received messages as read            |

The response is a **JSON array** of items, each `{"envelope": {...}, "account": "..."}`, or `[]`.
Run it in a loop (for example, every 2–5 seconds). Each call starts a signal-cli process, so
messages arrive with up to a few seconds' delay.

### json-rpc mode: WebSocket

Same path, but as a WebSocket. A plain GET answers 400.

```bash
websocat "ws://127.0.0.1:8080/v1/receive/$ACCOUNT"
```

- Each **text frame is one message**, `{"envelope": {...}, "account": "..."}`. It's the same
  object as one array item in native mode, so a single parser handles both.
- If signal-cli reports a failure, the frame is `{"error": "..."}`.
- The server pings every ~54 s. Most clients answer pings automatically.
- The server only forwards frames whose `account` equals the `{number}` in the URL. For a
  phoneless account, check that the frames really arrive when you use the UUID as `{number}`
  _(unverified)_.
- Use `JSON_RPC_RECEIVE_MODE=manual` so messages wait on Signal's servers while your consumer is
  disconnected, instead of being dropped.

Minimal Python consumer (`uv add websockets`):

```python
import asyncio, json
import websockets


async def consume(account: str) -> None:
    url = f"ws://signal-api:8080/v1/receive/{account}"
    async for ws in websockets.connect(url):  # reconnects automatically
        try:
            async for frame in ws:
                item = json.loads(frame)
                if "error" in item:
                    logger.warning("signal error: %s", item["error"])
                    continue
                await handle(item["envelope"])
        except websockets.ConnectionClosed:
            continue
```

### json-rpc mode: webhook

Set `RECEIVE_WEBHOOK_URL=http://app:8000/signal/webhook` on the `signal-api` service, and
signal-cli-rest-api POSTs every incoming message there. The body is the **raw JSON-RPC
notification**, one level deeper than the WebSocket payload:

```json
{ "jsonrpc": "2.0", "method": "receive", "params": { "envelope": { ... }, "account": "..." } }
```

Reply with 200 or 201. There are no retries, so a failure or timeout loses the message. The
WebSocket with `manual` receive mode is the safer choice. (`RECEIVE_WEBHOOK_URL` is in the
current upstream source; confirm the pinned CI image has it before you rely on it.)

## 8. Message structure

Everything Signal delivers is an **envelope**. The envelope describes *who* and *when*. Exactly
one content field (usually) describes *what*.

### Envelope

```json
{
  "envelope": {
    "source": "74f5673c-1c12-4543-a441-b1429093642d",
    "sourceNumber": null,
    "sourceUuid": "74f5673c-1c12-4543-a441-b1429093642d",
    "sourceName": "Alice",
    "sourceDevice": 1,
    "timestamp": 1792886400123,
    "serverReceivedTimestamp": 1792886400200,
    "serverDeliveredTimestamp": 1792886400310,
    "dataMessage": { ... }
  },
  "account": "..."
}
```

| Field          | Meaning                                                                                   |
| -------------- | ----------------------------------------------------------------------------------------- |
| `sourceUuid`   | Sender's ACI. **Always key on this.** It's stable and always present for real messages     |
| `sourceNumber` | Sender's phone number, often `null` (number privacy, phoneless accounts)                  |
| `source`       | The number if known, otherwise the UUID                                                   |
| `sourceName`   | Sender's profile name, for display only. It can change                                    |
| `sourceDevice` | Which of the sender's devices sent it (`1` = their phone)                                 |
| `timestamp`    | Sent time in ms, set by the sender. **Together with `sourceUuid` it identifies the message.** Quotes, reactions, edits, and deletes refer to it |

Content fields. Expect one per envelope:

| Field             | When                                                                                |
| ----------------- | ----------------------------------------------------------------------------------- |
| `dataMessage`     | Someone else sent something: text, attachment, reaction, group update, deletion…   |
| `syncMessage`     | The account's **own other device** did something: sent a message, read messages     |
| `editMessage`     | A sender edited an earlier message                                                  |
| `receiptMessage`  | Delivery, read, or viewed receipts for messages *we* sent                           |
| `typingMessage`   | Typing indicator started or stopped                                                 |
| `callMessage`, `storyMessage` | Calls and stories. A bot usually ignores them                          |

### `dataMessage`: an incoming message

Direct message:

```json
"dataMessage": {
  "timestamp": 1792886400123,
  "message": "hi bot",
  "expiresInSeconds": 0,
  "viewOnce": false
}
```

The same message in a group. The only difference is `groupInfo`:

```json
"dataMessage": {
  "timestamp": 1792886400123,
  "message": "hi bot",
  "expiresInSeconds": 0,
  "viewOnce": false,
  "groupInfo": {
    "groupId": "X5Oxu7cq4G7sOcibULZ/WA1tMTKKiqvLaEpsXOGalSI=",
    "groupName": "Megabot",
    "revision": 3,
    "type": "DELIVER"
  }
}
```

| Field                     | Meaning                                                                         |
| ------------------------- | ------------------------------------------------------------------------------- |
| `message`                 | Text. `null` for attachment-only, reaction, or group-update messages            |
| `groupInfo`               | Present ⇢ group message. `groupId` is the **internal** ID (convert it with `to_rest_group_id`) |
| `groupInfo.type`          | `DELIVER` = a normal message. `UPDATE` = group changed (members, name, you were invited) |
| `mentions[]`              | `{uuid, number, name, start, length}`. The mention appears in `message` as `￼` (U+FFFC) |
| `quote`                   | Reply to an earlier message: `{id (= its timestamp), authorUuid, text, attachments}` |
| `attachments[]`           | `{id, contentType, filename, size, width, height, caption, isVoiceNote}`. Download with `GET /v1/attachments/{id}` |
| `reaction`                | `{emoji, isRemove, targetAuthorUuid, targetSentTimestamp}`                      |
| `remoteDelete`            | `{timestamp}` of the message the sender deleted                                 |
| `sticker`, `previews[]`, `textStyles[]`, `contacts[]`, `pollCreate`, `pollVote`, `pinMessage` | Less common content types |
| `expiresInSeconds`        | Disappearing-messages timer (0 = off)                                           |

### `syncMessage`: our own other devices

```json
"syncMessage": {
  "sentMessage": {
    "destination": "74f5673c-…",
    "destinationUuid": "74f5673c-…",
    "destinationNumber": null,
    "timestamp": 1792886500000,
    "message": "sent from my phone",
    "groupInfo": { "groupId": "X5Ox…", "type": "DELIVER" }
  }
}
```

`sentMessage` has the same fields as `dataMessage`, plus `destination*` for 1:1 chats. **Note to
Self** is a `sentMessage` whose `destinationUuid` is our own ACI. That makes it handy as a
private command channel to the bot. Other sync variants: `readMessages[]`, `blockedNumbers`,
`blockedGroupIds`, `type` (for example `CONTACTS_SYNC`).

### Other envelopes

```json
"receiptMessage": { "when": 1792886401000, "isDelivery": true, "isRead": false, "isViewed": false,
                    "timestamps": [1792886400999] }

"typingMessage":  { "action": "STARTED", "timestamp": 1792886400000, "groupId": "X5Ox…" }

"editMessage":    { "targetSentTimestamp": 1792886400123,
                    "dataMessage": { "timestamp": 1792886460000, "message": "hi bot!!" } }
```

The full schema is in Swagger under the `receive.*` definitions
(`curl -s http://127.0.0.1:8080/swagger/doc.json`).

## 9. Processing and storing messages

### Dispatch

```python
def handle(env: dict) -> None:
    sender = env.get("sourceUuid")
    ts = env["timestamp"]

    if dm := env.get("dataMessage"):
        group = dm.get("groupInfo")
        if group and group.get("type") == "UPDATE":
            return on_group_update(to_rest_group_id(group["groupId"]))  # refresh /v1/groups
        if dm.get("reaction"):
            return on_reaction(sender, dm["reaction"])
        if dm.get("remoteDelete"):
            return on_delete(sender, dm["remoteDelete"]["timestamp"])
        reply_to = to_rest_group_id(group["groupId"]) if group else sender
        return on_message(sender, ts, dm.get("message"), dm.get("attachments", []), reply_to)

    if edit := env.get("editMessage"):
        return on_edit(sender, edit["targetSentTimestamp"], edit["dataMessage"].get("message"))

    if sent := env.get("syncMessage", {}).get("sentMessage"):
        return on_own_message(sent)  # from our phone. Never auto-reply to these

    # receiptMessage, typingMessage, callMessage, storyMessage: ignore or log
```

Rules of thumb:

- **Reply target:** group message → the REST group ID; direct message → `sourceUuid`.
- **No loops:** the bot never receives its own sends. Messages typed on the phone arrive as
  `syncMessage`, so don't treat those as user input (Note to Self excepted, if you use it).
- **Idempotency:** `(sourceUuid, timestamp)` is unique per message. Make it a unique key so
  redeliveries (reconnects, restarts) are harmless.
- **Attachments** stay in the container (`GET /v1/attachments` lists them). Download what you
  need, then `DELETE /v1/attachments/{id}`, or skip them with `ignore_attachments=true`.

### Storage

Keep the raw envelope alongside a few extracted columns. That way you can re-parse later
without losing anything:

| Column             | Type         | Source                                              |
| ------------------ | ------------ | --------------------------------------------------- |
| `id`               | UUID PK      | `UuidPrimaryKeyMixin`                               |
| `source_uuid`      | UUID         | `envelope.sourceUuid`                               |
| `sent_at_ms`       | BIGINT       | `envelope.timestamp`                                |
| `group_id`         | TEXT NULL    | `to_rest_group_id(groupInfo.groupId)`               |
| `kind`             | TEXT         | `message` / `reaction` / `edit` / `delete` / `sync` / … |
| `text`             | TEXT NULL    | `dataMessage.message`                               |
| `raw`              | JSONB        | the whole envelope                                  |
| `created_at`, `updated_at` | TIMESTAMPTZ | `TimestampMixin`                              |

Unique constraint on `(source_uuid, sent_at_ms)`; insert with `ON CONFLICT DO NOTHING`. Store the
`timestamp` returned by `/v2/send` for the bot's own messages too, because you need it to edit,
delete, or react to them later.

## 10. Sending messages

Everything goes through **`POST /v2/send`** (`/v1/send` is the deprecated predecessor).

### Direct message to a user

```bash
curl -s -X POST http://127.0.0.1:8080/v2/send -H 'Content-Type: application/json' -d '{
  "number": "'"$ACCOUNT"'",
  "recipients": ["74f5673c-1c12-4543-a441-b1429093642d"],
  "message": "Hello from megabot"
}'
# 201 → [{"timestamp":"1792886600123"}]
```

A recipient can be an **ACI UUID** (preferred), an **E.164 number** (`+15551234567`), or a
**username** (`name.01`). Several users in one call are fine: `"recipients": ["<uuid1>", "<uuid2>"]`.

### Message to a group

```bash
curl -s -X POST http://127.0.0.1:8080/v2/send -H 'Content-Type: application/json' -d '{
  "number": "'"$ACCOUNT"'",
  "recipients": ["group.WDVPeHU3Y3E0RzdzT2NpYlVMWi9XQTF0TVRLS2lxdkxhRXBzWE9HYWxTST0="],
  "message": "Hello, group"
}'
```

The group recipient must be the **REST** ID (`group.…`), not `groupInfo.groupId`.

### Group + a user directly

One request can't mix them. The API rejects:

- groups together with numbers or UUIDs (`Groups and phone numbers cannot be specified together…`)
- more than one group (`cannot be sent to more than one group at once`)
- usernames together with groups or numbers

So send **one request per group** plus **one request for all direct recipients**:

```python
async def broadcast(text: str, group_ids: list[str], user_ids: list[str]) -> None:
    for gid in group_ids:
        await send(text, [gid])
    if user_ids:
        await send(text, user_ids)
```

### Request fields

| Field              | Type      | Meaning                                                                 |
| ------------------ | --------- | ----------------------------------------------------------------------- |
| `number`           | string    | **Required.** Sending account (our UUID)                                |
| `recipients`       | string[]  | **Required.** See the rules above                                       |
| `message`          | string    | Text                                                                    |
| `text_mode`        | `normal` \| `styled` | `styled` enables `**bold**`, `*italic*`, `~strike~`, `` `mono` ``, `\|\|spoiler\|\|` |
| `base64_attachments` | string[] | `"data:image/png;filename=a.png;base64,<data>"` or plain base64      |
| `mentions`         | object[]  | `{author: <uuid>, start, length}`. Offsets cover a placeholder in `message` (UTF-16 units) |
| `quote_timestamp`, `quote_author`, `quote_message` | | Reply to a message: its `timestamp`, its `sourceUuid`, and its text |
| `edit_timestamp`   | int       | Edit an earlier bot message (its send `timestamp`)                      |
| `link_preview`     | object    | `{url, title, description, base64_thumbnail}`                           |
| `sticker`          | string    | `"<pack_id>:<sticker_id>"`                                              |
| `view_once`        | bool      | Attachments only                                                        |
| `notify_self`      | bool      | Also notify our own devices                                             |

Quote-reply to an incoming group message:

```json
{
  "number": "<ACCOUNT>",
  "recipients": ["group.WDVP…ST0="],
  "message": "Got it",
  "quote_timestamp": 1792886400123,
  "quote_author": "74f5673c-1c12-4543-a441-b1429093642d",
  "quote_message": "hi bot"
}
```

### Response and errors

| Status | Body                                                  | Meaning                                         |
| ------ | ----------------------------------------------------- | ----------------------------------------------- |
| 201    | `[{"timestamp": "1792886600123"}]`                    | Sent. Save the timestamp (it's a string) as the message ID |
| 400    | `{"error": "..."}`                                    | Bad payload, unknown recipient, mixed recipient types, partial failure |
| 429    | `{"error": "...", "challenge_tokens": [...]}`         | Rate limited. Solve the captcha through `POST /v1/accounts/{n}/rate-limit-challenge` |

### Other outgoing actions

```bash
# React to a message
curl -s -X POST "http://127.0.0.1:8080/v1/reactions/$ACCOUNT" -d '{
  "recipient": "<uuid or group.…>", "reaction": "👍",
  "target_author": "<sourceUuid>", "timestamp": 1792886400123 }'

# Read receipt (1:1)
curl -s -X POST "http://127.0.0.1:8080/v1/receipts/$ACCOUNT" -d '{
  "recipient": "<uuid>", "receipt_type": "read", "timestamp": 1792886400123 }'

# Typing indicator on / off
curl -s -X PUT    "http://127.0.0.1:8080/v1/typing-indicator/$ACCOUNT" -d '{"recipient":"<uuid or group.…>"}'
curl -s -X DELETE "http://127.0.0.1:8080/v1/typing-indicator/$ACCOUNT" -d '{"recipient":"<uuid or group.…>"}'

# Delete a bot message for everyone
curl -s -X DELETE "http://127.0.0.1:8080/v1/remote-delete/$ACCOUNT" -d '{
  "recipient": "<uuid or group.…>", "timestamp": 1792886600123 }'
```

## 11. Endpoint reference

Live list: <http://127.0.0.1:8080/swagger/index.html> (spec: `/swagger/doc.json`, JSON only).
`{n}` = account UUID or number, `{gid}` = REST group ID (`group.…`).

**General and linking**

| Method | Path                         | Purpose                                         |
| ------ | ---------------------------- | ----------------------------------------------- |
| GET    | `/v1/health`                 | 204 when healthy (Compose healthcheck)          |
| GET    | `/v1/about`                  | Version, mode, capabilities                     |
| GET    | `/v1/qrcodelink/raw`         | Link URI (`?device_name=`), used by the link script |
| GET    | `/v1/qrcodelink`             | Link QR as a PNG (`?device_name=&qrcode_version=15`) |
| GET    | `/v1/accounts`               | Linked or registered accounts                   |
| GET    | `/v1/devices/{n}`            | Devices on the account; doubles as a link check |
| DELETE | `/v1/devices/{n}/{deviceId}` | Unlink a device (primary only)                  |
| DELETE | `/v1/devices/{n}/local-data` | Delete local account data                       |
| GET/POST | `/v1/configuration/{n}/settings` | Trust mode                                  |

**Messages**

| Method | Path                         | Purpose                                         |
| ------ | ---------------------------- | ----------------------------------------------- |
| GET / WS | `/v1/receive/{n}`          | Receive (GET in native mode, WebSocket in json-rpc mode) |
| POST   | `/v2/send`                   | Send text, attachments, quotes, mentions, edits |
| POST/DELETE | `/v1/reactions/{n}`     | Add or remove a reaction                        |
| POST   | `/v1/receipts/{n}`           | Read or viewed receipt                          |
| PUT/DELETE | `/v1/typing-indicator/{n}` | Show or hide typing                           |
| DELETE | `/v1/remote-delete/{n}`      | Delete a sent message for everyone              |
| GET    | `/v1/attachments`            | List downloaded attachments                     |
| GET/DELETE | `/v1/attachments/{id}`   | Fetch or delete one attachment                  |
| POST/DELETE | `/v1/polls/{n}`, POST `/v1/polls/{n}/vote` | Polls                     |

**Groups**

| Method | Path                         | Purpose                                         |
| ------ | ---------------------------- | ----------------------------------------------- |
| GET    | `/v1/groups/{n}`             | All groups, including invitations (`member:false`) |
| POST   | `/v1/groups/{n}`             | Create a group                                  |
| GET/PUT/DELETE | `/v1/groups/{n}/{gid}` | Get / update / delete a group                 |
| POST   | `/v1/groups/{n}/{gid}/join`  | Accept an invitation                            |
| POST   | `/v1/groups/{n}/{gid}/quit`  | Leave or decline                                |
| POST   | `/v1/groups/{n}/{gid}/block` | Block a group                                   |
| POST/DELETE | `/v1/groups/{n}/{gid}/members` | Add or remove members                     |
| POST/DELETE | `/v1/groups/{n}/{gid}/admins`  | Add or remove admins                      |
| POST/DELETE | `/v1/groups/{n}/{gid}/pin-message` | Pin or unpin a message                |
| GET    | `/v1/groups/{n}/{gid}/avatar` | Group avatar                                   |

**Contacts, profile, identity**

| Method | Path                         | Purpose                                         |
| ------ | ---------------------------- | ----------------------------------------------- |
| GET    | `/v1/contacts/{n}`           | Contacts: uuid, number, names, username         |
| GET    | `/v1/contacts/{n}/{uuid}`    | One contact                                     |
| PUT    | `/v1/contacts/{n}`           | Add or rename a contact                         |
| GET    | `/v1/search/{n}?numbers=`    | Are these numbers on Signal?                    |
| PUT    | `/v1/profiles/{n}`           | Set profile name, about, avatar (**changes the real account's profile**) |
| GET    | `/v1/identities/{n}`         | Safety numbers                                  |
| PUT    | `/v1/identities/{n}/trust/{peer}` | Trust a changed identity                   |

Not relevant for a linked device: `/v1/register/*`, `/v1/unregister/*`, `/v1/accounts/{n}/pin`,
`/v1/accounts/{n}/username`, `/v1/accounts/{n}/settings`. These manage the primary account. Use
the phone.

## 12. Gotchas

- **Two group IDs.** Incoming `groupInfo.groupId` ≠ REST `group.…` ID. Convert before replying
  or calling group endpoints.
- **Phoneless account.** `/v1/accounts` returns `[""]`. Use the ACI UUID from `accounts.json` as
  `{number}`.
- **One consumer.** Receiving drains the server queue. Run exactly one poller or WebSocket per account.
- **json-rpc drops messages by default** while no WebSocket client is connected. Set
  `JSON_RPC_RECEIVE_MODE=manual`.
- **The bot speaks as you.** Sends appear as the account owner on every device. Profile and
  group-admin changes affect the real account.
- **Stay online.** Receive at least every few days, or Signal unlinks the device after about 30
  days offline.
- **No auth.** Keep the port on `127.0.0.1` and on the internal Compose network only. Anyone who
  reaches it can read and send as the account, and anyone who has the `signal-cli-data`
  volume can too.
- **`nopni2`.** Link phoneless accounts only through `signal-api-link-device.sh` until a
  signal-cli release includes the fix.
- **Swagger** is JSON only (`doc.yaml` returns 404) and is only up while the container runs.
