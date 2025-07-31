local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

exord_core = {}

exord_core.mod_storage = minetest.get_mod_storage()
ISDEBUG = false
-- ISDEBUG = true

exord_core.pl = {}
local pl = exord_core.pl
function exord_core.check_player(player)
    local pi = pl[player]
    if not pi then pi = {}; pl[player] = pi end
    exord_core.player_loadout_check(player, pi)
    return pl[player]
end

function exord_core.dist2(v, b)
    return (v.x - b.x)^2 + (v.y - b.y)^2 + (v.z - b.z)^2
end

dofile(mod_path .. "/modules/map/map.lua")
dofile(mod_path .. "/modules/hud.lua")
dofile(mod_path .. "/modules/mapgen/mapgen.lua")
dofile(mod_path .. "/modules/gamestate/MFSM.lua")
dofile(mod_path .. "/modules/soundtracks.lua")
dofile(mod_path .. "/modules/gamestate/gamestate.lua")
dofile(mod_path .. "/modules/spawning.lua")
dofile(mod_path .. "/modules/cooldown.lua")
dofile(mod_path .. "/modules/loadout.lua")
dofile(mod_path .. "/modules/damage.lua")
dofile(mod_path .. "/modules/gui.lua")
dofile(mod_path .. "/modules/waypoint.lua")
dofile(mod_path .. "/modules/voiceover.lua")
dofile(mod_path .. "/modules/events.lua")
dofile(mod_path .. "/modules/stats.lua")
