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
})
