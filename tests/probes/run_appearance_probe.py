#!/usr/bin/env python3
"""Run plasma/appearance.py's real KDE steps in isolation (KUM-21).

Re-executes itself inside a private D-Bus session with temporary HOME/XDG
directories, so the live desktop, its config and its D-Bus services are never
read or changed. Uses the real plasma-apply-lookandfeel and kwriteconfig6.
Preflight is skipped: the private bus has no kded services.
"""
from pathlib import Path
import importlib.util
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
MARKER = 'KUMIOS_APPEARANCE_PROBE_ISOLATED'
ACCENT = '200,100,50'
WALLPAPER = '[Containments][1][Wallpaper][org.kde.image][General]\nImage=file:///kumios-probe.png\n'


def outer():
    with tempfile.TemporaryDirectory(prefix='kumios-appearance-probe-') as home:
        env = {'PATH': os.environ['PATH'], 'HOME': home, MARKER: '1',
               'XDG_CONFIG_HOME': f'{home}/config', 'XDG_DATA_HOME': f'{home}/data',
               'XDG_CACHE_HOME': f'{home}/cache', 'XDG_STATE_HOME': f'{home}/state',
               'XDG_RUNTIME_DIR': home, 'QT_QPA_PLATFORM': 'offscreen'}
        # start_new_session + timeout: helpers the private bus activates are
        # cleaned up with it rather than keeping the probe waiting.
        try:
            result = subprocess.run(['dbus-run-session', '--', sys.executable, '-I', __file__],
                                    env=env, timeout=240, start_new_session=True)
        except subprocess.TimeoutExpired:
            print('FAIL: probe timed out')
            return 1
        return result.returncode


def inner():
    home = Path(os.environ['HOME'])
    config, data = Path(os.environ['XDG_CONFIG_HOME']), Path(os.environ['XDG_DATA_HOME'])
    config.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location('kumios_appearance', ROOT / 'plasma/appearance.py')
    appearance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(appearance)

    # Starting point resembling v0.2.0: BreezeDark, KumiOS style, an accent already
    # computed from the wallpaper, and GTK linked into a legacy package.
    scheme = Path('/usr/share/color-schemes/BreezeDark.colors').read_text()
    (config / 'kdeglobals').write_text(f'{scheme}\n[General]\nColorScheme=BreezeDark\nAccentColor={ACCENT}\n')
    (config / 'plasmarc').write_text('[Theme]\nname=KumiOS\n')
    applets = config / 'plasma-org.kde.plasma.desktop-appletsrc'
    applets.write_text(WALLPAPER)
    legacy = home / 'dotfiles/gtk/.config/gtk-3.0'
    legacy.mkdir(parents=True)
    (legacy / 'gtk.css').write_text('@import url("matugen.css");\n')
    (legacy / 'settings.ini').write_text('[Settings]\ngtk-theme-name=Breeze-Dark\n')
    os.symlink(legacy, config / 'gtk-3.0')

    failures = []

    def check(label, condition, detail=''):
        print(('PASS ' if condition else 'FAIL ') + label + (f' ({detail})' if detail else ''))
        if not condition:
            failures.append(label)

    backup = appearance.backup(config, data)
    appearance.install(data)
    check('backup recorded the GTK link', str(legacy) in (backup / 'gtk-links.json').read_text())
    check('GTK handed to KDE', appearance.adopt_gtk(config) == ['gtk-3.0'] and
          not (config / 'gtk-3.0').is_symlink())

    for mode, variant, automatic in (('light', 'light', False), ('dark', 'dark', False),
                                     ('auto', 'dark', True), ('current', 'dark', True),
                                     ('light', 'light', False), ('current', 'light', False)):
        package, kept_auto = appearance.apply(mode)
        try:
            appearance.verify(package, kept_auto)
            verified = ''
        except RuntimeError as error:
            verified = str(error)
        background = appearance.read_config('kdeglobals', 'Colors:Window', 'BackgroundNormal')
        label = f'--apply {mode}'
        check(f'{label}: verified', not verified, verified or package)
        check(f'{label}: {variant} colors', appearance.variant_of(background) == variant, background)
        check(f'{label}: automatic {"on" if automatic else "off"}',
              appearance.automatic_enabled() == automatic)
        check(f'{label}: accent kept',
              appearance.read_config('kdeglobals', 'General', 'AccentColor') == ACCENT)
        check(f'{label}: wallpaper/layout untouched', applets.read_text() == WALLPAPER)
        check(f'{label}: KumiOS Plasma style kept', 'name=KumiOS' in
              ''.join(p.read_text() for p in (config / 'plasmarc', config / 'kdedefaults/plasmarc') if p.exists()))

    check('legacy GTK package untouched', (legacy / 'gtk.css').read_text() == '@import url("matugen.css");\n')
    print(f'Totals: {"0 failed" if not failures else str(len(failures)) + " failed"}')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(inner() if os.environ.get(MARKER) else outer())
