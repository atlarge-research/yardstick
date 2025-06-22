local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

exord_swarm = {}

dofile(mod_path .. "/system.lua")
dofile(mod_path .. "/mobs/worker.lua")
dofile(mod_path .. "/mobs/nest.lua")