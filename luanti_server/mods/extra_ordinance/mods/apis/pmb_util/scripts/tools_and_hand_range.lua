
function pmb_util.get_tool_range(itemstack)
    local range = itemstack and itemstack:get_definition().range
    if not range then
        range = minetest.registered_items[""].range or 4
    end
    return range
end
