local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

local function nullfunc(...) end

local pl = {}

local function _on_target_hit(self, ent, pointed_thing, multiplier)
    exord_core.damage_entity(ent, exord_core.NumSet.new({
        piercing = 1   * (multiplier or 1),
        burning  = 4   * (multiplier or 1),
        player   = 0.5 * (multiplier or 1),
    }), self._parent)
end

minetest.register_globalstep(function(dtime)
    for player, beam_ent in pairs(pl) do
        local pos = beam_ent and beam_ent.object:get_pos()
        local node = minetest.get_node(pos)
        if node.name == "air" then
            minetest.set_node(pos, {name="pmb_util:light_node_14"})
            local nt = minetest.get_node_timer(pos)
            nt:start(1)
            nt:set(1,0.99)
        end

        local fplayer = exord_player.get_alive_fplayer_or_nil(player)
        local barrel_pos = fplayer and fplayer:_get_barrel_position(2)
        local target_pos = (exord_player.get_player_pointed_thing(player) or {}).intersection_point
        if fplayer and beam_ent and beam_ent.object:get_pos() and target_pos and barrel_pos then
            local list, point = beam_ent:_get_pointed_list(barrel_pos, target_pos)
            beam_ent._parent = fplayer.object
            for i, entdef in ipairs(list) do
                beam_ent:_on_target_hit(entdef[1], entdef[2], dtime*10)
            end
            beam_ent:_face_dir(barrel_pos, point)
        end
    end
end)

minetest.register_tool("exord_guns:asm100", {
    description = S("ASM-100 Laser Rifle"),
    _exord_guns_name = S("ASM-100"),
    inventory_image = "exord_guns_asm100.png",
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
    _mag_capacity = 30,
    _proj_number_per_round = 1,
    _infinite_ammo = false,
    _auto_reload = true,
    _proj_gravity = 0,
    _proj_inaccuracy = 0,
    _proj_max_range = 60,
    _proj_barrel_index = 2,
    _on_started_firing = function(itemstack, player, pi)
        local fplayer = exord_player.get_alive_fplayer_or_nil(player)
        if not fplayer then return end
        local pos = fplayer.object:get_pos()
        local object = minetest.add_entity(pos, "exord_guns:beam")
        local ent = object:get_luaentity()
        if not ent then return end
        ent._beam_width = 0.3
        ent.object:set_properties({
            textures = {"[fill:1x1:0,0:#fd9"}
        })
        ent._on_target_hit = _on_target_hit
        ent._player = player
        ent:_fade_in(0.1)
        pl[player] = ent
    end,
    _on_stopped_firing = function(itemstack, player, pi)
        local ent = pl[player]
        if ent and ent.object:get_pos() then
            ent:_fade(0.2)
        end
        pl[player] = nil
    end,
    _proj_on_prefire = function(itemstack, player, barrel_pos, target_pos)
        return true
    end,
    _sound_firing_loop = {
        name = "exord_guns_beam_fire_loop",
        gain = 1 * exord_core.sound_gain_multiplier,
        pitch = 1.2,
        max_hear_distance = 220,
        fade_out = 100,
        loop = true,
    },
    _sound_firing_loop_end = {
        name = "exord_guns_beam_fire_loop_end",
        gain = 1 * exord_core.sound_gain_multiplier,
        pitch = 1.2,
        max_hear_distance = 220,
    },
    _sound_firing_loop_start = {
        name = "exord_guns_beam_fire_loop_start",
        gain = 0.7 * exord_core.sound_gain_multiplier,
        pitch = 1.2,
        max_hear_distance = 220,
    },
    _sound_reload_start = {
        name = "exord_guns_beam_reload_start",
        gain = 0.9,
        pitch = 1,
        max_hear_distance = 200,
    },
    _sound_reload_end = {
        name = "exord_guns_beam_reload_end",
        gain = 0.9,
        pitch = 1,
        max_hear_distance = 200,
    },
    -- _sound_impact_close = exord_guns.sounds._sound_impact_close,
    -- _sound_impact = exord_guns.sounds._sound_impact,
    _sound_empty = exord_guns.sounds._sound_empty,
    _cooldown = 3.8,
    _on_cooldown_complete = exord_guns.end_reload,
})
