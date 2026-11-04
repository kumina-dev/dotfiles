"""Desktop appearance as KDE records it: colors, accent, Light/Dark and wallpaper.

Shared by the login greeter, the lock screen and the login-screen sync so all
three resolve the same wallpaper and colors. Reads KDE configuration only.
"""
import configparser
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlparse

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
APPLETSRC = 'plasma-org.kde.plasma.desktop-appletsrc'


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


def current(config=None):
    """(colors, dark, wallpaper path or None) for the desktop's current appearance."""
    config = Path(config) if config else CONFIG
    colors = kde_colors(config / 'kdeglobals')
    dark = is_dark(colors)
    return colors, dark, plasma_wallpaper(config / APPLETSRC, dark)
