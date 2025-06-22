
local function dist2(p1, p2)
    return (p1.x - p2.x)^2 + (p1.z - p2.z)^2 + (p1.y - p2.y)^2
end

exord_mg_custom.register_generator("flat", {
    nv_maps = {
        cover = {
            np = {
                spread = {x = 20, y = 1000000, z = 20},
                seed = 8467,
                octaves = 4,
                persist = 0.1,
                lacunarity = 2.476,
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
        if false then
        elseif pos.y == 1 then
            data[di] = exord_mg_custom.to_cid("exord_nodes:stone")
        elseif pos.y > exord_core.map.wall_height + 1 and pos.y < exord_core.map.wall_height + 9 then
            if self.nv_maps.cover.data[ni] < 0.0 then
                data[di] = exord_mg_custom.to_cid("exord_nodes:barrier")
            else
                data[di] = exord_mg_custom.to_cid("exord_nodes:barrier_light_block")
            end
        else
            data[di] = exord_mg_custom.to_cid("air")
        end
    end,
})
