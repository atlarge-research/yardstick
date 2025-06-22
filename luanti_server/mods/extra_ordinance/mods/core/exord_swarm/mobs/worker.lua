local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

local function do_digging_particles(self, offset, timemax)
    local vel = 1
    local dist = 2
    local pos = self.object:get_pos()
    if offset then pos = pos + offset end
    minetest.add_particlespawner({
        amount = 10,
        time = 1,
        vertical = false,
        texpool = {
            { name = "exord_swarm_rock_0.png^[multiply:#555" },
            { name = "exord_swarm_rock_1.png^[multiply:#777" },
            { name = "exord_swarm_rock_2.png^[multiply:#999" },
            { name = "exord_swarm_rock_3.png^[multiply:#ccc" },
        },
        glow = 1,
        collisiondetection = true,
        minpos = vector.new(-dist, 0.2, -dist) + pos,
        maxpos = vector.new( dist, 0.2,  dist) + pos,
        minvel = vector.new( vel*-1,     0, vel*-1),
        maxvel = vector.new( vel* 1, vel*10, vel* 1),
        minacc = vector.new(0, -9, 0),
        maxacc = vector.new(0, -9, 0),
        minexptime = 1,
        maxexptime = timemax or 2,
        minsize = 8,
        maxsize = 16,
    })
end

exord_swarm.sound_use = 0
function exord_swarm.try_sound_use()
    if exord_swarm.sound_use < 1 then
        exord_swarm.sound_use = exord_swarm.sound_use + 0.2
        return true
    else
        return false
    end
end

minetest.register_globalstep(function(dtime)
    exord_swarm.sound_use = math.max(0, exord_swarm.sound_use - dtime)
end)

exord_swarm.worker = {
    initial_properties = {
        visual = "mesh",
        mesh = "exord_worker.b3d",
        textures = {"exord_swarm_colors.png"},
        use_texture_alpha = false,
        stepheight = 0.0,
        hp_max = 3,
        collide_with_objects = false,
        physical = true,
        collisionbox = {-0.1, 0, -0.1, 0.9, 0.5, 0.1},
        selectionbox = {-0.8, 0, -0.8, 1.5, 1.5, 0.8},
        pointable = true,
        damage_texture_modifier = "^[colorize:#ff9999:0",
        static_save = false,
        -- glow = 1,
        visual_size = vector.new(1,1,1)*1.3,
    },

    _eye_height = 1,
    _mobcap = true,
    _exord_swarm = true,
    _exord_allow_steal_path = true,
    _exord_can_be_leader = true,
    _time_since_los = 0,
    _time_since_try_dir = 0,
    _hp = 6,
    _exord_armor = {
        explosion = 1,
        piercing = 0.8,
        burning = 1,
        player = 0,
    },
    _on_damage = function(self, damage, source)
        if self._is_dead then return end
        self._hp = self._hp - damage
        if self._hp <= 0 then
            self._is_dead = true
            local fplayer = exord_player.is_object_fake_player(source) and source:get_luaentity()
            local player = fplayer and fplayer._player
            if player then
                SIGNAL("on_player_kill", player, self)
            end
            pmb_entity_api.set_state(self, "death")
        else
            return true
        end
    end,
    _exord_proj_on_damage = function(self, damage, proj)
        if self._is_dead then return end
        self._hp = self._hp - damage
        if self._hp <= 0 then
            self._is_dead = true
            pmb_entity_api.set_state(self, "death")
        end
        return true
    end,

    on_step = pmb_entity_api.do_states(),
    _drop = {
        max_items = 1,
        items = {
            {
                items = {""},
            },
        }
    },

    on_death = function(self, killer)
    end,

    _states = {
        on_step = function(self, dtime, moveresult)
            if not self.object:get_pos() then
                return "death"
            end
            if self._pmb_target then
                self._pmb_speed = 17
            else
                self._pmb_speed = 4
            end

            exord_swarm.on_step(self, dtime)
            pmb_entity_api.decelerate(self, 0.97)

            -- if self._exord_is_leader then
            --     exord_swarm.debug_particle(self.object:get_pos(), "#ff0", 1, vector.new(0,10,0), 8)
            -- end

            self._pmb_time_since_target = (self._pmb_time_since_target or 0) + dtime
        end,
        idle = {
            -- animation = "idle",
            on_state_start = function(self)
                self._lazy = exord_swarm.burrow_time_min + math.max(0.0, math.random() * 2 + 0.7 - 2 * exord_core.difficulty)
                local a = self._animations.spawn
                local fc = a.frames.y - a.frames.x
                self.object:set_animation(a.frames, fc / self._lazy, a.blend, a.loop)
                do_digging_particles(self, nil, 1 + self._lazy)
            end,
            step = function(self, dtime, moveresult)
                if self._pmb_state_time > self._lazy * 0.2 and not self._dig_sound then
                    self._dig_sound = true
                    minetest.sound_play("exord_rubble_explosion", {
                        pos = self.object:get_pos(),
                        max_hear_distance = 160,
                        gain = 0.4 * exord_core.sound_gain_multiplier ,
                        pitch = 0.8 + math.random() * 0.6,
                    })
                end
                if self._pmb_state_time > self._lazy then
                    self._dig_sound = nil
                    self._lazy = nil
                    return "chase"
                end
            end,
        },
        roam = {
            animation = "walk",
            on_state_start = function(self)
            end,
            step = function(self, dtime, moveresult)
                exord_swarm.get_target(self)
                local pos = self.object:get_pos()
                if self._pmb_target then
                    return "chase"
                end

                if not self._exord_is_leader then
                    exord_swarm.push_away(self, dtime*600)
                end

                if not self._roam_target then
                    self._roam_target = pos + exord_guns.vec3_randrange(-30, 30)
                    self._roam_target.y = pos.y
                    -- exord_core.debug_particle(self._roam_target, "#f00", 1, vector.new(0,10,0), 8)
                    self._path_timer = -1
                end

                if self._roam_target then
                    local tmp_vel = self.object:get_velocity()
                    tmp_vel.y = 0
                    local tpos = self._roam_target
                    local force = false
                    self._path_timer = (self._path_timer or 0) - dtime
                    if self._path_timer < 0 then
                        force = true
                        self._path_timer = 30
                    end
                    local dir = exord_swarm.check_get_path_dir(self, tpos, force)
                    if dir then
                        pmb_entity_api.rotate_to_pos(self, pos + dir, 0.1, false)
                        self.object:set_velocity((tmp_vel * 19 + dir * self._pmb_speed)/20)
                    end
                    if exord_core.dist2(pos, self._roam_target) < 2^2 then
                        self._roam_target = nil
                    end
                end

                self._destroy_nodes_timer = (self._destroy_nodes_timer or 0.5) - dtime

                if (self._destroy_nodes_timer < 0) then
                    local front = self.object:get_pos()
                    local destroyed = false
                    for x = 0, 1 do
                        for z = 0, 1 do
                            if exord_core.map.destroy_column(vector.offset(front, x-0.5, 0, z-0.5)) then
                                destroyed = true
                            end
                        end
                    end
                    if destroyed then
                        self._destroy_nodes_timer = 1
                        do_digging_particles(self, vector.new(0, exord_core.map.wall_height-2, 0))
                    end
                end
            end,
        },
        chase = {
            -- animation = "walk",
            on_state_start = function(self)
                local a = self._animations.walk
                self.object:set_animation(a.frames, a.speed * (math.random()*0.2+0.9), a.blend, a.loop)
            end,
            step = function(self, dtime, moveresult)
                if not self then return end
                if not self._pmb_attack_cooldown then self._pmb_attack_cooldown = 1 end
                if self._pmb_attack_cooldown > 0 then self._pmb_attack_cooldown = self._pmb_attack_cooldown - dtime end

                exord_swarm.push_away(self, dtime*600)
                exord_swarm.get_target(self)

                local dist = pmb_entity_api.get_target_dist(self)

                if self._pmb_target and not dist then
                    self._pmb_target = nil
                end

                if (not dist) or self._pmb_target:get_luaentity()._hp <= 0 then
                    return "roam"
                end

                local has_los
                if self._pmb_target ~= nil then
                    has_los = pmb_entity_api.has_los_to_object(self, self._pmb_target)
                    self.__since_los = self.__since_los + 2
                end

                if not has_los then
                    self._time_since_los = (self._time_since_los or 0) + dtime
                elseif dist then
                    local pos = self._pmb_target:get_pos() - self._pmb_target:get_velocity():normalize() * 5
                    self._last_los_pos = pos
                    self._time_since_los = 0
                end

                if self._last_los_pos and exord_core.dist2(self._last_los_pos, self.object:get_pos()) < 4 then
                    self._last_los_pos = nil
                end

                if self._time_since_try_dir > 3 then
                    self._path_angle_offset = (math.random(0,1)*2 - 1)
                elseif not has_los then
                    self._time_since_try_dir = self._time_since_try_dir + dtime
                end

                local pos = self.object:get_pos()
                local tmp_vel = self.object:get_velocity()
                tmp_vel.y = 0

                if dist and self._pmb_target then
                    if dist < 1 then
                        if self._pmb_attack_cooldown < 0 then
                            exord_core.damage_entity(self._pmb_target:get_luaentity(), exord_core.NumSet.new({
                                piercing = 0.1,
                                player   = 0.1,
                                swarm    = 0.1,
                            }), self)
                            self._pmb_attack_cooldown = 0.1
                        end
                    else
                        local NV = exord_swarm.perlin_cost_add:get_3d(vector.round(pos) + self._path_perlin_offset)
                        local tpos = self._pmb_target:get_pos()
                        if has_los then
                            tpos = tpos + self._pmb_target:get_velocity() * math.min(3, dist * math.abs(NV) * 0.15)
                        end
                        local force = false
                        self._path_timer = (self._path_timer or 0) - dtime
                        if self._path_timer < 0 then
                            force = true
                            self._path_timer = 30
                        end
                        local dir = exord_swarm.check_get_path_dir(self, tpos, force)
                        if dir then
                            pmb_entity_api.rotate_to_pos(self, pos + dir, 0.1, false)
                            self.object:set_velocity((tmp_vel * 19 + dir * self._pmb_speed)/20)
                        end
                    end
                end

                if dist and dist > 50 and self._time_since_los > 10 then
                    -- core.log("destroying because inactive swarm")
                    return "burrow_and_remove"
                end

                self._destroy_nodes_timer = (self._destroy_nodes_timer or 0.5) - dtime

                if (self._destroy_nodes_timer < 0) then
                    local destroyed = exord_core.map.damage_radius(pos, 2, 3, false, 0.7)
                    if destroyed then
                        self._destroy_nodes_timer = 1
                        do_digging_particles(self, vector.new(0, exord_core.map.wall_height-2, 0))
                    end
                end

                if self._pmb_to_pos and self._pmb_attack_cooldown <= 0 and dist and dist < 6 then
                    -- ATTACK
                end
            end,
        },
        burrow_and_remove = {
            -- animation = "death",
            on_state_start = function(self)
                local a = self._animations.death
                self.object:set_animation(a.frames, (a.speed or 24) * (math.random()*0.2+0.9), a.blend, a.loop)
                self._pmb_detectable = false
            end,
            step = function(self, dtime, moveresult)
                pmb_entity_api.decelerate(self, 0.2)
                if self._pmb_state_time > 1 then
                    self.object:remove()
                end
            end,
        },
        death = {
            -- animation = "death",
            on_state_start = function(self)
                if exord_swarm.try_sound_use() then
                    minetest.sound_play("exord_swarm_bug_destroy", {
                        gain = 2 * exord_core.sound_gain_multiplier,
                        pos = self.object:get_pos(),
                        max_hear_distance = 70,
                    }, true)
                end
                local a = self._animations.death
                self.object:set_animation(a.frames, (a.speed or 24) * (math.random()*0.2+0.9), a.blend, a.loop)
                self._pmb_detectable = false
                self.object:set_properties({
                    pointable = false,
                })
            end,
            step = function(self, dtime, moveresult)
                pmb_entity_api.decelerate(self, 0.2)
                if self._pmb_state_time > 1 then
                    self.object:remove()
                end
            end,
        },
    },
    _default_state = "idle",
    on_activate = function(self, staticdata, dtime_s)
        self._path_perlin_offset = vector.new(
            math.random(-10,10),
            math.random(-30,30),
            math.random(-10,10)
        )
        local h = math.random(-1,1) * 10
        local s = math.random(-2,0) * 20
        local l = math.random(-2,1) * 15
        self.object:set_properties({
            textures = {"exord_swarm_colors.png^[hsl:"..h..":"..s..":"..l},
        })
        self._hp = 1 + 7 * exord_core.difficulty
        self._pmb_speed = 17  * math.min(1.2, math.max(0.5, exord_core.difficulty + 0.5))
        pmb_entity_api.on_activate(self, staticdata, dtime_s)
    end,
    get_staticdata = function(self)
        return pmb_entity_api.get_staticdata(self)
    end,
    on_deactivate = function(self, removal)
        pmb_entity_api.on_deactivate(self, removal)
    end,
    on_punch = function(self, puncher, time_from_last_punch, tool_capabilities, dir, damage)
        return pmb_entity_api.damage.on_punch(self, puncher, time_from_last_punch, tool_capabilities, dir, damage)
    end,
    _pmb_staticdata_load_list = {
    },
    _path_perlin_offset = vector.new(
        math.random(-8,8),
        math.random(-2,2),
        math.random(-8,8)
    ),
    _pmb_speed = 10,
    _pmb_acceleration = 0.1,
    _pmb_gravity = 1,
    _pmb_max_health = 3,
    _pmb_hostile = {["exord_player:player"] = 1},
    _pmb_damage_groups = {
        pierce=1,
    },
    _animations = {
        idle = {frames={x=20, y=20}, blend=0.2},
        spawn = {frames={x=0, y=29}, blend=0.0, loop=false},
        walk = {frames={x=30, y=49}, blend=0.2, speed = 50},
        death = {frames={x=50, y=65}, blend=0.1, loop=false},
    },
    _pmb_statusfx_enable = true,
}

minetest.register_entity("exord_swarm:worker", exord_swarm.worker)

minetest.register_craftitem("exord_swarm:worker_spawn",
{
    description = "Worker spawn egg",
    inventory_image = "blank.png^[noalpha^[colorize:#f0f:255",
    on_place = function(itemstack, placer, pointed_thing)
        local ent = minetest.add_entity(vector.offset(minetest.get_pointed_thing_position(pointed_thing), 0, 1, 0), "exord_swarm:worker")
    end,
})
