"""Test snapshot portability and rollback boundaries without system changes."""
import importlib.util
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('greeter_setup', Path(__file__).resolve().parents[1] / 'greeter/setup.py')
greeter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(greeter)


class GreeterTests(unittest.TestCase):
    def test_export_only_known_literal_colors(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'colors.css'
            source.write_text('@import url("/home/private/colors.css");\n'
                              '@define-color accent_color #123abc;\n'
                              '@define-color window_bg_color url("private");\n'
                              '@define-color unexpected #abcdef;\n')
            colors = greeter.palette(source)
            self.assertIn('@define-color accent_color #123abc;', colors)
            self.assertIn('@define-color window_bg_color #121318;', colors)
            self.assertNotIn('private', colors)
            self.assertNotIn('unexpected', colors)

    def test_missing_palette_uses_complete_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            colors = greeter.palette(Path(temp) / 'missing')
            for name in greeter.DEFAULTS:
                self.assertIn(f'@define-color {name} ', colors)

    def test_preview_and_install_paths_and_commands(self):
        with tempfile.TemporaryDirectory(prefix='greeter spaces ') as temp:
            root = Path(temp)
            wallpaper = root / 'wallpaper.png'
            wallpaper.write_bytes(b'wallpaper snapshot')
            stage = root / 'stage'
            stage.mkdir()
            for installed in (False, True):
                greeter.prepare(stage, wallpaper, root / 'no-colors', installed)
                config = tomllib.loads((stage / 'regreet.toml').read_text())
                expected = (greeter.DEST if installed else stage) / 'kumios-wallpaper.png'
                self.assertEqual(config['background']['path'], str(expected))
                self.assertEqual(config['commands'], {'reboot': ['systemctl', 'reboot'], 'poweroff': ['systemctl', 'poweroff']})
                self.assertFalse(config['skip_selection'])
                self.assertEqual((stage / 'kumios-wallpaper.png').read_bytes(), wallpaper.read_bytes())
                if installed:
                    self.assertNotIn(temp, (stage / 'regreet.toml').read_text())

    def test_missing_wallpaper_does_not_generate_config(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                greeter.prepare(root, root / 'missing', root / 'colors')
            self.assertFalse((root / 'regreet.toml').exists())

    def test_restore_rejects_unrelated_directory(self):
        with patch.object(greeter, 'sudo') as sudo:
            with self.assertRaises(ValueError):
                greeter.restore(Path('/tmp/not-a-greeter-backup'))
            sudo.assert_not_called()

    def test_restore_validates_all_files_before_writing(self):
        import subprocess
        with patch.object(greeter.subprocess, 'run') as run, patch.object(greeter, 'sudo') as sudo:
            run.return_value.returncode = 1
            sudo.side_effect = subprocess.CalledProcessError(1, ['test'])
            with self.assertRaises(subprocess.CalledProcessError):
                greeter.restore(Path('/etc/greetd/kumios-backup.test'))
            self.assertEqual(sudo.call_args.args[0], 'test')


if __name__ == '__main__':
    unittest.main()
