
local UP = vector.new(0,1,0)
function exord_guns.get_eyepos(player)
    local eyepos = player:get_pos() + (player:get_eye_offset()*0.1):rotate_around_axis(UP, player:get_look_horizontal())
    eyepos.y = eyepos.y + player:get_properties().eye_height
    return eyepos
end

function exord_guns.vec3_randrange(s, e)
    return vector.new(
        math.random() * (e-s) + s,
        math.random() * (e-s) + s,
        math.random() * (e-s) + s
    )
end

function exord_guns.dist2(p1, p2)
    return (p1.x - p2.x)^2 + (p1.z - p2.z)^2 + (p1.y - p2.y)^2
end

exord_guns._pl = {}
local pl = exord_guns._pl

function exord_guns.check_player(player)
    local pi = pl[player]
    if not pi then
        pi = {
            t_is_firing = {},
        }
        pl[player] = pi
    end
    return pi
end

function exord_guns.log_sound(player, id)
    local pi = exord_guns.check_player(player)
    if not pi.sounds then pi.sounds = {} end
    table.insert(pi.sounds, id)
end

function exord_guns.stop_all_sounds_for_player(player, fade)
    local pi = exord_guns.check_player(player)
    for i = #(pi.sounds or {}), 1, -1 do
        local id = pi.sounds[i]
        if fade then
            minetest.sound_fade(id, fade, 0)
        else
            minetest.sound_stop(id)
        end
        table.remove(pi.sounds, i)
    end
end

LISTEN("on_fplayer_killed", function(fplayer, player)
    exord_guns.stop_all_sounds_for_player(player, 50)
end)

LISTEN("on_fplayer_destroyed", function(fplayer, player)
    exord_guns.stop_all_sounds_for_player(player, 50)
end)

function exord_guns.play_looped(itemstack, player, pi)
    local idef = itemstack:get_definition()
    if not idef._sound_firing_loop then return end
    if not pi.looping_sounds then pi.looping_sounds = {} end
    local name = itemstack:get_name()
    if pi.looping_sounds[name] then return end
    local sdef = table.copy(idef._sound_firing_loop)
    sdef.object = (exord_player.get_alive_fplayer_or_nil(player) or {}).object
    if not sdef.object then return end
    pi.looping_sounds[name] = minetest.sound_play(sdef.name, sdef)
    return true
end

function exord_guns.stop_looped(itemstack, player, pi)
    local idef = itemstack:get_definition()
    if not idef._sound_firing_loop then return end
    if not pi.looping_sounds then pi.looping_sounds = {} end
    local name = itemstack:get_name()
    if not pi.looping_sounds[name] then return end
    local sdef = idef._sound_firing_loop
    minetest.sound_fade(pi.looping_sounds[name], sdef.fade_out or 4, 0)
    pi.looping_sounds[name] = nil
    return true
end

function exord_guns.on_trigger_pull(itemstack, player, pointed_thing, flag)
    flag = flag or {}
    local pi = exord_guns.check_player(player)

    local ppi = exord_player.check_player(player)
    local fplayer = exord_player.get_alive_fplayer_or_nil(player)
    if not fplayer then return end
    local fpos = fplayer and fplayer.object:get_pos()
    if not fpos then return end
    fpos.y = 2

    local idef = itemstack:get_definition()
    local meta = itemstack:get_meta()

    if not exord_core.cooldown.can_use(itemstack) then
        meta:set_string("chambered", tostring(0))
        return itemstack
    end

    local rounds = idef._infinite_ammo and 9999 or meta:get_int("rounds") or idef._mag_capacity

    if (rounds < 1) or not exord_core.cooldown.can_use(itemstack) then
        local sdef = idef._sound_empty
        if sdef then
            minetest.sound_play(sdef.name, {
                gain = sdef.gain or 1,
                max_hear_distance = sdef.max_hear_distance or 20,
                sdef.pitch or 1,
                to_player = player:get_player_name(),
            }, true)
        end
        if idef._auto_reload then
            itemstack = exord_guns.start_reload(itemstack, player) or itemstack
        end

        return itemstack
    end

    exord_guns.on_start_firing(itemstack, player, idef, pi)

    local chambered = tonumber(meta:get_string("chambered")) or 0
    if chambered < 1 then return end
    chambered = chambered - 1

    local is_shot = false

    local tpos = flag.pos or (exord_player.get_player_pointed_thing(player) or {}).intersection_point
    if not tpos then return end

    if fplayer._get_barrel_position then
        local barrelindex = idef._proj_barrel_index or 1
        fpos = fplayer:_get_barrel_position(barrelindex) or fpos
    end

    local callb_result = idef._proj_on_prefire and idef._proj_on_prefire(itemstack, player, fpos, tpos)
    if callb_result then
        if type(callb_result) ~= "boolean" then
            itemstack = callb_result
            meta = itemstack:get_meta()
        end
        is_shot = true
    end

    if not is_shot then
        for i = 1, (idef._proj_number_per_round or 1) do
            is_shot = exord_guns.on_fire_round(ItemStack(itemstack), player, fpos, tpos, pi, idef)
        end
    end

    if not is_shot then
        return
    end

    rounds = rounds - 1
    meta:set_int("rounds", rounds)
    meta:set_string("chambered", tostring(chambered))

    if idef._sound_fire then
        minetest.sound_play(idef._sound_fire.name, {
            pos = fpos,
            gain = idef._sound_fire.gain or 1,
            max_hear_distance = idef._sound_fire.max_hear_distance or 200,
            pitch = idef._sound_fire.pitch or 1,
            to_player_direct = player,
        }, true)
    end

    return itemstack
end

function exord_guns.on_fire_round(itemstack, player, fpos, tpos, pi, idef)
    pi = pi or exord_guns.check_player(player)
    idef = idef or itemstack:get_definition()
    local Y = 2 -- slice of world aimable

    -- pos = pos or exord_guns.get_eyepos(player)
    local u = exord_proj.projectile_proto.new(
        fpos,
        idef._proj_bullet_def or exord_guns.projectile_bullet
    )
    u.inaccuracy = idef._proj_inaccuracy or 1
    u.speed = idef._proj_speed or 100

    local point_pos = vector.copy(tpos)
    -- point_pos.y = Y
    -- exord_core.debug_particle(point_pos, "#f0f", 1, vector.new(0, 20, 0), 8)

    local vel = vector.direction(fpos, point_pos)

    vel.y = vel.y + (idef._proj_zeroing or 0)
    vel = vel * u.speed + exord_guns.vec3_randrange(-u.inaccuracy, u.inaccuracy)
    u:set_velocity(vel)
    u.parent = (exord_player.get_fplayer_or_nil(player) or {}).object
    u.idef = idef
    u.damage_nodes = idef._proj_damage_nodes or 1
    u.damage_players = idef._proj_damage_players or 1
    u.max_range = idef._proj_max_range or 100
    u.target_pos = point_pos
    u.start_pos = fpos
    u.tracer = idef._proj_tracer or 100
    u.penetrations_remaining = idef._proj_penetration or 0
    u.penetration_slow = idef._proj_penetration_slow
    u:set_acceleration(vector.new(0, idef._proj_gravity or 0, 0))

    if idef._proj_on_fire then
        idef._proj_on_fire(u, itemstack, player, point_pos)
    end
    return true
end


function exord_guns.init_stack(itemstack, player)
    local pi = exord_guns.check_player(player)
    pi.is_reloading = false
    local idef = itemstack:get_definition()
    local meta = itemstack:get_meta()
    meta:set_int("rounds", idef._mag_capacity or 1)
end

function exord_guns.start_reload(itemstack, player)
    local pi = exord_guns.check_player(player)
    if pi.is_reloading then return end
    local idef = itemstack:get_definition()
    local meta = itemstack:get_meta()

    if meta:get_int("rounds") == idef._mag_capacity then
        return
    end

    if exord_core.cooldown.can_use(itemstack) then
        itemstack = exord_core.cooldown.cooldown_start(itemstack, player) or itemstack
        meta = itemstack:get_meta()
    else
        return
    end
    meta:set_string("chambered", tostring(0))
    meta:set_int("rounds", 0)
    if idef._sound_reload_start then
        exord_guns.log_sound(player, minetest.sound_play(idef._sound_reload_start.name, {
            gain = idef._sound_reload_start.gain or 1,
            max_hear_distance = idef._sound_reload_start.max_hear_distance or 200,
            pitch = idef._sound_reload_start.pitch or 1,
            to_player = player:get_player_name(),
        }))
    end
    return itemstack
end

function exord_guns.end_reload(itemstack, player)
    local pi = exord_guns.check_player(player)
    local idef = itemstack:get_definition()
    local meta = itemstack:get_meta()

    pi.is_reloading = false
    meta:set_string("chambered", tostring(0))
    meta:set_int("rounds", idef._mag_capacity or 1)

    if idef._sound_reload_end then
        minetest.sound_play(idef._sound_reload_end.name, {
            gain = idef._sound_reload_end.gain or 1,
            max_hear_distance = idef._sound_reload_end.max_hear_distance or 200,
            pitch = idef._sound_reload_end.pitch or 1,
            to_player = player:get_player_name(),
        }, true)
    end
    exord_guns.update_hud(player)
end

function exord_guns.check_firing(itemstack, player, pi)
    pi = pi or exord_guns.check_player(player)
    local name = itemstack:get_name()
    if not pi.t_is_firing then pi.t_is_firing = {} end
    if pi.t_is_firing[name] == nil then
        pi.t_is_firing[name] = 0
    end
end
-- -1 = started stopping firing, 0 = stopped, 1 = started firing, 2 = firing
function exord_guns.on_start_firing(itemstack, player, idef, pi)
    pi = pi or exord_guns.check_player(player)
    idef = idef or itemstack:get_definition()
    local name = itemstack:get_name()
    if pi.t_is_firing[name] == 2 then return end
    if pi.t_is_firing[name] == -1 or pi.t_is_firing[name] == 1 then
        pi.t_is_firing[name] = 2
        return
    elseif pi.t_is_firing[name] == 0 then
        pi.t_is_firing[name] = 1
        -- DO THE START CODE
    end

    if idef._on_started_firing then
        local ret = idef._on_started_firing(itemstack, player, pi)
        if ret and not ret:equals(itemstack) then
            itemstack = ret
        end
    end
    local sound_loop_started = exord_guns.play_looped(itemstack, player, pi)
    if sound_loop_started and idef._sound_firing_loop_start then
        local sdef = table.copy(idef._sound_firing_loop_start)
        sdef.object = (exord_player.get_fplayer_or_nil(player) or {}).object
        minetest.sound_play(sdef.name, sdef)
    end
    return itemstack
end

function exord_guns.on_stop_firing(itemstack, player, idef, pi)
    pi = pi or exord_guns.check_player(player)
    idef = idef or itemstack:get_definition()
    if idef._on_stopped_firing then
        local ret = idef._on_stopped_firing(itemstack, player, pi)
        if ret and not ret:equals(itemstack) then
            itemstack = ret
        end
    end
    exord_guns.stop_looped(itemstack, player, pi)
    if idef._sound_firing_loop_end then
        local sdef = table.copy(idef._sound_firing_loop_end)
        sdef.object = (exord_player.get_fplayer_or_nil(player) or {}).object
        minetest.sound_play(sdef.name, sdef)
    end
    return itemstack
end

function exord_guns.get_crosshair_mag_GUI(rounds, max)
    if max == 0 then return "blank.png" end
    local tex = {}
    local segs = math.min(12, math.ceil((rounds / max) * 12))
    if segs <= 0 then return "blank.png" end
    for i = 0, segs-1 do
        table.insert(tex, (i>0 and "^" or "(") .. "crosshair_"..i..".png")
    end
    table.insert(tex, ")^[opacity:50")
    return table.concat(tex)
end

function exord_guns.update_hud(player)
    local itemstack = player:get_wielded_item()
    local idef = itemstack:get_definition()
    if (not idef) or (not idef._guns_hud) then
        if pmb_hud.has_hud(player, "exord_guns:magazine") then
            pmb_hud.remove_hud(player, "exord_guns:magazine")
            pmb_hud.remove_hud(player, "exord_guns:magazine2")
            pmb_hud.remove_hud(player, "exord_guns:crosshair_mag")
            pmb_hud.remove_hud(player, "exord_guns:name")
        end
        return
    end
    local max = idef._infinite_ammo and 999 or idef._mag_capacity or 1
    local rounds = idef._infinite_ammo and 999 or itemstack:get_meta():get_int("rounds") or idef._mag_capacity or 1
    if not pmb_hud.has_hud(player, "exord_guns:magazine") then
        pmb_hud.add_hud(player, "exord_guns:magazine", {
            type = "text",
            text = minetest.colorize("#ff5", idef._infinite_ammo and "∞" or rounds),
            position = {x=1, y=1},
            alignment = {x=-1, y=-1},
            z_index = 1999,
            size = {x=4, y=0},
            offset = {x = -100, y = -16},
        })
        pmb_hud.add_hud(player, "exord_guns:magazine2", {
            type = "text",
            text = minetest.colorize("#f65", idef._infinite_ammo and "" or max),
            position = {x=1, y=1},
            alignment = {x=1, y=-1},
            z_index = 1999,
            size = {x=2, y=0},
            offset = {x = -90, y = -24},
        })
        pmb_hud.add_hud(player, "exord_guns:name", {
            type = "text",
            text = minetest.colorize("#37f", idef._exord_guns_name or idef.description),
            position = {x=0.75, y=1},
            alignment = {x=-1, y=-1},
            z_index = 1999,
            size = {x=2, y=0},
            offset = {x = 200, y = -4},
        })
        pmb_hud.add_hud(player, "exord_guns:crosshair_mag", {
            type = "image",
            text = exord_guns.get_crosshair_mag_GUI(rounds, max),
            position = {x=0.5, y=0.5},
            alignment = {x=0.0, y=0.0},
            z_index = 1999,
            scale = {x = 0.2, y = 0.2},
            offset = {x = -1, y = -2},
        })
    else
        pmb_hud.change_hud(player, "exord_guns:magazine", {
            text = minetest.colorize("#ff5", idef._infinite_ammo and "∞" or rounds),
        })
        pmb_hud.change_hud(player, "exord_guns:magazine2", {
            text = minetest.colorize("#f65", idef._infinite_ammo and "" or max),
        })
        pmb_hud.change_hud(player, "exord_guns:name", {
            text = minetest.colorize("#b3a555", idef._exord_guns_name or idef.description),
        })
        pmb_hud.change_hud(player, "exord_guns:crosshair_mag", {
            text = exord_guns.get_crosshair_mag_GUI(rounds, max),
        })
    end
end

function exord_guns.on_step_manage_chambered(itemstack, player, dtime)
    local pi = exord_guns.check_player(player)
    local name = itemstack:get_name()
    local fplayer = exord_player.get_alive_fplayer_or_nil(player)
    if not fplayer then
        if exord_guns.stop_looped(itemstack, player, pi) and pi.t_is_firing[name] then
            exord_guns.check_firing(itemstack, player, pi)
            exord_guns.on_stop_firing(itemstack, player, itemstack:get_definition(), pi)
            pi.t_is_firing[name] = 0
        end
        return
    end
    local idef = itemstack:get_definition()
    if (not idef) or (not idef._fire_rpm) then return end
    local meta = itemstack:get_meta()
    -- when this item has never been used before
    if meta:get_string("init") == "" then
        meta:set_string("init", "1")
        itemstack = exord_guns.init_stack(itemstack, player) or itemstack
    end
    local rounds = meta:get_int("rounds") or idef._mag_capacity
    local chambered = tonumber(meta:get_string("chambered")) or 0
    if chambered > 1 then chambered = 1 end
    chambered = chambered + dtime * ((1 / 60) * idef._fire_rpm)
    chambered = math.min(chambered, rounds)
    meta:set_string("chambered", tostring(chambered))
    exord_guns.check_firing(itemstack, player, pi)
    -- -1 stopping, 0 stopped, 1 started 2 firing
    if pi.t_is_firing[name] == -1 then
        exord_guns.on_stop_firing(itemstack, player, idef, pi)
        pi.t_is_firing[name] = 0
    elseif pi.t_is_firing[name] ~= 0 then
        pi.t_is_firing[name] = -1
    end
    return itemstack
end

function exord_guns.on_step(itemstack, player, dtime)
    local pi = exord_guns.check_player(player)
    local fplayer = exord_player.get_alive_fplayer_or_nil(player)
    if not fplayer then return end
    exord_guns.check_firing(itemstack, player, pi)
    exord_guns.update_hud(player)
    local idef = itemstack:get_definition()
    local ctrl = player:get_player_control()
    local meta = itemstack:get_meta()
    -- switch stack if needed
    if (pi.last_stack == nil) or (pi.last_stack:get_name() ~= itemstack:get_name()) then
        meta:set_string("chambered", tostring(0))
        pi.last_stack = itemstack
    end

    if not exord_core.cooldown.can_use(itemstack) then return end

    meta = itemstack:get_meta()

    local rounds = meta:get_int("rounds") or idef._mag_capacity
    if idef._full_auto and ctrl.dig then
        exord_guns.on_start_firing(itemstack, player, idef, pi)
        for i = 1, 1000 do
            if (tonumber(itemstack:get_meta():get_string("chambered")) or 0) >= 1 then
                itemstack = exord_guns.on_trigger_pull(itemstack, player, nil) or itemstack
            else
                break
            end
        end
        if idef._auto_reload and rounds <= 0 then
            itemstack = exord_guns.start_reload(itemstack, player) or itemstack
        end
    end

    return itemstack
end

minetest.register_globalstep(function(dtime)
    for k, player in ipairs(minetest.get_connected_players()) do
        local inv = player:get_inventory()
        local lists = inv:get_lists()
        for listname, list in pairs(lists) do
            local changes = false
            for i, itemstack in ipairs(list) do
                -- minetest.log(tostring(itemstack))
                local new = exord_guns.on_step_manage_chambered(ItemStack(itemstack), player, dtime)
                if new then
                    list[i] = new
                    changes = true
                end
            end
            if changes then
                inv:set_list(listname, list)
            end
        end
        exord_guns.update_hud(player)
    end
end)
