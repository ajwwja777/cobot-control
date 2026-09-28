#!/usr/bin/env bash
# Explicit administrator operation for a NEW machine; never called by the web.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${1:-}" != --apply ]]; then
  echo "Review scripts/system/*.rules and sudoers example, then run sudo ./scripts/install_system.sh --apply USER"
  exit 0
fi
[[ $EUID == 0 ]] || { echo "Run as root"; exit 2; }
user="${2:?deployment user required}"
id "$user" >/dev/null
[[ "$user" =~ ^[a-z_][a-z0-9_-]*$ ]] || exit 2
install -o root -g root -m 0755 "$ROOT/scripts/system/cobot-can-recover-one" /usr/local/sbin/cobot-can-recover-one
temporary="$(mktemp)"
trap 'rm -f -- "$temporary"' EXIT
sed "s/^agilex /$user /" "$ROOT/scripts/system/cobot-can-recover-one.sudoers.example" >"$temporary"
visudo -cf "$temporary"
install -o root -g root -m 0440 "$temporary" /etc/sudoers.d/cobot-can-recover-one
install -o root -g root -m 0644 "$ROOT/scripts/system/56-orbbec-usb.rules" /etc/udev/rules.d/56-orbbec-usb.rules
# CAN port names come from machine config; do not install the historical arx_can.rules blindly.
udevadm control --reload-rules
echo "Installed; no USB trigger, CAN reset or robot launch performed."
