from .command import (
    output,
    run,
)


ACTIONS = {
    "previous",
    "play-pause",
    "next",
}


METADATA_FORMAT = (
    "{{artist}} — {{title}}"
)


def get_state():
    player = get_player()

    if not player:
        return {
            "player": "",
            "status": "",
            "metadata": "",
        }

    return {
        "player": player,
        "status": get_status(
            player
        ),
        "metadata": get_metadata(
            player
        ),
    }


def get_player():
    players = output([
        "playerctl",
        "-l",
    ]).splitlines()

    if not players:
        return ""

    for wanted_status in (
        "Playing",
        "Paused",
    ):
        for player in players:
            status = output([
                "playerctl",
                f"--player={player}",
                "status",
            ])

            if status == wanted_status:
                return player

    return players[0]


def get_status(
    player=None,
):
    player = (
        player
        or get_player()
    )

    if not player:
        return ""

    return output([
        "playerctl",
        f"--player={player}",
        "status",
    ])


def get_metadata(
    player=None,
):
    player = (
        player
        or get_player()
    )

    if not player:
        return ""

    return output([
        "playerctl",
        f"--player={player}",
        "metadata",
        "--format",
        METADATA_FORMAT,
    ])


def command(
    action,
):
    if action not in ACTIONS:
        raise ValueError(
            "Unsupported media action."
        )

    player = get_player()

    if not player:
        return None

    return run([
        "playerctl",
        f"--player={player}",
        action,
    ])


def previous():
    return command(
        "previous"
    )


def play_pause():
    return command(
        "play-pause"
    )


def next():
    return command(
        "next"
    )