
minetest.register_entity("exord_player:compass", {
    initial_properties = {
        visual = "mesh",
        mesh = "exord_compass.b3d",
        textures = {"[fill:1x2:0,0:#eed^[fill:1x1:0,1:#49f"},
        -- use_texture_alpha = true,
        stepheight = 0,
        hp_max = 20,
        physical = false,
        pointable = false,
        damage_texture_modifier = "^[colorize:#ff9999:50",
        static_save = false,
        glow = 14,
        visual_size = vector.new(1, 1, 1) * 2,
    },
    _hidden = true,
    _hide = function(self)
        if self._hidden then return end
        self._hidden = true
        -- self.object:set_properties({
        --     visual_size = vector.new(0, 0, 0)
        -- })
        COMPAT.set_bone_override(self.object, "origin", {
            scale = {
                vec = vector.new(0,1,0),
                interpolation = 0.4,
                absolute = true,
            },
        })
    end,
    _show = function(self)
        if not self._hidden then return end
        self._hidden = false
        -- self.object:set_properties({
        --     visual_size = vector.new(1, 1, 1)*2
        -- })
        COMPAT.set_bone_override(self.object, "origin", {
            scale = {
                vec = vector.new(1,1,1),
                interpolation = 0.4,
                absolute = true,
            },
        })
    end,
    _get_animation = function(self, radians)
        local deg = (radians * 180 / math.pi) + 360
        deg = 360 - math.round(deg)%360
        self.object:set_animation({x=deg,y=deg}, 1, 0.0, false)
    end,
	on_step = function(self, dtime)
        local player = self._player
        local pi = minetest.is_player(player) and exord_player.check_player(player)
        if not pi then
            -- error("could not get pi in fplayer")
            self.object:remove()
            return
        end
        if pi.compass ~= self then
            -- error("player has not got fplayer logged in pi")
            self.object:remove()
            return
        end

        self._temp_show = (self._temp_show or 0) - dtime

        local ctrl = player:get_player_control()
        if self._temp_show < 0 and not ctrl.aux1 then
            self:_hide()
            return
        end

        local target = exord_core.current_objective or exord_core.last_center_waypoint
        if not target then self:_hide(); return end
        local tpos = target.object:get_pos()
        if not tpos then self:_hide(); return end
        self:_show()
        local dir = vector.direction(self.object:get_pos(), tpos)
        self:_get_animation(minetest.dir_to_yaw(dir))
	end,
    on_deactivate = function(self)
    end,
    on_activate = function(self, staticdata, dtime_s)
        COMPAT.set_bone_override(self.object, "origin", {
            scale = {
                vec = vector.new(0,1,0),
                interpolation = 0.0,
                absolute = true,
            },
        })
    end,
})

LISTEN("on_objective_spawned", function(objective)
    for i, player in ipairs(minetest.get_connected_players()) do
        local pi = exord_player.check_player(player)
        if pi.compass then
            pi.compass._temp_show = 5
        end
    end
end)
