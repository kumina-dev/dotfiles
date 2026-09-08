from kumina_common.process import (
    output,
    run,
)


def is_wifi_enabled():
    return (
        output([
            "nmcli",
            "radio",
            "wifi",
        ])
        == "enabled"
    )


def set_wifi_enabled(enabled):
    return run([
        "nmcli",
        "radio",
        "wifi",
        "on" if enabled else "off",
    ])


def get_current_ssid():
    raw = output([
        "nmcli",
        "-t",
        "-f",
        "ACTIVE,SSID",
        "device",
        "wifi",
    ])

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


def get_wifi_device():
    raw = output([
        "nmcli",
        "-t",
        "-f",
        "DEVICE,TYPE,STATE",
        "device",
        "status",
    ])

    for line in raw.splitlines():
        parts = line.split(":", 2)

        if len(parts) != 3:
            continue

        device, device_type, state = parts

        if (
            device_type == "wifi"
            and state != "unavailable"
        ):
            return device

    return ""


def get_saved_profiles():
    raw = output([
        "nmcli",
        "-t",
        "-f",
        "UUID,TYPE",
        "connection",
        "show",
    ])

    profiles = {}

    for line in raw.splitlines():
        uuid, separator, connection_type = (
            line.partition(":")
        )

        if (
            not separator
            or connection_type
            not in (
                "802-11-wireless",
                "wifi",
            )
        ):
            continue

        ssid = output([
            "nmcli",
            "-g",
            "802-11-wireless.ssid",
            "connection",
            "show",
            "uuid",
            uuid,
        ])

        if not ssid:
            continue

        name = output([
            "nmcli",
            "-g",
            "connection.id",
            "connection",
            "show",
            "uuid",
            uuid,
        ])

        profiles[ssid] = {
            "uuid": uuid,
            "name": name or ssid,
        }

    return profiles


def get_networks():
    raw = output([
        "nmcli",
        "-t",
        "-f",
        "IN-USE,SSID,SIGNAL,SECURITY",
        "device",
        "wifi",
        "list",
        "--rescan",
        "yes",
    ])

    profiles = get_saved_profiles()

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

        seen.add(ssid)

        try:
            signal = int(signal)
        except ValueError:
            signal = 0

        profile = profiles.get(ssid)

        networks.append({
            "ssid": ssid,
            "signal": signal,
            "security": security,
            "secured": bool(
                security
                and security != "--"
            ),
            "connected": active == "*",
            "saved": profile is not None,
            "profile_uuid": (
                profile["uuid"]
                if profile
                else None
            ),
        })

    networks.sort(
        key=lambda item: (
            not item["connected"],
            not item["saved"],
            -item["signal"],
        )
    )

    return networks


def get_state():
    enabled = is_wifi_enabled()

    if not enabled:
        return {
            "enabled": False,
            "ssid": "",
            "networks": [],
        }

    return {
        "enabled": True,
        "ssid": get_current_ssid(),
        "networks": get_networks(),
    }


def connect_saved(profile_uuid):
    return run([
        "nmcli",
        "connection",
        "up",
        "uuid",
        profile_uuid,
    ])


def connect_new(
    ssid,
    password=None,
):
    command = [
        "nmcli",
        "device",
        "wifi",
        "connect",
        ssid,
    ]

    if password:
        command.extend([
            "password",
            password,
        ])

    return run(command)


def disconnect():
    device = get_wifi_device()

    if not device:
        return None

    return run([
        "nmcli",
        "device",
        "disconnect",
        device,
    ])


def forget(profile_uuid):
    return run([
        "nmcli",
        "connection",
        "delete",
        "uuid",
        profile_uuid,
    ])