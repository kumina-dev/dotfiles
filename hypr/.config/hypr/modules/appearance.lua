local colors = require("generated.colors")

hl.config({
    general = {
        gaps_in = 5,
        gaps_out = 10,
        border_size = 2,

        ["col.active_border"] = colors.primary,
        ["col.inactive_border"] = colors.outline,
    },

    decoration = {
        rounding = 10,

        blur = {
            enabled = true,
            size = 8,
            passes = 3,
            ignore_opacity = true,
        },

        shadow = {
            enabled = true,
            range = 15,
            render_power = 3,
            color = colors.background,
        },
    },

    animations = {
        enabled = true,
        workspace_wraparound = true,
    },
})

-- Fast and smooth rather than floaty.
hl.curve("desktop", {
    type = "bezier",
    points = {
        { 0.2, 0.8 },
        { 0.2, 1.0 },
    },
})

hl.curve("desktopOut", {
    type = "bezier",
    points = {
        { 0.4, 0.0 },
        { 1.0, 1.0 },
    },
})

-- Windows

hl.animation({
    leaf = "windowsIn",
    enabled = true,
    speed = 2.2,
    bezier = "desktop",
    style = "popin 92%",
})

hl.animation({
    leaf = "windowsOut",
    enabled = true,
    speed = 1.8,
    bezier = "desktopOut",
    style = "popin 96%",
})

hl.animation({
    leaf = "windowsMove",
    enabled = true,
    speed = 2.4,
    bezier = "desktop",
})

-- Workspaces

hl.animation({
    leaf = "workspaces",
    enabled = true,
    speed = 3.0,
    bezier = "desktop",
    style = "slidefade 12%",
})

-- Layer surfaces such as launchers and panels

hl.animation({
    leaf = "layersIn",
    enabled = true,
    speed = 2.0,
    bezier = "desktop",
    style = "fade",
})

hl.animation({
    leaf = "layersOut",
    enabled = true,
    speed = 1.6,
    bezier = "desktopOut",
    style = "fade",
})

-- Opacity changes

hl.animation({
    leaf = "fade",
    enabled = true,
    speed = 2.0,
    bezier = "desktop",
})
