
pmb_wield.on_move = {}

pmb_wield.on_move.listeners = {}

function pmb_wield.on_move.register_on_move_item(name, func)
    if not pmb_wield.on_move.listeners[name] then pmb_wield.on_move.listeners[name] = {} end
    pmb_wield.on_move.listeners[name][#pmb_wield.on_move.listeners[name]+1] = func
end


minetest.register_on_player_inventory_action(function(player, action, inventory, inventory_info)
    local item = {}
    local info = {}
    if action == "move" then
        item.stack = inventory:get_stack(inventory_info.to_list, inventory_info.to_index)
        item.name = item.stack:get_name()
        info = inventory_info
        info.stack = item.stack
    elseif action == "put" then
        item.stack = inventory_info.stack
        item.name = item.stack:get_name()
        info = {
            to_list = inventory_info.listname,
            to_index = inventory_info.index,
            stack = item.stack}
    elseif action == "take" then
        item.stack = inventory_info.stack
        item.name = item.stack:get_name()
        info = {
            from_list = inventory_info.listname,
            from_index = inventory_info.index,
            stack = item.stack}
    end
    if item.name then
        pmb_wield.on_move.on_moved(player, item.name, info)
    end
end)


local equipment_lists = {
    armor = true,
    accessories = true,
}
pmb_wield.on_move.equipment_lists = equipment_lists

function pmb_wield.on_move.add_equipment_list(listname)
    equipment_lists[listname] = true
end

function pmb_wield.on_move.remove_equipment_list(listname)
    equipment_lists[listname] = nil
end

function pmb_wield.on_move.test_and_call_equipment(stack, player, info, idef)
    if not idef then return end
    if idef._on_move_item then
        idef._on_move_item(stack, player, info)
    end

    if equipment_lists[info.to_list] and not equipment_lists[info.from_list] then
        pmb_wield.on_move.on_equipped(stack, player, info, idef)
    elseif equipment_lists[info.from_list] and not equipment_lists[info.to_list] then
        pmb_wield.on_move.on_unequipped(stack, player, info, idef)
    end
end

function pmb_wield.on_move.on_equipped(stack, player, info, idef)
    if idef and idef._on_equipped then
        idef._on_equipped(stack, player, info)
    end
end

function pmb_wield.on_move.on_unequipped(stack, player, info, idef)
    if idef and idef._on_unequipped then
        idef._on_unequipped(stack, player, info)
    end
end


function pmb_wield.on_move.on_moved(player, name, info)
    for i, func in pairs(pmb_wield.on_move.listeners[name] or {}) do
        func(player, info)
    end

    local stack = info.stack
    if not stack then return end
    local idef = minetest.registered_items[stack:get_name()]
    pmb_wield.on_move.test_and_call_equipment(stack, player, info, idef)
end


minetest.register_on_joinplayer(function(player, last_login)
    minetest.after(0.1, function()
        if not player then return end
        local inv = player:get_inventory()
        if not inv then return end
        for listname, list in pairs(inv:get_lists()) do
            for i = 1, inv:get_size(listname) do
                local stack = inv:get_stack(listname, i)
                local name = stack:get_name()
                if name then
                    pmb_wield.on_move.on_moved(player, name, {
                        to_list = listname,
                        to_index = i,
                        stack = stack,
                        is_from_joining = true,
                    })
                end
            end
        end
    end)
end)
