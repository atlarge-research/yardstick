local empty_cap = {
    dig_immediate = {
        maxlevel = 0,
        uses = 0,
    },
}

minetest.register_on_mods_loaded(function()
    if not minetest.get_modpath("pmb_vars") then return false end
    if pmb_vars.prevent_digging then
        minetest.override_item("", {
            tool_capabilities = {
                groupcaps = empty_cap,
            }
        })
        for index, value in pairs(minetest.registered_tools) do
            if value.tool_capabilities ~= nil then
                minetest.override_item(index, {
                    tool_capabilities = {
                        groupcaps = empty_cap,
                    }
                })
            end
        end
    end
end)
