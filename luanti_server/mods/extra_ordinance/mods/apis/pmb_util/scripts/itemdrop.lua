
pmb_util.itemdrop = {}
pmb_util.itemdrop_nodes = {}

function pmb_util.register_tool_cap(name, param)
    pmb_util.itemdrop[name] = table.copy(param)
    return param
end

function pmb_util.get_tool_caps(name)
    return pmb_util.itemdrop[name]
end

function pmb_util.register_node_drop(name, param)
    pmb_util.itemdrop_nodes[name] = table.copy(param)
    return param
end

function pmb_util.get_node_drop(name)
    if pmb_util.itemdrop_nodes[name] then
        return pmb_util.itemdrop_nodes[name]
    end
    return nil
end

function pmb_util.drop_items(pos, items)
    for _, item in ipairs(items) do
        local obj = minetest.add_item(pos, item)
        if obj then
            obj:set_velocity(vector.new(
                (math.random()*2-1),
                2,
                (math.random()*2-1)
            ))
        end
    end
end

minetest.register_tool("pmb_util:dig_anything", {
    description = "",
    inventory_image = "white.png",
    tool_capabilities = pmb_util.register_tool_cap("pmb_util:dig_anything", {
        full_punch_interval = 1,
        groupcaps = {
            oddly_breakable_by_hand = {
                times = { 0.1, 0.1, 0.1, 0.1 },
            },
            cracky = {
                times = { 0.1, 0.1, 0.1, 0.1 },
            },
        },
    }),
    groups = { not_in_creative_inventory = 1, unobtainable = 1 },
})

local function test_tcaps(icaps, node)
    local can_drop = true
    for group, def in pairs(icaps.groupcaps) do
        if icaps and icaps[group] then def = icaps[group] end
        local gval = minetest.get_item_group(node.name, group)
        if gval > 0 then
            can_drop = false
            if ((not def.max_drop_level)
            or (def.max_drop_level and def.max_drop_level >= gval)) then
                can_drop = true
                break
            end
        end
    end
    return can_drop
end

function minetest.handle_node_drops(pos, drops, digger)
    local node = minetest.get_node(pos)
    -- local node_def = minetest.registered_nodes[node.name]

    if digger and digger.get_player_name and digger:get_player_name() == "" then
        digger = nil
    end

    local tool
    local tname
    if digger then
        tool = digger:get_wielded_item()
        tname = tool:get_name()
    else
        tname = "pmb_util:dig_anything"
        tool = ItemStack(tname)
    end

    local icaps = pmb_util.get_tool_caps(tname)
    if not icaps then
        tname = "__hand"
        -- minetest.log("no tool caps for "..tname)
    end

    local can_drop = true
    local hand_caps = pmb_util.get_tool_caps("__hand")

    local icap_drop = nil

    if icaps then
        can_drop = test_tcaps(icaps, node)
        -- minetest.log("got icaps")
    end
    if not can_drop and hand_caps then
        can_drop = test_tcaps(hand_caps, node)
        icap_drop = (icaps and icaps._on_get_drops and icaps._on_get_drops(tool, node, drops)) or nil
        -- minetest.log("can't drop")
    end

    if (not can_drop) and (icap_drop == nil) then
        drops = {}
    elseif icap_drop ~= nil then
        drops = icap_drop
    end

    local inv = digger and digger:get_inventory()
    if not inv then
        pmb_util.drop_items(pos, drops)
        -- minetest.log("no inventory, dropping on ground")
        return
    end

    -- drop if set by server or by player
    local drop_enabled
    if minetest.get_modpath("aom_settings") then
        drop_enabled = aom_settings.get_setting(digger, "gameplay_force_node_drop", true)
    else
        drop_enabled = minetest.settings:get_bool("pmb_node_drops", false)
    end

    if drop_enabled then
        pmb_util.drop_items(pos, drops)
        -- minetest.log("can drop")
    elseif inv then
        local idef = minetest.registered_nodes[node.name]
        local on_pickup = idef and idef.on_pickup or minetest.item_pickup
        for _, item in ipairs(drops) do
            drops[_] = on_pickup(ItemStack(item), digger, nil, nil)
        end
        pmb_util.drop_items(pos, drops)
        -- minetest.log("given to player")
    else
        pmb_util.drop_items(pos, drops)
        -- minetest.log("gave up and dropped")
    end
end

function pmb_util.get_drops_from_drop_table(drop_table)
    local max_items = drop_table.max_items
    local total_items = 0 -- counter for items
    local item_result = {}
    for _, drop in ipairs(drop_table.items) do
        if drop.chance == 1 or math.random(1, drop.rarity or 1) == 1 then
            for i, item in ipairs(drop.items) do
                local stack = ItemStack(item)
                local count = stack:get_count()
                total_items = total_items + count
                table.insert(item_result, stack)
                if total_items >= max_items then
                    stack:set_count(count - (total_items - max_items))
                    return true -- don't add more stacks if reached max
                end
            end
        end
    end
    return item_result
end

minetest.register_on_mods_loaded(function()
    if minetest.get_modpath("aom_settings") then
        aom_settings.register_setting(
            "gameplay_force_node_drop",
            minetest.get_modpath("age_of_mending") ~= nil, -- only use default drop if AoM
            "Nodes will drop items in world instead of inventory", "server"
        )
    end
end)

--[[
    Get a result from a list of items with proportional chances. Example:

    local itemlist = {
        {item = "my_mod:my_item", chance = 1},
        {item = "my_mod:my_other_item", chance = 8},
        {item = "my_mod:my_other_other_item", chance = 3},
    }
    local stack = ItemStack(pmb_util.get_droptable_item(itemlist))
    minetest.log(dump(pmb_util.get_droptable_item(itemlist)))
]]
function pmb_util.get_droptable_item(def, randfunc)
    randfunc = randfunc or math.random
    if def.max_chance == nil then
        def.max_chance = 0
        for i, entry in ipairs(def) do
            def.max_chance = def.max_chance + (entry.chance or 1)
        end
    end

    local rand_index = randfunc(1, def.max_chance)
    for i, entry in ipairs(def) do
        rand_index = rand_index - entry.chance
        if rand_index <= 0 then -- stop on the item which hits the index we wanted
            return entry.item
        end
    end
end
