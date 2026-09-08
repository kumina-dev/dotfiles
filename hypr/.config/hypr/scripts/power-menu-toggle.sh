#!/usr/bin/env bash

set -euo pipefail

APP="$HOME/.config/hypr/scripts/kumina-power-menu.py"
PATTERN="[k]umina-power-menu.py"

if pgrep -f -- "$PATTERN" >/dev/null; then
    pkill -f -- "$PATTERN" || true
    exit 0
fi

"$APP" >/dev/null 2>&1 &