
local _t = 0
function exord_core.set_mob_spawning_time(time)
    _t = time
end

minetest.register_globalstep(function(dtime)
    if _t > 0 then _t = _t - dtime; return
    else
        _t = _t + exord_core.mobs_spawn_interval * 0.5 + 0.5 * math.random() * exord_core.mobs_spawn_interval
    end

    if not exord_core.tags.spawning then return end

    local amount = exord_core.mobs_max
    local count = 0
    -- local gen_min, gen_max = minetest.get_mapgen_edges()
    for i, object in ipairs(minetest.get_objects_in_area(exord_mg_custom.minp*2, exord_mg_custom.maxp*2)) do
        local ent = object and object:get_luaentity()
        if ent and ent._mobcap then
            count = count + 1
        end
    end
    amount = amount - count
    if amount <= 0 then return end

    exord_core.spawn_mobs(amount)
end)

function exord_core.spawn_mobs(amount)
    local fplayers = exord_player.get_alive_fake_players()
    local iter = 0
    while amount > 0 and iter < 100 do
        iter = iter + 1
        local fcount = #fplayers
        local rk = math.random(0, fcount-1)
        for k = 1, #fplayers do repeat
            local fplayer = fplayers[(k + rk - 1) % fcount + 1]
            if amount <= 0 then break end
            local pos = fplayer.object:get_pos()
            local player = fplayer._player
            if (not player) or (not pos) then break end

            local spawn_pos
            for a = 1, 30 do
                local yaw = math.random() * math.pi * 2
                local dir = minetest.yaw_to_dir(yaw)
                local dist = math.random() * (exord_core.mobs_spawn_dist_max - exord_core.mobs_spawn_dist_min)
                dist = dist + exord_core.mobs_spawn_dist_min
                spawn_pos = pos + dir * dist
                local node = minetest.get_node_or_nil(spawn_pos)
                if node and minetest.get_item_group(node.name, "traversible_extra_cost") <= 0 then
                    break
                else
                    spawn_pos = nil
                end
            end

            if not spawn_pos then break end

            for i = 1, math.random(4, 20) do
                if amount <= 0 then break end
                amount = amount - 1
                local op = vector.new(
                    (math.random()*2-1)*5,
                    0,
                    (math.random()*2-1)*5
                ) + spawn_pos
                op.y = 1.51
                local below = minetest.get_node(vector.offset(op, 0, -1, 0))
                if minetest.get_item_group(below.name, "traversible_floor_extra_cost") == 0
                and minetest.get_item_group(below.name, "game_area") > 0 then
                    minetest.add_entity(op, "exord_swarm:worker")
                end
            end
        until true end
    end
end
