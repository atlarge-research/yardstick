
local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(minetest.get_current_modname())
local save_path = minetest.get_worldpath()

local serverinfo = {
    dtimeavg = 0.1
}

minetest.register_chatcommand("serverinfo", {
    params = "",
    description = S("Tells you things like the avg step time"),
    privs = {},
    func = function(name, param)
        pmb_util.get_abm_calls()
        return true, ("  Server step avg\n"..tostring(serverinfo.dtimeavg).."\nWorld Path: "..save_path)
    end
})

minetest.register_globalstep(function (dtime)
    serverinfo.dtimeavg = (serverinfo.dtimeavg * 99 + dtime) / 100
end)
