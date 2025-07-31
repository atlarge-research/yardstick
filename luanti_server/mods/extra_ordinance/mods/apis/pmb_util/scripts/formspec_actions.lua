
pmb_util.formspec_actions = {}

local forms = {
    ["_builtin_inventory"] = {}
}

function pmb_util.formspec_actions.register_on_form_fields(formname, func)
    if formname == "" then
        formname = "_builtin_inventory"
    end
    if not forms[formname] then forms[formname] = {} end

    forms[formname][#forms[formname]+1] = func
end

minetest.register_on_player_receive_fields(function(player, formname, fields)
    if formname == "" then formname = "_builtin_inventory" end
    if not forms[formname] then return end

    for i, func in ipairs(forms[formname] or {}) do
        func(player, formname, fields)
    end
end)
