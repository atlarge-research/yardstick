local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(minetest.get_current_modname())



local voronoi
local function to_flat(x,y)
    x = math.round(x)
    y = math.round(y)
    return (x+1) + (y)*100
end
local function to_2d(i)
    i = math.round(i)
    return (i-1) % 100, math.floor((i-1)/100)
end
local function dist2(x1, y1, x2, y2)
    return (x1-x2)^2 + (y1-y2)^2
end

local function generate_voronoi()
    voronoi = {}
    for x=0, 100 do for y=0, 100 do
        local mindist = 999
        local minbiome = nil
        for biomename, def in pairs(minetest.registered_biomes) do
            local d = dist2(x, y, def.heat_point, def.humidity_point)
            if d > mindist then
                mindist = d
                minbiome = def
            end
        end
        voronoi[to_flat(x, y)] = minbiome
    end end
end

local function get_voronoi(heat, humid)
    return voronoi[to_flat(heat, humid)]
end

local function is_position_within_bounds(p)
    if math.abs(p.x)>31000 then return false end
    if math.abs(p.y)>31000 then return false end
    if math.abs(p.z)>31000 then return false end
    return true
end

function pmb_util.find_biome(centerpos, biomename)
    local perlinheat = PerlinNoise(minetest.get_mapgen_setting_noiseparams("mg_biome_np_heat") or {})
    local perlinhumid = PerlinNoise(minetest.get_mapgen_setting_noiseparams("mg_biome_np_humidity") or {})
    local biomedef = minetest.registered_biomes[biomename]
    if not biomedef then return end
    local chsize = 20
    local searchsize = 40
    if not voronoi then generate_voronoi() end
    for x = -searchsize, searchsize do
    for y = -4, 4 do
    for z = -searchsize, searchsize do repeat
        local pos = vector.new(
            x * chsize + centerpos.x,
            y * chsize + centerpos.y,
            z * chsize + centerpos.z
        )
        local nvheat = perlinheat:get_3d(pos)
        local nvhumid = perlinhumid:get_3d(pos)
        local biome = get_voronoi(nvheat, nvhumid)
        if biome and biome.name == biomedef.name then
            return pos
        end
    until true end end end
end

minetest.register_chatcommand("findbiome", {
    params = "(biomename)",
    description = S("Looks for a biome"),
    privs = {give = true},
    func = function(name, param)
        local player = minetest.get_player_by_name(name)
        local centerpos = player:get_pos()
        local biomepos = pmb_util.find_biome(centerpos, param)
        if not biomepos then return false, "Biome not valid, or none found." end
        return true, "Found biome at "..tostring(biomepos)
    end
})

minetest.register_chatcommand("gobiome", {
    params = "(biomename)",
    description = S("Looks for a biome and teleports you there"),
    privs = {give = true},
    func = function(name, param)
        local player = minetest.get_player_by_name(name)
        local centerpos = player:get_pos()
        local biomepos = pmb_util.find_biome(centerpos, param)
        if not biomepos then return false, "Biome not valid, or none found."
        else
            if not is_position_within_bounds(biomepos) then return false, "" end
            player:set_pos(biomepos)
        end
        return true, "Found biome at "..tostring(biomepos)
    end
})

