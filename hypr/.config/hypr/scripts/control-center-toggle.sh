#!/usr/bin/env bash

set -euo pipefail

APP="$HOME/.config/hypr/scripts/kumina-control-center.py"
PATTERN="[k]umina-control-center.py"

if pgrep -f -- "$PATTERN" >/dev/null; then
    pkill -f -- "$PATTERN" || true
    exit 0
fi

"$APP" >/dev/null 2>&1 &