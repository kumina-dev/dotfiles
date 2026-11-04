#!/usr/bin/env python3
"""KumiOS lock screen: the desktop's wallpaper, kept in sync.

KDE's lock screen (kscreenlocker) already follows Light/Dark and the accent
through the KumiOS Plasma style and color scheme, but has its own wallpaper
setting. This points it at Plasma's current desktop wallpaper.

  lockscreen.py                 read-only status
  lockscreen.py sync            update the lock screen wallpaper if it changed
  lockscreen.py install-sync    back up kscreenlockerrc, sync now, and keep in sync
                                with a user systemd path unit
  lockscreen.py remove-sync     stop and remove that unit (wallpaper setting stays)

Never locks the session and needs no root.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from desktop_appearance import APPLETSRC, CONFIG, current, read_kde  # noqa: E402

LOCKRC = 'kscreenlockerrc'
WALLPAPER_GROUPS = ('Greeter', 'Wallpaper', 'org.kde.image', 'General')
UNIT = 'kumios-lockscreen-sync'
UNIT_DIR = CONFIG / 'systemd' / 'user'


def run(*args, check=True):
    return subprocess.run([str(a) for a in args], text=True, capture_output=True, check=check, timeout=60)


def lock_wallpaper(config=None):
    """The image URL the lock screen is configured with, or None."""
    section = ']['.join(WALLPAPER_GROUPS)
    return read_kde(Path(config or CONFIG) / LOCKRC).get((section, 'Image'))


def sync(config=None, write=None):
    """Point the lock screen at the desktop wallpaper. Returns (changed, path).

    Written as a plain absolute path, the same form Plasma's desktop config uses.
    """
    config = Path(config or CONFIG)
    _, _, wallpaper = current(config)
    if wallpaper is None:
        raise RuntimeError("Plasma's desktop wallpaper could not be found")
    url = str(wallpaper.resolve())
    if lock_wallpaper(config) == url:
        return False, url
    write = write or (lambda *args: run('kwriteconfig6', '--file', str(config / LOCKRC), *args))
    write('--group', 'Greeter', '--key', 'WallpaperPlugin', 'org.kde.image')
    groups = [arg for group in WALLPAPER_GROUPS for arg in ('--group', group)]
    write(*groups, '--key', 'Image', url)
    return True, url


def units(script=None, config=None):
    """systemd user units: re-sync when the desktop wallpaper or color scheme changes."""
    script = Path(script or Path(__file__).resolve())
    config = Path(config or CONFIG)
    path_unit = f'''[Unit]
Description=Keep the KumiOS lock screen wallpaper in sync with the desktop

[Path]
PathChanged={config / APPLETSRC}
PathChanged={config / 'kdeglobals'}

[Install]
WantedBy=default.target
'''
    service_unit = f'''[Unit]
Description=Sync the KumiOS lock screen wallpaper with the desktop

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {script} sync
'''
    return {f'{UNIT}.path': path_unit, f'{UNIT}.service': service_unit}


def backup(config=None):
    config = Path(config or CONFIG)
    root = config / 'kumios'
    root.mkdir(parents=True, exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix='lockscreen-backup-', dir=root))
    source = config / LOCKRC
    if source.is_file():
        shutil.copy2(source, target / LOCKRC)
    else:
        (target / (LOCKRC + '.absent')).touch()
    return target


def install_sync(config=None, systemctl=None):
    config = Path(config or CONFIG)
    systemctl = systemctl or (lambda *args: run('systemctl', '--user', *args))
    target = backup(config)
    changed, url = sync(config)
    unit_dir = config / 'systemd' / 'user'
    unit_dir.mkdir(parents=True, exist_ok=True)
    for name, text in units(config=config).items():
        (unit_dir / name).write_text(text)
    systemctl('daemon-reload')
    systemctl('enable', '--now', f'{UNIT}.path')
    return target, changed, url


def remove_sync(config=None, systemctl=None):
    config = Path(config or CONFIG)
    systemctl = systemctl or (lambda *args: run('systemctl', '--user', *args, check=False))
    systemctl('disable', '--now', f'{UNIT}.path')
    for name in units(config=config):
        (config / 'systemd' / 'user' / name).unlink(missing_ok=True)
    systemctl('daemon-reload')


def status(config=None):
    config = Path(config or CONFIG)
    _, dark, wallpaper = current(config)
    desktop = str(wallpaper.resolve()) if wallpaper else None
    active = run('systemctl', '--user', 'is-active', f'{UNIT}.path', check=False).stdout.strip()
    return {'desktop_wallpaper': desktop, 'lock_screen_wallpaper': lock_wallpaper(config),
            'in_sync': desktop is not None and desktop == lock_wallpaper(config),
            'dark': dark, 'sync_unit': active or 'unknown'}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', nargs='?', choices=('sync', 'install-sync', 'remove-sync'))
    args = parser.parse_args()
    home = str(Path.home())
    if args.action is None:
        for key, value in status().items():
            print(f'{key}: {str(value).replace(home, "~")}')
        print('Read-only check: nothing changed.')
    elif args.action == 'sync':
        changed, url = sync()
        print(('Lock screen wallpaper set to ' if changed else 'Lock screen wallpaper already ') + url.replace(home, '~'))
    elif args.action == 'install-sync':
        target, changed, url = install_sync()
        print('Backup: ' + str(target).replace(home, '~'))
        print('Lock screen wallpaper: ' + url.replace(home, '~') + (' (updated)' if changed else ' (unchanged)'))
        print(f'Sync enabled: {UNIT}.path re-syncs when the desktop wallpaper or color scheme changes.')
    else:
        remove_sync()
        print(f'Sync disabled and {UNIT} units removed; the current lock screen wallpaper is kept.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print('KumiOS lock screen failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
