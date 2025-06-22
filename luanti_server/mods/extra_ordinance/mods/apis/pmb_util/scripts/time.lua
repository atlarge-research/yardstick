
local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(minetest.get_current_modname())

pmb_util.time = {}

pmb_util.time.force_time = false

minetest.register_on_mods_loaded(function()
    if minetest.get_modpath("world_storage") then
        pmb_util.time.force_time = world_storage.get("pmb_util:time", "force_time") or false
    end
end)

function pmb_util.time.force_set_time(time)
    pmb_util.time.force_time = time
    world_storage.set("pmb_util:time", "force_time", time)
    world_storage.set_timeout("pmb_util:time", 0.1)
end

function pmb_util.time.set_time(time)
    if pmb_util.time.force_time then
        pmb_util.time.force_set_time(false)
    end
    minetest.set_timeofday(time)
end

local on_globalstep = function(dtime)
    if pmb_util.time.force_time then
        minetest.set_timeofday(pmb_util.time.force_time)
        return
    end
end
minetest.register_globalstep(on_globalstep)

minetest.unregister_chatcommand("time")
minetest.register_chatcommand("time", {
    params = "",
    description = S("Forcibly sets the time and keeps it there. Uses sine scale, 0 midnight, 0.5 noon, 1 midnight."),
    privs = {},
    func = function(name, params)
        local param = string.split(params, " ")
        if param[1] == "day" then
            pmb_util.time.set_time(0.25)
            return true, S("Setting time to day (0.25)")
        elseif param[1] == "night" then
            pmb_util.time.set_time(0.8)
            return true, S("Setting time to night (0.8)")
        end
        if param[1] == "lock" then
            local num = tonumber(param[2])
            if num then
                pmb_util.time.force_set_time(num % 1)
                return true, S("Forcing time to stay at " .. tostring(num % 1))
            else
                pmb_util.time.force_set_time(false)
                return true, S("Releasing forced time.")
            end
        end
        if param[1] == "set" then
            local num = tonumber(param[2])
            if num then
                pmb_util.time.set_time(num % 1)
                return true, S("Setting time to  " .. (num % 1))
            else
                return false, S("Error, you must supply a number.")
            end
        end
    end
})

