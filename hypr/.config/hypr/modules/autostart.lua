hl.on("hyprland.start", function()
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd("gnome-keyring-daemon --start --components=secrets")

    hl.exec_cmd("pgrep -x hyprlauncher >/dev/null || hyprlauncher -d")
    hl.exec_cmd("pgrep -x hypridle >/dev/null || hypridle")
    hl.exec_cmd("pgrep -x swaync >/dev/null || swaync")
    hl.exec_cmd("pgrep -x waybar >/dev/null || waybar")

    hl.exec_cmd("pgrep -f 'wl-paste --type text --watch cliphist store' >/dev/null || wl-paste --type text --watch cliphist store")
    hl.exec_cmd("pgrep -f 'wl-paste --type image --watch cliphist store' >/dev/null || wl-paste --type image --watch cliphist store")

    hl.exec_cmd("pgrep -x hyprpaper >/dev/null || hyprpaper")
end)
