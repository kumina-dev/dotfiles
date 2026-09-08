local input = {
    kb_layout = "fi,us",
    kb_options = "grp:alt_shift_toggle",
}

package.loaded["generated.keyboard"] = nil

local loaded, keyboard = pcall(
    require,
    "generated.keyboard"
)

if loaded and type(keyboard) == "table" then
    for key, value in pairs(keyboard) do
        input[key] = value
    end
end

hl.config({
    input = input,
})
