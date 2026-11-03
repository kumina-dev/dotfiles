# KumiOS login greeter

greetd + ReGreet, themed from KDE and run on KWin. This is a system configuration
package installed into `/etc/greetd` with sudo, **not** a dotfile link.

- **Colors** come from KDE: your active color scheme and the wallpaper accent in
  `~/.config/kdeglobals` (falling back to `kdedefaults/`, then to Breeze Dark).
- **Wallpaper** defaults to Plasma's current desktop wallpaper, read from
  `~/.config/plasma-org.kde.plasma.desktop-appletsrc`. A KDE wallpaper package
  uses its largest image, preferring its dark variant in dark mode.
- **Light/Dark** follows the current KDE variant (ReGreet's GTK dark preference).
- **Compositor:** install makes greetd start ReGreet on KWin, as SDDM runs its
  Wayland greeter:
  `dbus-run-session -- kwin_wayland --drm --no-lockscreen --no-global-shortcuts --locale1 --exit-with-session /usr/bin/regreet`.
  Only the `command` in `[default_session]` of `/etc/greetd/config.toml` changes;
  the greeter user, TTY and any other section stay as they are. greetd and PAM
  authentication are not changed.

The theme is a snapshot. After changing the wallpaper or Light/Dark, run preview
and install again to update the login screen. The snapshot makes the wallpaper
readable by the greeter account even when your home directory is not.

## Look: mirrors the lock screen

`style.css` styles ReGreet like KDE's lock screen, so the login screen, lock
screen and desktop look like one system: the desktop wallpaper blurred and
dimmed, a large Noto Sans clock with the date below, the controls floating on the
wallpaper instead of a card, Breeze-like fields with the KDE accent as focus
ring, the accent Login button, and flat Reboot/Power Off buttons.
`tests/probes/run_lock_login_look_probe.py` renders both screens offscreen for
a side-by-side comparison.

ReGreet's layout itself cannot be changed: it shows a greeting and user/session
selectors instead of the lock screen's avatar. User/session selection, password
visibility, authentication prompts, cancellation and power controls remain
ReGreet's own UI. The clock format (`CLOCK_FORMAT` in `setup.py`) uses Pango
markup; any `%` in it is a clock code, and an unknown one crashes ReGreet's clock,
which the tests guard against.

## Security key

greetd's PAM stack (`/etc/pam.d/greetd`, not managed by this repository) has
`pam_u2f` (touch only) as `sufficient` before the password. At the login screen,
pick the user and session, choose Login, and ReGreet shows the key's touch
prompt; a touch logs in. With the key unplugged, or if it is not touched, the
password prompt follows. Touch only means possession of the key logs in. A
key-only login does not unlock password-based keyrings (gnome-keyring/KWallet),
which may then ask for the password once. The lock screen's key unlock is
configured separately: see `../security_key.py` and the runbook.

## Preview

As your normal desktop user, from the repository:

```sh
python3 plasma/greeter/setup.py preview
```

It prints the colors and wallpaper it uses and the greetd command install would
set, then opens ReGreet's demo window (fake authentication: any demo password or
OTP in its log belongs to the demo, not your account; reboot/shutdown are skipped).
Close it with your normal close-window shortcut. Override the sources with
`--wallpaper PATH` and `--colors PATH` (a `kdeglobals` or `*.colors` file).

The KWin side can be checked without greetd: `python3 tests/probes/run_greeter_kwin_probe.py`
runs the demo under a virtual KWin in a private session and checks that the window
maps, goes fullscreen and stays up. It cannot exercise DRM, the seat or the greeter
account; the first real logout does.

## Install

After reviewing the preview:

```sh
python3 plasma/greeter/setup.py install
```

Before using sudo it checks that `dbus-run-session`, `kwin_wayland` and `regreet`
exist. It backs up the current files in `/etc/greetd/kumios-backup.XXXXXX` and
prints that path: keep it. It then installs root-owned, world-readable copies and
verifies that the greeter account can read them, in this order:

1. `/etc/greetd/kumios-wallpaper.png`
2. `/etc/greetd/regreet.css`
3. `/etc/greetd/regreet.toml` (includes the `systemctl reboot`/`poweroff` commands)
4. `/etc/greetd/config.toml` (launch command, last)

If any step fails, the backup is restored automatically. Nothing is restarted: the
new greeter starts at the next normal logout or reboot. Earlier Hyprland greeter
files (`/etc/greetd/hyprland.lua`) are left in place but no longer used.

## Restore and recovery

Use the backup directory printed by the installer:

```sh
python3 plasma/greeter/setup.py restore /etc/greetd/kumios-backup.XXXXXX
```

This restores the previous files, including the previous launch command, and
removes files that were absent before. If the login screen does not appear after a
logout, switch to a text console with **Ctrl+Alt+F2**, log in there, run the
restore command from the repository, then run `sudo systemctl restart greetd` (or
reboot). Before installing, note the backup path somewhere you can read from a
text console.
