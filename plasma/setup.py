#!/usr/bin/env python3
"""Read-only preflight by default; explicit, backed-up live layout application."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parent
NATIVE = ["org.kde.plasma.kickerdash", "org.kde.plasma.appmenu",
          "org.kde.plasma.panelspacer", "org.kde.plasma.digitalclock",
          "org.kde.plasma.notifications", "org.kde.plasma.icontasks"]
CONFIGS = ["plasma-org.kde.plasma.desktop-appletsrc", "plasmashellrc",
           "kglobalshortcutsrc"]
INVENTORY = '''print(JSON.stringify({types:knownWidgetTypes,panels:panels().map(p=>({
    id:p.id,location:p.location,screen:p.screen,widgets:p.widgets().map(w=>({
    id:w.id,type:w.type,index:w.index,shortcut:w.globalShortcut}))}))}));'''


def run(*args):
    return subprocess.run(args, text=True, capture_output=True, check=True).stdout.strip()


def plasma(method, *args):
    return run("qdbus6", "org.kde.plasmashell", "/PlasmaShell",
               "org.kde.PlasmaShell." + method, *args)


def preflight():
    for tool in ("qdbus6", "kcmshell6"):
        if not shutil.which(tool):
            raise RuntimeError("Missing required command: " + tool)
    inventory = json.loads(plasma("evaluateScript", INVENTORY))
    missing = set(NATIVE) - set(inventory["types"])
    if missing:
        raise RuntimeError("Missing KDE widgets: " + ", ".join(sorted(missing)))
    modules = {line.split()[0] for line in run("kcmshell6", "--list").splitlines() if line.split()}
    for module in ("kcm_bluetooth", "kcm_pulseaudio", "kcm_about-distro"):
        if module not in modules:
            raise RuntimeError("Missing KDE settings module: " + module)
    # The current presentation still needs this existing service; don't silently
    # provision dependencies or enable services as a side effect of layout setup.
    run("systemctl", "--user", "is-active", "kumi-audio.service")
    for location, kind in (("top", "org.kumios.systemmenu"),
                           ("bottom", "org.kde.plasma.icontasks")):
        matches = [p for p in inventory["panels"] if p["location"] == location and
                   any(w["type"] == kind for w in p["widgets"])]
        if len(matches) > 1:
            raise RuntimeError("Multiple matching " + location + " panels; review before applying")
        for panel in matches:
            types = [w["type"] for w in panel["widgets"]]
            for kind in NATIVE + [p.name for p in (SOURCE / "plasmoids").iterdir()]:
                if types.count(kind) > 1:
                    raise RuntimeError("Duplicate widget requires review: " + kind)
    return inventory


def backup(config, data, inventory):
    root = config / "kumios"
    root.mkdir(parents=True, exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix="layout-backup-", dir=root))
    # mkdtemp is private: desktop configuration may include personal app names.
    (target / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    (target / "layout.js").write_text(plasma("dumpCurrentLayoutJS") + "\n")
    absent = []
    for name in CONFIGS:
        path = config / name
        if path.exists():
            shutil.copy2(path, target / name)
        else:
            absent.append(name)
    for source in (SOURCE / "plasmoids").iterdir():
        installed = data / "plasma/plasmoids" / source.name
        if installed.exists():
            shutil.copytree(installed, target / "plasmoids" / source.name)
        else:
            absent.append("plasmoids/" + source.name)
    (target / "absent.json").write_text(json.dumps(absent, indent=2) + "\n")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="read-only preflight (default)")
    mode.add_argument("--apply-layout", action="store_true",
                      help="install widgets and change live panels; obtain session approval first")
    args = parser.parse_args()
    inventory = preflight()
    print("Preflight passed: KDE dashboard, settings modules and KumiOS audio are available.")
    print("Top bar + centered dock; existing panels and dock pins will be retained.")
    if not args.apply_layout:
        print("Read-only check: no files or panels changed.")
        return
    config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    target = backup(config, data, inventory)
    print("Backup: " + str(target), flush=True)
    for source in (SOURCE / "plasmoids").iterdir():
        shutil.copytree(source, data / "plasma/plasmoids" / source.name, dirs_exist_ok=True)
    result = plasma("evaluateScript", (SOURCE / "shell/layout-v2.js").read_text())
    if "KumiOS layout reconciled;" not in result:
        raise RuntimeError("Layout did not report success: " + result +
                           "; preserve the printed backup for recovery")
    print(result)
    print("No desktop restart performed. Existing widget code may stay cached until the next login.")
    print("Verify the desktop before tagging a release; see plasma/README.md for recovery.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print("KumiOS setup failed: " + str(error), file=sys.stderr)
        sys.exit(1)
