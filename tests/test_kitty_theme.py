"""kitty follows KumiOS Light/Dark with colors from KDE's Breeze schemes (KUM-27)."""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kumios_kitty_theme', ROOT / 'plasma/kitty_theme.py')
kitty_theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kitty_theme)
KITTY = ROOT / 'plasma/kitty'
SCHEME = '''[Colors:View]
BackgroundNormal=1,2,3
ForegroundNormal=250,251,252
DecorationFocus=10,20,30
ForegroundLink=40,50,60
ForegroundNegative=200,0,0
ForegroundPositive=0,200,0
ForegroundNeutral=200,200,0
ForegroundVisited=200,0,200

[Colors:Selection]
BackgroundNormal=61,174,233
ForegroundNormal=255,255,255
'''


class RenderTests(unittest.TestCase):
    def test_maps_kde_colors_to_kitty_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'Test.colors').write_text(SCHEME)
            text = kitty_theme.render('Test', Path(directory))
        settings = dict(line.split() for line in text.splitlines() if not line.startswith('#'))
        self.assertEqual(settings, {
            'background': '#010203', 'foreground': '#fafbfc',
            'selection_background': '#3daee9', 'selection_foreground': '#ffffff',
            'cursor': '#0a141e', 'url_color': '#28323c',
            'color1': '#c80000', 'color2': '#00c800', 'color3': '#c8c800',
            'color4': '#28323c', 'color5': '#c800c8',
        })

    def test_missing_scheme_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                kitty_theme.render('Missing', Path(directory))


class ConfigTests(unittest.TestCase):
    def test_all_three_auto_theme_files_exist(self):
        for name in ('light-theme.auto.conf', 'dark-theme.auto.conf', 'no-preference-theme.auto.conf'):
            self.assertTrue((KITTY / name).is_file(), name)

    def test_kitty_conf_sets_no_colors_and_includes_no_matugen_output(self):
        text = (KITTY / 'kitty.conf').read_text()
        settings = [line.split()[0] for line in text.splitlines() if line.strip() and not line.startswith('#')]
        self.assertEqual(settings, ['font_family', 'font_size', 'background_opacity', 'window_padding_width'])
        self.assertNotIn('include', settings)

    @unittest.skipUnless(Path('/usr/share/color-schemes/BreezeDark.colors').is_file(), 'Breeze schemes not installed')
    def test_committed_themes_match_installed_breeze(self):
        for name, scheme in kitty_theme.THEMES.items():
            with self.subTest(name):
                self.assertEqual((KITTY / name).read_text(), kitty_theme.render(scheme))

    @unittest.skipUnless(shutil.which('kitty'), 'kitty not installed')
    def test_kitty_parses_config_with_each_theme(self):
        for name in ('light-theme.auto.conf', 'dark-theme.auto.conf'):
            with self.subTest(name):
                code = ('from kitty.config import load_config; '
                        f'o = load_config({str(KITTY / "kitty.conf")!r}, {str(KITTY / name)!r}); '
                        'print(o.background)')
                result = subprocess.run(['kitty', '+runpy', code], capture_output=True, text=True,
                                        timeout=60, check=True)
                expected = re.search(r'^background\s+#(\w+)', (KITTY / name).read_text(), re.M).group(1)
                rgb = tuple(int(expected[i:i + 2], 16) for i in (0, 2, 4))
                self.assertIn(f'Color({rgb[0]}, {rgb[1]}, {rgb[2]})', result.stdout)


if __name__ == '__main__':
    unittest.main()
