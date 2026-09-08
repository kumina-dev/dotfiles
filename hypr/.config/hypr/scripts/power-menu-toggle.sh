#!/usr/bin/env bash

POWER_MENU="$HOME/.config/hypr/scripts/kumina-power-menu.py"

if pgrep -f "[k]umina-power-menu.py" >/dev/null; then
    pkill -f "[k]umina-power-menu.py"
else
    "$POWER_MENU" >/dev/null 2>&1 &
fi