from .command import output, run


def get_volume():
    value = output(
        "wpctl get-volume @DEFAULT_AUDIO_SINK@"
    )

    try:
        volume = float(
            value.split()[1]
        )

        return round(volume * 100)
    except (IndexError, ValueError):
        return 0


def is_muted():
    value = output(
        "wpctl get-volume @DEFAULT_AUDIO_SINK@"
    )

    return "[MUTED]" in value


def set_volume(volume):
    volume = max(
        0,
        min(100, int(volume)),
    )

    return run(
        "wpctl set-volume "
        "@DEFAULT_AUDIO_SINK@ "
        f"{volume}%"
    )


def toggle_mute():
    return run(
        "wpctl set-mute "
        "@DEFAULT_AUDIO_SINK@ toggle"
    )

def get_state():
    value = output(
        "wpctl get-volume "
        "@DEFAULT_AUDIO_SINK@"
    )

    try:
        volume = round(
            float(value.split()[1])
            * 100
        )
    except (IndexError, ValueError):
        volume = 0

    return {
        "volume": volume,
        "muted": "[MUTED]" in value,
    }