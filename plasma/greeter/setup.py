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
import configparser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent
DEST = Path('/etc/greetd')
FILES = ('regreet.toml', 'regreet.css', 'kumios-wallpaper.png', 'config.toml')
# Installed in this order: resources first, greetd's launch command last.
INSTALL_ORDER = ('kumios-wallpaper.png', 'regreet.css', 'regreet.toml', 'config.toml')
# KWin needs a session bus, which the greeter account does not have.
GREETER_COMMAND = ('dbus-run-session -- kwin_wayland --drm --no-lockscreen --no-global-shortcuts'
                   ' --locale1 --exit-with-session /usr/bin/regreet')
COMMAND_TOOLS = ('dbus-run-session', 'kwin_wayland', 'regreet')
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config')
# Breeze Dark, used for any color the KDE configuration does not provide.
DEFAULTS = {
    'accent_color': '#3daee9', 'accent_bg_color': '#3daee9',
    'accent_fg_color': '#fcfcfc', 'window_bg_color': '#202326',
    'window_fg_color': '#fcfcfc', 'view_bg_color': '#141618',
    'destructive_bg_color': '#da4453', 'destructive_fg_color': '#fcfcfc',
}
# Theme color -> KDE (group, key). The accent comes from General/AccentColor
# (KDE's wallpaper accent) when set, otherwise from the selection color.
KDE_COLORS = {
    'accent_bg_color': ('Colors:Selection', 'BackgroundNormal'),
    'accent_fg_color': ('Colors:Selection', 'ForegroundNormal'),
    'window_bg_color': ('Colors:Window', 'BackgroundNormal'),
    'window_fg_color': ('Colors:Window', 'ForegroundNormal'),
    'view_bg_color': ('Colors:View', 'BackgroundNormal'),
    'destructive_bg_color': ('Colors:View', 'ForegroundNegative'),
    'destructive_fg_color': ('Colors:Selection', 'ForegroundNormal'),
}
IMAGE_SUFFIXES = ('.png', '.jpg', '.jpeg', '.webp')


def run(*args):
    return subprocess.run([str(a) for a in args], check=True)


def read_kde(*paths):
    """KDE ini files, later paths filling only keys earlier ones lack."""
    merged = {}
    for path in paths:
        parser = configparser.RawConfigParser(strict=False, interpolation=None)
        parser.optionxform = str
        try:
            parser.read(path, encoding='utf-8')
        except (configparser.Error, UnicodeDecodeError):
            continue
        for section in parser.sections():
            for key, value in parser[section].items():
                merged.setdefault((section, key), value)
    return merged


def hex_color(value):
    parts = value.split(',') if value else []
    if len(parts) < 3 or not all(p.strip().isdigit() for p in parts[:3]):
        return None
    return '#' + ''.join(f'{min(int(p), 255):02x}' for p in parts[:3])


def kde_colors(path):
    """Theme colors from a kdeglobals (or *.colors scheme) file; Breeze Dark fallback."""
    kde = read_kde(path, path.parent / 'kdedefaults' / path.name)
    colors = DEFAULTS.copy()
    for name, key in KDE_COLORS.items():
        colors[name] = hex_color(kde.get(key)) or colors[name]
    colors['accent_bg_color'] = hex_color(kde.get(('General', 'AccentColor'))) or colors['accent_bg_color']
    colors['accent_color'] = colors['accent_bg_color']
    return colors


def is_dark(colors):
    red, green, blue = (int(colors['window_bg_color'][i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue < 128


def palette(colors):
    return '\n'.join(f'@define-color {k} {v};' for k, v in colors.items()) + '\n'


def package_image(directory, dark):
    """Largest image of a KDE wallpaper package, preferring images_dark when dark."""
    folders = (['images_dark'] if dark else []) + ['images']
    for folder in folders:
        candidates = [p for p in (directory / 'contents' / folder).glob('*') if p.suffix.lower() in IMAGE_SUFFIXES]
        def pixels(p):
            size = re.match(r'(\d+)x(\d+)', p.stem)
            return int(size[1]) * int(size[2]) if size else 0
        if candidates:
            return max(candidates, key=pixels)
    return None


def plasma_wallpaper(appletsrc, dark):
    """The image Plasma's desktop shows, from its containment config."""
    kde = read_kde(appletsrc)
    images = [value for (section, key), value in sorted(kde.items())
              if key == 'Image' and section.endswith('][Wallpaper][org.kde.image][General')]
    for value in images or ['/usr/share/wallpapers/Next']:
        path = Path(unquote(urlparse(value).path)) if value.startswith('file:') else Path(value).expanduser()
        if path.is_dir():
            path = package_image(path, dark)
        if path and path.is_file():
            return path
    return None


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
    print('If the login screen does not appear, switch to a text console (Ctrl+Alt+F2), log in there and run:')
    print(f'Rollback: python3 plasma/greeter/setup.py restore {backup}')


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
