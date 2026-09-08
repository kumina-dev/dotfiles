package.loaded["generated.monitors"] = nil

local loaded = pcall(
    require,
    "generated.monitors"
)

if not loaded then
    hl.monitor({
        output = "",
        mode = "preferred",
        position = "auto",
        scale = "auto",
    })
end