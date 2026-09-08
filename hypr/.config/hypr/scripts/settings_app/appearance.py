from pathlib import Path

from kumina_common.process import (
    output,
)


CURRENT_WALLPAPER = (
    Path.home()
    / "Pictures"
    / "Wallpapers"
    / "main.png"
)

MODE_FILE = (
    Path.home()
    / ".config"
    / "kumina"
    / "appearance-mode"
)

SET_WALLPAPER = (
    Path.home()
    / ".local"
    / "bin"
    / "set-wallpaper"
)

MODES = (
    "dark",
    "light",
)


class AppearanceError(RuntimeError):
    pass


def get_mode():
    if not MODE_FILE.exists():
        return "dark"

    try:
        mode = (
            MODE_FILE
            .read_text(
                encoding="utf-8"
            )
            .strip()
        )
    except OSError:
        return "dark"

    if mode not in MODES:
        return "dark"

    return mode


def get_state():
    return {
        "mode": get_mode(),
        "wallpaper": (
            str(CURRENT_WALLPAPER)
            if CURRENT_WALLPAPER.exists()
            else ""
        ),
    }


def apply_settings(
    wallpaper,
    mode,
):
    if mode not in MODES:
        raise AppearanceError(
            "Invalid appearance mode."
        )

    if wallpaper:
        source = (
            Path(wallpaper)
            .expanduser()
        )
    else:
        source = CURRENT_WALLPAPER

    if not source.is_file():
        raise AppearanceError(
            "Choose a wallpaper first."
        )

    if not SET_WALLPAPER.is_file():
        raise AppearanceError(
            "set-wallpaper is not installed."
        )

    output(
        [
            str(SET_WALLPAPER),
            str(source),
            mode,
        ],
        timeout=30,
        check=True,
        error_type=AppearanceError,
        fallback=(
            "Could not apply appearance settings."
        ),
    )

    return get_state()