

pmb_wield.playerdata = {}

--[[
pl[player_ref] -->
    last_list,
    last_index,
    last_stack,
]]
local pl = {}

-- [1] on_select, [2] on_deselect, [3] on_step
local registers = {
    {}, {}, {},
}

-- call all registered funcs for this event
local function on_select(stack, player)
    for i, func in ipairs(registers[1]) do
        stack = func(ItemStack(stack), player) or stack
    end
    return stack
end
-- call all registered funcs for this event
local function on_deselect(stack, player)
    for i, func in ipairs(registers[2]) do
        stack = func(ItemStack(stack), player) or stack
    end
    return stack
end
-- call all registered funcs for this event
local function on_step(stack, player, dtime)
    for i, func in ipairs(registers[3]) do
        stack = func(ItemStack(stack), player, dtime) or stack
    end
    return stack
end

-- function(stack, player) ==> nil | itemstack
function pmb_wield.register_on_select(func)
    registers[1][#registers[1]+1] = func
end
-- functionct(stack, player) ==> nil | itemstack
function pmb_wield.register_on_deselect(func)
    registers[2][#registers[1]+1] = func
end
-- function(stack, player, dtime) ==> nil | itemstack
function pmb_wield.register_on_step(func)
    registers[3][#registers[1]+1] = func
end

-- make sure not nil, return if was nil (new player seen)
local function check_player(player)
    if not pl[player] then
        pl[player] = {}
        return true
    end
    return false
end

local function do_player_equipment_tick(player, dtime)
    local inv = player:get_inventory()
    for listname, _ in pairs(pmb_wield.on_move.equipment_lists) do
        local list = inv:get_list(listname)
        for k, stack in ipairs(list or {}) do repeat
            local def = stack:get_definition()
            if not def then break end
            if def._on_equipment_step then
                stack = def._on_equipment_step(ItemStack(stack), player, dtime)
                if stack then
                    inv:set_stack(listname, k, stack)
                end
            end
        until true end
    end
end

-- runs through checks and callbacks and sets stacks if the callbacks return any
local function player_tick(player, dtime)
    local first_tick_for_player = check_player(player)

    local pi = pl[player]
    local inv = player:get_inventory()

    local w = {}
    w.stack = player:get_wielded_item()
    w.list = player:get_wield_list()
    w.index = player:get_wield_index()

    local f
    if not first_tick_for_player and pi.last_index then
        f = {
            stack = pi.last_stack
        }
    end

    -- only trigger calls if it changed, but forget meta and wear
    w.changed = (not f) or (w.stack:get_name() ~= f.stack:get_name())
    w.changed = w.changed or ((pi.last_index ~= w.index) or pi.last_list ~= w.list)
    w.changed = w.changed or not w.stack:equals(inv:get_stack(pi.last_list, pi.last_index))

    -- if wield changed, or is first time ticked
    -- if (not f) or not w.stack:equals(f.stack) then w.changed = true end

    w.def = w.stack:get_definition() or {}

    -- if the wield item has changed, run through the on deselect and select funcs

    -- on deselect
    if w.changed and f then
        local ret
        f.def = f.stack:get_definition() or {}
        -- on deselect
        ret = on_deselect(ItemStack(f.stack), player)
        ret = (f.def.on_deselect and f.def.on_deselect(ItemStack(ret or f.stack), player)) or ret
        if (ret ~= nil) and not ret:equals(f.stack) then
            f.stack_changed = true -- later, only set if there's a change
            f.stack = ItemStack(ret)
        end
    end

    -- on select
    if w.changed then
        local ret
        ret = on_select(ItemStack(w.stack), player)
        ret = (w.def.on_select and w.def.on_select(ItemStack(ret or w.stack), player)) or ret
        if (ret ~= nil) and not ret:equals(w.stack) then
            w.stack_changed = true -- later, only set if there's a change
            w.stack = ItemStack(ret)
        end
    end


    if w.def.on_step then
        local ret = on_step(ItemStack(w.stack), player, dtime)
        ret = w.def.on_step(ItemStack(ret or w.stack), player, dtime) or ret
        if (ret ~= nil) and not w.stack:equals(ret) then
            w.stack_changed = true -- later, only set if there's a change
            w.stack = ItemStack(ret)
        end
    end


    -- only set any changes if changes were made
    if w.stack_changed then
        inv:set_stack(w.list, w.index, w.stack)
        -- minetest.log(w.stack:to_string())
    end
    if f and f.stack_changed then
        inv:set_stack(pi.last_list, pi.last_index, f.stack)
    end
    pi.last_list = w.list
    pi.last_index = w.index
    pi.last_stack = w.stack

    do_player_equipment_tick(player, dtime)
    -- cool, desel, windup, decel, cool
end

minetest.register_globalstep(function(dtime)
    for i, player in ipairs(minetest.get_connected_players()) do
        player_tick(player, dtime)
    end
end)


local function deselect_wielded(player, fromstack, set_stack)
    local last_list = player:get_wield_list()
    local last_index = player:get_wield_index()
    local inv = player:get_inventory()

    local f = {stack = fromstack or inv:get_stack(last_list, last_index)}
    local ret
    f.def = f.stack:get_definition()
    -- on deselect
    ret = on_deselect(ItemStack(f.stack), player)
    ret = (f.def.on_deselect and f.def.on_deselect(ItemStack(ret or f.stack), player)) or ret
    if (ret ~= nil) and not ret:equals(f.stack) then
        f.stack_changed = true -- later, only set if there's a change
        f.stack = ItemStack(ret)
    end
    if set_stack and f and f.stack_changed then
        inv:set_stack(last_list, last_index, f.stack)
    end
    return f.stack
end

-- must do this after all other modifications to this function
minetest.register_on_mods_loaded(function()
-- if dropped, 
local core_drop = minetest.item_drop
minetest.item_drop = function(itemstack, dropper, pos)
    local do_set
    if dropper:is_player() and itemstack:equals(dropper:get_wielded_item()) then
        check_player(dropper)
        itemstack = deselect_wielded(dropper, itemstack, false)
        local pi = pl[dropper]
        pi.last_list = dropper:get_wield_list()
        pi.last_index = dropper:get_wield_index()
        do_set = true
    end

    itemstack = core_drop(itemstack, dropper, pos)

    if do_set then
        pl[dropper].last_stack = itemstack
    end
    return itemstack
end

minetest.register_on_leaveplayer(function(player, timed_out)
    deselect_wielded(player, nil, true)
end)

end)


