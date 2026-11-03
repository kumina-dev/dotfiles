#!/usr/bin/env python3
"""A broken KDE audio module must not take down the Control Center (KUM-23).

Copies the production widget into a temporary directory, replaces NativeAudio.qml
with one that imports a module that does not exist (as a KDE release that removed
or renamed the private audio module would), and constructs the real popup
offscreen. As a control, the same break is applied to a copy whose main.qml
instantiates NativeAudio directly, as before KUM-23, which must fail to load.
No installed files, devices or services are touched.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'plasma/plasmoids/org.kumios.controlcenter/contents/ui'
BROKEN = '''import QtQuick
import org.kde.plasma.private.volume.removedInFutureRelease as PulseAudio
QtObject { property var output: PulseAudio.Server.defaultSink }
'''
TEST = '''import QtQuick
import QtQuick.Layouts
import QtTest

TestCase {
    id: test
    name: "AudioIsolation"
    function test_controlCenterLoadsWithBrokenAudioModule() {
        const component = Qt.createComponent(Qt.resolvedUrl("ui/main.qml"))
        compare(component.status, Component.Ready, component.errorString())
        const widget = createTemporaryObject(component, test)
        verify(widget !== null)
        verify(!widget.probeAudio.compatible, "audio must report incompatibility")
        verify(widget.probeAudio.incompatibility.includes("could not be loaded"))
        verify(!widget.audioAvailable)
        const popup = createTemporaryObject(widget.fullRepresentation, test, {width: 320})
        verify(popup !== null, "popup must still construct")
        wait(50)
        verify(popup.Layout.preferredHeight > 0)
        // Non-audio controls are still present and usable.
        verify(typeof widget.toggleWifi === "function")
        verify(typeof widget.toggleBluetooth === "function")
        verify(typeof widget.setBrightness === "function")
        verify(widget.probeAppearance !== null)
        console.log("ISOLATED: " + widget.probeAudio.unavailableMessage)
    }
}
'''


def run(ui_transform):
    with tempfile.TemporaryDirectory(prefix='kumios-audio-isolation-') as directory:
        target = Path(directory)
        shutil.copytree(UI, target / 'ui')
        (target / 'ui/NativeAudio.qml').write_text(BROKEN)
        main = target / 'ui/main.qml'
        source = main.read_text()
        anchor = '    id: root\n'
        if source.count(anchor) != 1:
            raise SystemExit('Instrumentation anchor must be unique')
        source = source.replace(anchor, anchor + '    property alias probeAudio: audio\n'
                                '    property alias probeAppearance: appearance\n', 1)
        main.write_text(ui_transform(source))
        (target / 'tst_AudioIsolation.qml').write_text(TEST)
        result = subprocess.run(
            ['/usr/lib/qt6/bin/qmltestrunner', '-input', str(target / 'tst_AudioIsolation.qml'), '-o', '-,txt'],
            env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software'},
            capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout + result.stderr


def direct_import(source):
    """Reproduce the pre-KUM-23 structure: main.qml instantiates NativeAudio directly."""
    old = '    AudioBackend { id: audio }\n'
    if source.count(old) != 1:
        raise SystemExit('AudioBackend anchor must be unique')
    return source.replace(old, '    NativeAudio { id: audio }\n')


def main():
    code, output = run(lambda source: source)
    isolated = code == 0
    print(('PASS' if isolated else 'FAIL') + ': Control Center loads with a broken audio module')
    for line in output.splitlines():
        if 'ISOLATED:' in line or line.startswith(('FAIL', 'Totals')) or 'Actual' in line:
            print('  ' + line.split('qml: ')[-1].strip())
    control_code, control_output = run(direct_import)
    control = control_code != 0 and 'NativeAudio' in control_output
    print(('PASS' if control else 'FAIL') + ': control — direct NativeAudio import fails to load the Control Center')
    failures = (not isolated) + (not control)
    print(f'Totals: {2 - failures} passed, {failures} failed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
