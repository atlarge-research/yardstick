
function pmb_util.take_if_not_creative_player(itemstack, player)
    if (not minetest.is_player(player)) or not minetest.is_creative_enabled(player:get_player_name()) then
        itemstack:take_item(1)
    end
    return itemstack
end
