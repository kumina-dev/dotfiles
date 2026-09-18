# Changelog

## Unreleased

### Added

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

- Control Center now presents quick controls on one page, with details in Settings.
- Long quick-control labels use tooltips instead of expanding the layout.
- The SwayNC popup area is limited to 240 pixels in height.
- The lock screen displays the available PAM prompt and keeps empty password input visible.

### Fixed

- Invalid notification-theme font declaration.

### Still pending

- Fixed dimensions for individual notification cards.
- Conditional password-input visibility during FIDO authentication.
- Desktop verification of number/currency controls and About formatting.
- Desktop verification of regional settings and time-zone authentication.
- Desktop verification before the first release tag.
