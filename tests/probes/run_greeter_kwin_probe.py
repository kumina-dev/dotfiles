#!/usr/bin/env python3
"""Pre-check for running the login greeter on KWin (KUM-29), without greetd.

Starts a virtual (offscreen) KWin in a private D-Bus session with temporary
HOME/XDG directories and runs ReGreet in demo mode (fake authentication) inside
it, using the theme plasma/greeter/setup.py would install. A KWin script reports
ReGreet's window, so the probe checks that it maps, goes fullscreen and stays up.
It never touches greetd, PAM, /etc or the live session. DRM, seat and the real
greeter account cannot be exercised this way; the logout test covers those.
"""
from pathlib import Path
import importlib.util
import os
import re
import signal
import subprocess
import sys
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[2]
WIDTH, HEIGHT = 1280, 800
SCRIPT = '''
const windows = workspace.windowList().filter(w => /regreet/i.test(w.resourceClass + " " + w.resourceName));
for (const w of windows)
    print("KUMIOS_WINDOW class=" + w.resourceClass + " fullscreen=" + w.fullScreen
          + " size=" + Math.round(w.frameGeometry.width) + "x" + Math.round(w.frameGeometry.height));
print("KUMIOS_COUNT " + windows.length);
'''


def main():
    spec = importlib.util.spec_from_file_location('greeter_setup', ROOT / 'plasma/greeter/setup.py')
    greeter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(greeter)
    with tempfile.TemporaryDirectory(prefix='kumios-greeter-kwin-') as home:
        home = Path(home)
        stage = home / 'stage'
        stage.mkdir()
        wallpaper = Path('/usr/share/wallpapers/Next/contents/images_dark')
        image = max(wallpaper.glob('*.png'), default=None) if wallpaper.is_dir() else None
        if image is None:
            print('FAIL: no KDE wallpaper available for the demo')
            return 1
        greetd = home / 'greetd.toml'
        greetd.write_text('[default_session]\ncommand = "placeholder"\nuser = "greeter"\n')
        greeter.prepare(stage, image, home / 'no-kdeglobals', greetd_config=greetd)   # Breeze Dark defaults
        (home / 'query.js').write_text(SCRIPT)
        session = home / 'session.sh'
        session.write_text(textwrap.dedent(f'''\
            #!/bin/sh
            regreet --demo --config {stage}/regreet.toml --style {stage}/regreet.css --logs {home}/regreet.log &
            pid=$!
            sleep 6
            id=$(qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript {home}/query.js kumios-probe 2>&1)
            echo "KUMIOS_SCRIPT_ID $id"
            qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.start 2>&1 | sed 's/^/KUMIOS_RUN /'
            sleep 1
            kill -0 $pid 2>/dev/null && echo KUMIOS_ALIVE || echo KUMIOS_EXITED
            kill $pid 2>/dev/null
            '''))
        session.chmod(0o755)
        env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'XDG_CONFIG_HOME': str(home / 'config'),
               'XDG_DATA_HOME': str(home / 'data'), 'XDG_CACHE_HOME': str(home / 'cache'),
               'XDG_STATE_HOME': str(home / 'state'), 'XDG_RUNTIME_DIR': str(home),
               # Qt logs to the journal when not on a terminal; keep the script output here.
               'QT_FORCE_STDERR_LOGGING': '1', 'QT_LOGGING_RULES': 'kwin_scripting.debug=true'}
        process = subprocess.Popen(
            ['dbus-run-session', '--', 'kwin_wayland', '--virtual', '--width', str(WIDTH), '--height', str(HEIGHT),
             '--no-lockscreen', '--no-global-shortcuts', '--exit-with-session', str(session)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        try:
            output, _ = process.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            output = ''
            print('FAIL: KWin session did not finish')
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        log = (home / 'regreet.log').read_text(errors='replace') if (home / 'regreet.log').exists() else ''
    windows = re.findall(r'KUMIOS_WINDOW class=(\S+) fullscreen=(\w+) size=(\d+)x(\d+)', output)
    checks = [
        ('ReGreet window mapped under KWin', len(windows) == 1, f'{len(windows)} window(s)'),
        ('ReGreet fullscreen', bool(windows) and windows[0][1] == 'true', windows[0][1] if windows else 'n/a'),
        ('covers the output', bool(windows) and (int(windows[0][2]), int(windows[0][3])) == (WIDTH, HEIGHT),
         f'{windows[0][2]}x{windows[0][3]}' if windows else 'n/a'),
        ('ReGreet still running after 7 s', 'KUMIOS_ALIVE' in output, ''),
        ('no ReGreet errors logged', not re.search(r'\bERROR\b|panicked', log), ''),
    ]
    failures = 0
    for label, ok, detail in checks:
        failures += not ok
        print(('PASS ' if ok else 'FAIL ') + label + (f' ({detail})' if detail else ''))
    if failures:
        print('--- KWin/ReGreet output (tail) ---')
        print('\n'.join(output.splitlines()[-25:]))
        print('\n'.join(log.splitlines()[-15:]))
    print(f'Totals: {len(checks) - failures} passed, {failures} failed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
