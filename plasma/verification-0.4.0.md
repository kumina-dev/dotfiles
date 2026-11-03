# v0.4.0 verification — Plasma-only main, Hyprland preserved on a branch

Canonical repository evidence record for **v0.4.0**. Git identifies the tested
implementation; Linear (milestone "v0.4.0 — Plasma-only main, Hyprland preserved on a
branch", KUM-26–29) owns issue status and acceptance. Resume from `../SESSION_HANDOFF.md`.

Status 2026-11-03: accepted by the user (login greeter and kitty Light/Dark).
KUM-26–29 Done. Merged into `main`, versioned 0.4.0 and tagged `v0.4.0`.

## Scope and decisions

The user asked to move the Hyprland-era code off `main`, keep the pieces Plasma still
uses with Plasma-native sources, and make the docs match. User decisions, 2026-11-03:
switch the login greeter's compositor from Hyprland to KWin; retire the Hyprland
session links after a backup.

| Piece | Used by Plasma? | Outcome |
| --- | --- | --- |
| Hyprland config, GTK Settings/Calendar/Control Center, Waybar, SwayNC, fuzzel, matugen, `gtk/`, `set-wallpaper`, legacy docs and 15 tests | No | Branch `legacy/hyprland` (KUM-26) |
| Project version file | Yes | Root `VERSION` |
| kitty config | Yes (running) | `plasma/kitty/`, Breeze Light/Dark (KUM-27) |
| ReGreet login theme | Yes (every login) | `plasma/greeter/`, KDE colors/wallpaper (KUM-28) |
| Hyprland as the greeter's compositor | Yes (every login) | KWin (KUM-29) |

## Evidence

| Check | Result |
| --- | --- |
| `legacy/hyprland` | Pushed; full tree at v0.3.0 (116 `hypr/` files) with history and a README note |
| Plasma suites after removal | Python 60, QML 82, Node 5; all probes and read-only `setup.py`/`appearance.py` checks pass |
| Session links (KUM-26) | `~/.config/hypr`, `waybar`, `swaync`, `fuzzel`, `matugen`, `~/.local/bin/set-wallpaper` recorded and removed; ignored generated files (including the legacy Settings app's monitors/keyboard/mouse files) moved into `~/.config/kumios/hyprland-links-backup-*` |
| `tests/test_kitty_theme.py` (KUM-27) | 6 pass: mapping, all theme files, no colors in `kitty.conf`, committed themes match installed Breeze, kitty parses each theme |
| Live kitty | `~/.config/kitty` → `plasma/kitty`; desktop portal reports dark, so `dark-theme.auto.conf` applies |
| `tests/test_greeter_setup.py` (KUM-28/29) | 17 pass. It was wrongly removed with the legacy tests in `86b2e9c`, then restored and adapted |
| `tests/probes/run_greeter_kwin_probe.py` | 5/5: ReGreet demo under a virtual KWin maps, is fullscreen, covers the output, stays up, logs no errors |
| Greeter install (user, own sudo) | Backup `/etc/greetd/kumios-backup.xsQDDA`. Read-only check: only `[default_session].command` changed; dark theme, accent `#7133cf`, wallpaper identical to Plasma's `nebula.png`; files root-owned and world-readable |
| **User logout/login test** | **Passed** (2026-11-03): "The login screen works, reboot and power buttons are there". Afterwards greetd was active with no errors, Plasma was running on tty1, and Hyprland was no longer running |
| **User kitty check** | **Passed** (2026-11-03): "kitty switches with Light/Dark" |
| Docs | Every repository path referenced by the current docs exists; the legacy docs are linked on their branch |

## Pending

- Not exercised: greeter recovery from a failed start (restore path documented, not
  needed). The greeter theme is a snapshot, so reinstall it after wallpaper or
  Light/Dark changes.
