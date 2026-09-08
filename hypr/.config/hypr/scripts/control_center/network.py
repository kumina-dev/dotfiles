from .command import (
    output,
    run,
)


def is_wifi_enabled():
    return (
        output(
            [
                "nmcli",
                "radio",
                "wifi",
            ],
            check=True,
            fallback=(
                "Could not read Wi-Fi state."
            ),
        )
        == "enabled"
    )


def set_wifi_enabled(
    enabled,
):
    return run(
        [
            "nmcli",
            "radio",
            "wifi",
            "on" if enabled else "off",
        ],
        check=True,
        fallback=(
            "Could not change Wi-Fi state."
        ),
    )


def toggle_wifi():
    return set_wifi_enabled(
        not is_wifi_enabled()
    )


def get_current_ssid():
    raw = output(
        [
            "nmcli",
            "-t",
            "-f",
            "ACTIVE,SSID",
            "device",
            "wifi",
        ],
        check=True,
        fallback=(
            "Could not read the current Wi-Fi network."
        ),
    )

    for line in raw.splitlines():
        active, separator, ssid = (
            line.partition(":")
        )

        if (
            separator
            and active == "yes"
            and ssid
        ):
            return ssid

    return ""


def get_state():
    enabled = is_wifi_enabled()

    return {
        "enabled": enabled,
        "ssid": (
            get_current_ssid()
            if enabled
            else ""
        ),
    }


def get_networks(
    rescan=True,
):
    raw = output(
        [
            "nmcli",
            "-t",
            "-f",
            "IN-USE,SSID,SIGNAL,SECURITY",
            "device",
            "wifi",
            "list",
            "--rescan",
            (
                "yes"
                if rescan
                else "no"
            ),
        ],
        check=True,
        fallback=(
            "Could not load Wi-Fi networks."
        ),
    )

    networks = []
    seen = set()

    for line in raw.splitlines():
        parts = line.split(
            ":",
            3,
        )

        if len(parts) != 4:
            continue

        (
            active,
            ssid,
            signal,
            security,
        ) = parts

        if (
            not ssid
            or ssid in seen
        ):
            continue

        seen.add(
            ssid
        )

        try:
            signal_value = int(
                signal
            )
        except ValueError:
            signal_value = 0

        networks.append({
            "ssid": ssid,
            "signal": signal_value,
            "security": security,
            "connected": (
                active == "*"
            ),
        })

    return networks


def connect_saved_network(
    ssid,
):
    return run(
        [
            "nmcli",
            "connection",
            "up",
            "id",
            ssid,
        ],
        check=True,
        fallback=(
            "Could not connect to the Wi-Fi network."
        ),
    )