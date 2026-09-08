#!/usr/bin/env bash

SETTINGS="$HOME/.config/hypr/scripts/kumina-settings.py"

PAGE="${1:-overview}"

if pgrep -f "[k]umina-settings.py" >/dev/null; then
    pkill -f "[k]umina-settings.py"
else
    "$SETTINGS" "$PAGE" >/dev/null 2>&1 &
fi