#!/usr/bin/env python3
"""Security-key unlock for the KDE lock screen (KUM-31).

  security_key.py            read-only status
  security_key.py install    back up and install plasma/pam/kde-smartcard as
                             /etc/pam.d/kde-smartcard (uses your sudo)
  security_key.py remove     remove that override; KDE's vendor file applies again

kscreenlocker runs the `kde-smartcard` PAM service in parallel with the password
service `kde`. The override makes a touch of the security key unlock the lock
screen; the password keeps working. No other PAM file is changed.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / 'pam' / 'kde-smartcard'
TARGET = Path('/etc/pam.d/kde-smartcard')
VENDOR = Path('/usr/lib/pam.d/kde-smartcard')
MODULE = Path('/usr/lib/security/pam_u2f.so')
BACKUP_DIR = Path('/etc/pam.d')
BACKUP_PREFIX = 'kde-smartcard.kumios-backup.'


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


def problems(user, template=TEMPLATE, module=MODULE):
    """Why installing would not give a working key unlock (empty when ready)."""
    found = []
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
        return 'not installed (KDE vendor kde-smartcard applies)'
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
        print('Ready to install.' if not found else 'Not ready: ' + '; '.join(found))
        print(f'Password unlock (PAM service kde) is not changed by this tool. Vendor file: {VENDOR}')
        print('Read-only check: nothing changed.')
    elif args.action == 'install':
        backup = install(user)
        print(f'Installed {TARGET}.' + (f' Previous override backed up to {backup}.' if backup else ''))
        print('A key touch now unlocks the lock screen; the password still works.')
        print('Undo: python3 plasma/security_key.py remove' + (f' --restore {backup}' if backup else ''))
    else:
        print(f'{TARGET} {remove(args.restore)}; '
              + ('the earlier override is back.' if args.restore else "KDE's vendor kde-smartcard applies again."))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print('KumiOS security key setup failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
