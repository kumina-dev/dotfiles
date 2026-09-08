# Arch Linux Dotfiles

Personal Arch Linux + Hyprland desktop configuration.

The desktop is built around a small set of custom GTK utilities alongside standard Linux components. The current focus is a reliable daily-driver environment before deeper integrations and visual polish.

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
- Keyboard
- Mouse
- Sound

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
~/.config/hypr/scripts/open-settings.sh keyboard
~/.config/hypr/scripts/open-settings.sh mouse
~/.config/hypr/scripts/open-settings.sh sound
```

Display, Keyboard, and Mouse settings persist their configuration in ignored files under:

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

Wi-Fi and Bluetooth have lightweight detail pages inside the Control Center, while full management remains available through Kumina Settings.

Open it with:

```sh
~/.config/hypr/scripts/control-center-toggle.sh
```

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

Settings and Control Center provide:

- Default output and microphone selection
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

The Control Center only exposes paired-device connection management.

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
