#!/usr/bin/env python3
"""Screenshots of the lock screen and the login screen for a side-by-side look (KUM-32).

Each runs inside its own virtual KWin (1600x900) in a private D-Bus session with
copies of the user's appearance config, so neither the session nor greetd is
touched: kscreenlocker_greet --testing for the lock screen, and ReGreet --demo
with the theme plasma/greeter/setup.py would install for the login screen.
Writes lockscreen.png and loginscreen.png to the given directory.
"""
from pathlib import Path
import importlib.util
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[2]
SIZE = ('1600', '900')


def nested(home, script, out, name):
    session = home / f'{name}.sh'
    session.write_text(textwrap.dedent(f'''\
        #!/bin/sh
        {script} > {out}/{name}.log 2>&1 &
        sleep 7
        spectacle -b -n -f -o {out}/{name}.png > /dev/null 2>&1
        sleep 1
        kill %1 2>/dev/null
        '''))
    session.chmod(0o755)
    env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'USER': os.environ.get('USER', ''),
           'XDG_CONFIG_HOME': str(home / 'config'), 'XDG_DATA_HOME': str(Path.home() / '.local/share'),
           'XDG_DATA_DIRS': '/usr/local/share:/usr/share', 'XDG_CACHE_HOME': str(home / 'cache'),
           'XDG_RUNTIME_DIR': str(home), 'QT_FORCE_STDERR_LOGGING': '1'}
    process = subprocess.Popen(['dbus-run-session', '--', 'kwin_wayland', '--virtual', '--width', SIZE[0],
                                '--height', SIZE[1], '--no-lockscreen', '--no-global-shortcuts',
                                '--exit-with-session', str(session)],
                               env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        process.wait(timeout=60)
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    return (out / f'{name}.png').is_file()


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix='kumios-look-'))
    out.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('greeter_setup', ROOT / 'plasma/greeter/setup.py')
    greeter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(greeter)
    with tempfile.TemporaryDirectory(prefix='kumios-look-home-') as home:
        home = Path(home)
        config = home / 'config'
        (config / 'kdedefaults').mkdir(parents=True)
        real = Path.home() / '.config'
        for name in ('kdeglobals', 'plasmarc', 'kscreenlockerrc', greeter.APPLETSRC if hasattr(greeter, 'APPLETSRC')
                     else 'plasma-org.kde.plasma.desktop-appletsrc'):
            if (real / name).is_file():
                shutil.copy2(real / name, config / name)
        for item in (real / 'kdedefaults').glob('*'):
            shutil.copy2(item, config / 'kdedefaults' / item.name)
        stage = home / 'stage'
        stage.mkdir()
        greetd = home / 'greetd.toml'
        greetd.write_text('[default_session]\ncommand = "placeholder"\nuser = "greeter"\n')
        with_config = greeter.CONFIG
        greeter.CONFIG = config
        try:
            greeter.prepare(stage, None, config / 'kdeglobals', greetd_config=greetd)
        finally:
            greeter.CONFIG = with_config
        results = {
            'lockscreen': nested(home, '/usr/lib/kscreenlocker_greet --testing', out, 'lockscreen'),
            'loginscreen': nested(home, f'regreet --demo --config {stage}/regreet.toml --style {stage}/regreet.css'
                                  f' --logs {out}/regreet-demo.log', out, 'loginscreen'),
        }
    for name, ok in results.items():
        print(('PASS ' if ok else 'FAIL ') + f'{name}: {out / (name + ".png")}')
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
