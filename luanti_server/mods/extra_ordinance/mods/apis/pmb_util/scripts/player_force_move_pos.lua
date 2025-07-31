
if not minetest.get_modpath("playerphysics") then return end

local pl = {}
local function start_move(player, flags)
    playerphysics.add_physics_factor(player, "speed", "pmb_util:forcemoveplayer", 0)
    playerphysics.add_physics_factor(player, "gravity", "pmb_util:forcemoveplayer", 0)
end
local function end_move(player)
    playerphysics.remove_physics_factor(player, "speed", "pmb_util:forcemoveplayer")
    playerphysics.remove_physics_factor(player, "gravity", "pmb_util:forcemoveplayer")
    player:set_properties({
        stepheight = (pl[player] and pl[player].stepheight) or nil,
        collisionbox = (pl[player] and pl[player].collisionbox) or nil,
    })
end

function pmb_util.player_force_move_to_pos(player, pos, flags, callback)
    end_move(player)
    local props = player:get_properties()
    pl[player] = {
        target = pos,
        callback = callback,
        waittime = 0.3,
        timeout = 5,
        flags = flags or {},
        collisionbox = props.collisionbox,
        stepheight = props.stepheight,
    }
    start_move(player, flags)
end

minetest.register_globalstep(function(dtime)
    for player, info in pairs(pl) do repeat
        if info.waittime > 0 then
            info.waittime = info.waittime - dtime
            break
        end
        local pos = player:get_pos()
        local dist = vector.distance(pos, info.target)
        local dir = vector.direction(pos, info.target)
        local vel = player:get_velocity()

        local factor = 1 - math.max(0.0, math.min(1, vector.length(vel)/6))^2
        factor = factor * math.max(0.0, math.min(1, dist))^2
        local normdtime = 1 * (1 - math.max(0.0, math.min(0.98, dtime)))
        factor = factor * normdtime
        factor = factor * (math.random()*0.5+0.5)
        local add = dir * 4 * -(factor+0.1)
        add = (add + vel) * -0.1 * normdtime
        player:add_velocity(add)
        -- force it every frame since other things might override it again
        if (not info.init) or (not info.flags.no_phase) then
            player:set_properties({
                stepheight = 0,
                collisionbox = {0,0,0,0,0,0},
            })
        end
        if (not info.init) and info.timeout > 0.5 then
            player:add_velocity(player:get_velocity() * -0.9)
            info.init = true
        end
        info.timeout = info.timeout - dtime
        if (dist < 0.1) or (info.timeout <= 0) then
            player:add_velocity(player:get_velocity() * -0.9)
            if info.callback and (info.callback(player) == true) then
            else
                end_move(player)
            end
            pl[player] = nil
            return
        end
    until true end
end)

minetest.register_on_joinplayer(function(player, last_login)
    end_move(player)
end)
