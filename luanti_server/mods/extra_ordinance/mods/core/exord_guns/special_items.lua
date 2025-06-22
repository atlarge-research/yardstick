local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

local UP = vector.new(0,1,0)
local FORWARD = vector.new(0,0,1)

minetest.register_tool("exord_guns:dodge_wallbreak", {
    description = S("Dodge Wallbreak"),
    inventory_image = "exord_guns_dodge_wallbreak.png",
    wield_image = "blank.png",
    groups = {},
    on_use = function(itemstack, player, pointed_thing)
        if exord_core.cooldown.can_use(itemstack) then
            local ctrl = player:get_player_control()
            local movevel = vector.new(
                (ctrl.left and -1 or 0) + (ctrl.right and 1 or 0),
                0,
                (ctrl.down and -1 or 0) + (ctrl.up and 1 or 0)
            ):normalize()
            -- don't dodge if no movement
            if vector.length(movevel) <= 0.001 then return end
            movevel = vector.rotate_around_axis(movevel, UP, player:get_look_horizontal())
            local pi = exord_player.check_player(player)
            pi._dodge_dir = movevel
            pi._dodge_time = 0
            pi.ent.object:add_velocity(movevel * 30)
            return exord_core.cooldown.cooldown_start(itemstack, player)
        end
    end,
    on_step = function(itemstack, player, dtime)
    end,
    _cooldown = 3,
    -- _windup = 0,
    _on_cooldown_start = function(itemstack, player)
        -- minetest.log("cooldown")
        return itemstack
    end,
    _on_cooldown_complete = function(itemstack, player)
        -- minetest.log("ready")
        return itemstack
    end,
    _on_cooldown_step = function(itemstack, player, dtime)
        local pi = exord_player.check_player(player)
        if not pi._dodge_dir then return end
        if (pi._dodge_time or 0) > 0.3 then else
            local fplayer = exord_player.get_alive_fplayer_or_nil(player)
            if not fplayer then return end
            local front = fplayer.object:get_pos() + fplayer.object:get_velocity():normalize()*2
            local destroyed = exord_core.map.damage_radius(front, 1.9, 10, false, 0.6)
            if destroyed then
                exord_guns.do_digging_particles(front, nil)
            end
            fplayer.object:set_velocity(pi._dodge_dir * 30)
        end
        return itemstack
    end,
})


function exord_guns.do_shockwave(pos, radius, count, force, size, exp)
    force = force or 1
    radius = radius or 1
    count = count or 30
    size = size or 1
    exp = exp or 1
    local vel = force * 8
    minetest.add_particlespawner({
        amount = count,
        time = 0.000001,
        vertical = false,
        texpool = {
            {
                name = "explosion_anim.png^[hsl:170:100:100",
                animation = {
                    type = "vertical_frames",
                    aspect_w = 8, aspect_h = 8,
                    length = 2 * exp,
                }
            },
            {
                name = "explosion_anim.png^[hsl:180:0:0",
                animation = {
                    type = "vertical_frames",
                    aspect_w = 8, aspect_h = 8,
                    length = 2.3 * exp,
                }
            },
        },
        glow = 14,
        collisiondetection = true,
        attract = {
            kind = "point",
            strength = {
                min = -40,
                max = -40,
            },
            origin = vector.offset(pos, 0, 1, 0),
            die_on_contact = false,
        },
        radius = {
            min = 4,
            max = 4,
        },
        minpos = vector.offset(pos, -0, 2, -0),
        maxpos = vector.offset(pos,  0, 2,  0),
        -- minvel = vector.new( vel*-1,       0, vel*-1),
        -- maxvel = vector.new( vel* 1, vel*0.1, vel* 1),
        minacc = vector.new(0, -9000, 0),
        maxacc = vector.new(0, -9000, 0),
        drag = vector.new(10, 40, 10),
        minexptime = 1.5 * exp,
        maxexptime = 1.5 * exp,
        minsize = 4 * size,
        maxsize = 32 * size,
    })
end

minetest.register_tool("exord_guns:shockwave", {
    description = S("Shockwave"),
    _exord_guns_name = S("ACTIVE ARMOR"),
    inventory_image = "exord_guns_shockwave.png",
    wield_image = "blank.png",
    groups = {},
    on_use = function(itemstack, player, pointed_thing)
        if exord_core.cooldown.can_use(itemstack) then
            local fplayer = exord_player.get_alive_fplayer_or_nil(player)
            local pos = fplayer and fplayer.object:get_pos()
            if not pos then return end
            exord_core.map.damage_radius(pos, 8.5, 3, true, 1)
            exord_core.damage_radius(pos, 20, exord_core.NumSet.new({
                explosive = 8,
                burning = 4,
                shock = 4,
            }), fplayer, 2, 20)
            exord_guns.do_shockwave(pos, 0, 100, 6, 1, 1)
            minetest.sound_play("exord_guns_explosion_4", {
                gain = 1 * exord_core.sound_gain_multiplier,
                pitch = 1,
                pos = pos,
                max_hear_distance = 300,
            }, true)
            return exord_core.cooldown.cooldown_start(itemstack, player)
        end
    end,
    on_step = function(itemstack, player, dtime)
    end,
    _cooldown = 4,
    _on_cooldown_start = function(itemstack, player)
        -- minetest.log("cooldown")
        return itemstack
    end,
    _on_cooldown_complete = function(itemstack, player)
        -- minetest.log("ready")
        return itemstack
    end,
    _on_cooldown_step = function(itemstack, player, dtime)
    end,
})

function exord_guns.turret_get_target_and_pos(itemstack, player)
    local LEAD_FACTOR = 1/80
    local pi = exord_player.check_player(player)
    local pos = pi.turret_target and pi.turret_target.object:get_pos()
    -- don't use dead targets, sometimes force refresh
    if pos and pi.turret_target._hp <= 0 or pi._t_turret_refresh < 0 then
        pos = nil
    end

    -- don't do anything if the player has no fplayer
    local fplayer = exord_player.get_alive_fplayer_or_nil(player)
    local fpos = fplayer and fplayer.object:get_pos()
    if not fpos then return end

    if pos then
        local tpos = pi.turret_target.object:get_pos()
        local dist = vector.distance(tpos, fpos) * LEAD_FACTOR
        tpos = tpos + (pi.turret_target.object:get_velocity() * dist)
        return tpos
    end
    if not pos then pi.turret_target = nil end

    pi._t_turret_refresh = 1
    local nearby_objects = minetest.get_objects_inside_radius(fpos, 40)
    local closest_dist
    local closest_target
    for i, object in ipairs(nearby_objects) do
        local opos = object and object:get_pos()
        local ent = opos and object:get_luaentity()
        local dist = ent and ent._exord_swarm and (ent._hp > 0) and exord_core.dist2(opos, fpos)
        if dist and ((not closest_dist) or (dist < closest_dist)) then
            if minetest.line_of_sight(fpos, opos) then
                closest_target = ent
                closest_dist = dist
            end
        end
    end
    pi.turret_target = closest_target
    if closest_target then
        local tpos = closest_target.object:get_pos()
        local dist = vector.distance(tpos, fpos) * LEAD_FACTOR
        tpos = tpos + (closest_target.object:get_velocity() * dist)
        return tpos
    end
end

minetest.register_tool("exord_guns:turret", {
    description = S("Turret"),
    _exord_guns_name = S("MG70 TURRET"),
    inventory_image = "exord_guns_turret.png",
    wield_image = "blank.png",
    on_drop = function(...)end,
    -- on_use = exord_guns.on_trigger_pull,
    on_secondary_use = exord_guns.start_reload,
    on_place = exord_guns.start_reload,
    on_step = exord_guns.on_step,
    after_use = function(...) end,
    _guns_hud = true,
    _fire_rpm = 900,
    -- _full_auto = true,
    _auto_reload = true,
    -- _infinite_ammo = true,
    _mag_capacity = 120,
    _proj_number_per_round = 1,
    _proj_gravity = 0,
    _proj_inaccuracy = 1,
    _proj_damage_nodes = 0,
    _proj_damage_players = 0,
    _proj_speed = 70,
    _proj_tracer = 1.5,
    _proj_max_range = 50,
    _proj_zeroing = 0.0,
    _proj_barrel_index = 3,
    _proj_on_prefire = function (itemstack, player, barrel_pos, target_pos)
        local dir = vector.direction(barrel_pos, target_pos)
        exord_guns.do_proj_muzzle_flash_typical(barrel_pos + dir*0.8, dir, player, 10, 2, 0.5, 0.7)
    end,
    _proj_on_hit_target = function(self, target_ent, pointed_thing)
        exord_core.damage_entity(target_ent, exord_core.NumSet.new({
            piercing = 1,
            player   = 0.2,
        }), self.parent)
        return true
    end,
    _sound_firing_loop = {
        name = "exord_guns_mg_fire_loop",
        gain = 0.9 * exord_core.sound_gain_multiplier,
        pitch = 1,
        max_hear_distance = 220,
        fade_out = 100,
        loop = true,
    },
    _sound_firing_loop_end = {
        name = "exord_guns_mg_fire",
        gain = 0.2 * exord_core.sound_gain_multiplier,
        pitch = 1,
        max_hear_distance = 220,
    },
    _sound_firing_loop_start = {
        name = "exord_tone_attention_0",
        gain = 0.2 * exord_core.sound_gain_multiplier,
        pitch = 2,
        max_hear_distance = 220,
    },
    -- _sound_impact_close = exord_guns.sounds._sound_impact_close,
    -- _sound_impact = exord_guns.sounds._sound_impact,
    _sound_reload_start = {
        name = "exord_guns_reload_start_whirring",
        gain = 0.2,
        pitch = 1.6,
        max_hear_distance = 200,
    },
    _sound_reload_end = {
        name = "exord_tone_attention_0",
        gain = 1,
        pitch = 1.2,
        max_hear_distance = 200,
    },
    _cooldown = 4,
    _on_cooldown_complete = exord_guns.end_reload,
    groups = {turret = 1},
    _on_equipment_step = function(itemstack, player, dtime)
        local pi = exord_player.check_player(player)
        pi._t_turret_refresh = (pi._t_turret_refresh or 0) - dtime
        local fplayer = exord_player.get_alive_fplayer_or_nil(player)
        if (not fplayer) or not pi.has_turret then return end
        local tpos = exord_guns.turret_get_target_and_pos(itemstack, player)
        if not tpos then
            return
        end
        pi.turret_target_pos = tpos
        if not pi.turret_can_fire then return end

        -- exord_core.debug_particle(tpos, "#ff0", 1, UP, 4)
        return exord_guns.on_trigger_pull(itemstack, player, nil, {
            pos = tpos
        })
    end,
})
