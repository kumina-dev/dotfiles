local input = {
    kb_layout = "fi,us",
    kb_options = "grp:alt_shift_toggle",
}

local function merge_generated(module_name)
    package.loaded[module_name] = nil

    local loaded, values = pcall(
        require,
        module_name
    )

    if not loaded or type(values) ~= "table" then
        return
    end

    for key, value in pairs(values) do
        input[key] = value
    end
end

merge_generated(
    "generated.keyboard"
)

merge_generated(
    "generated.mouse"
)

hl.config({
    input = input,
})
