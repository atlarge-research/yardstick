
if not minetest.get_modpath("playerphysics") then return end

local pl = {}
local function start_move(player)
    playerphysics.add_physics_factor(player, "speed", "pmb_util:forcemoveplayer", 0)
    playerphysics.add_physics_factor(player, "gravity", "pmb_util:forcemoveplayer", 0)
end
local function end_move(player)
    playerphysics.remove_physics_factor(player, "speed", "pmb_util:forcemoveplayer")
    playerphysics.remove_physics_factor(player, "gravity", "pmb_util:forcemoveplayer")
end

function pmb_util.player_force_set_velocity(player, vel, callback)
    local props = player:get_properties()
    pl[player] = {
        target = vel,
        callback = callback,
        timeout = 3,
    }
    start_move(player)
end

minetest.register_globalstep(function(dtime)
    for player, info in pairs(pl) do
        local vel = player:get_velocity()
        local dist = vector.distance(vel, info.target)
        local dir = vector.direction(vel, info.target)
        local add = dir * dist * (math.random()*0.1) / math.min(0.9, math.max(0.2, dtime))
        player:add_velocity(add)
        if dist < 0.1 then
            if info.callback and (info.callback(player) == true) then
            else
                end_move(player)
            end
            pl[player] = nil
            return
        end
    end
end)

minetest.register_on_joinplayer(function(player, last_login)
    end_move(player)
end)
