#!/usr/bin/env python3
"""Keep the login screen in sync with the desktop (KUM-33).

Run by the root service kumios-greeter-sync from a root-owned copy in
/usr/local/lib/kumios/greeter. Security boundaries:

* `stage` runs as the desktop user (dropped from root before any user file is
  opened): it resolves the user's colors, Light/Dark and wallpaper from KDE and
  writes them into a fresh directory root created for this run. A wallpaper path
  pointing at a file the user cannot read simply fails here.
* `apply` runs as root and never opens paths from the user's configuration. It
  reads only the two staged files, without following symlinks, accepting a
  regular single-link file owned by the user, a bounded size, a PNG/JPEG/WebP
  signature and exact #rrggbb colors. It renders regreet.toml and regreet.css
  itself and replaces only changed files, atomically. greetd's config.toml and PAM
  are never touched.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from desktop_appearance import DEFAULTS, current  # noqa: E402

# Load the greeter's setup.py from this directory by file path: a bare
# `import setup` could pick up another setup.py earlier on sys.path.
_spec = importlib.util.spec_from_file_location('kumios_greeter_setup', HERE / 'setup.py')
greeter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(greeter)

DEST = Path('/etc/greetd')
RUN_DIR = Path('/run/kumios-greeter-sync')
THEME_FILE = 'theme.json'
IMAGE_FILE = 'wallpaper'
MAX_IMAGE = 64 * 1024 * 1024
HEX = re.compile(r'#[0-9a-f]{6}')
OUTPUTS = ('kumios-wallpaper.png', 'regreet.css', 'regreet.toml')


def stage(directory, config=None):
    """As the user: write theme.json and a copy of the wallpaper into `directory`."""
    directory = Path(directory)
    colors, dark, wallpaper = current(config)
    if wallpaper is None:
        raise RuntimeError("Plasma's desktop wallpaper could not be found")
    with open(wallpaper, 'rb') as source:          # opened with the user's rights
        data = source.read(MAX_IMAGE + 1)
    if len(data) > MAX_IMAGE:
        raise ValueError('wallpaper is larger than 64 MiB')
    (directory / IMAGE_FILE).write_bytes(data)
    (directory / THEME_FILE).write_text(json.dumps({'colors': colors, 'dark': dark}))


def read_staged(path, owner, limit):
    """Bytes of a staged file: regular, not a symlink, single link, owned by `owner`."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        if not (info.st_mode & 0o170000 == 0o100000):
            raise ValueError(f'{path.name} is not a regular file')
        if info.st_uid != owner or info.st_nlink != 1:
            raise ValueError(f'{path.name} has an unexpected owner or link count')
        if info.st_size > limit:
            raise ValueError(f'{path.name} is too large')
        with os.fdopen(os.dup(fd), 'rb') as handle:
            data = handle.read(limit + 1)
    finally:
        os.close(fd)
    if len(data) > limit:
        raise ValueError(f'{path.name} is too large')
    return data


def image_kind(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    return None


def validate_theme(raw):
    """(colors, dark) from staged theme.json, or ValueError."""
    data = json.loads(raw)
    colors, dark = data.get('colors'), data.get('dark')
    if not isinstance(colors, dict) or set(colors) != set(DEFAULTS):
        raise ValueError('theme colors are missing or unexpected')
    if not all(isinstance(v, str) and HEX.fullmatch(v) for v in colors.values()):
        raise ValueError('theme colors must be #rrggbb')
    if not isinstance(dark, bool):
        raise ValueError('theme dark flag must be true or false')
    return colors, dark


def replace(target, data):
    """Atomically replace `target` with `data` (root-owned, 0644) when it differs."""
    try:
        if target.read_bytes() == data:
            return False
    except FileNotFoundError:
        pass
    fd, temporary = tempfile.mkstemp(prefix='.kumios-sync-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return True


def apply(directory, owner, dest=DEST, style=None):
    """As root: validate the staged files and install changed theme files. Returns names changed."""
    directory, dest = Path(directory), Path(dest)
    colors, dark = validate_theme(read_staged(directory / THEME_FILE, owner, 64 * 1024))
    image = read_staged(directory / IMAGE_FILE, owner, MAX_IMAGE)
    if image_kind(image) is None:
        raise ValueError('wallpaper is not a PNG, JPEG or WebP image')
    config, css = greeter.render(colors, dark, dest / OUTPUTS[0], style)
    changed = []
    # Same order as install: the image and stylesheet before the config that uses them.
    for name, data in zip(OUTPUTS, (image, css.encode(), config.encode())):
        if replace(dest / name, data):
            changed.append(name)
    return changed


def run(user):
    """As root: stage as `user` in a fresh directory, then apply."""
    if os.geteuid() != 0:
        raise PermissionError('run must be started as root (by kumios-greeter-sync.service)')
    account = pwd.getpwnam(user)
    RUN_DIR.mkdir(mode=0o711, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='stage-', dir=RUN_DIR))
    try:
        os.chown(directory, account.pw_uid, account.pw_gid)
        env = {'HOME': account.pw_dir, 'USER': user, 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'}
        subprocess.run([sys.executable, '-I', str(Path(__file__).resolve()), 'stage', str(directory)],
                       user=account.pw_uid, group=account.pw_gid, extra_groups=[], env=env,
                       cwd='/', check=True, timeout=120)
        return apply(directory, account.pw_uid)
    finally:
        for item in directory.iterdir():
            item.unlink(missing_ok=True)
        directory.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('stage').add_argument('directory', type=Path)
    sub.add_parser('run').add_argument('--user', required=True)
    args = parser.parse_args()
    if args.action == 'stage':
        if os.geteuid() == 0:
            parser.error('stage must not run as root')
        stage(args.directory)
    else:
        changed = run(args.user)
        print('Login screen updated: ' + ', '.join(changed) if changed else 'Login screen already in sync.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyError) as error:
        print('KumiOS login screen sync failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
