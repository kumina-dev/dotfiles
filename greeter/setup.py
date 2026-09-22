#!/usr/bin/env python3
"""Preview or install a self-contained ReGreet theme snapshot."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
DEST = Path('/etc/greetd')
FILES = ('regreet.toml', 'regreet.css', 'kumios-wallpaper.png')
DEFAULTS = {
    'accent_color': '#b9c3ff', 'accent_bg_color': '#b9c3ff',
    'accent_fg_color': '#222b60', 'window_bg_color': '#121318',
    'window_fg_color': '#e3e1e9', 'view_bg_color': '#1e1f25',
    'destructive_bg_color': '#ffb4ab', 'destructive_fg_color': '#690005',
}


def run(*args):
    return subprocess.run([str(a) for a in args], check=True)


def palette(path):
    colors = DEFAULTS.copy()
    if path.is_file():
        # Export color values only; never import CSS or private home paths.
        for name, value in re.findall(
            r'@define-color\s+(\w+)\s+(#[0-9a-fA-F]{6})\s*;',
            path.read_text(encoding='utf-8'),
        ):
            if name in colors:
                colors[name] = value
    return '\n'.join(f'@define-color {k} {v};' for k, v in colors.items()) + '\n'


def prepare(stage, wallpaper, colors, installed=False):
    if not wallpaper.is_file():
        raise ValueError(f'Wallpaper not found: {wallpaper}. Use --wallpaper PATH.')
    shutil.copyfile(wallpaper, stage / FILES[2])
    background = (DEST if installed else stage) / FILES[2]
    config = f'''skip_selection = false

[background]
path = {json.dumps(str(background))}
fit = "Cover"

[GTK]
application_prefer_dark_theme = true
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
        palette(colors) + (HERE / 'style.css').read_text(encoding='utf-8'),
        encoding='utf-8',
    )


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
        for name in (FILES[2], FILES[1], FILES[0]):
            sudo('install', '-o', 'root', '-g', 'root', '-m', '644', stage / name, DEST / name)
            sudo('-u', 'greeter', 'test', '-r', DEST / name)
    except subprocess.CalledProcessError:
        restore(backup)
        raise
    print('Installed. The theme will appear on your next normal logout or reboot.')
    print(f'Rollback: python3 greeter/setup.py restore {backup}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preview', 'install', 'restore'))
    parser.add_argument('backup', nargs='?', type=Path)
    parser.add_argument('--wallpaper', type=Path, default=Path.home() / 'Pictures/Wallpapers/main.png')
    parser.add_argument('--colors', type=Path, default=Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'gtk-4.0/matugen.css')
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
            prepare(stage, args.wallpaper.expanduser(), args.colors.expanduser(), args.action == 'install')
            if args.action == 'preview':
                run('regreet', '--demo', '--config', stage / FILES[0],
                    '--style', stage / FILES[1], '--logs', stage / 'preview.log')
            else:
                install(stage)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Greeter setup failed: {error}\n')


if __name__ == '__main__':
    main()
