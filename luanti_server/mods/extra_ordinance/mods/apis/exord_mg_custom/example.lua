
local function dist2(p1, p2)
    return (p1.x - p2.x)^2 + (p1.z - p2.z)^2 + (p1.y - p2.y)^2
end

exord_mg_custom.register_generator("flat", {
    nv_maps = {
        ter1 = {
            np = {
                spread = {x = 16, y = 10000, z = 16},
                seed = 8467,
                octaves = 2,
                persist = 0.4,
                lacunarity = 2.11,
                offset = 0.0,
                scale = 1.0,
            },
        },
        var1 = {
            np = {
                spread = {x = 30, y = 10000, z = 30},
                seed = 7653,
                octaves = 4,
                persist = 0.6,
                lacunarity = 2.5,
                offset = 0.0,
                scale = 1.0,
            },
        },
        var2 = {
            np = {
                spread = {x = 6, y = 10000, z = 6},
                seed = 876,
                octaves = 2,
                persist = 0.8,
                lacunarity = 2,
                offset = 0.0,
                scale = 1.0,
            },
        },
        lava1 = {
            np = {
                spread = {x = 30, y = 10000, z = 30},
                seed = 4351,
                octaves = 3,
                persist = 0.3,
                lacunarity = 2.8,
                offset = 0.0,
                scale = 1.0,
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
        local nv_maps = self.nv_maps
        local T1 = nv_maps.ter1.data[ni]
        local V1 = nv_maps.var1.data[ni]
        local V2 = nv_maps.var2.data[ni]
        local LAVA1 = nv_maps.lava1.data[ni]
        local RAND = nv_maps.rand.data[ni]

        local w_height = exord_core.map.wall_height
        local d2 = dist2(pos, vector.new(0,pos.y,0))
        local is_terrain = T1 < -0.3
        local is_in_grace_zone = (d2 < 20^2)
        local is_solid = (pos.y <= 1 or (pos.y <= w_height and is_terrain)) and not ((pos.y > 1) and is_in_grace_zone)
        local is_floor = pos.y <= 1
        local nodename = "exord_nodes:stone"
        if math.abs(LAVA1) > 0.8 and not is_terrain and not is_in_grace_zone then
            if pos.y >= 1 and pos.y <= w_height then
                local f = pos.y
                if f > 1 then f = math.min(w_height, math.max(1, f + math.floor(RAND + 1))) end
                data[di] = exord_mg_custom.to_cid("exord_nodes:lava_glow_"..f)
                return
            elseif pos.y == 0 then
                nodename = "exord_nodes:lava"
            end
        elseif V1 > 0.6 then
            nodename = "exord_nodes:gravel"
        elseif V2 > 0.2 then
            nodename = "exord_nodes:gravel"
        else
            nodename = "exord_nodes:stone"
        end
        if (pos.y > w_height and pos.y < w_height + 6) and (d2 > 10^2) then
            data[di] = exord_mg_custom.to_cid("exord_nodes:barrier_translucent")
        elseif is_solid then
            data[di] = exord_mg_custom.to_cid(nodename..((not is_floor) and "_wall" or ""))
        else
            data[di] = exord_mg_custom.to_cid("air")
        end
    end,
})
