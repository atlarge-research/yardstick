
local function dist2(p1, p2)
    return (p1.x - p2.x)^2 + (p1.z - p2.z)^2 + (p1.y - p2.y)^2
end

local voronoi = {}
local voronoi_dist = {}
local function to_flat(x,y)
    x = math.min(100, math.max(0, math.round(x)))
    y = math.min(100, math.max(0, math.round(y)))
    return (x+1) + (y)*100
end
local function to_2d(i)
    i = math.round(i)
    return (i-1) % 100, math.floor((i-1)/100)
end

local function dist2xy(x1, y1, x2, y2)
    return (x1-x2)^2 + (y1-y2)^2
end

local biomes = {
    stone = {
        x=20, y=55,
        main_floor = {
            "exord_nodes:grass_stone",
            "exord_nodes:stone",
            "exord_nodes:stone",
            "exord_nodes:grass_stone",
            "exord_nodes:gravel",
            "exord_nodes:gravel",
        },
        main_wall = {
            "exord_nodes:grass_stone",
            "exord_nodes:stone",
            "exord_nodes:stone",
            "exord_nodes:gravel",
            "exord_nodes:gravel",
        },
        liquid     = "exord_nodes:lava",
        liquid_alt = "exord_nodes:rocks_lava",
    },
    tan = {
        x=86, y=47,
        light = 0.7,
        main_floor = {
            "exord_nodes:tan_dirt",
            "exord_nodes:tan_mud_blend",
            "exord_nodes:tan_dirt",
            "exord_nodes:tan_mud_blend",
            "exord_nodes:tan_mud_cracked",
        },
        main_wall = {
            "exord_nodes:tan_stone",
            "exord_nodes:tan_stone",
            "exord_nodes:sandstone",
        },
        liquid     = "exord_nodes:tan_mud_cracked",
        liquid_alt = "exord_nodes:tan_mud_blend",
        density_offset = -0.1,
    },
    dirt = {
        x=78, y=87,
        main_floor = {
            "exord_nodes:dirt_gravel",
            "exord_nodes:dirt_rocks_2",
        },
        main_wall = {
            "exord_nodes:sandstone",
            "exord_nodes:sandstone",
            "exord_nodes:tan_stone",
        },
        liquid     = "exord_nodes:lava",
        liquid_alt = "exord_nodes:rocks_lava",
    },
}

local function generate_voronoi()
    for x=0, 100 do for y=0, 100 do
        local mindist = 9999999
        local minbiome = nil
        for biomename, def in pairs(biomes) do
            local d = dist2xy(x, y, def.x, def.y)
            if d < mindist then
                mindist = d
                minbiome = def
            end
        end
        voronoi[to_flat(x, y)] = minbiome
        voronoi_dist[to_flat(x, y)] = mindist
    end end
end

generate_voronoi()

local function get_biome(x,y)
    return voronoi[to_flat(x, y)], voronoi_dist[to_flat(x, y)]
end

local heathumid_scale = 140
exord_mg_custom.register_generator("biomes", {
    nv_maps = {
        biomex = {
            np = {
                spread = {x = heathumid_scale, y = 1000000, z = heathumid_scale},
                seed = 645369,
                octaves = 3,
                persist = 0.4,
                lacunarity = 2.9,
                offset = 50.0,
                scale = 50.0,
            },
        },
        biomey = {
            np = {
                spread = {x = heathumid_scale, y = 1000000, z = heathumid_scale},
                seed = 3428,
                octaves = 3,
                persist = 0.4,
                lacunarity = 2.9,
                offset = 50.0,
                scale = 50.0,
            },
        },
        ter1 = {
            np = {
                spread = {x = 12, y = 1000000, z = 12},
                seed = 8467,
                octaves = 2,
                persist = 0.4,
                lacunarity = 2.11,
                offset = 0.5,
                scale = 0.5,
            },
        },
        cover = {
            np = {
                spread = {x = 12, y = 1000000, z = 12},
                seed = 8467,
                octaves = 2,
                persist = 0.2,
                lacunarity = 2.17,
                offset = 0.0,
                scale = 1.0,
            },
        },
        var1 = {
            np = {
                spread = {x = 6, y = 24, z = 6},
                seed = 7653,
                octaves = 2,
                persist = 0.2,
                lacunarity = 2.17,
                offset = 0.5,
                scale = 0.5,
            },
        },
        liquid1 = {
            np = {
                spread = {x = 16, y = 1000000, z = 16},
                seed = 4351,
                octaves = 3,
                persist = 0.3,
                lacunarity = 2.14,
                offset = 0.5,
                scale = 0.5,
            },
        },
        rand = {
            np = {
                spread = {x = 1, y = 1, z = 1},
                seed = 653474,
                octaves = 1,
                persist = 0.1,
                lacunarity = 2,
                offset = 0.0,
                scale = 1.0,
            },
        },
    },
    nv_perlin = {
    },
    enable_schems = false,
    nv = {
    },
    cid = {},
    barrier_node = "exord_nodes:barrier",
    on_initialise = function(self, seed)
    end,
    on_position_generated = function(self, pos, w, data, di, ni)
        local w_height = exord_core.map.wall_height
        if (pos.y > w_height + 9) then
            data[di] = exord_mg_custom.to_cid("exord_nodes:barrier")
            return
        end

        local nv_maps = self.nv_maps
        local d2 = dist2(pos, vector.new(0,pos.y,0))

        if d2 > (exord_mg_custom.maxp.x)^2 - 8 then
            if (pos.y <= w_height) then
                data[di] = exord_mg_custom.to_cid("exord_nodes:barrier_black")
            else
                data[di] = exord_mg_custom.to_cid("air")
            end
            return
        end

        local BX = nv_maps.biomex.data[ni]
        local BY = nv_maps.biomey.data[ni]
        local biome, bdist = get_biome(BX,BY)
        local df = math.min(1, math.max(0, bdist / (20^2)))
        if not biome then
            core.log("warning", BX .. " :: " .. BY)
            return
        end

        if (pos.y > w_height + 1) then
            if pos.y == w_height + 4 then
                if nv_maps.cover.data[ni] < (biome.light or 0.75) and (d2 > 10^2) then
                    data[di] = exord_mg_custom.to_cid(biome.barrier_node_light_block or "exord_nodes:barrier_light_block")
                    return
                else
                    data[di] = exord_mg_custom.to_cid(biome.barrier_node_sky or "exord_nodes:barrier_sky")
                    return
                end
            else
                data[di] = exord_mg_custom.to_cid(biome.barrier_node or "exord_nodes:barrier")
                return
            end
        end

        local T1 = nv_maps.ter1.data[ni]
        local V1 = nv_maps.var1.data[ni]

        local LIQUID = nv_maps.liquid1.data[ni]
        local RAND = nv_maps.rand.data[ni]

        local is_terrain = T1 < (0.5) + (df * (biome.density_offset or 0))
        local is_in_grace_zone = (d2 < 20^2)
        local is_solid = (pos.y <= 1 or (pos.y <= w_height and is_terrain)) and not ((pos.y > 1) and is_in_grace_zone)

        if not is_solid then
            data[di] = exord_mg_custom.to_cid("air")
            return
        end
        local is_floor = pos.y <= 1

        local nodename = biome.main_floor[1]
        if biome.liquid and math.abs(LIQUID) > 0.9 and not is_terrain and not is_in_grace_zone then
            if pos.y > (biome.liquid_y or 1) and pos.y <= w_height then
                local f = pos.y
                if f > 1 then f = math.min(w_height, math.max(1, f + math.floor(RAND + 1))) end
                if biome.liquid_glow then
                    data[di] = exord_mg_custom.to_cid(biome.liquid_glow..f)
                end
                return
            elseif pos.y == (biome.liquid_y or 1) then
                nodename = biome.liquid
            end
        elseif is_floor and (not is_in_grace_zone) and (not is_terrain)
        and biome.liquid_alt and math.abs(LIQUID) > 0.82 + RAND*0.05 and pos.y <= 1 then
            nodename = biome.liquid_alt
        elseif is_floor then
            local v = math.ceil(V1 * #biome.main_floor)
            v = math.min(#biome.main_floor, math.max(1, v))
            nodename = biome.main_floor[v]
        else
            local v = math.ceil(V1 * #biome.main_wall)
            v = math.min(#biome.main_wall, math.max(1, v))
            nodename = biome.main_wall[v]
        end
        if is_solid then
            data[di] = exord_mg_custom.to_cid(nodename..((not is_floor) and "_wall" or ""))
        end
    end,
})
