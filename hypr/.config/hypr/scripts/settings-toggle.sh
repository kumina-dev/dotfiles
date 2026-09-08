#!/usr/bin/env bash

set -euo pipefail

APP="$HOME/.config/hypr/scripts/kumina-settings.py"
PATTERN="[k]umina-settings.py"

PAGE="${1:-overview}"

if pgrep -f -- "$PATTERN" >/dev/null; then
    pkill -f -- "$PATTERN" || true
    exit 0
fi

"$APP" "$PAGE" >/dev/null 2>&1 &