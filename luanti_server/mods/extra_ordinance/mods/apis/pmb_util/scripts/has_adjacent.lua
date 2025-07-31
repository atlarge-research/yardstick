
local adjacent = {
    [0] = vector.new( 0,-1, 0),
    [1] = vector.new( 0, 1, 0),
    [2] = vector.new( 1, 0, 0),
    [3] = vector.new(-1, 0, 0),
    [4] = vector.new( 0, 0, 1),
    [5] = vector.new( 0, 0,-1),
}

function pmb_util.has_adjacent(pos, group)
    local count = 0
    local node
    for i, offset in pairs(adjacent) do
    local p = vector.add(pos, offset)
    local n = minetest.get_node(p).name
    if n == group or minetest.get_item_group(n, group) ~= 0 then
        count = count + 1
        node = node or minetest.get_node(p)
    end
    end
    return count, node
end

function pmb_util.has_to_side(pos, group)
    local count = 0
    local node
    for i=2, #adjacent do
    local p = vector.add(pos, adjacent[i])
    local n = minetest.get_node(p).name
    if n == group or minetest.get_item_group(n, group) ~= 0 then
        count = count + 1
        node = minetest.get_node(p)
    end
    end
    return count, node
end

function pmb_util.has_vertically(pos, group)
    local count = 0
    local node
    for i=0, 1 do
    local p = vector.add(pos, adjacent[i])
    local n = minetest.get_node(p).name
    if n == group or minetest.get_item_group(n, group) ~= 0 then
        count = count + 1
        node = minetest.get_node(p)
    end
    end
    return count, node
end
