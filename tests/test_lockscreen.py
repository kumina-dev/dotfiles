"""Lock screen wallpaper follows the desktop (KUM-30). Nothing here locks the
session or runs systemctl; KDE config is written into temporary directories."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plasma'))
spec = importlib.util.spec_from_file_location('kumios_lockscreen', ROOT / 'plasma/lockscreen.py')
lockscreen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lockscreen)

DARK = '[Colors:Window]\nBackgroundNormal=32,35,38\n'
LIGHT = '[Colors:Window]\nBackgroundNormal=239,240,241\n'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Path(self.temp.name, 'config')
        self.config.mkdir()
        self.image = Path(self.temp.name, 'walls', 'nebula.png')
        self.image.parent.mkdir()
        self.image.write_bytes(b'\x89PNG\r\n\x1a\n')
        (self.config / 'kdeglobals').write_text(DARK)
        self.desktop(self.image)

    def tearDown(self):
        self.temp.cleanup()

    def desktop(self, image):
        (self.config / lockscreen.APPLETSRC).write_text(
            f'[Containments][1][Wallpaper][org.kde.image][General]\nImage={image}\n')


class SyncTests(Fixture):
    @unittest.skipUnless(shutil.which('kwriteconfig6'), 'kwriteconfig6 not installed')
    def test_sync_writes_kde_config_and_is_idempotent(self):
        changed, path = lockscreen.sync(self.config)
        self.assertTrue(changed)
        self.assertEqual(path, str(self.image.resolve()))
        self.assertEqual(lockscreen.lock_wallpaper(self.config), str(self.image.resolve()))
        text = (self.config / 'kscreenlockerrc').read_text()
        self.assertIn('[Greeter]\nWallpaperPlugin=org.kde.image', text)
        self.assertIn('[Greeter][Wallpaper][org.kde.image][General]\nImage=', text)
        before = text
        self.assertEqual(lockscreen.sync(self.config), (False, path))
        self.assertEqual((self.config / 'kscreenlockerrc').read_text(), before)

    def test_follows_wallpaper_change_and_dark_variant_of_packages(self):
        writes = []
        package = Path(self.temp.name, 'Next')
        for folder in ('images', 'images_dark'):
            (package / 'contents' / folder).mkdir(parents=True)
            (package / 'contents' / folder / '1920x1080.png').write_bytes(b'x')
        self.desktop(package)
        _, path = lockscreen.sync(self.config, write=lambda *a: writes.append(a))
        self.assertTrue(path.endswith('images_dark/1920x1080.png'))
        (self.config / 'kdeglobals').write_text(LIGHT)
        _, path = lockscreen.sync(self.config, write=lambda *a: writes.append(a))
        self.assertTrue(path.endswith('contents/images/1920x1080.png'))
        self.assertEqual([a[-2:] for a in writes if 'Image' in a][-1], ('Image', path))

    def test_missing_wallpaper_is_an_error_and_writes_nothing(self):
        writes = []
        (self.config / lockscreen.APPLETSRC).write_text('')
        with unittest.mock.patch.object(sys.modules['desktop_appearance'], 'plasma_wallpaper', return_value=None):
            with self.assertRaises(RuntimeError):
                lockscreen.sync(self.config, write=lambda *a: writes.append(a))
        self.assertEqual(writes, [])


class InstallTests(Fixture):
    def test_units_watch_desktop_config_and_run_sync(self):
        units = lockscreen.units(script='/repo/plasma/lockscreen.py', config=self.config)
        path_unit = units['kumios-lockscreen-sync.path']
        self.assertIn(f'PathChanged={self.config / lockscreen.APPLETSRC}', path_unit)
        self.assertIn(f'PathChanged={self.config / "kdeglobals"}', path_unit)
        self.assertIn('WantedBy=default.target', path_unit)
        self.assertIn('ExecStart=/usr/bin/python3 /repo/plasma/lockscreen.py sync',
                      units['kumios-lockscreen-sync.service'])

    def test_install_backs_up_syncs_writes_units_and_enables_path(self):
        (self.config / 'kscreenlockerrc').write_text('[Daemon]\nTimeout=5\n')
        calls = []
        with unittest.mock.patch.object(lockscreen, 'sync', return_value=(True, 'x')):
            target, changed, _ = lockscreen.install_sync(self.config, systemctl=lambda *a: calls.append(a))
        self.assertEqual((target / 'kscreenlockerrc').read_text(), '[Daemon]\nTimeout=5\n')
        self.assertEqual(target.stat().st_mode & 0o777, 0o700)
        for name in ('kumios-lockscreen-sync.path', 'kumios-lockscreen-sync.service'):
            self.assertTrue((self.config / 'systemd/user' / name).is_file())
        self.assertEqual(calls, [('daemon-reload',), ('enable', '--now', 'kumios-lockscreen-sync.path')])

    def test_backup_records_absent_config(self):
        target = lockscreen.backup(self.config)
        self.assertTrue((target / 'kscreenlockerrc.absent').exists())

    def test_remove_disables_and_deletes_units(self):
        unit_dir = self.config / 'systemd/user'
        unit_dir.mkdir(parents=True)
        for name in lockscreen.units(config=self.config):
            (unit_dir / name).write_text('x')
        calls = []
        lockscreen.remove_sync(self.config, systemctl=lambda *a: calls.append(a))
        self.assertEqual(list(unit_dir.iterdir()), [])
        self.assertEqual(calls[0], ('disable', '--now', 'kumios-lockscreen-sync.path'))


if __name__ == '__main__':
    unittest.main()
