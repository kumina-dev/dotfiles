#!/usr/bin/env bash

set -euo pipefail

APP="$HOME/.config/hypr/scripts/kumina-calendar.py"
PATTERN="[k]umina-calendar.py"

if pgrep -f "$PATTERN" >/dev/null; then
    pkill -f "$PATTERN"
    exit 0
fi

"$APP" >/dev/null 2>&1 &
