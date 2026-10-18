#!/usr/bin/env python3
"""Offscreen production-popup fault injection; never installs or changes live devices."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='kumios-control-faults-') as directory:
    target = Path(directory)
    shutil.copytree(ROOT / 'plasma/plasmoids/org.kumios.controlcenter/contents/ui', target / 'ui')
    main = target / 'ui/main.qml'
    source = main.read_text()
    # Expose internal objects only in this disposable test copy. Production behavior
    # and presentation bindings stay intact; all injected writers target test doubles.
    replacements = {
        '    id: root\n': '    id: root\n    property alias probeAudio: audio\n    property alias probeBluetooth: bluetooth\n    property alias probeBrightness: brightnessChange\n',
        'text: [wifiChange.error, bluetooth.error]': 'objectName: "probeRadioError"\n                text: [wifiChange.error, bluetooth.error]',
        'text: [audio.output.error, audio.input.error]': 'objectName: "probeAudioError"\n                    text: [audio.output.error, audio.input.error]',
        'text: "Applying audio change…"': 'objectName: "probeAudioPending"\n                    text: "Applying audio change…"',
        'text: brightnessChange.busy ?': 'objectName: "probeBrightnessError"\n                    text: brightnessChange.busy ?',
        'title: root.bluetoothTitle': 'objectName: "probeBluetoothTile"\n                    title: root.bluetoothTitle',
        'text: "Devices & Microphone…"': 'objectName: "probeAudioSettings"\n                    text: "Devices & Microphone…"',
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise SystemExit(f'Instrumentation anchor must be unique: {old!r}')
        source = source.replace(old, new)
    main.write_text(source)
    shutil.copyfile(Path(__file__).with_name('tst_ControlFaults.qml'), target / 'tst_ControlFaults.qml')
    raise SystemExit(subprocess.call(
        ['/usr/lib/qt6/bin/qmltestrunner', '-input', str(target / 'tst_ControlFaults.qml'), '-o', '-,txt'],
        env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software'}, timeout=30))
