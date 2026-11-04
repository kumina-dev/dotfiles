"""Login screen sync service: staging as the user, validation as root (KUM-33).
Runs unprivileged in temporary directories; never touches /etc or systemd."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plasma'))
spec = importlib.util.spec_from_file_location('kumios_greeter_sync', ROOT / 'plasma/greeter/sync.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
setup = sync.greeter

PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 32
UID = os.getuid()


def theme(**overrides):
    colors = dict(sync.DEFAULTS)
    colors.update(overrides)
    return json.dumps({'colors': colors, 'dark': True}).encode()


class Staged(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.stage = Path(self.temp.name, 'stage')
        self.dest = Path(self.temp.name, 'greetd')
        self.stage.mkdir()
        self.dest.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def put(self, theme_bytes=None, image=PNG):
        (self.stage / sync.THEME_FILE).write_bytes(theme_bytes or theme())
        (self.stage / sync.IMAGE_FILE).write_bytes(image)


class ValidationTests(Staged):
    def test_theme_must_be_exact_hex_colors_and_a_bool(self):
        self.assertEqual(sync.validate_theme(theme())[1], True)
        bad = [theme(window_bg_color='#FFF'), theme(window_bg_color='url(/etc/shadow)'),
               theme(window_bg_color='#123456; } * { color: red'),
               json.dumps({'colors': {'accent_color': '#000000'}, 'dark': True}).encode(),
               json.dumps({'colors': dict(sync.DEFAULTS, extra='#000000'), 'dark': True}).encode(),
               json.dumps({'colors': dict(sync.DEFAULTS), 'dark': 'yes'}).encode()]
        for raw in bad:
            with self.subTest(raw=raw[:60]):
                with self.assertRaises(ValueError):
                    sync.validate_theme(raw)

    def test_image_signatures(self):
        self.assertEqual(sync.image_kind(PNG), 'png')
        self.assertEqual(sync.image_kind(b'\xff\xd8\xff\xe0rest'), 'jpeg')
        self.assertEqual(sync.image_kind(b'RIFF\x00\x00\x00\x00WEBPVP8 '), 'webp')
        self.assertIsNone(sync.image_kind(b'root:x:0:0:root:/root:/bin/bash\n'))

    def test_read_staged_rejects_symlinks_hardlinks_owner_and_size(self):
        target = Path(self.temp.name, 'secret')
        target.write_bytes(PNG)
        (self.stage / 'link').symlink_to(target)
        with self.assertRaises(OSError):                 # O_NOFOLLOW
            sync.read_staged(self.stage / 'link', UID, 1024)
        os.link(target, self.stage / 'hard')
        with self.assertRaisesRegex(ValueError, 'owner or link count'):
            sync.read_staged(self.stage / 'hard', UID, 1024)
        (self.stage / 'own').write_bytes(PNG)
        with self.assertRaisesRegex(ValueError, 'owner or link count'):
            sync.read_staged(self.stage / 'own', UID + 1, 1024)
        with self.assertRaisesRegex(ValueError, 'too large'):
            sync.read_staged(self.stage / 'own', UID, 8)
        (self.stage / 'dir').mkdir()
        with self.assertRaises((ValueError, OSError)):
            sync.read_staged(self.stage / 'dir', UID, 1024)
        self.assertEqual(sync.read_staged(self.stage / 'own', UID, 1024), PNG)


class ApplyTests(Staged):
    def test_installs_rendered_files_then_is_idempotent(self):
        self.put()
        changed = sync.apply(self.stage, UID, self.dest, style='/* style */\n')
        self.assertEqual(changed, list(sync.OUTPUTS))
        self.assertEqual((self.dest / 'kumios-wallpaper.png').read_bytes(), PNG)
        css = (self.dest / 'regreet.css').read_text()
        self.assertIn('@define-color accent_bg_color #3daee9;', css)
        self.assertIn(f'path = "{self.dest / "kumios-wallpaper.png"}"', (self.dest / 'regreet.toml').read_text())
        for name in sync.OUTPUTS:
            self.assertEqual((self.dest / name).stat().st_mode & 0o777, 0o644)
        self.assertEqual(sync.apply(self.stage, UID, self.dest, style='/* style */\n'), [])
        self.assertFalse(list(self.dest.glob('.kumios-sync-*')))

    def test_invalid_input_changes_nothing(self):
        for theme_bytes, image in ((theme(window_bg_color='bad'), PNG), (theme(), b'not an image')):
            with self.subTest(image=image[:8]):
                self.put(theme_bytes, image)
                with self.assertRaises(ValueError):
                    sync.apply(self.stage, UID, self.dest, style='')
                self.assertEqual(list(self.dest.iterdir()), [])

    def test_theme_is_rendered_by_root_not_copied(self):
        self.put()
        sync.apply(self.stage, UID, self.dest, style='')
        toml = (self.dest / 'regreet.toml').read_text()
        self.assertIn(setup.CLOCK_FORMAT, toml)
        self.assertIn('[commands]', toml)


class StageTests(unittest.TestCase):
    def config(self, temp, image):
        config = Path(temp, 'config')
        config.mkdir()
        (config / 'kdeglobals').write_text('[General]\nAccentColor=113,51,207\n')
        (config / 'plasma-org.kde.plasma.desktop-appletsrc').write_text(
            f'[Containments][1][Wallpaper][org.kde.image][General]\nImage={image}\n')
        return config

    def test_stage_writes_theme_and_wallpaper_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp, 'nebula.png')
            image.write_bytes(PNG)
            out = Path(temp, 'out')
            out.mkdir()
            sync.stage(out, self.config(temp, image))
            data = json.loads((out / sync.THEME_FILE).read_text())
            self.assertEqual(data['colors']['accent_bg_color'], '#7133cf')
            self.assertEqual((out / sync.IMAGE_FILE).read_bytes(), PNG)

    @unittest.skipIf(UID == 0, 'must run unprivileged')
    def test_wallpaper_pointing_at_a_root_only_file_is_not_copied(self):
        protected = Path('/etc/shadow')
        if not protected.exists() or os.access(protected, os.R_OK):
            self.skipTest('needs an unreadable root-only file')
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp, 'out')
            out.mkdir()
            with self.assertRaises(PermissionError):
                sync.stage(out, self.config(temp, protected))
            self.assertFalse((out / sync.IMAGE_FILE).exists())

    @unittest.skipIf(UID == 0, 'must run unprivileged')
    def test_run_refuses_without_root(self):
        with self.assertRaises(PermissionError):
            sync.run('nobody')


class UnitTests(unittest.TestCase):
    def test_units_run_root_owned_code_hardened_and_watch_only_appearance(self):
        units = setup.sync_units('alice', '/home/alice')
        path_unit, service = units['kumios-greeter-sync.path'], units['kumios-greeter-sync.service']
        self.assertEqual([l for l in path_unit.splitlines() if l.startswith('PathChanged=')],
                         ['PathChanged=/home/alice/.config/plasma-org.kde.plasma.desktop-appletsrc',
                          'PathChanged=/home/alice/.config/kdeglobals'])
        self.assertIn('ExecStart=/usr/bin/python3 -I /usr/local/lib/kumios/greeter/sync.py run --user alice', service)
        self.assertNotIn('/home/alice', service)
        for setting in ('ProtectSystem=strict', 'ReadWritePaths=/etc/greetd', 'ProtectHome=read-only',
                        'PrivateNetwork=yes', 'NoNewPrivileges=yes'):
            self.assertIn(setting, service)
        self.assertNotIn('CAP_SYS_ADMIN', service)

    def test_lib_copies_are_outside_home(self):
        for target in setup.LIB_FILES.values():
            self.assertTrue(str(target).startswith('/usr/local/lib/kumios/'), target)


if __name__ == '__main__':
    unittest.main()
