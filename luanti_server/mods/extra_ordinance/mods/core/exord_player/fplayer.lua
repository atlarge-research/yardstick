
local UP = vector.new(0,1,0)

local cbox = {
    -0.8,   0,-0.8,
     0.8,   3, 0.8
}
local sbox = {
    -0.7,   0,-0.7,
     0.7,   2, 0.7
}
local function shortAngleDist(a0, a1)
    local max = math.pi * 2
    local da = (a1 - a0) % max
    return 2 * da % max - da
end

local function angleLerp(a0, a1, t)
    return a0 + shortAngleDist(a0, a1) * t
end

local function angleToward(a0, a1, t)
    local d = shortAngleDist(a0, a1)
    return a0 + math.min(math.abs(d), t) * math.sign(d)
end

minetest.register_entity("exord_player:player", {
    initial_properties = {
        visual = "mesh",
        mesh = "exord_player_mech.b3d",
        textures = {"exord_global_palette.png"},
        use_texture_alpha = false,
        stepheight = 0,
        hp_max = 20,
        physical = true,
        collisionbox = cbox,
        selectionbox = cbox,
        pointable = false,
        damage_texture_modifier = "^[colorize:#ff9999:50",
        static_save = false,
        glow = 0,
        visual_size = vector.new(1, 1, 1),
    },
    _animations = {
        idle = {frames={x=0, y=0}, blend=0.2},
        walk = {frames={x=50, y=79}, speed = 30, blend=0.2},
        spawn = {frames={x=2, y=49}, blend=0.0, loop=false},
        death = {frames={x=81, y=110}, blend=0.2, loop=false},
    },
    _eye_height = 1,
    _fake_player = true,
    _hp = 3,
    _speed = 6,
    _animation_time = 0,
    _since_damage = 0,
    _heal = function(self, amount)
        if self._is_dead then return end
        local pi = minetest.is_player(self._player) and exord_player.check_player(self._player)
        if not pi then return end
        local max = (pi.max_hp or exord_player.max_hp)
        self._hp = math.min(max, self._hp + amount)
    end,
    _on_damage = function(self, damage, source)
        if self._is_dead then return end
        self._hp = math.max(0, self._hp - damage)
        if self._hp < 4 and not self._low_hp_sound_played then
            local player = minetest.is_player(self._player) and self._player
            if player then
                self._low_hp_sound_played = true
                minetest.sound_play("exord_tone_attention_2", {
                    gain = 1,
                    to_player = player:get_player_name(),
                }, true)
            end
        end
        if self._since_damage > 0.3 then
            self._since_damage = 0 + math.random()*0.2
            minetest.sound_play("exord_player_damage", {
                gain = 3 * exord_core.sound_gain_multiplier,
                pos = self.object:get_pos(),
                max_hear_distance = 70,
                pitch = 0.8,
            }, true)
        end
        if self._hp <= 0 then
            self._is_dead = true
            local fplayer = exord_player.is_object_fake_player(source) and source:get_luaentity()
            local player = fplayer and fplayer._player
            if player then
                SIGNAL("on_player_kill", player, self)
            end
            SIGNAL("on_fplayer_killed", self, self._player)
            MFSM.set_states(self, {
                death = true,
            })
        else
            return true
        end
    end,
    _warp_up = function(self)
        self._warp_time = 1
        self._is_dead = true
        self._hp = 0
        self.object:set_velocity(vector.new(0,2,0))
    end,
    _force_update_player_position = function(self)
    end,
	on_step = function(self, dtime)
        local player = self._player
        local pi = minetest.is_player(player) and exord_player.check_player(player)
        if not pi then
            -- error("could not get pi in fplayer")
            self.object:remove()
            return
        end
        if pi.ent ~= self then
            -- error("player has not got fplayer logged in pi")
            self.object:remove()
            return
        end

        if self._warp_time then
            if self._warp_time <= 0 then
                self.object:remove()
            else
                self._warp_time = math.max(0, self._warp_time - dtime)
            end
            self.object:set_properties({
                visual_size = vector.new(
                    1*self._warp_time,
                    1 + (1 - self._warp_time) * 5,
                    1*self._warp_time),
                physical = false,
            })
            self.object:set_velocity(vector.new(0,2,0))
            return
        end

        if not self._init then
            self._init = true
            MFSM.set_states(self, {
                spawning_in = true,
                do_camera = true,
            })
        end
        self._since_damage = self._since_damage + dtime
        self._animation_time = self._animation_time + dtime
        MFSM.on_step(self, dtime)
	end,
    _barrel_offsets = {
        [1] = vector.new(-1.15, 2.5, 1.2),
        [2] = vector.new(1.2, 2.4, 1.7),
        [3] = vector.new(0.4, 3.7, 0.0),
    },
    _get_barrel_position = function(self, barrel)
        local pi = minetest.is_player(self._player) and exord_player.check_player(self._player)
        if not pi then
            core.log("error got no player in fplayer")
            return self.object:get_pos()
        end
        local bpos = self._barrel_offsets[barrel or 1] or vector.zero()
        return self.object:get_pos() + bpos:rotate_around_axis(
            UP, (pi.last_cabin_yaw_override or 0)
        )
    end,
    on_deactivate = function(self)
        SIGNAL("on_fplayer_destroyed", self, self._player)
    end,
    _MFSM_states = {
        {
            name = "do_controls",
            on_step = function(self, dtime, meta)
                exord_player.do_fplayer_movement(self, self._player, dtime)
            end,
            on_start = function(self, meta)
            end,
            on_end = function(self, meta)
            end,
        },
        {
            name = "do_camera",
            on_step = function(self, dtime, meta)
                exord_player.do_fplayer_camera(self, self._player, dtime)
            end,
            on_start = function(self, meta)
            end,
            on_end = function(self, meta)
            end,
        },
        {
            name = "do_proc_anim",
            on_step = function(self, dtime, meta)
                exord_player.do_fplayer_animation(self, self._player, dtime)
            end,
            on_start = function(self, meta)
            end,
            on_end = function(self, meta)
            end,
        },
        {
            name = "spawning_in",
            on_step = function(self, dtime, meta)
                self._t_state = self._t_state + dtime
                if self._t_state > 2 then
                    self._t_state = 0
                    SIGNAL("on_fplayer_give_control", self, self._player)
                    MFSM.set_state(self, "normal_play", true)
                end
                if self._t_state > 0.5 and not self._done_drop then
                    self._done_drop = true
                    exord_core.voiceover.play_voice_situation("player_spawn", self._player)
                    local pos = self.object:get_pos()
                    exord_guns.do_shockwave(pos, 0, 100, 6, 1, 1)
                    minetest.sound_play("exord_guns_explosion_1", {
                        gain = 1,
                        pitch = 0.8,
                        pos = pos,
                        max_hear_distance = 300,
                        to_player_direct = self._player,
                    }, true)

                    SIGNAL("on_fplayer_landed", self, self._player)
                end
            end,
            on_start = function(self, meta)
                self._t_state = 0
                self._done_drop = nil
                exord_player.set_fplayer_animation(self, "spawn")
            end,
            on_end = function(self, meta)
            end,
        },
        {
            name = "normal_play",
            on_step = function(self, dtime, meta)
                self._t_state = self._t_state + dtime
            end,
            on_start = function(self, meta)
                local name = self._player:get_player_name()
                self.object:set_properties({
                    nametag = name ~= "singleplayer" and name or " ",
                    nametag_color = "#ffffff50",
                    nametag_bgcolor = "#00000000",
                })
                self._t_state = 0
                MFSM.set_states(self, {
                    spawning_in = false,
                    do_camera = true,
                    do_proc_anim = true,
                    do_controls = true,
                })
            end,
            on_end = function(self, meta)
            end,
        },
        {
            name = "death",
            on_step = function(self, dtime, meta)
                self._t_state = self._t_state + dtime
                self.object:set_velocity(vector.zero())
                if self._t_state > 4 then
                    self.object:remove()
                end
            end,
            on_start = function(self, meta)
                exord_player.die_fplayer(self)
                self._t_state = 0
                exord_guns.do_explosion(self.object:get_pos(), 1, 20, 2, 1.0, 0.6)
                exord_guns.do_explosion(self.object:get_pos(), 1, 10, 3, 0.5, 0.3)
                minetest.sound_play("exord_guns_explosion_4", {
                    gain = 0.9 * exord_core.sound_gain_multiplier,
                    pitch = 1,
                    pos = self.object:get_pos(),
                    max_hear_distance = 300,
                }, true)
                minetest.sound_play("exord_guns_explosion_5", {
                    gain = 0.5 * exord_core.sound_gain_multiplier,
                    pitch = 1,
                    pos = self.object:get_pos(),
                    max_hear_distance = 300,
                }, true)
                MFSM.set_states(self, {
                    spawning_in = false,
                    do_camera = false,
                    do_proc_anim = false,
                    do_controls = false,
                })
                exord_player.set_fplayer_animation(self, "death")
            end,
            on_end = function(self, meta)
            end,
            is_protected = true,
        },
    },
    on_activate = function(self, staticdata, dtime_s)
        pmb_entity_api.on_activate(self, staticdata, dtime_s)
        self._exord_armor = exord_core.NumSet.new({
            explosive = 0.0,
            piercing  = 0.0,
            burning   = 0.0,
            shock     = 0.0,
            player    = 0.0,
        })
        MFSM.init_states(self)
    end,
})


function exord_player.do_fplayer_movement(self, player, dtime)
    local pi = exord_player.check_player(player)
    local ctrl = player:get_player_control()
    local walkdir = vector.new(
        (ctrl.left and -1 or 0) + (ctrl.right and 1 or 0),
        0,
        (ctrl.down and -1 or 0) + (ctrl.up and 1 or 0)
    ):normalize()
    walkdir = vector.rotate_around_axis(walkdir, UP, player:get_look_horizontal())
    self._last_move_dir = walkdir
    local tmp_vel = self.object:get_velocity()
    if (pi._dodge_time or 0) > 0.3 then
        tmp_vel = (tmp_vel * 9 + (walkdir * self._speed)) * 0.1
    else
    end
    self.object:set_velocity(tmp_vel)
end

function exord_player.do_fplayer_camera(self, player, dtime)
    local pi = exord_player.check_player(player)
    local ppos = player:get_pos() + player:get_velocity() * 0.2
    local vel_len_f = player:get_velocity():length()
    vel_len_f = 1 - math.max(0, math.min(1, vel_len_f / 40))
    local fpos = self.object:get_pos()
    -- decelerate player
    local offset = exord_player.cam_offset

    if exord_player.cam_rotation then
        local look_yaw = player:get_look_horizontal()
        local cam_yaw = minetest.dir_to_yaw(
            vector.direction(ppos, fpos)
        )
        local should_be_pos_rotated = vector.rotate_around_axis(
            offset, UP, look_yaw + math.pi
        ) + fpos

        local should_be_pos_static = vector.rotate_around_axis(
            offset, UP, cam_yaw + math.pi
        ) + fpos

        -- exord_core.debug_particle(should_be_pos_static, "#fff", 1, vector.direction(ppos, fpos)*20, 4)

        local pvel = player:get_velocity()

        local yaw_factor = math.abs(shortAngleDist(look_yaw, cam_yaw)) / math.pi
        yaw_factor = math.max(0, yaw_factor - (exord_player.cam_rotate_threshold or 0.4))

        -- we'll say the max camera distance is 10 nodes for a guide
        local dist_static = vector.distance(should_be_pos_static, ppos) - exord_player.cam_follow_threshold
        dist_static = math.max(0, dist_static)
        local dist_factor_static = math.min(1, dist_static/10)

        local factor = 0
        do
            -- cosine just makes it more boosted in the lower values, so that the camera reacts more quickly
            local f = dist_factor_static
            f = f + f * math.min(1, math.cos(f) * 20)
            factor = math.min(5.0, f * 10)
        end

        do
            local f = yaw_factor
            f = f + f * math.min(1, math.cos(f) * 20)
            -- get the biggest factor and use that
            factor = math.max(factor, math.min(5.0, f * 10))
        end

        local dir = vector.direction(ppos, should_be_pos_rotated)
        dir.y = dir.y * 0.02
        factor = math.min(4, math.max(-4, factor * vel_len_f))
        player:add_velocity(dir * factor)
        pvel.x = pvel.x * -0.01
        pvel.z = pvel.z * -0.01
        player:add_velocity(pvel * -0.05)
    else
        local should_be_pos = vector.rotate_around_axis(
            offset, UP,
            exord_player.starting_cam_rotation + math.pi
        ) + fpos
        local dist = vector.distance(should_be_pos, ppos)
        local dir = vector.direction(ppos, should_be_pos)
        if dist > 0 then
            local factor = (dist*4)^2
            local vel = dir * math.min(6, factor * dtime * 100 * exord_player.cam_rotation_mult)
            vel.y = vel.y * 0.3
            player:add_velocity(vel)
        end
    end
end

function exord_player.set_fplayer_animation(self, anim_name, force)
    local anim = self._animations[anim_name]
    if not anim then return end
    if (not force) and (self._last_animation == anim_name) then return end
    self._last_animation = anim_name
    self.object:set_animation(anim.frames, anim.speed or 24, anim.blend, anim.loop ~= false)
    self._animation_time = 0
end

function exord_player.get_fplayer_dir(player)
    local fplayer = exord_player.get_fplayer_or_nil(player)
    if not fplayer then return vector.zero() end
    return vector.direction(player:get_pos(), fplayer.object:get_pos())
end

function exord_player.do_fplayer_animation(self, player, dtime)
    local pi = exord_player.check_player(player)
    local move_dir = self._last_move_dir
    if move_dir:length() > 0.1 then
        local move_yaw = minetest.dir_to_yaw(move_dir)
        pi.last_hips_yaw_override = angleLerp(pi.last_hips_yaw_override or 0, move_yaw, 0.1)
        COMPAT.set_bone_override(self.object, "hips_o", {
            rotation = {
                vec = vector.new(0, -pi.last_hips_yaw_override, 0),
                interpolation = dtime + 0.05,
                absolute = true,
            },
        })
        exord_player.set_fplayer_animation(self, "walk")

        local t = self._animation_time
        local tmax = (self._animations.walk.frames.y - self._animations.walk.frames.x) / (self._animations.walk.speed or 24)
        local f = (t % tmax) / tmax
        local do_footstep = false
        if f > 0.5 and not self._footstep then
            self._footstep = true
            do_footstep = true
        elseif f < 0.5 and f > 0.0 and self._footstep then
            self._footstep = false
            do_footstep = true
        end
        if do_footstep then
            core.sound_play("exord_walk", {
                pos = self.object:get_pos(),
                gain = 0.5 * exord_core.sound_gain_multiplier,
                max_hear_distance = 300,
                to_player_direct = player,
                distance_factor = 0.4,
            }, true)
        end
    else
        exord_player.set_fplayer_animation(self, "idle")
    end

    local cabin_yaw = pi.last_cabin_yaw_override or 0
    if pi.last_pointed_thing then
        cabin_yaw = minetest.dir_to_yaw(
            vector.direction(self.object:get_pos(), pi.last_pointed_thing.intersection_point)
        )
    end
    pi.last_cabin_yaw_override = cabin_yaw
    COMPAT.set_bone_override(self.object, "cabin_o", {
        rotation = {
            vec = vector.new(0, -cabin_yaw, 0),
            interpolation = dtime + 0.05,
            absolute = true,
        },
    })

    pi.has_turret = minetest.get_item_group(player:get_inventory():get_stack("main", 1):get_name(), "turret") > 0
    if pi.has_turret and (self._turret_removed ~= false) then
        self._turret_removed = false
        COMPAT.set_bone_override(self.object, "turret", {scale = {
            vec = vector.new(1, 1, 1),
            interpolation = 1,
            absolute = true,
        }})
    elseif (not pi.has_turret) and (self._turret_removed ~= true) then
        self._turret_removed = true
        COMPAT.set_bone_override(self.object, "turret", {scale = {
            vec = vector.new(1, 1, 1)*0,
            interpolation = 1,
            absolute = true,
        }})
    end
    if pi.has_turret and pi.turret_target_pos then
        local turret_yaw = - minetest.dir_to_yaw(
            vector.direction(self.object:get_pos(), pi.turret_target_pos)
        )
        -- pi.turret_yaw = angleToward(pi.turret_yaw or 0, turret_yaw, math.pi*dtime)
        pi.turret_yaw = angleLerp(pi.turret_yaw or 0, turret_yaw, 0.1)
        pi.turret_can_fire = math.abs(shortAngleDist(pi.turret_yaw, turret_yaw)) < 0.2
        COMPAT.set_bone_override(self.object, "turret", {
            rotation = {
            vec = vector.new(0,  pi.turret_yaw + (cabin_yaw or 0), 0),
            interpolation = dtime + 0.05,
            absolute = true,
        }})
    end
end


function exord_player.heal_all_fplayers(amount)
    for i, fplayer in ipairs(exord_player.get_alive_fake_players()) do
        fplayer:_heal(amount)
    end
end

function exord_player.spawn_player(player, pos)
    -- core.log("trying to spawn player")
    local obj = minetest.add_entity(pos, "exord_player:player")
    local ent = obj and obj:get_luaentity()
    if not ent then
        minetest.kick_player(
            player:get_player_name(),
            "Could not spawn an entity for the player to use. Try again later."
        )
        return nil
    end
    exord_player.force_reset_camera(player)
    ent._player = player

    local pi = exord_player.check_player(player)
    local compassobj = minetest.add_entity(pos, "exord_player:compass")
    local entc = compassobj and compassobj:get_luaentity()
    entc._player = player
    ent._compass_ent = entc
    pi.compass = entc
    compassobj:set_attach(ent.object, "", vector.new(0,25,0), nil, true)
    return ent
end

function exord_player.spawn_fake_player(player, pos)
    local pi = exord_player.check_player(player)
    local node = minetest.get_node_or_nil(pos)
    if node then
        local ent = exord_player.spawn_player(player, pos)
        if ent then
            pi.queued = false
            pi.ent = ent
            exord_player.queue[player] = nil
            table.insert(exord_player.playing_list, ent)
            SIGNAL("on_fplayer_spawned", player, ent)
            ent._hp = (pi.max_hp or exord_player.max_hp)
        end
    end
end
