"""plasma/appearance.py: wallpaper accent and light/dark setup (KUM-21). All mocked."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'kumios_appearance', Path(__file__).resolve().parents[1] / 'plasma/appearance.py')
appearance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(appearance)


class FakeConfig:
    """Stands in for kreadconfig6/kwriteconfig6 with an in-memory kdeglobals."""

    def __init__(self, values=None):
        self.values = dict(values or {})
        self.writes = []

    def read(self, name, group, key):
        return self.values.get((name, group, key), '')

    def write(self, name, group, key, value):
        self.writes.append((name, group, key, value))
        self.values[(name, group, key)] = value


DARK = {('kdeglobals', 'Colors:Window', 'BackgroundNormal'): '32,35,38'}
LIGHT = {('kdeglobals', 'Colors:Window', 'BackgroundNormal'): '239,240,241'}


class VariantTests(unittest.TestCase):
    def test_variant_from_window_background(self):
        self.assertEqual(appearance.variant_of('32,35,38'), 'dark')
        self.assertEqual(appearance.variant_of('239,240,241'), 'light')
        self.assertEqual(appearance.variant_of('32,35,38,255'), 'dark')

    def test_choose_manual_modes_turn_automatic_off(self):
        fake = FakeConfig({**DARK, ('kdeglobals', 'KDE', 'AutomaticLookAndFeel'): 'true'})
        with patch.object(appearance, 'read_config', fake.read):
            self.assertEqual(appearance.choose('light'), ('org.kumios.light', False))
            self.assertEqual(appearance.choose('dark'), ('org.kumios.dark', False))

    def test_choose_auto_follows_day_night_schedule(self):
        fake = FakeConfig(DARK)
        with patch.object(appearance, 'read_config', fake.read):
            with patch.object(appearance, 'daytime', return_value=True):
                self.assertEqual(appearance.choose('auto'), ('org.kumios.light', True))
            with patch.object(appearance, 'daytime', return_value=False):
                self.assertEqual(appearance.choose('auto'), ('org.kumios.dark', True))
            with patch.object(appearance, 'daytime', return_value=None):
                self.assertEqual(appearance.choose('auto'), ('org.kumios.dark', True))

    def test_choose_current_keeps_variant_and_automatic_setting(self):
        for values, expected in ((LIGHT, ('org.kumios.light', False)),
                                 ({**DARK, ('kdeglobals', 'KDE', 'AutomaticLookAndFeel'): 'true'},
                                  ('org.kumios.dark', True))):
            with patch.object(appearance, 'read_config', FakeConfig(values).read):
                self.assertEqual(appearance.choose('current'), expected)


class ApplyTests(unittest.TestCase):
    def apply(self, mode, values):
        fake = FakeConfig(values)
        with patch.object(appearance, 'read_config', fake.read), \
             patch.object(appearance, 'write_config', fake.write), \
             patch.object(appearance, 'daytime', return_value=None), \
             patch.object(appearance, 'run') as run:
            result = appearance.apply(mode)
        return result, fake, run

    def test_manual_apply_enables_accent_registers_pair_and_drops_auto(self):
        (package, automatic), fake, run = self.apply('light', DARK)
        self.assertEqual((package, automatic), ('org.kumios.light', False))
        self.assertIn(('kdeglobals', 'General', 'accentColorFromWallpaper', 'true'), fake.writes)
        self.assertIn(('kdeglobals', 'KDE', 'DefaultLightLookAndFeel', 'org.kumios.light'), fake.writes)
        self.assertIn(('kdeglobals', 'KDE', 'DefaultDarkLookAndFeel', 'org.kumios.dark'), fake.writes)
        self.assertNotIn('AutomaticLookAndFeel', [w[2] for w in fake.writes])
        run.assert_called_once_with('plasma-apply-lookandfeel', '--apply', 'org.kumios.light')

    def test_auto_apply_keeps_automatic_mode(self):
        (package, automatic), fake, run = self.apply('auto', DARK)
        self.assertEqual((package, automatic), ('org.kumios.dark', True))
        self.assertIn(('kdeglobals', 'KDE', 'AutomaticLookAndFeel', 'true'), fake.writes)
        run.assert_called_once_with('plasma-apply-lookandfeel', '--keep-auto', '--apply', 'org.kumios.dark')

    def test_verify_requires_observed_state(self):
        good = {('kdeglobals', 'KDE', 'LookAndFeelPackage'): 'org.kumios.dark',
                ('kdeglobals', 'General', 'accentColorFromWallpaper'): 'true'}
        with patch.object(appearance, 'read_config', FakeConfig(good).read):
            appearance.verify('org.kumios.dark', False)
            with self.assertRaisesRegex(RuntimeError, 'automatic light/dark is off'):
                appearance.verify('org.kumios.dark', True)
            with self.assertRaisesRegex(RuntimeError, 'global theme is not org.kumios.light'):
                appearance.verify('org.kumios.light', False)
        no_accent = {**good, ('kdeglobals', 'General', 'accentColorFromWallpaper'): 'false'}
        with patch.object(appearance, 'read_config', FakeConfig(no_accent).read):
            with self.assertRaisesRegex(RuntimeError, 'wallpaper accent'):
                appearance.verify('org.kumios.dark', False)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config, self.data = self.root / 'config', self.root / 'data'
        self.config.mkdir()
        # A legacy package directory that ~/.config/gtk-3.0 links into.
        self.legacy = self.root / 'dotfiles/gtk/.config/gtk-3.0'
        self.legacy.mkdir(parents=True)
        for name, text in (('settings.ini', '[Settings]\ngtk-font-name=Noto Sans, 10\n'),
                           ('colors.css', '@define-color a #000;\n'),
                           ('gtk.css', '@import url("matugen.css");\n'),
                           ('matugen.css', '@define-color accent_bg_color #123456;\n')):
            (self.legacy / name).write_text(text)
        os.symlink(self.legacy, self.config / 'gtk-3.0')
        (self.config / 'gtk-4.0').mkdir()
        (self.config / 'gtk-4.0/settings.ini').write_text('[Settings]\n')
        (self.config / 'kdeglobals').write_text('[General]\nColorScheme=BreezeDark\n')

    def tearDown(self):
        self.temporary.cleanup()

    def test_default_check_changes_nothing(self):
        with patch.object(appearance, 'preflight'), \
             patch.object(appearance, 'status', return_value={}), \
             patch.object(appearance, 'backup') as backup, \
             patch.object(appearance, 'install') as install, \
             patch.object(appearance, 'adopt_gtk') as adopt, \
             patch.object(appearance, 'apply') as apply, \
             patch('sys.argv', ['appearance.py']):
            appearance.main()
        for step in (backup, install, adopt, apply):
            step.assert_not_called()

    def test_preflight_failure_stops_before_any_change(self):
        with patch.object(appearance, 'preflight', side_effect=RuntimeError('services not running')), \
             patch.object(appearance, 'backup') as backup, \
             patch('sys.argv', ['appearance.py', '--apply', 'dark']):
            with self.assertRaisesRegex(RuntimeError, 'services not running'):
                appearance.main()
        backup.assert_not_called()

    def test_backup_is_private_and_records_configs_links_and_absence(self):
        installed = self.data / 'plasma/desktoptheme/KumiOS'
        installed.mkdir(parents=True)
        (installed / 'colors').write_text('old palette')
        target = appearance.backup(self.config, self.data)
        self.assertEqual(target.stat().st_mode & 0o777, 0o700)
        self.assertEqual((target / 'kdeglobals').read_text(), '[General]\nColorScheme=BreezeDark\n')
        self.assertEqual(json.loads((target / 'gtk-links.json').read_text()), {'gtk-3.0': str(self.legacy)})
        self.assertEqual((target / 'gtk-4.0/settings.ini').read_text(), '[Settings]\n')
        self.assertEqual((target / 'plasma/desktoptheme/KumiOS/colors').read_text(), 'old palette')
        absent = json.loads((target / 'absent.json').read_text())
        self.assertIn('plasmarc', absent)
        self.assertIn('plasma/look-and-feel/org.kumios.light', absent)

    def test_install_replaces_stale_files(self):
        stale = self.data / 'plasma/desktoptheme/KumiOS/colors'
        stale.parent.mkdir(parents=True)
        stale.write_text('old fixed palette')
        appearance.install(self.data)
        self.assertFalse(stale.exists())
        self.assertTrue((self.data / 'plasma/desktoptheme/KumiOS/widgets/panel-background.svg').is_file())
        for package in ('org.kumios.light', 'org.kumios.dark'):
            self.assertTrue((self.data / 'plasma/look-and-feel' / package / 'contents/defaults').is_file())

    def test_adopt_gtk_replaces_only_links_and_keeps_legacy_package(self):
        before = {p.name: p.read_text() for p in self.legacy.iterdir()}
        adopted = appearance.adopt_gtk(self.config)
        self.assertEqual(adopted, ['gtk-3.0'])
        gtk3 = self.config / 'gtk-3.0'
        self.assertFalse(gtk3.is_symlink())
        self.assertEqual(sorted(p.name for p in gtk3.iterdir()), ['colors.css', 'gtk.css', 'settings.ini'])
        self.assertEqual((gtk3 / 'gtk.css').read_text(), "@import 'colors.css';\n")
        self.assertEqual((gtk3 / 'settings.ini').read_text(), before['settings.ini'])
        # The legacy package is untouched and an existing real directory is left alone.
        self.assertEqual({p.name: p.read_text() for p in self.legacy.iterdir()}, before)
        self.assertEqual(sorted(p.name for p in (self.config / 'gtk-4.0').iterdir()), ['settings.ini'])
        self.assertEqual(appearance.adopt_gtk(self.config), [])


class ThemePackageTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1] / 'plasma/lookandfeel'

    def test_packages_change_appearance_only(self):
        for variant, scheme, icons in (('light', 'BreezeLight', 'breeze'), ('dark', 'BreezeDark', 'breeze-dark')):
            with self.subTest(variant=variant):
                package = self.ROOT / f'org.kumios.{variant}'
                metadata = json.loads((package / 'metadata.json').read_text())
                self.assertEqual(metadata['KPackageStructure'], 'Plasma/LookAndFeel')
                self.assertEqual(metadata['KPlugin']['Id'], f'org.kumios.{variant}')
                defaults = (package / 'contents/defaults').read_text()
                self.assertIn(f'ColorScheme={scheme}\n', defaults)
                self.assertIn(f'[kdeglobals][Icons]\nTheme={icons}\n', defaults)
                self.assertIn('[plasmarc][Theme]\nname=KumiOS\n', defaults)
                # Breeze's own global themes set these, replacing the wallpaper (and so
                # the accent) or other user choices; KumiOS themes must not.
                for forbidden in ('[Wallpaper]', 'cursorTheme', 'kdecoration', 'KSplash', 'widgetStyle'):
                    self.assertNotIn(forbidden, defaults)
                self.assertFalse((package / 'contents/layouts').exists())


if __name__ == '__main__':
    unittest.main()
