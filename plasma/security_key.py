#!/usr/bin/env python3
"""Security-key unlock for the KDE lock screen (KUM-31).

  security_key.py            read-only status
  security_key.py install    back up and install plasma/pam/kde-fingerprint as
                             /etc/pam.d/kde-fingerprint (uses your sudo)
  security_key.py remove     remove that override; KDE's vendor file applies again

kscreenlocker 6.8 runs the `kde-fingerprint` PAM service in parallel with the
password service `kde` (its other methods, including kde-u2f, replace the
password box instead). The override makes a touch of the security key unlock the
lock screen while the password keeps working. No other PAM file is changed.
install also removes the unused /etc/pam.d/kde-smartcard override that earlier
0.5.0-dev builds installed, when it is unmodified KumiOS content.
"""
import argparse
import configparser
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / 'pam' / 'kde-fingerprint'
TARGET = Path('/etc/pam.d/kde-fingerprint')
VENDOR = Path('/usr/lib/pam.d/kde-fingerprint')
OBSOLETE = Path('/etc/pam.d/kde-smartcard')
OBSOLETE_MARK = '# KumiOS: unlock the KDE lock screen by touching the security key'
LOCKER_RC = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'kscreenlockerrc'
MODULE = Path('/usr/lib/security/pam_u2f.so')
BACKUP_DIR = Path('/etc/pam.d')
BACKUP_PREFIX = 'kde-fingerprint.kumios-backup.'


def authfile(text):
    match = re.search(r'pam_u2f\.so\b[^\n]*\bauthfile=(\S+)', text)
    return Path(match[1]) if match else None


def mapped(mapping, user):
    """Number of key credentials mapped to `user` in a pam_u2f authfile (0 if none)."""
    try:
        for line in mapping.read_text().splitlines():
            fields = line.split(':')
            if fields and fields[0] == user:
                return len(fields) - 1
    except OSError:
        pass
    return 0


def fingerprint_enabled(rc=LOCKER_RC):
    """kscreenlocker's [Authenticators] Fingerprint switch (default on)."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read_string(rc.read_text())
    except (OSError, configparser.Error):
        return True
    return parser.get('Authenticators', 'Fingerprint', fallback='true').strip().lower() != 'false'


def obsolete_ours(path=OBSOLETE):
    """True when `path` is the unmodified kde-smartcard override an earlier build installed."""
    try:
        return not path.is_symlink() and OBSOLETE_MARK in path.read_text()
    except OSError:
        return False


def problems(user, template=TEMPLATE, module=MODULE, rc=LOCKER_RC):
    """Why installing would not give a working key unlock (empty when ready)."""
    found = []
    if not fingerprint_enabled(rc):
        found.append(f'the lock screen fingerprint method is turned off ([Authenticators] Fingerprint=false in {rc})')
    if not module.is_file():
        found.append(f'pam_u2f is not installed ({module})')
    mapping = authfile(template.read_text())
    if mapping is None:
        found.append('the template has no pam_u2f authfile')
    elif not mapped(mapping, user):
        found.append(f'no security key is registered for {user} in {mapping}')
    return found


def state(target=TARGET, template=TEMPLATE):
    if not target.exists():
        return 'not installed (KDE vendor kde-fingerprint applies)'
    try:
        same = target.read_text() == template.read_text()
    except OSError:
        same = False
    return 'installed (matches the repository)' if same else 'installed, but differs from the repository template'


def sudo(*args):
    return subprocess.run(['sudo', *[str(a) for a in args]], check=True)


def install(user):
    found = problems(user)
    if found:
        raise ValueError('; '.join(found) + '. Not installing.')
    if TARGET.is_symlink():
        raise ValueError(f'{TARGET} is a symlink; not replacing it.')
    backup = None
    if TARGET.exists():
        backup = subprocess.check_output(['sudo', 'mktemp', str(BACKUP_DIR / (BACKUP_PREFIX + 'XXXXXX'))],
                                         text=True).strip()
        sudo('cp', '-a', TARGET, backup)
    sudo('install', '-o', 'root', '-g', 'root', '-m', '644', TEMPLATE, TARGET)
    if obsolete_ours():
        sudo('rm', '-f', OBSOLETE)
    return backup


def remove(backup=None):
    if backup:
        backup = Path(backup)
        if backup.parent != BACKUP_DIR or not backup.name.startswith(BACKUP_PREFIX):
            raise ValueError(f'Use a {BACKUP_DIR / BACKUP_PREFIX}* file printed by install.')
        sudo('cp', '-a', '--remove-destination', backup, TARGET)
        return 'restored'
    sudo('rm', '-f', TARGET)
    return 'removed'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', nargs='?', choices=('install', 'remove'))
    parser.add_argument('--restore', metavar='BACKUP', help='with remove: restore this earlier override instead')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run as your normal user; sudo is requested when needed.')
    user = os.environ.get('USER') or Path.home().name
    if args.action is None:
        found = problems(user)
        print('Lock screen key unlock: ' + state())
        if found:
            print('Not ready: ' + '; '.join(found))
        elif not TARGET.exists():
            print('Ready to install.')
        if obsolete_ours():
            print(f'Unused earlier override {OBSOLETE} is present; install removes it.')
        print(f'Password unlock (PAM service kde) is not changed by this tool. Vendor file overridden: {VENDOR}')
        print('Read-only check: nothing changed.')
    elif args.action == 'install':
        backup = install(user)
        print(f'Installed {TARGET}.' + (f' Previous override backed up to {backup}.' if backup else ''))
        if not OBSOLETE.exists():
            print(f'{OBSOLETE} is not present (KDE vendor file applies).')
        print('A key touch now unlocks the lock screen; the password still works.')
        print('Undo: python3 plasma/security_key.py remove' + (f' --restore {backup}' if backup else ''))
    else:
        print(f'{TARGET} {remove(args.restore)}; '
              + ('the earlier override is back.' if args.restore else "KDE's vendor kde-fingerprint applies again."))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print('KumiOS security key setup failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
