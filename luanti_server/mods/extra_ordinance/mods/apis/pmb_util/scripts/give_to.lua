

function pmb_util.give_to(object, stack)
    if not minetest.is_player(object) then return false end
    local inv = object:get_inventory()
    stack = inv:add_item("main", stack)
    if not stack:is_empty() then
        minetest.add_item(object:get_pos(), stack)
    end
    return true
end
