#!/usr/bin/env bash
# Generate a fresh "Link device" QR code and open it.
# The QR is only valid for about a minute, so scan it right away.
#
# Workaround for phone-numberless accounts (signal-cli issue #2140):
# Signal Android 8.30+ requires the "nopni2" capability in the link URI, but
# signal-cli 0.14.9 only advertises "nopni", so the phone says the device is
# outdated. We take the raw URI from the API, add nopni2, and render the QR
# locally with qrencode (brew install qrencode). Fixed upstream in signal-cli
# master (32f652e); remove this patch once a release with the fix is out.
set -euo pipefail

API="${API:-http://localhost:8080}"
DEVICE_NAME="${1:-signal-bot-poc}"
OUT="$(dirname "$0")/signal-api-qrcode.png"

command -v qrencode >/dev/null || { echo "qrencode missing: brew install qrencode" >&2; exit 1; }

resp=$(curl -s "$API/v1/qrcodelink/raw?device_name=$DEVICE_NAME")
uri=$(printf '%s' "$resp" | python3 -c 'import sys,json; print(json.load(sys.stdin)["device_link_uri"])') || {
  echo "Failed to get link URI: $resp" >&2; exit 1; }

case "$uri" in
  *nopni2*) ;;
  *capabilities=*) uri="${uri/capabilities=nopni/capabilities=nopni,nopni2}" ;;
  *) uri="${uri}&capabilities=nopni,nopni2" ;;
esac

qrencode -o "$OUT" -s 10 -m 4 "$uri"
echo "Capabilities: ${uri##*capabilities=}"
echo "QR saved to $OUT, opening it. Scan with: Signal > Settings > Linked devices > Link new device"
open "$OUT" 2>/dev/null || xdg-open "$OUT" 2>/dev/null || true
