from .command import output, run


def get_state():
    player = get_player()

    if not player:
        return {
            "player": "",
            "status": "",
            "metadata": "",
        }

    status = get_status(player)

    metadata = output(
        f"playerctl --player='{player}' "
        "metadata "
        "--format '{{artist}} — {{title}}'"
    )

    return {
        "player": player,
        "status": status,
        "metadata": metadata,
    }


def get_player():
    players = output(
        "playerctl -l"
    ).splitlines()

    if not players:
        return ""

    for wanted_status in (
        "Playing",
        "Paused",
    ):
        for player in players:
            status = output(
                f"playerctl "
                f"--player='{player}' "
                "status"
            )

            if status == wanted_status:
                return player

    return players[0]


def get_status(player=None):
    player = player or get_player()

    if not player:
        return ""

    return output(
        f"playerctl "
        f"--player='{player}' "
        "status"
    )


def get_metadata(player=None):
    player = player or get_player()

    if not player:
        return ""

    return output(
        f"playerctl "
        f"--player='{player}' "
        "metadata "
        "--format '{{artist}} — {{title}}'"
    )


def command(action):
    player = get_player()

    if not player:
        return None

    return run(
        f"playerctl "
        f"--player='{player}' "
        f"{action}"
    )


def previous():
    return command("previous")


def play_pause():
    return command("play-pause")


def next():
    return command("next")