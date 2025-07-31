local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)

exord_core.mapgen_profile = "biomes"
exord_core.is_map_generated = false

exord_mg_custom.minc = vector.new(-2, 0,   -2)
exord_mg_custom.maxc = vector.new( 2, 0.25, 2)
exord_mg_custom.minp = exord_mg_custom.minc * 80
exord_mg_custom.maxp = exord_mg_custom.maxc * 80

local gen_path = mod_path .. "/modules/mapgen/generators/"
dofile(gen_path .. "biomes.lua")
dofile(gen_path .. "flat.lua")

minetest.register_alias("mapgen_stone", "")
minetest.register_alias("mapgen_water_source", "")
minetest.register_alias("mapgen_river_water_source", "")

-- this is the only way the game can restart, so the mapgen better work
LISTEN("on_mapgen_finished", function()
    exord_core.is_map_generated = true
    -- core.log("mapgen done")
end)
