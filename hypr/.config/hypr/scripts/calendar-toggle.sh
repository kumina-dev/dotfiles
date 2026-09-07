#!/bin/sh

CALENDAR="$HOME/.config/hypr/scripts/kumina-calendar.py"

if pgrep -f "[k]umina-calendar.py" >/dev/null; then
    pkill -f "[k]umina-calendar.py"
else
    "$CALENDAR" >/dev/null 2>&1 &
fi
