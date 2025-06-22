

exord_core.gametime = 0
-- 0: waiting, 1: grace, 2: playing, 3: gameover
exord_core.gamestate = 0
exord_core.grace_max = 2
exord_core.last_center_waypoint = nil
exord_core.show_gametime = true
exord_core.mobs_max = 10
exord_core.mobs_spawn_interval = 7
exord_core.mobs_spawn_dist_min = 30
exord_core.mobs_spawn_dist_max = 60
exord_core.difficulty = 0.3
exord_core.difficulty_modes = {
    easy      = 0.17,
    normal    = 0.3,
    hard      = 0.5,
    fun_hard  = 0.65,
    very_hard = 1,
}

exord_core.objectives_max = ISDEBUG and 2 or 4
exord_core.objectives_completed = 0
exord_core.current_objective = nil
exord_core.objective_time = 0
exord_core.objective_time_complete = ISDEBUG and 6 or 60

exord_core.tags = {
    spawning = false,
}
exord_core.timescale = 1

exord_mg_custom.set_generator(exord_core.mapgen_profile)

function exord_core.destroy_entities_on_map()
    for i, ent in pairs(minetest.luaentities) do
        ent.object:remove()
    end
end

function exord_core.kill_enemies_on_map()
    for i, ent in pairs(minetest.luaentities) do
        if ent._exord_swarm then
            -- ent:_on_damage(1000)
            pmb_entity_api.set_state(ent, "burrow_and_remove")
        end
    end
end

function exord_core.waypoint_add()
    local waypoint = minetest.add_entity(vector.new(0,2,0), "exord_core:waypoint")
    local entity = waypoint and waypoint:get_luaentity()
    entity._radius = 9
    entity:_set_bottom_height(2)
    entity:_hide_top()
    entity._color_ready = "[fill:1x1:0,0:#4f6^[opacity:100"
    entity._on_enter = exord_core._on_waypoint_enter
    entity._on_leave = exord_core._on_waypoint_leave
    entity._on_counted = exord_core._on_waypoint_counted
    return entity
end

function exord_core._on_waypoint_counted(self, list)
    local fplayers = exord_player.get_alive_fake_players()
    self._is_ready = (#list > #fplayers * 0.66)
end

function exord_core._on_waypoint_enter(self, entity)
    if entity._fake_player and minetest.is_player(entity._player) then
        exord_player.set_ready(entity._player, true)
    end
end

function exord_core._on_waypoint_leave(self, entity)
    if entity._fake_player and minetest.is_player(self._player) then
        exord_player.set_ready(entity._player, false)
    end
end


LISTEN("update_mobspawning_rules", function()
    local f = (exord_core.objectives_completed / exord_core.objectives_max)
    exord_core.mobs_spawn_dist_min = 30
    exord_core.mobs_spawn_dist_max = 50
    exord_core.mobs_max = (exord_core.difficulty * 30) + (f^2 * exord_core.difficulty * 20)
    exord_core.mobs_spawn_interval = math.max(1, 8 - 3 * exord_core.difficulty)

    if exord_core.objectives_completed == 0 then
        exord_core.mobs_max = exord_core.mobs_max / 2
        exord_core.mobs_spawn_interval = 4
    end
    if exord_core.objectives_completed >= exord_core.objectives_max then
        exord_core.mobs_max = (exord_core.difficulty * 30) + (exord_core.difficulty * 20)
        exord_core.mobs_spawn_interval = math.max(0, 4 - 2 * exord_core.difficulty)
        exord_core.mobs_spawn_dist_min = 40
        exord_core.mobs_spawn_dist_max = 60
    end

    -- core.log("mobs_max " .. exord_core.mobs_max)
    -- core.log("mobs_spawn_interval " .. exord_core.mobs_spawn_interval)
end)

LISTEN("on_objective_spawned", function(self)
    exord_core.current_objective = self
    exord_core.voiceover.play_voice_situation("objective_spawned")
end)

LISTEN("on_objective_secured", function(self)
    -- core.log("SECURED")
    exord_core.current_objective = nil
    exord_core.objectives_completed = exord_core.objectives_completed + 1
    exord_core.voiceover.play_voice_situation("objective_secured")
    local pos = self.object:get_pos()
    exord_core.last_objective_position = pos
    exord_player.try_spawn_all_players(pos)
    exord_core.apply_all_player_loadout_selections()
    if exord_core.difficulty < 1 then
        exord_player.heal_all_fplayers(3)
    end
end)

LISTEN("on_objective_secure_start", function(self)
    -- core.log("FIRST CONTACT")
    exord_core.objectives_completed = exord_core.objectives_completed + 1
    SIGNAL("update_mobspawning_rules")
    exord_core.objectives_completed = exord_core.objectives_completed - 1
    if exord_core.objectives_completed == exord_core.objectives_max - 1 then
        exord_core.voiceover.play_voice_situation("objective_secure_start_final")
        exord_core.sfx.stop_tag("ambient_tension")
        exord_core.sfx.start_track("action_tension", {
            name = "507747_magmisoundtracks_action",
            gain = 0.3,
            fade_in_time = 1,
            fade_out_time = 6,
            sound = {
                loop = true,
            },
        }, nil)
    else
        exord_core.voiceover.play_voice_situation("objective_secure_start")
    end
end)

function exord_core.generate_map()
    exord_core.is_map_generated = false
    exord_core.destroy_entities_on_map()
    exord_mg_custom.generate_map(exord_core.mapgen_profile, math.random(1,999999999999), true)
end

exord_core.GameState = {_MFSM_states={}}
table.insert(exord_core.GameState._MFSM_states, {
    name = "tick",
    on_step = function(self, dtime, meta)
        self.t_since_check_players = self.t_since_check_players + dtime
        exord_core.gametime = exord_core.gametime + dtime
    end,
    on_start = function(self, meta)
        self.t_since_check_players = 0
    end,
    is_protected = true,
})

table.insert(exord_core.GameState._MFSM_states, {
    name = "await_mapgen",
    on_step = function(self, dtime, meta)
        if exord_core.is_map_generated then
            MFSM.set_state(self, "waiting", true, true)
        end
    end,
    on_start = function(self, meta)
        exord_core.sfx.stop_tag("ambient_tension")
        exord_core.sfx.stop_tag("action_tension")
        exord_core.gamestate = -1
        exord_core.gametime = 0
        exord_core.tags.spawning = false
        exord_core.show_gametime = false
        SIGNAL("on_gamestate_changed", exord_core.gamestate)
    end,
    on_end = function(self, meta)
    end,
})

table.insert(exord_core.GameState._MFSM_states, {
    name = "waiting",
    on_step = function(self, dtime, meta)
        exord_player.try_spawn_all_players()
        exord_core.apply_all_player_loadout_selections()
        -- only check each second
        if exord_core.last_center_waypoint and exord_core.last_center_waypoint._is_ready then
            MFSM.set_state(self, "grace", true, true)
        end
    end,
    on_start = function(self, meta)
        exord_core.sfx.start_track("ambient_tension", {
            name = "476556_magmisoundtracks_tension",
            gain = 0.14,
            fade_in_time = 1,
            fade_out_time = 2,
            sound = {
                loop = true,
            },
        }, true)
        for i, player in ipairs(exord_player.get_non_spectator_players()) do
            exord_core.stats.reset_player_stats(player)
        end
        SIGNAL("update_mobspawning_rules")
        exord_core.last_center_waypoint = exord_core.waypoint_add()

        exord_core.objectives_completed = 0
        exord_core.current_objective = nil
        exord_core.objective_time = 0

        exord_core.gamestate = 0
        exord_core.gametime = 0
        exord_core.tags.spawning = false
        exord_core.show_gametime = false
        SIGNAL("on_gamestate_changed", exord_core.gamestate)
    end,
    on_end = function(self, meta)
        local waypoint = exord_core.last_center_waypoint
        if waypoint then
            waypoint:_fade_and_destroy()
            exord_core.last_center_waypoint = nil
        end
    end,
})

table.insert(exord_core.GameState._MFSM_states, {
    name = "grace",
    on_step = function(self, dtime, meta)
        exord_player.try_spawn_all_players()
        if exord_core.gametime > 0 then
            MFSM.set_state(self, "game", true, true)
        end
    end,
    on_start = function(self, meta)
        SIGNAL("update_mobspawning_rules")
        exord_core.voiceover.play_voice_situation("game_start")
        exord_core.gamestate = 1
        exord_core.gametime = -exord_core.grace_max
        exord_core.tags.spawning = false
        exord_core.show_gametime = true
        SIGNAL("on_gamestate_changed", exord_core.gamestate)
    end,
})

table.insert(exord_core.GameState._MFSM_states, {
    name = "game",
    on_step = function(self, dtime, meta)
        if self.t_since_check_players > 1 then
            local fplayers = exord_player.get_alive_fake_players()
            -- if all players left or dead
            if #fplayers == 0 then
                MFSM.set_state(self, "gameover", true, true)
                self.t_since_check_players = 0
                return
            end
            self.t_since_check_players = 0
        end

        meta.event_meta = meta.event_meta or {
            time_to_next = math.random(60,120) * (ISDEBUG and 0.01 or 1)
        }
        meta.event_list = meta.event_list or {
            "mob_surge",
            "mob_burrow",
        }
        exord_core.event_request(meta.event_list, meta.event_meta, dtime)

        if exord_core.objectives_completed >= exord_core.objectives_max then
            MFSM.set_state(self, "game_return_to_dropzone", true, true)
            return
        end
        local objective = exord_core.current_objective
        if objective then
            local pos = objective.object:get_pos()
            if pos then
                if objective._is_ready then
                    exord_core.objective_time = exord_core.objective_time + dtime
                end

                if objective._is_ready and not objective._first_enter then
                    objective._first_enter = true
                    SIGNAL("on_objective_secure_start", objective)
                end

                if exord_core.objective_time > exord_core.objective_time_complete then
                    exord_core.objective_time = 0
                    exord_core.current_objective:_fade_and_destroy()
                    exord_core.current_objective:_hide_top()
                    SIGNAL("on_objective_secured", objective)
                end
            else
                objective.object:remove()
                exord_core.current_objective = nil
            end
        else
            meta.last_objective_yaw = meta.last_objective_yaw or (math.random() * math.pi * 2)
            local ryaw = meta.last_objective_yaw + (math.random()*0.6+0.3) * math.pi * (math.random(0,1)*2-1)
            meta.last_objective_yaw = (ryaw + math.pi * 2) % (math.pi * 2)
            local rdir = minetest.yaw_to_dir(ryaw)
            local rpos = rdir * (math.min(exord_mg_custom.maxp.x, exord_mg_custom.maxp.z) * 0.6)
            rpos.y = 2
            local object = minetest.add_entity(rpos, "exord_core:waypoint")
            local ent = object and object:get_luaentity()
            exord_core.current_objective = ent
            ent._radius = 20
            ent._visual_radius = 18
            ent:_hide_top()
            -- ent:_set_top_height(exord_core.map.wall_height+0.1)
            ent:_set_bottom_height(2)
            exord_core.map.damage_radius(rpos, ent._radius + 1, 2000, false, nil)
            SIGNAL("on_objective_spawned", ent)
        end
    end,
    on_start = function(self, meta)
        exord_core.gametime = 0
        exord_core.gamestate = 2
        exord_core.tags.spawning = true
        exord_core.show_gametime = true
        SIGNAL("on_gamestate_changed", exord_core.gamestate)
    end,
})

table.insert(exord_core.GameState._MFSM_states, {
    name = "game_return_to_dropzone",
    on_step = function(self, dtime, meta)
        if self.t_since_check_players > 1 then
            local fplayers = exord_player.get_alive_fake_players()
            local ready = exord_player.get_ready_players()
            if (#ready > 0) and #ready >= #fplayers then
                exord_core.voiceover.play_voice_situation("extraction_start")
                MFSM.set_state(self, "game_extraction", true, true)
                self.t_since_check_players = 0
                return
            end
            -- if all players left or dead
            if #fplayers == 0 then
                MFSM.set_state(self, "gameover", true, true)
                self.t_since_check_players = 0
                return
            end
            self.t_since_check_players = 0
        end
    end,
    on_start = function(self, meta)
        local pos = exord_core.last_objective_position
        exord_player.try_spawn_all_players(pos)
        exord_core.voiceover.play_voice_situation("go_to_extraction")
        exord_player.unready_all_players()
        exord_core.last_center_waypoint = exord_core.waypoint_add()
        exord_core.gamestate = 2.1
        SIGNAL("on_gamestate_changed", exord_core.gamestate)
    end,
    on_end = function(self, meta)
        local waypoint = exord_core.last_center_waypoint
        if waypoint then
            waypoint:_fade_and_destroy()
            exord_core.last_center_waypoint = nil
        end
        exord_player.unready_all_players()
    end,
})

table.insert(exord_core.GameState._MFSM_states, {
    name = "game_extraction",
    on_step = function(self, dtime, meta)
        if self.t_since_check_players > 1 then
            local fplayers = exord_player.get_alive_fake_players()
            -- if all players left or dead
            if #fplayers == 0 then
                MFSM.set_state(self, "gameover", true, true)
                self.t_since_check_players = 0
                return
            end
            self.t_since_check_players = 0
        end

        exord_core.objective_time = exord_core.objective_time + dtime

        if exord_core.objective_time > exord_core.objective_time_complete and not meta.finalised_extraction then
            meta.finalised_extraction = true
            exord_core.voiceover.play_voice_situation("extraction_finish")
            MFSM.set_state(self, "gamewin", true, true)
        end
    end,
    on_start = function(self, meta)
        exord_core.objective_time = 0
        exord_core.tags.spawning = true
        exord_core.show_gametime = true
        exord_player.unready_all_players()
        exord_core.gamestate = 2.2
        SIGNAL("on_gamestate_changed", exord_core.gamestate)
    end,
    on_end = function(self, meta)
        local waypoint = exord_core.last_center_waypoint
        if waypoint then
            waypoint:_fade_and_destroy()
            exord_core.last_center_waypoint = nil
        end
        exord_player.unready_all_players()
    end,
})

table.insert(exord_core.GameState._MFSM_states, {
    name = "gameover",
    on_step = function(self, dtime, meta)
        if meta.state_time > 2 and not meta.hud then
            meta.hud = true
            exord_core.show_stats_form(true)
            for i, player in ipairs(minetest.get_connected_players()) do
                pmb_hud.add_hud(player, "exord_core:gameover", {
                    type = "text",
                    text = minetest.colorize("#f12", "YOU DIED"),
                    position = {x=0.5, y=0.1},
                    alignment = {x=0, y=1},
                    z_index = 807,
                    size = {x=3, y=0},
                })
                pmb_hud.add_hud(player, "exord_core:gameoverbg", {
                    type = "image",
                    text = "[fill:1x1:0,0:#111111f0",
                    position = {x=0.5, y=0.5},
                    alignment = {x=0, y=0},
                    z_index = 806,
                    scale = {x=-100, y=-100},
                })
            end
        end
        if meta.state_time > 7 and not meta.generation_started then
            meta.generation_started = true
            for i, player in ipairs(minetest.get_connected_players()) do
                pmb_hud.add_hud(player, "exord_core:gameover_gen", {
                    type = "text",
                    text = minetest.colorize("#fa3", "Regenerating Map\nThis can take a while."),
                    position = {x=0.5, y=0.1},
                    alignment = {x=0, y=1},
                    offset = {x=0, y=60},
                    z_index = 807,
                    size = {x=1.5, y=0},
                })
                exord_player.set_ready(player, false)
            end

            exord_core.generate_map()
        end

        if meta.state_time > 7 and exord_core.is_map_generated then
            exord_core.close_stats_form()
            MFSM.set_state(self, "await_mapgen", true, true)
        end
    end,
    on_start = function(self, meta)
        exord_core.tags.spawning = false
        exord_core.show_gametime = false
        exord_core.sfx.stop_tag("action_tension")
    end,
    on_end = function(self, meta)
        for i, player in ipairs(minetest.get_connected_players()) do
            pmb_hud.remove_hud(player, "exord_core:gameover")
            pmb_hud.remove_hud(player, "exord_core:gameoverbg")
            pmb_hud.remove_hud(player, "exord_core:gameover_gen")
        end
    end,
})

table.insert(exord_core.GameState._MFSM_states, {
    name = "gamewin",
    on_step = function(self, dtime, meta)
        if meta.state_time > 1.5 and not meta.extract_sequence then
            meta.extract_sequence = true
            for i, fplayer in ipairs(exord_player.get_alive_fake_players()) do
                local pos = fplayer.object:get_pos()
                minetest.add_particlespawner({
                    amount = 300,
                    time = 0.000001,
                    vertical = false,
                    texpool = {
                        {name="[fill:1x1:0,0:#7af"},
                        {name="[fill:1x1:0,0:#adf"},
                        {name="[fill:1x1:0,0:#cef"},
                        {name="[fill:1x1:0,0:#eff"},
                    },
                    alpha_tween = {0, 1},
                    glow = 14,
                    minpos = pos + vector.new(-0.5, -3, -0.5),
                    maxpos = pos + vector.new( 0.5, 0,  0.5),
                    minvel = vector.new(-1, 2, -1),
                    maxvel = vector.new( 1, 40,  1),
                    minexptime = 1,
                    maxexptime = 3,
                    size = {
                        min = 0.1,
                        max = 5,
                        bias = 0.1,
                    },
                })
                minetest.add_particlespawner({
                    amount = 10,
                    time = 0.00001,
                    vertical = false,
                    texpool = {
                        {name="[fill:1x1:0,0:#fff"},
                        {name="[fill:1x1:0,0:#eff"},
                    },
                    alpha_tween = {0, 1},
                    glow = 14,
                    minpos = pos + vector.new(-1, 0, -1)*0.2,
                    maxpos = pos + vector.new( 1, 0,  1)*0.2,
                    minvel = vector.new(-3, 0, -3),
                    maxvel = vector.new( 3, 1,  3),
                    minexptime = 0.1,
                    maxexptime = 0.2,
                    size = {
                        min = 4,
                        max = 8,
                    },
                })
                minetest.sound_play("exord_player_teleport", {
                    pos = pos,
                    gain = 2 * exord_core.sound_gain_multiplier,
                    max_hear_distance = 100,
                })
                exord_guns.stop_all_sounds_for_player(fplayer._player, 50)
                fplayer:_warp_up()
            end
        end
        if meta.state_time > 5 and not meta.hud_shown then
            meta.hud_shown = true
            exord_core.show_stats_form(true)
            for i, player in ipairs(minetest.get_connected_players()) do
                pmb_hud.add_hud(player, "exord_core:gamewin", {
                    type = "text",
                    text = minetest.colorize("#ff8", "MISSION SUCCESS"),
                    position = {x=0.5, y=0.1},
                    alignment = {x=0, y=1},
                    z_index = 807,
                    size = {x=3, y=0},
                })
                pmb_hud.add_hud(player, "exord_core:gamewinbg", {
                    type = "image",
                    text = "[fill:1x1:0,0:#111111f0",
                    position = {x=0.5, y=0.5},
                    alignment = {x=0, y=0},
                    z_index = 806,
                    scale = {x=-100, y=-100},
                })
                exord_player.set_ready(player, false)
            end
        end
        if meta.state_time > 10 and not meta.generation_started then
            meta.generation_started = true
            for i, player in ipairs(minetest.get_connected_players()) do
                pmb_hud.add_hud(player, "exord_core:gamewin_gen", {
                    type = "text",
                    text = minetest.colorize("#fa3", "Regenerating Map\nThis can take a while."),
                    position = {x=0.5, y=0.1},
                    alignment = {x=0, y=1},
                    offset = {x=0, y=60},
                    z_index = 807,
                    size = {x=1.5, y=0},
                })
            end

            exord_core.generate_map()
        end

        if meta.state_time > 11 and exord_core.is_map_generated then
            exord_core.close_stats_form()
            MFSM.set_state(self, "await_mapgen", true, true)
        end
    end,
    on_start = function(self, meta)
        exord_core.sfx.stop_tag("action_tension")
        exord_core.sfx.stop_tag("ambient_tension")
        exord_core.gametime = -10
        exord_core.gamestate = 3
        exord_core.tags.spawning = false
        exord_core.show_gametime = false
        exord_core.timescale = 0
        exord_core.kill_enemies_on_map()
        SIGNAL("on_gamestate_changed", exord_core.gamestate)
    end,
    on_end = function(self, meta)
        for i, player in ipairs(minetest.get_connected_players()) do
            pmb_hud.remove_hud(player, "exord_core:gamewin")
            pmb_hud.remove_hud(player, "exord_core:gamewinbg")
            pmb_hud.remove_hud(player, "exord_core:gamewin_gen")
        end
    end,
})

exord_core.GameState = MFSM.new(exord_core.GameState)
exord_core.GameState:enable_globalstep()

exord_core.GameState:set_states({
    tick = true,
    await_mapgen = true,
}, true)

local _init = false
local _t = 0

minetest.register_globalstep(function(dtime)
    minetest.set_timeofday(0.6)
    if not _init then
        exord_mg_custom.emerge(function()
            SIGNAL("on_mapgen_finished")
        end)
        _init = true
    end

    -- only do once per second
    if _t > 0 then _t = _t - dtime; return else _t = _t + 0.1 end
    -- core.log(exord_core.gametime .. " : " .. math.floor(exord_core.gametime))
    for i, player in ipairs(minetest.get_connected_players()) do
        exord_core.update_capture_hud(player)
        exord_core.update_objectives_hud(player)
    end
end)
