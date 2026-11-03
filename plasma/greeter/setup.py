#!/usr/bin/env python3
"""Preview or install a self-contained ReGreet login theme snapshot.

Colors come from KDE: the active color scheme and the wallpaper accent in
kdeglobals. The wallpaper defaults to Plasma's current desktop wallpaper, and
dark mode follows the current KDE Light/Dark variant. The snapshot is static:
rerun install after changing the wallpaper or Light/Dark to update the login screen.

Install also makes greetd start ReGreet on KWin (as SDDM runs its Wayland greeter)
by changing only the `command` in `[default_session]` of greetd's config.toml.
greetd and PAM authentication are not changed.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from desktop_appearance import (  # noqa: E402  (shared with the lock screen and sync)
    CONFIG, DEFAULTS, KDE_COLORS, IMAGE_SUFFIXES, hex_color, is_dark, kde_colors,
    package_image, plasma_wallpaper, read_kde)
DEST = Path('/etc/greetd')
FILES = ('regreet.toml', 'regreet.css', 'kumios-wallpaper.png', 'config.toml')
# Installed in this order: resources first, greetd's launch command last.
INSTALL_ORDER = ('kumios-wallpaper.png', 'regreet.css', 'regreet.toml', 'config.toml')
# KWin needs a session bus, which the greeter account does not have.
GREETER_COMMAND = ('dbus-run-session -- kwin_wayland --drm --no-lockscreen --no-global-shortcuts'
                   ' --locale1 --exit-with-session /usr/bin/regreet')
COMMAND_TOOLS = ('dbus-run-session', 'kwin_wayland', 'regreet')

def run(*args):
    return subprocess.run([str(a) for a in args], check=True)


def palette(colors):
    return '\n'.join(f'@define-color {k} {v};' for k, v in colors.items()) + '\n'


def with_greeter_command(text, command=GREETER_COMMAND):
    """greetd config.toml text with only [default_session] command replaced."""
    lines = text.splitlines(keepends=True)
    section, replaced = None, False
    for index, line in enumerate(lines):
        header = re.match(r'\s*\[([^\]]+)\]\s*(#.*)?$', line)
        if header:
            section = header[1].strip()
        elif section == 'default_session' and re.match(r'\s*command\s*=', line):
            if replaced:
                raise ValueError('greetd config.toml has more than one default_session command')
            lines[index] = f'command = {json.dumps(command)}\n'
            replaced = True
    if not replaced:
        raise ValueError('greetd config.toml has no [default_session] command; not changing it')
    return ''.join(lines)


def prepare(stage, wallpaper, colors, installed=False, greetd_config=None):
    """Stage the theme. `colors` is a kdeglobals or *.colors file; `wallpaper` an image
    or None to use Plasma's current desktop wallpaper."""
    theme = kde_colors(colors)
    dark = is_dark(theme)
    if wallpaper is None:
        wallpaper = plasma_wallpaper(CONFIG / 'plasma-org.kde.plasma.desktop-appletsrc', dark)
        if wallpaper is None:
            raise ValueError("Plasma's wallpaper could not be found. Use --wallpaper PATH.")
    if not wallpaper.is_file():
        raise ValueError(f'Wallpaper not found: {wallpaper}. Use --wallpaper PATH.')
    shutil.copyfile(wallpaper, stage / FILES[2])
    background = (DEST if installed else stage) / FILES[2]
    config = f'''skip_selection = false

[background]
path = {json.dumps(str(background))}
fit = "Cover"

[GTK]
application_prefer_dark_theme = {"true" if dark else "false"}
font_name = "Noto Sans 12"
theme_name = "Adwaita"
icon_theme_name = "Adwaita"
cursor_theme_name = "Adwaita"

[appearance]
greeting_msg = "Welcome to KumiOS"

[widget.clock]
format = "%a %d %b  •  %H:%M"
resolution = "1s"

[commands]
reboot = ["systemctl", "reboot"]
poweroff = ["systemctl", "poweroff"]
'''
    (stage / FILES[0]).write_text(config, encoding='utf-8')
    (stage / FILES[1]).write_text(
        palette(theme) + (HERE / 'style.css').read_text(encoding='utf-8'),
        encoding='utf-8',
    )
    source = greetd_config or DEST / FILES[3]
    (stage / FILES[3]).write_text(with_greeter_command(source.read_text(encoding='utf-8')), encoding='utf-8')
    return theme, wallpaper


def sudo(*args):
    return run('sudo', *args)


def restore(backup):
    backup = backup.resolve()
    if backup.parent != DEST or not backup.name.startswith('kumios-backup.'):
        raise ValueError('Use the /etc/greetd/kumios-backup.* directory printed during installation.')
    # Verify the whole backup before changing anything.
    for name in FILES:
        exists = subprocess.run(['sudo', 'test', '-f', str(backup / name)]).returncode == 0
        if not exists:
            sudo('test', '-f', backup / (name + '.absent'))
    for name in FILES:
        absent = subprocess.run(['sudo', 'test', '-f', str(backup / (name + '.absent'))]).returncode == 0
        if absent:
            sudo('rm', '-f', DEST / name)
        else:
            sudo('cp', '-a', '--remove-destination', backup / name, DEST / name)
    print('Previous theme restored. It will be used the next time the greeter starts.')


def install(stage):
    missing = [tool for tool in COMMAND_TOOLS if not shutil.which(tool)]
    if missing:
        raise ValueError('Greeter command needs ' + ', '.join(missing) + '; installation not started.')
    sudo('test', '-f', DEST / 'config.toml')
    # ReGreet must be able to traverse this existing system configuration directory.
    sudo('-u', 'greeter', 'test', '-x', DEST)
    backup = Path(subprocess.check_output(
        ['sudo', 'mktemp', '-d', str(DEST / 'kumios-backup.XXXXXX')], text=True,
    ).strip())
    for name in FILES:
        target = DEST / name
        # Do not follow a managed-file symlink when replacing the theme.
        if target.is_symlink():
            raise ValueError(f'{target} is a symlink; installation stopped before changing theme files.')
        if target.exists():
            sudo('cp', '-a', target, backup / name)
        else:
            sudo('touch', backup / (name + '.absent'))
    print(f'Backup: {backup}', flush=True)
    try:
        # Config goes last, after both referenced resources are installed.
        for name in INSTALL_ORDER:
            sudo('install', '-o', 'root', '-g', 'root', '-m', '644', stage / name, DEST / name)
            sudo('-u', 'greeter', 'test', '-r', DEST / name)
    except subprocess.CalledProcessError:
        restore(backup)
        raise
    print('Installed. greetd will start ReGreet on KWin with this theme at the next logout or reboot.')
    print('Keep the backup path. If the login screen does not appear, switch to a text console')
    print('(Ctrl+Alt+F2), log in, and from the repository run:')
    print(f'  python3 plasma/greeter/setup.py restore {backup}')
    print('  sudo systemctl restart greetd')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preview', 'install', 'restore'))
    parser.add_argument('backup', nargs='?', type=Path)
    parser.add_argument('--wallpaper', type=Path, default=None,
                        help="image to show (default: Plasma's current desktop wallpaper)")
    parser.add_argument('--colors', type=Path, default=CONFIG / 'kdeglobals',
                        help='KDE color source: kdeglobals or a *.colors scheme (default: your kdeglobals)')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run as your normal desktop user; install/restore request sudo when needed.')
    try:
        if args.action == 'restore':
            if args.backup is None:
                parser.error('restore needs the backup directory printed during installation')
            restore(args.backup)
            return
        if args.backup is not None:
            parser.error('backup is only used with restore')
        with tempfile.TemporaryDirectory(prefix='kumios-greeter-') as directory:
            stage = Path(directory)
            wallpaper = args.wallpaper.expanduser() if args.wallpaper else None
            theme, used = prepare(stage, wallpaper, args.colors.expanduser(), args.action == 'install')
            print(f"Colors from {args.colors.name}: accent {theme['accent_bg_color']}, "
                  f"{'dark' if is_dark(theme) else 'light'}; wallpaper {used.name}", flush=True)
            print('greetd command after install: ' + GREETER_COMMAND, flush=True)
            if args.action == 'preview':
                run('regreet', '--demo', '--config', stage / FILES[0],
                    '--style', stage / FILES[1], '--logs', stage / 'preview.log')
            else:
                install(stage)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Greeter setup failed: {error}\n')


if __name__ == '__main__':
    main()
