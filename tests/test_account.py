import grp
import os
from pathlib import Path
import pwd
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hypr/.config/hypr/scripts'))
from kumina_common import i18n
from settings_app import account


def user_entry(*, name='kumina', uid=1000, gid=1000, gecos='Ville,Office,Phone', home='/home/kumina', shell='/bin/bash'):
    return pwd.struct_passwd((name, 'PASSWORD-MUST-NOT-BE-COPIED', uid, gid, gecos, home, shell))


class AccountTests(unittest.TestCase):
    def setUp(self):
        patches = [
            patch.object(i18n, 'LANGUAGE', 'en'),
            patch.object(account.os, 'getuid', return_value=1000),
            patch.object(account.os, 'getgid', return_value=1000),
            patch.object(account.os, 'getgroups', return_value=[998, 1000, 998]),
            patch.object(account.pwd, 'getpwuid', return_value=user_entry()),
            patch.object(account.grp, 'getgrgid', side_effect=lambda gid: grp.struct_group(
                ({1000: 'kumina', 998: 'wheel'}.get(gid, 'group'), 'GROUP-SECRET', gid, []))),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def test_collect_uses_uid_not_environment_identity(self):
        with patch.dict(os.environ, USER='someone-else', LOGNAME='other', HOME='/tmp/fake'):
            info = account.collect()
        account.pwd.getpwuid.assert_called_once_with(1000)
        self.assertEqual(info.username, 'kumina')
        self.assertEqual(info.home, '/home/kumina')
        self.assertEqual(info.shell, '/bin/bash')
        self.assertEqual(info.uid, 1000)

    def test_only_name_from_gecos_is_copied_and_no_password_fields(self):
        info = account.collect()
        report = account.format_report(info)
        self.assertEqual(info.full_name, 'Ville')
        self.assertEqual(info.display_name, 'Ville')
        self.assertIn('Full name: Ville', report)
        for secret in ('Office', 'Phone', 'PASSWORD-MUST-NOT-BE-COPIED', 'GROUP-SECRET'):
            self.assertNotIn(secret, report)

    def test_session_groups_are_deduplicated_with_kernel_primary_group(self):
        info = account.collect()
        self.assertEqual(info.primary_group, 'kumina (1000)')
        self.assertEqual(info.session_groups, 'wheel (998), kumina (1000)')
        with patch.object(account.os, 'getgroups', return_value=[]):
            self.assertEqual(account.collect().session_groups, 'kumina (1000)')

    def test_database_primary_and_active_session_groups_can_differ(self):
        with patch.object(account.pwd, 'getpwuid', return_value=user_entry(gid=1234)):
            info = account.collect()
        self.assertEqual(info.primary_group, 'group (1234)')
        self.assertNotIn('1234', info.session_groups)

    def test_unknown_group_retains_numeric_identity(self):
        with patch.object(account.grp, 'getgrgid', side_effect=KeyError):
            info = account.collect()
        self.assertEqual(info.primary_group, 'Unknown group (GID 1000)')
        self.assertIn('GID 998', info.session_groups)

    def test_session_lookup_failure_does_not_hide_account(self):
        with patch.object(account.os, 'getgroups', side_effect=OSError):
            info = account.collect()
        self.assertEqual(info.session_groups, 'Unavailable')
        self.assertEqual(info.username, 'kumina')

    def test_missing_user_is_reported_without_environment_fallback(self):
        for error in (KeyError(1000), OSError('Lookup failed')):
            with patch.object(account.pwd, 'getpwuid', side_effect=error):
                with self.assertRaisesRegex(account.AccountError, 'user ID 1000'):
                    account.collect()

    def test_missing_fields_have_clear_labels_and_username_fallback(self):
        with patch.object(account.pwd, 'getpwuid', return_value=user_entry(gecos='', shell='', home='')):
            info = account.collect()
        rows = dict(info.rows())
        self.assertEqual(info.display_name, 'kumina')
        self.assertEqual(rows['Full name'], 'Not set')
        self.assertEqual(rows['Home directory'], 'Not set')
        self.assertEqual(rows['Login shell'], 'System default')

    def test_finnish_labels_preserve_ids_and_account_values(self):
        with patch.object(i18n, 'LANGUAGE', 'fi'):
            rows = dict(account.collect().rows())
        self.assertEqual(rows['Käyttäjätunnus'], 'kumina')
        self.assertEqual(rows['Käyttäjän ID'], '1000')
        self.assertEqual(rows['Kotihakemisto'], '/home/kumina')

    def test_special_characters_are_kept_as_plain_text(self):
        with patch.object(account.pwd, 'getpwuid', return_value=user_entry(gecos='<Ville> & {name}\nsecond line')):
            info = account.collect()
        self.assertEqual(info.display_name, '<Ville> & {name}\nsecond line')
        self.assertIn('Full name: <Ville> & {name}\n  second line', account.format_report(info))


if __name__ == '__main__':
    unittest.main()
