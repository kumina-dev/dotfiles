"""Security-key lock screen unlock (KUM-31). Nothing here runs sudo or touches /etc."""
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kumios_security_key', ROOT / 'plasma/security_key.py')
security_key = importlib.util.module_from_spec(spec)
spec.loader.exec_module(security_key)
TEMPLATE = (ROOT / 'plasma/pam/kde-fingerprint').read_text()


def rules(text, facility):
    return [line.split() for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith('#') and line.split()[0] == facility]


class TemplateTests(unittest.TestCase):
    def test_only_a_key_touch_can_pass_auth(self):
        auth = rules(TEMPLATE, 'auth')
        u2f = [r for r in auth if r[2] == 'pam_u2f.so']
        self.assertEqual(len(u2f), 1)
        self.assertEqual(u2f[0][1], 'required')
        modules = [r[2] for r in auth]
        # No password module or included stack that could accept a password here.
        for forbidden in ('pam_unix.so', 'system-auth', 'system-local-login', 'system-login', 'pam_permit.so'):
            self.assertNotIn(forbidden, modules)
        self.assertNotIn('include', [r[1] for r in auth])
        self.assertNotIn('sufficient', [r[1] for r in auth])

    def test_failures_never_count_towards_a_lockout(self):
        faillock = [r for r in rules(TEMPLATE, 'auth') if r[2] == 'pam_faillock.so']
        self.assertEqual(faillock, [['auth', 'requisite', 'pam_faillock.so', 'preauth']])
        self.assertNotIn('authfail', TEMPLATE.split('#')[0] + ''.join(
            l for l in TEMPLATE.splitlines() if not l.lstrip().startswith('#')))

    def test_touch_only_with_same_options_as_sudo(self):
        u2f = next(r for r in rules(TEMPLATE, 'auth') if r[2] == 'pam_u2f.so')
        self.assertEqual(u2f[3:], ['cue', 'authfile=/etc/Yubico/u2f_keys', 'origin=pam://arch', 'appid=pam://arch'])
        self.assertNotIn('pinverification', TEMPLATE)
        self.assertEqual(rules(TEMPLATE, 'password'), [['password', 'required', 'pam_deny.so']])

    def test_matches_the_systems_sudo_key_options_when_present(self):
        sudo = Path('/etc/pam.d/sudo')
        if not sudo.is_file() or 'pam_u2f' not in sudo.read_text():
            self.skipTest('no pam_u2f in /etc/pam.d/sudo')
        line = next(l for l in sudo.read_text().splitlines() if 'pam_u2f.so' in l and not l.lstrip().startswith('#'))
        self.assertEqual(re.findall(r'(?:authfile|origin|appid)=\S+', line),
                         re.findall(r'(?:authfile|origin|appid)=\S+', TEMPLATE))


class ToolTests(unittest.TestCase):
    def test_authfile_and_mapping(self):
        self.assertEqual(security_key.authfile(TEMPLATE), Path('/etc/Yubico/u2f_keys'))
        with tempfile.TemporaryDirectory() as temp:
            mapping = Path(temp, 'u2f_keys')
            mapping.write_text('alice:cred1,key1,es256,+presence:cred2,key2,es256,+presence\nbob:c,k,es256,+presence\n')
            self.assertEqual(security_key.mapped(mapping, 'alice'), 2)
            self.assertEqual(security_key.mapped(mapping, 'bob'), 1)
            self.assertEqual(security_key.mapped(mapping, 'carol'), 0)
            self.assertEqual(security_key.mapped(Path(temp, 'missing'), 'alice'), 0)

    def test_problems_block_install_without_module_or_mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            mapping = temp / 'keys'
            mapping.write_text('alice:c,k,es256,+presence\n')
            template = temp / 'kde-fingerprint'
            template.write_text(f'auth required pam_u2f.so cue authfile={mapping}\n')
            module = temp / 'pam_u2f.so'
            rc = temp / 'kscreenlockerrc'
            self.assertIn('pam_u2f is not installed', security_key.problems('alice', template, module, rc)[0])
            module.write_text('')
            self.assertEqual(security_key.problems('alice', template, module, rc), [])
            self.assertIn('no security key is registered for carol', security_key.problems('carol', template, module, rc)[0])
            rc.write_text('[Authenticators]\nFingerprint=false\n')
            self.assertIn('fingerprint method is turned off', security_key.problems('alice', template, module, rc)[0])

    def test_fingerprint_switch_defaults_on(self):
        with tempfile.TemporaryDirectory() as temp:
            rc = Path(temp, 'kscreenlockerrc')
            self.assertTrue(security_key.fingerprint_enabled(rc))
            rc.write_text('[Greeter]\nWallpaperPlugin=org.kde.image\n\n[Authenticators]\nUniversal2Factor=true\n')
            self.assertTrue(security_key.fingerprint_enabled(rc))
            rc.write_text('[Authenticators]\nFingerprint=False\n')
            self.assertFalse(security_key.fingerprint_enabled(rc))

    def test_obsolete_smartcard_override_removed_only_when_ours(self):
        with tempfile.TemporaryDirectory() as temp:
            old = Path(temp, 'kde-smartcard')
            self.assertFalse(security_key.obsolete_ours(old))
            old.write_text('auth required pam_sss.so\n')
            self.assertFalse(security_key.obsolete_ours(old))
            old.write_text(security_key.OBSOLETE_MARK + ' (KUM-31).\nauth required pam_u2f.so\n')
            self.assertTrue(security_key.obsolete_ours(old))
            link = Path(temp, 'link')
            link.symlink_to(old)
            self.assertFalse(security_key.obsolete_ours(link))
        calls = []
        with patch.object(security_key, 'problems', return_value=[]), \
             patch.object(security_key, 'sudo', side_effect=lambda *a: calls.append(a)), \
             patch.object(security_key, 'obsolete_ours', return_value=True), \
             patch.object(Path, 'is_symlink', return_value=False), patch.object(Path, 'exists', return_value=False):
            security_key.install('alice')
        self.assertEqual(calls[-1], ('rm', '-f', security_key.OBSOLETE))
        self.assertEqual(calls[0][-1], security_key.TARGET)

    def test_targets_the_service_run_beside_the_password(self):
        self.assertEqual(security_key.TARGET, Path('/etc/pam.d/kde-fingerprint'))
        self.assertTrue(security_key.TEMPLATE.is_file())

    def test_install_refuses_when_not_ready_without_sudo(self):
        with patch.object(security_key, 'problems', return_value=['pam_u2f is not installed']), \
             patch.object(security_key, 'sudo') as sudo:
            with self.assertRaisesRegex(ValueError, 'Not installing'):
                security_key.install('alice')
            sudo.assert_not_called()

    def test_install_backs_up_existing_override_then_installs_template(self):
        calls = []
        with patch.object(security_key, 'problems', return_value=[]), \
             patch.object(security_key, 'sudo', side_effect=lambda *a: calls.append(a)), \
             patch.object(security_key.subprocess, 'check_output', return_value='/etc/pam.d/kde-fingerprint.kumios-backup.x1\n'), \
             patch.object(security_key, 'obsolete_ours', return_value=False), \
             patch.object(Path, 'is_symlink', return_value=False), patch.object(Path, 'exists', return_value=True):
            backup = security_key.install('alice')
        self.assertEqual(backup, '/etc/pam.d/kde-fingerprint.kumios-backup.x1')
        self.assertEqual(calls[0][0], 'cp')
        self.assertEqual(calls[-1], ('install', '-o', 'root', '-g', 'root', '-m', '644',
                                     security_key.TEMPLATE, security_key.TARGET))

    def test_remove_validates_restore_source(self):
        with patch.object(security_key, 'sudo') as sudo:
            with self.assertRaises(ValueError):
                security_key.remove('/tmp/kde-fingerprint.kumios-backup.x')
            sudo.assert_not_called()
            self.assertEqual(security_key.remove(), 'removed')
            sudo.assert_called_once_with('rm', '-f', security_key.TARGET)


if __name__ == '__main__':
    unittest.main()
