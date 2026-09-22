# KumiOS greeter

ReGreet 0.5.0 theme for the existing greetd + Hyprland Lua setup. This is a
system configuration package, **not a Stow package**.

The theme adds the current wallpaper, exported Matugen colors, rounded controls,
a KumiOS greeting, and a 24-hour clock. User/session selection, password visibility,
authentication prompts, cancellation, and power controls remain ReGreet's own UI.
The font is Noto Sans with the normal system fallback.

## Preview

From the dotfiles repository, as your normal desktop user:

```sh
python3 greeter/setup.py preview
```

Close the demo window with your normal close-window shortcut. Demo mode uses
fake authentication; it does not log you into a real session. Any demo password
or OTP shown in its log belongs to the demo, not your account. ReGreet demo mode
also skips reboot and shutdown actions. GTK warnings or a missing image should
be resolved before installation.

The default image is `~/Pictures/Wallpapers/main.png`. The default colors come
from `$XDG_CONFIG_HOME/gtk-4.0/matugen.css` (normally `~/.config/gtk-4.0/matugen.css`).
Only known literal hex colors are exported. Missing palette entries use a
built-in dark palette; a missing wallpaper stops the operation.

You can override either source for both preview and install:

```sh
python3 greeter/setup.py preview --wallpaper /path/to/image.png --colors /path/to/matugen.css
```

## Install

After reviewing the preview:

```sh
python3 greeter/setup.py install
```

The script uses sudo only for the system installation, backs up existing theme
files in `/etc/greetd/kumios-backup.XXXXXX`, and prints the exact rollback command.
Keep that path. It replaces these three files with root-owned, world-readable
copies and verifies that the greeter account can read them:

- `/etc/greetd/regreet.toml`
- `/etc/greetd/regreet.css`
- `/etc/greetd/kumios-wallpaper.png`

The new TOML includes the current `systemctl reboot` and `systemctl poweroff`
commands. If you later customize ReGreet's configuration, merge those changes
into this helper before reinstalling; install replaces the entire ReGreet TOML.
Wallpaper and colors are an explicit snapshot. After changing the desktop theme,
rerun preview and install to update the greeter. This makes the selected wallpaper
available to all local users, even when your home directory is inaccessible.

The helper does not modify greetd's `config.toml`, `hyprland.lua`, PAM, or restart
any service. The theme appears on the next normal logout or reboot. ReGreet's
default stylesheet path is `/etc/greetd/regreet.css`, so the current launch
command needs no changes.

Clock language and timezone use system defaults. The clock format and greeting
are currently fixed, independent of per-user KumiOS Language & Region settings.
The remaining ReGreet labels are upstream labels, not KumiOS translations.

## Restore

Use the actual backup directory printed by the installer:

```sh
python3 greeter/setup.py restore /etc/greetd/kumios-backup.XXXXXX
```

This restores previous files and removes files that were absent before that
installation. It does not restart greetd. If the greeter cannot be used, run the
same command from a text console after signing in.

## Desktop verification

1. Preview: check wallpaper, readable text, visible focus while tabbing, account
   and session dropdowns, and password-entry layout. Close with your normal
   close-window shortcut.
2. Install, then log out normally: check the greeter appears and choose Hyprland.
3. Check failed authentication and cancellation, then sign in successfully.
4. Reopen the greeter on a later logout to check remembered user/session selection.

Automated snapshot and rollback-boundary checks are in
`tests/test_greeter_setup.py`. Actual GTK rendering and greetd authentication
must be verified on the Arch desktop.

Implementation references: the [ReGreet 0.5.0 source and documentation](https://github.com/rharish101/ReGreet/tree/0.5.0).
