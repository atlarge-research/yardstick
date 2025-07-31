
local on_proj_hit = function(self, entity, pointed_thing)
    if entity and entity._exord_proj_on_damage
    and entity._exord_proj_on_damage(entity, self.damage_players or 1, self) ~= false then
        return true
    end
    return false
end

exord_guns.projectile_bullet = {
    damage_nodes = 3,
    damage_players = 2,
    inaccuracy = 4,
    tracer = 0.3,
    on_step = function(self, dtime)
        if not self.idef then self.idef = {} end
        if not self.hits then self.hits = {} end
        if self._inaccurate == nil then
            self._inaccurate = exord_guns.vec3_randrange(-self.inaccuracy, self.inaccuracy)
            if self._inaccurate.y > 0 then self._inaccurate.y = 0 end
            self._inaccurate = vector.normalize(self._inaccurate) * self.inaccuracy
        end
        local r = math.random() * 10
        self:set_velocity(self.velocity + self._inaccurate * dtime * r)
        self._inaccurate = self._inaccurate - (self._inaccurate * dtime * r)

        local dist2 = exord_proj.dist2(self.position, self.origin)
        local dist_factor = dist2 / (self.max_range^2)
        if self.tracer > 0 then
            minetest.add_particle({
                pos = vector.offset(self.position, 0, -0.1, 0),
                velocity = self.velocity*0.95,
                collisiondetection = true,
                collision_removal = true,
                texture = "blank.png^[noalpha^[colorize:#"..(
                       (dist_factor > 0.8 and "777")
                    or (dist_factor > 0.4 and "f72")
                    or "fe8"
                )..":255",
                expirationtime = dtime + 0.01,
                size = self.tracer,
                acceleration = self.acceleration,
                glow = 14,
            })
        end
        if self.idef._force_horizontal then
            self.velocity.y = 0
        end

        if self.idef._proj_on_step then
            self.idef._proj_on_step(self, dtime)
        end
    end,
    can_collide = function(self, pointed_thing)
        if minetest.is_player(pointed_thing.ref) then
            return false
        elseif pointed_thing.ref then
            local ent = pointed_thing.ref:get_luaentity()
            return (ent._is_dead ~= true) and (ent._hp > 0) and (pointed_thing.ref ~= self.parent)
        elseif pointed_thing.type == "node" then
            local ndef = minetest.registered_nodes[minetest.get_node(pointed_thing.under).name]
            if ndef.walkable ~= false then
                return true
            end
        end
        return true
    end,
    on_collide = function(self, pointed_thing)
        local point = pointed_thing.intersection_point or pointed_thing.above
        if point then self:set_position(point + vector.new(1,1,1)*0.0001) end
        if self.idef._sound_impact then
            minetest.sound_play(self.idef._sound_impact.name, {
                gain = (self.idef._sound_impact.gain or 1),
                max_hear_distance = self.idef._sound_impact.max_hear_distance or 20,
                pitch = (self.idef._sound_impact.pitch or 1) + (self.idef._sound_impact.pitch_random or 0) * (math.random()*2-1),
                pos = self.position,
            })
        end
        minetest.add_particlespawner({
            amount = 8,
            time = 0.00001,
            vertical = false,
            texture = "blank.png^[noalpha^[colorize:#fe8:255",
            glow = 1,
            pos = pointed_thing.intersection_point or pointed_thing.above,
            minvel = (pointed_thing.intersection_normal or vector.new(0,0,0)) * 0.1 + vector.new(-5,-5,-5),
            maxvel = (pointed_thing.intersection_normal or vector.new(0,0,0)) * 5 + vector.new(5,5,5),
            minexptime = 0.05,
            maxexptime = 0.1,
            minsize = 0.1,
            maxsize = 2,
        })

        local ent = pointed_thing.ref and (pointed_thing.ref ~= self.parent) and pointed_thing.ref:get_luaentity()
        local hit_function = self.idef._proj_on_hit_target or on_proj_hit
        if ent and hit_function(self, ent, pointed_thing) and not self.hits[ent] then
            self.hits[ent] = true
            if self.penetrations_remaining and self.penetrations_remaining > 0 then
                self.penetrations_remaining = self.penetrations_remaining - 1
                local len = vector.length(self.velocity)
                local vel = vector.normalize(
                    vector.normalize(self.velocity) + exord_guns.vec3_randrange(-0.3, 0.3)
                ) * len * 0.8
                -- vel.y = 0
                self:set_velocity(vel)
                return false
            end
            if self.idef._proj_on_destroy then
                if self.idef._proj_on_destroy(self, pointed_thing) then
                    return false
                end
            end
            return true
        elseif pointed_thing.type == "node" then
            if self.idef._proj_on_destroy then
                if self.idef._proj_on_destroy(self, pointed_thing) then
                    return false
                end
            end
            return true
        end
    end,
    on_removed = function(self)
        if self.idef._proj_on_destroy then
            self.idef._proj_on_destroy(self, nil)
        end
    end,
}
