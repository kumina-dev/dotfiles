# KumiOS

Personal Arch Linux + Hyprland desktop environment with familiar Windows-style shortcuts and a macOS-inspired interface.

The desktop is built around a small set of custom GTK utilities alongside standard Linux components. The current focus is a reliable daily-driver environment before deeper integrations and visual polish.

## Versioning

The development version is stored in [hypr/.config/hypr/VERSION](hypr/.config/hypr/VERSION). Settings reads that same installed file for About and copied system information.

Changes are recorded in [CHANGELOG.md](CHANGELOG.md). Release tags will identify tested desktop snapshots; the current version is a development build.

## Desktop

- Hyprland
- Waybar
- SwayNC
- Hyprlock
- Hypridle
- Hyprpaper
- Hyprlauncher
- Fuzzel
- Kitty
- Nautilus

## Custom desktop utilities

### Kumina Settings

GTK 3 settings application with pages for:

- Wi-Fi
- Bluetooth
- Display
- Appearance
- Input
  - Keyboard
  - Mouse
- Sound
- Account
- Language & Region (English/Finnish interface, date/time, numbers, and currency)

Open the overview:

```sh
~/.config/hypr/scripts/open-settings.sh
```

Open a specific page:

```sh
~/.config/hypr/scripts/open-settings.sh wifi
~/.config/hypr/scripts/open-settings.sh bluetooth
~/.config/hypr/scripts/open-settings.sh display
~/.config/hypr/scripts/open-settings.sh appearance
~/.config/hypr/scripts/open-settings.sh input
~/.config/hypr/scripts/open-settings.sh about
~/.config/hypr/scripts/open-settings.sh account
~/.config/hypr/scripts/open-settings.sh sound
~/.config/hypr/scripts/open-settings.sh region
```

Display and Input settings persist their generated Hyprland configuration in ignored files under:

```text
~/.config/hypr/generated/
```

Hyprland loads these generated settings when available and falls back to the repository defaults otherwise.

### Control Center

The Control Center provides compact daily controls for:

- Wi-Fi
- Bluetooth
- Audio output
- Microphone
- Media playback

All primary controls are on one page without a scroll container. Wi-Fi and Bluetooth arrows open their Settings pages. The Sound button opens device selection and other sound settings; the Settings button opens the overview. Escape closes the Control Center.

Long network names, device names, media titles, and errors do not expand the quick-controls layout. Full text is available through tooltips. Hover the Output or Microphone heading to identify its current default device.

Open it with:

```sh
~/.config/hypr/scripts/control-center-toggle.sh
```

### Account

Account shows the existing Linux account running Settings. It reads the account
by the process user ID, not environment variables, so launching Settings as a
different user correctly shows that user's account.

The page provides the username, full name (when set), user ID, primary group,
active session groups, home directory, and configured login shell. The heading
falls back to the username when no full name is set. Unknown groups retain their
numeric IDs. Session groups describe the current process's group membership;
they may differ from newly edited account group assignments until a new session.

Refresh reloads the data. Copy account information copies the displayed snapshot
as plain text. Only the name portion of the GECOS field is used; office and phone
fields are omitted. Both English and Finnish are supported. Long values wrap
inside a scrollable page; the Settings sidebar also scrolls when necessary.

This first iteration is read-only and uses the existing Linux account. It has
no separate login, cloud account, account editing, or password-management flow.

Desktop check: open `open-settings.sh account`, compare the details with your
account, try Refresh and Copy account information, and check the page/sidebar
at your normal display scale. The copied text should match the displayed values.

### About this PC

The About page reads the current computer's:

- KumiOS version, hostname, distribution, and kernel
- Processor and PCI graphics devices
- Usable memory reported by Linux
- Total, used, and free space for the system filesystem and a separate home filesystem when present

Refresh reloads the information. Copy system information copies the displayed values as plain text. Device names are read using `lspci` from the optional `pciutils` package; if unavailable, the other information still loads. Storage values describe mounted filesystems, not the sum of all physical disks.

### Language & Region

Language & Region provides:

- English/Finnish interface selection for Settings, Control Center, the power menu, and calendar
- 12/24-hour clock, numeric date format, and Monday/Sunday week start
- Finnish/English number styles and EUR/USD/GBP currency previews
- A preview and explicitly applied, per-user preferences
- System time-zone selection through `timedatectl` and the existing polkit agent

Formats are stored atomically in `$XDG_CONFIG_HOME/kumios/region.json` (normally
`~/.config/kumios/region.json`). They affect the KumiOS panel clock, its calendar
tooltip, the calendar window, and memory/storage quantities in About this PC. Defaults remain 24-hour time, day-first dates,
and Monday-first weeks. The panel and open calendar observe changes within a
second, including midnight and system time-zone changes. No logout is required.
Other applications keep their own regional formats.

Number formatting is independent of the interface language: Finnish uses
`1 234,56` (with non-breaking grouping spaces), while English uses `1,234.56`.
The default is Finnish numbers and EUR. Existing preference files gain these
defaults when read without changing their saved clock/date/week choices.

The live currency preview supports EUR, USD, and GBP. Finnish formatting places
the symbol after the amount; English places it before. Currency is a display
preference, not conversion. The desktop has no monetary data view yet; currency
formatting is currently used by the preview and is available through the shared
`format_currency` helper. Callers with monetary data should pass its actual
currency explicitly. Display rounding uses decimal half-up rounding.

Choose **Apply formats**, then open or refresh **About this PC** to see the new
number style in memory/storage values. Copy system information preserves the
values from that same displayed snapshot. Technical identifiers and editable
backend values (such as display mode IDs) are not reformatted.

The panel clock now uses a Waybar custom JSON stream. Left-click still toggles
the calendar; right-click opens Language & Region. Reload Waybar once after
installing this change (`pkill -SIGUSR2 -x waybar`). Subsequent preference changes
do not need a reload. Both calendars use month and weekday names from the
selected KumiOS interface language.

Time-zone changes apply system-wide and may prompt for authentication. Errors
and cancelled authentication are shown on the page. Format preferences remain
usable if timedated is unavailable. Invalid preference files fall back to the
defaults in the clock/calendar and are reported in Settings; applying formats
replaces the invalid file.

Interface language is stored separately in `$XDG_CONFIG_HOME/kumios/language.json`.
English is the default. Choose **English** or **Suomi**, then **Apply language**.
Close and reopen the custom GTK apps to apply it; the panel tooltip updates
within a second. No logout is needed. Existing windows retain their language
until reopened, so changing a preference cannot disrupt an in-progress action.

This translates KumiOS-owned labels, actions, status messages, and calendar
names. Device names, SSIDs, time-zone identifiers, and hardware values are
preserved. External command errors and GTK-provided standard dialogs still use
their own language. Hyprland-matched window titles remain stable. Language
selection does not set system `LANG`/`LC_*`, generate locales, change keyboard
layouts, or alter saved regional formats. Keyboard layouts stay under Input.

Translations live in `hypr/.config/hypr/scripts/kumina_common/translations/fi.json`.
Messages use named placeholders; never translate command arguments, device data,
or internal IDs. Unknown messages fall back to their English source. Invalid
language preferences fall back to English and are reported on the settings page;
applying a language replaces the invalid preference file.

Desktop verification:

1. Open `open-settings.sh region`; apply 12-hour time and an ISO date. Check the
   preview, panel tooltip, and open calendar agree. Restore your preferred values.
2. Change the week start; check both calendar headers and day columns move together.
3. Apply the current time zone; this should not request authentication. A different
   time zone may prompt through polkit; cancellation must show an error. Restore
   your original zone after testing an actual change.
4. Close/reopen Settings and the calendar; saved format choices should remain.
5. Apply **Suomi**, reopen Settings, Control Center, the power menu, and calendar.
   Check labels, long Finnish confirmations, and both calendar weekday headers.
   Check that selected devices and keyboard layouts remain the same.
6. Apply **English** and reopen the apps to switch back. Verify that the panel
   calendar tooltip switches without restarting Waybar.
7. Change the number style and currency. Check both previews before applying;
   applying must preserve the selected date, clock, week start, and interface language.
8. Refresh About this PC and copy the system information. Memory/storage values
   should use the selected decimal separator both on screen and in the copied text.

### Lock screen

The password input stays visible even when empty and uses Hyprlock's `$PAMPROMPT` variable as its placeholder. It displays the actual input prompt when PAM asks for a password or PIN.

A fingerprint-style icon and "Touch your security key" appear while the locking Hyprlock process holds `pam_u2f`'s default `/var/run/user/$UID/pam-u2f-authpending` file open. The indicator checks every 250 ms and disappears when that descriptor closes. A leftover file alone does not trigger it, and requests from other processes such as sudo are ignored. The icon is a security-key touch indicator, not fingerprint authentication.

The helper reads process metadata and file-descriptor metadata only. It does not read key registrations or credentials, and this configuration does not change the PAM stack. If the pending state cannot be inspected, the icon stays hidden; password input remains available. A custom `authpending_file` path would need a corresponding helper change.

Hyprlock 0.9.6 cannot conditionally hide its input field based on this signal through configuration. That part remains pending; the field is visible during both security-key and password authentication.

### Power menu

The custom power menu provides:

- Lock
- Sleep
- Log Out
- Restart
- Shut Down

Destructive session and power actions require confirmation.

Open it with:

```sh
~/.config/hypr/scripts/power-menu-toggle.sh
```

The configured Hyprland shortcut is:

```text
Super + Shift + L
```

### Calendar

The current local calendar utility can be toggled with:

```sh
~/.config/hypr/scripts/calendar-toggle.sh
```

Calendar event integrations are planned separately.

## Sound

Sound controls use PipeWire and WirePlumber.

Settings provides default output and microphone selection. Both Settings and Control Center provide:

- Separate output and microphone volume
- Mute controls
- Automatic updates while visible
- Device hotplug handling
- Visible backend errors

Default device selection is handled through WirePlumber's `wpctl` policy.

Applications with explicitly selected audio devices may continue using their own selection.

The current UI does not manage:

- device profiles
- ports
- per-application routing

Existing amplification above 100% is displayed without modifying it. Moving a Kumina volume slider writes a value in the 0–100% range.

## Wi-Fi

Wi-Fi management uses NetworkManager through `nmcli`.

Settings supports:

- adapter on/off
- network discovery
- saved networks
- secured network connection
- disconnect
- forget network

The Control Center provides a smaller view intended for normal daily use.

## Bluetooth

Bluetooth management uses BlueZ through `bluetoothctl`.

Settings supports:

- adapter on/off
- scanning
- pairing
- connecting
- disconnecting
- forgetting paired devices

The Control Center provides an adapter toggle and a shortcut to Bluetooth settings for device management.

## Notifications

SwayNC popup width is 420 pixels, and its popup area has a maximum height of 240 pixels. This bounds the visible notification stack, including long messages. SwayNC may scroll overflow inside that area; this is not a fixed height for each individual notification card. Fixed-size cards remain a separate roadmap item.

The notification center remains available with `Super + N`.

## Workspace shortcuts

`Super + Alt + 1–9` moves the focused window to the selected workspace without following it. The existing `Super + Shift + 1–9` bindings remain available.

## Appearance

Wallpaper-based dynamic theming uses Matugen.

The canonical command is:

```sh
~/.local/bin/set-wallpaper <image> [dark|light]
```

It:

1. stores the active wallpaper at `~/Pictures/Wallpapers/main.png`
2. stores the selected color mode
3. regenerates Matugen colors
4. applies the wallpaper to active monitors
5. reloads supported desktop components

Generated theme files are intentionally not tracked by Git.

## Runtime dependencies

The custom desktop utilities rely on standard command-line tools from the desktop stack, including:

- `hyprctl`
- `nmcli`
- `bluetoothctl`
- `wpctl`
- `playerctl`
- `matugen`

GTK utilities require Python, PyGObject, and GTK 3.

## Installation

Configurations are managed using GNU Stow.

```sh
git clone https://github.com/kumina-dev/dotfiles ~/dotfiles
cd ~/dotfiles

stow hypr waybar swaync kitty fuzzel matugen gtk scripts
```

Re-stow Hyprland configuration after repository changes when necessary:

```sh
stow -R hypr
```

## Generated and runtime files

Repository configuration is kept separate from generated machine state.

Examples of ignored generated files include:

```text
hypr/.config/hypr/generated/
kitty/.config/kitty/colors.conf
fuzzel/.config/fuzzel/colors.ini
gtk/.config/gtk-3.0/matugen.css
gtk/.config/gtk-4.0/matugen.css
theme/.config/theme/colors.css
```

Python bytecode and cache directories are also ignored.

## Development

The project prioritizes:

1. basic functionality
2. reliability and error recovery
3. tests and cleanup
4. visual/UX polish
5. larger integrations

See [ROADMAP.md](ROADMAP.md).

### Tests

Run the full suite without generating Python bytecode:

```sh
PYTHONDONTWRITEBYTECODE=1 \
python3 -m unittest discover -s tests -v
```

Some widget tests require GTK 3 and an active display. They skip when those are unavailable.

They can also be run under Xvfb:

```sh
xvfb-run -a \
env PYTHONDONTWRITEBYTECODE=1 \
python3 -m unittest discover -s tests -v
```

### Syntax check

```sh
python3 - <<'PY'
from pathlib import Path

root = Path(
    "hypr/.config/hypr/scripts"
)

files = sorted(
    root.rglob("*.py")
)

for path in files:
    compile(
        path.read_text(
            encoding="utf-8"
        ),
        str(path),
        "exec",
    )

print(
    f"Syntax OK: {len(files)} Python files"
)
PY
```
