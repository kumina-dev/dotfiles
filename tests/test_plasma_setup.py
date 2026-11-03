import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('plasma_setup', Path(__file__).resolve().parents[1] / 'plasma/setup.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class PlasmaSetupTests(unittest.TestCase):
    def test_default_check_never_installs_or_backs_up(self):
        with patch.object(setup, 'preflight', return_value={}), \
             patch.object(setup, 'backup') as backup, \
             patch.object(setup.shutil, 'copytree') as copy, \
             patch('sys.argv', ['setup.py']):
            setup.main()
        backup.assert_not_called()
        copy.assert_not_called()

    def test_backup_keeps_configs_widgets_absence_and_live_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, data = root / 'config', root / 'data'
            config.mkdir()
            (config / setup.CONFIGS[0]).write_text('original panels')
            installed = data / 'plasma/plasmoids/org.kumios.systemmenu'
            installed.mkdir(parents=True)
            (installed / 'main.qml').write_text('original widget')
            with patch.object(setup, 'plasma', return_value='original live layout'):
                target = setup.backup(config, data, {'panels': []})
            self.assertEqual(target.stat().st_mode & 0o777, 0o700)
            self.assertEqual((target / setup.CONFIGS[0]).read_text(), 'original panels')
            self.assertEqual((target / 'layout.js').read_text(), 'original live layout\n')
            self.assertEqual((target / 'plasmoids/org.kumios.systemmenu/main.qml').read_text(), 'original widget')
            self.assertIn('plasmashellrc', json.loads((target / 'absent.json').read_text()))
            self.assertIn('plasmoids/org.kumios.controlcenter', json.loads((target / 'absent.json').read_text()))

    def test_preflight_failure_cannot_start_installation(self):
        with patch.object(setup, 'preflight', side_effect=RuntimeError('missing module')), \
             patch.object(setup, 'backup') as backup, \
             patch('sys.argv', ['setup.py', '--apply-layout']):
            with self.assertRaisesRegex(RuntimeError, 'missing module'):
                setup.main()
        backup.assert_not_called()

    def test_widget_only_install_does_not_evaluate_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            widget = source / 'plasmoids/org.kumios.controlcenter'
            widget.mkdir(parents=True)
            (widget / 'metadata.json').write_text('{}')
            with patch.object(setup, 'SOURCE', source), \
                 patch.object(setup, 'preflight', return_value={}), \
                 patch.object(setup, 'backup', return_value=root / 'backup'), \
                 patch.object(setup, 'plasma') as plasma, \
                 patch.dict(setup.os.environ, {'XDG_CONFIG_HOME':str(root / 'config'), 'XDG_DATA_HOME':str(root / 'data')}), \
                 patch('sys.argv', ['setup.py', '--install-widgets']):
                setup.main()
            plasma.assert_not_called()
            self.assertEqual((root / 'data/plasma/plasmoids/org.kumios.controlcenter/metadata.json').read_text(), '{}')
