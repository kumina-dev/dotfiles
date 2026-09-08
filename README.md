# Arch Linux Dotfiles

Personal Arch Linux + Hyprland desktop configuration.

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

## Theming

Wallpaper-based dynamic theming using Matugen.

`set-wallpaper` updates the active wallpaper, generates the color palette,
and reloads supported desktop components.

## Installation

Configurations are managed using GNU Stow.

```sh
git clone <repo-url> ~/dotfiles
cd ~/dotfiles

stow hypr waybar swaync kitty fuzzel matugen gtk scripts
```

Generated theme files are not tracked by Git.

## Custom settings and control center

GTK 3 and PyGObject run both windows. Sound controls use the existing PipeWire
and WirePlumber session; no PulseAudio server or additional Python packages
are required.

```sh
sudo pacman -S --needed python-gobject gtk3 pipewire wireplumber
stow -R hypr
~/.config/hypr/scripts/open-settings.sh sound
```

Sound settings and the control center both provide:

- Default output and microphone selection from currently available devices.
- Separate 0–100% volume and mute controls for output and microphone.
- Automatic updates while visible, including external volume changes and
  connected or disconnected devices.
- Disabled controls for missing devices and visible command errors.

Device selection uses [WirePlumber's default-device policy](https://pipewire.pages.freedesktop.org/wireplumber/man/wpctl.html#set-default).
Applications with
an explicitly selected device can keep using their own selection. This version
does not change device profiles, ports, or individual application routing.
Existing amplification above 100% is displayed without changing it; moving
the slider sets a value within 0–100%.

The control center's Sound Settings button opens the Sound page. Its main
view scrolls when the controls do not fit the window. Wi-Fi stays available
in both windows.

Display settings provide active-display selection, supported resolution and
refresh-rate modes, and display scaling. Applied settings are persisted in the
ignored `generated/monitors.lua` runtime configuration.

Development intentionally prioritizes basic daily-driver functionality before
advanced features and polish. See [ROADMAP.md](ROADMAP.md).

### Verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The widget tests need GTK 3 and a display; they skip when those are unavailable.
They can also run under Xvfb with the same command prefixed by `xvfb-run -a`.

On the desktop, open Sound settings and the control center together. Adjust
each volume and mute control and check that the other window catches up.
Switch output during playback, change the microphone, then disconnect and
reconnect a device. Check media-key updates and switching away from and back
to the Sound page. Confirm the chosen devices after logging out and back in.
