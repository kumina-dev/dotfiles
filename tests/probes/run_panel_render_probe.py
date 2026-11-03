#!/usr/bin/env python3
"""Render the KumiOS panel SVG offscreen under Breeze Light and Breeze Dark (KUM-20).

Proves KDE's SVG engine recolors the panel from the active color scheme while
keeping its translucency. Each run uses a private D-Bus session and temporary
XDG directories, so the live desktop's appearance is never read or changed.
"""
from pathlib import Path
import configparser
import os
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SVG = ROOT / 'plasma/desktoptheme/KumiOS/widgets/panel-background.svg'
SCHEMES = Path('/usr/share/color-schemes')
BACKDROP = (255, 0, 255)   # magenta: shows whether the SVG drew and how opaque it is
OPACITY = 0.78             # fill-opacity of the generic "center" element
TOLERANCE = 3

QML = '''import QtQuick
import QtTest
import org.kde.ksvg as KSvg

TestCase {
    name: "PanelRender"
    width: 64; height: 64; visible: true; when: windowShown
    Rectangle { id: backdrop; anchors.fill: parent; color: "#ff00ff"
        KSvg.SvgItem { width: 40; height: 40; imagePath: "%s"; elementId: "center" }
    }
    function test_render() {
        wait(300)
        var c = grabImage(backdrop).pixel(20, 20)
        console.log("PIXEL", Math.round(c.r * 255), Math.round(c.g * 255), Math.round(c.b * 255))
    }
}
'''


def window_background(scheme):
    colors = configparser.RawConfigParser(strict=False)
    colors.read(SCHEMES / f'{scheme}.colors')
    return tuple(int(v) for v in colors['Colors:Window']['BackgroundNormal'].split(','))


def render(scheme, test_file):
    with tempfile.TemporaryDirectory(prefix='kumios-panel-render-') as home:
        config = Path(home, 'config')
        config.mkdir()
        kdeglobals = (SCHEMES / f'{scheme}.colors').read_text()
        (config / 'kdeglobals').write_text(f'{kdeglobals}\n[General]\nColorScheme={scheme}\n')
        env = {
            'PATH': os.environ['PATH'], 'HOME': home, 'XDG_CONFIG_HOME': str(config),
            'XDG_CACHE_HOME': f'{home}/cache', 'XDG_RUNTIME_DIR': home,
            'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software',
            'QT_QPA_PLATFORMTHEME': 'kde', 'KDE_FULL_SESSION': 'true', 'XDG_CURRENT_DESKTOP': 'KDE',
        }
        result = subprocess.run(
            ['dbus-run-session', '--', '/usr/lib/qt6/bin/qmltestrunner', '-input', str(test_file)],
            env=env, capture_output=True, text=True, timeout=60)
    match = re.search(r'PIXEL (\d+) (\d+) (\d+)', result.stdout + result.stderr)
    if not match:
        raise SystemExit(f'{scheme}: no pixel reported\n{result.stdout}{result.stderr}')
    return tuple(int(v) for v in match.groups())


def main():
    failures = 0
    with tempfile.TemporaryDirectory(prefix='kumios-panel-qml-') as directory:
        test_file = Path(directory, 'tst_PanelRender.qml')
        test_file.write_text(QML % SVG)
        for scheme in ('BreezeLight', 'BreezeDark'):
            pixel = render(scheme, test_file)
            # Undo the blend over the backdrop to recover the fill color.
            fill = tuple(round((p - (1 - OPACITY) * b) / OPACITY) for p, b in zip(pixel, BACKDROP))
            expected = window_background(scheme)
            ok = all(abs(f - e) <= TOLERANCE for f, e in zip(fill, expected))
            failures += not ok
            print(f'{"PASS" if ok else "FAIL"} {scheme}: rendered {pixel} -> fill {fill}, '
                  f'expected window background {expected} at {OPACITY:.0%} opacity')
    print(f'Totals: {2 - failures} passed, {failures} failed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
