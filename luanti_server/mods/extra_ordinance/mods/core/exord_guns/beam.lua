

function exord_guns.fire_beam_weapon(itemstack, player, barrel_pos, target_pos)
end

minetest.register_entity("exord_guns:beam", {
    initial_properties = {
        visual = "mesh",
        mesh = "exord_beam_mesh.b3d",
        textures = {
            "[fill:1x1:0,0:#fff",
        },
        use_texture_alpha = false,
        backface_culling = false,
        stepheight = 0,
        hp_max = 20,
        physical = false,
        pointable = false,
        damage_texture_modifier = "^[colorize:#ff9999:50",
        static_save = false,
        glow = 14,
        visual_size = vector.new(0, 0, 1),
    },
    _max_targets = 3,
    _phase_nodes = false,
    _is_valid_target = function(self, ent)
        if ent._on_damage and (ent ~= self._parent) then return true
        else return false end
    end,
    _on_target_hit = function(self, ent, pointed_thing)
    end,
    _get_pointed_list = function(self, barrel_pos, target_pos)
        local dir = vector.direction(barrel_pos, target_pos)
        target_pos = barrel_pos + dir * (self._max_range or 1)
        local ray = minetest.raycast(barrel_pos, target_pos, true, false, nil)
        local targets = self._max_targets
        local furthest_point
        local ents = {}
        for pointed_thing in ray do
            if pointed_thing.type == "node" and not self._phase_nodes then
                furthest_point = pointed_thing.intersection_point or furthest_point
                break
            end
            local ent = pointed_thing.ref and pointed_thing.ref:get_luaentity()
            if ent and self:_is_valid_target(ent) then
                furthest_point = pointed_thing.intersection_point or ent.object:get_pos() or furthest_point
                targets = targets - 1
                table.insert(ents, {ent, pointed_thing})
            end
            if targets <= 0 then break end
        end
        return ents, furthest_point
    end,
    _do_beam = function(self, barrel_pos, target_pos)
        local list, furthest_point = self:_get_pointed_list(barrel_pos, target_pos)
        for i, entdef in ipairs(list) do
            self:_on_target_hit(entdef[1], entdef[2])
        end
        return furthest_point
    end,
    _beam_width = 1,
    _max_range = 50,
    _face_dir = function(self, barrel_pos, target_pos)
        target_pos = target_pos or self._last_point
        if not target_pos then return end
        local dir = vector.direction(barrel_pos, target_pos)
        local rot = vector.dir_to_rotation(dir)
        local dist = self._last_dist or vector.distance(barrel_pos, target_pos)
        dist = math.min(self._max_range, dist)
        self.object:move_to(barrel_pos, true)
        self.object:set_rotation(rot)
        local vs = self.object:get_properties().visual_size
        self.object:set_properties({
            visual_size = vector.new(vs.x, vs.y, dist)
        })
    end,
    _fire_at = function(self, player, barrel_pos, target_pos)
        self._player = player
        self._parent = exord_player.get_alive_fplayer_or_nil(player)
        local point = self:_do_beam(barrel_pos, target_pos)
        self._last_point = point
        self._last_dist = vector.distance(self.object:get_pos(), point)
        self:_face_dir(barrel_pos, point)
    end,
    _fade = function(self, time)
        self._t_fade = time
        self._fade_time_max = time
    end,
    _fade_in = function(self, time)
        self._t_fade_in = time
        self._fade_in_time_max = time
    end,
    _on_fade_complete = function(self)
        self.object:remove()
    end,
    _on_step = function(self, dtime)
    end,
	on_step = function(self, dtime)
        if not minetest.is_player(self._player) then
            return self.object:remove()
        end

        if self._t_fade then
            if self._t_fade > 0 then
                self._t_fade = self._t_fade - dtime
                local factor = math.max(0, self._t_fade / self._fade_time_max)
                local props = self.object:get_properties()
                self.object:set_properties({
                    visual_size = vector.new(
                        self._beam_width * factor,
                        self._beam_width * factor,
                        props.visual_size.z)
                })
            else
                self:_on_fade_complete()
            end
        elseif self._t_fade_in then
            if self._t_fade_in > 0 then
                self._t_fade_in = self._t_fade_in - dtime
                local factor = math.min(1, 1 - self._t_fade_in / self._fade_in_time_max)
                local props = self.object:get_properties()
                self.object:set_properties({
                    visual_size = vector.new(
                        self._beam_width * factor,
                        self._beam_width * factor,
                        props.visual_size.z)
                })
            else
                self._t_fade_in = nil
            end
        elseif not self._init then
            self._init = true
            self.object:set_properties({
                visual_size = vector.new(
                    self._beam_width,
                    self._beam_width,
                    1)
            })
        end

        self:_on_step(dtime)
	end,
    on_deactivate = function(self)
    end,
    on_activate = function(self, staticdata, dtime_s)
    end,
})
