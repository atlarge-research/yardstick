
exord_core.waypoint = {}


local cbox = {
    -0.3, 0,-0.3,
     0.3, 2, 0.3,
}
local sbox = {
    -1, 0,-1,
     1, 2, 1,
}

minetest.register_entity("exord_core:waypoint", {
    initial_properties = {
        visual = "mesh",
        mesh = "exord_waypoint_objective.b3d",
        textures = {
            "[fill:1x1:0,0:#00000000",
        },
        use_texture_alpha = true,
        backface_culling = false,
        stepheight = 0,
        hp_max = 20,
        physical = false,
        collisionbox = cbox,
        selectionbox = sbox,
        pointable = false,
        damage_texture_modifier = "^[colorize:#ff9999:50",
        static_save = false,
        glow = 14,
        visual_size = vector.new(30, 1, 30),
    },
    _radius = 8,
    _height = 1,
    _refresh_time = 1,
    _t_refresh = 0,
    _is_ready = false,
    _can_be_counted = function(self, entity)
        return entity and entity._fake_player == true
    end,
    _color_ready = "[fill:1x1:0,0:#4f6^[opacity:20",
    _color_idle = "[fill:1x1:0,0:#4af^[opacity:100",
    _color_fade = "[fill:1x1:0,0:#4f6^[opacity:20",
    _set_bottom_height = function(self, height)
        COMPAT.set_bone_override(self.object, "bottom", {
            scale = {
                vec = vector.new(1, height*10, 1),
                interpolation = 0.2,
                absolute = false,
            },
        })
    end,
    _set_top_height = function(self, height)
        COMPAT.set_bone_override(self.object, "top", {
            position = {
                vec = vector.new(0, (height-1)*10, 0),
                interpolation = 0.2,
                absolute = false,
            },
        })
    end,
    _hide_top = function(self)
        COMPAT.set_bone_override(self.object, "top", {
            scale = {
                vec = vector.new(0, 0, 0),
                absolute = false,
            }
        })
    end,
    _show_top = function(self)
        COMPAT.set_bone_override(self.object, "top", {
            scale = {
                vec = vector.new(1, 1, 1),
                absolute = false,
            }
        })
    end,
    _update_texture = function(self)
        if self._is_ready then
            self.object:set_properties({
                textures = {self._color_ready},
            })
        else
            self.object:set_properties({
                textures = {self._color_idle},
            })
        end
    end,
    _on_counted = function(self, list)
        self._is_ready = #list > 0
    end,
    _count_within = function(self)
        local last_list = self._last_list or {}
        local list = {}
        for i, object in ipairs(core.get_objects_inside_radius(self.object:get_pos(), self._radius)) do
            local entity = object and object:get_luaentity()
            if self._can_be_counted(self, entity) then
                table.insert(list, entity)
                if table.indexof(last_list, entity) <= 0 then
                    self._on_enter(self, entity)
                end
            end
        end
        for i, entity in ipairs(last_list) do
            if table.indexof(list, entity) <= 0 then
                self._on_leave(self, entity)
            end
        end
        return list
    end,
    _on_enter = function(self, entity)
    end,
    _on_leave = function(self, entity)
    end,
    _fade_and_destroy = function(self)
        self._deactivate_time = 1
        self.object:set_animation({x=40,y=50}, 24, 0.0, false)
        self.object:set_properties({
            textures = {self._color_fade},
        })
    end,
	on_step = function(self, dtime)
        if self._deactivate_time then
            self._deactivate_time = self._deactivate_time - dtime
            if self._deactivate_time < 0 then
                self.object:remove()
            end
            return
        end
        if self._t_refresh > 0 then
            self._t_refresh = self._t_refresh - dtime
        else self._t_refresh = self._t_refresh + self._refresh_time;
            local props = self.object:get_properties()
            local radius = self._visual_radius or self._radius
            if (props.visual_size.x ~= radius*2)
            or (props.visual_size.y ~= self._height) then
                self.object:set_properties({
                    visual_size = vector.new(
                        radius*2,
                        self._height,
                        radius*2
                    )
                })
            end

            local list = self._count_within(self)
            self._on_counted(self, list)
            self._update_texture(self)
        end
	end,
    on_deactivate = function(self)
    end,
    on_activate = function(self, staticdata, dtime_s)
        pmb_entity_api.on_activate(self, staticdata, dtime_s)
        self.object:set_animation({x=0,y=39}, 24, 0.2, true)
    end,
})
