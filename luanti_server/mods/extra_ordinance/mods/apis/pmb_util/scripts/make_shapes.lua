


local function texture_align_world(tiles)
    local r = {}
    for i, t in pairs(tiles) do
        if t.name then
            r[i] = {name = t.name}
        else
            r[i] = {name = t}
        end
        r[i].align_style = "world"
        r[i].scale = t.scale or 1
    end
    return r
end


local function apply_scrap_values(def, mult)
    do return end -- disable different value for shapes
    if not def._scrap then return end
    def._scrap = table.copy(def._scrap)
    for iname, val in pairs(def._scrap) do
        def._scrap[iname] = math.floor(val * mult)
        if def._scrap[iname] == 0 then
            def._scrap[iname] = nil
        end
    end
end

local function on_shape_for_node(node_name)
    if minetest.registered_nodes[node_name]._full_node_name ~= nil then return end
    minetest.override_item(node_name, {
        _full_node_name = node_name
    })
end


local slab_box = {
    -8/16,  -8/16, -8/16,
     8/16,   0,     8/16
}
function pmb_util.register_slab(node_name, flags)
    on_shape_for_node(node_name)
    if not flags then flags = {} end
    local def = table.copy(minetest.registered_nodes[node_name])
    def.name = node_name .. '_slab'
    def.groups = table.copy(def.groups)
    if not def then error(node_name.." is not a real node! Cannot make a slab!") end
    local name = string.split(node_name, ":")[1]
    def.groups.slab = 1
    def.groups.shape = 1
    def.groups["item_"..name.."_slab"] = 1
    def.groups.full_solid = 0
    for i, group in pairs(flags and flags.remove_groups or {}) do
        if def.groups[group] then
            def.groups[group] = nil
        end
    end
    def.description = (def.description .. ' slab')
    if def.groups.fuel then def.groups.fuel = math.floor(def.groups.fuel * 0.5) end
    apply_scrap_values(def, 4/8)
    def.drawtype = "nodebox"
    def.paramtype = "light"
    def.paramtype2 = "facedir"
    if flags.drop then def.drop = flags.drop end
    if flags.tiles then
        def.tiles = flags.tiles
    elseif flags.offset_textures == true then
        def.tiles[3] = "[combine:16x16:0,8="..def.tiles[3]
    elseif not flags.no_world_align then
        def.tiles = texture_align_world(def.tiles)
    end
    def.use_texture_alpha = "clip"
    def.node_box = {
        type = "fixed",
        fixed = slab_box
    }
    def.on_place = function(itemstack, placer, pointed_thing)
        local pi = player_info.get(placer)
        if pi and not (pi.ctrl.sneak and pi.ctrl.aux1) then
            return pmb_util.rotate_and_place_stair(itemstack, placer, pointed_thing, {no_yaw=true})
        else
            return minetest.rotate_and_place(itemstack, placer, pointed_thing, nil, {force_facedir=true})
        end
    end
    def._shape_name = "slab"

    minetest.register_node(def.name, def)

    if minetest.get_modpath("pmb_tcraft") then
        pmb_tcraft.register_craft({
            output = node_name..'_slab',
            items = {
                [node_name] = 1,
            }
        })
    end
end


-- Takes (tiles) and gives back tiles that fit properly for a stair texture, 
-- assuming you want the top of the side [3] texture to line up with the top of the steps
local function get_stair_textures(t)
    local r = {}
    r[1] = t[1]
    r[2] = t[2]
    -- right side
    r[3] = "[combine:16x16:0,8="..t[3]..":8,0="..t[3]
    -- left side
    r[4] = "[combine:16x16:0,8="..t[3]..":-8,0="..t[3]
    -- front side (facing away)
    r[5] = t[3]
    -- back side (facing player)
    r[6] = "[combine:16x16:0,0="..t[3]..":0,8="..t[3]
    return r
end

local stair_box = {
    {-8/16,-8/16, -8/16,
      8/16,    0,  8/16},
    {-8/16,    0,     0,
      8/16, 8/16,  8/16},
}
function pmb_util.register_stair(node_name, flags)
    on_shape_for_node(node_name)
    if not flags then flags = {} end
    local def = table.copy(minetest.registered_nodes[node_name])
    def.name = node_name .. '_stair'
    def.groups = table.copy(def.groups)
    if not def then error(node_name.." is not a real node! Cannot make a stair!") end
    local name = string.split(node_name, ":")[1]
    def.groups.stair = 1
    def.groups.shape = 1
    def.groups["item_"..name.."_stair"] = 1
    def.groups.full_solid = 0
    for i, group in pairs(flags and flags.remove_groups or {}) do
        if def.groups[group] then
            def.groups[group] = nil
        end
    end
    def.description = (def.description .. ' stair')
    if def.groups.fuel then def.groups.fuel = math.floor(def.groups.fuel * 0.75) end
    apply_scrap_values(def, 6/8)
    def.drawtype = "nodebox"
    def.paramtype = "light"
    def.paramtype2 = "facedir"
    if flags.drop then def.drop = flags.drop end
    if flags.tiles then
        def.tiles = flags.tiles
    elseif flags.offset_textures == true then
        def.tiles = (get_stair_textures(def.tiles))
    elseif not flags.no_world_align then
        def.tiles = texture_align_world(def.tiles)
    end
    def.use_texture_alpha = "clip"
    def.node_box = {
        type = "fixed",
        fixed = stair_box
    }
    def.on_place = function(itemstack, placer, pointed_thing)
        local pi = player_info.get(placer)
        if pi and not (pi.ctrl.sneak and pi.ctrl.aux1) then
            return pmb_util.rotate_and_place_stair(itemstack, placer, pointed_thing, {no_yaw=false})
        else
            return minetest.rotate_and_place(itemstack, placer, pointed_thing, nil, {force_facedir=nil,})
        end
    end
    def._shape_name = "stair"

    minetest.register_node(def.name, def)

    if minetest.get_modpath("pmb_tcraft") then
        pmb_tcraft.register_craft({
            output = node_name..'_stair',
            items = {
                [node_name] = 1,
            }
        })
    end
end




-- local beam_box = {
--      -8/16, -8/16,     0,
--       8/16,    0,  8/16,
-- }
local beam_box = {
    -2/16,  -8/16,  -8/16,
     2/16,   0/16,   8/16,
}
function pmb_util.register_beam(node_name, flags)
    on_shape_for_node(node_name)
    if not flags then flags = {} end
    local def = table.copy(minetest.registered_nodes[node_name])
    def.name = node_name .. '_beam'
    def.groups = table.copy(def.groups)
    if not def then error(node_name.." is not a real node! Cannot make a beam!") end
    local name = string.split(node_name, ":")[1]
    def.groups.beam = 1
    def.groups.shape = 1
    def.groups["item_"..name.."_beam"] = 1
    def.groups.full_solid = 0
    for i, group in pairs(flags and flags.remove_groups or {}) do
        if def.groups[group] then
            def.groups[group] = nil
        end
    end
    def.description = (def.description .. ' beam')
    if def.groups.fuel then def.groups.fuel = math.floor(def.groups.fuel * 0.25) end
    apply_scrap_values(def, 1/8)
    def.drawtype = "nodebox"
    def.paramtype = "light"
    def.paramtype2 = "facedir"
    if flags.drop then def.drop = flags.drop end
    if flags.tiles then
        def.tiles = flags.tiles
    elseif flags.offset_textures == true then
        def.tiles[3] = {name="[combine:16x16:0,8="..def.tiles[3]}
    elseif not flags.no_world_align then
        def.tiles = texture_align_world(def.tiles)
    end
    def.use_texture_alpha = "clip"
    def.node_box = {
        type = "fixed",
        fixed = beam_box
    }
    def.on_place = function(itemstack, placer, pointed_thing)
        local pi = player_info.get(placer)
        if pi and not (pi.ctrl.sneak and pi.ctrl.aux1) then
            return pmb_util.rotate_and_place_stair(itemstack, placer, pointed_thing, {no_yaw=false})
        else
            return minetest.rotate_and_place(itemstack, placer, pointed_thing, nil, {force_facedir=nil,})
        end
    end
    def._shape_name = "beam"

    minetest.register_node(def.name, def)

    if minetest.get_modpath("pmb_tcraft") then
        pmb_tcraft.register_craft({
            output = node_name..'_beam',
            items = {
                [node_name] = 1,
            }
        })
    end
end

local w = 4
local post_box = {
    {-w/16, -8/16, -w/16,
      w/16,  8/16,  w/16},
}
local post_count = 3
function pmb_util.register_post(node_name, flags)
    on_shape_for_node(node_name)
    if not flags then flags = {} end
    local def = table.copy(minetest.registered_nodes[node_name])
    def.name = node_name .. '_post'
    def.groups = table.copy(def.groups)
    if not def then error(node_name.." is not a real node! Cannot make a post!") end
    local name = string.split(node_name, ":")[1]
    def.groups.post = 1
    def.groups.shape = 1
    def.groups["item_"..name.."_post"] = 1
    def.groups.full_solid = 0
    for i, group in pairs(flags and flags.remove_groups or {}) do
        if def.groups[group] then
            def.groups[group] = nil
        end
    end
    if def.groups.fuel then def.groups.fuel = math.floor(def.groups.fuel * 0.25) end
    apply_scrap_values(def, 1/8)
    def.description = (def.description .. ' post')
    def.drawtype = "nodebox"
    def.paramtype = "light"
    def.paramtype2 = "facedir"
    if flags.drop then def.drop = flags.drop end
    if flags.tiles then
        def.tiles = flags.tiles
    elseif not flags.no_world_align then
        def.tiles = texture_align_world(def.tiles)
    end
    def.node_box = {
        type = "fixed",
        fixed = post_box
    }
    def.use_texture_alpha = "clip"
    def.on_place = function(itemstack, placer, pointed_thing)
        return minetest.rotate_and_place(itemstack, placer, pointed_thing, nil, {force_facedir=true})
    end
    def._shape_name = "post"

    minetest.register_node(node_name .. '_post', def)

    if minetest.get_modpath("pmb_tcraft") then
        pmb_tcraft.register_craft({
            output = node_name..'_post',
            items = {
                [node_name] = 1,
            }
        })
    end
end


w = 8
local quarter_box = {
    {-8/16, -8/16, -8/16,
      0/16,  0/16,  8/16},
}
function pmb_util.register_quarter(node_name, flags)
    on_shape_for_node(node_name)
    if not flags then flags = {} end
    local def = table.copy(minetest.registered_nodes[node_name])
    def.name = node_name .. '_quarter'
    def.groups = table.copy(def.groups)
    if not def then error(node_name.." is not a real node! Cannot make a quarter!") end
    local name = string.split(node_name, ":")[1]
    def.groups.post = 1
    def.groups.shape = 1
    def.groups["item_"..name.."_quarter"] = 1
    def.groups.full_solid = 0
    for i, group in pairs(flags and flags.remove_groups or {}) do
        if def.groups[group] then
            def.groups[group] = nil
        end
    end
    if def.groups.fuel then def.groups.fuel = math.floor(def.groups.fuel * 0.25) end
    apply_scrap_values(def, 1/8)
    def.description = (def.description .. " quarter")
    def.drawtype = "nodebox"
    def.paramtype = "light"
    def.paramtype2 = "facedir"
    if flags.drop then def.drop = flags.drop end
    if flags.tiles then
        def.tiles = flags.tiles
    elseif not flags.no_world_align then
        def.tiles = texture_align_world(def.tiles)
    end
    def.node_box = {
        type = "fixed",
        fixed = quarter_box
    }
    def.use_texture_alpha = "clip"
    def.on_place = function(itemstack, placer, pointed_thing)
        local pi = player_info.get(placer)
        if pi and not (pi.ctrl.sneak and pi.ctrl.aux1) then
            return pmb_util.rotate_and_place_quarter(itemstack, placer, pointed_thing, {no_yaw=false})
        else
            return minetest.rotate_and_place(itemstack, placer, pointed_thing, nil, {force_facedir=nil,})
        end
    end
    def._shape_name = "quarter"

    minetest.register_node(node_name .. "_quarter", def)

    if minetest.get_modpath("pmb_tcraft") then
        pmb_tcraft.register_craft({
            output = node_name.."_quarter",
            items = {
                [node_name] = 1,
            }
        })
    end
end


local shapes = {
    slab = pmb_util.register_slab,
    stair = pmb_util.register_stair,
    post = pmb_util.register_post,
    beam = pmb_util.register_beam,
    quarter = pmb_util.register_quarter,
}
function pmb_util.register_all_shapes(node_name, exclude, flags)
    exclude = exclude or {}
    for shape, func in pairs(shapes) do
        if not exclude[shape] then
            func(node_name, flags)
        end
    end
end
