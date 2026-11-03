#!/usr/bin/env python3
"""KumiOS appearance: wallpaper accent and Light / Dark / Automatic mode.

Read-only check by default. `--apply MODE` backs up the current appearance,
installs the KumiOS Plasma style and the appearance-only KumiOS Light/Dark
global themes, hands the GTK settings directories to KDE, enables KDE's
wallpaper accent and selects the mode. It never changes the wallpaper or the
panel layout, and never restarts Plasma.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parent
PACKAGES = {"light": "org.kumios.light", "dark": "org.kumios.dark"}
MODES = ("current", "light", "dark", "auto")
TOOLS = ("plasma-apply-lookandfeel", "kwriteconfig6", "kreadconfig6", "qdbus6")
SCHEMES = ("BreezeLight", "BreezeDark")
# KDE services that provide the wallpaper accent, the light/dark auto-switch and
# GTK settings synchronization.
KDED_MODULES = ("plasma_accentcolor_service", "lookandfeelautoswitcher", "gtkconfig")
APPEARANCE_CONFIGS = ("kdeglobals", "plasmarc", "kdedefaults/kdeglobals", "kdedefaults/plasmarc")
GTK_DIRS = ("gtk-3.0", "gtk-4.0")
# Files KDE's GTK integration generates; anything else in a linked directory
# (such as legacy Hyprland/matugen styling) stays with its original package.
GTK_KDE_FILES = ("settings.ini", "colors.css")
GTK_CSS = "@import 'colors.css';\n"


def run(*args):
    return subprocess.run(args, text=True, capture_output=True, check=True, timeout=120).stdout.strip()


def read_config(name, group, key):
    return run("kreadconfig6", "--file", name, "--group", group, "--key", key)


def write_config(name, group, key, value):
    run("kwriteconfig6", "--notify", "--file", name, "--group", group, "--key", key, value)


def dirs():
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config")))
    data = Path(os.environ.get("XDG_DATA_HOME", str(home / ".local/share")))
    return config, data


def variant_of(rgb):
    """'dark' or 'light' from a KDE "r,g,b" window background."""
    red, green, blue = (int(part) for part in rgb.split(",")[:3])
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "dark" if luminance < 128 else "light"


def current_variant():
    background = read_config("kdeglobals", "Colors:Window", "BackgroundNormal")
    return variant_of(background) if background else "dark"


def automatic_enabled():
    return read_config("kdeglobals", "KDE", "AutomaticLookAndFeel").lower() == "true"


def daylight():
    """KWin Night Light's day/night state, which drives KDE's automatic switch."""
    try:
        value = run("qdbus6", "org.kde.KWin", "/org/kde/KWin/NightLight",
                    "org.kde.KWin.NightLight.daylight")
    except (OSError, subprocess.SubprocessError):
        return None
    return {"true": True, "false": False}.get(value.lower())


def preflight():
    for tool in TOOLS:
        if not shutil.which(tool):
            raise RuntimeError("Missing required command: " + tool)
    for scheme in SCHEMES:
        if not Path("/usr/share/color-schemes", scheme + ".colors").is_file():
            raise RuntimeError("Missing KDE color scheme: " + scheme)
    loaded = set(run("qdbus6", "org.kde.kded6", "/kded", "org.kde.kded6.loadedModules").split())
    missing = [module for module in KDED_MODULES if module not in loaded]
    if missing:
        raise RuntimeError("KDE appearance services not running: " + ", ".join(missing))


def status(config):
    gtk = {name: ("linked to " + os.readlink(config / name)) if (config / name).is_symlink()
           else "KDE-managed directory" if (config / name).is_dir() else "absent"
           for name in GTK_DIRS}
    return {
        "variant": current_variant(),
        "automatic": automatic_enabled(),
        "global_theme": read_config("kdeglobals", "KDE", "LookAndFeelPackage") or "(default)",
        "wallpaper_accent": read_config("kdeglobals", "General", "accentColorFromWallpaper") == "true",
        "gtk": gtk,
    }


def backup(config, data):
    root = config / "kumios"
    root.mkdir(parents=True, exist_ok=True)
    # mkdtemp is private (0700): appearance config can name personal themes/fonts.
    target = Path(tempfile.mkdtemp(prefix="appearance-backup-", dir=root))
    absent, links = [], {}
    for name in APPEARANCE_CONFIGS:
        path = config / name
        if path.is_file():
            (target / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target / name)
        else:
            absent.append(name)
    for name in GTK_DIRS:
        path = config / name
        if path.is_symlink():
            links[name] = os.readlink(path)
        elif path.is_dir():
            shutil.copytree(path, target / name, symlinks=True)
        else:
            absent.append(name)
    installed = [("plasma/desktoptheme", "KumiOS")] + [("plasma/look-and-feel", p) for p in PACKAGES.values()]
    for parent, name in installed:
        path = data / parent / name
        if path.exists():
            shutil.copytree(path, target / parent / name)
        else:
            absent.append(parent + "/" + name)
    (target / "absent.json").write_text(json.dumps(absent, indent=2) + "\n")
    (target / "gtk-links.json").write_text(json.dumps(links, indent=2) + "\n")
    return target


def install(data):
    # Replace whole directories so files removed from the source (such as the
    # old fixed `colors` palette) do not linger in the installed copy.
    pairs = [(SOURCE / "desktoptheme/KumiOS", data / "plasma/desktoptheme/KumiOS")]
    pairs += [(SOURCE / "lookandfeel" / p, data / "plasma/look-and-feel" / p) for p in PACKAGES.values()]
    for source, destination in pairs:
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)


def adopt_gtk(config):
    """Replace GTK directories that link elsewhere with KDE-managed directories.

    The link target is left untouched. KDE-generated settings are carried over
    so fonts, cursor and decoration choices survive; KDE regenerates them on the
    next color change.
    """
    adopted = []
    for name in GTK_DIRS:
        path = config / name
        if not path.is_symlink():
            continue
        origin = path.resolve()
        path.unlink()
        path.mkdir()
        for file in GTK_KDE_FILES:
            if (origin / file).is_file():
                shutil.copy2(origin / file, path / file)
        (path / "gtk.css").write_text(GTK_CSS)
        adopted.append(name)
    return adopted


def choose(mode):
    """Return (global theme package, keep automatic mode) for the requested mode."""
    if mode in PACKAGES:
        return PACKAGES[mode], False
    if mode == "auto":
        day = daylight()
        variant = current_variant() if day is None else ("light" if day else "dark")
        return PACKAGES[variant], True
    return PACKAGES[current_variant()], automatic_enabled()


def apply(mode):
    write_config("kdeglobals", "General", "accentColorFromWallpaper", "true")
    write_config("kdeglobals", "KDE", "DefaultLightLookAndFeel", PACKAGES["light"])
    write_config("kdeglobals", "KDE", "DefaultDarkLookAndFeel", PACKAGES["dark"])
    package, automatic = choose(mode)
    if automatic:
        write_config("kdeglobals", "KDE", "AutomaticLookAndFeel", "true")
    # Without --keep-auto, KDE turns automatic mode off: a manual choice wins.
    run("plasma-apply-lookandfeel", *(["--keep-auto"] if automatic else []), "--apply", package)
    return package, automatic


def verify(package, automatic):
    problems = []
    if read_config("kdeglobals", "KDE", "LookAndFeelPackage") != package:
        problems.append("global theme is not " + package)
    if read_config("kdeglobals", "General", "accentColorFromWallpaper") != "true":
        problems.append("wallpaper accent is not enabled")
    if automatic_enabled() != automatic:
        problems.append("automatic light/dark is " + ("off" if automatic else "still on"))
    if problems:
        raise RuntimeError("Appearance not confirmed: " + "; ".join(problems))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", choices=MODES, metavar="MODE",
                        help="current (keep light/dark), light, dark or auto; changes the live "
                             "appearance, so obtain session approval first")
    args = parser.parse_args()
    preflight()
    config, data = dirs()
    print("Preflight passed: KDE wallpaper accent, light/dark switching and GTK sync are available.")
    print("Current: " + json.dumps(status(config)))
    if not args.apply:
        print("Read-only check: no files or appearance changed.")
        return
    target = backup(config, data)
    print("Backup: " + str(target), flush=True)
    install(data)
    adopted = adopt_gtk(config)
    if adopted:
        print("GTK settings now managed by KDE: " + ", ".join(adopted) +
              " (previous links recorded in the backup).")
    package, automatic = apply(args.apply)
    verify(package, automatic)
    print("Applied " + package + (" with automatic light/dark switching" if automatic else "") +
          "; accent follows the wallpaper. Wallpaper and panel layout unchanged.")
    print("Applications that cache colors may need reopening. No desktop restart performed.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        detail = getattr(error, "stderr", "") or ""
        print("KumiOS appearance failed: " + str(error) + (": " + detail.strip() if detail else ""),
              file=sys.stderr)
        sys.exit(1)
