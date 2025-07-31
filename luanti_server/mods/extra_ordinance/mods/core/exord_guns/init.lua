local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

exord_guns = {}

dofile(mod_path .. "/system.lua")
dofile(mod_path .. "/items.lua")
dofile(mod_path .. "/special_items.lua")
dofile(mod_path .. "/projectile_types.lua")
dofile(mod_path .. "/beam.lua")
dofile(mod_path .. "/asm100.lua")
dofile(mod_path .. "/mining_laser.lua")
