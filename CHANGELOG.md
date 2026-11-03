# Changelog

## Unreleased — 0.4.0-dev

- `main` is Plasma-only. The Hyprland-era code (Hyprland, Waybar, SwayNC, fuzzel,
  matugen, the GTK utilities and their tests) is preserved, unmaintained, on the
  `legacy/hyprland` branch with full history. The project version moved to the root
  `VERSION` file.

## 0.3.0 — 2026-11-03

- The accent color follows the wallpaper (KDE's accent service), and the user
  chooses Light, Dark or Automatic appearance from the Control Center. Automatic
  follows KDE's day/night schedule (sunrise/sunset, KNightTime) and does not need
  Night Light enabled.
- The KumiOS Plasma style no longer hardcodes a dark palette: the top bar and dock
  draw with the active color scheme at their existing translucency.
- `plasma/appearance.py` replaces `apply-defaults.sh`: appearance-only KumiOS
  Light/Dark global themes keep the wallpaper and Plasma style, with backups and
  verification of the applied state. KDE now manages the GTK settings directories.
- Upgrade safety for KDE's private audio API: it is loaded at runtime, so a KDE
  release that changes it disables only the audio controls (with a pointer to
  Sound settings) instead of the whole Control Center. Missing members are
  detected before use. `plasma/audio_api.py` checks the installed module against
  a recorded contract after KDE upgrades and in setup preflight.
- Retired the legacy KumiOS audio service (`kumi-audio.service`, D-Bus
  `org.kumios.Audio`): nothing used it since 0.2.0. It is stopped, disabled and
  removed, together with its legacy-only continuity probe.
- A deliberate multi-monitor panel layout is optional and deferred: it needs a
  second monitor to test. Other screens keep Plasma's defaults.
- Verification and manual acceptance: [verification-0.3.0](plasma/verification-0.3.0.md).

## 0.2.0 — 2026-11-03 (accepted 2026-10-18)

- Control Center uses KDE audio defaults and reconnect handling, with quick
  microphone mute, actual device labels and optional client-only Retry audio.
- Bluetooth follows BluezQt adapter/device events rather than hci0 and polling.
- Wireless connection/SSID state comes from KDE's wireless rows, independently
  of wired/VPN connectivity. Active-app labels clear when no task is active.
- Audio, radio and brightness changes show pending state and actionable errors;
  completion follows observed state, with bounded waits and late-reply protection.
- Native/read-only and isolated-bus probes complement mock recovery tests.
- Activated through a user-approved Plasma restart and accepted by the user on
  2026-10-18 with documented unverified limitations (physical Bluetooth removal,
  native audio-backend restart, live-shell error display); see
  [verification](plasma/verification-0.2.0.md). Tagged `v0.2.0` on 2026-11-03; no GitHub release.

## 0.1.0 — 2026-10-18

First Plasma daily-driver release. See [release notes](releases/0.1.0.md).

### Added

- Read-only Plasma preflight and explicit layout application with private config,
  live-layout and installed-widget backups, without automatic desktop restarts.
- Native KDE Bluetooth, audio/microphone and About entry points from KumiOS controls.
- Plasma setup, acceptance and recovery documentation.

### Changed

- Reconcile the complete top bar and centered dock in place, retaining dock pins
  and personal panels instead of deleting all panels.
- Use KDE Application Dashboard for the panel, Meta+Space and launcher helper;
  retire incompatible AppGrid only after creating its replacement.
- Distinguish the supported Plasma release from legacy Hyprland utilities.

### Verification and known limitations

- Current-session manual checks passed, confirmed by the user after an approved
  Plasma restart. Automated checks: 33 Qt/QML, five layout and three setup checks.
- **Unverified:** layout and pinned-app persistence across the next voluntary
  login/reboot. KUM-8 remains open; user explicitly accepts release before this check.
  *Update 2026-10-18:* the user reported the login/reboot check passed; KUM-8 is Done.
- Setup targets the existing installation, requires the KumiOS audio service, and
  does not provision a fresh machine. Bluetooth quick toggle assumes hci0.
- Installed widget code may require an approved Plasma restart or next normal login.

## Earlier development notes

These notes preserve prior development history, including legacy Hyprland/GTK
features. They are not claims that every legacy feature was validated for 0.1.0.

### Added

- Saved Wi-Fi Forget controls with inline confirmation, profile identity checks, progress, and actionable errors.

- Plasma Wi-Fi disconnect controls with device-state progress and reconnect support.

- Plasma Control Center Wi-Fi selection, saved/new personal-network activation, native password prompts, progress, cancellation, and inline errors.
- Wi-Fi refresh controls and QML regression coverage for filtering and connection state handling.

- Local all-day calendar events with notes, date changes, editing, confirmed deletion, and persistent SQLite storage.
- Selected-day event list and month-grid event markers in English/Finnish.

- Read-only Account page with Linux user details, active session groups, refresh, and plain-text copy in English/Finnish.

- Finnish/English number styles and EUR/USD/GBP currency previews with independent saved preferences.
- Shared decimal-based number/currency formatting and regional memory/storage values in About this PC.

- English/Finnish interface selection for Settings, Control Center, the power menu, and calendar.
- Shared translated month/weekday names for the calendar and live Waybar tooltip.

- Language & Region first iteration: shared 12/24-hour clock, numeric dates, week start, and system time-zone selection.
- Live panel/calendar preference updates and a right-click shortcut from the clock to regional settings.

- KumiOS project identity and a single installed development-version file.
- About this PC with live system information, refresh, and plain-text copy.
- Super + Alt + 1–9 to move a window without following it.
- Security-key touch indicator using the locking process's pam_u2f pending-file descriptor.

### Changed

- Calendar window expanded to 740×480 for the month grid and event list.

- Settings navigation scrolls when needed to keep all pages reachable.

- Control Center now presents quick controls on one page, with details in Settings.
- Long quick-control labels use tooltips instead of expanding the layout.
- The SwayNC popup area is limited to 240 pixels in height.
- The lock screen displays the available PAM prompt and keeps empty password input visible.

### Fixed

- Wi-Fi cancellation now waits for the active connection to stop and blocks duplicate cancellation requests.
- Connection failures show NetworkManager reasons instead of a generic authentication/network error.

- Plasma Wi-Fi discovery filtering: wired, bridge, and loopback connections no longer appear as available wireless networks.

- Invalid notification-theme font declaration.

### Still pending


- Desktop verification of local calendar events and the wider calendar layout.

- Desktop verification of Account values, copy/refresh, and sidebar scrolling.

- Fixed dimensions for individual notification cards.
- Conditional password-input visibility during FIDO authentication.
- Desktop verification of number/currency controls and About formatting.
- Desktop verification of regional settings and time-zone authentication.
- Desktop verification before the first release tag.
