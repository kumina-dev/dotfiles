#!/usr/bin/env python3
"""Interactive: does a security-key touch unlock KDE's lock screen? (KUM-31)

Runs kscreenlocker_greet in --testing mode inside a virtual KWin in a private
D-Bus session, so the real session is never locked. The greeter authenticates
through the real PAM services as the current user. A screenshot shows whether
the smartcard (security key) authenticator is offered; then the user touches
the key. The greeter exits 0 when authentication succeeds. Typing the password
into the virtual output is not possible here; check the password on a real lock.
"""
from pathlib import Path
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[2]
WAIT = 45


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='kumios-unlock-probe-out-'))
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='kumios-unlock-probe-') as home:
        home = Path(home)
        config = home / 'config'
        (config / 'kdedefaults').mkdir(parents=True)
        real = Path.home() / '.config'
        for name in ('kdeglobals', 'plasmarc', 'kscreenlockerrc'):
            if (real / name).is_file():
                shutil.copy2(real / name, config / name)
        for item in (real / 'kdedefaults').glob('*'):
            shutil.copy2(item, config / 'kdedefaults' / item.name)
        session = home / 'session.sh'
        session.write_text(textwrap.dedent(f'''\
            #!/bin/sh
            /usr/lib/kscreenlocker_greet --testing > {out}/greet.log 2>&1 &
            pid=$!
            sleep 5
            spectacle -b -n -f -o {out}/lockscreen.png > /dev/null 2>&1
            echo KUMIOS_READY_TOUCH_KEY_NOW
            i=0
            while kill -0 $pid 2>/dev/null && [ $i -lt {WAIT} ]; do sleep 1; i=$((i+1)); done
            if kill -0 $pid 2>/dev/null; then echo KUMIOS_TIMEOUT; kill $pid; else wait $pid; echo KUMIOS_EXIT $?; fi
            '''))
        session.chmod(0o755)
        env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'USER': os.environ.get('USER', ''),
               'XDG_CONFIG_HOME': str(config), 'XDG_DATA_HOME': str(Path.home() / '.local/share'),
               'XDG_DATA_DIRS': '/usr/local/share:/usr/share', 'XDG_CACHE_HOME': str(home / 'cache'),
               'XDG_RUNTIME_DIR': str(home), 'QT_FORCE_STDERR_LOGGING': '1'}
        print(f'Touch your security key when asked (within {WAIT} s).', flush=True)
        process = subprocess.Popen(
            ['dbus-run-session', '--', 'kwin_wayland', '--virtual', '--width', '1600', '--height', '900',
             '--no-lockscreen', '--no-global-shortcuts', '--exit-with-session', str(session)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        lines = []
        try:
            for line in process.stdout:
                lines.append(line)
                if 'KUMIOS_READY_TOUCH_KEY_NOW' in line:
                    print('>>> Touch the security key now.', flush=True)
            process.wait(timeout=WAIT + 30)
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    text = ''.join(lines)
    unlocked = 'KUMIOS_EXIT 0' in text
    print(('PASS' if unlocked else 'FAIL') + ': key touch unlocked the testing lock screen'
          + ('' if unlocked else (' (timed out)' if 'KUMIOS_TIMEOUT' in text else ' (greeter exited non-zero)')))
    print(f'Screenshot: {out / "lockscreen.png"}; greeter log: {out / "greet.log"}')
    return 0 if unlocked else 1


if __name__ == '__main__':
    sys.exit(main())
