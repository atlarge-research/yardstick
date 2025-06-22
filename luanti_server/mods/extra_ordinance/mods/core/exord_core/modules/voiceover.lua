


exord_core.voiceover = {}
exord_core._registered_voiceline_situations = {}

function exord_core.voiceover.radio_start(player_name)
    minetest.sound_play("exord_radio_start", {
        gain = 1,
        to_player = player_name,
    }, true)
end
function exord_core.voiceover.radio_stop(player_name)
    minetest.sound_play("exord_radio_stop", {
        gain = 1,
        to_player = player_name,
    }, true)
end

local _queue = {}

local buffer_time = 0

local function add_to_queue(def, player)
    local event = {
        def = table.copy(def),
        player_name = minetest.is_player(player) and player:get_player_name() or nil,
        time = def.time,
        started = false,
    }
    table.insert(_queue, event)
end

local function play_event(event)
    local sdef = event.def
    if not sdef then return end
    exord_core.voiceover.radio_start(event.player_name)
    minetest.sound_play(sdef.name, sdef, true)
end

minetest.register_globalstep(function(dtime)
    local event = _queue[1]
    if buffer_time > 0 then
        buffer_time = buffer_time - dtime
        return
    end

    if not event then return end
    if not event.started then
        event.started = true
        play_event(event)
    end

    event.time = event.time - dtime
    if event.time < 0 then
        buffer_time = 0.5
        exord_core.voiceover.radio_stop(event.player_name)
        table.remove(_queue, 1)
    end
end)


function exord_core.voiceover.play_voice_track(def, player)
    add_to_queue(def, player)
end

function exord_core.voiceover.play_voice_situation(tag, player)
    local voices_for_tag = exord_core._registered_voiceline_situations[tag]
    if not voices_for_tag then return end
    local ri = math.random(1, #voices_for_tag)
    local track = voices_for_tag[ri]
    if not track then
        -- core.log("warning", "NO TRACK FOR VOICEOVER TAG " .. tag)
        return
    end
    exord_core.voiceover.play_voice_track(track, player)
end

function exord_core.voiceover.register_voiceline_situation(tag, def)
    local voices_for_tag = exord_core._registered_voiceline_situations[tag]
    if not voices_for_tag then
        voices_for_tag = {}
        exord_core._registered_voiceline_situations[tag] = voices_for_tag
    end
    table.insert(voices_for_tag, def)
end

-- PLAYER SPECIFIC SPAWN
exord_core.voiceover.register_voiceline_situation("player_spawn", {
name = "exord_f_systems_online_proceed_to_zone", time = 3.1,})
exord_core.voiceover.register_voiceline_situation("player_spawn", {
name = "exord_m_we_just_landed", time = 3.4,})
exord_core.voiceover.register_voiceline_situation("player_spawn", {
name = "exord_m_engines_running_regrouping", time = 2.4,})

exord_core.voiceover.register_voiceline_situation("player_spawn", {
name = "exord_m_regrouping_now", time = 1.4,})
exord_core.voiceover.register_voiceline_situation("player_spawn", {
name = "exord_m_all_engines_weapons_ready", time = 2.62,})
exord_core.voiceover.register_voiceline_situation("player_spawn", {
name = "exord_m_ground_crew_down_ready", time = 2.6,})
exord_core.voiceover.register_voiceline_situation("player_spawn", {
name = "exord_m_ground_crew_here_ready", time = 2.5,})
exord_core.voiceover.register_voiceline_situation("player_spawn", {
name = "exord_m_touch_down_ready", time = 2.6,})

-- GAME STARTED
exord_core.voiceover.register_voiceline_situation("game_start", {
name = "exord_m_lets_go", time = 0.75,})
exord_core.voiceover.register_voiceline_situation("game_start", {
name = "exord_m_lets_move_out", time = 1.1,})
exord_core.voiceover.register_voiceline_situation("game_start", {
name = "exord_f_mission_underway_move_first", time = 4,})
exord_core.voiceover.register_voiceline_situation("game_start", {
name = "exord_f_move_to_first", time = 2.78,})
exord_core.voiceover.register_voiceline_situation("game_start", {
name = "exord_f_give_em_hell", time = 2.1,})
exord_core.voiceover.register_voiceline_situation("game_start", {
name = "exord_f_good_luck_out_there", time = 1.2,})

-- OBJECTIVE SECURE START
exord_core.voiceover.register_voiceline_situation("objective_secure_start", {
name = "exord_m_securing_objective", time = 1.7,})

-- OBJECTIVE SECURE START (FINAL)
exord_core.voiceover.register_voiceline_situation("objective_secure_start_final", {
name = "exord_f_huge_wave_incoming", time = 3.6,})
exord_core.voiceover.register_voiceline_situation("objective_secure_start_final", {
name = "exord_f_watch_out_ground_crew", time = 3.1,})
exord_core.voiceover.register_voiceline_situation("objective_secure_start_final", {
name = "exord_m_oh_theyre_coming_in_now", time = 1.9,})
exord_core.voiceover.register_voiceline_situation("objective_secure_start_final", {
name = "exord_m_oh_they_didnt_like_that", time = 2,})

-- OBJECTIVE SECURED
exord_core.voiceover.register_voiceline_situation("objective_secured", {
name = "exord_m_objective_secured", time = 1.45,})
exord_core.voiceover.register_voiceline_situation("objective_secured", {
name = "exord_f_nice_work_objective_secured", time = 2.85,})
exord_core.voiceover.register_voiceline_situation("objective_secured", {
name = "exord_f_one_objective_down", time = 2.6,})
exord_core.voiceover.register_voiceline_situation("objective_secured", {
name = "exord_f_objective_confirmed", time = 3.1,})

--- EXTRACTION
exord_core.voiceover.register_voiceline_situation("go_to_extraction", {
name = "exord_f_you_are_clear_to_return_to_dropzone", time = 2.7,})
exord_core.voiceover.register_voiceline_situation("go_to_extraction", {
name = "exord_f_well_done_return_to_dropzone", time = 3.3,})
exord_core.voiceover.register_voiceline_situation("go_to_extraction", {
name = "exord_m_time_to_head_home", time = 2.7,})
exord_core.voiceover.register_voiceline_situation("go_to_extraction", {
name = "exord_m_objectives_complete_heading_home", time = 2.7,})

-- EXTRACTION START
exord_core.voiceover.register_voiceline_situation("extraction_start", {
name = "exord_f_starting_extraction_stand_by", time = 3.8,})
exord_core.voiceover.register_voiceline_situation("extraction_start", {
name = "exord_f_i_see_you_just_one_moment", time = 3.8,})

-- EXTRACTION FINISH
exord_core.voiceover.register_voiceline_situation("extraction_finish", {
name = "exord_f_engage", time = 1.2,})
exord_core.voiceover.register_voiceline_situation("extraction_finish", {
name = "exord_f_teleporting", time = 1,})
exord_core.voiceover.register_voiceline_situation("extraction_finish", {
name = "exord_f_teleporting_2", time = 1.2,})

-- MOB_SURGE
exord_core.voiceover.register_voiceline_situation("mob_surge", {
name = "exord_m_uhoh_seismic", time = 3.0,})
exord_core.voiceover.register_voiceline_situation("mob_surge", {
name = "exord_m_we_got_incoming", time = 1.4,})

-- MOB_BURROW
exord_core.voiceover.register_voiceline_situation("mob_burrow", {
name = "exord_m_theyre_coming_up_from_below", time = 1.3,})
exord_core.voiceover.register_voiceline_situation("mob_burrow", {
name = "exord_m_theyre_right_under_us", time = 1.3,})
