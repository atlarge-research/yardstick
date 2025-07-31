
exord_player.playing_list = {}
exord_player.queue = {}

exord_player.cam_offset = vector.new(0,30,20)
exord_player.cam_rotation = true
exord_player.third_person = false
exord_player.fov_base = 40
exord_player.cam_follow_threshold = 0.1
exord_player.cam_rotation_mult = 40
exord_player.cam_follow_mult = 40
exord_player.starting_cam_rotation = 0.4
exord_player.admin = nil
exord_player.max_hp = 10
exord_player.min_respawn_time = 3
exord_player.spawn_radius_min = 14

local UP = vector.new(0,1,0)

function exord_player.get_fplayer_or_nil(player)
    if not minetest.is_player(player) then return end
    local pi = exord_player.check_player(player)
    if pi.ent and not pi.ent.object:get_pos() then
        pi.ent = nil
        return
    end
    return pi.ent or nil
end

function exord_player.get_alive_fplayer_or_nil(player)
    if not minetest.is_player(player) then return end
    local pi = exord_player.check_player(player)
    if pi.ent and not pi.ent.object:get_pos() then
        pi.ent = nil
        return
    end
    if not pi.ent then return nil end
    return (pi.ent._hp > 0) and pi.ent or nil
end

function exord_player.get_eyepos(player)
    local eyepos = player:get_pos() + (player:get_eye_offset()*0.1):rotate_around_axis(UP, player:get_look_horizontal())
    eyepos.y = eyepos.y + player:get_properties().eye_height
    return eyepos
end local get_eyepos = exord_player.get_eyepos

-- if something is (1, 0, 6) away from the fplayer and player is at (2, 0, 1) then return (3, 0, 7)
-- otherwise return player pos plus some of the direction
function exord_player.get_relative_pos_to_fplayer(player, pos, factor)
    if not minetest.is_player(player) then return pos end
    local pi = exord_player.check_player(player)
    local ppos = exord_player.get_eyepos(player)
    local fpos = pi.ent and pi.ent.object:get_pos()
    if not fpos then return ppos + vector.direction(ppos, pos) end
    return ppos + (pos - fpos) * (factor or 1)
end

exord_player.pl = {}
local pl = exord_player.pl
function exord_player.check_player(player)
    local pi = pl[player]
    if not pi then
        pi = {
            hp = 3,
            ent = nil,
            ready = false,
            respawn_time = 0,
            camera_zoom = 1,
            last_ctrl = {},
        }
        pl[player] = pi
    end
    return pl[player]
end

function exord_player.is_fake_player(ent)
    return ent and (ent._fake_player == true)
end

function exord_player.is_alive_fake_player(ent)
    return ent and (ent._fake_player == true) and (ent._hp > 0)
end

function exord_player.is_object_fake_player(obj)
    local ent = obj and obj.get_luaentity and obj:get_luaentity()
    return ent and (ent._fake_player == true)
end

function exord_player.remove_from_playing(i)
    exord_player.playing_list[i] = exord_player.playing_list[#exord_player.playing_list]
    table.remove(exord_player.playing_list, #exord_player.playing_list)
end

function exord_player.die_fplayer(fplayer)
    local i = table.indexof(exord_player.playing_list, fplayer)
    if i and i > 0 then
        exord_player.remove_from_playing(i)
    end
end

function exord_player.unready_all_players()
    for i, player in ipairs(minetest.get_connected_players()) do
        exord_player.set_ready(player, false)
    end
end

function exord_player.get_ready_players()
    local list = {}
    for i, player in ipairs(minetest.get_connected_players()) do
        local pi = exord_player.check_player(player)
        if pi.ready or exord_player.admin == player then
            table.insert(list, player)
        end
    end
    return list
end

function exord_player.get_non_spectator_players()
    local list = {}
    for i, player in ipairs(minetest.get_connected_players()) do
        local pi = exord_player.check_player(player)
        if not pi.spectator then
            table.insert(list, player)
        end
    end
    return list
end

function exord_player.set_ready(player, ready)
    local pi = exord_player.check_player(player)
    if (pi.ready==true) == ready then
        return
    end

    if ready then
        pi.ready = true
        SIGNAL("on_player_ready", player)
    else
        pi.ready = false
        SIGNAL("on_player_unready", player)
    end
end

function exord_player.get_new_admin()
    local pool = exord_player.get_ready_players()
    if #pool == 0 then
        pool = minetest.get_connected_players()
    end
    local ri = math.random(1, #pool)
    if not pool[ri] then return end
    exord_player.admin = pool[ri]
    SIGNAL("on_new_player_admin", exord_player.admin)
    return exord_player.admin
end

minetest.register_on_leaveplayer(function(player, timed_out)
    exord_player.set_ready(player, false)
    if exord_player.admin == player then
        exord_player.get_new_admin()
    end
end)

function exord_player.debug_particle(pos, color, time, vel, size)
    -- do return end
    minetest.add_particle({
        size = size or 2, pos = pos,
        texture = "blank.png^[noalpha^[colorize:"..(color or "#fff")..":255",
        velocity = vel or vector.new(0, 0, 0),expirationtime = time, glow = 14,
    })
end

function exord_player.clamp(a,min,max)
    return math.min(math.max(a, min),max)
end

function exord_player.dist2(v, b)
    return (
        (v.x - b.x)^2 + (v.y - b.y)^2 + (v.z - b.z)^2
    )
end

function exord_player.update_hud(player, pi)
    if not pi then pi = exord_player.check_player(player) end
    if not pi.has_fplayer then
        pmb_hud.change_hud(player, "exord_player:hp", {
            text = "[fill:1x1:0,0:#00000000",
        })
        pmb_hud.change_hud(player, "exord_player:hp_bg", {
            text = "[fill:1x1:0,0:#00000000",
        })
        return
    end
    local w = 300
    local h = 10
    local m = 1
    local hf = (pi.ent._hp or 0) / (pi.max_hp or exord_player.max_hp)
    local color = (
        (hf < 0.2) and "#ff1f45" or
        (hf < 0.5) and "#d9af76" or
        "#a1c256"
    )
    if pmb_hud.has_hud(player, "exord_player:hp") then
        pmb_hud.change_hud(player, "exord_player:hp", {
            text = "[fill:1x1:0,0:"..color,
            scale = {x = w * hf, y = h},
        })
        pmb_hud.change_hud(player, "exord_player:hp_bg", {
            text = "[fill:1x1:0,0:#2f2029",
        })
    else
        pmb_hud.add_hud(player, "exord_player:hp", {
            type = "image",
            text = "[fill:1x1:0,0:"..color,
            position = {x=0.5, y=1},
            alignment = {x=0, y=0},
            z_index = 1999,
            scale = {x = w, y = h},
            offset = {x = 0, y = -70+2},
        })
        pmb_hud.add_hud(player, "exord_player:hp_bg", {
            type = "image",
            text = "[fill:1x1:0,0:#2f2029",
            position = {x=0.5, y=1},
            alignment = {x=0, y=0},
            z_index = 1996,
            scale = {x = w, y = h+m*2},
            offset = {x = -0, y = -70+2},
        })
    end
end

LISTEN("on_fplayer_destroyed", function(fplayer, player)
    if not minetest.is_player(player) then return end
    local pi = exord_player.check_player(player)
    pi.respawn_time = exord_player.min_respawn_time
end)

function exord_player.get_player_pointed_thing(player)
    if not minetest.is_player(player) then return end
    local pi = exord_player.check_player(player)
    local pos = get_eyepos(player)
    local dir = player:get_look_dir()
    local ray = minetest.raycast(pos, pos + dir * 300, false, false)
    for pointed_thing in ray do
        if pointed_thing.type == "node" and pointed_thing.under.y == 1 then
            pi.last_pointed_thing = pointed_thing
            return pointed_thing
        end
    end
end

function exord_player.on_fplayer_step(player, fplayer, dtime)
    local pi = exord_player.check_player(player)

    pi._dodge_time = (pi._dodge_time or 0) + dtime

    local pointed_thing = exord_player.get_player_pointed_thing(player)
    if not pointed_thing then return end

    local ctrl = player:get_player_control()

    if ctrl.jump and (pi._dodge_time > 2) then
        exord_core.loadout_use(player, 5, pointed_thing)
    end

    if ctrl.sneak then
        exord_core.loadout_use(player, 1, pointed_thing)
    end

end

function exord_player.get_spawn_pos()
    local yaw = math.random()*math.pi*2
    local dir = minetest.yaw_to_dir(yaw)
    dir = dir * exord_player.spawn_radius_min
    dir.y = 1.51
    return dir
end

minetest.register_globalstep(function(dtime)
    for i, player in ipairs(minetest.get_connected_players()) do
        local pi = exord_player.check_player(player)
        local ctrl = player:get_player_control()
        pi.respawn_time = pi.respawn_time - dtime

        player:set_fov(exord_player.fov_base, false, 0)

        local look_vert = player:get_look_vertical()
        pi.last_look_vert = (pi.last_look_vert or look_vert) * 0.9 + look_vert * 0.1
        if look_vert < -0.1 then
            pi.last_look_vert = pi.last_look_vert
            player:set_look_vertical(look_vert * 0.9)
        end

        local fplayer = pi.ent
        pi.has_fplayer = (fplayer and fplayer.object and fplayer.object:get_pos() ~= nil)
        if pi.has_fplayer then
            exord_player.on_fplayer_step(player, fplayer, dtime)
        elseif (not pi.no_queue) and (pi.respawn_time <= 0)
        and not exord_player.is_player_queued(player) then
            exord_player.queue_player(player)
            -- core.log("queued player")
        end
        if not pi.has_fplayer then
            local vel = player:get_velocity()
            player:add_velocity(vel*-0.02)
        end

        if ctrl.zoom and not pi.last_ctrl.zoom then
            pi.camera_zoom = (
                (pi.camera_zoom == 1) and 0.7 or 1
            )
        end

        exord_player.update_hud(player, pi)
        pi.last_ctrl = ctrl

        if not ISDEBUG then
            --
        elseif pmb_hud.has_hud(player, "dtime") then
            pmb_hud.change_hud(player, "dtime", {scale = {x=5, y=500 * dtime}})
        else
            pmb_hud.add_hud(player, "dtime", {
                type = "image",
                text = "[fill:1x1:0,0:#fff",
                position = {x=0.01, y=0.8},
                alignment = {x=1, y=-1},
                z_index = 807,
                scale = {x=8, y=500 * dtime},
            })
            pmb_hud.add_hud(player, "dtimebg", {
                type = "image",
                text = "[fill:1x1:0,0:#111",
                position = {x=0.01, y=0.8},
                alignment = {x=1, y=-1},
                z_index = 806,
                scale = {x=8, y=500},
            })
        end

        local ppos = player:get_pos()
        local o_f, o_t, o_r = player:get_eye_offset()
        local offset = (o_t * 0.1)
        offset = offset:rotate_around_axis(UP, player:get_look_horizontal())
        ppos = ppos + offset - player:get_look_dir()*2.1
        minetest.add_particle({
            pos = ppos,
            texture = "exord_obnoxious_warning_thirdperson.jpg",
            size = 3,
            expirationtime = dtime+0.01,
            glow = 14,
            to_player = player:get_player_name(),
        })
        minetest.add_particle({
            pos = ppos - player:get_look_dir()*8,
            texture = "exord_obnoxious_warning_thirdperson.jpg^[transformFX",
            size = 40,
            expirationtime = dtime+0.01,
            glow = 14,
            to_player = player:get_player_name(),
        })
        player:hud_set_hotbar_itemcount(5)
        player:hud_set_hotbar_selected_image("exord_inv_hotbar_select.png")
        player:hud_set_hotbar_image("[fill:42x42:0,0:#00000080")
    end

    -- core.emerge_area(vector.offset(exord_mg_custom.minp, 0, -10, 0), vector.offset(exord_mg_custom.maxp, 0, 10, 0))
    core.load_area(vector.offset(exord_mg_custom.minp, 0, -10, 0), vector.offset(exord_mg_custom.maxp, 0, 10, 0))
end)

function exord_player.get_alive_fake_players(copy)
    if copy then
        return table.copy(exord_player.playing_list)
    end
    return exord_player.playing_list
end

function exord_player.is_player_queued(player)
    return exord_player.queue[player] ~= nil
end

function exord_player.queue_player(player, pos)
    pos = pos or exord_player.get_spawn_pos()
    local pi = exord_player.check_player(player)
    pi.queued = true
    pi.ent = nil
    exord_player.queue[player] = pos
end

function exord_player.try_spawn_all_players(offset)
    for player, pos in pairs(exord_player.queue) do
        if offset then pos = pos + offset end
        exord_player.spawn_fake_player(player, pos)
    end
end

function exord_player.force_reset_camera(player, offset)
    if exord_player.third_person then
        player:set_look_vertical(0.7)
    else
        player:set_look_vertical(0.7)
    end
	player:set_look_horizontal(exord_player.starting_cam_rotation)
    local topos = (offset or vector.zero()) + vector.rotate_around_axis(exord_player.cam_offset, UP, exord_player.starting_cam_rotation + math.pi)
	player:set_pos(topos)
end

function exord_player.set_third_person(player)
    player:set_eye_offset(vector.new(0,0,5)*-10, vector.new(0,15,5), vector.new(0,15,5))
    exord_player.cam_offset = vector.new(0,7,0)
    exord_player.cam_rotation = true
    exord_player.fov_base = 70
    exord_player.cam_follow_threshold = 1
    exord_player.cam_rotate_threshold = 0.05
    exord_player.cam_rotation_mult = 40
    player:set_sky({
        fog = {
            fog_distance = 50,
            fog_start = 0.6,
            fog_color = "#100006",
        },
    })
end

function exord_player.set_top_down(player)
    player:set_eye_offset(vector.new(0,0,0), vector.new(0,15,-95), vector.new(0,15,95))
    exord_player.cam_offset = vector.new(0,20,20)
    exord_player.cam_rotation = true
    exord_player.fov_base = 50
    exord_player.cam_follow_threshold = 1
    exord_player.cam_rotate_threshold = 0.05
    exord_player.cam_rotation_mult = 40
    player:set_sky({
        fog = {
            fog_distance = 100,
            fog_start = 0.5,
            fog_color = "#0a0009",
        },
        type = "plain",
        base_color = "#0a0009",
    })
end

minetest.register_on_joinplayer(function(player, last_login)
    player:set_lighting({
        saturation = 1,
        shadows = {
            intensity = 0.4,
            tint = {r=60, g=0, b=10},
        },
        bloom = {
            intensity = 0.05,
            strength_factor = 1.0,
            radius = 1.0,
        },
        exposure = {
            luminance_min = -3.0,
            luminance_max = -3.0,
            exposure_correction = 0.9,
            speed_dark_bright = 1000,
            speed_bright_dark = 1000,
            center_weight_power = 1,
        },
    })
    player:set_physics_override({
        jump = 0,
    })
    -- player:override_day_night_ratio(0.3)
    player:set_sun({
        visible = true,
        texture = "blank.png"
    })
    player:set_sky({
        fog = {
            fog_distance = 100,
            fog_start = 0.5,
            fog_color = "#000000",
        },
    })
    exord_player.force_reset_camera(player)

    local pos = vector.new(0,1.51,0)
    exord_player.queue_player(player)

	playerphysics.add_physics_factor(player, "gravity", ":temp", 0)
    player:set_properties({
        eye_height = 0,
        textures = {"blank.png"},
        physical = false,
        collisionbox = {0,0,0,0,0,0},
        nametag = " ",
        nametag_color = "#00000000",
        nametag_bgcolor = "#00000000",
    })
    if exord_player.third_person then
        exord_player.set_third_person(player)
    else
        exord_player.set_top_down(player)
    end

    pmb_hud.add_hud(player, "exord_player:background", {
        type = "image",
        text = "[fill:1x1:0,0:#2f2c2880",
        position = {x=0, y=1},
        alignment = {x=1, y=1},
        z_index = -200,
        scale = {x=-100, y=200},
        offset = {x = 0, y = -40},
    })
    minetest.forceload_block(pos, false, 999)
end)

minetest.register_globalstep(function(dtime)
    -- prune destroyed fake players
    for i, fplayer in ipairs(exord_player.playing_list) do
        if (not fplayer) or fplayer.object:get_pos() == nil then
            -- clear destroyed ones
            exord_player.remove_from_playing(i)
        end
    end
end)

pmb_wield.on_move.add_equipment_list("main")


LISTEN("on_fplayer_landed", function(fplayer, player)
    if not minetest.is_player(player) then return end
    local pi = exord_player.check_player(player)
    if pi.tutorial_text_shown then return end
    pi.tutorial_text_shown = true
    pmb_hud.add_hud(player, "exord_player:info_tutorial", {
        type = "text",
        text = minetest.colorize("#fe9", "open the inventory for controls and loadout selection"),
        position = {x=0.5, y=0.6},
        alignment = {x=0, y=0},
        z_index = 805,
        size = {x=2, y=0},
        offset = {x=0, y=0}
    })
end)

LISTEN("on_fplayer_give_control", function(fplayer, player)
    minetest.after(3, function()
        if not minetest.is_player(player) then return end
        pmb_hud.remove_hud(player, "exord_player:info_tutorial")
    end)
end)
