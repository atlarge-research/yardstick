
local mg_name = minetest.get_mapgen_setting("mg_name")
local is_flat_creative = mg_name and ((mg_name == "flat") or (mg_name == "singlenode")) and minetest.is_creative_enabled()

minetest.register_node("pmb_util:barrier", {
    description = "barrier",
    groups = { solid = 1, blast_resistance = -1 },
    paramtype = 'light',
    drawtype = "airlike",
    sunlight_propagates = true,
    floodable = false,
    pointable = false,
    walkable = true,
    buildable_to = false,
    diggable = false,
    drop = "",
})


local function destroy_near(pos)
    minetest.set_node(pos, {name="air"})
    local size = 4
    local near = minetest.find_nodes_in_area(
        vector.offset(pos, -size, -size, -size),
        vector.offset(pos,  size,  size,  size),
        {"pmb_util:temp_air"}, true
    )
    for i, p in ipairs((near and near["pmb_util:temp_air"]) or {}) do
        minetest.set_node(p, {name="air"})
    end
end

local cid_air = minetest.get_content_id("air")
minetest.register_node("pmb_util:temp_air", {
    description = "for schematics",
    groups = { blast_resistance = -1, dig_immediate = 3, no_mapgen = 1, },
    paramtype = 'light',
    drawtype = (is_flat_creative and "nodebox") or "airlike",
    use_texture_alpha = "blend",
    node_box = {
        type = "fixed",
        fixed = {
            -4/16, -4/16, -4/16,
             4/16,  4/16,  4/16,
        },
    },
    tiles = {"blank.png^[noalpha^[colorize:#ffeeaae0:255"},
    sunlight_propagates = true,
    floodable = false,
    pointable = is_flat_creative,
    _on_node_update = is_flat_creative and function(pos, ...)
        if is_flat_creative then return end
        destroy_near(pos)
    end,
    walkable = false,
    buildable_to = true,
    diggable = true,
    drop = "",
})
