
exord_core.stats = {}

local function check_stats(player, pi)
    pi = pi or exord_core.check_player(player)
    if not pi.stats then
        pi.stats = {
            kills = 0,
            objectives = 0,
            deaths = 0,
            shots_fired = 0,
            weapon_kills = {},
        }
    end
    return pi.stats
end

function exord_core.stats.reset_player_stats(player)
    local stats = check_stats(player)
    stats.deaths = 0
    stats.kills = 0
    stats.objectives = 0
    stats.shots_fired = 0
    for k, v in pairs(stats.weapon_kills) do
        stats.weapon_kills[k] = 0
    end
end

function exord_core.stats.get_player_stats(player)
    return check_stats(player)
end

LISTEN("on_player_stats_elem_update", function(player, elem)
    local stats = exord_core.stats.get_player_stats(player)
    local name = player:get_player_name()
    ---@type bform_prototype
    local kills = assert(elem:get_element_by_id("player_stat:"..name..":kills"))
    local objectives = assert(elem:get_element_by_id("player_stat:"..name..":objectives"))
    local deaths = assert(elem:get_element_by_id("player_stat:"..name..":deaths"))

    kills:set_params({
        _text = minetest.formspec_escape(stats.kills),
    }):signal_changes()
    objectives:set_params({
        _text = minetest.formspec_escape(stats.objectives),
    }):set_visible(false) -- disabled for now
    deaths:set_params({
        _text = minetest.formspec_escape(stats.deaths),
    })
end)

LISTEN("on_fplayer_killed", function(fplayer, player)
    local stats = check_stats(player)
    stats.deaths = stats.deaths + 1
end)

LISTEN("on_player_kill", function(player, enemy)
    local stats = check_stats(player)
    stats.kills = stats.kills + 1
end)

LISTEN("on_player_shot_fired", function(player)
    local stats = check_stats(player)
    stats.shots_fired = stats.shots_fired + 1
end)
