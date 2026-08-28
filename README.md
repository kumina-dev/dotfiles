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
