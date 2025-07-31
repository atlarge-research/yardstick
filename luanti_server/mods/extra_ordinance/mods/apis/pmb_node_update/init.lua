

-- this is intended to form a node update system, where if a node is updated by being dug, it notifies its neighbours in case they need to do something in response.

pmb_node_update = {}


pmb_node_update.update_functions = {}


local calls = 0
local call_limit = 500 -- per step

local function reset_calls(dtime)
    -- if calls ~= 0 then
    --   minetest.log(calls)
    -- end
    if calls > call_limit then
        minetest.log("WARNING! TOO MANY NODE UPDATES ARE HAPPENING.")
    end
    calls = 0
end

minetest.register_globalstep(reset_calls)

function pmb_node_update.register_on_node_update(func)
    pmb_node_update.update_functions[#pmb_node_update.update_functions+1] = func
end

local adjacent = {
    [1] = vector.new(0, 1, 0),
    [2] = vector.new(0, -1, 0),
    [3] = vector.new(1, 0, 0),
    [4] = vector.new(-1, 0, 0),
    [5] = vector.new(0, 0, 1),
    [6] = vector.new(0, 0, -1),
}

local function propagate(pos, cause, user, count, delay, payload, last_pos)
    local offset = 2 -- math.random(0, 5)
    for i=1, #adjacent do
        local p = adjacent[(i + offset) % 6 + 1]
        local v = vector.add(pos, p)
        if (not last_pos) or not vector.equals(v, last_pos) then
            pmb_node_update.update_node(v, cause, user, count-1, delay, payload, pos)
        end
    end
end

function pmb_node_update.update_node_propagate(pos, cause, user, count, delay, payload, last_pos)
    if not delay then delay = 0.1 end
    -- only allow a certain limit on total updates per server step
    if calls > call_limit then
        return false end

    -- only allow 15 recursions per update
    if count <= 0 then return end

    if not last_pos then
        pmb_node_update.update_node(pos, cause, user, count-1, delay, payload, pos)
    end
    if delay == 0 then
        propagate(pos, cause, user, count, delay, payload, last_pos)
    else
        minetest.after(delay, propagate, pos, cause, user, count, delay, payload, last_pos)
    end
end

function pmb_node_update.update_node(pos, cause, user, count, delay, payload, last_pos)
    if count <= 0 then return false end

    local node = minetest.registered_nodes[(minetest.get_node(pos).name)]

    if node then
        local updated = false
        if node._on_node_update then
            calls = calls + 1
            -- allow the payload to propogate
            payload = node._on_node_update(pos, cause, user, count-1, payload, last_pos)
            if payload ~= false and payload ~= nil then
                updated = true
            end
        end
        -- go through the registered update funcs and if any of them return true, propogate the update
        for _, node_func in ipairs(pmb_node_update.update_functions) do
            if node_func(pos, cause, user, count, delay, payload, last_pos) then
                updated = true
            end
        end

        if updated then
            pmb_node_update.update_node_propagate(pos, cause, user, count, delay, payload, last_pos)
            return true
        end
    end
end



minetest.register_on_dignode(
    function(pos, oldnode, digger)
        pmb_node_update.update_node_propagate(pos, "dig", digger, 15)
    end
)
minetest.register_on_placenode(
    function(pos, oldnode, digger)
        pmb_node_update.update_node_propagate(pos, "place", digger, 15)
    end
)
minetest.register_on_punchnode(
    function(pos, node, puncher, pointed_thing)
        pmb_node_update.update_node(pos, "punch", puncher, 15)
    end
)

minetest.register_on_liquid_transformed(function(pos_list, node_list)
    -- local time = os.clock()
    for i, pos in ipairs(pos_list) do repeat
        local prev_ndef = minetest.registered_nodes[node_list[i].name]
        if prev_ndef and prev_ndef._liquid_type then
            break end
        local node = minetest.get_node(pos)
        local def = minetest.registered_nodes[node.name]
        if not def then break end

        if def._liquid_type ~= nil then
            pmb_node_update.update_node_propagate(pos, "liquid", nil, 2, 0, nil, nil)
        end
    until true end
    -- minetest.log(dump((os.clock() - time) * 100))
end)

local core_set_node = minetest.set_node
minetest.set_node = function(pos, node, update)
    core_set_node(pos, node)
    if not update then return end
    pmb_node_update.update_node_propagate(pos, "place", nil, 15)
end

