local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

local function do_digging_particles(self, offset)
    local vel = 1
    local dist = 2
    local pos = self.object:get_pos()
    if offset then pos = pos + offset end
    minetest.add_particlespawner({
        amount = 30,
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
        maxexptime = self._lazy + 1,
        minsize = 8,
        maxsize = 16,
    })
end

exord_swarm.worker = {
    initial_properties = {
        visual = "sprite",
        textures = {"[fill:1x1:0,0:#f0f"},
        use_texture_alpha = false,
        stepheight = 0.0,
        hp_max = 3,
        collide_with_objects = false,
        physical = true,
        collisionbox = {-0.1, -0.5, -0.1, 0.1, 0.5, 0.1},
        selectionbox = {-0.8, -0.5, -0.8, 0.8, 1.5, 0.8},
        pointable = true,
        damage_texture_modifier = "^[colorize:#ff9999:0",
        static_save = false,
    },

    _mobcap = false,
    _exord_swarm = true,
    _hp = 30,
    _exord_armor = {
        explosion = 1,
        piercing = 1,
        burning = 1,
        player = 0,
    },
    _on_damage = function(self, damage, source)
        if self._is_dead then return end
        self._hp = self._hp - damage
        if self._hp <= 0 then
            self._is_dead = true
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
        end,
        spawn = {
            -- animation = "spawn",
            on_state_start = function(self)
                self._lazy = math.random() * 2 + 2
                do_digging_particles(self)
                SIGNAL("on_nest_spawned", self)
            end,
            step = function(self, dtime, moveresult)
                if self._pmb_state_time > self._lazy then
                    return "idle"
                end
            end,
        },
        idle = {
            -- animation = "idle",
            on_state_start = function(self)
                exord_core.map.damage_radius(self.object:get_pos(), 9.5, 2000, false, 1)
            end,
            step = function(self, dtime, moveresult)
            end,
        },
        death = {
            -- animation = "death",
            on_state_start = function(self)
                if not self._signalled then
                    self._signalled = true
                    SIGNAL("on_nest_destroyed", self)
                end
                self._pmb_detectable = false
                self.object:set_properties({
                    pointable = false,
                })
                self.object:set_properties({
                    textures = {"[fill:1x1:0,0:#777"}
                })
            end,
            step = function(self, dtime, moveresult)
                if self._pmb_state_time > 3 and not self._removed then
                    self._removed = true
                    self.object:remove()
                end
            end,
        },
    },
    _default_state = "idle",
    on_activate = function(self, staticdata, dtime_s)
        self.object:set_armor_groups({})
        pmb_entity_api.on_activate(self, staticdata, dtime_s)
    end,
    get_staticdata = function(self)
        return pmb_entity_api.get_staticdata(self)
    end,
    on_deactivate = function(self, removal)
        pmb_entity_api.on_deactivate(self, removal)
    end,
    on_punch = function(self, puncher, time_from_last_punch, tool_capabilities, dir, damage)
    end,
    _pmb_staticdata_load_list = {
    },
    _pmb_speed = 0,
    _pmb_acceleration = 0.1,
    _animations = {
        spawn = {frames={x=0, y=0}, blend=0.1, loop=false},
        idle = {frames={x=0, y=0}, blend=0.1},
        death = {frames={x=0, y=0}, blend=0.2, loop=false},
    },
    _pmb_statusfx_enable = true,
}

minetest.register_entity("exord_swarm:nest", exord_swarm.worker)

minetest.register_craftitem("exord_swarm:nest_spawn",
{
    description = "Nest spawn egg",
    inventory_image = "blank.png^[noalpha^[colorize:#f0f:255",
    on_place = function(itemstack, placer, pointed_thing)
        local ent = minetest.add_entity(vector.offset(minetest.get_pointed_thing_position(pointed_thing), 0, 1, 0), "exord_swarm:nest")
    end,
})
