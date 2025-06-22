local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

local function nullfunc(...) end

exord_guns.gun_defs = {}

exord_core.sound_gain_multiplier = 4

exord_guns.sounds = {
    _sound_impact_close = {
        name = "exord_guns_generic_impact_close",
        gain = 0.1,
        max_hear_distance = 30,
    },
    _sound_impact = {
        name = "exord_guns_generic_impact",
        gain = 1,
        max_hear_distance = 30,
        pitch_random = 0.5
    },
    _sound_empty = {
        name = "exord_guns_pistol_empty",
        gain = 0.9,
        max_hear_distance = 20,
    },
    _sound_reload_start = {
        name = "exord_guns_pistol_empty",
        gain = 0.9,
        max_hear_distance = 20,
    },
    _sound_reload_end = {
        name = "exord_guns_pistol_cocked",
        gain = 0.9,
        max_hear_distance = 20,
    },
}

function exord_guns.do_explosion(pos, radius, count, force, size, exp)
    local node = minetest.get_node(pos)
    if node.name == "air" then
        minetest.set_node(pos, {name="pmb_util:light_node_11"})
        local nt = minetest.get_node_timer(pos)
        nt:start(1)
        nt:set(1,0.99)
    end
    force = force or 1
    radius = radius or 1
    count = count or 30
    size = size or 1
    exp = exp or 1
    local vel = force * 8
    minetest.add_particlespawner({
        amount = count,
        time = 0.00001,
        vertical = false,
        texpool = {
            {
                name = "explosion_anim.png",
                animation = {
                    type = "vertical_frames",
                    aspect_w = 8, aspect_h = 8,
                    length = 2 * exp,
                }
            },
            {
                name = "explosion_anim.png",
                animation = {
                    type = "vertical_frames",
                    aspect_w = 8, aspect_h = 8,
                    length = 2.5 * exp,
                }
            },
        },
        glow = 14,
        collisiondetection = true,
        minpos = vector.new(-radius, 0.1 + size*0.5,        -radius) + pos,
        maxpos = vector.new( radius, 1 + 0.2*radius,  radius) + pos,
        minvel = vector.new( vel*-1,     0, vel*-1),
        maxvel = vector.new( vel* 1, vel*1, vel* 1),
        minacc = vector.new(0, -9, 0),
        maxacc = vector.new(0, -9, 0),
        drag = vector.new(1, 2, 1),
        minexptime = 1.5 * exp,
        maxexptime = 1.5 * exp,
        minsize = 4 * size,
        maxsize = 32 * size,
    })
end

function exord_guns.do_muzzle_flash(pos, vel, count, force, size, exp)
    force = force or 1
    count = count or 30
    size = size or 1
    exp = exp or 1
    vel = vel * force
    local off = vector.new(1,1,1)
    minetest.add_particlespawner({
        amount = count,
        time = 0.00001,
        vertical = false,
        texpool = {
            {
                name = "explosion_anim.png",
                animation = {
                    type = "vertical_frames",
                    aspect_w = 8, aspect_h = 8,
                    length = exp * 1.1,
                }
            },
            {
                name = "explosion_anim.png",
                animation = {
                    type = "vertical_frames",
                    aspect_w = 8, aspect_h = 8,
                    length = exp * 1.5,
                }
            },
        },
        glow = 14,
        collisiondetection = true,
        minpos = pos,
        maxpos = pos,
        minvel = vel * 0.75 - off,
        maxvel = vel + off,
        minacc = vector.new(0, 0, 0),
        maxacc = vector.new(0, 0, 0),
        drag = vector.new(1, 1, 1),
        minexptime = exp,
        maxexptime = exp,
        minsize = 4 * size,
        maxsize = 32 * size,
    })
end

local UP = vector.new(0,1,0)

function exord_guns.do_proj_muzzle_flash_typical(pos, vel, player, force, count, size, exp)
    local fplayer = exord_player.get_alive_fplayer_or_nil(player)
    local fvel = fplayer and fplayer.object:get_velocity() or vector.zero()
    local pvel = fvel * 0.05 + vel

    local node = minetest.get_node(pos)
    if node.name == "air" then
        minetest.set_node(pos, {name="pmb_util:light_node_14"})
        local nt = minetest.get_node_timer(pos)
        nt:start(1)
        nt:set(1,0.99)
    end

    local off = vector.new(1,1,1)
    if count >= 3 then
        exord_guns.do_muzzle_flash(pos, pvel, math.ceil(count/3), force*3, 0.4 * size, exp)
        exord_guns.do_muzzle_flash(pos, pvel, math.ceil(count/3), force*2, 0.4 * size, exp)
        exord_guns.do_muzzle_flash(pos, pvel, math.ceil(count/3), force, 0.4 * size, exp)
        return
    end
    for i = 1, count do
        local pv = pvel:normalize() + exord_guns.vec3_randrange(-0.3, 0.3)
        pv = pv * pvel:length() * (math.random()*0.5+1) * force
        minetest.add_particle({
            size = 32 * (size or 1) * 0.4 * (math.random()/2+0.5),
            pos = pos,
            texture = "explosion_anim.png",
            animation = {
                type = "vertical_frames",
                aspect_w = 8, aspect_h = 8,
                length = exp * 1.2,
            },
            velocity = pv,
            expirationtime = exp,
            glow = 14,
        })
    end
end

minetest.register_tool("exord_guns:he20", {
    description = S("20cm Cannon"),
    _exord_guns_name = S("200mm CANNON"),
    inventory_image = "exord_guns_he20.png",
    wield_image = "blank.png",
    on_drop = nullfunc,
    on_use = exord_guns.on_trigger_pull,
    on_secondary_use = exord_guns.start_reload,
    on_place = exord_guns.start_reload,
    on_step = exord_guns.on_step,
    after_use = function(itemstack, user, node, digparams) end,
    _guns_hud = true,
    _fire_rpm = 200,
    _full_auto = true,
    -- _mag_capacity = 2,
    _mag_capacity = 18,
    -- _reload_time = 3,
    _auto_reload = true,
    _proj_gravity = 0,
    _proj_inaccuracy = 1,
    _proj_damage_nodes = 0,
    _proj_damage_players = 0,
    _proj_speed = 30,
    _proj_tracer = 6,
    _proj_barrel_index = 2,
    _enable_look_crouch = true,
    _proj_on_step = function(self, dtime)
    end,
    _proj_on_prefire = function (itemstack, player, barrel_pos, target_pos)
        local dir = vector.direction(barrel_pos, target_pos)
        exord_guns.do_proj_muzzle_flash_typical(barrel_pos, dir, player, 5, 20, 0.9, 1)
        exord_guns.do_proj_muzzle_flash_typical(barrel_pos, dir, player, 10, 10, 0.7, 0.6)
    end,
    _proj_on_fire = function(self, itemstack, player)
        local dist = vector.distance(self.position, self.target_pos)
        self.max_range = math.min(self.max_range, dist)
    end,
    _proj_on_destroy = function(self, pointed_thing)
        local pos = self:get_position()
        exord_core.map.damage_radius(pos, 5.7, 1, true, 1)
        exord_core.damage_radius(pos, 4.7, exord_core.NumSet.new({
            explosive = 5.1,
            burning = 1,
            player = 3,
        }), self.parent, 1.5, 4)
        exord_guns.do_explosion(self.position, 1, 20, 2, 1.0, 0.6)
        exord_guns.do_explosion(self.position, 1, 10, 3, 0.5, 0.3)
        minetest.sound_play("exord_guns_explosion_4", {
            gain = 0.6 * exord_core.sound_gain_multiplier,
            pitch = 1,
            pos = self.position,
            max_hear_distance = 300,
        }, true)
    end,
    _sound_fire = {
        name = "exord_guns_heavy_fire",
        gain = 1 * exord_core.sound_gain_multiplier,
        max_hear_distance = 200,
    },
    _sound_impact_close = exord_guns.sounds._sound_impact_close,
    _sound_impact = exord_guns.sounds._sound_impact,
    _sound_empty = exord_guns.sounds._sound_empty,
    _sound_reload_start = {
        name = "exord_guns_reload_start_whirring_clank",
        gain = 0.9,
        max_hear_distance = 200,
    },
    _sound_reload_end = {
        name = "exord_guns_reload_click_in",
        gain = 0.9,
        max_hear_distance = 200,
    },
    _proj_max_range = 60,
    _cooldown = 8,
    _on_cooldown_start = function(itemstack, player)
        return itemstack
    end,
    _on_cooldown_complete = exord_guns.end_reload,
})


minetest.register_tool("exord_guns:gl80", {
    description = S("GL-80mm Full Auto Grenade Launcher Minigun"),
    _exord_guns_name = S("GL-80"),
    inventory_image = "exord_guns_gl80.png",
    wield_image = "blank.png",
    on_drop = nullfunc,
    on_use = exord_guns.on_trigger_pull,
    on_secondary_use = exord_guns.start_reload,
    on_place = exord_guns.start_reload,
    on_step = exord_guns.on_step,
    after_use = function(itemstack, user, node, digparams) end,
    _guns_hud = true,
    _fire_rpm = 600,
    _full_auto = true,
    _mag_capacity = 42,
    _reload_time = 2,
    _auto_reload = true,
    _proj_gravity = 0,
    _proj_inaccuracy = 2,
    _proj_damage_nodes = 0,
    _proj_damage_players = 0,
    _proj_speed = 50,
    _proj_tracer = 5,
    _proj_barrel_index = 2,
    _enable_look_crouch = true,
    _proj_on_step = function(self, dtime)
    end,
    _proj_on_prefire = function (itemstack, player, barrel_pos, target_pos)
        local dir = vector.direction(barrel_pos, target_pos)
        exord_guns.do_proj_muzzle_flash_typical(barrel_pos, dir, player, 4, 10, 0.8, 1)
    end,
    _proj_on_fire = function(self, itemstack, player)
        local dist = vector.distance(self.position, self.target_pos)
        self.max_range = math.min(self.max_range, dist)
    end,
    _proj_on_destroy = function(self, pointed_thing)
        local pos = self:get_position()
        exord_core.map.damage_radius(pos, 1.7, 1, true, 0.6)
        exord_core.damage_radius(pos, 4, exord_core.NumSet.new({
            explosive = 2.1,
            burning = 1,
            player = 1,
        }), self.parent, 2, 3)
        exord_guns.do_explosion(self.position, 1, 14, 2.3, 0.4, 0.3)
        minetest.sound_play("exord_guns_explosion_5", {
            gain = 0.3 * exord_core.sound_gain_multiplier,
            pitch = 1,
            pos = self.position,
            max_hear_distance = 300,
        }, true)
    end,
    _sound_fire = {
        name = "exord_guns_rifle_fire_alt",
        gain = 1.5 * exord_core.sound_gain_multiplier,
        pitch = 1,
        max_hear_distance = 200,
    },
    _sound_reload_start = {
        name = "exord_guns_reload_start_whirring",
        gain = 0.4,
        max_hear_distance = 200,
    },
    _sound_reload_end = {
        name = "exord_guns_reload_click_in",
        gain = 0.9,
        max_hear_distance = 200,
    },
    _sound_impact_close = exord_guns.sounds._sound_impact_close,
    _sound_impact = exord_guns.sounds._sound_impact,
    _sound_empty = exord_guns.sounds._sound_empty,
    _proj_max_range = 60,
    _cooldown = 6.0,
    _on_cooldown_complete = exord_guns.end_reload,
})

exord_guns.gun_defs.mtaw_mk3 = {
    description = S("Multi Target Assult Weapon, or in other words, a full auto grenade launcher shotgun"),
    _exord_guns_name = S("MTAW MK3"),
    inventory_image = "exord_guns_mtaw_mk3.png",
    wield_image = "blank.png",
    on_drop = nullfunc,
    on_use = exord_guns.on_trigger_pull,
    on_secondary_use = exord_guns.start_reload,
    on_place = exord_guns.start_reload,
    on_step = exord_guns.on_step,
    after_use = function(itemstack, user, node, digparams) end,
    _guns_hud = true,
    _fire_rpm = 260,
    _full_auto = true,
    _mag_capacity = 14,
    _auto_reload = true,
    _proj_number_per_round = 6,
    _proj_gravity = 0,
    _proj_inaccuracy = 5,
    _proj_damage_nodes = 0,
    _proj_damage_players = 0,
    _proj_speed = 70,
    _proj_tracer = 5,
    _proj_barrel_index = 1,
    _enable_look_crouch = true,
    _proj_on_step = function(self, dtime)
    end,
    _proj_on_prefire = function (itemstack, player, barrel_pos, target_pos)
        local dir = vector.direction(barrel_pos, target_pos)
        exord_guns.do_proj_muzzle_flash_typical(barrel_pos, dir, player, 5, 20, 0.7, 0.7)
    end,
    _proj_on_fire = function(self, itemstack, player)
        local dist = vector.distance(self.position, self.target_pos)
        self.max_range = math.min(self.max_range, dist)
    end,
    _proj_on_destroy = function(self, pointed_thing)
        local pos = self:get_position()
        exord_core.damage_radius(pos, 3.5, exord_core.NumSet.new({
            explosive = 1.7,
            burning = 1,
            player = 0.5,
        }), self.parent, 1.4, 2)
        exord_guns.do_explosion(self.position, 1, 10, 3, 0.2, 0.2)
        minetest.sound_play("exord_guns_explosion_1", {
            gain = 0.2 * exord_core.sound_gain_multiplier,
            pitch = 1.5,
            pos = self.position,
            max_hear_distance = 300,
        }, true)
    end,
    _sound_fire = {
        name = "exord_guns_heavy_fire",
        gain = 0.8 * exord_core.sound_gain_multiplier,
        pitch = 1.5,
        max_hear_distance = 200,
    },
    -- _sound_impact_close = exord_guns.sounds._sound_impact_close,
    -- _sound_impact = exord_guns.sounds._sound_impact,
    _sound_empty = exord_guns.sounds._sound_empty,
    _sound_reload_start = {
        name = "exord_guns_reload_start_whirring",
        gain = 0.4,
        pitch = 1.2,
        max_hear_distance = 200,
    },
    _sound_reload_end = {
        name = "exord_guns_reload_click_in",
        gain = 0.8,
        pitch = 1.2,
        max_hear_distance = 200,
    },
    _proj_max_range = 40,
    _cooldown = 5.8,
    _on_cooldown_complete = exord_guns.end_reload,
}

minetest.register_tool("exord_guns:mtaw_mk3", exord_guns.gun_defs.mtaw_mk3)
exord_guns.gun_defs.mtaw_mk3_coaxial = table.copy(exord_guns.gun_defs.mtaw_mk3)
local mtaw_mk3_coaxial = exord_guns.gun_defs.mtaw_mk3_coaxial
mtaw_mk3_coaxial._infinite_ammo = true
mtaw_mk3_coaxial._fire_rpm = 90
mtaw_mk3_coaxial._proj_number_per_round = 4
minetest.register_tool("exord_guns:mtaw_mk3_coaxial", exord_guns.gun_defs.mtaw_mk3_coaxial)


minetest.register_tool("exord_guns:mg70", {
    description = S(".70cal Coaxial Machinegun"),
    _exord_guns_name = S("MG70 COAXIAL"),
    inventory_image = "exord_guns_mg70.png",
    wield_image = "blank.png",
    on_drop = nullfunc,
    on_use = exord_guns.on_trigger_pull,
    -- on_secondary_use = exord_guns.start_reload,
    -- on_place = exord_guns.start_reload,
    on_step = exord_guns.on_step,
    after_use = function(itemstack, user, node, digparams) end,
    _guns_hud = true,
    _fire_rpm = 1400,
    _full_auto = true,
    -- _mag_capacity = 300,
    _infinite_ammo = true,
    -- _reload_time = 2,
    _auto_reload = true,
    _proj_gravity = 0,
    _proj_inaccuracy = 2,
    _proj_damage_nodes = 0,
    _proj_damage_players = 1,
    _proj_speed = 60,
    _proj_tracer = 3,
    _proj_max_range = 50,
    _proj_zeroing = 0.0,
    _proj_barrel_index = 1,
    _proj_on_prefire = function (itemstack, player, barrel_pos, target_pos)
        local rounds = itemstack:get_meta():get_int("rounds") or 0
        local dir = vector.direction(barrel_pos, target_pos)
        exord_guns.do_proj_muzzle_flash_typical(barrel_pos, dir, player, 4, 2, 0.5, 0.5)
    end,
    _proj_on_fire = function(self, itemstack, player)
        local dist = vector.distance(self.position, self.target_pos)
        self.max_range = math.min(self.max_range, dist)
    end,
    _proj_on_hit_target = function(self, target_ent, pointed_thing)
        exord_core.damage_entity(target_ent, exord_core.NumSet.new({
            piercing = 0.7,
            player   = 0.5,
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
        gain = 0.4 * exord_core.sound_gain_multiplier,
        pitch = 1,
        max_hear_distance = 220,
    },
    _sound_firing_loop_start = {
        name = "exord_guns_mg_fire",
        gain = 0.4 * exord_core.sound_gain_multiplier,
        pitch = 1,
        max_hear_distance = 220,
    },
    -- _sound_impact_close = exord_guns.sounds._sound_impact_close,
    -- _sound_impact = exord_guns.sounds._sound_impact,
    _sound_empty = exord_guns.sounds._sound_empty,
    _cooldown = 0.1,
    _on_cooldown_complete = exord_guns.end_reload,
})

minetest.register_tool("exord_guns:amr30", {
    description = S("30mm Antimaterial Rifle"),
    _exord_guns_name = S("AMR-30"),
    inventory_image = "exord_guns_amr30.png",
    wield_image = "blank.png",
    on_drop = nullfunc,
    on_use = exord_guns.on_trigger_pull,
    on_secondary_use = exord_guns.start_reload,
    on_place = exord_guns.start_reload,
    on_step = exord_guns.on_step,
    after_use = function(itemstack, user, node, digparams) end,
    _guns_hud = true,
    _fire_rpm = 200,
    _full_auto = true,
    _mag_capacity = 14,
    -- _infinite_ammo = true,
    -- _reload_time = 2,
    _auto_reload = true,
    _proj_gravity = 0,
    _proj_inaccuracy = 0.2,
    _proj_speed = 220,
    _proj_tracer = 6,
    _proj_max_range = 90,
    _proj_zeroing = 0.0,
    _proj_barrel_index = 2,
    _proj_on_prefire = function (itemstack, player, barrel_pos, target_pos)
        local dir = vector.direction(barrel_pos, target_pos)
        exord_guns.do_proj_muzzle_flash_typical(barrel_pos, dir, player, 8, 10, 1, 2)
    end,
    _proj_on_fire = function(self, itemstack, player)
        local dist = vector.distance(self.position, self.target_pos)
        self.max_range = math.min(self.max_range, dist)
    end,
    _proj_on_hit_target = function(self, target_ent, pointed_thing)
        -- exord_core.damage_entity(target_ent, exord_core.NumSet.new({
        --     piercing = 6,
        --     player   = 0.5,
        -- }), self.parent)
        return true
    end,
    _proj_on_destroy = function(self, pointed_thing)
        local pos = self:get_position()
        exord_core.map.damage_radius(pos, 1.5, 1, false, 1)
        exord_core.damage_radius(pos, 3, exord_core.NumSet.new({
            explosive = 4,
            burning = 3,
            piercing = 14,
            player = 3,
        }), self.parent, 2, 4)
        exord_guns.do_explosion(self.position, 1, 10, 3, 0.2, 0.2)
    end,
    _sound_fire = {
        name = "exord_guns_sniper",
        gain = 1 * exord_core.sound_gain_multiplier,
        pitch = 1,
        max_hear_distance = 220,
    },
    _sound_impact_close = exord_guns.sounds._sound_impact_close,
    _sound_impact = exord_guns.sounds._sound_impact,
    _sound_empty = exord_guns.sounds._sound_empty,
    _sound_reload_start = {
        name = "exord_guns_reload_start_whirring",
        gain = 0.4,
        pitch = 1.5,
        max_hear_distance = 200,
    },
    _sound_reload_end = {
        name = "exord_guns_reload_click_in",
        gain = 0.7,
        pitch = 1.2,
        max_hear_distance = 200,
    },
    _cooldown = 4.0,
    _on_cooldown_complete = exord_guns.end_reload,
})

minetest.register_tool("exord_guns:similon4b", {
    description = S("Automatic 4-bore shotgun loaded with buckshot."),
    _exord_guns_name = S("SIMILON-4B"),
    inventory_image = "exord_guns_similon4b.png",
    wield_image = "blank.png",
    on_drop = nullfunc,
    on_use = exord_guns.on_trigger_pull,
    -- on_secondary_use = exord_guns.start_reload,
    -- on_place = exord_guns.start_reload,
    on_step = exord_guns.on_step,
    after_use = function(itemstack, user, node, digparams) end,
    _guns_hud = true,
    _fire_rpm = 200,
    _full_auto = true,
    -- _mag_capacity = 300,
    _proj_number_per_round = 6,
    _infinite_ammo = true,
    _auto_reload = true,
    _proj_gravity = 0,
    _proj_inaccuracy = 4,
    _proj_damage_nodes = 0,
    _proj_damage_players = 0.0,
    _proj_speed = 60,
    _proj_tracer = 3,
    _proj_max_range = 50,
    _proj_zeroing = 0.0,
    _proj_barrel_index = 1,
    _proj_on_prefire = function (itemstack, player, barrel_pos, target_pos)
        local dir = vector.direction(barrel_pos, target_pos)
        exord_guns.do_proj_muzzle_flash_typical(barrel_pos, dir, player, 8, 10, 0.6, 0.5)
    end,
    _proj_on_fire = function(self, itemstack, player)
        local dist = vector.distance(self.position, self.target_pos)
        self.max_range = math.min(self.max_range, dist)
    end,
    _proj_on_hit_target = function(self, target_ent, pointed_thing)
        exord_core.damage_entity(target_ent, exord_core.NumSet.new({
            piercing = 1,
            player   = 0.3,
        }), self.parent)
        return true
    end,
    _sound_fire = {
        name = "exord_guns_rifle_fire_alt",
        gain = 0.8 * exord_core.sound_gain_multiplier,
        pitch = 1.3,
        max_hear_distance = 220,
    },
    -- _sound_impact_close = exord_guns.sounds._sound_impact_close,
    -- _sound_impact = exord_guns.sounds._sound_impact,
    _sound_empty = exord_guns.sounds._sound_empty,
    _cooldown = 0.1,
    _on_cooldown_complete = exord_guns.end_reload,
})

minetest.register_tool("exord_guns:concrete_gun", {
    description = S("Concrete Launcher"),
    _exord_guns_name = S("CONCRETE GUN"),
    inventory_image = "exord_guns_concrete.png",
    wield_image = "blank.png",
    on_drop = nullfunc,
    on_use = exord_guns.on_trigger_pull,
    on_secondary_use = exord_guns.start_reload,
    on_place = exord_guns.start_reload,
    on_step = exord_guns.on_step,
    after_use = function(itemstack, user, node, digparams) end,
    _guns_hud = true,
    _fire_rpm = 150,
    _full_auto = true,
    _mag_capacity = 30,
    _reload_time = 3,
    _auto_reload = true,
    _proj_gravity = 0,
    _proj_inaccuracy = 1,
    _proj_damage_nodes = 0,
    _proj_damage_players = 0,
    _proj_speed = 30,
    _proj_tracer = 6,
    _enable_look_crouch = true,
    _proj_on_step = function(self, dtime)
        local dist = vector.distance(self.position, self.target_pos)
        if dist < 5 then
            self:set_velocity(self._start_vel * (dist*0.1 + 0.01))
        end
    end,
    _proj_on_fire = function(self, itemstack, player)
        local dist = vector.distance(self.position, self.target_pos)
        self.max_range = math.min(self.max_range, dist)
        self._start_vel = self:get_velocity()
    end,
    _proj_on_destroy = function(self, pointed_thing)
        local front = self:get_position()
        exord_core.map.build_radius(self:get_position(), 5.8, "exord_nodes:concrete", false)
        -- 
        exord_guns.do_explosion(self.position, 1, 30, 3)
    end,
    _sound_fire = {
        name = "exord_guns_mk19_gl",
        gain = 0.9 * exord_core.sound_gain_multiplier,
        max_hear_distance = 200,
    },
    _sound_impact_close = exord_guns.sounds._sound_impact_close,
    _sound_impact = exord_guns.sounds._sound_impact,
    _sound_empty = exord_guns.sounds._sound_empty,
    _sound_reload_start = exord_guns.sounds._sound_reload_start,
    _sound_reload_end = exord_guns.sounds._sound_reload_end,
    _proj_max_range = 60,
    _cooldown = 8,
    _on_cooldown_complete = exord_guns.end_reload,
})


minetest.register_tool("exord_guns:gl80coaxial", {
    description = S("GL-80mm Full Auto Coaxial Grenade Launcher Minigun"),
    _exord_guns_name = S("GL-80 COAXIAL"),
    inventory_image = "exord_guns_gl30ca.png",
    wield_image = "blank.png",
    on_drop = nullfunc,
    on_use = exord_guns.on_trigger_pull,
    on_secondary_use = exord_guns.start_reload,
    on_place = exord_guns.start_reload,
    on_step = exord_guns.on_step,
    after_use = function(itemstack, user, node, digparams) end,
    _guns_hud = true,
    _fire_rpm = 230,
    _full_auto = true,
    _infinite_ammo = true,
    -- _mag_capacity = 42,
    -- _auto_reload = true,
    _proj_gravity = 0,
    _proj_inaccuracy = 3,
    _proj_damage_nodes = 0,
    _proj_damage_players = 0,
    _proj_speed = 50,
    _proj_tracer = 5,
    _proj_barrel_index = 2,
    _enable_look_crouch = true,
    _proj_on_step = function(self, dtime)
    end,
    _proj_on_prefire = function (itemstack, player, barrel_pos, target_pos)
        local dir = vector.direction(barrel_pos, target_pos)
        exord_guns.do_proj_muzzle_flash_typical(barrel_pos, dir, player, 4, 10, 0.8, 1)
    end,
    _proj_on_fire = function(self, itemstack, player)
        local dist = vector.distance(self.position, self.target_pos)
        self.max_range = math.min(self.max_range, dist)
    end,
    _proj_on_destroy = function(self, pointed_thing)
        local pos = self:get_position()
        exord_core.map.damage_radius(pos, 1.7, 1, true, 0.7)
        exord_core.damage_radius(pos, 4, exord_core.NumSet.new({
            explosive = 3.6,
            burning = 1,
            player = 1,
        }), self.parent, 1, 2)
        exord_guns.do_explosion(self.position, 1, 14, 2.3, 0.4, 0.3)
        minetest.sound_play("exord_guns_explosion_5", {
            gain = 0.3 * exord_core.sound_gain_multiplier,
            pitch = 1,
            pos = self.position,
            max_hear_distance = 300,
        }, true)
    end,
    _sound_fire = {
        name = "exord_guns_rifle_fire_alt",
        gain = 1.5 * exord_core.sound_gain_multiplier,
        pitch = 1,
        max_hear_distance = 200,
    },
    _sound_impact_close = exord_guns.sounds._sound_impact_close,
    _sound_impact = exord_guns.sounds._sound_impact,
    _sound_empty = exord_guns.sounds._sound_empty,
    _proj_max_range = 60,
    _cooldown = 6.0,
    _on_cooldown_complete = exord_guns.end_reload,
})

