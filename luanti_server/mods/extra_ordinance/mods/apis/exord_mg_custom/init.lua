local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)

exord_mg_custom = {}

local mapsize = vector.new(
    tonumber(minetest.settings:get("exord_mapgen_x")) or 2, 0,
    tonumber(minetest.settings:get("exord_mapgen_z")) or 2
)

exord_mg_custom.minc = vector.new(-mapsize.x, 0, -mapsize.z)
exord_mg_custom.maxc = vector.new( mapsize.x, 0.5,  mapsize.z)
exord_mg_custom.minp = exord_mg_custom.minc * 80
exord_mg_custom.maxp = exord_mg_custom.maxc * 80


----
dofile(mod_path .. "/register.lua")
----

exord_mg_custom.seed = math.random(1,999999999999999)

-- exord_mg_custom.set_generator("valleys", false)
