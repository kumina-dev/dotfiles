from decimal import Decimal
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hypr/.config/hypr/scripts'))
from kumina_common import formatting, i18n, region
from settings_app import system_info

FI = dict(region.DEFAULTS, number_format='fi', currency='EUR')
EN = dict(region.DEFAULTS, number_format='en', currency='USD')


class NumberFormatTests(unittest.TestCase):
    def test_decimal_and_group_separators(self):
        self.assertEqual(formatting.format_number('1234567.89', FI), '1\u00a0234\u00a0567,89')
        self.assertEqual(formatting.format_number('1234567.89', EN), '1,234,567.89')
        self.assertEqual(formatting.format_number('1234.5', FI, grouping=False), '1234,50')

    def test_rounding_carries_across_group_boundary(self):
        self.assertEqual(formatting.format_number('999.995', FI), '1\u00a0000,00')
        self.assertEqual(formatting.format_number(Decimal('1.005'), EN), '1.01')
        self.assertEqual(formatting.format_number('-1.005', EN), '-1.01')

    def test_negative_values_and_rounded_zero(self):
        self.assertEqual(formatting.format_number('-1234.5', FI), '-1\u00a0234,50')
        self.assertEqual(formatting.format_number('-0.004', EN), '0.00')
        self.assertEqual(formatting.format_currency('-0.004', EN), '$0.00')

    def test_precision_and_whole_numbers(self):
        self.assertEqual(formatting.format_number(1234, EN, decimals=0), '1,234')
        self.assertEqual(formatting.format_number('0.000123', FI, decimals=6), '0,000123')
        self.assertEqual(formatting.format_number('123456789012345678901234567890.12', EN),
                         '123,456,789,012,345,678,901,234,567,890.12')

    def test_currency_symbols_placement_and_sign(self):
        for code, symbol in (('EUR', '€'), ('USD', '$'), ('GBP', '£')):
            with self.subTest(currency=code):
                self.assertEqual(formatting.format_currency('1234.56', FI, currency=code),
                                 '1\u00a0234,56\u00a0' + symbol)
                self.assertEqual(formatting.format_currency('-1234.56', EN, currency=code),
                                 '-' + symbol + '1,234.56')

    def test_explicit_currency_overrides_default_without_conversion(self):
        self.assertEqual(formatting.format_currency('25', EN, currency='EUR'), '€25.00')
        self.assertEqual(formatting.format_currency('25', EN), '$25.00')

    def test_invalid_inputs_do_not_render_as_money(self):
        for value in ('NaN', 'Infinity', '-Infinity', 'bad', None, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                formatting.format_currency(value, FI)
        for decimals in (-1, 7, 2.5, True):
            with self.assertRaises(ValueError):
                formatting.format_number(1, FI, decimals=decimals)
        with self.assertRaises(ValueError):
            formatting.format_number(1, dict(FI, number_format='unknown'))
        with self.assertRaises(ValueError):
            formatting.format_currency(1, FI, currency='unknown')

    def test_format_style_is_independent_of_interface_language(self):
        with patch.object(i18n, 'LANGUAGE', 'en'):
            self.assertEqual(formatting.format_number('1234.56', FI), '1\u00a0234,56')
        with patch.object(i18n, 'LANGUAGE', 'fi'):
            self.assertEqual(formatting.format_number('1234.56', EN), '1,234.56')

    def test_about_values_and_copied_report_use_selected_style(self):
        with patch.object(i18n, 'LANGUAGE', 'en'):
            memory = system_info.memory_size('MemTotal: 8388608 kB', FI)
            self.assertEqual(memory, '8,0 GiB usable')
            self.assertEqual(system_info.format_report([('Memory', memory)]), 'Memory: 8,0 GiB usable')
            self.assertEqual(system_info.memory_size('MemTotal: 8388608 kB', EN), '8.0 GiB usable')
            self.assertEqual(system_info.format_bytes(1536, FI), '1,5 KiB')

    def test_about_refresh_takes_one_consistent_preference_snapshot(self):
        with patch.object(system_info, 'read_preferences', return_value=FI) as read, \
                patch.object(system_info.shutil, 'which', return_value=None), \
                patch.object(system_info, 'memory_size', return_value='memory') as memory, \
                patch.object(system_info, 'storage', return_value='storage') as storage:
            system_info.collect()
            read.assert_called_once_with()
            self.assertEqual(memory.call_args.args[1], FI)
            for call in storage.call_args_list:
                self.assertEqual(call.args[1], FI)


class FormatPreferencesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        env = patch.dict(os.environ, {'XDG_CONFIG_HOME': temp.name})
        env.start()
        self.addCleanup(env.stop)

    def test_legacy_preferences_keep_existing_choices(self):
        legacy = {'clock': '12', 'date': 'iso', 'week_start': 'sunday'}
        path = region.preferences_path()
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(legacy))
        loaded = region.read_preferences(strict=True)
        self.assertEqual(loaded, dict(legacy, number_format='fi', currency='EUR'))
        # Reading does not rewrite a user's existing settings.
        self.assertEqual(json.loads(path.read_text()), legacy)
        region.save_preferences(loaded)
        self.assertEqual(region.read_preferences(strict=True), loaded)

    def test_saved_formats_take_effect_on_next_read_and_preserve_language(self):
        i18n.save_language('fi')
        language_bytes = i18n.language_path().read_bytes()
        region.save_preferences(FI)
        self.assertEqual(formatting.format_currency('1234.56'), '1\u00a0234,56\u00a0€')
        region.save_preferences(EN)
        self.assertEqual(formatting.format_currency('1234.56'), '$1,234.56')
        self.assertEqual(i18n.language_path().read_bytes(), language_bytes)

    def test_invalid_choices_cannot_replace_valid_settings(self):
        region.save_preferences(FI)
        original = region.preferences_path().read_bytes()
        for key in ('number_format', 'currency'):
            with self.assertRaises(ValueError):
                region.save_preferences(dict(FI, **{key: 'unsupported'}))
            self.assertEqual(region.preferences_path().read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
