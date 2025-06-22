local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

exord_player = {}

dofile(mod_path .. "/player.lua")
dofile(mod_path .. "/fplayer.lua")
dofile(mod_path .. "/compass.lua")
