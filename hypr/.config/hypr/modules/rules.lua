-- Layer surfaces

hl.layer_rule({
    match = {
        namespace = "waybar",
    },

    blur = true,
    ignore_alpha = 0.2,
})

-- Generic floating dialogs.
-- Keep normal application windows tiled, but dialogs should behave like dialogs.

hl.window_rule({
    name = "float-dialogs",

    match = {
        title = ".*(Open|Save|Choose|Select|Preferences|Settings).*",
    },

    float = true,
    center = true,
})

-- Common small utility windows.

hl.window_rule({
    name = "float-pavucontrol",

    match = {
        class = "org.pulseaudio.pavucontrol",
    },

    float = true,
    center = true,
    size = { 900, 620 },
})

hl.window_rule({
    name = "float-blueman",

    match = {
        class = "blueman-manager",
    },

    float = true,
    center = true,
    size = { 780, 560 },
})

-- Picture-in-picture windows should float above tiled applications.

hl.window_rule({
    name = "picture-in-picture",

    match = {
        title = ".*Picture-in-Picture.*",
    },

    float = true,
    pin = true,
    keep_aspect_ratio = true,
})

hl.window_rule({
    name = "kumina-calendar",
    match = {
        title = "Kumina Calendar",
    },
    float = true,
    center = true,
    size = { 340, 350 },
})

hl.window_rule({
    name = "kumina-updater",
    match = {
        class = "kumina-updater",
    },

    float = true,
    center = true,
    size = { 720, 480 },
})

hl.window_rule({
    name = "kumina-control-center",
    match = {
        title = "Kumina Control Center",
    },

    float = true,
    center = true,
    size = { 420, 520 },
})

hl.window_rule({
    name = "kumina-settings",

    match = {
        title = "Kumina Settings",
    },

    float = true,
    center = true,
    size = { 820, 560 },
})
