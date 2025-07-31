

local delme = function(p)
    local node = minetest.get_node(p)
    if minetest.get_item_group(node.name, "pmb_util_transient_light") > 0 then
        minetest.set_node(p, {name = "air"})
    end
end

for i = 1, 14 do
    minetest.register_node("pmb_util:light_node_"..i, {
        description = "Light",
        groups = { pmb_util_transient_light = i, not_in_creative_inventory = 1, },
        paramtype = 'light',
        drawtype = "airlike",
        floodable = true,
        pointable = false,
        walkable = false,
        buildable_to = true,
        sunlight_propagates = true,
        drop = "",
        light_source = i,
        on_timer = delme,
        on_construct = function(pos)
            minetest.get_node_timer(pos):start(5)
        end
    })
end

-- minetest.register_abm({
--     nodenames = {"group:pmb_util_transient_light"},
--     interval = 5.0,
--     chance = 10,
--     action = function(pos, node, active_object_count, active_object_count_wider)
--         if not minetest.get_node_timer(pos).is_started then
--             minetest.get_node_timer(pos):start(1)
--         end
--     end
-- })
