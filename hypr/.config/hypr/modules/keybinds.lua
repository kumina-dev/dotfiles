local terminal = "kitty"
local file_manager = "nautilus"
local browser = "microsoft-edge-stable"

-- Applications

hl.bind(
    "SUPER + SPACE",
    hl.dsp.exec_cmd("hyprlauncher"),
    { description = "Open launcher" }
)

hl.bind(
    "SUPER + Return",
    hl.dsp.exec_cmd(terminal),
    { description = "Open terminal" }
)

hl.bind(
    "SUPER + E",
    hl.dsp.exec_cmd(file_manager),
    { description = "Open file manager" }
)

hl.bind(
    "SUPER + B",
    hl.dsp.exec_cmd(browser),
    { description = "Open browser" }
)

hl.bind(
    "SUPER + I",
    hl.dsp.exec_cmd(
        [[bash "$HOME/.config/hypr/scripts/settings-toggle.sh"]]
    ),
    { description = "Open settings" }
)

-- Windows

hl.bind(
    "SUPER + Q",
    hl.dsp.window.close(),
    { description = "Close window" }
)

hl.bind(
    "SUPER + SHIFT + F",
    hl.dsp.window.fullscreen({
	mode = "fullscreen",
	action = "toggle",
    }),
    { description = "Toggle fullscreen" }
)

hl.bind(
    "SUPER + F",
    hl.dsp.window.float({
        action = "toggle",
    }),
    { description = "Toggle floating" }
)

-- Focus

hl.bind(
    "SUPER + left",
    hl.dsp.focus({ direction = "l" }),
    { description = "Focus left" }
)

hl.bind(
    "SUPER + right",
    hl.dsp.focus({ direction = "r" }),
    { description = "Focus right" }
)

hl.bind(
    "SUPER + up",
    hl.dsp.focus({ direction = "u" }),
    { description = "Focus up" }
)

hl.bind(
    "SUPER + down",
    hl.dsp.focus({ direction = "d" }),
    { description = "Focus down" }
)

-- Move windows

hl.bind(
    "SUPER + SHIFT + left",
    hl.dsp.window.move({ direction = "l" }),
    { description = "Move window left" }
)

hl.bind(
    "SUPER + SHIFT + right",
    hl.dsp.window.move({ direction = "r" }),
    { description = "Move window right" }
)

hl.bind(
    "SUPER + SHIFT + up",
    hl.dsp.window.move({ direction = "u" }),
    { description = "Move window up" }
)

hl.bind(
    "SUPER + SHIFT + down",
    hl.dsp.window.move({ direction = "d" }),
    { description = "Move window down" }
)

-- Workspaces

for i = 1, 9 do
    hl.bind(
        "SUPER + " .. i,
        hl.dsp.focus({ workspace = tostring(i) }),
        { description = "Switch to workspace " .. i }
    )

    hl.bind(
        "SUPER + SHIFT + " .. i,
        hl.dsp.window.move({
	    workspace = tostring(i),
	    follow = false,
        }),
        { description = "Move window to workspace " .. i }
    )
end

hl.bind(
    "SUPER + TAB",
    hl.dsp.focus({ workspace = "previous" }),
    { description = "Previous workspace" }
)

hl.bind(
    "SUPER + mouse_down",
    hl.dsp.focus({ workspace = "e+1" }),
    { description = "Next workspace" }
)

hl.bind(
    "SUPER + mouse_up",
    hl.dsp.focus({ workspace = "e-1" }),
    { description = "Previous workspace" }
)

-- Mouse window manipulation

hl.bind(
    "SUPER + mouse:272",
    hl.dsp.window.drag(),
    {
        mouse = true,
	    description = "Move window",
    }
)

hl.bind(
    "SUPER + mouse:273",
    hl.dsp.window.resize(),
    {
        mouse = true,
	    description = "Resize window",
    }
)

-- Screenshots
-- Windows-style SUPER + SHIFT + S.
-- Selected region is copied directly to clipboard.

hl.bind(
    "SUPER + SHIFT + S",
    hl.dsp.exec_cmd(
	[[grim -g "$(slurp)" - | wl-copy]]
    ),
    { description = "Screenshot region" }
)

-- Print Screen saves the whole screen.

hl.bind(
    "Print",
    hl.dsp.exec_cmd(
	[[mkdir -p "$HOME/Pictures/Screenshots" && grim "$HOME/Pictures/Screenshots/$(date + '%Y-%m-%d_%H-%M-%S').png"]]
    ),
    { description = "Screenshot screen" }
)

-- Clipboard history
-- Windows-style SUPER + V.

hl.bind(
    "SUPER + V",
    hl.dsp.exec_cmd(
	[[cliphist list | fuzzel --dmenu --with-nth 2 | cliphist decode | wl-copy]]
    ),
    { description = "Clipboard history" }
)

-- Lock / notifications / power

hl.bind(
    "SUPER + L",
    hl.dsp.exec_cmd("hyprlock"),
    { description = "Lock session" }
)

hl.bind(
    "SUPER + N",
    hl.dsp.exec_cmd("swaync-client -t -sw"),
    { description = "Notification center" }
)

hl.bind(
    "SUPER + SHIFT + L",
    hl.dsp.exec_cmd(
        [[bash "$HOME/.config/hypr/scripts/power-menu-toggle.sh"]]
    ),
    { description = "Power menu" }
)

-- Audio

hl.bind(
    "XF86AudioRaiseVolume",
    hl.dsp.exec_cmd("wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+"),
    {
	repeating = true,
	locked = true,
	description = "Volume up",
    }
)

hl.bind(
    "XF86AudioLowerVolume",
    hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),
    {
	repeating = true,
	locked = true,
	description = "Volume down",
    }
)

hl.bind(
    "XF86AudioMute",
    hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),
    {
	repeating = true,
	locked = true,
	description = "Mute audio",
    }
)

hl.bind(
    "XF86AudioMicMute",
    hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),
    {
	repeating = true,
	locked = true,
	description = "Mute microphone",
    }
)

-- Media

hl.bind(
    "XF86AudioPlay",
    hl.dsp.exec_cmd("playerctl play-pause"),
    {
	locked = true,
	description = "Play / pause",
    }
)

hl.bind(
    "XF86AudioNext",
    hl.dsp.exec_cmd("playerctl next"),
    {
	locked = true,
	description = "Next track",
    }
)

hl.bind(
    "XF86AudioPrev",
    hl.dsp.exec_cmd("playerctl previous"),
    {
	locked = true,
	description = "Previous track",
    }
)

hl.bind(
    "XF86AudioStop",
    hl.dsp.exec_cmd("playerctl stop"),
    {
	locked = true,
	description = "Stop playback",
    }
)
