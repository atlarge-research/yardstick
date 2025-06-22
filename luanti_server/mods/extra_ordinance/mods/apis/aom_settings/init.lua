local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)


aom_settings = {}
aom_settings.form = {}

aom_settings.mod_storage = minetest.get_mod_storage()

--  API
dofile(mod_path .. "/settings.lua")

aom_settings.register_setting("debug_enabled", false, "Debug enabled", "server")
aom_settings.register_setting("menu_commands", false, "Allow player menu command", "server")

dofile(mod_path .. "/formspec_system.lua")
dofile(mod_path .. "/formspec.lua")
