"""ReGreet login theme: KDE colors/wallpaper, snapshot portability and rollback
boundaries (KUM-28). Nothing here touches /etc/greetd or runs sudo."""
import importlib.util
import re
import xml.etree.ElementTree as ET
import sys
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'greeter_setup', Path(__file__).resolve().parents[1] / 'plasma/greeter/setup.py')
greeter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(greeter)

LIGHT = '''[General]
AccentColor=113,51,207
ColorScheme=BreezeLight

[Colors:Window]
BackgroundNormal=239,240,241
ForegroundNormal=35,38,41

[Colors:View]
BackgroundNormal=255,255,255
ForegroundNegative=218,68,83

[Colors:Selection]
BackgroundNormal=61,174,233
ForegroundNormal=255,255,255

[Colors:Header][Inactive]
BackgroundNormal=1,2,3
'''


GREETD = '''# greetd configuration
[terminal]
vt = 1

[default_session]
# The greeter
command = "start-hyprland -- -c /etc/greetd/hyprland.lua"
user = "greeter"

[initial_session]
command = "do-not-touch"
user = "someone"
'''


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


class ColorTests(unittest.TestCase):
    def test_kde_scheme_and_wallpaper_accent(self):
        with tempfile.TemporaryDirectory() as temp:
            colors = greeter.kde_colors(write(Path(temp) / 'kdeglobals', LIGHT))
        self.assertEqual(colors['accent_bg_color'], '#7133cf')   # wallpaper accent wins
        self.assertEqual(colors['accent_color'], '#7133cf')
        self.assertEqual(colors['window_bg_color'], '#eff0f1')
        self.assertEqual(colors['window_fg_color'], '#232629')
        self.assertEqual(colors['view_bg_color'], '#ffffff')
        self.assertEqual(colors['destructive_bg_color'], '#da4453')
        self.assertFalse(greeter.is_dark(colors))

    def test_without_accent_uses_selection_color(self):
        with tempfile.TemporaryDirectory() as temp:
            colors = greeter.kde_colors(write(Path(temp) / 'kdeglobals', LIGHT.replace('AccentColor=113,51,207\n', '')))
        self.assertEqual(colors['accent_bg_color'], '#3daee9')

    def test_kdedefaults_fill_missing_keys_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / 'kdedefaults/kdeglobals', '[Colors:Window]\nBackgroundNormal=20,22,24\nForegroundNormal=9,9,9\n')
            colors = greeter.kde_colors(write(root / 'kdeglobals', '[Colors:Window]\nForegroundNormal=252,252,252\n'))
        self.assertEqual(colors['window_bg_color'], '#141618')   # from kdedefaults
        self.assertEqual(colors['window_fg_color'], '#fcfcfc')   # user value kept
        self.assertTrue(greeter.is_dark(colors))

    def test_missing_or_invalid_values_use_complete_breeze_dark_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(greeter.kde_colors(root / 'missing'), greeter.DEFAULTS)
            colors = greeter.kde_colors(write(root / 'kdeglobals', '[Colors:Window]\nBackgroundNormal=url(private)\n'))
        self.assertEqual(colors['window_bg_color'], greeter.DEFAULTS['window_bg_color'])
        self.assertTrue(greeter.is_dark(colors))

    def test_palette_exports_only_known_color_literals(self):
        css = greeter.palette(greeter.DEFAULTS)
        self.assertEqual(css.count('@define-color'), len(greeter.DEFAULTS))
        self.assertNotIn('url', css)


class WallpaperTests(unittest.TestCase):
    def appletsrc(self, root, image):
        return write(root / 'appletsrc', '[Containments][1]\nplugin=org.kde.plasma.folder\n\n'
                     f'[Containments][1][Wallpaper][org.kde.image][General]\nImage={image}\n')

    def test_plain_path_and_file_url(self):
        with tempfile.TemporaryDirectory(prefix='wall paper ') as temp:
            root = Path(temp)
            image = write(root / 'nebula.png', 'x')
            self.assertEqual(greeter.plasma_wallpaper(self.appletsrc(root, image), True), image)
            url = 'file://' + str(image).replace(' ', '%20')
            self.assertEqual(greeter.plasma_wallpaper(self.appletsrc(root, url), True), image)

    def test_wallpaper_package_prefers_largest_and_dark_variant(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / 'Next'
            write(package / 'contents/images/1920x1080.png', 'x')
            largest = write(package / 'contents/images/3840x2160.png', 'x')
            dark = write(package / 'contents/images_dark/3840x2160.png', 'x')
            source = self.appletsrc(root, package)
            self.assertEqual(greeter.plasma_wallpaper(source, False), largest)
            self.assertEqual(greeter.plasma_wallpaper(source, True), dark)

    def test_missing_image_is_none(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(sys.modules['desktop_appearance'], 'package_image', return_value=None):
                self.assertIsNone(greeter.plasma_wallpaper(self.appletsrc(root, root / 'gone.png'), True))


class SnapshotTests(unittest.TestCase):
    def test_preview_and_install_paths_commands_and_dark_preference(self):
        with tempfile.TemporaryDirectory(prefix='greeter spaces ') as temp:
            root = Path(temp)
            wallpaper = write(root / 'wallpaper.png', 'wallpaper snapshot')
            stage = root / 'stage'
            stage.mkdir()
            for colors, dark in ((write(root / 'light/kdeglobals', LIGHT), False), (root / 'no-colors', True)):
                for installed in (False, True):
                    greeter.prepare(stage, wallpaper, colors, installed, write(root / 'greetd.toml', GREETD))
                    config = tomllib.loads((stage / 'regreet.toml').read_text())
                    expected = (greeter.DEST if installed else stage) / 'kumios-wallpaper.png'
                    self.assertEqual(config['background']['path'], str(expected))
                    self.assertIs(config['GTK']['application_prefer_dark_theme'], dark)
                    self.assertEqual(config['commands'], {'reboot': ['systemctl', 'reboot'], 'poweroff': ['systemctl', 'poweroff']})
                    self.assertFalse(config['skip_selection'])
                    self.assertEqual((stage / 'kumios-wallpaper.png').read_text(), 'wallpaper snapshot')
                    css = (stage / 'regreet.css').read_text()
                    self.assertIn('@define-color accent_bg_color #7133cf;' if not dark else '@define-color accent_bg_color #3daee9;', css)
                    if installed:
                        self.assertNotIn(temp, (stage / 'regreet.toml').read_text())

    def test_default_wallpaper_comes_from_plasma(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = write(root / 'current.png', 'plasma wallpaper')
            write(root / 'config/plasma-org.kde.plasma.desktop-appletsrc',
                  f'[Containments][1][Wallpaper][org.kde.image][General]\nImage={image}\n')
            stage = root / 'stage'
            stage.mkdir()
            with patch.object(greeter, 'CONFIG', root / 'config'):
                _, used = greeter.prepare(stage, None, root / 'config/kdeglobals', greetd_config=write(root / 'g.toml', GREETD))
            self.assertEqual(used, image)
            self.assertEqual((stage / 'kumios-wallpaper.png').read_text(), 'plasma wallpaper')

    def test_missing_wallpaper_does_not_generate_config(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                greeter.prepare(root, root / 'missing', root / 'colors')
            self.assertFalse((root / 'regreet.toml').exists())


class ClockTests(unittest.TestCase):
    """ReGreet's clock formats with chrono: an unknown `%` code panics the clock
    (seen when Pango markup used size='300%'), so the installed format is checked."""
    CHRONO = set('aAbBcCdDeFgGhHIjklmMnpPrRsStTuUVwWxXyYzZ%')

    def test_every_percent_is_a_known_chrono_code(self):
        fmt = greeter.CLOCK_FORMAT.replace('\\n', '\n')
        for match in re.finditer(r'%(-?)(.)', fmt):
            self.assertIn(match[2], self.CHRONO, f'unknown clock code %{match[1]}{match[2]}')
        self.assertNotIn("%'", fmt)

    def test_markup_is_well_formed_and_installed(self):
        fmt = greeter.CLOCK_FORMAT.replace('\\n', '\n')
        ET.fromstring('<root>' + fmt.replace('&', '&amp;') + '</root>')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wallpaper = write(root / 'w.png', 'x')
            greeter.prepare(root, wallpaper, root / 'none', greetd_config=write(root / 'g.toml', GREETD))
            config = tomllib.loads((root / 'regreet.toml').read_text())
        self.assertEqual(config['widget']['clock']['format'], fmt)
        self.assertIn('%H:%M', config['widget']['clock']['format'])


class GreetdCommandTests(unittest.TestCase):
    def test_replaces_only_the_default_session_command(self):
        updated = greeter.with_greeter_command(GREETD)
        config = tomllib.loads(updated)
        self.assertEqual(config['default_session']['command'], greeter.GREETER_COMMAND)
        self.assertTrue(config['default_session']['command'].startswith('dbus-run-session -- kwin_wayland --drm'))
        self.assertIn('--exit-with-session /usr/bin/regreet', config['default_session']['command'])
        self.assertEqual(config['default_session']['user'], 'greeter')
        self.assertEqual(config['initial_session'], {'command': 'do-not-touch', 'user': 'someone'})
        self.assertEqual(config['terminal'], {'vt': 1})
        self.assertIn('# The greeter', updated)
        self.assertNotIn('hyprland', updated)
        # Only the one line differs.
        diff = [a for a, b in zip(GREETD.splitlines(), updated.splitlines()) if a != b]
        self.assertEqual(diff, ['command = "start-hyprland -- -c /etc/greetd/hyprland.lua"'])

    def test_refuses_config_without_or_with_duplicate_command(self):
        with self.assertRaisesRegex(ValueError, 'no \\[default_session\\] command'):
            greeter.with_greeter_command('[terminal]\nvt = 1\n')
        with self.assertRaisesRegex(ValueError, 'more than one'):
            greeter.with_greeter_command('[default_session]\ncommand = "a"\ncommand = "b"\n')

    def test_install_backs_up_everything_and_switches_command_last(self):
        calls = []
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(greeter, 'sudo', side_effect=lambda *a: calls.append(a)), \
             patch.object(greeter.subprocess, 'check_output', return_value='/etc/greetd/kumios-backup.test\n'), \
             patch.object(greeter.shutil, 'which', return_value='/usr/bin/tool'), \
             patch.object(Path, 'is_symlink', return_value=False), \
             patch.object(Path, 'exists', return_value=True), \
             patch('builtins.print'):
            greeter.install(Path(temp))
        backups = [a[2].name for a in calls if a[0] == 'cp']
        self.assertEqual(sorted(backups), sorted(greeter.FILES))
        installed = [a[-1].name for a in calls if a[0] == 'install']
        self.assertEqual(installed, list(greeter.INSTALL_ORDER))
        self.assertEqual(installed[-1], 'config.toml')
        self.assertLess(calls.index(next(a for a in calls if a[0] == 'cp')),
                        calls.index(next(a for a in calls if a[0] == 'install')))

    def test_install_refuses_when_command_tools_are_missing(self):
        with patch.object(greeter.shutil, 'which', return_value=None), patch.object(greeter, 'sudo') as sudo:
            with self.assertRaisesRegex(ValueError, 'kwin_wayland'):
                greeter.install(Path('/nonexistent'))
            sudo.assert_not_called()


class RestoreTests(unittest.TestCase):
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
