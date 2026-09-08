import re
import subprocess


ADDRESS_PATTERN = re.compile(
    r"^[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}$"
)


class BluetoothError(RuntimeError):
    pass


def _command(
    *args,
    timeout=20,
    check=True,
):
    try:
        result = subprocess.run(
            [
                "bluetoothctl",
                *args,
            ],
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as error:
        raise BluetoothError(
            "bluetoothctl is not installed."
        ) from error
    except subprocess.TimeoutExpired as error:
        raise BluetoothError(
            "Bluetooth operation timed out."
        ) from error

    output = "\n".join(
        part
        for part in (
            result.stdout.strip(),
            result.stderr.strip(),
        )
        if part
    )

    failed = (
        result.returncode != 0
        or "Failed to " in output
        or "No default controller available" in output
        or "Invalid command" in output
    )

    if check and failed:
        raise BluetoothError(
            output
            or "Bluetooth operation failed."
        )

    return result


def _output(
    *args,
    timeout=20,
    check=True,
):
    return _command(
        *args,
        timeout=timeout,
        check=check,
    ).stdout.strip()


def _controller_state():
    raw = _output(
        "show",
        check=False,
    )

    available = False
    enabled = False

    for line in raw.splitlines():
        stripped = line.strip()

        if line.startswith(
            "Controller "
        ):
            available = True

        if stripped.startswith(
            "Powered:"
        ):
            enabled = (
                stripped.split(
                    ":",
                    1,
                )[1].strip()
                == "yes"
            )

    return {
        "available": available,
        "enabled": enabled,
    }


def is_available():
    return _controller_state()[
        "available"
    ]


def is_enabled():
    return _controller_state()[
        "enabled"
    ]


def set_enabled(enabled):
    if not is_available():
        raise BluetoothError(
            "No Bluetooth adapter found."
        )

    _command(
        "power",
        "on" if enabled else "off",
    )


def toggle():
    set_enabled(
        not is_enabled()
    )


def _parse_devices(raw):
    devices = {}

    for line in raw.splitlines():
        if not line.startswith(
            "Device "
        ):
            continue

        parts = line.split(
            " ",
            2,
        )

        if len(parts) < 2:
            continue

        address = parts[
            1
        ].strip()

        if not ADDRESS_PATTERN.fullmatch(
            address
        ):
            continue

        name = (
            parts[2].strip()
            if len(parts) == 3
            else address
        )

        address = address.upper()

        devices[address] = {
            "address": address,
            "name": (
                name
                or address
            ),
        }

    return devices


def _device_map(
    filter_name=None,
):
    command = [
        "devices",
    ]

    if filter_name:
        command.append(
            filter_name
        )

    return _parse_devices(
        _output(
            *command
        )
    )


def get_devices():
    all_devices = _device_map()

    paired = _device_map(
        "Paired"
    )

    connected = _device_map(
        "Connected"
    )

    merged = {}

    for source in (
        all_devices,
        paired,
        connected,
    ):
        for (
            address,
            device,
        ) in source.items():
            merged.setdefault(
                address,
                device,
            )

    paired_addresses = set(
        paired
    )

    connected_addresses = set(
        connected
    )

    devices = []

    for (
        address,
        device,
    ) in merged.items():
        devices.append({
            **device,
            "paired": (
                address
                in paired_addresses
            ),
            "connected": (
                address
                in connected_addresses
            ),
        })

    devices.sort(
        key=lambda device: (
            not device[
                "connected"
            ],
            not device[
                "paired"
            ],
            device[
                "name"
            ].casefold(),
            device[
                "address"
            ],
        )
    )

    return devices


def get_connected_device():
    connected = _device_map(
        "Connected"
    )

    if not connected:
        return ""

    return next(
        iter(
            connected.values()
        )
    )["name"]


def get_state(
    include_devices=False,
):
    controller = (
        _controller_state()
    )

    available = controller[
        "available"
    ]

    enabled = controller[
        "enabled"
    ]

    state = {
        "available": available,
        "enabled": enabled,
        "device": "",
        "devices": [],
    }

    if not available:
        return state

    if enabled:
        state["device"] = (
            get_connected_device()
        )

        if include_devices:
            state["devices"] = (
                get_devices()
            )

    return state


def scan(
    seconds=5,
):
    if not is_enabled():
        raise BluetoothError(
            "Bluetooth is turned off."
        )

    seconds = max(
        1,
        min(
            int(seconds),
            15,
        ),
    )

    _command(
        "--timeout",
        str(seconds),
        "scan",
        "on",
        timeout=seconds + 5,
    )

    return get_devices()


def _validate_address(
    address,
):
    address = str(
        address
    ).upper()

    if not ADDRESS_PATTERN.fullmatch(
        address
    ):
        raise BluetoothError(
            "Invalid Bluetooth device address."
        )

    return address


def pair(
    address,
):
    address = _validate_address(
        address
    )

    _command(
        "--timeout",
        "30",
        "--agent",
        "NoInputNoOutput",
        "pair",
        address,
        timeout=35,
    )


def connect(
    address,
):
    address = _validate_address(
        address
    )

    _command(
        "--timeout",
        "15",
        "connect",
        address,
        timeout=20,
    )


def disconnect(
    address,
):
    address = _validate_address(
        address
    )

    _command(
        "--timeout",
        "15",
        "disconnect",
        address,
        timeout=20,
    )


def forget(
    address,
):
    address = _validate_address(
        address
    )

    _command(
        "remove",
        address,
    )