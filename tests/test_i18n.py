import ast
from datetime import datetime
import json
import os
from pathlib import Path
import select
from string import Formatter
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'hypr/.config/hypr/scripts'
sys.path.insert(0, str(SCRIPTS))
from kumina_common import i18n, region
from settings_app import system_info


class TranslationTests(unittest.TestCase):
    def test_selected_language_and_english_fallback(self):
        with patch.object(i18n, 'LANGUAGE', 'fi'):
            self.assertEqual(i18n.translate('Settings'), 'Asetukset')
            self.assertEqual(i18n.translate('Unknown external device'), 'Unknown external device')
            self.assertEqual(i18n.translate('Settings', language='en'), 'Settings')

    def test_placeholder_values_are_preserved(self):
        name = 'Router {untrusted} <Network> äö'
        self.assertEqual(i18n.translate('Connected to {name}', language='fi', name=name),
                         'Yhdistetty verkkoon ' + name)

    def test_all_catalog_placeholders_match(self):
        formatter = Formatter()
        for source, translated in i18n.FINNISH.items():
            with self.subTest(source=source):
                self.assertTrue(isinstance(translated, str) and translated)
                source_fields = {field for _, field, _, _ in formatter.parse(source) if field is not None}
                translated_fields = {field for _, field, _, _ in formatter.parse(translated) if field is not None}
                self.assertEqual(source_fields, translated_fields)
                # Exercise formatting, including messages with multiple arguments.
                i18n.translate(source, language='fi', **dict.fromkeys(source_fields, 'example'))

    def test_every_authored_translation_call_has_a_finnish_entry(self):
        for path in SCRIPTS.rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'tr':
                    if node.args and isinstance(node.args[0], ast.Constant):
                        self.assertIn(node.args[0].value, i18n.FINNISH, f'{path}:{node.lineno}')

    def test_date_names_and_week_order_are_localized_without_changing_formats(self):
        now = datetime(2026, 9, 18, 16, 10)
        prefs = dict(region.DEFAULTS, date='iso', week_start='sunday')
        english = region.clock_payload(now, prefs, language='en')
        finnish = region.clock_payload(now, prefs, language='fi')
        self.assertEqual(english['text'], finnish['text'])
        self.assertIn('2026-09-18', finnish['tooltip'])
        self.assertIn('September 2026', english['tooltip'])
        self.assertIn('Syyskuu 2026', finnish['tooltip'])
        self.assertIn('Su Mo Tu We Th Fr Sa', english['tooltip'])
        self.assertIn('Su Ma Ti Ke To Pe La', finnish['tooltip'])

    def test_system_information_phrases_localize_without_modifying_machine_data(self):
        with patch.object(i18n, 'LANGUAGE', 'fi'):
            self.assertEqual(system_info.memory_size('MemTotal: 1048576 kB'), '1.0 GiB käytettävissä')
            self.assertEqual(system_info.cpu_model('model name: Example CPU'), 'Example CPU')
            self.assertEqual(system_info.format_report([('Suoritin', 'Example CPU')]), 'Suoritin: Example CPU')


class LanguagePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.environment = patch.dict(os.environ, {'XDG_CONFIG_HOME': self.directory.name})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_default_and_round_trip_leave_regional_preferences_unchanged(self):
        self.assertEqual(i18n.read_language(), 'en')
        region.save_preferences(dict(region.DEFAULTS, clock='12'))
        before = region.preferences_path().read_bytes()
        for language in ('fi', 'en'):
            i18n.save_language(language)
            self.assertEqual(i18n.read_language(strict=True), language)
            self.assertEqual(region.preferences_path().read_bytes(), before)

    def test_invalid_preferences_fall_back_but_settings_can_report_error(self):
        path = i18n.language_path()
        path.parent.mkdir(parents=True)
        for content in ('{', 'null', '[]', '{}', '{"language": "xx"}', '{"language": []}'):
            with self.subTest(content=content):
                path.write_text(content)
                self.assertEqual(i18n.read_language(), 'en')
                with self.assertRaises(RuntimeError):
                    i18n.read_language(strict=True)

    def test_invalid_language_does_not_overwrite_saved_choice(self):
        i18n.save_language('fi')
        for invalid in ('xx', None, []):
            with self.assertRaises(ValueError):
                i18n.save_language(invalid)
        self.assertEqual(i18n.read_language(strict=True), 'fi')

    def test_failed_write_retains_previous_language_and_removes_temporary_file(self):
        i18n.save_language('fi')
        with patch.object(Path, 'replace', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                i18n.save_language('en')
        self.assertEqual(i18n.read_language(strict=True), 'fi')
        self.assertEqual(list(i18n.language_path().parent.iterdir()), [i18n.language_path()])

    def test_new_process_uses_saved_language_without_system_locale_changes(self):
        i18n.save_language('fi')
        env = dict(os.environ, PYTHONPATH=str(SCRIPTS), LC_ALL='C', LANGUAGE='en')
        result = subprocess.run([sys.executable, '-c',
            'import os; from kumina_common.i18n import translate; '
            'print(translate("Settings")); print(os.environ["LC_ALL"]); print(os.environ["LANGUAGE"])'],
            env=env, text=True, capture_output=True, check=True, timeout=5)
        self.assertEqual(result.stdout.splitlines(), ['Asetukset', 'C', 'en'])

    def test_open_app_keeps_its_language_until_reopened(self):
        i18n.save_language('en')
        with patch.object(i18n, 'LANGUAGE', 'en'):
            i18n.save_language('fi')
            self.assertEqual(i18n.translate('Settings'), 'Settings')
            self.assertEqual(i18n.translate('Settings', language=i18n.read_language()), 'Asetukset')

    def test_live_panel_clock_picks_up_language_change(self):
        i18n.save_language('en')
        process = subprocess.Popen([sys.executable, str(SCRIPTS / 'kumina-clock.py')],
                                   stdout=subprocess.PIPE, text=True, env=dict(os.environ))
        try:
            self.assertTrue(select.select([process.stdout], [], [], 5)[0])
            before = json.loads(process.stdout.readline())
            self.assertIn('Mo Tu We Th Fr Sa Su', before['tooltip'])
            i18n.save_language('fi')
            self.assertTrue(select.select([process.stdout], [], [], 5)[0])
            after = json.loads(process.stdout.readline())
            self.assertIn('Ma Ti Ke To Pe La Su', after['tooltip'])
            self.assertRegex(after['text'], r'^\d{2}:\d{2}$')
        finally:
            process.terminate()
            process.wait(timeout=5)
            process.stdout.close()


if __name__ == '__main__':
    unittest.main()
