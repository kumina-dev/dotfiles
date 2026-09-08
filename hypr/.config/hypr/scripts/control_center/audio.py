"""PipeWire discovery and WirePlumber controls shared by both windows."""

import json
import math
import os
import re
import subprocess
from dataclasses import dataclass


class AudioError(RuntimeError):
    pass


@dataclass(frozen=True)
class Device:
    id: int
    serial: str
    name: str
    description: str
    kind: str


def _command(*arguments):
    try:
        result = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            timeout=4,
            env={**os.environ, "LC_ALL": "C"},
        )
    except FileNotFoundError as error:
        package = "pipewire" if arguments[0] == "pw-dump" else "wireplumber"
        raise AudioError(f"{arguments[0]} is missing. Install {package}.") from error
    except subprocess.TimeoutExpired as error:
        raise AudioError("The audio service did not respond. Try again.") from error

    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise AudioError(detail or "The audio command failed. Try again.")

    return result.stdout.strip()


def _snapshot():
    try:
        objects = json.loads(_command("pw-dump", "--no-colors"))
    except json.JSONDecodeError as error:
        raise AudioError("Could not read the audio device list.") from error

    if not isinstance(objects, list):
        raise AudioError("Could not read the audio device list.")

    devices = {"output": [], "input": []}
    defaults = {"output": None, "input": None}
    classes = {
        "Audio/Sink": "output",
        "Audio/Source": "input",
        "Audio/Source/Virtual": "input",
    }
    keys = {"default.audio.sink": "output", "default.audio.source": "input"}

    for item in objects:
        if item.get("type") == "PipeWire:Interface:Node":
            props = (item.get("info") or {}).get("props") or {}
            kind = classes.get(props.get("media.class"))
            name = props.get("node.name")
            if kind and name:
                devices[kind].append(Device(
                    id=int(item["id"]),
                    serial=str(props.get("object.serial", "")),
                    name=name,
                    description=(props.get("node.description")
                                 or props.get("node.nick") or name),
                    kind=kind,
                ))

        elif (item.get("type") == "PipeWire:Interface:Metadata"
              and (item.get("props") or {}).get("metadata.name") == "default"):
            for entry in item.get("metadata", []):
                kind = keys.get(entry.get("key"))
                if kind is None or entry.get("subject") != 0:
                    continue
                value = entry.get("value")
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        continue
                if isinstance(value, dict):
                    defaults[kind] = value.get("name")

    for values in devices.values():
        values.sort(key=lambda device: (device.description.casefold(), device.name))

    return devices, defaults


def _volume(device):
    value = _command("wpctl", "get-volume", str(device.id))
    match = re.fullmatch(r"Volume:\s+(\d+(?:\.\d+)?)\s*(\[MUTED\])?", value)
    if match is None:
        raise AudioError("Could not read this device's volume.")
    volume = float(match[1]) * 100
    if not math.isfinite(volume):
        raise AudioError("Could not read this device's volume.")
    return round(volume), bool(match[2])


def get_state():
    devices, defaults = _snapshot()
    state = {}
    for kind in ("output", "input"):
        device = next((item for item in devices[kind]
                       if item.name == defaults[kind]), None)
        endpoint = {
            "devices": devices[kind],
            "device": device,
            "volume": None,
            "muted": False,
            "error": None,
        }
        if device is not None:
            try:
                endpoint["volume"], endpoint["muted"] = _volume(device)
            except AudioError as error:
                endpoint["error"] = str(error)
        state[kind] = endpoint
    return state


def _target(device):
    # Recheck the displayed node instead of writing to a potentially changed default.
    devices, _defaults = _snapshot()
    for current in devices[device.kind]:
        if (current.id, current.serial, current.name) == (
            device.id, device.serial, device.name,
        ):
            return str(current.id)
    raise AudioError("The audio device disconnected. Choose a device and try again.")


def set_default(device):
    _command("wpctl", "set-default", _target(device))


def set_volume(device, volume):
    volume = max(0, min(100, round(volume)))
    _command("wpctl", "set-volume", "--limit", "1.0", _target(device), f"{volume}%")


def set_mute(device, muted):
    _command("wpctl", "set-mute", _target(device), "1" if muted else "0")
