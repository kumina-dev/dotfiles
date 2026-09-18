#!/usr/bin/env python3
"""Waybar JSON stream; refresh preferences and local time without restarting."""
import json
import time

from kumina_common.i18n import read_language
from kumina_common.region import clock_payload, local_now, read_preferences


def main():
    previous = None
    while True:
        payload = clock_payload(local_now(), read_preferences(), language=read_language())
        if payload != previous:
            print(json.dumps(payload), flush=True)
            previous = payload
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except (BrokenPipeError, KeyboardInterrupt):
        pass
