# v0.5.0 verification — Unified lock screen and login with security key

Canonical repository evidence record for **v0.5.0**. Git identifies the tested
implementation (branch `kumios/lock-and-login`); Linear (milestone "v0.5.0 — Unified
lock screen and login with security key", KUM-30–33) owns issue status and
acceptance. Resume from `../SESSION_HANDOFF.md`.

Status 2026-11-04: accepted by the user. KUM-30–33 Done. Merged into `main`,
versioned 0.5.0 and tagged `v0.5.0`; the merged `kumios/lock-and-login` branch is deleted.

## Scope and decisions

The user asked for a lock screen with the desktop wallpaper that follows Light/Dark
and the accent, unlocked by a security key alone with the password as fallback, with
the lock screen, login screen and desktop looking unified. User decisions:

- 2026-11-03: the login touch prompt already works (greetd PAM `pam_u2f`); key unlock is
  touch only; the login screen mirrors the lock screen; the login screen is kept in
  sync automatically by a root service.
- 2026-11-04: key unlock uses the `kde-fingerprint` PAM slot. kscreenlocker 6.8 starts
  one method at a time (password, smartcard, face, its own `kde-u2f`), and only
  `kde-fingerprint` runs beside the password; its own security-key method hides the
  password box and is remembered after use. No fingerprint reader exists here.

| Piece | Outcome |
| --- | --- |
| Lock screen wallpaper (KUM-30) | `plasma/lockscreen.py` + user path unit keep `kscreenlockerrc` on the desktop wallpaper |
| Lock screen key unlock (KUM-31) | `/etc/pam.d/kde-fingerprint` from `plasma/pam/kde-fingerprint` via `plasma/security_key.py` |
| Login look (KUM-32) | ReGreet CSS/TOML mirror the lock screen (`plasma/greeter/`) |
| Login sync (KUM-33) | `kumios-greeter-sync.path`/`.service`, root-owned code in `/usr/local/lib/kumios` |

## Evidence

| Check | Result |
| --- | --- |
| Automated suites | Python 92 (incl. security key 12, greeter sync 11, greeter setup 19, lock screen 7), QML 82, Node 5; KWin greeter probe 5/5 |
| Look parity (`tests/probes/run_lock_login_look_probe.py`) | Lock and login screenshots side by side under a virtual KWin: same blurred wallpaper, clock and date, accent fields |
| Lock screen sync live (KUM-30) | Path unit active; lock screen followed the desktop to `nebula.png`, then to the "Next" wallpaper on 2026-11-04 (`in_sync: True`) |
| kscreenlocker 6.8 behaviour | Reverse-read from the installed greeter and confirmed in the testing greeter: `[Authenticators]` switches in `kscreenlockerrc`, remembered method in state `kscreenlockerrc [Greeter] Authenticator`; first `kde-smartcard` install never ran |
| Key unlock install (KUM-31) | User's sudo; `/etc/pam.d/kde-fingerprint` root 644, identical to the template; no earlier override, so no backup; unused `kde-smartcard` override removed; `kde`, sudo, greetd, `system-*` unchanged |
| Key unlock probe (isolated, physical key) | PASS: testing greeter started `kde-fingerprint` + `kde`; "Success from non-interactive authenticator kde-fingerprint"; the probe requires that line |
| **User lock screen check** | **Passed** 2026-11-04: "Touch and password unlock both work" (touch unlocks; password with the key unplugged) |
| Login sync install (KUM-33) | User's sudo; path unit enabled; code copies identical to the repository; greetd `config.toml` and PAM untouched |
| Login sync live | Light→Dark switch: automatic runs 13:42:20/13:42:24. Wallpaper change: `kumios-wallpaper.png` updated 13:46:14 and the accent followed (`#815eaf`). No sudo |
| **User login screen check** | **Passed** 2026-11-04: "The login screen works with the new look" |
| **User password login, key unplugged** (KUM-32) | **Passed** 2026-11-04: "Password login works" |
| **User lock screen look** (KUM-30) | **Passed** 2026-11-04: "the lock screen looks right" |

## Pending

- None for acceptance. Known cosmetic: while the key is plugged in, KDE's hint under
  the name reads "(or scan your fingerprint on the reader)"; that is the key, and
  KDE's text is fixed.
