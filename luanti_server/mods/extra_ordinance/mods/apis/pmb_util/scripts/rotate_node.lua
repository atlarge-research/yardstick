
-- just use a lookup table because it's easier
pmb_util.node_dirs = {
    [tostring(vector.new(1, 0, 0))] = 12 + 1,
    [tostring(vector.new(0, 0, -1))] = 8 + 2,
    [tostring(vector.new(0, 0, 1))] = 4 + 0,
    [tostring(vector.new(-1, 0, 0))] = 16 + 3,
    [tostring(vector.new(0, 1, 0))] = 0,
    [tostring(vector.new(0, -1, 0))] = 20,
}

-- returns a vector that has the binary of the best look direction
-- if you put in (0.1, 0.9, 0.2) it will give you (0, 1, 0) because 0.9 is the biggest
function pmb_util.get_face_dir_vector(v)
    if math.abs(v.y) > math.abs(v.x) and math.abs(v.y) > math.abs(v.z) then
        v.x = 0
        v.z = 0
    elseif math.abs(v.x) > math.abs(v.z) then
        v.z = 0
        v.y = 0
    else
        v.x = 0
        v.y = 0
    end
    return v
end

local function get_node_info(pos)
    local node = minetest.get_node_or_nil(pos)
    if not node then return end
    return node, minetest.registered_nodes[node.name]
end

-- places the node so that the base of the node is attached to the face of the node you're pointing at
function pmb_util.rotate_and_place(itemstack, placer, pointed_thing)
    if not placer then return itemstack end
    local ret = pmb_util.try_rightclick(itemstack, placer, nil, false)
    if ret then
        return ret, nil
    end
    local stack = minetest.rotate_and_place(ItemStack(itemstack), placer, pointed_thing, nil, {})
    if placer and placer:is_player() and minetest.is_creative_enabled(placer:get_player_name()) then
        return itemstack
    end
    return stack
end

function pmb_util.rotate_and_place_against(itemstack, placer, pointed_thing, flags)
    if not placer then return itemstack end
    local ret = pmb_util.try_rightclick(itemstack, placer, nil, true)
    if ret then
        return ret, nil
    end
    -- make sure you don't index nil
    if flags == nil then flags = {} end

    -- get the name of the node
    local wield_name = itemstack:get_name()

    local facedir = 0

    -- copy the node you're placing it to if the flag is set
    local place_node = minetest.get_node(pointed_thing.under)
    if flags.copy_same_node and place_node and place_node.name == wield_name then
        facedir = place_node.param2
    else
        local dir = vector.subtract(pointed_thing.under, pointed_thing.above)
        facedir = minetest.dir_to_facedir(dir, true)
    end

    -- predict if under or above, then pipe this to the can_place callback if given
    if flags.can_place then
        local unode, udef = get_node_info(pointed_thing.under)
        local anode, adef = get_node_info(pointed_thing.above)
        local predict_pos = (udef and udef.buildable_to and pointed_thing.under) or (adef and adef.buildable_to and pointed_thing.above)
        if predict_pos then
            local node = {name=wield_name, param2=0, param1=0}
            if not flags.can_place(predict_pos, node) then
                return itemstack, nil
            end
        end
    end

    local retpos
    itemstack, retpos = minetest.item_place_node(itemstack, placer, pointed_thing, facedir)

    return itemstack, retpos
end

local UP = vector.new(0,1,0)
local function get_eyepos(player)
    local eyepos = player:get_pos() + (player:get_eye_offset()*0.1):rotate_around_axis(UP, player:get_look_horizontal())
    eyepos.y = eyepos.y + player:get_properties().eye_height
    return eyepos
end

local stair_look_dir = {
    [tostring(vector.new(0, 0, 1))] = 0,
    [tostring(vector.new(1, 0, 0))] = 1,
    [tostring(vector.new(0, 0, -1))] = 2,
    [tostring(vector.new(-1, 0, 0))] = 3,
}


function pmb_util.get_ray_intersect_from_look(itemstack, player, pointed_thing, flags)
    local lookdir = vector.normalize(player:get_look_dir())
    local pos = get_eyepos(player)
    local range = itemstack:get_definition().range or 12
    local lookpos = vector.multiply(lookdir, range)
    lookpos = vector.add(lookpos, pos)
    pointed_thing = nil

    local ray = minetest.raycast(pos, lookpos, false, false)
    for pt in ray do
        if pt.type == "node" then
            pointed_thing = pt
            break
        end
    end
    return pointed_thing
end


function pmb_util.rotate_and_place_stair(itemstack, placer, pointed_thing, flags)
    local ret = pmb_util.try_rightclick(itemstack, placer, nil)
    if ret then return ret end
    if not pointed_thing then return itemstack end
    if pointed_thing.type ~= "node" then return itemstack end
    local def = minetest.registered_nodes[minetest.get_node(pointed_thing.above).name]
    if (not def) or not (def.buildable_to) then return itemstack end

    pointed_thing = pmb_util.get_ray_intersect_from_look(itemstack, placer, pointed_thing, flags)

    if (not pointed_thing) or not pointed_thing.intersection_point then
        return itemstack end

    local facedir = 0
    local intpos = pointed_thing.intersection_point
    local y_dir = pointed_thing.under.y - pointed_thing.above.y
    intpos.x = math.abs(intpos.x % 1)
    intpos.y = math.abs((intpos.y-y_dir*0.001) % 1)
    intpos.z = math.abs(intpos.z % 1)
    if (intpos.y < 0.5) then
        facedir = 20
    end

    -- copy the node you're placing it to if the flag is set
    local place_node = minetest.get_node(pointed_thing.under)
    if flags.copy_same_node and place_node and place_node.param2 then
        facedir = place_node.param2
    elseif not (flags and flags.no_yaw) then
        -- local norm = vector.subtract(pointed_thing.under, pointed_thing.above)
        local look_dir = minetest.yaw_to_dir(placer:get_look_horizontal())
        look_dir = vector.round(pmb_util.get_face_dir_vector(look_dir))
        local result = stair_look_dir[tostring(look_dir)]
        local to_facedir = 0
        if result then to_facedir = result end
        if facedir == 20 and (to_facedir % 2 == 1) then
            to_facedir = (to_facedir + 2) % 4
        end
        facedir = (facedir + to_facedir) % 25
    end

    return minetest.item_place(itemstack, placer, pointed_thing, facedir)
end


pmb_util.quarter_facedir_array = {
    get_facedir = function(self, pos, face)
        local ta = {
            tostring(face)..":",
            tostring(math.floor(math.abs(pos.x % 1)*2)),
            tostring(math.floor(math.abs(pos.y % 1)*2)),
            tostring(math.floor(math.abs(-pos.z % 1)*2))
        }
        -- ignore axis of face
        local fi = self.face_axis_ignore[face]
        ta[fi] = "1"

        local t = ""
        for i, v in pairs(ta) do
            t = t..v
        end
        return self[t] or 0
    end,
    face_axis_ignore = {
        [5]=4,
        [4]=4,
        [3]=2,
        [2]=2,
        [1]=3,
        [0]=3,
    },

    ["5:111"] = 0,
    ["5:011"] = 2,
    ["5:001"] = 20,
    ["5:101"] = 22,

    ["4:101"] = 22,
    ["4:001"] = 20,
    ["4:111"] = 0,
    ["4:011"] = 2,

    ["2:100"] = 23,
    ["2:101"] = 21,
    ["2:111"] = 1,
    ["2:110"] = 3,

    ["3:100"] = 23,
    ["3:101"] = 21,
    ["3:111"] = 1,
    ["3:110"] = 3,

    ["1:111"] = 8,
    ["1:011"] = 10,
    ["1:010"] = 6,
    ["1:110"] = 4,

    ["0:110"] = 4,
    ["0:010"] = 6,
    ["0:111"] = 8,
    ["0:011"] = 10,
}

function pmb_util.rotate_and_place_quarter(itemstack, placer, pointed_thing, flags)
    local ret = pmb_util.try_rightclick(itemstack, placer, nil)
    if ret then return ret end
    if not pointed_thing then return itemstack end
    if pointed_thing.type ~= "node" then return itemstack end
    local def = minetest.registered_nodes[minetest.get_node(pointed_thing.above).name]
    if (not def) or not (def.buildable_to) then return itemstack end

    pointed_thing = pmb_util.get_ray_intersect_from_look(itemstack, placer, pointed_thing, flags)

    if (not pointed_thing) or not pointed_thing.intersection_point then
        return itemstack end

    local facedir = 0
    local intpos = pointed_thing.intersection_point
    facedir = pmb_util.quarter_facedir_array:get_facedir(
        intpos,
        minetest.dir_to_wallmounted(pointed_thing.under - pointed_thing.above))

    return minetest.item_place(itemstack, placer, pointed_thing, facedir)
end

local adjacent = {
    [0] = vector.new( 0,-1, 0),
    [1] = vector.new( 0, 1, 0),
    [2] = vector.new( 1, 0, 0),
    [3] = vector.new(-1, 0, 0),
    [4] = vector.new( 0, 0, 1),
    [5] = vector.new( 0, 0,-1),
}

function pmb_util.rotate_to_any_walkable(pos)
    local node = minetest.get_node(pos)
    for i=2, #adjacent do
        local p = vector.subtract(pos, adjacent[i])
        if minetest.registered_nodes[minetest.get_node(p).name].walkable then
            node.param2 = minetest.dir_to_facedir(vector.multiply(adjacent[i], -1))
            minetest.swap_node(pos, node)
            return true
        end
    end
end

function pmb_util.rotate_to_group(pos, group)
    local node = minetest.get_node(pos)
    for i=1, #adjacent+1 do
        local p = vector.subtract(pos, adjacent[i%6])
        if minetest.get_item_group(minetest.get_node(p).name, group) ~= 0 then
            node.param2 = (pmb_util.node_dirs[tostring(vector.multiply(adjacent[i%6], 1))])
            minetest.swap_node(pos, node)
            return true
        end
    end
end

