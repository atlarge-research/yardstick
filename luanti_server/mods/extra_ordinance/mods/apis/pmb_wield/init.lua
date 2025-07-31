local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)


pmb_wield = {}

dofile(mod_path .. "/on_move_item.lua")
dofile(mod_path .. "/api.lua")
dofile(mod_path .. "/example.lua")
