#!/usr/bin/env bash

CONTROL_CENTER="$HOME/.config/hypr/scripts/kumina-control-center.py"

if pgrep -f "[k]umina-control-center.py" >/dev/null; then
    pkill -f "[k]umina-control-center.py"
else
    "$CONTROL_CENTER" >/dev/null 2>&1 &
fi