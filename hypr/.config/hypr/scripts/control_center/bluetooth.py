from .command import output, run


def is_enabled():
    raw = output(
        "bluetoothctl show"
    )

    for line in raw.splitlines():
        line = line.strip()

        if line.startswith("Powered:"):
            return (
                line.split(":", 1)[1].strip()
                == "yes"
            )

    return False


def set_enabled(enabled):
    return run(
        "bluetoothctl power on"
        if enabled
        else "bluetoothctl power off"
    )


def toggle():
    return set_enabled(
        not is_enabled()
    )


def get_connected_device():
    raw = output(
        "bluetoothctl devices Connected"
    )

    for line in raw.splitlines():
        parts = line.split(
            " ",
            2,
        )

        if len(parts) == 3:
            return parts[2]

    return ""


def get_state():
    enabled = is_enabled()

    return {
        "enabled": enabled,
        "device": (
            get_connected_device()
            if enabled
            else ""
        ),
    }