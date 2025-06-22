local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)

COMPAT = {}
COMPAT.flags = {}
-- tracks current protocol (proto_max) version
COMPAT.version = 45

dofile(mod_path .. "/scripts/api.lua")