#!/usr/bin/env bash
# Apply KumiOS appearance to the current user's running Plasma 6 session.
set -euo pipefail

if [[ $# -ne 0 ]]; then
    echo "Usage: $0" >&2
    exit 2
fi

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}"
data_dir="${XDG_DATA_HOME:-$HOME/.local/share}"
for tool in plasma-apply-colorscheme plasma-apply-desktoptheme kwriteconfig6 python3; do
    command -v "$tool" >/dev/null || { echo "Required command missing: $tool" >&2; exit 1; }
done
[[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]] || { echo 'Run inside your Plasma desktop session.' >&2; exit 1; }

mkdir -p "$config_dir/kumios"
backup_dir="$(mktemp -d "$config_dir/kumios/appearance-backup-XXXXXXXX")"
for file in kdeglobals plasmarc gtk-3.0/settings.ini gtk-4.0/settings.ini; do
    if [[ -f "$config_dir/$file" ]]; then
        mkdir -p "$backup_dir/$(dirname "$file")"
        cp -L --preserve=mode,timestamps "$config_dir/$file" "$backup_dir/$file"
    fi
done
if [[ -e "$data_dir/plasma/desktoptheme/KumiOS" ]]; then
    cp -aL "$data_dir/plasma/desktoptheme/KumiOS" "$backup_dir/KumiOS"
fi
if command -v gsettings >/dev/null && gsettings list-schemas | grep -qx org.gnome.desktop.interface; then
    gsettings get org.gnome.desktop.interface color-scheme > "$backup_dir/gnome-color-scheme.txt"
    gsettings get org.gnome.desktop.interface gtk-theme > "$backup_dir/gnome-gtk-theme.txt"
fi
printf 'Appearance backup: %s\n' "$backup_dir"

mkdir -p "$data_dir/plasma/desktoptheme/KumiOS"
cp -a "$source_dir/desktoptheme/KumiOS/." "$data_dir/plasma/desktoptheme/KumiOS/"
plasma-apply-colorscheme BreezeDark
plasma-apply-desktoptheme KumiOS

# Update only appearance keys, retaining existing GTK settings and symlinks.
python3 - "$config_dir" <<'PY'
import pathlib
import re
import sys
for version in ('gtk-3.0', 'gtk-4.0'):
    path = pathlib.Path(sys.argv[1]) / version / 'settings.ini'
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text() if path.exists() else '[Settings]\n'
    if not re.search(r'^\[Settings\]\s*$', text, re.M):
        text += '\n[Settings]\n'
    start = re.search(r'^\[Settings\]\s*$', text, re.M).end()
    following = re.search(r'^\[', text[start:], re.M)
    end = start + following.start() if following else len(text)
    section = text[start:end]
    for key, value in [('gtk-application-prefer-dark-theme', 'true'), ('gtk-theme-name', 'Breeze-Dark')]:
        section = re.sub(r'^' + re.escape(key) + r'=.*\n?', '', section, flags=re.M)
        section = section.rstrip() + f'\n{key}={value}\n'
    path.write_text(text[:start] + section + text[end:])
PY

# Libadwaita and portal-aware applications use this preference.
if [[ -f "$backup_dir/gnome-color-scheme.txt" ]]; then
    gsettings set org.gnome.desktop.interface color-scheme prefer-dark
    gsettings set org.gnome.desktop.interface gtk-theme Breeze-Dark
fi
printf 'Applied KumiOS Plasma style and Breeze Dark application colors.\nReopen applications that retain their previous appearance.\n'
