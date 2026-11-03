"""plasma/audio_api.py: KDE private audio API compatibility check (KUM-23)."""
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kumios_audio_api', ROOT / 'plasma/audio_api.py')
audio_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio_api)
CONTRACT = json.loads((ROOT / 'plasma/audio-api-contract.json').read_text())
UI = ROOT / 'plasma/plasmoids/org.kumios.controlcenter/contents/ui'
INSTALLED = Path('/usr/lib/qt6/qml/org/kde/plasma/private/volume/plasma-volume-declarative.qmltypes')

# A minimal qmltypes document shaped like plasma-pa 6.8's, covering the contract.
COMPATIBLE = '''import QtQuick.tooling 1.2

// Generated-style comment.
Module {
    Component {
        name: "PulseAudioQt::Context"
        prototype: "QObject"
        exports: ["org.kde.plasma.private.volume/Context 0.0"]
        isCreatable: false
        isSingleton: true
        Enum {
            name: "State"
            isScoped: true
            values: ["Unconnected", "Connecting", "Authorizing", "SettingName", "Ready", "Failed"]
        }
        Property { name: "state"; type: "State"; isReadonly: true }
        Property { name: "autoConnecting"; type: "bool"; isReadonly: true }
        Method { name: "reconnectDaemon" }
    }
    Component {
        name: "PulseAudioQt::Server"
        prototype: "QObject"
        exports: ["org.kde.plasma.private.volume/Server 0.0"]
        isCreatable: false
        isSingleton: true
        Property { name: "defaultSink"; type: "Sink"; isPointer: true }
        Property { name: "defaultSource"; type: "Source"; isPointer: true }
    }
    Component {
        name: "PulseAudioQt::PulseObject"
        prototype: "QObject"
        Property { name: "name"; type: "QString"; isReadonly: true }
    }
    Component {
        name: "PulseAudioQt::VolumeObject"
        prototype: "PulseAudioQt::PulseObject"
        Property { name: "volume"; type: "qlonglong" }
        Property { name: "muted"; type: "bool" }
        Property { name: "volumeWritable"; type: "bool"; isReadonly: true }
    }
    Component {
        name: "PulseAudioQt::Device"
        prototype: "PulseAudioQt::VolumeObject"
        Property { name: "description"; type: "QString"; isReadonly: true }
    }
    Component { name: "PulseAudioQt::Sink"; prototype: "PulseAudioQt::Device" }
    Component { name: "PulseAudioQt::Source"; prototype: "PulseAudioQt::Device" }
    Component {
        name: "PulseAudioQt::SinkModel"
        prototype: "QAbstractListModel"
        exports: ["org.kde.plasma.private.volume/SinkModel 0.0"]
    }
    Component {
        name: "PulseAudioQt::SourceModel"
        prototype: "QAbstractListModel"
        exports: ["org.kde.plasma.private.volume/SourceModel 0.0"]
    }
}
'''


def mutated(old, new):
    assert COMPATIBLE.count(old) == 1, old
    return COMPATIBLE.replace(old, new)


class CheckTests(unittest.TestCase):
    def test_compatible_document_passes(self):
        self.assertEqual(audio_api.check(COMPATIBLE, CONTRACT), [])

    def test_detects_each_kind_of_breaking_change(self):
        cases = {
            'removed type': (mutated('"org.kde.plasma.private.volume/SinkModel 0.0"', ''),
                             'type SinkModel is no longer exported'),
            'renamed property': (mutated('name: "autoConnecting"', 'name: "isAutoConnecting"'),
                                 'Context.autoConnecting property removed or renamed'),
            'renamed method': (mutated('Method { name: "reconnectDaemon" }', 'Method { name: "reconnect" }'),
                               'Context.reconnectDaemon() method removed or renamed'),
            'removed enum value': (mutated('"SettingName", ', ''),
                                   'Context.State.SettingName value removed or renamed'),
            'renamed enum': (mutated('name: "State"', 'name: "ConnectionState"'),
                             'Context.State enum removed or renamed'),
            'no longer singleton': (mutated('exports: ["org.kde.plasma.private.volume/Server 0.0"]\n        isCreatable: false\n        isSingleton: true',
                                            'exports: ["org.kde.plasma.private.volume/Server 0.0"]\n        isCreatable: false'),
                                    'Server is no longer a singleton'),
            'inherited device property removed': (mutated('Property { name: "volumeWritable"; type: "bool"; isReadonly: true }', ''),
                                                  'Server.defaultSink.volumeWritable property removed or renamed'),
            'device property now read-only': (mutated('Property { name: "muted"; type: "bool" }',
                                                      'Property { name: "muted"; type: "bool"; isReadonly: true }'),
                                              'Server.defaultSink.muted is no longer writable'),
            'device type changed': (mutated('name: "defaultSource"; type: "Source"', 'name: "defaultSource"; type: "AudioNode"'),
                                    "Server.defaultSource has unknown device type 'AudioNode'"),
        }
        for label, (document, expected) in cases.items():
            with self.subTest(label):
                self.assertIn(expected, audio_api.check(document, CONTRACT))

    def test_qualified_and_unqualified_device_types_resolve(self):
        qualified = mutated('type: "Sink"; isPointer', 'type: "PulseAudioQt::Sink"; isPointer')
        self.assertEqual(audio_api.check(qualified, CONTRACT), [])

    def test_unreadable_document_raises(self):
        with self.assertRaises(ValueError):
            audio_api.check('Module { Component { name: "x" ', CONTRACT)

    @unittest.skipUnless(INSTALLED.is_file(), 'KDE audio module not installed')
    def test_installed_kde_module_is_compatible(self):
        self.assertEqual(audio_api.check(INSTALLED.read_text(), CONTRACT), [])


class ReportTests(unittest.TestCase):
    def test_reports_problems_and_fallback(self):
        with patch.object(audio_api, 'qmltypes_path', side_effect=FileNotFoundError('module is not installed')), \
             patch.object(audio_api, 'installed_version', return_value='6.9.0'):
            compatible, lines = audio_api.report()
        self.assertFalse(compatible)
        self.assertIn('INCOMPATIBLE', lines[0])
        self.assertIn('module is not installed', '\n'.join(lines))
        self.assertIn('other controls keep working', '\n'.join(lines))

    def test_newer_version_passing_check_asks_for_recheck(self):
        with tempfile.TemporaryDirectory() as directory:
            qmltypes = Path(directory, 'plasma-volume-declarative.qmltypes')
            qmltypes.write_text(COMPATIBLE)
            with patch.object(audio_api, 'qmltypes_path', return_value=qmltypes), \
                 patch.object(audio_api, 'installed_version', return_value='6.9.0'):
                compatible, lines = audio_api.report()
        self.assertTrue(compatible)
        self.assertIn('compatible (plasma-pa 6.9.0)', lines[0])
        self.assertIn('Last verified with 6.8.2', lines[1])


class ContractSyncTests(unittest.TestCase):
    """The QML runtime guard must check exactly what the contract records."""

    def qml_list(self, file, name):
        text = (UI / file).read_text()
        match = re.search(rf'property var {name}: \[([^\]]*)\]', text)
        self.assertIsNotNone(match, f'{file} must declare {name}')
        return re.findall(r'"(\w+)"', match.group(1))

    def test_native_audio_guard_matches_contract(self):
        types = CONTRACT['types']
        self.assertEqual(self.qml_list('NativeAudio.qml', 'requiredContext'), types['Context']['properties'])
        self.assertEqual(self.qml_list('NativeAudio.qml', 'requiredContextMethods'), types['Context']['methods'])
        self.assertEqual(self.qml_list('NativeAudio.qml', 'requiredStates'), types['Context']['enums']['State'])
        self.assertEqual(self.qml_list('NativeAudio.qml', 'requiredServer'), types['Server']['properties'])

    def test_endpoint_guard_matches_contract(self):
        self.assertEqual(self.qml_list('AudioEndpoint.qml', 'requiredMembers'), CONTRACT['devices']['properties'])

    def test_only_native_audio_imports_private_module(self):
        importers = sorted(p.name for p in UI.glob('*.qml')
                           if 'org.kde.plasma.private.volume' in p.read_text())
        self.assertEqual(importers, ['NativeAudio.qml'])
        self.assertNotIn('NativeAudio {', (UI / 'main.qml').read_text())


if __name__ == '__main__':
    unittest.main()
